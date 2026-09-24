#!/usr/bin/env python
"""Generate the schema v2 reference from the DDL and its descriptions (CORE-2232).

Two sources, one output:

* ``legesher_i18n/db/schema_v2.sql`` is the single source of truth for what
  EXISTS: tables, columns, types, keys, constraints, indexes, triggers, views.
  It is parsed as text, never queried, so this runs in a fresh clone with no
  database.
* ``legesher_i18n/db/schema_v2.descriptions.yml`` holds every word of prose:
  what each object is for and why it is shaped the way it is.

The output is ``docs/schema-v2-reference.md``, committed and kept current by
``make check-generated``.

The previous hand-written reference rotted because nothing failed when the
schema moved and the prose did not. So this generator REFUSES, naming the
offender, whenever the two sources disagree:

* a table, column, view, trigger, section banner, pragma or seed insert in
  the SQL that has no description;
* a description of anything the SQL no longer has (indexes included);
* an enumerated column whose described values differ from its CHECK list;
* a ``[[name]]`` cross-reference in the prose that resolves to nothing;
* a comment in the SQL outside the header block and the section banners
  (prose belongs in the descriptions file, where it is rendered and checked);
* a parse that does not round-trip: the parsed structure is compared with
  SQLite's own reading of the same DDL in an in-memory database.

Usage::

    uv run python libs/i18n/scripts/generate_schema_reference.py
    uv run python libs/i18n/scripts/generate_schema_reference.py --out /tmp/x
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_I18N_ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = _I18N_ROOT / "legesher_i18n" / "db" / "schema_v2.sql"
DESCRIPTIONS_PATH = _I18N_ROOT / "legesher_i18n" / "db" / "schema_v2.descriptions.yml"
V1_SCHEMA_PATH = _I18N_ROOT / "legesher_i18n" / "db" / "schema.py"
OUT_DIR = _I18N_ROOT / "docs"
OUT_NAME = "schema-v2-reference.md"

REGENERATE_COMMAND = "make generate-schema-reference"

#: Repo-relative spellings used in messages and in the generated page.
_SQL_REL = "libs/i18n/legesher_i18n/db/schema_v2.sql"
_DESC_REL = "libs/i18n/legesher_i18n/db/schema_v2.descriptions.yml"
_V1_REL = "libs/i18n/legesher_i18n/db/schema.py"

_TOP_LEVEL_KEYS = {
    "overview",
    "scope",
    "pragmas",
    "sections",
    "tables",
    "views",
    "triggers",
}
_TABLE_KEYS = {"description", "columns", "notes", "indexes", "seed"}
_COLUMN_KEYS = {"description", "values"}

_PLACEHOLDER = re.compile(r"^\s*(TODO|TBD|FIXME|XXX)\b", re.IGNORECASE)
_REF = re.compile(r"\[\[([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?\]\]")
_RULE = re.compile(r"^=+$")


class SchemaReferenceError(Exception):
    """The SQL and the descriptions disagree, or the SQL could not be parsed."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass
class ForeignKey:
    columns: tuple[str, ...]
    table: str
    references: tuple[str, ...]
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"


@dataclass
class Column:
    name: str
    type: str
    not_null: bool = False
    primary_key: bool = False
    autoincrement: bool = False
    unique: bool = False
    default: str | None = None
    checks: list[str] = field(default_factory=list)
    references: ForeignKey | None = None
    generated: str | None = None
    generated_kind: str | None = None
    #: Allowed values, when a CHECK pins the column to an IN (...) list.
    values: list[str] | None = None


@dataclass
class Table:
    name: str
    section: str
    line: int
    columns: list[Column]
    constraints: list[str]
    primary_key: tuple[str, ...]
    foreign_keys: list[ForeignKey]
    without_rowid: bool
    sql: str


@dataclass
class Index:
    name: str
    table: str
    section: str
    line: int
    unique: bool
    columns: tuple[str, ...]
    where: str | None
    sql: str


@dataclass
class Trigger:
    name: str
    table: str
    section: str
    line: int
    timing: str
    event: str
    of_columns: tuple[str, ...]
    when: str | None
    messages: list[str]
    sql: str


@dataclass
class View:
    name: str
    section: str
    line: int
    sql: str


@dataclass
class Pragma:
    name: str
    value: str
    line: int
    sql: str


@dataclass
class Seed:
    table: str
    line: int
    columns: tuple[str, ...]
    rows: list[list[str]]


@dataclass
class Schema:
    sections: list[str]
    tables: dict[str, Table]
    indexes: dict[str, Index]
    triggers: dict[str, Trigger]
    views: dict[str, View]
    pragmas: dict[str, Pragma]
    seeds: dict[str, Seed]
    sqlite_requirement: str | None
    create_table_count: int
    #: The file's leading comment block, rendered verbatim on the page so that
    #: nothing the SQL says is missing from it.
    header: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lexing
# ---------------------------------------------------------------------------


@dataclass
class _Comment:
    line: int
    text: str
    own_line: bool


#: Quoting SQLite accepts but this schema never uses. Refused outright, so the
#: lexer below needs to know only two token kinds that can hide text (single-
#: quoted strings and ``--`` comments), and its idea of what is a comment is
#: therefore exactly SQLite's. A bracket identifier such as ``[/*]`` is quoted
#: to SQLite but not to a two-kind lexer, and that gap is enough to run SQL the
#: page never shows.
_FORBIDDEN_QUOTING = {
    '"': "double-quoted identifiers",
    "[": "bracket-quoted identifiers",
    "`": "backtick-quoted identifiers",
    "/*": "block comments",
}


def _strip_comments(text: str) -> tuple[str, list[_Comment], list[str]]:
    """Blank out ``--`` comments, keeping offsets and newlines.

    Quote-aware for single-quoted strings, so a ``--`` inside one is data.
    Returns the comment-free code, the comments, and a problem for every
    use of the quoting in :data:`_FORBIDDEN_QUOTING`.
    """
    out = list(text)
    comments: list[_Comment] = []
    problems: list[str] = []
    i, n, line = 0, len(text), 1
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
        elif ch == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    break
                if text[j] == "\n":
                    line += 1
                j += 1
            i = j + 1
        elif text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j == -1 else j
            start_of_line = text.rfind("\n", 0, i) + 1
            own_line = text[start_of_line:i].strip() == ""
            comments.append(_Comment(line, text[i + 2 : j].strip(), own_line))
            for k in range(i, j):
                out[k] = " "
            i = j
        else:
            token = "/*" if text.startswith("/*", i) else ch
            if token in _FORBIDDEN_QUOTING:
                problems.append(
                    f"{_SQL_REL}:{line}: {_FORBIDDEN_QUOTING[token]} are not part of this "
                    "schema's shape; use a plain name (or a `--` comment in the header)"
                )
            i += 1
    return "".join(out), comments, problems


