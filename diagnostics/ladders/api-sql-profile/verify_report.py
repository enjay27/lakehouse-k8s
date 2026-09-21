"""Re-derive every figure in the combined report from the JSON, and fail loudly.

A report is a claim about files that outlive it. Numbers get transcribed by
hand, a run gets re-taken, a table gets edited around one figure that nobody
re-checks -- and the document keeps asserting it. This reads the qprofile and
relabel JSONs, recomputes each headline figure, and requires the document to
contain the string form of what it recomputed.

It checks arithmetic and presence, not prose. A figure that is right and
missing from the document fails here; a sentence that misreads a figure it
quotes correctly does not. Run it after any edit to the report.
"""

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "runs"
DOC = HERE / "doc-grant-index-contrast-20260831.md"

TIERS = [
    ("user", "absent", "110305"),
    ("user", "present", "111114"),
    ("authz", "absent", "105310"),
    ("authz", "present", "111200"),
    ("admin", "absent", "105456"),
    ("admin", "present", "111255"),
]
GRANTEE = "grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?"
SECURABLE = "securable_id = ? AND securable_catalog_id = ? AND realm_id = ?"


def q(rid):
    return json.loads((RUNS / f"qprofile-20260831-{rid}.json").read_text())


def r(rid):
    return json.loads((RUNS / f"relabel-20260831-{rid}.json").read_text())


def run(rid):
    return json.loads((RUNS / f"privscan-20260831-{rid}.json").read_text())


def grantee_explain(d):
    for e in d["explains"]:
        if e.get("table") == "grant_records" and GRANTEE in e["sql"]:
            return e
    raise AssertionError("no grantee lookup in this qprofile")


