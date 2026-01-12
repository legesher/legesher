"""Tests for fix_comment_syntax.py script.

This module tests the YAML comment syntax fixer that resolves issues where:
1. Comments are embedded inside quoted strings (parsed as part of value)
2. Apostrophes in translations break Python identifier syntax

These tests ensure the fix script works correctly and help prevent regression.
"""

from pathlib import Path
import tempfile
import sys

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fix_comment_syntax import (
    fix_quoted_comment_line,
    fix_apostrophe_line,
    fix_multiline_quoted_comments,
    fix_file,
    FixResult,
)


class TestFixQuotedCommentLine:
    """Test fixing single-line quoted comments."""

    def test_fixes_comment_inside_quotes(self):
        """Test that comments inside quotes are moved outside."""
        line = "  abs: 'абсолютноезначение  #абсолютное значение'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is True
        assert fixed == "  abs: абсолютноезначение  # абсолютное значение\n"
        assert "'" not in fixed  # No quotes in output

    def test_preserves_original_in_comment(self):
        """Test that original translation is preserved in comment."""
        line = "  delattr: 'удалитьатрибут  #удалить атрибут'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is True
        assert "удалить атрибут" in fixed  # Original preserved in comment
        assert fixed.startswith("  delattr: удалитьатрибут  # ")

    def test_handles_yaml_escaped_quotes(self):
        """Test handling of YAML escaped single quotes ('')."""
        line = "  any: 'n''importequel  #n''importe quel'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is True
        # Escaped quotes should be unescaped and removed from value
        assert "nimportequel" in fixed
        assert "n'importe quel" in fixed  # Comment has unescaped apostrophe

    def test_no_change_for_unquoted_line(self):
        """Test that unquoted lines are not modified."""
        line = "  def: определение\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is False
        assert fixed == line

    def test_no_change_for_already_correct_syntax(self):
        """Test that already-correct syntax is not modified."""
        line = "  abs: абсолютноезначение  # абсолютное значение\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is False
        assert fixed == line

    def test_handles_various_indentation(self):
        """Test handling of different indentation levels."""
        line = "    exception: 'исключение  #исключение'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is True
        assert fixed.startswith("    exception: ")  # Preserves indentation

    def test_removes_apostrophes_from_value(self):
        """Test that apostrophes are removed from the translation value."""
        line = "  test: 'val''ue  #val''ue'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        assert was_fixed is True
        # Value should have apostrophe removed
        assert "value" in fixed.split("#")[0]  # No apostrophe in value


class TestFixApostropheLine:
    """Test fixing apostrophes in unquoted translation values."""

    def test_fixes_apostrophe_in_value(self):
        """Test that apostrophes in values are removed."""
        line = "  break: s'échapper\n"
        fixed, was_fixed = fix_apostrophe_line(line)

        assert was_fixed is True
        assert "séchapper" in fixed  # Apostrophe removed
        assert "# s'échapper" in fixed  # Original preserved in comment

    def test_no_change_without_apostrophe(self):
        """Test that lines without apostrophes are not modified."""
        line = "  break: перебор\n"
        fixed, was_fixed = fix_apostrophe_line(line)

        assert was_fixed is False
        assert fixed == line

    def test_no_change_if_already_has_comment(self):
        """Test that lines with existing comments are not modified."""
        line = "  break: séchapper  # s'échapper\n"
        fixed, was_fixed = fix_apostrophe_line(line)

        assert was_fixed is False
        assert fixed == line


class TestFixMultilineQuotedComments:
    """Test fixing multi-line quoted comments."""

    def test_fixes_multiline_comment(self):
        """Test fixing comments that span multiple lines."""
        content = """  unicodedecodeerror: 'ошибкадекодированияунитногокода  #ошибка декодирования унитного
    кода'
"""
        fixed, count = fix_multiline_quoted_comments(content)

        assert count == 1
        # Should be on single line now
        assert (
            "ошибкадекодированияунитногокода  # ошибка декодирования унитного кода"
            in fixed
        )
        assert "'" not in fixed  # No quotes

    def test_normalizes_multiline_comment_whitespace(self):
        """Test that multi-line comment whitespace is normalized."""
        content = """  test: 'значение  #комментарий
      продолжение'
"""
        fixed, count = fix_multiline_quoted_comments(content)

        assert count == 1
        # Whitespace should be normalized to single spaces
        assert "# комментарий продолжение" in fixed

    def test_no_change_for_single_line(self):
        """Test that single-line content is unchanged."""
        content = "  test: значение  # комментарий\n"
        fixed, count = fix_multiline_quoted_comments(content)

        assert count == 0
        assert fixed == content


