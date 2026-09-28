"""
nb_support.py
=============
Shared utilities for all Polaris error case notebooks.
"""

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import requests
import urllib3
from opensearchpy import OpenSearch

urllib3.disable_warnings()

try:
    import yaml
except ImportError:
    yaml = None

# ── Environment / Config ──────────────────────────────────────
# Config comes from config/<env>.yaml (+ common.yaml). Secrets may also be
# supplied via environment variables, which OVERRIDE file values.
# Select the environment with init_env("local"|"dev"|"prod") in your notebook, or
# set the POLARIS_ENV environment variable. Default is "local" (safe — your own
# device). "dev"/"prod" are the SHARED company environments with totally different
# endpoints/secrets; "prod" runs availability tests only.

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")


def _load_config(env):
    if yaml is None:
        raise RuntimeError("pyyaml not installed: pip install pyyaml")
    cfg = {}
    common = os.path.join(_CONFIG_DIR, "common.yaml")
    if os.path.exists(common):
        with open(common) as f:
            cfg.update(yaml.safe_load(f) or {})
    envfile = os.path.join(_CONFIG_DIR, f"{env}.yaml")
    if not os.path.exists(envfile):
        raise FileNotFoundError(
            f"Config not found: {envfile}\n"
            f"  → copy config/{env}.example.yaml to config/{env}.yaml and fill it in."
        )
    with open(envfile) as f:
        cfg.update(yaml.safe_load(f) or {})
    return cfg


# Test resource names (env-independent)
TEST_CATALOG = "test-error-catalog"
TEST_NAMESPACE = "test-ns"
TEST_TABLE = "test-table"
TEST_PRINCIPAL = "test-principal"
TEST_PR = "test-principal-role"
TEST_CR = "test-catalog-role"
WATCHDOG_PRINCIPAL = "watchdog-principal"
WATCHDOG_PR = "watchdog-principal-role"
WATCHDOG_CR = "watchdog-catalog-role"
WATCHDOG_CATALOG = "watchdog-catalog"
WATCHDOG_NAMESPACE = "watchdog-ns"
WATCHDOG_TABLE = "watchdog-table"

# Globals populated by init_env() — declared here so they always exist.
ENV = None
CFG = {}
POLARIS_URL = REALM = ROOT_CLIENT = ROOT_SECRET = POLARIS_USER_SECRET = None
#: Quarkus management interface -- `/q/health`, `/q/health/ready`, `/q/metrics`.
#: A DIFFERENT port from the Polaris APIs. Both the Catalog API and the
#: Management API are served on 8181; 8182 is Quarkus and is NOT the Polaris
#: Management API. Asking 8181 for /q/health returns 404.
POLARIS_MGMT_URL = None
OPENSEARCH_HOST = None
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = None
OPENSEARCH_PASS = None
LOG_INDEX = None
POLARIS_CONTAINER = None
MINIO_ENDPOINT = MINIO_ENDPOINT_INTERNAL = MINIO_ACCESS_KEY = MINIO_SECRET_KEY = (
    BUCKET
) = None
PG_HOST = None
PG_PORT = 5432
PG_DB = "polaris"
PG_USER = "polaris"
PG_PASSWORD = None
PG_URL = None
PG_CONFIG = {}
BASE_MGMT = BASE_CAT = None
#: Quarkus management port. 8182 on this cluster -- NOT 8282, which is what
#: the upstream docs default to (.memory/environments-platform.md).
QUARKUS_MGMT_PORT = 8182
PURGE_DELETES_FILES = None
POLARIS_VERSION = None
mc = None  # MinioREST client (built by init_env)


def init_env(env=None):
    """Initialize or switch the active environment. Call once at the top of a
    notebook: `init_env("dev")` or `init_env("prod")`. Re-runnable (no kernel
    restart needed). Returns the active config dict.

    Secrets resolve in this order: environment variable > config file value.
      POLARIS_ROOT_SECRET, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, OPENSEARCH_PASS
    """
    global ENV, CFG, POLARIS_URL, REALM, ROOT_CLIENT, ROOT_SECRET
    global POLARIS_USER_SECRET
    global OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USER, OPENSEARCH_PASS
    global LOG_INDEX, POLARIS_CONTAINER, BASE_MGMT, BASE_CAT, POLARIS_MGMT_URL
    global MINIO_ENDPOINT, MINIO_ENDPOINT_INTERNAL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, BUCKET
    global PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD, PG_URL, PG_CONFIG
    global PURGE_DELETES_FILES, POLARIS_VERSION, mc

    ENV = env or os.environ.get("POLARIS_ENV", "local")
    CFG = _load_config(ENV)

    POLARIS_URL = CFG["polaris_url"]
    REALM = CFG.get("realm", "POLARIS")
    ROOT_CLIENT = CFG.get("root_client", "root")
    ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", CFG.get("root_secret"))
    #: The ONE secret every seeded principal (user/authz/admin) authenticates
    #: with. It cannot be read back from the ledger: `polaris_seed` discards the
    #: clientId/clientSecret `create_principal` returns, so this is set by hand
    #: in `principal_authentication_data` and recorded here. Same env-overrides-
    #: file shape as every other secret, so a shared env can supply it without
    #: a file. NOT the same value as any single-purpose principal's own secret —
    #: conflating them authenticates the wrong identity and reports 401 as if
    #: the fixture were broken.
    POLARIS_USER_SECRET = os.environ.get(
        "POLARIS_USER_SECRET", CFG.get("polaris_user_secret")
    )

    OPENSEARCH_HOST = CFG.get("opensearch_host", "localhost")
    OPENSEARCH_PORT = CFG.get("opensearch_port", 9200)
    OPENSEARCH_USER = CFG.get("opensearch_user", "admin")
    OPENSEARCH_PASS = os.environ.get("OPENSEARCH_PASS", CFG.get("opensearch_pass"))
    LOG_INDEX = CFG.get("log_index", "k8s-logs-*")
    POLARIS_CONTAINER = CFG.get("polaris_container_name", "benchmarks-polaris")

    MINIO_ENDPOINT = CFG["minio_endpoint"]
    MINIO_ENDPOINT_INTERNAL = CFG.get("minio_endpoint_internal", MINIO_ENDPOINT)
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", CFG.get("minio_access_key"))
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", CFG.get("minio_secret_key"))
    BUCKET = CFG.get("bucket", "data-catalog-bucket")

    # PostgreSQL metastore (used by diagnostics notebooks). Password may be
    # overridden by the POSTGRES_PASSWORD env var. PG_URL / PG_CONFIG are ready-made
    # for sqlalchemy.create_engine(PG_URL) and psycopg2.connect(**PG_CONFIG).
    PG_HOST = CFG.get("postgres_host")
    PG_PORT = CFG.get("postgres_port", 5432)
    PG_DB = CFG.get("postgres_db", "polaris")
    PG_USER = CFG.get("postgres_user", "polaris")
    PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", CFG.get("postgres_password"))
    PG_URL = (
        f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        if PG_HOST
        else None
    )
    PG_CONFIG = {
        "host": PG_HOST,
        "port": PG_PORT,
        "dbname": PG_DB,
        "user": PG_USER,
        "password": PG_PASSWORD,
    }

    PURGE_DELETES_FILES = CFG.get("purge_deletes_files", False)
    POLARIS_VERSION = CFG.get("polaris_version", "unknown")

    BASE_MGMT = f"{POLARIS_URL}/api/management/v1"
    BASE_CAT = f"{POLARIS_URL}/api/catalog/v1"
    # Quarkus management interface. Config key wins; otherwise derive it by
    # swapping the Polaris API port for the Quarkus one, so an existing
    # <env>.yaml that predates this key keeps working.
    POLARIS_MGMT_URL = os.environ.get("POLARIS_MGMT_URL") or CFG.get("polaris_mgmt_url") or re.sub(
        r":(\d+)(/|$)", lambda m: f":{QUARKUS_MGMT_PORT}{m.group(2)}", POLARIS_URL
    )

    # Build the MinIO REST client (pure requests + SigV4; no s3fs/boto3)
    try:
        from minio_rest import MinioREST

        if MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
            mc = MinioREST(MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, BUCKET)
        else:
            mc = None
    except ImportError:
        mc = None

    banner = {"prod": "🔴 PROD", "dev": "🟡 DEV (shared)"}.get(ENV, "🟢 LOCAL")
    print(f"{banner}   POLARIS_ENV={ENV}   (Polaris {POLARIS_VERSION})")
    print(f"   Polaris: {POLARIS_URL}")
    print(f"   MinIO:   {MINIO_ENDPOINT}  bucket={BUCKET}")
    print(f"   OpenSearch: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}  index={LOG_INDEX}")
    if mc is None:
        print("   ⚠️  MinIO client not built (missing creds or minio_rest.py)")
    print(f"   purge_deletes_files={PURGE_DELETES_FILES}")
    return CFG


