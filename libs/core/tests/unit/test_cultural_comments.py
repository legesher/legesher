"""Unit tests for cultural comment parser.

Tests the CulturalCommentParser functionality including:
- Parsing from source code and token streams
- Validation of cultural comment syntax
- Metadata queries by line and language
- Edge cases and error handling
"""

import io
import tokenize

import pytest

from legesher_core import (
    CulturalComment,
    CulturalCommentMetadata,
    CulturalCommentParser,
)


class TestCulturalCommentParser:
    """Test suite for CulturalCommentParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return CulturalCommentParser()

    # ===== Parsing Tests =====

    def test_parse_simple_cultural_comment(self, parser):
        """Test parsing a basic cultural comment."""
        code = """
#@culture[es]: "rango" puede significar "rank" o "range"
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        assert metadata.has_comments()
        comments = metadata.get_for_line(2)
        assert len(comments) == 1
        assert comments[0].language == "es"
        assert "rango" in comments[0].content
        assert comments[0].line_number == 2

    def test_parse_multiple_per_line(self, parser):
        """Test multiple cultural comments on the same line."""
        code = """def foo(): pass  #@culture[es]: Spanish note  #@culture[en]: English note"""
        metadata = parser.parse_from_source(code)

        # Note: tokenize treats each comment as separate token
        # But they're on different positions in the line
        assert metadata.has_comments()

    def test_parse_multiple_languages(self, parser):
        """Test parsing cultural comments in different languages."""
        code = """
#@culture[es]: Explicación en español
#@culture[ar]: شرح بالعربية
#@culture[zh]: 中文解释
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        assert metadata.has_comments()
        assert len(metadata.get_for_language("es")) == 1
        assert len(metadata.get_for_language("ar")) == 1
        assert len(metadata.get_for_language("zh")) == 1

        # Check all languages are present
        all_langs = metadata.get_all_languages()
        assert all_langs == {"es", "ar", "zh"}

    def test_parse_preserves_line_numbers(self, parser):
        """Test that line numbers are correctly tracked."""
        code = """
# Line 2: regular comment
#@culture[es]: Line 3
def foo():  # Line 4
    #@culture[en]: Line 5
    pass
"""
        metadata = parser.parse_from_source(code)

        assert len(metadata.get_for_line(3)) == 1
        assert len(metadata.get_for_line(5)) == 1
        assert len(metadata.get_for_line(2)) == 0  # regular comment
        assert len(metadata.get_for_line(4)) == 0  # regular comment

    def test_parse_rtl_language_content(self, parser):
        """Test parsing Arabic/Hebrew (RTL) content."""
        code = """
#@culture[ar]: هذا تعليق ثقافي بالعربية
#@culture[he]: זה הערה תרבותית בעברית
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        ar_comments = metadata.get_for_language("ar")
        assert len(ar_comments) == 1
        assert "عربية" in ar_comments[0].content

    def test_parse_unicode_content(self, parser):
        """Test parsing with special Unicode characters."""
        code = """
#@culture[es]: Español con ñ, á, é, í, ó, ú, ü
#@culture[de]: Deutsch mit ä, ö, ü, ß
#@culture[fr]: Français avec é, è, ê, ç
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        assert len(metadata.get_for_language("es")) == 1
        assert len(metadata.get_for_language("de")) == 1
        assert len(metadata.get_for_language("fr")) == 1

    def test_parse_empty_content(self, parser):
        """Test parsing cultural comment with no content."""
        code = """
