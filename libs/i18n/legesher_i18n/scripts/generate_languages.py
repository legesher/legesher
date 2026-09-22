#!/usr/bin/env python3
"""Generate the language-registry artifacts from translations.db.

CORE-611: ``translations.db`` (the ``languages`` table, rows where
``in_registry = 1``) is the single source of truth for the published language
registry. This script regenerates the two derived, git-tracked artifacts from
it — nothing else reads the database at runtime:

1. ``languages.json``                          — Python read-path
   (``language_registry.py``, ``prompt_builder.py``, ``style_guides.py``, ...)
2. ``libs/vs-code/src/generated/languages.ts``  — VS Code extension read-path

To add or change a published language, edit the DB (``languages`` table) — set
its fields and ``in_registry = 1`` — then run this script. Never hand-edit
``languages.json`` or ``languages.ts``; a drift test fails if they diverge from
the DB.

CORE-1887: the generator refuses to write an empty registry, or one that
shrank drastically against the committed ``languages.json`` — the signature of
regenerating from a stray empty/partial ``translations.db``, which would
silently gut both artifacts. ``--force-shrink`` overrides the refusal.

Usage:
    uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
    # or:
    python -m legesher_i18n.scripts.generate_languages
"""

import argparse
import json
import sys
from pathlib import Path

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
I18N_DIR = SCRIPT_DIR.parent
REPO_ROOT = I18N_DIR.parent.parent.parent
LANGUAGES_JSON = I18N_DIR / "languages.json"
VSCODE_GENERATED_DIR = REPO_ROOT / "libs" / "vs-code" / "src" / "generated"

# Make ``legesher_i18n`` importable when this file is run as a plain script path
# (e.g. ``python .../scripts/generate_languages.py``) rather than ``-m``.
sys.path.insert(0, str(I18N_DIR.parent))

from legesher_i18n.db import TranslationDatabase, default_db_path  # noqa: E402

# The canonical language: the language Legesher's Python keywords are authored
# in. translations.db has no canonical flag, so it is fixed here (this matches
# the value that has always shipped in languages.json).
CANONICAL_LANGUAGE = "en"

# Kept in sync with languages.schema.json (a sibling of languages.json).
JSON_SCHEMA_REF = "./languages.schema.json"
JSON_COMMENT = (
    "AUTO-GENERATED from translations.db (languages table, in_registry = 1). "
    "Do not edit directly; edit the DB and run "
    "libs/i18n/legesher_i18n/scripts/generate_languages.py."
)


def load_registry_from_db(db_path: str | Path | None = None) -> dict:
    """Load the published language registry from translations.db.

    Returns the same shape the rest of the toolchain expects from
    ``languages.json``: ``{"canonical_language": str, "languages": {code: meta}}``,
    with languages sorted by code and only the published (``in_registry = 1``)
    set included. DB columns are mapped onto the json field names
    (``native_name`` -> ``native``, ``direction`` -> ``rtl`` boolean).

    Args:
        db_path: Optional path to the SQLite database. Defaults to the canonical
            translations.db; overridable mainly for testing.
    """
    # CORE-1887: opening a missing path would create a fresh empty DB (schema
    # auto-init) and the run would then "succeed" with zero languages. Refuse
    # up front instead.
    resolved = Path(db_path) if db_path is not None else default_db_path()
    if not resolved.exists():
        raise FileNotFoundError(
            f"translations.db not found at {resolved}. The registry can only be "
            f"regenerated from the working database — copy it in first "
            f"(libs/i18n/CLAUDE.md, 'Durable home & sync ritual')."
        )
    db = TranslationDatabase(db_path)
    try:
        rows = db.get_languages(in_registry=True)
    finally:
        db.close()

    languages: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: r["code"]):
        code = row["code"]
        # iso639_2 / bcp47 are nullable columns. For a *published* language they
        # are required by languages.schema.json, so fail fast rather than emit an
        # empty string that would silently ship a broken registry (this is the
        # exact gap CORE-611 backfilled — guard against it regressing).
        if not row["iso639_2"] or not row["bcp47"]:
            raise ValueError(
                f"Published language {code!r} is missing iso639_2/bcp47 in "
                f"translations.db (iso639_2={row['iso639_2']!r}, "
                f"bcp47={row['bcp47']!r}). The DB must be the complete source of "
                f"truth for published languages — backfill it before regenerating."
            )
        languages[code] = {
            "name": row["name"],
            "native": row["native_name"],
            "iso639_2": row["iso639_2"],
            "bcp47": row["bcp47"],
            "rtl": row["direction"] == "rtl",
            "has_case_distinction": bool(row["has_case_distinction"]),
            "status": row["status"],
        }
    return {"canonical_language": CANONICAL_LANGUAGE, "languages": languages}


