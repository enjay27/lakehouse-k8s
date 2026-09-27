"""charts/polaris/files/log-batch/polaris_log_batch.py -- the hourly Polaris log batch (P1a).

Every test builds a log directory in tmp_path with the file names Polaris really writes
(polaris-<pod>.log, polaris-<pod>.log.<YYYY-MM-DD-HH>[.N].gz), sets mtimes explicitly, and runs the
job at a chosen "now". No cluster, no network: the pod list is a lambda.
"""

import datetime as dt
import fcntl
import gzip
import hashlib
import io
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(
    0,
    str(
        pathlib.Path(__file__).resolve().parent.parent
        / "charts/polaris/files/log-batch"
    ),
)
import polaris_log_batch as plb  # noqa: E402

KST = plb.KST
A = "benchmarks-polaris-7f4d69c67c-aaaaa"
B = "benchmarks-polaris-7f4d69c67c-bbbbb"


def T(text):
    """'2026-09-28 10:15:00' -> aware KST datetime."""
    return dt.datetime.fromisoformat(text).replace(tzinfo=KST)


def E(text):
    return T(text).timestamp()


def line(when, pod, msg="m", level="INFO", ns=0):
    t = T(when)
    stamp = f"{t:%Y-%m-%dT%H:%M:%S}.{ns:09d}+09:00"
    return (
        json.dumps(
            {
                "timestamp": stamp,
                "level": level,
                "loggerName": "x",
                "message": msg,
                "hostName": pod,
            }
        )
        + "\n"
    )


def put(path, data, mtime):
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    os.utime(path, (E(mtime), E(mtime)))
    return path


def current(d, pod, lines, mtime):
    return put(d / f"polaris-{pod}.log", "".join(lines), mtime)


def roll(d, pod, hour, lines, mtime, n=None):
    name = f"polaris-{pod}.log.{hour}" + (f".{n}" if n else "") + ".gz"
    return put(d / name, gzip.compress("".join(lines).encode()), mtime)


def cfg(d, pods=(A, B), **kw):
    lister = kw.pop("lister", None)
    if lister is None and pods is not None:
        lister = lambda: set(pods)  # noqa: E731
    return plb.Config(str(d), pod_lister=lister, **kw)


def run(c, now):
    out = io.StringIO()
    res = plb.run(c, now=T(now), out=out)
    res["log"] = [json.loads(x) for x in out.getvalue().splitlines()]
    return res


def jl(path):
    return [json.loads(x) for x in pathlib.Path(path).read_text().splitlines()]


def summary(d, key):
    return jl(d / "aggregated-logs" / f"{key}.jsonl")[0]


# ------------------------------------------------------------------ selection by timestamp


def test_hour_boundary_is_by_timestamp_to_the_nanosecond(tmp_path):
    current(
        tmp_path,
        A,
        [
            line("2026-09-28 10:59:59", A, "last of 10", ns=999_999_999),
            line("2026-09-28 11:00:00", A, "first of 11", ns=0),
            line("2026-09-28 11:02:00", A, "later"),
        ],
        "2026-09-28 11:02:00",
    )
    r = run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert r["published"] == ["20260928-10"]
    docs = jl(tmp_path / "processed-logs/20260928-10.jsonl")
    assert [x["message"] for x in docs] == ["last of 10"]
    raw = (
        line("2026-09-28 10:59:59", A, "last of 10", ns=999_999_999)
        .rstrip("\n")
        .encode()
    )
    assert docs[0]["event_id"] == hashlib.sha1(raw).hexdigest()
    assert docs[0]["log_hour"] == "20260928-10"

    r = run(cfg(tmp_path), "2026-09-28 12:03:00")
    assert r["published"] == ["20260928-11"]
    msgs = [x["message"] for x in jl(tmp_path / "processed-logs/20260928-11.jsonl")]
    assert msgs == ["first of 11", "later"]


def test_utc_timestamps_are_converted_to_kst(tmp_path):
    raw = json.dumps(
        {"timestamp": "2026-09-28T01:30:00.5Z", "level": "INFO", "message": "utc"}
    )
    current(tmp_path, A, [raw + "\n"], "2026-09-28 10:30:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert [
        x["message"] for x in jl(tmp_path / "processed-logs/20260928-10.jsonl")
    ] == ["utc"]


