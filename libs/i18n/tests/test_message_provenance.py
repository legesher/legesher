"""Provenance on message_translations (CORE-1881).

The messages partition's translation rows gain ``source`` /
``model_version`` / ``created_by`` — a carried-forward DB upgrade: the v2
schema carries the columns for fresh builds and activations,
``scripts/add_message_provenance.py`` retrofits databases whose partition
predates them, and both write paths (the seeder and the locale addition)
record provenance and refuse an un-migrated database rather than silently
dropping it.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.activate_messages_partition import activate
from scripts.add_message_locale import add_locale
from scripts.add_message_provenance import PROVENANCE_COLUMNS, add_provenance
from scripts.seed_message_templates import seed_database

PRE_PROVENANCE_PARTITION = """
CREATE TABLE message_templates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    implementation TEXT NOT NULL,
    key            TEXT NOT NULL,
    template_en    TEXT NOT NULL,
    placeholders   TEXT,
    matcher        TEXT,
    concept_id     INTEGER REFERENCES concepts(id) ON DELETE SET NULL,
    version_added  TEXT,
    version_removed TEXT,
    UNIQUE (implementation, key, version_added)
);
CREATE TABLE message_translations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES message_templates(id) ON DELETE CASCADE,
    locale      TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    template    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'machine'
                CHECK (status IN ('machine', 'experimental', 'reviewed', 'official')),
    UNIQUE (template_id, locale)
);
CREATE TABLE message_endorsements (id INTEGER PRIMARY KEY AUTOINCREMENT);
"""


def translation_columns(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(message_translations)")
    }
    conn.close()
    return columns


@pytest.fixture
def bare_v1_db(tmp_path: Path) -> Path:
    """A languages-only operational-shaped database, no partition."""
    path = tmp_path / "translations.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL);
        INSERT INTO languages (code, name) VALUES
            ('es', 'Spanish'), ('ar', 'Arabic'), ('fr', 'French');
        """
    )
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def legacy_db(bare_v1_db: Path) -> Path:
    """The pre-CORE-1881 partition shape, with one seeded es row."""
    conn = sqlite3.connect(bare_v1_db)
    conn.executescript(PRE_PROVENANCE_PARTITION)
    conn.execute(
        "INSERT INTO message_templates (implementation, key, template_en, "
        "placeholders, matcher, version_added) VALUES "
        "('cpython', 'ZeroDivisionError.division_by_zero', 'division by zero', "
        "'[]', '^division by zero$', '3.10')"
    )
    conn.execute(
        "INSERT INTO message_translations (template_id, locale, template) "
        "VALUES (1, 'es', 'división por cero')"
    )
    conn.commit()
    conn.close()
    return bare_v1_db


def seed_dict() -> dict:
    return {
        "implementation": "cpython",
        "version_added": "3.10",
        "templates": [
            {
                "key": "ZeroDivisionError.division_by_zero",
                "template_en": "division by zero",
                "placeholders": [],
                "matcher": "^division by zero$",
                "translations": {
                    "es": {"template": "división por cero", "status": "machine"},
                },
            },
        ],
    }


class TestSchemaCarriesProvenance:
    def test_fresh_activation_includes_provenance_columns(self, bare_v1_db: Path):
        activate(bare_v1_db)
        assert set(PROVENANCE_COLUMNS) <= translation_columns(bare_v1_db)


class TestMigration:
    def test_adds_all_three_columns(self, legacy_db: Path):
        added = add_provenance(legacy_db)
        assert sorted(added) == sorted(PROVENANCE_COLUMNS)
        assert set(PROVENANCE_COLUMNS) <= translation_columns(legacy_db)

    def test_existing_rows_stay_null_without_backfill(self, legacy_db: Path):
        add_provenance(legacy_db)
        conn = sqlite3.connect(legacy_db)
        row = conn.execute(
            "SELECT source, model_version, created_by FROM message_translations"
        ).fetchone()
        conn.close()
        assert row == (None, None, None)

    def test_backfill_labels_pre_migration_rows(self, legacy_db: Path):
        add_provenance(legacy_db, backfill_source="seed")
        conn = sqlite3.connect(legacy_db)
        row = conn.execute(
            "SELECT source, created_by FROM message_translations"
        ).fetchone()
        conn.close()
        assert row[0] == "seed"
        assert "backfill" in row[1]

    def test_second_run_is_a_noop(self, legacy_db: Path):
        add_provenance(legacy_db)
        assert add_provenance(legacy_db) == []

    def test_partial_columns_are_completed(self, legacy_db: Path):
        conn = sqlite3.connect(legacy_db)
        conn.execute("ALTER TABLE message_translations ADD COLUMN source TEXT")
        conn.commit()
        conn.close()
        added = add_provenance(legacy_db)
        assert sorted(added) == ["created_by", "model_version"]

    def test_dry_run_writes_nothing(self, legacy_db: Path):
        add_provenance(legacy_db, dry_run=True)
        assert not set(PROVENANCE_COLUMNS) & translation_columns(legacy_db)

    def test_backfill_on_migrated_db_fills_only_null_rows(self, legacy_db: Path):
        add_provenance(legacy_db)
        conn = sqlite3.connect(legacy_db)
        conn.execute(
            "UPDATE message_translations SET source = 'claude_agent', "
            "created_by = 'generate_messages.py'"
        )
        conn.commit()
        conn.close()
        add_provenance(legacy_db, backfill_source="seed")
        conn = sqlite3.connect(legacy_db)
        row = conn.execute(
            "SELECT source, created_by FROM message_translations"
        ).fetchone()
        conn.close()
        assert row == ("claude_agent", "generate_messages.py")

    def test_missing_partition_is_refused(self, bare_v1_db: Path):
        with pytest.raises(SystemExit, match="partition"):
            add_provenance(bare_v1_db)

    def test_dry_run_with_backfill_writes_nothing(self, legacy_db: Path):
        """The one-transaction discipline: a dry run rolls back the backfill
        UPDATE together with the column DDL, stranding neither."""
        add_provenance(legacy_db, backfill_source="seed", dry_run=True)
        assert not set(PROVENANCE_COLUMNS) & translation_columns(legacy_db)

    def test_backfill_preserves_an_existing_created_by(self, legacy_db: Path):
        add_provenance(legacy_db)
        conn = sqlite3.connect(legacy_db)
        conn.execute("UPDATE message_translations SET created_by = 'someone'")
        conn.commit()
        conn.close()
        add_provenance(legacy_db, backfill_source="seed")
        conn = sqlite3.connect(legacy_db)
        row = conn.execute(
            "SELECT source, created_by FROM message_translations"
        ).fetchone()
        conn.close()
        assert row == ("seed", "someone")


