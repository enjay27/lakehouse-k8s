#!/usr/bin/env python3
"""step16 -- does the batch's AuditPolicy keep and count what polaris_access_log.lua does?

Feeds the same records, in timestamp order, through
  * releases/fluent-bit/polaris_access_log.lua (policy v5 / report v6), in LuaJIT via `lupa`, and
  * charts/polaris/files/log-batch/polaris_log_batch.py AuditPolicy (policy v5 / report v7),
and compares the kept records and every summary / resource / principal / app_dropped counter.

    pip install lupa          # not a project dependency; bundles LuaJIT 2.1 (Fluent Bit's runtime)
    python3 logging/scripts/step16-batch-lua-parity.py                  # synthetic hour, seed 7
    python3 logging/scripts/step16-batch-lua-parity.py --seed 3 --n 5000
    python3 logging/scripts/step16-batch-lua-parity.py --file polaris-<pod>.log[.gz] ...  # real lines

The synthetic hour avoids the two DOCUMENTED differences (logging/SPEC-polaris-log-batch.ko.md):
an error that precedes the first success of its resource (Lua: __errors__, batch: the resource
row), and a request-id pair split across the hour. On real files those can show up as diffs.
Exit 0 when identical.
"""

import argparse
import datetime as dt
import gzip
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve()
while not (ROOT / "charts").is_dir() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "charts/polaris/files/log-batch"))
import polaris_log_batch as plb  # noqa: E402

LUA = ROOT / "releases/fluent-bit/polaris_access_log.lua"
KST = plb.KST
HOUR0 = dt.datetime(2026, 9, 28, 10, tzinfo=KST)
COUNTERS = (
    "access_seen access_kept access_counted counted_read counted_post counted_404 errors_kept "
    "parse_errors errors_4xx errors_5xx auth_denied bytes_total app_dropped_total app_dropped_404 "
    "held_orphans distinct_resources distinct_principals role_keys_forced"
).split()
ROW_FIELDS = (
    "requests reads writes errors errors_4xx errors_5xx auth_denied response_bytes "
    "last_read_bytes last_write_bytes commit_count commit_ms_sum commit_ms_min commit_ms_max"
).split()


# ------------------------------------------------------------------ fixture


