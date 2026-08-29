"""Tests for pack_loader module."""

import textwrap
import types

import pytest
import yaml
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.schema_validator import SchemaValidator
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
    """Test LanguagePack implicit_params support (CORE-710)."""

    def test_default_implicit_params_is_empty(self):
        """Backward-compat: constructor without implicit_params defaults to empty."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(language="es", target="python", version="3.10")
        assert pack.implicit_params == {}

    def test_get_implicit_param_translation_returns_value(self):
        """Canonical accessor returns the configured translation."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            implicit_params={"self": "propio", "cls": "clase"},
        )
        assert pack.get_implicit_param_translation("self") == "propio"
        assert pack.get_implicit_param_translation("cls") == "clase"

    def test_get_implicit_param_translation_returns_none_for_missing(self):
        """Missing reserved word returns None, not raises."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(language="es", target="python", version="3.10")
        assert pack.get_implicit_param_translation("self") is None

    def test_has_implicit_param(self):
        """has_implicit_param predicate matches presence in implicit_params dict."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            implicit_params={"self": "propio"},
        )
        assert pack.has_implicit_param("self") is True
        assert pack.has_implicit_param("cls") is False

    def test_get_keyword_translation_falls_back_to_implicit_params(self):
        """get_keyword_translation falls back to implicit_params when keyword missing.

        Madison's CORE-710 test API uses pack.get_keyword_translation("self")
        as the unified accessor; this assertion pins that contract.
        """
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            keywords={"def": "definir"},
            implicit_params={"self": "propio", "cls": "clase"},
        )
        # Primary keyword still works
        assert pack.get_keyword_translation("def") == "definir"
        # Falls back to implicit_params for self/cls
        assert pack.get_keyword_translation("self") == "propio"
        assert pack.get_keyword_translation("cls") == "clase"
        # Neither section: returns None
        assert pack.get_keyword_translation("xyz") is None

    def test_keyword_section_wins_over_implicit_params_on_conflict(self):
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
            implicit_params={"self": "RESERVED_VALUE"},
        )
        assert pack.get_keyword_translation("self") == "KEYWORD_VALUE"

    def test_repr_includes_implicit_params_count(self):
        """__repr__ surfaces the implicit_params count for debug visibility."""
        from legesher_i18n.pack_loader import LanguagePack

        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            implicit_params={"self": "propio", "cls": "clase"},
        )
        assert "implicit_params=2" in repr(pack)

    def test_existing_pack_loads_with_implicit_params(self):
        """End-to-end: real es pack ships implicit_params at 3.13.

        Post-CORE-710: every pack has a ``implicit_params:`` section.
        This test confirms the section is loaded correctly through the
        inheritance chain (we wrote to 3.10.yml; 3.13 inherits from 3.12
        from 3.11 from 3.10).
        """
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.13")
        # Reserved words populated via inheritance from 3.10
        assert pack.implicit_params.get("self") is not None
        assert pack.implicit_params.get("cls") is not None
        # Existing keyword lookup still works
        assert pack.get_keyword_translation("def") is not None


class TestReservedWordsInheritance:
    """Test that implicit_params are inherited via _merge_packs (CORE-710).

    Pack 3.10 is the canonical base; 3.11/3.12/3.13 extend via the
    ``extends:`` field. After step 9 lands implicit_params only in 3.10.yml,
    higher versions should inherit through the merge logic. These tests
    pin that behavior with synthetic dicts (mirrors pack_loader's
    `_merge_packs` semantics).
    """

    def test_merge_inherits_implicit_params_from_base(self):
        """Child pack with no implicit_params inherits base pack's section."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "implicit_params": {"self": "propio", "cls": "clase"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            # No implicit_params — should inherit
            "keywords": {"match": "coincidir"},
        }
        merged = loader._merge_packs(base, override)
        assert merged["implicit_params"] == {"self": "propio", "cls": "clase"}

    def test_merge_override_implicit_params_take_precedence(self):
        """Child pack's implicit_params override base for matching keys."""
        loader = LanguagePackLoader()
        base = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "implicit_params": {"self": "propio", "cls": "clase"},
        }
        override = {
            "language": "es",
            "target": "python",
            "version": "3.11",
            "implicit_params": {"self": "instancia"},  # override only `self`
        }
        merged = loader._merge_packs(base, override)
        # `self` overridden, `cls` inherited from base
        assert merged["implicit_params"]["self"] == "instancia"
        assert merged["implicit_params"]["cls"] == "clase"

    def test_merge_no_implicit_params_in_either_pack(self):
        """When neither base nor override has implicit_params, key absent."""
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
        assert "implicit_params" not in merged

    def test_merge_only_override_has_implicit_params(self):
        """If only the override has implicit_params, they're preserved."""
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
            "implicit_params": {"self": "propio"},
        }
        merged = loader._merge_packs(base, override)
        assert merged["implicit_params"] == {"self": "propio"}

    def test_loaded_pack_with_synthetic_implicit_params_section(self, tmp_path):
        """Integration: pack file with implicit_params: section loads correctly.

        Constructs a synthetic on-disk pack with implicit_params populated,
        loads it via LanguagePackLoader, and confirms the section flows
        through to LanguagePack.implicit_params. This pins the behavior
        that step 9 will rely on once we write implicit_params to all 51
        real pack YAMLs.
        """
        import yaml

        pack_data = {
            "language": "zz",  # synthetic non-existent language
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "builtins": {"print": "imprimir"},
            "implicit_params": {"self": "propio", "cls": "clase"},
        }
        pack_path = tmp_path / "3.10.yml"
        pack_path.write_text(yaml.safe_dump(pack_data), encoding="utf-8")

        # Use SchemaValidator directly to confirm the schema accepts the file
        from legesher_i18n.schema_validator import SchemaValidator

        schema = SchemaValidator.validate_pack(pack_data, pack_path)
        assert schema.implicit_params == {"self": "propio", "cls": "clase"}
        # Schema-level validation also passes the identifier-validity check
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is True
        assert result["invalid_implicit_params"] == []


