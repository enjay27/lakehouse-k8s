#!/usr/bin/env python3
"""
Verify migrate_v3_to_v4.sql against the schema-v4.sql that the 1.6.0 image actually ships.

WHY THIS EXISTS
  postgresql/schema/migrate_v3_to_v4.sql was TRANSCRIBED from upstream, not taken from the
  distribution. Its correctness rests on two claims:

    (1) v3 -> v4 is ADDITIVE ONLY -- every object v3 and v4 share is declared identically,
        so the migration needs no ALTER and rewrites no data;
    (2) the additive statements in our script match the shipped ones.

  A plain `diff` cannot check either: the shipped file is a FULL schema and ours is a delta
  plus a guard, so the two differ almost everywhere while still agreeing on what matters.
  This script checks the two claims directly and exits non-zero if either fails.

  Both claims are about CREATE TABLE/INDEX/SCHEMA/VIEW and nothing else, which is a narrower
  guarantee than the PASS line suggests -- in the shipped v3, 26 of 36 statements are neither.
  So a third check was added 2026-09-18 (see RESIDUAL STATEMENTS below), after the first real
  run of this script passed on the claims while the migration was in fact missing two
  statements the shipped file has.

RESIDUAL STATEMENTS -- the claims' blind spot, and why it is checked separately
  Everything that is not one of those four CREATE forms -- COMMENT ON, GRANT, CREATE FUNCTION
  / SEQUENCE / TYPE / TRIGGER, seed INSERTs -- is invisible to both claims. If the shipped v4
  added a function and the migration omitted it, claims 1 and 2 would both still pass and the
  migration would be incomplete. The residual check compares those statements too:

    * a v4-added statement the migration omits FAILS, unless
    * it only annotates (COMMENT ON), which is reported as a NOTE -- the database ends up
      functionally identical, so it is not worth blocking a migration over.

  Statements whose shape legitimately differs between a full schema and a delta -- BEGIN /
  COMMIT, SET search_path, psql meta-commands, our version guard, and the version row write
  itself -- are excluded; `declared_version` already covers the last of those.

USAGE
  Extract the shipped file first (runbook step 2c, via Docker -- not from the running pod):

    python3 postgresql/schema/verify_v4_transcription.py \\
        --v3        /tmp/schema-v3.shipped.sql \\
        --v4        /tmp/schema-v4.shipped.sql \\
        --migration postgresql/schema/migrate_v3_to_v4.sql

  Pass the SHIPPED v3, not this repo's schema_v3.sql. The jar carries both. Feeding the repo
  copy back as the baseline would check the transcription against the assumption it rests on
  -- that the repo copy IS the shipped v3. (That assumption was tested on 2026-09-18 and
  holds: the two differ in indentation only. The shipped file is still the right input.)

  PASS means: run either script in step 2e; they agree. Prefer the shipped one -- it is the
  authority -- and keep ours for its version guard.
  FAIL means: STOP. Run the SHIPPED file in 2e, not ours, and read what this printed.

WHAT IT DELIBERATELY DOES NOT DO
  It does not execute SQL, connect to anything, or claim the migration will succeed. It
  compares three text files. A PASS here is not a substitute for reading version_value back
  out of the database in step 2f.
"""

import argparse
import re
import sys

# ---------------------------------------------------------------- parsing

COMMENT = re.compile(r"--[^\n]*")
WS = re.compile(r"\s+")


def strip_sql_comments(text):
    return COMMENT.sub(" ", text)


def split_statements(text):
    """Split on semicolons that are not inside a dollar-quoted block or a string literal.

    The scanner must skip `--` comments INLINE, not strip them first and not ignore them.
    Stripping first would corrupt any `--` inside a string literal; ignoring them lets an
    apostrophe in a comment ("1.6.0's backend") open a bogus string literal and swallow every
    following semicolon, which silently yields zero statements. That bug was live in the first
    version of this file and only the round-trip self-test caught it -- a verifier that reports
    FAIL on everything reads exactly like a failing transcription.
    """
    out, buf, i, n = [], [], 0, len(text)
    in_squote = False
    dollar_tag = None
    while i < n:
        ch = text[i]
        if dollar_tag:
            if text.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue
        if in_squote:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_squote = False
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j == -1 else j + 1
            buf.append(" ")
            continue
        if ch == "'":
            in_squote = True
            buf.append(ch)
            i += 1
            continue
        m = re.match(r"\$[A-Za-z_]*\$", text[i:])
        if m:
            dollar_tag = m.group(0)
            buf.append(dollar_tag)
            i += len(dollar_tag)
            continue
        if ch == ";":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf))
    return out


