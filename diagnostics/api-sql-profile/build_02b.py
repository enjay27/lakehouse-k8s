"""Generate 02b_grant_scale_sweep.ipynb. Run once; the notebook is the artifact."""

import json
import pathlib

C = []


def md(text):
    C.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})


def code(text):
    C.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": text.rstrip("\n").splitlines(True),
        }
    )


md("""# 02b — Grant-record scaling sweep

How the `grant_records` grantee index behaves **as a realm grows**.

`02_index_audit.ipynb` measured the remedy at one point. That number is true and
reproducible, and it sits at one corner of a two-dimensional space the report
never separated:

| variable | what it drives |
|---|---|
| total rows in `grant_records` | Seq Scan cost — it reads every row |
| rows returned for one grantee | Index Only Scan cost |

An upstream reviewer will ask what happens in a realm shaped like theirs. A
single ratio cannot answer that, and a reviewer who seeds their own realm and
gets a different number has grounds to dismiss the finding entirely. **A trend
answers it.**

**Stated in advance, so a null result is still informative:** Seq Scan time
grows linearly with total rows and is flat across grantees within a size; Index
Only Scan time is flat across total rows and grows only with rows returned. If
Seq Scan does *not* grow linearly, the fixture is wrong — most likely a missing
`ANALYZE` — and nothing here should be published until that is explained.

**Prerequisites**
- statement logging **OFF** (`./capture.sh pgoff`) — with it on, the same plan
  measured a 4.6x spread and moved a headline on noise alone;
- the fixture upgraded to ~50 grants per role (`seed_polaris.py --upgrade-grants`);
- a kernel restarted since any `src/` edit.

Everything mechanical lives in `src/grant_scale.py`; this notebook orchestrates
and renders.""")

md("## 0 — Configuration and guards")

code("""import os, sys, time, json, pathlib, datetime

REPO = pathlib.Path.cwd()
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

POLARIS_URL = "http://192.168.139.2:8181"
REALM       = "POLARIS"
ROOT_CLIENT = "root"
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")

# Pgpool is a POOLER, not a node: it load-balances SELECTs across replicas, and
# EXPLAIN must run on the PRIMARY or the plan is measured against different
# statistics. Every statement below carries /*NO LOAD BALANCE*/ (applied inside
# api_trace and grant_scale) and section 0 asserts we are not on a standby.
PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = "polaris_schema"

# --- what state to hand to 03 ------------------------------------------------
# The manifest RECORDS the index; it does not require one. `run_manifest.
# diff_live` only asserts on the index when `left_in_place` is true, so either
# choice produces a valid handover -- this flag decides which, in one place,
# and is written straight into the manifest so the two cannot disagree.
#
#   True  -> rebuild and leave it. 03's LATENCY pass then measures a cluster
#            where the grantee lookup is 0.015 ms instead of a 1.2-3.2 ms Seq
#            Scan that swings with node contention. That term sits in the
#            7-statement auth prelude of EVERY request 03 times, so leaving it
#            unindexed puts a large, noisy confound on top of the cache signal
#            03 is actually trying to see.
#
#   False -> leave it off. 03 then measures Polaris AS SHIPPED -- upstream has
#            no such index (schema-v3.sql gives grant_records a PK and nothing
#            else), which is the same reasoning that says 01 should capture the
#            access map with the index dropped.
#
# The tension is real and unresolved: 03's SHAPE pass (batched_share) does not
# care either way, so this only affects the latency pass. Measuring that pass in
# BOTH states costs little at ~55k rows and is the honest answer if 03's
# latencies are going upstream.
LEAVE_INDEX_FOR_03 = True

assert any(h in POLARIS_URL for h in ("localhost", "127.0.0.1", "192.168.")), \\
    "refusing to run: POLARIS_URL is not a local address"
assert any(h in PG["host"] for h in ("127.0.0.1", "localhost", "192.168.")), \\
    "refusing to run: PG host is not on the local network"

OUT = REPO / "diagnostics" / "api-sql-profile"
print("repo    :", REPO)
print("postgres:", f"{PG['host']}:{PG['port']}/{PG['dbname']}")""")

