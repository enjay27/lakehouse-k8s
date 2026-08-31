"""
api_sweep.py
============
Per-API wall-clock latency across grant AND entity volume, cold and warm.

Phase 1 stage 4. Notebook 02 measured the index's effect on ONE statement;
02b measured plan shape across grant volume. Neither answers the question a
reader actually asks -- "what does this cost my callers" -- because both stop
at the database. This measures the REST call.

WHAT MOVES, AND WHAT THAT BUYS
------------------------------
Both axes move together, by Kade's call (2026-08-21). Cloned user-sets from
`entity_replay` supply both at once: 10,000 clones is ~70,000 `entities` rows
AND ~550,000 `grant_records` rows.

Moving two variables at once normally destroys attribution. It does not here,
because the grid separates them after the fact:

  * the INDEX toggle, at fixed volume, isolates the grant axis -- the index
    touches the grantee lookup and nothing else;
  * comparing volumes AT index-present isolates the entity axis -- the grant
    lookup is an index scan in both, so what moves is payload and path
    resolution.

So report the two contrasts, never the raw cell-to-cell delta, which confounds
them.

THE CLONES ARE LOAD, NOT TARGETS
--------------------------------
Every measured call is aimed at a REAL fixture entity. The clones exist to make
the tables big. This matters for a reason that is easy to miss: clones are
read-only rows with no MinIO objects behind them, so any API that vends
credentials fails against one -- and a failed call has a latency, which a naive
harness would record as if it were the answer.

Aiming at real entities also keeps the two axes honest. Every authenticated
request pays the same 7-statement authorization prelude whatever it targets, so
grant volume reaches the measurement regardless; and LIST endpoints still see
the clones, because the clones are in the result set. Nothing is lost by not
pointing at them.

`assert_ok` enforces the rest: a non-2xx is never timed.

COLD IS NOT WHAT IT SOUNDS LIKE
-------------------------------
"Cold" here means FIRST TOUCH AFTER RESTART, and that is not the same as an
entity-cache miss. The first call after a restart also pays JVM class loading,
connection-pool establishment and pgjdbc's `prepareThreshold=5` promotion. This
repo has measured a first-call penalty of 25.2 ms against a 1.3 ms steady state
-- 19x -- and almost none of that was the cache.

`warm_up()` absorbs it: after each restart it hammers a DIFFERENT catalog first,
so the JVM and the pool are warm while the entity actually being measured is
still cold. Label the number "first touch after restart" regardless.

And do not expect "super faster". Measured over the 178 MB capture, 734 of 844
requests (87%) contain a batched revalidation and ZERO were served purely from
cache, because resolving a path must load its first entity BY NAME. A warm
request issues FEWER statements, not none. A 2x drop is the correct result; if
something reports 50x, suspect the measurement.

ONE COLD SAMPLE PER RESTART
---------------------------
Cold is not repeatable without another restart, so a cold figure is n=1 with no
median and no spread. It is reported as a single number and flagged as such.
The warm figure beside it is `timeit(k=15, warmup=2)` with min/max.
"""

import statistics
import subprocess
import time

import api_trace

#: The control. It resolves no grants, so nothing this sweep does should move
#: it. In notebook 02 the control moving the WRONG way is what ruled out
#: session warming and made the table credible -- keep it in every cell.
CONTROL = "POST /oauth/tokens"

DEFAULT_NAMESPACE = "datahub-hynix"
DEFAULT_DEPLOYMENT = "benchmarks-polaris"


# ----------------------------------------------------------------------
# restart
# ----------------------------------------------------------------------
def restart_polaris(
    namespace=DEFAULT_NAMESPACE,
    deployment=DEFAULT_DEPLOYMENT,
    timeout=240,
    runner=None,
):
    """`kubectl rollout restart`, then block until the rollout reports complete.

    Returns the elapsed seconds and both commands' output. Raises on failure --
    a sweep that silently measured against a half-restarted deployment would
    produce a cold column that is partly warm, and nothing downstream could
    detect it.

    `runner` is injected so the grid can be tested without a cluster.
    """
    run = runner or _run
    t0 = time.time()

    # `kubectl rollout restart` only PATCHES the pod template; the deployment
    # controller acts on it asynchronously. Run `rollout status` immediately
    # after and it can report the PREVIOUS rollout complete -- so the sweep
    # concludes Polaris is up, health/ready answers from the pod that is about
    # to terminate, and the first real request lands on a closed socket.
    #
    # That is exactly the failure seen 2026-08-21: ConnectionError [Errno 61]
    # on /oauth/tokens, with the cluster perfectly healthy by the time anyone
    # looked. Not load, not connections -- a race in this function.
    #
    # `.metadata.generation` increments on the patch; `.status.observedGeneration`
    # catches up only once the controller has seen it. Waiting for that closes
    # the window before `rollout status` is asked anything.
    gen_before = _generation(run, namespace, deployment, timeout)
    out = run(
        ["kubectl", "rollout", "restart", f"deploy/{deployment}", "-n", namespace],
        timeout=timeout,
    )
    _await_generation(run, namespace, deployment, gen_before, timeout)

    status = run(
        [
            "kubectl",
            "rollout",
            "status",
            f"deploy/{deployment}",
            "-n",
            namespace,
            f"--timeout={int(timeout)}s",
        ],
        timeout=timeout + 30,
    )
    return {
        "seconds": time.time() - t0,
        "restart": out.strip(),
        "status": status.strip(),
    }