def test_rolls_and_current_files_of_two_pods_merge_into_one_hour(tmp_path):
    roll(
        tmp_path,
        A,
        "2026-09-28-10",
        [line("2026-09-28 10:10:00", A), line("2026-09-28 10:20:00", A)],
        "2026-09-28 11:00:01",
    )
    current(tmp_path, A, [line("2026-09-28 11:00:01", A)], "2026-09-28 11:00:01")
    current(
        tmp_path,
        B,
        [line("2026-09-28 10:30:00", B), line("2026-09-28 10:50:00", B)],
        "2026-09-28 10:50:00",
    )
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert s["processed"] == 4 and s["by_pod"] == {A: 2, B: 2}
    assert s["lines_in"] == s["processed"] + s["dropped"] + s["malformed"]
    # the roll of 10 moved to done/, both current files stayed (both pods are listed)
    assert (tmp_path / "done/20260928" / f"polaris-{A}.log.2026-09-28-10.gz").exists()
    assert (tmp_path / f"polaris-{A}.log").exists() and (
        tmp_path / f"polaris-{B}.log"
    ).exists()


def test_a_roll_of_the_next_hour_contributes_its_boundary_skew_lines(tmp_path):
    # thread race at the boundary: a 10:59:59.9 record written after the 11:00 rotation
    roll(
        tmp_path,
        A,
        "2026-09-28-11",
        [
            line("2026-09-28 11:00:00", A, "rotated it"),
            line("2026-09-28 10:59:59", A, "skew"),
        ],
        "2026-09-28 12:00:00",
    )
    c = cfg(tmp_path)
    run(c, "2026-09-28 12:03:00")  # catch-up publishes 10 and 11
    assert [
        x["message"] for x in jl(tmp_path / "processed-logs/20260928-10.jsonl")
    ] == ["skew"]
    assert [
        x["message"] for x in jl(tmp_path / "processed-logs/20260928-11.jsonl")
    ] == ["rotated it"]


