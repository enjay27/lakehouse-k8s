#!/usr/bin/env python3
"""What GET/HEAD operations exist here, and which does the harness drive?

    python3 probe_api_surface.py                         # captured inventory (default)
    python3 probe_api_surface.py --profile catalog-scoped
    python3 probe_api_surface.py --server                 # also try the live OpenAPI
    python3 probe_api_surface.py --json --out ../runs/coverage.json

WHY THIS EXISTS
---------------
On 2026-08-31 the privilege scan was found to drive 13 of 29 GET/HEAD
operations, and nothing in the harness said so. Nobody made a mistake: the op
list was its own authority, so there was no place for a disagreement to appear.
This runner is that place.

THREE SOURCES, AND THEY ARE NOT EQUAL
-------------------------------------
1. **CAPTURED (default, strongest).** `reports/doc-api-sql-matrix-*.md` records
   every API a previous live run issued against THIS cluster, with method, path
   and response status. Each entry is proof that the operation exists here and
   answers. The 2026-08-20 matrix holds **19 distinct GET/HEAD operations**.

   Its limit is the important part: a call log is a LOWER BOUND. It proves
   existence for what was called and says nothing whatever about what was not,
   because an operation nobody invoked leaves no trace to find. Judging the
   harness complete against it alone would be circular -- measuring a harness
   against a record of what a harness once did.

2. **SPEC (candidates).** The 1.3.0 OpenAPI files name 29 GET/HEAD operations.
   That is a statement about a VERSION, not about this DEPLOYMENT: generic
   tables and policies are feature-flagged in 1.3 and may be off here. Useful
   only as a list of things to go and check -- never as a coverage verdict.

3. **SERVER (--server, and it did not work here).** A live OpenAPI document
   would settle both at once. Polaris 8181/8182 serves none: every `/q/openapi`
   and `/openapi` candidate came back empty on 2026-08-31. Two plausible
   reasons -- the `quarkus-smallrye-openapi` extension is not in the server
   build, or it is present but not exposed outside dev mode -- and neither is
   worth chasing, because source 1 is better evidence than a document would be.
   A document describes what the build INTENDS to serve; the matrix records
   what it actually served.

SO THE VERDICT IS THREE-WAY, DELIBERATELY
-----------------------------------------
    confirmed gap  -- the cluster SERVED it, the harness does not drive it.
                      A fact. This is what the number should be zero.
    unverified     -- the harness drives it, nothing has ever called it here.
                      Open question, resolved by running the probe.
    candidate      -- the spec names it, nothing observed it, nothing drives it.

Collapsing these into one percentage would let a transcribed endpoint this
build does not serve count as a failure, and let a genuinely missing one hide
behind the same asterisk.
"""

import argparse
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_sweep  # noqa: E402
import privilege_scan as ps  # noqa: E402
import query_profile as qp  # noqa: E402

POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
MGMT_URL = os.environ.get("POLARIS_MGMT_URL", "http://192.168.139.2:8182")
REPORTS_DIR = HERE / "reports"

#: Where a Quarkus service would serve its document, if it served one.
CANDIDATES = (
    "/q/openapi?format=json",
    "/q/openapi.json",
    "/openapi?format=json",
    "/openapi.json",
    "/api/catalog/v1/openapi.json",
)


def newest_matrix(reports_dir=None):
    """The most recent api-sql-matrix report that actually parses.

    By CONTENT, not by name: `doc-api-sql-matrix-latest.md` is a copy whose
    mtime says nothing about which run produced it, and a report that yields no
    operations is not a newer inventory -- it is a broken one.
    """
    d = pathlib.Path(reports_dir or REPORTS_DIR)
    if not d.is_dir():
        return None, []
    #: A timestamped report names the run that produced it; `-latest.md` is a
    #: copy whose own mtime says nothing about which run it came from. Prefer
    #: the named one so the coverage report can cite a run id rather than a
    #: filename that will mean something different next week.
    named = [p for p in d.glob("doc-api-sql-matrix-*.md") if "latest" not in p.name]
    copies = [p for p in d.glob("doc-api-sql-matrix-*.md") if "latest" in p.name]
    candidates = sorted(named, key=lambda p: p.stat().st_mtime, reverse=True) + sorted(
        copies, key=lambda p: p.stat().st_mtime, reverse=True
    )
    for p in candidates:
        ops = qp.parse_api_matrix(p.read_text(encoding="utf-8"))
        if ops:
            return p, ops
    return None, []


def fetch_server_documents(urls, timeout=10):
    """Any OpenAPI document these bases hand over. Returns ([(url, doc)], tried)."""
    import requests

    found, tried = [], []
    for base in urls:
        for path in CANDIDATES:
            url = base.rstrip("/") + path
            tried.append(url)
            try:
                r = requests.get(url, timeout=timeout)
            except Exception:  # noqa: BLE001
                continue
            if r.status_code != 200:
                continue
            try:
                doc = r.json()
            except ValueError:
                continue
            if isinstance(doc, dict) and doc.get("paths"):
                found.append((url, doc))
                break
    return found, tried


def read_operations_from(doc):
    """(method, full_path) for every GET/HEAD a document declares."""
    bases = []
    for s in doc.get("servers") or []:
        u = s.get("url", "") if isinstance(s, dict) else ""
        if "://" in u:
            rest = u.split("://", 1)[1]
            u = "/" + rest.split("/", 1)[1] if "/" in rest else ""
        if u:
            bases.append(u.rstrip("/"))
    ops = []
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in ("get", "head"):
            if method in item:
                for base in bases or [""]:
                    ops.append((method.upper(), f"{base}{path}"))
    return ops


