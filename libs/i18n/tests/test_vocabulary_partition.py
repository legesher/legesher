"""Tests for the pack vocabulary partition (CORE-1396).

``symbols`` (what a Python symbol is CALLED in a language) and
``variable_conventions`` (the idiomatic short names) are vocabulary, not
rules, so they live in the packs rather than the style guides. What must
hold:

1. The canonical inventory is internally consistent and its own English
   values pass the publish gate — English is seeded from it, never
   generated, so a bad inventory entry would ship unexamined.
2. The publish gate applies two different regimes: prose for ``symbols``,
   real identifiers for ``variable_conventions``. Each rejects what the
   other must allow.
3. The pack schema accepts both sections, defaults them empty (so every
   shipped pack validates unchanged), and routes each through its own
   validator.
4. The strict safety layer catches the failures that matter for advice a
   developer types: keywords, shadowed term surfaces, partial sections.
5. The loader carries both sections through construction and ``extends``
   inheritance.
6. The database enforces the gate at the write boundary, and the exporter
   is all-or-nothing per section.
7. The DB gate and pack-load return the SAME verdict for every value —
   asserted directly (gate verdict == pack-load verdict), because the two
   once disagreed over ``except*`` and both silently passed fullwidth
   ``ｉ`` (see ``TestLayerAgreement``).
"""

from __future__ import annotations

import keyword

import pytest
from pydantic import ValidationError

from legesher_i18n.db import TranslationDatabase
from legesher_i18n.pack_loader import LanguagePack, LanguagePackLoader
from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from tests.interpreter_gaps import IDENTIFIER_RULES_ARE_UNICODE_15_1
from legesher_i18n.selection import (
    MAX_SYMBOL_NAME_LENGTH,
    vocabulary_value_error,
)
from legesher_i18n.vocabulary_definitions import (
    SYMBOLS,
    VARIABLE_CONVENTIONS,
    VOCABULARY_SECTIONS,
    english_values,
    slugs_for_section,
)


def make_schema(**overrides) -> LanguagePackSchema:
    data = {
        "language": "es",
        "target": "python",
        "version": "3.10",
        **overrides,
    }
    return LanguagePackSchema(**data)


def complete(section: str, **overrides: str) -> dict[str, str]:
    """A complete section, English-valued, with selected slugs overridden."""
    values = dict(english_values(section))
    values.update(overrides)
    return values


class TestCanonicalInventory:
    def test_slugs_are_unique_within_each_section(self) -> None:
        for section in VOCABULARY_SECTIONS:
            slugs = slugs_for_section(section)
            assert len(slugs) == len(set(slugs)), f"{section} has duplicate slugs"

    def test_slugs_are_plain_ascii_identifiers(self) -> None:
        # Slugs are YAML keys and DB keys; anything needing quoting would be
        # a standing hazard (this is why glyphs are not the keys).
        for section in VOCABULARY_SECTIONS:
            for slug in slugs_for_section(section):
                assert slug.isascii() and slug.isidentifier(), slug

    def test_every_english_value_passes_its_own_publish_gate(self) -> None:
        # English is SEEDED from this inventory, so a bad entry here would
        # reach a shipped pack without any model or reviewer in the way.
        for section in VOCABULARY_SECTIONS:
            for slug, value in english_values(section).items():
                assert vocabulary_value_error(section, slug, value) is None, (
                    f"{section}.{slug} = {value!r}"
                )

    def test_english_variable_conventions_are_distinct(self) -> None:
        values = list(english_values("variable_conventions").values())
        assert len(values) == len(set(values))

    def test_english_variable_conventions_are_not_keywords(self) -> None:
        for slug, value in english_values("variable_conventions").items():
            assert value not in keyword.kwlist, f"{slug} = {value}"

    def test_symbols_without_a_glyph_are_still_nameable(self) -> None:
        # indentation / newline / space have no printable form and are named
        # by error messages constantly; that is why they are in scope.
        glyphless = {entry.slug for entry in SYMBOLS if entry.glyph is None}
        assert {"indentation", "newline", "space"} <= glyphless

    def test_every_entry_carries_prompt_context(self) -> None:
        for entry in (*SYMBOLS, *VARIABLE_CONVENTIONS):
            assert entry.role.strip(), entry.slug