class TestFixFile:
    """Test the complete file fixing function."""

    def test_fixes_file_with_quoted_comments(self):
        """Test fixing a file with quoted comment issues."""
        content = """language: ru
target: python
version: '3.10'
keywords:
  and: и
  break: перебор
builtins:
  abs: 'абсолютноезначение  #абсолютное значение'
  all: все
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = fix_file(temp_path)

            assert isinstance(result, FixResult)
            assert result.fixes_applied == 1
            assert result.apostrophe_fixes == 0

            # Read back and verify
            fixed_content = temp_path.read_text(encoding="utf-8")
            assert "абсолютноезначение  # абсолютное значение" in fixed_content
            assert "'абсолютноезначение" not in fixed_content
        finally:
            temp_path.unlink()

    def test_fixes_file_with_apostrophes(self):
        """Test fixing a file with apostrophe issues."""
        content = """language: fr
target: python
version: '3.10'
keywords:
  break: s'échapper
  continue: continuer
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = fix_file(temp_path)

            assert result.apostrophe_fixes == 1
            assert result.fixes_applied == 0

            # Read back and verify
            fixed_content = temp_path.read_text(encoding="utf-8")
            assert "séchapper  # s'échapper" in fixed_content
        finally:
            temp_path.unlink()

    def test_no_changes_to_correct_file(self):
        """Test that correct files are not modified."""
        content = """language: es
target: python
version: '3.10'
keywords:
  def: definir
  class: clase
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = fix_file(temp_path)

            assert result.fixes_applied == 0
            assert result.apostrophe_fixes == 0

            # File should be unchanged
            fixed_content = temp_path.read_text(encoding="utf-8")
            assert fixed_content == content
        finally:
            temp_path.unlink()


class TestYAMLCommentSyntaxRegression:
    """Regression tests to ensure the bug doesn't recur.

    These tests verify that translation values don't contain embedded
    YAML comments (the # character inside quoted strings).
    """

    def test_translation_value_without_hash(self):
        """Test that fixed translations don't have # in the value."""
        # This represents what YAML parses - if # is inside quotes, it's in the value
        line = "  abs: 'value  #comment'\n"
        fixed, was_fixed = fix_quoted_comment_line(line)

        if was_fixed:
            # The value part (before the comment) should not contain #
            value_part = fixed.split("#")[0].split(":")[1].strip()
            assert "#" not in value_part

    def test_multiple_fixes_in_file(self):
        """Test that multiple issues in one file are all fixed."""
        content = """language: test
target: python
version: '3.10'
builtins:
  abs: 'значение1  #комментарий1'
  all: 'значение2  #комментарий2'
  any: 'значение3  #комментарий3'
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = fix_file(temp_path)

            assert result.fixes_applied == 3

            fixed_content = temp_path.read_text(encoding="utf-8")
            # All should be fixed
            assert "'значение1" not in fixed_content
            assert "'значение2" not in fixed_content
            assert "'значение3" not in fixed_content
            # All should have proper comment syntax
            assert "значение1  # комментарий1" in fixed_content
            assert "значение2  # комментарий2" in fixed_content
            assert "значение3  # комментарий3" in fixed_content
        finally:
            temp_path.unlink()


class TestValidPythonIdentifiers:
    """Test that fixed values are valid Python identifiers."""

    def test_no_spaces_in_fixed_value(self):
        """Test that fixed values don't contain spaces."""
        line = "  abs: 'абсолютноезначение  #абсолютное значение'\n"
        fixed, _ = fix_quoted_comment_line(line)

        # Extract value (between : and #)
        value = fixed.split(":")[1].split("#")[0].strip()
        assert " " not in value

    def test_no_apostrophes_in_fixed_value(self):
        """Test that fixed values don't contain apostrophes."""
        line = "  test: s'échapper\n"
        fixed, _ = fix_apostrophe_line(line)

        # Extract value (between : and #)
        value = fixed.split(":")[1].split("#")[0].strip()
        assert "'" not in value

    def test_value_is_valid_identifier(self):
        """Test that fixed values could be valid Python identifiers."""
        lines = [
            "  abs: 'абсолютноезначение  #абсолютное значение'\n",
            "  test: s'échapper\n",
        ]

        for line in lines:
            fixed, was_fixed = fix_quoted_comment_line(line)
            if not was_fixed:
                fixed, was_fixed = fix_apostrophe_line(line)

            if was_fixed:
                # Extract value
                value = fixed.split(":")[1].split("#")[0].strip()

                # Basic identifier checks (simplified - real check would use regex)
                assert value  # Not empty
                assert " " not in value  # No spaces
                assert "'" not in value  # No apostrophes
                assert "/" not in value  # No slashes
                assert (
                    "-" not in value or value.count("-") == 0
                )  # No dashes (or underscore allowed)
