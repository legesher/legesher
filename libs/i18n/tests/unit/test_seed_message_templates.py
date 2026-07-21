"""Tests for scripts/seed_message_templates.py against the real v2 schema."""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

LIB_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(LIB_ROOT / "scripts"))

from seed_message_templates import (  # noqa: E402
    DEFAULT_SEED,
    seed_database,
    validate_seed,
)

from legesher_i18n.db.schema_v2 import read_schema_sql  # noqa: E402

SCHEMA = read_schema_sql()


@pytest.fixture
def v2_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "translations_v2.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)
    connection.execute(
        "INSERT INTO locales "
        "(tag, language_subtag, name, native_name, direction, has_case_distinction) "
        "VALUES ('ar', 'ar', 'Arabic', 'العربية', 'rtl', 0)"
    )
    connection.commit()
    connection.close()
    return db_path


@pytest.fixture
def seed() -> dict:
    return json.loads(DEFAULT_SEED.read_text(encoding="utf-8"))


class TestSeedValidation:
    def test_shipped_seed_is_valid(self, seed):
        assert validate_seed(seed) == []

    def test_duplicate_keys_rejected(self, seed):
        seed["templates"].append(dict(seed["templates"][0]))
        assert any("duplicate key" in p for p in validate_seed(seed))

    def test_placeholder_mismatch_rejected(self, seed):
        seed["templates"][0]["translations"]["ar"]["template"] = "بدون عناصر نائبة"
        assert any("placeholders" in p for p in validate_seed(seed))

    def test_stored_bidi_controls_rejected(self, seed):
        entry = seed["templates"][0]
        entry["translations"]["ar"]["template"] = "⁨" + entry["translations"]["ar"]["template"] + "⁩"
        assert any("bidi" in p for p in validate_seed(seed))


class TestSeeding:
    def test_seeds_all_templates_and_translations(self, v2_db, seed):
        templates, translations = seed_database(v2_db, seed)
        assert templates == 35
        assert translations == 35
        connection = sqlite3.connect(v2_db)
        row = connection.execute(
            "SELECT t.template_en, tr.template, tr.status FROM message_templates t "
            "JOIN message_translations tr ON tr.template_id = t.id "
            "WHERE t.implementation = 'v8' AND t.key = 'jej.construct_not_allowed'"
        ).fetchone()
        connection.close()
        assert row is not None
        assert "{construct}" in row[0]
        assert "{construct}" in row[1]
        assert row[2] == "machine"

    def test_reseed_refuses(self, v2_db, seed):
        seed_database(v2_db, seed)
        with pytest.raises(SystemExit, match="refusing to seed"):
            seed_database(v2_db, seed)

    def test_dry_run_writes_nothing(self, v2_db, seed):
        seed_database(v2_db, seed, dry_run=True)
        connection = sqlite3.connect(v2_db)
        templates = connection.execute("SELECT COUNT(*) FROM message_templates").fetchone()[0]
        translations = connection.execute(
            "SELECT COUNT(*) FROM message_translations"
        ).fetchone()[0]
        connection.close()
        assert (templates, translations) == (0, 0)

    def test_templates_only_seed_is_supported(self, v2_db, seed):
        # A seed with no translations is deliberately valid — templates land,
        # zero translations, no locale lookup required.
        for entry in seed["templates"]:
            entry["translations"] = {}
        templates, translations = seed_database(v2_db, seed)
        assert (templates, translations) == (35, 0)

    def test_missing_locale_fails_closed(self, tmp_path, seed):
        db_path = tmp_path / "no_locale.db"
        connection = sqlite3.connect(db_path)
        connection.executescript(SCHEMA)
        connection.commit()
        connection.close()
        with pytest.raises(SystemExit, match="locales missing"):
            seed_database(db_path, seed)
