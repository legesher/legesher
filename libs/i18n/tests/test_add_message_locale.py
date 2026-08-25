"""The locale-addition path for existing message templates (CORE-1850).

``scripts/seed_message_templates.py`` is append-once by design: templates and
their translations enter together, and a database already carrying a seed's
``(implementation, version_added)`` pair is refused. Adding a LOCALE to
templates that already exist is a different operation —
``scripts/add_message_locale.py`` inserts only into ``message_translations``,
against template rows that are already there, reusing the seeder's validation
(placeholder parity, bidi hygiene, locale existence) rather than
reimplementing it.

These tests run against synthetic databases, mirroring
``test_messages_partition.py``; the content of the real seeded
``translations.db`` stays covered by ``test_messages_catalog.py``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.activate_messages_partition import activate
from scripts.add_message_locale import add_locale
from scripts.seed_message_templates import seed_database


@pytest.fixture
def v1_db(tmp_path: Path) -> Path:
    """An operational-shaped database with the partition active and seeded."""
    path = tmp_path / "translations.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL);
        INSERT INTO languages (code, name) VALUES
            ('es', 'Spanish'), ('ar', 'Arabic'), ('fr', 'French'), ('am', 'Amharic');
        """
    )
    conn.commit()
    conn.close()
    activate(path)
    seed_database(path, base_seed())
    return path


def base_seed() -> dict:
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


def fr_addition(**overrides) -> dict:
    base = {
        "implementation": "cpython",
        "locale": "fr",
        "translations": [
            {
                "key": "ZeroDivisionError.division_by_zero",
                "version_added": "3.10",
                "template": "division par zéro",
            },
            {
                "key": "NameError.not_defined",
                "version_added": "3.10",
                "template": "le nom '{name}' n'est pas défini",
                "status": "machine",
            },
        ],
    }
    base.update(overrides)
    return base


def stored_translations(db_path: Path, locale: str) -> dict[str, tuple[str, str]]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT t.key, tr.template, tr.status FROM message_translations tr "
        "JOIN message_templates t ON t.id = tr.template_id WHERE tr.locale = ?",
        (locale,),
    ).fetchall()
    conn.close()
    return {key: (template, status) for key, template, status in rows}


class TestAddLocale:
    def test_round_trip(self, v1_db: Path):
        inserted = add_locale(v1_db, fr_addition())
        assert inserted == 2
        stored = stored_translations(v1_db, "fr")
        assert stored["ZeroDivisionError.division_by_zero"] == (
            "division par zéro",
            "machine",
        )
        assert stored["NameError.not_defined"] == (
            "le nom '{name}' n'est pas défini",
            "machine",
        )

    def test_no_new_version_added_is_invented(self, v1_db: Path):
        """The addition writes translations only — template rows stay as seeded."""
        add_locale(v1_db, fr_addition())
        conn = sqlite3.connect(v1_db)
        versions = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT version_added FROM message_templates"
            )
        ]
        conn.close()
        assert versions == ["3.10"]

    def test_dry_run_writes_nothing(self, v1_db: Path):
        add_locale(v1_db, fr_addition(), dry_run=True)
        assert stored_translations(v1_db, "fr") == {}

    def test_rerun_identical_is_an_explicit_noop(self, v1_db: Path):
        add_locale(v1_db, fr_addition())
        assert add_locale(v1_db, fr_addition()) == 0
        assert len(stored_translations(v1_db, "fr")) == 2

    def test_rerun_with_diverging_content_is_refused(self, v1_db: Path):
        add_locale(v1_db, fr_addition())
        diverged = fr_addition()
        diverged["translations"][0]["template"] = "division par zéro !"
        with pytest.raises(SystemExit, match="already"):
            add_locale(v1_db, diverged)

    def test_partial_identical_rows_are_topped_up_not_duplicated(self, v1_db: Path):
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "INSERT INTO message_translations (template_id, locale, template) "
            "SELECT id, 'fr', 'division par zéro' FROM message_templates "
            "WHERE key = 'ZeroDivisionError.division_by_zero'"
        )
        conn.commit()
        conn.close()
        assert add_locale(v1_db, fr_addition()) == 1
        assert len(stored_translations(v1_db, "fr")) == 2

    def test_partial_diverging_rows_are_refused(self, v1_db: Path):
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "INSERT INTO message_translations (template_id, locale, template) "
            "SELECT id, 'fr', 'division par zéro !' FROM message_templates "
            "WHERE key = 'ZeroDivisionError.division_by_zero'"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit, match="differ"):
            add_locale(v1_db, fr_addition())


