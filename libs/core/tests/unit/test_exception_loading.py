"""Tests for exception translation loading in TokenTranslator."""

import pytest

from legesher_core.transformer import TokenTranslator


class TestExceptionPascalCaseRemapping:
    """Verify exception names are remapped from lowercase to PascalCase."""

    def test_value_error_pascal_case(self):
        """ValueError (not valueerror) should be in the builtin map."""
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("ValueError") is not None
        assert translator.mapper.get_builtin("valueerror") is None

    def test_type_error_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("TypeError") is not None

    def test_index_error_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("IndexError") is not None

    def test_key_error_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("KeyError") is not None

    def test_zero_division_error_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("ZeroDivisionError") is not None

    def test_base_exception_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("BaseException") is not None

    def test_exception_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("Exception") is not None

    def test_runtime_error_pascal_case(self):
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("RuntimeError") is not None


class TestExceptionTranslationValues:
    """Verify exception translations are actual translations, not English."""

    @pytest.mark.parametrize("lang", ["es", "zh", "ur"])
    def test_exceptions_are_translated_not_english(self, lang):
        """Exception translations should differ from English names."""
        translator = TokenTranslator.from_language_pack(lang)
        for exc in ["ValueError", "TypeError", "KeyError"]:
            translation = translator.mapper.get_builtin(exc)
            assert translation is not None
            assert translation != exc, f"{exc} not translated in {lang}"
            assert translation != exc.lower(), f"{exc} just lowercased in {lang}"


class TestExceptionCountInBuiltinMap:
    """Verify builtin map includes exceptions."""

    def test_builtin_count_includes_exceptions(self):
        """Builtin map should have builtins + exceptions (>100 total)."""
        translator = TokenTranslator.from_language_pack("es")
        total = len(translator.mapper.builtin_map)
        assert total > 100, f"Expected >100 builtins+exceptions, got {total}"

    def test_pack_info_reflects_merged_count(self):
        """get_pack_info() should show the merged count."""
        translator = TokenTranslator.from_language_pack("es")
        info = translator.get_pack_info()
        assert info["builtin_count"] > 100


class TestTreeSitterExceptionLoading:
    """Verify TreeSitterTranslator also loads exceptions."""

    def test_tree_sitter_has_exceptions(self):
        """TreeSitterTranslator.from_language_pack should include exceptions."""
        from legesher_core.tree_sitter import TreeSitterTranslator

        translator = TreeSitterTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("ValueError") is not None
        assert translator.mapper.get_builtin("TypeError") is not None

    def test_tree_sitter_matches_token_translator(self):
        """Both translators should have the same exception translations."""
        from legesher_core.tree_sitter import TreeSitterTranslator

        token = TokenTranslator.from_language_pack("es")
        tree = TreeSitterTranslator.from_language_pack("es")

        for exc in ["ValueError", "TypeError", "KeyError", "IndexError"]:
            assert token.mapper.get_builtin(exc) == tree.mapper.get_builtin(exc)


class TestIdentityExceptionValueCanonicalization:
    """Lowercase identity exception VALUES must not reach the output (CORE-1570).

    The en pack ships every exception entry as a lowercase identity mapping
    (``typeerror: typeerror``). ``merge_exception_translations`` PascalCases
    the keys, but a value passed through verbatim maps ``TypeError`` to
    ``typeerror`` and the en-target translator emits broken except clauses.
    The engine canonicalizes identity values so a pack with this quirk cannot
    emit broken code.
    """

    def test_identity_value_is_pascal_cased(self):
        from legesher_core.utils import merge_exception_translations

        merged = merge_exception_translations({}, {"typeerror": "typeerror"})
        assert merged == {"TypeError": "TypeError"}

    def test_real_translation_value_is_untouched(self):
        from legesher_core.utils import merge_exception_translations

        merged = merge_exception_translations({}, {"typeerror": "errordetipo"})
        assert merged == {"TypeError": "errordetipo"}

    def test_unknown_exception_name_passes_through(self):
        """A key that is not a Python builtin exception cannot be canonicalized."""
        from legesher_core.utils import merge_exception_translations

        merged = merge_exception_translations({}, {"notarealerror": "notarealerror"})
        assert merged == {"notarealerror": "notarealerror"}

    def test_en_pack_exception_values_are_pascal_case(self):
        """The identity baseline must map every exception to its canonical name."""
        translator = TokenTranslator.from_language_pack("en")
        for exc in ["TypeError", "ValueError", "KeyError", "ZeroDivisionError"]:
            assert translator.mapper.get_builtin(exc) == exc

    def test_en_target_except_clause_round_trips_unchanged(self):
        """Regression: en-target translate_code round-trips ``except TypeError:``."""
        translator = TokenTranslator.from_language_pack("en")
        code = "try:\n    pass\nexcept TypeError:\n    pass\n"
        out = translator.translate_code(code, source_lang="en", target_lang="en")
        assert out == code
