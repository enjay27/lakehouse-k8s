#!/usr/bin/env python3
"""Generate `02c_api_latency_sweep.ipynb`.

The notebook is generated rather than hand-edited for the same reason 02b was:
a 20-cell notebook edited in place drifts from the module it drives, and a
`replace()` that silently matches nothing is the specific way that drift got
into this directory before. Every substitution here is asserted.

    python3 build_02c.py && python3 verify_02c.py
"""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "02c_api_latency_sweep.ipynb"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip("\n"),
    }


CELLS = [
    md("""
# 02c — per-API latency across grant *and* entity volume

**What this measures.** Wall-clock milliseconds for every read API on both REST
surfaces, across cloned volume, with and without `idx_grant_records_grantee`,
cold and warm.

**What 02 and 02b did not.** 02 measured one statement. 02b measured plan shape
across grant volume and found its own clock unusable once the scan went
parallel. Both stop at the database. A reader asking "what does this cost my
callers" gets no answer from either.

**Both axes move together**, by design (Kade, 2026-08-21). Cloned user-sets
supply `entities` and `grant_records` at once. That would normally destroy
attribution; here the grid recovers it:

| contrast | held fixed | isolates |
|---|---|---|
| index absent vs present | volume | **grant** volume — the index touches the grantee lookup and nothing else |
| volume, at index-present | index | **entity** volume — the grant lookup is an index scan on both sides |

Report those two. The raw cell-to-cell delta confounds them.

**The clones are load, not targets.** Every measured call is aimed at a real
fixture entity. Clones have no MinIO objects behind them, so an API that vends
credentials fails against one — and a failed call still has a latency, which a
naive harness would print in a column headed "ms". `assert_ok` refuses to time
any non-2xx.

**Cold means first touch after restart**, not a cache miss. This repo has
measured a 25.2 ms first call against a 1.3 ms steady state — 19x, almost none
of it the cache. `warm_up()` absorbs the JVM and pool cost against a *decoy*
catalog so the measured entity stays cold. Cold is n=1 and is labelled as such.

**Do not expect "super faster."** Over the 178 MB capture, 734 of 844 requests
(87%) contained a batched revalidation and **zero** were served purely from
cache, because resolving a path must load its first entity by name. A warm
request issues fewer statements, not none. 2x is the correct result.
"""),
    code("""
import os, sys, json, time, pathlib, datetime
import requests

HERE = pathlib.Path.cwd()
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import psycopg2
import api_trace, api_sweep, entity_replay, grant_scale, run_manifest
from polaris_rest import PolarisREST

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
MGMT_URL = os.environ.get("POLARIS_MGMT_URL", "http://192.168.139.2:8182")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")
K8S_NS = os.environ.get("POLARIS_K8S_NAMESPACE", "datahub-hynix")
K8S_DEPLOY = os.environ.get("POLARIS_K8S_DEPLOYMENT", "benchmarks-polaris")

conn = psycopg2.connect(**PG)
conn.autocommit = True          # CONCURRENTLY cannot run inside a transaction
with conn.cursor() as cur:
    cur.execute(api_trace.NO_LOAD_BALANCE + "SELECT version(), pg_is_in_recovery()")
    ver, standby = cur.fetchone()
assert not standby, "routed to a STANDBY — every DDL and count here needs the primary"
print(ver.split(",")[0])
print(f"polaris {POLARIS_URL}   mgmt {MGMT_URL}   deploy {K8S_NS}/{K8S_DEPLOY}")
"""),
    md("""
## 1. Preflight — resolve the fixture, and prove kubectl can drive the restart

Three things have to be true before a four-hour grid is worth starting, and all
three are cheap to check now and expensive to discover later:

1. a **real, complete** user-set exists to aim at, and a **different** one
   exists to use as the warm-up decoy — sharing them would warm the very cache
   entry the cold sample is supposed to find empty;
2. `kubectl` can reach the deployment, because the notebook drives the restart
   itself;
3. nothing is already wearing the clone prefix, because volume changes start
   from a known-empty state.
"""),
    code("""
# --- a real fixture to aim at, and a DIFFERENT one as the decoy ---
FIXTURE_USER = os.environ.get("SWEEP_FIXTURE", "user1")
DECOY_USER = os.environ.get("SWEEP_DECOY", "user2")
assert FIXTURE_USER != DECOY_USER, (
    "the decoy must not be the measured user-set — warming it would fill the "
    "cache entry the cold sample exists to find empty"
)

tmpl = entity_replay.read_template(conn, SCHEMA, REALM, FIXTURE_USER)
_ = entity_replay.read_template(conn, SCHEMA, REALM, DECOY_USER)   # must exist too

FIXTURE = {
    "catalog": f"{FIXTURE_USER}_catalog",
    "namespace": "ns1",
    "principal": f"{FIXTURE_USER}_principal",
    "principal_role": f"{FIXTURE_USER}_principal_role",
    "catalog_role": "owner_principal",
}
DECOY = f"{DECOY_USER}_catalog"
print(f"target {FIXTURE['catalog']}   decoy {DECOY}")
print(f"template: {len(tmpl['entities'])} entities, {len(tmpl['grants'])} grants per clone")

# --- kubectl reachable? ---
probe = api_sweep._run(["kubectl", "get", "deploy", K8S_DEPLOY, "-n", K8S_NS], timeout=30)
print(probe.strip().splitlines()[-1])

# --- clone prefix free? ---
entity_replay.assert_prefix_is_free(conn, SCHEMA, REALM)
TABLES = ("entities", "grant_records")
base_counts = run_manifest.table_counts(conn, SCHEMA, TABLES)
print("baseline rows:", base_counts)
"""),
    md("""
## 2. The grid

`VOLUMES` are clone counts, not row counts. Each clone is one whole user-set, so
the row cost is `len(template)` entities and `len(grants)` grant rows apiece —
printed below so the projection is visible before anything is written, not
inferred afterwards.

Three volume points, because two cannot show whether the curve is linear. The
prediction on record: a serial Seq Scan over ~600k `grant_records` rows is tens
of milliseconds **per authenticated request**, so the index-absent column should
rise roughly linearly with volume while the index-present column stays flat.

If it does not — if per-API latency barely moves at 600k rows without the index
— then either the auth prelude is not issuing the statement we think it is, or
the cache is absorbing it. Either would be a bigger finding than the sweep, and
the notebook should say so rather than reporting "no effect".
"""),
    code("""
VOLUMES = [int(x) for x in os.environ.get("SWEEP_VOLUMES", "0,1000,10000").split(",")]
INDEX_STATES = [False, True]
K = int(os.environ.get("SWEEP_K", "15"))
WARMUP = int(os.environ.get("SWEEP_WARMUP", "2"))

per_e, per_g = len(tmpl["entities"]), len(tmpl["grants"])
print(f"{'clones':>8} {'entities':>12} {'grant_records':>15}")
for n in VOLUMES:
    print(f"{n:>8,} {base_counts['entities'] + n * per_e:>12,} "
          f"{base_counts['grant_records'] + n * per_g:>15,}")
print(f"\\ncells: {len(VOLUMES)} volumes x {len(INDEX_STATES)} index states = "
      f"{len(VOLUMES) * len(INDEX_STATES)} restarts")
print(f"per cell: {len(api_sweep.read_operations(FIXTURE))} APIs x ({K}+{WARMUP}) warm "
      f"+ 1 cold, plus the control")
"""),
    md("""
### A decision left open on purpose

02b escalated to a **parallel** Seq Scan at ~233k rows and its timings became
unusable: probes with identical plan cost and identical buffer counts measured a
3–10x spread. At 600k rows this sweep will certainly escalate.

`grant_scale.set_parallelism(conn, 0)` pins it — but only for *that* psycopg2
session, which is not the connection Polaris uses. Suppressing it for the API
path means `ALTER ROLE polaris SET max_parallel_workers_per_gather = 0`, a
**server-side change**, and this repo's standing rule is explicit sign-off
before touching PostgreSQL config (an earlier multi-setting change took the HA
cluster down and forced a full OrbStack reset).

So the default below is **leave the cluster alone and record the escalation**.
An unindexed grantee lookup that goes parallel is burning worker slots on the
authorization path of every authenticated request — that is a worse operational
story than "it is slow", and it belongs upstream on its own. Set
`SWEEP_PIN_PARALLELISM=1` only after deciding deliberately; the notebook resets
it in teardown either way.
"""),
    code("""
PIN_PARALLELISM = os.environ.get("SWEEP_PIN_PARALLELISM", "0") == "1"

def role_parallelism(value):
    \"\"\"Server-side pin for the *Polaris* connections. Takes effect on new
    sessions, so it must be paired with the restart the grid already does.\"\"\"
    with conn.cursor() as cur:
        if value is None:
            cur.execute(f"ALTER ROLE {PG['user']} RESET max_parallel_workers_per_gather")
        else:
            cur.execute(
                f"ALTER ROLE {PG['user']} SET max_parallel_workers_per_gather = {int(value)}"
            )
    return value

if PIN_PARALLELISM:
    role_parallelism(0)
    print("max_parallel_workers_per_gather pinned to 0 for role", PG["user"])
else:
    print("parallelism left at cluster default; escalation will be RECORDED, not suppressed")

def scan_shape():
    \"\"\"Did the grantee lookup go parallel? Recorded per cell as evidence that
    survives even when the clock does not.\"\"\"
    probe = grant_scale.resolve_probes(conn, SCHEMA, REALM, targets=("max",))[0]
    m = grant_scale.measure(conn, SCHEMA, REALM, probe)
    # `resolve_probes` excludes filler by `grantee_id >= 0`, which was enough
    # when the only synthetic rows were negative. Clones are POSITIVE, so it
    # cannot tell one from a real grantee and will happily label a cloned
    # owner_principal "the fattest identity in the realm". The plan shape is
    # unaffected — but the label would be a fabricated fact about the fixture,
    # which is the specific failure this directory keeps catching.
    clone_grantee = probe["grantee_id"] in set(
        entity_replay.clone_ids(conn, SCHEMA, REALM)
    )
    return {"label": m["label"], "plan": m["path"], "cost": m["total_cost"],
            "buffers": m["shared_hit"], "rows_filtered": m["rows_filtered"],
            "parallel": m["parallel"], "probe_is_clone": clone_grantee,
            "probe_rows": probe["rows"]}
"""),
    md("""
## 3. The four callbacks

`api_sweep.run_sweep` owns the ordering and the measurement; everything
cluster-specific is injected here. Volume is the outer loop because it rewrites
hundreds of thousands of rows; the index toggle is inner because `CONCURRENTLY`
needs no restart. A restart happens per `(volume, index)` pair — that is what
makes the cold sample cold.

`connect()` re-authenticates every time. The old token belongs to a process that
no longer exists.
"""),
    code("""
def apply_volume(n):
    \"\"\"Set clone volume to exactly n. Always from a known-empty state.\"\"\"
    removed = entity_replay.delete_clones(conn, SCHEMA, REALM)
    entity_replay.assert_prefix_is_free(conn, SCHEMA, REALM)
    inserted = {"entities": 0, "grants": 0}
    if n:
        band, width = entity_replay.find_clone_band(conn, SCHEMA, REALM, n)
        inserted = entity_replay.insert_clones(
            conn, SCHEMA, REALM, tmpl, n, band,
            on_progress=lambda line: print(line, flush=True),
        )
    with conn.cursor() as cur:
        cur.execute(f"ANALYZE {SCHEMA}.entities")
        cur.execute(f"ANALYZE {SCHEMA}.grant_records")
    rows = run_manifest.table_counts(conn, SCHEMA, TABLES)
    # Polaris reads through Pgpool, which load-balances SELECTs to standbys.
    # Until this insert has replicated, a request served by a standby scans a
    # SMALLER table -- the cell would be labelled 10,000 clones and measured at
    # something else. The seed run made this concrete: 4 of 4 create_namespace
    # calls returned 500 for writes that had already committed.
    repl = api_sweep.wait_for_replicas(conn)
    print(f"  replicas caught up: {repl['standbys']} standby(s) in "
          f"{repl['seconds']:.1f}s")
    print(f"  volume {n:,}: removed {removed['entities']:,}e, "
          f"inserted {inserted['entities']:,}e/{inserted['grants']:,}g -> {rows}")
    return {"clones": n, "removed": removed, "inserted": inserted, "rows": rows}


def apply_index(present):
    return grant_scale.set_index(conn, SCHEMA, present)


def polaris_is_serving():
    r = requests.get(f"{MGMT_URL}/q/health/ready", timeout=5)
    return r.status_code == 200


def restart():
    out = api_sweep.restart_polaris(namespace=K8S_NS, deployment=K8S_DEPLOY)
    out["serving"] = api_sweep.wait_until_serving(polaris_is_serving)
    print(f"  restarted in {out['seconds']:.1f}s, serving after "
          f"{out['serving']['seconds']:.1f}s more")
    return out


def connect_polaris():
    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    assert r.status_code < 300, f"auth failed [{r.status_code}]: {r.text[:200]}"
    pc.token = r.json()["access_token"]
    return pc


def ops_for(pc):
    return api_sweep.read_operations(FIXTURE), DECOY, (ROOT_CLIENT, ROOT_SECRET)
"""),
    md("""
## 4. Run it

Long. `len(VOLUMES) x 2` restarts, each followed by ~13 APIs x (K+WARMUP) warm
calls plus one cold call and the control. The insert at 10,000 clones writes
~70,000 `entities` and ~550,000 `grant_records` rows.
"""),
    code("""
RUN_ID = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
t_start = time.time()

cells = api_sweep.run_sweep(
    volumes=VOLUMES,
    index_states=INDEX_STATES,
    apply_volume=apply_volume,
    apply_index=apply_index,
    restart=restart,
    connect=connect_polaris,
    ops_for=ops_for,
    on_progress=print,
    k=K,
    warmup=WARMUP,
)

for c in cells:
    c["scan"] = scan_shape()          # plan-shape evidence, per cell
print(f"\\n{len(cells)} cells in {(time.time() - t_start) / 60:.1f} min")
"""),
    md("""
## 5. Read the control first

If `POST /oauth/tokens` moved as much as the treatment, this grid measured
ambient noise. That is not a disappointing result to be buried under the
headline table — it is the result, and it goes first.
"""),
    code("""
drift = api_sweep.control_drift(cells)
print(f"control: median {drift['median_ms']:.2f} ms, "
      f"spread {drift['spread_ms']:.2f} ms ({drift['min_ms']:.2f}..{drift['max_ms']:.2f})")

biggest = max(
    (abs(r["delta_ms"]) for a in {a for c in cells for a in c["warm"]}
     for r in api_sweep.index_effect(cells, a)),
    default=0.0,
)
print(f"largest index effect: {biggest:.2f} ms")
if biggest <= drift["spread_ms"]:
    print("\\n*** The largest effect is within the control's own spread. ***")
    print("Report this as inconclusive. Do not publish the tables below.")
else:
    print(f"\\neffect is {biggest / max(drift['spread_ms'], 1e-9):.1f}x the control spread")
"""),
    code("""
report = api_sweep.render_report(cells, {
    "run_id": RUN_ID, "realm": REALM, "schema": SCHEMA, "polaris": POLARIS_URL,
})
print(report)
"""),
    code("""
# escalation, recorded rather than suppressed
print(f"{'clones':>8} {'index':>6}  parallel  plan")
for c in cells:
    s = c.get("scan") or {}
    print(f"{c['clones']:>8,} {str(c['index']):>6}  {str(s.get('parallel')):>8}  {s.get('plan')}")
"""),
    md("""
## 6. Persist, then restore

The run JSON carries the cells, the row counts each was measured at, and the
plan shape — so a later reader can tell whether a number came from a parallel
scan without re-running anything.

Teardown removes every clone and resets the role's parallelism. It deliberately
leaves the index **present**: that is the remediated state the rest of the
directory assumes, and 02's section-5 guard refuses to run when it finds the
index already there, which is the correct failure rather than a silent 1x.
"""),
    code("""
runs = pathlib.Path("runs"); runs.mkdir(exist_ok=True)
reports = pathlib.Path("reports"); reports.mkdir(exist_ok=True)

(runs / f"{RUN_ID}-02c.json").write_text(json.dumps({
    "run_id": RUN_ID, "volumes": VOLUMES, "index_states": INDEX_STATES,
    "k": K, "warmup": WARMUP, "fixture": FIXTURE, "decoy": DECOY,
    "pinned_parallelism": PIN_PARALLELISM, "cells": cells,
}, indent=2, default=str))
(reports / "doc-api-latency-sweep-latest.md").write_text(report)
print("wrote", runs / f"{RUN_ID}-02c.json")
"""),
    code("""
removed = entity_replay.delete_clones(conn, SCHEMA, REALM)
print(f"removed {removed['entities']:,} clone entities, {removed['grants']:,} grants")

if PIN_PARALLELISM:
    role_parallelism(None)
    print("parallelism reset for role", PG["user"])

final = grant_scale.set_index(conn, SCHEMA, True)
print("index left present:", final["state"])
print("rows:", run_manifest.table_counts(conn, SCHEMA, TABLES))
conn.close()
"""),
]

NB = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

if __name__ == "__main__":
    for cell in NB["cells"]:
        cell["source"] = [line + "\n" for line in cell["source"].split("\n")[:-1]] + [
            cell["source"].split("\n")[-1]
        ]
    OUT.write_text(json.dumps(NB, indent=1))
    n_code = sum(1 for c in NB["cells"] if c["cell_type"] == "code")
    print(f"wrote {OUT.name}: {len(NB['cells'])} cells ({n_code} code)")
