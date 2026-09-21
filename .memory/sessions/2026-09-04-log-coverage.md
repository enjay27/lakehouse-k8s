# 2026-09-04 — building the log-coverage harness, including the wrong turns

**What was asked:** read `local-k8s`'s `CLAUDE.md`, `MEMORY.md` and
`POLARIS-API-LOG-COVERAGE-NOTEBOOK.md`, then prepare the notebook task. Then: proceed.

**What was produced:** `log-coverage/PLAN-log-coverage.md` (commit `5002085`), then the harness
itself (commit `d3a1161`). The notebook has never been run — no cluster reach from a Cowork
session — so everything below about what the pipeline *decides* is measured and everything
about what VictoriaLogs *holds* is not.

---

## The thing that made the plan worth writing

The source plan's headline is one audit asymmetry: `POST /v1/principals` is dropped while its
DELETE is kept, so a principal is created invisibly and deleted visibly. It calls demonstrating
that "the most persuasive output this notebook can produce".

Working the deployed Lua over `api_surface.operations()` by hand gave **eight** dropped
operations, not one — and the two the plan does not name are worse than the one it does:

- **`POST /v1/principals/{p}/reset`** — a credential reset leaves no trace. A security event.
- **`POST /v1/{cat}/tables/rename`** and the view equivalent — the rename path carries no
  `/namespaces/{ns}/tables` segment, so it misses `KEEP_POST_PATTERNS` entirely.

Rule 5's own comment in `fb-values.yaml` says the drop was *aimed at the OAuth token endpoint*.
Nothing bounded it there. The finding is a **count**, not an asymmetry.

The hand-computed table was then verified end to end against the deployed filter, and came back
exactly as written. That is the only reason it is quoted as a number rather than as a worry.

---

## Wrong turns, in order

**1. The hand-computed table was the wrong artifact, and it took writing it to see that.**
`PLAN` §3 is a 46-row prediction typed out by hand. It is also precisely the kind of document
this pair of repos distrusts — `local-k8s/.memory/README.md`: *written is not live*. The fix
was to stop treating it as the expected column and make `log_coverage.Policy` extract
`polaris_noise_filter` from `fb-values.yaml` and run it under a real Lua interpreter, the same
mechanism `logging/scripts/test-polaris-filters.py` already uses. The hand table survives in
the plan as something to falsify, not as the oracle.

**2. Predicting from the operation TEMPLATE would have made load_table look like rule 7.**
`api_surface` abbreviates long paths — `/v1/{cat}/.../tables/{tbl}`. Rule 6 matches
`/namespaces/[^/]+/tables/[^/?]+`, and an ellipsis where the namespace segment should be does
not match it, so every deduplicated table read would have been predicted as an
always-stored rule-7 keep and the mismatch reported as a pipeline finding. Fixed by recording
`resp.request.url` — the URL actually issued — and predicting against that.

**3. Predicting each policy probe in its own interpreter gave the wrong expectation.**
Rule 6's dedup state spans the whole run. Cell 3 already reads `probe_tbl` once, so cell 5's
twenty reads are the second through twenty-first of the day and the honest expectation is
**zero**, not one. A per-probe prediction starts from a fresh interpreter, says one, and the
"mismatch" would have been reported as a finding about the pipeline when it was an artifact of
predicting in the wrong scope. Expectations are now computed once, across the whole run, in
issue order.

**4. Driving as the run's own principal is not free, and a 403 here would have looked like a
finding.** `%u` is the fallback correlation key, so the run wants its own principal. But
`polaris_test_utils.get_token` records that a non-root principal generally cannot request
`PRINCIPAL_ROLE:ALL` — it yields a token with no effective role and everything 403s. A 403
would have made the matrix report endpoints as "not callable" when they were merely
unauthorized: a fixture bug wearing a finding's clothes, which is the same shape as the
2026-09-01 "authorized" drive that was really a second unauthorized one. So
`elect_drive_identity` provisions the principal, **proves** it can do one management read and
one catalog read, and demotes to root loudly when it cannot.

**5. Two bugs the tests caught that review had not.** `coverage_rows` fell through
`driven or captured or spec` when an inventory entry was legitimately an empty dict and handed
`None` to `.get`. And the request-id slug stripped underscores, so `load_table` and
`load-table` were indistinguishable in an id. Both were found by tests written before the
notebook was assembled.

---

## Corrections to the source plan, and where they went

Four of its `[assumed]`s were settled **from this repo**, not by calling anything: both APIs on
8181, and the realm header name `Polaris-Realm`, are settled by `polaris_rest.py` driving this
cluster daily. Only the `Polaris-Request-Id` round-trip is genuinely open. The plan spends a
paragraph warning that 8182 is the Quarkus management interface and not the Polaris Management
API — that warning is right, and `local-k8s/CLAUDE.md`'s "Management port **8182**" is what
invites the confusion. One line there is worth fixing, separately.

Its §4 — *"do not hand-write the endpoint list, parse the two OpenAPI documents"* — has the
right instinct and names a mechanism that does not exist here: this Polaris serves no document
(measured 2026-08-31, every `/q/openapi*` and `/openapi*` empty). Kade's call was **both**:
vendor the 1.3.0 specs *and* keep `probe_api_surface.py`'s three-way verdict, and diff them.

And its §2.4 sample record carries `http_status` as a **string** while `fb-values.yaml` sets
`type_int_key` on that field. Both cannot be true of one deployment, and every LogsQL status
filter depends on the answer. Filed in `active-issues.md`; cell 0 settles it off a raw record.

---

## What could not be run, and what was done instead