def test_files_last_written_before_the_hour_are_not_opened(tmp_path):
    plb.ensure_dirs(str(tmp_path))
    plb.save_checkpoint(
        str(tmp_path),
        {"schema": plb.SCHEMA, "last_published": "20260928-09", "hours": {}},
    )
    put(
        tmp_path / f"polaris-{A}.log.2026-09-28-08.gz",
        b"not gzip at all",
        "2026-09-28 09:00:00",
    )
    current(tmp_path, B, [line("2026-09-28 10:05:00", B)], "2026-09-28 10:05:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert s["corrupt_files"] == [] and s["processed"] == 1


def test_other_prefixes_and_subdirectories_are_ignored(tmp_path):
    put(
        tmp_path / "polaris-sizetest-shared.log",
        line("2026-09-28 10:05:00", "x"),
        "2026-09-28 10:05:00",
    )
    (tmp_path / "legacy-shared").mkdir()
    put(
        tmp_path / "legacy-shared/polaris.log",
        line("2026-09-28 10:05:00", "x"),
        "2026-09-28 10:05:00",
    )
    current(tmp_path, A, [line("2026-09-28 10:06:00", A)], "2026-09-28 10:06:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert summary(tmp_path, "20260928-10")["processed"] == 1
    assert (tmp_path / "polaris-sizetest-shared.log").exists()


def test_an_empty_hour_is_published_empty_not_skipped(tmp_path):
    current(
        tmp_path,
        A,
        [line("2026-09-28 10:05:00", A), line("2026-09-28 12:10:00", A)],
        "2026-09-28 12:10:00",
    )
    r = run(cfg(tmp_path), "2026-09-28 13:03:00")
    assert r["published"] == ["20260928-10", "20260928-11", "20260928-12"]
    assert (tmp_path / "processed-logs/20260928-11.jsonl").read_text() == ""
    assert summary(tmp_path, "20260928-11")["lines_in"] == 0


# ------------------------------------------------------------------ files being written


def test_an_unterminated_last_line_is_not_read(tmp_path):
    data = line("2026-09-28 10:10:00", A) + '{"timestamp":"2026-09-28T10:59:5'
    put(tmp_path / f"polaris-{A}.log", data, "2026-09-28 11:02:50")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert s["processed"] == 1 and s["malformed"] == 0


def test_malformed_line_is_booked_once_to_the_previous_valid_hour(tmp_path):
    current(
        tmp_path,
        A,
        [
            line("2026-09-28 10:50:00", A),
            "garbage, not json\n",
            line("2026-09-28 11:10:00", A),
        ],
        "2026-09-28 11:10:00",
    )
    run(cfg(tmp_path), "2026-09-28 12:03:00")
    bad = jl(tmp_path / "malformed/20260928-10.jsonl")
    assert (
        len(bad) == 1
        and bad[0]["line_no"] == 2
        and bad[0]["raw"] == "garbage, not json"
    )
    assert not (tmp_path / "malformed/20260928-11.jsonl").exists()
    assert summary(tmp_path, "20260928-10")["malformed"] == 1
    assert summary(tmp_path, "20260928-11")["malformed"] == 0


def test_a_fresh_undecodable_roll_defers_the_hour(tmp_path):
    put(
        tmp_path / f"polaris-{A}.log.2026-09-28-10.gz",
        gzip.compress(b"x" * 100)[:20],
        "2026-09-28 11:02:50",
    )
    current(tmp_path, A, [line("2026-09-28 10:00:01", A)], "2026-09-28 10:00:01")
    r = run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert r["status"] == "deferred" and r["published"] == []
    assert not (tmp_path / "processed-logs/20260928-10.jsonl").exists()


def test_a_stale_undecodable_roll_is_quarantined_and_the_hour_published(tmp_path):
    put(
        tmp_path / f"polaris-{A}.log.2026-09-28-10.gz",
        gzip.compress(b"x" * 100)[:20],
        "2026-09-28 11:00:00",
    )
    current(tmp_path, A, [line("2026-09-28 10:00:01", A)], "2026-09-28 10:00:01")
    r = run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert r["published"] == ["20260928-10"]
    s = summary(tmp_path, "20260928-10")
    assert [c["file"] for c in s["corrupt_files"]] == [
        f"polaris-{A}.log.2026-09-28-10.gz"
    ]
    assert (tmp_path / "malformed/files" / f"polaris-{A}.log.2026-09-28-10.gz").exists()


# ------------------------------------------------------------------ orphans


def test_orphan_moves_only_when_its_pod_is_gone_and_it_is_complete(tmp_path):
    current(
        tmp_path,
        A,
        [line("2026-09-28 10:37:00", A), line("2026-09-28 10:48:00", A)],
        "2026-09-28 10:48:00",
    )
    current(tmp_path, B, [line("2026-09-28 10:40:00", B)], "2026-09-28 10:40:00")
    run(cfg(tmp_path, pods=(B,)), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert s["processed"] == 3  # the orphan's lines are processed like any other
    assert [o["pod"] for o in s["orphans_moved"]] == [A]
    assert (
        tmp_path / "done/20260928" / f"polaris-{A}.log.2026-09-28-10.orphan"
    ).exists()
    assert not (tmp_path / f"polaris-{A}.log").exists()
    assert (tmp_path / f"polaris-{B}.log").exists()  # listed pod: never moved


def test_orphan_still_in_the_current_hour_is_left_alone(tmp_path):
    current(
        tmp_path,
        A,
        [line("2026-09-28 10:30:00", A), line("2026-09-28 11:00:30", A)],
        "2026-09-28 11:00:30",
    )
    run(cfg(tmp_path, pods=()), "2026-09-28 11:03:00")
    assert (tmp_path / f"polaris-{A}.log").exists()
    assert summary(tmp_path, "20260928-10")["orphans_moved"] == []


def test_orphan_quiet_less_than_120s_is_left_alone(tmp_path):
    # last line is in hour 10 but the file was touched 30 s ago -- something is still writing
    current(tmp_path, A, [line("2026-09-28 10:59:00", A)], "2026-09-28 11:02:30")
    run(cfg(tmp_path, pods=()), "2026-09-28 11:03:00")
    assert (tmp_path / f"polaris-{A}.log").exists()


def test_pod_list_failure_moves_no_log_but_still_publishes(tmp_path):
    current(tmp_path, A, [line("2026-09-28 10:48:00", A)], "2026-09-28 10:48:00")

    def broken():
        raise ConnectionError("apiserver unreachable")

    run(cfg(tmp_path, pods=None, lister=broken), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert s["processed"] == 1 and s["orphans_moved"] is None
    assert "apiserver unreachable" in s["pod_list_error"]
    assert (tmp_path / f"polaris-{A}.log").exists()


def test_orphan_cut_mid_write_sends_its_tail_to_malformed(tmp_path):
    data = line("2026-09-28 10:40:00", A) + '{"timestamp":"2026-09-28T10:41:0'
    put(tmp_path / f"polaris-{A}.log", data, "2026-09-28 10:41:00")
    run(cfg(tmp_path, pods=()), "2026-09-28 11:03:00")
    bad = jl(tmp_path / "malformed/20260928-10.jsonl")
    assert len(bad) == 1 and "orphaned" in bad[0]["reason"]
    s = summary(tmp_path, "20260928-10")
    assert (
        s["processed"] == 1
        and s["malformed"] == 1
        and s["orphans_moved"][0]["unterminated_tail"]
    )


def test_idle_live_pod_rolling_an_old_hour_later_is_not_counted_twice(tmp_path):
    current(tmp_path, A, [line("2026-09-28 10:40:00", A, "ten")], "2026-09-28 10:40:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")  # publishes 10 from the current file
    run(cfg(tmp_path), "2026-09-28 12:03:00")  # 11: nothing
    # 12:20 -- the idle pod writes: its file rolls to -10.gz first, then the new line
    os.remove(tmp_path / f"polaris-{A}.log")
    roll(
        tmp_path,
        A,
        "2026-09-28-10",
        [line("2026-09-28 10:40:00", A, "ten")],
        "2026-09-28 12:20:00",
    )
    current(
        tmp_path, A, [line("2026-09-28 12:20:00", A, "twelve")], "2026-09-28 12:20:00"
    )
    run(cfg(tmp_path), "2026-09-28 13:03:00")
    assert [
        x["message"] for x in jl(tmp_path / "processed-logs/20260928-12.jsonl")
    ] == ["twelve"]
    assert [
        x["message"] for x in jl(tmp_path / "processed-logs/20260928-10.jsonl")
    ] == ["ten"]
    assert (tmp_path / "done/20260928" / f"polaris-{A}.log.2026-09-28-10.gz").exists()


def test_idle_listed_pod_is_reported_not_moved(tmp_path):
    current(tmp_path, A, [line("2026-09-28 09:40:00", A)], "2026-09-28 09:40:00")
    current(tmp_path, B, [line("2026-09-28 10:10:00", B)], "2026-09-28 10:10:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    s = summary(tmp_path, "20260928-10")
    assert [i["pod"] for i in s["idle_log_files"]] == [A]
    assert (tmp_path / f"polaris-{A}.log").exists()


# ------------------------------------------------------------------ exactly once


def test_crash_before_the_checkpoint_redoes_the_hour_to_the_same_lines(
    tmp_path, monkeypatch
):
    current(
        tmp_path,
        A,
        [line("2026-09-28 10:10:00", A), line("2026-09-28 10:20:00", A)],
        "2026-09-28 10:20:00",
    )
    real = plb.save_checkpoint

    def crash(*a, **k):
        raise RuntimeError("killed")

    monkeypatch.setattr(plb, "save_checkpoint", crash)
    with pytest.raises(RuntimeError):
        run(cfg(tmp_path), "2026-09-28 11:03:00")
    first = (tmp_path / "processed-logs/20260928-10.jsonl").read_bytes()
    assert plb.load_checkpoint(str(tmp_path))["last_published"] is None
    monkeypatch.setattr(plb, "save_checkpoint", real)
    r = run(cfg(tmp_path), "2026-09-28 11:05:00")
    assert r["published"] == ["20260928-10"]
    assert (tmp_path / "processed-logs/20260928-10.jsonl").read_bytes() == first
    assert plb.load_checkpoint(str(tmp_path))["last_published"] == "20260928-10"


def test_a_published_hour_is_never_redone(tmp_path):
    current(tmp_path, A, [line("2026-09-28 10:10:00", A)], "2026-09-28 10:10:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    r = run(cfg(tmp_path), "2026-09-28 11:30:00")
    assert r["published"] == []


def test_catch_up_is_bounded_per_run(tmp_path):
    current(tmp_path, A, [line("2026-09-28 01:10:00", A)], "2026-09-28 01:10:00")
    r = run(cfg(tmp_path, max_hours=3), "2026-09-28 11:03:00")
    assert r["published"] == ["20260928-01", "20260928-02", "20260928-03"]
    r = run(cfg(tmp_path, max_hours=100), "2026-09-28 11:03:00")
    assert r["published"][-1] == "20260928-10" and len(r["published"]) == 7


def test_hour_is_not_published_before_the_grace(tmp_path):
    current(tmp_path, A, [line("2026-09-28 10:10:00", A)], "2026-09-28 10:10:00")
    assert run(cfg(tmp_path), "2026-09-28 11:00:30")["published"] == []
    assert run(cfg(tmp_path), "2026-09-28 11:01:30")["published"] == ["20260928-10"]


def test_a_held_lock_skips_the_run(tmp_path):
    plb.ensure_dirs(str(tmp_path))
    with open(tmp_path / ".state/lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert r["status"] == "locked"


def test_dry_run_writes_nothing(tmp_path):
    current(tmp_path, A, [line("2026-09-28 10:10:00", A)], "2026-09-28 10:10:00")
    r = run(cfg(tmp_path, dry_run=True), "2026-09-28 11:03:00")
    assert r["published"] == ["20260928-10"]
    assert not list((tmp_path / "processed-logs").iterdir())
    assert plb.load_checkpoint(str(tmp_path))["last_published"] is None


# ------------------------------------------------------------------ retention


def test_retention_deletes_outputs_and_done_older_than_three_days(tmp_path):
    plb.ensure_dirs(str(tmp_path))
    old = put(
        tmp_path / "processed-logs/20260924-10.jsonl", "{}\n", "2026-09-24 11:03:00"
    )
    (tmp_path / "done/20260924").mkdir(parents=True)
    old_done = put(tmp_path / "done/20260924/x.gz", b"x", "2026-09-24 11:03:00")
    current(tmp_path, A, [line("2026-09-28 10:10:00", A)], "2026-09-28 10:10:00")
    run(cfg(tmp_path), "2026-09-28 11:03:00")
    assert not old.exists() and not old_done.exists()
    assert not (tmp_path / "done/20260924").exists()
    assert (tmp_path / "processed-logs/20260928-10.jsonl").exists()


def test_the_real_2tklb_orphan_shape(tmp_path):
    """HPA removed 2tklb at ~23:00 on 09-27 leaving 22:37-22:48 unrotated (#48)."""
    pod = "benchmarks-polaris-7f4d69c67c-2tklb"
    current(
        tmp_path,
        pod,
        [line(f"2026-09-27 22:{m:02d}:00", pod) for m in range(37, 49)],
        "2026-09-27 22:48:00",
    )
    current(
        tmp_path,
        "benchmarks-polaris-7f4d69c67c-bmt4t",
        [line("2026-09-27 23:02:00", "b")],
        "2026-09-27 23:02:00",
    )
    run(
        cfg(
            tmp_path,
            pods=(
                "benchmarks-polaris-7f4d69c67c-bmt4t",
                "benchmarks-polaris-7f4d69c67c-rz56d",
            ),
        ),
        "2026-09-27 23:03:00",
    )
    s = summary(tmp_path, "20260927-22")
    assert s["processed"] == 12
    assert (
        tmp_path / "done/20260927" / f"polaris-{pod}.log.2026-09-27-22.orphan"
    ).exists()