def generate_json(data: dict) -> str:
    """Render schema-valid ``languages.json`` content from registry data."""
    document = {
        "$schema": JSON_SCHEMA_REF,
        "_comment": JSON_COMMENT,
        "canonical_language": data["canonical_language"],
        "languages": data["languages"],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def generate_typescript(data: dict) -> str:
    """Generate TypeScript module from language data."""
    languages = data["languages"]
    canonical = data["canonical_language"]

    # Build the TypeScript file
    lines = [
        "/**",
        " * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY",
        " *",
        " * This file is generated from translations.db (languages table, in_registry = 1)",
        " * Run: uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py",
        " */",
        "",
        "export type LanguageStatus = 'available' | 'experimental' | 'deprecated';",
        "",
        "export interface LanguageMetadata {",
        "    name: string;",
        "    native: string;",
        "    iso639_2: string;",
        "    bcp47: string;",
        "    rtl: boolean;",
        "    status: LanguageStatus;",
        "}",
        "",
        "export type LanguageCode =",
    ]

    # Add union type of all language codes
    # Format: 'code1' | 'code2' | ... | 'codeN';
    codes = sorted(languages.keys())
    for i, code in enumerate(codes):
        is_last = i == len(codes) - 1
        terminator = ";" if is_last else " |"
        lines.append(f"    '{code}'{terminator}")

    lines.extend(
        [
            "",
            f"export const CANONICAL_LANGUAGE: LanguageCode = '{canonical}';",
            "",
            "export const LANGUAGE_METADATA: Record<LanguageCode, LanguageMetadata> = {",
        ]
    )

    # Add each language
    for code in codes:
        lang = languages[code]
        name = lang["name"].replace("\\", "\\\\").replace("'", "\\'")
        native = lang["native"].replace("\\", "\\\\").replace("'", "\\'")
        iso639_2 = lang["iso639_2"]
        bcp47 = lang["bcp47"]
        rtl = "true" if lang["rtl"] else "false"
        status = lang["status"]
        lines.append(
            f"    '{code}': {{ name: '{name}', native: '{native}', iso639_2: '{iso639_2}', bcp47: '{bcp47}', rtl: {rtl}, status: '{status}' }},"
        )

    lines.extend(
        [
            "};",
            "",
            "/**",
            " * Get all available language codes.",
            " */",
            "export function getAvailableLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => LANGUAGE_METADATA[code as LanguageCode].status === 'available') as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get all active (non-deprecated) language codes.",
            " * Returns both 'available' and 'experimental' status languages.",
            " */",
            "export function getActiveLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => {",
            "            const status = LANGUAGE_METADATA[code as LanguageCode].status;",
            "            return status === 'available' || status === 'experimental';",
            "        }) as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get all RTL (right-to-left) language codes.",
            " */",
            "export function getRtlLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => LANGUAGE_METADATA[code as LanguageCode].rtl) as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get the English name for a language code.",
            " */",
            "export function getLanguageName(code: string): string {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.name ?? code.toUpperCase();",
            "}",
            "",
            "/**",
            " * Get the native name for a language code.",
            " */",
            "export function getLanguageNativeName(code: string): string {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.native ?? code.toUpperCase();",
            "}",
            "",
            "/**",
            " * Check if a language code uses RTL script.",
            " */",
            "export function isRtlLanguage(code: string): boolean {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.rtl ?? false;",
            "}",
            "",
            "/**",
            " * Check if a language code is supported.",
            " */",
            "export function isSupportedLanguage(code: string): boolean {",
            "    return code in LANGUAGE_METADATA;",
            "}",
            "",
        ]
    )

    return "\n".join(lines)


def _committed_language_count(path: Path) -> int | None:
    """Entry count of the committed ``languages.json``, or None if unreadable."""
    try:
        committed = json.loads(path.read_text(encoding="utf-8"))
        return len(committed["languages"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def check_registry_guard(data: dict, committed_json: Path) -> str | None:
    """Return a refusal message if the freshly loaded registry looks gutted.

    CORE-1887: a stray empty or partial ``translations.db`` (e.g. one created
    as a side effect of a test run — the DB is untracked since CORE-1794)
    yields zero or near-zero published rows, and writing that result silently
    destroys the registry both artifacts are generated from. Refuse when the
    load produced no languages, or drastically fewer (less than half) than the
    committed ``languages.json`` it would replace. Returns None when the write
    is safe.
    """
    count = len(data["languages"])
    if count == 0:
        return (
            "Refusing to write an EMPTY language registry: translations.db "
            "yielded zero in_registry = 1 rows. The source DB is most likely "
            "empty or partial (e.g. a stray translations.db left behind by a "
            "test run — the real working DB is untracked since CORE-1794). "
            "Point the generator at the real database, or pass --force-shrink "
            "to override (CORE-1887)."
        )
    committed = _committed_language_count(committed_json)
    if committed is not None and count * 2 < committed:
        return (
            f"Refusing to shrink the language registry from {committed} to "
            f"{count} languages. A drop this large is the signature of "
            f"regenerating from a partial translations.db, not of an "
            f"intentional edit. If the shrink is really intended, pass "
            f"--force-shrink (CORE-1887)."
        )
    return None


def main(argv: list[str] | None = None) -> int:
    """Regenerate languages.json and the VS Code languages.ts from the DB."""
    parser = argparse.ArgumentParser(
        description="Regenerate languages.json and the VS Code languages.ts "
        "from translations.db (languages table, in_registry = 1)."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to translations.db (defaults to the canonical working DB).",
    )
    parser.add_argument(
        "--force-shrink",
        action="store_true",
        help="Write the registry even if it is empty or drastically smaller "
        "than the committed languages.json (CORE-1887 guard override).",
    )
    args = parser.parse_args(argv)

    print("Loading published language registry from translations.db...")
    try:
        data = load_registry_from_db(args.db)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Found {len(data['languages'])} published languages (in_registry = 1)")

    refusal = check_registry_guard(data, LANGUAGES_JSON)
    if refusal is not None:
        if not args.force_shrink:
            print(f"ERROR: {refusal}", file=sys.stderr)
            print("Nothing was written.", file=sys.stderr)
            return 1
        print(f"WARNING: --force-shrink override in effect: {refusal}")

    LANGUAGES_JSON.write_text(generate_json(data), encoding="utf-8")
    print(f"Generated {LANGUAGES_JSON}")

    VSCODE_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    ts_output = VSCODE_GENERATED_DIR / "languages.ts"
    ts_output.write_text(generate_typescript(data), encoding="utf-8")
    print(f"Generated {ts_output}")

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