def main():
    doc = DOC.read_text(encoding="utf-8")
    checks, failures = 0, []

    def want(value, why):
        nonlocal checks
        checks += 1
        if str(value) not in doc:
            failures.append(f"{why}: report does not contain {value!r}")

    def must(cond, why):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(why)

    # ---- volume, identical across all six -----------------------------
    rows = {q(rid)["grant_rows"] for _t, _s, rid in TIERS}
    must(len(rows) == 1, f"the six captures disagree on grant_rows: {rows}")
    want(f"{rows.pop():,}", "measured volume")

    # ---- the headline contrast ---------------------------------------
    for tier, state, rid in TIERS:
        d = q(rid)
        e = grantee_explain(d)
        expect_scan = "Seq Scan" if state == "absent" else "Index Scan"
        must(
            e["scan"] == expect_scan,
            f"{tier}/{state}: grantee lookup took {e['scan']}, expected {expect_scan}",
        )
        must(
            (d["index_state"] == "index PRESENT") == (state == "present"),
            f"{tier}/{state}: qprofile records index_state={d['index_state']!r}",
        )
        # the plan and the recorded pg_indexes state must agree
        has_idx = any(i["name"] == "idx_grant_records_grantee" for i in d["indexes"])
        must(
            has_idx == (state == "present"),
            f"{tier}/{state}: live pg_indexes disagrees with the capture's state",
        )
        want(e["shared_hit_blocks"], f"{tier}/{state} buffers")
        if state == "absent":
            want(f"{e['rows_removed_by_filter']:,}", f"{tier}/{state} rows removed")
            must(
                e["shared_hit_blocks"] == 572,
                f"{tier}/{state}: expected the full 572-page table scan",
            )
            must(
                e["rows_removed_by_filter"] + e["actual_rows"] == d["grant_rows"],
                f"{tier}/{state}: removed + returned != table rows -- the scan is "
                "not reading the whole table, so 'sequential scan' is the wrong word",
            )
        else:
            must(
                e.get("rows_removed_by_filter") in (None, 0),
                f"{tier}/{state}: an index scan should discard nothing",
            )
            must(
                e["index"] == "idx_grant_records_grantee",
                f"{tier}/{state}: index scan used {e['index']!r}",
            )

    # ---- the control: securable lookup, unchanged by the toggle -------
    sec = {}
    for tier, state, rid in TIERS:
        for e in q(rid)["explains"]:
            if e.get("table") == "grant_records" and SECURABLE in e["sql"]:
                sec[(tier, state)] = (e["scan"], e["shared_hit_blocks"])
    must(sec, "the securable-side control statement is missing entirely")
    must(
        {v[0] for v in sec.values()} == {"Index Only Scan"},
        f"the control statement changed plan across states: {sec}",
    )
    must(
        max(v[1] for v in sec.values()) <= 5,
        f"the control statement's buffers moved: {sec}",
    )

    # ---- aggregate page traffic --------------------------------------
    ua, up = grantee_explain(q("110305")), grantee_explain(q("111114"))
    want(f"{ua['occurrences']:,}", "user index-absent grantee lookups")
    want(f"{up['occurrences']:,}", "user index-present grantee lookups")
    total_absent = ua["occurrences"] * ua["shared_hit_blocks"]
    must(
        abs(total_absent / 1e6 - 10.3) < 0.05,
        f"aggregate absent buffer hits is {total_absent:,}, report says 10.3 million",
    )
    gib = total_absent * 8192 / 1024**3
    must(
        abs(gib - 79) < 1,
        f"aggregate absent page traffic is {gib:.1f} GiB, report says 79",
    )

    # ---- the denial path ---------------------------------------------
    for state, rid in [("absent", "110305"), ("present", "111114")]:
        cls = r(rid)["outcome_classes"]
        ref = cls["refused (403)"]
        must(
            ref["requests"] == 6000,
            f"{state}: {ref['requests']} refusals, expected 6000",
        )
        must(
            ref["min"] == ref["median"] == ref["max"] == 7,
            f"{state}: the 403 prelude is not a flat 7 statements: "
            f"{ref['min']}/{ref['median']}/{ref['max']}",
        )
        must(
            abs(ref["table_per_request"] - 1.0) < 1e-9,
            f"{state}: refusals average {ref['table_per_request']} grantee lookups, "
            "expected exactly 1.000",
        )
        must(
            "unclassified (not an op)" not in cls,
            f"{state}: an unclassified class survived the label fix",
        )
    denial = 6000 * 572
    must(
        abs(denial / 1e6 - 3.4) < 0.05,
        f"denial-path buffer hits {denial:,} disagrees with the report's 3.4 million",
    )
    must(
        abs(denial * 8192 / 1024**3 - 26) < 1,
        "denial-path page traffic disagrees with the report's ~26 GiB",
    )

    # ---- per-API coverage --------------------------------------------
    for state, rids in [
        ("absent", ["110305", "105310", "105456"]),
        ("present", ["111114", "111200", "111255"]),
    ]:
        scans, ops = {}, {}
        for rid in rids:
            for e in q(rid)["explains"]:
                if e.get("plan"):
                    scans.setdefault(e["sql"], set()).add(e["scan"])
            for sh in r(rid)["shapes"]:
                for label in sh["labels"]:
                    ops.setdefault(label, set()).add(sh["sql"])
        reads = {o for o in ops if o != "POST /oauth/tokens"}
        must(len(reads) == 29, f"{state}: {len(reads)} read ops seen, expected 29")
        seq = {
            o for o in reads if any("Seq Scan" in scans.get(s, set()) for s in ops[o])
        }
        if state == "absent":
            must(
                len(seq) == 29,
                f"absent: {len(seq)} of 29 read ops issue a Seq Scan, expected all 29",
            )
            must(
                not any(
                    "Seq Scan" in scans.get(s, set()) for s in ops["POST /oauth/tokens"]
                ),
                "absent: the token endpoint should not touch grant_records",
            )
        else:
            must(not seq, f"present: sequential scans remain on {sorted(seq)}")

    # ---- reconciliation, all six -------------------------------------
    for tier, state, rid in TIERS:
        rec = r(rid)["reconciliation"]
        must(
            rec["unexplained_total"] == 0,
            f"{tier}/{state}: unexplained {rec['unexplained_total']}",
        )
        must(
            rec["probe_total"] == 2,
            f"{tier}/{state}: probe allowance {rec['probe_total']}, expected 2",
        )
        must(rec["clean"], f"{tier}/{state}: reconciliation not clean")
        must(
            not r(rid)["unclassified_paths"],
            f"{tier}/{state}: unclassified paths remain",
        )
        must(r(rid)["orphan_statements"] == 0, f"{tier}/{state}: orphan statements")
        total = rec["expected_total"]
        want(f"{total:,}" if total >= 1000 else total, f"{tier}/{state} expected")

    # ---- statement-count asymmetry, stated as NOT explained ----------
    a, b = r("110305")["statements"], r("111114")["statements"]
    must(a != b, "the two user passes issued the same statement count after all")
    want(f"{a:,}", "user index-absent statement total")
    want(f"{b:,}", "user index-present statement total")

    # ---- elapsed times, labelled inflated ----------------------------
    for tier, state, rid in TIERS:
        want(run(rid)["elapsed_s"], f"{tier}/{state} elapsed")
    must(
        re.search(r"not latency|not request latency|must not be quoted", doc),
        "the report does not disclaim the timings",
    )

    print(f"{checks} checks")
    for f in failures:
        print(f"  FAIL  {f}")
    print("OK — every figure re-derived" if not failures else f"{len(failures)} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
