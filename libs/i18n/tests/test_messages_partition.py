"""Activation + seeding invariants of the messages partition (CORE-1679).

The partition's DDL is read back from ``schema_v2.sql`` (single source of
truth), applied to the operational database by
``scripts/activate_messages_partition.py``, and filled append-once by
``scripts/seed_message_templates.py``. These tests run against synthetic
databases; the content of the REAL seeded ``translations.db`` is covered by
``test_messages_catalog.py``.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    MESSAGE_PARTITION_TABLES,
    messages_partition_ddl,
)
from scripts.activate_messages_partition import activate, existing_partition_tables
from scripts.seed_message_templates import seed_database, validate_seed


@pytest.fixture
def v1_db(tmp_path: Path) -> Path:
    """A minimal operational-shaped database: ``languages``, no partition."""
    path = tmp_path / "translations.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL);
        INSERT INTO languages (code, name) VALUES ('es', 'Spanish'), ('ar', 'Arabic');
        """
    )
    conn.commit()
    conn.close()
    return path


def seed_dict(**overrides) -> dict:
    base = {
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
                    "ar": {"template": "القسمة على صفر", "status": "machine"},
                },
            },
            {
                "key": "NameError.not_defined",
                "template_en": "name '{name}' is not defined",
                "placeholders": [{"name": "name", "example": "x"}],
                "matcher": "^name '(?P<name>[^']+)' is not defined$",
                "translations": {
                    "es": {"template": "el nombre '{name}' no está definido"},
                },
            },
        ],
    }
    base.update(overrides)
    return base


class TestDdlExtraction:
    def test_partition_ddl_covers_tables_indexes_and_triggers(self):
        statements = messages_partition_ddl()
        tables = [s for s in statements if s.upper().startswith("CREATE TABLE")]
        triggers = [s for s in statements if s.upper().startswith("CREATE TRIGGER")]
        assert len(tables) == 3
        for name in MESSAGE_PARTITION_TABLES:
            assert any(name in s for s in tables)
        # the message_endorsements append-only discipline rides along
        assert any("append-only" in s for s in triggers)

    def test_ddl_is_verbatim_from_schema_v2(self):
        """The extracted DDL is byte-identical to what a v2 build creates."""
        from legesher_i18n.db.schema_v2 import apply_schema_v2

        conn = sqlite3.connect(":memory:")
        apply_schema_v2(conn)
        expected = {
            row[0]
            for row in conn.execute(
                "SELECT sql FROM sqlite_master WHERE tbl_name IN (?, ?, ?) "
                "AND sql IS NOT NULL",
                MESSAGE_PARTITION_TABLES,
            )
        }
        conn.close()
        assert set(messages_partition_ddl()) == expected


class TestActivation:
    def test_creates_all_three_tables(self, v1_db: Path):
        statements = activate(v1_db)
        assert statements  # applied, not skipped
        conn = sqlite3.connect(v1_db)
        assert existing_partition_tables(conn) == set(MESSAGE_PARTITION_TABLES)
        conn.close()

    def test_idempotent_second_run_is_a_noop(self, v1_db: Path):
        activate(v1_db)
        assert activate(v1_db) == []  # second run reports already-active

    def test_partial_partition_is_refused(self, v1_db: Path):
        conn = sqlite3.connect(v1_db)
        conn.execute("CREATE TABLE message_templates (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit, match="partial"):
            activate(v1_db)

    def test_missing_database_is_refused(self, tmp_path: Path):
        with pytest.raises(SystemExit, match="not found"):
            activate(tmp_path / "nope.db")

    def test_dry_run_writes_nothing(self, v1_db: Path):
        activate(v1_db, dry_run=True)
        conn = sqlite3.connect(v1_db)
        assert existing_partition_tables(conn) == set()
        conn.close()

    def test_append_only_triggers_are_live_after_activation(self, v1_db: Path):
        activate(v1_db)
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "INSERT INTO message_templates (implementation, key, template_en) "
            "VALUES ('cpython', 'X.y', 'x')"
        )
        conn.execute(
            "INSERT INTO message_translations (template_id, locale, template) "
            "VALUES (1, 'es', 'x')"
        )
        conn.execute(
            "INSERT INTO message_endorsements "
            "(uid, message_translation_id, contributor_id, method, rung_at_endorsement) "
            f"VALUES ('men_{'0' * 24}', 1, 'c_{'0' * 16}', 'portal', 'machine')"
        )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("DELETE FROM message_endorsements")
        conn.close()


