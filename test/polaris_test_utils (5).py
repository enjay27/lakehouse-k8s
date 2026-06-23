"""
polaris_test_utils.py
=====================
Shared utilities for all Polaris error case notebooks.
"""
import requests
import json
import time
from datetime import datetime
from opensearchpy import OpenSearch
import urllib3
urllib3.disable_warnings()

# ── Config ────────────────────────────────────────────────────
POLARIS_URL     = "http://192.168.139.2:8181"
REALM           = "POLARIS"
ROOT_CLIENT     = "root"
ROOT_SECRET     = "polaris-secret"

OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "Str0ngP@ssw0rd123!"
LOG_INDEX       = "k8s-logs-*"

# Test resource names
TEST_CATALOG    = "test-error-catalog"
TEST_NAMESPACE  = "test-ns"
TEST_TABLE      = "test-table"
TEST_PRINCIPAL  = "test-principal"
TEST_PR         = "test-principal-role"
TEST_CR         = "test-catalog-role"

# Watchdog resource names (daily availability test — uses default POLARIS realm)
WATCHDOG_PRINCIPAL = "watchdog-principal"
WATCHDOG_PR        = "watchdog-principal-role"
WATCHDOG_CR        = "watchdog-catalog-role"
WATCHDOG_CATALOG   = "watchdog-catalog"
WATCHDOG_NAMESPACE = "watchdog-ns"
WATCHDOG_TABLE     = "watchdog-table"

BASE_MGMT = f"{POLARIS_URL}/api/management/v1"
BASE_CAT  = f"{POLARIS_URL}/api/catalog/v1"

# ── Token ─────────────────────────────────────────────────────
def get_token(client_id=ROOT_CLIENT, client_secret=ROOT_SECRET, realm=REALM):
    r = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": realm},
        data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
            "scope":         "PRINCIPAL_ROLE:ALL",
        },
    )
    return r

def root_token():
    r = get_token()
    assert r.status_code == 200, f"Root token failed: {r.text}"
    return r.json()["access_token"]

