"""Making traffic against Polaris -- and nothing about what the logs did with it.

**Why this file exists.** `SCENARIO-logging-test.md` §3 asks for a guard: the
traffic side must not be able to import a logging module, so the two repos
cannot end up holding two answers about one policy. `log_coverage.py` made that
impossible to state. It is the v1 verification module *and* it held every
function that drives a call -- the tagging, the run principal, the 500 ladder --
so `make_traffic` could not be written without importing the very thing the
boundary forbids.

So the traffic half moved here, **verbatim**. Nothing in this file was
rewritten; the docstrings still describe the runs that earned them.
`log_coverage` re-imports every name below, so notebooks that call them as
`lc.<name>` keep working untouched.

The dependency runs ONE WAY and the guard in `test_make_traffic.py` asserts it:

    make_traffic  ->  traffic_helpers        (never log_coverage, os_report)
    log_coverage  ->  traffic_helpers

A helper belongs here if it *issues a request or shapes one*. It belongs in
`log_coverage` if it reads what a log pipeline stored. `classify_500` sits here
by that test: it reads the label the driver wrote, not a record.
"""

import hashlib
import re
import time

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


# ----------------------------------------------------------------------
# driving the surface with a request id per call
# ----------------------------------------------------------------------
#: `api_trace._MDC_REQUEST_ID` accepts [0-9a-zA-Z-_], so an underscore is
#: kept and everything else -- the dots in a label, the `[snapshots=refs]`
#: brackets -- folds to a dash. Stripping underscores too would still work,
#: but it makes `load_table` and `load-table` indistinguishable in an id.
_SLUG = re.compile(r"[^0-9A-Za-z_]+")


def _as_int(value, default=0):
    """One integer coercion, for two callers that both need it.

    Polaris hands `entityVersion` back as a JSON number; VictoriaLogs hands
    every report field back as a string and the Lua oracle returns numbers. One
    coercion so the same comparison runs against all three, and so this file
    and `log_coverage` cannot drift into two answers about `"3"` vs `3`.
    """
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
        #: BYTES POLARIS SENT BACK. `make_traffic`'s contract lists
        #: `response_bytes` per call, and the report's `last_write_bytes`
        #: claim is a comparison against a size. Same field, same way, as
        #: `api_status_matrix.execute` -- so a ladder row and a grid row
        #: are still one shape. Measured off the response, never the request.
        "response_bytes": None,
    }
    try:
        resp = fn()
        row["status"] = getattr(resp, "status_code", None)
        row["actual_path"] = _issued_path(resp)
        row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        row["echoed_request_id"] = getattr(resp, "headers", {}).get(header)
        row["response_bytes"] = len(getattr(resp, "content", b"") or b"")
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


def deprovision_run_principal(adm_pc, name, prole, run=None, seq=9900, tag=None):
    """Best-effort cleanup. Returns a list of what failed, never raises.

    The cleanup DELETEs are themselves part of the test, so they run inside the
    tagged window -- but a failure here must not lose the run's findings.

    `run` makes that first sentence true. Without it these two DELETEs went out
    with a Quarkus-generated request id and the verifier could not select them,
    while the notebook's section 11 asserted in a comment that cleanup IS the
    test.
    """
    problems = []
    #: ONE ID PER DELETE. This made two calls under one id until 2026-09-21,
    #: which is two of the three places run `1789955605`'s issued count could
    #: not close against `access_seen`.
    if tag is None and run is not None:
        tag = Tagger([adm_pc], run, start=seq, prefix="teardown-deprovision-")
    _tag = tag or (lambda label, fn: fn())
    for call, what in (
        (lambda: adm_pc.delete_principal(name), f"delete_principal {name}"),
        (lambda: adm_pc.delete_principal_role(prole), f"delete_principal_role {prole}"),
    ):
        try:
            r = _tag(what.split()[0].replace("_", "-"), call)
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
            #: BYTES POLARIS SENT BACK. `make_traffic`'s contract lists
            #: `response_bytes` per call, and the report's `last_write_bytes`
            #: claim is a comparison against a size. Same field, same way, as
            #: `api_status_matrix.execute` -- so a ladder row and a grid row
            #: are still one shape. Measured off the response, never the request.
            "response_bytes": None,
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
            row["response_bytes"] = len(getattr(resp, "content", b"") or b"")
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


