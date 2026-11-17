"""The ``messages`` section from the database to the packs and back (CORE-2630).

Covers the exporter (what it writes, where, and what it refuses), the reverse
import, the regeneration gate's view of the section, the dataset export that
must keep messages out, and the shipped packs themselves: a pack's messages
render exactly what the seed's translations rendered before the packs carried
them.

The English side is the real tracked seed. Translations that are not the
seed's are vocalised Arabic and Devanagari.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

import legesher_i18n
from legesher_i18n.db import TranslationDatabase
from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.messages import load_catalog, match_message
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.pack_messages import message_fingerprint
from scripts.activate_messages_partition import activate
from scripts.seed_message_templates import seed_database
from scripts.translate import import_yaml_to_db
from tests.interpreter_gaps import NEEDS_UNICODE_15_1
from tests.translate.test_yaml_exporter import _pack_file, _populate_full_language
from scripts.translate.yaml_exporter import (
    BulkExportError,
    CorruptSelectionError,
    UnplaceableMessageError,
    YAMLExporter,
    _PACK_SECTIONS,
    _PACK_VERSIONS,
)

I18N_ROOT = Path(legesher_i18n.__file__).parents[1]
PACKS_DIR = I18N_ROOT / "language-packs" / "python"
SEED = json.loads(
    (
        Path(legesher_i18n.__file__).parent / "db" / "seeds" / "cpython_messages.json"
    ).read_text(encoding="utf-8")
)
#: Every locale the seed translates, read from the seed.
SEED_LOCALES = sorted(
    {tag for template in SEED["templates"] for tag in template.get("translations", {})}
)


def strip_translations(seed: dict) -> dict:
    copy = json.loads(json.dumps(seed))
    for template in copy["templates"]:
        template.pop("translations", None)
    return copy


def make_db(path: Path, seed: dict | None = SEED) -> TranslationDatabase:
    """A v1 database with the messages partition, seeded from ``seed``."""
    db = TranslationDatabase(db_path=str(path))
    connection = db._get_connection()
    for tag in [*SEED_LOCALES, "zz"]:
        connection.execute(
            "INSERT OR IGNORE INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            (tag, tag, tag),
        )
    connection.commit()
    activate(path)
    if seed is not None:
        seed_database(path, seed)
    return db


def by_version(locale: str) -> dict[str, dict[str, str]]:
    """``{version: {key: text}}`` the seed gives ``locale``, placed by tier."""
    placed: dict[str, dict[str, str]] = {}
    for template in SEED["templates"]:
        translation = template.get("translations", {}).get(locale)
        if translation is None:
            continue
        version = template.get("version_added", SEED["version_added"])
        placed.setdefault(version, {})[template["key"]] = translation["template"]
    return placed


@pytest.fixture
def seeded(tmp_path: Path) -> TranslationDatabase:
    db = make_db(tmp_path / "translations.db")
    yield db
    db.close()


@pytest.fixture
def no_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "home" / ".legesher" / "translations.db"
    monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: path)
    return path


# ---------------------------------------------------------------------------
# What the exporter builds
# ---------------------------------------------------------------------------


class TestBuild:
    @pytest.mark.parametrize("locale", SEED_LOCALES)
    def test_every_translation_is_placed_by_its_tier(self, seeded, tmp_path, locale):
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections(locale)
        got = {
            version: {
                key: entry["text"] for key, entry in body["messages"]["cpython"].items()
            }
            for version, body in built.items()
        }
        assert got == by_version(locale)

    def test_entries_carry_the_fingerprint_of_their_wording(self, seeded, tmp_path):
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections("es")
        key = "UnboundLocalError.before_assignment"
        templates = {
            t.get("version_added", "3.10"): t["template_en"]
            for t in SEED["templates"]
            if t["key"] == key
        }
        for version, template_en in templates.items():
            entry = built[version]["messages"]["cpython"][key]
            assert entry["src"] == message_fingerprint(template_en)

    def test_machine_status_is_left_out_and_others_are_written(self, seeded, tmp_path):
        connection = seeded._get_connection()
        connection.execute(
            "UPDATE message_translations SET status = 'reviewed' WHERE locale = 'ar' "
            "AND template_id = (SELECT id FROM message_templates "
            "WHERE key = 'traceback.header')"
        )
        connection.commit()
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections("ar")
        entries = built["3.10"]["messages"]["cpython"]
        assert entries["traceback.header"]["status"] == "reviewed"
        assert "status" not in entries["NameError.not_defined"]
        assert set(entries["NameError.not_defined"]) == {"text", "src"}

    def test_entries_follow_the_catalog_order(self, seeded, tmp_path):
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections("es")
        assert list(built["3.10"]["messages"]["cpython"]) == list(
            by_version("es")["3.10"]
        )

    def test_a_locale_with_some_translations_exports_those(self, tmp_path):
        """Partial is allowed: one message is a valid section."""
        seed = strip_translations(SEED)
        (zero_div,) = [
            t
            for t in seed["templates"]
            if t["key"] == "ZeroDivisionError.division_by_zero"
        ]
        zero_div["translations"] = {"zz": {"template": "शून्य से भाग"}}
        db = make_db(tmp_path / "translations.db", seed)
        try:
            built = YAMLExporter(
                db, output_dir=tmp_path / "out"
            )._build_message_sections("zz")
        finally:
            db.close()
        assert built == {
            "3.10": {
                "messages": {
                    "cpython": {
                        "ZeroDivisionError.division_by_zero": {
                            "text": "शून्य से भाग",
                            "src": message_fingerprint("division by zero"),
                        }
                    }
                }
            }
        }

    def test_a_locale_with_no_translations_exports_nothing(self, seeded, tmp_path):
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        assert exporter._build_message_sections("zz") == {}

    def test_a_database_without_the_partition_exports_nothing(self, tmp_path):
        db = TranslationDatabase(db_path=str(tmp_path / "translations.db"))
        try:
            exporter = YAMLExporter(db, output_dir=tmp_path / "out")
            assert exporter._build_message_sections("es") == {}
        finally:
            db.close()

    def test_another_implementations_rows_are_not_exported(self, seeded, tmp_path):
        # A plain connection, as the seeder uses: the v1 file has no
        # ``concepts`` table for the partition's foreign key to resolve.
        connection = sqlite3.connect(seeded.db_path)
        cursor = connection.execute(
            "INSERT INTO message_templates (implementation, key, template_en, "
            "placeholders, matcher, version_added) VALUES "
            "('v8', 'ReferenceError.not_defined', 'x is not defined', '[]', "
            "'^x is not defined$', '3.10')"
        )
        connection.execute(
            "INSERT INTO message_translations (template_id, locale, template, status, "
            "source) VALUES (?, 'ar', 'إِكْس غَيْرُ مُعَرَّفٍ', 'machine', 'test')",
            (cursor.lastrowid,),
        )
        connection.commit()
        connection.close()
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections("ar")
        assert {impl for body in built.values() for impl in body["messages"]} == {
            "cpython"
        }

    def test_a_row_that_fails_a_join_rule_is_refused(self, seeded, tmp_path):
        connection = seeded._get_connection()
        connection.execute(
            "UPDATE message_translations SET template = 'الاسم غير معرف' "
            "WHERE locale = 'ar' AND template_id = (SELECT id FROM message_templates "
            "WHERE key = 'NameError.not_defined')"
        )
        connection.commit()
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        with pytest.raises(CorruptSelectionError, match="NameError.not_defined"):
            exporter._build_message_sections("ar")

    def test_a_stored_bidi_control_is_refused(self, seeded, tmp_path):
        connection = seeded._get_connection()
        connection.execute(
            "UPDATE message_translations SET template = ? WHERE locale = 'ar' AND "
            "template_id = (SELECT id FROM message_templates "
            "WHERE key = 'traceback.header')",
            ("‫" + "التتبع (آخر استدعاء في الأسفل):",),
        )
        connection.commit()
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        with pytest.raises(CorruptSelectionError, match="U\\+202B"):
            exporter._build_message_sections("ar")

    def test_a_wording_with_no_pack_file_is_refused(self, seeded, tmp_path):
        connection = seeded._get_connection()
        connection.execute(
            "UPDATE message_templates SET version_added = '3.15' "
            "WHERE key = 'NameError.forgot_import'"
        )
        connection.commit()
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        with pytest.raises(UnplaceableMessageError, match="3.15"):
            exporter._build_message_sections("es")

    def test_the_section_is_registered_with_the_writer(self) -> None:
        assert "messages" in _PACK_SECTIONS
        assert _PACK_VERSIONS == gate.EXPECTED_VERSIONS

    def test_a_key_a_pack_load_would_refuse_stops_the_export(self, seeded, tmp_path):
        """The seeder accepts any key; the exporter must not write a pack that
        does not load, which would take its keywords down with it."""
        connection = sqlite3.connect(seeded.db_path)
        cursor = connection.execute(
            "INSERT INTO message_templates (implementation, key, template_en, "
            "placeholders, matcher, version_added) VALUES "
            "('cpython', 'Recursion', 'maximum recursion depth exceeded', '[]', "
            "'^maximum recursion depth exceeded$', '3.10')"
        )
        connection.execute(
            "INSERT INTO message_translations (template_id, locale, template, status, "
            "source) VALUES (?, 'es', 'profundidad máxima de recursión excedida', "
            "'machine', 'test')",
            (cursor.lastrowid,),
        )
        connection.commit()
        connection.close()
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        with pytest.raises(CorruptSelectionError, match="'Recursion'"):
            exporter._build_message_sections("es")

    def test_unreadable_placeholders_stop_the_export(self, seeded, tmp_path):
        connection = seeded._get_connection()
        connection.execute(
            "UPDATE message_templates SET placeholders = 'not json' "
            "WHERE key = 'NameError.not_defined'"
        )
        connection.commit()
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        with pytest.raises(CorruptSelectionError, match="NameError.not_defined"):
            exporter._build_message_sections("es")

    def test_a_refused_message_leaves_every_pack_file_untouched(self, tmp_path):
        db = make_db(tmp_path / "translations.db")
        try:
            _populate_full_language(db, "es")
            out = tmp_path / "out"
            exporter = YAMLExporter(db, output_dir=out)
            exporter.export_language("es", overwrite=True)
            files = {
                version: _pack_file(out, "es", version).read_bytes()
                for version in _PACK_VERSIONS
            }
            assert b"messages:" in files["3.10"] and b"messages:" in files["3.12"]
            connection = sqlite3.connect(db.db_path)
            # A valid change to a 3.10 translation, so an export that wrote
            # 3.10.yml before reaching the bad 3.12 row would show here.
            connection.execute(
                "UPDATE message_translations SET template = ? WHERE locale = 'es' AND "
                "template_id = (SELECT id FROM message_templates "
                "WHERE key = 'traceback.header')",
                ("Rastreo de llamadas (la más reciente al final):",),
            )
            connection.execute(
                "UPDATE message_translations SET template = ? WHERE locale = 'es' AND "
                "template_id = (SELECT id FROM message_templates "
                "WHERE key = 'NameError.forgot_import')",
                ("\u202b" + "el nombre '{name}' no está definido",),
            )
            connection.commit()
            connection.close()
            with pytest.raises(CorruptSelectionError, match="NameError.forgot_import"):
                exporter.export_language("es", overwrite=True)
            for version, before in files.items():
                assert _pack_file(out, "es", version).read_bytes() == before, version
        finally:
            db.close()

    def test_an_unplaceable_message_is_ranked_as_a_data_failure(self, tmp_path):
        db = make_db(tmp_path / "translations.db")
        try:
            _populate_full_language(db, "es")
            connection = sqlite3.connect(db.db_path)
            connection.execute(
                "UPDATE message_templates SET version_added = '3.15' "
                "WHERE key = 'NameError.forgot_import'"
            )
            connection.commit()
            connection.close()
            exporter = YAMLExporter(db, output_dir=tmp_path / "out")
            with pytest.raises(BulkExportError) as excinfo:
                exporter.export_all_languages(overwrite=True, strict=True)
            assert isinstance(
                excinfo.value.data_integrity.get("es"), UnplaceableMessageError
            )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# What the writer puts on disk
# ---------------------------------------------------------------------------


def write(exporter: YAMLExporter, path: Path, sections: dict) -> str:
    exporter._write_yaml_pack(
        path,
        "zz",
        "3.10",
        None,
        sections,
        "# header\n\n",
        exporter._read_existing(path),
    )
    return path.read_text(encoding="utf-8")


class TestWrite:
    def test_the_built_sections_are_plain_data(self, seeded, tmp_path):
        """A caller may ``yaml.safe_dump`` what the builder returns."""
        built = YAMLExporter(
            seeded, output_dir=tmp_path / "out"
        )._build_message_sections("es")
        assert yaml.safe_load(yaml.safe_dump(built, allow_unicode=True)) == built

    def test_src_is_always_double_quoted(self, seeded, tmp_path):
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        sections = {
            "keywords": {"def": "परिभाषा"},
            **exporter._build_message_sections("es")["3.10"],
        }
        text = write(exporter, tmp_path / "3.10.yml", sections)
        src_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("src:")
        ]
        assert len(src_lines) == len(by_version("es")["3.10"])
        assert all(
            line.startswith('src: "') and line.endswith('"') for line in src_lines
        )

    @pytest.mark.parametrize("src", ["123456789012", "1e1234567890", "0000000000e5"])
    def test_a_numeric_looking_src_reads_back_as_text(self, seeded, tmp_path, src):
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        sections = {
            "keywords": {"def": "परिभाषा"},
            "messages": {"cpython": {"A.b": {"text": "नमस्ते", "src": src}}},
        }
        write(exporter, tmp_path / "3.10.yml", sections)
        loaded = yaml.safe_load((tmp_path / "3.10.yml").read_text(encoding="utf-8"))
        assert loaded["messages"]["cpython"]["A.b"]["src"] == src

    def test_text_survives_the_write_byte_for_byte(self, seeded, tmp_path):
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        text = "الاِسْمُ '{name}' غَيْرُ مُعَرَّفٍ: “{name}”؛ नाम"
        sections = {
            "keywords": {"def": "परिभाषा"},
            "messages": {
                "cpython": {"NameError.not_defined": {"text": text, "src": "a" * 12}}
            },
        }
        write(exporter, tmp_path / "3.10.yml", sections)
        loaded = yaml.safe_load((tmp_path / "3.10.yml").read_text(encoding="utf-8"))
        stored = loaded["messages"]["cpython"]["NameError.not_defined"]["text"]
        assert stored.encode("utf-8") == text.encode("utf-8")

    def test_a_section_with_nothing_left_is_removed_not_emptied(self, seeded, tmp_path):
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        path = tmp_path / "3.10.yml"
        with_messages = {
            "keywords": {"def": "परिभाषा"},
            **exporter._build_message_sections("es")["3.10"],
        }
        assert "messages:" in write(exporter, path, with_messages)
        assert "messages" not in write(exporter, path, {"keywords": {"def": "परिभाषा"}})

    def test_other_sections_are_written_as_before(self, seeded, tmp_path):
        """The pack writer's dumper changes how ``src`` is quoted and nothing else."""
        exporter = YAMLExporter(seeded, output_dir=tmp_path / "out")
        shipped = PACKS_DIR / "fr" / "legesher_i18n_python_fr" / "packs" / "3.10.yml"
        data = yaml.safe_load(shipped.read_text(encoding="utf-8"))
        path = tmp_path / "3.10.yml"
        path.write_bytes(shipped.read_bytes())
        sections = {name: data[name] for name in _PACK_SECTIONS if name in data}
        exporter._write_yaml_pack(
            path, "fr", "3.10", None, sections, "", exporter._read_existing(path)
        )
        assert path.read_bytes() == shipped.read_bytes()


