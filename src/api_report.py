"""Render a drive's records as a `doc-api-sql-matrix-*.md` report.

Extracted from cell 33 of `01_api_access_map.ipynb`, unchanged in format. The
format is load-bearing in a way a report's usually is not: `query_profile.
parse_api_statements` reads it back to build the EXPLAIN worklist, so renderer
and parser are two halves of one contract. `test_api_report` asserts the
round-trip rather than the bytes -- render, parse, and get the same statements
back -- because that is the property anything downstream actually depends on.

STATEMENTS ARE EMITTED IN FULL, IN FENCED BLOCKS. An earlier version put them
in table cells, and a markdown cell cannot hold a newline, so each statement was
flattened and cut at 180 characters -- which silently removed the WHERE clause
from exactly the long statements worth reading (the `grant_records` OR-delete,
the row-constructor IN). The report is the artifact people quote from and the
input the sweep replays; it must carry the whole statement.

Everything routes through the redacting record objects, never raw log text, so
no secret material can reach a committed document. A secret-table statement
arrives here already `<redacted>` and cannot be un-redacted.
"""

from datetime import datetime

#: Emitted when a record has no table or no verb to attribute. The parser
#: accepts it and refuses to replay the statement, which is the honest outcome
#: -- it is not a parse failure.
DASH = "—"


def _fmt_ms(v):
    return f"{v:.2f} ms" if v is not None else "no timing"


def render_empty_window(rec):
    """What to print when an API recorded NO statements.

    A row reading `0 statements · tables: —` is the least useful line this
    report can contain: it is equally consistent with an operation that issued
    no SQL, a capture that was not recording, and a parser that dropped the
    lines -- three faults with three different fixes. Three drives and most of
    a session went into deciding which, and the answer was in the raw window
    the whole time.

    So an empty row now carries the verdict, the fix, and the raw text it was
    read from. Nothing to re-derive.
    """
    from api_trace import diagnose_empty_window

    raw = getattr(rec, "raw_log", None)
    verdict, hint = diagnose_empty_window(raw or "")
    out = [
        "> **No SQL was captured for this operation.**",
        f"> Verdict: {verdict}.",
        f"> {hint}",
        "",
    ]
    if raw:
        out += [
            "<details><summary>raw Polaris log for this trace window "
            "(last 40 lines, each truncated)</summary>",
            "",
            "```",
            raw,
            "```",
            "",
            "</details>",
            "",
        ]
    else:
        out += [
            "_No raw window was retained — this record predates the fallback, "
            "or no Polaris stream was attached to the tracer._",
            "",
        ]
    return out


def render_statements(rec):
    """The per-statement blocks for one API record."""
    if not rec.sql:
        return render_empty_window(rec)
    out = []
    for s in rec.sql or []:
        #: Defensive, and it should now never fire: a statement with no text
        #: rendered as a heading over an EMPTY code block, which reads as a
        #: capture fault and is not one. The cause was Pgpool health-check
        #: rows and is fixed in `parse_pg_log`; this says so out loud rather
        #: than printing a blank box if anything else ever produces one.
        if not (s.sql or "").strip():
            out += [
                f"**[{s.seq}]** _statement with no SQL text_ · "
                f"{_fmt_ms(s.duration_ms)}",
                "",
                "> Not a captured query. A statement reaching the report with "
                "no text is a parser or pooler artefact — see "
                "`parse_pg_log`'s blank-statement guard — and must not be "
                "counted as an operation's SQL.",
                "",
            ]
            continue
        out += [
            f"**[{s.seq}]** `{s.table or DASH}` · {s.verb or DASH} · "
            f"{_fmt_ms(s.duration_ms)}",
            "",
            "```sql",
            (s.sql or "").strip(),
            "```",
        ]
        #: Only when the statement actually bound values. The parser treats a
        #: missing line as "no parameters recorded" and refuses the replay,
        #: rather than reading the block as malformed.
        if s.params:
            out += [f"params: `{s.params}`", ""]
        else:
            out.append("")
    return out


def explain_index(explains):
    """Index EXPLAIN results by `(normalised SQL, params)` — the pair key.

    The run file's `explains` and the matrix's pairs are produced by zipping two
    lists, so position is meaningless once either is re-read from disk. But each
    explain carries its own `sql` and `params`, and that pair is what
    `query_profile` groups on in the first place, so it is a real key rather
    than an alignment assumption.

    Measured on the 2026-09-03 admin pair: 561 of 564 statement blocks join, and
    the 3 that do not are the `principal_authentication_data` statements whose
    parameters were redacted at capture.
    """
    from api_trace import normalize_sql

    out = {}
    for e in explains or []:
        out.setdefault((normalize_sql(e.get("sql") or ""), e.get("params")), e)
    return out


