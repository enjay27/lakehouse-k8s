"""The audit policy in charts/polaris/files/log-batch/polaris_log_batch.py (P1b).

A port of releases/fluent-bit/polaris_access_log.lua (policy v5) to a batch over one KST hour.
Each test writes real-shaped Polaris JSON lines (Quarkus access-log messages, allow-listed and
other application loggers, mdc.requestId) into a pod's current file, runs the job, and reads the
processed and aggregated files back.
"""

import datetime as dt
import io
import json
import os
import pathlib
import sys

sys.path.insert(
    0,
    str(
        pathlib.Path(__file__).resolve().parent.parent
        / "charts/polaris/files/log-batch"
    ),
)
import polaris_log_batch as plb  # noqa: E402

KST = plb.KST
POD = "benchmarks-polaris-7f4d69c67c-aaaaa"
ACCESS = plb.ACCESS_LOGGER
MAPPER = "org.apache.polaris.service.exception.IcebergExceptionMapper"
ADMIN = "org.apache.polaris.service.admin.PolarisServiceImpl"
CAT = "/api/catalog/v1/cat"
MGMT = "/api/management/v1"


def stamp(when, ms=0):
    t = dt.datetime.fromisoformat(when)
    return f"{t:%Y-%m-%dT%H:%M:%S}.{ms:03d}000000+09:00"


def rec(when, logger, message, ms=0, level="INFO", rid=None, **extra):
    r = {
        "timestamp": stamp(when, ms),
        "sequence": 1,
        "loggerClassName": "org.jboss.logging.Logger",
        "loggerName": logger,
        "level": level,
        "message": message,
        "threadName": "executor-thread-1",
        "threadId": 42,
        "hostName": POD,
        "processName": "quarkus-run.jar",
        "processId": 1,
        "ndc": "",
    }
    if rid:
        r["mdc"] = {"requestId": rid}
    r.update(extra)
    return json.dumps(r)


def acc(when, method, path, status, size=10, user="root", ms=0, rid=None, level="INFO"):
    msg = f'10.0.0.7 - {user} [28/Sep/2026:10:00:00 +0900] "{method} {path} HTTP/1.1" {status} {size}'
    return rec(when, ACCESS, msg, ms=ms, rid=rid, level=level)


def app(when, logger, message, ms=0, rid=None, level="INFO"):
    return rec(when, logger, message, ms=ms, rid=rid, level=level)


def drive(tmp_path, lines, now="2026-09-28 11:03:00", mtime=None, **kw):
    path = tmp_path / f"polaris-{POD}.log"
    path.write_text("".join(x + "\n" for x in lines))
    t = (
        dt.datetime.fromisoformat(mtime or "2026-09-28 10:59:00")
        .replace(tzinfo=KST)
        .timestamp()
    )
    os.utime(path, (t, t))
    c = plb.Config(str(tmp_path), pod_lister=lambda: {POD}, **kw)
    plb.run(
        c, now=dt.datetime.fromisoformat(now).replace(tzinfo=KST), out=io.StringIO()
    )


def processed(tmp_path, key="20260928-10"):
    p = tmp_path / "processed-logs" / f"{key}.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()]


def report(tmp_path, key="20260928-10"):
    rows = [
        json.loads(x)
        for x in (tmp_path / "aggregated-logs" / f"{key}.jsonl")
        .read_text()
        .splitlines()
    ]
    s = rows[0]
    assert s["report_type"] == "summary" and s["schema_version"] == 7
    res = {r["resource"]: r for r in rows if r["report_type"] == "resource"}
    pri = {r["user_principal_name"]: r for r in rows if r["report_type"] == "principal"}
    drop = {r["logger_name"]: r for r in rows if r["report_type"] == "app_dropped"}
    return s, res, pri, drop


# ------------------------------------------------------------------ rules 1-7