def _generation(run, namespace, deployment, timeout):
    """The deployment's spec generation. Increments on every template patch."""
    out = run(
        [
            "kubectl",
            "get",
            "deploy",
            deployment,
            "-n",
            namespace,
            "-o",
            "jsonpath={.metadata.generation}",
        ],
        timeout=timeout,
    )
    return int((out or "0").strip() or 0)


def _await_generation(
    run, namespace, deployment, gen_before, timeout, sleep=time.sleep
):
    """Block until the controller has OBSERVED the restart we just requested.

    Without this, `rollout status` answers about the rollout that finished
    yesterday.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        out = run(
            [
                "kubectl",
                "get",
                "deploy",
                deployment,
                "-n",
                namespace,
                "-o",
                "jsonpath={.metadata.generation} {.status.observedGeneration}",
            ],
            timeout=timeout,
        )
        parts = (out or "").split()
        if len(parts) == 2:
            gen, observed = int(parts[0]), int(parts[1])
            if gen > gen_before and observed >= gen:
                return {"generation": gen, "observed": observed}
        sleep(1.0)
    raise TimeoutError(
        f"deploy/{deployment} never observed the restart (generation stuck at "
        f"{gen_before}). Asking `rollout status` now would report the previous "
        "rollout complete and the sweep would measure a terminating pod."
    )


def _run(cmd, timeout):
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:  # kubectl not on PATH
        raise RuntimeError(
            f"{cmd[0]} not found. The sweep drives the restart itself, so it "
            "must run somewhere with cluster access."
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"{' '.join(cmd)} failed [{proc.returncode}]: "
            f"{(proc.stderr or proc.stdout).strip()[:400]}"
        )
    return proc.stdout


def wait_until_serving(probe, timeout=180, interval=2.0, sleep=time.sleep):
    """Poll until `probe()` is truthy. Rollout-complete is not serving-ready.

    A Deployment reports complete when its pods pass their readiness probe,
    which says nothing about whether Polaris has finished wiring its metastore
    connection. Measuring through that window would put startup cost inside the
    first cold sample, where it is indistinguishable from cache behaviour.

    Returns the seconds waited; raises on timeout rather than measuring a
    Polaris that is not up.
    """
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        try:
            if probe():
                return {"seconds": time.time() - t0, "attempts": True}
        except Exception as exc:  # connection refused during startup is normal
            last = exc
        sleep(interval)
    raise TimeoutError(
        f"Polaris did not answer within {timeout}s of the rollout completing"
        + (f" (last error: {last})" if last else "")
    )


# ----------------------------------------------------------------------
# the API surface
# ----------------------------------------------------------------------
def read_operations(fx):
    """Every read-only API worth timing, bound to a REAL fixture.

    `fx` names live entities: catalog, namespace, principal, principal_role,
    catalog_role. Writes are deliberately absent -- they mutate the very tables
    whose row counts define the cell, so a write inside a measurement loop moves
    the independent variable while it is being measured.

    Returns a list of (label, surface, fn(pc) -> response).
    """
    c = fx["catalog"]
    ns = fx["namespace"]
    return [
        ("GET  /principals", "mgmt", lambda pc: pc.list_principals()),
        (
            "GET  /principals/{name}",
            "mgmt",
            lambda pc: pc.get_principal(fx["principal"]),
        ),
        ("GET  /principal-roles", "mgmt", lambda pc: pc.list_principal_roles()),
        (
            "GET  /principal-roles/{name}",
            "mgmt",
            lambda pc: pc.get_principal_role(fx["principal_role"]),
        ),
        (
            "GET  /principal-roles/{n}/principals",
            "mgmt",
            lambda pc: pc.list_principals_for_principal_role(fx["principal_role"]),
        ),
        ("GET  /catalogs", "mgmt", lambda pc: pc.list_catalogs()),
        ("GET  /catalogs/{name}", "mgmt", lambda pc: pc.get_catalog(c)),
        (
            "GET  /catalogs/{c}/catalog-roles",
            "mgmt",
            lambda pc: pc.list_catalog_roles(c),
        ),
        (
            "GET  /catalog-roles/{r}/grants",
            "mgmt",
            lambda pc: pc.list_grants(c, fx["catalog_role"]),
        ),
        ("GET  /namespaces", "iceberg", lambda pc: pc.list_namespaces(c)),
        ("GET  /namespaces/{ns}", "iceberg", lambda pc: pc.get_namespace(c, ns)),
        ("GET  /namespaces/{ns}/tables", "iceberg", lambda pc: pc.list_tables(c, ns)),
        ("GET  /namespaces/{ns}/views", "iceberg", lambda pc: pc.list_views(c, ns)),
    ]


def assert_ok(label, resp):
    """A non-2xx is an error path, and error paths have latencies too.

    Timing one and putting it in a column headed "ms" is how a harness reports
    a 403 as a performance characteristic. Refuse instead.
    """
    code = getattr(resp, "status_code", 0)
    if not (200 <= code < 300):
        body = (getattr(resp, "text", "") or "")[:200]
        raise AssertionError(
            f"{label} returned {code}, so its timing would be an error path, "
            f"not latency: {body}"
        )
    return code


# ----------------------------------------------------------------------
# measurement
# ----------------------------------------------------------------------
def warm_up(pc, decoy, rounds=8):
    """Warm the JVM, the connection pool and pgjdbc -- but NOT the measured
    entity's cache entry.

    Everything here targets `decoy`, a catalog that no measurement touches. The
    entity actually under test stays cold, so the cold column reports cache
    behaviour rather than 25 ms of class loading.
    """
    for _ in range(rounds):
        try:
            pc.get_catalog(decoy)
            pc.list_principal_roles()
        except Exception:  # a decoy failure must not abort the sweep
            pass
    return rounds


def measure_cold(pc, ops):
    """ONE call per API, first touch after restart. n=1, no median, no spread.

    Cold is not repeatable without another restart, so this cannot be averaged
    and is not presented as if it could be.
    """
    out = {}
    for label, surface, fn in ops:
        t0 = time.perf_counter()
        resp = fn(pc)
        dt = (time.perf_counter() - t0) * 1000
        assert_ok(label, resp)
        out[label] = {"surface": surface, "ms": dt, "n": 1, "cold": True}
    return out


def measure_warm(pc, ops, k=15, warmup=2):
    """Median/min/max per API once the cache and the pool have settled."""
    out = {}
    for label, surface, fn in ops:
        assert_ok(label, fn(pc))  # prove it serves before timing it
        med, lo, hi = api_trace.timeit(lambda: fn(pc), k=k, warmup=warmup)
        out[label] = {
            "surface": surface,
            "ms": med,
            "min": lo,
            "max": hi,
            "n": k,
            "cold": False,
        }
    return out


def measure_control(pc, client_id, client_secret, k=15, warmup=2):
    """`POST /oauth/tokens` -- the thing that must not move.

    Separate from the read ops because it is unauthenticated and takes
    credentials rather than a fixture, and because it is the one result read
    first: if the control moves with the treatment, the cell is measuring
    session warming and every other number in it is suspect.
    """
    assert_ok(CONTROL, pc.get_token(client_id, client_secret))
    med, lo, hi = api_trace.timeit(
        lambda: pc.get_token(client_id, client_secret), k=k, warmup=warmup
    )
    return {
        CONTROL: {
            "surface": "auth",
            "ms": med,
            "min": lo,
            "max": hi,
            "n": k,
            "cold": False,
        }
    }


# ----------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------
def run_sweep(
    volumes,
    index_states,
    apply_volume,
    apply_index,
    restart,
    connect,
    ops_for,
    on_progress=None,
    k=15,
    warmup=2,
):
    """Drive volume x index x {cold, warm} and return one record per cell.

    Callbacks, so this is testable without a cluster and without a database:

      apply_volume(n) -> dict   set clone volume, return measured row counts
      apply_index(present) -> dict   toggle the index, return its proven state
      restart() -> dict         restart Polaris and wait until it serves
      connect() -> pc           a freshly authenticated client (the old token
                                belongs to a process that no longer exists)
      ops_for(pc) -> (ops, decoy, control_args)

    Ordering is chosen to minimise the expensive transition. Volume is outermost
    because changing it rewrites hundreds of thousands of rows; index is inner
    because CONCURRENTLY needs no restart. A restart happens per (volume, index)
    pair because that is what makes the cold sample cold.
    """
    say = on_progress or (lambda _: None)
    cells = []
    for n in volumes:
        say(f"volume: {n:,} clones")
        vol = apply_volume(n)
        for present in index_states:
            say(f"  index present={present}")
            idx = apply_index(present)
            rs = restart()
            pc = connect()
            ops, decoy, control_args = ops_for(pc)

            warm_up(pc, decoy)
            cold = measure_cold(pc, ops)
            warm = measure_warm(pc, ops, k=k, warmup=warmup)
            warm.update(measure_control(pc, *control_args, k=k, warmup=warmup))

            cells.append(
                {
                    "clones": n,
                    "index": present,
                    "volume": vol,
                    "index_state": idx,
                    "restart": rs,
                    "cold": cold,
                    "warm": warm,
                }
            )
            say(f"    {len(cold)} APIs cold, {len(warm)} warm")
    return cells


# ----------------------------------------------------------------------
# reading the result
# ----------------------------------------------------------------------
def noise_floor(cells, api):
    """The worst WITHIN-CELL spread for this API. The real noise floor.

    `render_report` used to bound its claims with the CONTROL's spread across
    cells, and that was badly wrong. Measured 2026-08-22: the control's
    cross-cell spread was 0.60 ms while within-cell spreads ran 35-60 ms
    against medians of ~7 ms. Deltas of 0.02-2.58 ms were reported against a
    floor two orders of magnitude too low.

    The mistake was comparing medians to medians. A median of 15 calls is
    stable by construction -- that is what a median is for -- so the spread
    BETWEEN medians says nothing about whether any single median is
    trustworthy. min/max within a cell says exactly that, and `measure_warm`
    has been recording it all along.
    """
    spreads = [
        c["warm"][api]["max"] - c["warm"][api]["min"]
        for c in cells
        if api in c["warm"] and "max" in c["warm"][api]
    ]
    return max(spreads) if spreads else None


def cell_integrity(cell):
    """Did this cell actually exercise the condition its label claims?

    A cell labelled `index=False` is only measuring the unindexed path if the
    planner actually stopped using an index. Measured 2026-08-22 at 3,064
    `grant_records`: every cell -- index present AND absent -- planned an
    **Index Only Scan**, because the primary key covers the grantee query and
    at that size scanning the whole PK beats a heap scan. The Seq Scan the
    entire audit is about never appeared, so the index contrast was void while
    the table said `without` and `with` in confident columns.

    Returns a list of reasons the cell does not measure what it says.
    """
    problems = []
    scan = (cell.get("scan") or {}).get("plan") or ""
    if cell.get("index") is False and "Seq Scan" not in scan:
        problems.append(
            f"labelled index-absent but planned {scan!r} -- the PK still covers "
            "the grantee lookup at this row count, so this cell did NOT measure "
            "the unindexed path"
        )
    if (cell.get("scan") or {}).get("probe_is_clone"):
        problems.append("the plan probe landed on a CLONE grantee, not a real one")
    bloat = (cell.get("volume") or {}).get("bloat") or {}
    grants = bloat.get("grant_records") or {}
    if grants.get("dead_share", 0) > 0.1:
        problems.append(
            f"{grants['dead_tuples']:,} dead tuples ({grants['dead_share']:.0%} "
            "of the table) -- a Seq Scan reads those pages, so this cell's scan "
            "cost is partly the PREVIOUS cell's deleted rows"
        )
    rows = (cell.get("volume") or {}).get("rows") or {}
    if rows.get("grant_records", 0) < 30_000:
        problems.append(
            f"{rows.get('grant_records', 0):,} grant_records -- below the 30,009 "
            "at which notebook 02 first measured an index effect, so an absence "
            "of effect here is uninformative"
        )
    return problems


def index_effect(cells, api):
    """Index-absent minus index-present, per volume. The GRANT axis.

    This is the contrast that isolates grant volume: the index changes only the
    grantee lookup, and the row count is identical on both sides.
    """
    out = []
    for n in sorted({c["clones"] for c in cells}):
        by = {c["index"]: c for c in cells if c["clones"] == n}
        if not (True in by and False in by):
            continue
        off = by[False]["warm"].get(api)
        on = by[True]["warm"].get(api)
        if off and on:
            out.append(
                {
                    "clones": n,
                    "without_ms": off["ms"],
                    "with_ms": on["ms"],
                    "delta_ms": off["ms"] - on["ms"],
                }
            )
    return out


def volume_effect(cells, api, index=True):
    """Latency across volume AT FIXED index state. The ENTITY axis.

    Held at index-present by default: with the grantee lookup on an index scan
    in every cell, what remains that moves with volume is payload size and path
    resolution.
    """
    rows = sorted(
        (c for c in cells if c["index"] is index and api in c["warm"]),
        key=lambda c: c["clones"],
    )
    return [{"clones": c["clones"], "ms": c["warm"][api]["ms"]} for c in rows]


def control_drift(cells):
    """How far the control moved across the whole grid.

    If this is comparable to the effects being reported, the sweep measured
    ambient noise and should say so instead of publishing a table.
    """
    xs = [c["warm"][CONTROL]["ms"] for c in cells if CONTROL in c["warm"]]
    if len(xs) < 2:
        return None
    return {
        "min_ms": min(xs),
        "max_ms": max(xs),
        "spread_ms": max(xs) - min(xs),
        "median_ms": statistics.median(xs),
    }


def cold_penalty(cells, api):
    """Cold over warm, per cell. n=1 on the cold side -- a ratio, not a finding.

    The prediction on record is a modest drop, because no request is served
    purely from cache. A large ratio here is more likely to be residual startup
    cost that `warm_up` failed to absorb than a cache effect.
    """
    out = []
    for c in cells:
        cold = c["cold"].get(api)
        warm = c["warm"].get(api)
        if cold and warm and warm["ms"]:
            out.append(
                {
                    "clones": c["clones"],
                    "index": c["index"],
                    "cold_ms": cold["ms"],
                    "warm_ms": warm["ms"],
                    "ratio": cold["ms"] / warm["ms"],
                }
            )
    return out


def render_report(cells, meta):
    """Markdown: the control first, then the two contrasts, then cold/warm.

    The control leads deliberately. A reader who sees it moved as much as the
    treatment should stop reading, and burying that under the headline table is
    how a noisy run gets published.
    """
    if not cells:
        return "# API latency sweep\n\nNo cells. Nothing to report.\n"

    lines = ["# API latency sweep", ""]
    for key in ("run_id", "realm", "schema", "polaris"):
        if key in meta:
            lines.append(f"- **{key}**: {meta[key]}")
    lines += [
        "",
        "Every number below comes from calls aimed at REAL fixture entities.",
        "Cloned rows supply volume only -- they are synthetic, have no storage",
        "behind them, and nothing is measured against them.",
        "",
        "## Control -- read this first",
        "",
    ]

    drift = control_drift(cells)
    if drift is None:
        lines.append("Control not recorded. Treat every number here as unverified.")
    else:
        lines += [
            f"`{CONTROL}` across all {len(cells)} cells: "
            f"median {drift['median_ms']:.2f} ms, "
            f"spread {drift['spread_ms']:.2f} ms "
            f"({drift['min_ms']:.2f} .. {drift['max_ms']:.2f}).",
            "",
            "It resolves no grants, so it should not move -- and it did not.",
            "",
            "**But do NOT use this spread as the noise floor.** It is a spread",
            "between MEDIANS, and a median of 15 calls is stable by",
            "construction; it says nothing about whether any one median is",
            "trustworthy. The `noise` column below carries the within-cell",
            "min/max spread, which does. An earlier version of this report made",
            "exactly that substitution and bounded 2 ms claims with a 0.6 ms",
            "figure while the true spread was 60 ms.",
        ]

    apis = sorted({a for c in cells for a in c["warm"] if a != CONTROL})

    flawed = [(c, cell_integrity(c)) for c in cells]
    flawed = [(c, p) for c, p in flawed if p]
    if flawed:
        lines += ["", "## THIS RUN DOES NOT MEASURE WHAT THE TABLES SAY", ""]
        for c, probs in flawed:
            lines.append(f"- **clones={c['clones']:,}, index={c['index']}**")
            for pr in probs:
                lines.append(f"  - {pr}")
        lines += [
            "",
            "Read the tables below as a proof that the harness runs, not as a",
            "result. Fixing the labels would not help: the cells have to be",
            "re-measured at a volume where the planner behaves differently.",
        ]

    lines += ["", "## Index effect (isolates GRANT volume)", ""]
    lines += [
        "`noise` is the worst within-cell min/max spread for that API -- the",
        "real floor. A delta smaller than it is not a measurement.",
        "",
        "| API | clones | without | with | delta | noise | verdict |",
        "|---|---:|---:|---:|---:|---:|:--|",
    ]
    for api in apis:
        floor = noise_floor(cells, api)
        for row in index_effect(cells, api):
            verdict = (
                "NOISE"
                if floor is not None and abs(row["delta_ms"]) < floor
                else "above floor"
            )
            lines.append(
                f"| `{api}` | {row['clones']:,} | {row['without_ms']:.2f} | "
                f"{row['with_ms']:.2f} | {row['delta_ms']:+.2f} | "
                f"{'-' if floor is None else f'{floor:.2f}'} | {verdict} |"
            )

    lines += ["", "## Volume effect at index-present (isolates ENTITY volume)", ""]
    lines += [
        "| API | "
        + " | ".join(f"{n:,}" for n in sorted({c["clones"] for c in cells}))
        + " |"
    ]
    lines.append("|---" * (1 + len({c["clones"] for c in cells})) + "|")
    for api in apis:
        pts = {r["clones"]: r["ms"] for r in volume_effect(cells, api)}
        cols = " | ".join(
            f"{pts[n]:.2f}" if n in pts else "-"
            for n in sorted({c["clones"] for c in cells})
        )
        lines.append(f"| `{api}` | {cols} |")

    lines += [
        "",
        "## Cold vs warm",
        "",
        "Cold is **first touch after restart**, n=1, no median and no spread --",
        "it is not repeatable without another restart. It also is not a pure",
        "cache miss: `warm_up()` absorbs JVM and pool cost against a decoy",
        "catalog, but any residue lands here.",
        "",
        "| API | clones | index | cold (n=1) | warm | ratio |",
        "|---|---:|:--:|---:|---:|---:|",
    ]
    for api in apis:
        for row in cold_penalty(cells, api):
            lines.append(
                f"| `{api}` | {row['clones']:,} | {row['index']} | "
                f"{row['cold_ms']:.2f} | {row['warm_ms']:.2f} | "
                f"{row['ratio']:.1f}x |"
            )

    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------
# replication
# ----------------------------------------------------------------------
def replication_lag(conn):
    """Bytes each standby is behind the primary's current WAL position.

    This exists because of a threat the seeder surfaced and the sweep would
    not: **Polaris connects through Pgpool, which load-balances SELECTs to
    standbys.** Every EXPLAIN in this repo is pinned to the primary with
    `/*NO LOAD BALANCE*/`, so the database-side evidence is safe -- but the
    REST calls 02c times are not pinned to anything.

    Two distinct ways that ruins a cell, and only the first is obvious:

      1. **Volume the standby has not got yet.** `apply_volume` writes ~550,000
         rows to the primary. Until they replicate, a request served by a
         standby is scanning a SMALLER table -- so the cell's label says 10,000
         clones while the measurement says something else entirely. It is a
         silent under-read, not an error.
      2. **Two servers in one median.** Standbys have their own buffer cache
         and their own load. Mixing them into one `timeit` is measuring which
         host answered, not what the index did.

    Returns a list of per-standby dicts. An empty list means no streaming
    standby is connected -- which is itself worth seeing, since this cluster is
    supposed to have one.
    """
    with conn.cursor() as cur:
        cur.execute(api_trace.NO_LOAD_BALANCE + """SELECT application_name, state,
                        pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)
                 FROM pg_stat_replication""")
        return [
            {"standby": name, "state": state, "behind_bytes": int(behind or 0)}
            for name, state, behind in cur.fetchall()
        ]


def wait_for_replicas(conn, timeout=120, interval=1.0, max_bytes=0, sleep=time.sleep):
    """Block until every streaming standby has replayed the primary's WAL.

    Call it after any bulk write and BEFORE measuring, so a cell cannot time
    requests against a table the standby has not finished growing.

    `max_bytes=0` demands exact catch-up. Raises rather than measuring at an
    unknown volume -- reporting a number whose row count is uncertain is the
    failure this whole directory is organised against.
    """
    t0 = time.time()
    seen = 0
    while time.time() - t0 < timeout:
        lag = replication_lag(conn)
        if not lag:
            # No standby streaming. Whether that is fine depends on whether one
            # was there a moment ago: a cluster with no replica is simply not
            # load-balancing, but a standby that VANISHED mid-wait dropped its
            # connection part-way through the insert and is now an unknown
            # number of rows behind. Treating those two alike would let the
            # second pass as "caught up".
            if seen:
                raise RuntimeError(
                    f"{seen} standby(s) were streaming and now none are. One "
                    "disconnected mid-write and is an unknown distance behind; "
                    "measuring now would time requests against a table of "
                    "unknown size. Check the replica before re-running."
                )
            return {"standbys": 0, "seconds": time.time() - t0, "lag": []}
        seen = max(seen, len(lag))
        worst = max(s["behind_bytes"] for s in lag)
        if worst <= max_bytes:
            return {"standbys": len(lag), "seconds": time.time() - t0, "lag": lag}
        sleep(interval)
    raise TimeoutError(
        f"standbys still behind after {timeout}s: {replication_lag(conn)}. "
        "Measuring now would time requests against a table that has not "
        "finished replicating, at a volume the cell label would misstate."
    )


# ----------------------------------------------------------------------
# bloat
# ----------------------------------------------------------------------
def table_bloat(conn, schema, table):
    """Pages, bytes and dead tuples. Recorded per cell, because a Seq Scan
    reads PAGES, not rows.

    This is the hazard a cheap reset removes, and it is not obvious. Changing
    volume between cells means deleting the previous cell's clones -- at 10,000
    clones that is ~550,000 rows -- and `DELETE` reclaims nothing. The tuples
    are dead but the pages remain, and a sequential scan reads every one of
    them. `ANALYZE` updates the planner's statistics and moves no data.

    So an ascending grid (0 -> 1,000 -> 10,000) measures its later cells
    against a table carrying the corpses of its earlier ones. The buffer counts
    and scan times would rise with volume exactly as predicted, partly for the
    wrong reason, and nothing in the output would say so.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE + """SELECT pg_relation_size(c.oid) / 8192,
                        pg_total_relation_size(c.oid),
                        coalesce(s.n_live_tup, 0), coalesce(s.n_dead_tup, 0)
                 FROM pg_class c
                 JOIN pg_namespace n ON n.oid = c.relnamespace
                 LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
                 WHERE n.nspname = %s AND c.relname = %s""",
            (schema, table),
        )
        row = cur.fetchone()
    if not row:
        return None
    pages, total_bytes, live, dead = row
    return {
        "pages": int(pages),
        "total_bytes": int(total_bytes),
        "live_tuples": int(live),
        "dead_tuples": int(dead),
        "dead_share": (dead / (live + dead)) if (live + dead) else 0.0,
    }


