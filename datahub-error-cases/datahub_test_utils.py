# ============================================================
# DataHub Test Utilities
# GMS: http://192.168.139.2:8080
# ============================================================

import requests
import json
import time
import subprocess

# ── Connection ───────────────────────────────────────────────
DATAHUB_URL   = "http://192.168.139.2:8080"
FRONTEND_URL  = "http://192.168.139.2:9002"
DATAHUB_ES    = "http://192.168.139.2:9200"   # opensearch-cluster-master-lb
NAMESPACE     = "datahub-hynix"

# ── Default credentials ───────────────────────────────────────
DEFAULT_USER  = "datahub"
DEFAULT_PASS  = "datahub"

# ── DataHub internal Elasticsearch ───────────────────────────
# DataHub uses opensearch-cluster-master via LoadBalancer
# DATAHUB_ES defined above in Connection section

def datahub_es_indices():
    """List DataHub Elasticsearch indices."""
    r = requests.get(f"{DATAHUB_ES}/_cat/indices?h=index,health,status,docs.count&s=index")
    return r.text

def datahub_es_health():
    """Check DataHub Elasticsearch cluster health."""
    r = requests.get(f"{DATAHUB_ES}/_cluster/health")
    return r.json()

# ── OpenSearch ────────────────────────────────────────────────
import opensearchpy
from opensearchpy import OpenSearch

OS_HOST   = "192.168.194.1"
OS_PORT   = 9200
OS_USER   = "admin"
OS_PASS   = "Str0ngP@ssw0rd123!"
LOG_INDEX = "k8s-logs-*"

def os_client():
    return OpenSearch(
        hosts=[{"host": OS_HOST, "port": OS_PORT}],
        http_auth=(OS_USER, OS_PASS),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )

