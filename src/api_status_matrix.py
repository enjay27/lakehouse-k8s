"""The operation x status grid: every API the vendored specs name, at every
status this build can actually return.

WHY THIS DOES NOT GO THROUGH THE CLIENT CLASSES
-----------------------------------------------
`api_surface.operations()` drives 40 of the 63 operations, and it drives them
through `PolarisREST` / `IcebergREST` methods. That is the right shape for a
happy-path sweep and the wrong shape here, for two reasons:

* **The 23 operations with no driver are exactly the ones with no client
  method** -- `planTableScan`, `fetchScanTasks`, `fetchPlanningResult`,
  `cancelPlanning`, `loadCredentials` on the catalog side, half the role graph
  on the management side. Binding the grid to client methods would reproduce
  the gap it exists to close.
* **The status axis needs to mutate the REQUEST, not the call.** A 401 is the
  same request with a different Authorization header; a 404 is the same request
  with one path segment replaced. Expressed against a client method those are
  twenty-three special cases; expressed against a (method, path, headers, body)
  tuple they are one transform each.

So the grid is built from the spec's own path templates and issued directly.
The client classes stay where they belong -- setting up the fixture, which is
where their retry and token handling earn their keep.

WHAT A CELL IS
--------------
One (operation, target_status) pair, with everything needed to drive it and
nothing that needs a cluster to compute. A cell that comes back with a status
other than its target is **MISSED, actual=NNN** -- it is never silently
re-labelled as coverage of the status it happened to hit. That relabelling is
how a matrix comes to agree with itself and with nothing else.
"""

import copy
import pathlib

#: Path parameters that name a thing that must exist. `{prefix}` is the Iceberg
#: spec's name for what the management spec calls `{catalogName}` and what this
#: harness calls the catalog -- three names, one value.
CATALOG_PARAMS = ("prefix", "catalogName")

#: The value substituted to provoke a 404. Deliberately ugly: it must not
#: collide with a real fixture name, and it must be visible in a log line.
MISSING = "definitely-not-here-404"

#: Statuses this build cannot produce, with the reason each one is out of
#: reach. An honest gap beats a fabricated pass -- but a reason written from a
#: spec is an assumption, so anything marked `probe` gets ONE call whose result
#: is recorded either way (plan section 2).
NOT_REACHABLE = {
    429: (
        "rateLimiter.type is no-op on this build -- the limiter cannot "
        "produce a 429",
        "settled",
    ),
    502: ("nothing proxies Polaris here; a port-forward is not a gateway", "settled"),
    504: ("same -- no gateway to time out", "settled"),
    503: (
        "the only route is scaling Polaris, and HPA movement invalidates the "
        "run (local-k8s #8)",
        "settled",
    ),
    "5XX": ("a spec placeholder, not a status", "settled"),
    304: ("needs If-None-Match support on loadTable", "probe"),
    406: ("needs content negotiation to refuse a JSON-only endpoint", "probe"),
    419: (
        "Iceberg's credential-refresh code; this build is expected to answer "
        "401 instead",
        "probe",
    ),
}

#: Codes the specs never declare but this build demonstrably returns -- 405 and
#: 500 both appear in `polaris-logs-*` (measured 2026-09-10: 405 x7, 500 x21).
UNDECLARED_EXTRAS = (405, 500)

HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head")


class SpecUnavailable(RuntimeError):
    """`log-coverage/spec/` is empty -- run ./fetch_specs.sh."""


class Operation:
    """One spec operation, with everything the grid needs to shape a request."""

    __slots__ = (
        "op_id",
        "method",
        "template",
        "api",
        "base",
        "declared",
        "params",
        "has_body",
        "source",
    )

    def __init__(
        self, op_id, method, template, api, base, declared, params, has_body, source
    ):
        self.op_id = op_id
        self.method = method.upper()
        self.template = template
        self.api = api
        self.base = base
        self.declared = tuple(declared)
        self.params = tuple(params)
        self.has_body = has_body
        self.source = source

    @property
    def full_template(self):
        return f"{self.base}{self.template}"

    @property
    def key(self):
        return f"{self.method} {self.full_template}"

    def __repr__(self):
        return f"<Operation {self.op_id} {self.method} {self.full_template}>"


