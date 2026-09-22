"""CORE-1887: the registry generator must refuse an empty/gutted regeneration.

A stray empty or partial ``translations.db`` (the working DB is untracked since
CORE-1794, so a half-present copy is reachable) used to make the generator
silently rewrite ``languages.json`` — and the VS Code ``languages.ts`` — down to
an empty registry. These tests pin the refusal: no write on an absent DB, an
empty row set, or a drastic shrink against the committed registry, unless
``--force-shrink`` is passed explicitly.
"""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db import TranslationDatabase

I18N_ROOT = Path(__file__).parent.parent
GENERATOR = I18N_ROOT / "legesher_i18n" / "scripts" / "generate_languages.py"


def _load_generator():
    """Import generate_languages.py by path (its dir has no __init__)."""
    spec = importlib.util.spec_from_file_location("generate_languages", GENERATOR)
    assert spec and spec.loader, f"could not create import spec for {GENERATOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()

_LANGS = [
    ("ar", "Arabic", "العربية", "ara", "ar", "rtl"),
    ("es", "Spanish", "Español", "spa", "es", "ltr"),
    ("fr", "French", "Français", "fra", "fr", "ltr"),
]


def _make_db(path: Path, published: int) -> Path:
    """Create a schema-valid translations.db with N published languages."""
    TranslationDatabase(path).close()  # initializes the schema
    conn = sqlite3.connect(path)
    for code, name, native, iso639_2, bcp47, direction in _LANGS[:published]:
        conn.execute(
            "INSERT INTO languages (code, name, native_name, iso639_2, bcp47, "
            "direction, has_case_distinction, status, in_registry) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, 'available', 1)",
            (code, name, native, iso639_2, bcp47, direction),
        )
    conn.commit()
    conn.close()
    return path


def _committed_json(path: Path, codes: list[str]) -> Path:
    """Write a stand-in for the committed languages.json with these entries."""
    path.write_text(
        json.dumps(
            {
                "canonical_language": "en",
                "languages": {
                    code: {"name": code.upper(), "native": code} for code in codes
                },
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    """Point the generator's output paths into tmp_path; return them."""
    languages_json = tmp_path / "languages.json"
    vscode_dir = tmp_path / "generated"
    monkeypatch.setattr(gen, "LANGUAGES_JSON", languages_json)
    monkeypatch.setattr(gen, "VSCODE_GENERATED_DIR", vscode_dir)
    return languages_json, vscode_dir


class TestRegistryGuard:
    def test_missing_db_fails_without_writing(self, tmp_path, artifacts):
        languages_json, vscode_dir = artifacts
        _committed_json(languages_json, ["ar", "es", "fr"])
        before = languages_json.read_text(encoding="utf-8")
        missing = tmp_path / "nope" / "translations.db"

        assert gen.main(["--db", str(missing)]) != 0
        assert languages_json.read_text(encoding="utf-8") == before
        assert not (vscode_dir / "languages.ts").exists()
        # The refusal must not itself create an empty DB at the missing path.
        assert not missing.exists()

    def test_empty_db_fails_without_writing(self, tmp_path, artifacts):
        languages_json, vscode_dir = artifacts
        _committed_json(languages_json, ["ar", "es", "fr"])
        before = languages_json.read_text(encoding="utf-8")
        db = _make_db(tmp_path / "translations.db", published=0)

        assert gen.main(["--db", str(db)]) != 0
        assert languages_json.read_text(encoding="utf-8") == before
        assert not (vscode_dir / "languages.ts").exists()

    def test_drastic_shrink_fails_without_writing(self, tmp_path, artifacts):
        languages_json, vscode_dir = artifacts
        _committed_json(languages_json, ["ar", "es", "fr"])
        before = languages_json.read_text(encoding="utf-8")
        db = _make_db(tmp_path / "translations.db", published=1)

        assert gen.main(["--db", str(db)]) != 0
        assert languages_json.read_text(encoding="utf-8") == before
        assert not (vscode_dir / "languages.ts").exists()

    def test_force_shrink_overrides_refusal(self, tmp_path, artifacts):
        languages_json, vscode_dir = artifacts
        _committed_json(languages_json, ["ar", "es", "fr"])
        db = _make_db(tmp_path / "translations.db", published=1)

        assert gen.main(["--db", str(db), "--force-shrink"]) == 0
        written = json.loads(languages_json.read_text(encoding="utf-8"))
        assert list(written["languages"]) == ["ar"]
        # languages.ts is emitted from the same run, so the override covers it.
        assert "'ar'" in (vscode_dir / "languages.ts").read_text(encoding="utf-8")

    def test_healthy_regeneration_writes_both_artifacts(self, tmp_path, artifacts):
        languages_json, vscode_dir = artifacts
        _committed_json(languages_json, ["ar", "es", "fr"])
        db = _make_db(tmp_path / "translations.db", published=3)

        assert gen.main(["--db", str(db)]) == 0
        written = json.loads(languages_json.read_text(encoding="utf-8"))
        assert sorted(written["languages"]) == ["ar", "es", "fr"]
        ts = (vscode_dir / "languages.ts").read_text(encoding="utf-8")
        assert "'ar'" in ts and "'fr'" in ts

    def test_first_generation_without_committed_json_allows_write(
        self, tmp_path, artifacts
    ):
        # No committed languages.json to compare against: only the empty-DB
        # refusal applies; a small non-empty registry may be written.
        languages_json, vscode_dir = artifacts
        db = _make_db(tmp_path / "translations.db", published=2)

        assert gen.main(["--db", str(db)]) == 0
        written = json.loads(languages_json.read_text(encoding="utf-8"))
        assert sorted(written["languages"]) == ["ar", "es"]