class TestPublishGate:
    def test_symbol_names_may_contain_spaces(self) -> None:
        # The whole point of the separate regime: the identifier gate would
        # reject every correct multi-word symbol name.
        assert vocabulary_value_error("symbols", "colon", "dos puntos") is None

    def test_symbol_name_rejects_padding(self) -> None:
        assert vocabulary_value_error("symbols", "colon", " dos puntos ") is not None

    def test_symbol_name_rejects_empty(self) -> None:
        assert vocabulary_value_error("symbols", "colon", "") is not None

    def test_symbol_name_rejects_bidi_control(self) -> None:
        error = vocabulary_value_error(
            "symbols", "colon", "dos" + chr(0x202E) + "puntos"
        )
        assert error is not None and "U+202E" in error

    def test_symbol_name_rejects_a_definition(self) -> None:
        definition = (
            "the mark that opens the indented block of a def, class, if, "
            "for, while or with statement"
        )
        error = vocabulary_value_error("symbols", "colon", definition)
        assert error is not None and str(MAX_SYMBOL_NAME_LENGTH) in error

    def test_variable_convention_rejects_prose(self) -> None:
        error = vocabulary_value_error(
            "variable_conventions", "loop_index", "el contador"
        )
        assert error is not None and "identifier" in error

    def test_variable_convention_accepts_the_throwaway_underscore(self) -> None:
        # `_` is a soft keyword, which is exactly why the generic
        # keyword-collision check is not reused for this section.
        assert vocabulary_value_error("variable_conventions", "throwaway", "_") is None

    def test_variable_convention_rejects_a_313_only_character(self) -> None:
        # ZWJ is XID_Continue from CPython 3.13. A pack translation can be
        # tiered into a 3.13 overlay; advice has no overlay to live in.
        # Before Unicode 15.1 the value is no identifier at all, and the
        # rejection says so instead.
        error = vocabulary_value_error(
            "variable_conventions", "loop_index", "a" + chr(0x200D) + "b"
        )
        reason = (
            "3.13"
            if IDENTIFIER_RULES_ARE_UNICODE_15_1
            else "not a valid Python identifier"
        )
        assert error is not None and reason in error

    def test_unknown_section_is_reported_not_silently_passed(self) -> None:
        assert vocabulary_value_error("cultural_notes", "x", "y") is not None

    def test_symbol_name_rejects_a_trailing_star(self) -> None:
        # A name is the word for a glyph, not the glyph; the trailing star
        # is the term sections' soft-keyword marker and never enters this
        # partition.
        error = vocabulary_value_error("symbols", "asterisk", "hoshijirushi*")
        assert error is not None and "*" in error


class TestLayerAgreement:
    """The DB gate and pack-load must return the SAME verdict (CORE-1396 review).

    The gate is :func:`selection.vocabulary_value_error` — what
    ``TranslationDatabase.set_selected_vocabulary`` enforces at the write
    boundary. Pack-load is pydantic validation of ``LanguagePackSchema``.
    Before the fix the two disagreed twice over ``variable_conventions``:

    * the literal ``'except*'`` PASSED the gate (the ``SOFT_KEYWORDS``
      short-circuit in ``_is_valid_identifier`` with no source term) while
      pack-load rejected every starred value — so a generation run could
      write a selection that then corrupted pack-load;
    * the fullwidth ``'ｉ'`` passed BOTH silently, even though Python
      NFKC-folds identifiers at parse time, so the advice would recommend a
      spelling that binds a different identifier than the reader sees.

    These tests assert the verdicts directly against each other, so any
    future drift between the layers fails here by construction.
    """

    @staticmethod
    def _gate_accepts(value: str) -> bool:
        return (
            vocabulary_value_error("variable_conventions", "loop_index", value) is None
        )

    @staticmethod
    def _pack_load_accepts(value: str) -> bool:
        try:
            make_schema(variable_conventions={"loop_index": value})
        except ValidationError:
            return False
        return True

    def test_except_star_is_rejected_identically_at_both_layers(self) -> None:
        # Finding 2: the SOFT_KEYWORDS short-circuit made the DB gate accept
        # what pack-load rejects. Both must refuse it, and agree.
        assert self._gate_accepts("except*") is False
        assert self._pack_load_accepts("except*") is False
        assert self._gate_accepts("except*") == self._pack_load_accepts("except*")

    def test_fullwidth_i_is_rejected_identically_at_both_layers(self) -> None:
        # Finding 1: NFKC-unstable — CPython parses 'ｉ' as 'i', so the
        # recommended spelling would not be the identifier bound.
        assert self._gate_accepts("ｉ") is False
        assert self._pack_load_accepts("ｉ") is False
        assert self._gate_accepts("ｉ") == self._pack_load_accepts("ｉ")

    def test_sara_am_value_is_allowed_identically_at_both_layers(self) -> None:
        # The stated allowance: same posture as the term-side
        # check_normalization gate (CORE-1514). 'ตำแหน่ง' (Thai, position) is
        # NFC-stable and its only NFKC delta is SARA AM (U+0E33), which
        # CPython folds in identifiers — both spellings are one identifier,
        # legitimate orthography, no spoofing surface. Allowed at BOTH
        # layers, so the pack's own term surfaces and its advice are held to
        # one policy.
        assert self._gate_accepts("ตำแหน่ง") is True
        assert self._pack_load_accepts("ตำแหน่ง") is True

    def test_lao_analogue_stays_rejected_at_both_layers(self) -> None:
        # The allowance is deliberately Thai-SARA-AM-only, exactly as the
        # term gates cut it: Lao U+0EB3 also decomposes under NFKC but is
        # NOT in the allowance, so it must fail both layers the same way.
        assert self._gate_accepts("ຕົວຳ") is False
        assert self._pack_load_accepts("ຕົວຳ") is False

    def test_verdicts_agree_across_the_probe_set(self) -> None:
        # Accept and reject cases together: the assertion is EQUALITY of
        # verdicts, not any particular verdict, so a rule added to one
        # layer and forgotten in the other fails loudly here.
        probes = (
            "i",  # the canonical loop counter
            "_",  # soft keyword, deliberately allowed
            "idx",
            "ตำแหน่ง",  # SARA AM allowance
            "except*",  # finding 2
            "excepto*",  # any starred value, not just the literal
            "ｉ",  # finding 1
            "ﬁle",  # NFKC-unstable ligature
            "ຕົວຳ",  # Lao analogue, outside the allowance
            "el contador",  # prose
            "a‍b",  # 3.13-only XID (ZWJ)
        )
        for value in probes:
            assert self._gate_accepts(value) == self._pack_load_accepts(value), (
                f"layers disagree on {value!r}"
            )