def require_not_prod(action="this destructive action"):
    """Guard: raise on prod unless POLARIS_ALLOW_PROD=1 is set. Use in
    destructive helpers (cleanup, purge) to prevent accidental prod damage."""
    if ENV == "prod" and os.environ.get("POLARIS_ALLOW_PROD") != "1":
        raise RuntimeError(
            f"Refusing {action} on PROD. Set POLARIS_ALLOW_PROD=1 to override."
        )


# Auto-initialize from POLARIS_ENV (default "local", NOT dev -- this comment said
# dev until 2026-09-21 and line 122 has always said local) so a bare `import *`
# works. This is why a notebook that never calls init_env() still has populated
# BASE_CAT / BASE_MGMT / POLARIS_URL: 26 notebooks rely on exactly that.
# A notebook can re-run init_env("prod") afterwards to switch.
try:
    init_env()
except Exception as _e:
    print(f"[nb_support] init_env deferred: {_e}")


# ── Token ─────────────────────────────────────────────────────
def get_token(
    client_id=None, client_secret=None, realm=None, scope="PRINCIPAL_ROLE:ALL"
):
    # Read config globals at CALL time (init_env sets them); None = use active env
    client_id = client_id if client_id is not None else ROOT_CLIENT
    client_secret = client_secret if client_secret is not None else ROOT_SECRET
    realm = realm if realm is not None else REALM
    # NOTE on scope: root (service_admin) can request PRINCIPAL_ROLE:ALL. A NON-ROOT
    # principal generally CANNOT — requesting ALL yields a token with no effective
    # role, which downstream policy (OPA) / Polaris then denies (403). Non-root
    # callers must request their SPECIFIC assigned principal-role, e.g.
    # scope=f"PRINCIPAL_ROLE:{their_role}".
    r = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": realm},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
    )
    return r


def root_token():
    r = get_token()
    assert r.status_code == 200, f"Root token failed: {r.text}"
    return r.json()["access_token"]


def h(token=None, realm=None):
    tok = token or root_token()
    realm = realm if realm is not None else REALM
    return {
        "Authorization": f"Bearer {tok}",
        "Polaris-Realm": realm,
        "Content-Type": "application/json",
    }


# ── Watchdog bootstrap ──────────────────────────────────────────
def ensure_watchdog_setup():
    """
    Idempotent one-time setup for the daily watchdog test.
    Uses the root token + default POLARIS realm (no separate realm needed).

    Creates (only if missing):
      principal       watchdog-principal
      principal role  watchdog-principal-role
      catalog         watchdog-catalog
      catalog role    watchdog-catalog-role  (granted CATALOG_MANAGE_CONTENT)

    Returns: (client_id, client_secret) for the watchdog principal.
    If the principal already existed, client_secret is None
    (Polaris does not return secrets again — reuse the stored one).
    """
    tok = root_token()
    print("🔧 Checking watchdog setup (realm: POLARIS)...")

    # 1. Principal
    # principals = (
    #     requests.get(f"{BASE_MGMT}/principals", headers=h(tok))
    #     .json()
    #     .get("principals", [])
    # )
    # existing = next((p for p in principals if p["name"] == WATCHDOG_PRINCIPAL), None)
    #
    # client_secret = None
    # if existing:
    #     print(f"  ✅ principal exists: {WATCHDOG_PRINCIPAL}")
    #     client_id = existing.get("clientId", WATCHDOG_PRINCIPAL)
    # else:
    #     r = create_principal(name=WATCHDOG_PRINCIPAL, token=tok)
    #     assert r.status_code in (
    #         200,
    #         201,
    #     ), f"create_principal failed: {r.status_code} {r.text}"
    #     body = r.json()
    #     client_id = body.get("principal", {}).get("clientId", WATCHDOG_PRINCIPAL)
    #     client_secret = body.get("credentials", {}).get("clientSecret")
    #     print(f"  ✅ principal created: {WATCHDOG_PRINCIPAL}")
    #     print(f"     clientId:     {client_id}")
    #     print(f"     clientSecret: {client_secret}")
    #     print("     ⚠️  Save this secret — Polaris will not show it again.")

    # 2. Principal role
    # pr_list = (
    #     requests.get(f"{BASE_MGMT}/principal-roles", headers=h(tok))
    #     .json()
    #     .get("roles", [])
    # )
    # if any(pr["name"] == WATCHDOG_PR for pr in pr_list):
    #     print(f"  ✅ principal role exists: {WATCHDOG_PR}")
    # else:
    #     r = create_principal_role(name=WATCHDOG_PR, token=tok)
    #     assert r.status_code in (
    #         200,
    #         201,
    #     ), f"create_principal_role failed: {r.status_code} {r.text}"
    #     print(f"  ✅ principal role created: {WATCHDOG_PR}")

    # 3. Assign principal role to principal (idempotent — PUT is safe to repeat)
    r = assign_principal_role_to_principal(
        principal="user11_principal", pr=WATCHDOG_PR, token=tok
    )
    print(f"  ✅ principal role assigned ({r.status_code})")

    # 4. Catalog
    # catalogs = (
    #     requests.get(f"{BASE_MGMT}/catalogs", headers=h(tok)).json().get("catalogs", [])
    # )
    # if any(c["name"] == WATCHDOG_CATALOG for c in catalogs):
    #     print(f"  ✅ catalog exists: {WATCHDOG_CATALOG}")
    # else:
    #     r = create_catalog(name=WATCHDOG_CATALOG, token=tok)
    #     assert r.status_code in (
    #         200,
    #         201,
    #     ), f"create_catalog failed: {r.status_code} {r.text}"
    #     print(f"  ✅ catalog created: {WATCHDOG_CATALOG}")
    #
    # # 5. Catalog role
    # cr_list = (
    #     requests.get(
    #         f"{BASE_MGMT}/catalogs/{WATCHDOG_CATALOG}/catalog-roles", headers=h(tok)
    #     )
    #     .json()
    #     .get("roles", [])
    # )
    # if any(cr["name"] == WATCHDOG_CR for cr in cr_list):
    #     print(f"  ✅ catalog role exists: {WATCHDOG_CR}")
    # else:
    #     r = create_catalog_role(catalog=WATCHDOG_CATALOG, name=WATCHDOG_CR, token=tok)
    #     assert r.status_code in (
    #         200,
    #         201,
    #     ), f"create_catalog_role failed: {r.status_code} {r.text}"
    #     print(f"  ✅ catalog role created: {WATCHDOG_CR}")
    #
    # # 6. Grant + assign (idempotent — safe to repeat)
    # grant_privilege(
    #     catalog=WATCHDOG_CATALOG,
    #     cr=WATCHDOG_CR,
    #     privilege="CATALOG_MANAGE_CONTENT",
    #     token=tok,
    # )
    # assign_catalog_role_to_principal_role(
    #     catalog=WATCHDOG_CATALOG, pr=WATCHDOG_PR, cr=WATCHDOG_CR, token=tok
    # )
    # print(f"  ✅ grants verified")
    #
    # print("🔧 Watchdog setup complete (realm: POLARIS)\n")
    # return client_id, client_secret


