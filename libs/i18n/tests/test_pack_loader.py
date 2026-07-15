"""Tests for pack_loader module."""

import textwrap

import pytest
import yaml
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.exceptions import (
    CircularInheritanceError,
    MaxInheritanceDepthError,
    PackNotFoundError,
    PackValidationError,
    PathTraversalError,
    UnsupportedInterpreterError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _write_yml(path: Path, body: str) -> None:
    """Write dedented YAML to *path*. Mirrors the conftest `_write_pack` helper."""
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


class TestLanguagePackLoading:
    """Test basic language pack loading."""

    def test_load_spanish_pack(self):
        """Test loading Spanish language pack for Python 3.10."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        assert pack.language == "es"
        assert pack.target == "python"
        assert pack.version == "3.10"
        assert len(pack.keywords) > 0
        assert "def" in pack.keywords
        assert pack.keywords["def"] == "definir"

    def test_load_arabic_pack(self):
        """Test loading Arabic language pack."""
        loader = LanguagePackLoader()
        pack = loader.load("ar", "python", "3.10")

        assert pack.language == "ar"
        assert "def" in pack.keywords
        assert pack.keywords["def"] == "تعريف"  # Arabic translation

    def test_load_nonexistent_pack(self):
        """Test error for nonexistent pack."""
        loader = LanguagePackLoader()

        with pytest.raises(PackNotFoundError) as exc_info:
            loader.load("xx", "python", "3.10")

        assert "xx" in str(exc_info.value)

    def test_pack_immutability(self):
        """Test that LanguagePack is immutable (frozen dataclass)."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        # Should not be able to modify
        with pytest.raises((AttributeError, Exception)):
            pack.language = "fr"


class TestPackInheritance:
    """Test language pack inheritance."""

    def test_inheritance_keyword_merging(self):
        """Test that child pack inherits and overrides parent keywords."""
        loader = LanguagePackLoader()

        # Load 3.10 pack (base)
        _ = loader.load("es", "python", "3.10")

        # Load 3.11 pack (inherits from 3.10)
        pack_311 = loader.load("es", "python", "3.11")

        # 3.11 should have all 3.10 keywords
        assert "def" in pack_311.keywords
        assert "class" in pack_311.keywords
        assert pack_311.keywords["def"] == "definir"

        # Plus 3.11-specific keywords
        assert "except*" in pack_311.keywords
        assert pack_311.keywords["except*"] == "excepto*"

    def test_multi_level_inheritance(self):
        """Test inheritance through multiple levels."""
        loader = LanguagePackLoader()

        # 3.13 inherits from 3.12, which inherits from 3.11, which inherits from 3.10
        pack_313 = loader.load("es", "python", "3.13")

        # Should have keywords from all levels
        assert "def" in pack_313.keywords  # From 3.10
        assert "except*" in pack_313.keywords  # From 3.11
        assert "type" in pack_313.keywords  # From 3.12

        # Verify inheritance chain
        assert len(pack_313.inheritance_chain) >= 4

    def test_inheritance_builtins(self):
        """Test that builtins are also inherited."""
        loader = LanguagePackLoader()

        pack_311 = loader.load("es", "python", "3.11")

        # Builtins from base pack should be present
        assert "print" in pack_311.builtins
        assert pack_311.builtins["print"] == "imprimir"

    def test_fixture_inheritance(self):
        """Test inheritance with test fixtures."""
        # TODO: Implement fixture-based inheritance tests
        # For now, test with real packs which have proper inheritance
        pass


class TestPackCaching:
    """Test language pack caching."""

    def test_cache_hit(self):
        """Test that packs are cached after first load."""
        loader = LanguagePackLoader()

        # Load pack twice
        pack1 = loader.load("es", "python", "3.10")
        pack2 = loader.load("es", "python", "3.10")

        # Should be the same object (cached)
        assert pack1 is pack2

        # Check cache stats
        stats = loader.get_cache_stats()
        assert stats["size"] >= 1

    def test_cache_clear(self):
        """Test cache clearing."""
        loader = LanguagePackLoader()

        # Load and cache
        loader.load("es", "python", "3.10")
        assert loader.get_cache_stats()["size"] >= 1

        # Clear cache
        loader.clear_cache()
        assert loader.get_cache_stats()["size"] == 0


class TestLanguagePackMethods:
    """Test LanguagePack methods."""

    def test_get_keyword_translation(self):
        """Test getting keyword translations."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        assert pack.get_keyword_translation("def") == "definir"
        assert pack.get_keyword_translation("class") == "clase"
        assert pack.get_keyword_translation("nonexistent") is None

    def test_get_builtin_translation(self):
        """Test getting builtin translations."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        assert pack.get_builtin_translation("print") == "imprimir"
        assert pack.get_builtin_translation("len") == "longitud"
        assert pack.get_builtin_translation("nonexistent") is None

    def test_get_exception_translation_falls_back_to_original_case(self):
        """Exception lookup tries lowercase first, then the original-case key.

        The lowercase-first convention is a translation-table internal detail;
        the fallback path exists so callers can pass either canonical form.
        Also pins the ``or``-based fallthrough for falsy values: an empty
        translation string is treated as falsy and falls through to the
        original-case lookup, which is the current intended semantics for
        packs that partially populate both keys.
        """
        from legesher_i18n.pack_loader import LanguagePack

        # Only original-case entry, no lowercase
        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            exceptions={"ValueError": "ErrorDeValor"},
        )
        assert pack.get_exception_translation("ValueError") == "ErrorDeValor"
        # Lowercase-only entry also works via the first branch
        pack2 = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            exceptions={"valueerror": "errordevalor"},
        )
        assert pack2.get_exception_translation("ValueError") == "errordevalor"
        # Empty lowercase value falls through to the original-case key
        # (`or` treats "" as falsy — intentional for packs that partially
        # populate both keys without wanting the lowercase entry to win).
        pack3 = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            exceptions={"valueerror": "", "ValueError": "ErrorDeValor"},
        )
        assert pack3.get_exception_translation("ValueError") == "ErrorDeValor"
        # Missing altogether
        assert pack.get_exception_translation("TypeError") is None

    def test_has_keyword(self):
        """Test keyword existence checking."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        assert pack.has_keyword("def")
        assert pack.has_keyword("class")
        assert not pack.has_keyword("nonexistent")

    def test_repr(self):
        """Test __repr__ method."""
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")

        repr_str = repr(pack)
        assert "LanguagePack" in repr_str
        assert "es" in repr_str
        assert "python" in repr_str


class TestPathTraversalDefense:
    """Unit tests for _is_safe_parent_path heuristic (CORE-1143).

    Tests the simplified signature after dead-parameter removal:
    ``_is_safe_parent_path(self, extends: str) -> bool``
    """

    @pytest.mark.parametrize(
        "extends,expected",
        [
            ("../3.10/es.yml", True),
            ("../3.10.yml", True),
            ("../../etc/passwd", False),
            ("../../../secrets.yml", False),
            ("foo/../bar.yml", False),
            ("foo/../../bar.yml", False),
            ("..", False),
            ("../", True),  # starts with ../ and count==1; heuristic allows it
            ("..\\passwd", False),
            ("..%2Fpasswd", False),
            ("\u3002\u3002\uff0fpasswd", False),  # fullwidth ..／
        ],
    )
    def test_is_safe_parent_path_branches(self, extends, expected):
        loader = LanguagePackLoader()
        assert loader._is_safe_parent_path(extends) is expected

    def test_safe_parent_path_rejects_bare_dotdot(self):
        loader = LanguagePackLoader()
        assert loader._is_safe_parent_path("..") is False

    def test_safe_parent_path_allows_single_level(self):
        """Pin the True branch so future hardening doesn't break version inheritance."""
        loader = LanguagePackLoader()
        assert loader._is_safe_parent_path("../3.10/es.yml") is True