def format_explain(e, index_state):
    """One EXPLAIN result as a single readable line.

    Deliberately one line per statement. The full plan is in the run JSON; a
    report that inlines it is unreadable at 500+ statements, and the question a
    reader has here is "did this use an index, or read the table".

    TWO THINGS THIS HAS TO COLLAPSE, both from real output (2026-09-03):

      * a `Bitmap Index Scan` node has no `Relation Name` -- only the heap node
        above it does -- so naming each scan produced
        `Bitmap Index Scan on None using entities_pkey`, five times in one line.
      * a `BitmapOr` repeats the same index once per branch. The five sub-scans
        of one plan were entities_pkey, idx_entities, entities_pkey,
        entities_pkey, idx_entities -- read as five scans, meaning two.

    So: name the node that touches the relation, then list the indexes with
    their multiplicity.
    """
    if e is None:
        return None
    if e.get("skipped") or e.get("error"):
        why = e.get("error") or e.get("skipped")
        return f"EXPLAIN ({index_state}) — not planned: {why}"

    scans = e.get("scans") or []
    heap = next((s for s in scans if s.get("relation")), None)
    if heap:
        head = f"{heap.get('node')} on {heap.get('relation')}"
    else:
        head = ", ".join(e.get("node_types") or []) or "no scan node"

    #: Index multiplicity, in first-seen order. A dict preserves that and a
    #: Counter's ordering is not guaranteed to be meaningful to a reader.
    counts = {}
    for s in scans:
        name = s.get("index")
        if name:
            counts[name] = counts.get(name, 0) + 1
    if counts:
        head += " using " + ", ".join(
            f"{n}" + (f" ×{c}" if c > 1 else "") for n, c in counts.items()
        )

    plan = (e.get("plan") or {}).get("Plan", {})
    extra = []
    if e.get("plan_rows") is not None:
        n = e["plan_rows"]
        extra.append(f"est. {n:,} row" + ("" if n == 1 else "s"))
    if isinstance(plan.get("Total Cost"), (int, float)):
        extra.append(f"cost {plan['Total Cost']:.2f}")
    if e.get("rows_removed_by_filter"):
        extra.append(f"{e['rows_removed_by_filter']:,} rows filtered")
    tail = " · ".join(extra)
    return f"EXPLAIN ({index_state}) — {head}" + (f" · {tail}" if tail else "")


#: Why a statement carries no plan, in the reader's terms rather than the
#: tool's. A blank line here would read as a capture fault, which is what the
#: whole 2026-09-02 session was spent proving something was not.
NO_EXPLAIN_REDACTED = (
    "_No EXPLAIN: parameters were redacted at capture (secret table), so this "
    "statement can never be replayed._"
)
NO_EXPLAIN_UNMATCHED = (
    "_No EXPLAIN: this statement was not in the sweep's worklist — it was "
    "refused as unreplayable. See the run's refusal list._"
)


def annotate_with_explains(text, explains, index_state="index absent"):
    """Insert an EXPLAIN line under every statement block in a matrix report.

    Works on the RENDERED report rather than on records, so everything the
    report already says is preserved byte-for-byte and only the annotation is
    added. Re-running is safe: an existing annotation is replaced, not stacked.

    Returns:
        (annotated_text, stats) where stats counts matched / redacted /
        unmatched — a silent join is a join nobody checked.
    """
    import re as _re

    from api_trace import REDACTED, normalize_sql

    idx = explain_index(explains)
    stats = {"matched": 0, "redacted": 0, "unmatched": 0}

    #: A statement block: the fenced SQL, an optional `params:` line, and any
    #: annotation a previous run left behind.
    block = _re.compile(
        r"(```sql\n(?P<sql>.*?)\n```\n)" r"(?P<params>params: `(?P<pv>.*?)`\n)?"
        #: `\n?` swallows the blank line a previous annotation inserted, so a
        #: re-run REPLACES it instead of adding another. Without it, running
        #: twice grows a blank line each time.
        r"(?P<old>\n?(?:(?:EXPLAIN \(|_No EXPLAIN)[^\n]*\n)*)",
        _re.S,
    )

    def sub(m):
        sql, pv = m.group("sql"), m.group("pv")
        head = m.group(1) + (m.group("params") or "")
        e = idx.get((normalize_sql(sql), pv))
        if e is not None:
            stats["matched"] += 1
            line = format_explain(e, index_state)
        elif pv and REDACTED in pv:
            stats["redacted"] += 1
            line = NO_EXPLAIN_REDACTED
        else:
            stats["unmatched"] += 1
            line = NO_EXPLAIN_UNMATCHED
        #: BLANK LINE FIRST. Without it markdown joins the annotation onto the
        #: `params:` line above and the report renders as a wall of prose --
        #: 561 of them in the first merged admin report.
        return head + "\n" + line + "\n"

    return block.sub(sub, text), stats


