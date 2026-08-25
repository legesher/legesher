"""validate_identifier_translations: the deterministic layer for identifiers.

Packs make keyword translation deterministic. Identifiers have no pack —
the model proposes them — so the guarantee they get instead is this check:
a proposal may not take a name the pack has reserved, and one concept may
not end up with two terms (or one term with two concepts).
"""

from __future__ import annotations

import unicodedata

import pytest
from mcp import ClientSession

from legesher_mcp.engine import get_engine
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio


def reserved_translation(language: str, category: str, term: str) -> str:
    """How ``term`` is spelled in ``language`` — a name proposals may not take."""
    engine = get_engine()
    return engine.pack_categories(engine.load_pack(language, "3.13"))[category][term]


async def test_translation_colliding_with_a_pack_keyword_is_rejected(
    client: ClientSession,
) -> None:
    taken = reserved_translation("es", "keywords", "def")

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "define_user", "translation": taken}],
        },
    )

    entry = result["results"][0]
    assert entry["source"] == "define_user"
    assert entry["ok"] is False
    assert entry["conflicts"] == [
        {"kind": "reserved_term", "against": "pack", "detail": "keyword:def"}
    ]


GLOSSARY = {"calculate_tax": "calcular_impuesto"}


async def test_a_second_translation_for_a_known_source_is_drift(client: ClientSession) -> None:
    """One concept, two terms — the drift a long session produces."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": GLOSSARY,
            "proposals": [{"source": "calculate_tax", "translation": "computar_impuesto"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"] == [
        {"kind": "drift", "against": "glossary", "detail": "calcular_impuesto"}
    ]
    assert result["accepted"] == {}


async def test_a_known_translation_reused_for_a_new_source_is_a_collision(
    client: ClientSession,
) -> None:
    """Two concepts, one term — the reverse mapper could not tell them apart."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": GLOSSARY,
            "proposals": [{"source": "compute_levy", "translation": "calcular_impuesto"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"] == [
        {"kind": "collision", "against": "glossary", "detail": "calculate_tax"}
    ]


async def test_reproposing_the_existing_translation_is_not_a_conflict(
    client: ClientSession,
) -> None:
    """Reuse is the point of the glossary — it must not read as drift."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": GLOSSARY,
            "proposals": [{"source": "calculate_tax", "translation": "calcular_impuesto"}],
        },
    )

    assert result["results"][0]["ok"] is True
    assert result["results"][0]["conflicts"] == []


async def test_drift_inside_one_batch_is_caught_without_a_glossary(
    client: ClientSession,
) -> None:
    """The first session has no glossary yet — the batch must still be self-consistent."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "calculate_tax", "translation": "calcular_impuesto"},
                {"source": "calculate_tax", "translation": "computar_impuesto"},
            ],
        },
    )

    first, second = result["results"]
    assert first["ok"] is True
    assert second["conflicts"] == [
        {"kind": "drift", "against": "batch", "detail": "calcular_impuesto"}
    ]
    assert result["accepted"] == {"calculate_tax": "calcular_impuesto"}


async def test_collision_inside_one_batch_is_caught(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "calculate_tax", "translation": "calcular_impuesto"},
                {"source": "compute_levy", "translation": "calcular_impuesto"},
            ],
        },
    )

    first, second = result["results"]
    assert first["ok"] is True
    assert second["conflicts"] == [
        {"kind": "collision", "against": "batch", "detail": "calculate_tax"}
    ]


async def test_a_clean_batch_returns_every_pair_ready_to_record(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "calculate_tax", "translation": "calcular_impuesto"},
                {"source": "student_scores", "translation": "notas_estudiante"},
            ],
        },
    )

    assert [entry["ok"] for entry in result["results"]] == [True, True]
    assert result["accepted"] == {
        "calculate_tax": "calcular_impuesto",
        "student_scores": "notas_estudiante",
    }