def reset_watchdog_principal():
    """
    Force-recreate watchdog principal using root token.
    Use when: 401 unauthorized_client (stale/lost secret).

    Deletes existing principal if present, creates fresh one,
    returns (client_id, client_secret).
    """
    tok = root_token()
    print("🔄 Resetting watchdog principal...")

    # Delete if exists (ignore 404)
    r = requests.delete(f"{BASE_MGMT}/principals/{WATCHDOG_PRINCIPAL}", headers=h(tok))
    print(f"  DELETE existing principal: {r.status_code}")

    # Recreate
    r = create_principal(name=WATCHDOG_PRINCIPAL, token=tok)
    assert r.status_code in (
        200,
        201,
    ), f"create_principal failed: {r.status_code} {r.text}"
    body = r.json()
    client_id = body.get("principal", {}).get("clientId", WATCHDOG_PRINCIPAL)
    client_secret = body.get("credentials", {}).get("clientSecret")
    print(f"  ✅ principal recreated")
    print(f"     clientId:     {client_id}")
    print(f"     clientSecret: {client_secret}")
    print("     ⚠️  Save this secret — Polaris will not show it again.")

    # Re-assign principal role (catalog role already exists)
    r = assign_principal_role_to_principal(
        principal=WATCHDOG_PRINCIPAL, pr=WATCHDOG_PR, token=tok
    )
    print(f"  ✅ principal role re-assigned ({r.status_code})")

    return client_id, client_secret


def get_watchdog_token(client_id, client_secret):
    """
    Acquire a token for the watchdog principal using the default POLARIS realm.
    client_secret must be the value saved from ensure_watchdog_setup()'s
    first run (or wherever it's stored — e.g. K8s secret).

    Note: unlike root (service_admin, can use PRINCIPAL_ROLE:ALL),
    watchdog-principal must request its specific assigned role scope.
    """
    r = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": REALM},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": f"PRINCIPAL_ROLE:{WATCHDOG_PR}",
        },
    )
    assert r.status_code == 200, f"Watchdog token failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


# ── Management API helpers ────────────────────────────────────
# Instance principal (run tests as a dedicated non-root principal)
#
# Instead of authenticating as root (whose service_admin role BYPASSES catalog
# privilege checks and hides real authorization behavior), each test runs its
# data operations (namespace / table / view create + drop) as a DEDICATED
# "instance principal" with exactly the catalog privileges it needs. Root is used
# ONLY to bootstrap - create the catalog, the principal, its roles, and the
# grants - because those are Management-API operations that require admin.

# Privilege set for an instance principal. MODELED ON THE PRODUCTION-VERIFIED
# watchdog availability test: a single CATALOG_MANAGE_CONTENT grant on the
# principal's OWN catalog is sufficient for all namespace/table/view CRUD
# (proven by watchdog T03/T04 in dev AND prod). Granting only this — and nothing
# at the management/service_admin level — is the "limited scope for safety"
# property: the principal can fully operate inside its own catalog but cannot
# touch any other catalog or management resource (watchdog T05 proves this).
INSTANCE_PRINCIPAL_PRIVS = ["CATALOG_MANAGE_CONTENT"]


def instance_principal(catalog, privileges=None, suffix="inst", root=None):
    """Create (idempotently) a dedicated instance principal for `catalog` and
    return (auth_header, names) where auth_header authenticates AS THE INSTANCE
    PRINCIPAL (use it for all namespace/table/view operations), and
    names = (principal, principal_role, catalog_role).

    Bootstrap uses the root token (`root`, defaults to root_token()), since
    creating principals/roles/grants requires admin. `privileges` defaults to
    INSTANCE_PRINCIPAL_PRIVS; pass a narrower list to test least-privilege."""
    rtok = root or root_token()
    privs = privileges if privileges is not None else INSTANCE_PRINCIPAL_PRIVS
    P = f"{catalog}-{suffix}-prin"
    PR = f"{catalog}-{suffix}-prole"
    CR = f"{catalog}-{suffix}-crole"

    requests.delete(f"{BASE_MGMT}/principals/{P}", headers=h(rtok))
    requests.delete(f"{BASE_MGMT}/principal-roles/{PR}", headers=h(rtok))

    rp = create_principal(P, token=rtok).json()
    # Extract credentials exactly as the production-verified watchdog setup does:
    #   clientId    is under  body["principal"]["clientId"]
    #   clientSecret is under body["credentials"]["clientSecret"]
    cid = rp.get("principal", {}).get("clientId") or rp.get("clientId")
    csec = rp.get("credentials", {}).get("clientSecret") or rp.get("clientSecret")

    create_principal_role(PR, token=rtok)
    create_catalog_role(catalog=catalog, name=CR, token=rtok)
    assign_catalog_role_to_principal_role(catalog=catalog, pr=PR, cr=CR, token=rtok)
    assign_principal_role_to_principal(principal=P, pr=PR, token=rtok)
    for pv in privs:
        grant_privilege(catalog=catalog, cr=CR, privilege=pv, token=rtok)

    itok = (
        get_token(client_id=cid, client_secret=csec, scope=f"PRINCIPAL_ROLE:{PR}")
        .json()
        .get("access_token")
    )
    header = {
        "Authorization": f"Bearer {itok}",
        "Polaris-Realm": REALM,
        "Content-Type": "application/json",
    }
    return header, (P, PR, CR)


# Suffixes used by tests when creating instance principals (instance_principal's
# default plus the ones the view-purge probe and the scaff/worker pattern use).
# Cleanup sweeps all of them.
INSTANCE_PRINCIPAL_SUFFIXES = ("inst", "full", "scaffold", "scaff", "worker")


def delete_instance_principal(names, catalog=None, root=None):
    """Delete ONE instance principal + its principal-role (and catalog-role if a
    catalog is given). Pass the `names` tuple (P, PR, CR) returned by
    instance_principal(). Safe/idempotent — ignores 404s."""
    if not names:
        return
    rtok = root or root_token()
    P, PR, CR = names
    requests.delete(f"{BASE_MGMT}/principals/{P}", headers=h(rtok))
    requests.delete(f"{BASE_MGMT}/principal-roles/{PR}", headers=h(rtok))
    if catalog:
        requests.delete(
            f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles/{CR}", headers=h(rtok)
        )


def delete_instance_principals_for(
    catalog, suffixes=INSTANCE_PRINCIPAL_SUFFIXES, root=None
):
    """Delete every instance principal + principal-role created for `catalog` by
    naming convention ({catalog}-{suffix}-prin / -prole). Called from catalog
    teardown so each test cleans up its own instance principals (they are
    catalog-independent and otherwise leak). Idempotent."""
    rtok = root or root_token()
    for sfx in suffixes:
        requests.delete(f"{BASE_MGMT}/principals/{catalog}-{sfx}-prin", headers=h(rtok))
        requests.delete(
            f"{BASE_MGMT}/principal-roles/{catalog}-{sfx}-prole", headers=h(rtok)
        )


