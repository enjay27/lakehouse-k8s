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

import api_sweep
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

#: Bootstrapped by Polaris. Mirrors `polaris_seed.SERVICE_ADMIN_ROLE`; named
#: here too so `PROFILES` does not have to import the seeder for one string.
SERVICE_ADMIN_ROLE = "service_admin"

#: Label for the `GET /namespaces` call `drive()` makes to resolve a namespace,
#: kept distinct from the identical call the drive itself issues. See the note
#: in `drive()`.
NS_RESOLVE_LABEL = "GET  /namespaces [ns-resolve]"

#: Suffix marking a call the HARNESS made to prepare a drive, not an operation
#: the drive was measuring. Same idea as `NS_RESOLVE_LABEL`, generalised
#: because entity resolution adds four more per identity -- and they land on
#: paths that are ALSO real operations (`GET /namespaces/{ns}/tables` is both).
#:
#: Without this the capture holds roughly twice as many of those four as the
#: run JSON accounts for, and `query_profile.reconcile` reports a large
#: unexplained delta on ops that are not missing anything. Recorded under their
#: own labels so the run JSON accounts for them; folded back by the reconciler,
#: which prints the fold rather than hiding it.
ENTITY_RESOLVE_SUFFIX = " [entity-resolve]"

#: The op label each resolution call shares a path with.
RESOLVE_BASE_LABELS = {
    "table": "GET  /namespaces/{ns}/tables",
    "view": "GET  /namespaces/{ns}/views",
    "generic_table": "GET  /generic-tables",
    "policy": "GET  /policies",
}


@dataclass
class Profile:
    """A named identity tier: which principals, and which operations.

    The two tiers measure different things and must not be conflated:

    * **catalog-scoped** -- `user{N}_principal`, holding `owner_principal` on
      its OWN catalog and nothing at service level. Six of its thirteen
      operations 403. This is NOT "an unauthorized principal": 8,000 of its
      15,000 requests succeeded. It is the least-privileged tier that is still
      a real working identity.
    * **service-scoped** -- granted service-level access as well, so the whole
      29-operation surface should answer 2xx. Its probe is GATED on that: a
      suite named "fully authorized" that quietly contains 403s is the same
      error as a 403 in a column headed "ms".

    THE TRAP, and it is the reason this is a Profile and not a flag.
    `api_sweep.bind_identity` records that root resolves ~2 grant rows while an
    ordinary principal resolves 25 or 50 -- and that Seq Scan cost is FLAT in
    rows-owned while index-scan cost tracks rows RETURNED. So the identity's
    grant footprint barely moves the index-absent column and dominates the
    index-present one.

    A service-scoped principal granted service access and little else would
    therefore sit at a completely different point on that curve, and diffing
    its numbers against the catalog-scoped suite's would compare two volumes
    while appearing to compare two privilege levels. Hence `footprint_must_match`:
    measure both tiers with `api_sweep.identity_grant_footprint`, and claim
    comparability only when they agree.

    Root is disqualified for the same reason -- it is authorized for
    everything and resolves two rows, so a suite built on it would sweep the
    whole surface and report the least representative identity in the realm.
    """

    name: str
    prefix: str
    #: The `api_sweep` builder's NAME, not the function. So a profile stays a
    #: plain data record -- serialisable into the run JSON, printable in
    #: `--list-profiles` -- and the op list it names is resolved from
    #: `api_sweep`, which remains the single definition of the surface.
    operations: str
    description: str = ""
    footprint_must_match: str = None
    #: Resolve a table / view / policy / generic table per identity before
    #: driving. Only the 29-op profiles need it; the 13-op surface names no
    #: entity below the namespace.
    resolve_entities: bool = False

    #: OAuth scope to request, or None for the identity's OWN principal-role.
    #:
    #: THE BUG THIS FIXES (2026-08-31, and it silently defeated a whole
    #: fixture). A principal holding TWO principal-roles gets a token scoped to
    #: ONE of them. The `admin{N}` principals hold their own role plus
    #: `service_admin`, and the probe requested
    #: `PRINCIPAL_ROLE:admin1_principal_role` -- so service_admin's grants were
    #: never in scope, and the "fully authorized" profile refused EXACTLY the
    #: same nine operations as the catalog-scoped one. Identical output from
    #: two privilege levels is the shape of a scope bug, not a finding.
    #:
    #: `PRINCIPAL_ROLE:ALL` is NOT the answer: it is root's scope, and a
    #: non-root principal asking for it is handed a token with no effective
    #: role which then 403s everything (`polaris_test_utils`, and
    #: `authenticate`'s own docstring). A SPECIFIC assigned role is what works.
    scope: str = None

    def ops(self, fx):
        return getattr(api_sweep, self.operations)(fx)


