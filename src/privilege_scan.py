"""
privilege_scan.py
=================
Drive EVERY seeded principal through the authenticated GET surface, so the
grantee lookup can be observed firing with a thousand different grantee ids
against one `grant_records` table.

WHY THIS EXISTS, AND WHY IT IS NOT `api_sweep`
----------------------------------------------
`api_sweep` measures latency per API across a volume grid, as ONE identity.
Notebook 01 traces one call per API, as ROOT. Both answer "what does this API
cost"; neither answers the question this scan is for:

    with 1,000 real principals holding 50 grants each, does the privilege
    query use an index -- and does that hold across the whole distribution
    of grantees, not one probe?

Root is the least representative identity in the realm: its authorization
resolves to two grant rows. An ordinary `user{N}_principal` resolves through
its principal-role to a catalog-role holding 50. Sweeping only as root measures
the identity that benefits most from the index and reports it as typical.

THE SCOPE TRAP, MEASURED BEFORE (see `polaris_test_utils.get_token`)
--------------------------------------------------------------------
Root can request `PRINCIPAL_ROLE:ALL`. A NON-ROOT principal generally cannot:
the token exchange still returns 200, but the token carries no effective role
and every downstream call 403s. Driving 1,000 principals with the wrong scope
would produce a clean, total, entirely artificial "the GET surface is
unauthorized" result. So `authenticate()` defaults to the identity's OWN
principal-role and records which scope produced the token.

WHAT IS READ FROM THE DATABASE, AND WHY NOT CONSTRUCTED
--------------------------------------------------------
`polaris_seed` discards the `clientId`/`clientSecret` that `create_principal`
returns, and the ledger records only which user indices finished. So the
client_ids of a seeded fixture exist in exactly one place --
`principal_authentication_data` -- and this module reads them from there.

It would be one line shorter to build them from a format string. This repo has
been wrong three times about constants it did not ask the server for (the
25-privilege list, `CLONE_ID_BASE`, a catalog's own `catalog_id`), each time
because a plausible pattern was assumed instead of queried. `load_identities`
asks.
"""

from dataclasses import dataclass, field

import api_trace

#: `entities.type_code` values, from `entity_replay` where they were confirmed
#: against live rows rather than inferred from an enum.
TYPE_PRINCIPAL = 2
TYPE_CATALOG = 4

#: The catalog-role `polaris_seed` gives every user. Mirrors
#: `polaris_seed.OWNER_ROLE_NAME`; imported by name rather than duplicated
#: would couple this module to the seeder for one string, and this module has
#: to work against a fixture built by any means.
OWNER_ROLE_NAME = "owner_principal"

#: Label for the `GET /namespaces` call `drive()` makes to resolve a namespace,
#: kept distinct from the identical call the drive itself issues. See the note
#: in `drive()`.
NS_RESOLVE_LABEL = "GET  /namespaces [ns-resolve]"


@dataclass
class Identity:
    """One seeded principal, with everything needed to authenticate AS it.

    `client_id` comes from `principal_authentication_data`; `namespace` is
    resolved later, from the live API, because a namespace the identity cannot
    list is not a namespace this scan can drive.
    """

    index: int
    principal: str
    principal_role: str
    client_id: str
    catalog: str
    catalog_role: str = OWNER_ROLE_NAME
    namespace: str = None

    def fixture(self):
        """The `fx` mapping `api_sweep.read_operations` expects."""
        return {
            "catalog": self.catalog,
            "namespace": self.namespace,
            "principal": self.principal,
            "principal_role": self.principal_role,
            "catalog_role": self.catalog_role,
        }


@dataclass
class OpStatus:
    """One API, driven once, with what actually came back."""

    label: str
    surface: str
    status: int
    detail: str = ""

    @property
    def ok(self):
        return 200 <= self.status < 300


@dataclass
class ScanResult:
    """Outcome of a full drive. Counts, and everything that did not work."""

    identities: int = 0
    authenticated: int = 0
    requests: int = 0
    #: (identity index, op label) -> status, for every call made.
    statuses: dict = field(default_factory=dict)
    #: Identities that never got a usable token, with the reason.
    auth_failures: list = field(default_factory=list)
    #: Identities dropped before driving, e.g. no namespace they can list.
    skipped: list = field(default_factory=list)
    #: Non-2xx responses from the drive itself, as (index, label, status).
    errors: list = field(default_factory=list)
    elapsed_s: float = 0.0

    def summary(self):
        return (
            f"{self.authenticated}/{self.identities} identities authenticated, "
            f"{self.requests} requests, {len(self.errors)} non-2xx, "
            f"{len(self.auth_failures)} auth failures, "
            f"{len(self.skipped)} skipped, {self.elapsed_s:.0f}s"
        )


