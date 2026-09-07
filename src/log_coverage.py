"""
log_coverage.py
===============
The logic behind `log-coverage/polaris_log_coverage.ipynb`: what the Polaris ->
Fluent Bit -> VictoriaLogs pipeline is EXPECTED to store, what it actually
stored, and the difference.

THE EXPECTED COLUMN IS NOT A TABLE ANYONE TYPED
-----------------------------------------------
`PLAN-log-coverage.md` section 3 contains a hand-computed prediction of what
each of the 43 driven operations should produce. It is useful for arguing
about; it is exactly the wrong thing to measure against, because a table
someone typed drifts from the filter it describes and nothing warns -- which is
the failure mode both of these repos exist to avoid (`local-k8s`
`.memory/README.md`: *written is not live*).

So `Policy.predict()` extracts `polaris_access_log` and `polaris_noise_filter`
out of the DEPLOYED `logging/fb-values.yaml` and runs them under a real Lua
interpreter, over synthetic records shaped exactly like the ones Fluent Bit
tails. The same mechanism `local-k8s/logging/scripts/test-polaris-filters.py`
already uses, for the same reason: *the tests cannot drift from what ships*.

**There is deliberately no Python re-implementation to fall back on.** A port
that agrees with itself is not evidence, and the first time it disagreed with
the Lua the notebook would report a pipeline finding that was really a
translation bug. If the values file or a Lua binary is missing, `load_policy`
raises and the expected column is reported as UNAVAILABLE.

BOTH FILTERS, IN ORDER, NOT JUST THE SECOND
-------------------------------------------
`predict` runs `polaris_access_log` first and feeds its output to
`polaris_noise_filter`, because that is the deployed order and because the
parse is where the interesting edge cases live: a query string travels into the
dedup key, `%b` writes `-` for a zero-byte body, and a line that does not parse
has no `http_status` at all and is kept by rule 3's null branch.

STATE IS REAL AND IS THE POINT
------------------------------
`polaris_noise_filter` keeps two day-buckets of seen keys in module-local Lua
state. One `predict()` call runs the whole sequence in ONE interpreter, so
asking it for twenty identical table GETs returns keep, drop, drop ... exactly
as the shipper would. That is what makes the section 5 policy probes
predictable rather than merely observed.

THREE-WAY COVERAGE, NOT A PERCENTAGE
------------------------------------
The denominator comes from three unequal sources and they are kept apart, the
argument being `diagnostics/api-sql-profile/probe_api_surface.py`'s and not
re-litigated here:

    spec       the 1.3.0 OpenAPI documents -- a statement about a VERSION.
               Polaris 8181/8182 serves no document (measured 2026-08-31), so
               these are vendored by `log-coverage/fetch_specs.sh`.
    captured   `doc-api-sql-matrix-*.md` -- operations a live run ISSUED
               against THIS deployment. Strongest, and a lower bound.
    driven     `api_surface.operations()` -- what this notebook itself calls.

Collapsing them into one number lets a feature-flagged endpoint this build does
not serve count as a failure, and lets a genuinely missing one hide behind the
same asterisk.
"""

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone

ACCESS_LOGGER = "io.quarkus.http.access-log"
LUA_KEY = "polaris_access_log.lua"

KEEP = "keep"
DROP = "drop"

#: Lua interpreters, in preference order. macOS ships none, but a TeX install
#: provides `luatex --luaonly`, which is a standalone Lua 5.3 -- the same
#: fallback `local-k8s/logging/scripts/test-polaris-filters.py` relies on.
LUA_CANDIDATES = (
    ("lua", ()),
    ("lua5.4", ()),
    ("lua5.3", ()),
    ("luajit", ()),
    ("luatex", ("--luaonly",)),
)


class PolicyUnavailable(RuntimeError):
    """The deployed filter could not be loaded or executed.

    Raised rather than degraded. The whole value of the expected column is that
    it came from the file that ships; an expected column computed some other
    way would be indistinguishable in the report from one that did.
    """


# ----------------------------------------------------------------------
# the deployed filter, as an oracle
# ----------------------------------------------------------------------
def lua_binary():
    for exe, pre in LUA_CANDIDATES:
        path = shutil.which(exe)
        if path:
            return [path, *pre]
    raise PolicyUnavailable(
        "no Lua interpreter found (tried "
        + ", ".join(e for e, _ in LUA_CANDIDATES)
        + "). macOS ships none; `brew install lua`, or a TeX install provides "
        "`luatex --luaonly`."
    )


def resolve_fb_values(explicit=None):
    """Find the deployed Fluent Bit values file, or None.

    In order: what the caller passed, `$FB_VALUES_PATH`, the documented
    location, and finally the sibling checkout two levels up from this repo.
    That last one resolves correctly both on the machine (`~/hynix/local-k8s`)
    and inside a Cowork mount (`.../mnt/local-k8s`), which is what lets the
    policy tests run in either place without a config file.
    """
    here = pathlib.Path(__file__).resolve().parents[1]
    for cand in (
        explicit,
        os.environ.get("FB_VALUES_PATH"),
        "~/hynix/local-k8s/logging/fb-values.yaml",
        here / ".." / ".." / "local-k8s" / "logging" / "fb-values.yaml",
    ):
        if not cand:
            continue
        q = pathlib.Path(os.path.expanduser(str(cand)))
        if q.is_file():
            return q.resolve()
    return None


def load_policy(fb_values_path=None, key=LUA_KEY):
    """Read the deployed Lua out of the Fluent Bit values file.

    `fb_values_path` comes from `init_env()` (`FB_VALUES_PATH`), defaulting to
    `~/hynix/local-k8s/logging/fb-values.yaml`. That file is the ONE
    authoritative copy of the script -- the chart renders `luaScripts` into a
    ConfigMap mounted at `/fluent-bit/scripts/`, and nothing is passed with
    `--set`.
    """
    import yaml

    p = resolve_fb_values(fb_values_path)
    if p is None:
        raise PolicyUnavailable(
            "fb-values.yaml not found. Set fb_values_path in "
            "src/config/local.yaml (see local.example.yaml), or export "
            "FB_VALUES_PATH."
        )
    raw = p.read_bytes()
    doc = yaml.safe_load(raw.decode("utf-8"))
    scripts = (doc or {}).get("luaScripts") or {}
    if key not in scripts:
        raise PolicyUnavailable(
            f"{p} has no luaScripts['{key}'] (found: {sorted(scripts)})"
        )
    return Policy(
        script=scripts[key],
        sha256=hashlib.sha256(raw).hexdigest(),
        source=str(p),
        values=(doc or {}),
    )


def deployed_policy_status(configmap_yaml, policy, key=LUA_KEY):
    """Is the policy in the values file the policy that is RUNNING?

    Returns (verdict, detail) where verdict is True (the ConfigMap carries the
    same script), False (it does not), or None (could not tell -- no kubectl,
    or nothing recognisable in the YAML).

    WHY THIS GUARD EXISTS, AND IT IS NOT HYPOTHETICAL. On its first run
    (2026-09-04) this notebook reported that NOTHING was dropped: 20 identical
    table GETs all stored, every successful POST stored, the OAuth token
    exchange stored. The retention policy was not broken -- it had never been
    installed. `logging/fb-values.yaml` gained `polaris_noise_filter` in commit
    2120ed9 at 08:26:18Z on 2026-09-03; the shipper pod had been running since
    08:04:06Z, from commit 60b94d9, which has the access-log parser and no noise
    filter. Parsed fields present, zero drops -- exactly what was measured.

    That is this repo's signature failure (`local-k8s` `.memory/README.md`:
    *written is not live*), and a coverage matrix taken against an undeployed
    policy is a statement about a pipeline nobody is running. So the notebook
    checks the ConfigMap before it drives anything, rather than discovering it
    from the shape of the results afterwards.

    Compared on whitespace-normalised text, because Helm re-emits the block
    with its own indentation and a byte comparison would cry wolf every time.
    """
    if not configmap_yaml:
        return None, "kubectl unavailable -- cannot tell what is deployed"
    if "polaris_noise_filter" not in configmap_yaml:
        return False, (
            "the running ConfigMap has NO polaris_noise_filter. The retention "
            "policy in fb-values.yaml has never been applied -- reinstall with\n"
            "    helm upgrade --install fb-polaris-shipper fluent/fluent-bit \\\n"
            "      --version 0.58.1 -n datahub-hynix -f logging/fb-values.yaml"
        )

    def norm(t):
        return " ".join(t.split())

    want = norm(policy.script)
    have = norm(configmap_yaml)
    if want in have:
        return True, "the running ConfigMap carries this exact script"
    return False, (
        "the running ConfigMap has A polaris_noise_filter, but not the one in "
        "fb-values.yaml -- the file has been edited since the last helm upgrade"
    )