code("""import psycopg2
import api_trace, grant_scale, run_manifest
from grant_scale import INDEX_NAME

# autocommit is REQUIRED: CREATE/DROP INDEX CONCURRENTLY cannot run inside a
# transaction, and this notebook does both once per grid cell.
conn = psycopg2.connect(**PG)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute(api_trace.NO_LOAD_BALANCE +
                "SELECT version(), pg_is_in_recovery(), inet_server_addr()")
    ver, standby, node = cur.fetchone()
print(ver.split(",")[0])
print("node    :", node, " standby:", standby)
assert not standby, (
    "the pooler routed this session to a STANDBY. EXPLAIN must run on the "
    "primary. If /*NO LOAD BALANCE*/ is not honoured, connect to the primary "
    "pod directly: PG_HOST=<primary-pod-ip>"
)

# --- parallelism ------------------------------------------------------------
# The first live run escalated to a parallel Seq Scan at ~233k rows, and the
# timings became unusable: probes whose plan cost and buffer counts were
# IDENTICAL measured a 3-10x spread, because worker startup dominates a scan
# this small and worker availability varies run to run. (This cluster also has
# a documented /dev/shm constraint that parallel DSM allocation is sensitive
# to -- see diagnostics/doc-shm-exhaustion-test-plan.md.)
#
# 0 pins the controlled trend to a serial scan. The escalation is still worth
# knowing about, so section 3 records what the planner WOULD choose before
# turning it off -- an unindexed grantee lookup that goes parallel is burning
# worker slots on every authenticated request, which is a worse story than
# latency and belongs in the report either way.
MAX_PARALLEL_WORKERS = 0
grant_scale.set_parallelism(conn, MAX_PARALLEL_WORKERS)
print("max_parallel_workers_per_gather:", MAX_PARALLEL_WORKERS)

EXPLAIN_N = api_trace.EXPLAIN_N
print("explain repeats:", EXPLAIN_N, f"(first discarded, so n={EXPLAIN_N - 1})")""")

md("""## 1 — Preconditions

Four things are checked before a single row is written. The third is the one
that matters most: it is what makes the cleanup `DELETE` safe.""")

code('''# --- the fixture is the production-shaped one -------------------------------
with conn.cursor() as cur:
    cur.execute(api_trace.NO_LOAD_BALANCE + f"""
        WITH g AS (SELECT grantee_id, count(*) n FROM {SCHEMA}.grant_records
                   WHERE realm_id = %s AND grantee_id >= 0 GROUP BY 1)
        SELECT count(*), percentile_disc(0.5)  WITHIN GROUP (ORDER BY n),
               percentile_disc(0.95) WITHIN GROUP (ORDER BY n), max(n) FROM g""",
        (REALM,))
    n_grantees, p50, p95, gmax = cur.fetchone()

base_rows = grant_scale.total_rows(conn, SCHEMA)
print(f"grant_records : {base_rows:,} rows")
print(f"grantees      : {n_grantees:,}   p50={p50}  p95={p95}  max={gmax}")

if p95 and p95 < 50:
    print()
    print("  NOTE: p95 is below 50, so this fixture has NOT been upgraded to")
    print("  production grant volume (seed_polaris.py --upgrade-grants). The")
    print("  sweep still measures a real surface; it just starts from a")
    print("  thinner realm than the one the report claims. Say so if you")
    print("  publish from this run.")

# --- the index is in a known state ------------------------------------------
print("\\nindex at start:", run_manifest.index_state(conn, SCHEMA, INDEX_NAME))
print("  (either state is fine — every grid cell sets it explicitly)")''')

