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

P1a SCOPE: the policy is a passthrough -- every valid line is a processed line, and the aggregated file
holds one summary row. The port of policy v5 / report schema v6 (releases/fluent-bit/
polaris_access_log.lua) is P1b and replaces `PassthroughPolicy`.
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


class PassthroughPolicy:
    """P1a: every valid line is kept as-is. Replaced by the policy v5 / schema v6 port in P1b."""

    name = "passthrough-p1a"

    def keep(self, rec):
        return True


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
    processed, malformed, sources, corrupt = [], [], [], []
    by_pod, by_level = {}, {}
    lines_in = dropped = 0

    for f in files:
        if f.mtime < h0:  # last written before H: cannot hold an H line
            continue
        try:
            lines, _tail = read_file(f, now_epoch, cfg.quiet)
        except Corrupt as exc:
            corrupt.append({"file": f.name, "error": str(exc)})
            continue
        n_here = 0
        for line_no, raw, rec, ts, hour in classify(f, lines):
            if hour != h:
                continue
            n_here += 1
            lines_in += 1
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
            if not cfg.policy.keep(rec):
                dropped += 1
                continue
            processed.append(processed_doc(rec, raw, key))
            by_pod[f.pod] = by_pod.get(f.pod, 0) + 1
            lvl = str(rec.get("level", "?"))
            by_level[lvl] = by_level.get(lvl, 0) + 1
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
        elif pods is not None and f.pod in pods and floor_hour(last_ts) < h:
            idle.append(entry)
    for f, entry, tail in orphans:
        if tail is not None:
            malformed.append(
                {
                    "reason": "unterminated last line of an orphaned file (pod killed mid-write)",
                    "file": f.name,
                    "line_no": None,
                    "raw": tail.decode("utf-8", "replace"),
                }
            )
            lines_in += 1

    assert lines_in == len(processed) + dropped + len(
        malformed
    ), "line accounting broke"
    summary = {
        "report_type": "summary",
        "schema": SCHEMA,
        "policy": cfg.policy.name,
        "hour": key,
        "window_start": h.isoformat(),
        "window_end": (h + HOUR).isoformat(),
        "window_seconds": 3600,
        "lines_in": lines_in,
        "processed": len(processed),
        "dropped": dropped,
        "malformed": len(malformed),
        "by_pod": dict(sorted(by_pod.items())),
        "by_level": dict(sorted(by_level.items())),
        "sources": sources,
        "corrupt_files": corrupt,
        "orphans_moved": None if pods is None else [e for _, e, _ in orphans],
        "pod_list_error": pod_error,
        "idle_log_files": None if pods is None else idle,
    }
    return {
        "key": key,
        "processed": processed,
        "malformed": malformed,
        "summary": summary,
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
    atomic_write(
        d,
        os.path.join(d, "aggregated-logs", f"{key}.jsonl"),
        (dumps(summary) + "\n").encode(),
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
        self.policy = policy or PassthroughPolicy()
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
