"""
polaris_seed.py
===============
Build (and tear down) the large synthetic fixture the index audit needs.

WHY THIS EXISTS
---------------
An `EXPLAIN` against a near-empty metastore proves nothing: PostgreSQL picks a
sequential scan on a small table because that genuinely IS the cheaper plan.
To tell whether an access path is missing, the tables have to be big enough
that the planner's choice carries information.

FIXTURE SHAPE (as specified)
----------------------------
    1,000 x  user{N}_principal
    1,000 x  user{N}_principal_role      assigned to user{N}_principal
    1,000 x  user{N}_catalog
               +-- catalog role `owner_principal`
               |     assigned to user{N}_principal_role
               |     granted the FULL explicit privilege set on the catalog
               +-- 2 namespaces
                     +-- 5 tables each  (10 tables per catalog)

    ~= 16,000 entities rows and ~16,000 grant_records rows at the default
    privilege set. The grant_records volume is the point: it is the table
    whose grantee access path is under suspicion, and a realm with thousands
    of grants is where a missing index stops being theoretical.

COST — READ BEFORE RUNNING
--------------------------
    * ~17,000-33,000 API calls. At ~50 ms each that is 15-30 minutes, more if
      table creation writes metadata.json synchronously.
    * ~10,000 metadata objects in MinIO. Check disk headroom first.
    * The realm is left holding ~16,000 entities. `teardown()` must be run,
      and it works from the LEDGER rather than a name sweep, because at this
      scale a half-finished manual cleanup is genuinely unpleasant.

RESUMABLE AND IDEMPOTENT
------------------------
Every completed user index is appended to a JSON ledger. Re-running `seed()`
with the same ledger skips finished users and picks up where it stopped, so an
interrupted run costs minutes rather than the whole fixture. Individual create
calls tolerate 409 (already exists), so a partially-completed user is repaired
rather than duplicated.

LOCAL ONLY
----------
`require_local()` refuses to run against any non-local host, and is called by
both `seed()` and `teardown()`. This fixture must never touch a shared realm —
16,000 entities and a teardown pass would be a serious incident on a company
cluster.
"""

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field

# ----------------------------------------------------------------------
# privileges
# ----------------------------------------------------------------------

#: The full explicit catalog-scoped privilege set granted to each owner role.
#: Granting all of them individually (rather than one coarse master) is
#: deliberate: it multiplies grant_records volume by ~16x, and grant_records is
#: the table under audit.
#:
#: Names are validated by the server. Any it rejects is REPORTED rather than
#: raised — an unknown name should not abort a 30-minute seed — and shows up in
#: `SeedResult.invalid_privileges`. Check that field before trusting the
#: expected row count.
FULL_CATALOG_PRIVILEGES = [
    "CATALOG_MANAGE_ACCESS",
    "CATALOG_MANAGE_CONTENT",
    "CATALOG_MANAGE_METADATA",
    "CATALOG_READ_PROPERTIES",
    "CATALOG_WRITE_PROPERTIES",
    "NAMESPACE_CREATE",
    "NAMESPACE_DROP",
    "NAMESPACE_LIST",
    "NAMESPACE_READ_PROPERTIES",
    "NAMESPACE_WRITE_PROPERTIES",
    "NAMESPACE_FULL_METADATA",
    "TABLE_CREATE",
    "TABLE_DROP",
    "TABLE_LIST",
    "TABLE_READ_PROPERTIES",
    "TABLE_WRITE_PROPERTIES",
    "TABLE_READ_DATA",
    "TABLE_WRITE_DATA",
    "TABLE_FULL_METADATA",
    "VIEW_CREATE",
    "VIEW_DROP",
    "VIEW_LIST",
    "VIEW_READ_PROPERTIES",
    "VIEW_WRITE_PROPERTIES",
    "VIEW_FULL_METADATA",
]

#: Minimal single-grant alternative, for a fast seed when grant volume is not
#: the object of study. Measured 2026-07-02: CATALOG_MANAGE_CONTENT authorizes
#: all 11 tested actions, so this is functionally equivalent for access — it
#: just produces ~16x fewer grant_records rows.
COARSE_CATALOG_PRIVILEGES = ["CATALOG_MANAGE_CONTENT"]