# ----------------------------------------------------------------------
# reading the fixture
# ----------------------------------------------------------------------
def load_identities(conn, schema, realm, prefix="user", limit=None):
    """Every seeded principal that can actually be authenticated as.

    Two queries against the metastore, not 2,000 REST calls: the fixture exists
    as rows, so the rows are the authority.

    A principal WITHOUT a `principal_authentication_data` entry, or without its
    catalog, is not returned -- it is reported. Both are real states here: SQL
    clones are created without credential rows on purpose, and non-atomic
    catalog creation has stranded catalog-less principals before.

    Args:
        conn: psycopg2 connection. Reads go through `NO_LOAD_BALANCE` so the
            pooler cannot answer from a replica that is behind the seeder.
        schema / realm: metastore schema and realm id.
        prefix: seeder name prefix (`user` -> `user7_principal`).
        limit: stop after this many identities, for a trial run.

    Returns:
        (identities, problems) -- `problems` maps a reason to the principal
        names it applies to, so a caller can print what it is NOT driving.
    """
    like = f"{prefix}%"
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT id, name, type_code FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND type_code = ANY(%s) AND name LIKE %s",
            (realm, [TYPE_PRINCIPAL, TYPE_CATALOG], like),
        )
        rows = cur.fetchall()

        cur.execute(
            api_trace.NO_LOAD_BALANCE + "SELECT principal_id, principal_client_id "
            f"FROM {schema}.principal_authentication_data "  # noqa: S608
            "WHERE realm_id = %s",
            (realm,),
        )
        client_ids = {pid: cid for pid, cid in cur.fetchall()}

    principals = {}  # index -> (id, name)
    catalogs = set()  # catalog names
    for ent_id, name, type_code in rows:
        if type_code == TYPE_CATALOG:
            catalogs.add(name)
            continue
        idx = _user_index(name, prefix, "_principal")
        if idx is not None:
            principals[idx] = (ent_id, name)

    identities, problems = [], {"no_credential": [], "no_catalog": []}
    for idx in sorted(principals):
        ent_id, name = principals[idx]
        client_id = client_ids.get(ent_id)
        catalog = f"{prefix}{idx}_catalog"
        if not client_id:
            problems["no_credential"].append(name)
            continue
        if catalog not in catalogs:
            problems["no_catalog"].append(name)
            continue
        identities.append(
            Identity(
                index=idx,
                principal=name,
                principal_role=f"{prefix}{idx}_principal_role",
                client_id=client_id,
                catalog=catalog,
            )
        )
        if limit and len(identities) >= limit:
            break
    return identities, problems


def _user_index(name, prefix, suffix):
    """`user37_principal` -> 37, and None for anything else.

    Deliberately strict: `root`, `service_admin` and any hand-made principal
    that happens to start with the prefix must not be driven as if the seeder
    had made them.
    """
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    middle = name[len(prefix) : -len(suffix)]
    return int(middle) if middle.isdigit() else None


# ----------------------------------------------------------------------
# authenticating as one of them
# ----------------------------------------------------------------------
def authenticate(pc, identity, secret, scope=None):
    """A token for `identity`, at the scope a non-root principal can use.

    Returns (token, scope_used, detail). `token` is None on failure and
    `detail` says why.

    THE FAILURE THIS AVOIDS. `PRINCIPAL_ROLE:ALL` is root's scope. A non-root
    principal asking for it can still be handed a 200 and a token that carries
    no effective role -- and then every API call 403s. Run at 1,000 identities
    that reads as "the GET surface is unauthorized for ordinary principals",
    which is a statement about the scope string and nothing else. So the
    default scope is the identity's OWN principal-role, and the scope that
    produced the token is returned for the report to state.
    """
    scope = scope or f"PRINCIPAL_ROLE:{identity.principal_role}"
    r = pc.get_token(identity.client_id, secret, scope=scope)
    if r.status_code >= 300:
        return None, scope, f"token [{r.status_code}] {(r.text or '')[:160]}"
    try:
        token = (r.json() or {}).get("access_token")
    except Exception:  # noqa: BLE001
        return None, scope, "token response was not JSON"
    if not token:
        return None, scope, "token response carried no access_token"
    return token, scope, ""


