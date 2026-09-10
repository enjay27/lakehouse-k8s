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
ERROR = "error"

#: Outcomes for a whole pass.
PASS = "PASS"
FAIL = "FAIL"
VOID = "VOID"

DEFAULT_TIMEOUT = 15


class PrismUnavailable(RuntimeError):
    """Prism is not answering. Not a finding -- nothing was measured."""


def prism_mounts(spec_dir):
    """`{api: mount path}`, read from each document's own `servers` entry.

    Server URLs are templated (`{scheme}://{host}/{basePath}`), so the
    variables are resolved to their declared defaults before the path is taken.
    A `basePath` defaulting to `""` yields `""`, which is correct and is
    exactly the case that differs from `Operation.base`.
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
        mounts[api] = _server_path(servers[0]) if servers else ""
    return mounts


def _server_path(server):
    url = str((server or {}).get("url") or "")
    for name, var in ((server or {}).get("variables") or {}).items():
        url = url.replace("{" + name + "}", str((var or {}).get("default", "")))
    path = urlsplit(url).path if "//" in url else url
    return "/" + path.strip("/") if path.strip("/") else ""


def prism_path(op, request_path, mounts):
    """The Polaris request path, re-aimed at where Prism serves that spec.

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
    return (mounts.get(op.api, "") + request_path[len(base) :]) or "/"


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

    `NOT_ROUTED` is kept apart from `REJECTED` deliberately. A 404 from Prism
    means the mount is wrong or the document has no such path -- a fault in
    THIS module or in the spec -- while a 422 with violations is a statement
    about the request. Folding them together would report a mounting mistake
    as 286 invalid requests.
    """
    if status is None:
        return ERROR
    if status == 404 and not _violations(body):
        return NOT_ROUTED
    if 200 <= status < 400:
        return ACCEPTED
    if _violations(body) or status in (400, 422):
        return REJECTED
    return ERROR


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


def controls(spec_dir, prism, binding, tokens, realm, session, timeout=DEFAULT_TIMEOUT):
    """Prove Prism is enforcing before believing anything it says.

    Returns `{"negative": ..., "positive": ..., "ok": bool, "why": str}`.
    Both controls come from the real grid rather than from a hand-written
    request, so a control cannot pass while the thing it vouches for is built
    differently.
    """
    import api_status_matrix as mx

    mounts = prism_mounts(spec_dir)
    grid = mx.cells(mx.load_spec(spec_dir))

    # NOT `getToken`. It is the only form-encoded operation in the grid, and
    # the grid's sort order lands on it first -- so the naive pick made the
    # least representative cell vouch for all 286. Whether Prism validates a
    # form body against the spec's schema is an open question; whether it
    # validates a JSON body is not, and the control must rest on the settled
    # one. The form-encoded cell is still CHECKED, it just does not vouch.
    neg = next(
        (
            c
            for c in grid
            if c.target == 400 and c.op.has_body and c.op.op_id not in mx.FORM_ENCODED
        ),
        None,
    )
    pos = next((c for c in grid if c.target == 2 and not c.op.params), None)
    if neg is None or pos is None:
        return {
            "ok": False,
            "why": "the grid has no cell to build a control from",
            "negative": None,
            "positive": None,
        }

    out = {}
    for name, cell, want in (("negative", neg, REJECTED), ("positive", pos, ACCEPTED)):
        req = mx.request_for(cell, binding, tokens, f"speccheck-{name}", realm)
        url = prism[cell.op.api].rstrip("/") + prism_path(cell.op, req["path"], mounts)
        try:
            status, body = _send(session, url, req, timeout)
        except Exception as exc:  # noqa: BLE001
            raise PrismUnavailable(
                f"the {name} control could not reach Prism at {url}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        got = classify(status, body)
        out[name] = {
            "op_id": cell.op.op_id,
            "url": url,
            "status": status,
            "verdict": got,
            "expected": want,
            "ok": got == want,
            "detail": violation_summary(body),
        }

    why = ""
    unrouted = [n for n in ("negative", "positive") if out[n]["verdict"] == NOT_ROUTED]
    if unrouted:
        why = (
            f"the {' and '.join(unrouted)} control(s) were NOT ROUTED: Prism "
            "answered 404 to a path the document declares, so the mount is "
            "wrong or the document did not load. Every request below would "
            "404 for the same reason, and NONE of it would be about the "
            f"requests. Mounts in use: {mounts}."
        )
    elif not out["negative"]["ok"]:
        why = (
            "the negative control was NOT rejected: Prism is serving the spec "
            "but not enforcing it. `prism mock` without `--errors` logs "
            "violations and answers 200 anyway, and every request below would "
            "then read as valid. Restart it with --errors."
        )
    elif not out["positive"]["ok"]:
        why = (
            "the positive control was not accepted "
            f"({out['positive']['verdict']}): a request known to be valid did "
            "not get through, so the mount or the document is wrong and every "
            "rejection below would be this fault, not the request's."
        )
    out["ok"] = out["negative"]["ok"] and out["positive"]["ok"]
    out["why"] = why
    return out


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

    ctl = controls(spec_dir, prism, binding, tokens, realm, session, timeout)
    mounts = prism_mounts(spec_dir)
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

    unexpected = [r for r in rows if not r["ok"]]
    not_routed = [r for r in rows if r["verdict"] == NOT_ROUTED]
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
        "errors": sum(1 for r in rows if r["verdict"] == ERROR),
        "unexpected": unexpected,
        "rows": rows,
        "build_findings": build_findings(rows),
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


def render_report(report):
    """Markdown, with the verdict and its reason first."""
    v = report["verdict"]
    lines = [
        f"# Request conformance against the spec -- {v}",
        "",
        f"{report['cells']} cells: {report['accepted']} accepted, "
        f"{report['rejected']} rejected, {report['not_routed']} not routed, "
        f"{report['errors']} error.",
        "",
    ]
    if v == VOID:
        lines += [
            "**VOID -- nothing was measured.** " + (report["why"] or ""),
            "",
            "A VOID pass is not a pass. Do not read the counts above as a result.",
            "",
        ]
    ctl = report.get("controls") or {}
    lines += [
        "## Controls",
        "",
        "| control | operation | expected | got | ok |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in ("negative", "positive"):
        c = ctl.get(name)
        if c:
            lines.append(
                f"| {name} | `{c['op_id']}` | {c['expected']} | {c['verdict']} | "
                f"{'yes' if c['ok'] else 'NO'} |"
            )
    if report["unexpected"]:
        lines += [
            "",
            "## Cells that did not do what the spec says they should",
            "",
            "| operation | target | expected | got | detail |",
            "| --- | ---: | --- | --- | --- |",
        ]
        for r in report["unexpected"][:40]:
            lines.append(
                f"| `{r['op_id']}` | {r['target']} | {r['expected']} | "
                f"{r['verdict']} | {r['detail'][:110]} |"
            )
    if report["build_findings"]:
        lines += ["", "## Build findings -- about Polaris, not about this check", ""]
        for f in report["build_findings"]:
            lines.append(f"- **{f['title']}** -- {f['measured']}")
    return "\n".join(lines)
