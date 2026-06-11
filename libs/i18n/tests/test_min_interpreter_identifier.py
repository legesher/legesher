"""Tests for the minimum-interpreter XID check.

Synthetic fixtures. The Sinhala ZWJ trap: ``virama + ZWJ + consonant`` is a
valid identifier on CPython 3.13+ (Unicode 13.0 XID) but a ``SyntaxError`` on
3.10-3.12. The check is static (never calls ``compile()``): a value using a
post-Unicode-13 XID character is flagged when the pack's declared minimum
interpreter is < 3.13.
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.script_policy import ZWJ


def _schema(
    language: str,
    version: str,
    *,
    python_version_min: str | None = None,
    **sections,
) -> LanguagePackSchema:
    """Build a schema bypassing Pydantic, optionally setting metadata min."""
    metadata = None
    if python_version_min is not None:
        from legesher_i18n.schema_validator import LanguagePackMetadata

        metadata = LanguagePackMetadata(python_version_min=python_version_min)
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version=version,
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        reserved_words=sections.get("reserved_words", {}),
        operators=sections.get("operators", {}),
        standard_library=sections.get("standard_library", {}),
        cultural_notes=[],
        metadata=metadata,
    )


class TestMinInterpreterIdentifier:
    """ZWJ-bearing values require a declared minimum interpreter of 3.13+."""

    def test_zwj_value_with_min_310_is_flagged(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.10", python_version_min="3.10", keywords={"x": value})
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "si")
        assert len(findings) == 1
        assert findings[0].code == "min-interpreter-xid"
        assert findings[0].location == "keywords.x"

    def test_zwj_value_with_min_313_passes(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.13", python_version_min="3.13", keywords={"x": value})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_zwj_value_with_min_314_passes(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.14", python_version_min="3.14", keywords={"x": value})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_plain_value_with_min_310_passes(self) -> None:
        # No ZWJ -> nothing version-sensitive -> always fine.
        schema = _schema("si", "3.10", python_version_min="3.10", keywords={"x": "අය"})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_min_version_argument_overrides_metadata(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.13", python_version_min="3.13", keywords={"x": value})
        # Explicit override to an old interpreter re-flags it.
        findings = SchemaValidator.check_min_interpreter_identifier(
            schema, "si", min_version="3.11"
        )
        assert len(findings) == 1

    def test_falls_back_to_pack_version_when_no_metadata(self) -> None:
        value = f"අ{ZWJ}ය"
        # No metadata; pack version is 3.10 -> flagged.
        schema = _schema("si", "3.10", keywords={"x": value})
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "si")
        assert len(findings) == 1

    def test_version_at_least_helper(self) -> None:
        assert SchemaValidator._version_at_least("3.13", 3, 13) is True
        assert SchemaValidator._version_at_least("3.14", 3, 13) is True
        assert SchemaValidator._version_at_least("3.12", 3, 13) is False
        assert SchemaValidator._version_at_least("3.10", 3, 13) is False
        assert SchemaValidator._version_at_least(None, 3, 13) is False
        assert SchemaValidator._version_at_least("garbage", 3, 13) is False