def test_access_rules_keep_writes_and_failures_count_reads_and_catalog_posts(tmp_path):
    T = "2026-09-28 10:10:00"
    drive(
        tmp_path,
        [
            acc(T, "GET", f"{CAT}/namespaces/ns/tables/t", 200, 900, ms=1),  # 6 counted
            acc(
                T, "GET", f"{CAT}/namespaces/ns/tables/t/metrics", 200, 5, ms=2
            ),  # same row
            acc(
                T, "POST", f"{CAT}/namespaces/ns/tables/t", 200, 700, ms=3
            ),  # 5 catalog: counted
            acc(T, "POST", f"{MGMT}/principals", 201, 300, ms=4),  # 5 management: kept
            acc(T, "DELETE", f"{MGMT}/principals/p1", 204, 0, ms=5),  # 4 kept
            acc(
                T, "PUT", f"{MGMT}/catalogs/cat/catalog-roles/cr/grants", 201, 0, ms=6
            ),  # 4
            acc(T, "GET", f"{MGMT}/catalogs", 401, 50, user="-", ms=7),  # 3 kept
            acc(
                T, "GET", f"{CAT}/namespaces/ns/tables/missing", 404, 80, ms=8
            ),  # 3' counted
            acc(
                T, "GET", f"{CAT}/namespaces/ns/tables/t", 200, 900, ms=9, level="WARN"
            ),  # 1
            rec(
                T, ACCESS, "this is not the access-log pattern", ms=10
            ),  # parse error: kept
        ],
    )
    kept = processed(tmp_path)
    assert [d.get("http_method") for d in kept] == [
        "POST",
        "DELETE",
        "PUT",
        "GET",
        "GET",
        None,
    ]
    assert kept[-1]["access_log_parse_error"] is True
    assert kept[3]["http_status"] == 401 and kept[3]["user_principal_name"] == "-"
    s, res, pri, _ = report(tmp_path)
    assert (s["access_seen"], s["access_kept"], s["access_counted"]) == (9, 5, 4)
    assert (s["counted_read"], s["counted_post"], s["counted_404"]) == (2, 1, 1)
    assert (s["errors_kept"], s["parse_errors"], s["auth_denied"]) == (2, 1, 1)
    t = res[f"{CAT}/namespaces/ns/tables/t"]
    assert (t["requests"], t["reads"], t["writes"], t["resource_kind"]) == (
        3,
        2,
        1,
        "table",
    )
    assert t["last_read_bytes"] == 5 and t["last_write_bytes"] == 700
    role = res[f"{MGMT}/catalogs/cat/catalog-roles/cr"]
    assert role["resource_kind"] == "catalog-role" and role["writes"] == 1
    # the 404 and the 401 had no successful row to join this hour
    assert res["__errors__"]["requests"] == 2 and res["__errors__"]["auth_denied"] == 1
    assert set(pri) == {"root", "-"}
    assert s["lines_in"] == s["processed"] + s["dropped"] + s["malformed"]


def test_kept_documents_are_trimmed_like_tier_2_and_carry_an_event_id(tmp_path):
    drive(tmp_path, [acc("2026-09-28 10:10:00", "DELETE", f"{MGMT}/principals/p", 204)])
    (d,) = processed(tmp_path)
    for gone in ("processName", "loggerClassName", "processId", "ndc"):
        assert gone not in d
    for kept in ("timestamp", "threadName", "threadId", "hostName", "message"):
        assert kept in d
    assert len(d["event_id"]) == 40 and d["log_hour"] == "20260928-10"


# ------------------------------------------------------------------ allow-list and the request-id hold


def test_a_404_drops_its_request_s_app_lines_and_a_500_keeps_them(tmp_path):
    T = "2026-09-28 10:20:00"
    drive(
        tmp_path,
        [
            app(T, MAPPER, "Handling runtimeException NoSuchTable", ms=1, rid="r404"),
            acc(T, "GET", f"{CAT}/namespaces/ns/tables/x", 404, ms=5, rid="r404"),
            app(T, MAPPER, "Handling runtimeException boom", ms=10, rid="r500"),
            acc(T, "POST", f"{CAT}/namespaces/ns/tables", 500, ms=15, rid="r500"),
        ],
    )
    msgs = [d["message"] for d in processed(tmp_path)]
    assert "Handling runtimeException boom" in msgs
    assert "Handling runtimeException NoSuchTable" not in msgs
    s, *_ = report(tmp_path)
    assert (s["app_dropped_404"], s["counted_404"], s["errors_5xx"]) == (1, 1, 1)