OWNER_ROLE_NAME = "owner_principal"

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"}


# ----------------------------------------------------------------------
# guards
# ----------------------------------------------------------------------
def require_local(url, extra_allowed=()):
    """Refuse to operate against anything but a local Polaris.

    Args:
        url: the Polaris base URL being targeted.
        extra_allowed: additional host substrings to permit — an OrbStack VM
            IP such as "192.168.139.2" is local in practice but not by name,
            so it has to be named explicitly rather than pattern-matched.
            Requiring the caller to spell it out is the point.

    Raises:
        AssertionError: if the host is not recognisably local.
    """
    host = (url or "").split("//")[-1].split("/")[0].split(":")[0]
    allowed = set(_LOCAL_HOSTS) | set(extra_allowed)
    assert host in allowed or host.startswith("192.168."), (
        f"polaris_seed refuses to run against host {host!r}. This fixture "
        f"creates ~16,000 entities and its teardown deletes them — it is "
        f"local-only by design. Allowed: {sorted(allowed)} or 192.168.*. "
        f"Pass extra_allowed=(...) only for a host you are certain is your "
        f"own machine."
    )
    return True


# ----------------------------------------------------------------------
# spec / results
# ----------------------------------------------------------------------
@dataclass
class SeedSpec:
    """Shape of the fixture to build.

    Attributes:
        n_users: number of user{N} sets.
        namespaces_per_catalog / tables_per_namespace: tree under each catalog.
        prefix: name prefix for every created entity. Everything the seeder
            makes starts with this, so a stray-entity sweep has something
            unambiguous to match.
        privileges: privilege names granted to each owner role.
        start_index: first user index (1-based), for extending an existing seed.
        create_tables: set False for a metadata-only seed — builds principals,
            roles, catalogs, namespaces and grants but no tables. Roughly 10x
            faster and still populates grant_records fully, which is enough for
            the grantee-index hypothesis.
    """

    n_users: int = 1000
    namespaces_per_catalog: int = 2
    tables_per_namespace: int = 5
    prefix: str = "user"
    privileges: list = field(default_factory=lambda: list(FULL_CATALOG_PRIVILEGES))
    start_index: int = 1
    create_tables: bool = True

    def names(self, i):
        """Entity names for user index `i`."""
        return {
            "principal": f"{self.prefix}{i}_principal",
            "principal_role": f"{self.prefix}{i}_principal_role",
            "catalog": f"{self.prefix}{i}_catalog",
            "catalog_role": OWNER_ROLE_NAME,
            "namespaces": [f"ns{j}" for j in range(1, self.namespaces_per_catalog + 1)],
            "tables": [f"tbl{k}" for k in range(1, self.tables_per_namespace + 1)],
        }

    def expected_counts(self):
        """Projected entity and grant counts, for a pre-flight sanity check."""
        n = self.n_users
        ns = n * self.namespaces_per_catalog
        tbl = ns * self.tables_per_namespace if self.create_tables else 0
        return {
            "principals": n,
            "principal_roles": n,
            "catalogs": n,
            "catalog_roles": n,
            "namespaces": ns,
            "tables": tbl,
            "entities_total": n * 4 + ns + tbl,
            "grant_records": n * len(self.privileges),
        }


@dataclass
class SeedResult:
    """Outcome of a seed run."""

    completed_users: int = 0
    skipped_users: int = 0
    failed_users: list = field(default_factory=list)
    invalid_privileges: list = field(default_factory=list)
    elapsed_s: float = 0.0
    calls: int = 0
    lag_recovered: list = field(default_factory=list)
    repaired_catalogs: list = field(default_factory=list)

    def summary(self):
        rec = ""
        if self.lag_recovered:
            rec = f" lag_recovered={len(self.lag_recovered)}"
        if self.repaired_catalogs:
            rec += f" repaired_catalogs={len(self.repaired_catalogs)}"
        return (
            f"seeded={self.completed_users} skipped={self.skipped_users} "
            f"failed={len(self.failed_users)} calls={self.calls} "
            f"elapsed={self.elapsed_s:.1f}s "
            f"invalid_privileges={sorted(set(self.invalid_privileges))}{rec}"
        )


