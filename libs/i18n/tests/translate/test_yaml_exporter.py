"""Tests for the YAML exporter (CORE-1400 authoritative rewrite).

The exporter's safety contract:

- exports ONLY from ``selected_translations`` (the publish-gated
  canonical layer), never from the dirty-tolerant candidate pool
- rewrites pack sections authoritatively (add / remove / relocate)
- preserves ``implicit_params``, header comments, metadata, and key order
- refuses to write anything for a language with incomplete selections
  (the pre-CORE-1400 partial-rewrite bug class)
- refuses to rewrite an existing pack file it cannot parse back, because
  the rewrite is authoritative and would reset curated metadata — and
  parses ALL five version files before writing the first
- tiers 3.13-only XID characters (CORE-1521) without ever fabricating a
  collision in the stripped pre-3.13 packs, grouping by term NAME the
  way the DB-side guard does
- reports every language a bulk run could not export at the end of the
  run, so the blast radius is never alphabetical — data-integrity
  failures ranked above environmental ones, neither one silent
- never regenerates packaging files over existing ones (uv-workspace
  safety), and generated pyproject carries no [tool.uv.sources]
"""

import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

import pytest
import yaml

from legesher_i18n.db import TranslationDatabase
from tests.interpreter_gaps import NEEDS_UNICODE_15_1
from legesher_i18n.term_definitions import (
    BUILTIN_FUNCTIONS,
    BUILTIN_TYPES,
    EXCEPTIONS,
    EXCEPTIONS_3_11,
    EXCEPTIONS_3_13,
    KEYWORDS_3_10,
    KEYWORDS_3_11,
    KEYWORDS_3_12,
    KEYWORDS_BASE,
    IMPLICIT_PARAMS,
    SPECIAL_CONSTANTS,
    SPECIAL_VALUES,
)
from scripts.translate.yaml_exporter import (
    BulkExportError,
    CorruptSelectionError,
    IncompleteSelectionError,
    InterpreterFloorCollisionError,
    UnparseablePackError,
    UnstrippableXIDError,
    YAMLExporter,
)

# Zero-width joiner: a valid identifier character only on CPython 3.13+
# (Unicode 15.1 XID) — the Sinhala conjunct trap behind CORE-1521.
ZWJ = "‍"

# Katakana middle dot: the same trap in a VISIBLE character. It separates the
# parts of a Japanese compound reading and entered XID_Continue in the same
# Unicode release as ZWJ, which is how `ja` shipped a hard SyntaxError in a
# 3.10-floor pack (CORE-1905).
MIDDLE_DOT = "・"

# In the 3.10 -> 3.13 delta but NOT strippable: removing a Telugu nukta changes
# the word rather than its rendering, so tiering must refuse instead of silently
# publishing something else.
TELUGU_NUKTA = "఼"

#: Strict, so the tests report XPASS once this interpreter assigns the nukta.
#: U+0C3C is new in Unicode 14.0 (CPython 3.11). Before that it is no
#: identifier character at all, so the database refuses to select the value
#: and the exporter never sees it.
NEEDS_TELUGU_NUKTA = pytest.mark.xfail(
    unicodedata.category(TELUGU_NUKTA) == "Cn",
    strict=True,
    reason=(
        "U+0C3C TELUGU SIGN NUKTA is unassigned in this interpreter's Unicode "
        f"tables ({unicodedata.unidata_version}; assigned from 14.0, CPython 3.11)"
    ),
)

_CATEGORY_TERMS = [
    (
        KEYWORDS_BASE + SPECIAL_VALUES + KEYWORDS_3_10 + KEYWORDS_3_11 + KEYWORDS_3_12,
        "keyword",
    ),
    (BUILTIN_FUNCTIONS, "builtin_func"),
    (BUILTIN_TYPES, "builtin_type"),
    (SPECIAL_CONSTANTS, "special_constant"),
    (EXCEPTIONS + EXCEPTIONS_3_11 + EXCEPTIONS_3_13, "exception"),
    (IMPLICIT_PARAMS, "implicit_param"),
]


def _add_language(db, code):
    """Helper to ensure a language exists in the database."""
    conn = db._get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO languages (code, name, native_name) VALUES (?, ?, ?)",
        (code, code.upper(), code.upper()),
    )
    conn.commit()


def _test_value(name: str) -> str:
    """Deterministic unique valid identifier for a term name."""
    if name.endswith("*"):
        return f"t_{name[:-1]}*"
    return f"t_{name}"


def _populate_full_language(db, lang: str) -> dict[str, int]:
    """Create terms + canonical selections covering the full inventory.

    Returns a map of term name -> term id for follow-up tweaks.
    """
    _add_language(db, lang)
    ids: dict[tuple[str, str], int] = {}
    for names, category in _CATEGORY_TERMS:
        for name in names:
            term_id = db.get_or_create_term(
                name, "python", category, allow_duplicate_name=True
            )
            ids[(category, name)] = term_id
            value = _test_value(name)
            db.add_translation(
                term_id=term_id, language_code=lang, translation=value, source="test"
            )
            db.set_selected(term_id=term_id, language_code=lang, translation=value)
    return ids


def _reselect(db, ids, lang: str, category: str, name: str, value: str):
    """Replace the canonical selection for one (category, term) slot."""
    db.set_selected(
        term_id=ids[(category, name)], language_code=lang, translation=value
    )


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = TranslationDatabase(db_path=db_path)
    yield db

    # Close DB before cleanup to avoid Windows file-locking errors
    db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for YAML files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def exporter(temp_db, temp_output_dir):
    """Create YAML exporter instance writing to a temp dir."""
    return YAMLExporter(db=temp_db, output_dir=temp_output_dir)