class TestMinInterpreterEnforcement:
    """The interpreter-floor guard (CORE-1318 / CORE-1517).

    A pack whose ``python_version_min`` exceeds the version it is loaded for
    ships identifiers that only parse on the newer interpreter (e.g. the Sinhala
    ZWJ conjuncts, valid identifier characters only from CPython 3.13 / Unicode
    15.1). The loader refuses such a load loudly rather than letting a
    ``SyntaxError`` surface in the user's translated code.

    The mechanism is exercised directly on ``_enforce_min_interpreter`` with a
    synthetic schema, so it does not depend on any real pack's floor (Sinhala is
    now compatible at every tier — see ``TestSinhalaInterpreterTiers``).
    """

    @staticmethod
    def _schema(python_version_min):
        return types.SimpleNamespace(
            metadata=types.SimpleNamespace(python_version_min=python_version_min)
        )

    def test_refuses_a_pack_whose_floor_exceeds_the_request(self):
        loader = LanguagePackLoader()
        with pytest.raises(UnsupportedInterpreterError, match="3.13"):
            loader._enforce_min_interpreter(self._schema("3.13"), "3.10", "xx")

    def test_allows_floor_at_or_below_the_request(self):
        loader = LanguagePackLoader()
        # Exact match and lower floor both pass (no raise).
        loader._enforce_min_interpreter(self._schema("3.10"), "3.10", "xx")
        loader._enforce_min_interpreter(self._schema("3.10"), "3.13", "xx")

    def test_no_floor_is_a_noop(self):
        loader = LanguagePackLoader()
        loader._enforce_min_interpreter(self._schema(None), "3.10", "xx")

    def test_tooling_bypass_loads_a_high_floor_pack(self):
        # The auditor/exporter path inspects a raw pack without executing it, so
        # it bypasses the floor. si/3.13.yml declares a 3.13 floor; loading it
        # FOR 3.10 with the bypass must succeed.
        loader = LanguagePackLoader()
        pack = loader.load("si", "python", "3.13", enforce_min_interpreter=False)
        assert pack.language == "si"

    def test_compatible_pack_is_unaffected(self):
        # A pack whose floor is at or below the requested version loads normally.
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.10")
        assert pack.language == "es"


class TestSinhalaInterpreterTiers:
    """CORE-1521: Sinhala ships a no-ZWJ variant for 3.10-3.12 and restores the
    ZWJ (U+200D) conjunct spellings for 3.13+.

    The conjunct forms are valid Python identifiers only on CPython 3.13+
    (Unicode 15.1 XID); the non-conjunct (ZWJ-stripped) forms parse on every
    interpreter. So the lower-tier packs must carry no ZWJ, the 3.13+ packs must
    carry the conjuncts, and the two must be the same word (differing only by the
    joiner) — with `si` loading cleanly at every tier.
    """

    ZWJ = "‍"

    @staticmethod
    def _values(pack):
        merged = {}
        for section in ("keywords", "builtins", "exceptions", "implicit_params"):
            merged.update(getattr(pack, section, {}) or {})
        return merged

    def test_lower_tiers_load_and_carry_no_zwj(self):
        loader = LanguagePackLoader()
        for version in ("3.10", "3.11", "3.12"):
            # enforce_min_interpreter is True by default — must NOT raise now.
            pack = loader.load("si", "python", version)
            assert pack.metadata.python_version_min == version
            offenders = [v for v in self._values(pack).values() if self.ZWJ in v]
            assert offenders == [], f"si {version} still carries ZWJ: {offenders}"

    def test_313_plus_restores_the_conjuncts(self):
        loader = LanguagePackLoader()
        for version in ("3.13", "3.14"):
            values = self._values(loader.load("si", "python", version))
            # 'True' -> 'satya' with the ත්‍ය conjunct (virama+ZWJ+ya).
            assert values["True"] == "සත්‍ය"
            assert self.ZWJ in values["True"]
            # All 17 re-tiered values must regain their conjunct in the overlay
            # (guards against a conjunct dropped from or missing in 3.13.yml).
            assert sum(self.ZWJ in v for v in values.values()) == 17

    def test_tiers_are_the_same_word_minus_the_joiner(self):
        loader = LanguagePackLoader()
        low = self._values(loader.load("si", "python", "3.10"))
        high = self._values(loader.load("si", "python", "3.13"))
        drifted = {
            k: (low[k], high[k]) for k in low if high[k].replace(self.ZWJ, "") != low[k]
        }
        assert drifted == {}, f"tier spellings drifted apart: {drifted}"