def h(token=None, realm=REALM):
    tok = token or root_token()
    return {
        "Authorization":  f"Bearer {tok}",
        "Polaris-Realm":  realm,
        "Content-Type":   "application/json",
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
    principals = requests.get(f"{BASE_MGMT}/principals", headers=h(tok)).json().get("principals", [])
    existing = next((p for p in principals if p["name"] == WATCHDOG_PRINCIPAL), None)

    client_secret = None
    if existing:
        print(f"  ✅ principal exists: {WATCHDOG_PRINCIPAL}")
        client_id = existing.get("clientId", WATCHDOG_PRINCIPAL)
    else:
        r = create_principal(name=WATCHDOG_PRINCIPAL, token=tok)
        assert r.status_code in (200, 201), f"create_principal failed: {r.status_code} {r.text}"
        body = r.json()
        client_id = body.get("principal", {}).get("clientId", WATCHDOG_PRINCIPAL)
        client_secret = body.get("credentials", {}).get("clientSecret")
        print(f"  ✅ principal created: {WATCHDOG_PRINCIPAL}")
        print(f"     clientId:     {client_id}")
        print(f"     clientSecret: {client_secret}")
        print("     ⚠️  Save this secret — Polaris will not show it again.")

    # 2. Principal role
    pr_list = requests.get(f"{BASE_MGMT}/principal-roles", headers=h(tok)).json().get("roles", [])
    if any(pr["name"] == WATCHDOG_PR for pr in pr_list):
        print(f"  ✅ principal role exists: {WATCHDOG_PR}")
    else:
        r = create_principal_role(name=WATCHDOG_PR, token=tok)
        assert r.status_code in (200, 201), f"create_principal_role failed: {r.status_code} {r.text}"
        print(f"  ✅ principal role created: {WATCHDOG_PR}")

    # 3. Assign principal role to principal (idempotent — PUT is safe to repeat)
    r = assign_principal_role_to_principal(principal=WATCHDOG_PRINCIPAL, pr=WATCHDOG_PR, token=tok)
    print(f"  ✅ principal role assigned ({r.status_code})")

    # 4. Catalog
    catalogs = requests.get(f"{BASE_MGMT}/catalogs", headers=h(tok)).json().get("catalogs", [])
    if any(c["name"] == WATCHDOG_CATALOG for c in catalogs):
        print(f"  ✅ catalog exists: {WATCHDOG_CATALOG}")
    else:
        r = create_catalog(name=WATCHDOG_CATALOG, token=tok)
        assert r.status_code in (200, 201), f"create_catalog failed: {r.status_code} {r.text}"
        print(f"  ✅ catalog created: {WATCHDOG_CATALOG}")

    # 5. Catalog role
    cr_list = requests.get(f"{BASE_MGMT}/catalogs/{WATCHDOG_CATALOG}/catalog-roles", headers=h(tok)).json().get("roles", [])
    if any(cr["name"] == WATCHDOG_CR for cr in cr_list):
        print(f"  ✅ catalog role exists: {WATCHDOG_CR}")
    else:
        r = create_catalog_role(catalog=WATCHDOG_CATALOG, name=WATCHDOG_CR, token=tok)
        assert r.status_code in (200, 201), f"create_catalog_role failed: {r.status_code} {r.text}"
        print(f"  ✅ catalog role created: {WATCHDOG_CR}")

    # 6. Grant + assign (idempotent — safe to repeat)
    grant_privilege(catalog=WATCHDOG_CATALOG, cr=WATCHDOG_CR,
                     privilege="CATALOG_MANAGE_CONTENT", token=tok)
    assign_catalog_role_to_principal_role(catalog=WATCHDOG_CATALOG, pr=WATCHDOG_PR, cr=WATCHDOG_CR, token=tok)
    print(f"  ✅ grants verified")

    print("🔧 Watchdog setup complete (realm: POLARIS)\n")
    return client_id, client_secret

def get_watchdog_token(client_secret):
    """
    Acquire a token for the watchdog principal using the default POLARIS realm.
    client_secret must be the value saved from ensure_watchdog_setup()'s
    first run (or wherever it's stored — e.g. K8s secret).
    """
    r = get_token(client_id=WATCHDOG_PRINCIPAL, client_secret=client_secret, realm=REALM)
    assert r.status_code == 200, f"Watchdog token failed: {r.status_code} {r.text}"
    return r.json()["access_token"]

# ── Management API helpers ────────────────────────────────────
def create_catalog(name=TEST_CATALOG, token=None):
    return requests.post(f"{BASE_MGMT}/catalogs", headers=h(token), json={
        "catalog": {
            "name": name,
            "type": "INTERNAL",
            "properties": {
                "default-base-location": f"s3a://data-catalog-bucket/{name}/",
                "polaris.config.drop-with-purge.enabled": "true",
            },
            "storageConfigInfo": {
                "storageType": "S3",
                "allowedLocations": ["s3a://data-catalog-bucket/"],
                "pathStyleAccess": True,
                "endpoint": "http://192.168.139.2:9000",
                "endpointInternal": "http://benchmarks-minio.datahub-hynix.svc.cluster.local:9000",
            },
        }
    })

def create_catalog_no_endpoint(name=TEST_CATALOG, token=None):
    return requests.post(f"{BASE_MGMT}/catalogs", headers=h(token), json={
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
    })

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
    return requests.post(f"{BASE_MGMT}/principals", headers=h(token), json={
        "principal": {"name": name, "type": "SERVICE"},
        "credentialRotationRequired": False,
    })

def delete_principal(name=TEST_PRINCIPAL, token=None):
    return requests.delete(f"{BASE_MGMT}/principals/{name}", headers=h(token))

def create_principal_role(name=TEST_PR, token=None):
    return requests.post(f"{BASE_MGMT}/principal-roles", headers=h(token),
        json={"principalRole": {"name": name}})

def delete_principal_role(name=TEST_PR, token=None):
    return requests.delete(f"{BASE_MGMT}/principal-roles/{name}", headers=h(token))

def create_catalog_role(catalog=TEST_CATALOG, name=TEST_CR, token=None):
    return requests.post(
        f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles",
        headers=h(token),
        json={"catalogRole": {"name": name}},
    )

def assign_catalog_role_to_principal_role(catalog=TEST_CATALOG, pr=TEST_PR, cr=TEST_CR, token=None):
    return requests.put(
        f"{BASE_MGMT}/principal-roles/{pr}/catalog-roles/{catalog}",
        headers=h(token),
        json={"catalogRole": {"name": cr}},
    )

def assign_principal_role_to_principal(principal=TEST_PRINCIPAL, pr=TEST_PR, token=None):
    return requests.put(
        f"{BASE_MGMT}/principals/{principal}/principal-roles",
        headers=h(token),
        json={"principalRole": {"name": pr}},
    )

def grant_privilege(catalog=TEST_CATALOG, cr=TEST_CR,
                    privilege="CATALOG_MANAGE_CONTENT", token=None):
    return requests.put(
        f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles/{cr}/grants",
        headers=h(token),
        json={"grant": {"type": "catalog", "privilege": privilege}},
    )

# ── Cleanup ───────────────────────────────────────────────────
# System entities — never delete
_SKIP_PRINCIPALS      = {'root'}
_SKIP_PRINCIPAL_ROLES = {'service_admin'}
_SKIP_CATALOG_ROLES   = {'catalog_admin'}

def _delete(url, tok, label):
    """Delete a resource, print result."""
    r = requests.delete(url, headers=h(tok))
    icon = '✅' if r.status_code in [200, 204] else '⚠️ '
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
    catalogs = requests.get(
        f"{BASE_MGMT}/catalogs", headers=h(tok)
    ).json().get("catalogs", [])

    principals = requests.get(
        f"{BASE_MGMT}/principals", headers=h(tok)
    ).json().get("principals", [])

    principal_roles = requests.get(
        f"{BASE_MGMT}/principal-roles", headers=h(tok)
    ).json().get("roles", [])

    # ── Step 1+2: Tables + Views + Namespaces (recursive) ───────
    def _ns_to_url(ns):
        """Convert namespace list to URL-safe string."""
        if isinstance(ns, list):
            return '%1F'.join(ns)
        return ns

    def _ns_to_label(ns):
        """Convert namespace list to readable string."""
        if isinstance(ns, list):
            return '.'.join(ns)
        return ns

    def _delete_ns(cname, ns_url, ns_label, tok):
        """Recursively delete child namespaces, tables, views, then namespace."""
        # Get children of this namespace
        child_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces",
            headers=h(tok),
            params={"parent": ns_label}
        )
        for child in child_r.json().get("namespaces", []):
            _delete_ns(cname, _ns_to_url(child), _ns_to_label(child), tok)

        # Delete tables in this namespace
        t_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}/tables",
            headers=h(tok)
        )
        for t in t_r.json().get("identifiers", []):
            tname = t.get("name", str(t))
            _delete(
                f"{BASE_CAT}/{cname}/namespaces/{ns_url}/tables/{tname}",
                tok, f"table: {cname}.{ns_label}.{tname}"
            )

        # Delete views in this namespace
        v_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}/views",
            headers=h(tok)
        )
        for v in v_r.json().get("identifiers", []):
            vname = v.get("name", str(v))
            _delete(
                f"{BASE_CAT}/{cname}/namespaces/{ns_url}/views/{vname}",
                tok, f"view: {cname}.{ns_label}.{vname}"
            )

        # Delete namespace itself (now empty)
        _delete(
            f"{BASE_CAT}/{cname}/namespaces/{ns_url}",
            tok, f"namespace: {cname}.{ns_label}"
        )

    # Process all top-level namespaces recursively
    for c in catalogs:
        cname = c["name"]
        ns_r = requests.get(
            f"{BASE_CAT}/{cname}/namespaces", headers=h(tok)
        )
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
                tok, f"catalog-role: {cname}/{crname}"
            )

    # ── Step 4: Catalogs ──────────────────────────────────────
    for c in catalogs:
        cname = c["name"]
        _delete(
            f"{BASE_MGMT}/catalogs/{cname}",
            tok, f"catalog: {cname}"
        )

    # ── Step 5: Principals ────────────────────────────────────
    for p in principals:
        pname = p["name"]
        if pname in _SKIP_PRINCIPALS:
            continue
        _delete(
            f"{BASE_MGMT}/principals/{pname}",
            tok, f"principal: {pname}"
        )

    # ── Step 6: Principal Roles ───────────────────────────────
    for pr in principal_roles:
        prname = pr["name"]
        if prname in _SKIP_PRINCIPAL_ROLES:
            continue
        _delete(
            f"{BASE_MGMT}/principal-roles/{prname}",
            tok, f"principal-role: {prname}"
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

def search_logs(request_id=None, level=None, message=None,
                minutes_ago=10, size=20):
    """Search Polaris logs in OpenSearch."""
    client = os_client()
    must = [
        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
        # Only Polaris container logs
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}}
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
            "size": size
        },
    )
    return result["hits"]["hits"]

