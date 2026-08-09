"""Tests for the allowlist ↔ DB identity reconciliation (CORE-1355).

One policy, two layers: the pack-layer intentional-loanword allowlist
(`untranslated_allowlist.yml`) and the DB identity marker must agree.
`find_untranslated.py --check-db` verifies every allowlist entry against
the DB's selected translation using the same case/NFKC-insensitive rule
the migration uses to populate `canon_selections.identity_ok`.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "translate"))

from find_untranslated import check_db_drift  # noqa: E402


def _v1_db(tmp_path: Path, selected: list[tuple[str, str, str]]) -> Path:
    """Minimal v1 DB: (term_name, language_code, translation) selected rows."""
    path = tmp_path / "translations.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE terms (
            id INTEGER PRIMARY KEY, name TEXT, programming_language TEXT,
            category TEXT
        );
        CREATE TABLE selected_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term_id INTEGER,
            language_code TEXT, translation TEXT
        );
        """
    )
    term_ids: dict[str, int] = {}
    for name, lang, translation in selected:
        if name not in term_ids:
            term_ids[name] = len(term_ids) + 1
            conn.execute(
                "INSERT INTO terms (id, name, programming_language, category) "
                "VALUES (?, ?, 'python', 'keyword')",
                (term_ids[name], name),
            )
        conn.execute(
            "INSERT INTO selected_translations (term_id, language_code, "
            "translation) VALUES (?, ?, ?)",
            (term_ids[name], lang, translation),
        )
    conn.commit()
    conn.close()
    return path


def test_consistent_allowlist_passes(tmp_path: Path) -> None:
    db = _v1_db(tmp_path, [("lambda", "cs", "lambda")])
    assert check_db_drift(db, {("cs", "lambda")}) == []


def test_identity_is_case_and_compat_insensitive(tmp_path: Path) -> None:
    # StopIteration vs the pack-layer lowercase key: still one policy.
    db = _v1_db(tmp_path, [("StopIteration", "da", "stopiteration")])
    assert check_db_drift(db, {("da", "stopiteration")}) == []


def test_translated_term_in_allowlist_is_drift(tmp_path: Path) -> None:
    db = _v1_db(tmp_path, [("lambda", "cs", "lambda_cz")])
    errors = check_db_drift(db, {("cs", "lambda")})
    assert len(errors) == 1
    assert "cs" in errors[0] and "lambda" in errors[0]


def test_allowlist_entry_without_db_selection_is_drift(tmp_path: Path) -> None:
    db = _v1_db(tmp_path, [("lambda", "cs", "lambda")])
    errors = check_db_drift(db, {("ga", "lambda")})
    assert len(errors) == 1
    assert "ga" in errors[0]
