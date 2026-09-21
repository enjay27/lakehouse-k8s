#!/usr/bin/env python3
"""Build the per-case EXPLAIN comparison workbook.

    uv run python render_explain_workbook.py \
        --case admin \
        --matrix reports/doc-api-sql-matrix-admin-20260903-094137.md \
        --explain runs/apiexplain-admin-20260903-110152.json

One workbook per case (Kade, 2026-09-03). Design and the reasoning behind each
sheet are in `PLAN-explain-workbook.md`; this is the implementation.

A VIEW, NOT A SOURCE. Every figure is read from the matrix report and the run
file at build time. `runs/apiexplain-*.json` remains authoritative -- when the
workbook and the run disagree, the run is right and this script has a bug.

NO FORMULAS OVER THE DATA, deliberately. The rows are imported measurements, not
a model: nothing recalculates when a cell changes, because the inputs are JSON
files rather than other cells. The only formulas are the derived counts on
`Provenance`, which really are computed from sheet contents and therefore should
follow them.
"""

import argparse
import collections
import json
import pathlib
import re
import shutil
import sys

from datetime import datetime

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

from api_report import explain_index  # noqa: E402
from api_trace import REDACTED, extract_verb, normalize_sql  # noqa: E402
from schema_audit import STOCK_INDEX_NAMES  # noqa: E402

FONT = "Arial"
#: Excel's hard limit is 32,767 characters in a cell. A silently truncated cell
#: is worse than a short one, so the marker is visible and the run file is named
#: as the place to go instead.
CELL_MAX = 32_000
HEAD_FILL = PatternFill("solid", fgColor="DDDDDD")
FLAG_FILL = PatternFill("solid", fgColor="FFE0E0")


def truncate(s):
    s = "" if s is None else str(s)
    return s if len(s) <= CELL_MAX else s[:CELL_MAX] + f"… [truncated, {len(s)} chars]"


def where_of(sql):
    m = re.search(r"\bWHERE\b(.*)$", " ".join((sql or "").split()), re.I)
    return m.group(1).strip() if m else ""


def predicate_columns(sql):
    """The SET of columns a statement constrains, order-insensitive.

    THE POINT OF THE `Shapes` SHEET. The predicate column ORDER varies between
    runs, so the same grantee lookup appears under several distinct SQL texts.
    Comparing text reports differences that do not exist; comparing the column
    set does not.
    """
    return tuple(sorted(set(re.findall(r"([a-z_]+)\s*=\s*[?$]", where_of(sql), re.I))))


def plan_cost(e):
    return ((e.get("plan") or {}).get("Plan") or {}).get("Total Cost")


def relation_scan_node(e):
    """The plan node that actually touches a base relation, with its own cost.

    NOT the top node. On a DELETE the top is `ModifyTable`; on a Bitmap plan
    the heap node sits above the Bitmap Index Scan that carries the condition.
    The scan node is the one whose cost and row estimate describe READING the
    table, which is the only thing this comparison is about.
    """
    found = []

    def walk(n):
        if not isinstance(n, dict):
            return
        if n.get("Relation Name") and "Scan" in (n.get("Node Type") or ""):
            found.append(n)
        for c in n.get("Plans") or []:
            walk(c)

    walk(plan_node(e))
    return found[0] if found else {}


def rows_scanned(e, vol):
    """(rows the plan READS from its relation, why that number).

    A Seq Scan reads the whole table. Its `Plan Rows` is what SURVIVES the
    Filter -- 1, here, on a 60,815-row table -- and putting that in a
    "rows scanned" column makes this comparison say the opposite of what
    happened. The width of a Seq Scan comes from the table, and `volume` on the
    run file is a real count(*) taken at sweep time, not `reltuples`.

    An index node reads what the `Index Cond` matched, which IS `Plan Rows`
    when nothing was left over in `Filter`. Where a Filter remains, the node
    read more than it returned and the number is a LOWER BOUND -- `rows_basis`
    says so on the row, and the `filter` column beside it is the evidence.
    """
    n = relation_scan_node(e)
    node, rel = n.get("Node Type"), n.get("Relation Name")
    if not node or not rel:
        return None, ""
    if node == "Seq Scan":
        return vol.get(rel), "whole table"
    rows = n.get("Plan Rows")
    return rows, "index match" + (", lower bound" if n.get("Filter") else "")


