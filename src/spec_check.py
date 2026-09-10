"""Are the 286 requests VALID? Ask the spec, through Prism.

`make_traffic.drive(dry_run=True)` answers a weaker question -- does every cell
in the grid produce a request at all -- and it answers it by nothing raising.
That is a floor, not a check. This module asks the real one: **does each
request satisfy the OpenAPI document the run already uses as its denominator?**

Stoplight Prism (`prism mock --errors`) serves the vendored specs and rejects a
request that violates one. Nothing here needs Polaris, MinIO, a fixture or a
token, and nothing here mutates anything.

## The assertion is TWO-SIDED, and that is the point

The grid contains deliberately broken cells. A one-sided *"every request must
validate"* check would flag them and read as a harness bug, so the expectation
is per cell:

- a cell targeting **400 on an operation with a body** substitutes
  `MALFORMED_BODY` -- it MUST be rejected. A spec-valid "malformed" body is a
  cell that is not testing what it claims to.
- **every other cell** -- 2xx, 401, 403, 404, 409 -- is a well-formed request
  whose outcome is about auth or state, not shape. It MUST be accepted.

A `getConfig` 400 cell is the exception that proves it: `warehouse` is
`required: false` in the Iceberg document, so the bare call is SPEC-VALID and
Prism accepts it -- while this build answers 400. That is a divergence between
Polaris and its own spec, and it is reported as a **build finding**, not as a
failure of this check.

## Two controls, because a check that cannot fail is worse than none

`prism mock` WITHOUT `--errors` logs violations and returns 200 anyway. Run
against that, this whole module reports every request valid and passes without
having looked -- the same shape as Gate 5's term filter matching nothing, and
as the two gates that reported PASS on zero rows in run 1789007773. So:

- the **negative control** sends a request known to be invalid and requires a
  rejection. No rejection means Prism is not enforcing, and the run is VOID.
- the **positive control** sends a request known to be valid and requires
  acceptance. No acceptance means the mount is wrong or the spec did not load,
  and everything after it would be a false rejection. Also VOID.

VOID is never PASS. It is not FAIL either -- nothing was measured.

## Mounting, which is derived rather than assumed

Prism serves each spec's paths under the path in that spec's own `servers`
entry. The two documents differ, and the difference is invisible until every
request 404s:

    management   servers[0] = {scheme}://{host}/api/management/v1
                 path `/catalogs`      -> mounted at /api/management/v1/catalogs
    catalog      servers[0] = {scheme}://{host}/{basePath}, basePath default ""
                 path `/v1/config`     -> mounted at /v1/config

`Operation.base` is a different thing -- POLARIS's deployment prefix, which is
`/api/catalog` for the Iceberg document and is not in the spec at all. So a
request built for Polaris has to have `op.base` stripped and the spec's own
mount prepended. `prism_mounts` reads that from the `servers` block rather than
hardcoding the two cases, so a spec that changes its server path corrects this
instead of silently breaking it.
"""

import json
import pathlib
from urllib.parse import urlsplit

#: Verdicts for one request.
ACCEPTED = "accepted"
REJECTED = "rejected"
NOT_ROUTED = "not_routed"
#: Prism could not generate a spec-valid RESPONSE from the document. That is a
#: statement about the document, and never about the request that provoked it.
#: Measured on the first real run: 36 cells came back this way, with the SAME
#: violation for targets 2, 401, 403, 404 and 409 of the same operation --
#: identical regardless of what was sent, which is what proves it cannot be
#: about the request. Counted as `REJECTED` they read as 36 invalid requests.
SPEC_EXAMPLE = "spec_example"
#: Prism refused on a SECURITY SCHEME rather than on the request's shape.
#: Measured on the second real run: `getToken` came back 401 with no
#: violations. It declares no operation-level `security`, so it inherits the
#: Iceberg document's global `security: [OAuth2, BearerAuth]` -- and Prism then
#: demands a bearer token in order to OBTAIN a bearer token. The request is
#: correct: an OAuth token endpoint carries its credentials in the form body,
#: not in an Authorization header. So this says nothing about the request, and
#: counting it as one left three unreadable `error` rows.
AUTH_REQUIRED = "auth_required"
ERROR = "error"