# ----------------------------------------------------------------------
# ledger
# ----------------------------------------------------------------------
class Ledger:
    """Records what has been created, so a run is resumable and teardown exact.

    Deliberately a plain JSON file flushed after every user: a crash costs at
    most one user's worth of progress, and teardown works from what was
    actually recorded rather than from a naming convention. At 16,000 entities
    a name sweep is not a safe cleanup strategy — a typo in a prefix either
    misses entities or deletes something it shouldn't.
    """

    def __init__(self, path):
        self.path = path
        self.data = {"spec": None, "users": [], "created_at": time.time()}
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    self.data = json.load(fh)
            except (ValueError, OSError):
                # A corrupt ledger must not silently look like "nothing done".
                raise RuntimeError(
                    f"Ledger at {path} exists but could not be read. Move it "
                    "aside and re-seed, or repair it — proceeding would risk "
                    "leaving orphaned entities with no record of them."
                )

    @property
    def done_users(self):
        return set(self.data.get("users", []))

    def set_spec(self, spec):
        self.data["spec"] = asdict(spec)
        self.flush()

    def mark_user(self, i):
        if i not in self.done_users:
            self.data.setdefault("users", []).append(i)
            self.flush()

    def drop_user(self, i):
        self.data["users"] = [u for u in self.data.get("users", []) if u != i]
        self.flush()

    def flush(self):
        if not self.path:
            return
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)
        os.replace(tmp, self.path)  # atomic — never a half-written ledger

    def spec(self):
        d = self.data.get("spec")
        return SeedSpec(**d) if d else None


# ----------------------------------------------------------------------
# seeding
# ----------------------------------------------------------------------
def _ok(resp, *accept):
    """True when a response is success or one of the tolerated statuses."""
    return resp.status_code < 300 or resp.status_code in accept


# A write that violated a PRIMARY KEY or unique constraint did not fail --
# it already happened. Polaris has no upsert path (see the note in
# `polaris_rest.grant_privilege`: the grant PUT is a bare INSERT), so a
# retried write that committed the first time comes back as 23505 wrapped in
# a 500. Retrying that can never succeed, and treating it as failure loses a
# user whose data is fully present.
_DUPLICATE = re.compile(
    r"duplicate key value"
    r"|violates unique constraint"
    r"|already exists"
    r"|\b23505\b",
    re.I,
)


def _is_duplicate(resp):
    """True when a non-2xx response means 'this was already written'."""
    try:
        return bool(_DUPLICATE.search(resp.text or ""))
    except Exception:  # noqa: BLE001
        return False