def _pack_file(temp_output_dir: Path, lang: str, version: str) -> Path:
    return (
        temp_output_dir
        / lang
        / f"legesher_i18n_python_{lang}"
        / "packs"
        / f"{version}.yml"
    )


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestSelectionSourcing:
    """The exporter reads ONLY the canonical selection layer."""

    def test_candidates_alone_do_not_export(self, exporter, temp_db, temp_output_dir):
        """Un-selected candidate translations must never reach a pack."""
        _add_language(temp_db, "es")
        term_id = temp_db.get_or_create_term("def", "python", "keyword")
        temp_db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="definir",
            source="aya",
            confidence="high",
        )
        result = exporter.export_language("es", overwrite=True, strict=False)
        assert result is None
        assert not (temp_output_dir / "es").exists() or not list(
            (temp_output_dir / "es").rglob("*.yml")
        )

    def test_selected_values_are_exported(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        result = exporter.export_language("es", overwrite=True)
        assert result is not None
        data = _load(_pack_file(temp_output_dir, "es", "3.10"))
        assert data["keywords"]["def"] == "t_def"
        assert data["builtins"]["print"] == "t_print"
        assert data["exceptions"]["valueerror"] == "t_valueerror"

    def test_dirty_candidate_never_wins_over_selection(
        self, exporter, temp_db, temp_output_dir
    ):
        """The original CORE-1400 defect: a high-confidence dirty candidate
        must not displace the clean selected value on regen."""
        ids = _populate_full_language(temp_db, "fr")
        temp_db.add_translation(
            term_id=ids[("exception", "arithmeticerror")],
            language_code="fr",
            translation="erreur arithmétique",
            source="aya",
            confidence="high",
        )
        exporter.export_language("fr", overwrite=True)
        data = _load(_pack_file(temp_output_dir, "fr", "3.10"))
        assert data["exceptions"]["arithmeticerror"] == "t_arithmeticerror"


class TestAuthoritativeRewrite:
    """Sections are rewritten from selections: add, remove, relocate."""

    def test_removed_selection_removes_term_from_file(
        self, exporter, temp_db, temp_output_dir
    ):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)

        # Simulate a stale key that no longer belongs in the pack.
        pack = _pack_file(temp_output_dir, "es", "3.10")
        data = _load(pack)
        text = pack.read_text(encoding="utf-8")
        text = text.replace(
            "exceptions:\n", "exceptions:\n  fabricatederror: fabricated\n", 1
        )
        pack.write_text(text, encoding="utf-8")
        assert "fabricatederror" in _load(pack)["exceptions"]

        exporter.export_language("es", overwrite=True)
        data = _load(pack)
        assert "fabricatederror" not in data["exceptions"]
        # Everything legitimate is still there.
        assert data["keywords"]["def"] == "t_def"

    def test_updated_selection_updates_value(self, exporter, temp_db, temp_output_dir):
        ids = _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)

        temp_db.set_selected(
            term_id=ids[("keyword", "while")],
            language_code="es",
            translation="mientras",
        )
        exporter.export_language("es", overwrite=True)
        data = _load(_pack_file(temp_output_dir, "es", "3.10"))
        assert data["keywords"]["while"] == "mientras"

    def test_implicit_params_survive_rewrite(self, exporter, temp_db, temp_output_dir):
        """The old exporter silently dropped implicit_params on rewrite."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        assert _load(pack)["implicit_params"] == {"self": "t_self", "cls": "t_cls"}

        # Rewrite again — still present.
        exporter.export_language("es", overwrite=True)
        assert _load(pack)["implicit_params"] == {"self": "t_self", "cls": "t_cls"}

    def test_version_slot_placement(self, exporter, temp_db, temp_output_dir):
        """Version-specific terms land in their version file only."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)

        d310 = _load(_pack_file(temp_output_dir, "es", "3.10"))
        d311 = _load(_pack_file(temp_output_dir, "es", "3.11"))
        d312 = _load(_pack_file(temp_output_dir, "es", "3.12"))
        d313 = _load(_pack_file(temp_output_dir, "es", "3.13"))
        d314 = _load(_pack_file(temp_output_dir, "es", "3.14"))

        assert "match" in d310["keywords"] and "case" in d310["keywords"]
        assert "except*" not in d310["keywords"]
        assert d311["keywords"] == {"except*": "t_except*"}
        assert set(d311["exceptions"]) == {"exceptiongroup", "baseexceptiongroup"}
        assert d312["keywords"] == {"type": "t_type"}
        assert d313["keywords"] == {}
        assert set(d313["exceptions"]) == {"pythonfinalizationerror"}
        assert d314["keywords"] == {} and d314["exceptions"] == {}
        assert d311["extends"] == "3.10.yml"
        assert d314["extends"] == "3.13.yml"

    def test_dual_slot_type_exports_both_values(
        self, exporter, temp_db, temp_output_dir
    ):
        """'type' as 3.10 builtin and 3.12 soft keyword may differ."""
        ids = _populate_full_language(temp_db, "ca")
        temp_db.set_selected(
            term_id=ids[("keyword", "type")],
            language_code="ca",
            translation="tipus_",
        )
        temp_db.set_selected(
            term_id=ids[("builtin_type", "type")],
            language_code="ca",
            translation="tipus",
        )
        exporter.export_language("ca", overwrite=True)
        assert _load(_pack_file(temp_output_dir, "ca", "3.10"))["builtins"]["type"] == (
            "tipus"
        )
        assert _load(_pack_file(temp_output_dir, "ca", "3.12"))["keywords"]["type"] == (
            "tipus_"
        )