class TestPathTraversalIntegration:
    """End-to-end tests exercising _resolve_inheritance with tempdir YAML (CORE-1143)."""

    def test_rejects_multi_level_parent_traversal(self, traversal_packs_dir):
        child = traversal_packs_dir(extends_value="../../etc/passwd")
        loader = LanguagePackLoader()
        with pytest.raises(PathTraversalError):
            loader._resolve_inheritance(child, set())

    def test_rejects_embedded_dotdot(self, traversal_packs_dir):
        child = traversal_packs_dir(extends_value="foo/../bar.yml")
        loader = LanguagePackLoader()
        with pytest.raises(PathTraversalError):
            loader._resolve_inheritance(child, set())

    def test_allows_sibling_extends(self, traversal_packs_dir):
        """Sibling extends (no ..) should resolve normally."""
        child = traversal_packs_dir(extends_value="3.10.yml")
        loader = LanguagePackLoader()
        data, chain = loader._resolve_inheritance(child, set())
        assert "keywords" in data

    def test_symlink_escaping_packs_dir_is_rejected(self, symlink_escape_packs):
        """Symlink to outside packs dir should be rejected by some defense layer."""
        loader = LanguagePackLoader()
        with pytest.raises((PathTraversalError, PackValidationError)):
            loader._resolve_inheritance(symlink_escape_packs, set())

    def test_null_byte_in_extends_is_rejected(self, traversal_packs_dir):
        child = traversal_packs_dir(extends_value="pack\x00.yml")
        loader = LanguagePackLoader()
        # Null byte is caught by YAML reader before pack loader sees it
        with pytest.raises((PackValidationError, yaml.YAMLError)):
            loader._resolve_inheritance(child, set())

    def test_dotdot_substring_in_filename_not_blocked(self, traversal_packs_dir):
        """CORE-1187: benign filenames containing ``..`` must not trip
        ``PathTraversalError``.

        The pre-CORE-1187 call site did ``".." in extends`` (substring
        match), which spuriously routed ``foo..bar.yml`` through the
        traversal path. The component check should let it proceed; the
        load then fails with ``PackValidationError`` because the file
        doesn't exist, which is the correct error for a missing parent.
        """
        child = traversal_packs_dir(extends_value="foo..bar.yml")
        loader = LanguagePackLoader()
        with pytest.raises(PackValidationError):
            loader._resolve_inheritance(child, set())