class TestSeeder:
    def test_seed_round_trip(self, v1_db: Path):
        activate(v1_db)
        seed = seed_dict()
        assert validate_seed(seed) == []
        templates, translations = seed_database(v1_db, seed)
        assert (templates, translations) == (2, 3)
        conn = sqlite3.connect(v1_db)
        row = conn.execute(
            "SELECT matcher, version_added FROM message_templates "
            "WHERE key = 'NameError.not_defined'"
        ).fetchone()
        conn.close()
        assert row == ("^name '(?P<name>[^']+)' is not defined$", "3.10")

    def test_reseed_is_refused(self, v1_db: Path):
        activate(v1_db)
        seed_database(v1_db, seed_dict())
        with pytest.raises(SystemExit, match="append-once"):
            seed_database(v1_db, seed_dict())

    def test_unknown_locale_is_refused(self, v1_db: Path):
        activate(v1_db)
        seed = seed_dict()
        seed["templates"][0]["translations"]["xx"] = {"template": "?"}
        with pytest.raises(SystemExit, match="locales missing"):
            seed_database(v1_db, seed)

    def test_unactivated_database_is_refused(self, v1_db: Path):
        with pytest.raises(SystemExit, match="activate_messages_partition"):
            seed_database(v1_db, seed_dict())

    def test_per_template_version_added_overrides_seed_default(self, v1_db: Path):
        activate(v1_db)
        seed = seed_dict()
        seed["templates"][1]["version_added"] = "3.12"
        seed_database(v1_db, seed)
        conn = sqlite3.connect(v1_db)
        versions = dict(
            conn.execute("SELECT key, version_added FROM message_templates")
        )
        conn.close()
        assert versions["ZeroDivisionError.division_by_zero"] == "3.10"
        assert versions["NameError.not_defined"] == "3.12"


class TestSeedValidation:
    def test_placeholder_mismatch_in_translation(self):
        seed = seed_dict()
        seed["templates"][1]["translations"]["es"]["template"] = "sin marcador"
        assert any("placeholders" in p for p in validate_seed(seed))

    def test_matcher_group_placeholder_mismatch(self):
        seed = seed_dict()
        seed["templates"][1]["matcher"] = "^name '(?P<wrong>[^']+)' is not defined$"
        assert any("named groups" in p for p in validate_seed(seed))

    def test_unanchored_matcher_is_refused(self):
        seed = seed_dict()
        seed["templates"][0]["matcher"] = "division by zero"
        assert any("anchored" in p for p in validate_seed(seed))

    def test_matcher_must_fullmatch_its_example(self):
        seed = seed_dict()
        seed["templates"][1]["matcher"] = '^name "(?P<name>[^"]+)" is not defined$'
        assert any("fullmatch" in p for p in validate_seed(seed))

    def test_matcher_groups_must_give_examples_back(self):
        # \S+ swallows the quotes: fullmatch succeeds but the slot round-trip
        # returns "'x'" instead of the declared example "x".
        seed = seed_dict()
        seed["templates"][1]["matcher"] = "^name (?P<name>\\S+) is not defined$"
        assert any("round-trip" in p for p in validate_seed(seed))

    def test_bidi_controls_are_refused(self):
        seed = seed_dict()
        seed["templates"][0]["translations"]["ar"]["template"] = "‏القسمة على صفر"
        assert any("bidi" in p for p in validate_seed(seed))

    def test_duplicate_key_same_version_is_refused(self):
        seed = seed_dict()
        seed["templates"].append(dict(seed["templates"][0]))
        assert any("duplicate" in p for p in validate_seed(seed))

    def test_duplicate_key_different_version_is_allowed(self):
        seed = seed_dict()
        twin = json.loads(json.dumps(seed["templates"][0]))
        twin["version_added"] = "3.12"
        seed["templates"].append(twin)
        assert validate_seed(seed) == []
