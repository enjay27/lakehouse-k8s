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
    out = run(
        ["kubectl", "rollout", "restart", f"deploy/{deployment}", "-n", namespace],
        timeout=timeout,
    )
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
            "It resolves no grants, so it should not move. Any effect reported",
            "below that is smaller than this spread is noise.",
        ]

    apis = sorted({a for c in cells for a in c["warm"] if a != CONTROL})

    lines += ["", "## Index effect (isolates GRANT volume)", ""]
    lines += ["| API | clones | without | with | delta |", "|---|---:|---:|---:|---:|"]
    for api in apis:
        for row in index_effect(cells, api):
            lines.append(
                f"| `{api}` | {row['clones']:,} | {row['without_ms']:.2f} | "
                f"{row['with_ms']:.2f} | {row['delta_ms']:+.2f} |"
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