class TestInheritanceEdgeCases:
    """Non-security edge cases that close adjacent coverage gaps (CORE-1143)."""

    def test_circular_inheritance_raises(self, circular_packs):
        loader = LanguagePackLoader()
        with pytest.raises(CircularInheritanceError):
            loader._resolve_inheritance(circular_packs, set())

    def test_max_inheritance_depth_raises(self, deep_chain_packs):
        loader = LanguagePackLoader()
        with pytest.raises(MaxInheritanceDepthError):
            loader._resolve_inheritance(deep_chain_packs, set())

    def test_empty_yaml_pack_resolves(self, empty_pack):
        loader = LanguagePackLoader()
        data, chain = loader._resolve_inheritance(empty_pack, set())
        assert data == {}
        assert len(chain) == 1

    def test_pack_outside_packs_dir_refuses_inheritance(self, tmp_path):
        """CORE-1112 / CORE-1187: cover the defensive raise that fires when
        a pack with an ``extends`` field isn't inside a ``packs/`` directory.

        This path is unreachable through the public ``load()`` API (all 51
        real packs live in the monorepo ``packs/`` layout) but guards
        against future layout changes that would otherwise silently skip
        the sandbox derivation. ``_resolve_inheritance`` is called
        directly to exercise it.
        """
        # Base sibling in the same directory (no packs/ ancestor)
        _write_yml(
            tmp_path / "base.yml",
            """
            language: es
            target: python
            version: "3.10"
            keywords: {}
            builtins: {}
            exceptions: {}
            """,
        )
        # Child extends the base, but neither is inside a packs/ dir
        child = tmp_path / "child.yml"
        _write_yml(
            child,
            """
            language: es
            target: python
            version: "3.11"
            extends: base.yml
            keywords: {}
            builtins: {}
            exceptions: {}
            """,
        )
        loader = LanguagePackLoader()
        with pytest.raises(PackValidationError, match="Cannot derive sandbox root"):
            loader._resolve_inheritance(child, set())


class TestPackLoaderEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_keywords_section(self):
        """Test pack with empty keywords (like 3.13/es.yml)."""
        loader = LanguagePackLoader()

        # 3.13 has empty keywords section but inherits everything
        pack = loader.load("es", "python", "3.13")

        # Should still have keywords from inheritance
        assert len(pack.keywords) > 0
        assert "def" in pack.keywords

    def test_metadata_inheritance(self):
        """Test that metadata is properly set from child pack."""
        loader = LanguagePackLoader()

        pack = loader.load("es", "python", "3.11")

        assert pack.metadata is not None
        assert pack.metadata.python_version_min == "3.11"

    def test_loader_repr(self):
        """Test LanguagePackLoader __repr__."""
        loader = LanguagePackLoader()
        repr_str = repr(loader)

        assert "LanguagePackLoader" in repr_str

    def test_list_available_languages_handles_unreadable_metadata(self, tmp_path):
        """CORE-1112: cover the except branch in ``list_available_languages``
        that falls back to the uppercased language code when a discovered
        pack's metadata YAML can't be parsed.

        Builds a fake discovered pack with an invalid ``default.yml`` and
        injects it directly into ``_discovered_packs`` so the method walks
        the broken-metadata path without needing a real installed dist.
        """
        fake_pack_dir = tmp_path / "legesher_i18n_python_zz"
        (fake_pack_dir / "packs").mkdir(parents=True)
        (fake_pack_dir / "packs" / "default.yml").write_text(
            ":\n:invalid-yaml:\n", encoding="utf-8"
        )

        loader = LanguagePackLoader()
        loader._discovered_packs = {"python-zz": fake_pack_dir}

        results = loader.list_available_languages("python")
        # The fake pack still appears in results, with the fallback name
        # (uppercased language code) since metadata parsing failed.
        fake_entry = [(code, name) for code, name in results if code == "zz"]
        assert fake_entry == [("zz", "ZZ")]


