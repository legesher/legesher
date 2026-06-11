"""Tests for the live-keyword/builtin collision check.

Synthetic fixtures. A translation must not equal — nor NFKC-fold to — a real
Python keyword, soft keyword, or builtin, unless it is that key's own English
target. Catches active-keyword collisions (a ``globals`` value rendered as
``global``) and fullwidth spoofs (``ｉｆ`` NFKC-folds to ``if``).
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator

FULLWIDTH_IF = "ｉｆ"  # U+FF49 U+FF46 — NFKC-folds to "if"


def _schema(
    language: str = "xx", version: str = "3.13", **sections
) -> LanguagePackSchema:
    """Build a schema bypassing Pydantic field validation (see other suites)."""
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
        metadata=None,
    )


class TestKeywordCollisions:
    """A translation must not be another live keyword/builtin."""

    def test_distinct_translations_pass(self) -> None:
        schema = _schema(keywords={"def": "definir", "class": "clase"})
        assert SchemaValidator.check_keyword_collisions(schema) == []

    def test_own_keyword_translation_is_allowed(self) -> None:
        # The English identity mapping `in` -> `in` is this key's own target.
        schema = _schema(keywords={"in": "in"})
        assert SchemaValidator.check_keyword_collisions(schema) == []

    def test_globals_rendered_as_global_is_flagged(self) -> None:
        # de/id/ms failure mode: builtins.globals translated to the keyword
        # `global`.
        schema = _schema(builtins={"globals": "global"})
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert len(findings) == 1
        assert findings[0].code == "keyword-collision"
        assert findings[0].location == "builtins.globals"

    def test_print_rendered_as_in_is_flagged(self) -> None:
        # vi failure mode: builtins.print translated to the keyword `in`.
        schema = _schema(builtins={"print": "in"})
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert len(findings) == 1
        assert "in" in findings[0].message

    def test_except_star_collision_is_flagged(self) -> None:
        # no/tr failure mode: except* translated to bare `except`.
        schema = _schema(keywords={"except*": "except"})
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert len(findings) == 1
        assert findings[0].location == "keywords.except*"

    def test_except_star_own_translation_with_star_is_allowed(self) -> None:
        # except* -> except* is its own target (base `except` == base key).
        schema = _schema(keywords={"except*": "except*"})
        assert SchemaValidator.check_keyword_collisions(schema) == []

    def test_fullwidth_if_spoof_is_flagged(self) -> None:
        # Fullwidth 'ｉｆ' is isidentifier()-True and NFKC-folds to `if`.
        schema = _schema(keywords={"def": FULLWIDTH_IF})
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert len(findings) == 1
        assert findings[0].code == "keyword-collision"

    def test_builtin_name_collision_is_flagged(self) -> None:
        # A keyword translated to the builtin `len`.
        schema = _schema(keywords={"def": "len"})
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert len(findings) == 1

    def test_one_finding_per_colliding_value(self) -> None:
        schema = _schema(
            builtins={"globals": "global", "print": "in", "ok": "imprimir"}
        )
        findings = SchemaValidator.check_keyword_collisions(schema)
        assert {f.location for f in findings} == {
            "builtins.globals",
            "builtins.print",
        }