class TestSchemaField:
    def test_both_sections_default_empty(self) -> None:
        schema = make_schema()
        assert schema.symbols == {}
        assert schema.variable_conventions == {}

    def test_symbols_accept_prose(self) -> None:
        schema = make_schema(symbols=complete("symbols", colon="dos puntos"))
        assert schema.symbols["colon"] == "dos puntos"

    def test_symbols_reject_a_padded_value(self) -> None:
        with pytest.raises(ValidationError):
            make_schema(symbols={"colon": " dos puntos "})

    def test_variable_conventions_take_the_identifier_gate(self) -> None:
        with pytest.raises(ValidationError):
            make_schema(variable_conventions={"loop_index": "el contador"})

    def test_variable_conventions_accept_an_identifier(self) -> None:
        schema = make_schema(variable_conventions=complete("variable_conventions"))
        assert schema.variable_conventions["loop_index"] == "i"


class TestSafetyLayer:
    def test_shipped_packs_are_unaffected(self) -> None:
        # No shipped pack carries either section yet. Both sections default
        # empty, so every new check runs over nothing and finds nothing.
        schema = make_schema(keywords={"def": "definir"})
        findings = SchemaValidator.validate_pack_strict(schema, "es")
        assert not [
            f
            for f in findings
            if f.location.startswith(("symbols", "variable_conventions"))
        ]

    def test_partial_section_is_an_error(self) -> None:
        schema = make_schema(symbols={"colon": "dos puntos"})
        findings = SchemaValidator.check_vocabulary_inventory(schema)
        assert any(f.code == "partial-vocabulary-section" for f in findings)

    def test_complete_section_is_clean(self) -> None:
        schema = make_schema(symbols=complete("symbols"))
        assert SchemaValidator.check_vocabulary_inventory(schema) == []

    def test_unknown_slug_is_an_error(self) -> None:
        symbols = complete("symbols")
        symbols["interrobang"] = "interrobang"
        schema = make_schema(symbols=symbols)
        findings = SchemaValidator.check_vocabulary_inventory(schema)
        assert any(f.code == "unknown-vocabulary-slug" for f in findings)

    def test_symbol_name_must_be_nfc_stable(self) -> None:
        # Decomposed "é": renders identically, compares unequal.
        schema = LanguagePackSchema.model_construct(
            language="fr",
            target="python",
            version="3.10",
            symbols={"colon": "deux-points é"},
        )
        findings = SchemaValidator.check_symbols(schema)
        assert any(f.code == "unnormalized-symbol-name" for f in findings)

    def test_convention_that_is_a_keyword_is_an_error(self) -> None:
        schema = LanguagePackSchema.model_construct(
            language="es",
            target="python",
            version="3.10",
            variable_conventions={"loop_index": "for"},
        )
        findings = SchemaValidator.check_variable_conventions(schema)
        assert any(f.code == "variable-convention-keyword" for f in findings)

    def test_convention_shadowing_a_translated_surface_is_an_error(self) -> None:
        # Recommending a name the engine rewrites is the failure mode with
        # teeth: the variable would not survive translation.
        schema = make_schema(
            keywords={"for": "por"},
            variable_conventions=complete("variable_conventions", loop_index="por"),
        )
        findings = SchemaValidator.check_variable_conventions(schema)
        assert any(f.code == "variable-convention-shadows-term" for f in findings)

    def test_convention_shadowing_a_builtin_is_only_a_warning(self) -> None:
        schema = make_schema(
            variable_conventions=complete("variable_conventions", item="list")
        )
        findings = SchemaValidator.check_variable_conventions(schema)
        shadowing = [
            f for f in findings if f.code == "variable-convention-shadows-builtin"
        ]
        assert shadowing and all(f.severity == "warning" for f in shadowing)

    def test_two_roles_sharing_a_name_is_only_a_warning(self) -> None:
        schema = make_schema(
            variable_conventions=complete("variable_conventions", coordinate_y="x")
        )
        findings = SchemaValidator.check_variable_conventions(schema)
        duplicates = [f for f in findings if f.code == "duplicate-variable-convention"]
        assert duplicates and all(f.severity == "warning" for f in duplicates)

    def test_english_inventory_validates_clean_end_to_end(self) -> None:
        schema = make_schema(
            symbols=complete("symbols"),
            variable_conventions=complete("variable_conventions"),
        )
        findings = SchemaValidator.validate_pack_strict(schema, "en")
        errors = [f for f in findings if f.severity == "error"]
        assert errors == []

    def test_vocabulary_is_outside_the_translation_section_inventory(self) -> None:
        # Deliberate: the generic checks would fight correct data here (a
        # language keeping `i` is not a script-consistency failure), and the
        # round-trip bijection does not apply to advice.
        from legesher_i18n.schema_validator import TRANSLATION_SECTIONS

        assert "symbols" not in TRANSLATION_SECTIONS
        assert "variable_conventions" not in TRANSLATION_SECTIONS

    def test_vocabulary_keys_are_allowed_by_the_data_contract(self) -> None:
        from legesher_i18n.data_contract import ALLOWED_TOP_LEVEL_KEYS

        assert {"symbols", "variable_conventions"} <= ALLOWED_TOP_LEVEL_KEYS


