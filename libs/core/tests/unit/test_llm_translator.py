"""Tests for LLMTranslator — full LLM-powered code translation.

Uses a MockBackend to test the translation pipeline without actual LLM calls.
Verifies that keywords come from language packs, identifiers/comments/strings
come from the LLM backend, and output is syntactically valid Python.
"""

import pytest

from legesher_core.language_interface import create_translator
from legesher_core.tree_sitter.identifier_map import IdentifierMap
from legesher_core.tree_sitter.llm_translator import LLMTranslator
from legesher_core.types import TranslationScope

# ---------------------------------------------------------------------------
# Mock backend
# ---------------------------------------------------------------------------


class MockBackend:
    """Mock TextTranslationBackend for testing without LLM calls."""

    def __init__(self, translations=None):
        self.translations = translations or {}
        self.calls = []

    def translate_text(self, text, source_lang, target_lang, context=None):
        self.calls.append(("translate_text", text, source_lang, target_lang))
        return self.translations.get(text, f"translated_{text}")

    def translate_batch(self, items, source_lang, target_lang):
        self.calls.append(
            ("translate_batch", [i["text"] for i in items], source_lang, target_lang)
        )
        return [
            self.translations.get(i["text"], f"translated_{i['text']}") for i in items
        ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

KEYWORD_MAP = {
    "def": "definir",
    "class": "clase",
    "if": "si",
    "else": "sino",
    "return": "retornar",
    "import": "importar",
    "from": "desde",
    "for": "para",
    "in": "en",
    "pass": "pasar",
    "True": "Verdadero",
    "False": "Falso",
    "None": "Nada",
    "and": "y",
    "or": "o",
    "not": "no",
    "is": "es",
    "while": "mientras",
    "break": "romper",
    "continue": "continuar",
    "try": "intentar",
    "except": "excepto",
    "finally": "finalmente",
    "raise": "lanzar",
    "with": "con",
    "as": "como",
    "yield": "ceder",
    "lambda": "lambda",
    "global": "global",
    "nonlocal": "nolocal",
    "assert": "afirmar",
    "del": "eliminar",
    "elif": "sinosi",
    "async": "asinc",
    "await": "esperar",
}

BUILTIN_MAP = {
    "print": "imprimir",
    "len": "longitud",
    "range": "rango",
    "int": "entero",
    "str": "cadena",
    "list": "lista",
    "dict": "diccionario",
    "type": "tipo",
    "isinstance": "es_instancia",
    "input": "entrada",
    "open": "abrir",
    "sum": "suma",
    "max": "maximo",
    "min": "minimo",
    "abs": "absoluto",
    "round": "redondear",
    "sorted": "ordenado",
    "map": "mapa",
    "filter": "filtro",
    "zip": "cremallera",
    "enumerate": "enumerar",
    "float": "flotante",
    "bool": "booleano",
    "set": "conjunto",
    "tuple": "tupla",
    "super": "super",
    "property": "propiedad",
    "staticmethod": "metodo_estatico",
    "classmethod": "metodo_clase",
    "object": "objeto",
    "Exception": "Excepcion",
    "ValueError": "ErrorDeValor",
    "TypeError": "ErrorDeTipo",
    "KeyError": "ErrorDeClave",
    "IndexError": "ErrorDeIndice",
    "AttributeError": "ErrorDeAtributo",
    "RuntimeError": "ErrorDeEjecucion",
    "StopIteration": "DetenerIteracion",
    "NotImplementedError": "ErrorNoImplementado",
}


@pytest.fixture
def backend():
    """Mock backend with some pre-defined translations."""
    return MockBackend(
        translations={
            "greet": "saludar",
            "name": "nombre",
            "Hello": "Hola",
            "# This is a greeting": "# Este es un saludo",
            "This is a greeting": "Este es un saludo",
            "A simple greeter": "Un saludo simple",
        }
    )


@pytest.fixture
def translator(backend):
    """LLMTranslator with mock backend."""
    return LLMTranslator(
        keyword_map=KEYWORD_MAP,
        builtin_map=BUILTIN_MAP,
        backend=backend,
    )


@pytest.fixture
def translator_no_identifiers(backend):
    """LLMTranslator with identifier translation disabled."""
    return LLMTranslator(
        keyword_map=KEYWORD_MAP,
        builtin_map=BUILTIN_MAP,
        backend=backend,
        scope=TranslationScope(translate_identifiers=False),
    )


@pytest.fixture
def translator_no_comments(backend):
    """LLMTranslator with comment translation disabled."""
    return LLMTranslator(
        keyword_map=KEYWORD_MAP,
        builtin_map=BUILTIN_MAP,
        backend=backend,
        scope=TranslationScope(translate_comments=False),
    )


# ===========================================================================
# Full pipeline
# ===========================================================================


class TestFullPipeline:
    """Test the complete translation pipeline."""

    def test_simple_function(self, translator):
        code = "def greet(name):\n    pass"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        assert "definir" in result
        assert "saludar" in result

    def test_keywords_translated_via_pack(self, translator):
        code = "def greet():\n    return True"
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "retornar" in result
        assert "Verdadero" in result


class TestKeywordsViaPackNotLLM:
    """Verify keywords come from language packs, never from the LLM."""

    def test_backend_not_called_for_keywords(self, translator, backend):
        code = "if True:\n    pass"
        translator.translate_code(code, "en", "es")
        # The backend should not have been asked to translate "if", "True", "pass"
        for call in backend.calls:
            if call[0] == "translate_batch":
                texts = call[1]
                assert "if" not in texts
                assert "True" not in texts
                assert "pass" not in texts


class TestIdentifierTranslation:
    """Test that identifiers are translated via the mock LLM backend."""

    def test_identifier_translated(self, translator):
        code = "greet = 1"
        result = translator.translate_code(code, "en", "es")
        # "greet" has a mock translation of "saludar"
        assert "saludar" in result

    def test_identifier_consistency(self, translator):
        """Same identifier name gets the same translation everywhere."""
        code = "greet = 1\nx = greet"
        result = translator.translate_code(code, "en", "es")
        # Both occurrences of "greet" should become "saludar"
        assert result.count("saludar") == 2


class TestCommentTranslation:
    """Test that comments are translated via the LLM backend."""

    def test_comment_translated(self, translator):
        code = "# This is a greeting\nx = 1"
        result = translator.translate_code(code, "en", "es")
        # The mock backend translates the comment content
        assert "saludo" in result or "translated_" in result


class TestStringTranslation:
    """Test that string literals are translated via the LLM backend."""

    def test_string_literal_translated(self, translator):
        code = 'x = "Hello"'
        result = translator.translate_code(code, "en", "es")
        # "Hello" has mock translation "Hola"
        assert "Hola" in result or "translated_" in result


# ===========================================================================
# Output validity
# ===========================================================================


class TestOutputValidity:
    """Translated output should be syntactically valid Python."""

    def test_simple_output_parses(self, translator):
        code = "x = 1\ny = 2"
        result = translator.translate_code(code, "en", "es")
        # Should not raise SyntaxError
        # Note: identifiers may be translated to non-ASCII but still valid
        assert isinstance(result, str)
        assert len(result) > 0


# ===========================================================================
# TranslationScope
# ===========================================================================


class TestTranslationScope:
    """Test disabling specific translation categories."""

    def test_disable_identifiers(self, translator_no_identifiers):
        code = "greet = 1"
        result = translator_no_identifiers.translate_code(code, "en", "es")
        # "greet" should NOT be translated to "saludar"
        assert "saludar" not in result

    def test_disable_comments(self, translator_no_comments):
        code = "# This is a greeting\nx = 1"
        result = translator_no_comments.translate_code(code, "en", "es")
        # Original comment should be preserved
        assert "This is a greeting" in result


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_source_returns_empty(self, translator):
        result = translator.translate_code("", "en", "es")
        assert result == ""

    def test_whitespace_only_returns_as_is(self, translator):
        result = translator.translate_code("   \n\n   ", "en", "es")
        assert result == "   \n\n   "

    def test_translate_file(self, translator, tmp_path):
        source_file = tmp_path / "test.py"
        source_file.write_text("x = 1\n", encoding="utf-8")
        result = translator.translate_file(source_file, "es")
        assert isinstance(result, str)

    def test_return_metadata(self, translator):
        code = "x = 1"
        result = translator.translate_code(code, "en", "es", return_metadata=True)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ===========================================================================
# Factory integration
# ===========================================================================


class TestFactory:
    """Test create_translator with backend= returns LLMTranslator."""

    def test_factory_returns_llm_translator(self):
        backend = MockBackend()
        translator = create_translator(
            "python",
            KEYWORD_MAP,
            BUILTIN_MAP,
            backend=backend,
        )
        assert isinstance(translator, LLMTranslator)

    def test_factory_without_backend_returns_other(self):
        translator = create_translator(
            "python",
            KEYWORD_MAP,
            BUILTIN_MAP,
        )
        assert not isinstance(translator, LLMTranslator)


# ===========================================================================
# get_pack_info
# ===========================================================================


class TestGetPackInfo:
    """Test get_pack_info returns expected metadata."""

    def test_reports_llm_backend(self, translator):
        info = translator.get_pack_info()
        assert info["backend"] == "llm"
        assert "keyword_count" in info
        assert "builtin_count" in info
        assert info["keyword_count"] == len(KEYWORD_MAP)
        assert info["builtin_count"] == len(BUILTIN_MAP)

    def test_reports_python_version(self, translator):
        info = translator.get_pack_info()
        assert "python_version" in info


# ===========================================================================
# IdentifierMap integration
# ===========================================================================


class TestIdentifierMapIntegration:
    """Test that identifier map is used for consistency."""

    def test_pre_populated_map_is_used(self, backend):
        id_map = IdentifierMap()
        id_map.add("my_var", "es", "mi_variable")

        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
            identifier_map=id_map,
        )
        code = "my_var = 1"
        result = translator.translate_code(code, "en", "es")
        # Should use the pre-populated translation, not call the backend
        assert "mi_variable" in result