code('''# --- THE SENTINEL RANGE -----------------------------------------------------
# PLAN-grant-scale-sweep.md B1 reserved ids ">= 1_000_000_000" for filler and
# removed them with `DELETE ... WHERE grantee_id >= 1000000000`.
#
# That predicate matches EVERY REAL GRANT. Polaris ids are snowflake-style and
# land around 10^18 -- 7985247348701050877, 2490852191059560064 -- so the
# documented cleanup would have deleted the entire fixture and left the
# synthetic rows behind. Filler therefore uses NEGATIVE ids, and this asserts
# the disjointness against live data rather than trusting the paragraph.
safety = grant_scale.assert_filler_range_is_safe(conn, SCHEMA)
print("filler range is disjoint from real data")
print("  smallest real (grantee, securable, grantee_cat, securable_cat):",
      safety["real_minimums"])
print("  filler rows already present:", safety["existing_filler_rows"])

# --- no foreign key to entities ---------------------------------------------
# Polaris emits no JOINs anywhere, which suggests none exists -- but that is an
# inference from query shape. A hidden FK makes synthetic grantee ids
# impossible and drops the sweep's ceiling to what REST can create.
with conn.cursor() as cur:
    cur.execute("""SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
                   WHERE conrelid = %s::regclass AND contype = 'f'""",
                (f"{SCHEMA}.grant_records",))
    fks = cur.fetchall()
assert not fks, (
    f"grant_records carries a foreign key: {fks}. Filler rows with synthetic "
    "grantee ids are not viable; fall back to pure-REST volume (~110k ceiling) "
    "and say so in the report."
)
print("\\nno foreign key on grant_records — filler rows are viable")''')

md("""## 2 — Probes

Four points on the rows-returned axis. Real grantees are preferred; a target the
fixture does not occupy is created explicitly and marked **SYNTHETIC** wherever
it appears, because a number quoted out of a table is quoted without its
preamble.""")

code("""# The rows-returned axis. 10,000 is not arbitrary: `service_admin` gains one
# grant per catalog (measured — 1,006 at 1,000 catalogs, 1,007 the moment one
# more appeared), so in a 10,000-catalog realm the FATTEST grantee holds
# ~10,006 rows. The speedup is inversely related to grantee size, so that is
# where the index looks least good and where an upstream reviewer with a large
# realm lands first. The current fixture pins "max" at 1,006 and cannot see it.
PROBE_TARGETS = (1, 50, 500, 10_000, "max")

probes = grant_scale.resolve_probes(conn, SCHEMA, REALM, targets=PROBE_TARGETS)
for p in probes:
    if p.get("synthetic"):
        grant_scale.ensure_probe_grantee(conn, SCHEMA, REALM, p["wanted"],
                                         grantee_id=p["grantee_id"])
        print(f"  created synthetic grantee {p['grantee_id']} "
              f"with {p['wanted']} rows")

print()
print(f"{'probe':<26} {'grantee':>22} {'rows':>7}  source")
for p in probes:
    print(f"{p['label']:<26} {p['grantee_id']:>22} {p['rows']:>7}  "
          f"{'SYNTHETIC' if p['synthetic'] else 'real'}")""")

md("""## 3 — The grid

Three table sizes x four probes, **both index states at every cell**. Each point
therefore carries its own before/after and cannot be contaminated by a stale
index or by drift between two long passes.

Sizes ascend and filler is only ever added: removing part of it would leave the
remaining synthetic grantees uneven and change what the probes mean.

This is the long cell. `CREATE INDEX CONCURRENTLY` at 500,000 rows is expected
to slow down — that build time is part of the cost being proposed upstream, so
it is recorded rather than hidden.""")

code("""# Sizes as SIMULATED USERS, not raw row counts. `production_shape`
# reproduces the measured histogram of a real realm -- 2n+2 grantees holding
# 1 row, n holding 2 (catalog_admin), n holding the granted privileges -- so
# the top cell is a 10,000-user realm's grant_records, not uniform ballast.
#
# In SQL, in seconds. The same realm over REST is ~610,000 calls and ~8.5
# hours, and a Seq Scan cannot tell the two apart: same plan, same buffers,
# same timing. What REST would buy is provenance, not measurement -- which is
# why every table below marks these rows synthetic.
SIMULATED_USERS = [1_000, 3_000, 10_000]
GRANTS_PER_ROLE = 50


def _shape(u):
    return grant_scale.production_shape(u, GRANTS_PER_ROLE)


SIZES = [base_rows + grant_scale.shape_rows(_shape(u)) for u in SIMULATED_USERS]
for u, sz in zip(SIMULATED_USERS, SIZES):
    print(f"  {u:>6,} simulated users -> {sz:,} rows")
print()

_step = [0]


def shaped_fill(conn_, schema_, realm_, rows_needed):
    # Add the DELTA shape for this step. The bands are linear in user count,
    # so inserting production_shape(delta) is exactly right -- no band diffing.
    i = _step[0]
    delta = SIMULATED_USERS[i] - (SIMULATED_USERS[i - 1] if i else 0)
    _step[0] += 1
    print(f"  +{delta:,} simulated users")
    return grant_scale.insert_shaped_filler(
        conn_, schema_, realm_, _shape(delta),
        on_progress=lambda line: print(line, flush=True),
    )["total"]


# What the planner WOULD do, recorded once at the top size before the sweep
# pins parallelism off. This is evidence, not a measurement -- plan shape only.
grant_scale.set_parallelism(conn, 4)
_would = grant_scale.measure(conn, SCHEMA, REALM, probes[0], k=2)
grant_scale.set_parallelism(conn, MAX_PARALLEL_WORKERS)
print(f"planner with parallelism available: {_would['path']} "
      f"(parallel={_would['parallel']})")
print(f"pinned off for the sweep: every cell below is a serial scan\\n")

t0 = time.time()
cells = grant_scale.run_grid(
    conn, SCHEMA, REALM,
    sizes=SIZES,
    probes=probes,
    k=EXPLAIN_N,
    fill=shaped_fill,
    on_progress=lambda line: print(line, flush=True),
)
print(f"\\nswept {len(cells)} cells in {time.time() - t0:.0f}s")""")