class TestLoader:
    def test_merge_carries_both_sections_with_override_precedence(self) -> None:
        loader = LanguagePackLoader()
        merged = loader._merge_packs(
            base={
                "symbols": {"colon": "dos puntos", "comma": "coma"},
                "variable_conventions": {"loop_index": "i"},
            },
            override={
                "symbols": {"comma": "coma decimal"},
                "variable_conventions": {"count": "n"},
            },
        )
        assert merged["symbols"] == {"colon": "dos puntos", "comma": "coma decimal"}
        assert merged["variable_conventions"] == {"loop_index": "i", "count": "n"}

    def test_shipped_python_packs_load_with_empty_vocabulary(self) -> None:
        pack = LanguagePackLoader().load("es", version="3.10")
        assert pack.symbols == {}
        assert pack.variable_conventions == {}
        assert "symbols=0" in repr(pack)
        assert "variable_conventions=0" in repr(pack)

    def test_accessors_return_none_when_the_pack_carries_no_vocabulary(self) -> None:
        pack = LanguagePack(language="es", target="python", version="3.10")
        assert pack.get_symbol_name("colon") is None
        assert pack.get_variable_convention("loop_index") is None

    def test_accessors_read_the_sections(self) -> None:
        pack = LanguagePack(
            language="es",
            target="python",
            version="3.10",
            symbols={"colon": "dos puntos"},
            variable_conventions={"loop_index": "i"},
        )
        assert pack.get_symbol_name("colon") == "dos puntos"
        assert pack.get_variable_convention("loop_index") == "i"


@pytest.fixture
def db(tmp_path) -> TranslationDatabase:
    database = TranslationDatabase(db_path=str(tmp_path / "vocab.db"))
    conn = database._get_connection()
    conn.execute(
        "INSERT INTO languages (code, name, native_name) VALUES "
        "('es', 'Spanish', 'Espanol')"
    )
    conn.commit()
    yield database
    database.close()