#: Three columns, in the order they are written to every statement sheet.
READ_HEADERS = ("rows_scanned", "rows_basis", "scales_with_table")
READ_WIDTHS = (13, 23, 18)
READ_BLANK = (None, "", None)


def read_width(e, vol):
    """(rows read, why that number, whether that number grows with the table).

    NO RATIO, ON PURPOSE. Rows and cost sit side by side and the reader draws
    the line between them; a ratio against some other statement's plan buries
    the two numbers that actually forecast anything under an arithmetic nobody
    can re-derive from the sheet.

    `scales_with_table` is the column to sort on before a reseed. TRUE means
    the plan reads the WHOLE relation, so its rows_scanned and its cost both
    move with the row count -- seeding 10,000 principals multiplies these and
    leaves the FALSE rows where they are. It is a statement about plan SHAPE,
    which is what plain EXPLAIN measures reliably, not about the estimates.
    """
    if not e or e.get("skipped") or e.get("error"):
        return READ_BLANK
    rows, basis = rows_scanned(e, vol)
    if not basis:
        return READ_BLANK
    return (rows, basis, basis == "whole table")


def scan_summary(e):
    """`node on relation using index ×n` -- the same collapse the report uses."""
    scans = e.get("scans") or []
    heap = next((s for s in scans if s.get("relation")), None)
    head = (
        f"{heap.get('node')} on {heap.get('relation')}"
        if heap
        else ", ".join(e.get("node_types") or [])
    )
    counts = {}
    for s in scans:
        if s.get("index"):
            counts[s["index"]] = counts.get(s["index"], 0) + 1
    if counts:
        head += " using " + ", ".join(
            n + (f" ×{c}" if c > 1 else "") for n, c in counts.items()
        )
    return head


def plan_node(e):
    """The top plan node, or {}."""
    return ((e.get("plan") or {}).get("Plan")) or {}


def cond_and_filter(e):
    """`Index Cond` and `Filter` from anywhere in the plan tree.

    THE PAIR IS THE FINDING, at row level. `Index Cond` is what the planner
    pushed INTO the index -- a seek. `Filter` is what it had to test on every
    row it read. The grantee lookup has NO Index Cond and carries its whole
    predicate in Filter, which is what "no usable index" means concretely; the
    securable lookup is the reverse. Sorting on these two columns separates the
    served statements from the unserved without opening a single plan.

    Read from the whole tree: on a Bitmap plan the condition sits on the Bitmap
    Index Scan child, not on the heap node above it.
    """
    conds, filters = [], []

    def walk(n):
        if not isinstance(n, dict):
            return
        if n.get("Index Cond"):
            conds.append(n["Index Cond"])
        if n.get("Filter"):
            filters.append(n["Filter"])
        for c in n.get("Plans") or []:
            walk(c)

    walk(plan_node(e))
    return " AND ".join(conds), " AND ".join(filters)


def parse_matrix(text):
    """Every statement occurrence in a rendered matrix report, in order.

    Returns list of dicts: api, http_status, seq, table, verb, duration_ms,
    sql, params.
    """
    out = []
    for block in re.split(r"^### `", text, flags=re.M)[1:]:
        api = block.split("`")[0]
        st = re.search(r"→ \*\*(\d+)\*\*", block)
        status = int(st.group(1)) if st else None
        for m in re.finditer(
            r"\*\*\[(?P<seq>\d+)\]\*\* `(?P<table>[^`]*)` · (?P<verb>[^·]*) · "
            r"(?P<dur>[^\n]*)\n\n```sql\n(?P<sql>.*?)\n```\n"
            r"(?:params: `(?P<params>.*?)`\n)?",
            block,
            re.S,
        ):
            dur = re.match(r"([\d.]+)\s*ms", (m.group("dur") or "").strip())
            out.append(
                {
                    "api": api,
                    "http_status": status,
                    "seq": int(m.group("seq")),
                    "table": m.group("table").strip("`"),
                    "verb": (m.group("verb") or "").strip(),
                    "duration_ms": float(dur.group(1)) if dur else None,
                    "sql": m.group("sql"),
                    "params": m.group("params"),
                }
            )
    return out


