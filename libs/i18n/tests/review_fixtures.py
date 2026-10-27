"""Filled review files made from the real generated templates (CORE-2508).

Every fixture starts from a pack's own ``REFERENCE.md`` on disk, the file a
reviewer copies, and edits it the way a reviewer does: two cells per row, the
About-you lines, the boxes, the credit line, the notes section. Nothing here
types a template by hand, so a template change reaches the parser's tests the
moment it is regenerated.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path

from legesher_i18n.db.schema_v2 import apply_schema_v2
from legesher_i18n.surface_validation import allowed_scripts_for

ROOT = Path(__file__).resolve().parents[3]
PACKS_DIR = ROOT / "libs" / "i18n" / "language-packs" / "python"
REGISTRY: dict[str, dict] = json.loads(
    (ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json").read_text(
        encoding="utf-8"
    )
)["languages"]
CODES = sorted(REGISTRY)

#: Scripts whose words carry combining marks or joiners. Latin proves nothing
#: about a parser that must keep every byte of a cell.
COMBINING_SCRIPTS = frozenset({"Sinhala", "Devanagari", "Arabic", "Thai"})
COMBINING_CODES = sorted(
    code for code in CODES if (allowed_scripts_for(code) or set()) & COMBINING_SCRIPTS
)

PR_AUTHOR = "native-reviewer"
PR_URL = "https://github.com/legesher/language-packs/pull/400"

#: ``terms.category`` values per template section, as the v2 migration mints them.
SECTION_CATEGORIES = {
    "keywords": "keyword",
    "builtins": "builtin_func",
    "exceptions": "exception",
    "implicit_params": "implicit_param",
}

_CONSENT_BOXES = 6
_RELATIONSHIP_TAIL = "(keep one): native speaker · fluent · professional · learning"
_CREDIT_LINE = (
    "Credit me as (keep one): anonymous · my GitHub handle · this name: `<name>`"
)
_NOTES_ANCHOR = "review; they often matter more than any single word.\n"


def template_text(code: str) -> str:
    return (PACKS_DIR / code / "REFERENCE.md").read_text(encoding="utf-8")


def bcp47(code: str) -> str:
    return REGISTRY[code]["bcp47"]


def review_path(code: str, username: str = PR_AUTHOR) -> str:
    tag = bcp47(code)
    return f"reviews/{tag}/{tag}-{username}.md"


def row_cells(text: str) -> dict[str, list[str]]:
    """Key -> stripped cells of every term row in *text*."""
    rows: dict[str, list[str]] = {}
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows[cells[0].strip("`")] = cells
    return rows


def current_word(text: str, key: str) -> str:
    return row_cells(text)[key][2].strip("`")


def fill(
    template: str,
    rows: Mapping[str, tuple[str, str]] | None = None,
    *,
    username: str = PR_AUTHOR,
    relationship: str | None = "native speaker",
    credit: str | None = "my GitHub handle",
    ticked: Iterable[int] = range(_CONSENT_BOXES),
    notes: str | None = None,
) -> str:
    """A review of *template*: ``rows`` maps key -> (Suggested, Comments)."""
    text = template.replace("`<your-github-username>`", f"`{username}`", 1)
    if relationship is not None:
        text = text.replace(_RELATIONSHIP_TAIL, f"(keep one): {relationship}", 1)
    if credit is not None:
        text = text.replace(_CREDIT_LINE, f"Credit me as (keep one): {credit}", 1)
    boxes = set(ticked)
    parts = text.split("- [ ]")
    text = parts[0] + "".join(
        ("- [x]" if index in boxes else "- [ ]") + part
        for index, part in enumerate(parts[1:])
    )
    if rows:
        lines = text.split("\n")
        for index, line in enumerate(lines):
            for key, (suggested, comments) in rows.items():
                if line.startswith(f"| `{key}` |"):
                    assert line.endswith("| | |"), line
                    lines[index] = (
                        f"{line[: -len('| | |')]}| {suggested} | {comments} |"
                    )
        text = "\n".join(lines)
        missing = [key for key in rows if f"| `{key}` |" not in text]
        assert not missing, missing
    if notes is not None:
        assert _NOTES_ANCHOR in text
        text = text.replace(_NOTES_ANCHOR, f"{_NOTES_ANCHOR}\n{notes}\n", 1)
    return text


def pull_request(
    author: str = PR_AUTHOR,
    url: str = PR_URL,
    *,
    merged: bool = True,
    merge_commit: str | None = None,
    head: str | None = None,
    base: str | None = None,
    files: Iterable[str] = (),
) -> dict:
    """The ``gh pr view --json`` payload shape the import command reads."""
    number = int(url.rsplit("/", 1)[1])
    return {
        "number": number,
        "url": url,
        "author": {"login": author},
        "createdAt": "2026-10-28T09:00:00Z",
        "state": "MERGED" if merged else "OPEN",
        "mergedAt": "2026-10-29T09:00:00Z" if merged else None,
        "mergeCommit": {"oid": merge_commit} if merge_commit else None,
        "headRefOid": head,
        "baseRefOid": base,
        "files": [{"path": path} for path in files],
    }


def review_db(path: Path, codes: Iterable[str]) -> Path:
    """A v2 database holding Python, the *codes*' locales and every template key's concept."""
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.execute(
        "INSERT INTO programming_languages(code, name, status)"
        " VALUES ('python', 'Python', 'shipping')"
    )
    for code in codes:
        entry = REGISTRY.get(code, REGISTRY.get(code.split("-")[0], {}))
        tag = entry.get("bcp47", code) if code in REGISTRY else code
        conn.execute(
            "INSERT OR IGNORE INTO locales(tag, language_subtag, name, native_name,"
            " direction, in_registry) VALUES (?, ?, ?, ?, ?, 1)",
            (
                tag,
                tag.split("-")[0],
                entry.get("name", tag),
                entry.get("native", tag),
                "rtl" if entry.get("rtl") else "ltr",
            ),
        )
    # One primary term per name, as the migration mints them: `type` is a
    # keyword and a builtin, two concepts, and the second term is secondary.
    named: set[str] = set()
    for key in row_cells(template_text("en")):
        section, term = key.split(".", 1)
        category = SECTION_CATEGORIES[section]
        slug = f"{section}-{term}".lower()
        cursor = conn.execute(
            "INSERT INTO concepts(slug, definition_en, category) VALUES (?, ?, ?)",
            (slug, f"the Python {term}", category),
        )
        conn.execute(
            "INSERT INTO terms(concept_id, programming_language, name, category,"
            " export_role) VALUES (?, 'python', ?, ?, ?)",
            (
                cursor.lastrowid,
                term,
                category,
                "secondary" if term in named else "primary",
            ),
        )
        named.add(term)
    conn.commit()
    conn.close()
    return path


def concept_slug(key: str) -> str:
    section, term = key.split(".", 1)
    return f"{section}-{term}".lower()