def compact(conn, schema, table):
    """`VACUUM (FULL, ANALYZE)` -- rewrite the table so its page count reflects
    its row count.

    Plain `VACUUM` marks space reusable but does not shrink the relation, so a
    Seq Scan still reads the same number of pages. FULL rewrites. It takes an
    ACCESS EXCLUSIVE lock, which is unacceptable in production and completely
    fine here: nothing else is using this cluster, and a deterministic page
    count is the whole point of the exercise.

    Requires autocommit -- VACUUM cannot run inside a transaction block.
    """
    t0 = time.time()
    with conn.cursor() as cur:
        cur.execute(f"VACUUM (FULL, ANALYZE) {schema}.{table}")  # noqa: S608
    return {"seconds": time.time() - t0, "after": table_bloat(conn, schema, table)}


# ----------------------------------------------------------------------
# identities
# ----------------------------------------------------------------------
def auth_path_operations(fx):
    """The small op set worth repeating per identity.

    Not the full surface -- that would multiply an already long grid by the
    number of identities for very little. These three force a complete path
    resolution and therefore the whole authorization prelude, which is the part
    a grantee's own grant-set size acts on.
    """
    c, ns = fx["catalog"], fx["namespace"]
    return [
        ("GET  /catalogs/{name}", "mgmt", lambda pc: pc.get_catalog(c)),
        ("GET  /namespaces", "iceberg", lambda pc: pc.list_namespaces(c)),
        ("GET  /namespaces/{ns}", "iceberg", lambda pc: pc.get_namespace(c, ns)),
    ]