async def test_a_translation_that_is_not_a_valid_identifier_is_rejected(
    client: ClientSession,
) -> None:
    """A malformed rendering lands in every artifact, then SyntaxErrors at render time."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "a", "translation": "mi variable"},
                {"source": "b", "translation": "class"},
                {"source": "c", "translation": "2casa"},
            ],
        },
    )

    assert [entry["ok"] for entry in result["results"]] == [False, False, False]
    assert {conflict["kind"] for entry in result["results"] for conflict in entry["conflicts"]} == {
        "malformed"
    }
    assert result["accepted"] == {}


async def test_a_case_variant_of_a_pack_term_is_still_a_collision(
    client: ClientSession,
) -> None:
    """Comparison is NFKC+casefold — the CLI rejects this, so the tool must too."""
    taken = reserved_translation("es", "keywords", "def")

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "define_user", "translation": taken.upper()}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"][0]["kind"] == "reserved_term"
    assert entry["conflicts"][0]["detail"] == "keyword:def"


async def test_invisible_codepoints_are_rejected(client: ClientSession) -> None:
    """U+034F is NFKC-stable, so it defeats the collision check unless scanned for."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "a", "translation": "calcular" + chr(0x034F) + "impuesto"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"][0]["kind"] == "unsafe_text"
    assert result["accepted"] == {}


async def test_unsupported_script_marks_are_rejected(client: ClientSession) -> None:
    """U+2D7F defeats every property-based net: only script membership sees it.

    Mn, ID_Continue, NFKC-stable, and NOT Default_Ignorable — so it satisfies
    ``str.isidentifier()``, survives the collision check, and renders as
    nothing. Without the script allowlist it would merge into the glossary
    (CORE-1558).
    """
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "a", "translation": "calcular" + chr(0x2D7F) + "impuesto"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"][0]["kind"] == "unsafe_text"
    assert "U+2D7F" in entry["conflicts"][0]["detail"]
    assert result["accepted"] == {}


async def test_arabic_harakat_are_accepted(client: ClientSession) -> None:
    """The false positive that would make the allowlist unshippable.

    U+064B is Mn too. A category-based rule would reject vocalized Arabic
    outright; script membership keeps it writable.
    """
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "ar",
            "proposals": [{"source": "greeting", "translation": "مَرْحَبًا"}],
        },
    )

    assert result["results"][0]["ok"] is True
    assert result["accepted"] == {"greeting": "مَرْحَبًا"}


async def test_nfkc_equivalent_translations_are_the_same_identifier(
    client: ClientSession,
) -> None:
    """Store NFC, compare NFKC+fold — an NFD twin is not a second term."""
    nfc = unicodedata.normalize("NFC", "año")
    nfd = unicodedata.normalize("NFD", "año")
    assert nfc != nfd

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": {"year": nfc},
            "proposals": [{"source": "other", "translation": nfd}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"] == [{"kind": "collision", "against": "glossary", "detail": "year"}]


async def test_accepted_entries_are_normalized_to_nfc(client: ClientSession) -> None:
    """Storage stays NFC even when the model proposes a decomposed form."""
    nfd = unicodedata.normalize("NFD", "año")

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {"target_lang": "es", "proposals": [{"source": "year", "translation": nfd}]},
    )

    assert result["accepted"] == {"year": unicodedata.normalize("NFC", "año")}


