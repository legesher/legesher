"""Guards on the canon-packs export (CORE-1043).

The properties tested here are the ones whose failure would be discovered
after the dataset is public: the wrong locale count, a target this artifact
does not claim to cover, or a resolved row that misreports where its term is
defined.
"""

from __future__ import annotations

import json
import importlib.util
import inspect
import re
import sys
from pathlib import Path
from unittest import mock

import pytest
from tests.interpreter_gaps import NEEDS_UNICODE_15_1

_I18N_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _I18N_ROOT / "scripts" / "export_packs.py"


def _load_module():
    sys.path.insert(0, str(_I18N_ROOT))
    spec = importlib.util.spec_from_file_location("export_packs", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export_packs = _load_module()


def test_version_index_is_not_counted_as_a_locale() -> None:
    """``version-index.yml`` is a file in the pack tree, not a 52nd language.

    A plain directory listing of ``language-packs/python`` returns 52 entries
    and this is the one that is not a locale. The count reaches a public
    dataset card, so it is asserted rather than eyeballed.
    """
    locales = export_packs.pack_locales()
    assert "version-index.yml" not in locales
    assert all(not name.endswith(".yml") for name in locales)


def test_pack_tree_and_registry_name_the_same_locales() -> None:
    """The registry and the pack tree must agree, in both directions."""
    registry = export_packs.load_registry()
    locales = export_packs.pack_locales()
    assert set(registry) == set(locales)
    # Reconciliation is the guard that enforces it; it must not raise here.
    export_packs.reconcile_locales(registry, locales)


def test_reconcile_rejects_a_registry_locale_with_no_pack() -> None:
    """A registered locale with no pack tree would be silently omitted.

    ``uk`` is the live instance: six selection rows in the database, no pack
    tree. It must never reach the artifact by being quietly skipped.
    """
    with pytest.raises(SystemExit, match="uk"):
        export_packs.reconcile_locales({"es": {}, "uk": {}}, ["es"])


def test_reconcile_rejects_a_pack_with_no_registry_entry() -> None:
    """A pack with no registry entry has no tier stamp and no display name."""
    with pytest.raises(SystemExit, match="zz"):
        export_packs.reconcile_locales({"es": {}}, ["es", "zz"])


def test_assert_python_only_rejects_another_target() -> None:
    """The CORE-1913 property, checked on the rows about to be published.

    Sourcing from ``canon_selections`` would carry 62 Arabic JavaScript
    selections labelled by target. The pack tree cannot carry them, and this
    proves it on the way out instead of trusting that it did.
    """
    with pytest.raises(SystemExit, match="javascript"):
        export_packs.assert_python_only(
            [{"target": "python"}, {"target": "javascript"}]
        )


def test_assert_python_only_accepts_a_python_only_export() -> None:
    export_packs.assert_python_only([{"target": "python"}] * 3)


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    registry = export_packs.load_registry()
    return export_packs.build_rows(export_packs.pack_locales(), registry)


def test_every_row_is_python(rows: list[dict]) -> None:
    assert {r["target"] for r in rows} == {"python"}


def test_every_locale_ships_the_same_terms_at_a_given_version(
    rows: list[dict],
) -> None:
    """The card states one term count per version; that requires uniformity."""
    from collections import Counter

    per_pack = Counter((r["locale"], r["pl_version"]) for r in rows)
    for version in export_packs.VERSIONS:
        sizes = {n for (_, v), n in per_pack.items() if v == version}
        assert len(sizes) == 1, f"locales disagree at {version}: {sorted(sizes)}"


def test_inheritance_is_resolved_and_labelled(rows: list[dict]) -> None:
    """A 3.12 pack carries only a delta; the export must resolve the rest.

    ``for`` is defined in the 3.10 base and must still appear on 3.12, pointing
    at 3.10: the delta structure preserved rather than erased by the
    flattening. A row inherits exactly when ``defined_at`` differs from
    ``pl_version``, which is what the dropped ``inherited`` column used to say
    (0.3.0).
    """
    match = [
        r
        for r in rows
        if r["locale"] == "es"
        and r["pl_version"] == "3.12"
        and r["source_term"] == "for"
    ]
    assert len(match) == 1
    assert match[0]["defined_at"] == "3.10"
    assert match[0]["defined_at"] != match[0]["pl_version"], "3.12 inherits"

    # ``except*`` arrives with PEP 654 in 3.11, so on 3.11 it is defined, not
    # inherited.
    star = [
        r
        for r in rows
        if r["locale"] == "es"
        and r["pl_version"] == "3.11"
        and r["source_term"] == "except*"
    ]
    assert len(star) == 1
    assert star[0]["defined_at"] == "3.11"
    assert star[0]["defined_at"] == star[0]["pl_version"], "3.11 defines it"


def test_star_suffixed_terms_keep_their_mirror(rows: list[dict]) -> None:
    """Every ``except*`` rendering carries the trailing marker (CORE-1839).

    Nine packs once shipped a star-less value, which reverse-translated to
    ``except**``. The publish gate now requires the mirror; this asserts it
    over the rows actually being exported.
    """
    offenders = [
        (r["locale"], r["translation"])
        for r in rows
        if r["source_term"] == "except*" and not r["translation"].endswith("*")
    ]
    assert not offenders, f"star-less except* renderings: {offenders}"


def test_every_row_is_stamped_with_a_known_tier(rows: list[dict]) -> None:
    assert {r["tier"] for r in rows} <= {"experimental", "reviewed", "official"}


def test_a_redefined_term_points_at_the_redefinition(rows: list[dict]) -> None:
    """``defined_at`` must name the version supplying the value on THAT row.

    Sinhala redefines terms at 3.13 to their ZWJ conjunct forms, so ``True`` is
    one string on 3.10 and a different one from 3.13 on. Recording the earliest
    definition would publish a 3.13 row labelled ``defined_at=3.10`` while
    showing a value 3.10 does not carry.
    """
    by_version = {
        r["pl_version"]: r
        for r in rows
        if r["locale"] == "si" and r["source_term"] == "True"
    }
    early, late = by_version["3.10"], by_version["3.13"]
    assert early["translation"] != late["translation"], (
        "fixture assumption broken: si no longer redefines True at 3.13"
    )
    assert early["defined_at"] == early["pl_version"] == "3.10"
    assert late["defined_at"] == late["pl_version"] == "3.13"


def test_the_published_columns_carry_no_derived_flag(rows: list[dict]) -> None:
    """Dropping ``inherited`` lost nothing, and the schema must stay that way.

    It was ``defined_at != pl_version`` restated as a column, so a consumer
    could always compute it and a bug could make the three disagree. This
    asserts both halves: the flag is gone from what ships, and the two columns
    that replaced it still resolve every row.
    """
    assert "inherited" not in export_packs.VOCABULARY_COLUMNS
    assert "inherited" not in rows[0]

    inheriting = [r for r in rows if r["defined_at"] != r["pl_version"]]
    defining = [r for r in rows if r["defined_at"] == r["pl_version"]]
    assert inheriting and defining, (
        "every row falls on one side, so the distinction is still expressible"
    )
    assert len(inheriting) + len(defining) == len(rows)


def test_defined_at_never_points_forward(rows: list[dict]) -> None:
    """A row can only inherit from a version at or below its own."""
    order = {v: i for i, v in enumerate(export_packs.VERSIONS)}
    bad = [r for r in rows if order[r["defined_at"]] > order[r["pl_version"]]]
    assert not bad, f"{len(bad)} row(s) claim a future definition: {bad[:3]}"


def test_the_row_value_matches_the_version_it_claims(rows: list[dict]) -> None:
    """``defined_at`` must be checkable: that pack's row carries this value."""
    at = {
        (r["locale"], r["pl_version"], r["category"], r["source_term"]): r[
            "translation"
        ]
        for r in rows
    }
    mismatches = [
        r
        for r in rows
        if at.get((r["locale"], r["defined_at"], r["category"], r["source_term"]))
        != r["translation"]
    ]
    assert not mismatches, (
        f"{len(mismatches)} row(s) name a defined_at whose pack carries a "
        f"different value: {mismatches[:3]}"
    )


#: An NFKC-instability block shaped like the measured one, so the card's
#: normalization section renders from a manifest in tests the way it does in a
#: real export.
_NFKC_BLOCK = {
    "rows": 110,
    "renderings": 22,
    "locales": [{"locale": "th", "language_name": "Thai"}],
    "characters": [{"codepoint": "U+0E33", "name": "THAI CHARACTER SARA AM"}],
}


def _locale_rows(locales: list[str]) -> list[dict]:
    """Locale rows shaped like the real ones, for card rendering."""
    registry = export_packs.load_registry()
    return [
        {
            "locale": code,
            "language_name": registry[code].get("name"),
            "native_name": registry[code].get("native"),
            "tier": registry[code].get("status"),
            "package_version": "0.0.1",
        }
        for code in locales
    ]


def _manifest(
    locales: list[str],
    tiers: list[str] | None = None,
    tier_counts: dict[str, int] | None = None,
    nfkc: dict | None = None,
) -> dict:
    """Minimal manifest shaped like the real one, for card rendering."""
    tiers = tiers or ["experimental"]
    return {
        "counts": {
            "locales": len(locales),
            "pl_versions": len(export_packs.VERSIONS),
            "pl_terminology_rows": 0,
            "packs_rows": len(locales),
            "terms_per_locale_by_version": dict.fromkeys(export_packs.VERSIONS, 1),
        },
        "locales": locales,
        "tiers_present": tiers,
        "tier_counts": tier_counts or {"experimental": len(locales)},
        "nfkc_unstable": _NFKC_BLOCK if nfkc is None else nfkc,
        # The card's release block prints the library version out of here, so
        # a fixture without it renders a KeyError rather than a card.
        "toolchain": {"legesher_i18n": "0.0.0"},
        "source": {"commit": "0" * 40, "tag": "(untagged)"},
    }


def _term_rows() -> list[dict]:
    """One `pl_terminology` row per (category, subcategory) the export ships.

    Shaped like the real rows rather than the real rows themselves: the card's
    category table counts what it is handed, and a fixture that counted the
    live pack tree would pin the table to today's vocabulary instead of to the
    code that renders it.
    """
    kinds = {
        "keywords": ["keyword"],
        "builtins": ["builtin_func", "builtin_type", "special_constant"],
        "exceptions": ["exception"],
        "implicit_params": ["implicit_param"],
        "symbols": [None],
        "variable_conventions": [None],
        "messages": ["SyntaxError", "ValueError"],
    }
    rows = []
    for family in export_packs.CATEGORY_FAMILIES:
        for kind in kinds[family]:
            rows.append(
                {
                    "target": "python",
                    "category": family,
                    "subcategory": kind,
                    "source_term": f"{family}-{kind}",
                    "source_text": "",
                    "pl_versions": list(export_packs.VERSIONS),
                }
            )
    return rows


def test_card_states_the_tiers_the_artifact_actually_carries() -> None:
    """The card must not hard-code "everything is experimental".

    Promoting one locale would otherwise publish a card contradicting its own
    `tier` column, the failure generation exists to prevent. Every stamp is now
    a Status cell in the Languages table and nowhere else: prose asserting the
    spread was a second place for the same fact to go stale, and it went when
    the card was rewritten (2026-08-29).
    """
    locales = export_packs.pack_locales()
    rows = _locale_rows(locales)
    all_experimental = export_packs.render_card(
        _manifest(locales), {"MIT": 1}, rows, _term_rows()
    )
    table = all_experimental.split("## Languages")[1].split("\n## ")[0]
    assert "`reviewed`" not in table
    assert table.count("| `experimental` |") == len(rows)

    promoted = [{**r, "tier": "reviewed"} if i == 0 else r for i, r in enumerate(rows)]
    mixed = export_packs.render_card(
        _manifest(locales), {"MIT": 1}, promoted, _term_rows()
    )
    mixed_table = mixed.split("## Languages")[1].split("\n## ")[0]
    assert mixed_table.count("| `reviewed` |") == 1
    assert mixed_table.count("| `experimental` |") == len(rows) - 1


def test_card_language_codes_survive_a_yaml_parse() -> None:
    """``no`` unquoted is YAML boolean false, which drops Norwegian.

    The Hub parses this frontmatter to build the language facet, so an
    unquoted code is a locale that silently vanishes from discovery.
    """
    import yaml

    locales = export_packs.pack_locales()
    card = export_packs.render_card(
        _manifest(locales), {"MIT": 255}, _locale_rows(locales), _term_rows()
    )
    front = yaml.safe_load(card.split("---")[1])
    assert front["language"] == locales
    assert all(isinstance(code, str) for code in front["language"])
    assert "no" in front["language"]


def test_licence_agreement_is_case_insensitive() -> None:
    """SPDX writes ``Apache-2.0``; the Hub frontmatter wants ``apache-2.0``."""
    assert export_packs.licenses_agree({"Apache-2.0": 255})
    assert export_packs.licenses_agree({"apache-2.0": 255})
    assert not export_packs.licenses_agree({"MIT": 255})
    assert not export_packs.licenses_agree({"Apache-2.0": 254, "MIT": 1})


def test_shipped_packs_agree_with_the_declared_licence() -> None:
    """Both claims are public, so they must not drift apart again.

    Every pack carries its own `metadata.license`, and the dataset card
    declares one for the compilation. Until CORE-1043 the packs said `MIT`
    while the distribution that ships them said `Apache-2.0`; this pins the
    reconciliation so a regenerated or newly added pack cannot reintroduce it.
    """
    seen = export_packs.check_license_consistency(export_packs.pack_locales())
    assert export_packs.licenses_agree(seen), (
        f"pack metadata.license disagrees with "
        f"{export_packs.DECLARED_LICENSE!r}: {seen}"
    )


def test_the_card_carries_no_licence_caveat_when_they_agree() -> None:
    """The caveat is for a real disagreement, not decoration."""
    locales = export_packs.pack_locales()
    card = export_packs.render_card(
        _manifest(locales), {"Apache-2.0": 255}, _locale_rows(locales), _term_rows()
    )
    assert "Note on the license field" not in card

    # ...and it still appears when they genuinely differ.
    mixed = export_packs.render_card(
        _manifest(locales), {"MIT": 255}, _locale_rows(locales), _term_rows()
    )
    assert "Note on the license field" in mixed


# ---------------------------------------------------------------------------
# What the card has to say out loud
# ---------------------------------------------------------------------------


def test_the_card_states_how_the_vocabulary_was_reviewed() -> None:
    """The `experimental` stamp has to be defined, not just printed.

    A reader deciding whether to depend on these words needs to know they are
    machine-drafted and maintainer-curated, and that no native speaker has
    signed a pack off. That definition lives in the Maturity table, one row per
    stage; the prose section that used to repeat it was removed as a second
    statement of one fact (2026-08-29).
    """
    card = export_packs.render_card(
        _manifest(export_packs.pack_locales()),
        {"MIT": 1},
        _locale_rows(export_packs.pack_locales()),
        _term_rows(),
    )
    ladder = card.split("## Maturity")[1].split("\n## ")[0]
    assert "Machine-drafted, then curated by maintainers" in ladder
    assert "No native speaker has signed off." in ladder
    assert "A native speaker of the language has reviewed the pack" in ladder


def test_no_pack_claims_community_review() -> None:
    """The card's claim and the packs' own metadata must not contradict.

    Five `en` packs carried ``community_reviewed: true`` while the card said no
    native speaker had signed anything off, and no review evidence existed
    anywhere. Both claims are public; this is the one that keeps them one claim.
    """
    import yaml

    claimed = []
    for locale in export_packs.pack_locales():
        for version in export_packs.VERSIONS:
            path = (
                export_packs.PACKS_DIR
                / locale
                / f"legesher_i18n_python_{locale}"
                / "packs"
                / f"{version}.yml"
            )
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if (data.get("metadata") or {}).get("community_reviewed"):
                claimed.append(f"{locale}/{version}")
    assert claimed == [], (
        f"packs claim community review the card says nobody has given: {claimed}"
    )


def test_the_card_states_its_target_scope_and_the_join_key() -> None:
    """Two facts a consumer gets wrong without being told.

    A pack is defined by its target, and this release carries one of several,
    so the card has to say which target these words are for rather than let a
    reader assume they cover the language they happen to use. That now lives in
    the release table rather than a paragraph.

    And pack ids are not locale tags -- `no` here is `nb` in the corpus -- so
    someone joining on `locale` silently drops exactly the rows that differ.
    """
    card = export_packs.render_card(
        _manifest(export_packs.pack_locales()),
        {"MIT": 1},
        _locale_rows(export_packs.pack_locales()),
        _term_rows(),
    )
    assert f"| `{export_packs.TARGET}` |" in card.split("## Languages")[0]
    assert "`target`, `category`, `source_term`: the key" in card
    assert "`locale` is a pack id, not a language tag" in card
    assert "`no` is BCP 47 `nb`" in card


def test_the_card_describes_a_pack_without_assuming_its_target() -> None:
    """A pack is a shape, and Python is the target that shape is filled for.

    The card used to open by defining the artifact as Python's vocabulary,
    which reads as though a pack IS a Python thing. The target is one of a
    pack's parts, so the opening has to survive a second target existing.
    """
    card = export_packs.render_card(
        _manifest(export_packs.pack_locales()),
        {"MIT": 1},
        _locale_rows(export_packs.pack_locales()),
        _term_rows(),
    )
    definition = card.split("| Release |")[0]
    assert "Python" not in definition, (
        "the definition of a language pack must not name one target -- "
        "the target belongs in the release table, as one of a pack's parts"
    )
    for heading in ("### Target", "### Categories"):
        assert heading in card, f"{heading} missing from the pack breakdown"

    # The version range is a table cell now, not a paragraph.
    header = card.split("## Languages")[0]
    assert f"`{export_packs.VERSIONS[0]}`-`{export_packs.VERSIONS[-1]}`" in header


def test_the_card_lists_every_language_with_its_status_and_version() -> None:
    """Listed out the way the canon and corpus cards list theirs."""
    locales = export_packs.pack_locales()
    rows = _locale_rows(locales)
    card = export_packs.render_card(_manifest(locales), {"MIT": 1}, rows, _term_rows())

    table = card.split("## Languages")[1].split("##")[0]
    for row in rows:
        assert f"| `{row['locale']}` |" in table, f"{row['locale']} missing"
        assert row["native_name"] in table, f"{row['locale']} native name missing"
    assert "| `0.0.1` |" in table, "package version column not rendered"


def test_every_category_the_export_ships_is_described_on_the_card() -> None:
    """A partition added for another target must not reach the card unexplained."""
    card = export_packs.render_card(
        _manifest(export_packs.pack_locales()),
        {"MIT": 1},
        _locale_rows(export_packs.pack_locales()),
        _term_rows(),
    )
    assert set(export_packs.CATEGORY_BLURBS) == set(export_packs.CATEGORY_FAMILIES), (
        "CATEGORY_BLURBS and CATEGORY_FAMILIES have drifted; the card would "
        "render a KeyError or a bare category name"
    )
    for name in export_packs.CATEGORY_FAMILIES:
        assert f"| `{name}` |" in card


def test_the_release_block_carries_the_provenance_a_reader_needs() -> None:
    """Seven facts, stated once, at the top.

    Release, languages, target, version range, license, library version and
    commit used to be spread across an opening sentence, a Target paragraph, a
    Provenance section and a License section. A reader checking what they held
    had to read the whole card, and the release number appeared three times.
    All seven are now one table row, every value read from the manifest or a
    module constant rather than typed.
    """
    locales = export_packs.pack_locales()
    card = export_packs.render_card(
        _manifest(locales), {"MIT": 1}, _locale_rows(locales), _term_rows()
    )
    header = card.split("## Languages")[0]

    assert (
        "| Release | Languages supported | Target | Versions "
        "| License | `legesher-i18n` | Commit |"
    ) in header
    row = (
        f"| `{export_packs.DATASET_VERSION}` | {len(locales)} "
        f"| `{export_packs.TARGET}` | `{export_packs.VERSIONS[0]}`-"
        f"`{export_packs.VERSIONS[-1]}` | Apache-2.0 | `0.0.0` | `{'0' * 12}` |"
    )
    assert row in header, f"release block not rendered from the manifest: {row}"

    # Stated in the table and nowhere else. A second home is a second place to
    # go stale, which is why the prose sections that repeated these are gone.
    assert "## Provenance" not in card
    assert "## License" not in card
    assert card.count(export_packs.DATASET_VERSION) == 2, (
        "the release number belongs in the table and the citation, nowhere else"
    )


def test_the_category_table_counts_the_rows_it_was_given() -> None:
    """Subcategories and term counts are derived, never written down.

    The table used to be one blurb per category. It now carries the finer
    kinds and how many source terms sit under each, and both have to come off
    the emitted rows: a figure typed into the template outlives the vocabulary
    it counted, which is the whole reason this card is generated.
    """
    rows = _term_rows()
    table = export_packs.category_table(rows)

    # Counted, not asserted: change the fixture and the table changes with it.
    for family in export_packs.CATEGORY_FAMILIES:
        expected = sum(1 for r in rows if r["category"] == family)
        line = next(ln for ln in table.splitlines() if ln.startswith(f"| `{family}` |"))
        assert f"| {expected} |" in line, f"{family} count not derived: {line}"

    builtins = next(ln for ln in table.splitlines() if ln.startswith("| `builtins` |"))
    assert "`builtin_func`, `builtin_type`, `special_constant`" in builtins

    # symbols and variable_conventions never pass through classify_term, so
    # their cell is a rule rather than an invented kind. The table is allowed
    # to be uneven, because the data is.
    for family in ("symbols", "variable_conventions"):
        line = next(ln for ln in table.splitlines() if ln.startswith(f"| `{family}` |"))
        assert "| -- |" in line, f"{family} claims a subcategory it has not got"

    messages = next(ln for ln in table.splitlines() if ln.startswith("| `messages` |"))
    assert "message families" in messages, "twenty families would not fit in a cell"


def test_every_symbol_publishes_the_character_it_names(exported: Path) -> None:
    """A symbol row that cannot be resolved to a character names nothing.

    The inventory has always carried the glyph; the export dropped it, on the
    reasoning that shipping a language-invariant constant in 51 packs would be
    51 copies of it. True of the pack files, false of `pl_terminology`, which
    holds one row per symbol and exists for exactly the facts that do not vary
    by language. Without it the dataset said `paren_open` is called *opening
    parenthesis* in 51 languages and never said it means `(`.
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(exported / "data" / "pl_terminology.parquet").to_pylist()
    symbols = [r for r in rows if r["category"] == "symbols"]
    assert symbols, "no symbol rows; the guard would pass vacuously"

    glyphless = {r["source_term"] for r in symbols if r["glyph"] is None}
    # Null means "has no printable form", not "we forgot". Those three are the
    # whole set, and naming them here makes a fourth appearing a failure.
    assert glyphless == {"indentation", "newline", "space"}, (
        f"unexpected glyphless symbols: {sorted(glyphless)}"
    )

    by_slug = {r["source_term"]: r["glyph"] for r in symbols}
    assert by_slug["paren_open"] == "("
    assert by_slug["underscore"] == "_"

    # Every other category is glyphless by construction.
    assert all(r["glyph"] is None for r in rows if r["category"] != "symbols")


def test_source_text_distinguishes_absent_from_empty(exported: Path) -> None:
    """Null and `""` are different facts, and the card says which is which.

    Null means the row has no separate English surface, because `source_term`
    already is it. `""` means the surface genuinely is the empty string: a bare
    `assert` raises `AssertionError` with no message at all. A consumer
    filtering `IS NOT NULL` and one filtering `!= ''` get different row sets,
    so the distinction has to be deliberate rather than an artefact of which
    branch built the row.
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(exported / "data" / "pl_terminology.parquet").to_pylist()

    term_families = {"keywords", "builtins", "exceptions", "implicit_params"}
    assert all(
        r["source_text"] is None for r in rows if r["category"] in term_families
    ), "a term row carries a source_text, but its source_term IS the English"

    empty = {
        r["source_term"]
        for r in rows
        if r["category"] == "messages" and r["source_text"] == ""
    }
    assert empty == {
        "AssertionError.no_message",
        "KeyboardInterrupt.interrupt",
        "StopIteration.no_value",
    }, f"the no-text messages changed: {sorted(empty)}"
    assert all(
        r["source_text"] is not None for r in rows if r["category"] == "messages"
    ), 'a message row went null; empty text is `""`, never absent'


def test_the_renamed_category_reaches_every_published_surface(
    exported: Path,
) -> None:
    """`reserved_words` claimed the grammar reserved `self` and `cls`.

    It does not. The name is now `implicit_params`, and this asserts the rename
    landed everywhere a reader can see it rather than only where it was easy.
    """
    import pyarrow.parquet as pq

    assert "implicit_params" in export_packs.SECTIONS
    assert "reserved_words" not in export_packs.SECTIONS

    for config in ("pl_terminology", "vocabulary"):
        rows = pq.read_table(exported / "data" / f"{config}.parquet").to_pylist()
        seen = {r["category"] for r in rows}
        assert "implicit_params" in seen, f"{config} lost the category"
        assert "reserved_words" not in seen, f"{config} still publishes the old name"

    card = (exported / "README.md").read_text(encoding="utf-8")
    assert "| `implicit_params` |" in card
    assert "reserved_words" not in card


def test_the_worked_example_is_read_from_the_data(exported: Path) -> None:
    """The card's example version must be the one the `packs` row carries.

    It was typed as `0.0.4` and stayed there while CORE-2060 bumped all 51 pack
    versions, so the card told a reader to expect `legesher-i18n-python-ar==0.0.4`
    beside a `packs` row saying `0.0.5`. A generated card exists so a figure
    cannot outlive the thing it describes; this one was prose, so it did.
    """
    import pyarrow.parquet as pq

    card = (exported / "README.md").read_text(encoding="utf-8")
    rows = pq.read_table(exported / "data" / "packs.parquet").to_pylist()
    shipped = {r["locale"]: r["package_version"] for r in rows}

    version = shipped["ar"]
    assert f"`legesher-i18n-python-ar=={version}`" in card
    assert f"`ar` / `python` / `{version}`" in card

    # No other pack version may appear as the example, which is what makes this
    # fail on a bump rather than passing on a coincidence.
    stale = {v for v in shipped.values() if v != version}
    for other in stale:
        assert f"legesher-i18n-python-ar=={other}" not in card


def test_the_card_does_not_call_every_partition_reserved(exported: Path) -> None:
    """`pl_terminology` carries more than what the grammar reserves.

    Symbols, variable conventions and message templates are none of them
    reserved by anything, and they are the majority of that config's rows once
    the four translation sections are set aside. The summary table used to ask
    "what does the programming language reserve", which was true of 184 rows
    and false of 102.
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(exported / "data" / "pl_terminology.parquet").to_pylist()
    unreserved = [
        r
        for r in rows
        if r["category"] in {"symbols", "variable_conventions", "messages"}
    ]
    assert unreserved, "fixture assumption broken: those partitions are empty"

    card = (exported / "README.md").read_text(encoding="utf-8")
    assert "what does the programming language reserve" not in card

    # `except*` is a keyword and is not a legal identifier, so the keywords
    # blurb may not claim that all of them are.
    keywords = [r["source_term"] for r in rows if r["category"] == "keywords"]
    assert [k for k in keywords if not k.isidentifier()] == ["except*"], (
        "the set of non-identifier keywords changed; the blurb names except* "
        "specifically and would now be wrong"
    )
    assert "except `except*`" in card


def test_the_pack_ids_the_card_calls_out_really_do_differ_from_bcp47() -> None:
    """The join advice must stay true to the registry it describes."""
    registry = export_packs.load_registry()
    assert registry["no"]["bcp47"] == "nb"
    assert registry["zh"]["bcp47"] == "zh-Hans"


class TestTheNormalizationNote:
    """The NFKC caveat is measured from the rows, never written down."""

    def test_it_names_the_measured_count_locale_and_character(self) -> None:
        card = export_packs.render_card(
            _manifest(export_packs.pack_locales()),
            {"MIT": 1},
            _locale_rows(export_packs.pack_locales()),
            _term_rows(),
        )
        assert "## Normalization" in card
        assert "PEP 3131" in card
        assert "22 renderings in this release are NFKC-unstable" in card
        assert "Thai (`th`)" in card
        assert "`U+0E33` THAI CHARACTER SARA AM" in card

    def test_it_follows_the_data_rather_than_a_hard_coded_figure(self) -> None:
        """A different measurement must produce a different sentence.

        This is the whole point of deriving it: the packs are regenerated, so a
        count written into the template would outlive the thing it counted.
        """
        card = export_packs.render_card(
            _manifest(
                export_packs.pack_locales(),
                nfkc={
                    "rows": 5,
                    "renderings": 1,
                    "locales": [{"locale": "xx", "language_name": "Examplish"}],
                    "characters": [{"codepoint": "U+FFFF", "name": "NOT A CHARACTER"}],
                },
            ),
            {"MIT": 1},
            _locale_rows(export_packs.pack_locales()),
            _term_rows(),
        )
        assert "One rendering in this release is NFKC-unstable" in card
        assert "Examplish (`xx`)" in card
        assert "22 renderings" not in card

    def test_an_all_stable_release_says_so(self) -> None:
        """The empty branch must be a true statement, not a missing section."""
        card = export_packs.render_card(
            _manifest(
                export_packs.pack_locales(),
                nfkc={"rows": 0, "renderings": 0, "locales": [], "characters": []},
            ),
            {"MIT": 1},
            _locale_rows(export_packs.pack_locales()),
            _term_rows(),
        )
        assert "## Normalization" in card
        assert "No rendering in this release is NFKC-unstable" in card

    def test_the_measurement_reads_the_emitted_rows(self) -> None:
        measured = export_packs.nfkc_instability(
            [
                {"locale": "th", "language_name": "Thai", "translation": "ทำ"},
                {"locale": "th", "language_name": "Thai", "translation": "ทำ"},
                {"locale": "es", "language_name": "Spanish", "translation": "para"},
            ]
        )
        # Two rows, one distinct rendering, one locale, one character.
        assert measured["rows"] == 2
        assert measured["renderings"] == 1
        assert measured["locales"] == [{"locale": "th", "language_name": "Thai"}]
        assert measured["characters"] == [
            {"codepoint": "U+0E33", "name": "THAI CHARACTER SARA AM"}
        ]

    def test_a_stable_vocabulary_measures_as_empty(self) -> None:
        measured = export_packs.nfkc_instability(
            [{"locale": "es", "language_name": "Spanish", "translation": "para"}]
        )
        assert measured == {
            "rows": 0,
            "renderings": 0,
            "locales": [],
            "characters": [],
        }

    def test_the_shipped_vocabulary_matches_what_the_card_will_say(
        self, rows: list[dict]
    ) -> None:
        """Measured over the real rows, so the class the card describes is real.

        The card asserts the instability is confined to one character class. If
        a regenerated pack introduces a second one, the card says so on its own
        — but the claim that it is a SMALL, single-character class is worth
        knowing about the moment it stops being true.
        """
        measured = export_packs.nfkc_instability(rows)
        assert measured["characters"] == [
            {"codepoint": "U+0E33", "name": "THAI CHARACTER SARA AM"}
        ], f"a new NFKC-instability class appeared: {measured['characters']}"


# ---------------------------------------------------------------------------
# The publish surface
# ---------------------------------------------------------------------------


#: The publish-surface rule as a pattern. Case-insensitive because `source.tag`
#: is rendered verbatim into the card's provenance line and a branch or tag
#: named for the release ticket arrives lowercased, which a case-sensitive
#: match would wave through. ``\b`` so an ordinary word merely ending in the
#: prefix -- ``score-12`` -- is not read as a ticket.
TICKET = re.compile(r"\b(?:CORE|HOME)-\d+", re.IGNORECASE)


def test_the_ticket_pattern_matches_the_forms_that_reach_the_card() -> None:
    """A form the pattern misses is a leak the guard permits."""
    assert TICKET.search("still being defined** (CORE-1513).")
    assert TICKET.search("the announcement (HOME-44)")
    assert TICKET.search("commit `abc123` (core-1905)")  # a lowercased git tag
    assert not TICKET.search("score-12")
    assert not TICKET.search("CORE-")


@pytest.fixture(scope="module")
def exported(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run the export once and return the output directory."""
    out = tmp_path_factory.mktemp("canon") / "packs"
    with mock.patch.object(sys, "argv", ["export_packs.py", "--out", str(out)]):
        assert export_packs.main() == 0
    return out


def test_no_published_file_cites_an_internal_ticket(exported: Path) -> None:
    """Nothing a reader can see may reference a Linear issue.

    The card and the files beside it are read outside the project, where a
    bare ``CORE-####`` is an unresolvable reference. This is a publish-surface
    rule, not a style preference, so it is asserted over every file the export
    writes -- walked from the output tree rather than listed here, so a file
    the artifact gains later is covered without anyone remembering to add it.
    """
    import pyarrow.parquet as pq

    files = sorted(p for p in exported.rglob("*") if p.is_file())
    assert files, "the export wrote nothing; the guard would pass vacuously"

    for path in files:
        name = path.relative_to(exported)
        if path.suffix == ".parquet":
            # Parquet is compressed, so the bytes on disk are not searchable.
            # The values have to be decoded before they can be cleared.
            text = str(pq.read_table(path).to_pydict())
        else:
            # Bytes with undecodable sequences dropped, not `read_text`. The
            # sibling corpus card ships a banner PNG and this artifact may
            # gain one; a UnicodeDecodeError there would be the guard falling
            # over rather than the rule being broken.
            text = path.read_bytes().decode("utf-8", errors="ignore")
        assert not TICKET.search(text), f"{name} cites an internal ticket"


def test_the_cards_conditional_sections_cite_no_internal_ticket() -> None:
    """The rule reaches the card branch today's data never renders.

    :func:`test_no_published_file_cites_an_internal_ticket` runs the real
    export, so it only ever sees the card the CURRENT data produces, in which
    every pack agrees with the declared license. The license caveat is dark
    under that data, so a ticket reference reintroduced into it would ship on
    the first license drift with nothing having failed. It is rendered here
    from a synthetic manifest.
    """
    locales = export_packs.pack_locales()

    # Rendered only when the packs' own metadata.license contradicts
    # DECLARED_LICENSE, which the shipped packs no longer do.
    caveat = export_packs.render_card(
        _manifest(locales), {"MIT": 255}, _locale_rows(locales), _term_rows()
    )
    assert "Note on the license field" in caveat, "the caveat branch went dark"
    assert not TICKET.search(caveat)


def test_push_refuses_without_the_governance_signoff() -> None:
    with pytest.raises(export_packs.ExportRefused, match="governance-signoff"):
        export_packs.require_push_approval(None)
    with pytest.raises(export_packs.ExportRefused, match="governance-signoff"):
        export_packs.require_push_approval("CORE-0000")


def test_push_refuses_without_the_env_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The flag and the variable are two keys on purpose."""
    monkeypatch.delenv(export_packs.PUSH_ENV_VAR, raising=False)
    with pytest.raises(export_packs.ExportRefused, match=export_packs.PUSH_ENV_VAR):
        export_packs.require_push_approval(export_packs.GOVERNANCE_TICKET)

    monkeypatch.setenv(export_packs.PUSH_ENV_VAR, "1")
    export_packs.require_push_approval(export_packs.GOVERNANCE_TICKET)


def test_the_canonical_target_needs_no_second_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(export_packs.TARGET_OVERRIDE_ENV_VAR, raising=False)
    export_packs.require_intended_target(export_packs.DEFAULT_TARGET_REPO)


def test_a_non_default_target_must_be_repeated_verbatim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A typo must not be able to publish into the wrong namespace."""
    monkeypatch.delenv(export_packs.TARGET_OVERRIDE_ENV_VAR, raising=False)
    with pytest.raises(export_packs.ExportRefused, match="not the canonical"):
        export_packs.require_intended_target("someone-else/language-packs")

    monkeypatch.setenv(export_packs.TARGET_OVERRIDE_ENV_VAR, "someone-else/other")
    with pytest.raises(export_packs.ExportRefused, match="not the canonical"):
        export_packs.require_intended_target("someone-else/language-packs")

    monkeypatch.setenv(
        export_packs.TARGET_OVERRIDE_ENV_VAR, "someone-else/language-packs"
    )
    export_packs.require_intended_target("someone-else/language-packs")


def _source(**overrides: str) -> dict[str, str]:
    base = {
        "worktree": "clean",
        "commit": "abc123",
        "tag": export_packs.RELEASE_TAG,
    }
    base.update(overrides)
    return base


def test_push_refuses_a_dirty_or_unverifiable_worktree() -> None:
    """A pinned revision must rebuild from the commit its manifest names."""
    export_packs.require_reproducible_source(_source())

    for worktree in ("dirty", "unknown (git unavailable)"):
        with pytest.raises(export_packs.ExportRefused, match="worktree is"):
            export_packs.require_reproducible_source(_source(worktree=worktree))


def test_push_refuses_an_untagged_commit() -> None:
    """The tag is the one version string the Hub, Linear and the card share.

    An untagged push leaves the revision with no name its release ticket also
    knows.
    """
    with pytest.raises(export_packs.ExportRefused, match="not 'language-packs-v"):
        export_packs.require_reproducible_source(_source(tag=export_packs.UNTAGGED))

    # Absent key is treated as untagged rather than passing by omission.
    with pytest.raises(export_packs.ExportRefused, match="not 'language-packs-v"):
        export_packs.require_reproducible_source(
            {"worktree": "clean", "commit": "abc123"}
        )


def test_the_gate_refuses_a_packs_tag_for_a_different_version() -> None:
    """A tag with the right shape but the wrong version must not pass.

    This is the hole the earlier prefix check left open, and it is the one that
    actually ships a lie: a commit still carrying ``language-packs-v2026.08.24``
    would satisfy "starts with the prefix" while the build declares a different version,
    publishing a revision under a version it does not claim. Unlike an untagged
    commit, nothing downstream would look wrong.
    """
    stale = f"{export_packs.TAG_PREFIX}2026.08.24"
    with pytest.raises(export_packs.ExportRefused, match="not 'language-packs-v"):
        export_packs.require_reproducible_source(_source(tag=stale))

    # ...and so must the next version's tag on this version's build, which is
    # the same failure walking the other way.
    ahead = f"{export_packs.TAG_PREFIX}9.9.9"
    with pytest.raises(export_packs.ExportRefused, match="not 'language-packs-v"):
        export_packs.require_reproducible_source(_source(tag=ahead))


def test_the_card_states_the_release_version(exported: Path) -> None:
    """The card has to name its own version, or nothing published does.

    It used to borrow one from the git tag it quoted in the provenance line.
    That line is suppressed while the monorepo is private, so without this the
    artifact would ship announcing no version at all.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    assert f"`{export_packs.DATASET_VERSION}`" in card

    manifest = json.loads((exported / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == export_packs.DATASET_VERSION, (
        "the card and the manifest must state one version, not two"
    )


def test_the_card_cites_the_revision_the_manifest_records(exported: Path) -> None:
    """The card and the manifest must name ONE revision, not two.

    They are written from the same ``source`` block, so a drift here means the
    card was rendered from something other than the export it describes -- the
    failure that let a card documenting one provenance vocabulary ship over
    data carrying another.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    manifest = json.loads((exported / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["source"]["commit"][:12] in card

    # A dry-run export must not render "(untagged)" as if it were a revision
    # anyone could fetch. The tag itself is the push gate's business, not the
    # card's, so the card names the commit and stops there.
    assert export_packs.UNTAGGED not in card


def test_the_card_never_tells_a_reader_to_install_an_unpublished_package(
    exported: Path,
) -> None:
    """An install command for a package that 404s is a lie the card tells.

    Every ``legesher-i18n-python-<locale>`` is unpublished (CORE-626). The card
    names the distributions, because the `packs` config points at them by
    version, and stops short of telling anyone to install one. The paragraph
    that used to say so out loud was cut; this is the floor that remains.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")

    assert "legesher-i18n-python-ar" in card
    assert "pip install" not in card, (
        "the card tells the reader to install a package that is not published"
    )


def test_the_banner_ships_and_the_manifest_accounts_for_it(exported: Path) -> None:
    """The card links its banner relatively, so the file has to ride along.

    Three things have to line up or the dataset page shows a broken image, or
    ships a file nothing accounts for: the card references it, the export
    writes it, and the manifest checksums it. The first version of this copied
    the image AFTER the manifest was built, so the card's own promise of "a
    SHA-256 for every file" was false about the one file it had just added.
    """
    import fnmatch

    target = export_packs.CARD_IMAGE_TARGET.as_posix()

    card = (exported / "README.md").read_text(encoding="utf-8")
    assert f"({target})" in card, "the card does not link its banner"

    assert (exported / target).is_file(), "the banner was not written"

    manifest = json.loads((exported / "manifest.json").read_text(encoding="utf-8"))
    assert target in dict(manifest["files"]), (
        "the banner ships without a checksum, contradicting the card"
    )

    assert any(
        fnmatch.fnmatch(target, pattern) for pattern in export_packs.PUSH_ALLOW_PATTERNS
    ), "the banner is built but would be left out of the upload"


def test_the_export_refuses_when_the_banner_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing source image must stop the export, not ship a broken page."""
    monkeypatch.setattr(export_packs, "CARD_IMAGE_SOURCE", tmp_path / "not-here.png")
    with pytest.raises(SystemExit, match="banner image is missing"):
        export_packs.require_card_image()


def test_the_card_carries_no_em_dashes(exported: Path) -> None:
    """House voice, and a rule prose drifts back into without a guard.

    The Legesher voice charter (CORE-1465) rules them out of titles and asks
    that body copy avoid them. This card had 33 before the pass that removed
    them, all added a few at a time.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    offenders = [line for line in card.splitlines() if "—" in line]
    assert not offenders, "em dashes in the card:\n" + "\n".join(offenders[:8])


def test_the_locale_count_is_stated_once(exported: Path) -> None:
    """One source of truth reads as several when repeated per section.

    The count belongs in the opening and nowhere else. Restating it in the
    languages table, the maturity section and the citation made a single fact
    look like four claims that could drift apart.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    manifest = json.loads((exported / "manifest.json").read_text(encoding="utf-8"))
    count = str(manifest["counts"]["locales"])

    hits = [line for line in card.splitlines() if re.search(rf"\b{count}\b", line)]
    assert len(hits) == 1, (
        f"the locale count ({count}) appears {len(hits)} times; state it once "
        f"in the opening:\n" + "\n".join(hits)
    )


def test_the_release_tag_is_built_from_the_declared_version() -> None:
    """One source of truth, so the tag cannot drift from what the card says.

    If these were maintained separately, the gate would compare two strings
    that agree only by someone remembering to edit both.
    """
    assert export_packs.RELEASE_TAG == (
        f"{export_packs.TAG_PREFIX}{export_packs.DATASET_VERSION}"
    )

    # Semantic, not date-based. A date would parse as three ints too, so this
    # asserts the shape a consumer can actually order: no component may carry
    # a leading zero the way `2026.08.24` does.
    parts = export_packs.DATASET_VERSION.split(".")
    assert len(parts) == 3, export_packs.DATASET_VERSION
    for part in parts:
        assert part.isdigit(), export_packs.DATASET_VERSION
        assert part == str(int(part)), (
            f"{export_packs.DATASET_VERSION} is not semver -- {part!r} is "
            f"zero-padded, which is the date shape this replaced"
        )


def test_the_gate_refuses_every_tag_that_is_not_a_packs_tag() -> None:
    """The repo tags a lot, and only one shape names a revision of THIS dataset.

    `v0.24.0`, `mcp-v0.1.0` and the per-pack `i18n-python-ar-v0.0.4` all sit on
    release commits. Accepting any of them would stamp a version string this
    dataset does not have -- which is the failure the gate exists to prevent,
    not a near-miss of it.
    """
    for tag in ("v0.24.0", "mcp-v0.1.0", "i18n-python-ar-v0.0.4", "scratch"):
        with pytest.raises(export_packs.ExportRefused, match="not 'language-packs-v"):
            export_packs.require_reproducible_source(_source(tag=tag))

    export_packs.require_reproducible_source(_source(tag=export_packs.RELEASE_TAG))


def test_git_describe_only_ever_reports_a_packs_tag(tmp_path: Path) -> None:
    """The producer and the gate must agree, or the gate is dead in practice.

    Built on a real repo carrying a decoy tag alongside the packs tag, because
    the bug this guards against is `git describe --exact-match` returning
    whichever of several tags it likes.
    """
    import subprocess

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "f").write_text("x", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "c")

    assert export_packs.git_describe(tmp_path)["tag"] == export_packs.UNTAGGED

    git("tag", "v9.9.9")
    assert export_packs.git_describe(tmp_path)["tag"] == export_packs.UNTAGGED, (
        "a non-packs tag must not satisfy the gate"
    )

    git("tag", export_packs.RELEASE_TAG)
    assert export_packs.git_describe(tmp_path)["tag"] == export_packs.RELEASE_TAG


def test_published_schema_is_the_four_decided_configs(exported: Path) -> None:
    """CORE-2022: every config's published columns are exactly the decided set.

    Asserted on the written Parquet, not the builders, because the builders
    deliberately keep fuller dicts.
    """
    import pyarrow.parquet as pq

    expected = {
        "vocabulary": export_packs.VOCABULARY_COLUMNS,
        "locales": export_packs.LOCALE_COLUMNS,
        "pl_terminology": export_packs.PL_TERMINOLOGY_COLUMNS,
        "packs": export_packs.PACKS_COLUMNS,
    }
    for name, columns in expected.items():
        table = pq.read_table(exported / "data" / f"{name}.parquet")
        assert tuple(table.column_names) == columns, name

    # The loop proved the parquet columns ARE the constants, so the rest
    # asserts on the constants: per-locale facts stay out of vocabulary,
    # per-pairing state stays out of locales, and the vocabulary key keeps
    # `target` and `category` (the join spans targets, and `type` is rendered
    # once as a keyword and once as a builtin).
    assert not {"language_name", "native_name", "rtl"} & set(
        export_packs.VOCABULARY_COLUMNS
    )
    assert not {"tier", "package_version", "terms_latest", "pack_versions"} & set(
        export_packs.LOCALE_COLUMNS
    ), "(locale x target) facts belong in `packs`"
    assert {"target", "category"} <= set(export_packs.VOCABULARY_COLUMNS)


def test_package_version_matches_each_pack_pyproject(exported: Path) -> None:
    """The alignment claim the card makes has to be true of the bytes.

    A row reading `ar` / `0.0.4` says these words are in
    `legesher-i18n-python-ar==0.0.4`. If the column drifts from the pyproject
    the export is describing, the dataset misstates which package it matches.
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(exported / "data" / "packs.parquet").to_pylist()
    assert rows

    for row in rows:
        declared = export_packs.read_package_version(row["locale"])
        assert row["package_version"] == declared, (
            f"{row['locale']}: dataset says {row['package_version']}, "
            f"pyproject says {declared}"
        )
        assert row["package_version"], "a pairing must not publish a null version"
        assert row["target"] == "python"


@NEEDS_UNICODE_15_1
def test_main_wires_every_push_gate_and_pushes_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deleting the `if args.push:` block must fail something.

    Every other gate test calls the helpers directly, so without this the whole
    wiring could be dropped and the suite would stay green -- with the first
    symptom being a published revision.
    """
    called: list[str] = []

    def _record(name: str, result: object = None):
        def _fn(*_a: object, **_k: object) -> object:
            called.append(name)
            return result

        return _fn

    monkeypatch.setattr(export_packs, "preflight_hub_auth", _record("auth"))
    monkeypatch.setattr(export_packs, "push_to_hub", _record("push"))
    monkeypatch.setenv(export_packs.PUSH_ENV_VAR, "1")
    monkeypatch.setattr(
        export_packs,
        "git_describe",
        lambda _repo: _source(tag=export_packs.RELEASE_TAG),
    )

    out = tmp_path / "packs"
    argv = [
        "export_packs.py",
        "--out",
        str(out),
        "--push",
        "--governance-signoff",
        export_packs.GOVERNANCE_TICKET,
    ]
    with mock.patch.object(sys, "argv", argv):
        assert export_packs.main() == 0

    assert called == ["auth", "push"], (
        "auth must be proven before the export, and the push must come last -- "
        f"after the determinism check, not before it. Got {called}"
    )
    # --push forces the determinism proof on, whether or not it was asked for.
    assert (out.parent / f"{out.name}-verify").exists()


def test_main_refuses_push_flags_without_push(tmp_path: Path) -> None:
    """A forgotten --push must not exit 0 looking like a successful publish."""
    argv = [
        "export_packs.py",
        "--out",
        str(tmp_path / "packs"),
        "--governance-signoff",
        export_packs.GOVERNANCE_TICKET,
    ]
    with mock.patch.object(sys, "argv", argv):
        with pytest.raises(SystemExit, match="push options"):
            export_packs.main()


def test_the_push_never_changes_visibility_and_cites_no_internal_ticket() -> None:
    """Hub commit history is as public as the files it carries.

    This rule used to live in the runbook, because the artifact was pushed by
    hand and only an operator could carry it. Now the push is code, so a test
    carries it -- matching ``test_export_corpus.py``.
    """
    recorded: dict[str, object] = {}

    class _Api:
        def create_repo(self, **kwargs: object) -> None:
            recorded["create"] = kwargs

        def upload_folder(self, **kwargs: object) -> None:
            recorded.update(kwargs)

    with mock.patch.object(export_packs, "_require_hf_api", lambda: lambda: _Api()):
        export_packs.push_to_hub(Path("/tmp/nowhere"), export_packs.DEFAULT_TARGET_REPO)

    assert not TICKET.search(str(recorded["commit_message"]))

    # Private-first, always. Going public stays a deliberate act on the Hub,
    # so no invocation of this script can publish a private dataset.
    create = recorded["create"]
    assert isinstance(create, dict)
    assert create["private"] is True
    assert "public" not in str(recorded).lower()


def test_the_allow_list_covers_every_file_the_export_writes(exported: Path) -> None:
    """An upload allow-list that misses a file drops it silently.

    Walked from the real output tree rather than listed here, so a file the
    artifact gains later fails this instead of vanishing from the dataset.
    """
    import fnmatch

    written = sorted(
        str(p.relative_to(exported)) for p in exported.rglob("*") if p.is_file()
    )
    assert written, "the export produced no files"

    uncovered = [
        name
        for name in written
        if not any(
            fnmatch.fnmatch(name, pattern)
            for pattern in export_packs.PUSH_ALLOW_PATTERNS
        )
    ]
    assert not uncovered, (
        f"PUSH_ALLOW_PATTERNS does not cover {uncovered} -- these files would "
        f"be built and then silently left out of the upload"
    )


def test_no_published_file_mentions_the_sibling_datasets(exported: Path) -> None:
    """This artifact describes itself and nothing else.

    The packs card used to open by positioning the packs against the canon and
    spend a section choosing between three datasets. That is not what a reader
    who landed here came for, and a card that explains its neighbours is a card
    that has to be re-edited whenever they change.

    Asserted over every published file rather than the card alone, because the
    manifest sits beside it and was making the same claim in prose.
    """
    import pyarrow.parquet as pq

    offenders: list[str] = []
    for path in sorted(exported.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".parquet":
            text = " ".join(
                str(v) for v in pq.read_table(path).to_pydict().get("locale", [])
            )
        elif path.suffix == ".png":
            # The card's banner. Binary, and its filename is checked by the
            # sweep below like every other path, so there is no text to read.
            continue
        else:
            text = path.read_text(encoding="utf-8")
        for word in ("language-canon", "language-corpus"):
            if word in text:
                offenders.append(f"{path.relative_to(exported)}: {word}")
        # `canon_selections` is a table name, not a pointer at the dataset.
        for word in ("the canon", "the corpus"):
            if word in text.lower():
                offenders.append(f"{path.relative_to(exported)}: {word!r}")

    assert not offenders, f"published files point at a sibling dataset: {offenders}"


# --- the four-config split (CORE-2022) --------------------------------------


@pytest.fixture(scope="module")
def terminology(rows: list[dict]) -> list[dict]:
    """Derived from the SAME rows instance the integrity test joins against.

    Building from scratch here would double the module's most expensive
    setup and make the referential-integrity test validate a join between
    two independently built row sets -- one the export never performs.
    """
    return export_packs.build_pl_terminology(rows)


def test_pl_terminology_covers_every_category_family(terminology: list[dict]) -> None:
    """286 rows: 184 terms + 33 symbols + 15 conventions + 54 messages.

    54, not the seed's 55 entries: CPython reworded one message at 3.11 and
    the seed carries both wordings under one key, which the grain merges.
    """
    from collections import Counter

    by_family = Counter(r["category"] for r in terminology)
    assert by_family["symbols"] == 33
    assert by_family["variable_conventions"] == 15
    assert by_family["messages"] == 54
    term_rows = sum(by_family[s] for s in export_packs.SECTIONS)
    assert term_rows == 184
    assert set(by_family) == set(export_packs.CATEGORY_FAMILIES)
    assert all(r["target"] == "python" for r in terminology)


def test_type_carries_two_rows_with_their_own_validity(
    terminology: list[dict],
) -> None:
    """The one term in two categories, each with its own set and kind."""
    rows = {r["category"]: r for r in terminology if r["source_term"] == "type"}
    assert set(rows) == {"keywords", "builtins"}
    assert rows["builtins"]["subcategory"] == "builtin_type"
    assert rows["builtins"]["pl_versions"] == list(export_packs.VERSIONS)
    assert rows["keywords"]["subcategory"] == "keyword"
    assert rows["keywords"]["pl_versions"] == ["3.12", "3.13", "3.14"]


def test_every_term_subcategory_is_admitted_by_its_section(
    terminology: list[dict],
) -> None:
    """A subcategory outside its section's kinds means the taxonomy drifted."""
    from legesher_i18n.term_definitions import YAML_SECTION_CATEGORIES

    for row in terminology:
        if row["category"] in export_packs.SECTIONS:
            assert row["subcategory"] in YAML_SECTION_CATEGORIES[row["category"]], row


def test_messages_come_from_the_tracked_seed_with_version_windows(
    terminology: list[dict],
) -> None:
    """The messages category reads the seed file, never the database.

    CPython reworded ``UnboundLocalError.before_assignment`` at 3.11, and the
    seed carries both wordings as separate version-windowed entries. For this
    config that is ONE term whose English surface changed -- so it merges to a
    single row: union validity, latest wording. The old wording must NOT
    surface as a phantom "removed at 3.11" term.
    """
    messages = [r for r in terminology if r["category"] == "messages"]
    # `is not None`, not truthiness: three templates have a legitimately EMPTY
    # English surface (a bare `assert`, StopIteration with no value,
    # KeyboardInterrupt) -- the empty string IS the template, matcher `^$`.
    assert all(r["source_text"] is not None for r in messages), (
        "a message row without its English template is a key with no content"
    )

    reworded = [
        r for r in messages if r["source_term"] == "UnboundLocalError.before_assignment"
    ]
    assert len(reworded) == 1, "the seed's duplicate key must merge, not repeat"
    assert reworded[0]["pl_versions"] == list(export_packs.VERSIONS)
    assert reworded[0]["source_text"].startswith("cannot access local variable"), (
        "the merged row must carry the CURRENT wording, matching the JSON's "
        "union-at-latest convention"
    )

    windowed = [r for r in messages if r["pl_versions"] != list(export_packs.VERSIONS)]
    assert all(
        r["pl_versions"] == sorted(r["pl_versions"], key=export_packs.VERSIONS.index)
        for r in windowed
    )


def test_message_subcategory_is_the_keys_leading_component(
    terminology: list[dict],
) -> None:
    """Total grouping, no null bucket beside deliberate nulls.

    The seed's `cluster` field covers a minority of templates; a column the
    card documents as "the message cluster" that is null for most rows
    collapses "uncurated" onto the symbols rows' by-design nulls. The key
    convention is `<Surface>.<slug>`, and the leading component is a real,
    total grouping.
    """
    messages = [r for r in terminology if r["category"] == "messages"]
    for row in messages:
        assert row["subcategory"] == row["source_term"].split(".", 1)[0]


def test_message_windows_agree_with_the_runtime_catalog(
    terminology: list[dict],
) -> None:
    """Shared vectors against messages.py -- one window contract, not two.

    load_catalog resolves validity by numeric comparison; the exporter must
    agree on every published row, or the dataset documents behaviour the
    runtime does not have. Vectors include the case index-membership
    semantics got wrong: a boundary OUTSIDE the shipped range.
    """
    from legesher_i18n.messages import _parse_version

    def runtime_valid(version: str, added: str, removed: str | None) -> bool:
        if _parse_version(added) > _parse_version(version):
            return False
        return not (removed and _parse_version(removed) <= _parse_version(version))

    vectors = [
        ("3.10", None),
        ("3.11", None),
        ("3.10", "3.11"),
        ("3.12", "3.14"),
        ("3.15", None),  # future add: valid nowhere in range
        ("3.10", "3.9"),  # removed before range: valid nowhere
        ("3.8", None),  # added before range: valid everywhere
    ]
    for added, removed in vectors:
        expected = [
            v for v in export_packs.VERSIONS if runtime_valid(v, added, removed)
        ]
        assert export_packs._message_pl_versions(added, removed) == expected, (
            added,
            removed,
        )


def test_pl_terminology_grain_is_unique(terminology: list[dict]) -> None:
    """One row per (target, category, source_term) -- the declared grain."""
    from collections import Counter

    keys = Counter((r["target"], r["category"], r["source_term"]) for r in terminology)
    duplicated = {k: n for k, n in keys.items() if n > 1}
    assert not duplicated, duplicated


def test_source_text_is_present_exactly_when_the_key_is_not_the_text(
    terminology: list[dict],
) -> None:
    for row in terminology:
        if row["category"] in export_packs.SECTIONS:
            assert row["source_text"] is None, (
                f"{row['source_term']}: a term's source_term IS its English"
            )
        else:
            # Empty string is a real value here (see the messages test);
            # absence is the defect.
            assert row["source_text"] is not None, (
                f"{row['source_term']}: slug/key rows must carry the English"
            )


def test_every_vocabulary_row_is_inside_its_terms_validity_set(
    rows: list[dict], terminology: list[dict]
) -> None:
    """Referential integrity between the fact table and the dimension.

    This is the join the gap queries stand on: a vocabulary row whose
    (category, source_term, pl_version) is not covered by pl_terminology's
    validity set is a rendering of a term the dataset claims does not exist
    there.
    """
    valid = {
        (r["category"], r["source_term"]): set(r["pl_versions"]) for r in terminology
    }
    orphans = [
        r
        for r in rows
        if r["pl_version"] not in valid.get((r["category"], r["source_term"]), set())
    ]
    assert not orphans, (
        f"{len(orphans)} vocabulary rows outside validity: {orphans[:3]}"
    )


def test_the_known_gaps_are_the_expected_ones(
    rows: list[dict], terminology: list[dict]
) -> None:
    """symbols, variable_conventions and messages ship source-side only today.

    The inventory is deliberately ahead of the renderings — that is what makes
    the gap measurable. If this test fails because renderings EXIST, the gap
    closed: delete the expectation, not the mechanism.
    """
    rendered_categories = {r["category"] for r in rows}
    inventory_categories = {r["category"] for r in terminology}
    assert inventory_categories - rendered_categories == {
        "symbols",
        "variable_conventions",
        "messages",
    }


def test_packs_rows_are_one_per_pairing(exported: Path) -> None:
    import pyarrow.parquet as pq

    packs = pq.read_table(exported / "data" / "packs.parquet").to_pylist()
    locales = pq.read_table(exported / "data" / "locales.parquet").to_pylist()
    assert len(packs) == len(locales) == 51
    assert {r["locale"] for r in packs} == {r["locale"] for r in locales}
    assert all(r["pl_versions"] == list(export_packs.VERSIONS) for r in packs)


def test_json_is_one_loadable_file_per_pairing(exported: Path) -> None:
    """json/<locale>/<target>.json: translations alone, semver and range."""
    import json as jsonlib

    files = sorted((exported / "json").rglob("*.json"))
    assert len(files) == 51
    assert all(f.name == "python.json" for f in files)

    ar = jsonlib.loads((exported / "json" / "ar" / "python.json").read_text("utf-8"))
    assert ar["package_version"] == export_packs.read_package_version("ar")
    assert ar["pl_version_range"] == "3.10-3.14"
    # Union across the range: a mid-range arrival is present.
    assert "type" in {k.lower() for k in ar["keywords"]}
    # Translations alone -- no per-term structure.
    flat = set(ar) - {
        "locale",
        "target",
        "package_version",
        "tier",
        "pl_version_range",
    }
    assert flat <= set(export_packs.CATEGORY_FAMILIES)
    for section in flat:
        assert all(isinstance(v, str) for v in ar[section].values())


def test_json_union_carries_the_latest_rendering(
    exported: Path, rows: list[dict]
) -> None:
    """Sinhala's 3.13 conjunct redefinitions appear in their current form."""
    import json as jsonlib

    si = jsonlib.loads((exported / "json" / "si" / "python.json").read_text("utf-8"))
    latest = next(
        r["translation"]
        for r in rows
        if r["locale"] == "si"
        and r["source_term"] == "True"
        and r["pl_version"] == "3.14"
    )
    earliest = next(
        r["translation"]
        for r in rows
        if r["locale"] == "si"
        and r["source_term"] == "True"
        and r["pl_version"] == "3.10"
    )
    assert latest != earliest, "fixture assumption broken: si stopped redefining True"
    assert si["keywords"]["True"] == latest


def test_uniformity_gate_ignores_the_unevenly_rolling_families() -> None:
    """symbols/messages arriving for SOME locales must not fail uniformity.

    "Every locale ships the same term set" is a claim about the term
    sections; the vocabulary families roll out unevenly by design -- that is
    the measurable gap, not a defect.
    """
    term_rows = [
        {"locale": loc, "pl_version": v, "category": "keywords", "source_term": "for"}
        for loc in ("aa", "bb")
        for v in export_packs.VERSIONS
    ]
    uneven = [
        {
            "locale": "aa",
            "pl_version": "3.14",
            "category": "symbols",
            "source_term": "colon",
        }
    ]
    counts = export_packs.terms_per_version(term_rows + uneven)
    assert counts == dict.fromkeys(export_packs.VERSIONS, 1)


def test_null_version_added_ranks_by_the_shared_resolution(
    rows: list[dict], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit null version_added must not demote the current wording.

    The window resolution treats null as the seed default; if the wording
    ranking resolved it independently (ranking null lowest), a null-added
    rewording would publish the superseded template as the English surface.
    One resolution feeds both.
    """
    import json as jsonlib

    seed = {
        "implementation": "cpython",
        "version_added": "3.12",
        "templates": [
            {
                "key": "X.reworded",
                "template_en": "old wording",
                "version_added": "3.10",
                "version_removed": "3.12",
            },
            {
                # Explicit null: resolves to the seed default (3.12), which
                # outranks 3.10 -- this is the CURRENT wording.
                "key": "X.reworded",
                "template_en": "current wording",
                "version_added": None,
            },
        ],
    }
    path = tmp_path / "seed.json"
    path.write_text(jsonlib.dumps(seed), encoding="utf-8")
    monkeypatch.setattr(export_packs, "MESSAGES_SEED", path)

    terminology = export_packs.build_pl_terminology(rows)
    row = next(r for r in terminology if r["source_term"] == "X.reworded")
    assert row["source_text"] == "current wording"
    assert row["pl_versions"] == list(export_packs.VERSIONS)


# Every test built on the every-tier export needs the identifier rules of the
# ja and si 3.13+ tiers (tests/interpreter_gaps.py). One rule, applied here to
# each test, module-level or in a class, that takes one of the fixtures that
# run the export, rather than a marker on each test.
_EVERY_TIER_FIXTURES = frozenset({"rows", "exported", "terminology"})


def _runs_the_export(test: object) -> bool:
    return bool(_EVERY_TIER_FIXTURES & set(inspect.signature(test).parameters))


for _name, _obj in list(globals().items()):
    if _name.startswith("test_") and _runs_the_export(_obj):
        globals()[_name] = NEEDS_UNICODE_15_1(_obj)
    elif _name.startswith("Test") and isinstance(_obj, type):
        for _method_name, _method in list(vars(_obj).items()):
            if _method_name.startswith("test_") and _runs_the_export(_method):
                setattr(_obj, _method_name, NEEDS_UNICODE_15_1(_method))