def render_api_detail(records):
    out = ["## Per-API detail", ""]
    for rec in records:
        share = ""
        if getattr(rec, "batched_share", None) is not None:
            reads = (getattr(rec, "entity_access", None) or {}).get("entity_reads", 0)
            share = f" (batched {rec.batched_share:.0%} of {reads} reads)"
        out += [
            f"### `{rec.api}`",
            "",
            f"- `{rec.method} {rec.path}` → **{rec.status}**",
            f"- wall {rec.wall_ms:.0f} ms · {rec.sql_count} statements · "
            f"{rec.minio_count} object ops · entity access: {rec.cache_shape}" + share,
            f"- tables: {', '.join(rec.tables_touched) or DASH}",
            "",
        ]
        out += render_statements(rec)
        if getattr(rec, "minio", None):
            out += ["| # | Method | Path | ms |", "|---|---|---|---|"]
            for m in rec.minio:
                ms = f"{m.duration_ms:.2f}" if m.duration_ms is not None else DASH
                out.append(f"| {m.seq} | {m.method} | `{m.path}` | {ms} |")
            out.append("")
    return out


def render_table_matrix(matrix):
    """API → PostgreSQL tables, R / W / RW / ·."""
    tables = sorted({t for row in matrix.values() for t in row})
    out = [
        "## API → PostgreSQL tables",
        "",
        "| API | " + " | ".join(tables) + " |",
        "|---|" + "---|" * len(tables),
    ]
    for api in sorted(matrix):
        cells = " | ".join(matrix[api].get(t, "") or "·" for t in tables)
        out.append(f"| `{api}` | {cells} |")
    return out + [""]


def render_matrix_report(
    records,
    matrix,
    *,
    case=None,
    identity=None,
    polaris_version=None,
    realm="POLARIS",
    schema_version=None,
    schema_verdict=None,
    volume=None,
    now=None,
):
    """The whole report.

    `case` and `identity` are what the three-identity design adds: without them
    a reader cannot tell whose authorization a 403 column describes, and three
    reports that differ only by caller would be indistinguishable.

    `polaris_version` has no default version string on purpose: it defaulted
    to "1.3.0-incubating" and kept stamping that on reports after the 1.6.0
    upgrade. Callers pass `init_env`'s `POLARIS_VERSION`.
    """
    ts = (now or datetime.now()).strftime("%Y-%m-%d %H:%M")
    head = [
        "# API → SQL → MinIO Access Matrix",
        "",
        f"Generated {ts} from a live local run — "
        f"Polaris {polaris_version or 'version unrecorded'}, "
        f"realm {realm}.",
    ]
    if schema_version is not None:
        head.append(f"Schema version {schema_version} ({schema_verdict}).")
    if case:
        head += [
            "",
            f"**Identity case: `{case}`**"
            + (f" — driven as `{identity}`." if identity else "."),
            "",
            "Every plan and every refusal below is a statement about THIS "
            "caller. A 403 here is a measurement, not a gap: it still pays the "
            "full authorization prelude, including the `grant_records` grantee "
            "lookup, before the decision is made.",
        ]
    if volume:
        head += [
            "",
            "Measured volume at drive time: "
            + ", ".join(f"`{k}` {v:,}" for k, v in sorted(volume.items()))
            + ".",
        ]
    head += ["", "R = read, W = write, RW = both.", ""]
    return "\n".join(head + render_table_matrix(matrix) + render_api_detail(records))


def write_report(reports_dir, stem, text, stamp=None, latest=True):
    """Write `<stem>-<stamp>.md` and refresh `<stem>-latest.md`.

    The timestamped file is the record and is never overwritten, so a
    before/after pair survives. The `-latest` copy is the convenience handle for
    whatever reads "the current report" without knowing the stamp.

    CAUTION, and it is why `latest` is a parameter. Only `doc-*-latest.md` is
    tracked by `reports/.gitignore`; the stamped twin is ignored. So refreshing
    `-latest` replaces the only version-controlled copy of the previous report.
    Archive it as a tracked file first, or pass `latest=False`.
    """
    import pathlib

    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    d = pathlib.Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    stamped = d / f"{stem}-{stamp}.md"
    stamped.write_text(text, encoding="utf-8")
    if latest:
        (d / f"{stem}-latest.md").write_text(text, encoding="utf-8")
    return stamped