def _attempt(call, what, result, exists=None, accept=(409,), retries=6):
    """Issue one seeding call, tolerating read-after-write lag on PG-HA.

    THE PROBLEM THIS SOLVES
    -----------------------
    Under load, Polaris on a replicated PostgreSQL rejects operations whose
    prerequisite was written milliseconds earlier: the write lands on the
    primary, the confirming read is load-balanced onto a replica that has not
    caught up, and the miss surfaces as one of THREE different statuses
    depending on which code path handles it:

        500  the write itself committed, but the read-back failed
             (`create_namespace`, `create_catalog`)
        403  authorization resolved the just-created catalog's grants from a
             lagging replica, found none, and called it Forbidden
             (`create_catalog_role`)
        404  the just-created entity is not visible yet
             (`assign_principal_role`, and the case `polaris_rest.
             grant_privilege` already retries around)

    All three are the same fault. Handling only 5xx -- which is what this
    module did first -- left 403 and 404 to fail 29 users out of 1,000.

    Two different remedies are needed, because the states differ:
      * 5xx: the entity usually EXISTS already. Re-issuing is safe (409 is
        tolerated) and `exists` settles it without another write.
      * 403/404: the operation did NOT happen. It must be re-issued once the
        replica catches up.
    Retrying the call covers both, so that is what this does.

    A 4xx that is NOT 403/404 is a genuine client error -- a bad privilege
    name, a malformed payload -- and returns immediately. Retrying those would
    turn a real bug into a slow one.

    Args:
        call: zero-arg callable issuing the request, returning a Response.
        what: label recorded against any recovery.
        result: SeedResult, for call counting and recovery recording.
        exists: optional zero-arg bool callable, checked after a 5xx.
        accept: extra tolerated statuses (409 for idempotent re-creates).
        retries: attempts after the first (~0.25s doubling to 2s, ~8s total).

    Returns:
        (ok: bool, resp: Response) -- resp is the LAST response seen.
    """
    delay = 0.25
    resp = None
    first_fail = None  # the status that TRIGGERED the retry, not the
    # 201 that ended it -- the transient code is the
    # diagnostic signal worth keeping.
    for attempt in range(retries + 1):
        resp = call()
        result.calls += 1
        if _ok(resp, *accept):
            if attempt:
                result.lag_recovered.append(
                    {"what": what, "status": first_fail, "retries": attempt}
                )
            return True, resp

        # Duplicate key => the write landed (very likely on OUR own earlier
        # attempt). Success, and retrying would loop forever against the PK.
        if _is_duplicate(resp):
            result.lag_recovered.append(
                {
                    "what": what,
                    "status": resp.status_code,
                    "retries": attempt,
                    "reason": "duplicate",
                }
            )
            return True, resp

        if first_fail is None:
            first_fail = resp.status_code

        # Genuine client error: do not retry.
        if resp.status_code < 500 and resp.status_code not in (403, 404):
            return False, resp

        # 5xx often means "committed, but I could not read it back".
        if resp.status_code >= 500 and exists is not None:
            try:
                if exists():
                    result.lag_recovered.append(
                        {"what": what, "status": resp.status_code, "retries": attempt}
                    )
                    return True, resp
            except Exception:  # noqa: BLE001 -- the check can hit the lag too
                pass

        if attempt < retries:
            time.sleep(delay)
            delay = min(delay * 2, 2.0)
    return False, resp


def _catalog_is_complete(pc, catalog):
    """True only if the catalog is USABLE, not merely present.

    Creating a catalog is two writes: the entity, and the bootstrap of its
    `catalog_admin` role plus the grants that make the creator an admin of it.
    Under load the first commits and the second does not, leaving a catalog
    that answers GET /catalogs/{name} with 200 -- correct storage config,
    entityVersion 1, everything -- while `list_catalog_roles` returns 403
    because the caller has no grant on it. Nothing can then be created inside
    it, permanently: `create_catalog_role` 403s forever, and no retry helps
    because there is no lag to wait out.

    "Does the entity exist" was the check this module used after a 5xx, and it
    is what let those half-created catalogs be recorded as successes.
    """
    r = pc.get_catalog(catalog)
    if r.status_code >= 300:
        return False
    r = pc.list_catalog_roles(catalog)
    if r.status_code >= 300:
        # 403 here IS the signature: the entity exists but carries no grants.
        return False
    try:
        roles = [x.get("name") for x in r.json().get("roles", [])]
    except Exception:  # noqa: BLE001
        return False
    return "catalog_admin" in roles


def _ensure_catalog(pc, catalog, bucket, minio_endpoint, result, attempts=3):
    """Create the catalog, and guarantee it is administrable before returning.

    A half-created catalog cannot be repaired in place -- there is no endpoint
    to bootstrap a missing catalog_admin role, and the caller has no grant that
    would let it use one anyway. The only remedy is to delete and recreate.

    Raises:
        RuntimeError if the catalog cannot be made complete.
    """
    for attempt in range(attempts):
        if _catalog_is_complete(pc, catalog):
            return

        r = pc.get_catalog(catalog)
        if r.status_code < 300:
            # Present but incomplete -- remove it so the recreate is clean.
            d = pc.delete_catalog(catalog, purge=True)
            result.calls += 1
            if d.status_code >= 300 and d.status_code != 404:
                raise RuntimeError(
                    f"catalog {catalog} is half-created (entity present, no "
                    f"catalog_admin) and delete returned {d.status_code}: "
                    f"{d.text[:160]}. It cannot be repaired over REST -- remove "
                    f"the row directly in PostgreSQL, or drop the realm."
                )
            result.repaired_catalogs.append(catalog)

        c = pc.create_catalog(catalog, bucket=bucket, minio_endpoint=minio_endpoint)
        result.calls += 1
        if not _ok(c, 409) and not _is_duplicate(c):
            if attempt == attempts - 1:
                raise RuntimeError(f"create_catalog {c.status_code}: {c.text[:200]}")
            time.sleep(0.5 * (attempt + 1))
            continue
        # Give the grant bootstrap a moment to become visible before judging it.
        time.sleep(0.4)

    if not _catalog_is_complete(pc, catalog):
        raise RuntimeError(
            f"catalog {catalog} still has no catalog_admin after {attempts} "
            "create attempts"
        )


