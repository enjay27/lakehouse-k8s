"""Make traffic against Polaris. Learn nothing about what the logs did with it.

`local-k8s` runs the logging test; this module is the only thing it imports
from this repo. The scenario is `log-coverage/SCENARIO-logging-test.md`; the
boundary argument is `log-coverage/PLAN-split-traffic-and-verification.md`.

**The one rule this file exists to enforce.** It has no logging concept. It
does not know what a report window means, it does not read the Fluent Bit
ConfigMap, and it never imports `log_coverage`, `os_report` or `vlogs`.
`window_seconds` arrives as an ARGUMENT from the side that owns it, and the
run is described in terms of what was asked of Polaris and what Polaris said.
`test_make_traffic.py` asserts the import graph rather than trusting the
docstring, because a boundary that is a convention drifts and a boundary that
is a test does not.

**What it will not tell you.** Whether a call should have been stored. Under
the deployed filter's rule 6 a successful read is summarised and never stored
individually, so its request id finds nothing -- correctly. Which calls are
counted is a fact about the Lua the verifier owns, so `TrafficRun` carries no
keep/drop expectation at all. Two repos holding two answers about one policy
is the drift the whole split exists to prevent.

**Three fields worth knowing before you read the shape.**

`echo_ok` is the boundary doing its job. Polaris echoes `Polaris-Request-Id`
back unchanged (measured 2026-09-09, and run 1789008899 recovered 286 of 286
calls by `mdc.requestId`). An id that did NOT come back never reached the
server as sent -- a fault in THIS repo -- and without the check it looks
exactly like a record the pipeline lost. The verifier reports UNPROVEN on such
a call instead of accusing itself.

`claims` are keyed by request id, not by resource name. That is what shrinks
the verifier's Polaris knowledge to zero: it does not need to know that a
commit is a POST under `/tables/`, only that this id exists and what the access
log says about it. Gate 4 was unreadable in run 1789008899 -- `writes=1
granted=3`, with no way to tell an undercounting filter from a gate reading the
wrong row -- and with the ids that ambiguity cannot arise.

`incomplete` is first class. A drive that dies at call 40 still returns what it
drove, and still cleans up. Every downstream check then reports UNPROVEN rather
than FAIL: a half-run is not evidence of a broken pipeline.
"""

import json
import pathlib
import time
from datetime import datetime, timezone

#: `local-k8s` asserts this at collection. A change to the row shape bumps it
#: and breaks LOUDLY at import, not quietly at an assertion three tests later.
CONTRACT_VERSION = 1

#: What `drive(profile=...)` accepts. The values are what the caller is told;
#: `_PHASES` below is what the code reads, and the two are checked against each
#: other by a test so a profile cannot be documented and unimplemented.
PROFILES = {
    "full": "all 63 operations x every reachable status -- 286 cells, ~9 windows",
    "smoke": "~12 cells, one window: is the pipeline answering at all",
    "gate2": "one commit alone, then one DELETE alone -- the feature and its negative half",
    "gate4": "three grants and a denial on one role, one window",
}

#: profile -> the phases it drives, in order. "B"/"C"/"D" are grid phases;
#: E/F/G/H are the hand-shaped windows; cleanup is not a phase because it is
#: not optional -- it runs in `finally` for every profile including a failure.
_PHASES = {
    "full": ("B", "C", "D", "E", "F", "G", "H"),
    "smoke": ("B",),
    "gate2": ("E", "F"),
    "gate4": ("G",),
}

#: How many grid cells `smoke` drives. Small enough to fit one window at 30s,
#: large enough that a pipeline answering nothing is visible.
SMOKE_CELLS = 12

#: The privileges gate 4 grants, in order. Three, because the gate compares a
#: COUNT: one grant cannot distinguish "the filter counted the grant" from "the
#: filter wrote a 1 it would have written anyway".
GATE4_GRANTS = ("TABLE_READ_DATA", "TABLE_WRITE_DATA", "NAMESPACE_LIST")


class ContractError(RuntimeError):
    """The caller and this module disagree about the shape of the world."""


class TrafficRunInvalid(ValueError):
    """A `TrafficRun` read back from disk that cannot be trusted.

    Loud on read, never a warning. A verifier that runs against a half-written
    record reports pipeline faults that are file faults.
    """