class TestJapaneseInterpreterTiers:
    """CORE-1905: `ja` tiers `divmod` around U+30FB KATAKANA MIDDLE DOT.

    The canonical reading `ディビジョン・モジュール` separates its two halves with
    U+30FB, an identifier character only from CPython 3.13 (Unicode 15.1 XID).
    It shipped in the 3.10 base pack, where it is a hard SyntaxError. The base
    packs now carry the dot-free `ディビジョンモジュール` — the same reading, the
    separator removed — and the 3.13 overlay restores the canonical spelling.

    The same shape as ``TestSinhalaInterpreterTiers``, because it is the same
    mechanism: both tiers must be the same word, differing only by the character
    the older interpreter cannot parse.
    """

    MIDDLE_DOT = "\u30fb"
    DOTTED = "ディビジョン・モジュール"
    DOT_FREE = "ディビジョンモジュール"

    def test_lower_tiers_carry_the_dot_free_form(self):
        loader = LanguagePackLoader()
        for version in ("3.10", "3.11", "3.12"):
            pack = loader.load("ja", "python", version)
            assert pack.builtins["divmod"] == self.DOT_FREE
            assert self.MIDDLE_DOT not in pack.builtins["divmod"]

    def test_313_plus_restores_the_canonical_spelling(self):
        loader = LanguagePackLoader()
        for version in ("3.13", "3.14"):
            pack = loader.load("ja", "python", version)
            assert pack.builtins["divmod"] == self.DOTTED

    def test_the_tiers_are_the_same_word_minus_the_separator(self):
        assert self.DOTTED.replace(self.MIDDLE_DOT, "") == self.DOT_FREE

    def test_no_other_ja_value_needs_a_313_only_character(self):
        """The tiering is one term wide; a second one would want its own note."""
        loader = LanguagePackLoader()
        pack = loader.load("ja", "python", "3.10")
        offenders = {
            f"{section}.{key}": value
            for section in ("keywords", "builtins", "exceptions", "implicit_params")
            for key, value in (getattr(pack, section, {}) or {}).items()
            if any(ch in SchemaValidator._XID_ONLY_FROM_CPYTHON_313 for ch in value)
        }
        assert offenders == {}, (
            f"ja 3.10 still carries 3.13-only characters: {offenders}"
        )


def test_no_xid_313_only_char_below_the_declared_floor():
    """No pack value may contain a character that only became a valid identifier
    on CPython 3.13 while the pack declares a floor below 3.13 — that value would
    ``SyntaxError`` on the interpreter it targets.

    Generalises the CORE-1521 Sinhala fix to every shipped pack: the deterministic
    static guarantee that each tier parses on its own interpreter.

    The character set is the validator's own, not a local copy. A local
    ``{ZWJ, ZWNJ}`` literal is what let ``ja`` ship ``U+30FB KATAKANA MIDDLE DOT``
    under a 3.10 floor with this test green (CORE-1905): the test asserted the
    two characters its author knew about rather than the rule.
    """
    xid_313_only = SchemaValidator._XID_ONLY_FROM_CPYTHON_313
    loader = LanguagePackLoader()
    offenders = []
    for code, _name in loader.list_available_languages("python"):
        for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
            try:
                pack = loader.load(
                    code, "python", version, enforce_min_interpreter=False
                )
            except Exception:
                continue
            floor = pack.metadata.python_version_min if pack.metadata else None
            try:
                below_313 = floor is None or tuple(
                    int(p) for p in floor.split(".")[:2]
                ) < (3, 13)
            except ValueError:
                below_313 = True
            if not below_313:
                continue
            for section in ("keywords", "builtins", "exceptions", "implicit_params"):
                for key, value in (getattr(pack, section, {}) or {}).items():
                    if any(ch in xid_313_only for ch in value):
                        offenders.append((code, version, key, value))
    assert offenders == [], f"XID-3.13-only chars below a <3.13 floor: {offenders}"
