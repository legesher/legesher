"""Integration tests for file translation.

Tests full file translation workflows using realistic Python code fixtures.
"""

import pytest
from pathlib import Path

from legesher_core.transformer import TokenTranslator
from tests.data.keyword_maps_spanish import SPANISH_KEYWORDS, SPANISH_BUILTINS


class TestFileTranslation:
    """Integration tests for translating complete Python files."""

    @pytest.fixture
    def translator(self):
        """Create Spanish translator."""
        return TokenTranslator(
            keyword_map=SPANISH_KEYWORDS, builtin_map=SPANISH_BUILTINS
        )

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_translate_english_file(self, translator, fixtures_dir):
        """Test translating complete English Python file."""
        english_file = fixtures_dir / "sample_english.py"
        result = translator.translate_file(english_file, "es")

        # Verify keywords are translated
        assert "definir" in result  # def
        assert "clase" in result  # class
        assert "retornar" in result  # return
        assert "si" in result  # if
        assert "sino" in result  # else
        assert "sinosi" in result  # elif
        assert "para" in result  # for
        assert "intentar" in result  # try
        assert "excepto" in result  # except
        assert "lanzar" in result  # raise
        assert "asincrono" in result  # async
        assert "esperar" in result  # await

        # Verify builtins are translated
        assert "flotante" in result  # float
        assert "imprimir" in result  # print
        assert "lista" in result  # list
        assert "diccionario" in result  # dict

        # Verify identifiers are NOT translated
        assert "calculate_tax" in result
        assert "BankAccount" in result
        assert "process_transactions" in result

        # Verify comments are preserved
        assert "# High earners pay higher rate" in result

        # Verify docstrings are preserved
        assert "Calculate income tax" in result

    def test_translated_file_structure_preserved(self, translator, fixtures_dir):
        """Test that file structure is preserved in translation."""
        english_file = fixtures_dir / "sample_english.py"
        original = english_file.read_text(encoding="utf-8")
        translated = translator.translate_file(english_file, "es")

        # Same number of lines
        assert original.count("\n") == translated.count("\n")

        # Same indentation pattern
        orig_lines = original.split("\n")
        trans_lines = translated.split("\n")

        for i, (orig, trans) in enumerate(zip(orig_lines, trans_lines)):
            # Skip empty lines
            if not orig.strip():
                continue

            # Count leading whitespace
            orig_indent = len(orig) - len(orig.lstrip())
            trans_indent = len(trans) - len(trans.lstrip())

            assert (
                orig_indent == trans_indent
            ), f"Line {i+1}: Indentation mismatch ({orig_indent} vs {trans_indent})"

    def test_file_translation_encoding_utf8(self, translator, tmp_path):
        """Test that translated files are UTF-8 encoded."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def greet():\n    print('Hello')\n    return True", encoding="utf-8"
        )

        # Translate
        result = translator.translate_file(test_file, "es")

        # Verify result is valid UTF-8
        result.encode("utf-8").decode("utf-8")

        assert "definir" in result
        assert "imprimir" in result
        assert "retornar" in result

    def test_empty_file_translation(self, translator, tmp_path):
        """Test translating an empty file."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("", encoding="utf-8")

        result = translator.translate_file(empty_file, "es")
        assert result == ""

    def test_comments_only_file(self, translator, tmp_path):
        """Test translating file with only comments."""
        comments_file = tmp_path / "comments.py"
        content = "# Comment 1\n# Comment 2\n# Comment 3\n"
        comments_file.write_text(content, encoding="utf-8")

        result = translator.translate_file(comments_file, "es")
        assert result == content  # Unchanged

    def test_large_file_translation(self, translator, tmp_path):
        """Test translating a large file (5000+ lines)."""
        # Generate large file
        large_file = tmp_path / "large.py"
        code_lines = []

        for i in range(1000):
            code_lines.append(f"def function_{i}():")
            code_lines.append("    if True:")
            code_lines.append(f"        return {i}")
            code_lines.append("")  # blank line
            code_lines.append(f"# Comment {i}")

        large_content = "\n".join(code_lines)
        large_file.write_text(large_content, encoding="utf-8")

        # Translate
        result = translator.translate_file(large_file, "es")

        # Verify keywords translated
        assert "definir" in result
        assert "si" in result
        assert "retornar" in result

        # Verify function names preserved
        assert "function_0" in result
        assert "function_999" in result

        # Verify same line count
        assert large_content.count("\n") == result.count("\n")
