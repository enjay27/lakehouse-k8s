"""
Pytest regression suite for src/iceberg_rest.IcebergREST.

Mocks requests.get/post/head/delete — no live Polaris cluster required, so
this runs in CI / sandbox and on the live OrbStack host alike. Covers URL
construction (including the Iceberg `{prefix}` = catalog-name slot and the
\\x1f multi-level namespace joining), headers (including the opt-in
X-Iceberg-Access-Delegation), query params, and payload shape for every
method, plus the payload builders.

Mirrors the structure of test_polaris_rest.py.

Run: pytest test_iceberg_rest.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from iceberg_rest import (
    DELEGATION_VENDED_CREDENTIALS,  # noqa: E402
    IcebergREST,
    build_assert_table_uuid_requirement,
    build_create_table_payload,
    build_schema,
    build_set_properties_update,
)

BASE = "http://192.168.139.2:8181"
CAT_BASE = f"{BASE}/api/catalog/v1"
REALM = "POLARIS"
TOKEN = "tok-123"
CAT = "mycat"


@pytest.fixture
def calls():
    return []


@pytest.fixture
def ic(calls):
    """IcebergREST with every requests verb patched to record and return 200."""

    def fake_request(method):
        def _f(url, headers=None, json=None, data=None, params=None):
            calls.append(
                {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "data": data,
                    "params": params,
                }
            )
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            resp.json.return_value = {
                "defaults": {},
                "overrides": {},
                "namespaces": [],
                "identifiers": [],
            }
            resp.text = "{}"
            return resp

        return _f

    with patch("iceberg_rest.requests") as rq:
        rq.get.side_effect = fake_request("GET")
        rq.post.side_effect = fake_request("POST")
        rq.head.side_effect = fake_request("HEAD")
        rq.delete.side_effect = fake_request("DELETE")
        yield IcebergREST(BASE, REALM, token=TOKEN)


def last(calls):
    return calls[-1]


# ----------------------------------------------------------------------
# headers / helpers
# ----------------------------------------------------------------------
def test_headers_include_auth_realm_content_type(ic, calls):
    ic.get_config()
    h = last(calls)["headers"]
    assert h["Authorization"] == f"Bearer {TOKEN}"
    assert h["Polaris-Realm"] == REALM
    assert h["Content-Type"] == "application/json"
    assert "X-Iceberg-Access-Delegation" not in h


def test_per_call_token_override(ic, calls):
    ic.get_config(token="other-tok")
    assert last(calls)["headers"]["Authorization"] == "Bearer other-tok"


def test_missing_token_raises():
    client = IcebergREST(BASE, REALM)  # no token anywhere
    with pytest.raises(ValueError):
        client._h()


def test_delegation_header_opt_in(ic, calls):
    ic.load_table(CAT, "ns", "t", delegation=DELEGATION_VENDED_CREDENTIALS)
    assert last(calls)["headers"]["X-Iceberg-Access-Delegation"] == "vended-credentials"


def test_multi_level_namespace_joined_with_unit_separator(ic, calls):
    ic.load_namespace(CAT, ["a", "b", "c"])
    assert last(calls)["url"] == f"{CAT_BASE}/{CAT}/namespaces/a\x1fb\x1fc"


def test_bare_string_namespace_passes_through(ic, calls):
    ic.load_namespace(CAT, "solo")
    assert last(calls)["url"] == f"{CAT_BASE}/{CAT}/namespaces/solo"


# ----------------------------------------------------------------------
# config
# ----------------------------------------------------------------------
def test_get_config_no_warehouse(ic, calls):
    ic.get_config()
    c = last(calls)
    assert c["method"] == "GET" and c["url"] == f"{CAT_BASE}/config"
    assert c["params"] is None


def test_get_config_with_warehouse(ic, calls):
    ic.get_config(warehouse=CAT)
    assert last(calls)["params"] == {"warehouse": CAT}


# ----------------------------------------------------------------------
# namespaces
# ----------------------------------------------------------------------
def test_create_namespace_wraps_levels_in_list(ic, calls):
    ic.create_namespace(CAT, "ns", properties={"k": "v"})
    c = last(calls)
    assert c["method"] == "POST" and c["url"] == f"{CAT_BASE}/{CAT}/namespaces"
    assert c["json"] == {"namespace": ["ns"], "properties": {"k": "v"}}


def test_create_namespace_multilevel_and_default_properties(ic, calls):
    ic.create_namespace(CAT, ["a", "b"])
    assert last(calls)["json"] == {"namespace": ["a", "b"], "properties": {}}


def test_list_namespaces_params(ic, calls):
    ic.list_namespaces(CAT, parent=["a", "b"], page_token="pt", page_size=10)
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces"
    assert c["params"] == {"parent": "a\x1fb", "pageToken": "pt", "pageSize": 10}


def test_list_namespaces_omits_empty_params(ic, calls):
    ic.list_namespaces(CAT)
    assert last(calls)["params"] is None


def test_head_namespace_and_exists_wrapper(ic, calls):
    r = ic.head_namespace(CAT, "ns")
    c = last(calls)
    assert c["method"] == "HEAD" and c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns"
    assert r.status_code == 200
    assert ic.namespace_exists(CAT, "ns") is True


def test_update_namespace_properties_payload(ic, calls):
    ic.update_namespace_properties(CAT, "ns", updates={"a": "1"}, removals=["b"])
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/properties"
    assert c["json"] == {"updates": {"a": "1"}, "removals": ["b"]}


def test_update_namespace_properties_defaults(ic, calls):
    ic.update_namespace_properties(CAT, "ns")
    assert last(calls)["json"] == {"updates": {}, "removals": []}


def test_drop_namespace(ic, calls):
    ic.drop_namespace(CAT, "ns")
    c = last(calls)
    assert c["method"] == "DELETE" and c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns"


# ----------------------------------------------------------------------
# tables
# ----------------------------------------------------------------------
def test_list_tables_url_and_paging(ic, calls):
    ic.list_tables(CAT, "ns", page_size=5)
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables"
    assert c["params"] == {"pageSize": 5}


def test_create_table_passthrough_payload(ic, calls):
    payload = {"name": "t", "schema": {"type": "struct", "fields": []}}
    ic.create_table(CAT, "ns", payload)
    c = last(calls)
    assert c["method"] == "POST"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables"
    assert c["json"] == payload


def test_stage_create_sets_flag_without_mutating_caller_payload(ic, calls):
    payload = {"name": "t", "schema": {}}
    ic.stage_create_table(CAT, "ns", payload)
    assert last(calls)["json"]["stage-create"] is True
    assert "stage-create" not in payload  # caller's dict untouched


def test_register_table_payload(ic, calls):
    ic.register_table(CAT, "ns", "t", "s3://b/t/metadata/v1.metadata.json")
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/register"
    assert c["json"] == {
        "name": "t",
        "metadata-location": "s3://b/t/metadata/v1.metadata.json",
    }


def test_load_table_url_and_snapshots_param(ic, calls):
    ic.load_table(CAT, "ns", "t", snapshots="refs")
    c = last(calls)
    assert c["method"] == "GET"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables/t"
    assert c["params"] == {"snapshots": "refs"}


def test_load_table_omits_snapshots_when_unset(ic, calls):
    ic.load_table(CAT, "ns", "t")
    assert last(calls)["params"] is None


def test_head_table_and_exists_wrapper(ic, calls):
    ic.head_table(CAT, "ns", "t")
    c = last(calls)
    assert c["method"] == "HEAD"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables/t"
    assert c["json"] is None  # HEAD carries no body
    assert ic.table_exists(CAT, "ns", "t") is True


def test_commit_table_payload_shape(ic, calls):
    updates = [{"action": "set-properties", "updates": {"k": "v"}}]
    reqs = [{"type": "assert-table-uuid", "uuid": "u"}]
    ic.commit_table(CAT, "ns", "t", updates, requirements=reqs)
    c = last(calls)
    assert c["method"] == "POST"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables/t"
    assert c["json"] == {"requirements": reqs, "updates": updates}


def test_commit_table_defaults_requirements_to_empty(ic, calls):
    ic.commit_table(CAT, "ns", "t", [])
    assert last(calls)["json"]["requirements"] == []


def test_rename_table_is_catalog_scoped(ic, calls):
    ic.rename_table(CAT, "ns1", "old", ["ns2", "sub"], "new")
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/tables/rename"
    assert c["json"] == {
        "source": {"namespace": ["ns1"], "name": "old"},
        "destination": {"namespace": ["ns2", "sub"], "name": "new"},
    }


def test_drop_table_purge_param(ic, calls):
    ic.drop_table(CAT, "ns", "t", purge=True)
    c = last(calls)
    assert c["method"] == "DELETE"
    assert c["params"] == {"purgeRequested": "true"}


def test_drop_table_without_purge_sends_no_params(ic, calls):
    ic.drop_table(CAT, "ns", "t")
    assert last(calls)["params"] is None


def test_report_metrics(ic, calls):
    report = {"report-type": "scan-report", "table-name": "t"}
    ic.report_metrics(CAT, "ns", "t", report)
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/tables/t/metrics"
    assert c["json"] == report


# ----------------------------------------------------------------------
# views
# ----------------------------------------------------------------------
def test_list_views(ic, calls):
    ic.list_views(CAT, "ns")
    assert last(calls)["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/views"


def test_create_view_passthrough(ic, calls):
    payload = {"name": "v", "schema": {}}
    ic.create_view(CAT, "ns", payload)
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/views"
    assert c["json"] == payload


def test_load_view(ic, calls):
    ic.load_view(CAT, "ns", "v")
    c = last(calls)
    assert c["method"] == "GET"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/views/v"


def test_head_view_and_exists_wrapper(ic, calls):
    ic.head_view(CAT, "ns", "v")
    c = last(calls)
    assert c["method"] == "HEAD"
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/views/v"
    assert ic.view_exists(CAT, "ns", "v") is True


def test_commit_view_payload(ic, calls):
    ic.commit_view(CAT, "ns", "v", [{"action": "set-properties", "updates": {}}])
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/namespaces/ns/views/v"
    assert c["json"]["requirements"] == []


def test_rename_view_is_catalog_scoped(ic, calls):
    ic.rename_view(CAT, "ns1", "old", "ns2", "new")
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/views/rename"
    assert c["json"]["source"] == {"namespace": ["ns1"], "name": "old"}


def test_drop_view_purge_param(ic, calls):
    ic.drop_view(CAT, "ns", "v", purge=True)
    assert last(calls)["params"] == {"purgeRequested": "true"}


# ----------------------------------------------------------------------
# transactions
# ----------------------------------------------------------------------
def test_commit_transaction_payload(ic, calls):
    changes = [{"identifier": {"namespace": ["ns"], "name": "t"}, "updates": []}]
    ic.commit_transaction(CAT, changes)
    c = last(calls)
    assert c["url"] == f"{CAT_BASE}/{CAT}/transactions/commit"
    assert c["json"] == {"table-changes": changes}


# ----------------------------------------------------------------------
# payload builders
# ----------------------------------------------------------------------
def test_build_schema_shape():
    s = build_schema([(1, "id", "long", True), (2, "name", "string", False)])
    assert s["type"] == "struct" and s["schema-id"] == 0
    assert s["fields"][0] == {
        "id": 1,
        "name": "id",
        "required": True,
        "type": "long",
    }
    assert s["fields"][1]["required"] is False


def test_build_create_table_payload_minimal():
    p = build_create_table_payload("t", {"type": "struct", "fields": []})
    assert p == {"name": "t", "schema": {"type": "struct", "fields": []}}


def test_build_create_table_payload_full():
    p = build_create_table_payload(
        "t",
        {},
        location="s3://b/t",
        properties={"k": "v"},
        partition_spec={"fields": []},
        write_order={"fields": []},
        stage_create=True,
    )
    assert p["location"] == "s3://b/t"
    assert p["properties"] == {"k": "v"}
    assert p["partition-spec"] == {"fields": []}
    assert p["write-order"] == {"fields": []}
    assert p["stage-create"] is True


def test_build_update_and_requirement_helpers():
    assert build_set_properties_update({"a": "1"}) == {
        "action": "set-properties",
        "updates": {"a": "1"},
    }
    assert build_assert_table_uuid_requirement("u") == {
        "type": "assert-table-uuid",
        "uuid": "u",
    }


# ----------------------------------------------------------------------
# coverage guard — every public method must be exercised above
# ----------------------------------------------------------------------
def test_every_public_method_is_covered():
    """Fails when a method is added to IcebergREST without a test.

    Cheap insurance: this module is meant for company-wide reuse, so an
    untested method is a liability rather than a convenience.
    """
    public = {n for n in dir(IcebergREST) if not n.startswith("_")}
    source = Path(__file__).read_text()
    untested = {n for n in public if f"ic.{n}(" not in source}
    assert not untested, f"public methods with no test: {sorted(untested)}"
