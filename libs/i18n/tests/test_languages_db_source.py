"""CORE-611: translations.db is the single source of truth for the language registry.

These tests guard the DB -> generated-artifact wiring:

- The committed ``languages.json`` and the VS Code ``languages.ts`` must be
  exactly what the generator produces from the DB (drift guards), so a hand-edit
  or a stale regeneration fails CI.
- The DB's ``in_registry`` set must reproduce the published registry, and the DB
  must carry every field the json needs (no data loss).
"""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db import TranslationDatabase

I18N_ROOT = Path(__file__).parent.parent
PKG = I18N_ROOT / "legesher_i18n"
LANGUAGES_JSON = PKG / "languages.json"
LANGUAGES_TS = I18N_ROOT.parent / "vs-code" / "src" / "generated" / "languages.ts"
GENERATOR = PKG / "scripts" / "generate_languages.py"

_REGEN_HINT = (
    "Regenerate with: "
    "uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py"
)


def _load_generator():
    """Import generate_languages.py by path (its dir has no __init__)."""
    spec = importlib.util.spec_from_file_location("generate_languages", GENERATOR)
    assert spec and spec.loader, f"could not create import spec for {GENERATOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


class TestLanguagesGeneratedFromDb:
    """The committed artifacts must equal the generator's output from the DB."""

    def test_languages_json_matches_db(self):
        data = gen.load_registry_from_db()
        expected = gen.generate_json(data)
        actual = LANGUAGES_JSON.read_text(encoding="utf-8")
        assert actual == expected, (
            f"languages.json is out of sync with translations.db. {_REGEN_HINT}"
        )

    def test_languages_ts_matches_db(self):
        data = gen.load_registry_from_db()
        expected = gen.generate_typescript(data)
        actual = LANGUAGES_TS.read_text(encoding="utf-8")
        assert actual == expected, (
            f"vs-code languages.ts is out of sync with translations.db. {_REGEN_HINT}"
        )


class TestRegistryMembership:
    """in_registry defines the published set; it must match the shipped json."""

    def test_in_registry_reproduces_json_language_set(self):
        db_codes = set(gen.load_registry_from_db()["languages"])
        json_codes = set(
            json.loads(LANGUAGES_JSON.read_text(encoding="utf-8"))["languages"]
        )
        assert db_codes == json_codes

    def test_no_field_loss_for_published_languages(self):
        # Every published language must carry the json's required fields in the
        # DB — this is what regressed for 25 languages before the backfill
        # (NULL iso639_2 / bcp47) and must never silently return.
        for code, meta in gen.load_registry_from_db()["languages"].items():
            assert meta["iso639_2"], f"{code} missing iso639_2 in DB"
            assert meta["bcp47"], f"{code} missing bcp47 in DB"
            assert meta["name"], f"{code} missing name"
            assert meta["native"], f"{code} missing native name"
            assert meta["status"], f"{code} missing status"
            assert isinstance(meta["rtl"], bool)
            assert isinstance(meta["has_case_distinction"], bool)


class TestRegistrySanity:
    """Spot-check the DB->json field mapping."""

    def test_rtl_mapping(self):
        langs = gen.load_registry_from_db()["languages"]
        for rtl_code in ("ar", "ur", "fa"):
            assert langs[rtl_code]["rtl"] is True, f"{rtl_code} should be RTL"
        assert langs["es"]["rtl"] is False

    def test_canonical_language_is_en(self):
        assert gen.load_registry_from_db()["canonical_language"] == "en"


class TestGeneratorFailsFast:
    """A published language missing iso639_2/bcp47 must abort generation, not
    silently emit an empty string (guards the CORE-611 backfill from regressing)."""

    def test_missing_iso_or_bcp47_raises(self, tmp_path):
        db_path = str(tmp_path / "partial.db")
        TranslationDatabase(db_path=db_path).close()  # create schema + columns
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO languages (code, name, native_name, iso639_2, bcp47, "
            "direction, status, in_registry) "
            "VALUES ('xx', 'Example', 'Example', NULL, NULL, 'ltr', "
            "'experimental', 1)"
        )
        conn.commit()
        conn.close()
        with pytest.raises(ValueError, match="iso639_2/bcp47"):
            gen.load_registry_from_db(db_path=db_path)