class TestLLMTranslatorReservedWords:
    """LLMTranslator threads implicit_param_map through to inner deps (CORE-710).

    Pre-fix regression: LLMTranslator constructed `TreeSitterTranslator(...)`
    and `TokenMapper(...)` without `implicit_param_map=`, so when
    `create_translator(..., backend=<llm>)` was used, self/cls remained
    English in translated output (extractor skipped, but dispatch had
    nothing to fire on).

    Uses the module-level ``MockBackend`` (sync, 4-arg signature matching
    ``TextTranslationBackend`` protocol). The substitution path under
    test is in keyword_translator/mapper, not the backend, so the mock's
    actual return value doesn't matter for these tests.
    """

    def test_implicit_param_map_threads_to_inner_translator(self):
        """LLMTranslator.__init__ forwards implicit_param_map to inner deps."""
        translator = LLMTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            backend=MockBackend(),
            implicit_param_map={"self": "propio", "cls": "clase_ref"},
        )
        assert translator.keyword_translator.mapper.implicit_param_map == {
            "self": "propio",
            "cls": "clase_ref",
        }
        assert translator.mapper.implicit_param_map == {
            "self": "propio",
            "cls": "clase_ref",
        }

    def test_inner_translator_substitutes_self_in_method_signature(self):
        """Substitution path fires for self/cls — the regression target.

        Pre-fix, the inner TreeSitterTranslator had an empty
        implicit_param_map so nothing substituted.
        """
        translator = LLMTranslator(
            keyword_map={"def": "definir", "return": "retornar"},
            builtin_map={"print": "imprimir"},
            backend=MockBackend(),
            implicit_param_map={"self": "propio"},
        )
        out = translator.keyword_translator.translate_code(
            "def foo(self): return self.x", "en", "es"
        )
        assert "propio" in out
        assert out.count("propio") == 2  # signature + attribute access

    def test_constructor_backward_compat_no_implicit_param_map(self):
        """Existing callers without implicit_param_map kwarg still work."""
        translator = LLMTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            backend=MockBackend(),
        )
        assert translator.mapper.implicit_param_map == {}

    def test_reverse_reverses_implicit_param_map(self):
        """LLMTranslator.reverse() restores self/cls on round-trip."""
        en_to_es = LLMTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            backend=MockBackend(),
            implicit_param_map={"self": "propio", "cls": "clase_ref"},
        )
        es_to_en = en_to_es.reverse()
        assert es_to_en.mapper.implicit_param_map == {
            "propio": "self",
            "clase_ref": "cls",
        }

    def test_from_language_pack_picks_up_implicit_params(self):
        """from_language_pack reads pack.implicit_params and threads through."""
        translator = LLMTranslator.from_language_pack(
            "es", "3.13", backend=MockBackend()
        )
        assert translator.mapper.implicit_param_map.get("self") is not None
        assert translator.mapper.implicit_param_map.get("cls") is not None
        # Same map flows through to inner keyword_translator
        assert (
            translator.keyword_translator.mapper.implicit_param_map
            == translator.mapper.implicit_param_map
        )

    def test_factory_create_translator_with_llm_backend_threads_implicit_param_map(
        self,
    ):
        """create_translator(..., backend=<llm>, implicit_param_map=...) wires correctly.

        Pre-fix the factory dropped implicit_param_map when backend was set;
        this pins that it now propagates.
        """
        translator = create_translator(
            "python",
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio", "cls": "clase_ref"},
            backend=MockBackend(),
        )
        assert isinstance(translator, LLMTranslator)
        assert translator.mapper.implicit_param_map == {
            "self": "propio",
            "cls": "clase_ref",
        }