def events_table(conn):
    """Find and count the eventListener's audit table, whatever schema it is in.

    NOT `public.events`. Polaris creates its objects in `POLARIS_SCHEMA`
    (`api_trace` already knows this), and looking in `public` reports "no events
    table in this metastore" for a table that is right there -- which the
    2026-09-04 run did.

    Returns a dict with `schema`, `rows` and `sample`, or `note` when there is
    nothing to find.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_schema FROM information_schema.tables "
            "WHERE lower(table_name) = 'events' ORDER BY table_schema LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            return {"note": "no table named `events` in any schema of this metastore"}
        schema = row[0]
        cur.execute(f'SELECT count(*) FROM "{schema}".events')
        rows = cur.fetchone()[0]
        cur.execute(f'SELECT * FROM "{schema}".events LIMIT 3')
        cols = [d[0] for d in cur.description]
        sample = [dict(zip(cols, r)) for r in cur.fetchall()]
    return {"schema": schema, "rows": rows, "sample": sample}


def _lua_literal(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    s = str(value)
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'


def _lua_table(record):
    inner = ", ".join(
        f"[{_lua_literal(k)}]={_lua_literal(v)}"
        for k, v in record.items()
        if v is not None
    )
    return "{" + inner + "}"


class Policy:
    """The deployed retention policy, executable.

    Attributes:
        script: the Lua source, straight out of `luaScripts`.
        sha256: digest of the WHOLE values file, quoted in the report so a
            later reader can tell which policy the expected column came from.
        source: where it was read from.
    """

    def __init__(self, script, sha256, source, values=None):
        self.script = script
        self.sha256 = sha256
        self.source = source
        #: the WHOLE parsed values file. The report's cadence is not in the Lua
        #: at all -- the tick comes from a `dummy` INPUT in the Fluent Bit
        #: config, and the relationship between that interval and
        #: WINDOW_SECONDS is what decides whether a window can be skipped.
        self.values = values or {}

    def predict(self, records):
        """Run both filters over `records`, in order, in ONE interpreter.

        Args:
            records: the RAW records Fluent Bit tails, after the `modify`
                filter renames `message`->`_msg` and `timestamp`->`_time`.
                Build them with `access_log_record()` / `app_log_record()`.

        Returns:
            list of dicts: `verdict` ("keep"/"drop"), plus the fields the
            access-log parser extracted (`http_method`, `http_status`,
            `api_path`, `user_principal_name`, `response_size`) or None for a
            record it left alone.

        State carries ACROSS the list, deliberately -- rule 6's day-buckets are
        what make "the same table GET twenty times" predictable.
        """
        records = list(records)
        if not records:
            return []
        driver = [
            self.script,
            "",
            "local RECORDS = {",
        ]
        driver += [f"  {_lua_table(r)}," for r in records]
        driver += [
            "}",
            "for i = 1, #RECORDS do",
            "  local rec = RECORDS[i]",
            '  local _, _, r1 = polaris_access_log("t", 0, rec)',
            "  local r = r1 or rec",
            '  local code = polaris_noise_filter("t", 0, r)',
            "  local function s(v) if v == nil then return '' end return tostring(v) end",
            '  print(table.concat({i, code, s(r["http_method"]), s(r["http_status"]),',
            '        s(r["api_path"]), s(r["user_principal_name"]), s(r["response_size"]),',
            '        s(r["access_log_parse_error"])}, "\\t"))',
            "end",
        ]
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "predict.lua"
            f.write_text("\n".join(driver), encoding="utf-8")
            proc = subprocess.run(
                lua_binary() + [str(f)], capture_output=True, text=True
            )
        if proc.returncode != 0:
            raise PolicyUnavailable(
                f"the deployed Lua failed to run:\n{proc.stderr.strip()[:2000]}"
            )
        out = []
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            _, code, method, status, path, user, size, parse_err = parts[:8]
            out.append(
                {
                    #: -1 is Fluent Bit's "drop this record". 0 and 2 are
                    #: "keep" -- 0 unmodified, 2 modified-with-original-
                    #: timestamp. Nothing else is emitted by this filter.
                    "verdict": DROP if code.strip() == "-1" else KEEP,
                    "code": int(code),
                    "http_method": method or None,
                    "http_status": int(status) if status.strip() else None,
                    "api_path": path or None,
                    "user_principal_name": user or None,
                    "response_size": int(size) if size.strip() else None,
                    "parse_error": bool(parse_err.strip()),
                }
            )
        if len(out) != len(records):
            raise PolicyUnavailable(
                f"the Lua returned {len(out)} verdicts for {len(records)} records"
            )
        return out

    def verdicts(self, records):
        return [r["verdict"] for r in self.predict(records)]

    # ------------------------------------------------------------------
    # policy v3: records and report ticks in one interpreter
    # ------------------------------------------------------------------
    @property
    def window_seconds(self):
        """`WINDOW_SECONDS` as DEPLOYED. Never hardcode it, and never pass a
        different one to `report_windows` -- the filter derives its window
        index from its own constant, so a caller that assumes 60 while the
        shipper runs 1800 crosses no boundary, gets no report back, and sees an
        empty result rather than an error. That failure cost a debugging round
        on 2026-09-04, which is why `report_windows` now refuses a mismatch.
        """
        m = re.search(r"^\s*(?:local\s+)?WINDOW_SECONDS\s*=\s*(\d+)", self.script, re.M)
        if not m:
            raise PolicyUnavailable(
                "WINDOW_SECONDS is not in the deployed script -- this is not policy v3"
            )
        return int(m.group(1))

    @property
    def tick_seconds(self):
        """`Interval_Sec` of the `dummy` INPUT that drives the report, as
        DEPLOYED, or None if it cannot be found.

        THE TICK RATE IS NOT THE REPORT PERIOD -- but it bounds two things the
        period cannot. It bounds the STARTUP BLIND SPOT (records processed
        before the first tick are counted into no window), and if it ever
        reaches WINDOW_SECONDS it makes a SKIPPED WINDOW possible: a tick that
        arrives late moves the window index by two, the filter reports the
        window it was holding, and the one in between never existed at all.
        """
        #: `config.inputs` in the chart's values, NOT "any string containing
        #: [INPUT]" -- the Lua script itself talks about the dummy INPUT in a
        #: comment, and a looser search matches that instead.
        cfg = ((self.values.get("config") or {}).get("inputs")) or ""
        if not isinstance(cfg, str) or "[INPUT]" not in cfg:
            return None
        for block in cfg.split("[INPUT]")[1:]:
            head = block.split("[")[0]
            if REPORT_TAG in head:
                m = re.search(r"Interval_Sec\s+(\d+)", head)
                return int(m.group(1)) if m else None
        return None

    def run(self, events):
        """Run records and `Tick`s through the deployed filter, IN ORDER.

        Args:
            events: a sequence mixing record dicts (from `access_log_record` /
                `app_log_record`) and `Tick` objects.

        Returns:
            `(verdicts, reports)`. `verdicts` is one dict per RECORD event, in
            order, shaped exactly like `predict()`'s. `reports` maps each tick
            label that actually emitted to its list of report rows, with Lua
            numbers converted to ints and `partial_window` left as the string
            the filter writes.

        THE ORDER MATTERS AND IS NOT COSMETIC. `report_tick` opens its first
        window ON THE FIRST TICK: until one arrives `counts` is nil and
        `count_record()` returns immediately, so records fed before the first
        tick are routed by the policy but counted into no window at all. That
        is a real property of the deployed filter -- bounded by the tick period
        in production -- and the reason this method exists instead of a
        `predict()` that takes a `now`.
        """
        events = list(events)
        if not events:
            return [], {}
        driver = [self.script, "", _LUA_RUN_HELPERS]
        for n, ev in enumerate(events):
            if isinstance(ev, Tick):
                driver.append(f"nb_tick({ev.at}, {_lua_literal(ev.label)})")
            else:
                driver.append(f"nb_record({n}, {_lua_table(ev)})")
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "run.lua"
            f.write_text("\n".join(driver), encoding="utf-8")
            proc = subprocess.run(
                lua_binary() + [str(f)], capture_output=True, text=True
            )
        if proc.returncode != 0:
            raise PolicyUnavailable(
                f"the deployed Lua failed to run:\n{proc.stderr.strip()[:2000]}"
            )

        verdicts, rows, shapes = {}, {}, {}
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if parts[0] == "V" and len(parts) >= 9:
                _, n, code, method, status, path, user, size, parse_err = parts[:9]
                verdicts[int(n)] = {
                    "verdict": DROP if code.strip() == "-1" else KEEP,
                    "code": int(code),
                    "http_method": method or None,
                    "http_status": int(status) if status.strip() else None,
                    "api_path": path or None,
                    "user_principal_name": user or None,
                    "response_size": int(size) if size.strip() else None,
                    "parse_error": bool(parse_err.strip()),
                }
            elif parts[0] == "T" and len(parts) >= 5:
                shapes[parts[1]] = {
                    "code": int(parts[2]),
                    "returns": parts[3],
                    "n": int(parts[4]),
                }
            elif parts[0] == "R" and len(parts) >= 6:
                _, label, idx, key, lua_type, value = parts[:6]
                rows.setdefault(label, {}).setdefault(int(idx), {})[key] = _coerce(
                    lua_type, value
                )

        n_records = sum(1 for e in events if not isinstance(e, Tick))
        if len(verdicts) != n_records:
            raise PolicyUnavailable(
                f"the Lua returned {len(verdicts)} verdicts for {n_records} records"
            )
        ordered = [verdicts[n] for n in sorted(verdicts)]
        reports = {
            label: [by_idx[i] for i in sorted(by_idx)] for label, by_idx in rows.items()
        }
        for label, shape in shapes.items():
            if shape["n"] == 0 and label in reports:
                continue
            if shape["n"] and shape["returns"] != "table":
                raise PolicyUnavailable(
                    f"tick {label} returned {shape['returns']}, not a table"
                )
        self.last_tick_shapes = shapes
        return ordered, reports

    def report_windows(self, records, seconds=None, base=None, silent_windows=2):
        """The standard scheduled-report sequence, without sleeping.

        Opens a window, feeds `records` into it, then crosses
        `silent_windows + 1` boundaries. Returns `(verdicts, reports)` with the
        reports labelled `w1`, `w2`, ... -- `w1` holds the traffic, `w2` proves
        ZERO-CARRY (a resource active in w1 emits an explicit 0) and `w3`
        proves CARRY DECAY (a row that stayed 0 is not carried a third time).

        `base` defaults to the current window's start, so the synthetic records
        and the ticks agree about which window they are in.
        """
        deployed = self.window_seconds
        seconds = deployed if seconds is None else int(seconds)
        if seconds != deployed:
            raise PolicyUnavailable(
                f"asked for {seconds}s windows but the deployed filter runs "
                f"{deployed}s. It indexes windows with its OWN constant, so this "
                "would silently cross no boundary and emit no report."
            )
        if base is None:
            base = window_bounds(time.time(), seconds)[0]
        events = [Tick(base + 1, "open")]
        events += list(records)
        for i in range(silent_windows + 1):
            events.append(Tick(base + (i + 1) * seconds + 1, f"w{i + 1}"))
        verdicts, reports = self.run(events)
        missing = [
            f"w{i + 1}"
            for i in range(silent_windows + 1)
            if not reports.get(f"w{i + 1}")
        ]
        if missing:
            raise PolicyUnavailable(
                f"no report came back for {', '.join(missing)} -- the ticks did not "
                "cross a boundary the filter recognised"
            )
        return verdicts, reports

    def classify_paths(self, paths, method="GET", status=200, user="oracle"):
        """`{path: (resource_key, resource_kind)}`, from the deployed classify().

        `classify()` is local to the Lua and cannot be called directly, and
        re-implementing `RESOURCE_PATTERNS` in Python is exactly the thing this
        module refuses to do. So each path is driven through its OWN window and
        the resource row the filter emits IS the answer.
        """
        paths = list(paths)
        seconds, base = self.window_seconds, 0
        events, labels = [Tick(base + 1, "open")], []
        for i, path in enumerate(paths):
            events.append(access_log_record(method, path, status, size=1, user=user))
            label = f"p{i}"
            events.append(Tick(base + (i + 1) * seconds + 1, label))
            labels.append(label)
        _, reports = self.run(events)
        out = {}
        for path, label in zip(paths, labels):
            #: Every window after the first also carries the PREVIOUS window's
            #: keys, seeded at zero -- that is the zero-carry behaviour, and it
            #: means "the only resource row" is the wrong selector. The row this
            #: path incremented is the one with a non-zero request count.
            rows = [
                r
                for r in reports.get(label, [])
                if r.get("report_type") == "resource" and r.get("requests")
            ]
            out[path] = (
                (rows[0].get("resource"), rows[0].get("resource_kind"))
                if len(rows) == 1
                else (None, None)
            )
        return out


# ----------------------------------------------------------------------
# building the records the shipper would see
# ----------------------------------------------------------------------
def access_log_line(
    method, path, status, size=0, user="root", ip="192.168.194.1", when=None
):
    """One Quarkus access-log line, pattern `%h %l %u %t "%r" %s %b`.

    `%b` writes `-` for a zero-byte body -- CLF for 0, not for unknown -- and
    the parser normalises it. Passing size=0 produces the `-` form on purpose,
    because that is what a 204 actually writes.
    """
    stamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000", time.gmtime(when or time.time()))
    body = "-" if not size else str(size)
    return f'{ip} - {user} [{stamp}] "{method} {path} HTTP/1.1" {status} {body}'


def access_log_record(
    method,
    path,
    status,
    size=0,
    user="root",
    level="INFO",
    time_rfc3339=None,
    when=None,
):
    """A record shaped like the one the Lua filters receive.

    That is AFTER the `modify` filter (`message`->`_msg`,
    `timestamp`->`_time`, `app=polaris` added) and BEFORE the Lua -- which is
    the only point in the chain where the retention decision is made.
    """
    t = time_rfc3339 or time.strftime(
        "%Y-%m-%dT%H:%M:%S.000000000Z", time.gmtime(when or time.time())
    )
    return {
        "app": "polaris",
        "level": level,
        "loggerName": ACCESS_LOGGER,
        "_time": t,
        "_msg": access_log_line(method, path, status, size, user, when=when),
    }


def app_log_record(
    message,
    level="INFO",
    logger="org.apache.polaris.service.admin",
    time_rfc3339=None,
):
    """A non-access-log record -- rule 2's "keep, untouched" path."""
    return {
        "app": "polaris",
        "level": level,
        "loggerName": logger,
        "_time": time_rfc3339
        or time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z", time.gmtime()),
        "_msg": message,
    }


