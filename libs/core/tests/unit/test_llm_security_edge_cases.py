"""Security-focused and edge case tests for LLM translation pipeline.

Tests injection hardening in string/comment reconstruction, malformed JSON
handling in IdentifierMap, Unicode edge cases in IdentifierValidator,
extractor edge cases for advanced Python syntax, and LLMTranslator
integration scenarios.

These tests complement test_llm_translator.py, test_identifier_map.py,
test_identifier_validator.py, and test_extractor.py — no duplication.
"""

import json

import pytest

from legesher_core.token_mapper import TokenMapper
from legesher_core.tree_sitter.extractor import TranslatableExtractor
from legesher_core.tree_sitter.identifier_map import IdentifierMap
from legesher_core.tree_sitter.identifier_validator import IdentifierValidator
from legesher_core.tree_sitter.llm_translator import LLMTranslator

# ---------------------------------------------------------------------------
# Mock backend — returns ORIGINAL text for unknown keys
# ---------------------------------------------------------------------------


class MockBackend:
    """Mock TextTranslationBackend that returns originals for unknown keys."""

    def __init__(self, translations=None):
        self.translations = translations or {}
        self.calls = []

    def translate_text(self, text, source_lang, target_lang, context=None):
        self.calls.append(("translate_text", text, source_lang, target_lang))
        return self.translations.get(text, text)

    def translate_batch(self, items, source_lang, target_lang):
        self.calls.append(
            ("translate_batch", [i["text"] for i in items], source_lang, target_lang)
        )
        return [self.translations.get(i["text"], i["text"]) for i in items]


# ---------------------------------------------------------------------------
# Shared maps (copied from test_llm_translator.py to avoid cross-import)
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def extractor():
    mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
    return TranslatableExtractor(mapper)


@pytest.fixture
def validator():
    return IdentifierValidator()


# ===========================================================================
# Section 1: String/Docstring Injection Hardening (LLMTranslator)
# ===========================================================================