class Cell:
    """One (operation, target status) pair.

    `driver` names the transform that produces it, so the matrix can say HOW a
    status was reached and not only that it was. `phase` is the boundary-aligned
    window the call belongs in -- Gate 2 and Gate 4 are only unambiguous when
    their phase is alone in its window.
    """

    __slots__ = ("op", "target", "driver", "phase", "note")

    def __init__(self, op, target, driver, phase, note=""):
        self.op = op
        self.target = target
        self.driver = driver
        self.phase = phase
        self.note = note

    @property
    def key(self):
        return (self.op.op_id, self.target)

    @property
    def label(self):
        return f"{self.op.op_id}@{self.target}"

    def __repr__(self):
        return f"<Cell {self.label} via {self.driver} in phase {self.phase}>"


# ----------------------------------------------------------------------
# the spec
# ----------------------------------------------------------------------
def load_spec(spec_dir):
    """Parse the vendored OpenAPI documents into `Operation`s.

    The base path is taken from the FILE, not guessed from the path template:
    the Iceberg document's paths start `/v1/...` and are served under
    `/api/catalog`, the management document's start `/catalogs` and are served
    under `/api/management/v1`. Getting that wrong produced a matrix that
    reported five management POSTs where there were six (run 1).
    """
    import yaml

    d = pathlib.Path(spec_dir)
    files = sorted(d.glob("*.yml")) + sorted(d.glob("*.yaml")) if d.is_dir() else []
    if not files:
        raise SpecUnavailable(
            f"no OpenAPI document in {spec_dir} -- run log-coverage/fetch_specs.sh"
        )

    ops = []
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        management = "management" in f.name
        api = "management" if management else "catalog"
        base = "/api/management/v1" if management else "/api/catalog"
        for template, item in (doc.get("paths") or {}).items():
            for method, spec in (item or {}).items():
                if method not in HTTP_METHODS:
                    continue
                declared = sorted(str(c) for c in ((spec or {}).get("responses") or {}))
                params = [
                    seg[1:-1]
                    for seg in template.split("/")
                    if seg.startswith("{") and seg.endswith("}")
                ]
                ops.append(
                    Operation(
                        op_id=(spec or {}).get("operationId") or f"{method}:{template}",
                        method=method,
                        template=template,
                        api=api,
                        base=base,
                        declared=declared,
                        params=params,
                        has_body=bool((spec or {}).get("requestBody")),
                        source=f.name,
                    )
                )
    return sorted(ops, key=lambda o: (o.api, o.template, o.method))


# ----------------------------------------------------------------------
# binding a template to the fixture
# ----------------------------------------------------------------------
def bind_path(op, binding, break_param=None):
    """Substitute the fixture's names into the template.

    `break_param` replaces ONE parameter with `MISSING` -- by default the last,
    because breaking an earlier one tests the wrong endpoint: a bad catalog on
    `/catalogs/{c}/catalog-roles/{cr}` 404s on the catalog, and the role
    endpoint is never reached.

    Raises rather than leaving a `{param}` in the URL: a literal brace in a
    request path is a 404 that looks like a finding.
    """
    out = op.full_template
    unknown = [p for p in op.params if p not in binding and p not in CATALOG_PARAMS]
    if unknown:
        raise KeyError(f"{op.op_id}: no fixture value for {unknown}")
    target = break_param
    if target is True:
        target = op.params[-1] if op.params else None
    for p in op.params:
        value = binding["catalog"] if p in CATALOG_PARAMS else binding[p]
        if target is not None and p == target:
            value = MISSING
        out = out.replace("{" + p + "}", str(value))
    if "{" in out or "}" in out:
        raise KeyError(f"{op.op_id}: unsubstituted parameter in {out}")
    return out


# ----------------------------------------------------------------------
# payloads -- one per operation that carries a body
# ----------------------------------------------------------------------
def _schema():
    return {
        "type": "struct",
        "schema-id": 0,
        "fields": [
            {"id": 1, "name": "id", "required": True, "type": "long"},
            {"id": 2, "name": "val", "required": False, "type": "string"},
        ],
    }