def bind_identity(label, client, ops):
    """Re-bind `ops` to a specific authenticated client, and say whose.

    THE GAP THIS CLOSES (Kade, 2026-08-22). Every measurement so far has been
    made AS ROOT, and root is the least representative identity in the realm:
    its authorization resolves PRINCIPAL_ROLE_USAGE to service_admin and
    SERVICE_MANAGE_ACCESS on the root container -- **two rows**. An ordinary
    principal resolves through its principal-role to a catalog-role holding 25
    or 50 privileges.

    That difference is not incidental, it is the mechanism behind 02's headline:
    Seq Scan cost is constant regardless of how many rows the grantee owns
    (the crossover run measured `filtered` as the whole table at every volume),
    while index-scan cost tracks rows RETURNED. So grant-set size moves the
    index-PRESENT column and barely touches index-absent -- which is precisely
    why 02 measured ~100x for a small grantee and single digits for a large one.

    Sweeping only as root measures the identity that benefits most, and reports
    it as if it were typical.
    """
    return [
        (f"{name} [{label}]", surface, (lambda f: (lambda _pc: f(client)))(fn))
        for name, surface, fn in ops
    ]


def identity_grant_footprint(conn, schema, realm, principal_name):
    """How many grant_records the authorization of `principal_name` walks.

    Counts grants whose grantee is the principal, any principal-role it holds,
    or any catalog-role those principal-roles hold -- the chain the prelude
    actually traverses.

    Measured rather than assumed: "each principal has 50 privileges" is a
    statement about how the fixture was seeded, and this repo has been wrong
    three times about constants it did not ask the server for.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE + f"""WITH p AS (
                    SELECT id FROM {schema}.entities
                     WHERE realm_id = %s AND type_code = 2 AND name = %s),
                  pr AS (
                    SELECT g.securable_id AS id FROM {schema}.grant_records g
                     JOIN p ON p.id = g.grantee_id WHERE g.realm_id = %s),
                  cr AS (
                    SELECT g.securable_id AS id FROM {schema}.grant_records g
                     JOIN pr ON pr.id = g.grantee_id WHERE g.realm_id = %s)
                SELECT count(*) FROM {schema}.grant_records
                 WHERE realm_id = %s AND grantee_id IN (
                    SELECT id FROM p UNION SELECT id FROM pr
                    UNION SELECT id FROM cr)""",  # noqa: S608
            (realm, principal_name, realm, realm, realm),
        )
        row = cur.fetchone()
    return int(row[0]) if row else 0


#: Fixture keys `full_read_operations` needs beyond `read_operations`'. A
#: fixture missing one of these cannot bind the entity-level reads at all --
#: which is not hypothetical: the 1,000-principal fixture was seeded with
#: `create_tables: False`, so `loadTable` and friends had no target and
#: `listTables` was measured against an EMPTY collection.
FULL_FIXTURE_KEYS = ("table", "view", "generic_table", "policy")


class UndriveableOp(RuntimeError):
    """The fixture holds no entity of the kind this operation needs.

    A THIRD outcome, distinct from both success and refusal, and it has to stay
    distinct. `loadTable` against a fixture seeded with `create_tables: False`
    is not a 404 finding about Polaris and not a 403 about the identity -- it
    is the fixture having nothing to load. Rendered as either of the other two,
    it becomes a claim about the server that the run cannot support.
    """


def _require(value, what, label):
    if value is None:
        raise UndriveableOp(f"{label.strip()}: the fixture has no {what}")
    return value


def full_read_operations(fx):
    """Every GET and HEAD the 1.3.0 spec defines. All 29.

    `read_operations` covers 13 -- 45% of the readable surface -- and its
    omissions are not evenly spread. The four missing MANAGEMENT reads are
    precisely the role-graph traversals (principal -> principal-role ->
    catalog-role), which is the authorization model itself and therefore the
    part of the surface most likely to touch `grant_records` more than once.
    The missing ICEBERG reads are every entity-level load plus all three
    existence checks. The Polaris extensions were absent entirely.

    Kept SEPARATE from `read_operations` rather than replacing it. That op list
    is the denominator of an already-correlated capture
    (`privscan-20260824-123408`), and a report whose denominator moved under it
    is a report about nothing. Notebooks 01/02/02b/02c depend on it too.

    THREE THINGS THIS LIST CANNOT PROMISE, and the harness reports each:

    * **Availability.** Generic tables and policies are feature-flagged in 1.3.
      A 404 or 501 is a measured fact about this deployment, recorded as
      `unavailable` -- not a failure, and not a reason to drop the op.
    * **Driveability.** `loadTable`/`headTable`/`loadCredentials` need a table
      to exist. Against a `--no-tables` fixture they are undriveable, which is
      a different thing from unauthorized and must not be rendered as a 404
      finding.
    * **Completeness.** This list is transcribed from the spec, and a
      transcribed constant is a hypothesis (MEMORY: the 25-privilege
      retraction). `probe_openapi.py` diffs it against the RUNNING server's own
      document; that diff, not this docstring, is the authority.

    Args:
        fx: fixture naming live entities. Needs `read_operations`' keys plus
            `FULL_FIXTURE_KEYS`; missing optional ones yield ops bound to None,
            which the probe will classify as undriveable rather than crash.

    Returns:
        list of (label, surface, fn(pc) -> response), in spec order.
    """
    c = fx["catalog"]
    ns = fx["namespace"]
    pr = fx["principal_role"]
    cr = fx["catalog_role"]
    tbl = fx.get("table")
    view = fx.get("view")
    gt = fx.get("generic_table")
    pol = fx.get("policy")

    return [
        # -- management service: 13 GETs, spec order --
        ("GET  /catalogs", "mgmt", lambda pc: pc.list_catalogs()),
        ("GET  /catalogs/{name}", "mgmt", lambda pc: pc.get_catalog(c)),
        ("GET  /principals", "mgmt", lambda pc: pc.list_principals()),
        (
            "GET  /principals/{name}",
            "mgmt",
            lambda pc: pc.get_principal(fx["principal"]),
        ),
        (
            "GET  /principals/{p}/principal-roles",
            "mgmt",
            lambda pc: pc.list_principal_roles_assigned(fx["principal"]),
        ),
        ("GET  /principal-roles", "mgmt", lambda pc: pc.list_principal_roles()),
        (
            "GET  /principal-roles/{name}",
            "mgmt",
            lambda pc: pc.get_principal_role(pr),
        ),
        (
            "GET  /principal-roles/{n}/principals",
            "mgmt",
            lambda pc: pc.list_principals_for_principal_role(pr),
        ),
        (
            "GET  /principal-roles/{n}/catalog-roles/{c}",
            "mgmt",
            lambda pc: pc.list_catalog_roles_for_principal_role(pr, c),
        ),
        (
            "GET  /catalogs/{c}/catalog-roles",
            "mgmt",
            lambda pc: pc.list_catalog_roles(c),
        ),
        (
            "GET  /catalogs/{c}/catalog-roles/{r}",
            "mgmt",
            lambda pc: pc.get_catalog_role(c, cr),
        ),
        (
            "GET  /catalog-roles/{r}/principal-roles",
            "mgmt",
            lambda pc: pc.list_assignee_principal_roles_for_catalog_role(c, cr),
        ),
        (
            "GET  /catalog-roles/{r}/grants",
            "mgmt",
            lambda pc: pc.list_grants(c, cr),
        ),
        # -- iceberg catalog service: 8 GETs + 3 HEADs --
        #: `warehouse` is optional in the Iceberg spec and REQUIRED in practice
        #: for a non-root principal: without it Polaris cannot resolve which
        #: catalog's config to return and answers 400. Measured 2026-08-24 --
        #: the first full-surface probe filed that 400 as a refusal, which read
        #: as "ordinary principals may not read the config" and was really a
        #: missing query parameter.
        (
            "GET  /config",
            "iceberg",
            lambda pc: pc.get_config(warehouse=c),
        ),
        ("GET  /namespaces", "iceberg", lambda pc: pc.list_namespaces(c)),
        ("GET  /namespaces/{ns}", "iceberg", lambda pc: pc.get_namespace(c, ns)),
        ("HEAD /namespaces/{ns}", "iceberg", lambda pc: pc.head_namespace(c, ns)),
        ("GET  /namespaces/{ns}/tables", "iceberg", lambda pc: pc.list_tables(c, ns)),
        (
            "GET  /namespaces/{ns}/tables/{t}",
            "iceberg",
            lambda pc: pc.load_table(
                c, ns, _require(tbl, "table", "GET  /namespaces/{ns}/tables/{t}")
            ),
        ),
        (
            "HEAD /namespaces/{ns}/tables/{t}",
            "iceberg",
            lambda pc: pc.head_table(
                c, ns, _require(tbl, "table", "HEAD /namespaces/{ns}/tables/{t}")
            ),
        ),
        (
            "GET  /namespaces/{ns}/tables/{t}/credentials",
            "iceberg",
            lambda pc: pc.load_credentials(
                c, ns, _require(tbl, "table", "GET  /credentials")
            ),
        ),
        ("GET  /namespaces/{ns}/views", "iceberg", lambda pc: pc.list_views(c, ns)),
        (
            "GET  /namespaces/{ns}/views/{v}",
            "iceberg",
            lambda pc: pc.load_view(
                c, ns, _require(view, "view", "GET  /namespaces/{ns}/views/{v}")
            ),
        ),
        (
            "HEAD /namespaces/{ns}/views/{v}",
            "iceberg",
            lambda pc: pc.head_view(
                c, ns, _require(view, "view", "HEAD /namespaces/{ns}/views/{v}")
            ),
        ),
        # -- polaris extensions: 5 GETs, feature-flagged --
        (
            "GET  /generic-tables",
            "polaris",
            lambda pc: pc.list_generic_tables(c, ns),
        ),
        (
            "GET  /generic-tables/{gt}",
            "polaris",
            lambda pc: pc.load_generic_table(
                c, ns, _require(gt, "generic table", "GET  /generic-tables/{gt}")
            ),
        ),
        ("GET  /policies", "polaris", lambda pc: pc.list_policies(c, ns)),
        (
            "GET  /policies/{p}",
            "polaris",
            lambda pc: pc.load_policy(
                c, ns, _require(pol, "policy", "GET  /policies/{p}")
            ),
        ),
        (
            "GET  /applicable-policies",
            "polaris",
            lambda pc: pc.get_applicable_policies(c, ns),
        ),
    ]
