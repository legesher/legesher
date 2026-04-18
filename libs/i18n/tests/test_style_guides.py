"""Tests for StyleGuideLoader.

Covers loading, hierarchy resolution, deep merging, caching,
fallback behavior, and error handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from legesher_i18n.style_guides import StyleGuideLoader

# Path to the real style-guides directory shipped with the package.
_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def loader() -> StyleGuideLoader:
    """Return a StyleGuideLoader pointed at the real style-guides dir."""
    return StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)


@pytest.fixture
def tmp_style_guides(tmp_path: Path) -> Path:
    """Create a minimal style-guides directory for isolated tests."""
    base = {
        "language": "python",
        "naming": {"snake_case": {"rule": "base rule"}},
        "script": {"native_required": True},
        "translation": {"register": "technical-standard"},
        "formatting": {"comment_prefix": "#"},
    }
    ltr = {
        "language": "_ltr",
        "naming": {"text_direction": "left-to-right"},
        "script": {"bidirectional": {"handling": "none"}},
    }
    rtl = {
        "language": "_rtl",
        "naming": {"text_direction": "right-to-left"},
        "script": {"bidirectional": {"handling": "unicode-bidi-algorithm"}},
    }
    lang_es = {
        "language": "es",
        "translation": {"register": "technical-formal"},
        "naming": {
            "snake_case": {"rule": "Spanish snake_case rule", "examples": ["ejemplo"]}
        },
    }
    for name, data in [
        ("python.yml", base),
        ("_ltr.yml", ltr),
        ("_rtl.yml", rtl),
        ("es.yml", lang_es),
    ]:
        (tmp_path / name).write_text(yaml.dump(data, allow_unicode=True))

    return tmp_path


# ------------------------------------------------------------------
# 1. test_load_base_python
# ------------------------------------------------------------------


class TestLoadBasePython:
    """Loading python.yml should return a dict with the expected top-level keys."""

    def test_returns_dict_with_expected_keys(self, loader: StyleGuideLoader) -> None:
        # The "en" language has no dedicated file and is LTR,
        # so the result is python.yml + _ltr.yml (no language-specific layer).
        guide = loader.load("en")

        assert isinstance(guide, dict)
        for key in ("naming", "script", "translation", "formatting"):
            assert key in guide, f"Expected top-level key '{key}' in guide"

    def test_naming_section_has_snake_case(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("en")
        assert "snake_case" in guide["naming"]

    def test_script_section_has_native_required(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("en")
        assert guide["script"]["native_required"] is True


# ------------------------------------------------------------------
# 2. test_load_ltr_language
# ------------------------------------------------------------------


class TestLoadLTRLanguage:
    """Loading an LTR language (e.g. 'es') merges python.yml -> _ltr.yml -> es.yml."""

    def test_has_ltr_direction(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("es")
        # _ltr.yml adds naming.text_direction
        assert guide["naming"].get("text_direction") == "left-to-right"

    def test_has_base_formatting(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("es")
        assert guide["formatting"]["comment_prefix"] == "#"

    def test_has_language_specific_content(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("es")
        # es.yml overrides translation.register
        assert guide["translation"]["register"] == "technical-formal"


# ------------------------------------------------------------------
# 3. test_load_rtl_language
# ------------------------------------------------------------------


class TestLoadRTLLanguage:
    """Loading an RTL language (e.g. 'ur') merges python.yml -> _rtl.yml -> ur.yml."""

    def test_has_rtl_direction(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("ur")
        assert guide["naming"].get("text_direction") == "right-to-left"

    def test_has_rtl_bidirectional_handling(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("ur")
        assert guide["script"]["bidirectional"]["handling"] == "unicode-bidi-algorithm"

    def test_has_urdu_specific_content(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("ur")
        assert guide["translation"]["register"] == "modern-standard-urdu"

    def test_has_urdu_script_variant(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("ur")
        assert "Nastaliq" in guide["script"]["variant"]


# ------------------------------------------------------------------
# 4. test_hierarchy_merging
# ------------------------------------------------------------------


class TestHierarchyMerging:
    """Language-specific values should override base values."""

    def test_es_register_overrides_python_register(
        self, loader: StyleGuideLoader
    ) -> None:
        base_guide = loader.load("en")  # python.yml + _ltr.yml only
        es_guide = loader.load("es")

        # python.yml has "technical-standard", es.yml overrides to "technical-formal"
        assert (
            base_guide["translation"]["register"] != es_guide["translation"]["register"]
        )
        assert es_guide["translation"]["register"] == "technical-formal"

    def test_ur_register_overrides_python_register(
        self, loader: StyleGuideLoader
    ) -> None:
        ur_guide = loader.load("ur")
        assert ur_guide["translation"]["register"] == "modern-standard-urdu"

    def test_language_field_reflects_language_specific_file(
        self,
        loader: StyleGuideLoader,
    ) -> None:
        guide = loader.load("es")
        assert guide["language"] == "es"


# ------------------------------------------------------------------
# 5. test_deep_merge
# ------------------------------------------------------------------


class TestDeepMerge:
    """Nested dicts are recursively merged, not replaced wholesale."""

    def test_nested_keys_preserved(self, tmp_style_guides: Path) -> None:
        loader = StyleGuideLoader(style_guides_dir=tmp_style_guides)
        guide = loader.load("es")

        # base has naming.snake_case.rule, es overrides it and adds examples.
        # The base key "naming.script" from python.yml should still be present
        # alongside the overridden naming.snake_case.
        assert "snake_case" in guide["naming"]
        assert guide["naming"]["snake_case"]["rule"] == "Spanish snake_case rule"
        assert "examples" in guide["naming"]["snake_case"]

    def test_base_keys_not_lost(self, tmp_style_guides: Path) -> None:
        loader = StyleGuideLoader(style_guides_dir=tmp_style_guides)
        guide = loader.load("es")

        # "script" section from python.yml should survive the merge
        assert "native_required" in guide["script"]
        assert guide["script"]["native_required"] is True

    def test_sibling_keys_preserved_after_override(
        self,
        tmp_style_guides: Path,
    ) -> None:
        loader = StyleGuideLoader(style_guides_dir=tmp_style_guides)
        guide = loader.load("es")

        # formatting comes from python.yml, not overridden by es.yml
        assert guide["formatting"]["comment_prefix"] == "#"

    def test_deep_merge_method_directly(self) -> None:
        loader = StyleGuideLoader()
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 99, "z": 100}, "c": 4}

        result = loader._deep_merge(base, override)

        assert result == {"a": {"x": 1, "y": 99, "z": 100}, "b": 3, "c": 4}
        # Originals should be unmodified
        assert base == {"a": {"x": 1, "y": 2}, "b": 3}
        assert override == {"a": {"y": 99, "z": 100}, "c": 4}


# ------------------------------------------------------------------
# 6. test_cache_behavior
# ------------------------------------------------------------------


class TestCacheBehavior:
    """Loading the same language twice returns the same object (LRU cache)."""

    def test_same_object_returned(self, loader: StyleGuideLoader) -> None:
        first = loader.load("es")
        second = loader.load("es")
        assert first is second

    def test_different_languages_are_different_objects(
        self,
        loader: StyleGuideLoader,
    ) -> None:
        es = loader.load("es")
        ur = loader.load("ur")
        assert es is not ur

    def test_cache_dict_populated(self, loader: StyleGuideLoader) -> None:
        loader.load("es")
        loader.load("es")
        assert "es" in loader._cache


# ------------------------------------------------------------------
# 7. test_missing_language_fallback
# ------------------------------------------------------------------


class TestMissingLanguageFallback:
    """A language without a specific guide (e.g. 'fi') returns base + direction only."""

    def test_returns_base_plus_ltr(self, loader: StyleGuideLoader) -> None:
        # Finnish has no fi.yml but is LTR
        guide = loader.load("fi")

        assert isinstance(guide, dict)
        assert "naming" in guide
        assert "script" in guide

    def test_ltr_direction_applied(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("fi")
        assert guide["naming"].get("text_direction") == "left-to-right"

    def test_no_language_specific_override(self, loader: StyleGuideLoader) -> None:
        guide = loader.load("fi")
        # Should still have the base register, not a language-specific one
        assert guide["translation"]["register"] != "technical-formal"


# ------------------------------------------------------------------
# 8. test_get_supported_languages
# ------------------------------------------------------------------


class TestGetSupportedLanguages:
    """get_supported_languages returns codes for dedicated style guide files."""

    def test_returns_list(self, loader: StyleGuideLoader) -> None:
        result = loader.get_supported_languages()
        assert isinstance(result, list)

    def test_includes_known_languages(self, loader: StyleGuideLoader) -> None:
        result = loader.get_supported_languages()
        for lang in ("es", "ur", "zh"):
            assert lang in result, f"Expected '{lang}' in supported languages"

    def test_excludes_base_and_direction_files(self, loader: StyleGuideLoader) -> None:
        result = loader.get_supported_languages()
        for excluded in ("python", "_ltr", "_rtl"):
            assert excluded not in result, (
                f"'{excluded}' should not be in supported languages"
            )

    def test_is_sorted(self, loader: StyleGuideLoader) -> None:
        result = loader.get_supported_languages()
        assert result == sorted(result)

    def test_nonexistent_directory_returns_empty(self, tmp_path: Path) -> None:
        loader = StyleGuideLoader(style_guides_dir=tmp_path / "nonexistent")
        result = loader.get_supported_languages()
        assert result == []


# ------------------------------------------------------------------
# 9. test_missing_python_yml_raises
# ------------------------------------------------------------------


class TestMissingPythonYmlRaises:
    """If python.yml does not exist, a FileNotFoundError is raised."""

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        # Empty directory -- no python.yml
        loader = StyleGuideLoader(style_guides_dir=tmp_path)

        with pytest.raises(FileNotFoundError, match="python.yml"):
            loader.load("es")

    def test_error_message_mentions_required(self, tmp_path: Path) -> None:
        loader = StyleGuideLoader(style_guides_dir=tmp_path)

        with pytest.raises(FileNotFoundError, match="required"):
            loader.load("en")


# ------------------------------------------------------------------
# 10. test_language_code_validation
# ------------------------------------------------------------------


class TestLanguageCodeValidation:
    """Language code must be 2-3 lowercase ASCII letters."""

    def test_valid_two_letter_code(self, loader: StyleGuideLoader) -> None:
        """Two-letter codes should work."""
        guide = loader.load("es")
        assert isinstance(guide, dict)

    def test_valid_three_letter_code(self, loader: StyleGuideLoader) -> None:
        """Three-letter codes should work (even if no file exists)."""
        # Should not raise ValueError, just return base+direction
        guide = loader.load("eng")
        assert isinstance(guide, dict)

    def test_rejects_path_traversal(self, loader: StyleGuideLoader) -> None:
        """Path traversal attempts should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid language code"):
            loader.load("../../etc")

    def test_rejects_uppercase(self, loader: StyleGuideLoader) -> None:
        """Uppercase codes should be rejected."""
        with pytest.raises(ValueError, match="Invalid language code"):
            loader.load("ES")

    def test_rejects_numbers(self, loader: StyleGuideLoader) -> None:
        """Numeric codes should be rejected."""
        with pytest.raises(ValueError, match="Invalid language code"):
            loader.load("12")

    def test_rejects_empty(self, loader: StyleGuideLoader) -> None:
        """Empty string should be rejected."""
        with pytest.raises(ValueError, match="Invalid language code"):
            loader.load("")

    def test_rejects_long_code(self, loader: StyleGuideLoader) -> None:
        """Codes longer than 3 chars should be rejected."""
        with pytest.raises(ValueError, match="Invalid language code"):
            loader.load("english")