class TestNoPartialWrites:
    """A language with incomplete selections never touches disk."""

    def test_strict_raises_on_incomplete_selections(self, exporter, temp_db):
        _add_language(temp_db, "es")
        term_id = temp_db.get_or_create_term("def", "python", "keyword")
        temp_db.add_translation(
            term_id=term_id, language_code="es", translation="definir", source="test"
        )
        temp_db.set_selected(term_id=term_id, language_code="es", translation="definir")
        with pytest.raises(IncompleteSelectionError, match="no canonical selection"):
            exporter.export_language("es", overwrite=True, strict=True)

    def test_non_strict_skips_without_writing(self, exporter, temp_db, temp_output_dir):
        """Regression guard for the Turkish-pack bug class: a partial
        translation run must never replace/damage an existing pack."""
        _populate_full_language(temp_db, "tr")
        exporter.export_language("tr", overwrite=True)
        pack = _pack_file(temp_output_dir, "tr", "3.10")
        before = pack.read_text(encoding="utf-8")

        # A second language with only 3 selections must not write at all.
        _add_language(temp_db, "xx")
        for name in ("not", "if", "ord"):
            category = "keyword" if name != "ord" else "builtin_func"
            term_id = temp_db.get_or_create_term(
                name, "python", category, allow_duplicate_name=True
            )
            temp_db.add_translation(
                term_id=term_id,
                language_code="xx",
                translation=f"x_{name}",
                source="test",
            )
            temp_db.set_selected(
                term_id=term_id, language_code="xx", translation=f"x_{name}"
            )

        result = exporter.export_language("xx", overwrite=True, strict=False)
        assert result is None
        assert not (temp_output_dir / "xx").exists()
        # And the complete pack is untouched.
        assert pack.read_text(encoding="utf-8") == before

    def test_export_all_skips_incomplete_languages(
        self, exporter, temp_db, temp_output_dir
    ):
        _populate_full_language(temp_db, "es")
        _add_language(temp_db, "uk")
        term_id = temp_db.get_or_create_term("if", "python", "keyword")
        temp_db.add_translation(
            term_id=term_id, language_code="uk", translation="якщо", source="test"
        )
        temp_db.set_selected(term_id=term_id, language_code="uk", translation="якщо")

        results = exporter.export_all_languages(overwrite=True)
        assert "es" in results
        assert "uk" not in results