def synthetic(seed, n):
    rng = random.Random(seed)
    cat, mgmt = "/api/catalog/v1/cat", "/api/management/v1"
    ok_paths = [("GET", f"{cat}/namespaces/ns/tables/t{i}") for i in range(8)] + [
        ("GET", f"{cat}/namespaces/ns/tables/t1/metrics"),
        ("POST", f"{cat}/namespaces/ns/tables/t2"),
        ("POST", f"{cat}/namespaces/ns/tables"),
        ("GET", f"{cat}/namespaces"),
        ("HEAD", f"{cat}/namespaces/ns"),
        ("POST", f"{mgmt}/principals"),
        ("DELETE", f"{mgmt}/principals/p3"),
        ("PUT", f"{mgmt}/catalogs/cat/catalog-roles/cr1/grants"),
        ("PUT", f"{mgmt}/principal-roles/pr1/catalog-roles/cat"),
        ("POST", f"{cat}/v1/oauth/tokens"),
        ("GET", f"{cat}/v1/config?warehouse=cat"),
        ("POST", f"{cat}/transactions/commit"),
        ("POST", f"{cat}/namespaces/ns/register"),
    ]
    err_only = [
        ("GET", f"{cat}/namespaces/ns/tables/ghost"),
        ("PUT", f"{mgmt}/catalogs/cat/catalog-roles/denied/grants"),
        ("GET", f"{mgmt}/catalogs"),
    ]
    users = ["root", "etl", "reader", "-"]
    t = HOUR0.timestamp() + 1
    lines = []

    def stamp(sec):
        whole = int(sec)
        ns = int(round((sec - whole) * 1e9))
        return (
            f"{dt.datetime.fromtimestamp(whole, KST):%Y-%m-%dT%H:%M:%S}.{ns:09d}+09:00"
        )

    def rec(sec, logger, msg, level="INFO", rid=None):
        r = {
            "timestamp": stamp(sec),
            "loggerName": logger,
            "level": level,
            "message": msg,
            "threadName": "executor-thread-1",
            "hostName": "benchmarks-polaris-x",
        }
        if rid:
            r["mdc"] = {"requestId": rid}
        return r

    def access(sec, method, path, status, size, user, rid, level="INFO"):
        msg = f'10.0.0.{rng.randint(1, 9)} - {user} [28/Sep/2026:10:00:00 +0900] "{method} {path} HTTP/1.1" {status} {size}'
        return rec(sec, plb.ACCESS_LOGGER, msg, level, rid)

    # successes first (all of them), errors after -- see the module docstring
    for i in range(n):
        t += rng.uniform(0.2, 1.0)
        method, path = rng.choice(ok_paths)
        rid = f"r{i}" if rng.random() < 0.8 else None
        if rid and rng.random() < 0.3:
            lines.append(
                rec(
                    t - 0.004, rng.choice(sorted(plb.APP_ALLOW)), f"reason {i}", rid=rid
                )
            )
        if rng.random() < 0.2:
            lines.append(
                rec(
                    t - 0.002,
                    rng.choice(["a.Noise", "b.Chatter", plb.COMMIT_LOGGER]),
                    f"Successfully committed to table cat.ns.t{i % 8} in {rng.randint(3, 90)} ms",
                )
            )
        status = rng.choice([200, 200, 200, 201, 204]) if method != "GET" else 200
        size = 0 if status == 204 else rng.randint(1, 5000)
        lines.append(access(t, method, path, status, size, rng.choice(users), rid))
        if rid and rng.random() < 0.02:
            lines.append(
                rec(t + 0.003, rng.choice(sorted(plb.APP_ALLOW)), f"after {i}", rid=rid)
            )
    for i in range(n // 5):
        t += rng.uniform(0.2, 1.0)
        method, path = rng.choice(ok_paths + err_only)
        status = rng.choice([400, 401, 403, 404, 404, 409, 500])
        rid = f"e{i}"
        if rng.random() < 0.5:
            lines.append(
                rec(t - 0.003, rng.choice(sorted(plb.APP_ALLOW)), f"why {i}", rid=rid)
            )
        lines.append(
            access(
                t, method, path, status, rng.randint(20, 200), rng.choice(users), rid
            )
        )
    for i in range(3):  # allow-listed lines whose access line never comes
        t += 1
        lines.append(
            rec(
                t,
                sorted(plb.APP_ALLOW)[0],
                f"orphan {i}",
                rid=f"lost{i}",
            )
        )
    lines.append(rec(t + 1, plb.ACCESS_LOGGER, "not the access pattern"))
    lines.append(rec(t + 2, "x.Y", "WARNING kept", level="WARN"))
    lines.append(
        rec(
            t + 3,
            sorted(plb.APP_ALLOW)[1],
            "Created new principal class C {\n    clientId: a\n    clientSecret: leak\n}",
        )
    )
    assert t < HOUR0.timestamp() + 3600, "fixture ran past the hour -- lower --n"
    return [json.dumps(x) for x in lines]


def from_files(paths, hour):
    out = []
    for p in paths:
        data = gzip.open(p, "rb").read() if p.endswith(".gz") else open(p, "rb").read()
        for raw in data.split(b"\n"):
            rec, ts = plb.parse_line(raw) if raw else (None, None)
            if ts is not None and plb.floor_hour(ts) == hour:
                out.append(raw.decode())
    return out


# ------------------------------------------------------------------ the two sides


def run_batch(lines, hour):
    entries = []
    for i, raw in enumerate(lines):
        rec, ts = plb.parse_line(raw.encode())
        entries.append(
            {
                "rec": rec,
                "ts": ts,
                "raw": raw.encode(),
                "pod": "p",
                "file": "f",
                "line_no": i,
            }
        )
    kept, _dropped, summary, rows = plb.AuditPolicy().apply(
        entries, entries, hour, plb.hour_key(hour)
    )
    return kept, summary, rows


def run_lua(lines, hour):
    from lupa import luajit21 as lj

    lua = lj.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(LUA.read_text())
    filt = lua.globals().polaris_noise_filter
    win = hour.timestamp()  # every record inside one Lua window: pin its clock

    def to_lua(obj):
        if isinstance(obj, dict):
            return lua.table_from({k: to_lua(v) for k, v in obj.items()})
        return obj

    def to_py(t):
        if lupa_type(t) == "table":
            keys = list(t.keys())
            if keys and all(isinstance(k, int) for k in keys):
                return [to_py(t[k]) for k in sorted(keys)]
            return {k: to_py(v) for k, v in t.items()}
        return t

    lupa_type = lj.lua_type
    kept = []

    def feed(rec, now):
        r = dict(rec)
        r["_time"] = r.pop("timestamp")  # tier 2's Rename timestamp _time
        r["_now_override"] = now
        code, _ts, out = filt("polaris.logs", 0, to_lua(r))
        if code == -1:
            return
        out = to_py(out)
        for o in out if isinstance(out, list) else [out]:
            o.pop("_now_override", None)
            kept.append(o)

    parsed = sorted(
        ((plb.parse_line(x.encode()), x) for x in lines), key=lambda p: p[0][1]
    )
    for (rec, _ts), _raw in parsed:
        feed(rec, win + 1)
    # flush the held orphans (HOLD_MAX_SECONDS 30) with one extra record, then close the window
    feed(
        {
            "timestamp": "flush",
            "loggerName": "flush",
            "level": "ERROR",
            "message": "__flush__",
        },
        win + 40,
    )
    code, _ts, report = filt(
        "polaris.report", 0, to_lua({"_now_override": win + 10_000})
    )
    kept = [k for k in kept if k.get("message") != "__flush__"]
    return kept, to_py(report)


# ------------------------------------------------------------------ compare


def ident(doc):
    t = doc.get("timestamp", doc.get("_time"))
    return (
        t,
        doc.get("loggerName"),
        doc.get("message"),
        bool(doc.get("held_orphan")),
        doc.get("http_status"),
        bool(doc.get("secret_redacted")),
    )


def compare(lines, hour):
    b_kept, b_sum, b_rows = run_batch(lines, hour)
    l_kept, l_report = run_lua(lines, hour)
    l_sum = l_report[0]
    diffs = []
    bk, lk = sorted(map(ident, b_kept)), sorted(map(ident, l_kept))
    if bk != lk:
        only_b = [x for x in bk if x not in lk][:10]
        only_l = [x for x in lk if x not in bk][:10]
        diffs.append(
            f"kept records differ: batch {len(bk)}, lua {len(lk)}; only batch {only_b}; only lua {only_l}"
        )
    for c in COUNTERS:
        if b_sum.get(c) != l_sum.get(c):
            diffs.append(f"summary.{c}: batch {b_sum.get(c)} lua {l_sum.get(c)}")

    def index(rows, kind, key):
        return {r[key]: r for r in rows if r["report_type"] == kind}

    for kind, key in (("resource", "resource"), ("principal", "user_principal_name")):
        b, l = index(b_rows, kind, key), index(l_report[1:], kind, key)
        for k in sorted(set(b) | set(l)):
            if k not in b or k not in l:
                diffs.append(f"{kind} {k}: only in {'batch' if k in b else 'lua'}")
                continue
            for f in ROW_FIELDS:
                if b[k].get(f) != l[k].get(f):
                    diffs.append(
                        f"{kind} {k}.{f}: batch {b[k].get(f)} lua {l[k].get(f)}"
                    )
    bd = {
        r["logger_name"]: r["dropped"]
        for r in b_rows
        if r["report_type"] == "app_dropped"
    }
    ld = {
        r["logger_name"]: r["dropped"]
        for r in l_report[1:]
        if r["report_type"] == "app_dropped"
    }
    if bd != ld:
        diffs.append(f"app_dropped: batch {bd} lua {ld}")
    return len(lines), len(b_kept), b_sum, diffs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument(
        "--file", nargs="*", help="real Polaris log files instead of the synthetic hour"
    )
    ap.add_argument("--hour", default="20260928-10", help="YYYYMMDD-HH, with --file")
    a = ap.parse_args(argv)
    hour = plb.hour_from_key(a.hour)
    lines = from_files(a.file, hour) if a.file else synthetic(a.seed, a.n)
    n, kept, s, diffs = compare(lines, hour)
    print(
        f"lines {n}  kept {kept}  access_seen {s['access_seen']}  counted {s['access_counted']}  "
        f"app_dropped {s['app_dropped_total']}  404-dropped {s['app_dropped_404']}  "
        f"held_orphans {s['held_orphans']}  resources {s['distinct_resources']}"
    )
    for d in diffs:
        print("DIFF", d)
    print("PARITY:", "identical" if not diffs else f"{len(diffs)} difference(s)")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())