def sweep_instance_principals(
    prefixes=None, suffixes=INSTANCE_PRINCIPAL_SUFFIXES, root=None
):
    """Safety sweep: delete ALL leftover instance principals/principal-roles
    matching the test naming convention (…-{suffix}-prin / -prole). Use to clear
    accumulation from earlier runs. `prefixes` optionally restricts to names
    starting with one of the given strings (e.g. ['vptest-','vpprobe-'])."""
    rtok = root or root_token()

    def _match(name, tail):
        if not any(name.endswith(f"-{sfx}-{tail}") for sfx in suffixes):
            return False
        if prefixes and not any(name.startswith(p) for p in prefixes):
            return False
        return True

    prins = (
        requests.get(f"{BASE_MGMT}/principals", headers=h(rtok))
        .json()
        .get("principals", [])
    )
    n = 0
    for p in prins:
        nm = p["name"] if isinstance(p, dict) else p
        if nm != "root" and _match(nm, "prin"):
            requests.delete(f"{BASE_MGMT}/principals/{nm}", headers=h(rtok))
            n += 1
    roles = (
        requests.get(f"{BASE_MGMT}/principal-roles", headers=h(rtok))
        .json()
        .get("roles", [])
    )
    for r in roles:
        nm = r["name"] if isinstance(r, dict) else r
        if _match(nm, "prole"):
            requests.delete(f"{BASE_MGMT}/principal-roles/{nm}", headers=h(rtok))
            n += 1
    print(f"🧹 swept {n} leftover instance principal/role objects")
    return n


def worker_principal(catalog, privileges, suffix="worker", root=None):
    """Provision a CHALLENGE-phase worker principal holding EXACTLY the given
    privilege(s) and nothing else. Thin wrapper over instance_principal used by
    the scaffolding pattern: the worker fires the actual mutate/DELETE under test
    so its single privilege is the only thing that could authorize the action.
    Returns (auth_header, (P, PR, CR))."""
    privs = privileges if isinstance(privileges, (list, tuple)) else [privileges]
    return instance_principal(catalog, privileges=list(privs), suffix=suffix, root=root)


class case_scaffold:
    """Three-phase scaff/worker lifecycle as a context manager (blueprint §2B/§2C).

      Phase 1 SETUP       : a full-privilege scaff principal (CATALOG_MANAGE_CONTENT)
                            runs `build(scaff_header)` to create the namespace and
                            any prerequisite table/view the challenge needs.
      Phase 2 DESTROY     : the scaff principal is deleted (only if destroy_scaff=
                            True — strict isolation for the privilege matrix; set
                            False to keep a persistent scaffold for speed, e.g. in
                            view-purge).
      Phase 3 CHALLENGE   : the caller calls .worker([priv]) to get a header for a
                            principal holding only the privilege under test, then
                            fires the actual request inside the `with` block.
      __exit__ (ALWAYS)   : atomic teardown. Deletes the worker + scaff principals,
                            then runs `teardown(catalog)` if given (e.g. the
                            notebook's force_delete_catalog), else a self-contained
                            recursive catalog teardown + MinIO sweep.

    Usage:
        create_catalog(cat, token=tok, properties={...})          # caller owns config
        with case_scaffold(cat, build=build_fn, teardown=force_delete_catalog,
                           root=tok, destroy_scaff=True) as scaf:
            whdr, _ = scaf.worker(["VIEW_DROP"])
            r = requests.delete(view_url, headers=whdr)
        # teardown ran here, no leaks
    """

    def __init__(
        self,
        catalog,
        build=None,
        teardown=None,
        root=None,
        destroy_scaff=True,
        scaff_privs=None,
    ):
        self.catalog = catalog
        self.build = build
        self.teardown = teardown
        self.root = root or root_token()
        self.destroy_scaff = destroy_scaff
        self.scaff_privs = scaff_privs or ["CATALOG_MANAGE_CONTENT"]
        self.scaff_hdr = None
        self.scaff_names = None
        self._workers = []  # names of worker principals to clean up

    def __enter__(self):
        # Phase 1: setup with a full-priv scaff principal
        self.scaff_hdr, self.scaff_names = instance_principal(
            self.catalog, privileges=self.scaff_privs, suffix="scaff", root=self.root
        )
        if self.build is not None:
            self.build(self.scaff_hdr)
        # Phase 2: destroy scaff (strict isolation) — the entity it built remains
        if self.destroy_scaff:
            delete_instance_principal(
                self.scaff_names, catalog=self.catalog, root=self.root
            )
            self.scaff_names = None
        return self

    def worker(self, privileges, suffix="worker"):
        """Phase 3: provision the challenge principal with only `privileges`."""
        hdr, names = worker_principal(
            self.catalog, privileges, suffix=suffix, root=self.root
        )
        self._workers.append(names)
        return hdr, names

    def __exit__(self, exc_type, exc, tb):
        # Atomic teardown — always runs, even on exception.
        for names in self._workers:
            delete_instance_principal(names, catalog=self.catalog, root=self.root)
        if self.scaff_names is not None:
            delete_instance_principal(
                self.scaff_names, catalog=self.catalog, root=self.root
            )
        if self.teardown is not None:
            try:
                self.teardown(self.catalog)
            except Exception as e:
                print(f"   ⚠️ teardown({self.catalog}) raised: {e}")
        else:
            _teardown_catalog_selfcontained(self.catalog, root=self.root)
        return False  # never suppress exceptions