def _view_version(b):
    return {
        "version-id": 1,
        "timestamp-ms": 0,
        "schema-id": 0,
        "summary": {"engine-name": "api-status-matrix"},
        "default-namespace": [b["namespace"]],
        "representations": [{"type": "sql", "sql": "SELECT 1", "dialect": "spark"}],
    }


#: Keyed by operationId. Every operation whose spec declares a requestBody must
#: appear here -- `test_every_body_carrying_operation_has_a_payload` fails
#: otherwise, so a new endpoint in a re-vendored spec cannot be driven with an
#: empty body and reported as covered.
PAYLOADS = {
    # -- management ---------------------------------------------------
    "createCatalog": lambda b: {
        "catalog": {
            "type": "INTERNAL",
            "name": b["new_catalog"],
            "properties": {"default-base-location": b["base_location"]},
            "storageConfigInfo": {
                "storageType": "S3",
                "allowedLocations": [b["base_location"]],
                "endpoint": b["s3_endpoint"],
                "endpointInternal": b["s3_endpoint_internal"],
                "pathStyleAccess": True,
            },
        }
    },
    "updateCatalog": lambda b: {
        "currentEntityVersion": b["entity_version"],
        "properties": {"matrix.run": b["run"]},
    },
    "createCatalogRole": lambda b: {"catalogRole": {"name": b["new_catalog_role"]}},
    "updateCatalogRole": lambda b: {
        "currentEntityVersion": b["entity_version"],
        "properties": {"matrix.run": b["run"]},
    },
    "addGrantToCatalogRole": lambda b: {
        "grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"}
    },
    "revokeGrantFromCatalogRole": lambda b: {
        "grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"}
    },
    "createPrincipalRole": lambda b: {
        "principalRole": {"name": b["new_principal_role"]}
    },
    "updatePrincipalRole": lambda b: {
        "currentEntityVersion": b["entity_version"],
        "properties": {"matrix.run": b["run"]},
    },
    "assignCatalogRoleToPrincipalRole": lambda b: {
        "catalogRole": {"name": b["catalogRoleName"]}
    },
    "createPrincipal": lambda b: {"principal": {"name": b["new_principal"]}},
    "updatePrincipal": lambda b: {
        "currentEntityVersion": b["entity_version"],
        "properties": {"matrix.run": b["run"]},
    },
    "assignPrincipalRole": lambda b: {
        "principalRole": {"name": b["principalRoleName"]}
    },
    "resetCredentials": lambda b: {"principalName": b["principalName"]},
    # -- catalog ------------------------------------------------------
    "getToken": lambda b: {
        "grant_type": "client_credentials",
        "client_id": b["client_id"],
        "client_secret": b["client_secret"],
        "scope": "PRINCIPAL_ROLE:ALL",
    },
    "createNamespace": lambda b: {
        "namespace": [b["new_namespace"]],
        "properties": {"matrix.run": b["run"]},
    },
    "updateProperties": lambda b: {"removals": [], "updates": {"matrix.run": b["run"]}},
    "registerTable": lambda b: {
        "name": b["new_table"],
        "metadata-location": b["metadata_location"],
    },
    "createTable": lambda b: {
        "name": b["new_table"],
        "schema": _schema(),
        "properties": {"matrix.run": b["run"]},
    },
    "updateTable": lambda b: {
        "requirements": [],
        "updates": [{"action": "set-properties", "updates": {"matrix.run": b["run"]}}],
    },
    "reportMetrics": lambda b: {
        "report-type": "scan",
        "table-name": b["table"],
        "snapshot-id": 1,
        "filter": {"type": "true"},
        "schema-id": 0,
        "projected-field-ids": [1],
        "projected-field-names": ["id"],
        "metrics": {},
    },
    "planTableScan": lambda b: {"select": ["id"]},
    "fetchScanTasks": lambda b: {"plan-task": b.get("plan_task", "no-such-plan-task")},
    "createView": lambda b: {
        "name": b["new_view"],
        "schema": _schema(),
        "view-version": _view_version(b),
        "properties": {"matrix.run": b["run"]},
    },
    "replaceView": lambda b: {
        "requirements": [],
        "updates": [{"action": "set-properties", "updates": {"matrix.run": b["run"]}}],
    },
    "renameTable": lambda b: {
        "source": {"namespace": [b["namespace"]], "name": b["table"]},
        "destination": {"namespace": [b["namespace"]], "name": b["renamed_table"]},
    },
    "renameView": lambda b: {
        "source": {"namespace": [b["namespace"]], "name": b["view"]},
        "destination": {"namespace": [b["namespace"]], "name": b["renamed_view"]},
    },
    "commitTransaction": lambda b: {
        "table-changes": [
            {
                "identifier": {"namespace": [b["namespace"]], "name": b["table"]},
                "requirements": [],
                "updates": [
                    {"action": "set-properties", "updates": {"matrix.run": b["run"]}}
                ],
            }
        ]
    },
}