class TestSeederRecordsProvenance:
    def test_seeded_translations_carry_seed_provenance(self, bare_v1_db: Path):
        activate(bare_v1_db)
        seed_database(bare_v1_db, seed_dict())
        conn = sqlite3.connect(bare_v1_db)
        row = conn.execute(
            "SELECT source, created_by FROM message_translations"
        ).fetchone()
        conn.close()
        assert row == ("seed", "seed_message_templates.py")

    def test_seed_entry_may_state_its_own_provenance(self, bare_v1_db: Path):
        activate(bare_v1_db)
        seed = seed_dict()
        seed["templates"][0]["translations"]["es"]["source"] = "unipy"
        seed["templates"][0]["translations"]["es"]["model_version"] = "googletrans"
        seed_database(bare_v1_db, seed)
        conn = sqlite3.connect(bare_v1_db)
        row = conn.execute(
            "SELECT source, model_version FROM message_translations"
        ).fetchone()
        conn.close()
        assert row == ("unipy", "googletrans")

    def test_seed_entry_with_empty_source_is_refused(self, bare_v1_db: Path):
        from scripts.seed_message_templates import validate_seed

        seed = seed_dict()
        seed["templates"][0]["translations"]["es"]["source"] = ""
        assert any("source" in p for p in validate_seed(seed))

    def test_seeder_refuses_a_pre_provenance_partition(self, legacy_db: Path):
        conn = sqlite3.connect(legacy_db)
        conn.execute("DELETE FROM message_translations")
        conn.execute("DELETE FROM message_templates")
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit, match="add_message_provenance"):
            seed_database(legacy_db, seed_dict())


class TestAdditionRecordsProvenance:
    def fr_addition(self) -> dict:
        return {
            "implementation": "cpython",
            "locale": "fr",
            "source": "community",
            "created_by": "test-suite",
            "translations": [
                {
                    "key": "ZeroDivisionError.division_by_zero",
                    "version_added": "3.10",
                    "template": "division par zéro",
                },
            ],
        }

    @pytest.fixture
    def seeded_db(self, bare_v1_db: Path) -> Path:
        activate(bare_v1_db)
        seed_database(bare_v1_db, seed_dict())
        return bare_v1_db

    def test_added_rows_carry_the_addition_provenance(self, seeded_db: Path):
        add_locale(seeded_db, self.fr_addition())
        conn = sqlite3.connect(seeded_db)
        row = conn.execute(
            "SELECT source, model_version, created_by FROM message_translations "
            "WHERE locale = 'fr'"
        ).fetchone()
        conn.close()
        assert row == ("community", None, "test-suite")

    def test_missing_source_is_a_named_problem(self, seeded_db: Path):
        anonymous = self.fr_addition()
        del anonymous["source"]
        with pytest.raises(SystemExit, match="source"):
            add_locale(seeded_db, anonymous)

    @pytest.mark.parametrize("bad_source", [None, "", "   ", 42])
    def test_null_or_empty_source_is_refused(self, seeded_db: Path, bad_source):
        """Presence is not attribution: a null/empty source must not slip
        through and produce a row indistinguishable from a pre-migration one."""
        anonymous = self.fr_addition()
        anonymous["source"] = bad_source
        with pytest.raises(SystemExit, match="source"):
            add_locale(seeded_db, anonymous)

    def test_addition_refuses_a_pre_provenance_partition(self, legacy_db: Path):
        with pytest.raises(SystemExit, match="add_message_provenance"):
            add_locale(legacy_db, self.fr_addition())