class TestReservedWordsLanguagePack:
    """Test LanguagePack reserved_words support (CORE-710)."""

    def test_default_reserved_words_is_empty(self):
        """Backward-compat: constructor without reserved_words defaults to empty."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(language="es", target="python", version="3.10")
        assert pack.reserved_words == {}

    def test_get_reserved_word_translation_returns_value(self):
        """Canonical accessor returns the configured translation."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            reserved_words={"self": "propio", "cls": "clase"},
        )
        assert pack.get_reserved_word_translation("self") == "propio"
        assert pack.get_reserved_word_translation("cls") == "clase"

    def test_get_reserved_word_translation_returns_none_for_missing(self):
        """Missing reserved word returns None, not raises."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(language="es", target="python", version="3.10")
        assert pack.get_reserved_word_translation("self") is None

    def test_has_reserved_word(self):
        """has_reserved_word predicate matches presence in reserved_words dict."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            reserved_words={"self": "propio"},
        )
        assert pack.has_reserved_word("self") is True
        assert pack.has_reserved_word("cls") is False

    def test_get_keyword_translation_falls_back_to_reserved_words(self):
        """get_keyword_translation falls back to reserved_words when keyword missing.

        Madison's CORE-710 test API uses pack.get_keyword_translation("self")
        as the unified accessor; this assertion pins that contract.
        """
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            keywords={"def": "definir"},
            reserved_words={"self": "propio", "cls": "clase"},
        )
        # Primary keyword still works
        assert pack.get_keyword_translation("def") == "definir"
        # Falls back to reserved_words for self/cls
        assert pack.get_keyword_translation("self") == "propio"
        assert pack.get_keyword_translation("cls") == "clase"
        # Neither section: returns None
        assert pack.get_keyword_translation("xyz") is None

    def test_keyword_section_wins_over_reserved_words_on_conflict(self):
        """Lookup-order regression: keyword translation never shadowed.

        If a synthetic conflict is constructed (a key in BOTH sections),
        the keywords entry wins. self/cls would never appear in keywords
        in real packs, but this contract is enforced for safety.
        """
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="zz",
            target="python",
            version="3.10",
            keywords={"self": "KEYWORD_VALUE"},
            reserved_words={"self": "RESERVED_VALUE"},
        )
        assert pack.get_keyword_translation("self") == "KEYWORD_VALUE"

    def test_repr_includes_reserved_words_count(self):
        """__repr__ surfaces the reserved_words count for debug visibility."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            reserved_words={"self": "propio", "cls": "clase"},
        )
        assert "reserved_words=2" in repr(pack)

    def test_existing_pack_loads_with_reserved_words(self):
        """End-to-end: real es pack ships reserved_words at 3.13.

        Post-CORE-710: every pack has a ``reserved_words:`` section.
        This test confirms the section is loaded correctly through the
        inheritance chain (we wrote to 3.10.yml; 3.13 inherits from 3.12
        from 3.11 from 3.10).
        """
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.13")
        # Reserved words populated via inheritance from 3.10
        assert pack.reserved_words.get("self") is not None
        assert pack.reserved_words.get("cls") is not None
        # Existing keyword lookup still works
        assert pack.get_keyword_translation("def") is not None


class TestReservedWordsInheritance:
    """Test that reserved_words are inherited via _merge_packs (CORE-710).

    Pack 3.10 is the canonical base; 3.11/3.12/3.13 extend via the
    ``extends:`` field. After step 9 lands reserved_words only in 3.10.yml,
    higher versions should inherit through the merge logic. These tests
    pin that behavior with synthetic dicts (mirrors pack_loader's
    `_merge_packs` semantics).
    """

    def test_merge_inherits_reserved_words_from_base(self):
        """Child pack with no reserved_words inherits base pack's section."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            # No reserved_words — should inherit
            "keywords": {"match": "coincidir"},
        }
        merged = loader._merge_packs(base, override)
        assert merged["reserved_words"] == {"self": "propio", "cls": "clase"}

    def test_merge_override_reserved_words_take_precedence(self):
        """Child pack's reserved_words override base for matching keys."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            "reserved_words": {"self": "instancia"},  # override only `self`
        }
        merged = loader._merge_packs(base, override)
        # `self` overridden, `cls` inherited from base
        assert merged["reserved_words"]["self"] == "instancia"
        assert merged["reserved_words"]["cls"] == "clase"

    def test_merge_no_reserved_words_in_either_pack(self):
        """When neither base nor override has reserved_words, key absent."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            "keywords": {"match": "coincidir"},
        }
        merged = loader._merge_packs(base, override)
        # Reserved_words key not added when not present in either
        assert "reserved_words" not in merged

    def test_merge_only_override_has_reserved_words(self):
        """If only the override has reserved_words, they're preserved."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            "reserved_words": {"self": "propio"},
        }
        merged = loader._merge_packs(base, override)
        assert merged["reserved_words"] == {"self": "propio"}

    def test_loaded_pack_with_synthetic_reserved_words_section(self, tmp_path):
        """Integration: pack file with reserved_words: section loads correctly.

        Constructs a synthetic on-disk pack with reserved_words populated,
        loads it via LanguagePackLoader, and confirms the section flows
        through to LanguagePack.reserved_words. This pins the behavior
        that step 9 will rely on once we write reserved_words to all 51
        real pack YAMLs.
        """
        import yaml

        pack_data = {
            "language": "zz",  # synthetic non-existent language
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "builtins": {"print": "imprimir"},
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        pack_path = tmp_path / "3.10.yml"
        pack_path.write_text(yaml.safe_dump(pack_data), encoding="utf-8")

        # Use SchemaValidator directly to confirm the schema accepts the file
        from legesher_i18n.schema_validator import SchemaValidator

        schema = SchemaValidator.validate_pack(pack_data, pack_path)
        assert schema.reserved_words == {"self": "propio", "cls": "clase"}
        # Schema-level validation also passes the identifier-validity check
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is True
        assert result["invalid_reserved_words"] == []


class TestMinInterpreterEnforcement:
    """The interpreter-floor guard (CORE-1318).

    A pack whose ``python_version_min`` exceeds the version it is loaded for
    ships identifiers that only parse on the newer interpreter — the Sinhala ZWJ
    conjuncts are valid identifier characters only from CPython 3.13 (Unicode
    13.0 XID). The loader refuses such a load loudly rather than letting a
    ``SyntaxError`` surface in the user's translated code.
    """

    def test_sinhala_below_min_interpreter_is_refused(self):
        # si/3.10.yml declares python_version_min '3.13'; loading it FOR 3.10
        # must be refused with an actionable message.
        loader = LanguagePackLoader()
        with pytest.raises(UnsupportedInterpreterError, match="3.13"):
            loader.load("si", "python", "3.10")

    def test_sinhala_at_min_interpreter_loads(self):
        loader = LanguagePackLoader()
        pack = loader.load("si", "python", "3.13")
        assert pack.language == "si"

    def test_tooling_bypass_loads_incompatible_pack(self):
        # The auditor/exporter path inspects the raw pack without executing it.
        loader = LanguagePackLoader()
        pack = loader.load("si", "python", "3.10", enforce_min_interpreter=False)
        assert pack.language == "si"

    def test_compatible_pack_is_unaffected(self):
        # A pack whose floor is at or below the requested version loads normally.
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")
        assert pack.language == "es"