def _teardown_catalog_selfcontained(catalog, root=None):
    """Fallback recursive teardown when no notebook teardown is supplied:
    drop views/tables → namespaces (deepest first) → non-default catalog-roles →
    catalog, then sweep instance principals and MinIO objects. Best-effort."""
    rtok = root or root_token()
    if (
        requests.get(f"{BASE_MGMT}/catalogs/{catalog}", headers=h(rtok)).status_code
        == 404
    ):
        delete_instance_principals_for(catalog, root=rtok)
        return True
    nss = (
        requests.get(f"{BASE_CAT}/{catalog}/namespaces", headers=h(rtok))
        .json()
        .get("namespaces", [])
    )
    nss = sorted(
        nss, key=lambda n: len(n if isinstance(n, list) else [n]), reverse=True
    )
    for ns in nss:
        nsn = "\x1f".join(ns) if isinstance(ns, list) else ns
        for t in (
            requests.get(
                f"{BASE_CAT}/{catalog}/namespaces/{nsn}/tables", headers=h(rtok)
            )
            .json()
            .get("identifiers", [])
        ):
            requests.delete(
                f"{BASE_CAT}/{catalog}/namespaces/{nsn}/tables/{t['name']}",
                headers=h(rtok),
            )
        for v in (
            requests.get(
                f"{BASE_CAT}/{catalog}/namespaces/{nsn}/views", headers=h(rtok)
            )
            .json()
            .get("identifiers", [])
        ):
            requests.delete(
                f"{BASE_CAT}/{catalog}/namespaces/{nsn}/views/{v['name']}",
                headers=h(rtok),
            )
        requests.delete(f"{BASE_CAT}/{catalog}/namespaces/{nsn}", headers=h(rtok))
    for cr in (
        requests.get(f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles", headers=h(rtok))
        .json()
        .get("roles", [])
    ):
        crn = cr["name"] if isinstance(cr, dict) else cr
        if crn != "catalog_admin":
            requests.delete(
                f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles/{crn}", headers=h(rtok)
            )
    requests.delete(
        f"{BASE_MGMT}/catalogs/{catalog}?purgeRequested=true", headers=h(rtok)
    )
    delete_instance_principals_for(catalog, root=rtok)
    if mc is not None:
        try:
            mc.delete_prefix(f"{catalog}/", min_size=0)
        except Exception:
            pass
    return (
        requests.get(f"{BASE_MGMT}/catalogs/{catalog}", headers=h(rtok)).status_code
        == 404
    )


def teardown_catalog(catalog, root=None):
    """Public entry point for a recursive catalog teardown (views/tables →
    namespaces → non-default catalog-roles → catalog, then sweep instance
    principals + MinIO). Thin wrapper over `_teardown_catalog_selfcontained` so
    notebooks don't have to reach a private, underscore-prefixed name —
    `from nb_support import *` does NOT export leading-underscore names,
    so calling the private function directly raises NameError."""
    return _teardown_catalog_selfcontained(catalog, root=root)


# ─────────────────────────────────────────────────────────────────────────────
# Test-case orchestration (arrange → act → assert → guaranteed cleanup)
#
# A test case is four responsibilities, composed by `run_case`:
#   1. Suite   (arrange) — build_suite(): common; records setup entities.
#   2. Execute (act)     — per-case core logic; returns a response.
#   3. Result  (assert)  — per-case; PURE (prints/derives, changes nothing).
#   4. Cleaner (teardown)— clean(): common; deletes tracked entities, ALWAYS.
# Cleanup operates on the *recorded* Entities, not a naming guess — so no case
# can leak into another.
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Entities:
    """Cleanup ledger + light context bag for one test case. `Suite` fills it
    during arrange; `Execute` may record what it creates into a second Entities;
    `clean(*bundles)` reclaims all of it. Only GLOBAL objects need recording —
    catalogs, principals, principal-roles — because a catalog purge cascades its
    namespaces/tables/views/catalog-roles + MinIO objects. `ctx` carries the
    working handles Execute/Result need (catalog, ns, entity, worker_hdr, …)."""

    catalogs: list = field(default_factory=list)
    principals: list = field(default_factory=list)
    principal_roles: list = field(default_factory=list)
    catalog_roles: list = field(
        default_factory=list
    )  # (catalog, name); usually cascade-cleaned
    ctx: dict = field(default_factory=dict)


def provision_worker_multi(catalog, privileges, suffix="worker", root=None):
    """Provision a single-use worker principal holding EXACTLY `privileges`.
    Polls until the catalog-role is visible before granting (avoids the 404
    read-after-write lag under PG-HA), issues the token AFTER the grants (so it
    reflects the full footprint), and reports which names the build rejected.
    Returns (header_or_None, granted, invalid, (P, PR, CR))."""
    rtok = root or root_token()
    P = f"{catalog}-{suffix}-prin"
    PR = f"{catalog}-{suffix}-prole"
    CR = f"{catalog}-{suffix}-crole"
    requests.delete(f"{BASE_MGMT}/principals/{P}", headers=h(rtok))
    requests.delete(f"{BASE_MGMT}/principal-roles/{PR}", headers=h(rtok))
    rp = create_principal(P, token=rtok).json()
    cid = rp.get("principal", {}).get("clientId") or rp.get("clientId")
    csec = rp.get("credentials", {}).get("clientSecret") or rp.get("clientSecret")
    create_principal_role(PR, token=rtok)
    create_catalog_role(catalog=catalog, name=CR, token=rtok)
    assign_catalog_role_to_principal_role(catalog=catalog, pr=PR, cr=CR, token=rtok)
    assign_principal_role_to_principal(principal=P, pr=PR, token=rtok)
    # wait for the catalog-role to be visible before granting
    for _ in range(6):
        lr = requests.get(
            f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles", headers=h(rtok)
        )
        names = [
            (c.get("name") if isinstance(c, dict) else c)
            for c in (lr.json().get("roles", []) if lr.status_code == 200 else [])
        ]
        if CR in names:
            break
        time.sleep(0.5)
    privs = list(privileges) if isinstance(privileges, (list, tuple)) else [privileges]
    granted, invalid = [], []
    for pv in privs:
        gr = grant_privilege(catalog=catalog, cr=CR, privilege=pv, token=rtok)
        gb = gr.text.lower()
        ok = (
            gr.status_code < 400
            or "already exists" in gb
            or "23505" in gb
            or "duplicate key" in gb
        )
        (granted if ok else invalid).append(pv)
    tr = get_token(client_id=cid, client_secret=csec, scope=f"PRINCIPAL_ROLE:{PR}")
    if tr.status_code != 200:
        return None, granted, invalid, (P, PR, CR)
    wtok = tr.json().get("access_token")
    hdr = {
        "Authorization": f"Bearer {wtok}",
        "Polaris-Realm": REALM,
        "Content-Type": "application/json",
    }
    return hdr, granted, invalid, (P, PR, CR)


def build_suite(
    ents,
    root=None,
    *,
    prefix="case-",
    build=None,
    footprint=None,
    drop_gate=False,
    entity=None,
    scaff_privs=None,
):
    """Common **Suite** (arrange): fresh catalog (+optional drop-with-purge gate)
    → scaffold prereqs via a full-privilege scaff principal that is then destroyed
    (so the worker's single grant is the only thing under test) → provision a
    worker holding EXACTLY `footprint`. Every created entity (catalog, scaff +
    worker principals/roles) is recorded into `ents` BEFORE it might fail, so a
    mid-arrange error still cleans up. Working handles land in `ents.ctx`:
    catalog, ns, entity, worker_hdr, granted, invalid. `build(catalog, scaff_hdr,
    ctx)` creates any prerequisite namespace/table/view."""
    rtok = root or root_token()
    cat = f"{prefix}{uuid.uuid4().hex[:6]}"
    props = (
        {
            "polaris.config.drop-with-purge.enabled": "true",
            "polaris.config.purge-view-metadata-on-drop": "false",
        }
        if drop_gate
        else {}
    )
    create_catalog(cat, token=rtok, properties=props)
    ents.catalogs.append(cat)
    ent = entity or f"e{uuid.uuid4().hex[:6]}"
    ctx = {"catalog": cat, "ns": f"ns-{cat}", "entity": ent}
    # scaff — full-priv, records first (leak-proof), builds prereqs, then destroyed
    scaff_hdr, scaff_names = instance_principal(
        cat,
        privileges=scaff_privs or ["CATALOG_MANAGE_CONTENT"],
        suffix="scaff",
        root=rtok,
    )
    ents.principals.append(scaff_names[0])
    ents.principal_roles.append(scaff_names[1])
    ents.catalog_roles.append((cat, scaff_names[2]))
    if build is not None:
        build(cat, scaff_hdr, ctx)
    delete_instance_principal(scaff_names, catalog=cat, root=rtok)  # isolation
    # worker — exactly `footprint`
    whdr, granted, invalid, wnames = provision_worker_multi(
        cat, footprint or [], root=rtok
    )
    ents.principals.append(wnames[0])
    ents.principal_roles.append(wnames[1])
    ents.catalog_roles.append((cat, wnames[2]))
    ctx.update(worker_hdr=whdr, granted=granted, invalid=invalid)
    ents.ctx.update(ctx)
    return ents


def clean(*bundles, root=None):
    """Common **Cleaner**: delete every entity recorded across the given Entities
    bundles (suite + during-test). Global objects first (principals, principal-
    roles), then catalogs last (recursive purge cascades namespaces/tables/views/
    catalog-roles + MinIO). Deduped and idempotent — safe to call in a `finally`."""
    rtok = root or root_token()
    done = set()
    for b in bundles:
        for p in b.principals:
            if p and ("p", p) not in done:
                done.add(("p", p))
                requests.delete(f"{BASE_MGMT}/principals/{p}", headers=h(rtok))
        for pr in b.principal_roles:
            if pr and ("pr", pr) not in done:
                done.add(("pr", pr))
                requests.delete(f"{BASE_MGMT}/principal-roles/{pr}", headers=h(rtok))
    for b in bundles:
        for cr in b.catalog_roles:
            cat, name = cr if isinstance(cr, (tuple, list)) else (None, cr)
            if cat and name and ("cr", cat, name) not in done:
                done.add(("cr", cat, name))
                requests.delete(
                    f"{BASE_MGMT}/catalogs/{cat}/catalog-roles/{name}", headers=h(rtok)
                )
    for b in bundles:
        for cat in b.catalogs:
            if cat and ("c", cat) not in done:
                done.add(("c", cat))
                try:
                    _teardown_catalog_selfcontained(cat, root=rtok)
                except Exception as e:
                    print(f"  ⚠️ clean catalog {cat}: {e}")


def run_case(name, suite_fn, execute_fn, result_fn=None, root=None):
    """Orchestrate one test case as arrange → act → assert → **guaranteed** cleanup:

        suite_fn(suite_ents, root)                           # arrange
        resp = execute_fn(suite_ents, created_ents, root)    # act
        result_fn(name, resp, suite_ents, created_ents)      # assert (pure)
        clean(suite_ents, created_ents)                      # teardown, ALWAYS

    Returns whatever `result_fn` returns (or the raw response if it is None).
    Cleanup runs in a `finally`, so it happens even if execute/result raise."""
    rtok = root or root_token()
    suite_ents, created = Entities(), Entities()
    try:
        suite_fn(suite_ents, rtok)
        resp = execute_fn(suite_ents, created, rtok)
        return result_fn(name, resp, suite_ents, created) if result_fn else resp
    finally:
        clean(suite_ents, created, root=rtok)


def create_catalog(name=TEST_CATALOG, token=None, properties=None):
    """Create an INTERNAL S3/MinIO catalog using the ACTIVE environment's
    endpoints and bucket (from init_env). Pass `properties` to merge/override
    catalog properties (e.g. toggle drop-with-purge)."""
    props = {
        "default-base-location": f"s3a://{BUCKET}/{name}/",
        "polaris.config.drop-with-purge.enabled": "true",
    }
    if properties:
        props.update(properties)
    return requests.post(
        f"{BASE_MGMT}/catalogs",
        headers=h(token),
        json={
            "catalog": {
                "name": name,
                "type": "INTERNAL",
                "properties": props,
                "storageConfigInfo": {
                    "storageType": "S3",
                    "allowedLocations": [f"s3a://{BUCKET}/"],
                    "pathStyleAccess": True,
                    "endpoint": MINIO_ENDPOINT,
                    "endpointInternal": MINIO_ENDPOINT_INTERNAL,
                },
            }
        },
    )


def create_catalog_no_endpoint(name=TEST_CATALOG, token=None):
    return requests.post(
        f"{BASE_MGMT}/catalogs",
        headers=h(token),
        json={
            "catalog": {
                "name": name,
                "type": "INTERNAL",
                "properties": {
                    "default-base-location": f"s3a://data-catalog-bucket/{name}/",
                },
                "storageConfigInfo": {
                    "storageType": "S3",
                    "allowedLocations": ["s3a://data-catalog-bucket/"],
                    "pathStyleAccess": True,
                    "endpoint": "http://192.168.139.2:9000",
                },
            }
        },
    )


def delete_catalog(name=TEST_CATALOG, token=None):
    return requests.delete(f"{BASE_MGMT}/catalogs/{name}", headers=h(token))


def create_namespace(catalog=TEST_CATALOG, ns=TEST_NAMESPACE, token=None):
    return requests.post(
        f"{BASE_CAT}/{catalog}/namespaces",
        headers=h(token),
        json={"namespace": [ns], "properties": {}},
    )


def delete_namespace(catalog=TEST_CATALOG, ns=TEST_NAMESPACE, token=None):
    return requests.delete(
        f"{BASE_CAT}/{catalog}/namespaces/{ns}",
        headers=h(token),
    )


def create_principal(name=TEST_PRINCIPAL, token=None):
    return requests.post(
        f"{BASE_MGMT}/principals",
        headers=h(token),
        json={
            "principal": {"name": name, "type": "SERVICE"},
            "credentialRotationRequired": False,
        },
    )


def delete_principal(name=TEST_PRINCIPAL, token=None):
    return requests.delete(f"{BASE_MGMT}/principals/{name}", headers=h(token))


def create_principal_role(name=TEST_PR, token=None):
    return requests.post(
        f"{BASE_MGMT}/principal-roles",
        headers=h(token),
        json={"principalRole": {"name": name}},
    )


def delete_principal_role(name=TEST_PR, token=None):
    return requests.delete(f"{BASE_MGMT}/principal-roles/{name}", headers=h(token))


def create_catalog_role(catalog=TEST_CATALOG, name=TEST_CR, token=None):
    return requests.post(
        f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles",
        headers=h(token),
        json={"catalogRole": {"name": name}},
    )


def assign_catalog_role_to_principal_role(
    catalog=TEST_CATALOG, pr=TEST_PR, cr=TEST_CR, token=None
):
    return requests.put(
        f"{BASE_MGMT}/principal-roles/{pr}/catalog-roles/{catalog}",
        headers=h(token),
        json={"catalogRole": {"name": cr}},
    )


def assign_principal_role_to_principal(
    principal=TEST_PRINCIPAL, pr=TEST_PR, token=None
):
    return requests.put(
        f"{BASE_MGMT}/principals/{principal}/principal-roles",
        headers=h(token),
        json={"principalRole": {"name": pr}},
    )


def grant_privilege(
    catalog=TEST_CATALOG, cr=TEST_CR, privilege="CATALOG_MANAGE_CONTENT", token=None
):
    """Grant a catalog privilege to a catalog-role, idempotently and CHEAPLY.

    Polaris implements the grant PUT as an INSERT. If the grant already exists it
    does NOT no-op: it retries the write against the metastore for ~5 SECONDS and
    then throws a duplicate-key (23505) error. Under PG-Pool/PG-HA that 5s wait is
    pure dead time (the existence check reads a lagging replica, the insert hits
    the primary and conflicts, and it retries for the full window). Six redundant
    grants = ~30s wasted per run.

    To avoid that cost entirely, we SKIP the grant if the role already holds the
    privilege (a cheap GET on existing grants). If the grant still races through,
    we treat the 23505 / 'already exists' response as success (correctness)."""
    grants_url = f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles/{cr}/grants"
    # 1. skip-if-present: avoid the redundant INSERT (and its 5s server retry)
    try:
        existing = requests.get(grants_url, headers=h(token))
        if existing.status_code == 200:
            for g in existing.json().get("grants", []):
                if (
                    g.get("privilege") == privilege
                    and g.get("type", "catalog") == "catalog"
                ):
                    return existing  # already granted → no write, no 5s wait
    except Exception:
        pass  # if the check fails, fall through to the PUT (still safe)
    # 2. issue the grant. Retry on a transient 404 "…not found": the catalog-role
    #    was just created and may not yet be visible on a lagging PG read replica
    #    (read-after-write lag under PG-HA/PgBouncer). Without this, a perfectly
    #    valid grant 404s and callers misread it as GRANT_INVALID / BLOCKED_PRIV.
    r = None
    _MAX = 7
    for _attempt in range(_MAX):
        r = requests.put(
            grants_url,
            headers=h(token),
            json={"grant": {"type": "catalog", "privilege": privilege}},
        )
        if r.status_code < 400:
            return r
        body = r.text.lower()
        if (
            "already exists" in body
            or "23505" in body
            or "duplicate key" in body
            or "grant_records_pkey" in body
        ):
            # grant already present → treat as success (idempotent)
            return r
        if r.status_code == 404 and "not found" in body and _attempt < _MAX - 1:
            # read-after-write lag on the just-created catalog-role: back off
            # (capped) and retry — cumulative wait ~9s before giving up.
            time.sleep(min(0.5 * (_attempt + 1), 2.0))
            continue
        # genuine error (e.g. 400 invalid privilege name) → surface and stop
        print(
            f"  ⚠️ grant_privilege {privilege} on {catalog}/{cr} → "
            f"[{r.status_code}] {r.text[:160]}"
        )
        return r
    return r


# ── Cleanup ───────────────────────────────────────────────────
# System entities — never delete
_SKIP_PRINCIPALS = {"root"}
_SKIP_PRINCIPAL_ROLES = {"service_admin"}
_SKIP_CATALOG_ROLES = {"catalog_admin"}


def _delete(url, tok, label):
    """Delete a resource, print result."""
    r = requests.delete(url, headers=h(tok))
    icon = "✅" if r.status_code in [200, 204] else "⚠️ "
    print(f"  {icon} [{r.status_code}] {label}")
    return r.status_code


def cleanup(token=None):
    """
    Delete ALL test resources following dependency order:
      1. Tables + Views   (inside namespaces)
      2. Namespaces       (inside catalogs)
      3. Catalog Roles    (inside catalogs, skip catalog_admin)
      4. Catalogs
      5. Principals       (skip root)
      6. Principal Roles  (skip service_admin)

    Mirrors polaris_clean_all.ipynb logic.
    Safe: skips system entities, ignores 404s.
    """
    tok = token or root_token()
    print("🧹 Cleaning up all test resources...")

    # ── Fetch current state ───────────────────────────────────
    catalogs = (
        requests.get(f"{BASE_MGMT}/catalogs", headers=h(tok)).json().get("catalogs", [])
    )

    principals = (
        requests.get(f"{BASE_MGMT}/principals", headers=h(tok))
        .json()
        .get("principals", [])
    )

    principal_roles = (
        requests.get(f"{BASE_MGMT}/principal-roles", headers=h(tok))
        .json()
        .get("roles", [])
    )

    # ── Step 1+2: Tables + Views + Namespaces (recursive) ───────
    def _ns_to_url(ns):
        """Convert namespace list to URL-safe string."""
        if isinstance(ns, list):
            return "%1F".join(ns)
        return ns

    def _ns_to_label(ns):
        """Convert namespace list to readable string."""
        if isinstance(ns, list):
            return ".".join(ns)
        return ns

    def _delete_ns(cname, ns_url, ns_label, tok):
        """Recursively delete child namespaces, tables, views, then namespace."""
        # Get children of this namespace
        child_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces",
            headers=h(tok),
            params={"parent": ns_label},
        )
        for child in child_r.json().get("namespaces", []):
            _delete_ns(cname, _ns_to_url(child), _ns_to_label(child), tok)

        # Delete tables in this namespace
        t_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}/tables", headers=h(tok)
        )
        for t in t_r.json().get("identifiers", []):
            tname = t.get("name", str(t))
            _delete(
                f"{BASE_CAT}/{cname}/namespaces/{ns_url}/tables/{tname}",
                tok,
                f"table: {cname}.{ns_label}.{tname}",
            )

        # Delete views in this namespace
        v_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}/views", headers=h(tok)
        )
        for v in v_r.json().get("identifiers", []):
            vname = v.get("name", str(v))
            _delete(
                f"{BASE_CAT}/{cname}/namespaces/{ns_url}/views/{vname}",
                tok,
                f"view: {cname}.{ns_label}.{vname}",
            )

        # Delete namespace itself (now empty)
        _delete(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}",
            tok,
            f"namespace: {cname}.{ns_label}",
        )

    # Process all top-level namespaces recursively
    for c in catalogs:
        cname = c["name"]
        ns_r = requests.get(f"{BASE_CAT}/{cname}/namespaces", headers=h(tok))
        for ns in ns_r.json().get("namespaces", []):
            _delete_ns(cname, _ns_to_url(ns), _ns_to_label(ns), tok)

    # ── Step 3: Catalog Roles ─────────────────────────────────
    for c in catalogs:
        cname = c["name"]
        cr_r = requests.get(
            f"{BASE_MGMT}/catalogs/{cname}/catalog-roles", headers=h(tok)
        )
        for cr in cr_r.json().get("roles", []):
            crname = cr["name"]
            if crname in _SKIP_CATALOG_ROLES:
                continue
            _delete(
                f"{BASE_MGMT}/catalogs/{cname}/catalog-roles/{crname}",
                tok,
                f"catalog-role: {cname}/{crname}",
            )

    # ── Step 4: Catalogs ──────────────────────────────────────
    for c in catalogs:
        cname = c["name"]
        _delete(f"{BASE_MGMT}/catalogs/{cname}", tok, f"catalog: {cname}")

    # ── Step 5: Principals ────────────────────────────────────
    for p in principals:
        pname = p["name"]
        if pname in _SKIP_PRINCIPALS:
            continue
        _delete(f"{BASE_MGMT}/principals/{pname}", tok, f"principal: {pname}")

    # ── Step 6: Principal Roles ───────────────────────────────
    for pr in principal_roles:
        prname = pr["name"]
        if prname in _SKIP_PRINCIPAL_ROLES:
            continue
        _delete(
            f"{BASE_MGMT}/principal-roles/{prname}", tok, f"principal-role: {prname}"
        )

    print("✅ Cleanup done")