#: The token endpoint is form-encoded, not JSON. Sending it as JSON returns a
#: 400 that looks like a malformed-body finding and is a harness bug.
FORM_ENCODED = frozenset({"getToken"})

#: A body that is syntactically fine and semantically incomplete. Not `{}`:
#: several Polaris endpoints accept an empty object and answer 2xx, which would
#: make the 400 cell a miss for a reason that has nothing to do with validation.
MALFORMED_BODY = {"matrix": "deliberately-missing-required-fields"}


def payload_for(op, binding):
    """The body for `op`, or None if it carries none.

    KeyError -- loudly -- for a body-carrying operation with no entry, rather
    than an empty dict. An endpoint driven with a body it did not ask for
    answers 400 and would be recorded as covered at 400.
    """
    if not op.has_body:
        return None
    if op.op_id not in PAYLOADS:
        raise KeyError(
            f"{op.op_id} carries a requestBody and has no PAYLOADS entry. Add "
            "one; do not drive it with an empty body."
        )
    return copy.deepcopy(PAYLOADS[op.op_id](binding))


# ----------------------------------------------------------------------
# the status rules
# ----------------------------------------------------------------------
#: (target, driver, applies, phase, note). `applies` is a predicate on the
#: Operation, so the grid is derived from the spec rather than typed out.
def _has_params(op):
    """Any path parameter at all, `{prefix}` included.

    Breaking `{prefix}` is a real 404 -- a request against a catalog that does
    not exist -- so `GET /v1/{prefix}/namespaces` earns a 404 cell exactly as
    `GET .../tables/{table}` does. The plan first counted 50 here by excluding
    the catalog-only operations; the count is 55, and the five it left out were
    real coverage.
    """
    return bool(op.params)


def _declares(op, code):
    return str(code) in op.declared


RULES = (
    (
        2,
        "happy",
        lambda op: True,
        "B",
        "the operation's own success code -- 200 / 201 / 204, adjudicated against "
        "what the spec declares",
    ),
    (
        401,
        "unauthenticated",
        lambda op: True,
        "C",
        "the same request with a garbage bearer token; for getToken, a real "
        "client id and the wrong secret",
    ),
    (
        403,
        "denied",
        lambda op: op.op_id != "getToken",
        "C",
        "issued by a principal with a role and no grants",
    ),
    (
        404,
        "missing",
        lambda op: _has_params(op),
        "C",
        "the LAST path parameter replaced -- breaking an earlier one 404s on a "
        "different endpoint",
    ),
    (
        409,
        "conflict",
        lambda op: _declares(op, 409),
        "D",
        "create-twice, or a stale currentEntityVersion on the management PUTs",
    ),
    (
        400,
        "malformed",
        lambda op: op.has_body or op.op_id == "getConfig",
        "D",
        "a body missing its required fields; getConfig with no warehouse",
    ),
)


def cells(ops, include_extras=True):
    """The grid. One cell per (operation, reachable status).

    Deterministic in operation order so two runs are diffable, and unique on
    (op_id, target) so nothing is driven twice and counted twice.
    """
    out, seen = [], set()
    for op in ops:
        for target, driver, applies, phase, note in RULES:
            if not applies(op):
                continue
            key = (op.op_id, target)
            if key in seen:
                continue
            seen.add(key)
            out.append(Cell(op, target, driver, phase, note))
    return out