#: Label prefix `drive_500` puts on every call it issues. `classify_500` reads
#: it, and the results document reads that: coverage claimed for the ERROR path
#: must be traceable to a call this notebook made on purpose.
DELIBERATE_500_PREFIX = "probe.500."


def drop_catalog_tree(adm_pc, ic, cat, ns=None, tag=None):
    """Empty a catalog, then delete it. Returns every status, never raises.

    A LADDER RUNG'S CLEANUP IS NOT A FORMALITY. `provokers_500` promised that
    "every rung creates its own catalog and deletes it in cleanup, so a rung
    that fails leaves nothing behind", and it was not true: the cleanups
    deleted the catalog while its namespace was still in it, Polaris answered
    400 (a catalog must be empty), and the `except Exception: pass` around the
    call swallowed a response that had never raised. Run 1789950539 left
    `nb1789950539bh` on the cluster and the ladder reported nothing wrong.

    Returns a dict of what each step answered, so a caller can SEE the leak.
    """
    out = {}
    #: `tag("label", fn)` when the caller wants one id per call; otherwise the
    #: calls go out under whatever id the caller already set.
    tag = tag or (lambda label, fn: fn())

    def _step(key, fn):
        try:
            r = tag(key.replace(" ", "-"), fn)
            out[key] = getattr(r, "status_code", r)
        except Exception as exc:  # noqa: BLE001 - cleanup never fails the run
            out[key] = f"{type(exc).__name__}: {exc}"
        return out[key]

    if ns is not None and ic is not None:
        # Whatever the rung managed to create before it failed. A rung whose
        # tables all 500'd has none; one that half-succeeded has some, and
        # those are exactly the runs that leaked.
        for kind, lister, dropper in (
            ("view", getattr(ic, "list_views", None), getattr(ic, "drop_view", None)),
            (
                "table",
                getattr(ic, "list_tables", None),
                getattr(ic, "drop_table", None),
            ),
        ):
            if lister is None or dropper is None:
                continue
            try:
                r = tag(f"list-{kind}s", lambda l=lister: l(cat, ns))
                ids = (r.json().get("identifiers") or []) if r.ok else []
            except Exception:  # noqa: BLE001
                ids = []
            for ident in ids:
                name = ident.get("name") if isinstance(ident, dict) else str(ident)
                _step(f"drop {kind} {name}", lambda n=name, d=dropper: d(cat, ns, n))
        _step(f"drop namespace {ns}", lambda: ic.drop_namespace(cat, ns))
    _step(f"delete catalog {cat}", lambda: adm_pc.delete_catalog(cat, purge=False))
    out["leaked"] = out.get(f"delete catalog {cat}") not in (200, 204, 404)
    return out


def current_tag(clients, header="Polaris-Request-Id"):
    """The request id the clients are carrying, or None."""
    for client in clients_of(clients):
        return (getattr(client, "extra_headers", {}) or {}).get(header)
    return None


def tag_around(clients, run, seq, label, fn):
    """Run `fn` with every client carrying a request id, then RESTORE the one
    they had.

    Restore rather than clear, so this nests: a rung's cleanup tagged as a
    group can contain calls that tag themselves, and the calls after them still
    carry the group's id instead of going out bare.
    """
    rid = request_id(run, seq, label)
    previous = current_tag(clients)
    tag_clients(clients, rid)
    try:
        return fn()
    finally:
        tag_clients(clients, previous)


class Tagger:
    """Gives every CALL its own request id, and remembers them in order.

    ONE ID PER CALL, NOT PER GROUP, and the difference is measurable. The run
    record's `ISSUED` is a set of request ids to be found in the window, which
    is only an equality while each id stands for one access line. Run
    `1789955605` had exactly three ids carrying two calls each -- the black
    hole rung's cleanup, and both `teardown-deprovision`s -- so the notebook
    could claim "at least 345" against 354 seen and nothing could close the
    gap. A helper that makes four calls under one id turns a check into an
    estimate.

    `tagger("drop-namespace", lambda: ic.drop_namespace(cat, ns))` returns
    whatever `fn` returns and appends the id to `tagger.ids`.
    """

    def __init__(self, clients, run, start=9000, prefix=""):
        self.clients = list(clients_of(clients))
        self.run = run
        self.prefix = prefix
        self._next = start
        self.ids = []

    def next_id(self, label):
        #: A plain counter rather than `itertools.count`: `log_coverage` must
        #: re-export every public name this module has, and an imported module
        #: is a public name.
        rid = request_id(self.run, self._next, f"{self.prefix}{label}")
        self._next += 1
        self.ids.append(rid)
        return rid

    def __call__(self, label, fn):
        rid = self.next_id(label)
        previous = current_tag(self.clients)
        tag_clients(self.clients, rid)
        try:
            return fn()
        finally:
            tag_clients(self.clients, previous)


