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
FRONTEND_URL  = "http://localhost:32634"
NAMESPACE     = "datahub-hynix"

# ── Default credentials ───────────────────────────────────────
DEFAULT_USER  = "datahub"
DEFAULT_PASS  = "datahub"

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
def get_token(username=DEFAULT_USER, password=DEFAULT_PASS):
    """Get DataHub access token via login API."""
    r = requests.post(
        f"{FRONTEND_URL}/logIn",
        json={"username": username, "password": password},
    )
    return r

def get_access_token(username=DEFAULT_USER, password=DEFAULT_PASS):
    """Get DataHub personal access token."""
    token = get_token(username, password)
    assert token.status_code == 200, f"Login failed: {token.text}"
    session_cookie = token.cookies.get("actor")

    r = requests.post(
        f"{DATAHUB_URL}/api/v2/generateToken",
        headers={
            "Cookie": f"actor={session_cookie}",
            "Content-Type": "application/json",
        },
        json={
            "query": """
                mutation createAccessToken {
                    createAccessToken(input: {
                        type: PERSONAL,
                        actorUrn: "urn:li:corpuser:datahub",
                        duration: ONE_DAY,
                        name: "test-token"
                    }) {
                        accessToken
                    }
                }
            """
        }
    )
    return r

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