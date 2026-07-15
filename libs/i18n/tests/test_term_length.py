"""Tests for the descriptions-as-terms length rule (``check_term_length``).

A pack value is a TERM, not a definition. Machine translation occasionally emits
a sentence-length gloss ("isinstance is used to check whether an object is an
instance of a class or a tuple of classes…") in place of a short native term.
Those are valid Python identifiers, so the safety checks pass them — but they are
a quality defect. This rule flags them as WARNINGS (advisory), surfacing them for
native review without blocking the gate (which fails on errors only).
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.schema_validator import MAX_TERM_LENGTH


def _schema(language: str, **sections: dict[str, str]) -> LanguagePackSchema:
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version="3.13",
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        reserved_words=sections.get("reserved_words", {}),
        operators=sections.get("operators", {}),
        standard_library=sections.get("standard_library", {}),
        cultural_notes=[],
        metadata=None,
    )


def test_short_term_passes() -> None:
    schema = _schema("en", builtins={"len": "length", "abs": "absolutewert"})
    assert SchemaValidator.check_term_length(schema) == []


def test_sentence_length_value_is_flagged_as_a_warning() -> None:
    sentence = "e" * (MAX_TERM_LENGTH + 5)
    schema = _schema("th", builtins={"isinstance": sentence})
    findings = SchemaValidator.check_term_length(schema)
    assert len(findings) == 1
    assert findings[0].code == "descriptions-as-terms"
    assert findings[0].severity == "warning"
    assert findings[0].location == "builtins.isinstance"


def test_threshold_is_inclusive() -> None:
    # Exactly MAX_TERM_LENGTH-1 passes; exactly MAX_TERM_LENGTH is flagged.
    schema_ok = _schema("en", builtins={"len": "a" * (MAX_TERM_LENGTH - 1)})
    assert SchemaValidator.check_term_length(schema_ok) == []
    schema_bad = _schema("en", builtins={"len": "a" * MAX_TERM_LENGTH})
    assert len(SchemaValidator.check_term_length(schema_bad)) == 1


def test_soft_keyword_star_is_not_counted() -> None:
    # A value at the limit plus a soft-keyword '*' must measure the core only.
    core = "a" * (MAX_TERM_LENGTH - 1)
    schema = _schema("es", keywords={"match*": core + "*"})
    assert SchemaValidator.check_term_length(schema) == []


def test_length_is_code_points_not_bytes() -> None:
    # A short multi-byte native term (15 Thai code points) must not be flagged
    # just because its UTF-8 byte length exceeds the threshold.
    thai = "ก" * 15
    assert len(thai.encode("utf-8")) > MAX_TERM_LENGTH  # 45 bytes exceed...
    assert len(thai) < MAX_TERM_LENGTH  # ...but 15 code points do not
    schema = _schema("th", builtins={"len": thai})
    assert SchemaValidator.check_term_length(schema) == []  # ...code points do not