def _statements(code: str) -> list[tuple[int, str]]:
    """Split comment-free DDL into statements, using SQLite's own tokenizer.

    ``sqlite3.complete_statement`` knows that a trigger body's semicolons do
    not end the CREATE TRIGGER, and that a ``;`` inside a string is data.
    Returns ``(line, statement)`` with the trailing semicolon removed.
    """
    statements: list[tuple[int, str]] = []
    start = 0
    pos = code.find(";")
    while pos != -1:
        chunk = code[start : pos + 1]
        if sqlite3.complete_statement(chunk):
            body = chunk[:-1]
            stripped = body.strip()
            if stripped:
                lead = len(body) - len(body.lstrip())
                line = code.count("\n", 0, start + lead) + 1
                statements.append((line, stripped))
            start = pos + 1
        pos = code.find(";", pos + 1)
    if code[start:].strip():
        line = code.count("\n", 0, start) + 1
        raise SchemaReferenceError(
            [f"{_SQL_REL}:{line}: trailing text is not a complete SQL statement"]
        )
    return statements


def _read_balanced(text: str, i: int) -> int:
    """Index just past the ``)`` matching the ``(`` at ``text[i]``."""
    depth = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "'\"":
            j = i + 1
            while j < n and not (text[j] == ch and (j + 1 >= n or text[j + 1] != ch)):
                j += 2 if text[j] == ch else 1
            i = j + 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced parentheses in: {text[:60]!r}")


def _split_top_level(text: str, sep: str = ",", raw: bool = False) -> list[str]:
    """Split on ``sep`` outside parentheses and quotes (``raw`` keeps whitespace)."""
    parts: list[str] = []
    depth, start, i, n = 0, 0, 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "'\"":
            j = i + 1
            while j < n and not (text[j] == ch and (j + 1 >= n or text[j + 1] != ch)):
                j += 2 if text[j] == ch else 1
            i = j + 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
        i += 1
    parts.append(text[start:])
    if raw:
        return [p for p in parts if p.strip()]
    return [p.strip() for p in parts if p.strip()]


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_sql_ws(text: str) -> str:
    """Collapse whitespace outside single-quoted literals; literals stay exact."""
    parts = re.split(r"('(?:[^']|'')*')", text)
    return "".join(
        part if i % 2 else re.sub(r"\s+", " ", part) for i, part in enumerate(parts)
    ).strip()


def _display_item(raw: str) -> str:
    """A table-body item, dedented by the column it starts at in the source.

    Keeps continuation lines' indentation relative to the item's first line,
    which a plain dedent of the continuation lines would flatten.
    """
    leading = raw[: len(raw) - len(raw.lstrip())]
    column = len(leading.split("\n")[-1])
    first, *rest = raw.strip().splitlines()
    out = [first.rstrip()]
    for line in rest:
        strip = min(column, len(line) - len(line.lstrip()))
        out.append(line[strip:].rstrip())
    return "\n".join(out)


def _display_check(check: str) -> str:
    """A column-level CHECK, continuation lines aligned under its opening paren."""
    first, *rest = check.strip().splitlines()
    if not rest:
        return f"CHECK ({first})"
    body = textwrap.indent(textwrap.dedent("\n".join(rest)), " " * len("CHECK ("))
    return f"CHECK ({first}\n{body.rstrip()})"


def _display_sql(sql: str) -> str:
    """A statement as it should read in the page: dedented, no trailing space."""
    lines = [line.rstrip() for line in sql.splitlines()]
    if len(lines) > 1:
        rest = textwrap.dedent("\n".join(lines[1:]))
        lines = [lines[0], *rest.splitlines()]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_CONSTRAINT_START = re.compile(
    r"^(PRIMARY\s+KEY|NOT\s+NULL|NULL|UNIQUE|CHECK|DEFAULT|REFERENCES|GENERATED|"
    r"COLLATE|CONSTRAINT|AS)\b",
    re.IGNORECASE,
)
_ON_ACTION = re.compile(
    r"^ON\s+(DELETE|UPDATE)\s+(SET\s+NULL|SET\s+DEFAULT|CASCADE|RESTRICT|NO\s+ACTION)",
    re.IGNORECASE,
)


def _parse_fk_tail(tail: str, fk: ForeignKey) -> str:
    tail = tail.lstrip()
    while True:
        m = _ON_ACTION.match(tail)
        if not m:
            return tail
        action = _normalize_ws(m.group(2)).upper()
        if m.group(1).upper() == "DELETE":
            fk.on_delete = action
        else:
            fk.on_update = action
        tail = tail[m.end() :].lstrip()


