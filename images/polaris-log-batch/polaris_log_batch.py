#!/usr/bin/env python3
"""Hourly batch over Polaris's per-pod log files. Standard library only.

Design and every decision below: logging/PLAN-polaris-log-batch-2026-09-27.md (revised 2026-09-28).

    Polaris pod  --JSON, hourly .gz roll-->  PVC /deployments/logs/polaris-<pod>.log[.<hour>[.N].gz]
    this job (CronJob "3 * * * *" KST)  -->  processed-logs/YYYYMMDD-HH.jsonl
                                             aggregated-logs/YYYYMMDD-HH.jsonl
                                             malformed/YYYYMMDD-HH.jsonl
    Observability team                  -->  fetch from the PVC, index into OpenSearch

SELECTION IS BY TIMESTAMP, NOT BY FILE. For hour H the job reads every pod's rolls AND its current
.log, and keeps the lines whose `timestamp` is in [H:00, H+1:00) KST. A current file is read while
Polaris appends to it; only newline-terminated lines count. No sort: OpenSearch orders by timestamp.

ORPHANS. A current polaris-<pod>.log is orphaned when (1) the Kubernetes API no longer lists its pod
and (2) it is complete: its last line is in a published hour and it has been quiet > 120 s. Its lines
are read for their hours like any other file; after the hour is published the file moves to done/.
A live pod's file is never moved. If the pod list cannot be fetched, nothing is moved that run.

EXACTLY ONCE PER HOUR. The checkpoint is per hour. An hour is written to .tmp/, fsynced, os.replace'd
into place, and only then recorded; a crash anywhere means the next run redoes that hour from files
still in place, producing the same lines with the same event_id (sha1 of the raw line).

POLICY. AuditPolicy is releases/fluent-bit/polaris_access_log.lua (policy v5) ported to a batch:
processed-logs holds what the Lua kept for polaris-logs-* (tier 2); aggregated-logs holds one summary
row plus resource / principal / app_dropped rows -- report schema 7, i.e. v6 adapted to a complete
KST hour (see the policy section). The logic in Korean: logging/SPEC-polaris-log-batch.ko.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import gzip
import hashlib
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
import zlib

KST = dt.timezone(dt.timedelta(hours=9), "KST")
HOUR = dt.timedelta(hours=1)
SCHEMA = "polaris-log-batch/1"

QUIET_SECONDS = 120  # a file untouched this long is not being written right now
GRACE_SECONDS = 60  # hour H is publishable from H+1:00 + this
RETENTION_SECONDS = 3 * 24 * 3600  # D5: 3 days after publication
MAX_HOURS_PER_RUN = 72  # catch-up bound; the rest follows next run
TAIL_BYTES = (
    256 * 1024
)  # enough to hold a stack-trace line when reading a file's last line

CURRENT_RE = re.compile(r"^polaris-(?P<pod>.+)\.log$")
ROLL_RE = re.compile(
    r"^polaris-(?P<pod>.+?)\.log\.(?P<hour>\d{4}-\d{2}-\d{2}-\d{2})(?:\.(?P<n>\d+))?\.gz$"
)
TS_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$"
)

DIRS = ("processed-logs", "aggregated-logs", "malformed", "done", ".tmp", ".state")


# ---------------------------------------------------------------------------- time


def parse_ts(value):
    """ISO-8601 (Polaris writes nanoseconds and +09:00) -> aware datetime in KST, or None.

    Fractions beyond microseconds are truncated: selection only needs the hour, and the raw
    line -- nanoseconds included -- is what goes out.
    """
    if not isinstance(value, str):
        return None
    m = TS_RE.match(value.strip())
    if not m:
        return None
    y, mo, d, h, mi, s, frac, off = m.groups()
    micro = int((frac or "0")[:6].ljust(6, "0"))
    if off in (None, ""):
        tz = KST
    elif off == "Z":
        tz = dt.timezone.utc
    else:
        sign = 1 if off[0] == "+" else -1
        hh, mm = int(off[1:3]), int(off[-2:])
        tz = dt.timezone(sign * dt.timedelta(hours=hh, minutes=mm))
    try:
        t = dt.datetime(
            int(y), int(mo), int(d), int(h), int(mi), int(s), micro, tzinfo=tz
        )
    except ValueError:
        return None
    return t.astimezone(KST)


def floor_hour(t):
    return t.astimezone(KST).replace(minute=0, second=0, microsecond=0)


def hour_key(h):
    return h.strftime("%Y%m%d-%H")


def hour_from_key(key):
    return dt.datetime.strptime(key, "%Y%m%d-%H").replace(tzinfo=KST)


def roll_hour(text):
    return dt.datetime.strptime(text, "%Y-%m-%d-%H").replace(tzinfo=KST)


def epoch(t):
    return t.timestamp()


# ---------------------------------------------------------------------------- files


class LogFile:
    """One polaris-<pod>.log or polaris-<pod>.log.<hour>[.N].gz at the top of the log dir."""

    __slots__ = ("name", "path", "kind", "pod", "roll_hour", "mtime", "size")

    def __init__(self, name, path, kind, pod, rhour, mtime, size):
        self.name, self.path, self.kind, self.pod = name, path, kind, pod
        self.roll_hour, self.mtime, self.size = rhour, mtime, size

    def __repr__(self):  # pragma: no cover
        return f"<LogFile {self.name}>"


def scan(log_dir, pod_prefix):
    """Top-level log files of pods whose name starts with `pod_prefix`. Subdirectories
    (done/, legacy-shared/, sizetest/ ...) and other prefixes (polaris-sizetest-*) are ignored.
    """
    out = []
    for name in sorted(os.listdir(log_dir)):
        path = os.path.join(log_dir, name)
        m = ROLL_RE.match(name)
        if m:
            kind, pod, rh = "roll", m.group("pod"), roll_hour(m.group("hour"))
        else:
            m = CURRENT_RE.match(name)
            if not m:
                continue
            kind, pod, rh = "current", m.group("pod"), None
        if not pod.startswith(pod_prefix):
            continue
        try:
            st = os.stat(path)
        except FileNotFoundError:  # rotated away between listdir and stat
            continue
        if not os.path.isfile(path):
            continue
        out.append(LogFile(name, path, kind, pod, rh, st.st_mtime, st.st_size))
    return out


class Deferred(Exception):
    """A roll could not be decoded but is fresh -- probably still being compressed. Retry next run."""


class Corrupt(Exception):
    """A roll could not be decoded and is old enough that it never will be."""


def read_file(f, now_epoch, quiet):
    """-> (complete_lines, unterminated_tail). Raises Deferred / Corrupt for an undecodable roll."""
    if f.kind == "roll":
        try:
            with gzip.open(f.path, "rb") as fh:
                data = fh.read()
        except (EOFError, OSError, zlib.error) as exc:
            if now_epoch - f.mtime < quiet:
                raise Deferred(f"{f.name}: {exc}") from exc
            raise Corrupt(f"{f.name}: {exc}") from exc
        lines = data.split(b"\n")
        if lines and lines[-1] == b"":
            lines.pop()
        return lines, None  # a closed roll has no "being written" tail
    with open(f.path, "rb") as fh:
        data = fh.read()
    parts = data.split(b"\n")
    tail = parts.pop()  # b"" when the file ends with a newline
    return parts, (tail or None)


def last_complete_line(path):
    """The last newline-terminated line of a (possibly large) current file, read from the end."""
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        fh.seek(max(0, size - TAIL_BYTES))
        chunk = fh.read()
    parts = chunk.split(b"\n")
    tail = parts.pop()
    if size > TAIL_BYTES and len(parts) <= 1:
        return None, tail or None  # no complete line inside the window; do not guess
    if size > TAIL_BYTES:
        parts = parts[1:]  # the first piece may be the end of a line cut by the seek
    return (parts[-1] if parts else None), (tail or None)


def parse_line(raw):
    """-> (record dict, KST datetime) or (None, None) when the line is not a timestamped JSON object."""
    try:
        rec = json.loads(raw)
    except ValueError:
        return None, None
    if not isinstance(rec, dict):
        return None, None
    ts = parse_ts(rec.get("timestamp"))
    if ts is None:
        return None, None
    return rec, ts


def classify(f, lines):
    """Yield (line_no, raw, rec, ts, hour) for every line of one file.

    A malformed line has no timestamp of its own; it is booked to the hour of the nearest valid
    line BEFORE it in the same file (else the nearest after it, else the roll's hour, else the
    file's mtime hour) so that it is reported exactly once, in one hour's malformed file.
    """
    parsed = [parse_line(raw) for raw in lines]
    fallback = f.roll_hour or floor_hour(dt.datetime.fromtimestamp(f.mtime, KST))
    nxt = [None] * len(parsed)
    upcoming = None
    for i in range(len(parsed) - 1, -1, -1):
        if parsed[i][1] is not None:
            upcoming = floor_hour(parsed[i][1])
        nxt[i] = upcoming
    prev = None
    for i, (raw, (rec, ts)) in enumerate(zip(lines, parsed)):
        if ts is not None:
            prev = floor_hour(ts)
            yield i + 1, raw, rec, ts, prev
        else:
            yield i + 1, raw, None, None, (prev or nxt[i] or fallback)


# ---------------------------------------------------------------------------- policy
#
# A port of releases/fluent-bit/polaris_access_log.lua (policy v5, report schema v6) to a batch that
# sees the whole hour at once. What is the same: the keep/count rules 1-7, the allow-list, the 404
# rule, commit harvesting, the credential guard, the resource classification, the row caps. What a
# batch changes (report schema 7, logging/SPEC-polaris-log-batch.ko.md):
#   * the window is the KST clock hour, complete -- no ticks, no partial or skipped windows;
#   * the request-id hold is resolved by looking both ways (+-30 s, across the hour boundary), not
#     by holding records in memory until the access line arrives;
#   * an error request joins its resource row if that resource had a success or a commit ANYWHERE in
#     the hour -- the streaming filter could only see rows that existed at that instant;
#   * records are evaluated in timestamp order, so caps and role forcing are deterministic;
#   * one report per hour for all pods: `hostname` / `report_seq` give way to `pods`.

REPORT_SCHEMA_VERSION = 7

ACCESS_LOGGER = "io.quarkus.http.access-log"
ACCESS_RE = re.compile(r'^(\S+) \S+ (\S+) \[[^\]]*\] "([A-Z]+) (\S+)[^"]*" (\d+) (\S+)')

APP_ALLOW = frozenset(
    {
        "org.apache.polaris.service.exception.IcebergExceptionMapper",
        "org.apache.polaris.service.admin.PolarisServiceImpl",
    }
)
COMMIT_LOGGER = "org.apache.polaris.service.catalog.iceberg.IcebergCatalog"
COMMIT_RE = re.compile(r"^Successfully committed to ([A-Za-z]+) (\S+) in (\d+) ms")
COMMIT_KINDS = {"table": "tables", "view": "views"}
CATALOG_API = "/api/catalog/v1/"
NS_SEPARATOR = "%1F"
SECRET_RE = re.compile(r"(clientSecret:\s*)(\S+)")

READ_METHODS = frozenset({"GET", "HEAD"})
WRITE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})
KEEP_METHODS = frozenset({"PUT", "DELETE", "PATCH"})

HOLD_SECONDS = 30  # how far from an app line its access line may be and still decide it
REPORT_MAX_RESOURCES = 500
REPORT_MAX_PRINCIPALS = 200
REPORT_MAX_ROLE_KEYS = 100
REPORT_MAX_DROPPED_LOGGERS = 50
REPORT_OTHER = "__other__"
REPORT_ERRORS = "__errors__"
ROLE_KINDS = frozenset({"catalog-role", "principal-role"})

# the tier-2 field trim (releases/fluent-bit/values.yaml, polaris_field_trim)
TRIMMED_FIELDS = ("processName", "loggerClassName", "processId", "ndc")

# order is priority -- identical to the Lua table, see the comments there for why
RESOURCE_PATTERNS = [
    (kind, re.compile(rx))
    for kind, rx in (
        ("principal-role", r"^.*?/principal-roles/[^/]+"),
        ("collection", r"^.*?/principal-roles$"),
        ("catalog-role", r"^.*?/catalog-roles/[^/]+"),
        ("collection", r"^.*?/catalog-roles$"),
        ("auth", r"^.*?/oauth/tokens$"),
        ("config", r"^.*?/v1/config$"),
        ("table", r"^.*?/tables/rename$"),
        ("view", r"^.*?/views/rename$"),
        ("transaction", r"^.*?/transactions/commit$"),
        ("collection", r"^.*?/namespaces/[^/]+/register$"),
        ("namespace", r"^.*?/namespaces/[^/]+/properties$"),
        ("table", r"^.*?/namespaces/[^/]+/tables/[^/]+"),
        ("view", r"^.*?/namespaces/[^/]+/views/[^/]+"),
        ("collection", r"^.*?/namespaces/[^/]+/tables$"),
        ("collection", r"^.*?/namespaces/[^/]+/views$"),
        ("namespace", r"^.*?/namespaces/[^/]+$"),
        ("collection", r"^.*?/namespaces$"),
        ("catalog", r"^.*?/catalogs/[^/]+"),
        ("collection", r"^.*?/catalogs$"),
        ("principal", r"^.*?/principals/[^/]+"),
        ("collection", r"^.*?/principals$"),
    )
]


def parse_access(rec):
    """Add client_ip .. response_size to an access record. False (and access_log_parse_error) if
    the Quarkus pattern `%h %l %u %t "%r" %s %b` did not match -- a changed log pattern must show.
    """
    m = (
        ACCESS_RE.match(rec.get("message") or "")
        if isinstance(rec.get("message"), str)
        else None
    )
    if not m:
        rec["access_log_parse_error"] = True
        return False
    ip, user, method, path, status, size = m.groups()
    rec["client_ip"], rec["user_principal_name"] = ip, user
    rec["http_method"], rec["api_path"] = method, path
    rec["http_status"] = int(status)
    rec["response_size"] = (
        int(size) if size.isdigit() else 0
    )  # CLF %b writes "-" for 0 bytes
    return True


def redact_secret(rec):
    """Credential guard: a clientSecret that is not Polaris's own mask becomes <redacted>."""
    msg = rec.get("message")
    if not isinstance(msg, str) or "clientSecret" not in msg:
        return False
    hit = False

    def sub(m):
        nonlocal hit
        if m.group(2) in ("*", "<redacted>"):
            return m.group(0)
        hit = True
        return m.group(1) + "<redacted>"

    out = SECRET_RE.sub(sub, msg)
    if hit:
        rec["message"], rec["secret_redacted"] = out, True
    return hit


def path_only(p):
    return p.split("?", 1)[0] if isinstance(p, str) else ""


def api_of(path):
    if path.startswith("/api/management/"):
        return "management"
    if path.startswith("/api/catalog/"):
        return "catalog"
    return "other"


def classify_path(path):
    for kind, rx in RESOURCE_PATTERNS:
        m = rx.match(path)
        if m:
            return m.group(0), kind
    return path, "other"


def commit_key(kind, ident):
    seg = COMMIT_KINDS.get(kind)
    parts = [p for p in ident.split(".") if p]
    if seg is None or len(parts) < 3:
        return None
    return f"{CATALOG_API}{parts[0]}/namespaces/{NS_SEPARATOR.join(parts[1:-1])}/{seg}/{parts[-1]}"


def request_id(rec):
    m = rec.get("mdc")
    if isinstance(m, dict):
        rid = m.get("requestId")
        if isinstance(rid, str) and rid:
            return rid
    return None


def new_row():
    return {
        "requests": 0,
        "reads": 0,
        "writes": 0,
        "errors": 0,
        "errors_4xx": 0,
        "errors_5xx": 0,
        "auth_denied": 0,
        "response_bytes": 0,
    }


def bump(row, method, status, size, is_error):
    row["requests"] += 1
    if method in READ_METHODS:
        row["reads"] += 1
    elif method in WRITE_METHODS:
        row["writes"] += 1
    if is_error:
        row["errors"] += 1
        if status >= 500:
            row["errors_5xx"] += 1
        else:
            row["errors_4xx"] += 1
            if status in (401, 403):
                row["auth_denied"] += 1
    row["response_bytes"] += size
    if size > 0 and not is_error and 200 <= status < 300:
        if method in READ_METHODS:
            row["last_read_bytes"] = size
        elif method in WRITE_METHODS:
            row["last_write_bytes"] = size


class HourReport:
    """The v6 counters for one hour, filled in timestamp order."""

    def __init__(self, persistent_keys):
        self.persistent = (
            persistent_keys  # resources with a success or commit anywhere in H
        )
        self.resources, self.kinds, self.apis = {}, {}, {}
        self.principals, self.dropped = {}, {}
        self.other_keys = set()
        self.c = dict.fromkeys(
            (
                "access_seen access_counted role_keys_forced counted_read counted_post "
                "errors_kept parse_errors resources_over principals_over dropped_total "
                "counted_404 app_dropped_404 held_orphans"
            ).split(),
            0,
        )
        self.min_time = self.max_time = None

    def _add(self, key, kind, api):
        self.resources[key], self.kinds[key], self.apis[key] = new_row(), kind, api
        return self.resources[key]

    def resource(self, key, kind, api, create):
        if key in self.resources:
            return self.resources[key]
        if not create:
            return self.resources.get(REPORT_ERRORS) or self._add(
                REPORT_ERRORS, "error", "mixed"
            )
        real = (
            len(self.resources)
            - (REPORT_ERRORS in self.resources)
            - (REPORT_OTHER in self.resources)
        )
        if real >= REPORT_MAX_RESOURCES:
            self.c["resources_over"] += 1
            if len(self.other_keys) < REPORT_MAX_RESOURCES:
                self.other_keys.add(key)
            return self.resources.get(REPORT_OTHER) or self._add(
                REPORT_OTHER, "other", "mixed"
            )
        return self._add(key, kind, api)

    def principal(self, user):
        if user in self.principals:
            return self.principals[user]
        if (
            len(self.principals) - (REPORT_OTHER in self.principals)
            >= REPORT_MAX_PRINCIPALS
        ):
            self.c["principals_over"] += 1
            user = REPORT_OTHER
            if user in self.principals:
                return self.principals[user]
        self.principals[user] = new_row()
        return self.principals[user]

    def count_access(self, rec, parsed):
        self.c["access_seen"] += 1
        t = rec.get("timestamp")
        if isinstance(t, str):
            self.min_time = (
                t if self.min_time is None or t < self.min_time else self.min_time
            )
            self.max_time = (
                t if self.max_time is None or t > self.max_time else self.max_time
            )
        if not parsed:
            self.c["parse_errors"] += 1
            return
        method, status, size = (
            rec["http_method"],
            rec["http_status"],
            rec["response_size"],
        )
        path = path_only(rec["api_path"])
        key, kind = classify_path(path)
        is_error = status >= 400
        create = (not is_error) or key in self.persistent
        if not create and kind in ROLE_KINDS:
            if key in self.resources:
                create = True
            elif self.c["role_keys_forced"] < REPORT_MAX_ROLE_KEYS:
                self.c["role_keys_forced"] += 1
                create = True
        bump(
            self.resource(key, kind, api_of(path), create),
            method,
            status,
            size,
            is_error,
        )
        user = rec.get("user_principal_name") or "-"
        bump(self.principal(user), method, status, size, is_error)

    def count_commit(self, msg):
        m = COMMIT_RE.match(msg) if isinstance(msg, str) else None
        if not m:
            return
        kind, ident, ms = m.group(1), m.group(2), int(m.group(3))
        key = commit_key(kind, ident)
        if key is None:
            return
        row = self.resource(key, kind, "catalog", True)
        if "commit_count" not in row:
            row.update(
                commit_count=1, commit_ms_sum=ms, commit_ms_min=ms, commit_ms_max=ms
            )
        else:
            row["commit_count"] += 1
            row["commit_ms_sum"] += ms
            row["commit_ms_min"] = min(row["commit_ms_min"], ms)
            row["commit_ms_max"] = max(row["commit_ms_max"], ms)

    def count_dropped(self, logger):
        name = logger if isinstance(logger, str) and logger else "-"
        if name not in self.dropped and len(self.dropped) >= REPORT_MAX_DROPPED_LOGGERS:
            name = REPORT_OTHER
        self.dropped[name] = self.dropped.get(name, 0) + 1
        self.c["dropped_total"] += 1

    def rows(self, h, pods):
        start, end = h.isoformat(), (h + HOUR).isoformat()

        def base(kind):
            return {
                "schema_version": REPORT_SCHEMA_VERSION,
                "report_type": kind,
                "window_start": start,
                "window_end": end,
                "window_seconds": 3600,
                "_time": end,
            }

        rows, tot = [], dict(errors_4xx=0, errors_5xx=0, auth_denied=0, bytes_total=0)
        n_res = 0
        for key in sorted(self.resources):
            r = self.resources[key]
            tot["errors_4xx"] += r["errors_4xx"]
            tot["errors_5xx"] += r["errors_5xx"]
            tot["auth_denied"] += r["auth_denied"]
            tot["bytes_total"] += r["response_bytes"]
            if r["requests"] > 0 or "commit_count" in r:
                e = base("resource")
                e.update(
                    resource=key, resource_kind=self.kinds[key], api_kind=self.apis[key]
                )
                e.update(r)
                rows.append(e)
                n_res += r["requests"] > 0
        for user in sorted(self.principals):
            e = base("principal")
            e["user_principal_name"] = user
            # like the Lua: a principal row has no last_*_bytes (they describe a resource)
            e.update(
                {
                    k: v
                    for k, v in self.principals[user].items()
                    if not k.startswith("last_")
                }
            )
            rows.append(e)
        for name in sorted(self.dropped):
            e = base("app_dropped")
            e.update(logger_name=name, dropped=self.dropped[name])
            rows.append(e)
        c = self.c
        s = base("summary")
        s.update(
            pods=pods,
            access_seen=c["access_seen"],
            access_kept=c["access_seen"] - c["access_counted"],
            access_counted=c["access_counted"],
            role_keys_forced=c["role_keys_forced"],
            counted_read=c["counted_read"],
            counted_post=c["counted_post"],
            errors_kept=c["errors_kept"],
            parse_errors=c["parse_errors"],
            **tot,
            distinct_resources=n_res,
            distinct_principals=len(self.principals),
            resources_other=c["resources_over"],
            resources_other_distinct=len(self.other_keys),
            principals_other=c["principals_over"],
            app_dropped_total=c["dropped_total"],
            counted_404=c["counted_404"],
            app_dropped_404=c["app_dropped_404"],
            held_orphans=c["held_orphans"],
        )
        if (
            self.min_time is not None
        ):  # absent, never "", in an hour without access lines
            s["min_record_time"], s["max_record_time"] = self.min_time, self.max_time
        s["message"] = (
            f"polaris batch report {hour_key(h)} ({len(pods)} pods): {c['access_seen']} access "
            f"lines, {s['access_kept']} kept, {c['access_counted']} counted ({c['counted_read']} "
            f"read, {c['counted_post']} POST, {c['counted_404']} 404), {c['errors_kept']} errors "
            f"kept ({tot['errors_4xx']} 4xx, {tot['errors_5xx']} 5xx, {tot['auth_denied']} "
            f"denied), {n_res} resources, {len(self.principals)} principals, "
            f"{c['dropped_total']} app lines dropped, {tot['bytes_total']} bytes"
        )
        return s, rows


class PassthroughPolicy:
    """Every valid line kept as-is, one bare summary row. For framework tests and replays that
    want the raw lines; the CronJob runs AuditPolicy."""

    name = "passthrough"

    def apply(self, entries, context, h, key):
        out = [processed_doc(e["rec"], e["raw"], key) for e in entries]
        summary = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_type": "summary",
            "window_start": h.isoformat(),
            "window_end": (h + HOUR).isoformat(),
            "window_seconds": 3600,
            "_time": (h + HOUR).isoformat(),
            "pods": sorted({e["pod"] for e in entries}),
        }
        return out, 0, summary, []


