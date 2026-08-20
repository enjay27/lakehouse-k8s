#!/usr/bin/env python3
"""Compare a FAILING user's catalog against a WORKING one, to find what differs.

WHY
---
Seeding stalls for ~29 users on:

    create_catalog_role 403: Principal 'root' with activated PrincipalRoles
    '[service_admin]' ... is not authorized for op CREATE_CATALOG_ROLE

Root is obviously authorized -- it did this 921 times in the same run. And the
403 persists across retries spanning ~8s, so it is not replication lag.

HYPOTHESIS (unverified -- that is what this script is for)
    These are exactly the catalogs whose CREATE returned 500 and which the
    seeder then accepted because `get_catalog` found them. Creating a catalog
    writes the entity AND bootstraps its `catalog_admin` catalog-role plus the
    grants that make the creator an admin of it. If the entity write committed
    but the grant write did not, the catalog EXISTS while being unadministrable
    -- and "does the entity exist" was too weak a success check.

PREDICTION IF TRUE
    A failing catalog has no `catalog_admin` in list_catalog_roles, or has it
    with no grants, while a working catalog has both.

PREDICTION IF FALSE
    The two look identical -- and the cause is elsewhere (token scope drift,
    per-catalog policy, something in the 403 body we have not read in full).

Usage:
    python3 diagnose_catalog.py 56 63 97          # failing indices
    python3 diagnose_catalog.py 56 --good 1       # pick the known-good baseline
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

from polaris_rest import PolarisREST                       # noqa: E402
from polaris_seed import SeedSpec                          # noqa: E402

POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
REALM       = os.environ.get("POLARIS_REALM", "POLARIS")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")


def probe(pc, spec, i, label):
    n = spec.names(i)
    cat = n["catalog"]
    out = {"index": i, "label": label, "catalog": cat}

    r = pc.get_catalog(cat)
    out["get_catalog"] = r.status_code
    if r.status_code < 300:
        body = r.json()
        out["entityVersion"] = body.get("entityVersion")
        props = body.get("properties", {}) or {}
        out["has_base_location"] = "default-base-location" in props
        out["storage"] = bool(body.get("storageConfigInfo"))

    r = pc.list_catalog_roles(cat)
    out["list_catalog_roles"] = r.status_code
    roles = []
    if r.status_code < 300:
        roles = [x.get("name") for x in r.json().get("roles", [])]
    out["roles"] = roles
    out["has_catalog_admin"] = "catalog_admin" in roles

    # The decisive one: does catalog_admin actually hold grants?
    if out["has_catalog_admin"]:
        g = pc.list_grants(cat, "catalog_admin")
        out["admin_grants_status"] = g.status_code
        if g.status_code < 300:
            gr = g.json().get("grants", [])
            out["admin_grant_count"] = len(gr)
            out["admin_privileges"] = sorted(
                {x.get("privilege") for x in gr if x.get("privilege")}
            )[:6]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indices", nargs="+", type=int, help="failing user indices")
    ap.add_argument("--good", type=int, default=1,
                    help="index of a known-good user for comparison")
    ap.add_argument("--prefix", default="user")
    args = ap.parse_args()

    spec = SeedSpec(n_users=1000, prefix=args.prefix, create_tables=False)
    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    if r.status_code >= 300:
        sys.exit(f"auth failed [{r.status_code}]: {r.text[:200]}")
    pc.token = r.json()["access_token"]

    rows = [probe(pc, spec, args.good, "GOOD")]
    rows += [probe(pc, spec, i, "FAILING") for i in args.indices]

    for row in rows:
        print(f"\n--- {row['label']}  {row['catalog']}")
        for k, v in row.items():
            if k in ("label", "catalog", "index"):
                continue
            print(f"    {k:22s} {v}")

    good, bad = rows[0], rows[1:]
    print("\n" + "=" * 62)
    diffs = set()
    for b in bad:
        for k in good:
            if k in ("label", "catalog", "index"):
                continue
            if good.get(k) != b.get(k):
                diffs.add(k)
    if not diffs:
        print("NO DIFFERENCE between good and failing catalogs.")
        print("The hypothesis is REFUTED -- the cause is not a half-created")
        print("catalog. Next: capture the FULL 403 body and the Polaris log")
        print("for one failing create_catalog_role request id.")
    else:
        print("fields that differ between GOOD and FAILING:", sorted(diffs))
        if "has_catalog_admin" in diffs or "admin_grant_count" in diffs:
            print("\nHYPOTHESIS CONFIRMED: the catalog exists but its admin role")
            print("or its grants are missing -- the CREATE half-committed.")
            print("Remedy: delete these catalogs and let the seeder recreate")
            print("them, since there is no API to bootstrap the missing role.")
            print("\n  python3 diagnose_catalog.py --help   # then, to repair:")
            for b in bad:
                print(f"    pc.delete_catalog({b['catalog']!r}, purge=True)")

    print("\nraw:", json.dumps(rows, indent=1)[:1500])


if __name__ == "__main__":
    main()