# ── OpenSearch ────────────────────────────────────────────────
def os_client():
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )


def search_logs(request_id=None, level=None, message=None, minutes_ago=10, size=20):
    """Search Polaris logs in OpenSearch."""
    client = os_client()
    must = [
        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
        # Only Polaris container logs
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
    ]
    if request_id:
        # requestId is nested in mdc object
        must.append({"term": {"mdc.requestId.keyword": request_id}})
    if level:
        must.append({"term": {"level.keyword": level}})
    if message:
        must.append({"match": {"message": message}})

    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {"bool": {"must": must}},
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
        },
    )
    return result["hits"]["hits"]


def search_logs_raw(query_dict, size=5):
    """Raw OpenSearch query for debugging."""
    client = os_client()
    result = client.search(index=LOG_INDEX, body={**query_dict, "size": size})
    return result["hits"]["hits"]


def debug_opensearch(minutes_ago=5):
    """
    Debug helper — show what's actually in OpenSearch.
    Use when search_logs returns empty.
    """
    client = os_client()
    print("=== OpenSearch Debug ===\n")

    # 1. Show available indices
    indices = client.cat.indices(index="k8s-logs-*", format="json")
    print("Indices:")
    for idx in indices:
        print(f"  {idx['index']}: {idx['docs.count']} docs")

    # 2. Show all container names
    result = client.search(
        index=LOG_INDEX,
        body={
            "size": 0,
            "aggs": {
                "containers": {
                    "terms": {"field": "kubernetes.container_name.keyword", "size": 10}
                }
            },
        },
    )
    print("\nContainer names in index:")
    for b in result["aggregations"]["containers"]["buckets"]:
        print(f"  {b['key']}: {b['doc_count']} docs")

    # 3. Show last 3 Polaris logs (any field name for pod)
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"match": {"kubernetes.pod_name": "polaris"}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 3,
        },
    )
    total = result["hits"]["total"]["value"]
    print(f"\nPolaris logs last {minutes_ago}m: {total} docs")
    if result["hits"]["hits"]:
        print("Latest log sample:")
        src = result["hits"]["hits"][0]["_source"]
        print(f"  @timestamp: {src.get('@timestamp')}")
        print(f"  level:      {src.get('level', 'NOT FOUND')}")
        print(f"  message:    {src.get('message', src.get('log', 'NOT FOUND'))[:100]}")
        print(f"  mdc:        {src.get('mdc', 'NOT FOUND')}")
        print(
            f"  container:  {src.get('kubernetes', {}).get('container_name', 'NOT FOUND')}"
        )


