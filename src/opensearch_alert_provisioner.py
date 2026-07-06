"""
OpenSearch Alerting provisioner — Database Connection Pool monitor.

Scope (per 2026-07-02 request): ONLY "Monitor 7 — Database Connection Pool
Unavailable" from error-cases/opensearch-monitor-alert-guide.md. This module
does not touch the other six monitors in that guide (Critical Errors / 401 /
403 / 404 / 409 / 400) — those stay manually-provisioned via the OpenSearch
Dashboards UI steps in the guide, unchanged.

Flow this automates (see the guide's "Automation" note under Monitor 7):
    1. Register OpenSearch Monitor + Trigger   <- this module
    2. Trigger fires -> Action posts to the notification channel/destination
    3. Destination -> company Kafka REST proxy -> SMS + Messenger

Reuses the OpenSearch client + config already wired in polaris_test_utils
(os_client(), LOG_INDEX, POLARIS_CONTAINER) instead of re-deriving connection
details, per this repo's "Strict Logic Separation" convention. Call
polaris_test_utils.init_env(...) before using this module, same as every
other src module. LOG_INDEX/POLARIS_CONTAINER are read off the polaris_test_utils
module at call time (not imported by name), so a later init_env("dev") in the
same notebook is respected.

Request/response shapes below were checked against the OpenSearch Alerting
plugin REST API docs (docs.opensearch.org/1.3/observing-your-data/alerting/api/
and /triggers/, same API surface as the repo's OpenSearch 1.5.0), not guessed:
  - POST   /_plugins/_alerting/monitors                        create
  - PUT    /_plugins/_alerting/monitors/<id>                   update
  - GET    /_plugins/_alerting/monitors/_search                idempotency lookup
  - POST   /_plugins/_alerting/monitors/<id>/_execute           run now
  - GET    /_plugins/_alerting/monitors/alerts?monitorIds=<id>  list alerts
  - GET    /_plugins/_alerting/destinations                    list destinations

Query + trigger design (revised 2026-07-03 per live-run feedback):

  1. TIGHTENED QUERY — the first version's `should` clauses were too broad
     (a bare `loggerName: io.agroal.pool` term matched *any* Agroal log line,
     and terms like "SQLException"/"pool exhausted"/"Unable to acquire" never
     actually appeared in two live runs). Rebuilt from the real captured
     output of error-cases/15 and /27: `loggerName: io.agroal.pool` is now a
     mandatory `must` clause (not one-of-several `should` options), scoping
     everything to Agroal specifically, combined with `match_phrase` (not
     `match`) on only the message substrings actually observed or documented:
     "connection refused" (Case A, live), "too many clients already"
     (Case B, live — the real Agroal message turned out to be the raw
     PostgreSQL FATAL string, not a generic Agroal timeout message as
     originally guessed), and "broken pipe" (documented failure mode for an
     established connection getting killed mid-request — not exercised by
     either live run, which both test *new* connection attempts failing, but
     kept since it's a distinct, real Agroal/TCP signature).

     Explicitly EXCLUDED: Vert.x `BlockedThreadChecker` "has been blocked"
     warnings (io.vertx.core.impl.BlockedThreadChecker). These *did* appear
     in the live NB15 run, but per 2026-07-03 direction they are not a
     "database unavailable" signal on their own — thread blocking can have
     other causes, and when a request fails this way the client already gets
     a failed response and can retry; it doesn't warrant a P0 page. Kept
     available via polaris_test_utils.search_blocked_thread_errors() as a
     manual diagnostic, just not wired into this monitor's query.

  2. RESOLVED NOTIFICATION — OpenSearch Alerting has no native "notify when
     resolved" action for query-level monitors (confirmed against the 1.3/
     latest docs: actions fire on every execution where the trigger condition
     is true, rate-limited only by `throttle`; there is no built-in
     de-escalation action type, unlike bucket-level monitors' per-alert
     DEDUPED/NEW scoping). A naive second trigger with the negated condition
     (`hits.total.value == 0`) would fire on *every* healthy execution
     (spam), not just the recovery transition.

     Fix: the query uses a `date_range` aggregation with two buckets —
     `current` (now-1m..now) and `previous` (now-2m..now-1m) — computed from
     one shared query, so both triggers read off the same input:
       - ALERT trigger    : current.doc_count > 0
       - RESOLVED trigger : current.doc_count == 0 AND previous.doc_count > 0
     RESOLVED is true for exactly one execution per bad->good transition
     (the first clean minute right after a bad one), then goes false again
     on the next clean minute since `previous` is clean too — no flip-flop,
     no persisted state needed, no spam.

NOT LIVE-VERIFIED: this sandbox cannot reach the OrbStack/company OpenSearch
host, so this module is static-verified only (imports cleanly, py_compile
clean, request bodies hand-checked against the docs above). Run it from a
notebook against a real cluster to confirm the monitor is actually created
and both triggers behave as designed.
"""

