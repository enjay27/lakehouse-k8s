"""Per-run manifests for the API/SQL profiling notebooks.

Notebook 02 measures a cluster and leaves an index behind; notebook 03 measures
cache behaviour and needs to know it is looking at the same cluster, in the same
state, that 02 characterised. A manifest is how 02 hands that over.

The division of responsibility matters and is easy to get wrong:

  * the manifest carries **values** -- what was measured, when, against what
    fixture. It is provenance, and it is immutable once written.
  * the live cluster carries **truth**. A manifest that says "index present" is
    a statement about the past. Someone can drop the index between the two
    notebooks, and a consumer that trusts the manifest alone would then measure
    an unindexed cluster and label the result "indexed".

So `load_run` gives you the values and `diff_live` re-checks the claims against
the database. Never one without the other.
"""

import datetime
import json
import os
import pathlib

RUNS_DIRNAME = "runs"
RUN_ID_FORMAT = "%Y%m%d-%H%M%S"


def new_run_id(when=None):
    """Timestamp run id, lexicographically sortable so 'latest' is just max()."""
    return (when or datetime.datetime.now()).strftime(RUN_ID_FORMAT)


def runs_dir(base):
    """The runs/ directory under `base`, created if absent."""
    d = pathlib.Path(base) / RUNS_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_run(base, run_id, payload):
    """Write one run manifest as JSON. Refuses to overwrite an existing run.

    Overwriting is refused rather than allowed because a run id is a claim about
    a specific measurement: silently replacing one would make an already-written
    report unreproducible, and the failure would surface later as an
    unexplainable mismatch rather than here as a name collision.
    """
    path = runs_dir(base) / f"{run_id}.json"
    if path.exists():
        raise FileExistsError(
            f"{path} already exists. Run ids identify a specific measurement; "
            "pick a new one rather than overwriting a recorded run."
        )
    body = dict(payload)
    body.setdefault("run_id", run_id)
    body.setdefault("written_at", datetime.datetime.now().isoformat(timespec="seconds"))
    path.write_text(json.dumps(body, indent=2, default=str), encoding="utf-8")
    return path


def list_runs(base):
    """All run ids under `base`, oldest first."""
    d = pathlib.Path(base) / RUNS_DIRNAME
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def load_run(base, run_id=None):
    """Load one manifest. `run_id=None` (the default) loads the newest.

    Returns:
        (run_id, dict)

    Defaulting to the newest is the convenient behaviour, but it is also the one
    that can silently change under you between sessions, so the resolved id is
    returned alongside the payload -- callers are expected to print it.
    """
    ids = list_runs(base)
    if not ids:
        raise FileNotFoundError(
            f"no run manifests under {pathlib.Path(base) / RUNS_DIRNAME}. "
            "Run 02_index_audit.ipynb first -- it writes one per run."
        )
    if run_id is None:
        run_id = ids[-1]
    elif run_id not in ids:
        raise FileNotFoundError(f"run '{run_id}' not found. Available: {ids}")
    path = pathlib.Path(base) / RUNS_DIRNAME / f"{run_id}.json"
    return run_id, json.loads(path.read_text(encoding="utf-8"))


def index_state(conn, schema, index_name):
    """Live (present, valid, ready) for one index.

    `valid` matters as much as `present`: an interrupted CREATE/DROP INDEX
    CONCURRENTLY leaves a row in pg_index with indisvalid = false. The index
    shows up in a naive existence check but the planner will not use it, so a
    consumer would measure unindexed behaviour while believing otherwise.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT i.indisvalid, i.indisready
               FROM pg_class c
               JOIN pg_index i     ON i.indexrelid = c.oid
               JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = %s AND c.relname = %s""",
            (schema, index_name),
        )
        row = cur.fetchone()
    if row is None:
        return {"present": False, "valid": False, "ready": False}
    return {"present": True, "valid": bool(row[0]), "ready": bool(row[1])}


def table_counts(conn, schema, tables):
    """Exact `count(*)` per table. Exact, not pg_stat's estimate.

    `n_live_tup` is an estimate maintained by the stats collector and drifts
    from reality after bulk changes until the next ANALYZE, so it is fine for a
    report and useless as an equality check between two notebook runs.
    """
    out = {}
    for t in tables:
        with conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {schema}.{t}")
            out[t] = cur.fetchone()[0]
    return out


def diff_live(conn, manifest, schema=None, tolerance=0):
    """Compare the live cluster against what a manifest recorded.

    Args:
        conn: open psycopg2 connection.
        manifest: payload from `load_run`.
        schema: override the manifest's schema name.
        tolerance: allowed absolute row-count drift per table. 0 (default) means
            exact. Raise it only if you knowingly left fixtures behind.

    Returns:
        list[str]: human-readable mismatches, empty when the cluster matches.
        The caller decides what to do -- these notebooks assert on it.
    """
    schema = schema or manifest.get("schema") or "polaris_schema"
    problems = []

    idx = (manifest.get("index") or {}).get("name")
    if idx and (manifest.get("index") or {}).get("left_in_place"):
        state = index_state(conn, schema, idx)
        if not state["present"]:
            problems.append(
                f"index {schema}.{idx} is ABSENT; run {manifest.get('run_id')} "
                "recorded it as left in place. Re-run 02 to rebuild it."
            )
        elif not (state["valid"] and state["ready"]):
            problems.append(
                f"index {schema}.{idx} exists but is INVALID "
                f"(valid={state['valid']} ready={state['ready']}) -- an "
                "interrupted CREATE/DROP CONCURRENTLY. The planner will ignore "
                "it. Drop and rebuild it."
            )

    recorded = (manifest.get("fixture") or {}).get("exact_counts") or {}
    if recorded:
        live = table_counts(conn, schema, sorted(recorded))
        for t, want in sorted(recorded.items()):
            got = live.get(t)
            if got is None:
                continue
            if abs(got - want) > tolerance:
                problems.append(
                    f"{schema}.{t} holds {got} rows; run "
                    f"{manifest.get('run_id')} measured {want} "
                    f"(drift {got - want:+d}, tolerance {tolerance}). "
                    "The fixture is not the one that run characterised."
                )
    return problems


def require_live_match(conn, manifest, schema=None, tolerance=0):
    """`diff_live`, but raise AssertionError listing every mismatch.

    Fails rather than warning on purpose. A wrong-but-plausible measurement is
    the expensive failure mode in this suite -- it costs a re-run plus whatever
    was concluded from it in the meantime -- and refusing to start costs a
    minute.
    """
    problems = diff_live(conn, manifest, schema=schema, tolerance=tolerance)
    if problems:
        raise AssertionError(
            "live cluster does not match run "
            f"{manifest.get('run_id')}:\n  - " + "\n  - ".join(problems)
        )
    return True