#: Polaris serves the Management API under this prefix and the Iceberg REST
#: Catalog API under `/api/catalog/v1`. `api_surface` op paths are written
#: WITHOUT the prefix (`/v1/catalogs`), because that is how the SQL matrix
#: reports them; the access log records the full path, so predictions have to
#: be made against the full path or rule 5/6's patterns match differently.
MGMT_PREFIX = "/api/management"
CAT_PREFIX = "/api/catalog"


def full_path(api, path):
    """`("management", "/v1/catalogs")` -> `/api/management/v1/catalogs`."""
    prefix = MGMT_PREFIX if api == "management" else CAT_PREFIX
    return prefix + path if path.startswith("/v1") else prefix + "/v1" + path


# ----------------------------------------------------------------------
# the three inventories
# ----------------------------------------------------------------------
_PARAM = re.compile(r"\{[^}]*\}")


def canonical(path):
    """Compare paths across sources: drop the query, the API prefix and the
    `/v1`, and make every path parameter anonymous.

    `{prefix}` in the Iceberg spec and `{cat}` in the harness are the same
    slot; `probe_api_surface.py` learned that the hard way and this is the same
    normalisation.
    """
    p = (path or "").split("?", 1)[0]
    for pre in (MGMT_PREFIX, CAT_PREFIX):
        if p.startswith(pre):
            p = p[len(pre) :]
    if p.startswith("/v1"):
        p = p[3:]
    p = _PARAM.sub("{}", p)
    return "/" + p.strip("/")


def api_of(label_or_path):
    """ "management" or "catalog", from an `api_surface` label or a path."""
    s = str(label_or_path)
    if s.startswith("mgmt.") or s.startswith(MGMT_PREFIX):
        return "management"
    return "catalog"


def key_of(api, method, path):
    return (api, method.upper(), canonical(path))


def driven_inventory(items):
    """What this notebook calls.

    Accepts either `api_surface.operations()` or the rows `drive_tagged`
    returns, and **prefer the rows**. The op templates abbreviate long paths
    (`/v1/{cat}/.../tables/{tbl}`), and an ellipsis is not a path: it
    canonicalises to something that matches nothing in either spec, exactly as
    `query_profile.parse_api_matrix` found when it started dropping them. A
    driven row carries `actual_path`, which is the URL that was really issued.
    """
    out = {}
    for it in items:
        if isinstance(it, dict):
            label, method = it["label"], it["method"]
            path = it.get("actual_path") or it["path"]
        else:
            label, method, path = it.label, it.method, it.path
        if "..." in path:
            #: Unresolvable, and guessing what the ellipsis stood for is how a
            #: coverage number becomes fiction. Drive from rows, not templates.
            continue
        api = api_of(label)
        k = key_of(api, method, path)
        row = out.setdefault(
            k,
            {
                "source": "driven",
                "api": api,
                "method": method.upper(),
                "path": canonical(path),
                "labels": [],
            },
        )
        if label not in row["labels"]:
            row["labels"].append(label)
    return out


def captured_inventory(reports_dir):
    """From the newest `doc-api-sql-matrix-*.md` that actually parses.

    By CONTENT, not by name: `-latest.md` is a copy whose mtime says nothing
    about which run produced it, and a report that yields no operations is not
    a newer inventory, it is a broken one. Same rule as
    `probe_api_surface.newest_matrix`.
    """
    import query_profile as qp

    d = pathlib.Path(reports_dir)
    if not d.is_dir():
        return {}, None
    named = [p for p in d.glob("doc-api-sql-matrix-*.md") if "latest" not in p.name]
    copies = [p for p in d.glob("doc-api-sql-matrix-*.md") if "latest" in p.name]
    order = sorted(named, key=lambda p: p.stat().st_mtime, reverse=True) + sorted(
        copies, key=lambda p: p.stat().st_mtime, reverse=True
    )
    for p in order:
        ops = qp.parse_api_matrix(p.read_text(encoding="utf-8"), read_only=False)
        if ops:
            out = {}
            for method, path, label, status in ops:
                api = api_of(label if label else path)
                out[key_of(api, method, path)] = {
                    "source": "captured",
                    "api": api,
                    "method": method.upper(),
                    "path": canonical(path),
                    "labels": [label],
                    "observed_status": status,
                }
            return out, p
    return {}, None


def spec_inventory(spec_dir):
    """From the vendored 1.3.0 OpenAPI documents.

    A statement about a VERSION, never a coverage verdict: generic tables and
    policies are feature-flagged in 1.3 and may be off in this build. Returns
    ({} , []) when nothing is vendored -- `fetch_specs.sh` has not been run --
    so the notebook reports the column as absent instead of inventing it.
    """
    import yaml

    d = pathlib.Path(spec_dir)
    files = sorted(d.glob("*.yml")) + sorted(d.glob("*.yaml")) if d.is_dir() else []
    out, used = {}, []
    for f in files:
        api = "management" if "management" in f.name else "catalog"
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        paths = doc.get("paths") or {}
        if not paths:
            continue
        used.append(
            {
                "file": f.name,
                "api": api,
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                "paths": len(paths),
            }
        )
        for path, item in paths.items():
            for method, spec in (item or {}).items():
                if method.upper() not in (
                    "GET",
                    "HEAD",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                ):
                    continue
                k = key_of(api, method, path)
                out.setdefault(
                    k,
                    {
                        "source": "spec",
                        "api": api,
                        "method": method.upper(),
                        "path": canonical(path),
                        "operation_id": (spec or {}).get("operationId"),
                    },
                )
    return out, used


def coverage_rows(spec, captured, driven):
    """One row per endpoint across all three sources, with a three-way verdict.

    confirmed gap  this deployment SERVED it and the notebook does not
                   drive it. A fact, and the number that should be zero.
    unverified     driven here, never observed on this cluster before.
                   An open question, resolved by running the notebook.
    candidate      the spec names it; nothing observed it, nothing drives
                   it. May not exist in this build at all.
    driven         driven and previously observed. Nothing to report.
    """
    rows = []
    for k in sorted(set(spec) | set(captured) | set(driven)):
        api, method, path = k
        in_spec, in_cap, in_drv = k in spec, k in captured, k in driven
        if in_cap and not in_drv:
            verdict = "confirmed gap"
        elif in_drv and not in_cap:
            verdict = "unverified"
        elif in_drv and in_cap:
            verdict = "driven"
        else:
            verdict = "candidate"
        #: `or {}` at the end: an inventory entry can legitimately be an empty
        #: dict (a spec path with no operationId), and `or` would then fall
        #: through all three and hand None to `.get`.
        meta = driven.get(k) or captured.get(k) or spec.get(k) or {}
        rows.append(
            {
                "api": api,
                "method": method,
                "path": path,
                "label": ", ".join(meta.get("labels", []))
                or (spec.get(k, {}).get("operation_id") or ""),
                "in_spec": in_spec,
                "in_captured": in_cap,
                "in_driven": in_drv,
                "verdict": verdict,
            }
        )
    return rows


# ----------------------------------------------------------------------
# driving the surface with a request id per call
# ----------------------------------------------------------------------
#: `api_trace._MDC_REQUEST_ID` accepts [0-9a-zA-Z-_], so an underscore is
#: kept and everything else -- the dots in a label, the `[snapshots=refs]`
#: brackets -- folds to a dash. Stripping underscores too would still work,
#: but it makes `load_table` and `load-table` indistinguishable in an id.
_SLUG = re.compile(r"[^0-9A-Za-z_]+")


def _issued_path(resp):
    """Path + query of the request that produced `resp`, or None.

    `requests` keeps the prepared request on the response, so this is the exact
    string Quarkus wrote into `%r` -- no template expansion, no guessing which
    `{param}` held which value.
    """
    try:
        from urllib.parse import urlsplit

        parts = urlsplit(resp.request.url)
        return parts.path + (f"?{parts.query}" if parts.query else "")
    except Exception:  # noqa: BLE001
        return None


def request_id(run, seq, label):
    """`nb-<run>-<seq>-<label>`, restricted to what an MDC value survives.

    `api_trace._MDC_REQUEST_ID` accepts `[0-9a-zA-Z-_]`, so anything else in an
    operation label -- the dots, the `[snapshots=refs]` brackets -- is folded
    to a dash here rather than discovering later that half the ids did not come
    back.
    """
    return f"nb-{run}-{seq:03d}-{_SLUG.sub('-', label).strip('-')}"


def clients_of(ctx_or_clients):
    """The distinct REST clients in a `SurfaceContext`, or an iterable of them.

    `ctx.adm` is included: the fixture's own calls are part of the test --
    `POST /v1/catalogs` is one of the dropped mutations being measured -- so
    leaving admin untagged would make exactly the interesting calls the
    untraceable ones.
    """
    if hasattr(ctx_or_clients, "ic"):
        cands = (ctx_or_clients.ic, ctx_or_clients.pc, ctx_or_clients.adm)
    else:
        cands = tuple(ctx_or_clients)
    return list({id(c): c for c in cands if c is not None}.values())


def tag_clients(ctx_or_clients, value, header="Polaris-Request-Id"):
    """Set (or clear, with value=None) the request-id header on every client."""
    for client in clients_of(ctx_or_clients):
        headers = dict(getattr(client, "extra_headers", {}) or {})
        if value is None:
            headers.pop(header, None)
        else:
            headers[header] = value
        client.extra_headers = headers


def call_once(
    clients,
    run,
    seq,
    label,
    fn,
    method="",
    path="",
    header="Polaris-Request-Id",
    principals=None,
):
    """One tagged call outside the 43-op surface, in `drive_tagged`'s row shape.

    The negative cases and the policy probes are not operations in
    `api_surface` -- they are the same endpoints called deliberately wrong, or
    called twenty times -- but they belong in the same table, so they produce
    the same row.
    """
    rid = request_id(run, seq, label)
    tag_clients(clients, rid, header)
    started = time.perf_counter()
    row = {
        "seq": seq,
        "label": label,
        "method": method.upper(),
        "path": path,
        "actual_path": None,
        #: WHEN the call went out, so the matrix can say which report window
        #: it was counted into. A counted call leaves no individual record, so
        #: there is nowhere else to read its window from.
        "issued_at": time.time(),
        #: Filled from the request's own Authorization header, never assumed.
        "principal": None,
        "api": api_of(label if label.startswith(("mgmt.", "iceberg.")) else path),
        "request_id": rid,
        "status": None,
        "elapsed_ms": None,
        "error": None,
        "echoed_request_id": None,
    }
    try:
        resp = fn()
        row["status"] = getattr(resp, "status_code", None)
        row["actual_path"] = _issued_path(resp)
        row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        row["echoed_request_id"] = getattr(resp, "headers", {}).get(header)
        if principals:
            row["principal"] = principal_of(resp, principals)
        if not row["method"]:
            row["method"] = getattr(getattr(resp, "request", None), "method", "") or ""
    except Exception as exc:  # noqa: BLE001
        row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        tag_clients(clients, None, header)
    return row