async def test_a_glossary_with_duplicate_terms_does_not_invent_a_collision(
    client: ClientSession,
) -> None:
    """Re-proposing an entry the glossary already holds is reuse, not conflict."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": {"a": "equis", "b": "equis"},
            "proposals": [{"source": "a", "translation": "equis"}],
        },
    )

    assert result["results"][0]["ok"] is True
    assert result["results"][0]["conflicts"] == []


async def test_a_variant_spelling_does_not_rewrite_the_settled_entry(
    client: ClientSession,
) -> None:
    """Same term under the contract — so reuse the established spelling, don't restate it.

    Accepting the proposal's spelling would let a merge silently rewrite a
    settled glossary entry to a case or fullwidth variant, which is exactly
    the confusable the NFKC contract exists to keep out of storage.
    """
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": {"calculate_tax": "calcular_impuesto"},
            "proposals": [{"source": "calculate_tax", "translation": "Calcular_Impuesto"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is True
    assert entry["translation"] == "calcular_impuesto"
    # The substitution must be visible, or the agent writes the settled term
    # to the glossary while emitting its own variant in the code.
    assert entry["proposed"] == "Calcular_Impuesto"
    assert result["accepted"] == {"calculate_tax": "calcular_impuesto"}


async def test_an_unchanged_proposal_reports_no_substitution(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "calculate_tax", "translation": "calcular_impuesto"}],
        },
    )

    assert result["results"][0]["proposed"] is None


async def test_a_variant_spelling_inside_one_batch_keeps_the_first(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "a", "translation": "uno"},
                {"source": "a", "translation": "UNO"},
            ],
        },
    )

    assert [entry["ok"] for entry in result["results"]] == [True, True]
    assert result["accepted"] == {"a": "uno"}


async def test_a_decomposed_source_key_still_matches_its_entry(
    client: ClientSession,
) -> None:
    """Source keys are normalized too, or drift goes unreported and the merge duplicates the key."""
    nfd_source = unicodedata.normalize("NFD", "año_actual")
    nfc_source = unicodedata.normalize("NFC", "año_actual")
    assert nfd_source != nfc_source

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "glossary": {nfd_source: "anio_en_curso"},
            "proposals": [{"source": nfc_source, "translation": "anio_vigente"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert entry["conflicts"] == [
        {"kind": "drift", "against": "glossary", "detail": "anio_en_curso"}
    ]


async def test_unknown_language_is_a_clean_error(client: ClientSession) -> None:
    """Guards the shared error path: a pack failure must not leak paths or traces."""
    message = await call_err(
        client,
        "validate_identifier_translations",
        {"target_lang": "xx", "proposals": [{"source": "a", "translation": "b"}]},
    )
    assert "unsupported_language" in message
    assert_sanitized(message)


async def test_sinhala_conjunct_zwj_is_accepted(client: ClientSession) -> None:
    """Sinhala forms conjuncts with virama+ZWJ, so U+200D is orthography here.

    The gate scans for invisible format characters, which is right by default —
    but ZWJ is not decoration in Sinhala, it is how the script joins consonants.
    Legesher's own `si` pack ships `සත්‍ය` for `True` on 3.13+, so a blanket
    rejection refuses the vocabulary we publish. `script_policy` opens exactly
    the characters a registered script declares, and nothing more.
    """
    conjunct = "සත්‍යය"
    assert conjunct.isidentifier()

    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "si",
            "proposals": [{"source": "is_true", "translation": conjunct}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is True, entry["conflicts"]
    assert result["accepted"] == {"is_true": conjunct}


async def test_zwj_is_still_rejected_for_a_script_that_does_not_declare_it(
    client: ClientSession,
) -> None:
    """The allowance is per script, not global — default-deny still holds."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "total", "translation": "tot‍al"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert "unsafe_text" in {conflict["kind"] for conflict in entry["conflicts"]}


async def test_a_source_that_is_not_an_identifier_is_rejected(
    client: ClientSession,
) -> None:
    """`accepted` keys are described as ready to merge into a glossary.

    An unvalidated source seeds a key that can never match an identifier in
    code, and the caller is told the pair is fine.
    """
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [
                {"source": "calculate tax", "translation": "calcular_impuesto"},
                {"source": "class", "translation": "clase_usuario"},
            ],
        },
    )

    assert [entry["ok"] for entry in result["results"]] == [False, False]
    assert all(
        any(conflict["kind"] == "malformed" for conflict in entry["conflicts"])
        for entry in result["results"]
    )
    assert result["accepted"] == {}


async def test_a_source_carrying_an_invisible_is_rejected(
    client: ClientSession,
) -> None:
    """A source with a hidden codepoint is two glossary keys that look like one."""
    result = await call_ok(
        client,
        "validate_identifier_translations",
        {
            "target_lang": "es",
            "proposals": [{"source": "user͏name", "translation": "nombre_usuario"}],
        },
    )

    entry = result["results"][0]
    assert entry["ok"] is False
    assert "unsafe_text" in {conflict["kind"] for conflict in entry["conflicts"]}
    assert result["accepted"] == {}