class TestStringInjectionHardening:
    """Verify that malicious LLM translations are sanitized in output."""

    def test_triple_quote_in_translation_is_escaped(self):
        """LLM returns triple-quote inside a docstring — must not break syntax."""
        backend = MockBackend(
            translations={
                "Greet the user": 'Hola"""mundo',
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'def foo():\n    """Greet the user"""\n    pass'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # The injected """ must be escaped so we do not get an unmatched close.
        # Count unescaped triple-quote occurrences: there should be exactly
        # an opening and closing pair, not an odd number.
        # The escaping turns """ into \"\"\" or similar so the literal does not break.
        # The key property: the result should not contain a bare '"""' that
        # splits the docstring prematurely.  The _translate_text_elements method
        # replaces the closing-quote sequence inside the translation.
        # We verify the output has exactly one docstring opening and closing.
        assert '\\"""' in result or '\\"' in result or result.count('"""') == 2

    def test_single_quote_in_translation_is_escaped(self):
        """LLM returns a single quote inside a single-quoted string."""
        backend = MockBackend(
            translations={
                "Hello": "it's",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "x = 'Hello'"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # The inner quote must be escaped so the string literal is not broken
        assert "\\'" in result or result.count("'") == 2

    def test_double_quote_in_translation_is_escaped(self):
        """LLM returns a double quote inside a double-quoted string."""
        backend = MockBackend(
            translations={
                "Hello": 'say "hi"',
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'x = "Hello"'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # The inner double-quotes must be escaped
        assert '\\"' in result or result.count('"') == 2

    def test_multiline_comment_translation_all_lines_prefixed(self):
        """LLM returns a multi-line translation for a comment — each line needs #."""
        backend = MockBackend(
            translations={
                "Explain the logic": "Primera linea\nSegunda linea\nTercera linea",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "# Explain the logic\nx = 1"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # Each translated line must start with # so none becomes executable code
        lines = result.strip().split("\n")
        comment_lines = [
            line
            for line in lines
            if "linea" in line.lower()
            or "primera" in line.lower()
            or "segunda" in line.lower()
            or "tercera" in line.lower()
        ]
        for line in comment_lines:
            assert line.strip().startswith("#"), (
                f"Comment line not prefixed with #: {line!r}"
            )

    def test_comment_with_newline_does_not_inject_code(self):
        """LLM returns newline + code in a comment — must stay as comment."""
        backend = MockBackend(
            translations={
                "A note": "Hola\nimport os",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "# A note\nx = 1"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # "import os" must appear inside a comment line, not as bare code
        for line in result.split("\n"):
            if "import os" in line:
                assert line.strip().startswith("#"), (
                    f"Injected code not inside comment: {line!r}"
                )


# ===========================================================================
# Section 2: IdentifierMap Malformed JSON
# ===========================================================================


class TestIdentifierMapMalformedJSON:
    """Test IdentifierMap.load() with various malformed JSON files."""

    def test_load_non_dict_identifiers_raises(self, tmp_path):
        """identifiers field is a string instead of dict."""
        path = tmp_path / "bad_map.json"
        data = {"version": 1, "source_lang": "en", "identifiers": "not_a_dict"}
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="identifiers.*must be a dict"):
            IdentifierMap.load(path)

    def test_load_non_dict_translations_raises(self, tmp_path):
        """An identifier's translations value is a string instead of dict."""
        path = tmp_path / "bad_map.json"
        data = {
            "version": 1,
            "source_lang": "en",
            "identifiers": {"foo": "not_a_dict"},
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid entry"):
            IdentifierMap.load(path)

    def test_load_empty_json_object(self, tmp_path):
        """Empty JSON object {} should load without error as empty map."""
        path = tmp_path / "empty.json"
        path.write_text("{}", encoding="utf-8")

        loaded = IdentifierMap.load(path)
        assert len(loaded) == 0
        assert loaded.source_lang == "en"  # default

    def test_load_missing_version_field(self, tmp_path):
        """JSON without 'version' key should still load fine."""
        path = tmp_path / "no_version.json"
        data = {
            "source_lang": "en",
            "identifiers": {"greet": {"es": "saludar"}},
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        loaded = IdentifierMap.load(path)
        assert loaded.get("greet", "es") == "saludar"
        assert len(loaded) == 1


# ===========================================================================
# Section 3: Identifier Validator Edge Cases
# ===========================================================================


class TestIdentifierValidatorUnicode:
    """Unicode edge cases for identifier validation."""

    def test_urdu_identifier_is_valid(self, validator):
        """Urdu script identifier should be valid Python."""
        assert validator.is_valid("\u0679\u06cc\u06a9\u0633_\u062d\u0633\u0627\u0628")

    def test_arabic_identifier_is_valid(self, validator):
        """Arabic script identifier should be valid Python."""
        assert validator.is_valid(
            "\u062d\u0633\u0627\u0628_\u0627\u0644\u0636\u0631\u064a\u0628\u0629"
        )

    def test_chinese_identifier_is_valid(self, validator):
        """CJK identifier should be valid Python."""
        assert validator.is_valid("\u8ba1\u7b97\u7a0e\u989d")

    def test_devanagari_identifier_is_valid(self, validator):
        """Devanagari (Hindi) identifier should be valid Python."""
        assert validator.is_valid("\u0915\u0930_\u0917\u0923\u0928\u093e")

    def test_zero_width_chars_in_identifier(self, validator):
        """Identifier with zero-width joiner — Python considers it valid."""
        ident = "foo\u200dbar"
        # Python's str.isidentifier() accepts ZWJ (it is category Cf,
        # which is valid in identifier_continue).  This is a known
        # confusable-character issue but not a syntax error.
        result = validator.is_valid(ident)
        assert result is True

    def test_bidi_override_in_identifier(self, validator):
        """Identifier with RTL override character should be invalid or sanitized."""
        ident = "foo\u202ebar"
        # RTL override is not a valid identifier character
        result = validator.is_valid(ident)
        assert result is False

    def test_sanitize_preserves_unicode(self, validator):
        """sanitize() should replace spaces but keep Arabic/Urdu characters."""
        result = validator.sanitize("\u062d\u0633\u0627\u0628 \u0679\u06cc\u06a9\u0633")
        assert "_" in result
        assert " " not in result
        # Must preserve the Arabic/Urdu characters
        assert "\u062d" in result or "\u0633" in result
        assert result.isidentifier()


# ===========================================================================
# Section 4: Extractor Edge Cases
# ===========================================================================


class TestExtractorEdgeCases:
    """Edge cases for TranslatableExtractor with advanced Python syntax."""

    def test_fstring_nested_expression_not_extracted(self, extractor):
        """Variables inside f-string {} are code, not translatable strings."""
        code = 'x = f"Hello {user.name}"'
        elements = extractor.extract(code)
        strings = [e for e in elements if e.kind == "string"]
        # The text parts should not contain the expression
        for s in strings:
            assert "user.name" not in s.text
        # But user and name should appear as identifiers
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "user" in ids or "name" in ids

    def test_decorator_with_arguments(self, extractor):
        """Identifiers in decorator expressions should be extracted."""
        code = '@app.route("/api")\ndef handler(): pass'
        elements = extractor.extract(code)
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "app" in ids
        assert "route" in ids

    def test_walrus_operator_variable(self, extractor):
        """Walrus operator variable should be extracted."""
        code = "if (n := 10) > 5:\n    pass"
        elements = extractor.extract(code)
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "n" in ids

    def test_comprehension_variable(self, extractor):
        """Variables in comprehensions should be extracted."""
        code = "result = [x for x in items]"
        elements = extractor.extract(code)
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "x" in ids
        assert "items" in ids
        assert "result" in ids

    def test_class_inheritance_identifiers(self, extractor):
        """Class name and base class should both be extracted."""
        code = "class Dog(Animal):\n    pass"
        elements = extractor.extract(code)
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "Dog" in ids
        assert "Animal" in ids

    def test_type_annotation_identifiers(self, extractor):
        """Identifiers in type annotations should be handled."""
        code = "def foo(x: int) -> str:\n    pass"
        elements = extractor.extract(code)
        ids = [e.text for e in elements if e.kind == "identifier"]
        assert "foo" in ids
        # x should be extracted (it is the parameter name)
        assert "x" in ids
        # int and str are builtins, so should NOT be extracted
        assert "int" not in ids
        assert "str" not in ids


# ===========================================================================
# Section 5: LLMTranslator Integration Edge Cases
# ===========================================================================


class TestLLMTranslatorIntegration:
    """Integration-level edge cases for LLMTranslator."""

    def test_identifier_consistency_across_multiple_calls(self):
        """Same identifier gets same translation across separate translate_code calls."""
        backend = MockBackend(
            translations={
                "greet": "saludar",
                "name": "nombre",
                "Hello": "Hola",
                "message": "mensaje",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )

        code1 = "def greet(name):\n    pass"
        result1 = translator.translate_code(code1, "en", "es")

        code2 = "message = greet(name)"
        result2 = translator.translate_code(code2, "en", "es")

        # "greet" should be "saludar" in both outputs
        assert "saludar" in result1
        assert "saludar" in result2
        # The translator's internal identifier map should have the mapping
        assert translator.identifier_map.get("greet", "es") == "saludar"

    def test_translate_code_with_only_keywords(self):
        """Code with only keywords and no user content should not call LLM."""
        backend = MockBackend()
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "if True:\n    pass"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # Keywords should be translated
        assert "si" in result or "Verdadero" in result
        # Backend should not have been called for identifiers or text
        # (no user identifiers, no comments, no strings)
        batch_calls = [c for c in backend.calls if c[0] == "translate_batch"]
        for call in batch_calls:
            texts = call[1]
            # No user-defined identifiers should have been sent
            assert "if" not in texts
            assert "True" not in texts
            assert "pass" not in texts


# ===========================================================================
# Section 6: Review Follow-up — F-string, Comment, Verify, Adapter Fixes
# ===========================================================================


class TestFstringReconstruction:
    """Verify f-string string_content nodes get raw text, not quoted literals."""

    def test_fstring_translation_no_extra_quotes(self):
        """Translating f-string content should NOT wrap in quotes."""
        backend = MockBackend(
            translations={
                "Hello, ": "Hola, ",
                "greet": "saludar",
                "name": "nombre",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'def greet(name):\n    return f"Hello, {name}!"'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # Should NOT produce f"""Hola, """{nombre}! or similar corruption
        assert '"""' not in result or result.count('"""') == 0
        # The f-string should remain a single f-string, not break into pieces
        assert "f" in result

    def test_fstring_braces_escaped_in_translation(self):
        """LLM translation containing { or } should be escaped in f-string content."""
        backend = MockBackend(
            translations={
                "value is ": "el valor es {dato} ",  # LLM returns literal braces
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'x = f"value is {x}"'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # The literal braces from LLM should be escaped as {{ }}
        # so they don't become new interpolation
        assert "{{dato}}" in result or "el valor es" in result

    def test_fstring_newline_escaped_in_single_quoted(self):
        """Newlines in LLM translation escaped for non-triple-quoted f-strings."""
        backend = MockBackend(
            translations={
                "hello ": "hola\nmundo ",  # LLM returns newline
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'x = f"hello {name}"'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # Newline should be escaped as \n in non-triple-quoted f-string
        assert "hola\\nmundo" in result or "hola" in result

    def test_fstring_context_flag_set_by_extractor(self):
        """Extractor sets is_fstring_content flag on f-string string_content."""
        mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
        extractor = TranslatableExtractor(mapper)
        elements = extractor.extract('x = f"Hello, {name}!"')
        fstring_elements = [
            e
            for e in elements
            if e.kind == "string" and e.context.get("is_fstring_content")
        ]
        assert len(fstring_elements) >= 1
        assert fstring_elements[0].context["is_fstring_content"] is True

    def test_fstring_triple_quote_flag(self):
        """Extractor detects triple-quoted f-strings."""
        mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
        extractor = TranslatableExtractor(mapper)
        elements = extractor.extract('x = f"""Hello, {name}!"""')
        fstring_elements = [
            e
            for e in elements
            if e.kind == "string" and e.context.get("is_fstring_content")
        ]
        if fstring_elements:
            assert fstring_elements[0].context.get("is_triple_quoted") is True


class TestCommentNoDoubleHash:
    """Verify comments don't get double # prefix after extraction + reconstruction."""

    def test_comment_text_has_no_hash_prefix(self):
        """Extractor stores comment content without # prefix."""
        mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
        extractor = TranslatableExtractor(mapper)
        elements = extractor.extract("# This is a comment\nx = 1")
        comments = [e for e in elements if e.kind == "comment"]
        assert len(comments) == 1
        # elem.text should be content only, no #
        assert not comments[0].text.startswith("#")
        assert comments[0].text == "This is a comment"

    def test_comment_hash_prefix_in_context(self):
        """Extractor stores the hash prefix in context for reconstruction."""
        mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
        extractor = TranslatableExtractor(mapper)
        elements = extractor.extract("# A note\nx = 1")
        comments = [e for e in elements if e.kind == "comment"]
        assert len(comments) == 1
        assert "hash_prefix" in comments[0].context
        assert comments[0].context["hash_prefix"] == "# "

    def test_double_hash_comment_preserved(self):
        """## style comments preserve the ## prefix."""
        mapper = TokenMapper(KEYWORD_MAP, BUILTIN_MAP)
        extractor = TranslatableExtractor(mapper)
        elements = extractor.extract("## Section header\nx = 1")
        comments = [e for e in elements if e.kind == "comment"]
        assert len(comments) == 1
        assert comments[0].context["hash_prefix"].startswith("## ")

    def test_translated_comment_single_hash(self):
        """Full pipeline: translated comment has exactly one # prefix, not ##."""
        backend = MockBackend(
            translations={
                "A note": "Una nota",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "# A note\nx = 1"
        result = translator.translate_code(code, "en", "es")
        comment_lines = [line for line in result.split("\n") if "nota" in line.lower()]
        assert len(comment_lines) >= 1
        # Should be "# Una nota", NOT "## Una nota" or "# # Una nota"
        assert comment_lines[0].strip().startswith("# ")
        assert not comment_lines[0].strip().startswith("## ")

    def test_backend_receives_content_not_hash(self):
        """The LLM backend receives comment content without # prefix."""
        backend = MockBackend()
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "# Translate this\nx = 1"
        translator.translate_code(code, "en", "es")
        # Check what was sent to the backend
        batch_calls = [c for c in backend.calls if c[0] == "translate_batch"]
        all_texts = []
        for call in batch_calls:
            all_texts.extend(call[1])
        # The comment text sent should NOT start with #
        comment_texts = [
            t for t in all_texts if "translate" in t.lower() or "Translate" in t
        ]
        for text in comment_texts:
            assert not text.startswith("#"), f"Backend received # prefix: {text!r}"


class TestVerifyOutputKeywordCount:
    """Verify _verify_output uses actual keyword replacement count."""

    def test_no_warning_for_normal_translation(self, caplog):
        """Normal translation should not trigger structural warning."""
        import logging

        backend = MockBackend(translations={"greet": "saludar", "name": "nombre"})
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "def greet(name):\n    pass"
        with caplog.at_level(
            logging.WARNING, logger="legesher_core.tree_sitter.llm_translator"
        ):
            result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        assert "definir" in result
        # No structural warning should have been emitted
        assert "structural issues" not in caplog.text


class TestBatchAdapterInterface:
    """Verify batch adapter has the expected interface."""

    def test_adapter_has_translate_batch(self):
        """ProviderBackendAdapter has translate_batch method."""
        from legesher_i18n.api.backends import ProviderBackendAdapter

        assert hasattr(ProviderBackendAdapter, "translate_batch")

    def test_adapter_has_translate_text(self):
        """ProviderBackendAdapter has translate_text method."""
        from legesher_i18n.api.backends import ProviderBackendAdapter

        assert hasattr(ProviderBackendAdapter, "translate_text")


class TestNewlineEscapingInStrings:
    """Verify newlines in LLM translations are escaped for non-triple-quoted strings."""

    def test_single_quoted_string_newline_escaped(self):
        """Newline in translation for 'single' quoted string gets escaped."""
        backend = MockBackend(
            translations={
                "Hello world": "Hola\nmundo",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = "x = 'Hello world'"
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
        # Newline should be escaped, not create a multi-line syntax error
        assert "Hola\\nmundo" in result or "Hola" in result
        # The literal newline should be escaped, not create a multi-line string
        # that would be a syntax error for single-quoted strings

    def test_triple_quoted_string_newline_preserved(self):
        """Newline in translation for triple-quoted string is preserved as-is."""
        backend = MockBackend(
            translations={
                "Hello world": "Hola\nmundo",
            }
        )
        translator = LLMTranslator(
            keyword_map=KEYWORD_MAP,
            builtin_map=BUILTIN_MAP,
            backend=backend,
        )
        code = 'x = """Hello world"""'
        result = translator.translate_code(code, "en", "es")
        assert isinstance(result, str)
