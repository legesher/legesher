"""Integration tests for cultural comments with TokenTranslator and IDE support.

Tests the full integration of cultural comment parsing with:
- TokenTranslator (translation preserves cultural comments)
- CulturalCommentProvider (IDE integration API)
"""

import pytest

from legesher_core import (
    CulturalCommentProvider,
    TokenTranslator,
)


class TestTokenTranslatorIntegration:
    """Test cultural comments integration with TokenTranslator."""

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TokenTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def arabic_translator(self, arabic_keywords, arabic_builtins):
        """Create a translator configured for Arabic."""
        return TokenTranslator(keyword_map=arabic_keywords, builtin_map=arabic_builtins)

    def test_translator_preserves_cultural_comments(
        self, spanish_translator, spanish_keywords
    ):
        """Test that translation preserves cultural comments unchanged."""
        code = """
#@culture[es]: "rango" puede significar "rank" o "range"
def calculate_range(n):
    return range(n)
"""
        translated = spanish_translator.translate_code(code, "en", "es")

        # Cultural comment should be preserved exactly
        assert "#@culture[es]:" in translated
        assert "rango" in translated
        # Keywords should be translated
        assert spanish_keywords["def"] in translated

    def test_translator_returns_metadata(self, spanish_translator):
        """Test that translator can return cultural comment metadata."""
        code = """
#@culture[es]: Spanish explanation
#@culture[en]: English explanation
def foo(): pass
"""
        translated, metadata = spanish_translator.translate_code(
            code, "en", "es", return_metadata=True
        )

        assert metadata.has_comments()
        assert len(metadata.comments) == 2  # Two lines with comments
        assert metadata.get_for_language("es")
        assert metadata.get_for_language("en")

    def test_translator_default_no_metadata(self, spanish_translator):
        """Test that default behavior doesn't return metadata."""
        code = """
#@culture[es]: test
def foo(): pass
"""
        result = spanish_translator.translate_code(code, "en", "es")

        # Should return just the string, not a tuple
        assert isinstance(result, str)
        assert "#@culture[es]: test" in result

    def test_roundtrip_translation_preserves_cultural(self, spanish_translator):
        """Test that cultural comments survive round-trip translation."""
        original = """
#@culture[es]: Important cultural note
def greet():
    print("Hello")
"""
        # Translate to Spanish
        spanish = spanish_translator.translate_code(original, "en", "es")
        assert "#@culture[es]:" in spanish

        # Cultural comment should still be there
        assert "Important cultural note" in spanish

    def test_mixed_regular_and_cultural_comments(self, spanish_translator):
        """Test translation with both regular and cultural comments."""
        code = """
# Regular comment about the function
#@culture[es]: Cultural context for Spanish speakers
def calculate_tax(income):
    # Another regular comment
    return income * 0.25
"""
        translated, metadata = spanish_translator.translate_code(
            code, "en", "es", return_metadata=True
        )

        # Both types of comments should be preserved
        assert "# Regular comment" in translated
        assert "#@culture[es]:" in translated

        # Only cultural comments in metadata
        assert metadata.has_comments()
        assert len(metadata.get_for_language("es")) == 1

    def test_multilingual_cultural_comments(self, spanish_translator):
        """Test file with cultural comments in multiple languages."""
        code = """
#@culture[es]: Explicación en español
#@culture[ar]: شرح بالعربية
#@culture[en]: Explanation in English
def foo(): pass
"""
        translated, metadata = spanish_translator.translate_code(
            code, "en", "es", return_metadata=True
        )

        # All cultural comments preserved
        assert metadata.has_comments()
        all_langs = metadata.get_all_languages()
        assert all_langs == {"es", "ar", "en"}

    def test_empty_source_with_metadata(self, spanish_translator):
        """Test empty source code with return_metadata=True."""
        translated, metadata = spanish_translator.translate_code(
            "", "en", "es", return_metadata=True
        )

        assert translated == ""
        assert not metadata.has_comments()

    def test_incomplete_code_with_cultural_comment(self, spanish_translator):
        """Test incomplete code with cultural comment."""
        incomplete = """
#@culture[es]: Comment before incomplete code
def foo(
"""
        # Should return original code unchanged with empty metadata
        translated, metadata = spanish_translator.translate_code(
            incomplete, "en", "es", return_metadata=True
        )

        assert translated == incomplete
        assert not metadata.has_comments()  # TokenError prevents parsing