#: The tiers. `catalog-scoped` reproduces the completed pass EXACTLY -- same
#: prefix, same 13 operations -- because `privscan-20260824-123408` is already
#: correlated against it and a denominator that moved underneath would make
#: that report describe nothing.
PROFILES = {
    "catalog-scoped": Profile(
        name="catalog-scoped",
        prefix="user",
        operations="read_operations",
        description="owner_principal on its own catalog; 6 of 13 ops 403",
    ),
    #: RENAMED 2026-08-31, when the premise behind "service-scoped" turned out
    #: to be wrong. The 1.3.0 management API has NO service-level grant type --
    #: `GrantResource` is catalog / namespace / table / view / policy, and
    #: `SERVICE_MANAGE_ACCESS` is in none of them. An `authz{N}` principal is
    #: therefore still CATALOG-scoped, however many entities it owns; calling
    #: it service-scoped would have named the fixture after a privilege level
    #: it cannot reach.
    "catalog-scoped-full": Profile(
        name="catalog-scoped-full",
        prefix="authz",
        operations="full_read_operations",
        description="catalog privileges + full entities; MEASURED 2026-08-31: "
        "21 of 29 authorized, 8 refused (the 6 service-level reads plus the two "
        "role-graph traversals that walk from a principal)",
        footprint_must_match="catalog-scoped",
        resolve_entities=True,
    ),
    #: The only identity that can answer the whole surface -- and the reason it
    #: is a SEPARATE fixture rather than a flag. `service_admin` gains one
    #: grant per catalog (measured: 1,006 at 1,000 catalogs), so these
    #: principals resolve a grant set that grows with the REALM rather than
    #: with their own privileges. Seq Scan cost is flat in rows-owned while
    #: index-scan cost tracks rows returned, so they sit at a different point
    #: on the curve entirely.
    #:
    #: `footprint_must_match` is deliberately None: there is nothing to match,
    #: and pretending otherwise would invite the diff this whole distinction
    #: exists to prevent.
    "service-admin": Profile(
        name="service-admin",
        prefix="admin",
        operations="full_read_operations",
        description="member of service_admin; MEASURED 2026-08-31: 26 of 29 "
        "authorized — every management read, but NOT credential vending — and "
        "~1,100 grant rows, so NOT comparable to a catalog-scoped run",
        footprint_must_match=None,
        resolve_entities=True,
        scope=f"PRINCIPAL_ROLE:{SERVICE_ADMIN_ROLE}",
    ),
}

DEFAULT_PROFILE = "catalog-scoped"


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
    #: Entity-level reads need a target. Left None for a fixture seeded with
    #: `--no-tables`, which is not a defect in the identity -- it is the reason
    #: `loadTable` and friends are UNDRIVEABLE there, and the probe reports
    #: that as its own class rather than as a 404 finding.
    table: str = None
    view: str = None
    generic_table: str = None
    policy: str = None

    def fixture(self):
        """The `fx` mapping the `api_sweep` op builders expect."""
        return {
            "catalog": self.catalog,
            "namespace": self.namespace,
            "principal": self.principal,
            "principal_role": self.principal_role,
            "catalog_role": self.catalog_role,
            "table": self.table,
            "view": self.view,
            "generic_table": self.generic_table,
            "policy": self.policy,
        }