md("## 4 — Results")

code("""rows = grant_scale.speedups(cells)

print(f"{'table rows':>11}  {'probe':<26} {'returned':>8}  "
      f"{'no index':>18} {'ms':>9}  {'with index':>18} {'ms':>9}  {'x':>7}")
for r in rows:
    mark = " *" if r["synthetic"] else "  "
    print(f"{r['exact_rows']:>11,}  {r['label']:<26} {str(r['rows_returned']):>8}{mark}"
          f"{r['before_node']:>18} {r['before_ms']:>9.3f}  "
          f"{r['after_node']:>18} {r['after_ms']:>9.3f}  {r['speedup']:>6.1f}x")
if any(r["synthetic"] for r in rows):
    print("\\n* = synthetic grantee — do not quote upstream without that caveat.")

print()
print("Plan shapes, which are deterministic where the timings are not:")
seen = set()
for r in rows:
    key = (r["before_node"], r["after_node"])
    if key not in seen:
        seen.add(key)
        print(f"   {r['before_node']}  ->  {r['after_node']}")""")

md("""## 5 — The trend

Two plots, because twelve numbers in a table are not an argument and a slope
is. The first should rise with table size and be flat across probes; the second
should be flat across table size and rise only with rows returned.""")

code("""import matplotlib
matplotlib.use("Agg")          # headless: write files, do not open a window
import matplotlib.pyplot as plt

REPORTS_DIR = pathlib.Path(os.environ.get("REPORTS_DIR", OUT / "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RUN_STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

sizes = sorted({r["exact_rows"] for r in rows})
labels = list(dict.fromkeys(r["label"] for r in rows))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

for lbl in labels:
    xs = [r["exact_rows"] for r in rows if r["label"] == lbl]
    ys = [r["before_ms"] for r in rows if r["label"] == lbl]
    ax1.plot(xs, ys, marker="o", label=lbl)
ax1.set_title("Without the index: Seq Scan vs table size")
ax1.set_xlabel("rows in grant_records")
ax1.set_ylabel("EXPLAIN ANALYZE median (ms)")
ax1.legend(fontsize=8)
ax1.grid(alpha=0.3)

for s in sizes:
    pts = sorted(((r["rows_returned"] or 0), r["after_ms"])
                 for r in rows if r["exact_rows"] == s)
    ax2.plot([p[0] for p in pts], [p[1] for p in pts], marker="o",
             label=f"{s:,} rows")
ax2.set_title("With the index: Index Only Scan vs rows returned")
ax2.set_xlabel("rows returned for the probed grantee")
ax2.set_ylabel("EXPLAIN ANALYZE median (ms)")
ax2.set_xscale("log")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3)

fig.tight_layout()
PLOT = REPORTS_DIR / f"doc-grant-scale-sweep-{RUN_STAMP}.png"
fig.savefig(PLOT, dpi=130)
print("wrote", PLOT)
plt.show()""")

md("## 6 — Write the report")