class TestDatabase:
    def test_entry_creation_is_idempotent_and_converges(self, db) -> None:
        first = db.get_or_create_vocabulary_entry(
            "symbols", "colon", "colon", role="old", sort_order=1
        )
        second = db.get_or_create_vocabulary_entry(
            "symbols", "colon", "colon", role="new", sort_order=2
        )
        assert first == second
        entry = db.get_vocabulary_entries(section="symbols")[0]
        assert entry["role"] == "new" and entry["sort_order"] == 2

    def test_gate_runs_at_the_write_boundary(self, db) -> None:
        entry_id = db.get_or_create_vocabulary_entry("symbols", "colon", "colon")
        with pytest.raises(ValueError, match="whitespace"):
            db.set_selected_vocabulary(entry_id, "es", " dos puntos ")

    def test_gate_rejects_prose_for_a_variable_convention(self, db) -> None:
        entry_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "loop_index", "i"
        )
        with pytest.raises(ValueError, match="identifier"):
            db.set_selected_vocabulary(entry_id, "es", "el contador")

    def test_write_boundary_rejects_the_literal_except_star(self, db) -> None:
        # Finding 2 at the REAL write boundary: before the fix this write
        # succeeded (SOFT_KEYWORDS short-circuit), and the exported pack
        # then failed pack-load — a selection that corrupts the pack.
        entry_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "loop_index", "i"
        )
        with pytest.raises(ValueError, match=r"\*"):
            db.set_selected_vocabulary(entry_id, "es", "except*")

    def test_write_boundary_rejects_an_nfkc_unstable_name(self, db) -> None:
        # Finding 1 at the REAL write boundary: fullwidth 'ｉ' parses as
        # 'i', so the stored advice would be silently wrong.
        entry_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "loop_index", "i"
        )
        with pytest.raises(ValueError, match="normalization"):
            db.set_selected_vocabulary(entry_id, "es", "ｉ")

    def test_write_boundary_honors_the_sara_am_allowance(self, db) -> None:
        # The allowance is policy, not an oversight: NFC-stable, sara-am-only
        # values pass here exactly as they pass the term-side gates.
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES "
            "('th', 'Thai', 'Thai')"
        )
        conn.commit()
        entry_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "position", "pos"
        )
        db.set_selected_vocabulary(entry_id, "th", "ตำแหน่ง")
        rows = db.get_selected_vocabulary("th")
        assert len(rows) == 1 and rows[0]["value"] == "ตำแหน่ง"

    def test_selection_is_one_per_entry_and_language(self, db) -> None:
        entry_id = db.get_or_create_vocabulary_entry("symbols", "colon", "colon")
        db.set_selected_vocabulary(entry_id, "es", "dos puntos")
        db.set_selected_vocabulary(entry_id, "es", "dos-puntos")
        rows = db.get_selected_vocabulary("es")
        assert len(rows) == 1 and rows[0]["value"] == "dos-puntos"

    def test_candidate_pool_keeps_both_answers(self, db) -> None:
        # The pool is dirty-tolerant and additive: a re-generation must be
        # comparable against the previous one, not overwrite it.
        entry_id = db.get_or_create_vocabulary_entry("symbols", "colon", "colon")
        db.add_vocabulary_translation(entry_id, "es", "dos puntos", source="claude")
        db.add_vocabulary_translation(entry_id, "es", "dos-puntos", source="aya")
        assert len(db.get_vocabulary_translations(language_code="es")) == 2

    def test_unknown_entry_id_is_refused(self, db) -> None:
        with pytest.raises(ValueError, match="No vocabulary entry"):
            db.set_selected_vocabulary(9999, "es", "dos puntos")

    def test_coverage_reports_per_section_counts(self, db) -> None:
        symbol_id = db.get_or_create_vocabulary_entry("symbols", "colon", "colon")
        convention_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "loop_index", "i"
        )
        db.set_selected_vocabulary(symbol_id, "es", "dos puntos")
        db.set_selected_vocabulary(convention_id, "es", "i")
        assert db.get_vocabulary_coverage()["es"] == {
            "symbols": 1,
            "variable_conventions": 1,
        }

    def test_stats_report_the_partition(self, db) -> None:
        stats = db.get_stats()
        assert "vocabulary_entries_count" in stats
        assert "selected_vocabulary_count" in stats