def provision_run_principal(adm_pc, name, prole, fixture=None, service_admin=True):
    """Create the run's own principal, and return its credentials.

    WHY A PRINCIPAL PER RUN. `user_principal_name` is `%u` from the access log
    and is the FALLBACK correlation key -- the one that still works if Polaris
    turns out not to honour a client-supplied `Polaris-Request-Id`. Driving as
    `root` would put "root" on every record and leave the run unselectable, so
    the fallback has to be provisioned before it is needed, not after.

    `service_admin` because the drive must actually EXECUTE every operation:
    the question here is what the pipeline stores, not who is allowed to do
    what, and a 403 answers a different question (`privilege/` answers that
    one). `fixture` additionally grants the probe catalog's rights, because
    catalog operations authorize against `grant_records` for the TARGET
    catalog and `service_admin` does not cover them -- the correction
    `api_surface.authorize_on_fixture` records.

    Returns (client_id, client_secret). NEVER print these: notebooks get
    committed.
    """
    r = adm_pc.create_principal(name)
    if r.status_code not in (200, 201):
        raise RuntimeError(
            f"create_principal {name} -> [{r.status_code}] {r.text[:300]}"
        )
    creds = (r.json() or {}).get("credentials") or {}
    cid, secret = creds.get("clientId"), creds.get("clientSecret")
    if not cid or not secret:
        raise RuntimeError(
            f"create_principal {name} returned no credentials; "
            f"keys={sorted(r.json() or {})}"
        )
    adm_pc.create_principal_role(prole)
    adm_pc.assign_principal_role_to_principal(name, prole)
    if service_admin:
        adm_pc.assign_principal_role_to_principal(name, "service_admin")
    if fixture is not None:
        import api_surface as _surf

        _surf.authorize_on_fixture(fixture, adm_pc, prole)
    return cid, secret


def elect_drive_identity(
    adm_pc, adm_ic, base_url, realm, principal, prole, fixture=None, root_token=None
):
    """Provision the run's principal and prove it can drive, or fall back to root.

    WHY THIS IS AN ELECTION AND NOT A CHOICE. Two facts pull in opposite
    directions and neither is safe to assume:

      * `%u` in the access log is the FALLBACK correlation key, so the run
        wants its own principal -- driving as `root` writes "root" on every
        record and leaves the run unselectable if `Polaris-Request-Id` turns
        out not to be honoured.
      * `polaris_test_utils.get_token` records that a NON-ROOT principal
        generally cannot request `PRINCIPAL_ROLE:ALL` -- it yields a token with
        no effective role, and every call then 403s. Which scope works depends
        on the build.

    A 403 here would be a fixture bug wearing a finding's clothes: the notebook
    would report endpoints as "not callable" that are merely unauthorized, and
    the coverage matrix would be a statement about this function rather than
    about the pipeline. So the identity is VERIFIED before it is used -- one
    management read and one catalog read -- and demoted to root, loudly, if it
    cannot do both.

    Returns (label, pc, ic, principal_name, notes).
    """
    from iceberg_rest import IcebergREST
    from polaris_rest import PolarisREST

    notes = []
    try:
        cid, secret = provision_run_principal(
            adm_pc, principal, prole, fixture=fixture, service_admin=True
        )
    except Exception as exc:  # noqa: BLE001
        notes.append(f"could not provision {principal}: {type(exc).__name__}: {exc}")
        return "root", adm_pc, adm_ic, "root", notes

    for scope in ("PRINCIPAL_ROLE:ALL", f"PRINCIPAL_ROLE:{prole}"):
        r = adm_pc.get_token(cid, secret, scope=scope)
        if r.status_code != 200:
            notes.append(f"token scope={scope} -> [{r.status_code}]")
            continue
        tok = r.json().get("access_token")
        pc = PolarisREST(base_url, realm, token=tok)
        ic = IcebergREST(base_url, realm, token=tok)
        checks = {
            "management read": pc.list_principals().status_code,
            "catalog read": (
                ic.list_namespaces(fixture.cat).status_code if fixture else 200
            ),
        }
        if all(200 <= v < 300 for v in checks.values()):
            notes.append(f"driving as {principal} (scope={scope})")
            return principal, pc, ic, principal, notes
        notes.append(f"scope={scope} rejected: {checks}")

    notes.append(
        f"DEMOTED to root: {principal} could not drive both APIs. The "
        "user_principal_name fallback key is unavailable for this run -- "
        "correlation rests entirely on mdc.requestId."
    )
    return "root", adm_pc, adm_ic, "root", notes


def deprovision_run_principal(adm_pc, name, prole):
    """Best-effort cleanup. Returns a list of what failed, never raises.

    The cleanup DELETEs are themselves part of the test, so they run inside the
    tagged window -- but a failure here must not lose the run's findings.
    """
    problems = []
    for call, what in (
        (lambda: adm_pc.delete_principal(name), f"delete_principal {name}"),
        (lambda: adm_pc.delete_principal_role(prole), f"delete_principal_role {prole}"),
    ):
        try:
            r = call()
            if r.status_code not in (200, 204, 404):
                problems.append(f"{what} -> [{r.status_code}]")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{what} -> {type(exc).__name__}: {exc}")
    return problems


def drive_tagged(
    ops, ctx, run, on_call=None, header="Polaris-Request-Id", principals=None
):
    """Issue every operation in order, each under its own request id.

    Deliberately NOT `api_surface.drive()`. That function is built around a
    `Tracer` and raises `CaptureNotRecording` when the SQL capture reads
    nothing -- correct for the API->SQL audit, meaningless here, where no SQL
    stream is attached and the measurement is what reaches VictoriaLogs.

    A refusal is data, exactly as it is there: a non-2xx is recorded and the
    drive continues. An EXCEPTION is the harness failing and is kept apart.

    `elapsed_ms` is measured client-side because there is nowhere else to get
    it: the access-log pattern has no `%D`, so **nothing in VictoriaLogs can
    say how long any request took** (source plan section 2.5). These numbers
    are the evidence for adding it.
    """
    calls = []
    for seq, op in enumerate(ops, 1):
        rid = request_id(run, seq, op.label)
        if op.prepare:
            #: Outside the tagged window: a read-back the operation does not
            #: itself issue must not be attributed to it.
            tag_clients(ctx, None, header)
            try:
                op.prepare(ctx)
            except Exception:  # noqa: BLE001
                pass
        tag_clients(ctx, rid, header)
        started = time.perf_counter()
        row = {
            "seq": seq,
            "label": op.label,
            "method": op.method.upper(),
            "path": op.path,
            #: The URL actually issued, query string included. The op template
            #: is not good enough to predict against: it abbreviates
            #: (`/v1/{cat}/.../tables/{tbl}`), and rule 6 matches
            #: `/namespaces/[^/]+/tables/[^/?]+` -- an ellipsis in place of the
            #: namespace segment turns a deduplicated read into a rule-7 keep
            #: and the expected column would be quietly wrong.
            "actual_path": None,
            #: See `call_once`: the window a counted call landed in is not
            #: recoverable from anywhere else.
            "issued_at": time.time(),
            #: The 43 operations do not all go out on the same client -- the
            #: management block uses `ctx.adm` -- so this is read off the
            #: request rather than set to the run's principal.
            "principal": None,
            "api": api_of(op.label),
            "request_id": rid,
            "status": None,
            "elapsed_ms": None,
            "error": None,
            "echoed_request_id": None,
        }
        try:
            resp = op.fn(ctx)
            row["status"] = getattr(resp, "status_code", None)
            row["actual_path"] = _issued_path(resp)
            row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
            #: Polaris echoes the header on the response. If the echo differs
            #: from what was sent, the server minted its own id and the exact
            #: correlation design is off -- cell 1 checks this once, and every
            #: row records it so a mid-run change cannot hide.
            row["echoed_request_id"] = getattr(resp, "headers", {}).get(header)
            if principals:
                row["principal"] = principal_of(resp, principals)
        except Exception as exc:  # noqa: BLE001
            row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
            row["error"] = f"{type(exc).__name__}: {exc}"
        calls.append(row)
        if on_call:
            on_call(row)
    tag_clients(ctx, None, header)
    return calls


def expected_for(calls, policy, user="root"):
    """The verdict the DEPLOYED filter gives each call in `calls`.

    Runs the whole sequence in one interpreter so rule 6's per-day dedup state
    is built up in issue order -- the same way the shipper sees it.

    Calls that raised (no status) are skipped: the request never completed, so
    there is no access-log line to predict. That is itself a finding when it
    happens, and `drive_tagged` keeps the error.
    """
    indexed = [(i, c) for i, c in enumerate(calls) if c.get("status")]
    records = [
        access_log_record(
            c["method"],
            c.get("actual_path") or full_path(c["api"], c["path"]),
            c["status"],
            user=user,
        )
        for _, c in indexed
    ]
    verdicts = policy.predict(records)
    out = [None] * len(calls)
    for (i, _), v in zip(indexed, verdicts):
        out[i] = v
    return out


# ======================================================================
# policy v3: the scheduled flush report
# ======================================================================
#: The `dummy` INPUT ticks under this tag; the filter replaces the tick with an
#: ARRAY of records on a window boundary and resets its counters. They land on
#: their own stream, so `app:polaris` queries are unaffected.
REPORT_TAG = "polaris.report"
REPORT_APP = "polaris-shipper-report"
REPORT_LEVEL = "REPORT"
SCHEMA_VERSION = 1
REPORT_OTHER = "__other__"

#: Schema v1, read off the deployed `build_report` on 2026-09-04. Field names
#: are contract: renaming one after a month of data is the expensive mistake.
ENVELOPE_FIELDS = frozenset(
    {
        "app",
        "level",
        "schema_version",
        "report_type",
        "report_seq",
        "hostname",
        "window_start",
        "window_end",
        "window_seconds",
        "_time",
        "_msg",
    }
)
SUMMARY_FIELDS = frozenset(
    {
        "access_seen",
        "access_kept",
        "access_counted",
        "counted_get",
        "counted_post",
        "errors_kept",
        "parse_errors",
        "distinct_resources",
        "distinct_principals",
        "resources_other",
        "principals_other",
        "min_record_time",
        "max_record_time",
        "partial_window",
    }
)
RESOURCE_FIELDS = frozenset(
    {
        "resource",
        "resource_kind",
        "requests",
        "reads",
        "writes",
        "errors",
        "response_bytes",
    }
)
PRINCIPAL_FIELDS = frozenset(
    {
        "user_principal_name",
        "requests",
        "reads",
        "writes",
        "errors",
        "response_bytes",
    }
)
FIELDS_BY_TYPE = {
    "summary": SUMMARY_FIELDS,
    "resource": RESOURCE_FIELDS,
    "principal": PRINCIPAL_FIELDS,
}

#: The filter writes these as "" when a window saw no records (`counts.min_time or ""`),
#: and VictoriaLogs DOES NOT STORE EMPTY VALUES -- so they are simply absent from
#: a stored quiet window. Measured 2026-09-04: every silent window reported them
#: as "missing fields".
#: Absent and empty are the same statement here, and neither is schema drift.
EMPTY_DROPPED_FIELDS = frozenset({"min_record_time", "max_record_time"})

#: VictoriaLogs adds these to every record it returns -- they are not fields the
#: filter emitted, so a strict field check must not read them as schema drift.
#: The verify run on 2026-09-04 reported all six stored rows as carrying
#: "unexpected fields" because of exactly this, which would have fired on every
#: window of the real run.
VLOGS_META = frozenset({"_stream", "_stream_id"})

#: Properties of the PROCESS that emitted the report, not of the window. The
#: oracle runs on a laptop and the pipeline runs in a pod, so comparing these
#: would report a mismatch on every row. `hostname` is
#: `os.getenv("HOSTNAME") or "unknown"`; `report_seq` is a per-process counter
#: that restarts at 1 when the shipper does; `_msg` embeds `report_seq`.
VOLATILE_FIELDS = frozenset({"hostname", "report_seq", "_msg"})

#: The six values `classify()` can return. All six must appear in a run.
RESOURCE_KINDS = ("table", "view", "collection", "namespace", "management", "other")

KEPT = "kept"
COUNTED = "counted"

