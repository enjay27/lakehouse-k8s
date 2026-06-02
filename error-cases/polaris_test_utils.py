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
def cleanup(token=None):
    tok = token or root_token()
    print("🧹 Cleaning up test resources...")
    requests.delete(
        f"{BASE_CAT}/{TEST_CATALOG}/namespaces/{TEST_NAMESPACE}",
        headers=h(tok))
    requests.delete(
        f"{BASE_MGMT}/principal-roles/{TEST_PR}/catalog-roles/{TEST_CATALOG}",
        headers=h(tok))
    requests.delete(
        f"{BASE_MGMT}/catalogs/{TEST_CATALOG}/catalog-roles/{TEST_CR}",
        headers=h(tok))
    requests.delete(
        f"{BASE_MGMT}/principals/{TEST_PRINCIPAL}/principal-roles",
        headers=h(tok))
    requests.delete(f"{BASE_MGMT}/principals/{TEST_PRINCIPAL}", headers=h(tok))
    requests.delete(f"{BASE_MGMT}/principal-roles/{TEST_PR}", headers=h(tok))
    requests.delete(f"{BASE_MGMT}/catalogs/{TEST_CATALOG}", headers=h(tok))
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

def search_401_errors(minutes_ago=5):
    """Find all 401 unauthorized errors — general pattern."""
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


def search_403_errors(minutes_ago=5):
    """Find all 403 forbidden errors — general pattern."""
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
                        {"match": {"message": "not authorized"}},
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


def search_409_errors(minutes_ago=5):
    """Find all 409 conflict errors — general pattern."""
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


def search_500_errors(minutes_ago=5):
    """Find all 500 internal server errors — general pattern."""
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


def search_all_errors(minutes_ago=5):
    """Find ALL errors across all error types."""
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