class TestAddLocaleValidation:
    def test_mangled_placeholder_is_refused(self, v1_db: Path):
        mangled = fr_addition()
        mangled["translations"][1]["template"] = "le nom '{nom}' n'est pas défini"
        with pytest.raises(SystemExit, match="placeholder"):
            add_locale(v1_db, mangled)

    def test_dropped_placeholder_is_refused(self, v1_db: Path):
        dropped = fr_addition()
        dropped["translations"][1]["template"] = "le nom n'est pas défini"
        with pytest.raises(SystemExit, match="placeholder"):
            add_locale(v1_db, dropped)

    def test_bidi_controls_are_refused(self, v1_db: Path):
        tainted = fr_addition()
        tainted["translations"][0]["template"] = "‏division par zéro"
        with pytest.raises(SystemExit, match="bidi"):
            add_locale(v1_db, tainted)

    def test_unknown_locale_is_refused(self, v1_db: Path):
        with pytest.raises(SystemExit, match="locale"):
            add_locale(v1_db, fr_addition(locale="xx"))

    def test_unknown_template_identity_is_refused(self, v1_db: Path):
        unknown = fr_addition()
        unknown["translations"][0]["key"] = "OverflowError.too_large"
        with pytest.raises(SystemExit, match="OverflowError.too_large"):
            add_locale(v1_db, unknown)

    def test_wrong_version_added_is_refused(self, v1_db: Path):
        wrong = fr_addition()
        wrong["translations"][0]["version_added"] = "3.12"
        with pytest.raises(SystemExit, match="3.12"):
            add_locale(v1_db, wrong)

    def test_incomplete_coverage_is_refused(self, v1_db: Path):
        partial = fr_addition()
        partial["translations"] = partial["translations"][:1]
        with pytest.raises(SystemExit, match="NameError.not_defined"):
            add_locale(v1_db, partial)

    def test_duplicate_entry_is_refused(self, v1_db: Path):
        doubled = fr_addition()
        doubled["translations"].append(dict(doubled["translations"][0]))
        with pytest.raises(SystemExit, match="duplicate"):
            add_locale(v1_db, doubled)

    def test_invalid_status_is_refused(self, v1_db: Path):
        bad = fr_addition()
        bad["translations"][0]["status"] = "verified"
        with pytest.raises(SystemExit, match="status"):
            add_locale(v1_db, bad)

    def test_nothing_written_when_any_entry_is_invalid(self, v1_db: Path):
        """All-or-nothing: one bad entry blocks the whole locale."""
        mangled = fr_addition()
        mangled["translations"][1]["template"] = "le nom '{nom}' n'est pas défini"
        with pytest.raises(SystemExit):
            add_locale(v1_db, mangled)
        assert stored_translations(v1_db, "fr") == {}


class TestRenderContract:
    def test_stray_braces_are_legitimate_translation_content(self, v1_db: Path):
        """Unbalanced braces are accepted, deliberately.

        The catalog renders by LITERAL replacement, never ``str.format`` —
        templates legitimately carry stray braces (CPython's ``f-string:
        valid expression required before '}'``), and so may their
        translations. Refusing them would reject valid content; parity is
        about the named ``{slot}`` set only.
        """
        braced = fr_addition()
        braced["translations"][0]["template"] = "division par zéro }"
        assert add_locale(v1_db, braced) == 2
        stored = stored_translations(v1_db, "fr")
        assert stored["ZeroDivisionError.division_by_zero"][0] == "division par zéro }"


class TestMalformedAdditions:
    def test_missing_template_field_is_a_named_problem(self, v1_db: Path):
        broken = fr_addition()
        del broken["translations"][0]["template"]
        with pytest.raises(SystemExit, match="template"):
            add_locale(v1_db, broken)

    def test_missing_key_field_is_a_named_problem(self, v1_db: Path):
        broken = fr_addition()
        del broken["translations"][0]["key"]
        with pytest.raises(SystemExit, match="key"):
            add_locale(v1_db, broken)

    def test_missing_top_level_field_is_a_named_problem(self, v1_db: Path):
        broken = fr_addition()
        del broken["locale"]
        with pytest.raises(SystemExit, match="locale"):
            add_locale(v1_db, broken)

    def test_missing_database_file_is_refused_without_creating_it(self, tmp_path: Path):
        ghost = tmp_path / "nope.db"
        with pytest.raises(SystemExit, match="not found"):
            add_locale(ghost, fr_addition())
        assert not ghost.exists()