#: Verdicts that are NOT a judgement on the request that provoked them. Each
#: is about the DOCUMENT: one about the response it describes, one about the
#: security it declares.
NOT_ABOUT_THE_REQUEST = frozenset({SPEC_EXAMPLE, AUTH_REQUIRED})

#: Outcomes for a whole pass.
PASS = "PASS"
FAIL = "FAIL"
VOID = "VOID"

DEFAULT_TIMEOUT = 15


class PrismUnavailable(RuntimeError):
    """Prism is not answering. Not a finding -- nothing was measured."""


def candidate_mounts(spec_dir):
    """`{api: [mount, ...]}` -- the places Prism might be serving this document.

    **This used to be `prism_mounts`, and it returned ONE answer derived from
    the document's `servers` entry. It was wrong, and it was wrong in a way
    that looked principled.** Measured on the first real run: Prism ignores a
    templated server base path and mounts the document's paths at the ROOT. So
    the derived `""` was right for the Iceberg document by luck and the derived
    `/api/management/v1` was wrong for the management one -- and **all 144
    management cells came back 404** while the catalog half worked.

    The lesson is the one this repo keeps re-learning: a fact about a running
    thing is measured, not derived. So the mount is now a LIST of candidates,
    and `resolve_mounts` probes the live server to find out which one answers.
    The empty mount is first because that is what Prism was measured doing.
    """
    import yaml

    d = pathlib.Path(spec_dir)
    files = sorted(d.glob("*.yml")) + sorted(d.glob("*.yaml")) if d.is_dir() else []
    if not files:
        raise PrismUnavailable(f"no OpenAPI document in {spec_dir}")
    mounts = {}
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        api = "management" if "management" in f.name else "catalog"
        servers = doc.get("servers") or []
        declared = _server_path(servers[0]) if servers else ""
        # Order matters only as a first guess; `resolve_mounts` decides.
        mounts[api] = [""] + ([declared] if declared else [])
    return mounts


def _server_path(server):
    url = str((server or {}).get("url") or "")
    for name, var in ((server or {}).get("variables") or {}).items():
        url = url.replace("{" + name + "}", str((var or {}).get("default", "")))
    path = urlsplit(url).path if "//" in url else url
    return "/" + path.strip("/") if path.strip("/") else ""


