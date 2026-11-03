"""The message catalog with no translations database (CORE-1679).

No wheel and no clone carries ``translations.db`` (CORE-1794), so the default
path :func:`load_catalog` resolves has nothing behind it on an installed
package or a fresh checkout. The catalog then comes from the tracked seed the
database is filled from. None of these tests needs the real database: the
parity test fills a synthetic one through the real activation script and
seeder, then holds the seed reading to it, so an install renders exactly what
a seeded checkout renders.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

import legesher_i18n
from legesher_i18n import messages
from legesher_i18n.messages import load_catalog, match_message
from scripts.activate_messages_partition import activate
from scripts.seed_message_templates import seed_database, template_version_added

#: Every tracked seed. Located here rather than through ``messages.SEED_DIR``,
#: so a fallback pointed at the wrong directory fails the parity test instead
#: of emptying its parametrization.
SEEDS = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(
        (Path(legesher_i18n.__file__).parent / "db" / "seeds").glob("*.json")
    )
]

#: (implementation, locale, python_version) triples taken from the seeds
#: themselves: every locale a seed translates plus one it does not (English
#: fallback), at every version boundary a seed names plus the running
#: interpreter.
PARITY_CASES = sorted(
    {
        (seed["implementation"], locale, version)
        for seed in SEEDS
        for locale in {
            tag for t in seed["templates"] for tag in t.get("translations", {})
        }
        | {"xx"}
        for version in {template_version_added(t, seed) for t in seed["templates"]}
        | {t["version_removed"] for t in seed["templates"] if t.get("version_removed")}
        | {f"{sys.version_info[0]}.{sys.version_info[1]}"}
    }
)


def operational_db(path: Path, locales: set[str]) -> Path:
    """An operational-shaped database: ``languages`` only, no partition."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO languages (code, name) VALUES (?, ?)",
        [(tag, tag) for tag in sorted(locales)],
    )
    connection.commit()
    connection.close()
    return path


def one_template_seed(implementation: str = "cpython") -> dict:
    """A seed whose single translation no tracked seed carries."""
    return {
        "implementation": implementation,
        "version_added": "3.10",
        "templates": [
            {
                "key": "ZeroDivisionError.division_by_zero",
                "template_en": "division by zero",
                "placeholders": [],
                "matcher": "^division by zero$",
                "translations": {"es": {"template": "división entre cero"}},
            }
        ],
    }


@pytest.fixture
def default_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the default database at a path with nothing behind it yet."""
    path = tmp_path / "home" / ".legesher" / "translations.db"
    monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: path)
    return path


@pytest.fixture(scope="module")
def seeded_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A database filled from every tracked seed by the real seeder."""
    locales = {
        tag
        for seed in SEEDS
        for t in seed["templates"]
        for tag in t.get("translations", {})
    }
    path = operational_db(
        tmp_path_factory.mktemp("seeded") / "translations.db", locales
    )
    activate(path)
    for seed in SEEDS:
        seed_database(path, seed)
    return path