def spec_candidates():
    """The 1.3.0 GET/HEAD surface, transcribed. Candidates only -- see module doc."""
    mgmt, cat, pol = "/api/management/v1", "/api/catalog/v1", "/api/catalog/polaris/v1"
    return [
        ("GET", f"{mgmt}/catalogs"),
        ("GET", f"{mgmt}/catalogs/{{catalogName}}"),
        ("GET", f"{mgmt}/principals"),
        ("GET", f"{mgmt}/principals/{{principalName}}"),
        ("GET", f"{mgmt}/principals/{{principalName}}/principal-roles"),
        ("GET", f"{mgmt}/principal-roles"),
        ("GET", f"{mgmt}/principal-roles/{{principalRoleName}}"),
        ("GET", f"{mgmt}/principal-roles/{{principalRoleName}}/principals"),
        ("GET", f"{mgmt}/principal-roles/{{prName}}/catalog-roles/{{catalogName}}"),
        ("GET", f"{mgmt}/catalogs/{{catalogName}}/catalog-roles"),
        ("GET", f"{mgmt}/catalogs/{{catalogName}}/catalog-roles/{{crName}}"),
        (
            "GET",
            f"{mgmt}/catalogs/{{catalogName}}/catalog-roles/{{crName}}/principal-roles",
        ),
        ("GET", f"{mgmt}/catalogs/{{catalogName}}/catalog-roles/{{crName}}/grants"),
        ("GET", f"{cat}/config"),
        ("GET", f"{cat}/{{prefix}}/namespaces"),
        ("GET", f"{cat}/{{prefix}}/namespaces/{{namespace}}"),
        ("HEAD", f"{cat}/{{prefix}}/namespaces/{{namespace}}"),
        ("GET", f"{cat}/{{prefix}}/namespaces/{{namespace}}/tables"),
        ("GET", f"{cat}/{{prefix}}/namespaces/{{namespace}}/tables/{{table}}"),
        ("HEAD", f"{cat}/{{prefix}}/namespaces/{{namespace}}/tables/{{table}}"),
        (
            "GET",
            f"{cat}/{{prefix}}/namespaces/{{namespace}}/tables/{{table}}/credentials",
        ),
        ("GET", f"{cat}/{{prefix}}/namespaces/{{namespace}}/views"),
        ("GET", f"{cat}/{{prefix}}/namespaces/{{namespace}}/views/{{view}}"),
        ("HEAD", f"{cat}/{{prefix}}/namespaces/{{namespace}}/views/{{view}}"),
        ("GET", f"{pol}/{{prefix}}/namespaces/{{namespace}}/generic-tables"),
        ("GET", f"{pol}/{{prefix}}/namespaces/{{namespace}}/generic-tables/{{gt}}"),
        ("GET", f"{pol}/{{prefix}}/namespaces/{{namespace}}/policies"),
        ("GET", f"{pol}/{{prefix}}/namespaces/{{namespace}}/policies/{{policyName}}"),
        ("GET", f"{pol}/{{prefix}}/applicable-policies"),
    ]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--profile", default="catalog-scoped-full", choices=sorted(ps.PROFILES)
    )
    ap.add_argument("--matrix", default=None, help="a specific api-sql-matrix report")
    ap.add_argument(
        "--server",
        action="store_true",
        help="also try the live OpenAPI document (none served as of 2026-08-31)",
    )
    ap.add_argument(
        "--no-spec",
        action="store_true",
        help="omit the transcribed 1.3.0 candidates entirely",
    )
    ap.add_argument("--url", default=POLARIS_URL)
    ap.add_argument("--mgmt-url", default=MGMT_URL)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    profile = ps.PROFILES[args.profile]
    templates = qp.operation_templates(
        read_operations=getattr(api_sweep, profile.operations)
    )

    if args.matrix:
        path = pathlib.Path(args.matrix)
        observed = qp.parse_api_matrix(path.read_text(encoding="utf-8"))
    else:
        path, observed = newest_matrix()

    if not observed:
        print("no captured API inventory found.")
        print(f"  looked for doc-api-sql-matrix-*.md under {REPORTS_DIR}")
        print()
        print("That report is this runner's ground truth — it is the only source")
        print("that records what THIS cluster actually served. Re-run notebook 01")
        print("to produce one, or pass --matrix <path>.")
        return 2

    sources = [f"captured: {path.name}"]
    if args.server:
        docs, tried = fetch_server_documents([args.url, args.mgmt_url])
        if docs:
            for url, doc in docs:
                observed = observed + [
                    (m, p, "openapi", 0) for m, p in read_operations_from(doc)
                ]
                sources.append(f"server: {url}")
        else:
            sources.append(f"server: none served ({len(tried)} URLs tried)")

    candidates = () if args.no_spec else spec_candidates()
    cov = qp.coverage_from_evidence(templates, observed, candidates)

    payload = {
        "profile": profile.name,
        "sources": sources,
        "matrix": str(path) if path else None,
        "observed_operations": cov["observed_total"],
        "driven_operations": cov["driven_total"],
        "coverage": cov,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"profile : {profile.name} — {profile.description}")
        for s in sources:
            print(f"source  : {s}")
        print()
        print(qp.render_evidence_coverage(cov, source=path.name if path else ""))
        print()
        if cov["clean"]:
            print(
                "No confirmed gap. Operations listed as unverified are the ones\n"
                "to settle with `scan_privileges.py --probe`."
            )
        else:
            print(
                f"{len(cov['observed_not_driven'])} operations this cluster has "
                "served are NOT driven.\nAny report from this profile describes "
                "a subset of the surface, and must say so."
            )

    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(payload, indent=2), "utf-8")
        print(f"\nwritten to {args.out}")

    return 0 if cov["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
