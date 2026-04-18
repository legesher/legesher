"""Shared pytest fixtures for legesher-i18n tests."""

import json
import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from legesher_i18n.db import TranslationDatabase

# ---------------------------------------------------------------------------
# Path traversal / inheritance security fixtures (CORE-1143)
# ---------------------------------------------------------------------------


def _write_pack(path: Path, body: str) -> None:
    """Write a YAML pack file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def _build_packs_dir(root: Path, lang: str = "es") -> Path:
    """Create the legesher_i18n_python_{lang}/packs directory under root.

    Returns the ``packs`` directory path.
    """
    packs_dir = root / f"legesher_i18n_python_{lang}" / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    return packs_dir


@pytest.fixture
def traversal_packs_dir(tmp_path):
    """Factory fixture for path-traversal test packs.

    Returns a callable that writes a child pack whose ``extends`` value is
    parametrizable. The callable returns the path to the child pack file.
    """

    def _factory(extends_value: str, lang: str = "es") -> Path:
        packs_dir = _build_packs_dir(tmp_path, lang=lang)

        _write_pack(
            packs_dir / "3.10.yml",
            f"""
            language: {lang}
            target: python
            version: "3.10"
            keywords:
              def: definir
            builtins: {{}}
            exceptions: {{}}
            """,
        )

        _write_pack(
            packs_dir / "3.11.yml",
            f"""
            language: {lang}
            target: python
            version: "3.11"
            extends: "{extends_value}"
            keywords: {{}}
            builtins: {{}}
            exceptions: {{}}
            """,
        )

        return packs_dir / "3.11.yml"

    return _factory


@pytest.fixture
def circular_packs(tmp_path):
    """Two pack files that extend each other — triggers CircularInheritanceError."""
    packs_dir = _build_packs_dir(tmp_path)

    _write_pack(
        packs_dir / "a.yml",
        """
        language: es
        target: python
        version: "3.10"
        extends: "b.yml"
        keywords:
          def: definir
        builtins: {}
        exceptions: {}
        """,
    )

    _write_pack(
        packs_dir / "b.yml",
        """
        language: es
        target: python
        version: "3.10"
        extends: "a.yml"
        keywords:
          def: definir
        builtins: {}
        exceptions: {}
        """,
    )

    return packs_dir / "a.yml"


@pytest.fixture
def deep_chain_packs(tmp_path):
    """Chain of 12 packs (exceeds MAX_INHERITANCE_DEPTH=10)."""
    packs_dir = _build_packs_dir(tmp_path)

    # Base pack (no extends)
    _write_pack(
        packs_dir / "depth_0.yml",
        """
        language: es
        target: python
        version: "3.10"
        keywords:
          def: definir
        builtins: {}
        exceptions: {}
        """,
    )

    # Chain of 11 more packs (total depth = 12, exceeds MAX_INHERITANCE_DEPTH=10)
    for i in range(1, 12):
        _write_pack(
            packs_dir / f"depth_{i}.yml",
            f"""
            language: es
            target: python
            version: "3.10"
            extends: "depth_{i - 1}.yml"
            keywords: {{}}
            builtins: {{}}
            exceptions: {{}}
            """,
        )

    return packs_dir / "depth_11.yml"


@pytest.fixture
def empty_pack(tmp_path):
    """Pack file with empty/null YAML body."""
    packs_dir = _build_packs_dir(tmp_path)
    pack_file = packs_dir / "empty.yml"
    pack_file.write_text("", encoding="utf-8")
    return pack_file


@pytest.fixture
def symlink_escape_packs(tmp_path):
    """Pack dir with a symlink pointing outside the sandbox."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks not supported on this platform")

    packs_dir = _build_packs_dir(tmp_path)

    # Create a target file outside packs dir
    outside = tmp_path / "outside" / "evil.yml"
    _write_pack(
        outside,
        """
        language: es
        target: python
        version: "3.10"
        keywords:
          def: hacked
        builtins: {}
        exceptions: {}
        """,
    )

    # Symlink inside packs pointing outside
    symlink_path = packs_dir / "parent.yml"
    try:
        symlink_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation failed (permissions or OS)")

    # Child pack that extends the symlink
    _write_pack(
        packs_dir / "child.yml",
        """
        language: es
        target: python
        version: "3.11"
        extends: "parent.yml"
        keywords: {}
        builtins: {}
        exceptions: {}
        """,
    )

    return packs_dir / "child.yml"


@pytest.fixture
def temp_db():
    """Create a temporary database for testing.

    Yields a TranslationDatabase instance with a temporary file.
    Automatically cleans up after the test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = TranslationDatabase(db_path=db_path)

    yield db

    # Cleanup
    db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_translations_data():
    """Load sample translations from fixtures.

    Returns the parsed JSON data from sample_translations.json.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "sample_translations.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def populated_db(temp_db, sample_translations_data):
    """Create a database pre-populated with sample data.

    Uses temp_db and sample_translations_data to create a realistic
    test database with terms, languages, and translations.
    """
    conn = temp_db._get_connection()

    # Add languages
    for lang in sample_translations_data.get("languages", []):
        conn.execute(
            """INSERT OR IGNORE INTO languages
               (code, name, native_name, direction, status, has_yaml_pack)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                lang["code"],
                lang["name"],
                lang["native_name"],
                lang.get("direction", "ltr"),
                lang.get("status", "experimental"),
                1 if lang.get("has_yaml_pack") else 0,
            ),
        )
    conn.commit()

    # Add terms and build name->id lookup
    term_ids = {}
    for term in sample_translations_data.get("terms", []):
        term_id = temp_db.get_or_create_term(
            name=term["name"],
            programming_language=term.get("programming_language", "python"),
            category=term.get("category", "unknown"),
            subcategory=term.get("subcategory"),
        )
        term_ids[term["name"]] = term_id

    # Add translations
    translation_ids = []
    for trans in sample_translations_data.get("translations", []):
        term_name = trans["term_name"]
        term_id = term_ids.get(term_name)
        if term_id is None:
            # Auto-create term if not in terms list
            term_id = temp_db.get_or_create_term(
                name=term_name, programming_language="python", category="unknown"
            )
            term_ids[term_name] = term_id

        trans_id = temp_db.add_translation(
            term_id=term_id,
            language_code=trans["language_code"],
            translation=trans["translation"],
            source=trans.get("source", "test"),
            confidence=trans.get("confidence"),
            created_by=trans.get("created_by"),
        )
        translation_ids.append(trans_id)

    # Store IDs for reference in tests
    temp_db.translation_ids = translation_ids
    temp_db.term_ids = term_ids

    return temp_db
