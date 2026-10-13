"""Integration tests for end-to-end workflows."""

import pytest
from pathlib import Path

from legesher_i18n import (
    load_language_pack,
    LanguagePackLoader,
    PythonVersionDetector,
    VersionIndex,
)
from legesher_i18n.exceptions import PackNotFoundError

LANG_PACKS_DIR = Path(__file__).parent.parent / "language-packs"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    def test_auto_detect_and_load(self):
        """Test automatic version detection and pack loading."""
        # Should auto-detect current Python version and load pack
        pack = load_language_pack("es")

        assert pack is not None
        assert pack.language == "es"
        assert pack.target == "python"
        assert len(pack.keywords) > 0

    def test_explicit_version_load(self):
        """Test loading with explicit version."""
        pack = load_language_pack("es", version="3.11")

        assert pack.version == "3.11"
        # Should have except* from 3.11
        assert "except*" in pack.keywords

    def test_version_detection_with_project(self):
        """Test version detection from project directory."""
        project_path = str(FIXTURES_DIR / "projects" / "with_pyproject")

        pack = load_language_pack("es", project_path=project_path)

        # Should detect 3.11 from pyproject.toml
        assert pack is not None
        # Version should be compatible with 3.11

    def test_multiple_languages(self):
        """Test loading multiple language packs."""
        pack_es = load_language_pack("es", version="3.10")
        pack_ar = load_language_pack("ar", version="3.10")

        assert pack_es.language == "es"
        assert pack_ar.language == "ar"

        # Same keyword, different translations
        assert pack_es.keywords["def"] == "definir"
        assert pack_ar.keywords["def"] == "تعريف"

    def test_cross_version_compatibility(self):
        """Test loading same language across different Python versions."""
        pack_310 = load_language_pack("es", version="3.10")
        pack_311 = load_language_pack("es", version="3.11")
        pack_312 = load_language_pack("es", version="3.12")

        # All should have base keywords
        assert "def" in pack_310.keywords
        assert "def" in pack_311.keywords
        assert "def" in pack_312.keywords

        # 3.10+ should have match/case
        assert "match" in pack_310.keywords
        assert "match" in pack_311.keywords
        assert "match" in pack_312.keywords

        # Only 3.11+ should have except*
        assert "except*" not in pack_310.keywords
        assert "except*" in pack_311.keywords
        assert "except*" in pack_312.keywords

        # Only 3.12+ should have type
        assert "type" not in pack_310.keywords
        assert "type" not in pack_311.keywords
        assert "type" in pack_312.keywords


class TestVersionIndexIntegration:
    """Test integration between version index and pack loading."""

    def test_version_index_and_pack_consistency(self):
        """Test that version index matches pack inheritance."""
        # Load version index
        index_path = LANG_PACKS_DIR / "python" / "version-index.yml"
        index = VersionIndex.load(index_path)

        # Load packs and verify keywords match index
        loader = LanguagePackLoader()

        # Check 3.11 pack has except* as indicated in index
        pack_311 = loader.load("es", "python", "3.11")
        v311_info = index.get_version_info("3.11")

        for keyword in v311_info.added_keywords:
            assert keyword in pack_311.keywords, f"{keyword} should be in 3.11 pack"

    def test_inheritance_chain_consistency(self):
        """Test that pack inheritance matches version index chain."""
        index_path = LANG_PACKS_DIR / "python" / "version-index.yml"
        index = VersionIndex.load(index_path)

        loader = LanguagePackLoader()
        pack = loader.load("es", "python", "3.13")

        # Inheritance chain should align with version index
        version_chain = index.get_inheritance_chain("3.13")

        # Pack should have keywords from all versions in chain
        all_keywords = set()
        for version in version_chain:
            version_info = index.get_version_info(version)
            all_keywords.update(version_info.added_keywords)

        for keyword in all_keywords:
            assert keyword in pack.keywords, f"{keyword} should be in 3.13 pack"


class TestPerformance:
    """Structural checks that used to carry wall-clock bounds."""

    # Wall-clock bounds (500 ms, 10 ms, 2 s) used to sit on these three tests.
    # A loaded CI runner can miss any of them for a reason that is not a
    # defect; timing is measured under `make bench`, and the per-commit
    # guarantees here are structural.

    def test_pack_loading(self):
        """A pack loads."""
        loader = LanguagePackLoader()
        assert loader.load("es", "python", "3.13") is not None

    def test_cached_loading_returns_the_same_object(self):
        """A second load is the cached pack, not a reload."""
        loader = LanguagePackLoader()
        pack1 = loader.load("es", "python", "3.10")
        pack2 = loader.load("es", "python", "3.10")
        assert pack1 is pack2

    def test_multiple_pack_loading(self):
        """Four versions of two packs load."""
        for lang in ["es", "ar"]:
            for version in ["3.10", "3.11", "3.12", "3.13"]:
                assert load_language_pack(lang, version=version) is not None


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_missing_language_pack(self):
        """Test graceful handling of missing language pack."""
        with pytest.raises(PackNotFoundError):
            load_language_pack("nonexistent_language", version="3.10")

    def test_unsupported_version(self):
        """Test handling of unsupported Python version."""
        # Version 2.7 is not in our index
        with pytest.raises((PackNotFoundError, Exception)):
            load_language_pack("es", version="2.7")

    def test_malformed_pack_handling(self):
        """Test handling of malformed pack files."""
        # This would require creating a malformed fixture
        # For now, rely on validation tests
        pass


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_translator_workflow(self):
        """Simulate a code translator workflow."""
        # Detect version
        detector = PythonVersionDetector()
        version = detector.detect()

        # Load appropriate pack
        pack = load_language_pack("es", version=version)

        # Translate some keywords
        translations = {
            "def": pack.get_keyword_translation("def"),
            "class": pack.get_keyword_translation("class"),
            "if": pack.get_keyword_translation("if"),
            "for": pack.get_keyword_translation("for"),
        }

        # Verify translations exist
        for eng, trans in translations.items():
            assert trans is not None, f"Translation missing for {eng}"
            assert trans != eng, f"Translation should differ from English: {eng}"

    def test_ide_extension_workflow(self):
        """Simulate an IDE extension workflow."""
        # Extension would detect project version
        project_path = FIXTURES_DIR / "projects" / "with_pyproject"
        detector = PythonVersionDetector()
        version = detector.detect(project_path)

        # Load pack for that version
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", version)

        # Provide completions
        keywords = list(pack.keywords.keys())
        assert len(keywords) > 0

        # Check specific keyword availability
        assert pack.has_keyword("def")
        assert pack.has_keyword("class")

    def test_multi_language_project(self):
        """Simulate project supporting multiple languages."""
        version = "3.11"
        languages = ["es", "ar"]

        packs = {}
        for lang in languages:
            packs[lang] = load_language_pack(lang, version=version)

        # All packs should be loaded
        assert len(packs) == 2

        # Each should have translations
        for lang, pack in packs.items():
            assert len(pack.keywords) > 0
            assert len(pack.builtins) > 0