def access_status_index(entries):
    """request id -> [(epoch, status)] for every parsed access line in the context window."""
    idx = {}
    for e in entries:
        rec = e["rec"]
        if rec.get("loggerName") != ACCESS_LOGGER:
            continue
        rid = request_id(rec)
        if rid is None:
            continue
        m = (
            ACCESS_RE.match(rec.get("message") or "")
            if isinstance(rec.get("message"), str)
            else None
        )
        if m:
            idx.setdefault(rid, []).append((e["ts"].timestamp(), int(m.group(5))))
    return idx


def matching_status(idx, rid, t):
    """The status of this request id's access line: the nearest one AT OR AFTER the app line within
    HOLD_SECONDS (the usual order -- the reason is logged first), else the nearest before it.
    """
    cands = idx.get(rid) or []
    after = [(at - t, st) for at, st in cands if 0 <= at - t <= HOLD_SECONDS]
    if after:
        return min(after)[1]
    before = [(t - at, st) for at, st in cands if 0 < t - at <= HOLD_SECONDS]
    return min(before)[1] if before else None


class AuditPolicy:
    """Policy v5 over one hour. `apply` returns (processed docs, dropped count, summary, rows)."""

    name = "policy-v5/report-v7"

    def apply(self, entries, context, h, key):
        """entries: the hour's valid lines; context: valid lines in [H-30 s, H+1 h+30 s]."""
        entries = sorted(entries, key=lambda e: (e["ts"], e["file"], e["line_no"]))
        status_idx = access_status_index(context)
        persistent = set()
        for e in entries:  # pass 1: which resources exist in H regardless of order
            rec = e["rec"]
            if rec.get("loggerName") == ACCESS_LOGGER and rec.get("level") not in (
                "ERROR",
                "WARN",
            ):
                m = (
                    ACCESS_RE.match(rec.get("message") or "")
                    if isinstance(rec.get("message"), str)
                    else None
                )
                if m and int(m.group(5)) < 400:
                    persistent.add(classify_path(path_only(m.group(4)))[0])
            elif rec.get("loggerName") == COMMIT_LOGGER and isinstance(
                rec.get("message"), str
            ):
                cm = COMMIT_RE.match(rec["message"])
                if cm and commit_key(cm.group(1), cm.group(2)):
                    persistent.add(commit_key(cm.group(1), cm.group(2)))
        rep = HourReport(persistent)
        out, dropped = [], 0
        for e in entries:
            rec = dict(e["rec"])
            keep = self._decide(rec, e["ts"], rep, status_idx)
            if keep:
                for f in TRIMMED_FIELDS:
                    rec.pop(f, None)
                out.append(processed_doc(rec, e["raw"], key))
            else:
                dropped += 1
        pods = sorted({e["pod"] for e in entries})
        summary, rows = rep.rows(h, pods)
        # never publish an hour whose books do not balance (explicit, not assert: -O strips those)
        if len(entries) != len(out) + dropped:
            raise RuntimeError("policy lost or invented a line")
        counted = (
            summary["access_counted"]
            + summary["app_dropped_total"]
            + summary["app_dropped_404"]
        )
        if dropped != counted:
            raise RuntimeError(
                f"policy accounting broke: dropped {dropped} != counted {counted}"
            )
        return out, dropped, summary, rows

    def _decide(self, rec, ts, rep, status_idx):
        redact_secret(rec)
        level, logger = rec.get("level"), rec.get("loggerName")
        is_access = logger == ACCESS_LOGGER
        parsed = parse_access(rec) if is_access else False
        if level in ("ERROR", "WARN"):  # 1
            return True
        if not is_access:  # 2
            if logger == COMMIT_LOGGER:  # 2a
                rep.count_commit(rec.get("message"))
            if logger in APP_ALLOW:  # 2b
                rid = request_id(rec)
                if rid is None:
                    return True
                status = matching_status(status_idx, rid, ts.timestamp())
                if status is None:
                    rec["held_orphan"] = True
                    rep.c["held_orphans"] += 1
                    return True
                if status == 404:
                    rep.c["app_dropped_404"] += 1
                    return False
                return True
            rep.count_dropped(logger)  # 2c
            return False
        rep.count_access(rec, parsed)
        status, method = rec.get("http_status"), rec.get("http_method")
        path = path_only(rec.get("api_path"))
        if status == 404:  # 3'
            rep.c["counted_404"] += 1
            rep.c["access_counted"] += 1
            return False
        if status is None or status >= 400:  # 3
            rep.c["errors_kept"] += 1
            return True
        if method in KEEP_METHODS:  # 4
            return True
        if method == "POST":  # 5
            if path.startswith("/api/management/"):
                return True
            rep.c["counted_post"] += 1
            rep.c["access_counted"] += 1
            return False
        if method in READ_METHODS:  # 6
            rep.c["counted_read"] += 1
            rep.c["access_counted"] += 1
            return False
        return True  # 7