class TestLoadErrorPaths:
    """CORE-1112: coverage for error-handling branches in StyleGuideLoader.

    The merge loop in ``load()`` is defensive: missing files are skipped
    with a warning, non-dict YAML payloads are skipped with a warning,
    and YAML/OS errors are logged and moved past so one broken file
    doesn't tank the whole hierarchy.
    """

    def test_missing_hierarchy_file_is_skipped(self, tmp_path, caplog):
        """A style_guides_dir with only python.yml (no _ltr.yml and no
        language-specific file) should log "file not found" and still
        return a merged dict for the files that do exist."""
        import logging

        (tmp_path / "python.yml").write_text(
            "formatting:\n  comment_prefix: '#'\n", encoding="utf-8"
        )
        from legesher_i18n.style_guides import StyleGuideLoader

        loader = StyleGuideLoader(style_guides_dir=tmp_path)
        with caplog.at_level(logging.WARNING):
            result = loader.load("xx")  # xx isn't a real language
        assert result == {"formatting": {"comment_prefix": "#"}}
        assert any("not found" in rec.message for rec in caplog.records)

    def test_non_dict_yaml_payload_is_skipped(self, tmp_path, caplog):
        """Style guide files that don't parse to a dict should be skipped
        with a warning, not silently merged as garbage."""
        import logging

        (tmp_path / "python.yml").write_text(
            "- this\n- is\n- a\n- list\n", encoding="utf-8"
        )
        from legesher_i18n.style_guides import StyleGuideLoader

        loader = StyleGuideLoader(style_guides_dir=tmp_path)
        with caplog.at_level(logging.WARNING):
            result = loader.load("en")
        assert result == {}
        assert any("did not parse as a dict" in rec.message for rec in caplog.records)

    def test_malformed_yaml_is_logged_and_skipped(self, tmp_path, caplog):
        """A YAML parse error on one file should log an error and continue
        loading the rest of the hierarchy."""
        import logging

        (tmp_path / "python.yml").write_text(
            "formatting:\n  comment_prefix: '#'\n", encoding="utf-8"
        )
        (tmp_path / "en.yml").write_text(":\n:invalid:\n", encoding="utf-8")
        from legesher_i18n.style_guides import StyleGuideLoader

        loader = StyleGuideLoader(style_guides_dir=tmp_path)
        with caplog.at_level(logging.ERROR):
            result = loader.load("en")
        assert result == {"formatting": {"comment_prefix": "#"}}
        assert any("Error parsing" in rec.message for rec in caplog.records)

    def test_load_rtl_set_handles_missing_languages_json(
        self, tmp_path, monkeypatch, caplog
    ):
        """If languages.json can't be loaded, the RTL set falls back to
        empty and every language is treated as LTR."""
        import logging

        from legesher_i18n import style_guides as style_guides_module

        monkeypatch.setattr(
            style_guides_module, "_LANGUAGES_JSON", tmp_path / "does-not-exist.json"
        )

        loader = style_guides_module.StyleGuideLoader(style_guides_dir=tmp_path)
        with caplog.at_level(logging.ERROR):
            rtl_set = loader._load_rtl_set()
        assert rtl_set == set()
        assert any(
            "Failed to load languages.json" in rec.message for rec in caplog.records
        )