def seed_user(pc, ic, spec, i, result, bucket=None, minio_endpoint=None):
    """Create one complete user{i} set. Idempotent -- 409s are tolerated.

    Order matters: catalog before catalog-role, catalog-role and principal-role
    before their assignment, and grants last, because the role must be visible
    before it can be granted to. Every step goes through `_attempt`, which
    absorbs the PG-HA read-after-write lag described there.

    Returns:
        True on success; on failure the user index is appended to
        `result.failed_users` and False is returned.
    """
    n = spec.names(i)

    def step(call, what, exists=None):
        ok, r = _attempt(call, what, result, exists=exists)
        if not ok:
            raise RuntimeError(f"{what} {r.status_code}: {r.text[:200]}")
        return r

    try:
        step(
            lambda: pc.create_principal(n["principal"]),
            "create_principal",
            lambda: pc.get_principal(n["principal"]).status_code < 300,
        )

        step(
            lambda: pc.create_principal_role(n["principal_role"]),
            "create_principal_role",
            lambda: pc.get_principal_role(n["principal_role"]).status_code < 300,
        )

        step(
            lambda: pc.assign_principal_role_to_principal(
                n["principal"], n["principal_role"]
            ),
            "assign_principal_role",
        )

        # NOT a plain `step`: existence is not sufficient evidence that a
        # catalog was created properly. See _ensure_catalog.
        _ensure_catalog(pc, n["catalog"], bucket, minio_endpoint, result)

        step(
            lambda: pc.create_catalog_role(n["catalog"], n["catalog_role"]),
            "create_catalog_role",
            lambda: any(
                x.get("name") == n["catalog_role"]
                for x in pc.list_catalog_roles(n["catalog"]).json().get("roles", [])
            ),
        )

        step(
            lambda: pc.assign_catalog_role_to_principal_role(
                n["catalog"], n["principal_role"], n["catalog_role"]
            ),
            "assign_catalog_role",
        )

        for priv in spec.privileges:
            ok, r = _attempt(
                lambda priv=priv: pc.grant_privilege(
                    n["catalog"], n["catalog_role"], priv
                ),
                f"grant_privilege {priv}",
                result,
            )
            if not ok:
                # A rejected privilege NAME is data, not a fatal error -- record
                # it and keep going rather than losing the whole run.
                result.invalid_privileges.append(priv)

        for ns in n["namespaces"]:
            step(
                lambda ns=ns: ic.create_namespace(n["catalog"], ns),
                f"create_namespace {ns}",
                lambda ns=ns: ic.namespace_exists(n["catalog"], ns),
            )

            if not spec.create_tables:
                continue
            for tbl in n["tables"]:
                step(
                    lambda ns=ns, tbl=tbl: ic.create_table(
                        n["catalog"], ns, _table_payload(tbl)
                    ),
                    f"create_table {ns}.{tbl}",
                    lambda ns=ns, tbl=tbl: ic.table_exists(n["catalog"], ns, tbl),
                )
        return True
    except Exception as exc:  # noqa: BLE001 -- one bad user must not kill the seed
        result.failed_users.append(
            {"index": i, "error": f"{type(exc).__name__}: {exc}"}
        )
        return False