def test_an_app_line_after_its_access_line_is_decided_by_it(tmp_path):
    T = "2026-09-28 10:20:00"
    drive(
        tmp_path,
        [
            acc(T, "GET", f"{CAT}/namespaces/ns/tables/x", 404, ms=5, rid="late"),
            app(T, ADMIN, "late reason", ms=9, rid="late"),
        ],
    )
    assert processed(tmp_path) == []
    assert report(tmp_path)[0]["app_dropped_404"] == 1


def test_an_allow_listed_line_without_its_access_line_is_kept_as_a_held_orphan(
    tmp_path,
):
    drive(
        tmp_path,
        [app("2026-09-28 10:30:00", ADMIN, "Granted X", rid="nobody-answered")],
    )
    (d,) = processed(tmp_path)
    assert d["held_orphan"] is True
    assert report(tmp_path)[0]["held_orphans"] == 1


def test_an_allow_listed_line_without_a_request_id_is_kept(tmp_path):
    drive(tmp_path, [app("2026-09-28 10:30:00", ADMIN, "no id")])
    (d,) = processed(tmp_path)
    assert "held_orphan" not in d


def test_the_request_id_match_crosses_the_hour_boundary(tmp_path):
    drive(
        tmp_path,
        [
            app(
                "2026-09-28 10:59:59", MAPPER, "reason at the edge", ms=995, rid="edge"
            ),
            acc(
                "2026-09-28 11:00:00",
                "GET",
                f"{CAT}/namespaces/ns/tables/x",
                404,
                ms=5,
                rid="edge",
            ),
        ],
        now="2026-09-28 12:03:00",
        mtime="2026-09-28 11:00:01",
    )
    assert processed(tmp_path, "20260928-10") == []
    assert report(tmp_path, "20260928-10")[0]["app_dropped_404"] == 1
    assert report(tmp_path, "20260928-11")[0]["counted_404"] == 1


def test_warn_and_error_are_always_kept_whatever_the_logger(tmp_path):
    drive(
        tmp_path, [app("2026-09-28 10:30:00", "some.Other", "disk full", level="ERROR")]
    )
    assert [d["message"] for d in processed(tmp_path)] == ["disk full"]


# ------------------------------------------------------------------ app_dropped and commits


def test_other_loggers_are_counted_per_logger_and_commits_harvested_first(tmp_path):
    T = "2026-09-28 10:40:00"
    drive(
        tmp_path,
        [
            app(
                T,
                plb.COMMIT_LOGGER,
                "Successfully committed to table cat.ns.t in 20 ms",
                ms=1,
            ),
            app(
                T,
                plb.COMMIT_LOGGER,
                "Successfully committed to table cat.ns.t in 30 ms",
                ms=2,
            ),
            app(
                T,
                plb.COMMIT_LOGGER,
                "Successfully committed to view cat.a.b.v in 7 ms",
                ms=3,
            ),
            app(T, "org.apache.iceberg.CatalogUtil", "Loading custom FileIO", ms=4),
        ],
    )
    assert processed(tmp_path) == []
    s, res, _, drop = report(tmp_path)
    t = res[f"{CAT}/namespaces/ns/tables/t"]
    assert (
        t["commit_count"],
        t["commit_ms_sum"],
        t["commit_ms_min"],
        t["commit_ms_max"],
    ) == (
        2,
        50,
        20,
        30,
    )
    assert t["requests"] == 0  # commits never touch the access counters
    assert f"{CAT}/namespaces/a%1Fb/views/v" in res  # nested namespace, Iceberg's %1F
    assert (
        drop[plb.COMMIT_LOGGER]["dropped"] == 3
        and drop["org.apache.iceberg.CatalogUtil"]["dropped"] == 1
    )
    assert s["app_dropped_total"] == 4 and s["distinct_resources"] == 0