def print_logs(hits, show_debug_on_empty=True):
    """Pretty print OpenSearch log hits."""
    if not hits:
        print("⚠️  No logs found")
        if show_debug_on_empty:
            print("\nRunning debug to check OpenSearch state...")
            debug_opensearch()
        return

    print(f"Found {len(hits)} log entries:\n")
    for hit in hits:
        src = hit["_source"]
        ts = src.get("@timestamp", "")
        level = src.get("level", "INFO")
        msg = src.get("message", src.get("log", ""))
        mdc = src.get("mdc", {})
        req_id = mdc.get("requestId", "") if isinstance(mdc, dict) else ""
        realm = mdc.get("realmId", "") if isinstance(mdc, dict) else ""
        logger = src.get("loggerName", "")

        icon = {"ERROR": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ ", "DEBUG": "🔍"}.get(
            level, "  "
        )
        print(f"{icon} [{ts}] {level}")
        print(f"   logger    : {logger}")
        print(f"   requestId : {req_id}")
        print(f"   realmId   : {realm}")
        print(f"   message   : {msg[:200]}")
        print()


def get_request_id(response):
    """Extract Polaris-Request-Id from response headers."""
    return response.headers.get("Polaris-Request-Id", "not found")


def print_response(r, label="Response"):
    """Pretty print API response."""
    print(f"\n{label}:")
    print(f"  Status:     {r.status_code}")
    print(f"  Request-Id: {get_request_id(r)}")
    try:
        print(f"  Body: {json.dumps(r.json(), indent=2)}")
    except:
        print(f"  Body: {r.text[:500]}")