from __future__ import annotations

from typing import Optional

import polaris_test_utils as ptu

MONITOR_NAME = "Polaris DB Connection Pool Unavailable"
DESTINATION_NAME = "Polaris SMS Webhook"
ALERT_TRIGGER_NAME = "DB connection pool unavailable detected"
RESOLVED_TRIGGER_NAME = "DB connection pool RESOLVED"

# Tightened should-clauses — match_phrase on proven/documented substrings
# only. loggerName is enforced separately as a `must` (see build function),
# not included here as a should-option (that was the main source of
# over-broad matches in the first version).
_DB_POOL_SHOULD_CLAUSES = [
    {"match_phrase": {"message": "connection refused"}},
    {"match_phrase": {"message": "too many clients already"}},
    {"match_phrase": {"message": "broken pipe"}},
]


def _perform(method: str, path: str, body: Optional[dict] = None) -> dict:
    """Raw call into an OpenSearch plugin REST endpoint not wrapped by opensearch-py's high-level client."""
    client = ptu.os_client()
    return client.transport.perform_request(method, path, body=body)


def find_destination_id(name: str = DESTINATION_NAME) -> Optional[str]:
    """
    Look up an existing notification destination/channel by name.

    Returns None if it hasn't been created yet. This module intentionally
    does NOT create the destination itself: the webhook target is an
    internal-network Kafka REST proxy (guide Step 1) this sandbox can't
    reach to validate, and the real URL isn't finalized yet. Create the
    channel manually first via Alerting -> Notifications -> Create channel.
    """
    resp = _perform("GET", "/_plugins/_alerting/destinations")
    for dest in resp.get("destinations", []):
        if dest.get("name") == name:
            return dest["id"]
    return None


def find_monitor(name: str = MONITOR_NAME):
    """
    Idempotency lookup — find an existing monitor by name.
    Returns (monitor_id, seq_no, primary_term) or (None, None, None).
    """
    resp = _perform(
        "GET",
        "/_plugins/_alerting/monitors/_search",
        body={"query": {"match": {"monitor.name": name}}},
    )
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        return None, None, None
    hit = hits[0]
    return hit["_id"], hit.get("_seq_no"), hit.get("_primary_term")


