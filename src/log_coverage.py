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

    def __init__(self, script, sha256, source):
        self.script = script
        self.sha256 = sha256
        self.source = source

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
    return (
        f'{ip} - {user} [{stamp}] "{method} {path} HTTP/1.1" {status} {body}'
    )


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
    """"management" or "catalog", from an `api_surface` label or a path."""
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
    clients, run, seq, label, fn, method="", path="", header="Polaris-Request-Id"
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
    from polaris_rest import PolarisREST
    from iceberg_rest import IcebergREST

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


def drive_tagged(ops, ctx, run, on_call=None, header="Polaris-Request-Id"):
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