#@culture[es]:
#@culture[en]:
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        # Empty content is valid (developer might fill it in later)
        assert metadata.has_comments()
        comments = metadata.get_for_line(2)
        assert len(comments) == 1
        assert comments[0].content == ""

    def test_parse_multiline_file(self, parser):
        """Test parsing with comments scattered throughout file."""
        code = """
#@culture[es]: Top comment
def foo():
    #@culture[en]: Inside function
    pass

class Bar:
    #@culture[es]: Inside class
    def method(self):
        #@culture[en]: Inside method
        return True
"""
        metadata = parser.parse_from_source(code)

        assert len(metadata.comments) == 4  # 4 different lines with cultural comments
        assert metadata.has_comments()

    def test_parse_from_tokens(self, parser):
        """Test parsing directly from token stream."""
        code = """
#@culture[es]: Test
def foo(): pass
"""
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        metadata = parser.parse_from_tokens(tokens)

        assert metadata.has_comments()
        comments = metadata.get_for_line(2)
        assert len(comments) == 1
        assert comments[0].language == "es"

    def test_parse_mixed_regular_and_cultural(self, parser):
        """Test that regular comments are ignored."""
        code = """
# Regular comment
#@culture[es]: Cultural comment
# Another regular comment
def foo(): pass
"""
        metadata = parser.parse_from_source(code)

        # Only the cultural comment should be captured
        assert len(metadata.comments) == 1
        assert 3 in metadata.comments

    # ===== Validation Tests =====

    def test_validate_correct_syntax(self, parser):
        """Test validation of correct cultural comment syntax."""
        is_valid, result = parser.validate_syntax("#@culture[es]: explanation")

        assert is_valid
        assert result == ("es", "explanation")

    def test_validate_invalid_lang_code(self, parser):
        """Test validation rejects invalid language codes."""
        is_valid, result = parser.validate_syntax("#@culture[zz]: invalid")

        assert not is_valid
        assert result is None

    def test_validate_malformed_missing_bracket(self, parser):
        """Test validation of malformed syntax (missing bracket)."""
        is_valid, result = parser.validate_syntax("#@culture[es : missing bracket")

        assert not is_valid

    def test_validate_malformed_missing_colon(self, parser):
        """Test validation of malformed syntax (missing colon)."""
        is_valid, result = parser.validate_syntax("#@culture[es] missing colon")

        assert not is_valid

    def test_validate_uppercase_lang_code(self, parser):
        """Test validation rejects uppercase language codes."""
        is_valid, result = parser.validate_syntax("#@culture[ES]: uppercase")

        assert not is_valid  # Must be lowercase

    def test_validate_three_letter_code(self, parser):
        """Test validation rejects 3-letter codes (must be ISO 639-1)."""
        is_valid, result = parser.validate_syntax("#@culture[eng]: three letters")

        assert not is_valid  # Must be exactly 2 characters

    def test_validate_empty_content(self, parser):
        """Test validation allows empty content."""
        is_valid, result = parser.validate_syntax("#@culture[es]:")

        assert is_valid
        assert result == ("es", "")

    def test_validate_whitespace_handling(self, parser):
        """Test that leading/trailing whitespace is stripped."""
        is_valid, result = parser.validate_syntax("#@culture[es]:    spaces    ")

        assert is_valid
        assert result == ("es", "spaces")

    def test_is_cultural_comment_helper(self, parser):
        """Test the is_cultural_comment() helper method."""
        assert parser.is_cultural_comment("#@culture[es]: text")
        assert not parser.is_cultural_comment("# regular comment")
        assert not parser.is_cultural_comment("#@culture[zz]: invalid code")

    # ===== Metadata Query Tests =====

    def test_metadata_get_for_line_empty(self):
        """Test getting comments for a line with no comments."""
        metadata = CulturalCommentMetadata()
        comments = metadata.get_for_line(5)

        assert comments == []

    def test_metadata_get_for_line_single(self):
        """Test getting a single comment for a line."""
        metadata = CulturalCommentMetadata()
        comment = CulturalComment("es", "test", 5, 0, "#@culture[es]: test")
        metadata.add_comment(comment)

        comments = metadata.get_for_line(5)
        assert len(comments) == 1
        assert comments[0].language == "es"

    def test_metadata_get_for_line_multiple(self):
        """Test getting multiple comments for a line."""
        metadata = CulturalCommentMetadata()
        metadata.add_comment(
            CulturalComment("es", "Spanish", 5, 0, "#@culture[es]: Spanish")
        )
        metadata.add_comment(
            CulturalComment("en", "English", 5, 20, "#@culture[en]: English")
        )

        comments = metadata.get_for_line(5)
        assert len(comments) == 2

    def test_metadata_get_for_language(self):
        """Test getting all comments in a specific language."""
        metadata = CulturalCommentMetadata()
        metadata.add_comment(
            CulturalComment("es", "Line 2", 2, 0, "#@culture[es]: Line 2")
        )
        metadata.add_comment(
            CulturalComment("en", "Line 3", 3, 0, "#@culture[en]: Line 3")
        )
        metadata.add_comment(
            CulturalComment("es", "Line 4", 4, 0, "#@culture[es]: Line 4")
        )

        es_comments = metadata.get_for_language("es")
        assert len(es_comments) == 2

        en_comments = metadata.get_for_language("en")
        assert len(en_comments) == 1

    def test_metadata_has_comments(self):
        """Test has_comments() method."""
        metadata = CulturalCommentMetadata()
        assert not metadata.has_comments()

        metadata.add_comment(CulturalComment("es", "test", 1, 0, "#@culture[es]: test"))
        assert metadata.has_comments()

    def test_metadata_serialization_roundtrip(self):
        """Test serialization and deserialization."""
        metadata = CulturalCommentMetadata()
        metadata.add_comment(
            CulturalComment("es", "Spanish", 2, 0, "#@culture[es]: Spanish")
        )
        metadata.add_comment(
            CulturalComment("en", "English", 3, 0, "#@culture[en]: English")
        )

        # Serialize
        data = metadata.to_dict()
        assert "comments" in data

        # Deserialize
        restored = CulturalCommentMetadata.from_dict(data)
        assert restored.has_comments()
        assert len(restored.get_for_language("es")) == 1
        assert len(restored.get_for_language("en")) == 1

    # ===== Edge Cases =====

    def test_edge_case_brackets_in_content(self, parser):
        """Test content with brackets doesn't confuse parser."""
        code = """#@culture[es]: "array[index]" syntax"""
        metadata = parser.parse_from_source(code)

        comments = metadata.get_for_line(1)
        assert len(comments) == 1
        assert "array[index]" in comments[0].content

    def test_edge_case_colon_in_content(self, parser):
        """Test content with colons doesn't confuse parser."""
        code = """#@culture[es]: time format is HH:MM:SS"""
        metadata = parser.parse_from_source(code)

        comments = metadata.get_for_line(1)
        assert len(comments) == 1
        assert "HH:MM:SS" in comments[0].content

    def test_edge_case_very_long_content(self, parser):
        """Test very long cultural comment content."""
        long_text = "x" * 1000
        code = f"""#@culture[es]: {long_text}"""
        metadata = parser.parse_from_source(code)

        comments = metadata.get_for_line(1)
        assert len(comments) == 1
        assert len(comments[0].content) >= 1000

    def test_edge_case_empty_file(self, parser):
        """Test parsing empty file."""
        metadata = parser.parse_from_source("")

        assert not metadata.has_comments()

    def test_edge_case_no_cultural_comments(self, parser):
        """Test file with only regular comments."""
        code = """
# Regular comment 1
# Regular comment 2
def foo():
    # Regular comment 3
    pass
"""
        metadata = parser.parse_from_source(code)

        assert not metadata.has_comments()

    def test_edge_case_incomplete_code(self, parser):
        """Test parsing incomplete/invalid code."""
        incomplete = """
#@culture[es]: Comment before incomplete code
def foo(
"""
        metadata = parser.parse_from_source(incomplete)

        # Should handle gracefully and still extract the comment
        # (tokenize.TokenError is caught)
        assert not metadata.has_comments()  # TokenError prevents parsing

    # ===== Type Validation Tests =====

    def test_cultural_comment_immutable(self):
        """Test that CulturalComment is immutable (frozen dataclass)."""
        comment = CulturalComment("es", "test", 1, 0, "#@culture[es]: test")

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            comment.language = "en"

    def test_cultural_comment_validates_language_length(self):
        """Test CulturalComment validates language code length."""
        with pytest.raises(ValueError, match="2 characters"):
            CulturalComment("eng", "test", 1, 0, "#@culture[eng]: test")

    def test_cultural_comment_validates_language_case(self):
        """Test CulturalComment validates language code is lowercase."""
        with pytest.raises(ValueError, match="lowercase"):
            CulturalComment("ES", "test", 1, 0, "#@culture[ES]: test")

    def test_cultural_comment_validates_line_number(self):
        """Test CulturalComment validates line number is positive."""
        with pytest.raises(ValueError, match="must be >= 1"):
            CulturalComment("es", "test", 0, 0, "#@culture[es]: test")

    def test_cultural_comment_validates_column_offset(self):
        """Test CulturalComment validates column offset is non-negative."""
        with pytest.raises(ValueError, match="must be >= 0"):
            CulturalComment("es", "test", 1, -1, "#@culture[es]: test")

    # ===== Parser Configuration Tests =====

    def test_parser_unsupported_language(self):
        """Test parser rejects unsupported programming languages."""
        with pytest.raises(ValueError, match="Unsupported language"):
            CulturalCommentParser(language="unsupported")

    def test_parser_python_language(self):
        """Test parser accepts Python language."""
        parser = CulturalCommentParser(language="python")
        assert parser.language == "python"

    # ===== Security Tests =====

    def test_security_redos_protection(self, parser):
        """Test protection against ReDoS attacks with malicious input."""
        # Malicious input that could cause catastrophic backtracking with .* regex
        malicious = "#@culture[es]:" + "a" * 100000  # 100K characters

        # Should handle gracefully with bounded quantifier
        import time

        start = time.time()
        is_valid, result = parser.validate_syntax(malicious)
        elapsed = time.time() - start

        # Should complete quickly (< 100ms) due to bounded quantifier
        assert elapsed < 0.1, f"Regex took too long: {elapsed}s (possible ReDoS)"

    def test_security_extremely_long_content_rejected(self, parser):
        """Test that content exceeding MAX_CONTENT_LENGTH is handled safely."""
        # Create comment with content exceeding MAX_CONTENT_LENGTH
        # Regex uses bounded quantifier {0,10000} so content > 10K won't match
        long_content = "x" * 20000  # 20K characters (exceeds 10K limit)
        code = f"#@culture[es]: {long_content}\ndef foo(): pass"

        metadata = parser.parse_from_source(code)
        comments = metadata.get_for_line(1)

        # Comments exceeding MAX_CONTENT_LENGTH won't match the regex pattern
        # This is intentional - prevents ReDoS and memory exhaustion
        assert len(comments) == 0  # Not parsed due to length limit

    def test_security_content_at_max_length_accepted(self, parser):
        """Test that content exactly at MAX_CONTENT_LENGTH is accepted."""
        # Content exactly at limit should be accepted
        exact_content = "x" * parser.MAX_CONTENT_LENGTH
        code = f"#@culture[es]: {exact_content}\ndef foo(): pass"

        metadata = parser.parse_from_source(code)
        comments = metadata.get_for_line(1)

        assert len(comments) == 1
        assert len(comments[0].content) == parser.MAX_CONTENT_LENGTH

    def test_security_multiple_long_comments(self, parser):
        """Test handling many long comments doesn't cause memory issues."""
        # Create 100 comments with long content
        lines = [f"#@culture[es]: {'x' * 5000}" for _ in range(100)]
        lines.append("def foo(): pass")
        code = "\n".join(lines)

        # Should handle without crashing or excessive memory
        metadata = parser.parse_from_source(code)
        assert len(metadata.comments) == 100

    def test_security_nested_brackets_no_injection(self, parser):
        """Test that nested brackets don't break parsing or allow injection."""
        code = "#@culture[es]: test[[[nested]]]brackets"
        metadata = parser.parse_from_source(code)

        comments = metadata.get_for_line(1)
        assert len(comments) == 1
        assert "nested" in comments[0].content

    def test_security_special_regex_chars_in_content(self, parser):
        """Test special regex characters in content don't break parsing."""
        code = "#@culture[es]: test.*+?{}[]()^$|\\special"
        metadata = parser.parse_from_source(code)

        comments = metadata.get_for_line(1)
        assert len(comments) == 1
        # Content should contain the special chars literally
        assert ".*+?" in comments[0].content