def resolve_namespace(client, identity):
    """The first namespace this identity can actually list in its catalog.

    Not `ns1` by convention: a namespace the identity cannot see is not one the
    scan can drive, and finding that out here costs one call instead of
    producing a column of 403s that look like an authorization finding.

    Returns (name, detail); `name` is None when there is nothing to drive.
    """
    r = client.list_namespaces(identity.catalog)
    if r.status_code >= 300:
        return None, f"list_namespaces [{r.status_code}]"
    try:
        levels = (r.json() or {}).get("namespaces") or []
    except Exception:  # noqa: BLE001
        return None, "list_namespaces response was not JSON"
    if not levels:
        return None, "catalog has no namespaces"
    first = levels[0]
    #: The Iceberg REST shape is a list of multi-level namespaces, each itself
    #: a list of parts. A single-level `ns1` arrives as `["ns1"]`.
    return (first[0] if isinstance(first, (list, tuple)) else first), ""


# ----------------------------------------------------------------------
# what an ordinary principal is actually allowed to GET
# ----------------------------------------------------------------------
def probe_surface(client, identity, ops):
    """Issue every op ONCE and record what came back. No timing, no assertion.

    This is the pre-flight the whole scan rests on. A `user{N}_principal` holds
    `owner_principal` on its OWN catalog and nothing else, so the service-level
    reads (`GET /principals`, `/principal-roles`, `/catalogs`) may well 403 --
    and `api_sweep.assert_ok` refuses to time a non-2xx, correctly: an error
    path has a latency too, and putting it in a column headed "ms" reports a
    403 as a performance characteristic.

    Thirteen calls settle empirically what would otherwise be an assumption
    baked into thousands of requests.

    Returns a list of `OpStatus`, in the order the ops were given.
    """
    out = []
    for label, surface, fn in ops:
        try:
            r = fn(client)
            status, detail = r.status_code, ""
            if status >= 300:
                detail = (getattr(r, "text", "") or "")[:160]
        except Exception as exc:  # noqa: BLE001
            status, detail = 0, f"{type(exc).__name__}: {exc}"
        out.append(OpStatus(label, surface, status, detail))
    return out


def authorized_ops(ops, statuses):
    """The subset of `ops` the probe got a 2xx from, order preserved."""
    ok = {s.label for s in statuses if s.ok}
    return [(label, surface, fn) for label, surface, fn in ops if label in ok]


# ----------------------------------------------------------------------
# proving the capture is live BEFORE spending a pass on it
# ----------------------------------------------------------------------
#: A PostgreSQL statement line, in either of the two forms the capture can
#: produce: `log_statement='all'` writes `statement:`, and
#: `log_min_duration_statement=0` writes `duration: … ms  statement:`.
#: Checkpoint and restartpoint chatter matches NEITHER, which is the whole
#: point -- a pg log full of checkpoints looks alive and contains no evidence.
_PG_STATEMENT_MARKERS = ("statement:", "execute <unnamed>", "execute S_")

#: The Polaris logger that emits the SQL. Its absence from a non-empty log
#: means the level is above DEBUG, which is a different fault with a different
#: fix than a dead stream.
_POLARIS_SQL_MARKER = "DatasourceOperations"


def capture_snapshot(capture_dir):
    """`{filename: size}` for every log file in a capture directory.

    Sizes, not mtimes: a stream that reopens a file touches the mtime without
    writing anything, and this has to answer "did bytes arrive", not "did
    something happen to the file".
    """
    import os

    out = {}
    if not capture_dir or not os.path.isdir(capture_dir):
        return out
    for name in sorted(os.listdir(capture_dir)):
        if name.endswith(".log"):
            path = os.path.join(capture_dir, name)
            try:
                out[name] = os.path.getsize(path)
            except OSError:
                out[name] = 0
    return out