#: The Lua side of `Policy.run`. Kept as one string so the driver stays boring
#: and every emitted line is `TAG \t ...` -- a format that survives a `_msg`
#: containing anything, because tabs and newlines are stripped on the way out.
_LUA_RUN_HELPERS = """
local function nb_esc(v)
  return (tostring(v):gsub("[\\t\\n\\r]", " "))
end
local function nb_emit(label, idx, rec)
  for k, v in pairs(rec) do
    print(string.format("R\\t%s\\t%d\\t%s\\t%s\\t%s",
          label, idx, nb_esc(k), type(v), nb_esc(v)))
  end
end
function nb_record(n, rec)
  local _, _, r1 = polaris_access_log("t", 0, rec)
  local r = r1 or rec
  local code = polaris_noise_filter("t", 0, r)
  local function s(v) if v == nil then return "" end return nb_esc(v) end
  print(table.concat({"V", n, code, s(r["http_method"]), s(r["http_status"]),
        s(r["api_path"]), s(r["user_principal_name"]), s(r["response_size"]),
        s(r["access_log_parse_error"])}, "\\t"))
end
function nb_tick(at, label)
  local code, ts, out = polaris_noise_filter("polaris.report", 0,
                                             { _now_override = at })
  local n = 0
  if type(out) == "table" and type(out[1]) == "table" then n = #out end
  print(table.concat({"T", label, tostring(code), type(out), tostring(n)}, "\\t"))
  for i = 1, n do nb_emit(label, i, out[i]) end
end
"""


class Tick:
    """A report tick, to be interleaved with records in `Policy.run`.

    `at` sets `_now_override`, the filter's own test hook -- it is read by
    `now_seconds()` and is INERT in the deployed pipeline, because the dummy
    INPUT never sets it. That is what lets the oracle cross window boundaries
    deterministically instead of sleeping through them.
    """

    __slots__ = ("at", "label")

    def __init__(self, at, label=None):
        self.at = int(at)
        self.label = label if label is not None else f"t{self.at}"

    def __repr__(self):
        return f"Tick({self.at}, {self.label!r})"


def report_tick(now=None):
    """The record the dummy INPUT emits. `_now_override` only when asked."""
    return {} if now is None else {"_now_override": int(now)}


def window_index(when, seconds):
    return int(when) // int(seconds)


def window_bounds(when, seconds):
    """`(start, end)` of the window containing `when`, as epoch seconds.

    The filter derives both from `floor(now / WINDOW_SECONDS)`, so a
    `window_start` is ALWAYS a multiple of `window_seconds`. A stored record
    whose `window_start` is not aligned did not come from this filter.
    """
    seconds = int(seconds)
    start = window_index(when, seconds) * seconds
    return start, start + seconds


def _iso_z(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(epoch)))


def _coerce(lua_type, text):
    if lua_type == "number":
        try:
            f = float(text)
        except ValueError:
            return text
        return int(f) if f.is_integer() else f
    if lua_type == "boolean":
        return text == "true"
    return text


def row_key(row):
    """The join key for a report row: what makes it unique within a window."""
    kind = row.get("report_type")
    if kind == "resource":
        return row.get("resource", "")
    if kind == "principal":
        return row.get("user_principal_name", "")
    return ""


def disposition(verdict):
    """`kept` or `counted`.

    Every access-log record is COUNTED before any keep/drop decision -- that is
    what `access_seen` means -- so these are not exclusive categories in the
    summary. `counted` here is the notebook's column: the record left no
    individual trace and exists only inside an aggregate.
    """
    return KEPT if verdict == KEEP else COUNTED