# ── Auth ──────────────────────────────────────────────────────
def get_session(username=DEFAULT_USER, password=DEFAULT_PASS):
    """
    Login via frontend and return a requests.Session with cookies set.
    Use this session for all subsequent API calls.
    """
    session = requests.Session()
    r = session.post(
        f"{FRONTEND_URL}/logIn",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return session

def get_token(username=DEFAULT_USER, password=DEFAULT_PASS):
    """Login via frontend — returns raw response (for status check)."""
    return requests.post(
        f"{FRONTEND_URL}/logIn",
        json={"username": username, "password": password},
    )

def graphql(query, variables=None, session=None):
    """
    Execute GraphQL via frontend proxy.
    Requires session from get_session().
    """
    if session is None:
        session = get_session()
    r = session.post(
        f"{FRONTEND_URL}/api/v2/graphql",
        headers={"Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
    )
    return r

def get_access_token(username=DEFAULT_USER, password=DEFAULT_PASS):
    """
    Get DataHub personal access token (Bearer) via frontend login.
    Returns: access token string or None on failure.
    """
    # Step 1: Login via frontend → get session cookie
    r_login = get_token(username, password)
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    session_cookie = r_login.cookies.get("actor")
    assert session_cookie, "No actor cookie in login response"

    # Step 2: Generate personal access token via frontend GraphQL
    r = requests.post(
        f"{FRONTEND_URL}/api/v2/graphql",
        headers={
            "Cookie": f"actor={session_cookie}",
            "Content-Type": "application/json",
            "X-RestLi-Protocol-Version": "2.0.0",
        },
        json={
            "query": """
                mutation {
                    createAccessToken(input: {
                        type: PERSONAL,
                        actorUrn: "urn:li:corpuser:datahub",
                        duration: ONE_DAY,
                        name: "notebook-test-token"
                    }) {
                        accessToken
                    }
                }
            """
        }
    )
    if r.status_code == 200:
        data = r.json()
        token = data.get("data", {}).get("createAccessToken", {}).get("accessToken")
        if token:
            return token
    # Fallback: use session cookie directly on GMS
    return session_cookie

def gms_headers(token):
    """Return GMS API headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def frontend_headers(username=DEFAULT_USER, password=DEFAULT_PASS):
    """Return frontend session headers (cookie-based)."""
    r_login = get_token(username, password)
    assert r_login.status_code == 200
    session_cookie = r_login.cookies.get("actor")
    return {
        "Cookie": f"actor={session_cookie}",
        "Content-Type": "application/json",
    }

def auth_headers(token):
    """Return headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

# ── GraphQL helper ────────────────────────────────────────────
def gql(query, variables=None, token=None):
    """Execute a GraphQL query against DataHub GMS."""
    headers = auth_headers(token) if token else {}
    r = requests.post(
        f"{DATAHUB_URL}/api/graphql",
        headers=headers,
        json={"query": query, "variables": variables or {}},
    )
    return r

# ── Health check ──────────────────────────────────────────────
def health_check():
    """Check DataHub GMS health. Endpoint: /health"""
    return requests.get(f"{DATAHUB_URL}/health", timeout=5)

# ── OpenSearch search functions ───────────────────────────────
def wait_for_logs(seconds=10):
    print(f"⏳ Waiting {seconds}s for logs to reach OpenSearch...")
    time.sleep(seconds)

def print_logs(hits):
    if not hits:
        print("❌ No logs found")
        return
    print(f"✅ Found {len(hits)} log entries:\n")
    for h in hits:
        s = h["_source"]
        ts  = s.get("@timestamp", "")[:19]
        lvl = s.get("level", "?")
        lgr = s.get("logger", s.get("loggerName", "?"))
        msg = s.get("message", "")[:120]
        ctr = s.get("kubernetes", {}).get("container_name", "?")
        print(f"  [{ts}] {lvl:5} | {ctr} | {lgr}")
        print(f"         {msg}")
        print()

def search_datahub_errors(minutes_ago=2, container="datahub-gms"):
    """Find all ERROR/WARN logs from DataHub container."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"term": {"kubernetes.container_name.keyword": container}},
                        {"terms": {"level.keyword": ["ERROR", "WARN"]}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 10,
        }
    )
    return result["hits"]["hits"]

def search_datahub_auth_errors(minutes_ago=2):
    """Find DataHub auth failure logs."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"term": {"kubernetes.container_name.keyword": "datahub-gms"}},
                    ],
                    "should": [
                        {"match": {"message": "Failed to authenticate"}},
                        {"match": {"message": "invalid token"}},
                        {"match": {"message": "Unauthorized"}},
                        {"match": {"message": "expired"}},
                        {"match": {"message": "authentication"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 10,
        }
    )
    return result["hits"]["hits"]

def search_datahub_kafka_errors(minutes_ago=5):
    """Find DataHub Kafka consumer errors."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"bool": {
                            "should": [
                                {"term": {"kubernetes.container_name.keyword": "datahub-mae-consumer"}},
                                {"term": {"kubernetes.container_name.keyword": "datahub-mce-consumer"}},
                            ],
                            "minimum_should_match": 1,
                        }},
                        {"term": {"level.keyword": "ERROR"}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 10,
        }
    )
    return result["hits"]["hits"]

def search_datahub_ingestion_errors(minutes_ago=5):
    """Find DataHub ingestion failure logs."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"term": {"kubernetes.container_name.keyword": "datahub-gms"}},
                        {"term": {"level.keyword": "ERROR"}},
                    ],
                    "should": [
                        {"match": {"message": "ingestion"}},
                        {"match": {"message": "Ingestion"}},
                        {"match": {"message": "recipe"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 10,
        }
    )
    return result["hits"]["hits"]

def search_datahub_all_errors(minutes_ago=2):
    """Find ALL DataHub errors across all components."""
    client = os_client()
    result = client.search(
        index=LOG_INDEX,
        body={
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{minutes_ago}m"}}},
                        {"bool": {
                            "should": [
                                {"term": {"kubernetes.container_name.keyword": "datahub-gms"}},
                                {"term": {"kubernetes.container_name.keyword": "datahub-mae-consumer"}},
                                {"term": {"kubernetes.container_name.keyword": "datahub-mce-consumer"}},
                            ],
                            "minimum_should_match": 1,
                        }},
                        {"terms": {"level.keyword": ["ERROR", "WARN"]}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 20,
        }
    )
    return result["hits"]["hits"]

def kubectl(cmd):
    """Run kubectl command and return output."""
    result = subprocess.run(
        f"kubectl {cmd}",
        shell=True, capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    return result

def gms_pod():
    """Get current GMS pod name."""
    result = subprocess.run(
        "kubectl get pods -n datahub-hynix | grep datahub-gms | grep Running | awk '{print $1}'",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip()

print("✅ DataHub test utils loaded")
print(f"   GMS: {DATAHUB_URL}")
print(f"   OpenSearch: https://{OS_HOST}:{OS_PORT}")