def normalise(stmt):
    """Canonical form for comparison: comments gone, whitespace collapsed, case-folded.

    Also drops the IF NOT EXISTS clause, so a statement written with it and one written
    without it still compare equal -- the object being declared is what matters here.
    """
    s = strip_sql_comments(stmt)
    s = WS.sub(" ", s).strip().lower()
    s = s.replace("if not exists ", "")
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ") ", s)
    return WS.sub(" ", s).strip()


OBJ = re.compile(
    r"^create\s+(?:unique\s+)?(table|index|schema|view)\s+(?:if\s+not\s+exists\s+)?"
    r"([a-z0-9_.\"]+)",
    re.I,
)


def objects(text):
    """{(kind, name): normalised_statement} for every CREATE in the file."""
    found = {}
    for raw in split_statements(text):
        s = strip_sql_comments(raw).strip()
        m = OBJ.match(WS.sub(" ", s).strip())
        if not m:
            continue
        kind, name = m.group(1).lower(), m.group(2).lower().strip('"')
        name = name.split(".")[-1]
        found[(kind, name)] = normalise(raw)
    return found


# ---------------------------------------------------------------- residual statements

# Shapes that legitimately differ between a FULL schema and a delta, so they carry no
# information about the transcription: the transaction wrapper, the search_path, psql
# meta-commands, and our version guard. The version row write is handled by
# declared_version() -- the full schema INSERTs it, the migration UPDATEs it.
RESIDUAL_IGNORE = re.compile(
    r"^(set\s|\\set\s|begin\b|commit\b|rollback\b|start\s+transaction\b|do\s+\$)", re.I
)
VERSION_WRITE = re.compile(
    r"^(insert\s+into\s+(polaris_schema\.)?version\b"
    r"|update\s+(polaris_schema\.)?version\s+set)",
    re.I,
)

# Annotation only: omitting it leaves the database functionally identical, so it is reported
# rather than failed. Nothing else gets that treatment.
COSMETIC = re.compile(r"^comment\s+on\b", re.I)


def residual_kind(normalised):
    m = re.match(r"create\s+(?:or\s+replace\s+)?(\w+)", normalised)
    if m:
        return f"create {m.group(1)}"
    m = re.match(
        r"(comment|grant|revoke|alter|insert|update|delete|truncate|call|select|with)\b",
        normalised,
    )
    return m.group(1) if m else "other"


def residuals(text):
    """{normalised_statement: kind} for every statement the two object claims cannot see.

    OBJ matches CREATE TABLE/INDEX/SCHEMA/VIEW and nothing else, so both claims are silent
    about the rest of the file. In the shipped v3 that is 26 statements out of 36. Surfacing
    them is what makes a PASS mean what it looks like it means.
    """
    out = {}
    for raw in split_statements(text):
        n = normalise(raw)
        if not n:
            continue
        if OBJ.match(n) or RESIDUAL_IGNORE.match(n) or VERSION_WRITE.match(n):
            continue
        out[n] = residual_kind(n)
    return out


def declared_version(text):
    for pat in (
        r"insert\s+into\s+version[^;]*?values\s*\(\s*'version'\s*,\s*(\d+)",
        r"update\s+[a-z_.]*version\s+set\s+version_value\s*=\s*(\d+)",
    ):
        m = re.search(pat, WS.sub(" ", strip_sql_comments(text)), re.I)
        if m:
            return int(m.group(1))
    return None


# ---------------------------------------------------------------- report