def success_codes(op):
    """The 2xx codes this operation declares. The `happy` cell is adjudicated
    against the set, not against a guessed 200: `createCatalog` answers 201,
    `dropNamespace` 204, and a matrix that expected 200 would call both a miss."""
    return tuple(int(c) for c in op.declared if c.startswith("2"))


# ----------------------------------------------------------------------
# adjudication
# ----------------------------------------------------------------------
COVERED, MISSED, ERROR = "covered", "missed", "error"


def adjudicate(cell, status, error=None):
    """What a driven cell proved.

    A cell targeting 404 that returns 403 is MISSED with `actual=403`. It does
    NOT become coverage of 403 -- the 403 cell for that operation is driven
    separately, by an identity that makes the 403 mean something, and letting an
    accident stand in for it is how a coverage figure stops being a measurement.
    """
    if error is not None or status is None:
        return {"verdict": ERROR, "actual": status, "why": str(error or "no status")}
    if cell.target == 2:
        want = success_codes(cell.op) or (200, 201, 204)
        ok = status in want
        return {
            "verdict": COVERED if ok else MISSED,
            "actual": status,
            "why": "" if ok else f"expected one of {want}",
        }
    ok = status == cell.target
    return {
        "verdict": COVERED if ok else MISSED,
        "actual": status,
        "why": "" if ok else f"expected {cell.target}",
    }


def coverage_by_operation(ops, results):
    """Per operation: which targets are covered, which missed, what is absent.

    `results` maps (op_id, target) -> the dict `adjudicate` returned.
    """
    rows = []
    for op in ops:
        planned = [c for c in cells([op])]
        got = {c.target: results.get((op.op_id, c.target)) for c in planned}
        rows.append(
            {
                "op_id": op.op_id,
                "method": op.method,
                "path": op.full_template,
                "api": op.api,
                "planned": [c.target for c in planned],
                "covered": sorted(
                    t for t, r in got.items() if r and r["verdict"] == COVERED
                ),
                "missed": sorted(
                    t for t, r in got.items() if r and r["verdict"] == MISSED
                ),
                "not_driven": sorted(t for t, r in got.items() if r is None),
                "declared": op.declared,
            }
        )
    return rows


def ledger():
    """The not-reachable ledger, as rows -- settled entries and open probes.

    Rendered in the notebook next to the matrix so a reader sees what was NOT
    driven and why, in the same table as what was.
    """
    return [
        {"status": k, "why": v[0], "state": v[1]}
        for k, v in sorted(NOT_REACHABLE.items(), key=lambda kv: str(kv[0]))
    ]


# ----------------------------------------------------------------------
# the executor
# ----------------------------------------------------------------------
#: A syntactically valid bearer token that no realm will accept. Not an empty
#: Authorization header: an absent header and a bad one are different code
#: paths in Quarkus, and only the second is what a client with a stale token
#: actually looks like.
GARBAGE_TOKEN = "not-a-real-token-401-cell"  # noqa: S105 - deliberately invalid

#: A `currentEntityVersion` that cannot be current. 0 risks being read as
#: unset; 999 is unambiguously stale and was measured returning 409 on this
#: build (error-cases/18, and again in the 500 ladder on 2026-09-07).
STALE_ENTITY_VERSION = 999

#: Which identity issues which cell. Management endpoints refuse the run
#: principal, so a happy management cell driven as the run principal would be a
#: 403 recorded as a missed 2xx -- a harness gap wearing a finding's clothes.
ADMIN, RUNNER, DENIED, NOBODY = "admin", "runner", "denied", "nobody"


def identity_for(cell):
    if cell.target == 401:
        return NOBODY
    if cell.target == 403:
        return DENIED
    return ADMIN if cell.op.api == "management" else RUNNER


