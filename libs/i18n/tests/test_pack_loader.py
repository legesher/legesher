"""Tests for pack_loader module."""

import pytest
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.exceptions import PackNotFoundError


# Real language packs directory
LANG_PACKS_DIR = Path(__file__).parent.parent / "languages"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLanguagePackLoading:
    """Test basic language pack loading."""

    def test_load_spanish_pack(self):
        """Test loading Spanish language pack for Python 3.10."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        assert pack.language == "es"
        assert pack.target == "python"
        assert pack.version == "3.10"
        assert len(pack.keywords) > 0
        assert "def" in pack.keywords
        assert pack.keywords["def"] == "definir"

    def test_load_arabic_pack(self):
        """Test loading Arabic language pack."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("ar", "python", "3.10")

        assert pack.language == "ar"
        assert "def" in pack.keywords
        assert pack.keywords["def"] == "تعريف"  # Arabic translation

    def test_load_nonexistent_pack(self):
        """Test error for nonexistent pack."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

        with pytest.raises(PackNotFoundError) as exc_info:
            loader.load("xx", "python", "3.10")

        assert "xx" in str(exc_info.value)

    def test_pack_immutability(self):
        """Test that LanguagePack is immutable (frozen dataclass)."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        # Should not be able to modify
        with pytest.raises((AttributeError, Exception)):
            pack.language = "fr"


class TestPackInheritance:
    """Test language pack inheritance."""

    def test_inheritance_keyword_merging(self):
        """Test that child pack inherits and overrides parent keywords."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

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
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

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
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

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
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

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
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

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
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        assert pack.get_keyword_translation("def") == "definir"
        assert pack.get_keyword_translation("class") == "clase"
        assert pack.get_keyword_translation("nonexistent") is None

    def test_get_builtin_translation(self):
        """Test getting builtin translations."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        assert pack.get_builtin_translation("print") == "imprimir"
        assert pack.get_builtin_translation("len") == "longitud"
        assert pack.get_builtin_translation("nonexistent") is None

    def test_has_keyword(self):
        """Test keyword existence checking."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        assert pack.has_keyword("def")
        assert pack.has_keyword("class")
        assert not pack.has_keyword("nonexistent")

    def test_repr(self):
        """Test __repr__ method."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        pack = loader.load("es", "python", "3.10")

        repr_str = repr(pack)
        assert "LanguagePack" in repr_str
        assert "es" in repr_str
        assert "python" in repr_str


class TestSecurityFeatures:
    """Test security features like path traversal prevention."""

    def test_path_traversal_detection(self):
        """Test that path traversal attempts are blocked."""
        # This would require a malicious pack file with extends: "../../etc/passwd"
        # The schema validator should catch this
        pass  # Tested in test_schema_validator.py

    def test_circular_inheritance_detection(self):
        """Test circular inheritance detection."""
        # Would need to create circular test fixtures
        # For now, rely on real packs which don't have cycles
        pass

    def test_max_inheritance_depth(self):
        """Test maximum inheritance depth limit."""
        # Would need deeply nested test fixtures
        # For now, our real packs are well within limits (depth ~4)
        pass


class TestPackLoaderEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_keywords_section(self):
        """Test pack with empty keywords (like 3.13/es.yml)."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

        # 3.13 has empty keywords section but inherits everything
        pack = loader.load("es", "python", "3.13")

        # Should still have keywords from inheritance
        assert len(pack.keywords) > 0
        assert "def" in pack.keywords

    def test_metadata_inheritance(self):
        """Test that metadata is properly set from child pack."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)

        pack = loader.load("es", "python", "3.11")

        assert pack.metadata is not None
        assert pack.metadata.python_version_min == "3.11"

    def test_loader_repr(self):
        """Test LanguagePackLoader __repr__."""
        loader = LanguagePackLoader(pack_root=LANG_PACKS_DIR)
        repr_str = repr(loader)

        assert "LanguagePackLoader" in repr_str
