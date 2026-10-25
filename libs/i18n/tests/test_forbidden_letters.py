"""Same-script orthography leakage: ``ScriptPolicy.forbidden_letters``.

The script gate cannot see a Russian ``ы`` inside a Ukrainian value: both are
Cyrillic, which Ukrainian allows. The forbidden-letter denylist closes that
gap, and it is enforced at every layer a generated value passes through on
its way into a pack: the selection rule, the ``set_selected`` and
``set_selected_vocabulary`` write boundaries, the exporter's selection load,
and the strict pack audit.

The mechanism tests run against a synthetic policy (``zz``, Cyrillic with
``ы`` forbidden) so they hold whatever the shipped table contains. The policy
table itself is checked from the real ``SCRIPT_POLICIES``, so a language that
gains a denylist is covered without editing this file. The decomposed-input
cases use ``е`` + U+0308 COMBINING DIAERESIS: Latin proves nothing here.
"""

from __future__ import annotations

import unicodedata

import pytest

from legesher_i18n.schema_validator import (
    LanguagePackMetadata,
    LanguagePackSchema,
    SchemaValidator,
)
from legesher_i18n.script_policy import (
    SCRIPT_POLICIES,
    ScriptPolicy,
    forbidden_letters_in,
    scripts_of,
)
from legesher_i18n.selection import (
    is_valid_pack_value,
    select_canonical,
    vocabulary_value_error,
)

#: Every (language, forbidden letter) pair the shipped policy table declares.
_DENYLISTED = sorted(
    (code, letter)
    for code, policy in SCRIPT_POLICIES.items()
    for letter in policy.forbidden_letters
)

#: The synthetic language the mechanism tests police.
ZZ = "zz"
ZZ_FORBIDDEN = frozenset("ыЫёЁ")


@pytest.fixture
def zz_policy(monkeypatch):
    """Register a Cyrillic policy that forbids ы and ё, for this test only."""
    monkeypatch.setitem(
        SCRIPT_POLICIES,
        ZZ,
        ScriptPolicy(scripts=frozenset({"Cyrillic"}), forbidden_letters=ZZ_FORBIDDEN),
    )


def _pack(language: str, **sections) -> LanguagePackSchema:
    """Build a merged-pack schema, bypassing Pydantic field validation."""
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version="3.13",
        extends=None,
        keywords={},
        builtins=sections.get("builtins", {}),
        exceptions={},
        implicit_params={},
        operators={},
        standard_library={},
        symbols=sections.get("symbols", {}),
        variable_conventions=sections.get("variable_conventions", {}),
        cultural_notes=[],
        metadata=LanguagePackMetadata(python_version_min="3.13"),
    )


class TestPolicyTable:
    @pytest.mark.parametrize(("code", "letter"), _DENYLISTED)
    def test_each_letter_belongs_to_the_policy_scripts(self, code, letter) -> None:
        # A letter from another script is the script gate's job; listing one
        # here would be a typo, not extra protection.
        assert scripts_of(letter) <= SCRIPT_POLICIES[code].scripts

    @pytest.mark.parametrize(("code", "letter"), _DENYLISTED)
    def test_each_letter_is_listed_in_both_cases(self, code, letter) -> None:
        forbidden = SCRIPT_POLICIES[code].forbidden_letters
        assert letter.upper() in forbidden and letter.lower() in forbidden

    @pytest.mark.parametrize("bad", ["ыы", "1", "_", "̈"])
    def test_constructor_refuses_a_non_letter(self, bad) -> None:
        with pytest.raises(ValueError, match="single letters"):
            ScriptPolicy(
                scripts=frozenset({"Cyrillic"}), forbidden_letters=frozenset([bad])
            )


@pytest.mark.usefixtures("zz_policy")
class TestHelper:
    @pytest.mark.parametrize("letter", sorted(ZZ_FORBIDDEN))
    def test_flags_the_letter_mid_word(self, letter) -> None:
        assert forbidden_letters_in(f"р{letter}ба", ZZ) == [letter]

    def test_decomposed_letter_is_caught_as_the_letter_it_renders(self) -> None:
        # е + U+0308 COMBINING DIAERESIS renders as ё; NFC composes it.
        decomposed = unicodedata.normalize("NFD", "ёж")
        assert "̈" in decomposed
        assert forbidden_letters_in(decomposed, ZZ) == ["ё"]

    def test_allowed_letters_pass(self) -> None:
        assert forbidden_letters_in("ґанок_їжака_є_ціль", ZZ) == []

    def test_language_without_a_denylist_is_untouched(self) -> None:
        # Russian legitimately uses ы; only a language that declares the
        # letter refuses it.
        assert forbidden_letters_in("рыба", "ru") == []

    def test_unpolicied_language_forbids_nothing(self) -> None:
        assert forbidden_letters_in("рыба", "xx") == []