class TestStatusOwnership:
    def test_rerun_after_review_promotion_is_still_a_noop(self, v1_db: Path):
        """Status belongs to the review process once rows exist.

        A stored row promoted ``machine`` → ``reviewed`` must not make an
        identical re-run look like a revision: the idempotence comparison is
        on templates, not status.
        """
        add_locale(v1_db, fr_addition())
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "UPDATE message_translations SET status = 'reviewed' WHERE locale = 'fr'"
        )
        conn.commit()
        conn.close()
        assert add_locale(v1_db, fr_addition()) == 0
        assert stored_translations(v1_db, "fr")[
            "ZeroDivisionError.division_by_zero"
        ] == ("division par zéro", "reviewed")


class TestVersionTiers:
    def test_completed_locale_can_catch_up_to_a_later_seeded_tier(self, v1_db: Path):
        """A tier seeded AFTER a locale was added must not strand the locale.

        Top-up: stored rows that match the addition identically are kept,
        and only the missing tier's rows are inserted — never a duplicate,
        never a refusal of rows that do not differ.
        """
        add_locale(v1_db, fr_addition())
        seed_database(
            v1_db,
            {
                "implementation": "cpython",
                "version_added": "3.12",
                "templates": [
                    {
                        "key": "ZeroDivisionError.division_by_zero",
                        "template_en": "division by zero (reworded)",
                        "placeholders": [],
                        "matcher": "^division by zero \\(reworded\\)$",
                        "translations": {
                            "es": {"template": "división por cero (reformulado)"},
                        },
                    }
                ],
            },
        )
        catch_up = fr_addition()
        catch_up["translations"].append(
            {
                "key": "ZeroDivisionError.division_by_zero",
                "version_added": "3.12",
                "template": "division par zéro (reformulé)",
            }
        )
        assert add_locale(v1_db, catch_up) == 1
        conn = sqlite3.connect(v1_db)
        count = conn.execute(
            "SELECT COUNT(*) FROM message_translations WHERE locale = 'fr'"
        ).fetchone()[0]
        conn.close()
        assert count == 3

    def test_catch_up_with_a_diverging_stored_row_is_refused(self, v1_db: Path):
        add_locale(v1_db, fr_addition())
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "INSERT INTO message_templates "
            "(implementation, key, template_en, placeholders, matcher, version_added) "
            "VALUES ('cpython', 'ZeroDivisionError.division_by_zero', "
            "'division by zero (reworded)', '[]', "
            "'^division by zero \\(reworded\\)$', '3.12')"
        )
        conn.commit()
        conn.close()
        diverged = fr_addition()
        diverged["translations"][0]["template"] = "division par zéro !"
        diverged["translations"].append(
            {
                "key": "ZeroDivisionError.division_by_zero",
                "version_added": "3.12",
                "template": "division par zéro (reformulé)",
            }
        )
        with pytest.raises(SystemExit, match="differ"):
            add_locale(v1_db, diverged)

    def test_addition_covers_every_tier_of_a_key(self, v1_db: Path):
        """A reworded key holds two rows; the locale addition names both."""
        conn = sqlite3.connect(v1_db)
        conn.execute(
            "INSERT INTO message_templates "
            "(implementation, key, template_en, placeholders, matcher, version_added) "
            "VALUES ('cpython', 'ZeroDivisionError.division_by_zero', "
            "'division by zero (reworded)', '[]', "
            "'^division by zero \\(reworded\\)$', '3.12')"
        )
        conn.commit()
        conn.close()

        with pytest.raises(SystemExit, match="3.12"):
            add_locale(v1_db, fr_addition())

        tiered = fr_addition()
        tiered["translations"].append(
            {
                "key": "ZeroDivisionError.division_by_zero",
                "version_added": "3.12",
                "template": "division par zéro (reformulé)",
            }
        )
        assert add_locale(v1_db, tiered) == 3


class TestV2Database:
    def test_add_locale_against_a_v2_build(self, tmp_path: Path):
        from legesher_i18n.db.schema_v2 import read_schema_sql

        db_path = tmp_path / "translations_v2.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(read_schema_sql())
        conn.executemany(
            "INSERT INTO locales "
            "(tag, language_subtag, name, native_name, direction, has_case_distinction) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("es", "es", "Spanish", "español", "ltr", 1),
                ("fr", "fr", "French", "français", "ltr", 1),
            ],
        )
        conn.commit()
        conn.close()
        seed = base_seed()
        for template in seed["templates"]:
            template["translations"].pop("ar", None)
        seed_database(db_path, seed)

        assert add_locale(db_path, fr_addition(), dry_run=True) == 2
        assert stored_translations(db_path, "fr") == {}

        assert add_locale(db_path, fr_addition()) == 2
        stored = stored_translations(db_path, "fr")
        assert stored["NameError.not_defined"] == (
            "le nom '{name}' n'est pas défini",
            "machine",
        )