@dataclass
class OpStatus:
    """One API, driven once, with what actually came back."""

    label: str
    surface: str
    status: int
    detail: str = ""

    #: Sentinel statuses for the two non-HTTP outcomes. Negative so they can
    #: never collide with a real code, and named so a report never has to
    #: guess what a 0 meant.
    UNDRIVEABLE = -1
    RAISED = 0

    @property
    def ok(self):
        return 200 <= self.status < 300

    @property
    def undriveable(self):
        """The fixture had no entity to point this operation at.

        Not a refusal and not a server error. Keeping it separate is what stops
        `loadTable` against a `--no-tables` fixture from being reported as a
        Polaris 404.
        """
        return self.status == self.UNDRIVEABLE

    @property
    def unavailable(self):
        """Feature-flagged off on this deployment (generic tables, policies)."""
        return self.status in (404, 501) and not self.undriveable

    @property
    def malformed(self):
        """The server rejected the REQUEST, not the caller.

        A 400 is not an authorization outcome and must not sit in the same
        column as a 403. Measured 2026-08-31: `GET /v1/config` answered 400
        because the harness sent no `warehouse` parameter -- a bug in the op
        binding. Filed as "refused" it read as "ordinary principals may not
        read the catalog config", which is a claim about Polaris drawn from a
        mistake of ours.
        """
        return self.status in (400, 405, 415, 422)

    @property
    def verdict(self):
        if self.ok:
            return "authorized"
        if self.undriveable:
            return "undriveable"
        if self.unavailable:
            return "unavailable"
        if self.malformed:
            return "malformed"
        if self.status == self.RAISED:
            return "raised"
        return "refused"


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
    #: `{kind: {reason: count}}` for entity targets that could not be resolved.
    #: Aggregated rather than per-identity: 100 identities missing a policy for
    #: the same reason is ONE fact about the fixture, not 100 findings.
    unresolved: dict = field(default_factory=dict)
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