@pytest.mark.usefixtures("zz_policy")
class TestSelectionGate:
    def test_publish_gate_refuses_the_letter(self) -> None:
        assert not is_valid_pack_value("len", "довжына", ZZ)

    def test_publish_gate_without_a_language_is_unchanged(self) -> None:
        assert is_valid_pack_value("len", "довжына")

    def test_select_canonical_skips_a_leaked_candidate(self) -> None:
        # The leaked value is the most trusted candidate, so only the gate can
        # make the clean one win.
        result = select_canonical(
            "object",
            [
                {
                    "translation": "обыєкт",
                    "source": "community_review",
                    "confidence": "high",
                },
                {"translation": "обєкт", "source": "claude", "confidence": "low"},
            ],
            language=ZZ,
        )
        assert result is not None and result.translation == "обєкт"

    def test_leaked_shipped_value_does_not_anchor(self) -> None:
        result = select_canonical(
            "object",
            [{"translation": "обєкт", "source": "community"}],
            pack_value="рыба",
            language=ZZ,
        )
        assert result is not None and result.translation == "обєкт"

    @pytest.mark.parametrize("section", ["symbols", "variable_conventions"])
    def test_vocabulary_gate_refuses_the_letter(self, section) -> None:
        error = vocabulary_value_error(section, "counter", "лічыльник", ZZ)
        assert error is not None and "orthography never uses" in error

    @pytest.mark.parametrize("section", ["symbols", "variable_conventions"])
    def test_vocabulary_gate_without_a_language_is_unchanged(self, section) -> None:
        assert vocabulary_value_error(section, "counter", "лічыльник") is None


@pytest.mark.usefixtures("zz_policy")
class TestWriteBoundary:
    @pytest.fixture
    def db(self, tmp_path):
        from legesher_i18n.db import TranslationDatabase

        db = TranslationDatabase(db_path=str(tmp_path / "test.db"))
        conn = db._get_connection()
        conn.executemany(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            [(ZZ, "Test", "Тест"), ("ru", "Russian", "Русский")],
        )
        conn.commit()
        return db

    @pytest.mark.parametrize("letter", sorted(ZZ_FORBIDDEN))
    def test_set_selected_refuses_the_letter(self, db, letter) -> None:
        term_id = db.get_or_create_term("len", "python", "builtin_func")
        with pytest.raises(ValueError, match="orthography never uses"):
            db.set_selected(
                term_id=term_id, language_code=ZZ, translation=f"довж{letter}на"
            )
        assert db.get_selected(term_id, ZZ) is None

    def test_set_selected_accepts_an_allowed_value(self, db) -> None:
        term_id = db.get_or_create_term("len", "python", "builtin_func")
        assert db.set_selected(term_id=term_id, language_code=ZZ, translation="довжина")

    def test_a_language_keeps_its_own_letters(self, db) -> None:
        term_id = db.get_or_create_term("len", "python", "builtin_func")
        assert db.set_selected(term_id=term_id, language_code="ru", translation="рыба")

    def test_set_selected_vocabulary_refuses_the_letter(self, db) -> None:
        entry_id = db.get_or_create_vocabulary_entry(
            "variable_conventions", "loop_index", "i"
        )
        with pytest.raises(ValueError, match="orthography never uses"):
            db.set_selected_vocabulary(entry_id, ZZ, "лічыльник")


@pytest.mark.usefixtures("zz_policy")
class TestStrictAudit:
    def test_audit_names_the_value_and_its_location(self) -> None:
        findings = SchemaValidator.validate_pack_strict(
            _pack(ZZ, builtins={"len": "довжына", "print": "друкувати"})
        )
        leaked = [f for f in findings if f.code == "forbidden-letter"]
        assert [(f.severity, f.location) for f in leaked] == [("error", "builtins.len")]
        assert "ы" in leaked[0].message

    def test_audit_reads_the_vocabulary_sections(self) -> None:
        findings = SchemaValidator.check_forbidden_letters(
            _pack(
                ZZ,
                symbols={"colon": "двокрапка"},
                variable_conventions={"loop_index": "лічыльник"},
            )
        )
        assert [(f.code, f.location) for f in findings] == [
            ("forbidden-letter", "variable_conventions.loop_index")
        ]

    def test_clean_pack_passes_strict(self) -> None:
        assert (
            SchemaValidator.validate_pack_strict(_pack(ZZ, builtins={"len": "довжина"}))
            == []
        )


class TestUkrainian:
    def test_ukrainian_declares_the_russian_only_letters(self) -> None:
        # The shipped denylist, stated outright so a silent edit to the table
        # cannot shrink it without a test changing too.
        assert SCRIPT_POLICIES["uk"].forbidden_letters == frozenset("ыЫэЭъЪёЁ")

    def test_shipped_ukrainian_pack_is_clean(self) -> None:
        from legesher_i18n import load_language_pack

        pack = load_language_pack("uk", version="3.14")
        values = [
            *pack.keywords.values(),
            *pack.builtins.values(),
            *pack.exceptions.values(),
            *pack.implicit_params.values(),
        ]
        assert len(values) == 184
        assert [v for v in values if forbidden_letters_in(v, "uk")] == []


class TestSwahili:
    def test_swahili_declares_q_and_x(self) -> None:
        # Standard Swahili has no q or x, so either letter in a value is
        # untranslated English. Stated outright so the table cannot shrink
        # silently.
        assert SCRIPT_POLICIES["sw"].forbidden_letters == frozenset("qQxX")

    @pytest.mark.parametrize(
        ("term", "value"),
        [("max", "max"), ("hex", "hex"), ("exec", "exec"), ("str", "Squa")],
    )
    def test_english_leakage_is_refused(self, term: str, value: str) -> None:
        assert not is_valid_pack_value(term, value, "sw")

    def test_shipped_swahili_pack_is_clean(self) -> None:
        from legesher_i18n import load_language_pack

        pack = load_language_pack("sw", version="3.14")
        values = [
            *pack.keywords.values(),
            *pack.builtins.values(),
            *pack.exceptions.values(),
            *pack.implicit_params.values(),
        ]
        assert len(values) == 184
        assert [v for v in values if forbidden_letters_in(v, "sw")] == []