def _table_payload(name):
    """Minimal two-column Iceberg table payload.

    Kept deliberately small: the fixture exists to create ROW COUNT in the
    metastore, not to exercise wide schemas. Schema width is a separate sweep
    (it drives metadata.json size, not entity count).
    """
    return {
        "name": name,
        "schema": {
            "type": "struct",
            "schema-id": 0,
            "fields": [
                {"id": 1, "name": "id", "required": True, "type": "long"},
                {"id": 2, "name": "val", "required": False, "type": "string"},
            ],
        },
    }


def seed(
    pc,
    ic,
    spec=None,
    ledger_path="seed_ledger.json",
    bucket=None,
    minio_endpoint=None,
    progress_every=25,
    on_progress=None,
    extra_allowed_hosts=(),
):
    """Build the fixture. Resumable — re-run with the same ledger to continue.

    Args:
        pc: a `polaris_rest.PolarisREST` with a root token.
        ic: an `iceberg_rest.IcebergREST` with a root token.
        spec: a `SeedSpec`. Defaults to the full 1,000-user spec.
        ledger_path: JSON ledger. Its directory must be gitignored — it names
            every created entity.
        bucket / minio_endpoint: passed to `create_catalog` for storage config.
        progress_every: emit a progress callback every N users.
        on_progress: callable(done, total, result) for notebook output.
        extra_allowed_hosts: passed to `require_local`.

    Returns:
        SeedResult.
    """
    # Order matters: the safety guard runs FIRST. Both checks raise before any
    # work happens, so ordering cannot change what gets written -- but it does
    # change which mistake the caller is told about, and pointing this at a
    # shared company cluster is the more dangerous one. Validating arguments
    # first meant a seed() aimed at dev/prod with an incomplete storage config
    # reported the missing bucket, saying nothing about the wrong host.
    require_local(pc.base_url, extra_allowed_hosts)

    # Fail once, before any work, rather than once per user. A missing storage
    # config is a caller mistake, not a per-user failure, and reporting it 1,000
    # times buries it.
    if not bucket or not minio_endpoint:
        raise ValueError(
            "seed() requires bucket and minio_endpoint even when "
            "spec.create_tables is False: every catalog needs a storage config. "
            f"got bucket={bucket!r} minio_endpoint={minio_endpoint!r}"
        )

    spec = spec or SeedSpec()

    ledger = Ledger(ledger_path)
    if ledger.spec() is None:
        ledger.set_spec(spec)

    result = SeedResult()
    t0 = time.time()
    done = ledger.done_users
    total = spec.n_users
    indices = range(spec.start_index, spec.start_index + spec.n_users)

    for count, i in enumerate(indices, start=1):
        if i in done:
            result.skipped_users += 1
        elif seed_user(pc, ic, spec, i, result, bucket, minio_endpoint):
            ledger.mark_user(i)
            result.completed_users += 1
        if on_progress and (count % progress_every == 0 or count == total):
            result.elapsed_s = time.time() - t0
            on_progress(count, total, result)

    result.elapsed_s = time.time() - t0
    return result


# ----------------------------------------------------------------------
# teardown
# ----------------------------------------------------------------------
def teardown_user(pc, spec, i, result):
    """Delete one user{i} set, innermost first. Tolerates already-absent (404).

    Deletion order is the reverse of creation: the catalog is dropped with
    purge (which removes its namespaces and tables), then the catalog role goes
    with it, then the principal role, then the principal.
    """
    n = spec.names(i)
    errors = []
    for label, call in (
        ("catalog", lambda: pc.delete_catalog(n["catalog"], purge=True)),
        ("principal_role", lambda: pc.delete_principal_role(n["principal_role"])),
        ("principal", lambda: pc.delete_principal(n["principal"])),
    ):
        try:
            r = call()
            result.calls += 1
            if not _ok(r, 404):
                errors.append(f"{label}:{r.status_code}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}:{type(exc).__name__}")
    if errors:
        result.failed_users.append({"index": i, "error": ",".join(errors)})
        return False
    return True