def _enum_values(check: str, column: str) -> list[str] | None:
    """The IN-list of ``col IN (...)`` or ``col IS NULL OR col IN (...)``."""
    m = re.fullmatch(
        rf"(?:{column}\s+IS\s+NULL\s+OR\s+)?{column}\s+IN\s*\((.*)\)",
        _normalize_sql_ws(check),
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    values = []
    for item in _split_top_level(m.group(1)):
        if re.fullmatch(r"'(?:[^']|'')*'", item):
            values.append(item[1:-1].replace("''", "'"))
        elif re.fullmatch(r"-?\d+", item):
            values.append(item)
        else:
            return None
    return values


def _parse_column(table: str, item: str) -> Column:
    m = re.match(r'\s*"?(\w+)"?\s*(.*)', item, re.DOTALL)
    if not m:
        raise ValueError(f"table {table}: cannot read a column from {item!r}")
    name, rest = m.group(1), m.group(2)
    type_words: list[str] = []
    while rest and not _CONSTRAINT_START.match(rest):
        tm = re.match(r"([A-Za-z]+(?:\s*\([^)]*\))?)\s*", rest)
        if not tm:
            break
        type_words.append(tm.group(1))
        rest = rest[tm.end() :]
    col = Column(name=name, type=" ".join(type_words))
    while rest.strip():
        rest = rest.lstrip()
        if m := re.match(
            r"PRIMARY\s+KEY(?:\s+(?:ASC|DESC))?(\s+AUTOINCREMENT)?", rest, re.IGNORECASE
        ):
            col.primary_key = True
            col.autoincrement = bool(m.group(1))
        elif m := re.match(r"NOT\s+NULL", rest, re.IGNORECASE):
            col.not_null = True
        elif m := re.match(r"UNIQUE\b", rest, re.IGNORECASE):
            col.unique = True
        elif m := re.match(r"CHECK\s*(?=\()", rest, re.IGNORECASE):
            end = _read_balanced(rest, m.end())
            col.checks.append(rest[m.end() + 1 : end - 1].strip())
            rest = rest[end:]
            continue
        elif m := re.match(r"DEFAULT\s+", rest, re.IGNORECASE):
            after = rest[m.end() :]
            if after.startswith("("):
                end = _read_balanced(after, 0)
            else:
                dm = re.match(r"'(?:[^']|'')*'|[-+]?\d+(?:\.\d+)?|\w+", after)
                if not dm:
                    raise ValueError(f"{table}.{name}: unreadable DEFAULT in {rest!r}")
                end = dm.end()
            col.default = after[:end]
            rest = after[end:]
            continue
        elif m := re.match(r"REFERENCES\s+(\w+)\s*\(([^)]*)\)", rest, re.IGNORECASE):
            fk = ForeignKey(
                (name,), m.group(1), tuple(c.strip() for c in m.group(2).split(","))
            )
            col.references = fk
            rest = _parse_fk_tail(rest[m.end() :], fk)
            continue
        elif m := re.match(r"GENERATED\s+ALWAYS\s+AS\s*(?=\()", rest, re.IGNORECASE):
            end = _read_balanced(rest, m.end())
            col.generated = rest[m.end() + 1 : end - 1].strip()
            rest = rest[end:].lstrip()
            km = re.match(r"(STORED|VIRTUAL)\b", rest, re.IGNORECASE)
            col.generated_kind = km.group(1).upper() if km else "VIRTUAL"
            rest = rest[km.end() :] if km else rest
            continue
        else:
            raise ValueError(
                f"table {table}: column {name}: cannot parse {_normalize_ws(rest)[:50]!r}"
            )
        rest = rest[m.end() :]
    enums = [v for v in (_enum_values(c, name) for c in col.checks) if v is not None]
    if len(enums) > 1:
        raise ValueError(
            f"table {table}: column {name} has {len(enums)} IN-list CHECKs; the page "
            "shows one list of allowed values, so merge them into one"
        )
    col.values = enums[0] if enums else None
    return col


_TABLE_CONSTRAINT = re.compile(
    r"\s*(PRIMARY\s+KEY|UNIQUE|CHECK|FOREIGN\s+KEY|CONSTRAINT)\s*[(\s]", re.IGNORECASE
)


def _parse_table(section: str, line: int, stmt: str) -> Table:
    m = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\(", stmt, re.IGNORECASE)
    if m is None:
        raise ValueError(
            f"cannot read a table name from {_normalize_ws(stmt)[:60]!r} "
            "(IF NOT EXISTS, TEMP and quoted names are not part of this schema's shape)"
        )
    name = m.group(1)
    open_paren = m.end() - 1
    close = _read_balanced(stmt, open_paren)
    body = stmt[open_paren + 1 : close - 1]
    trailer = stmt[close:].strip()
    if trailer and not re.fullmatch(r"WITHOUT\s+ROWID", trailer, re.IGNORECASE):
        raise ValueError(
            f"table {name}: unexpected text after the column list: {trailer!r}"
        )
    columns: list[Column] = []
    constraints: list[str] = []
    primary_key: tuple[str, ...] = ()
    foreign_keys: list[ForeignKey] = []
    for raw_item in _split_top_level(body, raw=True):
        item = raw_item.strip()
        # A word boundary, not a prefix: `checked_at` is a column, not a CHECK.
        if _TABLE_CONSTRAINT.match(item):
            constraints.append(_display_item(raw_item))
            if pk := re.match(r"PRIMARY\s+KEY\s*\(([^)]*)\)", item, re.IGNORECASE):
                primary_key = tuple(c.strip() for c in pk.group(1).split(","))
            if fkm := re.match(
                r"FOREIGN\s+KEY\s*\(([^)]*)\)\s*REFERENCES\s+(\w+)\s*\(([^)]*)\)",
                item,
                re.IGNORECASE,
            ):
                fk = ForeignKey(
                    tuple(c.strip() for c in fkm.group(1).split(",")),
                    fkm.group(2),
                    tuple(c.strip() for c in fkm.group(3).split(",")),
                )
                _parse_fk_tail(item[fkm.end() :], fk)
                foreign_keys.append(fk)
        else:
            columns.append(_parse_column(name, item))
    if not primary_key:
        primary_key = tuple(c.name for c in columns if c.primary_key)
    foreign_keys = [c.references for c in columns if c.references] + foreign_keys
    return Table(
        name=name,
        section=section,
        line=line,
        columns=columns,
        constraints=constraints,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        without_rowid=bool(trailer),
        sql=_display_sql(stmt),
    )


_INDEX = re.compile(
    r"CREATE\s+(UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)\s*\(([^)]*)\)\s*(?:WHERE\s+(.*))?",
    re.IGNORECASE | re.DOTALL,
)
_TRIGGER = re.compile(
    r"CREATE\s+TRIGGER\s+(?P<name>\w+)\s+(?P<timing>BEFORE|AFTER|INSTEAD\s+OF)\s+"
    r"(?P<event>INSERT|UPDATE|DELETE)(?:\s+OF\s+(?P<of>.*?))?\s+ON\s+(?P<table>\w+)"
    r"(?:\s+FOR\s+EACH\s+ROW)?(?:\s+WHEN\s+(?P<when>.*?))?\s+BEGIN\b(?P<body>.*)\bEND",
    re.IGNORECASE | re.DOTALL,
)
_RAISE = re.compile(
    r"RAISE\s*\(\s*(?:ABORT|FAIL|ROLLBACK)\s*,\s*'((?:[^']|'')*)'\s*\)", re.IGNORECASE
)


def _parse_banners(comments: list[_Comment]) -> dict[int, str]:
    """``{line: title}`` for every three-line ``-- ====`` banner."""
    by_line = {c.line: c.text for c in comments if c.own_line}
    banners = {}
    for line, text in by_line.items():
        if (
            not _RULE.match(text)
            and _RULE.match(by_line.get(line - 1, "") or "x")
            and _RULE.match(by_line.get(line + 1, "") or "x")
        ):
            banners[line] = text
    return banners


def _header_lines(sql_text: str) -> set[int]:
    """Line numbers of the leading comment block (the file header)."""
    lines = set()
    for number, line in enumerate(sql_text.splitlines(), start=1):
        if not line.lstrip().startswith("--"):
            break
        lines.add(number)
    return lines


def parse_schema(sql_text: str) -> Schema:
    """Parse ``schema_v2.sql`` text into a :class:`Schema`.

    Raises:
        SchemaReferenceError: on an unparseable statement or a comment that is
            neither the file header nor a section banner.
    """
    code, comments, problems = _strip_comments(sql_text)
    banners = _parse_banners(comments)
    header = _header_lines(sql_text)

    banner_lines = set()
    for line in banners:
        banner_lines |= {line - 1, line, line + 1}
    for c in comments:
        if c.line in header or c.line in banner_lines:
            continue
        problems.append(
            f"{_SQL_REL}:{c.line}: comment outside the header and section banners "
            f"({c.text[:50]!r}). The SQL carries structure only; move this prose to "
            f"{_DESC_REL}, where it is rendered and checked."
        )

    requirement = None
    for line in sorted(header):
        m = re.search(
            r"Requires SQLite\s*>=\s*([\d.]+)", sql_text.splitlines()[line - 1]
        )
        if m:
            requirement = m.group(1)

    schema = Schema([], {}, {}, {}, {}, {}, {}, requirement, 0)
    source_lines = sql_text.splitlines()
    schema.header = [
        re.sub(r"^\s*-- ?", "", source_lines[line - 1]) for line in sorted(header)
    ]
    schema.sections = [banners[line] for line in sorted(banners)]
    for title in {t for t in schema.sections if schema.sections.count(t) > 1}:
        problems.append(
            f"{_SQL_REL}: section banner `{title}` appears more than once; "
            "each section is rendered once, so merge them or rename one"
        )
    schema.create_table_count = len(
        re.findall(r"^\s*CREATE\s+TABLE\b", sql_text, re.IGNORECASE | re.MULTILINE)
    )
    banner_starts = sorted(banners)

    for line, stmt in _statements(code):
        above = [b for b in banner_starts if b < line]
        section = banners[above[-1]] if above else ""
        upper = stmt.upper()
        if not section and not upper.startswith("PRAGMA"):
            problems.append(
                f"{_SQL_REL}:{line}: {_normalize_ws(stmt)[:40]!r} comes before the first "
                "section banner; the page renders objects by section, so it would be lost"
            )
            continue
        try:
            if re.match(r"CREATE\s+TABLE\b", upper):
                table = _parse_table(section, line, stmt)
                schema.tables[table.name] = table
            elif m := _INDEX.fullmatch(stmt):
                schema.indexes[m.group(2)] = Index(
                    name=m.group(2),
                    table=m.group(3),
                    section=section,
                    line=line,
                    unique=bool(m.group(1)),
                    columns=tuple(c.strip() for c in m.group(4).split(",")),
                    where=_normalize_sql_ws(m.group(5)) if m.group(5) else None,
                    sql=_display_sql(stmt),
                )
            elif m := _TRIGGER.fullmatch(stmt):
                of = m.group("of")
                schema.triggers[m.group("name")] = Trigger(
                    name=m.group("name"),
                    table=m.group("table"),
                    section=section,
                    line=line,
                    timing=_normalize_ws(m.group("timing")).upper(),
                    event=m.group("event").upper(),
                    of_columns=tuple(_normalize_ws(c) for c in of.split(","))
                    if of
                    else (),
                    when=m.group("when"),
                    messages=[msg.replace("''", "'") for msg in _RAISE.findall(stmt)],
                    sql=_display_sql(stmt),
                )
            elif m := re.fullmatch(
                r"CREATE\s+VIEW\s+(\w+)\s+AS\s+.*", stmt, re.I | re.S
            ):
                schema.views[m.group(1)] = View(
                    m.group(1), section, line, _display_sql(stmt)
                )
            elif m := re.fullmatch(r"PRAGMA\s+(\w+)\s*=\s*(\w+)", stmt, re.IGNORECASE):
                if m.group(1) in schema.pragmas:
                    raise ValueError(
                        f"PRAGMA {m.group(1)} is set twice; the page shows one setting"
                    )
                schema.pragmas[m.group(1)] = Pragma(m.group(1), m.group(2), line, stmt)
            elif m := re.fullmatch(
                r"INSERT\s+INTO\s+(\w+)\s*\(([^)]*)\)\s*VALUES\s*(.*)",
                stmt,
                re.I | re.S,
            ):
                if m.group(1) in schema.seeds:
                    raise ValueError(
                        f"a second seed INSERT into {m.group(1)}; merge it into the "
                        f"first (line {schema.seeds[m.group(1)].line}) so the page shows every row"
                    )
                rows = []
                for row in _split_top_level(m.group(3)):
                    if not (row.startswith("(") and row.endswith(")")):
                        raise ValueError(f"seed row is not a tuple: {row!r}")
                    rows.append(_split_top_level(row[1:-1]))
                schema.seeds[m.group(1)] = Seed(
                    m.group(1),
                    line,
                    tuple(c.strip() for c in m.group(2).split(",")),
                    rows,
                )
            else:
                problems.append(
                    f"{_SQL_REL}:{line}: unrecognised statement "
                    f"{_normalize_ws(stmt)[:60]!r}; teach the generator this shape"
                )
        except ValueError as exc:
            problems.append(f"{_SQL_REL}:{line}: {exc}")

    if problems:
        raise SchemaReferenceError(problems)
    return schema


# ---------------------------------------------------------------------------
# Round trip: the parse must agree with SQLite's own reading of the DDL
# ---------------------------------------------------------------------------


def _unwrap(default: str | None) -> str | None:
    """A DEFAULT as ``PRAGMA table_info`` reports it: one outer paren pair dropped."""
    if (
        default
        and default.startswith("(")
        and _read_balanced(default, 0) == len(default)
    ):
        return default[1:-1]
    return default


def _seed_values(seed: Seed) -> list[tuple]:
    """Each parsed seed row, evaluated by SQLite: the values the INSERT stores."""
    conn = sqlite3.connect(":memory:")
    try:
        return [
            conn.execute(f"SELECT {', '.join(row)}").fetchone()  # nosec B608 - the repo's own seed literals, in :memory:
            for row in seed.rows
        ]
    finally:
        conn.close()


def verify_round_trip(schema: Schema, sql_text: str) -> list[str]:
    """Compare the parsed model with an in-memory build of the same DDL.

    The generator never reads a database file; this builds the schema in
    ``:memory:`` purely to prove the text parse missed nothing: every table,
    column (name, order, type, NOT NULL, default, key position, generated
    kind), foreign key and index must agree; triggers and views must agree
    on name and owning table (their bodies are rendered verbatim from the
    text, so there is nothing further to drift); and the seed rows must equal
    what SQLite stores.
    """
    problems: list[str] = []
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(sql_text)

        def names(kind: str) -> set[str]:
            return {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = ? AND sql IS NOT NULL "
                    "AND name NOT LIKE 'sqlite_%'",
                    (kind,),
                )
            }

        tables = names("table")
        if schema.create_table_count != len(schema.tables) or len(tables) != len(
            schema.tables
        ):
            problems.append(
                f"round trip: {schema.create_table_count} CREATE TABLE statements in the "
                f"text, {len(schema.tables)} parsed, {len(tables)} built by SQLite"
            )
        for kind, parsed in (
            ("table", schema.tables),
            ("index", schema.indexes),
            ("trigger", schema.triggers),
            ("view", schema.views),
        ):
            built = names(kind)
            for missing in sorted(built - set(parsed)):
                problems.append(
                    f"round trip: SQLite built {kind} {missing}; the parse missed it"
                )
            for extra in sorted(set(parsed) - built):
                problems.append(
                    f"round trip: parsed {kind} {extra}; SQLite has no such {kind}"
                )

        for table in schema.tables.values():
            if table.name not in tables:
                continue
            info = conn.execute(f"PRAGMA table_xinfo({table.name})").fetchall()
            built_cols = [row[1] for row in info]
            parsed_cols = [c.name for c in table.columns]
            if built_cols != parsed_cols:
                problems.append(
                    f"round trip: {table.name} columns parsed as {parsed_cols}, "
                    f"SQLite has {built_cols}"
                )
                continue
            for (_, name, type_, notnull, default, pk, hidden), col in zip(
                info, table.columns
            ):
                parsed_pk = (
                    table.primary_key.index(name) + 1
                    if name in table.primary_key
                    else 0
                )
                parsed_hidden = {None: 0, "VIRTUAL": 2, "STORED": 3}[col.generated_kind]
                expected = (type_.upper(), bool(notnull), default, pk, hidden)
                got = (
                    col.type.upper(),
                    # A WITHOUT ROWID table's key columns are NOT NULL implicitly.
                    col.not_null or (table.without_rowid and parsed_pk > 0),
                    _unwrap(col.default),
                    parsed_pk,
                    parsed_hidden,
                )
                if expected != got:
                    problems.append(
                        f"round trip: {table.name}.{name} parsed as "
                        f"(type, not_null, default, pk, hidden) = {got}, SQLite has {expected}"
                    )
            built_fks = {}
            for row in conn.execute(f"PRAGMA foreign_key_list({table.name})"):
                fk_id, _, ref, frm, to, on_update, on_delete, _ = row
                cols, refs, _, _, _ = built_fks.get(
                    fk_id, ((), (), ref, on_update, on_delete)
                )
                built_fks[fk_id] = (
                    cols + (frm,),
                    refs + (to,),
                    ref,
                    on_update,
                    on_delete,
                )
            built_fk_set = {
                (cols, ref, refs, on_delete, on_update)
                for cols, refs, ref, on_update, on_delete in built_fks.values()
            }
            parsed_fk_set = {
                (fk.columns, fk.table, fk.references, fk.on_delete, fk.on_update)
                for fk in table.foreign_keys
            }
            if built_fk_set != parsed_fk_set:
                problems.append(
                    f"round trip: {table.name} foreign keys parsed as "
                    f"{sorted(parsed_fk_set)}, SQLite has {sorted(built_fk_set)}"
                )

        owners = dict(
            conn.execute(
                "SELECT name, tbl_name FROM sqlite_master WHERE type IN ('index', 'trigger')"
            ).fetchall()
        )
        for kind, objects in (("index", schema.indexes), ("trigger", schema.triggers)):
            for obj in objects.values():
                if obj.name in owners and owners[obj.name] != obj.table:
                    problems.append(
                        f"round trip: {kind} {obj.name} parsed as on {obj.table}, "
                        f"SQLite has it on {owners[obj.name]}"
                    )

        for seed in schema.seeds.values():
            if seed.table not in tables:
                continue
            columns = ", ".join(seed.columns)
            built_rows = conn.execute(
                f"SELECT {columns} FROM {seed.table}"  # nosec B608 - parsed identifiers
            ).fetchall()
            if sorted(map(repr, built_rows)) != sorted(map(repr, _seed_values(seed))):
                problems.append(
                    f"round trip: the seed rows of {seed.table} as parsed are not the rows "
                    "SQLite holds after the build"
                )

        for index in schema.indexes.values():
            built = tuple(
                row[2] for row in conn.execute(f"PRAGMA index_info({index.name})")
            )
            if built != index.columns:
                problems.append(
                    f"round trip: index {index.name} parsed on {index.columns}, "
                    f"SQLite has {built}"
                )
    except sqlite3.Error as exc:
        problems.append(f"round trip: SQLite could not build {_SQL_REL}: {exc}")
    finally:
        conn.close()
    return problems


# ---------------------------------------------------------------------------
# Descriptions: loading and the two-sided coverage check
# ---------------------------------------------------------------------------


class _UniqueKeyLoader(yaml.SafeLoader):
    """A SafeLoader that refuses duplicate mapping keys.

    Plain ``yaml.safe_load`` keeps the LAST of two same-named keys, so a second
    description of one column would silently erase the first.
    """


def _construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
    seen: dict[Any, int] = {}
    for key_node, _ in node.value:
        key = loader.construct_object(key_node)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f"duplicate key {key!r} (first at line {seen[key] + 1})",
                key_node.start_mark,
            )
        seen[key] = key_node.start_mark.line
    return loader.construct_mapping(node)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_descriptions(text: str) -> dict:
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)  # nosec B506 - SafeLoader subclass
    except yaml.YAMLError as exc:
        raise SchemaReferenceError([f"{_DESC_REL}: {exc}"]) from exc
    if not isinstance(data, dict):
        raise SchemaReferenceError(
            [f"{_DESC_REL}: expected a mapping at the top level"]
        )
    return data