class TestNoDatabase:
    def test_the_package_carries_the_cpython_seed(self):
        # The parity cases below come from SEEDS; an empty list would skip
        # them all rather than fail.
        assert "cpython" in {seed["implementation"] for seed in SEEDS}

    def test_spanish_header_comes_from_the_seed(self, default_db: Path):
        rules = load_catalog("es", "3.12")
        (header,) = [r for r in rules if r.key == "traceback.header"]
        assert header.template == "Rastreo (llamada más reciente al final):"
        assert header.localized
        assert header.status == "machine"

    @pytest.mark.parametrize(
        ("locale", "name", "expected"),
        [
            ("ar", "عَدَّادٌ", "الاسم 'عَدَّادٌ' غير معرف"),
            ("es", "गिनती", "el nombre 'गिनती' no está definido"),
        ],
    )
    def test_slot_values_survive_byte_for_byte(
        self, default_db, locale, name, expected
    ):
        # Vocalised Arabic and Devanagari carry combining marks a lossy
        # normalization would drop or reorder.
        rules = load_catalog(locale, "3.12")
        rendered = match_message(
            rules, f"name '{name}' is not defined", key_prefix="NameError"
        )
        assert rendered == expected
        assert rendered.encode("utf-8") == expected.encode("utf-8")

    def test_reading_the_seed_creates_no_database(self, default_db: Path):
        load_catalog("es", "3.12")
        assert not default_db.exists()
        assert not default_db.parent.exists()

    @pytest.mark.parametrize(("implementation", "locale", "version"), PARITY_CASES)
    def test_seed_reads_as_the_database_it_seeds(
        self, default_db: Path, seeded_db: Path, implementation, locale, version
    ):
        # Same rules, same order: rule order is first-match-wins.
        from_seed = load_catalog(locale, version, implementation=implementation)
        from_db = load_catalog(
            locale, version, implementation=implementation, db_path=seeded_db
        )
        assert from_seed == from_db

    def test_seed_defaults_read_as_the_seeder_stores_them(
        self, default_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # The tracked seeds state every status and most tiers explicitly, so
        # the parity cases above never reach the defaults. This seed leaves
        # both to them: no status (the seeder stores machine) and no
        # template-level version_added (the file's applies).
        seed = one_template_seed()
        seeds = tmp_path / "seeds"
        seeds.mkdir()
        (seeds / "one.json").write_text(
            json.dumps(seed, ensure_ascii=False), encoding="utf-8"
        )
        monkeypatch.setattr(messages, "SEED_DIR", seeds)
        seeded = operational_db(tmp_path / "seeded" / "translations.db", {"es"})
        activate(seeded)
        seed_database(seeded, seed)
        from_seed = load_catalog("es", "3.12")
        assert from_seed == load_catalog("es", "3.12", db_path=seeded)
        assert [(r.status, r.version_added) for r in from_seed] == [("machine", "3.10")]


class TestDatabaseRowsWin:
    def test_rows_in_the_default_database_are_the_whole_catalog(self, default_db: Path):
        operational_db(default_db, {"es"})
        activate(default_db)
        seed_database(default_db, one_template_seed())
        rules = load_catalog("es", "3.12")
        assert [(r.key, r.template) for r in rules] == [
            ("ZeroDivisionError.division_by_zero", "división entre cero")
        ]

    def test_database_without_the_partition_reads_the_seed(self, default_db: Path):
        operational_db(default_db, {"es"})
        keys = {r.key for r in load_catalog("es", "3.12")}
        assert "traceback.header" in keys

    def test_activated_but_unseeded_database_reads_the_seed(self, default_db: Path):
        operational_db(default_db, {"es"})
        activate(default_db)
        keys = {r.key for r in load_catalog("es", "3.12")}
        assert "traceback.header" in keys

    def test_rows_for_another_implementation_do_not_count(self, default_db: Path):
        operational_db(default_db, {"es"})
        activate(default_db)
        seed_database(default_db, one_template_seed(implementation="other"))
        keys = {r.key for r in load_catalog("es", "3.12")}
        assert "traceback.header" in keys


class TestExplicitDbPath:
    """An explicit ``db_path`` gets exactly what it names, never the seed."""

    def test_missing_explicit_database_is_an_empty_catalog(self, tmp_path: Path):
        assert load_catalog("es", "3.12", db_path=tmp_path / "missing.db") == []

    def test_explicit_database_without_the_partition_is_an_empty_catalog(
        self, tmp_path: Path
    ):
        path = operational_db(tmp_path / "old.db", {"es"})
        assert load_catalog("es", "3.12", db_path=path) == []


class TestSeedUnavailable:
    def test_no_database_and_no_seed_is_an_empty_catalog(
        self, default_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(messages, "SEED_DIR", tmp_path / "no-seeds")
        assert load_catalog("es", "3.12") == []

    def test_an_unreadable_seed_file_is_skipped(
        self, default_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        seeds = tmp_path / "seeds"
        seeds.mkdir()
        (seeds / "a_broken.json").write_text("{not json", encoding="utf-8")
        (seeds / "b_one.json").write_text(
            json.dumps(one_template_seed(), ensure_ascii=False), encoding="utf-8"
        )
        monkeypatch.setattr(messages, "SEED_DIR", seeds)
        assert [r.template for r in load_catalog("es", "3.12")] == [
            "división entre cero"
        ]