# ------------------------------------------------------------------ rows


def test_an_error_joins_its_row_if_the_resource_succeeds_anywhere_in_the_hour(tmp_path):
    # the streaming filter would have sent this 403 to __errors__: the success came later
    drive(
        tmp_path,
        [
            acc("2026-09-28 10:05:00", "GET", f"{CAT}/namespaces/ns/tables/t", 403),
            acc("2026-09-28 10:10:00", "GET", f"{CAT}/namespaces/ns/tables/t", 200),
        ],
    )
    s, res, *_ = report(tmp_path)
    assert "__errors__" not in res
    t = res[f"{CAT}/namespaces/ns/tables/t"]
    assert (t["requests"], t["errors"], t["auth_denied"]) == (2, 1, 1)


def test_a_denied_grant_creates_its_role_row(tmp_path):
    drive(
        tmp_path,
        [
            acc(
                "2026-09-28 10:05:00",
                "PUT",
                f"{MGMT}/catalogs/c/catalog-roles/crX/grants",
                403,
            )
        ],
    )
    s, res, *_ = report(tmp_path)
    assert res[f"{MGMT}/catalogs/c/catalog-roles/crX"]["auth_denied"] == 1
    assert s["role_keys_forced"] == 1


def test_principal_rows_are_capped_into_other(tmp_path, monkeypatch):
    monkeypatch.setattr(plb, "REPORT_MAX_PRINCIPALS", 2)
    T = "2026-09-28 10:05:00"
    drive(
        tmp_path,
        [
            acc(T, "GET", f"{CAT}/namespaces", 200, user=u, ms=i)
            for i, u in enumerate("abc")
        ],
    )
    s, _, pri, _ = report(tmp_path)
    assert set(pri) == {"a", "b", "__other__"} and s["principals_other"] == 1


# ------------------------------------------------------------------ credential guard


def test_an_unmasked_client_secret_is_redacted_before_it_is_written(tmp_path):
    T = "2026-09-28 10:05:00"
    drive(
        tmp_path,
        [
            # Polaris's generated models print as "class X {\n    field: value\n}"; the value is
            # the next run of non-space characters, exactly as the Lua's [^%s]+ reads it
            app(
                T,
                ADMIN,
                "Created new principal class C {\n    clientId: abc\n    clientSecret: s3cr3t\n}",
                ms=1,
            ),
            app(
                T,
                ADMIN,
                "Created new principal class C {\n    clientId: def\n    clientSecret: *\n}",
                ms=2,
            ),
        ],
    )
    a, b = processed(tmp_path)
    assert (
        "s3cr3t" not in a["message"]
        and "<redacted>" in a["message"]
        and a["secret_redacted"]
    )
    assert "clientSecret: *" in b["message"] and "secret_redacted" not in b
    raw = (tmp_path / "processed-logs/20260928-10.jsonl").read_text()
    assert "s3cr3t" not in raw


# ------------------------------------------------------------------ accounting


def test_every_line_is_kept_dropped_or_malformed_exactly_once(tmp_path):
    T = "2026-09-28 10:10:00"
    drive(
        tmp_path,
        [
            acc(T, "GET", f"{CAT}/namespaces", 200, ms=1),
            acc(T, "POST", f"{MGMT}/principals", 201, ms=2),
            app(T, "x.Y", "noise", ms=3),
            app(T, MAPPER, "reason", ms=4, rid="q"),
            acc(T, "GET", f"{CAT}/namespaces/n", 404, ms=5, rid="q"),
            "not json at all",
        ],
    )
    s, *_ = report(tmp_path)
    assert s["lines_in"] == 6
    assert (s["processed"], s["dropped"], s["malformed"]) == (1, 4, 1)
    assert (
        s["dropped"]
        == s["access_counted"] + s["app_dropped_total"] + s["app_dropped_404"]
    )