code("""meta = {
    "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "polaris_url": POLARIS_URL,
    "realm": REALM,
    "explain_n": EXPLAIN_N - 1,
}
doc = grant_scale.render_report(cells, meta)

path = REPORTS_DIR / f"doc-grant-scale-sweep-{RUN_STAMP}.md"
path.write_text(doc, encoding="utf-8")
(REPORTS_DIR / "doc-grant-scale-sweep-latest.md").write_text(doc, encoding="utf-8")
print("wrote", path)
print(f"       {len(doc):,} chars")""")

md("""## 7 — Restore, then hand over

The cluster must not be left in a state nobody chose. Filler comes out, the
statistics are refreshed, and the index is rebuilt and **left in place** —
`03_read_cache_profile.ipynb` requires it.

This notebook is the manifest producer for 03. `02_index_audit.ipynb` is not
re-run in between: its manifest would be invalidated by this sweep anyway.""")

code("""removed = grant_scale.delete_filler(conn, SCHEMA)
grant_scale.analyze(conn, SCHEMA)
restored = grant_scale.total_rows(conn, SCHEMA)
print(f"removed {removed:,} filler rows -> {restored:,} remain")
assert restored == base_rows, (
    f"expected to return to {base_rows:,} rows, got {restored:,}. Something "
    "other than filler changed during the sweep; do not hand this state to 03."
)

built = grant_scale.set_index(conn, SCHEMA, LEAVE_INDEX_FOR_03)
if LEAVE_INDEX_FOR_03:
    print("index rebuilt in %.1fs:" % built["seconds"], built["state"])
    print("  03 will measure latency on a PATCHED cluster; say so in its report.")
else:
    print("index left OFF:", built["state"])
    print("  03 will measure Polaris as shipped. The grantee lookup is a Seq")
    print("  Scan in every auth prelude it times — expect a larger, noisier")
    print("  baseline, and do not read that noise as cache behaviour.")""")

code("""_counts = run_manifest.table_counts(
    conn, SCHEMA, ["entities", "grant_records", "principal_authentication_data"])
_idx = run_manifest.index_state(conn, SCHEMA, INDEX_NAME)

run_id = run_manifest.new_run_id()
manifest = {
    "notebook": "02b_grant_scale_sweep.ipynb",
    "generated_at": meta["generated_at"],
    "polaris_url": POLARIS_URL,
    "realm": REALM,
    "postgres": {"host": PG["host"], "port": PG["port"], "dbname": PG["dbname"]},
    "schema": SCHEMA,
    "statement_logging": "off (see capture.sh pgoff)",
    # The keys 03 re-checks against the live cluster. `left_in_place` is what
    # makes require_live_match assert on the index at all.
    # left_in_place is the SWITCH diff_live gates its index check on. Recording
    # the flag rather than a literal True is what stops the manifest claiming a
    # state the notebook did not leave -- the failure 02's teardown comment
    # warns about in prose, made structural.
    "index": {"name": INDEX_NAME, "ddl": grant_scale.index_ddl(SCHEMA),
              "left_in_place": LEAVE_INDEX_FOR_03, "state_at_write": _idx},
    "fixture": {"exact_counts": _counts, "restored_to": restored,
                "filler_removed": removed},
    "grantee_distribution": {"grantees": n_grantees, "p50": p50,
                             "p95": p95, "max": gmax},
    "explain_n": EXPLAIN_N - 1,
    "sweep": {"sizes": SIZES, "probes": probes, "cells": cells,
              "speedups": rows},
    "report": str(path.name),
}
written = run_manifest.write_run(OUT, run_id, manifest)
print("wrote", written)

# Prove the handover works before 03 discovers it does not.
# This proves the CONTRACT, not drift: the manifest was written from this same
# cluster seconds ago, so of course it matches. What it catches is a malformed
# handover -- a missing key, the wrong schema name, `left_in_place` disagreeing
# with what section 7 actually did -- which would otherwise surface as a
# confusing failure at the start of 03. The drift check is the same call made
# LATER, from 03, when days may have passed and someone may have dropped the
# index to re-run something.
run_manifest.require_live_match(conn, manifest, schema=SCHEMA, tolerance=0)
print("manifest is a well-formed handover for 03 (contract check, not drift)")""")

code("""conn.close()
print("connection closed")""")

nb = {
    "cells": C,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
out = pathlib.Path("diagnostics/api-sql-profile/02b_grant_scale_sweep.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print(f"wrote {out} — {len(C)} cells")