class Report:
    def __init__(self):
        self.failures = []
        self.notes = []

    def fail(self, headline, detail=""):
        self.failures.append((headline, detail))

    def note(self, line):
        self.notes.append(line)

    def emit(self):
        for line in self.notes:
            print(f"  {line}")
        if not self.failures:
            print("\nPASS -- the transcription agrees with the shipped schema.")
            print(
                "Either script may be run in step 2e. Prefer the shipped one; keep ours"
            )
            print("for its version guard. Still read version_value back in 2f.")
            return 0
        print(
            f"\nFAIL -- {len(self.failures)} problem(s). Do NOT run the transcribed script."
        )
        print(
            "Run the SHIPPED schema-v4.sql in step 2e instead; it is the authority.\n"
        )
        for headline, detail in self.failures:
            print(f"* {headline}")
            if detail:
                for line in detail.splitlines():
                    print(f"    {line}")
        return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--v3", required=True, help="schema-v3.sql extracted from the 1.6.0 image"
    )
    ap.add_argument(
        "--v4", required=True, help="schema-v4.sql extracted from the 1.6.0 image"
    )
    ap.add_argument("--migration", required=True, help="migrate_v3_to_v4.sql")
    args = ap.parse_args()

    texts = {}
    for label, path in (
        ("v3", args.v3),
        ("v4", args.v4),
        ("migration", args.migration),
    ):
        try:
            with open(path, encoding="utf-8") as fh:
                texts[label] = fh.read()
        except OSError as exc:
            print(f"cannot read {label}: {exc}", file=sys.stderr)
            return 2

    v3, v4, mig = (objects(texts[k]) for k in ("v3", "v4", "migration"))
    r = Report()

    print("objects found:")
    r.note(f"v3 {len(v3)}   v4 {len(v4)}   migration {len(mig)}")

    # --- declared versions -------------------------------------------------
    ver3, ver4, verm = (declared_version(texts[k]) for k in ("v3", "v4", "migration"))
    r.note(f"declared version -- v3 {ver3}, v4 {ver4}, migration {verm}")
    if ver3 != 3:
        r.fail(f"the v3 file declares version {ver3}, not 3 -- wrong file?")
    if ver4 != 4:
        r.fail(f"the shipped file declares version {ver4}, not 4 -- wrong file?")
    if verm != 4:
        r.fail(f"the migration sets version {verm}, not 4")

    # --- claim 1: shared objects are declared identically ------------------
    shared = sorted(set(v3) & set(v4))
    drifted = [k for k in shared if v3[k] != v4[k]]
    r.note(f"shared objects: {len(shared)}, of which differing: {len(drifted)}")
    for kind, name in drifted:
        r.fail(
            f"CLAIM 1 BROKEN -- {kind} {name} differs between v3 and v4, "
            "so the migration is NOT additive-only and needs an ALTER",
            f"v3: {v3[(kind, name)]}\nv4: {v4[(kind, name)]}",
        )

    # --- claim 2: every new object is in the migration, identically --------
    added = sorted(set(v4) - set(v3))
    r.note(f"objects v4 adds over v3: {len(added)}")
    for key in added:
        kind, name = key
        if key not in mig:
            r.fail(
                f"CLAIM 2 BROKEN -- v4 adds {kind} {name} and the migration omits it"
            )
        elif mig[key] != v4[key]:
            r.fail(
                f"CLAIM 2 BROKEN -- {kind} {name} is transcribed differently from the shipped file",
                f"shipped:     {v4[key]}\ntranscribed: {mig[key]}",
            )

    # --- extras in the migration ------------------------------------------
    for key in sorted(set(mig) - set(v4)):
        kind, name = key
        r.fail(
            f"the migration creates {kind} {name}, which is in neither v3 nor v4 -- "
            "an invention, remove it"
        )

    # --- claim 3: the statements the object claims cannot see --------------
    r3, r4, rm = (residuals(texts[k]) for k in ("v3", "v4", "migration"))
    added_res = {n: k for n, k in r4.items() if n not in r3}
    r.note(
        f"non-object statements -- v3 {len(r3)}, v4 {len(r4)}, migration {len(rm)}; "
        f"v4 adds {len(added_res)}"
    )
    for n, kind in sorted(added_res.items()):
        if n in rm:
            continue
        if COSMETIC.match(n):
            r.note(
                f"NOTE, annotation only -- v4 has a `{kind}` the migration omits: {n}"
            )
        else:
            r.fail(
                f"CLAIM 3 BROKEN -- v4 adds a `{kind}` statement and the migration omits it. "
                "Neither object claim can see this, so a PASS on those alone would hide it",
                n,
            )

    # --- shape checks the claims imply ------------------------------------
    if re.search(r"\balter\s+table\b", strip_sql_comments(texts["migration"]), re.I):
        r.fail(
            "the migration contains an ALTER TABLE. The v3 -> v4 delta is additive-only, "
            "so an ALTER means either the claim or the script is wrong"
        )
    if not re.search(r"\bbegin\b", strip_sql_comments(texts["migration"]), re.I):
        r.fail("the migration is not wrapped in a transaction")

    return r.emit()


if __name__ == "__main__":
    sys.exit(main())