#: Markdown that can hide or restructure the rest of the page when a
#: description is dropped into it. Descriptions are prose, lists and fenced
#: blocks; the page owns its own headings, comments and <details> blocks. The
#: raw-HTML starts listed are the CommonMark block kinds that run until an end
#: tag, so an unclosed one swallows every later section.
_UNSAFE_MARKDOWN = re.compile(
    r"<!--|-->|</?details\b|</?summary\b|^\s{0,3}#{1,6}\s"
    r"|^\s{0,3}<(?:pre|script|style|textarea)\b|<\?|<!\[CDATA\[",
    re.M | re.IGNORECASE,
)
#: A line of only ``=`` or ``-`` under a text line is a setext heading.
_SETEXT_UNDERLINE = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")


def _setext_heading(value: str) -> bool:
    fenced, previous = False, ""
    for line in value.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
        elif not fenced and previous.strip() and _SETEXT_UNDERLINE.match(line):
            return True
        previous = "" if fenced else line
    return False


def _text_problem(where: str, value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{_DESC_REL}: {where}: expected a non-empty description"
    if _PLACEHOLDER.match(value):
        return f"{_DESC_REL}: {where}: a placeholder is not a description"
    if m := _UNSAFE_MARKDOWN.search(value):
        return (
            f"{_DESC_REL}: {where}: {m.group(0).strip()!r} would hide or restructure "
            "the page around it; descriptions may not contain HTML comments, "
            "<details>/<summary>, headings or unclosed raw-HTML blocks"
        )
    if _setext_heading(value):
        return (
            f"{_DESC_REL}: {where}: a line of only '=' or '-' under text is a "
            "heading; descriptions may not contain headings"
        )
    if len(re.findall(r"^\s*(```|~~~)", value, re.M)) % 2:
        return f"{_DESC_REL}: {where}: an unclosed code fence would swallow the page"
    return None


def _mapping(data: dict, key: str, problems: list[str]) -> dict:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        problems.append(f"{_DESC_REL}: {key}: expected a mapping")
        return {}
    return value


def _two_sided(
    kind: str,
    in_sql: dict[str, int],
    described: dict,
    where: str,
    problems: list[str],
) -> None:
    """Every SQL object described, every description backed by the SQL."""
    for name, line in in_sql.items():
        if name not in described:
            problems.append(
                f"{_SQL_REL}:{line}: {kind} `{name}` has no description; "
                f"add it under `{where}` in {_DESC_REL}"
            )
    for name in described:
        if name not in in_sql:
            problems.append(
                f"{_DESC_REL}: {where}.{name}: describes {kind} `{name}`, "
                f"which {_SQL_REL} does not have; remove or rename the description"
            )


def check_descriptions(schema: Schema, desc: dict) -> list[str]:
    """Every way the SQL and the descriptions can disagree, one line each."""
    problems: list[str] = []
    for key in desc:
        if key not in _TOP_LEVEL_KEYS:
            problems.append(f"{_DESC_REL}: unknown top-level key `{key}`")
    for key in ("overview", "scope"):
        if (p := _text_problem(key, desc.get(key))) is not None:
            problems.append(p)

    sections = _mapping(desc, "sections", problems)
    tables = _mapping(desc, "tables", problems)
    views = _mapping(desc, "views", problems)
    triggers = _mapping(desc, "triggers", problems)
    pragmas = _mapping(desc, "pragmas", problems)

    _two_sided(
        "section banner",
        {s: 0 for s in schema.sections},
        sections,
        "sections",
        problems,
    )
    _two_sided(
        "table",
        {n: t.line for n, t in schema.tables.items()},
        tables,
        "tables",
        problems,
    )
    _two_sided(
        "view", {n: v.line for n, v in schema.views.items()}, views, "views", problems
    )
    _two_sided(
        "trigger",
        {n: t.line for n, t in schema.triggers.items()},
        triggers,
        "triggers",
        problems,
    )
    _two_sided(
        "pragma",
        {n: p.line for n, p in schema.pragmas.items()},
        pragmas,
        "pragmas",
        problems,
    )
    problems[:] = [p.replace(f"{_SQL_REL}:0: ", f"{_SQL_REL}: ") for p in problems]

    for group, entries in (
        ("sections", sections),
        ("views", views),
        ("triggers", triggers),
        ("pragmas", pragmas),
    ):
        for name, value in entries.items():
            if (p := _text_problem(f"{group}.{name}", value)) is not None:
                problems.append(p)

    for name, entry in tables.items():
        table = schema.tables.get(name)
        if table is None:
            continue
        where = f"tables.{name}"
        if not isinstance(entry, dict):
            problems.append(
                f"{_DESC_REL}: {where}: expected a mapping with `description` and `columns`"
            )
            continue
        for key in entry:
            if key not in _TABLE_KEYS:
                problems.append(f"{_DESC_REL}: {where}: unknown key `{key}`")
        if (
            p := _text_problem(f"{where}.description", entry.get("description"))
        ) is not None:
            problems.append(p)
        if "notes" in entry and (p := _text_problem(f"{where}.notes", entry["notes"])):
            problems.append(p)

        columns = entry.get("columns") or {}
        if not isinstance(columns, dict):
            problems.append(f"{_DESC_REL}: {where}.columns: expected a mapping")
            columns = {}
        by_name = {c.name: c for c in table.columns}
        for col in table.columns:
            if col.name not in columns:
                problems.append(
                    f"{_SQL_REL}:{table.line}: column `{name}.{col.name}` has no "
                    f"description; add it under `{where}.columns` in {_DESC_REL}"
                )
        for col_name, value in columns.items():
            cwhere = f"{where}.columns.{col_name}"
            col = by_name.get(col_name)
            if col is None:
                problems.append(
                    f"{_DESC_REL}: {cwhere}: describes column `{name}.{col_name}`, which "
                    f"{_SQL_REL} does not have; remove or rename the description"
                )
                continue
            if isinstance(value, dict):
                for key in value:
                    if key not in _COLUMN_KEYS:
                        problems.append(f"{_DESC_REL}: {cwhere}: unknown key `{key}`")
                text = value.get("description")
                described_values = value.get("values")
            else:
                text, described_values = value, None
            if (p := _text_problem(cwhere, text)) is not None:
                problems.append(p)
            if described_values is None:
                continue
            if col.values is None:
                problems.append(
                    f"{_DESC_REL}: {cwhere}.values: `{name}.{col_name}` has no CHECK (... IN "
                    f"(...)) list in {_SQL_REL}, so there are no values to describe"
                )
                continue
            if not isinstance(described_values, dict):
                problems.append(f"{_DESC_REL}: {cwhere}.values: expected a mapping")
                continue
            bad = [k for k in described_values if not isinstance(k, str)]
            if bad:
                problems.append(
                    f"{_DESC_REL}: {cwhere}.values: keys {bad!r} are not strings; quote "
                    "them (YAML reads 0, 1, yes, on as numbers and booleans)"
                )
                continue
            keys = list(described_values)
            for missing in [v for v in col.values if v not in keys]:
                problems.append(
                    f"{_SQL_REL}:{table.line}: value '{missing}' of `{name}.{col_name}` "
                    f"has no description; add it under `{cwhere}.values`"
                )
            for orphan in [k for k in keys if k not in col.values]:
                problems.append(
                    f"{_DESC_REL}: {cwhere}.values.{orphan}: '{orphan}' is not an allowed "
                    f"value of `{name}.{col_name}` in {_SQL_REL}"
                )
            for key, text in described_values.items():
                if (p := _text_problem(f"{cwhere}.values.{key}", text)) is not None:
                    problems.append(p)

        indexes = entry.get("indexes") or {}
        if not isinstance(indexes, dict):
            problems.append(f"{_DESC_REL}: {where}.indexes: expected a mapping")
            indexes = {}
        for index_name, text in indexes.items():
            index = schema.indexes.get(index_name)
            if index is None or index.table != name:
                problems.append(
                    f"{_DESC_REL}: {where}.indexes.{index_name}: {_SQL_REL} has no index "
                    f"`{index_name}` on `{name}`; remove or move the description"
                )
            elif (
                p := _text_problem(f"{where}.indexes.{index_name}", text)
            ) is not None:
                problems.append(p)

        if name in schema.seeds and "seed" not in entry:
            problems.append(
                f"{_SQL_REL}:{schema.seeds[name].line}: the seed INSERT into `{name}` has no "
                f"description; add `{where}.seed` in {_DESC_REL}"
            )
        if "seed" in entry:
            if name not in schema.seeds:
                problems.append(
                    f"{_DESC_REL}: {where}.seed: {_SQL_REL} has no seed INSERT into `{name}`"
                )
            elif (p := _text_problem(f"{where}.seed", entry["seed"])) is not None:
                problems.append(p)

    for trigger in schema.triggers.values():
        if trigger.table not in schema.tables:
            problems.append(
                f"{_SQL_REL}:{trigger.line}: trigger `{trigger.name}` is on `{trigger.table}`, "
                "which is not a table; the page documents triggers with their table"
            )
    for index in schema.indexes.values():
        if index.table not in schema.tables:
            problems.append(
                f"{_SQL_REL}:{index.line}: index `{index.name}` is on `{index.table}`, "
                "which is not a table name as written (names are matched exactly)"
            )
    for seed in schema.seeds:
        if seed not in schema.tables:
            problems.append(f"{_SQL_REL}: seed INSERT into unknown table `{seed}`")

    for where, text in _all_prose(desc):
        for m in re.finditer(r"\[\[(.*?)\]\]", text):
            if not _REF.fullmatch(m.group(0)):
                problems.append(
                    f"{_DESC_REL}: {where}: malformed cross-reference {m.group(0)}; "
                    "write [[name]] or [[table.column]]"
                )
        for m in _REF.finditer(text):
            obj, column = m.group(1), m.group(2)
            if column is not None:
                table = schema.tables.get(obj)
                if table is None or column not in {c.name for c in table.columns}:
                    problems.append(
                        f"{_DESC_REL}: {where}: cross-reference [[{obj}.{column}]] names no "
                        f"column in {_SQL_REL}"
                    )
            elif not _object_exists(schema, obj):
                problems.append(
                    f"{_DESC_REL}: {where}: cross-reference [[{obj}]] names nothing in {_SQL_REL}"
                )
    return problems


def _object_exists(schema: Schema, name: str) -> bool:
    return any(
        name in group
        for group in (schema.tables, schema.views, schema.triggers, schema.indexes)
    )


def _all_prose(desc: dict) -> list[tuple[str, str]]:
    """Every string in the descriptions, with its dotted location."""
    found: list[tuple[str, str]] = []

    def walk(where: str, value: Any) -> None:
        if isinstance(value, str):
            found.append((where, value))
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(f"{where}.{key}" if where else str(key), item)

    walk("", desc)
    return found


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _anchor(name: str) -> str:
    """The id GitHub gives a heading: lowercase, punctuation dropped, spaces to -."""
    return re.sub(r"[^\w\- ]", "", name.lower()).replace(" ", "-")


def _resolve_refs(text: str, schema: Schema) -> str:
    def replace(m: re.Match) -> str:
        obj, column = m.group(1), m.group(2)
        label = f"{obj}.{column}" if column else obj
        return f"[`{label}`](#{_anchor(obj)})"

    # Inside an inline code span a link would render as literal text, so a
    # [[ref]] there is left as written.
    parts = re.split(r"(`+[^`]*?`+)", text)
    return "".join(
        part if i % 2 else _REF.sub(replace, part) for i, part in enumerate(parts)
    )


def _prose(text: str, schema: Schema, indent: str = "") -> list[str]:
    body = _resolve_refs(textwrap.dedent(text).strip(), schema)
    return [f"{indent}{line}" if line else "" for line in body.splitlines()]


def _code(value: str) -> str:
    """Inline code that survives backticks and pipes in the value."""
    fence = "``" if "`" in value else "`"
    pad = " " if value.startswith("`") or value.endswith("`") else ""
    return f"{fence}{pad}{value}{pad}{fence}"


def _column_line(table: Table, col: Column, long_checks: list[str]) -> str:
    parts = [
        f"**`{col.name}`**",
        _code(col.type) if col.type else "*(no declared type)*",
    ]
    if col.primary_key or (
        col.name in table.primary_key and len(table.primary_key) == 1
    ):
        parts.append("primary key" + (", autoincrement" if col.autoincrement else ""))
    elif col.name in table.primary_key:
        parts.append("part of the primary key")
    if col.not_null:
        parts.append("not null")
    if col.unique:
        parts.append("unique")
    if col.default is not None:
        parts.append(f"default {_code(col.default)}")
    if col.generated is not None:
        parts.append(
            f"generated {_code(_normalize_sql_ws(col.generated))} {col.generated_kind}"
        )
    if col.references is not None:
        fk = col.references
        ref = f"references [`{fk.table}`](#{_anchor(fk.table)})`({', '.join(fk.references)})`"
        if fk.on_delete != "NO ACTION":
            ref += f" on delete {fk.on_delete.lower()}"
        if fk.on_update != "NO ACTION":
            ref += f" on update {fk.on_update.lower()}"
        parts.append(ref)
    for check in col.checks:
        flat = _normalize_sql_ws(check)
        if col.values is not None and _enum_values(check, col.name) is not None:
            continue
        if "\n" in check or len(flat) > 70:
            long_checks.append(f"-- {col.name}\n{_display_check(check)}")
            parts.append("check: see constraints")
        else:
            parts.append(f"check {_code(flat)}")
    return "- " + " · ".join(parts)


def _render_table(table: Table, desc: dict, schema: Schema) -> list[str]:
    entry = desc["tables"][table.name]
    out = [f"### `{table.name}`", ""]
    if table.without_rowid:
        out += ["*`WITHOUT ROWID` table.*", ""]
    out += _prose(entry["description"], schema)
    out += ["", "**Columns**", ""]
    long_checks: list[str] = []
    for col in table.columns:
        value = entry["columns"][col.name]
        text = value["description"] if isinstance(value, dict) else value
        described = value.get("values") if isinstance(value, dict) else None
        out.append(_column_line(table, col, long_checks))
        out.append("")
        out += _prose(text, schema, indent="  ")
        if col.values is not None:
            out.append("")
            if described:
                out.append("  Allowed values:")
                out.append("")
                for v in col.values:
                    meaning = _resolve_refs(_normalize_ws(described[v]), schema)
                    out.append(f"  - {_code(v)}: {meaning}")
            else:
                out.append(
                    "  Allowed values: " + ", ".join(_code(v) for v in col.values) + "."
                )
        out.append("")

    constraints = table.constraints + long_checks
    if constraints:
        out += ["**Constraints**", "", "```sql"]
        for c in table.constraints:
            out.append(c)
        for c in long_checks:
            out.append(c)
        out += ["```", ""]
    if "notes" in entry:
        out += _prose(entry["notes"], schema)
        out.append("")

    indexes = [i for i in schema.indexes.values() if i.table == table.name]
    if indexes:
        out += ["**Indexes**", ""]
        notes = entry.get("indexes") or {}
        for index in indexes:
            line = f'- <a id="{_anchor(index.name)}"></a>`{index.name}`: '
            line += "unique on " if index.unique else "on "
            line += ", ".join(_code(c) for c in index.columns)
            if index.where:
                line += f" where {_code(index.where)}"
            out.append(line)
            if index.name in notes:
                out += ["", *_prose(notes[index.name], schema, indent="  ")]
            out.append("")

    triggers = [t for t in schema.triggers.values() if t.table == table.name]
    if triggers:
        out += ["**Triggers**", ""]
        for trigger in triggers:
            out += _render_trigger(trigger, desc["triggers"][trigger.name], schema)

    if table.name in schema.seeds:
        seed = schema.seeds[table.name]
        out += ["**Seed rows**", ""]
        out += _prose(entry["seed"], schema)
        out += ["", "| " + " | ".join(f"`{c}`" for c in seed.columns) + " |"]
        out.append("|" + "---|" * len(seed.columns))
        for row in _seed_values(seed):
            cells = [
                "NULL" if v is None else str(v).replace("\r", "").replace("\n", "<br>")
                for v in row
            ]
            out.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        out.append("")
    return out


def _render_trigger(trigger: Trigger, text: str, schema: Schema) -> list[str]:
    event = f"{trigger.timing} {trigger.event}"
    if trigger.of_columns:
        event += " OF " + ", ".join(trigger.of_columns)
    line = f"- **`{trigger.name}`** · {event}"
    if trigger.when:
        line += " · conditional"
    out = [f'<a id="{_anchor(trigger.name)}"></a>', "", line, ""]
    out += _prose(text, schema, indent="  ")
    for message in trigger.messages:
        out += ["", f"  Refuses with: {_code(message)}"]
    out += [
        "",
        "  <details><summary>Definition</summary>",
        "",
        "  ```sql",
        *[f"  {line}" if line else "" for line in trigger.sql.splitlines()],
        "  ```",
        "",
        "  </details>",
        "",
    ]
    return out


def _render_view(view: View, text: str, schema: Schema) -> list[str]:
    return [
        f"### `{view.name}`",
        "",
        "*View.*",
        "",
        *_prose(text, schema),
        "",
        "<details><summary>Definition</summary>",
        "",
        "```sql",
        view.sql,
        "```",
        "",
        "</details>",
        "",
    ]


def _v1_tables(v1_text: str) -> list[str]:
    tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", v1_text)
    if not tables:
        raise SchemaReferenceError(
            [
                f"{_V1_REL}: no CREATE TABLE found; the scope note cannot name the v1 tables"
            ]
        )
    return tables


def render(schema: Schema, desc: dict, v1_tables: list[str]) -> str:
    """The reference page as Markdown. Deterministic: no dates, no hashes."""
    out = [
        "<!-- GENERATED FILE: do not edit by hand.",
        f"     Structure:    {_SQL_REL}",
        f"     Descriptions: {_DESC_REL}",
        f"     Regenerate:   {REGENERATE_COMMAND} -->",
        "",
        "# Translations Schema v2 Reference",
        "",
        "> **Generated from the schema. Do not edit this page.** Tables, columns, types,",
        "> keys, indexes, triggers and views are parsed from",
        "> [`schema_v2.sql`](../legesher_i18n/db/schema_v2.sql); every description comes",
        "> from [`schema_v2.descriptions.yml`](../legesher_i18n/db/schema_v2.descriptions.yml).",
        f"> Edit those, then run `{REGENERATE_COMMAND}`. The generator refuses when the two",
        "> disagree (an undescribed table or column, or a description of something the",
        "> SQL no longer has), and `make check-generated` fails when this page is stale.",
        "",
        "## Scope",
        "",
        f"This page covers **schema v2 only**: the {len(schema.tables)} tables, "
        f"{len(schema.views)} views, {len(schema.triggers)} triggers and "
        f"{len(schema.indexes)} indexes in `schema_v2.sql`. Schema v1 (`schema.py`: "
        + ", ".join(f"`{t}`" for t in v1_tables)
        + ") is a separate database and is not described here.",
        "",
    ]
    if schema.sqlite_requirement:
        stored = any(
            c.generated_kind == "STORED"
            for t in schema.tables.values()
            for c in t.columns
        )
        out += [
            f"Requires SQLite {schema.sqlite_requirement} or later"
            + (" (the schema uses STORED generated columns)." if stored else "."),
            "",
        ]
    out += _prose(desc["scope"], schema)
    out += ["", "## Overview", ""]
    out += _prose(desc["overview"], schema)
    out.append("")

    if schema.pragmas:
        out += ["## Connection requirements", ""]
        for pragma in schema.pragmas.values():
            out += [f"`{pragma.sql}`", ""]
            out += _prose(desc["pragmas"][pragma.name], schema)
            out.append("")

    out += [
        "## Contents",
        "",
        "Sections follow the banners in `schema_v2.sql`. Triggers are documented with",
        "the table they guard, wherever the SQL declares them.",
        "",
        "| Section | Tables | Views | Triggers declared |",
        "|---|---|---|---|",
    ]
    for section in schema.sections:
        tables = [t for t in schema.tables.values() if t.section == section]
        views = [v for v in schema.views.values() if v.section == section]
        out.append(
            f"| [{section.title()}](#{_anchor(section.title())}) | "
            + (", ".join(f"[`{t.name}`](#{_anchor(t.name)})" for t in tables) or "none")
            + " | "
            + (", ".join(f"[`{v.name}`](#{_anchor(v.name)})" for v in views) or "none")
            + f" | {sum(1 for t in schema.triggers.values() if t.section == section)} |"
        )
    out.append("")

    for section in schema.sections:
        out += [f"## {section.title()}", ""]
        out += _prose(desc["sections"][section], schema)
        out.append("")
        elsewhere = [
            t
            for t in schema.triggers.values()
            if t.section == section and schema.tables[t.table].section != section
        ]
        if elsewhere:
            out += [
                "Triggers declared in this part of the SQL, each documented with its table: "
                + ", ".join(f"[`{t.name}`](#{_anchor(t.name)})" for t in elsewhere)
                + ".",
                "",
            ]
        for table in (t for t in schema.tables.values() if t.section == section):
            out += _render_table(table, desc, schema)
        for view in (v for v in schema.views.values() if v.section == section):
            out += _render_view(view, desc["views"][view.name], schema)

    if schema.header:
        longest = max(
            (len(r) for r in re.findall(r"~+", "\n".join(schema.header))), default=0
        )
        fence = "~" * max(4, longest + 1)
        out += [
            "## The SQL file's header",
            "",
            "The only prose `schema_v2.sql` may carry besides its section banners,",
            "reproduced so that nothing the SQL says is missing from this page.",
            "",
            fence + "text",
            *schema.header,
            fence,
        ]
    while out and out[-1] == "":
        out.pop()
    # Every line right-stripped: a trailing space from a description would be
    # rewritten by the trailing-whitespace hook, and the page would then never
    # match its own regeneration.
    return "\n".join(line.rstrip() for line in out) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build(
    sql_path: Path = SQL_PATH,
    descriptions_path: Path = DESCRIPTIONS_PATH,
    v1_path: Path = V1_SCHEMA_PATH,
) -> str:
    """Parse, verify, check and render. Raises :class:`SchemaReferenceError`."""
    sql_text = sql_path.read_text(encoding="utf-8")
    schema = parse_schema(sql_text)
    problems = verify_round_trip(schema, sql_text)
    desc = load_descriptions(descriptions_path.read_text(encoding="utf-8"))
    problems += check_descriptions(schema, desc)
    if problems:
        raise SchemaReferenceError(problems)
    return render(schema, desc, _v1_tables(v1_path.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the schema v2 reference.")
    parser.add_argument("--sql", type=Path, default=SQL_PATH)
    parser.add_argument("--descriptions", type=Path, default=DESCRIPTIONS_PATH)
    parser.add_argument("--v1", type=Path, default=V1_SCHEMA_PATH)
    parser.add_argument(
        "--out", type=Path, default=OUT_DIR, help=f"directory to write {OUT_NAME} into"
    )
    args = parser.parse_args(argv)
    try:
        page = build(args.sql, args.descriptions, args.v1)
    except SchemaReferenceError as exc:
        print(
            f"schema reference: {len(exc.problems)} problem(s); nothing written.",
            file=sys.stderr,
        )
        for problem in exc.problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / OUT_NAME
    target.write_text(page, encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