def wait_for_logs(seconds=10):
    """Wait for Fluent Bit to ship logs to OpenSearch."""
    print(f"⏳ Waiting {seconds}s for logs to reach OpenSearch...")
    time.sleep(seconds)


def search_and_debug(request_id, minutes_ago=10):
    """
    Search by requestId with automatic debug fallback.
    Call this instead of search_logs in notebooks.
    """
    print(f"🔍 Searching for requestId: {request_id}")

    # Try 1: exact requestId match
    hits = search_logs(request_id=request_id, minutes_ago=minutes_ago)
    if hits:
        print(f"✅ Found by requestId")
        print_logs(hits)
        return hits

    print("  → requestId not found, trying fallback searches...")

    # Try 2: recent Polaris logs any level
    hits = search_logs(minutes_ago=2, size=5)
    if hits:
        print(f"  → Found {len(hits)} recent Polaris logs (last 2 min):")
        print_logs(hits, show_debug_on_empty=False)
        return hits

    # Try 3: full debug
    print("  → No recent logs found, running full debug...")
    debug_opensearch(minutes_ago=minutes_ago)
    return []


# ── General error search functions ───────────────────────────
# Use these instead of search_and_debug(request_id)
# minutes_ago=1 → only current run logs


def search_401_errors(minutes_ago=1):
    """Find 401 unauthorized errors — general pattern, no requestId needed."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        # HTTP access log shows 401 status
                        {"match": {"message": '" 401'}},
                        # Auth failures
                        {"match": {"message": "Failed to resolve principal"}},
                        {"match": {"message": "unauthorized_client"}},
                        {"match": {"message": "getToken API with status code 401"}},
                        {"match": {"message": "not authorized"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_403_errors(minutes_ago=1):
    """Find 403 forbidden errors — general pattern."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": '" 403'}},
                        {"match": {"message": "ForbiddenException"}},
                        {"match": {"message": "lacks privilege"}},
                        {"match": {"message": "is not authorized"}},
                        {"match": {"message": "drop-with-purge"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_404_errors(minutes_ago=1):
    """Find 404 not found errors — general pattern."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": '" 404'}},
                        {"match": {"message": "not found"}},
                        {"match": {"message": "NoSuch"}},
                        {"match": {"message": "does not exist"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_409_errors(minutes_ago=1):
    """Find 409 conflict errors — general pattern."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": '" 409'}},
                        {"match": {"message": "already exists"}},
                        {"match": {"message": "not empty"}},
                        {"match": {"message": "NamespaceNotEmpty"}},
                        {"match": {"message": "AlreadyExists"}},
                        {"match": {"message": "duplicate key"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_400_errors(minutes_ago=1):
    """Find 400 bad request errors — general pattern."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": '" 400'}},
                        {"match": {"message": "Bad Request"}},
                        {"match": {"message": "validation"}},
                        {"match": {"message": "malformed"}},
                        {"match": {"message": "invalid"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_500_errors(minutes_ago=1):
    """Find 500 internal server errors — general pattern."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": '" 500'}},
                        {"match": {"message": "NullPointerException"}},
                        {"match": {"message": "getRawLeafEntity"}},
                        {"match": {"message": "Internal Server Error"}},
                        {"match": {"message": "RuntimeException"}},
                        {"match": {"message": "duplicate key"}},
                        {"match": {"message": "grant_records_pkey"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_db_errors(minutes_ago=1):
    """Find DB connection pool errors."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": "connection"}},
                        {"match": {"message": "pool exhausted"}},
                        {"match": {"message": "SQLException"}},
                        {"match": {"message": "connection refused"}},
                        {"match": {"message": "broken pipe"}},
                        {"match": {"message": "Unable to acquire"}},
                        {"match": {"message": "postmaster is accepting"}},
                        {"match": {"loggerName": "io.agroal.pool"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_all_errors(minutes_ago=1):
    """Find ALL errors across all error types — for dashboard overview."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                        {"terms": {"level.keyword": ["ERROR", "WARN"]}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 20,
        },
    )
    return result["hits"]["hits"]


def search_entity_version_errors(minutes_ago=5):
    """
    Find entity_version mismatch errors.
    Key signal for PostgreSQL restore-from-backup incidents.
    """
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": "EntityVersionMismatch"}},
                        {"match": {"message": "entity_version"}},
                        {"match": {"message": "version mismatch"}},
                        {"match": {"message": "optimistic lock"}},
                        {"match": {"message": "concurrent modification"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


def search_blocked_thread_errors(minutes_ago=2):
    """
    Find Vert.x blocked thread warnings.
    Key signal: event loop thread blocked by DB connection wait.
    Appears during PostgreSQL outage BEFORE service fully freezes.
    """
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {
                            "term": {
                                "kubernetes.container_name.keyword": "benchmarks-polaris"
                            }
                        },
                    ],
                    "should": [
                        {"match": {"message": "has been blocked"}},
                        {"match": {"message": "BlockedThreadChecker"}},
                        {
                            "match": {
                                "loggerName": "io.vertx.core.impl.BlockedThreadChecker"
                            }
                        },
                        {"match": {"message": "Thread blocked"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10,
        },
    )
    return result["hits"]["hits"]


# ── Test result helper ────────────────────────────────────────
class TestResult:
    """Lightweight pass/fail tracker for notebook test runs."""

    def __init__(self):
        self.results = {}

    def record(self, name, passed, detail=""):
        self.results[name] = {"passed": passed, "detail": detail}
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}: {detail}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v["passed"])
        failed = [k for k, v in self.results.items() if not v["passed"]]
        print(f"\n{'='*50}")
        print(f"Result: {passed}/{total} passed")
        if failed:
            print(f"Failed: {', '.join(failed)}")
        return passed == total


# (env banner is printed by init_env)