# ----------------------------------------------------------------------
# window arithmetic -- epoch maths, and NOT a logging concept
# ----------------------------------------------------------------------
# These two are the twins of `os_report.seconds_to_boundary` /
# `window_bounds`, and they are here rather than imported for the reason this
# file exists: importing them would put an OpenSearch client in the traffic
# side's import graph to get twelve lines of `//`. They take `seconds` as an
# argument and know nothing about what the number means.
def window_bounds(when, seconds):
    """The wall-clock-aligned window `when` falls in, as `(start, end)` ISO Z."""
    epoch = when if isinstance(when, (int, float)) else when.timestamp()
    lo = int(epoch // seconds) * seconds
    return _iso(lo), _iso(lo + seconds)


def seconds_to_boundary(window_seconds, lag=0.0, now=None):
    """Seconds to wait so the next call lands at the start of a fresh window."""
    now = time.time() if now is None else now
    return (window_seconds - (now % window_seconds)) + lag


def _iso(epoch):
    return (
        datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        + "Z"
    )


# ----------------------------------------------------------------------
# configuration
# ----------------------------------------------------------------------
def config_from_env(env="local"):
    """Everything `drive` needs, from THIS repo's gitignored config.

    `local-k8s` never holds a Polaris credential: it calls this, and the
    secrets are read by `init_env` out of `src/config/<env>.yaml` (or the env
    vars that override it) inside this checkout.

    The import is deliberately function-local. `polaris_test_utils` is the
    repo's config loader and is allowed on this side, but it pulls a client
    library along with it, and there is no reason for `import make_traffic` --
    which `local-k8s` does at collection, before it has decided anything -- to
    pay for that or to touch a config file.
    """
    import polaris_test_utils as ptu

    ptu.init_env(env)
    ptu.require_not_prod(
        "the traffic drive creates and deletes catalogs, principals, roles, "
        "namespaces, a table and a view, and provokes 500s"
    )
    return {
        "env": ptu.ENV,
        "polaris_url": ptu.POLARIS_URL,
        "realm": ptu.REALM,
        "root_client": ptu.ROOT_CLIENT,
        "root_secret": ptu.ROOT_SECRET,
        "bucket": ptu.BUCKET,
        "minio_endpoint": ptu.MINIO_ENDPOINT,
        "minio_endpoint_internal": ptu.MINIO_ENDPOINT_INTERNAL,
        "polaris_version": ptu.CFG.get("polaris_version"),
    }


_REQUIRED_CONFIG = (
    "polaris_url",
    "realm",
    "root_client",
    "root_secret",
    "bucket",
    "minio_endpoint",
)


def check_config(config):
    """Raise unless `config` can drive. Returns it, so it composes."""
    if not isinstance(config, dict):
        raise ContractError(f"config must be a dict, not {type(config).__name__}")
    missing = [k for k in _REQUIRED_CONFIG if not config.get(k)]
    if missing:
        raise ContractError(
            f"config is missing {missing}. `config_from_env()` builds a complete "
            "one; a hand-built dict has to carry all of "
            f"{list(_REQUIRED_CONFIG)}."
        )
    if str(config.get("env", "local")).lower() == "prod":
        raise ContractError(
            "refusing to drive against PROD. The drive MUTATES: it creates and "
            "deletes catalogs, principals, roles, namespaces, a table and a view."
        )
    return config


# ----------------------------------------------------------------------
# the record
# ----------------------------------------------------------------------
_TRAFFIC_RUN_FIELDS = (
    "contract_version",
    "run",
    "driven_at",
    "profile",
    "polaris",
    "fixture",
    "identities",
    "window_seconds",
    "windows",
    "phases",
    "calls",
    "claims",
    "coverage",
    "build_findings",
    "incomplete",
)


class TrafficRun:
    """What was driven, and what Polaris said. No claim about storage.

    Written to `runs/traffic-<run>.json` as EVIDENCE, not as an interface: a
    run that is only a Python object cannot be re-verified after a gate is
    fixed, cannot be compared against last week's, and cannot be looked at when
    someone asks why the report said what it said.
    """

    __slots__ = _TRAFFIC_RUN_FIELDS

    def __init__(self, **kw):
        unknown = set(kw) - set(_TRAFFIC_RUN_FIELDS)
        if unknown:
            raise ContractError(f"unknown TrafficRun field(s): {sorted(unknown)}")
        for name in _TRAFFIC_RUN_FIELDS:
            setattr(self, name, kw.get(name))
        if self.contract_version is None:
            self.contract_version = CONTRACT_VERSION
        for name in ("phases", "calls", "claims", "build_findings"):
            if getattr(self, name) is None:
                setattr(self, name, [])
        for name in ("polaris", "fixture", "identities", "windows", "coverage"):
            if getattr(self, name) is None:
                setattr(self, name, {})

    def to_dict(self):
        return {name: getattr(self, name) for name in _TRAFFIC_RUN_FIELDS}

    def write(self, runs_dir):
        """Write `runs/traffic-<run>.json` and return the path."""
        d = pathlib.Path(runs_dir)
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"traffic-{self.run}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))
        return path

    @classmethod
    def from_dict(cls, data):
        """Rebuild from JSON, refusing anything a verifier must not trust."""
        if not isinstance(data, dict):
            raise TrafficRunInvalid(f"expected an object, got {type(data).__name__}")
        got = data.get("contract_version")
        if got != CONTRACT_VERSION:
            raise TrafficRunInvalid(
                f"contract_version {got!r} != {CONTRACT_VERSION}. The row shape "
                "changed; read the diff rather than coercing this file."
            )
        for name in ("run", "profile", "window_seconds"):
            if data.get(name) in (None, ""):
                raise TrafficRunInvalid(f"{name} is missing")
        if not data.get("calls"):
            raise TrafficRunInvalid(
                "calls is empty. A run that drove nothing is not evidence that "
                "the pipeline stored nothing."
            )
        first = (data.get("windows") or {}).get("first")
        last = (data.get("windows") or {}).get("last")
        if first and last and str(first) > str(last):
            raise TrafficRunInvalid(
                f"windows.first {first} is after windows.last {last}"
            )
        span = {w for w in ((data.get("windows") or {}).get("distinct") or ()) if w}
        for claim in data.get("claims") or ():
            w = claim.get("window")
            if span and w and w not in span:
                raise TrafficRunInvalid(
                    f"claim {claim.get('claim')!r} names window {w}, which is not "
                    f"one of the run's {len(span)} windows"
                )
        return cls(**{k: v for k, v in data.items() if k in set(_TRAFFIC_RUN_FIELDS)})

    @classmethod
    def read(cls, path):
        return cls.from_dict(json.loads(pathlib.Path(path).read_text()))

    def __repr__(self):  # pragma: no cover - debugging aid
        return (
            f"<TrafficRun {self.run} profile={self.profile} "
            f"calls={len(self.calls)} incomplete={self.incomplete!r}>"
        )


#: The per-call row, exactly as PLAN §3.2 fixes it. No expectation about
#: storage appears here, and adding one is a contract change.
_CALL_FIELDS = (
    "request_id",
    "echoed",
    "echo_ok",
    "op_id",
    "method",
    "path",
    "api",
    "target",
    "status",
    "response_bytes",
    "principal",
    "phase",
    "window",
    "issued_at",
    "verdict",
)


def call_row(row, window_seconds, phase=None):
    """One driven row, reduced to the contract's fields.

    `echo_ok` is None -- not False -- when nothing came back to compare,
    because "the header was absent" and "the header disagreed" accuse different
    repos and collapsing them loses the distinction the check exists for.
    """
    rid = row.get("request_id")
    echoed = row.get("echoed_request_id")
    echo_ok = None if echoed is None else (echoed == rid)
    issued = row.get("issued_at")
    return {
        "request_id": rid,
        "echoed": echoed,
        "echo_ok": echo_ok,
        "op_id": row.get("op_id"),
        "method": (row.get("method") or "").upper(),
        "path": row.get("actual_path") or row.get("path"),
        "api": row.get("api"),
        "target": row.get("target"),
        "status": row.get("status"),
        "response_bytes": row.get("response_bytes"),
        "principal": row.get("principal"),
        "phase": phase if phase is not None else row.get("phase"),
        "window": window_bounds(issued, window_seconds)[0] if issued else None,
        "issued_at": issued,
        "verdict": row.get("verdict"),
    }


def echo_failures(calls):
    """Calls whose id did not come back. A fault HERE, never in the pipeline."""
    return [c for c in calls if c.get("request_id") and c.get("echo_ok") is False]


# ----------------------------------------------------------------------
# claims -- request-id-keyed, so the verifier needs no Polaris knowledge
# ----------------------------------------------------------------------
def claim_last_write_bytes(request_id, window, equals):
    return {
        "claim": "last_write_bytes",
        "window": window,
        "request_id": request_id,
        "equals": equals,
        "because": "the only 2xx write to a table in that window",
    }


def claim_no_last_write_bytes(request_id, window):
    return {
        "claim": "last_write_bytes_absent",
        "window": window,
        "request_id": request_id,
        "because": "a DELETE was the window's only write, and it returned no body -- "
        "the field must be ABSENT, not 0",
    }


def claim_role_writes(request_ids, window, equals):
    return {
        "claim": "role_writes",
        "window": window,
        "request_ids": list(request_ids),
        "equals": equals,
        "because": f"{equals} privilege(s) granted on one role, all 2xx",
    }


def claim_auth_denied(request_id, window, at_least=1):
    return {
        "claim": "auth_denied",
        "window": window,
        "request_id": request_id,
        "at_least": at_least,
        "because": "a denial on that role in that window, with no prior success "
        "from that identity",
    }


# ----------------------------------------------------------------------
# build findings -- facts about POLARIS, never work for `local-k8s`
# ----------------------------------------------------------------------
def build_findings(calls):
    """What this build did, read off the rows alone.

    SCENARIO §3 rule 3: `createNamespace` answering 500, `reportMetrics`
    answering 204 unauthorised, four endpoints unrouted -- those are facts
    about Polaris. Today's `REPORT-for-local-k8s.md` mixes them into the
    pipeline's work list and sends four Polaris facts to the wrong repo, so
    they are collected under their own name here and the report keeps them
    under their own heading.
    """
    out = []
    fivehundred = [c for c in calls if (c.get("status") or 0) >= 500]
    if fivehundred:
        out.append(
            {
                "about": "polaris",
                "title": f"{len(fivehundred)} response(s) of 500",
                "measured": "; ".join(
                    f"{c['op_id']} (target {c['target']}, as {c['principal']})"
                    for c in fivehundred
                ),
                "request_ids": [
                    c["request_id"] for c in fivehundred if c["request_id"]
                ],
            }
        )

    by_op = {}
    for c in calls:
        by_op.setdefault(c.get("op_id"), []).append(c)

    unrouted = sorted(
        op
        for op, rows in by_op.items()
        if op and len(rows) > 1 and all((r.get("status") or 0) == 404 for r in rows)
    )
    if unrouted:
        out.append(
            {
                "about": "polaris",
                "title": f"{len(unrouted)} operation(s) not routed on this build",
                "measured": ", ".join(unrouted)
                + " -- 404 to EVERY cell including the unauthenticated one, which "
                "is what separates 'not routed' from 'not found'",
                "request_ids": [],
            }
        )

    unauth_ok = [
        c
        for c in calls
        if c.get("target") in (401, 403) and 200 <= (c.get("status") or 0) < 300
    ]
    if unauth_ok:
        out.append(
            {
                "about": "polaris",
                "title": f"{len(unauth_ok)} cell(s) answered 2xx to an identity that "
                "should not have been allowed",
                "measured": "; ".join(
                    f"{c['op_id']} target {c['target']} -> {c['status']} as {c['principal']}"
                    for c in unauth_ok
                ),
                "request_ids": [c["request_id"] for c in unauth_ok if c["request_id"]],
            }
        )
    return out


def coverage_of(calls):
    """`{covered, missed, error, by_target}` over the contract's rows."""
    covered = missed = error = 0
    by_target = {}
    for c in calls:
        verdict = c.get("verdict")
        bucket = by_target.setdefault(
            str(c.get("target")), {"covered": 0, "missed": 0, "error": 0}
        )
        if c.get("status") is None:
            error += 1
            bucket["error"] += 1
        elif verdict == "covered":
            covered += 1
            bucket["covered"] += 1
        else:
            missed += 1
            bucket["missed"] += 1
    return {
        "covered": covered,
        "missed": missed,
        "error": error,
        "by_target": by_target,
    }


# ----------------------------------------------------------------------
# the drive
# ----------------------------------------------------------------------
def drive(
    config,
    *,
    window_seconds,
    profile="full",
    run=None,
    on_row=None,
    dry_run=False,
    spec_dir=None,
    runs_dir=None,
):
    """Drive Polaris and return a `TrafficRun`. Never look at a log.

    Args:
        config: from `config_from_env()`, or any dict carrying the same keys.
        window_seconds: **the caller's number.** This module aligns phases to
            a grid of this size and has no opinion about what the grid is for.
        profile: one of `PROFILES`.
        run: the run id. Defaults to the epoch second, which is what every
            document in this repo has called a run since v1.
        on_row: called with each contract row as it is driven, for progress.
        dry_run: build every request and CONTACT NOTHING. No token, no
            fixture, no mutation -- so it is safe against a cluster that is
            down, or absent. It answers one question only: does every cell in
            the grid produce a request at all. A missing payload or an
            unbindable path is a harness bug, and finding it at call 200 of
            286 wastes the run's windows. **It does not say the requests are
            VALID** -- `spec_check.check_requests` asks that, against Prism.
        spec_dir: the vendored OpenAPI documents. Defaults to
            `log-coverage/spec` beside this checkout -- the run's denominator
            is a fact about the specs, not about the cluster.
        runs_dir: where `traffic-<run>.json` is written. Defaults to
            `runs/` beside this checkout. Pass `False` to write nothing.

    Returns:
        `TrafficRun`. It ALWAYS returns one: a drive that dies at call 40
        cleans up, sets `incomplete`, and returns what it drove.
    """
    if profile not in PROFILES:
        raise ContractError(f"unknown profile {profile!r}. Known: {sorted(PROFILES)}")
    if not isinstance(window_seconds, (int, float)) or window_seconds <= 0:
        raise ContractError(
            f"window_seconds must be a positive number, got {window_seconds!r}. "
            "It is an ARGUMENT: this module never reads it from a ConfigMap."
        )
    check_config(config)

    # Imported here, not at module scope, so the guard test can walk
    # `make_traffic`'s own graph and so `import make_traffic` stays cheap.
    import api_status_matrix as mx
    import api_surface as surf
    import traffic_helpers as th
    from iceberg_rest import IcebergREST, build_create_table_payload, build_schema
    from polaris_rest import PolarisREST

    run = str(run or int(time.time()))
    base, realm = config["polaris_url"], config["realm"]
    spec_dir = pathlib.Path(
        spec_dir
        or pathlib.Path(__file__).resolve().parent.parent / "log-coverage" / "spec"
    )

    if dry_run:
        return _dry_run(config, run, profile, window_seconds, spec_dir, runs_dir)

    state = {
        "calls": [],
        "claims": [],
        "phases": [],
        "incomplete": None,
        "fixture": {},
        "identities": {},
    }
    fx = adm_pc = adm_ic = run_ic = denied_pc = None
    # Declared before the try so `finally` can clean up whatever setup reached.
    binding = {}
    runner_name = f"mx_{run}_runner"
    runner_role = f"mx_{run}_runner_role"
    denied_name = f"mx_{run}_denied"
    denied_role = f"mx_{run}_denied_role"

    def record(rows, phase):
        out = []
        for row in rows:
            c = call_row(row, window_seconds, phase=phase)
            state["calls"].append(c)
            out.append(c)
            if on_row:
                on_row(c)
        return out

    def phase_window(name, t0, t1, cells):
        w0 = window_bounds(t0, window_seconds)[0]
        w1 = window_bounds(t1, window_seconds)[0]
        entry = {
            "name": name,
            "start": w0,
            "end": w1,
            "straddled": w0 != w1,
            "cells": cells,
            "seconds": round(t1 - t0, 1),
        }
        state["phases"].append(entry)
        return entry

    try:
        root_tok = _root_token(config, PolarisREST)
        adm_pc = PolarisREST(base, realm, token=root_tok)
        adm_ic = IcebergREST(base, realm, token=root_tok)
        schema = build_schema([(1, "id", "long", True), (2, "val", "string", False)])
        tokens = {mx.ADMIN: root_tok}

        # THE DENIED IDENTITY IS PROVISIONED WITHOUT THE FIXTURE, ON PURPOSE:
        # a role and no grants at all is exactly what a 403 cell needs.
        denied_cid, denied_sec = th.provision_run_principal(
            adm_pc, denied_name, denied_role, fixture=None, service_admin=False
        )
        r = adm_pc.get_token(
            denied_cid, denied_sec, scope=f"PRINCIPAL_ROLE:{denied_role}"
        )
        if r.status_code == 200:
            tokens[mx.DENIED] = r.json()["access_token"]
            state["identities"]["denied"] = denied_name
        else:
            tokens[mx.DENIED] = mx.GARBAGE_TOKEN
            state["identities"]["denied"] = f"{denied_name} (NO TOKEN: {r.status_code})"

        fx = surf.ProbeFixture(prefix=f"apimatrix{run}")
        surf.setup_fixture(
            fx,
            adm_pc,
            adm_ic,
            config["bucket"],
            config["minio_endpoint"],
            schema,
            build_create_table_payload,
        )

        # THE RUNNER IS ELECTED ONLY NOW. `provision_run_principal` grants the
        # probe catalog's rights only when it is handed the fixture -- catalog
        # operations authorize against `grant_records` for the TARGET catalog
        # and `service_admin` does not cover them. Elected before the fixture
        # existed, the runner holds a role and no privileges, and 19 of the 2xx
        # cells came back 403: run 1789007773 then reported a Polaris that
        # refuses every catalog operation, which was a statement about the
        # harness.
        identity, run_pc, _run_ic, drive_principal, _notes = th.elect_drive_identity(
            adm_pc,
            adm_ic,
            base,
            realm,
            runner_name,
            runner_role,
            fixture=fx,
            root_token=root_tok,
        )
        tokens[mx.RUNNER] = run_pc.token or root_tok
        run_ic = IcebergREST(base, realm, token=tokens[mx.RUNNER])
        state["identities"].update(
            {"admin": "root", "runner": drive_principal, "elected": identity}
        )

        binding.update(_binding(config, fx, run, runner_name, runner_role))
        state["fixture"] = {
            "catalog": fx.cat,
            "namespace": fx.ns,
            "table": fx.tbl,
            "view": fx.view,
            **{k: v for k, v in binding.items() if k.startswith("doomed_")},
        }
        adm_pc.create_catalog_role(fx.cat, binding["catalogRoleName"])
        _setup_doomed(
            adm_pc, adm_ic, fx, binding, config, schema, build_create_table_payload
        )

        ops = mx.load_spec(spec_dir)
        grid = mx.cells(ops)
        # Every cell builds a request before ANY of them is issued. A missing
        # payload or an unbindable path is a harness bug, and finding it at
        # call 200 of 286 wastes the run's windows.
        for cell in grid:
            mx.request_for(cell, binding, tokens, "dry-run", realm)

        wanted = _PHASES[profile]
        if "B" in wanted:
            cells_ = [c for c in grid if c.phase == "B" and c.target == 2]
            if profile == "smoke":
                cells_ = cells_[:SMOKE_CELLS]
            _grid_phase(
                "B",
                cells_,
                mx,
                binding,
                tokens,
                base,
                realm,
                run,
                window_seconds,
                record,
                phase_window,
                len(state["calls"]),
            )
        for name in ("C", "D"):
            if name in wanted:
                _grid_phase(
                    name,
                    [c for c in grid if c.phase == name],
                    mx,
                    binding,
                    tokens,
                    base,
                    realm,
                    run,
                    window_seconds,
                    record,
                    phase_window,
                    len(state["calls"]),
                )
        if "E" in wanted:
            _phase_commit(
                state, th, mx, run, run_ic, fx, window_seconds, record, phase_window
            )
        if "F" in wanted:
            _phase_delete(
                state,
                th,
                mx,
                run,
                run_ic,
                fx,
                schema,
                build_create_table_payload,
                window_seconds,
                record,
                phase_window,
            )
        if "G" in wanted:
            denied_pc = PolarisREST(base, realm, token=tokens[mx.DENIED])
            _phase_grants(
                state,
                th,
                mx,
                run,
                adm_pc,
                denied_pc,
                fx,
                binding,
                window_seconds,
                record,
                phase_window,
            )
        if "H" in wanted:
            _phase_500(
                state,
                th,
                run,
                adm_pc,
                run_ic,
                config,
                schema,
                build_create_table_payload,
                window_seconds,
                record,
                phase_window,
            )
    except BaseException as exc:  # noqa: BLE001 - a KeyboardInterrupt still cleans up
        state["incomplete"] = (
            f"{type(exc).__name__}: {exc} -- after {len(state['calls'])} call(s). "
            "Every downstream check over this run is UNPROVEN, not FAIL."
        )
    finally:
        # THE CLEANUP DELETES ARE PART OF THE TEST, not tidying: dropTable,
        # dropView, dropNamespace, deleteCatalog and deletePrincipal are five
        # of the 63 operations. They are recorded as phase I, and they run
        # even when the drive died -- a session that dies must not leave a
        # catalog behind.
        if adm_pc is not None:
            _cleanup(
                state,
                run,
                adm_pc,
                run_ic,
                fx,
                binding,
                runner_name,
                runner_role,
                denied_name,
                denied_role,
                window_seconds,
                record,
                phase_window,
            )
        for client in (adm_pc, adm_ic, run_ic, denied_pc):
            try:
                client.session.close()
            except Exception:  # noqa: BLE001
                pass

    return _finish(state, run, profile, config, window_seconds, runs_dir)


def _root_token(config, polaris_rest_cls):
    pc = polaris_rest_cls(config["polaris_url"], config["realm"])
    r = pc.get_token(config["root_client"], config["root_secret"])
    if r.status_code != 200:
        raise ContractError(
            f"no root token from {config['polaris_url']}: {r.status_code} {r.text[:200]}"
        )
    return r.json()["access_token"]


def _binding(config, fx, run, runner_name, runner_role):
    """The names every cell is shaped against.

    The `doomed_*` family is the load-bearing part. The happy sweep drives
    `deleteCatalog`, `dropTable`, `dropView`, `dropNamespace`,
    `deletePrincipal` and the two revokes; bound naively they take the FIXTURE
    and the run destroys itself at about call 30 of 63, with every later cell
    404ing. `api_status_matrix.REBIND` points them here instead, so the deletes
    are real deletes of real entities and nothing the run still needs.
    """
    return {
        "catalog": fx.cat,
        "namespace": fx.ns,
        "table": fx.tbl,
        "view": fx.view,
        "principalName": runner_name,
        "principalRoleName": runner_role,
        "catalogRoleName": f"mx_{run}_crole",
        "plan-id": "no-such-plan-id",
        "new_catalog": f"mx{run}cat2",
        "new_namespace": f"mx_{run}_ns2",
        "new_table": f"mx_{run}_tbl2",
        "new_view": f"mx_{run}_vw2",
        "new_principal": f"mx_{run}_p2",
        "new_principal_role": f"mx_{run}_prole2",
        "new_catalog_role": f"mx_{run}_crole2",
        "renamed_table": f"{fx.tbl}_renamed",
        "renamed_view": f"{fx.view}_renamed",
        "doomed_catalog": f"mx{run}doomed",
        "doomed_namespace": f"mx_{run}_ns_doomed",
        "doomed_table": f"mx_{run}_tbl_doomed",
        "doomed_view": f"mx_{run}_vw_doomed",
        "doomed_principal": f"mx_{run}_p_doomed",
        "doomed_principal_role": f"mx_{run}_prole_doomed",
        "doomed_catalog_role": f"mx_{run}_crole_doomed",
        "entity_version": 1,
        "run": run,
        "base_location": f"s3a://{config['bucket']}/mx{run}cat2/",
        "allowed_location": f"s3a://{config['bucket']}/",
        "s3_endpoint": config["minio_endpoint"],
        "s3_endpoint_internal": config.get("minio_endpoint_internal"),
        "metadata_location": (
            f"s3a://{config['bucket']}/mx{run}cat2/never-registered/metadata.json"
        ),
        "client_id": config["root_client"],
        "client_secret": config["root_secret"],
    }


def dry_binding(config, run):
    """The binding a dry run shapes its requests against.

    The names are the ones a real run WOULD use -- `ProbeFixture` derives them
    from the prefix and touches nothing -- so an unbindable path fails here
    exactly as it would there. What is synthetic is only the credentials.
    """
    import api_surface as surf

    fx = surf.ProbeFixture(prefix=f"apimatrix{run}")
    return fx, _binding(config, fx, run, f"mx_{run}_runner", f"mx_{run}_runner_role")


#: What a dry run puts in the Authorization header. Not a token, and shaped so
#: that a request built with it could never be mistaken for one that was sent.
DRY_TOKEN = "dry-run-no-token-was-minted"  # noqa: S105


def _dry_run(config, run, profile, window_seconds, spec_dir, runs_dir):
    """Build every request in the grid and CONTACT NOTHING.

    WHY THIS TOUCHES NO CLUSTER, when the first version of it did. The check
    used to sit after the fixture was built, so a "dry run" created a catalog,
    a namespace, a table, a view, two principals, two roles and the whole
    `doomed_*` family before declining to issue the grid -- dozens of mutating
    calls, against a docstring that said it issued none. It also returned from
    inside the `try`, so the record was assembled and written to `runs/` BEFORE
    `finally` ran cleanup, and came back missing its own phase-I rows.

    Both were one mistake: a check that belongs before the work was placed
    after it. It is the floor now -- runnable with Polaris down, or absent --
    and `spec_check.check_requests` is the tier above it.
    """
    import api_status_matrix as mx

    fx, binding = dry_binding(config, run)
    tokens = {mx.ADMIN: DRY_TOKEN, mx.RUNNER: DRY_TOKEN, mx.DENIED: DRY_TOKEN}
    grid = mx.cells(mx.load_spec(spec_dir))
    for cell in grid:
        mx.request_for(cell, binding, tokens, "dry-run", config["realm"])
    state = {
        "calls": [],
        "claims": [],
        "phases": [],
        "fixture": {
            "catalog": fx.cat,
            "namespace": fx.ns,
            "table": fx.tbl,
            "view": fx.view,
        },
        "identities": {},
        "incomplete": (
            f"dry_run: {len(grid)} requests were built, none was issued, and "
            "nothing was created. This says every cell PRODUCES a request, not "
            "that any of them is valid -- spec_check.check_requests asks that."
        ),
    }
    # No calls, so `_finish` writes no evidence file. A dry run has none to give.
    return _finish(state, run, profile, config, window_seconds, runs_dir)


def _setup_doomed(adm_pc, adm_ic, fx, binding, config, schema, table_payload):
    """Create the entities the destructive cells are pointed at.

    Returns `{label: status}`. A setup that did not fully succeed is not fatal:
    the delete cells for those entities report 404 and are MISSED -- correctly,
    and as a harness gap rather than a pipeline finding.
    """
    out = {}
    out["doomed catalog"] = adm_pc.create_catalog(
        binding["doomed_catalog"],
        config["bucket"],
        config["minio_endpoint"],
        minio_endpoint_internal=config.get("minio_endpoint_internal"),
    ).status_code
    out["doomed namespace"] = adm_ic.create_namespace(
        fx.cat, binding["doomed_namespace"]
    ).status_code
    out["doomed table"] = adm_ic.create_table(
        fx.cat, fx.ns, table_payload(binding["doomed_table"], schema)
    ).status_code
    out["doomed view"] = adm_ic.create_view(
        fx.cat,
        fx.ns,
        {
            "name": binding["doomed_view"],
            "schema": schema,
            "view-version": {
                "version-id": 1,
                "timestamp-ms": 0,
                "schema-id": 0,
                "summary": {"engine-name": "make-traffic"},
                "default-namespace": [fx.ns],
                "representations": [
                    {"type": "sql", "sql": "SELECT 1", "dialect": "spark"}
                ],
            },
            "properties": {"mx.run": binding["run"]},
        },
    ).status_code
    out["doomed principal"] = adm_pc.create_principal(
        binding["doomed_principal"]
    ).status_code
    out["doomed principal role"] = adm_pc.create_principal_role(
        binding["doomed_principal_role"]
    ).status_code
    out["doomed catalog role"] = adm_pc.create_catalog_role(
        fx.cat, binding["doomed_catalog_role"]
    ).status_code
    out["assign prole->principal"] = adm_pc.assign_principal_role_to_principal(
        binding["doomed_principal"], binding["doomed_principal_role"]
    ).status_code
    # ARGUMENT ORDER IS (catalog, principal_role, catalog_role) -- and this PUT
    # can 404 immediately after `create_catalog_role` on PG-HA read-after-write
    # lag, which is a known signature here and not a finding. Retry rather than
    # record a false one.
    for _try in range(4):
        r = adm_pc.assign_catalog_role_to_principal_role(
            fx.cat, binding["doomed_principal_role"], binding["doomed_catalog_role"]
        )
        out["assign crole->prole"] = r.status_code
        if r.status_code != 404:
            break
        time.sleep(0.75)
    return out


def _grid_phase(
    name,
    cells_,
    mx,
    binding,
    tokens,
    base,
    realm,
    run,
    window_seconds,
    record,
    phase_window,
    seq_from,
):
    """One grid phase, alone in its window.

    Deliberately serial, and deliberately waiting for a boundary first. The
    report attributes a request to a window by the time it was served, so
    concurrent calls straddling a boundary would make the per-window margins
    UNPROVABLE rather than wrong -- which is worse, because it looks like a
    pass.
    """
    if not cells_:
        return []
    time.sleep(seconds_to_boundary(window_seconds, lag=0.5))
    t0 = time.time()
    rows = mx.drive(cells_, binding, tokens, base, realm, run, seq_from=2000 + seq_from)
    t1 = time.time()
    phase_window(name, t0, t1, len(cells_))
    return record(rows, name)


def _tagged(th, clients, request_id_, fn):
    """One call with an id on it, and the id off again afterwards."""
    th.tag_clients(clients, request_id_)
    try:
        return fn()
    finally:
        th.tag_clients(clients, None)


def _row_from(resp, request_id_, op_id, method, target, principal):
    return {
        "request_id": request_id_,
        "echoed_request_id": getattr(resp, "headers", {}).get("Polaris-Request-Id"),
        "op_id": op_id,
        "method": method,
        "actual_path": getattr(getattr(resp, "request", None), "path_url", None),
        "api": "catalog",
        "target": target,
        "status": getattr(resp, "status_code", None),
        "response_bytes": len(getattr(resp, "content", b"") or b""),
        "principal": principal,
        "issued_at": time.time(),
        "verdict": "covered",
    }


def _phase_commit(state, th, mx, run, run_ic, fx, window_seconds, record, phase_window):
    """ONE commit, alone in its window. The feature; everything else is plumbing.

    The claim is what the verifier resolves: `last_write_bytes` on the table
    row must equal the response size of THIS request id. The byte count taken
    here is what the CLIENT received -- the access log is the authority, and
    the two should agree.
    """
    time.sleep(seconds_to_boundary(window_seconds, lag=0.5))
    t0 = time.time()
    rid = mx.request_id(run, 3001, "gate2-the-commit")
    resp = _tagged(
        th,
        [run_ic],
        rid,
        lambda: run_ic.commit_table(
            fx.cat,
            fx.ns,
            fx.tbl,
            [{"action": "set-properties", "updates": {"mx.gate2": run}}],
        ),
    )
    row = _row_from(resp, rid, "updateTable", "POST", 200, "runner")
    row["issued_at"] = t0
    entry = phase_window("E", t0, t0, 1)
    record([row], "E")
    state["claims"].append(
        claim_last_write_bytes(rid, entry["start"], row["response_bytes"])
    )
    return row


def _phase_delete(
    state,
    th,
    mx,
    run,
    run_ic,
    fx,
    schema,
    table_payload,
    window_seconds,
    record,
    phase_window,
):
    """Gate 2's negative half, which is the one people skip.

    A window whose only write was a DELETE (204, empty body) must carry NO
    `last_write_bytes` at all -- ABSENT, not 0. The table is created in the
    PREVIOUS window, deliberately, so the delete is alone in its own.

    If the DELETE comes back with a body, the `size > 0` rule that separates a
    commit from a drop no longer applies, so no claim is made: the negative
    case is VOID rather than failed, and a claim nobody can resolve is worse
    than no claim.
    """
    doomed = f"mx_{run}_droponly"
    run_ic.create_table(fx.cat, fx.ns, table_payload(doomed, schema))
    time.sleep(seconds_to_boundary(window_seconds, lag=0.5))
    t0 = time.time()
    rid = mx.request_id(run, 3002, "gate2-the-delete")
    resp = _tagged(th, [run_ic], rid, lambda: run_ic.drop_table(fx.cat, fx.ns, doomed))
    row = _row_from(resp, rid, "dropTable", "DELETE", 204, "runner")
    row["issued_at"] = t0
    entry = phase_window("F", t0, t0, 1)
    record([row], "F")
    if row["response_bytes"] == 0:
        state["claims"].append(claim_no_last_write_bytes(rid, entry["start"]))
    else:
        state["incomplete"] = state["incomplete"] or (
            f"the DELETE returned {row['response_bytes']} bytes, so the "
            "last_write_bytes_absent claim was not made -- that check is VOID, "
            "not failed"
        )
    return row


def _phase_grants(
    state,
    th,
    mx,
    run,
    adm_pc,
    denied_pc,
    fx,
    binding,
    window_seconds,
    record,
    phase_window,
):
    """Grants, and a denied read on the same role, in one window.

    `writes` on a `catalog-role` row is the number of privileges granted in
    that window: grants fold into the role they are granted on. The denial is
    what forces the role's row to exist even under the `ROLE_KINDS` exemption,
    and it is the half that makes the count falsifiable.
    """
    crole = binding["catalogRoleName"]
    time.sleep(seconds_to_boundary(window_seconds, lag=0.5))
    t0 = time.time()
    rows, granted_ids = [], []
    for i, priv in enumerate(GATE4_GRANTS):
        rid = mx.request_id(run, 3100 + i, f"gate4-grant-{priv}")
        resp = _tagged(
            th, [adm_pc], rid, lambda p=priv: adm_pc.grant_privilege(fx.cat, crole, p)
        )
        row = _row_from(resp, rid, "addGrantToCatalogRole", "PUT", 201, "root")
        row["api"] = "management"
        rows.append(row)
        if 200 <= (row["status"] or 0) < 300:
            granted_ids.append(rid)

    denied_rid = mx.request_id(run, 3199, "gate4-denied-role-read")
    resp = _tagged(
        th, [denied_pc], denied_rid, lambda: denied_pc.get_catalog_role(fx.cat, crole)
    )
    denied_row = _row_from(resp, denied_rid, "getCatalogRole", "GET", 403, "denied")
    denied_row["api"] = "management"
    rows.append(denied_row)

    t1 = time.time()
    entry = phase_window("G", t0, t1, len(rows))
    record(rows, "G")
    state["claims"].append(
        claim_role_writes(granted_ids, entry["start"], len(granted_ids))
    )
    # A denial that did not come back as a denial cannot force the row, and a
    # claim the verifier cannot resolve reports a pipeline fault that is a
    # traffic fault.
    if denied_row["status"] in (401, 403):
        state["claims"].append(claim_auth_denied(denied_rid, entry["start"]))
    return rows


def _phase_500(
    state,
    th,
    run,
    adm_pc,
    run_ic,
    config,
    schema,
    table_payload,
    window_seconds,
    record,
    phase_window,
):
    """The 500 ladder, in its own pure window.

    The honest-failure contract is the point: if every rung answers 2xx or 4xx
    the result carries `winner=None`, and NOT PROVOKED is the correct outcome
    rather than a fallback to whatever 500s the drive produced by itself. On
    this build every rung answered a 4xx on 2026-09-07 -- a broken storage
    endpoint is 422, a missing bucket 400, a stale `entityVersion` 409, all
    mapped by `IcebergExceptionMapper` -- so storage misconfiguration is a
    CLIENT error here and `errors_5xx` may go unexercised.
    """
    provokers = th.provokers_500(
        adm_pc,
        run_ic,
        run,
        bucket=config["bucket"],
        endpoint=config["minio_endpoint"],
        endpoint_internal=config.get("minio_endpoint_internal"),
        table_payload=lambda name: table_payload(name, schema),
        repeat=3,
    )
    time.sleep(seconds_to_boundary(window_seconds, lag=0.5))
    t0 = time.time()
    result = th.drive_500([adm_pc, run_ic], run, 3200, provokers)
    t1 = time.time()
    rows = result["rows"]
    for row in rows:
        row.setdefault("op_id", row.get("label"))
        row.setdefault("target", 500)
        row.setdefault(
            "verdict", "covered" if (row.get("status") or 0) >= 500 else "missed"
        )
    phase_window("H", t0, t1, len(rows))
    record(rows, "H")
    return result


def _cleanup(
    state,
    run,
    adm_pc,
    run_ic,
    fx,
    binding,
    runner_name,
    runner_role,
    denied_name,
    denied_role,
    window_seconds,
    record,
    phase_window,
):
    """Phase I. Part of the test, and it runs whatever happened above.

    Never raises: a failure here must not lose the run's findings, and a run
    that dies in cleanup with a catalog still standing is the leak this
    function exists to prevent.
    """
    import traffic_helpers as th

    t0 = time.time()
    steps = []
    if fx is not None and run_ic is not None:
        steps += [
            ("dropView", "DELETE", lambda: run_ic.drop_view(fx.cat, fx.ns, fx.view)),
            ("dropTable", "DELETE", lambda: run_ic.drop_table(fx.cat, fx.ns, fx.tbl)),
            ("dropNamespace", "DELETE", lambda: run_ic.drop_namespace(fx.cat, fx.ns)),
        ]
    if fx is not None and binding.get("catalogRoleName"):
        steps.append(
            (
                "deleteCatalogRole",
                "DELETE",
                lambda: adm_pc.delete_catalog_role(fx.cat, binding["catalogRoleName"]),
            )
        )
    if fx is not None:
        steps.append(("deleteCatalog", "DELETE", lambda: adm_pc.delete_catalog(fx.cat)))
    for key, op in (
        ("new_principal", "deletePrincipal"),
        ("new_principal_role", "deletePrincipalRole"),
        ("new_catalog", "deleteCatalog"),
    ):
        name = binding.get(key)
        if not name:
            continue
        fn = {
            "new_principal": adm_pc.delete_principal,
            "new_principal_role": adm_pc.delete_principal_role,
            "new_catalog": adm_pc.delete_catalog,
        }[key]
        steps.append((op, "DELETE", lambda f=fn, n=name: f(n)))

    rows = []
    for i, (op_id, method, fn) in enumerate(steps):
        rid = th.request_id(run, 3300 + i, f"cleanup-{op_id}")
        try:
            resp = _tagged(
                th, [adm_pc, run_ic] if run_ic is not None else [adm_pc], rid, fn
            )
            rows.append(_row_from(resp, rid, op_id, method, 204, "root"))
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "request_id": rid,
                    "op_id": op_id,
                    "method": method,
                    "target": 204,
                    "status": None,
                    "issued_at": time.time(),
                    "verdict": "error",
                    "principal": "root",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    for name, role in ((runner_name, runner_role), (denied_name, denied_role)):
        try:
            th.deprovision_run_principal(adm_pc, name, role)
        except Exception:  # noqa: BLE001
            pass

    if rows:
        phase_window("I", t0, time.time(), len(rows))
        record(rows, "I")
    return rows


def _finish(state, run, profile, config, window_seconds, runs_dir):
    """Assemble the record, write it as evidence, and return it."""
    calls = state["calls"]
    starts = sorted({c["window"] for c in calls if c.get("window")})
    traffic = TrafficRun(
        contract_version=CONTRACT_VERSION,
        run=run,
        driven_at=_iso(time.time()),
        profile=profile,
        polaris={
            "url": config["polaris_url"],
            "realm": config["realm"],
            "version": config.get("polaris_version"),
        },
        fixture=state["fixture"],
        identities=state["identities"],
        window_seconds=window_seconds,
        windows={
            "first": starts[0] if starts else None,
            "last": starts[-1] if starts else None,
            "distinct": starts,
        },
        phases=state["phases"],
        calls=calls,
        claims=state["claims"],
        coverage=coverage_of(calls),
        build_findings=build_findings(calls),
        incomplete=state["incomplete"],
    )
    if runs_dir is not False and calls:
        traffic.write(
            runs_dir or pathlib.Path(__file__).resolve().parent.parent / "runs"
        )
    return traffic