def style(ws, widths, flag_col=None, n_rows=0):
    """Header, freeze, autofilter, widths -- and highlight ONE thing."""
    for c, w in enumerate(widths, start=1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(name=FONT, bold=True)
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(vertical="center")
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.freeze_panes = "A2"
    if n_rows:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(widths))}{n_rows + 1}"
    #: Exactly one conditional rule per sheet. Highlighting everything
    #: highlights nothing.
    if flag_col and n_rows:
        col = get_column_letter(flag_col)
        ws.conditional_formatting.add(
            f"{col}2:{col}{n_rows + 1}",
            CellIsRule(operator="equal", formula=["TRUE"], fill=FLAG_FILL),
        )


def write_rows(ws, header, rows, widths, flag_col=None):
    #: A row one cell shorter than its header does not raise -- it writes a
    #: sheet where every column after the gap is labelled with its neighbour's
    #: name, which reads as data and is invisible to anyone who did not build
    #: it. Cheap to check, expensive to find later.
    if widths is not None and len(widths) != len(header):
        raise ValueError(f"{ws.title}: {len(header)} headers but {len(widths)} widths")
    for i, r in enumerate(rows):
        if len(r) != len(header):
            raise ValueError(
                f"{ws.title} row {i}: {len(r)} cells, {len(header)} headers"
            )
    ws.append(header)
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name=FONT)
    style(ws, widths, flag_col=flag_col, n_rows=len(rows))