def _as_int(value, default=0):
    """VictoriaLogs hands every field back as a string; the oracle returns Lua
    numbers. One coercion so the same assertions run against both."""
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _epoch_of(iso_z):
    try:
        return int(
            datetime.strptime(str(iso_z), "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
    except (TypeError, ValueError):
        return None


def check_invariants(rows, strict_fields=True, merged=False):
    """Every violation in ONE window's report rows, as readable strings.

    Runs unchanged against the oracle's output and against what VictoriaLogs
    stored, which is the point: the same assertions on both sides make a
    difference between them a pipeline finding rather than a test artefact.

    A NOTE ON WHICH OF THESE IS EVIDENCE. `access_kept + access_counted ==
    access_seen` is TAUTOLOGICAL in the filter -- `build_report` computes
    `access_kept = access_seen - access_counted` and nothing counts kept
    records independently -- so on oracle rows it can never fail and proves
    nothing. On STORED rows it is worth checking anyway, because there it is a
    transport check: three fields that must still agree after Fluent Bit's
    array split and VictoriaLogs' ingest.

    The real self-check is the MARGIN pair. `errors` deliberately overlaps
    `reads` and `writes` -- reads/writes are counted by method, errors by
    status -- so the only cross-check the schema has is that the resource
    margin and the principal margin agree. If they disagree the report is
    miscounting and no trend built on it can be trusted.
    """
    bad = []
    rows = list(rows)
    if not rows:
        return ["no rows at all"]

    summaries = [r for r in rows if r.get("report_type") == "summary"]
    resources = [r for r in rows if r.get("report_type") == "resource"]
    principals = [r for r in rows if r.get("report_type") == "principal"]
    known = ("summary", "resource", "principal")
    other = [r for r in rows if r.get("report_type") not in known]
    if len(summaries) != 1:
        bad.append(f"expected exactly 1 summary row, found {len(summaries)}")
    for r in other:
        bad.append(f"unknown report_type {r.get('report_type')!r}")

    for r in rows:
        kind = r.get("report_type")
        missing = ENVELOPE_FIELDS - set(r)
        if missing:
            bad.append(f"{kind} row missing envelope fields: {sorted(missing)}")
        if strict_fields and kind in FIELDS_BY_TYPE:
            body = {
                f
                for f in set(r) - ENVELOPE_FIELDS - VLOGS_META
                if not f.startswith("_stream")
            }
            want = FIELDS_BY_TYPE[kind]
            if body - want:
                bad.append(f"{kind} row has unexpected fields: {sorted(body - want)}")
            gone = (want - body) - EMPTY_DROPPED_FIELDS
            if gone:
                bad.append(f"{kind} row is missing fields: {sorted(gone)}")
        if _as_int(r.get("schema_version"), -1) != SCHEMA_VERSION:
            bad.append(f"{kind} row has schema_version {r.get('schema_version')!r}")
        if r.get("_time") != r.get("window_end"):
            bad.append(f"{kind} row _time {r.get('_time')!r} != window_end")

        secs = _as_int(r.get("window_seconds"), 0)
        start, end = _epoch_of(r.get("window_start")), _epoch_of(r.get("window_end"))
        if not secs:
            bad.append(f"{kind} row has no usable window_seconds")
        elif start is None or end is None:
            bad.append(f"{kind} row has unparseable window bounds")
        else:
            if start % secs:
                bad.append(
                    f"window_start {r.get('window_start')} is not aligned to "
                    f"{secs}s -- the filter derives it from floor(now/W), so "
                    "an unaligned start did not come from this filter"
                )
            span = end - start
            if merged:
                #: a merged range covers N consecutive windows, so its span is a
                #: positive multiple. Everything else -- alignment, the margins,
                #: the per-row bounds -- still has to hold exactly.
                if span <= 0 or span % secs:
                    bad.append(
                        f"merged range spans {span}s, not a whole multiple of {secs}s"
                    )
            elif span != secs:
                bad.append(f"window spans {span}s, window_seconds says {secs}")

    for r in resources + principals:
        req = _as_int(r.get("requests"))
        rd, wr, er = (_as_int(r.get(k)) for k in ("reads", "writes", "errors"))
        who = r.get("resource") or r.get("user_principal_name")
        if rd + wr > req:
            bad.append(f"{who}: reads+writes {rd + wr} > requests {req}")
        if er > req:
            bad.append(f"{who}: errors {er} > requests {req}")

    if summaries:
        s = summaries[0]
        seen = _as_int(s.get("access_seen"))
        kept = _as_int(s.get("access_kept"))
        counted = _as_int(s.get("access_counted"))
        parse_errors = _as_int(s.get("parse_errors"))
        if kept + counted != seen:
            bad.append(
                f"access_kept + access_counted ({kept} + {counted}) != "
                f"access_seen ({seen}) -- these three are computed together in "
                "the filter, so a mismatch here is transport damage"
            )
        res_margin = sum(_as_int(r.get("requests")) for r in resources)
        pri_margin = sum(_as_int(r.get("requests")) for r in principals)
        want = seen - parse_errors
        if not (res_margin == pri_margin == want):
            bad.append(
                f"MARGINS DISAGREE: sum(resource.requests)={res_margin}, "
                f"sum(principal.requests)={pri_margin}, "
                f"access_seen-parse_errors={want}. The report is miscounting; "
                "no trend built on it can be trusted."
            )
        if _as_int(s.get("distinct_resources")) != len(resources):
            bad.append(
                f"distinct_resources={s.get('distinct_resources')} but "
                f"{len(resources)} resource rows were emitted"
            )
        if _as_int(s.get("distinct_principals")) != len(principals):
            bad.append(
                f"distinct_principals={s.get('distinct_principals')} but "
                f"{len(principals)} principal rows were emitted"
            )
    return bad


def diff_reports(expected, actual, ignore=VOLATILE_FIELDS | VLOGS_META):
    """Field-by-field diff of two windows' report rows.

    This is what makes "all schema coverage" a DIFF rather than a set of
    hand-written expectations: `expected` comes from the deployed Lua under
    `_now_override`, `actual` from VictoriaLogs, and anything that does not
    match names the row and the field rather than saying a call went missing.

    Rows join on `(report_type, row_key)`. `ignore` defaults to the fields that
    describe the emitting PROCESS rather than the window -- comparing those
    would fail on every row, since the oracle does not run in the shipper pod --
    PLUS `VLOGS_META`, which VictoriaLogs ADDS on the way out. The filter never
    emitted `_stream` / `_stream_id`, so the oracle cannot have them and every
    stored row otherwise contributes two guaranteed mismatches: 34 of the 60
    fixture mismatches listed for run `1788744260`, and the same fault
    `check_invariants` was fixed for on 2026-09-04. It is in the DEFAULT rather
    than left to the caller because the caller forgot.
    """
    ignore = set(ignore or ())

    def index(rows):
        return {(r.get("report_type"), row_key(r)): r for r in rows}

    exp, act = index(expected), index(actual)
    out = []
    for key in sorted(set(exp) | set(act), key=lambda k: (str(k[0]), str(k[1]))):
        kind, name = key
        e, a = exp.get(key), act.get(key)
        if e is None:
            out.append(
                {
                    "report_type": kind,
                    "key": name,
                    "field": "",
                    "expected": "",
                    "actual": "(row present)",
                    "status": "extra",
                }
            )
            continue
        if a is None:
            out.append(
                {
                    "report_type": kind,
                    "key": name,
                    "field": "",
                    "expected": "(row expected)",
                    "actual": "",
                    "status": "missing",
                }
            )
            continue
        for field in sorted((set(e) | set(a)) - ignore):
            ev, av = e.get(field), a.get(field)
            same = str(ev) == str(av) or (
                _as_int(ev, None) is not None and _as_int(ev, None) == _as_int(av, None)
            )
            out.append(
                {
                    "report_type": kind,
                    "key": name,
                    "field": field,
                    "expected": ev,
                    "actual": av,
                    "status": "match" if same else "differs",
                }
            )
    return out


def report_mismatches(diff):
    """Just the rows of `diff_reports` that are not a match."""
    return [d for d in diff if d["status"] != "match"]


#: Summary counters that are sums across windows. `distinct_resources` and
#: `distinct_principals` are NOT here: they are cardinalities, and adding them
#: across windows double-counts every resource that stayed busy.
SUMMABLE_SUMMARY_FIELDS = (
    "access_seen",
    "access_kept",
    "access_counted",
    "counted_get",
    "counted_post",
    "errors_kept",
    "parse_errors",
    "resources_other",
    "principals_other",
)
ROW_COUNTERS = ("requests", "reads", "writes", "errors", "response_bytes")


def merge_windows(windows):
    """Aggregate several consecutive windows' rows into one comparable set.

    A run that takes longer than `WINDOW_SECONDS` is spread across every window
    it touches. At the deployed 1800 that was rarely more than one; at 30 it is
    ALWAYS several, and reading a single window then reports whatever happened
    to land in the last 30 seconds -- which on 2026-09-04 was the cleanup
    DELETEs and nothing else: 8 records, all errors, one `__other__` row, and a
    coverage matrix that looked like the pipeline had lost the entire run.

    Args:
        windows: an iterable of row-lists, one per window, in any order.

    Returns:
        a list shaped like one window's rows -- one summary, the merged
        resource rows, the merged principal rows -- so `check_invariants` and
        `diff_reports` take it unchanged.

    Carried zero rows contribute nothing and must not create a key: a resource
    that was active before this range and merely echoed at 0 inside it is not a
    resource this range saw.
    """
    rows = [r for w in windows for r in (w or [])]
    if not rows:
        return []
    summaries = [r for r in rows if r.get("report_type") == "summary"]
    if not summaries:
        return []

    def merge(kind, key_field):
        #: `setdefault(key, dict(r))` and then "is it the same object?" does NOT
        #: work here: dict(r) is always a copy, so the first row of every key was
        #: added to itself and every count came out doubled. Track the key.
        out = {}
        for r in (r for r in rows if r.get("report_type") == kind):
            key = r.get(key_field)
            if key not in out:
                acc = dict(r)
                for f in ROW_COUNTERS:
                    acc[f] = _as_int(r.get(f))
                out[key] = acc
            else:
                acc = out[key]
                for f in ROW_COUNTERS:
                    acc[f] = acc[f] + _as_int(r.get(f))
        return [r for r in out.values() if any(_as_int(r.get(f)) for f in ROW_COUNTERS)]

    res = merge("resource", "resource")
    pri = merge("principal", "user_principal_name")

    ordered = sorted(summaries, key=lambda r: str(r.get("window_start", "")))
    s = dict(ordered[0])
    for f in SUMMABLE_SUMMARY_FIELDS:
        s[f] = sum(_as_int(r.get(f)) for r in summaries)
    s["distinct_resources"] = len(res)
    s["distinct_principals"] = len(pri)
    s["window_start"] = ordered[0].get("window_start")
    s["window_end"] = ordered[-1].get("window_end")
    s["_time"] = s["window_end"]
    any_partial = any(str(r.get("partial_window")) == "true" for r in summaries)
    s["partial_window"] = "true" if any_partial else "false"
    times = [
        t
        for r in summaries
        for t in (r.get("min_record_time"), r.get("max_record_time"))
        if t
    ]
    s["min_record_time"] = min(times) if times else ""
    s["max_record_time"] = max(times) if times else ""
    s["_msg"] = (
        f"merged {len(summaries)} windows {s['window_start']}..{s['window_end']}: "
        f"{s['access_seen']} access lines, {s['access_kept']} kept, "
        f"{s['access_counted']} counted, {len(res)} resources, {len(pri)} principals"
    )
    return [s] + res + pri


# ======================================================================
# reading a run back: who issued it, where it was counted, and whether
# the report's own totals reconcile
# ======================================================================
#: Every statistic about a call reads THIS, never a display column. The
#: coverage matrix truncates its `path` to the last 58 characters so the table
#: fits a terminal, and run 1 of v3 computed "Management POSTs kept: 5 of 5"
#: by filtering the truncated column: the cut removed `/api/management` from
#: `POST /api/management/v1/catalogs/{c}/catalog-roles`, dropping that call out
#: of the numerator AND the denominator, so the fraction agreed with itself and
#: was wrong. Six management POSTs were driven and six were kept.
def call_path(call):
    """The full path a call issued, query string included."""
    p = call.get("actual_path") or ""
    if not p and call.get("path"):
        p = full_path(call.get("api") or "catalog", call["path"])
    return str(p or "")


def _token_fp(token):
    """A stable, non-reversible handle for a bearer token.

    The registry is keyed on this rather than on the token so a principal map
    can be printed, put in a dataframe or pickled with a notebook's output
    without carrying a live credential with it.
    """
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()[:16]


def principal_registry(pairs):
    """`{token fingerprint: principal name}` for the clients a run drives with.

    Args:
        pairs: iterable of `(client_or_token, principal_name)`.
    """
    reg = {}
    for client, name in pairs:
        tok = client if isinstance(client, str) else getattr(client, "token", None)
        if tok:
            reg[_token_fp(tok)] = name
    return reg


def principal_of(resp, registry, default=None):
    """Which principal ISSUED this request, read off its own `Authorization`.

    MEASURED, NOT ASSUMED. Run 1 of v3 wrote a single constant into the
    matrix's `principal_row` for all 132 calls, which made the column an
    assertion about the harness rather than an observation: the management
    operations go out on the root client, the 403 case on `nb_<run>_denied`,
    and the token exchanges carry no principal at all (`%u` writes `-`). A
    column that cannot disagree with itself cannot catch a mis-attribution,
    and the per-principal margin is the schema's only real self-check.
    """
    try:
        auth = resp.request.headers.get("Authorization") or ""
    except Exception:  # noqa: BLE001
        return default
    parts = str(auth).split(None, 1)
    tok = parts[1].strip() if len(parts) == 2 else ""
    return registry.get(_token_fp(tok), default) if tok else default


def mgmt_post_stats(calls, expected, prefix=MGMT_PREFIX):
    """Management POSTs driven, and how many the deployed policy keeps.

    This is the number the v2 audit hole is reported by, so it is computed
    from `call_path` and split by status. A management POST that returned
    4xx/5xx is kept by the ERROR rule whatever rule 5 does -- first match wins
    in the filter and the error rule is matched first -- so counting it as
    evidence for "rule 5 keeps management POSTs" overstates what the run
    proved. Run 1 drove six, of which one (a 403 on `reset`) is in that
    position.

    Args:
        calls: the driven call rows.
        expected: `expected_for(...)` output, aligned with `calls`.

    Returns:
        {"driven", "kept", "kept_2xx", "kept_error", "rows"}, where `rows` is
        `[(label, path, status, verdict)]` for every management POST driven.
    """
    rows = []
    for call, exp in zip(calls, expected or [None] * len(calls)):
        if (call.get("method") or "").upper() != "POST":
            continue
        path = call_path(call)
        if not path.startswith(prefix):
            continue
        rows.append(
            (
                call.get("label"),
                path,
                call.get("status"),
                (exp or {}).get("verdict"),
            )
        )
    kept = [r for r in rows if r[3] == KEEP]
    err = [r for r in kept if _as_int(r[2]) >= 400]
    return {
        "driven": len(rows),
        "kept": len(kept),
        "kept_2xx": len(kept) - len(err),
        "kept_error": len(err),
        "rows": rows,
    }


def resource_rows(rows):
    """`{resource: row}` for the resource rows of a (merged) report."""
    return {r.get("resource"): r for r in rows if r.get("report_type") == "resource"}


def counted_where(calls, keys, rows, other=REPORT_OTHER):
    """For each call, the report row that ACTUALLY moved -- PLAN section 7.

    `resource_row` says which key a path CLASSIFIES to, which is where the
    call lands *if it succeeds*. That is not the same question. An error on a
    resource nobody has read successfully passes `create=false` and increments
    `__other__` instead, so for a 4xx/5xx row the classified key is a
    counterfactual. Without this column the matrix cannot do the thing it was
    added for -- name the row that is wrong -- and an oracle diff arrives as a
    number instead of a list.

    Args:
        calls: the driven call rows.
        keys: `Policy.classify_paths` output, `{path: (resource, kind)}`.
        rows: the merged report rows this run's windows produced.

    Returns:
        a list aligned with `calls`: the resource key that carries this call,
        `__other__`, `"ABSENT"` when neither exists, or `""` for a call that
        never completed.
    """
    present = resource_rows(rows)
    out = []
    for call in calls:
        if not call.get("status"):
            out.append("")
            continue
        key = (keys or {}).get(call_path(call).split("?")[0]) or (None, None)
        if key[0] and key[0] in present:
            out.append(key[0])
        elif other in present:
            out.append(other)
        else:
            out.append("ABSENT")
    return out


def reconcile_merged_rows(rows, calls, keys, other=REPORT_OTHER):
    """Does the merged report hold the rows THIS RUN can account for?

    A row count on its own is not readable. Run 1 reported `merged rows: 49`
    beside 30 distinct resource keys with a success and 4 error-only keys --
    about fifteen rows the run could not explain -- and the report said
    nothing, because nothing compared the two. The likely innocent
    explanation (rows carried at zero from a window before the run, or another
    client on the cluster) is still an explanation someone has to be given the
    means to check.

    Returns:
        {"expected", "actual", "unexplained", "missing", "counts"} -- the first
        four as sorted key lists, `counts` as the row arithmetic.
    """
    present = resource_rows(rows)
    expected = set()
    saw_error = False
    for call in calls:
        status = _as_int(call.get("status"), None)
        if status is None:
            continue
        key = (keys or {}).get(call_path(call).split("?")[0]) or (None, None)
        if status >= 400:
            saw_error = True
            continue
        if key[0]:
            expected.add(key[0])
    if saw_error:
        expected.add(other)
    actual = set(present)
    principals = [r for r in rows if r.get("report_type") == "principal"]
    summaries = [r for r in rows if r.get("report_type") == "summary"]
    return {
        "expected": sorted(expected),
        "actual": sorted(actual),
        "unexplained": sorted(actual - expected),
        "missing": sorted(expected - actual),
        "counts": {
            "summary": len(summaries),
            "resource": len(present),
            "principal": len(principals),
            "total": len(rows),
            "resource_expected": len(expected),
        },
    }


def reconcile_volume(stored, calls, run=None, id_field="mdc.requestId"):
    """Where every stored record went, so the volume figure adds up.

    Run 1 reported 2,117 records for 132 calls and a matrix whose columns summed
    to 2,109. Eight records were attributed to nothing, and since `app_lines` is
    `len(found) - len(access)` from the same pull, the two figures should agree
    by construction. They differ because a record can carry a request id this
    run minted for a call that is not in `ALL_CALLS`, or no request id at all.
    Name both rather than leaving a residue.

    Returns:
        {"total", "attributed", "run_other", "untagged", "reconciles"}.
    """
    ids = {c.get("request_id") for c in calls if c.get("request_id")}
    prefix = f"nb-{run}-" if run else None
    attributed = run_other = untagged = 0
    for rec in stored:
        rid = rec.get(id_field)
        if not rid:
            untagged += 1
        elif rid in ids:
            attributed += 1
        elif prefix and str(rid).startswith(prefix):
            run_other += 1
        else:
            untagged += 1
    total = len(stored)
    return {
        "total": total,
        "attributed": attributed,
        "run_other": run_other,
        "untagged": untagged,
        "reconciles": attributed + run_other + untagged == total,
    }


def named_assertions(rows, summary=None, started=None, ended=None):
    """The checks PLAN section 7 names, each as `(name, ok, detail)`.

    These were computed or implied by run 1 and stated by none of it. A
    report that says "invariants OK" and leaves the named assertions to the
    reader's memory is a report that cannot be audited later: `/metrics`
    folding onto its table is the v2 two-rows-per-table bug staying fixed, and
    nothing in the results document said so.

    `ok` is None where the run gave the check nothing to decide on. `started`
    and `ended` override the window range the time fields are checked against;
    they default to the summary's own `window_start` / `window_end`, which is
    the only bound that is a statement about the pipeline.
    """
    res = resource_rows(rows)
    summary = summary or next(
        (r for r in rows if r.get("report_type") == "summary"), {}
    )
    out = []

    metrics = sorted(k for k in res if k and k.endswith("/metrics"))
    out.append(
        (
            "no /metrics row (it folds onto its table; v2 emitted two)",
            not metrics,
            metrics or "none",
        )
    )

    other = _as_int(summary.get("resources_other"), None)
    out.append(
        (
            "resources_other > 0 (an error never creates a resource key)",
            None if other is None else other > 0,
            other,
        )
    )

    seen = [_as_int(r.get("response_bytes")) for r in res.values()]
    out.append(
        (
            "response_bytes takes both a zero and a non-zero value",
            bool(seen) and any(v == 0 for v in seen) and any(v > 0 for v in seen),
            f"{sum(1 for v in seen if v == 0)} zero, "
            f"{sum(1 for v in seen if v > 0)} non-zero",
        )
    )

    #: THE BOUND IS THE WINDOW RANGE, NOT THE WALL CLOCK. These are the
    #: timestamps of the records the WINDOWS saw, so the only thing assertable
    #: about them is that they fall inside the windows being summarised.
    #: Bracketing them against the notebook's own start and end reads as a
    #: check and is not one: the merged range always runs past `RUN_END` (to
    #: the last window's boundary) and opens before `STARTED` (the first window
    #: opened before the notebook did), so any traffic in either overhang fails
    #: an assertion about the pipeline that is really an assertion about when a
    #: human pressed run. Run `1788744260` FAILED it in exactly that way:
    #: max_record_time 01:25:18Z against a `RUN_END` a few seconds earlier,
    #: inside a window that closed at 01:25:30Z.
    lo, hi = summary.get("min_record_time"), summary.get("max_record_time")
    w0 = started if started is not None else _epoch_of(summary.get("window_start"))
    w1 = ended if ended is not None else _epoch_of(summary.get("window_end"))
    label = "min/max_record_time fall inside the merged window range"
    if not (lo and hi):
        #: VictoriaLogs does not store empty values, so a quiet window simply
        #: has no time fields. Absent is not drift and not a failure.
        out.append((label, None, "absent (quiet window)"))
    elif w0 is None or w1 is None:
        out.append((label, None, f"{lo} .. {hi}"))
    else:
        a, b = _epoch_of(str(lo)[:19] + "Z"), _epoch_of(str(hi)[:19] + "Z")
        ok = a is not None and b is not None and a >= int(w0) and b <= int(w1)
        detail = f"{lo} .. {hi}"
        if not ok:
            detail += f"   (window range {_iso_z(int(w0))} .. {_iso_z(int(w1))})"
        out.append((label, ok, detail))
    return out


def principal_mix(rows):
    """`{principal: {requests, reads, writes, errors}}` from a report's rows.

    The margin equality is the schema's only real self-check, and with ONE
    principal it is satisfied identically by a global counter: every principal
    total is the run total, so a filter that never attributed anything would
    pass. PLAN section 6.2 asks for two principals with different mixes for
    exactly that reason, and this is what makes the difference readable.
    """
    return {
        r.get("user_principal_name"): {
            f: _as_int(r.get(f)) for f in ("requests", "reads", "writes", "errors")
        }
        for r in rows
        if r.get("report_type") == "principal"
    }


def correlation_stats(stored, calls, id_field="mdc.requestId"):
    """How many of THESE calls had their request id recovered.

    Run `1788745242` reported "147 distinct ids recovered from 146 calls" --
    more ids than calls, because the numerator counted every run-minted id in
    the pull (cell 1's correlation probe among them, which is deliberately not
    in `ALL_CALLS`) while the denominator counted the calls. **A ratio whose
    halves come from different populations cannot be read literally**, and
    correlation is the statistic the entire per-call matrix rests on.

    Returns:
        {"calls", "with_id", "recovered", "missing", "other_ids"} -- `missing`
        names the calls whose id never came back, which is the half worth
        reading.
    """
    ids = {c.get("request_id") for c in calls if c.get("request_id")}
    seen = {r.get(id_field) for r in stored if r.get(id_field)}
    return {
        "calls": len(calls),
        "with_id": len(ids),
        "recovered": len(ids & seen),
        "missing": sorted(ids - seen),
        "other_ids": len(seen - ids),
    }


#: Substrings of a FIELD NAME that mean the field carries a throwable. Matched
#: against keys only -- a message mentioning an exception is not one.
EXCEPTION_KEY_HINTS = ("exception", "stacktrace", "stack_trace", "throwable", "frames")


def exception_fields(record):
    """The field names in `record` that carry a throwable -- NAMES, not a bool.

    A NAME IS NOT A SHAPE, AND THIS IS THE MISTAKE THIS FUNCTION EXISTS FOR.
    On 2026-09-07 this notebook reported "0 of 5 WARN/ERROR records carried an
    exception object" and a `grep -c stackTrace` on the source log returned 0,
    and the two were read as corroboration. They were the same error twice:
    this build emits Quarkus's **structured** exception output -- an object
    carrying a `frames` array of `{class, method, line}` -- so there is no
    `stackTrace` string to grep for, and `"exception" in record` fails against
    a nested object that a store has flattened into `exception.frames` /
    `exception.exceptionType`. The traces were there the whole time.

    So this returns the names it found and the caller reports them. A check
    that can only say yes or no cannot tell "absent" from "looked for the wrong
    name", and the two have opposite remedies: one is a logging change, the
    other is a one-line fix here.

    Covers the shapes this pipeline can produce: a nested or flattened object
    under any of `EXCEPTION_KEY_HINTS`, and a `formatted` trace sitting as text
    inside some other field's value.
    """
    found = []
    for key, value in (record or {}).items():
        lowered = str(key).lower()
        if any(hint in lowered for hint in EXCEPTION_KEY_HINTS):
            found.append(str(key))
        elif isinstance(value, str) and ("\n\tat " in value or ".java:" in value):
            found.append(f"{key} (formatted trace in the value)")
    return sorted(found)


# ---------------------------------------------------------------------------
# COVERAGE: 500 ERROR
# ---------------------------------------------------------------------------
#
# WHY THIS EXISTS. `neg.500_null_pointer` has returned 200 for three runs: the
# `create_catalog_no_endpoint` provocation stopped reproducing on this build,
# and nothing noticed because "0 of 0 records carried an exception object"
# reads exactly like an answer. The only 500s ever stored arrived BY ACCIDENT,
# from the PG-HA read-after-write failures on `iceberg.create_namespace` and
# `create_view` -- which are writes that COMMITTED, and therefore say nothing
# about the unhandled-exception path. So the ERROR path has never been driven
# on purpose, and `errors_5xx` has never been exercised against the real
# pipeline.
#
# A 500 IS TWO RECORDS, NOT ONE, and the whole section turns on the split:
#
#   the access-log line   loggerName io.quarkus.http.access-log, http_status
#                         500. Rule 3 KEEPS it, and every access-log record is
#                         COUNTED before any keep/drop decision -- so it is
#                         kept AND counted, and it moves `errors`, `errors_5xx`
#                         and the row's own `errors`.
#   the application line  the ERROR record the handler logs. Not an access-log
#                         record, so rule 2 hands it to rule 1: KEPT and NOT
#                         counted. This is the one carrying `exception.frames`.
#
# The two join on `mdc.requestId`. A check that looks at one of them can pass
# while the other is missing, which is how a half-working ERROR path would
# survive a run.

#: Label prefix `drive_500` puts on every call it issues. `classify_500` reads
#: it, and the results document reads that: coverage claimed for the ERROR path
#: must be traceable to a call this notebook made on purpose.
DELIBERATE_500_PREFIX = "probe.500."

#: The PG-HA read-after-write signature. A 500 on one of these is a write that
#: COMMITTED -- `load_view`/`head_view`/`drop_view` all answered 2xx afterwards
#: on 2026-09-01 -- so it is a replica-lag artefact, not an unhandled
#: exception, and counting it as ERROR-path coverage is the substitution this
#: whole section exists to stop.
PG_HA_500_LABELS = ("iceberg.create_namespace", "iceberg.create_view")

#: The v2 report's error split. Absent on a schema v1 window, and the
#: difference between "absent" and "zero" is the difference between a check
#: that is VOID and one that PASSED.
ERROR_SPLIT_FIELDS = ("errors", "errors_4xx", "errors_5xx", "auth_denied")


class Provoker:
    """One rung of the 500 ladder: API-only, reversible, self-cleaning.

    `prepare` and `cleanup` are the fixture; `calls` returns
    `(label, fn, method, path)` tuples for `call_once` to drive, and is called
    AFTER `prepare` so it can close over whatever prepare built. Nothing here
    touches kubectl, psql or the schema -- a rung that needs the cluster is not
    a rung this notebook can own.
    """

    def __init__(self, name, why, calls, prepare=None, cleanup=None, assumed=False):
        self.name = name
        self.why = why
        self._calls = calls
        self.prepare = prepare
        self.cleanup = cleanup
        #: True where the rung has never been observed to return 500 on this
        #: build. The ladder is ordered, not proven.
        self.assumed = assumed

    def calls(self):
        return list(self._calls())

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"<Provoker {self.name}{' [assumed]' if self.assumed else ''}>"


def provokers_500(
    adm_pc,
    ic,
    run,
    *,
    bucket,
    endpoint,
    endpoint_internal=None,
    table_payload=None,
    unreachable="http://127.0.0.1:1",
    bad_bucket=None,
    repeat=3,
):
    """The ladder, cheapest and most likely first. Drive it with `drive_500`.

    Every rung creates its own catalog and deletes it in `cleanup`, so a rung
    that fails leaves nothing behind and the next one starts clean.

    Args:
        adm_pc: a `PolarisREST` that may create and delete catalogs.
        ic: an `IcebergREST` on the same realm.
        run: the run id, so every fixture name is unique to this run.
        bucket / endpoint / endpoint_internal: the REAL storage config, from
            `init_env`. Rungs 1 and 3 differ from it in exactly one field.
        table_payload: `lambda name: <CreateTableRequest>`. Passed in rather
            than imported so this module keeps no dependency on
            `iceberg_rest`.
        unreachable: the black hole rung 1 points Polaris' own S3 client at.
            127.0.0.1:1 is chosen because it FAILS FAST -- a routable-but-dead
            host would hang, and a hang leaves no access-log line at all,
            which is the one failure this pipeline is blind to.
        repeat: how many 500s each rung drives. More than one because rule 3
            keeps errors with NO CAP, and one call cannot show the absence of
            a cap.

    Returns:
        a list of `Provoker`, in the order they should be tried.
    """
    if table_payload is None:
        raise ValueError(
            "provokers_500 needs table_payload=lambda name: <CreateTableRequest>; "
            "build it with iceberg_rest.build_create_table_payload in the notebook"
        )

    state = {}

    # -- rung 1: the storage endpoint Polaris itself cannot reach ------------
    # This is `error-cases/09`'s intent, repaired. 09 broke because it left
    # `endpoint` valid and only omitted `endpointInternal`, and this build
    # falls back to `endpoint` -- so the catalog worked and the notebook
    # reported 200 while still calling itself a NullPointerException test.
    # Pointing BOTH at a dead port removes the fallback.
    bh_cat = f"nb{run}bh"
    bh_ns = "bh_ns"

    def bh_prepare():
        r = adm_pc.create_catalog(
            bh_cat, bucket, unreachable, minio_endpoint_internal=unreachable
        )
        state["bh_catalog"] = r.status_code
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        # The namespace is metadata only and must SUCCEED -- it gives the
        # window a resource key that was read cleanly, so the 500s that follow
        # can be shown to land in `__other__` instead of creating one.
        state["bh_ns"] = ic.create_namespace(bh_cat, bh_ns).status_code

    def bh_calls():
        return [
            (
                f"create_table_{i}",
                (
                    lambda n=f"bh_tbl_{i}": ic.create_table(
                        bh_cat, bh_ns, table_payload(n)
                    )
                ),
                "POST",
                f"{CAT_PREFIX}/v1/{bh_cat}/namespaces/{bh_ns}/tables",
            )
            for i in range(repeat)
        ]

    def bh_cleanup():
        # purge=False DELIBERATELY. `purgeRequested=true` asks Polaris to
        # delete the underlying files, which means talking to the storage
        # endpoint this rung just pointed at a dead port -- so a purge here
        # either hangs or provokes a second, untagged 500 during cleanup.
        try:
            adm_pc.delete_catalog(bh_cat, purge=False)
        except Exception:  # noqa: BLE001 - cleanup never fails the run
            pass

    # -- rung 2: a bucket that is not there ---------------------------------
    nb_cat = f"nb{run}nobkt"
    nb_ns = "nobkt_ns"
    missing_bucket = bad_bucket or f"nb-{run}-no-such-bucket"

    def nb_prepare():
        r = adm_pc.create_catalog(
            nb_cat,
            missing_bucket,
            endpoint,
            minio_endpoint_internal=endpoint_internal or endpoint,
        )
        state["nb_catalog"] = r.status_code
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        state["nb_ns"] = ic.create_namespace(nb_cat, nb_ns).status_code

    def nb_calls():
        return [
            (
                f"create_table_{i}",
                (
                    lambda n=f"nobkt_tbl_{i}": ic.create_table(
                        nb_cat, nb_ns, table_payload(n)
                    )
                ),
                "POST",
                f"{CAT_PREFIX}/v1/{nb_cat}/namespaces/{nb_ns}/tables",
            )
            for i in range(repeat)
        ]

    def nb_cleanup():
        try:
            adm_pc.delete_catalog(nb_cat, purge=False)
        except Exception:  # noqa: BLE001
            pass

    # -- rung 3: a stale entity version -------------------------------------
    # [assumed], and flagged as such: `PolarisREST.update_catalog`'s own
    # docstring says a stale `currentEntityVersion` returns 409, not 500. If
    # that is right this rung can never fire and its value is the record of
    # having tried it. `error-cases/18` believed otherwise.
    sv_cat = f"nb{run}stale"

    def sv_prepare():
        r = adm_pc.create_catalog(
            sv_cat,
            bucket,
            endpoint,
            minio_endpoint_internal=endpoint_internal or endpoint,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        cat = adm_pc.get_catalog(sv_cat).json()
        state["sv_props"] = dict(cat.get("properties") or {})
        state["sv_version"] = _as_int(cat.get("entityVersion"), 1)

    def sv_calls():
        return [
            (
                f"stale_put_{i}",
                (
                    lambda i=i: adm_pc.update_catalog(
                        sv_cat,
                        {**state["sv_props"], "nb.stale": f"{run}-{i}"},
                        max(0, state["sv_version"] - 5),
                    )
                ),
                "PUT",
                f"{MGMT_PREFIX}/v1/catalogs/{sv_cat}",
            )
            for i in range(repeat)
        ]

    def sv_cleanup():
        try:
            adm_pc.delete_catalog(sv_cat, purge=False)
        except Exception:  # noqa: BLE001
            pass

    return [
        Provoker(
            "black_hole_endpoint",
            "both storage endpoints point at a dead port, so Polaris' own S3 "
            "client cannot resolve storage on table create",
            bh_calls,
            prepare=bh_prepare,
            cleanup=bh_cleanup,
            assumed=True,
        ),
        Provoker(
            "nonexistent_bucket",
            "the catalog's bucket does not exist in MinIO (error-cases/23, "
            "API-only half)",
            nb_calls,
            prepare=nb_prepare,
            cleanup=nb_cleanup,
            assumed=True,
        ),
        Provoker(
            "stale_entity_version",
            "optimistic-lock conflict on PUT /catalogs (error-cases/18) -- "
            "[assumed], and update_catalog's docstring says this is a 409",
            sv_calls,
            prepare=sv_prepare,
            cleanup=sv_cleanup,
            assumed=True,
        ),
    ]


def drive_500(clients, run, seq, provokers, principals=None, call=None, on_rung=None):
    """Walk the ladder and STOP at the first rung that really returns >= 500.

    THE HONEST-FAILURE CONTRACT IS THE POINT. If every rung returns 2xx the
    result carries `winner=None` and the per-rung statuses, and the caller
    reports NOT PROVOKED. It does not quietly fall back to whatever 500s the
    drive produced by itself: that substitution is what let `0 of 0` be read as
    an answer for three runs.

    Returns:
        `{"rows": [...], "ladder": [...], "winner": name or None, "seq": int}`
        -- `rows` in `call_once`'s shape, so they join the run's other calls.
    """
    call = call or call_once
    rows, ladder, winner = [], [], None
    for prov in provokers:
        note, rung_rows = None, []
        try:
            if prov.prepare is not None:
                prov.prepare()
            prepared = True
        except Exception as exc:  # noqa: BLE001
            prepared, note = False, f"setup: {type(exc).__name__}: {exc}"
        if prepared:
            try:
                for label, fn, method, path in prov.calls():
                    seq += 1
                    rung_rows.append(
                        call(
                            clients,
                            run,
                            seq,
                            f"{DELIBERATE_500_PREFIX}{prov.name}.{label}",
                            fn,
                            method,
                            path,
                            principals=principals,
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                note = f"drive: {type(exc).__name__}: {exc}"
            finally:
                if prov.cleanup is not None:
                    try:
                        prov.cleanup()
                    except Exception as exc:  # noqa: BLE001
                        note = f"{note + ' | ' if note else ''}cleanup: {type(exc).__name__}"
        statuses = [r.get("status") for r in rung_rows]
        provoked = [s for s in statuses if s is not None and int(s) >= 500]
        entry = {
            "rung": prov.name,
            "why": prov.why,
            "calls": len(rung_rows),
            "statuses": statuses,
            "provoked": len(provoked),
            "note": note,
        }
        ladder.append(entry)
        rows.extend(rung_rows)
        if on_rung is not None:
            on_rung(entry)
        if provoked:
            winner = prov.name
            break
    return {"rows": rows, "ladder": ladder, "winner": winner, "seq": seq}


def classify_500(call):
    """`deliberate` / `read_after_write` / `unknown` for one call row.

    Classified from the LABEL, not from the response: a 500 body cannot say
    whether the write committed, and the PG-HA signature is precisely a 500
    whose write DID commit. Anything unrecognised is `unknown` rather than
    folded into either bucket -- an unexplained 500 is a finding, not a
    rounding error.
    """
    label = str(call.get("label") or "")
    if label.startswith(DELIBERATE_500_PREFIX):
        return "deliberate"
    if any(label.startswith(sig) for sig in PG_HA_500_LABELS):
        return "read_after_write"
    return "unknown"


def classify_500s(calls):
    """`{deliberate: [...], read_after_write: [...], unknown: [...]}`."""
    out = {"deliberate": [], "read_after_write": [], "unknown": []}
    for call in calls or ():
        status = call.get("status")
        if status is None or int(status) < 500:
            continue
        out[classify_500(call)].append(call)
    return out


def error_record_pair(records, request_id, id_field="mdc.requestId"):
    """Both halves of one 500, split by logger, with the exception names found.

    `exception_fields` is applied to the application lines only and returns
    NAMES: the payload is stored FLATTENED as `exception.frames`, so a check
    for a key called `exception` reports absence for a record that carries the
    trace. That mistake was made twice and agreed with itself both times.
    """
    mine = [r for r in (records or ()) if str(r.get(id_field, "")) == str(request_id)]
    access = [r for r in mine if r.get("loggerName") == ACCESS_LOGGER]
    app = [r for r in mine if r.get("loggerName") != ACCESS_LOGGER]
    found = {}
    for rec in app:
        names = exception_fields(rec)
        if names:
            found.setdefault(rec.get("loggerName") or "(no loggerName)", []).extend(
                names
            )
    return {
        "request_id": str(request_id),
        "access": access[0] if access else None,
        "access_records": len(access),
        "app_records": len(app),
        "levels": sorted({str(r.get("level")) for r in app if r.get("level")}),
        "exception_fields": {k: sorted(set(v)) for k, v in found.items()},
        "loggers": sorted(
            {str(r.get("loggerName")) for r in app if r.get("loggerName")}
        ),
    }


def check_500_window(rows, driven_500, driven_4xx=0, driven_auth_denied=0):
    """The `errors_5xx` assertions, as `(name, ok, detail)` -- `ok=None` = VOID.

    Written for a PURE-500 BURST: a window into which this notebook drove
    nothing but 500s, so `errors_4xx` and `auth_denied` have a predicted value
    of zero and the negative cases have something to catch. Pass
    `driven_4xx` / `driven_auth_denied` if the burst was not pure; the checks
    then compare against what was driven rather than against zero.

    `>=` on the 5xx count, `==` on the 4xx and auth negatives. The asymmetry is
    deliberate: neighbour traffic and a PG-HA read-after-write 500 can ADD to
    `errors_5xx` in the same window, but nothing this notebook drove can add a
    4xx to a pure-500 burst, so an inequality there would pass a filter that
    charged the 500 to the wrong counter -- the exact bug the split exists to
    catch.
    """
    rows = list(rows or ())
    summary = next((r for r in rows if r.get("report_type") == "summary"), {})
    out = []

    present = [f for f in ERROR_SPLIT_FIELDS if f in summary]
    if "errors_5xx" not in present:
        out.append(
            (
                "the window carries the v2 error split",
                None,
                "`errors_5xx` is absent from the summary row -- this window came "
                "from a schema v1 filter, or the field was not stored. Every check "
                "below is VOID, not passed. Fields seen: "
                + (", ".join(present) or "none of them"),
            )
        )
        return out
    out.append(("the window carries the v2 error split", True, ", ".join(present)))

    errors = _as_int(summary.get("errors"))
    e5 = _as_int(summary.get("errors_5xx"))
    e4 = _as_int(summary.get("errors_4xx"))
    denied = _as_int(summary.get("auth_denied"))

    out.append(
        (
            f"errors_5xx >= the {driven_500} driven 500(s)",
            e5 >= driven_500,
            f"errors_5xx={e5}, driven={driven_500}"
            + (
                "  (>= because neighbour traffic and a PG-HA 500 land in the "
                "same window)"
                if e5 > driven_500
                else ""
            ),
        )
    )
    out.append(
        (
            "a 500 does not increment errors_4xx",
            e4 == driven_4xx,
            f"errors_4xx={e4}, driven 4xx={driven_4xx}",
        )
    )
    out.append(
        (
            "a 500 does not increment auth_denied",
            denied == driven_auth_denied,
            f"auth_denied={denied}, driven 401/403={driven_auth_denied}",
        )
    )
    out.append(
        (
            "auth_denied <= errors_4xx",
            denied <= e4,
            f"{denied} <= {e4}",
        )
    )
    #: INEQUALITY ON PURPOSE. A record with no parsable status is an error
    #: charged to neither split, so the two halves are a lower bound on
    #: `errors` and demanding equality would fail on a line that did not parse.
    out.append(
        (
            "errors_4xx + errors_5xx <= errors",
            e4 + e5 <= errors,
            f"{e4} + {e5} <= {errors}",
        )
    )

    for field in ("errors", "errors_5xx"):
        res = sum(
            _as_int(r.get(field)) for r in rows if r.get("report_type") == "resource"
        )
        pri = sum(
            _as_int(r.get(field)) for r in rows if r.get("report_type") == "principal"
        )
        has = any(
            field in r
            for r in rows
            if r.get("report_type") in ("resource", "principal")
        )
        out.append(
            (
                f"margin: sum(resource.{field}) == sum(principal.{field})",
                None if not has else res == pri,
                f"{res} vs {pri}" if has else f"no row carries `{field}`",
            )
        )
    return out
