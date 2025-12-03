"""Tests for AI context generation."""

from pathlib import Path

import pytest

from legesher_core import (
    AIContextGenerator,
    generate_bilingual_examples,
    generate_builtin_table,
    generate_exception_table,
    generate_keyword_table,
)


@pytest.fixture
def spanish_keywords():
    """Spanish keyword translations for testing."""
    return {
        "def": "definir",
        "return": "retornar",
        "if": "si",
        "else": "sino",
        "for": "para",
        "in": "en",
        "class": "clase",
        "import": "importar",
        "from": "desde",
        "as": "como",
    }


@pytest.fixture
def spanish_builtins():
    """Spanish builtin translations for testing."""
    return {
        "print": "imprimir",
        "len": "longitud",
        "range": "rango",
        "int": "entero",
        "str": "cadena",
        "list": "lista",
        "dict": "diccionario",
    }


@pytest.fixture
def spanish_exceptions():
    """Spanish exception translations for testing."""
    return {
        "ValueError": "ErrorDeValor",
        "TypeError": "ErrorDeTipo",
        "KeyError": "ErrorDeLlave",
    }


class TestAIContextGenerator:
    """Tests for AIContextGenerator class."""

    def test_generator_initialization(self, spanish_keywords, spanish_builtins):
        """Test that generator initializes correctly."""
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
        )

        assert generator.language_code == "es"
        assert generator.python_version == "3.13"
        assert generator.keywords == spanish_keywords
        assert generator.builtins == spanish_builtins
        assert generator.exceptions == {}

    def test_generator_with_exceptions(
        self, spanish_keywords, spanish_builtins, spanish_exceptions
    ):
        """Test generator with exception translations."""
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
            exceptions=spanish_exceptions,
        )

        assert generator.exceptions == spanish_exceptions

    def test_generate_creates_file(self, tmp_path, spanish_keywords, spanish_builtins):
        """Test that generate() creates AI context file."""
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
        )

        output_path = tmp_path / ".legesher" / "AI-CONTEXT.md"
        generator.generate(output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check for key sections
        assert "# Legesher AI Context - Spanish (Español) Python" in content
        assert "Language**: Spanish (es) - Español" in content
        assert "Python Version**: 3.13" in content
        assert "## Python Keywords" in content
        assert "## Python Builtins" in content
        assert "## Bilingual Examples" in content
        assert "## Best Practices for AI Assistants" in content

    def test_generate_includes_translations(
        self, tmp_path, spanish_keywords, spanish_builtins
    ):
        """Test that generated file includes translation tables."""
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
        )

        output_path = tmp_path / "AI-CONTEXT.md"
        generator.generate(output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for specific translations
        assert "definir" in content  # Spanish "def"
        assert "retornar" in content  # Spanish "return"
        assert "imprimir" in content  # Spanish "print"
        assert "longitud" in content  # Spanish "len"

    def test_generate_with_exceptions(
        self, tmp_path, spanish_keywords, spanish_builtins, spanish_exceptions
    ):
        """Test that exception table is included when provided."""
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
            exceptions=spanish_exceptions,
        )

        output_path = tmp_path / "AI-CONTEXT.md"
        generator.generate(output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for exception section and translations
        assert "## Python Exceptions" in content
        assert "ErrorDeValor" in content
        assert "ErrorDeTipo" in content
        assert "ErrorDeLlave" in content


class TestKeywordTable:
    """Tests for keyword table generation."""

    def test_generates_markdown_table(self, spanish_keywords):
        """Test that keyword table is valid markdown."""
        result = generate_keyword_table(spanish_keywords, "es")

        assert "## Python Keywords" in result
        assert "| English | ES | Usage Context |" in result
        assert "|---------|---------|---------------|" in result

    def test_includes_all_keywords(self, spanish_keywords):
        """Test that all keywords are included in table."""
        result = generate_keyword_table(spanish_keywords, "es")

        for english, spanish in spanish_keywords.items():
            assert f"`{english}`" in result
            assert f"`{spanish}`" in result


class TestBuiltinTable:
    """Tests for builtin table generation."""

    def test_generates_markdown_table(self, spanish_builtins):
        """Test that builtin table is valid markdown."""
        result = generate_builtin_table(spanish_builtins, "es")

        assert "## Python Builtins" in result
        assert "| English | ES | Description |" in result
        assert "|---------|---------|-------------|" in result

    def test_includes_all_builtins(self, spanish_builtins):
        """Test that all builtins are included in table."""
        result = generate_builtin_table(spanish_builtins, "es")

        for english, spanish in spanish_builtins.items():
            assert f"`{english}()`" in result
            assert f"`{spanish}()`" in result


class TestExceptionTable:
    """Tests for exception table generation."""

    def test_generates_markdown_table(self, spanish_exceptions):
        """Test that exception table is valid markdown."""
        result = generate_exception_table(spanish_exceptions, "es")

        assert "## Python Exceptions" in result
        assert "| English | ES | When Raised |" in result
        assert "|---------|---------|-------------|" in result

    def test_includes_all_exceptions(self, spanish_exceptions):
        """Test that all exceptions are included in table."""
        result = generate_exception_table(spanish_exceptions, "es")

        for english, spanish in spanish_exceptions.items():
            assert f"`{english}`" in result
            assert f"`{spanish}`" in result


class TestBilingualExamples:
    """Tests for bilingual code examples."""

    def test_generates_examples(self, spanish_keywords, spanish_builtins):
        """Test that bilingual examples are generated."""
        result = generate_bilingual_examples("es", spanish_keywords, spanish_builtins)

        assert "## Bilingual Examples" in result
        assert "### Example 1: Function Definition" in result
        assert "### Example 2: Conditional Logic" in result
        assert "### Example 3: Loops" in result

    def test_uses_translated_keywords(self, spanish_keywords, spanish_builtins):
        """Test that examples use translated keywords."""
        result = generate_bilingual_examples("es", spanish_keywords, spanish_builtins)

        # Check for Spanish keywords in examples
        assert "definir" in result  # def
        assert "retornar" in result  # return
        assert "si" in result  # if
        assert "sino" in result  # else
        assert "para" in result  # for

    def test_uses_translated_builtins(self, spanish_keywords, spanish_builtins):
        """Test that examples use translated builtins."""
        result = generate_bilingual_examples("es", spanish_keywords, spanish_builtins)

        # Check for Spanish builtins in examples
        assert "imprimir" in result  # print
        assert "longitud" in result  # len
        assert "rango" in result  # range

    def test_includes_best_practices(self, spanish_keywords, spanish_builtins):
        """Test that best practices section is included."""
        result = generate_bilingual_examples("es", spanish_keywords, spanish_builtins)

        assert "### When Suggesting Code" in result
        assert "DON'T" in result
        assert "DO" in result
        assert "mixing languages" in result.lower()


class TestIntegration:
    """Integration tests for AI context generation."""

    def test_full_workflow(self, tmp_path, spanish_keywords, spanish_builtins):
        """Test complete workflow from generator to file."""
        # Create generator
        generator = AIContextGenerator(
            language_code="es",
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
        )

        # Generate file
        output_path = tmp_path / ".legesher" / "AI-CONTEXT-es.md"
        generator.generate(output_path)

        # Verify file exists and has content
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 1000  # Should be substantial

        # Verify all major sections are present
        assert "# Legesher AI Context" in content
        assert "## Overview" in content
        assert "## Python Keywords" in content
        assert "## Python Builtins" in content
        assert "## Bilingual Examples" in content
        assert "## Best Practices" in content

        # Verify translations are present
        assert "definir" in content
        assert "imprimir" in content

    def test_multiple_languages(self, tmp_path, spanish_keywords, spanish_builtins):
        """Test generating context for multiple languages."""
        languages = ["es", "ar", "fr"]

        for lang in languages:
            generator = AIContextGenerator(
                language_code=lang,
                python_version="3.13",
                keywords=spanish_keywords,  # Using same for testing
                builtins=spanish_builtins,
            )

            output_path = tmp_path / f"AI-CONTEXT-{lang}.md"
            generator.generate(output_path)

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            # Check for language code in the header (with language name)
            assert f"({lang})" in content

    def test_unknown_language_fallback(self, spanish_keywords, spanish_builtins):
        """Test that unknown languages get uppercase fallback."""
        generator = AIContextGenerator(
            language_code="xx",  # Unknown language
            python_version="3.13",
            keywords=spanish_keywords,
            builtins=spanish_builtins,
        )

        assert generator.language_name == "XX"
        assert generator.language_native == "XX"
        assert generator.is_rtl is False

        # Test that file generation still works with fallback
        output_path = Path("test_fallback.md")
        try:
            generator.generate(output_path)
            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "XX" in content  # Fallback language name appears
        finally:
            if output_path.exists():
                output_path.unlink()  # Cleanup
