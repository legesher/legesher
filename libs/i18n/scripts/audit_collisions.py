#!/usr/bin/env python3
"""Collision audit for the i18n translation database and language packs.

Runs both layers of the CORE-950 collision guardrail and exits non-zero
on any failure:

1. **DB layer** — ``TranslationDatabase.find_collisions()``: catches
   collisions that cross separately-imported translations.
2. **Pack layer** — ``schema_validator.check_duplicates()
   ['cross_section_collisions']``: catches collisions in pack YAMLs at
   edit time, before they reach the DB.

Designed to be invoked from a shell-agnostic context (CI matrix runs on
Linux, macOS, and Windows). Prints GitHub Actions-style ``::error::``
annotations when running under ``GITHUB_ACTIONS`` so failures show up
inline in PR review UIs.

Usage:

    uv run python libs/i18n/scripts/audit_collisions.py

Exits 0 on clean audit, 1 on any collision.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

# Add parent directory so the script works whether invoked as a module
# or as a file path.
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.schema_validator import (  # noqa: E402
    LanguagePackSchema,
    SchemaValidator,
)

_IS_GHA = os.environ.get("GITHUB_ACTIONS") == "true"
_LANGUAGE_PACKS_DIR = _SCRIPT_DIR.parent / "language-packs" / "python"
_LANGUAGES_JSON = _SCRIPT_DIR.parent / "legesher_i18n" / "languages.json"


def _gha_error(message: str, file: str | None = None) -> None:
    """Emit a GitHub Actions error annotation when running under GHA;
    fall back to a plain stderr line otherwise."""
    if _IS_GHA:
        prefix = f"::error file={file}::" if file else "::error::"
        print(f"{prefix}{message}")
    else:
        print(f"ERROR: {message}", file=sys.stderr)


def audit_db() -> bool:
    """Return True if the DB has zero collisions."""
    try:
        db = TranslationDatabase()
        collisions = db.find_collisions()
    except Exception as exc:
        _gha_error(f"Database audit failed to run: {exc}")
        return False

    if collisions:
        _gha_error(
            f"Translation database has {len(collisions)} collision(s). "
            f"Run 'uv run legesher-i18n db collisions' locally to inspect."
        )
        return False
    return True


def _expected_pack_codes() -> list[str]:
    """Return the canonical list of language codes that must have packs.

    Source of truth: ``languages.json`` (the registry that owns ``rtl``,
    ``has_case_distinction``, etc.). If we silently iterate whatever
    happens to exist on disk, an accidental dir rename/removal hides
    behind a still-passing audit (Copilot review on PR #237).
    """
    try:
        data = json.loads(_LANGUAGES_JSON.read_text(encoding="utf-8"))
        return sorted(data.get("languages", {}).keys())
    except (OSError, json.JSONDecodeError) as exc:
        _gha_error(
            f"Could not read expected language codes from {_LANGUAGES_JSON}: "
            f"{exc}. Audit cannot determine the expected pack set."
        )
        return []


def audit_packs() -> bool:
    """Return True iff every language code in ``languages.json`` has an
    auditable pack file AND that file has zero cross-section collisions.

    Failure modes (Copilot review on PR #237):
    * Pack directory entirely missing → fail (was: silent skip).
    * Pack dir present but ``packs/3.10.yml`` missing → fail (was: silent
      skip).
    * Schema validation error on the YAML → fail.
    * Cross-section collision present → fail.
    """
    if not _LANGUAGE_PACKS_DIR.exists():
        _gha_error(f"Language packs directory not found: {_LANGUAGE_PACKS_DIR}")
        return False

    expected_codes = _expected_pack_codes()
    if not expected_codes:
        return False

    failed: list[tuple[str, list]] = []
    missing: list[str] = []
    audited = 0
    for code in expected_codes:
        pack = (
            _LANGUAGE_PACKS_DIR
            / code
            / f"legesher_i18n_python_{code}"
            / "packs"
            / "3.10.yml"
        )
        if not pack.exists():
            missing.append(code)
            _gha_error(
                f"Expected pack missing for language {code!r}: "
                f"{pack.relative_to(_SCRIPT_DIR.parent.parent.parent)}. "
                f"Either restore the file or remove the entry from "
                f"languages.json."
            )
            continue

        audited += 1
        try:
            data = yaml.safe_load(pack.read_text(encoding="utf-8"))
            schema = LanguagePackSchema(**data)
        except Exception as exc:
            _gha_error(
                f"Schema validation failed for {code}: {exc}",
                file=str(pack.relative_to(_SCRIPT_DIR.parent.parent.parent)),
            )
            failed.append((code, []))
            continue

        cs = SchemaValidator.check_duplicates(schema).get(
            "cross_section_collisions", []
        )
        if cs:
            failed.append((code, cs))
            _gha_error(
                f"Cross-section collisions in {code}: {cs}",
                file=str(pack.relative_to(_SCRIPT_DIR.parent.parent.parent)),
            )

    if failed or missing:
        return False
    print(
        f"Audited {audited} packs (all {len(expected_codes)} expected), "
        f"0 cross-section collisions."
    )
    return True


def main() -> int:
    db_ok = audit_db()
    packs_ok = audit_packs()
    return 0 if (db_ok and packs_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