No package index is reachable from a Cowork session, so `pytest`, `black` and `isort` could not
be installed; the `.venv` symlinks point at a macOS interpreter the mount cannot execute. The
suites were run under a **minimal pytest stand-in** written for the purpose — plain and yield
fixtures, fixtures depending on fixtures, function vs module scope, `raises`, `parametrize`.
111 passed, 0 failed, across the two modules changed and the two added. Other modules fail
under the stand-in on `capsys` and `monkeypatch`, which are its gaps.

`luatex` **is** present in the mount, which is the only reason the expected column could be
measured at all rather than merely written down. That was luck, and `load_policy` raises
`PolicyUnavailable` rather than degrading when it is absent — there is deliberately no Python
re-implementation to fall back on, because a port that agrees with itself is not evidence.

One operational note that keeps recurring: `git` in this mount leaves a `.git/index.lock` and
`HEAD.lock` it cannot unlink, and the delete-permission request was refused by the sandbox this
session. Renaming them aside (`mv .git/HEAD.lock .git/_stale/…`) works, because rename is
permitted where unlink is not. `.git/_stale/` can be deleted by hand.

---

## What the next session should do first

Run the notebook. In order: the two port-forwards, `./fetch_specs.sh`, then Restart & Run All.
Cell 1 decides whether the whole correlation design holds. Then `pytest && black . && isort .`,
which this session could not run, and finally re-scope `local-k8s` roadmap 4b from "the
create/delete asymmetry" to the number.

---

# Run 1, the same day: the harness found the repo's signature failure on its first pass

Kade ran all cells. The result was not a coverage matrix — it was a config finding.

**Nothing was dropped.** 20 identical table GETs stored 20 records. Three successful OAuth
token requests stored 3. Every `create_principal`, both renames, `update_namespace_properties`
and the credential reset stored. 0 of 34 expected drops dropped, while every "keep" rule
behaved perfectly.

That combination has exactly one explanation, and the git history confirms it rather than
merely allowing it: `logging/fb-values.yaml` gained `polaris_noise_filter` in `local-k8s`
commit **2120ed9 at 2026-09-03T08:26:18Z**; the shipper pod has been running since
**08:04:06Z** — 22 minutes earlier — from **60b94d9**, which carries `polaris_access_log` and
`record_modifier` and no noise filter. Parsed fields present, zero drops. No `helm upgrade`
since the policy was written.

**This is `local-k8s`'s signature failure, and the notebook caught it the only way it can be
caught: by asking the running system.** `local-k8s/CLAUDE.md` says it in as many words —
*never confirm a setting by reading the values file* — and the file's own header says the Lua
block is "new". The harness was built entirely against that file and the file was honest; what
was missing was anyone asking whether it had been applied.

The lesson has been made structural rather than remembered: **cell 0 now reads the running
ConfigMap and aborts** when it does not carry the policy, with the `helm upgrade` line in the
message. `lc.deployed_policy_status` compares whitespace-normalised text, so Helm's
re-indentation does not cry wolf, and it distinguishes "no filter at all" from "a different
filter than the file has".

## Three of run 1's findings were mine

Worth writing down because each looked exactly like a pipeline fault.

1. **The replay dedup keyed on `mdc.requestId`.** One API call produces MANY records that share
   a request id — measured in cell 1: a single `list_catalogs` yields **15**, its access-log
   line plus 14 DEBUG SQL lines. Keying on the request id collapsed 2,049 records to 122,
   capped every `stored` count at 1, reported **1,927 phantom duplicates** and made `app_lines`
   zero on every row. The key is the RECORD: `(hostName, sequence)`, with `sequence` being the
   JBoss log sequence number the pipeline keeps precisely so a gap is visible.
2. **The 403 case used a client that was never tagged.** `denied_ic` was not in the client list
   passed to `call_once`, so that request carried no `Polaris-Request-Id`, could not be found
   afterwards, and the matrix reported `EXPECTED STORED, ABSENT` — a harness gap wearing a
   finding's clothes, the same shape as the 2026-09-01 "authorized" drive that was really a
   second unauthorized one.
3. **The `http_status` type check was meaningless.** It reported "stored as string" and that
   said nothing: VictoriaLogs hands every field back as a JSON string on
   `/select/logsql/query` whatever it indexed. The question that matters is operational — does
   `http_status:>=400` match where `http_status:"404"` does — and it is now asked that way.

A fourth, smaller: the `events` lookup searched `public` and reported "no events table in this
metastore". Polaris creates its objects in `POLARIS_SCHEMA`.

## What run 1 settled anyway

- **`Polaris-Request-Id` round-trips.** The plan's one genuinely open `[assumed]`, closed in
  minute one exactly as intended. Correlation mode EXACT.
- **Latency, client-side**: 122 calls, median ~18 ms, slowest ~77 ms. The evidence for `%D`.
- **8 ERROR records, none with an `exception` object.** Not a verdict yet — the raw file has to
  be checked to separate "Polaris never logged the throwable" from "the pipeline dropped it".
- **`create_catalog_no_endpoint` no longer provokes a 500** on this cluster (201, then 200), so
  `error-cases/09` is stale and the stack-trace probe fell back to the drive's own two 500s —
  the known PG-HA read-after-write signature.
- **`mgmt.reset_principal_credentials` → 403 as root**, reproducing "admin is not a superset"
  from a completely different direction.

## Next

`helm upgrade` the shipper, then re-run. **Treat that upgrade as a change, not a fix**: it
switches on a filter that has never executed once, and `local-k8s` #F2 is the record of what
happens when configuration that never ran is enabled without reading it line by line against
the defaults it replaces.