def build_db_connection_pool_monitor(destination_id: str) -> dict:
    """
    Monitor + two triggers (ALERT, RESOLVED) + actions — mirrors Monitor 7
    in the guide doc exactly. See the module docstring for why there are two
    triggers sharing one date_range-aggregated query instead of a single
    hits.total.value check.
    """
    index = ptu.LOG_INDEX
    container = ptu.POLARIS_CONTAINER

    # Both templates reference ctx.results.0.hits.hits.0._source.* (the most
    # recent matching log line) so the engineer sees the ACTUAL detected
    # message in the notification itself — e.g. "Connection to ...:5432
    # refused" vs "FATAL: Sorry, too many clients already" — instead of just
    # a count, so they know immediately which failure mode this is without
    # having to go check OpenSearch. This is safe against the guide's
    # general "don't reference hits.hits.0._source without checking for
    # empty results first" caution: for THIS query, aggregations are
    # sub-filters over the SAME top-level hits (not a separate query), so
    # current.doc_count > 0 (ALERT's condition) and previous.doc_count > 0
    # (part of RESOLVED's condition) both guarantee hits.hits is non-empty
    # whenever the corresponding action actually fires.
    alert_message_body = (
        '{"value_schema_id": "225", "records": [{"value": {'
        '"noti_phone": "01012345678", '
        '"noti_title": "[POLARIS] \\ud83d\\udd34 DB Connection Pool Unavailable", '
        '"noti_content": "{{ctx.results.0.aggregations.current.doc_count}} DB '
        "connection pool errors in last 1 min. Detected: "
        "{{ctx.results.0.hits.hits.0._source.message}} (logger: "
        "{{ctx.results.0.hits.hits.0._source.loggerName}}). Check: kubectl "
        'get pods -n datahub-hynix | grep postgresql", '
        '"dt": "{{ctx.periodStart}}"'
        "}}]}"
    )
    resolved_message_body = (
        '{"value_schema_id": "225", "records": [{"value": {'
        '"noti_phone": "01012345678", '
        '"noti_title": "[POLARIS] \\u2705 DB Connection Pool Unavailable \\u2014 RESOLVED", '
        '"noti_content": "DB connection pool errors cleared. '
        "{{ctx.results.0.aggregations.previous.doc_count}} errors in the prior "
        "minute, 0 in the last minute. Last error before recovery: "
        '{{ctx.results.0.hits.hits.0._source.message}}", '
        '"dt": "{{ctx.periodStart}}"'
        "}}]}"
    )

    db_pool_filter = {
        "bool": {
            "must": [
                {"term": {"kubernetes.container_name.keyword": container}},
                {"term": {"loggerName.keyword": "io.agroal.pool"}},
                {
                    "bool": {
                        "should": _DB_POOL_SHOULD_CLAUSES,
                        "minimum_should_match": 1,
                    }
                },
            ]
        }
    }

    return {
        "type": "monitor",
        "name": MONITOR_NAME,
        "monitor_type": "query_level_monitor",
        "enabled": True,
        "schedule": {"period": {"interval": 1, "unit": "MINUTES"}},
        "inputs": [
            {
                "search": {
                    "indices": [index],
                    "query": {
                        "size": 3,
                        "query": {
                            "bool": {
                                "must": [
                                    {"range": {"@timestamp": {"gte": "now-2m"}}},
                                    db_pool_filter,
                                ]
                            }
                        },
                        "aggs": {
                            "current": {
                                "filter": {"range": {"@timestamp": {"gte": "now-1m"}}}
                            },
                            "previous": {
                                "filter": {
                                    "range": {
                                        "@timestamp": {
                                            "gte": "now-2m",
                                            "lt": "now-1m",
                                        }
                                    }
                                }
                            },
                        },
                        "_source": ["mdc.requestId", "level", "message", "loggerName"],
                        "sort": [{"@timestamp": {"order": "desc"}}],
                    },
                }
            }
        ],
        "triggers": [
            {
                "name": ALERT_TRIGGER_NAME,
                "severity": "1",
                "condition": {
                    "script": {
                        "source": "ctx.results[0].aggregations.current.doc_count > 0",
                        "lang": "painless",
                    }
                },
                "actions": [
                    {
                        "name": "Send SMS + Messenger",
                        "destination_id": destination_id,
                        "throttle_enabled": True,
                        "throttle": {"value": 30, "unit": "MINUTES"},
                        "subject_template": {
                            "source": "[POLARIS] DB Connection Pool Unavailable",
                            "lang": "mustache",
                        },
                        "message_template": {
                            "source": alert_message_body,
                            "lang": "mustache",
                        },
                    }
                ],
            },
            {
                "name": RESOLVED_TRIGGER_NAME,
                "severity": "3",
                "condition": {
                    "script": {
                        "source": (
                            "ctx.results[0].aggregations.current.doc_count == 0 "
                            "&& ctx.results[0].aggregations.previous.doc_count > 0"
                        ),
                        "lang": "painless",
                    }
                },
                "actions": [
                    {
                        "name": "Send SMS + Messenger (resolved)",
                        "destination_id": destination_id,
                        "throttle_enabled": True,
                        "throttle": {"value": 5, "unit": "MINUTES"},
                        "subject_template": {
                            "source": "[POLARIS] DB Connection Pool Unavailable — RESOLVED",
                            "lang": "mustache",
                        },
                        "message_template": {
                            "source": resolved_message_body,
                            "lang": "mustache",
                        },
                    }
                ],
            },
        ],
    }