def search_logs_raw(query_dict, size=5):
    """Raw OpenSearch query for debugging."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={**query_dict, "size": size}
    )
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
                    "terms": {
                        "field": "kubernetes.container_name.keyword",
                        "size": 10
                    }
                }
            }
        }
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
                        {"match": {"kubernetes.pod_name": "polaris"}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 3
        }
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
        print(f"  container:  {src.get('kubernetes', {}).get('container_name', 'NOT FOUND')}")

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
        ts      = src.get("@timestamp", "")
        level   = src.get("level", "INFO")
        msg     = src.get("message", src.get("log", ""))
        mdc     = src.get("mdc", {})
        req_id  = mdc.get("requestId", "") if isinstance(mdc, dict) else ""
        realm   = mdc.get("realmId", "") if isinstance(mdc, dict) else ""
        logger  = src.get("loggerName", "")

        icon = {"ERROR": "❌", "WARN": "⚠️ ",
                "INFO": "ℹ️ ", "DEBUG": "🔍"}.get(level, "  ")
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        # HTTP access log shows 401 status
                        {"match": {"message": "\" 401"}},
                        # Auth failures
                        {"match": {"message": "Failed to resolve principal"}},
                        {"match": {"message": "unauthorized_client"}},
                        {"match": {"message": "getToken API with status code 401"}},
                        {"match": {"message": "not authorized"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "\" 403"}},
                        {"match": {"message": "ForbiddenException"}},
                        {"match": {"message": "lacks privilege"}},
                        {"match": {"message": "is not authorized"}},
                        {"match": {"message": "drop-with-purge"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "\" 404"}},
                        {"match": {"message": "not found"}},
                        {"match": {"message": "NoSuch"}},
                        {"match": {"message": "does not exist"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "\" 409"}},
                        {"match": {"message": "already exists"}},
                        {"match": {"message": "not empty"}},
                        {"match": {"message": "NamespaceNotEmpty"}},
                        {"match": {"message": "AlreadyExists"}},
                        {"match": {"message": "duplicate key"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "\" 400"}},
                        {"match": {"message": "Bad Request"}},
                        {"match": {"message": "validation"}},
                        {"match": {"message": "malformed"}},
                        {"match": {"message": "invalid"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "\" 500"}},
                        {"match": {"message": "NullPointerException"}},
                        {"match": {"message": "getRawLeafEntity"}},
                        {"match": {"message": "Internal Server Error"}},
                        {"match": {"message": "RuntimeException"}},
                        {"match": {"message": "duplicate key"}},
                        {"match": {"message": "grant_records_pkey"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
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
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                        {"terms": {"level.keyword": ["ERROR", "WARN"]}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 20
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "EntityVersionMismatch"}},
                        {"match": {"message": "entity_version"}},
                        {"match": {"message": "version mismatch"}},
                        {"match": {"message": "optimistic lock"}},
                        {"match": {"message": "concurrent modification"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
                        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
                    ],
                    "should": [
                        {"match": {"message": "has been blocked"}},
                        {"match": {"message": "BlockedThreadChecker"}},
                        {"match": {"loggerName": "io.vertx.core.impl.BlockedThreadChecker"}},
                        {"match": {"message": "Thread blocked"}},
                    ],
                    "minimum_should_match": 1
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "collapse": {"field": "sequence"},
            "size": 10
        }
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
        total  = len(self.results)
        passed = sum(1 for v in self.results.values() if v["passed"])
        failed = [k for k, v in self.results.items() if not v["passed"]]
        print(f"\n{'='*50}")
        print(f"Result: {passed}/{total} passed")
        if failed:
            print(f"Failed: {', '.join(failed)}")
        return passed == total

print("✅ Polaris test utils loaded")
print(f"   Polaris: {POLARIS_URL}  | Realm: {REALM}")
print(f"   OpenSearch: https://{OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
