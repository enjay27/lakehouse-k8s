"""
Pytest regression suite for src/polaris_rest.PolarisREST.

Mocks requests.get/post/put/delete — no live Polaris cluster required, so
this runs in CI / sandbox and on the live OrbStack host alike. Covers URL
construction, headers, and payload shape for every method, plus the two
measured grant_privilege behaviors (skip-if-already-granted,
retry-through-404-read-after-write-lag) ported verbatim from
polaris_test_utils.grant_privilege.

Run: pytest test_polaris_rest.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from polaris_rest import PolarisREST

BASE = "http://192.168.139.2:8181"
REALM = "POLARIS"
TOKEN = "tok-123"


@pytest.fixture
def calls():
    return []


@pytest.fixture
def pc(calls):
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
            resp.json.return_value = {
                "grants": [],
                "catalogs": [],
                "principals": [],
                "roles": [],
                "namespaces": [],
                "identifiers": [],
            }
            resp.text = "{}"
            return resp

        return _f

    with (
        patch("requests.get", side_effect=fake_request("GET")),
        patch("requests.post", side_effect=fake_request("POST")),
        patch("requests.put", side_effect=fake_request("PUT")),
        patch("requests.delete", side_effect=fake_request("DELETE")),
    ):
        yield PolarisREST(BASE, REALM, token=TOKEN)


def test_headers_and_token_override(pc, calls):
    pc.list_catalogs()
    hdr = calls[-1]["headers"]
    assert hdr["Authorization"] == f"Bearer {TOKEN}"
    assert hdr["Polaris-Realm"] == REALM
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/catalogs"

    calls.clear()
    pc.list_catalogs(token="other-tok")
    assert calls[-1]["headers"]["Authorization"] == "Bearer other-tok"


def test_missing_token_raises():
    with pytest.raises(ValueError):
        PolarisREST(BASE, REALM).list_catalogs()


def test_get_token_oauth(pc, calls):
    pc.get_token("cid", "secret", scope="PRINCIPAL_ROLE:ALL")
    assert calls[-1]["url"] == f"{BASE}/api/catalog/v1/oauth/tokens"
    assert calls[-1]["data"]["client_id"] == "cid"
    assert calls[-1]["data"]["client_secret"] == "secret"


def test_create_catalog(pc, calls):
    pc.create_catalog("mycat", bucket="bkt", minio_endpoint="http://minio:9000")
    body = calls[-1]["json"]["catalog"]
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/catalogs"
    assert body["properties"]["default-base-location"] == "s3a://bkt/mycat/"
    assert body["storageConfigInfo"]["endpoint"] == "http://minio:9000"
    assert body["storageConfigInfo"]["endpointInternal"] == "http://minio:9000"


def test_get_catalog(pc, calls):
    pc.get_catalog("mycat")
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/catalogs/mycat"


def test_delete_catalog_purge_flag(pc, calls):
    pc.delete_catalog("mycat")
    assert "purgeRequested" not in calls[-1]["url"]
    calls.clear()
    pc.delete_catalog("mycat", purge=True)
    assert calls[-1]["url"].endswith("?purgeRequested=true")


def test_create_namespace_string_and_list(pc, calls):
    pc.create_namespace("mycat", "myns")
    assert calls[-1]["json"]["namespace"] == ["myns"]
    calls.clear()
    pc.create_namespace("mycat", ["a", "b"])
    assert calls[-1]["json"]["namespace"] == ["a", "b"]


def test_get_namespace(pc, calls):
    pc.get_namespace("mycat", ["a", "b"])
    assert calls[-1]["url"].endswith("namespaces/a\x1fb")
    assert calls[-1]["method"] == "GET"


def test_delete_namespace_joins_multilevel(pc, calls):
    pc.delete_namespace("mycat", ["a", "b"])
    assert calls[-1]["url"].endswith("namespaces/a\x1fb")


def test_list_namespaces_parent_param(pc, calls):
    pc.list_namespaces("mycat", parent=["a"])
    assert calls[-1]["params"] == {"parent": "a"}


def test_tables(pc, calls):
    pc.list_tables("mycat", "myns")
    assert calls[-1]["url"].endswith("namespaces/myns/tables")
    calls.clear()
    pc.load_table("mycat", "myns", "t1")
    assert calls[-1]["url"].endswith("namespaces/myns/tables/t1")
    calls.clear()
    pc.delete_table("mycat", "myns", "t1", purge=True)
    assert calls[-1]["url"].endswith("tables/t1?purgeRequested=true")


def test_views(pc, calls):
    pc.list_views("mycat", "myns")
    assert calls[-1]["url"].endswith("namespaces/myns/views")
    calls.clear()
    pc.delete_view("mycat", "myns", "v1")
    assert calls[-1]["url"].endswith("views/v1")


def test_create_table_passthrough(pc, calls):
    payload = {"name": "t1", "schema": {"type": "struct", "fields": []}}
    pc.create_table("mycat", "myns", payload)
    assert calls[-1]["url"].endswith("namespaces/myns/tables")
    assert calls[-1]["method"] == "POST"
    assert calls[-1]["json"] == payload  # body passed through unmodified


def test_create_view_passthrough(pc, calls):
    payload = {"name": "v1", "schema": {"type": "struct", "fields": []}}
    pc.create_view("mycat", "myns", payload)
    assert calls[-1]["url"].endswith("namespaces/myns/views")
    assert calls[-1]["method"] == "POST"
    assert calls[-1]["json"] == payload


def test_commit_table_body_shape(pc, calls):
    updates = [
        {
            "action": "set-snapshot-ref",
            "ref-name": "main",
            "type": "branch",
            "snapshot-id": 123,
        }
    ]
    pc.commit_table("mycat", "myns", "t1", updates)
    assert calls[-1]["url"].endswith("namespaces/myns/tables/t1")
    assert calls[-1]["json"] == {
        "identifier": {"namespace": ["myns"], "name": "t1"},
        "requirements": [],
        "updates": updates,
    }
    # multi-level namespace: identifier.namespace stays the full list, URL path uses \x1f
    calls.clear()
    pc.commit_table("mycat", ["a", "b"], "t1", updates)
    assert calls[-1]["url"].endswith("namespaces/a\x1fb/tables/t1")
    assert calls[-1]["json"]["identifier"]["namespace"] == ["a", "b"]

    calls.clear()
    reqs = [{"type": "assert-ref-snapshot-id", "ref": "main", "snapshot-id": 1}]
    pc.commit_table("mycat", "myns", "t1", updates, requirements=reqs)
    assert calls[-1]["json"]["requirements"] == reqs


def test_get_principal(pc, calls):
    pc.get_principal("worker1")
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/principals/worker1"
    assert calls[-1]["method"] == "GET"


def test_get_principal_role(pc, calls):
    pc.get_principal_role("worker1-role")
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/principal-roles/worker1-role"
    assert calls[-1]["method"] == "GET"


def test_principals_and_roles(pc, calls):
    pc.create_principal("worker1")
    assert calls[-1]["json"]["principal"] == {"name": "worker1", "type": "SERVICE"}

    calls.clear()
    pc.delete_principal("worker1")
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/principals/worker1"

    calls.clear()
    pc.create_principal_role("worker1-role")
    assert calls[-1]["json"] == {"principalRole": {"name": "worker1-role"}}

    calls.clear()
    pc.create_catalog_role("mycat", "worker1-cr")
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/catalogs/mycat/catalog-roles"

    calls.clear()
    pc.assign_catalog_role_to_principal_role("mycat", "worker1-role", "worker1-cr")
    assert calls[-1]["url"] == (
        f"{BASE}/api/management/v1/principal-roles/worker1-role/catalog-roles/mycat"
    )
    assert calls[-1]["json"] == {"catalogRole": {"name": "worker1-cr"}}

    calls.clear()
    pc.assign_principal_role_to_principal("worker1", "worker1-role")
    assert (
        calls[-1]["url"]
        == f"{BASE}/api/management/v1/principals/worker1/principal-roles"
    )


def test_reset_principal_credentials(pc, calls):
    pc.reset_principal_credentials("worker1")
    assert calls[-1]["method"] == "POST"
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/principals/worker1/reset"
    assert calls[-1]["json"] == {}


def test_rotate_credentials(pc, calls):
    pc.rotate_credentials("worker1")
    assert calls[-1]["method"] == "POST"
    assert calls[-1]["url"] == f"{BASE}/api/management/v1/principals/worker1/rotate"
    # self-service endpoint takes no body, just the caller's own token
    assert calls[-1]["json"] is None


def test_rotate_credentials_token_override(pc, calls):
    """rotate_credentials must be callable with a per-call token override
    (the target principal's own token), not just the client's default."""
    pc.rotate_credentials("worker1", token="worker1-own-token")
    assert calls[-1]["headers"]["Authorization"] == "Bearer worker1-own-token"


def test_list_principals_for_principal_role(pc, calls):
    pc.list_principals_for_principal_role("ops-admin")
    assert (
        calls[-1]["url"]
        == f"{BASE}/api/management/v1/principal-roles/ops-admin/principals"
    )
    assert calls[-1]["method"] == "GET"


def test_list_grants(pc, calls):
    pc.list_grants("mycat", "worker1-cr")
    assert calls[-1]["url"].endswith("catalog-roles/worker1-cr/grants")


def test_grant_privilege_issues_get_then_put(pc, calls):
    pc.grant_privilege("mycat", "worker1-cr", "TABLE_DROP")
    assert calls[0]["method"] == "GET"
    assert calls[1]["method"] == "PUT"
    assert calls[1]["json"] == {"grant": {"type": "catalog", "privilege": "TABLE_DROP"}}


def test_grant_privilege_skips_put_when_already_granted(pc):
    def fake_get_existing(url, headers=None, **kw):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "grants": [{"privilege": "TABLE_DROP", "type": "catalog"}]
        }
        return resp

    with (
        patch("requests.get", side_effect=fake_get_existing),
        patch("requests.put") as mock_put,
    ):
        pc.grant_privilege("mycat", "worker1-cr", "TABLE_DROP")
        assert not mock_put.called


def test_grant_privilege_retries_through_404_lag(pc):
    """Ports the measured PG-HA read-after-write-lag fix: a catalog-role
    created moments earlier can 404 on the grant PUT; grant_privilege must
    retry (capped) rather than misreport a valid grant as invalid."""
    attempt_state = {"n": 0}

    def fake_get_empty(url, headers=None, **kw):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"grants": []}
        return resp

    def fake_put_404_then_ok(url, headers=None, json=None, **kw):
        attempt_state["n"] += 1
        resp = MagicMock()
        if attempt_state["n"] < 3:
            resp.status_code = 404
            resp.text = "CatalogRole not found"
        else:
            resp.status_code = 200
            resp.text = "{}"
        return resp

    with (
        patch("requests.get", side_effect=fake_get_empty),
        patch("requests.put", side_effect=fake_put_404_then_ok),
        patch("time.sleep", return_value=None),
    ):
        r = pc.grant_privilege("mycat", "worker1-cr", "TABLE_DROP")
        assert attempt_state["n"] == 3
        assert r.status_code == 200


# ----------------------------------------------------------------------
# update_catalog — optimistic-concurrency property update
# ----------------------------------------------------------------------
def test_update_catalog_sends_version_and_properties(pc, calls):
    props = {"default-base-location": "s3a://b/c/", "k": "v"}
    pc.update_catalog("mycat", props, 7)
    c = calls[-1]
    assert c["method"] == "PUT"
    assert c["url"] == f"{BASE}/api/management/v1/catalogs/mycat"
    assert c["json"] == {"currentEntityVersion": 7, "properties": props}


def test_update_catalog_replaces_rather_than_merges(pc, calls):
    """The payload is sent verbatim — Polaris REPLACES the property map. Callers
    must merge themselves or they silently drop default-base-location and the
    storage config with it. This test pins that contract so nobody 'helpfully'
    adds a merge inside the client and changes the semantics."""
    pc.update_catalog("mycat", {"only": "this"}, 1)
    assert calls[-1]["json"]["properties"] == {"only": "this"}


def test_update_catalog_honours_per_call_token(pc, calls):
    pc.update_catalog("mycat", {}, 1, token="other-tok")
    assert calls[-1]["headers"]["Authorization"] == "Bearer other-tok"


# ----------------------------------------------------------------------
# revoke_privilege — note the method
# ----------------------------------------------------------------------
def test_revoke_privilege_posts_to_the_grants_url(pc, calls):
    """POST, not DELETE.

    Revocation reuses the grant URL and the grant body, and the obvious guess
    — DELETE — returns 405. Verified against `revokeGrantFromCatalogRole` in
    spec/polaris-management-service.yml at tag
    apache-polaris-1.3.0-incubating. This test exists so nobody "fixes" it into
    a DELETE on the reasonable-sounding grounds that revoking is a deletion.
    """
    pc.revoke_privilege("mycat", "myrole", "TABLE_DROP")
    c = calls[-1]
    assert c["method"] == "POST"
    assert c["url"] == (
        f"{BASE}/api/management/v1/catalogs/mycat/catalog-roles/myrole/grants"
    )
    assert c["json"] == {"grant": {"type": "catalog", "privilege": "TABLE_DROP"}}


def test_revoke_privilege_defaults_cascade_off(pc, calls):
    """Polaris's own default, and the safe one: a cascade can remove grants
    this call never named."""
    pc.revoke_privilege("mycat", "myrole", "TABLE_DROP")
    assert calls[-1]["params"] == {"cascade": "false"}
    calls.clear()
    pc.revoke_privilege("mycat", "myrole", "TABLE_DROP", cascade=True)
    assert calls[-1]["params"] == {"cascade": "true"}


def test_revoke_privilege_honours_per_call_token(pc, calls):
    pc.revoke_privilege("mycat", "myrole", "TABLE_DROP", token="other-tok")
    assert calls[-1]["headers"]["Authorization"] == "Bearer other-tok"


def test_revoke_privilege_returns_the_response_rather_than_interpreting_it(pc):
    """A 404 means "already absent" — success for an idempotent teardown, a
    real error for a caller that expected to find the grant. Only the caller
    knows which, so the status is handed back untouched and nothing raises."""
    with patch("requests.post") as post:
        post.return_value = MagicMock(status_code=404, text="not found")
        r = pc.revoke_privilege("mycat", "myrole", "TABLE_DROP")
    assert r.status_code == 404