def build(case, matrix_path, explain_path, dest):
    text = matrix_path.read_text(encoding="utf-8")
    run = json.loads(explain_path.read_text(encoding="utf-8"))

    #: The two refusals notebook 05 makes, for the same reason: a workbook built
    #: from a mismatched pair looks entirely correct.
    if run.get("case") != case:
        sys.exit(f"{explain_path.name} is a '{run.get('case')}' run, not '{case}'")
    if not str(run.get("matrix", "")).endswith(matrix_path.name):
        sys.exit(
            f"{explain_path.name} was taken against {run.get('matrix')}, "
            f"not {matrix_path.name}"
        )

    state = run.get("index_state")
    idx = explain_index(run.get("explains") or [])
    occurrences = parse_matrix(text)
    per_api = run.get("per_api", {})
    vol = run.get("volume") or {}

    wb = Workbook()
    wb.remove(wb.active)

    # ---- Summary -----------------------------------------------------------
    ws = wb.create_sheet("Summary")
    status_by_api = {o["api"]: o["http_status"] for o in occurrences}
    rows = []
    for api, r in sorted(per_api.items()):
        seq = r.get("seq_scanned") or []
        rows.append(
            [
                case,
                api,
                status_by_api.get(api),
                r.get("statements"),
                r.get("planned"),
                r.get("skipped"),
                ", ".join(seq) or "",
                ", ".join(r.get("indexes_used") or []) or "",
                #: The run file's key is `uses_index_only`, which does NOT
                #: mean "used an Index Only Scan". It means nothing this API
                #: issued scanned a table sequentially AND at least one
                #: statement used an index -- fully index-served. PostgreSQL's
                #: `Index Only Scan` is a different node type, satisfied from
                #: the index without touching the heap, and it appears 12 times
                #: in these very plans. Renamed on the way out; the collision
                #: is a trap either way round.
                bool(r.get("uses_index_only")),
                "grant_records" in seq,
            ]
        )
    write_rows(
        ws,
        [
            "case",
            "api",
            "http_status",
            "statements",
            "planned",
            "skipped",
            "seq_scanned",
            "indexes_used",
            "fully_index_served",
            "scans_grant_records",
        ],
        rows,
        [13, 42, 12, 11, 9, 9, 22, 46, 19, 20],
        flag_col=10,
    )

    # ---- Statements --------------------------------------------------------
    ws = wb.create_sheet("Statements")
    rows = []
    for o in occurrences:
        e = idx.get((normalize_sql(o["sql"]), o["params"]))
        rt = read_width(e, vol)
        rows.append(
            [
                case,
                o["api"],
                o["http_status"],
                o["seq"],
                o["table"],
                o["verb"],
                o["duration_ms"],
                scan_summary(e) if e else "",
                ", ".join((e or {}).get("indexes_used") or []) or "",
                bool(e and e.get("seq_scanned")),
                (e or {}).get("plan_rows"),
                plan_node(e).get("Startup Cost") if e else None,
                plan_cost(e) if e else None,
                *rt,
                bool(e and e.get("parallel")),
                truncate(cond_and_filter(e)[0]) if e else "",
                truncate(cond_and_filter(e)[1]) if e else "",
                truncate(" ".join((o["sql"] or "").split()))[:120],
                truncate(o["params"]),
                truncate(" ".join((o["sql"] or "").split())),
            ]
        )
    write_rows(
        ws,
        [
            "case",
            "api",
            "http_status",
            "seq",
            "table",
            "verb",
            "duration_ms",
            "plan",
            "index_used",
            "seq_scan",
            "plan_rows",
            "startup_cost",
            "total_cost",
            *READ_HEADERS,
            "parallel",
            "index_cond",
            "filter",
            "sql_short",
            "params",
            "sql_full",
        ],
        rows,
        [13, 40, 11, 6, 22, 8, 12, 46, 30, 10, 11, 12, 11]
        + list(READ_WIDTHS)
        + [10, 56, 56, 60, 34, 60],
        flag_col=10,
    )

    # ---- Distinct ----------------------------------------------------------
    ws = wb.create_sheet("Distinct")
    rows = []
    for e in run.get("explains") or []:
        refused = e.get("error") or e.get("skipped")
        rt = read_width(e, vol)
        rows.append(
            [
                case,
                e.get("table"),
                e.get("verb"),
                e.get("occurrences"),
                len(e.get("apis") or {}),
                scan_summary(e) if not refused else "",
                ", ".join(e.get("indexes_used") or []) or "",
                bool(e.get("seq_scanned")),
                e.get("plan_rows"),
                plan_node(e).get("Startup Cost"),
                plan_cost(e),
                *rt,
                bool(e.get("parallel")),
                truncate(cond_and_filter(e)[0]),
                truncate(cond_and_filter(e)[1]),
                truncate(", ".join(sorted(e.get("apis") or {}))),
                bool(e.get("params_observed")),
                truncate(where_of(e.get("sql"))),
                truncate(e.get("params")),
                not bool(refused),
                truncate(refused) if refused else "",
                truncate(" ".join((e.get("sql") or "").split())),
            ]
        )
    write_rows(
        ws,
        [
            "case",
            "table",
            "verb",
            "occurrences",
            "api_count",
            "plan",
            "index_used",
            "seq_scan",
            "plan_rows",
            "startup_cost",
            "total_cost",
            *READ_HEADERS,
            "parallel",
            "index_cond",
            "filter",
            "api_list",
            "params_observed",
            "where_clause",
            "params",
            "replayable",
            "refusal_reason",
            "sql_full",
        ],
        rows,
        [
            13,
            24,
            8,
            12,
            10,
            46,
            30,
            10,
            11,
            12,
            11,
            *READ_WIDTHS,
            10,
            56,
            56,
            70,
            16,
            60,
            34,
            11,
            40,
            60,
        ],
        flag_col=8,
    )

    # ---- Cost --------------------------------------------------------------
    #: Rows and cost, ranked. Every other sheet lists; this one puts the two
    #: numbers side by side and stops there -- no ratio, because the reader
    #: drawing the line between rows and cost themselves is the point, and a
    #: ratio against another statement's plan buries both under an arithmetic
    #: they cannot re-derive from the sheet.
    #:
    #: THE RESEED QUESTION. Sort on `scales_with_table`, then `cost_units`.
    #: TRUE means the plan reads the whole relation, so both its numbers move
    #: with the row count; seeding 10,000 principals multiplies those rows and
    #: leaves the FALSE ones where they are. That split, not today's estimates,
    #: is what forecasts.
    ws = wb.create_sheet("Cost")
    planned = [
        e
        for e in (run.get("explains") or [])
        if not (e.get("skipped") or e.get("error"))
    ]
    #: Planner cost units, summed over occurrences. NOT time, and not additive
    #: across cases -- a within-case weight and nothing else. It is here because
    #: "51 x 1637.26" is the shape of the finding, and leaving the reader to
    #: multiply it in their head loses it.
    total_units = (
        sum((plan_cost(e) or 0) * (e.get("occurrences") or 0) for e in planned) or 1
    )
    rows = []
    for e in planned:
        rows_read, basis, scales = read_width(e, vol)
        occ = e.get("occurrences") or 0
        cost = plan_cost(e)
        units = (cost or 0) * occ
        rows.append(
            [
                case,
                e.get("table"),
                e.get("verb"),
                occ,
                len(e.get("apis") or {}),
                scan_summary(e),
                rows_read,
                basis,
                scales,
                cost,
                round(units, 2),
                round(units / total_units, 4),
                ", ".join(predicate_columns(e.get("sql"))),
                truncate(where_of(e.get("sql")))[:120],
            ]
        )
    #: Weight first, then raw cost. The two ways of being expensive -- often,
    #: and badly -- both surface at the top instead of one hiding the other.
    rows.sort(key=lambda r: (-(r[10] or 0), -(r[9] or 0)))
    write_rows(
        ws,
        [
            "case",
            "table",
            "verb",
            "occurrences",
            "api_count",
            "plan",
            "rows_scanned",
            "rows_basis",
            "scales_with_table",
            "total_cost",
            "cost_units",
            "cost_share",
            "predicate_columns",
            "where_clause",
        ],
        rows,
        [13, 22, 8, 12, 10, 44, 13, 23, 18, 12, 13, 11, 46, 60],
        flag_col=9,
    )
    for r in range(2, len(rows) + 2):
        ws.cell(row=r, column=12).number_format = "0.0%"

    # ---- Shapes ------------------------------------------------------------
    ws = wb.create_sheet("Shapes")
    shapes = {}
    for e in run.get("explains") or []:
        key = (e.get("verb"), e.get("table"), predicate_columns(e.get("sql")))
        s = shapes.setdefault(
            key,
            {
                "texts": set(),
                "occ": 0,
                "apis": set(),
                "plan": "",
                "idx": "",
                "seq": False,
            },
        )
        s["texts"].add(normalize_sql(e.get("sql") or ""))
        s["occ"] += e.get("occurrences") or 0
        s["apis"].update(e.get("apis") or {})
        if not (e.get("error") or e.get("skipped")):
            s["plan"] = s["plan"] or scan_summary(e)
            s["idx"] = s["idx"] or ", ".join(e.get("indexes_used") or [])
            s["seq"] = s["seq"] or bool(e.get("seq_scanned"))
    rows = [
        [
            case,
            v,
            t,
            ", ".join(cols) or "(none)",
            len(s["texts"]),
            s["occ"],
            len(s["apis"]),
            s["plan"],
            s["idx"],
            s["seq"],
        ]
        for (v, t, cols), s in sorted(
            shapes.items(), key=lambda kv: (-kv[1]["occ"], str(kv[0]))
        )
    ]
    write_rows(
        ws,
        [
            "case",
            "verb",
            "table",
            "predicate_columns",
            "texts",
            "occurrences",
            "api_count",
            "plan",
            "index_used",
            "seq_scan",
        ],
        rows,
        [13, 8, 24, 62, 8, 13, 10, 46, 30, 10],
        flag_col=10,
    )

    # ---- Unplanned ---------------------------------------------------------
    ws = wb.create_sheet("Unplanned")
    rows = []
    for e in run.get("explains") or []:
        why = e.get("error") or e.get("skipped")
        if not why:
            continue
        kind = "redacted" if REDACTED in str(e.get("params")) else "refused"
        rows.append(
            [
                case,
                e.get("table"),
                e.get("verb"),
                kind,
                truncate(str(why)),
                bool(e.get("params_observed")),
                truncate(e.get("params")),
                truncate(" ".join((e.get("sql") or "").split())),
            ]
        )
    #: Statements in the report that never reached the worklist at all.
    for o in occurrences:
        if (normalize_sql(o["sql"]), o["params"]) in idx:
            continue
        kind = "redacted" if o["params"] and REDACTED in o["params"] else "unmatched"
        rows.append(
            [
                case,
                o["table"],
                o["verb"],
                kind,
                "not in the sweep's worklist",
                bool(o["params"]),
                truncate(o["params"]),
                truncate(" ".join((o["sql"] or "").split())),
            ]
        )
    write_rows(
        ws,
        [
            "case",
            "table",
            "verb",
            "kind",
            "reason",
            "params_observed",
            "params",
            "sql_full",
        ],
        rows,
        [13, 30, 8, 12, 46, 16, 34, 70],
    )

    # ---- Schema ------------------------------------------------------------
    ws = wb.create_sheet("Schema")
    rows = [
        [
            i.get("name"),
            run.get("indexes_on_focus_table") and "grant_records",
            truncate(" ".join((i.get("def") or "").split())),
            i.get("name") in STOCK_INDEX_NAMES,
        ]
        for i in (run.get("indexes_on_focus_table") or [])
    ]
    write_rows(
        ws,
        ["index_name", "table", "definition", "in_upstream_schema"],
        rows,
        [34, 18, 96, 20],
    )

    # ---- Provenance --------------------------------------------------------
    ws = wb.create_sheet("Provenance")
    n = len(per_api)
    prov = [
        #: First two rows, because "am I looking at the current one" has to be
        #: answerable without leaving the workbook. Three generations of these
        #: files once sat in reports/ under near-identical stamped names, and
        #: the oldest sorted first.
        ["workbook_file", dest.name],
        ["workbook_built", datetime.now().isoformat(timespec="seconds")],
        ["case", case],
        ["matrix_report", matrix_path.name],
        ["explain_run", explain_path.name],
        ["index_state", state],
        ["idx_grant_records_grantee", "absent" if state == "absent" else "present"],
        ["", ""],
        ["entities rows", vol.get("entities")],
        ["grant_records rows", vol.get("grant_records")],
        ["policy_mapping_record rows", vol.get("policy_mapping_record")],
        [
            "principal_authentication_data rows",
            vol.get("principal_authentication_data"),
        ],
        ["", ""],
        ["APIs", n],
        ["statement occurrences", len(occurrences)],
        ["distinct (SQL, params) pairs", run.get("pairs")],
        ["APIs that seq-scan grant_records", f"=COUNTIF(Summary!J2:J{n + 1},TRUE)"],
        ["", ""],
        ["READ THIS", ""],
        [
            "fully_index_served (Summary)",
            "TRUE means every statement that API issued was served by an index "
            "and NONE scanned a table sequentially. It does NOT mean 'used an "
            "Index Only Scan' — that is a different PostgreSQL node type, "
            "satisfied from the index without touching the heap, and it appears "
            "in these plans under `plan` on the Statements sheet. The run file "
            "calls this key uses_index_only; renamed here because the collision "
            "is a trap. FALSE for every API in every case here, because all 43 "
            "issue the grantee lookup and that scans grant_records.",
        ],
        [
            "rows_scanned",
            "Rows the plan READS from its table. For a Seq Scan that is the "
            "whole table (the count(*) above) — NOT its plan_rows, which is "
            "what SURVIVES the Filter and reads 1 on a 60,815-row table. For "
            "an index node it is the node's plan_rows, i.e. what the Index "
            "Cond matched; where a Filter also remains it is a lower bound and "
            "rows_basis says so.",
        ],
        [
            "rows and cost, no ratio",
            "The two numbers sit side by side and the reader draws the line. "
            "They are not proportional and should not be treated as though "
            "they were: reading 60,815 rows sequentially costs 194x a "
            "single-row index seek, not 60,815x, because a sequential read is "
            "far cheaper PER ROW than the same number of random index "
            "descents. Neither number is a latency — plain EXPLAIN does not "
            "execute, so nothing here was timed.",
        ],
        [
            "scales_with_table — the column to sort on before a reseed",
            "TRUE means the plan reads the WHOLE relation, so its rows and its "
            "cost both move with the row count. Seeding 10,000 principals "
            "multiplies the TRUE rows and leaves the FALSE ones where they "
            "are. This is a statement about plan SHAPE, which is what plain "
            "EXPLAIN measures reliably — unlike the estimates beside it. "
            "Growth is not uniform: grant_records grows with principals x "
            "grants, entities with catalogs and tables. Re-run the sweep after "
            "a reseed; do not extrapolate these numbers.",
        ],
        [
            "THE SHAPE FLIPS AT VOLUME — AND THIS SWEEP CANNOT SEE IT",
            "02b measured the unindexed grantee scan planning as a plain "
            "Seq Scan at 125,235 rows and as a PARALLEL Gather at 233,237 — a "
            "different regime, not more of this one. This sweep cannot "
            "reproduce that at any volume: explain_statements pins "
            "max_parallel_workers_per_gather = 0 for the session (deliberately "
            "— 02b measured parallel timings as unusable, identical cost and "
            "buffers with a 3-10x clock spread). So `parallel` is structurally "
            "FALSE here and a post-reseed sweep will still report Seq Scan. "
            "That is the pin, not the planner. To ask whether it escalates, "
            "run one unpinned pass — or read "
            "reports/doc-grant-scale-sweep-latest.md, which already did.",
        ],
        [
            "cost_units / cost_share (Cost sheet)",
            "total_cost × occurrences, and that as a share of the case. "
            "Planner cost units, NOT milliseconds, and not comparable across "
            "cases — a within-case ranking of which statement dominates.",
        ],
        [
            "total_cost / plan_rows are planner ESTIMATES",
            "They move with ANALYZE. Two sweeps 25 min apart differed in 11 of 264 "
            "plan_rows while 0 of 264 differed in plan SHAPE. Do not average, sum "
            "or trend them — sort and compare shape.",
        ],
        [
            "duration_ms is NOT from the EXPLAIN",
            "Plain EXPLAIN does not execute. It is the drive's observed "
            "server-side duration, a different measurement; the same plan has "
            "measured a 4.6x spread.",
        ],
        [
            "one volume",
            "Every plan is relative to the row counts above. A larger realm is a "
            "different regime, not more of this one.",
        ],
        [
            "authority",
            f"{explain_path.name} and {matrix_path.name}. Where this workbook and "
            "the run disagree, the run is right.",
        ],
    ]
    for r in prov:
        ws.append(r)
    for row in ws.iter_rows():
        row[0].font = Font(name=FONT, bold=True)
        for c in row[1:]:
            c.font = Font(name=FONT)
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"] = ws.column_dimensions["A"]
    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 96

    dest.parent.mkdir(exist_ok=True)
    wb.save(dest)
    return {
        "summary": n,
        "statements": len(occurrences),
        "distinct": len(run.get("explains") or []),
        "shapes": len(shapes),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--explain", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = pathlib.Path(
        args.out or HERE / "reports" / f"api-explain-{args.case}-{stamp}.xlsx"
    )
    counts = build(args.case, HERE / args.matrix, HERE / args.explain, dest)
    #: The same `-latest` convention the markdown reports use, and for the same
    #: reason: stamped names accumulate, sort by stamp rather than by recency in
    #: most file pickers, and whoever opens the wrong one gets a workbook that
    #: is internally consistent and silently a generation old. Only written for
    #: the default destination -- an explicit --out is a deliberate name and
    #: should not quietly claim to be latest.
    latest = None
    if args.out is None:
        latest = dest.parent / f"api-explain-{args.case}-latest.xlsx"
        shutil.copyfile(dest, latest)
    #: Line 1 stays exactly `-> <stamped name>`. Notebook 06 parses it, and
    #: a suffix appended here would silently poison the name it records.
    print(f"-> {dest.name}")
    if latest:
        print(f"   latest: {latest.name}")
    for k, v in counts.items():
        print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