class TestPresentationPreservation:
    """Header, metadata, and key order survive an authoritative rewrite."""

    def test_metadata_preserved_and_last_updated_stable(
        self, exporter, temp_db, temp_output_dir
    ):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")

        # Curate the metadata the way shipped packs are curated.
        data = _load(pack)
        text = pack.read_text(encoding="utf-8")
        text = text.replace(
            f"last_updated: '{data['metadata']['last_updated']}'",
            "last_updated: '2024-01-01'",
        )
        text = text.replace("community_reviewed: false", "community_reviewed: true")
        text = text.replace(
            "author: Legesher Team (Aya AI Model)", "author: Original Author"
        )
        pack.write_text(text, encoding="utf-8")

        # No content change -> metadata (incl. last_updated) untouched.
        exporter.export_language("es", overwrite=True)
        metadata = _load(pack)["metadata"]
        assert metadata["last_updated"] == "2024-01-01"
        assert metadata["community_reviewed"] is True
        assert metadata["author"] == "Original Author"

    def test_last_updated_refreshes_on_content_change(
        self, exporter, temp_db, temp_output_dir
    ):
        ids = _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        text = pack.read_text(encoding="utf-8")
        original = _load(pack)["metadata"]["last_updated"]
        pack.write_text(
            text.replace(f"last_updated: '{original}'", "last_updated: '2024-01-01'"),
            encoding="utf-8",
        )

        temp_db.set_selected(
            term_id=ids[("keyword", "while")],
            language_code="es",
            translation="mientras",
        )
        exporter.export_language("es", overwrite=True)
        assert _load(pack)["metadata"]["last_updated"] != "2024-01-01"

    def test_existing_header_comment_preserved(
        self, exporter, temp_db, temp_output_dir
    ):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        text = pack.read_text(encoding="utf-8")
        pack.write_text(
            "# Custom curated header\n# Do not lose me\n\nlanguage:"
            + text.split("language:", 1)[1],
            encoding="utf-8",
        )

        exporter.export_language("es", overwrite=True)
        new_text = pack.read_text(encoding="utf-8")
        assert new_text.startswith("# Custom curated header\n# Do not lose me\n")

    def test_existing_key_order_preserved(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        before_keys = list(_load(pack)["keywords"].keys())

        exporter.export_language("es", overwrite=True)
        assert list(_load(pack)["keywords"].keys()) == before_keys


class TestPackagingSafety:
    """Packaging files: YAML-only by default; never overwritten."""

    def test_yaml_only_by_default(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        lang_dir = temp_output_dir / "es"
        assert not (lang_dir / "pyproject.toml").exists()
        assert not (lang_dir / "README.md").exists()
        assert not (lang_dir / "CHANGELOG.md").exists()
        assert not (lang_dir / "legesher_i18n_python_es" / "__init__.py").exists()

    def test_packaging_created_when_requested(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True, include_packaging=True)
        lang_dir = temp_output_dir / "es"
        assert (lang_dir / "pyproject.toml").exists()
        assert (lang_dir / "README.md").exists()
        assert (lang_dir / "CHANGELOG.md").exists()
        assert (lang_dir / "legesher_i18n_python_es" / "__init__.py").exists()

    def test_generated_pyproject_is_workspace_safe(
        self, exporter, temp_db, temp_output_dir
    ):
        """The old template's [tool.uv.sources] editable-path override
        broke the uv workspace (root declares workspace=true)."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True, include_packaging=True)
        toml_text = (temp_output_dir / "es" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert "[tool.uv.sources]" not in toml_text
        assert "editable" not in toml_text

    def test_generated_pyproject_matches_the_shipped_shape(
        self, exporter, temp_db, temp_output_dir
    ):
        """A new pack's pyproject is the one the shipped packs share.

        The template once froze a pre-CORE-1852 shape whose bare
        ``pyproject.toml`` semantic-release path rewrites the ROOT pyproject
        on a pack's first release. Normalized for code, name and version, the
        generated file must equal the most common shipped shape, read from the
        real pack tree, so a future fix to the packs fails here until the
        template carries it too.
        """
        from legesher_i18n.language_registry import get_language_name
        from tests import language_packs_root

        def normalize(text: str, code: str) -> str:
            name = get_language_name(code)
            text = re.sub(r'^version = ".*"$', 'version = "V"', text, flags=re.M)
            for old, new in (
                (f"python/{code}/", "python/CODE/"),
                (f"python_{code}", "python_CODE"),
                (f"python-{code}", "python-CODE"),
                (name, "NAME"),
                (name.lower(), "name"),
            ):
                text = text.replace(old, new)
            return text

        shipped = Counter(
            normalize(path.read_text(encoding="utf-8"), path.parent.name)
            for path in language_packs_root().glob("*/pyproject.toml")
        )
        majority, count = shipped.most_common(1)[0]
        assert count > len(list(language_packs_root().glob("*/pyproject.toml"))) // 2

        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True, include_packaging=True)
        generated = (temp_output_dir / "es" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert normalize(generated, "es") == majority

    def test_packaging_names_the_language_from_the_registry(
        self, exporter, temp_db, temp_output_dir
    ):
        """Bengali was never in the old hand-kept name map, which fell back
        to the upper-cased code ("BN language pack")."""
        _populate_full_language(temp_db, "bn")
        exporter.export_language("bn", overwrite=True, include_packaging=True)
        lang_dir = temp_output_dir / "bn"
        toml_text = (lang_dir / "pyproject.toml").read_text(encoding="utf-8")
        assert "Natural Language :: Bengali" in toml_text
        readme = (lang_dir / "README.md").read_text(encoding="utf-8")
        assert "Bengali (বাংলা)" in readme
        assert "BN" not in readme

    def test_generated_changelog_starts_unreleased(
        self, exporter, temp_db, temp_output_dir
    ):
        """The release stamper rewrites ``## [Unreleased]`` and skips a
        changelog without one, so a new pack must not arrive pre-dated."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True, include_packaging=True)
        text = (temp_output_dir / "es" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [Unreleased]" in text
        assert re.search(r"^## \[\d", text, flags=re.M) is None

    def test_existing_packaging_never_overwritten(
        self, exporter, temp_db, temp_output_dir
    ):
        """Regen must not downgrade pack versions (e.g. fr is 0.0.3)."""
        _populate_full_language(temp_db, "es")
        lang_dir = temp_output_dir / "es"
        lang_dir.mkdir(parents=True, exist_ok=True)
        curated = '[project]\nname = "legesher-i18n-python-es"\nversion = "0.0.3"\n'
        (lang_dir / "pyproject.toml").write_text(curated, encoding="utf-8")

        exporter.export_language("es", overwrite=True, include_packaging=True)
        assert (lang_dir / "pyproject.toml").read_text(encoding="utf-8") == curated


class TestExportIdempotency:
    def test_double_export_is_byte_identical(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        files = sorted((temp_output_dir / "es").rglob("*.yml"), key=lambda p: p.name)
        before = {f.name: f.read_text(encoding="utf-8") for f in files}

        exporter.export_language("es", overwrite=True)
        after = {f.name: f.read_text(encoding="utf-8") for f in files}
        assert before == after

    def test_overwrite_false_skips_existing(self, exporter, temp_db, temp_output_dir):
        ids = _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        before = pack.read_text(encoding="utf-8")

        temp_db.set_selected(
            term_id=ids[("keyword", "while")],
            language_code="es",
            translation="mientras",
        )
        exporter.export_language("es", overwrite=False)
        assert pack.read_text(encoding="utf-8") == before


class TestUnreadableExistingPack:
    """A pack that cannot be read back is never rewritten.

    The rewrite is authoritative, so treating an unreadable file as empty
    silently reset the curated metadata block — license,
    ``python_version_min`` (the interpreter floor itself),
    ``python_version_max``, ``community_reviewed`` — to generated
    defaults, and flipped the new-file empty-section semantics mid-write.
    """

    @staticmethod
    def _curate(pack: Path) -> str:
        """Give a pack the curated metadata a shipped pack carries."""
        text = pack.read_text(encoding="utf-8")
        text = text.replace("python_version_min: '3.10'", "python_version_min: '3.13'")
        text = text.replace("python_version_max: '3.14'", "python_version_max: '3.13'")
        text = text.replace("license: Apache-2.0", "license: MIT")
        pack.write_text(text, encoding="utf-8")
        return text

    def test_corrupt_yaml_raises_and_leaves_the_pack_untouched(
        self, exporter, temp_db, temp_output_dir
    ):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        self._curate(pack)

        # Break the body the way a bad merge or a truncated write would.
        pack.write_text(
            pack.read_text(encoding="utf-8").replace(
                "keywords:\n", "keywords: not: valid: yaml: {{{\n", 1
            ),
            encoding="utf-8",
        )
        corrupted = pack.read_text(encoding="utf-8")
        with pytest.raises(UnparseablePackError, match="not valid YAML"):
            exporter.export_language("es", overwrite=True)
        assert pack.read_text(encoding="utf-8") == corrupted

    def test_corrupt_yaml_does_not_reset_curated_metadata(
        self, exporter, temp_db, temp_output_dir
    ):
        """The reproduced defect: python_version_min/max and license
        silently reverted to generated defaults on regen."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        self._curate(pack)
        before = _load(pack)["metadata"]
        assert before["python_version_min"] == "3.13"

        pack.write_text(
            pack.read_text(encoding="utf-8") + "\nthis is: not: valid: yaml: {{{\n",
            encoding="utf-8",
        )
        with pytest.raises(UnparseablePackError):
            exporter.export_language("es", overwrite=True)

        # Repair the file; the curated metadata is still the curated one.
        text = pack.read_text(encoding="utf-8")
        pack.write_text(
            text.replace("\nthis is: not: valid: yaml: {{{\n", ""), encoding="utf-8"
        )
        exporter.export_language("es", overwrite=True)
        after = _load(pack)["metadata"]
        assert after["python_version_min"] == "3.13"
        assert after["python_version_max"] == "3.13"
        assert after["license"] == "MIT"

    def test_non_mapping_yaml_raises(self, exporter, temp_db, temp_output_dir):
        """Valid YAML that isn't a pack mapping is equally unrewritable."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        pack.write_text("- clobbered\n- by a list\n", encoding="utf-8")

        with pytest.raises(UnparseablePackError, match="not a mapping"):
            exporter.export_language("es", overwrite=True)

    def test_undecodable_file_raises(self, exporter, temp_db, temp_output_dir):
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        pack.write_bytes(b"\xff\xfe not utf-8 at all")

        with pytest.raises(UnparseablePackError, match="not valid UTF-8"):
            exporter.export_language("es", overwrite=True)

    def test_os_error_is_not_a_data_integrity_failure(
        self, exporter, temp_db, temp_output_dir
    ):
        """A permission bit / EIO / IsADirectory is an environmental blip.

        Only the file's CONTENT can be a data-integrity failure; ranking
        an OSError alongside corrupt YAML would let a chmod decide how
        much of a run survives.
        """
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        pack.unlink()
        pack.mkdir()

        # OSError, NOT UnparseablePackError (which is a ValueError).
        with pytest.raises(OSError):
            exporter.export_language("es", overwrite=True)

    def test_a_bad_late_file_rewrites_none_of_the_earlier_ones(
        self, exporter, temp_db, temp_output_dir
    ):
        """The partial-pack-on-disk state, at file granularity.

        ``3.12.yml`` is parsed before ``3.10.yml`` is written, so a bad
        file in the middle of the chain leaves the whole pack directory
        exactly as it was — no rewritten sections, no re-dated metadata.
        """
        ids = _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        packs = sorted((temp_output_dir / "es").rglob("*.yml"))
        assert len(packs) == 5

        broken = _pack_file(temp_output_dir, "es", "3.12")
        broken.write_text(
            broken.read_text(encoding="utf-8") + "\nbad: not: valid: yaml: {{{\n",
            encoding="utf-8",
        )
        before = {p.name: p.read_bytes() for p in packs}

        # A real content change: pre-fix, 3.10 and 3.11 were rewritten
        # with the new value (and re-dated) before 3.12 raised.
        _reselect(temp_db, ids, "es", "keyword", "while", "mientras")
        with pytest.raises(UnparseablePackError, match="3.12.yml"):
            exporter.export_language("es", overwrite=True)

        assert {p.name: p.read_bytes() for p in packs} == before

    def test_missing_file_is_not_a_parse_error(self, exporter, temp_output_dir):
        """A file that does not exist is a new file, not a corrupt one."""
        assert exporter._read_existing(temp_output_dir / "nope.yml") == ({}, None)

    def test_empty_file_reads_as_no_existing_data(self, exporter, temp_output_dir):
        empty = temp_output_dir / "empty.yml"
        empty.write_text("", encoding="utf-8")
        assert exporter._read_existing(empty) == ({}, "")

    def test_bulk_export_does_not_swallow_the_error(
        self, exporter, temp_db, temp_output_dir
    ):
        """A corrupt pack must not be reduced to a log line in a whole-tree
        run — export_all reports data-integrity failures."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        pack = _pack_file(temp_output_dir, "es", "3.10")
        pack.write_text("this is: not: valid: yaml: {{{\n", encoding="utf-8")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)
        assert isinstance(excinfo.value.failures["es"], UnparseablePackError)


class TestInterpreterFloorTiering:
    """CORE-1521: 3.13-only XID characters ship stripped below 3.13.

    ``ZWJ`` is a valid identifier character only from CPython 3.13, so a
    canonical Sinhala conjunct spelling would not tokenize on 3.10-3.12.
    The pre-3.13 packs therefore carry the stripped compatibility form
    and the 3.13 overlay restores the canonical spelling.
    """

    @staticmethod
    def _populate_zwj(db, lang: str = "si") -> dict:
        """Full inventory where three slots carry a ZWJ conjunct."""
        ids = _populate_full_language(db, lang)
        _reselect(db, ids, lang, "keyword", "while", f"t_whi{ZWJ}le")
        _reselect(db, ids, lang, "builtin_func", "print", f"t_pri{ZWJ}nt")
        _reselect(db, ids, lang, "exception", "valueerror", f"t_valu{ZWJ}eerror")
        _reselect(db, ids, lang, "keyword", "except*", f"t_exce{ZWJ}pt*")
        _reselect(db, ids, lang, "implicit_param", "self", f"t_se{ZWJ}lf")
        return ids

    @NEEDS_UNICODE_15_1
    def test_310_carries_the_stripped_form(self, exporter, temp_db, temp_output_dir):
        self._populate_zwj(temp_db)
        exporter.export_language("si", overwrite=True)
        d310 = _load(_pack_file(temp_output_dir, "si", "3.10"))

        assert d310["keywords"]["while"] == "t_while"
        assert d310["builtins"]["print"] == "t_print"
        assert d310["exceptions"]["valueerror"] == "t_valueerror"
        assert d310["implicit_params"]["self"] == "t_self"
        assert ZWJ not in _pack_file(temp_output_dir, "si", "3.10").read_text(
            encoding="utf-8"
        )
        # Untouched values are untouched.
        assert d310["keywords"]["def"] == "t_def"

    @NEEDS_UNICODE_15_1
    def test_313_overlay_restores_the_canonical_form(
        self, exporter, temp_db, temp_output_dir
    ):
        self._populate_zwj(temp_db)
        exporter.export_language("si", overwrite=True)
        d313 = _load(_pack_file(temp_output_dir, "si", "3.13"))

        assert d313["keywords"]["while"] == f"t_whi{ZWJ}le"
        assert d313["builtins"]["print"] == f"t_pri{ZWJ}nt"
        assert d313["exceptions"]["valueerror"] == f"t_valu{ZWJ}eerror"
        assert d313["implicit_params"]["self"] == f"t_se{ZWJ}lf"
        # The 3.13-native term still ships alongside the overlay.
        assert d313["exceptions"]["pythonfinalizationerror"] == (
            "t_pythonfinalizationerror"
        )
        # Only the tiered terms are overlaid — the overlay is not a copy
        # of the base pack.
        assert set(d313["keywords"]) == {"while", "except*"}
        assert set(d313["builtins"]) == {"print"}
        assert set(d313["implicit_params"]) == {"self"}

    @NEEDS_UNICODE_15_1
    def test_311_keyword_is_tiered_in_its_own_file(
        self, exporter, temp_db, temp_output_dir
    ):
        """A version-specific keyword tiers in the file that carries it."""
        self._populate_zwj(temp_db)
        exporter.export_language("si", overwrite=True)

        d311 = _load(_pack_file(temp_output_dir, "si", "3.11"))
        d313 = _load(_pack_file(temp_output_dir, "si", "3.13"))
        assert d311["keywords"]["except*"] == "t_except*"
        assert d313["keywords"]["except*"] == f"t_exce{ZWJ}pt*"

    def test_implicit_params_section_appears_only_when_tiered(
        self, exporter, temp_db, temp_output_dir
    ):
        """Without a ZWJ reserved word, 3.13 grows no implicit_params stub."""
        _populate_full_language(temp_db, "es")
        exporter.export_language("es", overwrite=True)
        assert "implicit_params" not in _load(_pack_file(temp_output_dir, "es", "3.13"))

    @NEEDS_UNICODE_15_1
    def test_tiering_is_idempotent(self, exporter, temp_db, temp_output_dir):
        """Re-export must not re-strip, re-tier, or churn last_updated."""
        self._populate_zwj(temp_db)
        exporter.export_language("si", overwrite=True)
        files = sorted((temp_output_dir / "si").rglob("*.yml"), key=lambda p: p.name)
        before = {f.name: f.read_text(encoding="utf-8") for f in files}

        exporter.export_language("si", overwrite=True)
        after = {f.name: f.read_text(encoding="utf-8") for f in files}
        assert before == after
        d310 = _load(_pack_file(temp_output_dir, "si", "3.10"))
        d313 = _load(_pack_file(temp_output_dir, "si", "3.13"))
        assert d310["keywords"]["while"] == "t_while"
        assert d313["keywords"]["while"] == f"t_whi{ZWJ}le"

    @NEEDS_UNICODE_15_1
    def test_build_version_sections_tiers_without_touching_disk(
        self, exporter, temp_db, temp_output_dir
    ):
        """The tiering step is resolvable in isolation, before any write."""
        self._populate_zwj(temp_db)
        missing: list[str] = []
        sections = exporter._build_version_sections(
            "si", exporter._load_selected_slots("si"), missing
        )

        assert missing == []
        assert sections["3.10"]["keywords"]["while"] == "t_while"
        assert sections["3.13"]["keywords"]["while"] == f"t_whi{ZWJ}le"
        # Section shape per version is load-bearing for empty-stub emission.
        assert set(sections["3.10"]) == {
            "keywords",
            "builtins",
            "exceptions",
            "implicit_params",
        }
        assert set(sections["3.11"]) == {"keywords", "exceptions"}
        assert set(sections["3.12"]) == {"keywords", "exceptions"}
        assert set(sections["3.14"]) == {"keywords", "exceptions"}
        assert not (temp_output_dir / "si").exists()

    def test_incomplete_language_short_circuits_before_tiering(self, exporter, temp_db):
        _add_language(temp_db, "xx")
        term_id = temp_db.get_or_create_term("if", "python", "keyword")
        temp_db.set_selected(term_id=term_id, language_code="xx", translation="x_if")

        missing: list[str] = []
        sections = exporter._build_version_sections(
            "xx", exporter._load_selected_slots("xx"), missing
        )
        assert sections == {}
        assert missing

    @NEEDS_UNICODE_15_1
    def test_strip_collision_within_a_section_raises(
        self, exporter, temp_db, temp_output_dir
    ):
        """Two canonically-distinct keywords must not become one token.

        ``db.find_collisions()`` and audit_collisions.py compare canonical
        values and cannot see this: the values differ until the export
        strips them.
        """
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "while", f"t_aa{ZWJ}bb")
        _reselect(temp_db, ids, "si", "keyword", "for", "t_aabb")

        with pytest.raises(InterpreterFloorCollisionError) as excinfo:
            exporter.export_language("si", overwrite=True)
        message = str(excinfo.value)
        assert "keywords.while" in message and "keywords.for" in message
        assert "t_aabb" in message
        # Nothing was written — the guard runs before any file is opened.
        assert not (temp_output_dir / "si").exists()

    @NEEDS_UNICODE_15_1
    def test_strip_collision_across_sections_raises(self, exporter, temp_db):
        """Cross-section too: sections share one token namespace."""
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "while", f"t_cc{ZWJ}dd")
        _reselect(temp_db, ids, "si", "builtin_func", "print", "t_ccdd")

        with pytest.raises(InterpreterFloorCollisionError, match="builtins.print"):
            exporter.export_language("si", overwrite=True)

    @NEEDS_UNICODE_15_1
    def test_strip_collision_across_version_files_raises(self, exporter, temp_db):
        """The pre-3.13 packs chain by ``extends``, so a 3.10 keyword and
        a 3.12 keyword collide just as fatally.

        The database's own selection guard (``set_selected``) accepts both
        values: they are canonically distinct. Only the export sees them
        collapse.
        """
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "while", "t_eeff")
        _reselect(temp_db, ids, "si", "keyword", "type", f"t_ee{ZWJ}ff")

        with pytest.raises(InterpreterFloorCollisionError, match="keywords.type"):
            exporter.export_language("si", overwrite=True)

    @NEEDS_UNICODE_15_1
    def test_bulk_export_does_not_swallow_a_strip_collision(self, exporter, temp_db):
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "while", f"t_gg{ZWJ}hh")
        _reselect(temp_db, ids, "si", "keyword", "for", "t_gghh")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)
        assert isinstance(excinfo.value.failures["si"], InterpreterFloorCollisionError)

    @NEEDS_UNICODE_15_1
    def test_dual_slot_type_may_differ_by_a_conjunct(
        self, exporter, temp_db, temp_output_dir
    ):
        """The majority real-world pattern must not be blocked.

        22 shipped packs spell the two ``type`` slots (3.10
        builtin, 3.12 soft keyword) differently. One slot adopting a
        conjunct spelling strips onto the other's — but it is the SAME
        term name, which ``db.find_collisions`` deliberately does not
        treat as a round-trip ambiguity (CORE-1400). Keying the guard on
        ``section.name`` instead would block all 22.
        """
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "builtin_type", "type", f"t_ty{ZWJ}pe")
        _reselect(temp_db, ids, "si", "keyword", "type", "t_type")

        exporter.export_language("si", overwrite=True)
        assert _load(_pack_file(temp_output_dir, "si", "3.10"))["builtins"]["type"] == (
            "t_type"
        )
        assert _load(_pack_file(temp_output_dir, "si", "3.12"))["keywords"]["type"] == (
            "t_type"
        )
        # The conjunct spelling is still restored by the 3.13 overlay.
        assert _load(_pack_file(temp_output_dir, "si", "3.13"))["builtins"]["type"] == (
            f"t_ty{ZWJ}pe"
        )

    @NEEDS_UNICODE_15_1
    def test_a_different_term_still_collides_with_a_type_slot(
        self, exporter, temp_db, temp_output_dir
    ):
        """Grouping by name narrows the guard; it does not disable it.

        ``while`` is a different term from ``type``, so its conjunct
        spelling stripping onto the shared ``type`` token IS a round-trip
        ambiguity. ``set_selected`` accepts it — the two values are
        canonically distinct — so only the export can see the collapse.
        """
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "while", f"t_ty{ZWJ}pe")

        with pytest.raises(InterpreterFloorCollisionError) as excinfo:
            exporter.export_language("si", overwrite=True)
        message = str(excinfo.value)
        assert "builtins.type" in message and "keywords.while" in message
        assert not (temp_output_dir / "si").exists()

    def test_identical_values_are_not_a_strip_collision(
        self, exporter, temp_db, temp_output_dir
    ):
        """The dual-slot ``type`` term legitimately shares one spelling
        across sections — that is an upstream concern, not a fabricated
        collision, and must not block the export."""
        ids = _populate_full_language(temp_db, "si")
        _reselect(temp_db, ids, "si", "keyword", "type", "tipo")
        _reselect(temp_db, ids, "si", "builtin_type", "type", "tipo")

        exporter.export_language("si", overwrite=True)
        assert _load(_pack_file(temp_output_dir, "si", "3.10"))["builtins"]["type"] == (
            "tipo"
        )
        assert _load(_pack_file(temp_output_dir, "si", "3.12"))["keywords"]["type"] == (
            "tipo"
        )


@NEEDS_UNICODE_15_1
class TestKatakanaMiddleDotTiering:
    """CORE-1905: the tiering mechanism is not ZWJ-specific.

    U+30FB KATAKANA MIDDLE DOT is a valid identifier character only from
    CPython 3.13, exactly like ZWJ, and removing it leaves the same reading —
    so it tiers by the same route. The exporter's strip set had been written as
    a copy of a two-member ZWJ/ZWNJ list, and `ja`'s `divmod` went out
    untiered.
    """

    @staticmethod
    def _populate_middle_dot(db, lang: str = "ja") -> dict:
        ids = _populate_full_language(db, lang)
        _reselect(db, ids, lang, "builtin_func", "divmod", f"t_divi{MIDDLE_DOT}mod")
        return ids

    def test_310_carries_the_dot_free_form(self, exporter, temp_db, temp_output_dir):
        self._populate_middle_dot(temp_db)
        exporter.export_language("ja", overwrite=True)
        d310 = _load(_pack_file(temp_output_dir, "ja", "3.10"))

        assert d310["builtins"]["divmod"] == "t_divimod"
        assert MIDDLE_DOT not in _pack_file(temp_output_dir, "ja", "3.10").read_text(
            encoding="utf-8"
        )

    def test_313_overlay_restores_the_dot(self, exporter, temp_db, temp_output_dir):
        self._populate_middle_dot(temp_db)
        exporter.export_language("ja", overwrite=True)
        d313 = _load(_pack_file(temp_output_dir, "ja", "3.13"))

        assert d313["builtins"]["divmod"] == f"t_divi{MIDDLE_DOT}mod"
        # The overlay carries the tiered term and nothing it did not need to.
        assert set(d313["builtins"]) == {"divmod"}

    def test_the_two_tiers_are_the_same_word_minus_the_separator(
        self, exporter, temp_db, temp_output_dir
    ):
        self._populate_middle_dot(temp_db)
        exporter.export_language("ja", overwrite=True)
        low = _load(_pack_file(temp_output_dir, "ja", "3.10"))["builtins"]["divmod"]
        high = _load(_pack_file(temp_output_dir, "ja", "3.13"))["builtins"]["divmod"]
        assert high.replace(MIDDLE_DOT, "") == low

    def test_a_middle_dot_collision_is_still_refused(self, exporter, temp_db):
        """Stripping must not make two different terms one token, dot or not."""
        ids = _populate_full_language(temp_db, "ja")
        _reselect(temp_db, ids, "ja", "keyword", "while", f"t_du{MIDDLE_DOT}p")
        _reselect(temp_db, ids, "ja", "keyword", "for", "t_dup")

        with pytest.raises(InterpreterFloorCollisionError):
            exporter.export_language("ja", overwrite=True)


@NEEDS_TELUGU_NUKTA
class TestUnstrippableXIDCharacters:
    """Tiering deletes a character, so it may only delete meaningless ones.

    The validator's detection set is the whole 5,674-codepoint 3.10 -> 3.13
    delta. Most of it is real letters and marks. Stripping one of those would
    publish a DIFFERENT word under the same term while every gate stayed green,
    which is strictly worse than refusing to export.
    """

    def test_an_unstrippable_character_refuses_the_export(
        self, exporter, temp_db, temp_output_dir
    ):
        ids = _populate_full_language(temp_db, "te")
        _reselect(temp_db, ids, "te", "keyword", "while", f"t_whi{TELUGU_NUKTA}le")

        with pytest.raises(UnstrippableXIDError) as excinfo:
            exporter.export_language("te", overwrite=True)
        assert "U+0C3C" in str(excinfo.value)
        assert "keywords.while" in str(excinfo.value)
        # Nothing was written: the refusal happens during resolution.
        assert not (temp_output_dir / "te").exists()

    def test_a_bulk_run_reports_it_as_a_data_integrity_failure(self, exporter, temp_db):
        _populate_full_language(temp_db, "es")
        ids = _populate_full_language(temp_db, "te")
        _reselect(temp_db, ids, "te", "keyword", "while", f"t_whi{TELUGU_NUKTA}le")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)
        assert isinstance(excinfo.value.failures["te"], UnstrippableXIDError)
        assert "te" in excinfo.value.data_integrity


class TestBulkExportBlastRadius:
    """A bulk run's outcome never depends on alphabetical position.

    ``export_all_languages`` iterates ``sorted(...)``, so aborting on the
    first data-integrity failure meant a corrupt ``am`` dropped all 51
    packs while a corrupt ``zh`` dropped one. Each language is written
    all-or-nothing, so the healthy ones complete and the run then fails
    with every failure it found.
    """

    @staticmethod
    def _populate(temp_db, langs=("am", "es", "zh")) -> dict[str, dict]:
        return {lang: _populate_full_language(temp_db, lang) for lang in langs}

    @pytest.mark.parametrize("corrupt", ["am", "zh"])
    def test_blast_radius_is_not_alphabetical(
        self, exporter, temp_db, temp_output_dir, corrupt
    ):
        ids = self._populate(temp_db)
        exporter.export_all_languages(overwrite=True)

        _pack_file(temp_output_dir, corrupt, "3.10").write_text(
            "this is: not: valid: yaml: {{{\n", encoding="utf-8"
        )
        healthy = [lang for lang in ids if lang != corrupt]
        for lang in healthy:
            _reselect(temp_db, ids[lang], lang, "keyword", "while", "t_while2")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)

        assert set(excinfo.value.failures) == {corrupt}
        assert isinstance(excinfo.value.failures[corrupt], UnparseablePackError)
        # Every healthy language exported — first or last in the sort.
        for lang in healthy:
            data = _load(_pack_file(temp_output_dir, lang, "3.10"))
            assert data["keywords"]["while"] == "t_while2"

    def test_every_failure_is_reported_not_just_the_first(
        self, exporter, temp_db, temp_output_dir
    ):
        ids = self._populate(temp_db)
        exporter.export_all_languages(overwrite=True)
        for lang in ("am", "zh"):
            _pack_file(temp_output_dir, lang, "3.10").write_text(
                "this is: not: valid: yaml: {{{\n", encoding="utf-8"
            )
        _reselect(temp_db, ids["es"], "es", "keyword", "while", "t_while2")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)

        assert set(excinfo.value.failures) == {"am", "zh"}
        assert "am" in str(excinfo.value) and "zh" in str(excinfo.value)
        assert (
            _load(_pack_file(temp_output_dir, "es", "3.10"))["keywords"]["while"]
            == "t_while2"
        )

    def test_corrupt_selection_layer_is_not_swallowed(
        self, exporter, temp_db, temp_output_dir
    ):
        """The most severe failure the module names was the one still
        being reduced to a log line."""
        self._populate(temp_db, ("am", "es"))
        conn = temp_db._get_connection()
        conn.execute(
            "UPDATE selected_translations SET translation = ? "
            "WHERE language_code = 'am'",
            ("not an identifier",),
        )
        conn.commit()

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)

        assert isinstance(excinfo.value.failures["am"], CorruptSelectionError)
        assert "es" not in excinfo.value.failures
        assert not (temp_output_dir / "am").exists()
        assert _pack_file(temp_output_dir, "es", "3.10").exists()

    def test_forbidden_letter_planted_past_set_selected_is_refused(
        self, exporter, temp_db, temp_output_dir, monkeypatch
    ):
        """A forbidden letter written straight into the table, past the
        set_selected gate (an old or out-of-band write), still never reaches
        the pack: the exporter re-applies the language's forbidden letters
        when it loads selections. ``zz`` is a synthetic Cyrillic policy that
        forbids the Russian-only ы."""
        from legesher_i18n.script_policy import SCRIPT_POLICIES, ScriptPolicy

        monkeypatch.setitem(
            SCRIPT_POLICIES,
            "zz",
            ScriptPolicy(
                scripts=frozenset({"Cyrillic"}), forbidden_letters=frozenset("ыЫ")
            ),
        )
        _populate_full_language(temp_db, "zz")
        conn = temp_db._get_connection()
        conn.execute(
            "UPDATE selected_translations SET translation = ? "
            "WHERE language_code = 'zz' AND term_id = "
            "(SELECT id FROM terms WHERE name = 'len' AND category = 'builtin_func')",
            ("довжына",),
        )
        conn.commit()

        with pytest.raises(CorruptSelectionError, match="довжына"):
            exporter.export_language("zz", overwrite=True)
        assert not (temp_output_dir / "zz").exists()

    def test_environmental_failure_is_ranked_below_data_integrity(
        self, exporter, temp_db, temp_output_dir
    ):
        """An OSError is the milder diagnosis, not a silent one.

        Ranked below the data-integrity failures — but still reported:
        the pack it skipped is exactly as stale as one a corrupt file
        skipped, and only the raise tells the caller so. Logged-and-
        swallowed let the pipeline print "✓ Exported N language packs"
        over it.
        """
        ids = self._populate(temp_db, ("am", "es"))
        exporter.export_all_languages(overwrite=True)
        pack = _pack_file(temp_output_dir, "am", "3.10")
        pack.unlink()
        pack.mkdir()
        _reselect(temp_db, ids["es"], "es", "keyword", "while", "t_while2")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)

        assert set(excinfo.value.failures) == {"am"}
        assert isinstance(excinfo.value.failures["am"], OSError)
        # Ranked as environmental, NOT as a data-integrity failure.
        assert set(excinfo.value.environmental) == {"am"}
        assert excinfo.value.data_integrity == {}
        # The healthy language still exported — blast radius unchanged.
        assert (
            _load(_pack_file(temp_output_dir, "es", "3.10"))["keywords"]["while"]
            == "t_while2"
        )

    def test_both_failure_kinds_are_reported_and_ranked(
        self, exporter, temp_db, temp_output_dir
    ):
        """One run, both buckets: neither hides the other.

        The severity distinction lives in the buckets and the message
        order, not in whether the run fails at all.
        """
        ids = self._populate(temp_db)
        exporter.export_all_languages(overwrite=True)

        # 'am' sorts FIRST but is only environmental; 'zh' sorts last and
        # is the data-integrity failure — so the message order is a rank,
        # not the alphabet.
        blocked = _pack_file(temp_output_dir, "am", "3.10")
        blocked.unlink()
        blocked.mkdir()
        _pack_file(temp_output_dir, "zh", "3.10").write_text(
            "this is: not: valid: yaml: {{{\n", encoding="utf-8"
        )
        _reselect(temp_db, ids["es"], "es", "keyword", "while", "t_while2")

        with pytest.raises(BulkExportError) as excinfo:
            exporter.export_all_languages(overwrite=True)

        err = excinfo.value
        assert set(err.failures) == {"am", "zh"}
        assert set(err.data_integrity) == {"zh"}
        assert set(err.environmental) == {"am"}
        assert str(err).index("zh:") < str(err).index("am:")
        assert (
            _load(_pack_file(temp_output_dir, "es", "3.10"))["keywords"]["while"]
            == "t_while2"
        )