# ---------------------------------------------------------------------------
# Back into the database
# ---------------------------------------------------------------------------


def export_pack(db: TranslationDatabase, out: Path, locale: str) -> Path:
    """Write ``locale``'s message sections as bare pack files under ``out``."""
    packs = out / "packs"
    packs.mkdir(parents=True, exist_ok=True)
    exporter = YAMLExporter(db, output_dir=out / "unused")
    for version, body in exporter._build_message_sections(locale).items():
        (packs / f"{version}.yml").write_text(
            yaml.dump(body, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    return packs


def stored(path: Path, locale: str) -> dict[tuple[str, str], tuple[str, str]]:
    connection = sqlite3.connect(path)
    try:
        return {
            (key, added): (template, status)
            for key, added, template, status in connection.execute(
                "SELECT t.key, t.version_added, tr.template, tr.status "
                "FROM message_translations tr JOIN message_templates t "
                "ON t.id = tr.template_id WHERE tr.locale = ?",
                (locale,),
            )
        }
    finally:
        connection.close()


class TestImport:
    @pytest.mark.parametrize("locale", SEED_LOCALES)
    def test_export_then_import_restores_every_translation(
        self, seeded, tmp_path, locale
    ):
        packs = export_pack(seeded, tmp_path / "pack", locale)
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        imported, skipped = import_yaml_to_db.import_pack_messages(
            locale, fresh, packs_dir=packs
        )
        assert (imported, skipped) == (
            sum(len(v) for v in by_version(locale).values()),
            0,
        )
        assert stored(fresh, locale) == stored(Path(seeded.db_path), locale)

    def test_a_dry_run_writes_nothing(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "es")
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        counts = import_yaml_to_db.import_pack_messages(
            "es", fresh, packs_dir=packs, dry_run=True
        )
        assert counts == (sum(len(v) for v in by_version("es").values()), 0)
        assert stored(fresh, "es") == {}

    @pytest.mark.parametrize(
        ("text", "why"),
        [
            ("el nombre no está definido", "placeholders"),
            ("\u202bel nombre '{name}' no está definido", "bidi"),
        ],
    )
    def test_a_hand_written_entry_that_fails_a_rule_is_skipped(
        self, tmp_path, text, why
    ):
        packs = tmp_path / "packs"
        packs.mkdir()
        (packs / "3.10.yml").write_text(
            yaml.dump(
                {
                    "messages": {
                        "cpython": {
                            "NameError.not_defined": {
                                "text": text,
                                "src": message_fingerprint(
                                    "name '{name}' is not defined"
                                ),
                            }
                        }
                    }
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        assert import_yaml_to_db.import_pack_messages("es", fresh, packs_dir=packs) == (
            0,
            1,
        )
        assert stored(fresh, "es") == {}

    def test_an_unreadable_pack_file_is_skipped_not_fatal(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "es")
        (packs / "3.11.yml").write_text("messages: [unclosed\n", encoding="utf-8")
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        imported, skipped = import_yaml_to_db.import_pack_messages(
            "es", fresh, packs_dir=packs
        )
        assert imported == len(by_version("es")["3.10"]) + len(by_version("es")["3.12"])
        assert skipped == 0

    def test_the_script_imports_the_shipped_messages(self, tmp_path, monkeypatch):
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        monkeypatch.setattr(
            sys,
            "argv",
            ["import_yaml_to_db.py", "--languages", "es", "--db-path", str(fresh)],
        )
        import_yaml_to_db.main()
        assert len(stored(fresh, "es")) == sum(
            len(v) for v in by_version("es").values()
        )

    def test_a_second_import_is_a_no_op(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "ar")
        assert import_yaml_to_db.import_pack_messages(
            "ar", Path(seeded.db_path), packs_dir=packs
        ) == (0, 0)

    def test_the_database_wins_a_conflict(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "ar")
        text = (packs / "3.10.yml").read_text(encoding="utf-8")
        (packs / "3.10.yml").write_text(
            text.replace("الاسم '{name}' غير معرف", "الاِسْمُ '{name}' غَيْرُ مُعَرَّفٍ"),
            encoding="utf-8",
        )
        before = stored(Path(seeded.db_path), "ar")
        assert import_yaml_to_db.import_pack_messages(
            "ar", Path(seeded.db_path), packs_dir=packs
        ) == (0, 1)
        assert stored(Path(seeded.db_path), "ar") == before

    def test_an_entry_for_a_wording_the_database_lacks_is_skipped(self, tmp_path):
        packs = tmp_path / "packs"
        packs.mkdir()
        (packs / "3.10.yml").write_text(
            yaml.dump(
                {
                    "messages": {
                        "cpython": {
                            "NameError.not_defined": {
                                "text": "नाम '{name}' परिभाषित नहीं है",
                                "src": "0" * 12,
                            },
                            "traceback.header": {
                                "text": "ट्रेसबैक (सबसे हाल की कॉल अंत में):",
                                "src": message_fingerprint(
                                    "Traceback (most recent call last):"
                                ),
                                "status": "reviewed",
                            },
                        }
                    }
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        assert import_yaml_to_db.import_pack_messages("zz", fresh, packs_dir=packs) == (
            1,
            1,
        )
        assert stored(fresh, "zz") == {
            ("traceback.header", "3.10"): (
                "ट्रेसबैक (सबसे हाल की कॉल अंत में):",
                "reviewed",
            )
        }

    def test_imported_rows_say_where_they_came_from(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "es")
        fresh = tmp_path / "fresh.db"
        make_db(fresh, strip_translations(SEED)).close()
        import_yaml_to_db.import_pack_messages("es", fresh, packs_dir=packs)
        connection = sqlite3.connect(fresh)
        try:
            provenance = set(
                connection.execute(
                    "SELECT source, created_by FROM message_translations"
                )
            )
        finally:
            connection.close()
        assert provenance == {("pack-import", "import_yaml_to_db.py")}

    def test_a_database_without_the_partition_imports_nothing(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "es")
        bare = TranslationDatabase(db_path=str(tmp_path / "bare.db"))
        bare.close()
        assert import_yaml_to_db.import_pack_messages(
            "es", tmp_path / "bare.db", packs_dir=packs
        ) == (0, 0)

    def test_an_unknown_locale_is_refused(self, seeded, tmp_path):
        packs = export_pack(seeded, tmp_path / "pack", "es")
        with pytest.raises(SystemExit, match="qq"):
            import_yaml_to_db.import_pack_messages(
                "qq", Path(seeded.db_path), packs_dir=packs
            )


# ---------------------------------------------------------------------------
# The regeneration gate
# ---------------------------------------------------------------------------


def _load_gate():
    sys.path.insert(0, str(I18N_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "verify_pack_regen_messages", I18N_ROOT / "scripts" / "verify_pack_regen.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


class TestGate:
    def pack(self, path: Path, messages: dict) -> Path:
        path.write_text(
            yaml.dump(
                {
                    "language": "zz",
                    "target": "python",
                    "version": "3.10",
                    "keywords": {"def": "परिभाषा"},
                    "messages": messages,
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return path

    def test_a_changed_message_is_named_by_its_key(self, tmp_path):
        before = {
            "cpython": {
                "NameError.not_defined": {"text": "नाम", "src": "a" * 12},
                "traceback.header": {"text": "ट्रेसबैक", "src": "b" * 12},
            }
        }
        after = json.loads(json.dumps(before))
        after["cpython"]["NameError.not_defined"]["text"] = "नामः"
        findings: list[dict] = []
        shipped = self.pack(tmp_path / "shipped.yml", before)
        regen = self.pack(tmp_path / "regen.yml", after)
        gate.compare_file(shipped, regen, findings, "zz")
        changed = [f for f in findings if f["kind"] == "value_changed"]
        assert len(changed) == 1
        assert changed[0]["detail"].startswith(
            "messages.cpython.NameError.not_defined:"
        )

    def test_a_status_only_change_is_a_changed_message(self, tmp_path):
        before = {
            "cpython": {"NameError.not_defined": {"text": "नाम", "src": "a" * 12}}
        }
        after = json.loads(json.dumps(before))
        after["cpython"]["NameError.not_defined"]["status"] = "reviewed"
        findings: list[dict] = []
        gate.compare_file(
            self.pack(tmp_path / "s.yml", before),
            self.pack(tmp_path / "r.yml", after),
            findings,
            "zz",
        )
        changed = [f for f in findings if f["kind"] == "value_changed"]
        assert len(changed) == 1 and "reviewed" in changed[0]["detail"]

    def test_an_added_and_a_removed_message_are_named(self, tmp_path):
        before = {
            "cpython": {"NameError.not_defined": {"text": "नाम", "src": "a" * 12}}
        }
        after = {"cpython": {"traceback.header": {"text": "ट्रेसबैक", "src": "b" * 12}}}
        findings: list[dict] = []
        gate.compare_file(
            self.pack(tmp_path / "s.yml", before),
            self.pack(tmp_path / "r.yml", after),
            findings,
            "zz",
        )
        kinds = {(f["kind"], f["detail"].split(" ")[0]) for f in findings}
        assert ("key_removed", "messages.cpython.NameError.not_defined") in kinds
        assert ("key_added", "messages.cpython.traceback.header") in kinds

    def test_the_section_is_no_longer_unknown(self, tmp_path):
        messages = {
            "cpython": {"NameError.not_defined": {"text": "नाम", "src": "a" * 12}}
        }
        findings: list[dict] = []
        gate.compare_file(
            self.pack(tmp_path / "s.yml", messages),
            self.pack(tmp_path / "r.yml", messages),
            findings,
            "zz",
        )
        assert [f for f in findings if f["kind"] != "not_byte_identical"] == []


# ---------------------------------------------------------------------------
# The dataset export keeps messages out
# ---------------------------------------------------------------------------


def _load_export_packs():
    sys.path.insert(0, str(I18N_ROOT))
    spec = importlib.util.spec_from_file_location(
        "export_packs_messages", I18N_ROOT / "scripts" / "export_packs.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped_message_texts() -> dict[str, set[str]]:
    """Every non-empty message text each shipped pack carries, by locale."""
    texts: dict[str, set[str]] = {}
    for locale in get_active_language_codes():
        packs = PACKS_DIR / locale / f"legesher_i18n_python_{locale}" / "packs"
        for path in packs.glob("3.*.yml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for entries in (data.get("messages") or {}).values():
                for entry in entries.values():
                    if entry["text"]:
                        texts.setdefault(locale, set()).add(entry["text"])
    return texts


@NEEDS_UNICODE_15_1  # builds the export at every tier, like test_export_packs.py
def test_message_translations_stay_out_of_the_vocabulary_config() -> None:
    """Until the endorsement keys are content-addressed, no message
    translation is published to the dataset, though packs carry them."""
    texts = shipped_message_texts()
    assert set(SEED_LOCALES) <= set(texts), "the packs were expected to carry messages"
    export_packs = _load_export_packs()
    rows = export_packs.build_rows(
        export_packs.pack_locales(), export_packs.load_registry()
    )
    assert rows
    assert "messages" not in {row["category"] for row in rows}
    leaked = [
        (row["locale"], row["translation"])
        for row in rows
        if row["translation"] in texts.get(row["locale"], set())
    ]
    assert leaked == []


# ---------------------------------------------------------------------------
# The shipped packs
# ---------------------------------------------------------------------------


@pytest.fixture
def seeds_without_translations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the catalog at a copy of the seed with no translations in it."""
    seeds = tmp_path / "seeds"
    seeds.mkdir()
    (seeds / "cpython_messages.json").write_text(
        json.dumps(strip_translations(SEED), ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr("legesher_i18n.messages.SEED_DIR", seeds)
    return seeds


@pytest.fixture(scope="module")
def seeded_catalog(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("catalog") / "translations.db"
    make_db(path).close()
    return path


PARITY = [
    (locale, version)
    for locale in SEED_LOCALES
    for version in LanguagePackLoader().list_available_versions()
]


@pytest.mark.parametrize(("locale", "version"), PARITY)
def test_a_shipped_pack_renders_what_the_seed_rendered(
    no_database, seeds_without_translations, seeded_catalog, locale, version
) -> None:
    """Moving the translations into the packs changes no rendered line.

    The seed the catalog reads here has no translations, so every localized
    line on the pack side came from the pack.
    """
    from_pack = load_catalog(locale, version)
    from_seed = load_catalog(locale, version, db_path=seeded_catalog)
    assert [(r.key, r.template, r.status, r.localized) for r in from_pack] == [
        (r.key, r.template, r.status, r.localized) for r in from_seed
    ]
    assert any(r.localized for r in from_pack)


@pytest.mark.parametrize("locale", SEED_LOCALES)
def test_a_shipped_pack_is_where_the_translations_come_from(
    no_database, seeds_without_translations, locale
) -> None:
    """Prove the pack, not the seed's own translations, supplied the text."""
    loader = LanguagePackLoader()
    pack = loader.load(locale, "python", "3.12", enforce_min_interpreter=False)
    entry = pack.messages["cpython"]["NameError.not_defined"]
    name = "عَدَّادٌ"
    rendered = match_message(
        load_catalog(locale, "3.12"),
        f"name '{name}' is not defined",
        key_prefix="NameError",
    )
    assert rendered == entry["text"].replace("{name}", name)