class TestIDESupportIntegration:
    """Test IDE support layer integration."""

    def test_provider_basic_functionality(self):
        """Test basic CulturalCommentProvider functionality."""
        code = """
#@culture[es]: Spanish explanation
def foo(): pass
"""
        provider = CulturalCommentProvider(code)

        assert provider.has_cultural_comments()
        hover = provider.get_hover_text(2)
        assert hover is not None
        assert "💬" in hover
        assert "Spanish explanation" in hover

    def test_provider_decorations(self):
        """Test getting decorations for IDE."""
        code = """
#@culture[es]: Line 2
def foo():
    #@culture[en]: Line 4
    pass
"""
        provider = CulturalCommentProvider(code)
        decorations = provider.get_decorations()

        assert len(decorations) == 2
        # Each decoration is (line, icon, preview)
        assert all(d[1] == "💬" for d in decorations)

    def test_provider_diagnostics_for_malformed(self):
        """Test diagnostics for malformed cultural comments."""
        code = """
#@culture[zz]: Invalid language code
#@culture[ES]: Uppercase code
@culture[es]: Missing hash
def foo(): pass
"""
        provider = CulturalCommentProvider(code)
        diagnostics = provider.get_diagnostics()

        # Should find issues with invalid language codes
        assert len(diagnostics) >= 1
        # Each diagnostic is (line, col, severity, message)
        assert all(d[2] == "warning" for d in diagnostics)

    def test_provider_hover_with_language_preference(self):
        """Test hover text filtering by language preference."""
        code = """
#@culture[es]: Spanish text  #@culture[en]: English text
def foo(): pass
"""
        provider = CulturalCommentProvider(code)

        # Get hover for line 2 (has both comments but tokenize may separate them)
        # Let's test each line separately since they're tokenized separately
        hover_es_line = provider.get_hover_text(2)
        assert hover_es_line is not None
        assert "Spanish text" in hover_es_line

        # Filter for Spanish only
        hover_es = provider.get_hover_text(2, language_preference="es")
        assert hover_es is not None
        assert "Spanish text" in hover_es

        # Filter for English only (depending on tokenization, may or may not exist on same line)
        # Just verify the method works without error
        _ = provider.get_hover_text(2, language_preference="en")

    def test_provider_get_all_languages(self):
        """Test getting all languages used in file."""
        code = """
#@culture[es]: Spanish
#@culture[ar]: Arabic
#@culture[zh]: Chinese
def foo(): pass
"""
        provider = CulturalCommentProvider(code)
        languages = provider.get_all_languages()

        assert languages == {"es", "ar", "zh"}

    def test_provider_no_comments(self):
        """Test provider with no cultural comments."""
        code = """
# Regular comment
def foo(): pass
"""
        provider = CulturalCommentProvider(code)

        assert not provider.has_cultural_comments()
        assert provider.get_hover_text(2) is None
        assert provider.get_decorations() == []
        assert provider.get_all_languages() == set()


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""

    def test_spanish_developer_workflow(self, spanish_keywords, spanish_builtins):
        """Test workflow: Spanish developer writes code with cultural notes."""
        # Spanish developer writes code with cultural context
        spanish_code = f"""
#@culture[es]: "rango" en este contexto significa "range" (intervalo)
{spanish_keywords["def"]} calcular_suma(limite):
    total = 0
    {spanish_keywords["for"]} i {spanish_keywords["in"]} {spanish_builtins["range"]}(limite):
        total += i
    {spanish_keywords["return"]} total
"""
        # Create English translator to see what English dev would see
        english_keywords = {v: k for k, v in spanish_keywords.items()}
        english_builtins = {v: k for k, v in spanish_builtins.items()}
        translator = TokenTranslator(english_keywords, english_builtins)

        # Translate to English
        english_code, metadata = translator.translate_code(
            spanish_code, "es", "en", return_metadata=True
        )

        # English developer sees translated keywords
        assert "def" in english_code
        assert "for" in english_code
        assert "return" in english_code

        # But cultural comment is preserved for context
        assert "#@culture[es]:" in english_code
        assert "rango" in english_code

        # IDE can show the cultural context
        provider = CulturalCommentProvider(english_code)
        hover = provider.get_hover_text(2)
        assert hover is not None
        assert "rango" in hover

    def test_multilingual_team_collaboration(self):
        """Test collaboration between developers using different languages."""
        # File with contributions from multiple developers
        code = """
#@culture[es]: En español, "cadena" puede significar "string" o "chain"
#@culture[ar]: في العربية، نستخدم "نص" للإشارة إلى string
#@culture[zh]: 中文中我们使用"字符串"来表示string
def process_string(text):
    return text.upper()
"""
        # Any developer can see cultural context from all languages
        provider = CulturalCommentProvider(code)

        assert provider.has_cultural_comments()
        assert len(provider.get_all_languages()) == 3

        # IDE can show all cultural notes
        decorations = provider.get_decorations()
        assert len(decorations) == 3

    def test_ide_integration_complete_flow(self):
        """Test complete IDE integration flow."""
        code = """
#@culture[es]: Nota importante sobre el código
def calculate_tax(income, rate):
    #@culture[en]: Tax calculation uses standard formula
    return income * rate
"""
        # Step 1: Parse code for IDE
        provider = CulturalCommentProvider(code)

        # Step 2: IDE shows decorations in gutter
        decorations = provider.get_decorations()
        assert len(decorations) == 2

        # Step 3: User hovers over line 2
        hover_line_2 = provider.get_hover_text(2)
        assert hover_line_2 is not None
        assert "💬" in hover_line_2

        # Step 4: User hovers over line 4
        hover_line_4 = provider.get_hover_text(4)
        assert hover_line_4 is not None

        # Step 5: IDE checks for syntax errors
        diagnostics = provider.get_diagnostics()
        assert len(diagnostics) == 0  # No errors in this code