def capture_verdict(before, after, polaris_tail="", pg_tail=""):
    """Did a capture actually record the call that just happened?

    Returns `(ok, reasons)`. `ok` is False with one plain-language reason per
    fault, each naming its own fix -- these fail for different reasons and a
    single "capture looks wrong" would send the operator to the wrong one.

    WHY THIS IS A HARD GATE (2026-08-24, learned by losing a pass). A 9,000-
    request drive completed cleanly against a capture that held **410 bytes**:
    one line, `Apache Polaris Server stopped`, because the `kubectl logs -f`
    was attached to a pod that restarted three minutes before the drive began.
    The PostgreSQL logs held checkpoint chatter and not one statement, because
    `./capture.sh rotate` restarts the log STREAMS and does not touch
    `log_statement` -- which had been left at `'none'` by the `pgoff` that 02's
    timing work correctly required. Both faults are invisible from the drive's
    own output: it reported 1000/1000, zero non-2xx, 98 seconds.

    This is the same lesson as 01's preflight, which used to infer logging was
    off from a quiet log tail: do not reason about the stream, make one call
    and look for ITS output.

    Args:
        before / after: `capture_snapshot` results either side of one
            authenticated API call.
        polaris_tail: recent bytes of the Polaris log, for the SQL-logger check.
        pg_tail: recent bytes of any replica's log, for the statement check.
    """
    reasons = []
    grew = {n for n, size in after.items() if size > before.get(n, 0)}

    if not after:
        return False, [
            "the capture directory holds no .log files at all — is a capture "
            "running? ./capture.sh start <dir>"
        ]

    if "polaris.log" not in grew:
        reasons.append(
            "polaris.log did not grow. The stream is dead — a `kubectl logs -f` "
            "attached to a pod that has since restarted keeps the file open and "
            "writes nothing. Restart the capture AFTER Polaris is ready: "
            "./capture.sh rotate <dir>"
        )
    elif _POLARIS_SQL_MARKER not in polaris_tail:
        reasons.append(
            f"polaris.log is growing but carries no {_POLARIS_SQL_MARKER} lines "
            "— the logger is above DEBUG, so no SQL will ever be captured. "
            "./capture.sh preflight"
        )

    if not any(n.startswith("pg-") for n in grew):
        reasons.append("no PostgreSQL replica log grew. ./capture.sh preflight")
    elif not any(m in pg_tail for m in _PG_STATEMENT_MARKERS):
        reasons.append(
            "PostgreSQL is logging, but not statements — checkpoint chatter is "
            "not evidence. log_statement is almost certainly still 'none': "
            "`rotate` restarts the streams and does NOT re-enable it. "
            "Run: PGDUR=1 ./capture.sh pgon"
        )

    return (not reasons), reasons


# ----------------------------------------------------------------------
# the drive
# ----------------------------------------------------------------------
def drive(
    client_factory,
    identities,
    secret,
    ops_for,
    on_progress=None,
    progress_every=25,
    stop_after_auth_failures=None,
    tolerated_labels=None,
    clock=None,
):
    """Authenticate as every identity and issue its ops. Single-threaded.

    Single-threaded on purpose: upstream #761 (`InMemoryEntityCache`'s
    unsynchronised map) makes concurrency a variable this scan is not trying to
    measure, and a capture interleaved across threads is far harder to
    correlate on `mdc.requestId`.

    Args:
        client_factory: callable() -> a fresh `PolarisREST`, so each identity
            gets its own client rather than sharing a mutated `token`.
        identities: from `load_identities`.
        secret: the shared secret every seeded principal authenticates with.
        ops_for: callable(client, identity) -> the op list to drive for that
            identity. Usually a closure over the probe's authorized subset.
        on_progress: callable(done, total, result).
        stop_after_auth_failures: bail out after this many consecutive token
            failures. A wrong shared secret fails all 1,000 identically, and
            finding that out on identity 3 beats finding it out in 20 minutes.
        tolerated_labels: op labels whose non-2xx is EXPECTED and therefore not
            an error. Measured 2026-08-24: six of the thirteen GETs are
            service-scoped and 403 for an ordinary principal. A refused request
            still pays the full 7-statement authorization prelude -- Polaris
            has to resolve the grants to decide it is a 403 -- so driving a
            sample of them is evidence that the grantee lookup fires on the
            denial path too, rather than a claim read off the source. Their
            statuses are recorded; they just do not poison the error list.
        clock: injectable `time.monotonic` for tests.

    Returns:
        ScanResult.
    """
    import time

    clock = clock or time.monotonic
    t0 = clock()
    result = ScanResult(identities=len(identities))
    consecutive_auth_failures = 0

    for done, identity in enumerate(identities, start=1):
        client = client_factory()
        token, scope, detail = authenticate(client, identity, secret)
        result.requests += 1
        if not token:
            result.auth_failures.append((identity.index, scope, detail))
            consecutive_auth_failures += 1
            if (
                stop_after_auth_failures
                and consecutive_auth_failures >= stop_after_auth_failures
            ):
                result.skipped.extend(
                    (i.index, "aborted after repeated auth failures")
                    for i in identities[done:]
                )
                break
            continue

        consecutive_auth_failures = 0
        client.token = token
        result.authenticated += 1

        if identity.namespace is None:
            ns, why = resolve_namespace(client, identity)
            result.requests += 1
            #: Recorded under its OWN label, even though it is the same
            #: `GET /namespaces` the drive also issues. The capture will
            #: otherwise hold twice as many of that statement as of every
            #: other, and an unexplained 2x on one API is exactly the shape
            #: of a finding. Naming it here means the run JSON accounts for
            #: it instead of the report having to guess.
            result.statuses[(identity.index, NS_RESOLVE_LABEL)] = 200 if ns else 0
            if not ns:
                result.skipped.append((identity.index, why))
                continue
            identity.namespace = ns

        tolerated = set(tolerated_labels or ())
        for label, _surface, fn in ops_for(client, identity):
            try:
                r = fn(client)
                status = r.status_code
            except Exception as exc:  # noqa: BLE001
                status = 0
                result.errors.append((identity.index, label, f"{type(exc).__name__}"))
            else:
                if status >= 300 and label not in tolerated:
                    result.errors.append((identity.index, label, status))
            result.requests += 1
            result.statuses[(identity.index, label)] = status

        if on_progress and (done % progress_every == 0 or done == len(identities)):
            result.elapsed_s = clock() - t0
            on_progress(done, len(identities), result)

    result.elapsed_s = clock() - t0
    return result


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
def status_matrix(result, ops):
    """Per-op counts across every identity: {label: {status: n}}.

    The scan's own integrity check. An op that answered 200 for the probe
    identity and 403 for 999 others is not a latency result, it is a fixture
    fault, and it has to be visible before any plan shape is quoted.
    """
    matrix = {label: {} for label, _s, _f in ops}
    for (_idx, label), status in result.statuses.items():
        bucket = matrix.setdefault(label, {})
        bucket[status] = bucket.get(status, 0) + 1
    return matrix