def resolve_entities(client, identity):
    """Fill in a table, view, policy and generic table this identity can see.

    ASKED FOR, NOT CONSTRUCTED. The seeder names them `tbl1`, `vw1`, `pol1`,
    `gt1`, so a format string would work today and be a hypothesis about the
    fixture rather than a fact about it. This repo has paid for that twice --
    `CLONE_ID_BASE` and the 25-privilege list -- and `load_identities` already
    reads client_ids from the metastore for exactly this reason.

    It also makes the harness work against a fixture built by any means, which
    is the property `privilege_scan` was written to have.

    A kind that resolves to nothing leaves its field None, and the ops needing
    it report UNDRIVEABLE -- the fixture has no such entity, which is a
    different fact from a refusal and is kept that way.

    Returns (missing, statuses): `{kind: reason}` for every kind that did not
    resolve, and `{kind: http_status}` for every call made -- the caller
    records the latter so the run JSON accounts for calls the capture will
    hold.
    """
    missing = {}
    statuses = {}
    ns = identity.namespace
    if not ns:
        return (
            {
                k: "no namespace resolved"
                for k in ("table", "view", "policy", "generic_table")
            },
            {},
        )

    def first(call, key, kind):
        try:
            r = call()
        except Exception as exc:  # noqa: BLE001
            missing[kind] = f"{type(exc).__name__}"
            statuses[kind] = 0
            return None
        statuses[kind] = r.status_code
        if r.status_code >= 300:
            #: 404/501 from the extensions means the FEATURE is off; a 403
            #: means this identity may not list them. Both leave the field
            #: None, and both are worth telling apart in the reason.
            missing[kind] = f"list [{r.status_code}]"
            return None
        try:
            body = r.json() or {}
        except Exception:  # noqa: BLE001
            missing[kind] = "response was not JSON"
            return None
        if key not in body:
            #: Say what the response ACTUALLY held. Reading the wrong key
            #: returns an empty list, which is indistinguishable from an empty
            #: namespace -- and on 2026-08-31 that cost a proposal to TRUNCATE
            #: the realm and rebuild a 55,004-row fixture, to fix what was a
            #: one-word mistake here. `ListPoliciesResponse` holds its entries
            #: under `identifiers`, not `policies`.
            missing[kind] = (
                f"response has no '{key}' key (keys: {sorted(body)}) — "
                "this is a PARSING fault, not an empty namespace"
            )
            return None
        items = body.get(key) or []
        if not items:
            missing[kind] = "namespace holds none"
            return None
        item = items[0]
        if isinstance(item, dict):
            #: Iceberg returns `{"namespace": [...], "name": "tbl1"}`;
            #: the Polaris extensions return `{"name": ...}`.
            return item.get("name")
        if isinstance(item, (list, tuple)):
            return item[-1]
        return item

    identity.table = first(
        lambda: client.list_tables(identity.catalog, ns), "identifiers", "table"
    )
    identity.view = first(
        lambda: client.list_views(identity.catalog, ns), "identifiers", "view"
    )
    identity.generic_table = first(
        lambda: client.list_generic_tables(identity.catalog, ns),
        "identifiers",
        "generic_table",
    )
    #: `identifiers`, per ListPoliciesResponse -- the same shape the Iceberg
    #: listings use, not a `policies` key. Confirmed against the 1.3.0 spec
    #: after the wrong guess made a full namespace read as an empty one.
    identity.policy = first(
        lambda: client.list_policies(identity.catalog, ns), "identifiers", "policy"
    )
    return missing, statuses


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
        except api_sweep.UndriveableOp as exc:
            #: Its own class, ahead of the generic handler. A fixture with no
            #: tables makes `loadTable` undriveable; calling that a server
            #: error would put a fixture gap in a column about Polaris.
            status, detail = OpStatus.UNDRIVEABLE, str(exc)
        except Exception as exc:  # noqa: BLE001
            status, detail = OpStatus.RAISED, f"{type(exc).__name__}: {exc}"
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
    resolve_entity_targets=False,
    auth_scope=None,
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
        auth_scope: OAuth scope for every identity, or None for each one's
            OWN principal-role. A principal holding two principal-roles gets a
            token scoped to ONE of them, so the `service_admin` tier needs its
            scope named or its extra role is simply not in the token.
        resolve_entity_targets: ask the API for a table / view / policy /
            generic table per identity before driving. Required by the 29-op
            profiles; the 13-op surface names no entity below the namespace.
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
        token, scope, detail = authenticate(client, identity, secret, scope=auth_scope)
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

        if resolve_entity_targets:
            #: Costs up to four list calls per identity, and buys the
            #: difference between "loadTable returned 404" and "this fixture
            #: has no table to load". Those are not the same finding and a
            #: report cannot tell them apart afterwards.
            gone, resolved_statuses = resolve_entities(client, identity)
            for kind, status in resolved_statuses.items():
                #: Under its OWN label, exactly as `NS_RESOLVE_LABEL` is, so the
                #: run JSON accounts for a call the capture will hold on a path
                #: that is also a real operation. Unaccounted, these show up
                #: later as an unexplained 2x on four ops that are not missing
                #: anything.
                label = RESOLVE_BASE_LABELS[kind] + ENTITY_RESOLVE_SUFFIX
                result.statuses[(identity.index, label)] = status
                result.requests += 1
            for kind, why in gone.items():
                result.unresolved.setdefault(kind, {})
                result.unresolved[kind][why] = result.unresolved[kind].get(why, 0) + 1

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
        "| API | surface | status | verdict |",
        "| --- | --- | ---: | --- |",
    ]
    for s in statuses:
        shown = "" if s.status < 0 else s.status
        why = ""
        if not s.ok and s.detail:
            #: The BODY, not just the code. A 400 that does not say what was
            #: wrong sends the reader back to the cluster to find out; this
            #: probe costs 29 calls and should answer that in its own output.
            why = " " + s.detail.replace("\n", " ").replace("|", "/")[:110]
        lines.append(
            f"| `{s.label.strip()}` | {s.surface} | {shown} | {s.verdict}{why} |"
        )
    counts = {}
    for s in statuses:
        counts[s.verdict] = counts.get(s.verdict, 0) + 1
    lines.append("")
    lines.append(
        f"{counts.get('authorized', 0)} of {len(statuses)} operations authorized"
        + "".join(f", {n} {v}" for v, n in sorted(counts.items()) if v != "authorized")
        + "."
    )
    if counts.get("malformed"):
        lines.append("")
        lines.append(
            "**malformed** = the server rejected the REQUEST (400/422), which "
            "is a harness fault until proven otherwise — NOT an authorization "
            "outcome. Fix the op binding before reading anything into that row."
        )
    if counts.get("undriveable"):
        lines.append("")
        lines.append(
            "**undriveable** = the FIXTURE has no such entity, not that the "
            "server refused. Seed the missing entities before reading anything "
            "into that row."
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


# ----------------------------------------------------------------------
# across tiers: what the WHOLE suite reaches, which is not what any one does
# ----------------------------------------------------------------------
#: Best-to-worst. A union takes the best verdict any tier achieved for an
#: operation, because "some identity can drive this" is the question coverage
#: asks -- not "every identity can".
_VERDICT_RANK = (
    "authorized",
    "undriveable",
    "unavailable",
    "malformed",
    "refused",
    "raised",
)


def union_verdicts(probes):
    """Merge probe results across identity tiers.

    THE FINDING THIS EXISTS FOR (measured 2026-08-31). The two tiers are
    COMPLEMENTARY, not nested, and neither alone reaches the whole surface:

      * `catalog-scoped-full` drives 20 of 29 -- it cannot read the service
        surface, but it CAN vend storage credentials.
      * `service-admin` drives 26 of 29 -- every management read, and it CANNOT
        vend credentials. Its 403 names its own roles:
        `activated grants via '[service_admin, catalog_admin]'`.

    So administrative authority and data authority are separate in Polaris, and
    the admin tier is not a superset of the ordinary one. A report quoting
    either tier's count as "the coverage" understates the suite by the other
    tier's exclusive operations -- which is why this is computed rather than
    left to a reader to intersect two tables by eye.

    Args:
        probes: `{tier_name: probe_dict}` as written by `--probe`.

    Returns:
        {label: {"verdict", "tiers", "best_tier"}} plus the summary keys
        `covered`, `uncovered` and `exclusive`.
    """
    rank = {v: i for i, v in enumerate(_VERDICT_RANK)}
    merged = {}
    for tier, probe in probes.items():
        verdicts = probe.get("verdicts") or {}
        if not verdicts:
            #: An older probe recorded only `authorized` + `refused`. Recover
            #: what it does carry rather than dropping the tier silently.
            verdicts = {label: "authorized" for label in probe.get("authorized") or []}
            verdicts.update(
                {label: "refused" for label in (probe.get("refused") or {})}
            )
        for label, verdict in verdicts.items():
            slot = merged.setdefault(
                label, {"verdict": None, "tiers": {}, "best_tier": None}
            )
            slot["tiers"][tier] = verdict
            if slot["verdict"] is None or rank.get(verdict, 99) < rank.get(
                slot["verdict"], 99
            ):
                slot["verdict"] = verdict
                slot["best_tier"] = tier

    covered = sorted(l for l, v in merged.items() if v["verdict"] == "authorized")
    uncovered = sorted(l for l, v in merged.items() if v["verdict"] != "authorized")
    exclusive = {}
    for label, v in merged.items():
        if v["verdict"] != "authorized":
            continue
        winners = [t for t, x in v["tiers"].items() if x == "authorized"]
        if len(winners) == 1 and len(v["tiers"]) > 1:
            exclusive.setdefault(winners[0], []).append(label)
    return {
        "operations": merged,
        "covered": covered,
        "uncovered": uncovered,
        "exclusive": {k: sorted(v) for k, v in exclusive.items()},
        "total": len(merged),
    }


def render_union(union, probes=None):
    """Per-tier counts, the union, and what only one tier can reach."""
    lines = []
    if probes:
        lines += ["| tier | authorized | of | scope |", "|---|---:|---:|---|"]
        for tier, probe in sorted(probes.items()):
            v = probe.get("verdicts") or {}
            ok = sum(1 for x in v.values() if x == "authorized") or len(
                probe.get("authorized") or []
            )
            lines.append(
                f"| `{tier}` | {ok} | {len(v) or '—'} | `{probe.get('scope', '—')}` |"
            )
        lines.append("")
    lines.append(
        f"**Union: {len(union['covered'])} of {union['total']}** operations are "
        "reachable by at least one identity tier."
    )
    if union["exclusive"]:
        lines.append("")
        lines.append(
            "Neither tier is a superset of the other — these are reachable by "
            "ONE tier only:"
        )
        for tier, labels in sorted(union["exclusive"].items()):
            for label in labels:
                lines.append(f"  - `{label.strip()}` — only `{tier}`")
    if union["uncovered"]:
        lines.append("")
        lines.append(
            f"**{len(union['uncovered'])} operations no tier reached.** These "
            "are absent from every figure any report can produce:"
        )
        for label in union["uncovered"]:
            tiers = union["operations"][label]["tiers"]
            why = ", ".join(f"{t}: {v}" for t, v in sorted(tiers.items()))
            lines.append(f"  - `{label.strip()}` — {why}")
    return "\n".join(lines)