def provision_db_connection_pool_monitor() -> str:
    """
    Create (or update, if it already exists) the DB connection pool monitor.
    Returns the monitor id.

    Raises RuntimeError if the notification destination hasn't been created
    yet — create "Polaris SMS Webhook" manually first (guide Step 1) before
    calling this.
    """
    destination_id = find_destination_id()
    if destination_id is None:
        raise RuntimeError(
            f'Notification destination "{DESTINATION_NAME}" not found. '
            "Create it manually first (guide Step 1, Alerting -> "
            "Notifications -> Create channel) before provisioning the "
            "monitor — this module intentionally does not create "
            "destinations pointed at the internal Kafka webhook."
        )

    body = build_db_connection_pool_monitor(destination_id)
    monitor_id, seq_no, primary_term = find_monitor()

    if monitor_id:
        params = ""
        if seq_no is not None and primary_term is not None:
            params = f"?if_seq_no={seq_no}&if_primary_term={primary_term}"
        resp = _perform(
            "PUT", f"/_plugins/_alerting/monitors/{monitor_id}{params}", body=body
        )
        print(f"Updated existing monitor: {monitor_id}")
        return resp.get("_id", monitor_id)

    resp = _perform("POST", "/_plugins/_alerting/monitors", body=body)
    new_id = resp["_id"]
    print(f"Created monitor: {new_id}")
    return new_id


def execute_monitor_now(monitor_id: str, dryrun: bool = False) -> dict:
    """
    Force the monitor to run immediately instead of waiting for its 1-minute
    schedule. Returns the response with a `trigger_results` dict keyed by
    trigger ID — each entry also carries a `name` field, so use
    trigger_fired() below to look results up by trigger name instead of ID
    (the ID isn't known until after the monitor is created).
    """
    path = f"/_plugins/_alerting/monitors/{monitor_id}/_execute"
    if dryrun:
        path += "?dryrun=true"
    return _perform("POST", path)


def trigger_fired(execute_result: dict, trigger_name: str) -> bool:
    """
    Given the response from execute_monitor_now(), check whether the named
    trigger (ALERT_TRIGGER_NAME or RESOLVED_TRIGGER_NAME) fired this run.
    trigger_results is keyed by trigger ID, not name, so this scans values.
    """
    trigger_results = execute_result.get("trigger_results", {})
    for result in trigger_results.values():
        if result.get("name") == trigger_name and result.get("triggered"):
            return True
    return False


def get_alerts_for_monitor(monitor_id: str, state: Optional[str] = None) -> list:
    """
    List alerts raised by this monitor. Pass state="ACTIVE" to filter to
    currently-firing alerts — this is what the error-case notebooks use to
    assert the trigger actually fired, not just that a matching log line
    exists in OpenSearch.
    """
    resp = _perform(
        "GET", f"/_plugins/_alerting/monitors/alerts?monitorIds={monitor_id}"
    )
    alerts = resp.get("alerts", [])
    if state:
        alerts = [a for a in alerts if a.get("state") == state]
    return alerts


def has_active_alert(monitor_id: str) -> bool:
    """True if the monitor currently has at least one ACTIVE alert."""
    return len(get_alerts_for_monitor(monitor_id, state="ACTIVE")) > 0


def matches_db_pool_signal(logger_name: str, message: str) -> bool:
    """
    Pure-Python mirror of the monitor's must-clauses (loggerName ==
    io.agroal.pool AND message contains one of _DB_POOL_SHOULD_CLAUSES'
    phrases), no OpenSearch call needed. For asserting, in a notebook, that
    a given captured log line would or would not satisfy Monitor 7's query
    — e.g. proving a Vert.x BlockedThreadChecker line does NOT match, per
    the 2026-07-03 exclusion decision (see module docstring).
    """
    if logger_name != "io.agroal.pool":
        return False
    phrases = [clause["match_phrase"]["message"] for clause in _DB_POOL_SHOULD_CLAUSES]
    return any(phrase in message for phrase in phrases)