def render_probe_table(statuses):
    """Markdown table of the pre-flight: which GETs an ordinary principal has.

    Renders the REFUSALS as prominently as the successes -- the 403s are the
    measurement here, not noise to be filtered out before the interesting part.
    """
    lines = [
        "| API | surface | status | authorized |",
        "| --- | --- | ---: | --- |",
    ]
    for s in statuses:
        lines.append(
            f"| `{s.label.strip()}` | {s.surface} | {s.status} | "
            f"{'yes' if s.ok else 'NO'} |"
        )
    ok = sum(1 for s in statuses if s.ok)
    lines.append("")
    lines.append(
        f"{ok} of {len(statuses)} GET operations are authorized for this "
        "identity; the rest are service-scoped and belong to root."
    )
    return "\n".join(lines)


def render_scan_report(result, ops, title="Privilege scan"):
    """Markdown: the drive's shape and every way it fell short.

    Deliberately leads with what did NOT work. A scan that authenticated 1,000
    identities and drove 7,000 requests is only evidence if the failures are
    zero or named -- an unreported 403 column silently removes an API from the
    distribution the whole exercise is about.
    """
    lines = [f"## {title}", "", result.summary(), ""]

    if result.auth_failures:
        lines += [
            f"### {len(result.auth_failures)} identities never authenticated",
            "",
            "| user | scope | detail |",
            "| ---: | --- | --- |",
        ]
        for idx, scope, detail in result.auth_failures[:20]:
            lines.append(f"| {idx} | `{scope}` | {detail} |")
        if len(result.auth_failures) > 20:
            lines.append(f"| … | | {len(result.auth_failures) - 20} more |")
        lines.append("")

    if result.skipped:
        lines += [f"### {len(result.skipped)} identities skipped", ""]
        for idx, why in result.skipped[:20]:
            lines.append(f"- user{idx}: {why}")
        if len(result.skipped) > 20:
            lines.append(f"- … {len(result.skipped) - 20} more")
        lines.append("")

    lines += ["### Per-API status distribution", ""]
    lines += ["| API | 2xx | other |", "| --- | ---: | --- |"]
    for label, buckets in status_matrix(result, ops).items():
        ok = sum(n for s, n in buckets.items() if 200 <= s < 300)
        other = ", ".join(
            f"{s}×{n}" for s, n in sorted(buckets.items()) if not 200 <= s < 300
        )
        lines.append(f"| `{label.strip()}` | {ok} | {other or '—'} |")
    return "\n".join(lines)