#: The PG-HA read-after-write signature. A 500 on one of these is a write that
#: COMMITTED -- `load_view`/`head_view`/`drop_view` all answered 2xx afterwards
#: on 2026-09-01 -- so it is a replica-lag artefact, not an unhandled
#: exception, and counting it as ERROR-path coverage is the substitution this
#: whole section exists to stop.
PG_HA_500_LABELS = ("iceberg.create_namespace", "iceberg.create_view")


class Provoker:
    """One rung of the 500 ladder: API-only, reversible, self-cleaning.

    `prepare` and `cleanup` are the fixture; `calls` returns
    `(label, fn, method, path)` tuples for `call_once` to drive, and is called
    AFTER `prepare` so it can close over whatever prepare built. Nothing here
    touches kubectl, psql or the schema -- a rung that needs the cluster is not
    a rung this notebook can own.
    """

    def __init__(
        self, name, why, calls, prepare=None, cleanup=None, assumed=False, tagged=False
    ):
        self.name = name
        self.why = why
        self._calls = calls
        self.prepare = prepare
        self.cleanup = cleanup
        #: True where the rung has never been observed to return 500 on this
        #: build. The ladder is ordered, not proven.
        self.assumed = assumed
        #: True when `prepare`/`cleanup` tag each of their own calls. `drive_500`
        #: then does NOT wrap them in one id of its own -- an id that stands for
        #: no access line is a false positive in the run's ISSUED check, which
        #: is the same failure as an untagged call, pointing the other way.
        self.tagged = tagged

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
    unresolvable="http://nb-no-such-minio.datahub-hynix.svc.invalid:9000",
    bad_bucket=None,
    repeat=3,
    tag=None,
):
    """The ladder, cheapest and most likely first. Drive it with `drive_500`.

    Every rung creates its own catalog and empties and deletes it in
    `cleanup`, so a rung that fails leaves nothing behind and the next one
    starts clean. That sentence was false until 2026-09-21 -- the cleanups
    deleted a non-empty catalog, got 400, and swallowed it -- and
    `drop_catalog_tree` is what makes it true. `ladder[i]["cleanup"]` carries
    the statuses so a leak is visible rather than inferred from the cluster
    later.

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
        unresolvable: rung 2's endpoint, whose HOSTNAME does not resolve. Kept
            separate from `unreachable` because the two fail at different
            layers -- DNS versus TCP -- and the S3 client may handle them in
            different code paths, so one can 500 where the other does not.
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
    #: `tag("label", fn) -> result`, one request id per call. Without it the
    #: rung's fixture calls go out under whatever id `drive_500` set for the
    #: whole prepare or cleanup, which is two-to-four calls under one id.
    _tag = tag or (lambda label, fn: fn())
    _tagged = tag is not None

    # -- rung 1: the storage endpoint Polaris itself cannot reach ------------
    # This is `error-cases/09`'s intent, repaired. 09 broke because it left
    # `endpoint` valid and only omitted `endpointInternal`, and this build
    # falls back to `endpoint` -- so the catalog worked and the notebook
    # reported 200 while still calling itself a NullPointerException test.
    # Pointing BOTH at a dead port removes the fallback.
    bh_cat = f"nb{run}bh"
    bh_ns = "bh_ns"

    def bh_prepare():
        r = _tag(
            f"{bh_cat}-create-catalog",
            lambda: adm_pc.create_catalog(
                bh_cat, bucket, unreachable, minio_endpoint_internal=unreachable
            ),
        )
        state["bh_catalog"] = r.status_code
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        # The namespace is metadata only and must SUCCEED -- it gives the
        # window a resource key that was read cleanly, so the 500s that follow
        # can be shown to land in the report's error bucket instead of
        # creating one. THE BUCKET IS `__errors__`, not `__other__`: they are
        # different fields and `resources_other` was 0 in run 1789950539 while
        # `__errors__` held all three of this rung's 500s. Confirmed there --
        # `/nb1789950539bh/namespaces` got a clean row with 1 write and 0
        # errors, and `/namespaces/bh_ns/tables` got no row at all.
        state["bh_ns"] = _tag(
            f"{bh_cat}-create-namespace", lambda: ic.create_namespace(bh_cat, bh_ns)
        ).status_code

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
        #
        # THE NAMESPACE GOES FIRST. `bh_prepare` creates it and a catalog must
        # be empty to be deleted, so deleting the catalog alone answered 400
        # and `nb<run>bh` stayed on the cluster after every run.
        state["bh_cleanup"] = drop_catalog_tree(adm_pc, ic, bh_cat, bh_ns, tag=_tag)
        return state["bh_cleanup"]

    # -- rung 2: an endpoint whose HOSTNAME does not resolve ----------------
    # Kade's case, and a more realistic mistake than rung 1: a typo in the
    # in-cluster MinIO service name. It fails at a DIFFERENT layer -- DNS
    # resolution (UnknownHostException) rather than a refused TCP connect
    # (ConnectException) -- and the two can be handled by different code paths
    # in the S3 client, so one can 500 while the other does not. `.svc.invalid`
    # keeps the shape of the real internal name while RFC 2606 guarantees the
    # lookup fails; a plausible-but-wrong name risks resolving to something.
    dns_cat = f"nb{run}dns"
    dns_ns = "dns_ns"

    def dns_prepare():
        r = _tag(
            f"{dns_cat}-create-catalog",
            lambda: adm_pc.create_catalog(
                dns_cat, bucket, unresolvable, minio_endpoint_internal=unresolvable
            ),
        )
        state["dns_catalog"] = r.status_code
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        state["dns_ns"] = _tag(
            f"{dns_cat}-create-namespace", lambda: ic.create_namespace(dns_cat, dns_ns)
        ).status_code

    def dns_calls():
        return [
            (
                f"create_table_{i}",
                (
                    lambda n=f"dns_tbl_{i}": ic.create_table(
                        dns_cat, dns_ns, table_payload(n)
                    )
                ),
                "POST",
                f"{CAT_PREFIX}/v1/{dns_cat}/namespaces/{dns_ns}/tables",
            )
            for i in range(repeat)
        ]

    def dns_cleanup():
        state["dns_cleanup"] = drop_catalog_tree(adm_pc, ic, dns_cat, dns_ns, tag=_tag)
        return state["dns_cleanup"]

    # -- rung 3: a bucket that is not there ---------------------------------
    nb_cat = f"nb{run}nobkt"
    nb_ns = "nobkt_ns"
    missing_bucket = bad_bucket or f"nb-{run}-no-such-bucket"

    def nb_prepare():
        r = _tag(
            f"{nb_cat}-create-catalog",
            lambda: adm_pc.create_catalog(
                nb_cat,
                missing_bucket,
                endpoint,
                minio_endpoint_internal=endpoint_internal or endpoint,
            ),
        )
        state["nb_catalog"] = r.status_code
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        state["nb_ns"] = _tag(
            f"{nb_cat}-create-namespace", lambda: ic.create_namespace(nb_cat, nb_ns)
        ).status_code

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
        state["nb_cleanup"] = drop_catalog_tree(adm_pc, ic, nb_cat, nb_ns, tag=_tag)
        return state["nb_cleanup"]

    # -- rung 4: a stale entity version -------------------------------------
    # [assumed], and flagged as such: `PolarisREST.update_catalog`'s own
    # docstring says a stale `currentEntityVersion` returns 409, not 500. If
    # that is right this rung can never fire and its value is the record of
    # having tried it. `error-cases/18` believed otherwise.
    sv_cat = f"nb{run}stale"

    def sv_prepare():
        r = _tag(
            f"{sv_cat}-create-catalog",
            lambda: adm_pc.create_catalog(
                sv_cat,
                bucket,
                endpoint,
                minio_endpoint_internal=endpoint_internal or endpoint,
            ),
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"catalog create returned {r.status_code}: {r.text[:200]}"
            )
        cat = _tag(f"{sv_cat}-get-catalog", lambda: adm_pc.get_catalog(sv_cat)).json()
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
        # This rung creates no namespace, so there is nothing to empty.
        state["sv_cleanup"] = drop_catalog_tree(adm_pc, None, sv_cat, tag=_tag)
        return state["sv_cleanup"]

    return [
        Provoker(
            "black_hole_endpoint",
            "both storage endpoints point at a dead port, so Polaris' own S3 "
            "client cannot resolve storage on table create",
            bh_calls,
            prepare=bh_prepare,
            cleanup=bh_cleanup,
            assumed=True,
            tagged=_tagged,
        ),
        Provoker(
            "unresolvable_host",
            "the storage endpoint's hostname does not resolve -- a typo in the "
            "in-cluster MinIO service name, failing at DNS rather than at "
            "connect",
            dns_calls,
            prepare=dns_prepare,
            cleanup=dns_cleanup,
            assumed=True,
            tagged=_tagged,
        ),
        Provoker(
            "nonexistent_bucket",
            "the catalog's bucket does not exist in MinIO (error-cases/23, "
            "API-only half)",
            nb_calls,
            prepare=nb_prepare,
            cleanup=nb_cleanup,
            assumed=True,
            tagged=_tagged,
        ),
        Provoker(
            "stale_entity_version",
            "optimistic-lock conflict on PUT /catalogs (error-cases/18) -- "
            "[assumed], and update_catalog's docstring says this is a 409",
            sv_calls,
            prepare=sv_prepare,
            cleanup=sv_cleanup,
            assumed=True,
            tagged=_tagged,
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
        note, rung_rows, cleanup_out = None, [], None
        try:
            if prov.prepare is not None:
                # TAGGED. A rung's prepare creates a catalog and a namespace
                # and its cleanup deletes the catalog -- traffic in the same
                # window as the 500s, and until now the only way to find it
                # was to guess from the path. Run 1789950539 shows the cost:
                # `POST /api/management/v1/catalogs` and `DELETE
                # /api/management/v1/catalogs/nb1789950539bh` carry
                # Quarkus-generated request ids, so the catalog the ladder
                # leaves behind cannot be attributed to the ladder.
                #
                # NOT under DELIBERATE_500_PREFIX: a 500 out of a prepare or a
                # cleanup is an accident of the rung, not a 500 the ladder
                # drove on purpose, and `classify_500` must keep saying so.
                if getattr(prov, "tagged", False):
                    prov.prepare()
                else:
                    seq += 1
                    tag_around(clients, run, seq, f"{prov.name}.prepare", prov.prepare)
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
                        if getattr(prov, "tagged", False):
                            cleanup_out = prov.cleanup()
                        else:
                            seq += 1
                            cleanup_out = tag_around(
                                clients, run, seq, f"{prov.name}.cleanup", prov.cleanup
                            )
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
            #: What the cleanup answered, so a leaked catalog is reported by
            #: the run that leaked it rather than found on the cluster weeks
            #: later. `None` when the rung never ran.
            "cleanup": cleanup_out,
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


# ----------------------------------------------------------------------
# phase J -- a two-level namespace (added 2026-09-16, not moved from v1)
# ----------------------------------------------------------------------
#: Names defined here AFTER the split. They were never in `log_coverage`, so
#: `test_log_coverage_still_re_exports_every_moved_name` must not ask the v1
#: module to re-export them -- that test guards what MOVED.
__added_after_split__ = frozenset(
    {
        "NESTED_CHILD",
        "nested_table_resource_key",
        "drive_nested_namespace",
        #: 2026-09-21, with the tagging of a rung's prepare and cleanup,
        #: and with the cleanup that actually empties its catalog.
        "tag_around",
        "drop_catalog_tree",
        "Tagger",
        "current_tag",
    }
)

#: The child level phase J creates under the fixture namespace.
NESTED_CHILD = "nested"


def nested_table_resource_key(catalog, parent_ns, child, table):
    """The report row key a table in `parent_ns.child` must land on.

    Iceberg REST joins namespace levels with the ASCII unit separator, which a
    URL carries as `%1F`. The shipper's Lua keys a table row on the request path
    AND, for commit time, rebuilds the same key from the dotted identifier in
    `Successfully committed to table cat.parent.child.table`. If the two do not
    produce this exact string, the commit lands on a second row that no request
    touches -- which is what phase J exists to catch.
    """
    return f"{CAT_PREFIX}/v1/{catalog}/namespaces/{parent_ns}%1F{child}/tables/{table}"


def drive_nested_namespace(
    ic, run, catalog, parent_ns, schema, table_payload, seq=3400
):
    """Phase J: create, commit, load and drop a table in a two-level namespace.

    Six calls on one client, each tagged with its own request id:
    createNamespace, createTable, updateTable (a commit), loadTable, dropTable,
    dropNamespace. The two drops are attempted even when an earlier step failed,
    so a half-run leaves nothing behind.

    Args:
        ic: an `IcebergREST` client (the runner's, so the calls are attributed to
            a real principal).
        run: the run id.
        catalog: the fixture catalog -- Polaris's URL prefix is the catalog name.
        parent_ns: an existing single-level namespace in it.
        schema, table_payload: as the other phases build tables.
        seq: first request-id sequence number; the six steps use seq..seq+5.

    Returns:
        dict with `rows` (one per call, the same shape `make_traffic` records),
        `namespace` (the two levels), `table`, `resource_key` (what the verifier
        must find as ONE row carrying both requests and commit_count),
        `path_encoded` (True when every issued path carried `%1F`), and
        `request_ids`.
    """
    ns = [parent_ns, NESTED_CHILD]
    table = f"mx_{run}_deep"
    steps = [
        ("createNamespace", "POST", 200, lambda: ic.create_namespace(catalog, ns)),
        (
            "createTable",
            "POST",
            200,
            lambda: ic.create_table(catalog, ns, table_payload(table, schema)),
        ),
        (
            "updateTable",
            "POST",
            200,
            lambda: ic.commit_table(
                catalog,
                ns,
                table,
                [{"action": "set-properties", "updates": {"mx.nested": str(run)}}],
            ),
        ),
        ("loadTable", "GET", 200, lambda: ic.load_table(catalog, ns, table)),
        ("dropTable", "DELETE", 204, lambda: ic.drop_table(catalog, ns, table)),
        ("dropNamespace", "DELETE", 204, lambda: ic.drop_namespace(catalog, ns)),
    ]
    rows = []
    for i, (op_id, method, target, fn) in enumerate(steps):
        rid = request_id(run, seq + i, f"nested-{op_id}")
        tag_clients([ic], rid)
        t0 = time.time()
        try:
            resp = fn()
            status = getattr(resp, "status_code", None)
            rows.append(
                {
                    "request_id": rid,
                    "echoed_request_id": (getattr(resp, "headers", {}) or {}).get(
                        "Polaris-Request-Id"
                    ),
                    "op_id": op_id,
                    "method": method,
                    "actual_path": _issued_path(resp),
                    "api": "catalog",
                    "target": target,
                    "status": status,
                    "response_bytes": len(getattr(resp, "content", b"") or b""),
                    "principal": "runner",
                    "issued_at": t0,
                    "verdict": "covered" if status == target else "missed",
                }
            )
        except Exception as exc:  # noqa: BLE001 - the drops below must still run
            rows.append(
                {
                    "request_id": rid,
                    "op_id": op_id,
                    "method": method,
                    "api": "catalog",
                    "target": target,
                    "status": None,
                    "principal": "runner",
                    "issued_at": t0,
                    "verdict": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        finally:
            tag_clients([ic], None)
    # createNamespace names both levels in its BODY; every other step carries
    # them in the path, which is the encoding the report key depends on.
    paths = [
        r.get("actual_path")
        for r in rows
        if r["op_id"] != "createNamespace" and r.get("actual_path")
    ]
    return {
        "rows": rows,
        "namespace": ns,
        "table": table,
        "resource_key": nested_table_resource_key(
            catalog, parent_ns, NESTED_CHILD, table
        ),
        "path_encoded": bool(paths) and all("%1F" in p for p in paths),
        "request_ids": [r["request_id"] for r in rows],
    }