def teardown(
    pc,
    ledger_path="seed_ledger.json",
    spec=None,
    progress_every=25,
    on_progress=None,
    extra_allowed_hosts=(),
    keep_ledger=False,
):
    """Delete everything the ledger records, then clear it.

    Works from the LEDGER, not from a name sweep — see `Ledger`. Users are
    removed from the ledger only after their deletion succeeds, so an
    interrupted teardown can simply be re-run and will resume.

    Args:
        keep_ledger: leave the ledger file in place after a clean teardown.
            Off by default so a completed teardown leaves no stale record.

    Returns:
        SeedResult, where `completed_users` counts users torn down.
    """
    require_local(pc.base_url, extra_allowed_hosts)
    ledger = Ledger(ledger_path)
    spec = spec or ledger.spec() or SeedSpec()

    result = SeedResult()
    t0 = time.time()
    users = sorted(ledger.done_users)
    total = len(users)

    for count, i in enumerate(users, start=1):
        if teardown_user(pc, spec, i, result):
            ledger.drop_user(i)
            result.completed_users += 1
        if on_progress and (count % progress_every == 0 or count == total):
            result.elapsed_s = time.time() - t0
            on_progress(count, total, result)

    result.elapsed_s = time.time() - t0
    if not result.failed_users and not keep_ledger and ledger_path:
        if os.path.exists(ledger_path):
            os.remove(ledger_path)
    return result


# ----------------------------------------------------------------------
# verification
# ----------------------------------------------------------------------
def verify_counts(conn, spec, schema="polaris_schema"):
    """Compare actual metastore row counts against the spec's projection.

    Counts straight from the metastore rather than through the API: the point
    of the fixture is table volume, so the metastore is the authority. A large
    shortfall means the seed did not finish — check `SeedResult.failed_users`
    before running an audit against it, or the audit will be measuring a
    smaller table than intended and may report TOO_SMALL.

    Returns:
        dict: {expected, actual, entities_ok, grants_ok, notes}.
    """
    expected = spec.expected_counts()
    actual = {}
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.entities")  # noqa: S608
        actual["entities_total"] = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {schema}.grant_records")  # noqa: S608
        actual["grant_records"] = cur.fetchone()[0]

    notes = []
    entities_ok = actual["entities_total"] >= expected["entities_total"] * 0.95
    grants_ok = actual["grant_records"] >= expected["grant_records"] * 0.95
    if not entities_ok:
        notes.append(
            f"entities: {actual['entities_total']} < expected "
            f"~{expected['entities_total']}. The seed did not complete — audit "
            "verdicts from this state may be TOO_SMALL or misleading."
        )
    if not grants_ok:
        notes.append(
            f"grant_records: {actual['grant_records']} < expected "
            f"~{expected['grant_records']}. Check SeedResult.invalid_privileges "
            "— rejected privilege names are the usual cause."
        )
    if not notes:
        notes.append("Row counts match the spec; the fixture is audit-ready.")
    return {
        "expected": expected,
        "actual": actual,
        "entities_ok": entities_ok,
        "grants_ok": grants_ok,
        "notes": notes,
    }


def find_strays(pc, prefix="user"):
    """List entities matching the seed prefix that the ledger does not know about.

    Backstop for a crashed run whose ledger was lost. Read-only — it reports,
    it does not delete, because deleting by prefix is exactly the unsafe
    operation the ledger exists to avoid.

    Returns:
        dict: {principals, principal_roles, catalogs} of matching names.
    """

    def _names(resp, key):
        if resp.status_code >= 300:
            return []
        body = resp.json() or {}
        items = body.get(key) or []
        out = []
        for it in items:
            name = it.get("name") if isinstance(it, dict) else it
            if name and str(name).startswith(prefix):
                out.append(name)
        return sorted(out)

    return {
        "principals": _names(pc.list_principals(), "principals"),
        "principal_roles": _names(pc.list_principal_roles(), "roles"),
        "catalogs": _names(pc.list_catalogs(), "catalogs"),
    }


# ---------------------------------------------------------------------------
# public aliases
# ---------------------------------------------------------------------------
# The notebooks build probe fixtures against the same cluster and hit the same
# read-after-write lag, so they need this logic too. Exposed under non-private
# names rather than having each notebook re-implement it slightly differently
# -- three subtly different retry policies is how a fixture bug becomes an
# audit finding.
call_with_lag_retry = _attempt
ensure_catalog = _ensure_catalog
