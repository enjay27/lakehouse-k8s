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
    polaris_version="1.3.0-incubating",
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
    """
    ts = (now or datetime.now()).strftime("%Y-%m-%d %H:%M")
    head = [
        "# API → SQL → MinIO Access Matrix",
        "",
        f"Generated {ts} from a live local run — Polaris {polaris_version}, "
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