def request_for(cell, binding, tokens, request_id, realm):
    """Everything needed to issue one cell, and nothing that needs a network.

    Pure, so every transform in the status axis is unit-testable: the garbage
    token, the broken path segment, the stale entity version, the malformed
    body, the dropped query parameter.
    """
    op = cell.op
    who = identity_for(cell)
    token = GARBAGE_TOKEN if who is NOBODY else tokens[who]

    path = bind_path(op, binding, break_param=True if cell.target == 404 else None)

    body = payload_for(op, binding)
    if cell.target == 400:
        body = dict(MALFORMED_BODY) if op.has_body else body
    elif cell.target == 409 and body and "currentEntityVersion" in body:
        body["currentEntityVersion"] = STALE_ENTITY_VERSION

    params = None
    if op.op_id == "getConfig":
        # WITHOUT a warehouse this build answers 400, so the bare call tests
        # rule 3 and not the counted-2xx path. Run 1 recorded three 400s under
        # a label promising a successful GET.
        params = None if cell.target == 400 else {"warehouse": binding["catalog"]}

    headers = {"Polaris-Realm": realm, "Polaris-Request-Id": request_id}
    if op.op_id == "getToken":
        # Form-encoded, and it carries its credentials in the body rather than
        # in an Authorization header.
        data = dict(body or {})
        if cell.target == 401:
            data["client_secret"] = "not-the-secret"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return {
            "method": op.method,
            "path": path,
            "params": params,
            "headers": headers,
            "json": None,
            "data": data,
            "identity": who,
        }

    headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    return {
        "method": op.method,
        "path": path,
        "params": params,
        "headers": headers,
        "json": body,
        "data": None,
        "identity": who,
    }


def execute(cell, req, base_url, session=None, timeout=20, seq=0):
    """Issue one cell. Returns a row in `log_coverage.call_once`'s shape.

    Same keys as the v1 harness's rows on purpose: `correlation_stats`,
    `reconcile_volume` and the matrix printer already read that shape, and a
    second row shape would mean a second set of statistics that agree with
    nothing.
    """
    import time as _t

    import requests as _rq

    session = session or _rq.Session()
    row = {
        "seq": seq,
        "label": cell.label,
        "method": cell.op.method,
        "path": req["path"],
        "actual_path": None,
        "issued_at": _t.time(),
        "principal": req["identity"],
        "api": cell.op.api,
        "request_id": req["headers"].get("Polaris-Request-Id"),
        "status": None,
        "elapsed_ms": None,
        "error": None,
        "echoed_request_id": None,
        # -- what makes it a matrix row rather than a call row
        "op_id": cell.op.op_id,
        "target": cell.target,
        "driver": cell.driver,
        "phase": cell.phase,
        "verdict": None,
        "why": "",
    }
    started = _t.perf_counter()
    try:
        resp = session.request(
            cell.op.method,
            f"{base_url.rstrip('/')}{req['path']}",
            params=req["params"],
            headers=req["headers"],
            json=req["json"],
            data=req["data"],
            timeout=timeout,
        )
        row["status"] = resp.status_code
        row["actual_path"] = getattr(getattr(resp, "request", None), "path_url", None)
        row["echoed_request_id"] = resp.headers.get("Polaris-Request-Id")
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["elapsed_ms"] = round((_t.perf_counter() - started) * 1000, 1)

    verdict = adjudicate(cell, row["status"], row["error"])
    row["verdict"], row["why"] = verdict["verdict"], verdict["why"]
    return row


def drive(
    cells_,
    binding,
    tokens,
    base_url,
    realm,
    run,
    seq_from=2000,
    session=None,
    on_row=None,
):
    """Issue a phase's cells in order, tagged, and return their rows.

    Deliberately serial. The report attributes a request to a window by the
    time it was served, and concurrent calls straddling a boundary would make
    the per-window margins unprovable rather than wrong -- which is worse,
    because it looks like a pass.
    """
    rows, seq = [], seq_from
    for cell in cells_:
        seq += 1
        rid = request_id(run, seq, cell.label)
        req = request_for(cell, binding, tokens, rid, realm)
        row = execute(cell, req, base_url, session=session, seq=seq)
        rows.append(row)
        if on_row:
            on_row(row)
    return rows


_SLUG_OK = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_")


def request_id(run, seq, label):
    """`nb-<run>-<seq>-<label>`, in `log_coverage.request_id`'s exact format.

    Reimplemented rather than imported so this module has no dependency on
    `log_coverage` -- but the FORMAT is not free to differ: the v1 pull filters
    on `"mdc.requestId":"nb-<run>-"*` and a second format would go unfound.
    """
    slug = "".join(c if c in _SLUG_OK else "-" for c in label).strip("-")
    return f"nb-{run}-{seq:03d}-{slug}"