def resolve_mounts(
    spec_dir, prism, binding, tokens, realm, session, timeout=DEFAULT_TIMEOUT
):
    """Ask the running Prism where it is actually serving each document.

    For each API, one known-good request is sent at each candidate mount and
    the first that does not 404 wins. Returns
    `{api: {"mount", "resolved", "tried", "op_id"}}`.

    An API where NOTHING routes is left `resolved: False` rather than falling
    back to a guess. Every one of its cells would 404, and reporting 144
    invalid requests when the answer is "Prism is not serving that document
    here" is precisely the mistake this function exists to prevent.
    """
    import api_status_matrix as mx

    grid = mx.cells(mx.load_spec(spec_dir))
    candidates = candidate_mounts(spec_dir)
    out = {}
    for api in sorted({c.op.api for c in grid}):
        # A GET with no path parameters and no body: the least that can go
        # wrong other than the route itself.
        probe = next(
            (
                c
                for c in grid
                if c.op.api == api
                and c.target == 2
                and not c.op.params
                and c.op.method == "get"
            ),
            None,
        ) or next(c for c in grid if c.op.api == api and c.target == 2)
        req = mx.request_for(probe, binding, tokens, f"mount-probe-{api}", realm)
        tried, found = [], None
        for mount in candidates.get(api, [""]):
            url = prism[api].rstrip("/") + _join(mount, probe.op, req["path"])
            try:
                status, body = _send(session, url, req, timeout)
            except Exception as exc:  # noqa: BLE001
                raise PrismUnavailable(
                    f"probing the {api} mount could not reach Prism at {url}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            tried.append({"mount": mount, "url": url, "status": status})
            if classify(status, body) != NOT_ROUTED:
                found = mount
                break
        out[api] = {
            "mount": found if found is not None else "",
            "resolved": found is not None,
            "tried": tried,
            "op_id": probe.op.op_id,
        }
    return out


def _join(mount, op, request_path):
    """The Polaris request path, re-aimed at `mount`.

    Raises rather than guessing: a path that does not start with the base the
    spec loader recorded means the two disagree about the deployment prefix,
    and quietly sending it anywhere would produce a 404 that reads like a
    missing route.
    """
    base = op.base or ""
    if base and not request_path.startswith(base):
        raise ValueError(
            f"{op.op_id}: path {request_path!r} does not start with its "
            f"recorded base {base!r} -- the spec loader and the request "
            "builder disagree, and re-aiming it would 404 as a missing route"
        )
    return (mount + request_path[len(base) :]) or "/"


def prism_path(op, request_path, mounts):
    """The Polaris request path, re-aimed at where Prism serves that spec.

    Raises rather than guessing: a path that does not start with the base the
    spec loader recorded means the two disagree about the deployment prefix,
    and quietly sending it anywhere would produce a 404 that reads like a
    missing route.
    """
    mount = mounts.get(op.api, "")
    if isinstance(mount, dict):
        mount = mount.get("mount", "")
    return _join(mount, op, request_path)


def expectation(cell):
    """`REJECTED` for the cells that are deliberately malformed, else `ACCEPTED`.

    ONLY the body substitution makes a request spec-invalid. `getConfig`'s 400
    cell drops an OPTIONAL query parameter, so it stays spec-valid; that this
    build answers 400 to it is a fact about Polaris, reported separately.
    """
    if cell.target == 400 and cell.op.has_body:
        return REJECTED
    return ACCEPTED


def classify(status, body):
    """What Prism said about one request.

    THREE splits, each of which was a wrong answer before it was made:

    `NOT_ROUTED` apart from `REJECTED`. A 404 means the mount is wrong or the
    document has no such path -- a fault in THIS module -- while a 422 with
    violations is about the request. Folded together, a mounting mistake reads
    as 286 invalid requests, and on the first real run that would have been
    144 of them.

    `SPEC_EXAMPLE` apart from `REJECTED`. A violation whose location is in the
    RESPONSE is Prism failing to build a spec-valid example out of the
    document. The request was fine; there is nothing to fix in it.

    A violation list carrying BOTH is a rejection: the request half decides,
    because that is the half this check is asking about.
    """
    if status is None:
        return ERROR
    req_v, resp_v = _split_violations(body)
    if status == 404 and not (req_v or resp_v):
        return NOT_ROUTED
    if req_v:
        return REJECTED
    if resp_v:
        return SPEC_EXAMPLE
    if 200 <= status < 400:
        return ACCEPTED
    # A bare 401 is Prism enforcing a security scheme. It is not a shape
    # verdict, and it is checked BEFORE the 400/422 rejection rule so that a
    # security refusal can never be read as a malformed request.
    if status == 401:
        return AUTH_REQUIRED
    if status in (400, 422):
        return REJECTED
    return ERROR


#: A violation Prism raises about the response it generated, not the request it
#: received. Prism spells the location either as a dotted string beginning
#: `response` or as a list whose first element is `response`; the message text
#: ("Response body property ...") is the fallback for a shape not seen yet.
def _is_response_violation(v):
    if not isinstance(v, dict):
        return False
    where = v.get("location") or v.get("path") or v.get("in") or ""
    if isinstance(where, (list, tuple)):
        where = ".".join(str(w) for w in where)
    if str(where).lower().startswith("response"):
        return True
    return str(v.get("message") or "").lower().startswith("response ")


def _split_violations(body):
    """`(about the request, about the response)`."""
    req, resp = [], []
    for v in _violations(body):
        (resp if _is_response_violation(v) else req).append(v)
    return req, resp


def _violations(body):
    """Prism's violation list, under whichever key this version uses."""
    if not isinstance(body, dict):
        return []
    for key in ("validation", "violations", "errors"):
        found = body.get(key)
        if isinstance(found, list) and found:
            return found
    return []


def violation_summary(body, limit=3):
    out = []
    for v in _violations(body)[:limit]:
        if isinstance(v, dict):
            where = v.get("location") or v.get("path") or v.get("in") or ""
            if isinstance(where, list):
                where = ".".join(str(w) for w in where)
            out.append(f"{where}: {v.get('message') or v.get('code') or v}".strip(": "))
        else:
            out.append(str(v))
    return "; ".join(out)


# ----------------------------------------------------------------------
# the pass
# ----------------------------------------------------------------------
def _send(session, url, req, timeout):
    """One request at Prism. Returns `(status, body)`; never raises for HTTP."""
    resp = session.request(
        req["method"],
        url,
        params=req["params"],
        headers=req["headers"],
        json=req["json"],
        data=req["data"],
        timeout=timeout,
    )
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001 - a non-JSON body is not an error here
        body = {"_text": (resp.text or "")[:400]}
    return resp.status_code, body


def controls(
    spec_dir, prism, binding, tokens, realm, session, mounts, timeout=DEFAULT_TIMEOUT
):
    """Prove Prism is enforcing, FOR EVERY API, before believing anything.

    **One control per API, and that is not tidiness.** The first version took
    one negative and one positive from the whole grid; the grid's sort order
    put both on CATALOG operations, so on the first real run both controls
    reported green while **all 144 management cells 404'd**. A control that
    cannot fail for the thing it vouches for is the failure mode this module
    exists to avoid, and it was inside the module.

    Returns `{api: {"negative": ..., "positive": ...}, "ok": bool, "why": str}`.
    """
    import api_status_matrix as mx

    grid = mx.cells(mx.load_spec(spec_dir))
    out, problems = {}, []

    for api in sorted({c.op.api for c in grid}):
        rows = [c for c in grid if c.op.api == api]
        # NOT `getToken`: it is the only form-encoded operation, the grid's
        # sort order reaches it first, and whether Prism validates a form body
        # against a schema is unsettled -- so it must not vouch for anything.
        neg = next(
            (
                c
                for c in rows
                if c.target == 400
                and c.op.has_body
                and c.op.op_id not in mx.FORM_ENCODED
            ),
            None,
        )
        pos = next(
            (c for c in rows if c.target == 2 and not c.op.params),
            None,
        ) or next((c for c in rows if c.target == 2), None)

        api_out = {}
        for name, cell, want in (
            ("negative", neg, REJECTED),
            ("positive", pos, ACCEPTED),
        ):
            if cell is None:
                api_out[name] = None
                continue
            req = mx.request_for(cell, binding, tokens, f"speccheck-{name}", realm)
            url = prism[api].rstrip("/") + prism_path(cell.op, req["path"], mounts)
            try:
                status, body = _send(session, url, req, timeout)
            except Exception as exc:  # noqa: BLE001
                raise PrismUnavailable(
                    f"the {api} {name} control could not reach Prism at {url}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            got = classify(status, body)
            # THE POSITIVE CONTROL ASKS ONE QUESTION: did a request known to be
            # valid GET THROUGH? A `SPEC_EXAMPLE` means it did -- Prism accepted
            # it and then failed to build its own example response, which is
            # about the document. Requiring a literal ACCEPTED here VOIDed the
            # second real run over `listCatalogs`, whose response the document
            # cannot describe, while the check was working perfectly.
            #
            # The NEGATIVE control stays strict: a request Prism rejects never
            # reaches response generation, so it can never legitimately come
            # back as SPEC_EXAMPLE, and loosening it would let a non-enforcing
            # Prism through -- which is the one thing the controls exist for.
            ok = got in (ACCEPTED, SPEC_EXAMPLE) if name == "positive" else got == want
            api_out[name] = {
                "api": api,
                "op_id": cell.op.op_id,
                "url": url,
                "status": status,
                "verdict": got,
                "expected": want,
                "ok": ok,
                "detail": violation_summary(body),
            }
        out[api] = api_out

        mount = mounts.get(api) or {}
        if isinstance(mount, dict) and not mount.get("resolved", True):
            problems.append(
                f"{api}: NOT ROUTED at any candidate mount "
                f"({[t['mount'] for t in mount.get('tried', [])]}). Prism is not "
                f"serving that document at {prism.get(api)}, so every {api} "
                "cell would 404 and none of it would be about the requests."
            )
            continue
        for name in ("negative", "positive"):
            c = api_out.get(name)
            if c is None:
                problems.append(
                    f"{api}: the grid has no cell to build a {name} control from"
                )
            elif c["verdict"] == NOT_ROUTED:
                problems.append(
                    f"{api}: the {name} control was NOT ROUTED -- Prism answered "
                    f"404 to a path the document declares, at mount "
                    f"{_mount_of(mounts, api)!r}."
                )
            elif not c["ok"] and name == "negative":
                problems.append(
                    f"{api}: the negative control was NOT rejected (got "
                    f"{c['verdict']}). `prism mock` without `--errors` logs "
                    "violations and answers 200 anyway, and every request would "
                    "then read as valid. Restart it with --errors."
                )
            elif not c["ok"]:
                problems.append(
                    f"{api}: the positive control was not accepted (got "
                    f"{c['verdict']}) -- a request known to be valid did not get "
                    "through, so every rejection would be this fault."
                )

    out["ok"] = not problems
    out["why"] = " | ".join(problems)
    return out


def _mount_of(mounts, api):
    m = mounts.get(api, "")
    return m.get("mount", "") if isinstance(m, dict) else m


def check_requests(
    spec_dir,
    prism,
    *,
    config=None,
    run="speccheck",
    session=None,
    timeout=DEFAULT_TIMEOUT,
    on_row=None,
):
    """Validate every cell's request against the spec, through Prism.

    Args:
        spec_dir: the vendored OpenAPI documents -- the same denominator the
            run uses, so this cannot drift from what the matrix counts.
        prism: `{"management": url, "catalog": url}`. Two documents, two
            mounts, two servers.
        config: optional, only to shape the binding's names the way a real run
            would. Nothing in it is contacted.

    Returns a report dict; `verdict` is PASS, FAIL or VOID. **VOID is not a
    pass** -- it means the controls said nothing here was measured.
    """
    import api_status_matrix as mx
    import make_traffic as mt

    session = session or _session()
    config = dict(config or {})
    for key in mt._REQUIRED_CONFIG:
        config.setdefault(key, "spec-check-not-contacted")
    config.setdefault("realm", "POLARIS")
    realm = config["realm"]

    _fx, binding = mt.dry_binding(config, run)
    tokens = {
        mx.ADMIN: mt.DRY_TOKEN,
        mx.RUNNER: mt.DRY_TOKEN,
        mx.DENIED: mt.DRY_TOKEN,
    }

    # WHERE Prism is serving each document is measured, not derived. The
    # derived answer was wrong for the management spec and cost 144 cells.
    mounts = resolve_mounts(spec_dir, prism, binding, tokens, realm, session, timeout)
    ctl = controls(spec_dir, prism, binding, tokens, realm, session, mounts, timeout)
    grid = mx.cells(mx.load_spec(spec_dir))

    rows = []
    for i, cell in enumerate(grid):
        req = mx.request_for(cell, binding, tokens, f"speccheck-{run}-{i}", realm)
        want = expectation(cell)
        try:
            url = prism[cell.op.api].rstrip("/") + prism_path(
                cell.op, req["path"], mounts
            )
        except (ValueError, KeyError) as exc:
            rows.append(_row(cell, want, ERROR, None, str(exc), None))
            continue
        try:
            status, body = _send(session, url, req, timeout)
        except Exception as exc:  # noqa: BLE001
            rows.append(
                _row(cell, want, ERROR, None, f"{type(exc).__name__}: {exc}", url)
            )
            continue
        got = classify(status, body)
        row = _row(cell, want, got, status, violation_summary(body), url)
        rows.append(row)
        if on_row:
            on_row(row)

    # A SPEC_EXAMPLE row is not a verdict on the request, so it is not an
    # unexpected cell. It is a finding about the document, reported apart.
    unexpected = [
        r for r in rows if not r["ok"] and r["verdict"] not in NOT_ABOUT_THE_REQUEST
    ]
    not_routed = [r for r in rows if r["verdict"] == NOT_ROUTED]
    spec_examples = [r for r in rows if r["verdict"] == SPEC_EXAMPLE]
    auth_required = [r for r in rows if r["verdict"] == AUTH_REQUIRED]
    if not ctl["ok"]:
        verdict = VOID
    elif unexpected:
        verdict = FAIL
    else:
        verdict = PASS

    return {
        "verdict": verdict,
        "why": ctl["why"],
        "controls": ctl,
        "spec_dir": str(spec_dir),
        "mounts": mounts,
        "prism": dict(prism),
        "cells": len(rows),
        "accepted": sum(1 for r in rows if r["verdict"] == ACCEPTED),
        "rejected": sum(1 for r in rows if r["verdict"] == REJECTED),
        "not_routed": len(not_routed),
        "spec_examples": len(spec_examples),
        "auth_required": len(auth_required),
        "errors": sum(1 for r in rows if r["verdict"] == ERROR),
        "unexpected": unexpected,
        "rows": rows,
        "build_findings": build_findings(rows),
        "spec_findings": spec_findings(spec_examples)
        + auth_findings(auth_required, spec_dir),
        "harness_findings": harness_findings(spec_dir),
    }


def _row(cell, want, got, status, detail, url):
    return {
        "op_id": cell.op.op_id,
        "api": cell.op.api,
        "method": cell.op.method.upper(),
        "target": cell.target,
        "url": url,
        "status": status,
        "expected": want,
        "verdict": got,
        "ok": got == want,
        "detail": detail or "",
    }


def _session():
    import requests

    return requests.Session()


def build_findings(rows):
    """Divergences between Polaris and its own spec, which are NOT this
    check's failures and must not be reported as the pipeline's work.

    `getConfig` is the measured one: `warehouse` is `required: false` in the
    Iceberg document, so Prism accepts the bare call -- and this build answers
    400 to it (measured 2026-08-31, and the reason the 400 cell exists at all).
    A request the spec permits and the server refuses is a fact about the
    server.
    """
    out = []
    for r in rows:
        if (
            r["op_id"] == "getConfig"
            and r["target"] == 400
            and r["verdict"] == ACCEPTED
        ):
            out.append(
                {
                    "about": "polaris",
                    "title": "getConfig without `warehouse` is spec-valid and this "
                    "build answers 400",
                    "measured": "`warehouse` is required: false in the Iceberg "
                    "document; Prism accepts the bare call. The 400 cell in the "
                    "grid records what Polaris does, not what the spec says.",
                }
            )
    return out


def spec_findings(spec_example_rows):
    """Places the DOCUMENT cannot describe its own responses.

    Grouped by the violating property rather than listed per cell: on the
    first real run one property accounted for 23 rows across six operations,
    and 36 rows of the same sentence is not six findings' worth of reading.

    These are neither this check's failures nor Polaris's: Prism built an
    example response from the document and it did not satisfy the document.
    Whoever maintains the spec is the audience.
    """
    by_property = {}
    for r in spec_example_rows:
        prop = (r.get("detail") or "").split(":")[0].strip() or "(unnamed property)"
        entry = by_property.setdefault(prop, {"ops": set(), "cells": 0})
        entry["ops"].add(r["op_id"])
        entry["cells"] += 1
    out = []
    for prop, e in sorted(by_property.items()):
        out.append(
            {
                "about": "spec",
                "title": f"`{prop}` -- Prism cannot generate a spec-valid response",
                "measured": f"{e['cells']} cell(s) across {len(e['ops'])} "
                f"operation(s): {', '.join(sorted(e['ops']))}. The SAME violation "
                "appears for every target of each operation, which is what shows "
                "it is about the document and not about the request.",
                "operations": sorted(e["ops"]),
                "cells": e["cells"],
            }
        )
    return out


def request_schema(doc, op_id):
    """The resolved request-body schema for `op_id`, or None if it has no body.

    One `$ref` hop, which is all these two documents use. A deeper chain would
    return the wrapper, and `required_fields` would then read None and call the
    operation unmalformable -- so if a document ever nests further, this is the
    function to extend rather than the caller to work around.
    """
    comps = (doc.get("components") or {}).get("schemas") or {}
    for _path, item in (doc.get("paths") or {}).items():
        for _m, op in (item or {}).items():
            if not isinstance(op, dict) or op.get("operationId") != op_id:
                continue
            content = (op.get("requestBody") or {}).get("content") or {}
            if not content:
                return None
            sch = list(content.values())[0].get("schema") or {}
            if "$ref" in sch:
                sch = comps.get(sch["$ref"].split("/")[-1], {})
            return sch
    return None


def unmalformable_cells(spec_dir):
    """Operations whose 400 cell CANNOT be provoked by omitting a field.

    **Computed from the documents alone -- no Prism, no cluster.** The grid's
    400 rule is *"a body missing its required fields"*, and where a schema
    declares no `required` there is nothing to miss: `MALFORMED_BODY` is then a
    VALID body, the cell drives a successful call, and it reports a 400 it can
    never have provoked.

    Measured 2026-09-10 against the vendored 1.3.0 documents: **12 of the 27
    malformed-body cells**. Prism's second run surfaced 9 of them; the other
    three were masked behind other verdicts, which is the argument for
    computing this statically instead of waiting for a run to reveal it.
    """
    import api_status_matrix as mx
    import yaml

    d = pathlib.Path(spec_dir)
    docs = {}
    for f in sorted(d.glob("*.yml")) + sorted(d.glob("*.yaml")):
        docs[f.name] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}

    out = []
    for cell in mx.cells(mx.load_spec(spec_dir)):
        if cell.target != 400 or not cell.op.has_body:
            continue
        sch = request_schema(docs.get(cell.op.source) or {}, cell.op.op_id)
        if not (sch or {}).get("required"):
            out.append(
                {
                    "op_id": cell.op.op_id,
                    "api": cell.op.api,
                    "properties": sorted((sch or {}).get("properties") or {}),
                }
            )
    return sorted(out, key=lambda r: (r["api"], r["op_id"]))


def harness_findings(spec_dir):
    """Cells this repo drives that the document says cannot do what they claim.

    Not Polaris's, not the pipeline's, not the document's: **ours.** Kept in
    its own section so it is neither mistaken for a Polaris fact nor sent to
    `local-k8s` as work.
    """
    rows = unmalformable_cells(spec_dir)
    if not rows:
        return []
    return [
        {
            "about": "harness",
            "title": f"{len(rows)} of the grid's 400 cells cannot be provoked by "
            "omitting a required field",
            "measured": "their request schemas declare no `required`, so "
            "`MALFORMED_BODY` is a VALID body: the cell drives a successful call "
            "and reports a 400 it never provoked. "
            + "; ".join(f"{r['api']}/{r['op_id']}" for r in rows),
            "remedy": "either stop emitting a 400 cell where the schema cannot be "
            "violated by omission, or malform by wrong TYPE on a declared "
            "property, which any schema rejects. Both change `api_status_matrix` "
            "and one of them changes the denominator, so it is a decision and "
            "not a patch.",
            "operations": [r["op_id"] for r in rows],
        }
    ]


def auth_findings(auth_rows, spec_dir):
    """Operations Prism refused on a SECURITY scheme rather than on shape.

    `getToken` is the measured one: it declares no operation-level `security`,
    inherits the document's global `security: [OAuth2, BearerAuth]`, and Prism
    therefore demands a bearer token in order to obtain a bearer token. The
    request is right -- an OAuth token endpoint carries credentials in the form
    body -- so this is a fact about the document.
    """
    if not auth_rows:
        return []
    ops = sorted({r["op_id"] for r in auth_rows})
    return [
        {
            "about": "spec",
            "title": f"{', '.join(ops)} -- refused on a security scheme, not on "
            "the request",
            "measured": f"{len(auth_rows)} cell(s) came back 401 with no "
            "violations. These operations declare no `security` of their own and "
            "inherit the document's global requirement, so Prism demands a bearer "
            "token to obtain one. Nothing here is a statement about the request.",
        }
    ]


def render_report(report):
    """Markdown, with the verdict and its reason first."""
    v = report["verdict"]
    lines = [
        f"# Request conformance against the spec -- {v}",
        "",
        f"{report['cells']} cells: {report['accepted']} accepted, "
        f"{report['rejected']} rejected, {report['not_routed']} not routed, "
        f"{report.get('spec_examples', 0)} spec-example, "
        f"{report.get('auth_required', 0)} auth-required, {report['errors']} error.",
        "",
        "**spec-example** and **auth-required** are not verdicts on a request: "
        "the first is Prism failing to build a valid response out of the "
        "document, the second is Prism enforcing a security scheme the document "
        "declares. Neither counts as a failure below.",
        "",
    ]
    if v == VOID:
        lines += [
            "**VOID -- nothing was measured.** " + (report["why"] or ""),
            "",
            "A VOID pass is not a pass. Do not read the counts above as a result.",
            "",
        ]

    lines += [
        "## Where Prism is serving each document",
        "",
        "| api | mount | resolved | probed with | tried |",
        "| --- | --- | --- | --- | --- |",
    ]
    for api, m in sorted((report.get("mounts") or {}).items()):
        if not isinstance(m, dict):
            m = {"mount": m, "resolved": True, "tried": [], "op_id": ""}
        tried = ", ".join(
            f"{t['mount'] or '(root)'}->{t['status']}" for t in m.get("tried", [])
        )
        lines.append(
            f"| {api} | `{m.get('mount') or '(root)'}` | "
            f"{'yes' if m.get('resolved') else 'NO'} | `{m.get('op_id', '')}` | "
            f"{tried} |"
        )

    ctl = report.get("controls") or {}
    lines += [
        "",
        "## Controls -- one pair per api",
        "",
        "| api | control | operation | expected | got | status | ok |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for api, pair in sorted(ctl.items()):
        if not isinstance(pair, dict):
            continue
        for name in ("negative", "positive"):
            c = pair.get(name)
            if isinstance(c, dict):
                lines.append(
                    f"| {api} | {name} | `{c['op_id']}` | {c['expected']} | "
                    f"{c['verdict']} | {c['status']} | "
                    f"{'yes' if c['ok'] else 'NO'} |"
                )

    if report["unexpected"]:
        lines += [
            "",
            "## Cells that did not do what the spec says they should",
            "",
            "| operation | target | expected | got | status | detail |",
            "| --- | ---: | --- | --- | ---: | --- |",
        ]
        for r in report["unexpected"][:40]:
            lines.append(
                f"| `{r['op_id']}` | {r['target']} | {r['expected']} | "
                f"{r['verdict']} | {r['status']} | {r['detail'][:110]} |"
            )

    if report.get("spec_findings"):
        lines += [
            "",
            "## Spec findings -- about the DOCUMENT, not the requests",
            "",
            "Prism built an example response out of the document and it "
            "did not satisfy the document. Nothing here is a statement "
            "about a request, and nothing here is this repo's to fix.",
            "",
        ]
        for f in report["spec_findings"]:
            lines.append(f"- **{f['title']}** -- {f['measured']}")

    if report.get("harness_findings"):
        lines += ["", "## Harness findings -- THIS repo's, and nobody else's", ""]
        for f in report["harness_findings"]:
            lines.append(f"- **{f['title']}** -- {f['measured']}")
            if f.get("remedy"):
                lines.append(f"  - *Remedy:* {f['remedy']}")

    if report["build_findings"]:
        lines += ["", "## Build findings -- about Polaris, not about this check", ""]
        for f in report["build_findings"]:
            lines.append(f"- **{f['title']}** -- {f['measured']}")
    return "\n".join(lines)