def processed_doc(rec, raw, key):
    doc = dict(rec)
    doc["event_id"] = hashlib.sha1(raw).hexdigest()
    doc["log_hour"] = key
    return doc


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


# ---------------------------------------------------------------------------- disk


def ensure_dirs(log_dir):
    for d in DIRS:
        os.makedirs(os.path.join(log_dir, d), exist_ok=True)


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(log_dir, dest, data):
    """Write to .tmp/, fsync, os.replace into place (same filesystem), fsync the directory."""
    tmp = os.path.join(log_dir, ".tmp", f"{os.path.basename(dest)}.{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, dest)
    fsync_dir(os.path.dirname(dest))


def move_unique(src, dest_dir, name):
    """Move without ever overwriting: a taken name gets .1, .2 ..."""
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    n = 0
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(dest_dir, f"{name}.{n}")
    os.rename(src, dest)
    return dest


def load_checkpoint(log_dir):
    path = os.path.join(log_dir, ".state", "checkpoint.json")
    if not os.path.exists(path):
        return {"schema": SCHEMA, "last_published": None, "hours": {}}
    with open(path) as fh:
        return json.load(fh)


def save_checkpoint(log_dir, cp):
    atomic_write(
        log_dir,
        os.path.join(log_dir, ".state", "checkpoint.json"),
        json.dumps(cp, indent=1, sort_keys=True).encode(),
    )


# ---------------------------------------------------------------------------- pods


def k8s_pod_lister(selector):
    """Pod names from the API, with the CronJob's mounted ServiceAccount token (read-only Role)."""

    def lister():
        sa = "/var/run/secrets/kubernetes.io/serviceaccount"
        host = os.environ["KUBERNETES_SERVICE_HOST"]
        port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
        if ":" in host:
            host = f"[{host}]"
        with open(f"{sa}/namespace") as fh:
            ns = fh.read().strip()
        with open(f"{sa}/token") as fh:
            token = fh.read().strip()
        url = (
            f"https://{host}:{port}/api/v1/namespaces/{ns}/pods"
            f"?labelSelector={urllib.parse.quote(selector)}"
        )
        ctx = ssl.create_default_context(cafile=f"{sa}/ca.crt")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.load(resp)
        return {item["metadata"]["name"] for item in data.get("items", [])}

    return lister


# ---------------------------------------------------------------------------- one hour


def process_hour(cfg, files, h, now_epoch, pods, pod_error):
    """Everything for hour h, in memory. Nothing is written here."""
    key = hour_key(h)
    h0, h1 = epoch(h), epoch(h + HOUR)
    c0, c1 = h0 - HOLD_SECONDS, h1 + HOLD_SECONDS  # context for the request-id match
    entries, context, malformed, sources, corrupt = [], [], [], [], []

    for f in files:
        if f.mtime < c0:  # last written before the context window: nothing to read
            continue
        try:
            lines, _tail = read_file(f, now_epoch, cfg.quiet)
        except Corrupt as exc:
            corrupt.append({"file": f.name, "error": str(exc)})
            continue
        n_here = 0
        for line_no, raw, rec, ts, hour in classify(f, lines):
            if ts is not None and c0 <= ts.timestamp() < c1:
                context.append({"rec": rec, "ts": ts})
            if hour != h:
                continue
            n_here += 1
            if rec is None:
                malformed.append(
                    {
                        "reason": "not a timestamped JSON object",
                        "file": f.name,
                        "line_no": line_no,
                        "raw": raw.decode("utf-8", "replace"),
                    }
                )
                continue
            entries.append(
                {
                    "rec": rec,
                    "ts": ts,
                    "raw": raw,
                    "pod": f.pod,
                    "file": f.name,
                    "line_no": line_no,
                }
            )
        if n_here:
            sources.append({"file": f.name, "lines": n_here})

    # orphans and idle files: every current file, whatever its mtime, judged by its last line
    orphans, idle = [], []
    for f in files:
        if f.kind != "current":
            continue
        last, tail = last_complete_line(f.path)
        _, last_ts = parse_line(last) if last else (None, None)
        if last_ts is None or floor_hour(last_ts) > h:
            continue  # still in a later hour, or unreadable: leave it alone
        quiet = now_epoch - f.mtime > cfg.quiet
        entry = {
            "file": f.name,
            "pod": f.pod,
            "last_line_hour": hour_key(floor_hour(last_ts)),
        }
        if pods is not None and f.pod not in pods and quiet:
            entry["unterminated_tail"] = tail is not None
            orphans.append((f, entry, tail))
            if tail is not None:
                malformed.append(
                    {
                        "reason": "unterminated last line of an orphaned file (pod killed mid-write)",
                        "file": f.name,
                        "line_no": None,
                        "raw": tail.decode("utf-8", "replace"),
                    }
                )
        elif pods is not None and f.pod in pods and floor_hour(last_ts) < h:
            idle.append(entry)

    processed, dropped, summary, rows = cfg.policy.apply(entries, context, h, key)
    by_pod = {}
    for e in entries:
        by_pod[e["pod"]] = by_pod.get(e["pod"], 0) + 1
    lines_in = len(entries) + len(malformed)
    if lines_in != len(processed) + dropped + len(malformed):
        raise RuntimeError("line accounting broke")
    summary.update(
        {
            "hour": key,
            "batch_schema": SCHEMA,
            "policy": cfg.policy.name,
            "lines_in": lines_in,
            "processed": len(processed),
            "dropped": dropped,
            "malformed": len(malformed),
            "by_pod": dict(sorted(by_pod.items())),
            "sources": sources,
            "corrupt_files": corrupt,
            "orphans_moved": None if pods is None else [e for _, e, _ in orphans],
            "pod_list_error": pod_error,
            "idle_log_files": None if pods is None else idle,
        }
    )
    return {
        "key": key,
        "processed": processed,
        "malformed": malformed,
        "summary": summary,
        "rows": rows,
        "orphans": orphans,
        "corrupt": corrupt,
    }


def publish(cfg, result, now_epoch):
    d, key = cfg.log_dir, result["key"]
    if result["malformed"]:
        atomic_write(
            d,
            os.path.join(d, "malformed", f"{key}.jsonl"),
            "".join(dumps(m) + "\n" for m in result["malformed"]).encode(),
        )
    atomic_write(
        d,
        os.path.join(d, "processed-logs", f"{key}.jsonl"),
        "".join(dumps(p) + "\n" for p in result["processed"]).encode(),
    )
    summary = dict(result["summary"])
    summary["published_at"] = dt.datetime.fromtimestamp(now_epoch, KST).isoformat()
    body = [summary] + result["rows"]
    atomic_write(
        d,
        os.path.join(d, "aggregated-logs", f"{key}.jsonl"),
        "".join(dumps(r) + "\n" for r in body).encode(),
    )
    return summary


def housekeep_after(cfg, files, h, result):
    """After hour h is checkpointed: rolls named <= h and orphans go to done/, corrupt rolls to
    malformed/files/. Never a current file of a listed pod."""
    d = cfg.log_dir
    moved = []
    corrupt_names = {c["file"] for c in result["corrupt"]}
    for f in files:
        if not os.path.exists(f.path):
            continue
        if f.name in corrupt_names:
            moved.append(
                move_unique(f.path, os.path.join(d, "malformed", "files"), f.name)
            )
        elif f.kind == "roll" and f.roll_hour <= h:
            day = f.roll_hour.strftime("%Y%m%d")
            moved.append(move_unique(f.path, os.path.join(d, "done", day), f.name))
    for f, entry, _tail in result["orphans"]:
        if not os.path.exists(f.path):
            continue
        lh = hour_from_key(entry["last_line_hour"])
        name = f"{f.name}.{lh.strftime('%Y-%m-%d-%H')}.orphan"
        moved.append(
            move_unique(f.path, os.path.join(d, "done", lh.strftime("%Y%m%d")), name)
        )
    return moved


def retention(cfg, now_epoch):
    d, cutoff, removed = cfg.log_dir, now_epoch - cfg.retention, 0
    for sub in ("processed-logs", "aggregated-logs", "malformed", "done"):
        root = os.path.join(d, sub)
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            for name in filenames:
                p = os.path.join(dirpath, name)
                if os.stat(p).st_mtime < cutoff:
                    os.remove(p)
                    removed += 1
            if dirpath != root and not os.listdir(dirpath):
                os.rmdir(dirpath)
    return removed


# ---------------------------------------------------------------------------- run


class Config:
    def __init__(
        self,
        log_dir,
        pod_prefix="benchmarks-polaris-",
        pod_lister=None,
        quiet=QUIET_SECONDS,
        grace=GRACE_SECONDS,
        retention=RETENTION_SECONDS,
        max_hours=MAX_HOURS_PER_RUN,
        policy=None,
        dry_run=False,
    ):
        self.log_dir, self.pod_prefix, self.pod_lister = log_dir, pod_prefix, pod_lister
        self.quiet, self.grace, self.retention, self.max_hours = (
            quiet,
            grace,
            retention,
            max_hours,
        )
        self.policy = policy or AuditPolicy()
        self.dry_run = dry_run


def first_hour(files, now_epoch, quiet):
    """Earliest hour of any valid line on disk -- only for a run with no checkpoint yet.

    A full read, once. Roll names are not enough: a roll of 11 can open with a 10:59:59.9 line
    written after the rotation (thread race at the boundary), and a run starting at 11 would
    never publish it.
    """
    earliest = None
    for f in files:
        try:
            lines, _ = read_file(f, now_epoch, quiet)
        except (Deferred, Corrupt):
            continue
        for raw in lines:
            _, ts = parse_line(raw)
            if ts is not None and (earliest is None or ts < earliest):
                earliest = ts
    return floor_hour(earliest) if earliest else None


def run(cfg, now=None, out=sys.stdout):
    """One CronJob run. Returns a dict describing what happened (also printed as JSON lines)."""
    now = now or dt.datetime.now(KST)
    now_epoch = epoch(now)
    ensure_dirs(cfg.log_dir)
    lock = open(os.path.join(cfg.log_dir, ".state", "lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        if exc.errno in (errno.EAGAIN, errno.EACCES):
            print(
                dumps({"event": "skipped", "reason": "another run holds the lock"}),
                file=out,
            )
            return {"status": "locked", "published": []}
        raise
    try:
        return _run_locked(cfg, now, now_epoch, out)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def _run_locked(cfg, now, now_epoch, out):
    cp = load_checkpoint(cfg.log_dir)
    files = scan(cfg.log_dir, cfg.pod_prefix)
    last_ready = floor_hour(now - dt.timedelta(seconds=cfg.grace)) - HOUR
    if cp["last_published"]:
        h = hour_from_key(cp["last_published"]) + HOUR
    else:
        h = first_hour(files, now_epoch, cfg.quiet)
    published, status = [], "ok"
    if h is None:
        print(
            dumps({"event": "idle", "reason": "no log files and no checkpoint"}),
            file=out,
        )
        return {"status": "idle", "published": []}

    pods, pod_error = None, None
    if cfg.pod_lister is not None:
        try:
            pods = set(cfg.pod_lister())
        except (
            Exception
        ) as exc:  # noqa: BLE001 -- any failure means: move no .log this run
            pod_error = f"{type(exc).__name__}: {exc}"
    else:
        pod_error = "pod listing disabled"

    n = 0
    while h <= last_ready and n < cfg.max_hours:
        try:
            result = process_hour(cfg, files, h, now_epoch, pods, pod_error)
        except Deferred as exc:
            status = "deferred"
            print(
                dumps({"event": "deferred", "hour": hour_key(h), "reason": str(exc)}),
                file=out,
            )
            break
        if cfg.dry_run:
            print(dumps({"event": "dry-run", **result["summary"]}), file=out)
            published.append(result["key"])
        else:
            summary = publish(cfg, result, now_epoch)
            cp["last_published"] = result["key"]
            cp["hours"][result["key"]] = {
                "published_at": summary["published_at"],
                "processed": summary["processed"],
                "malformed": summary["malformed"],
                "sources": summary["sources"],
            }
            save_checkpoint(cfg.log_dir, cp)
            moved = housekeep_after(cfg, files, h, result)
            files = scan(cfg.log_dir, cfg.pod_prefix)
            print(
                dumps({"event": "published", **summary, "moved": len(moved)}), file=out
            )
            published.append(result["key"])
        h += HOUR
        n += 1

    if not cfg.dry_run:
        cutoff = now_epoch - cfg.retention
        cp["hours"] = {
            k: v
            for k, v in cp["hours"].items()
            if epoch(dt.datetime.fromisoformat(v["published_at"])) >= cutoff
        }
        save_checkpoint(cfg.log_dir, cp)
        removed = retention(cfg, now_epoch)
        if removed:
            print(dumps({"event": "retention", "removed": removed}), file=out)
    return {"status": status, "published": published, "pod_list_error": pod_error}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--log-dir", default=os.environ.get("LOG_DIR", "/deployments/logs"))
    ap.add_argument(
        "--pod-prefix", default=os.environ.get("POD_PREFIX", "benchmarks-polaris-")
    )
    ap.add_argument(
        "--selector",
        default=os.environ.get(
            "POD_SELECTOR", "app.kubernetes.io/instance=benchmarks-polaris"
        ),
    )
    ap.add_argument(
        "--no-pod-list",
        action="store_true",
        help="skip the API: process, but move no .log",
    )
    ap.add_argument("--now", help="ISO time to act as 'now' (replays, tests)")
    ap.add_argument(
        "--dry-run", action="store_true", help="compute and print, write nothing"
    )
    args = ap.parse_args(argv)
    cfg = Config(
        args.log_dir,
        pod_prefix=args.pod_prefix,
        pod_lister=None if args.no_pod_list else k8s_pod_lister(args.selector),
        dry_run=args.dry_run,
    )
    now = parse_ts(args.now) if args.now else None
    result = run(cfg, now=now)
    return 0 if result["status"] in ("ok", "idle", "locked", "deferred") else 1


if __name__ == "__main__":
    sys.exit(main())
