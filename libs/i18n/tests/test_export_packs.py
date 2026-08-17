"""Guards on the canon-packs export (CORE-1043).

The properties tested here are the ones whose failure would be discovered
after the dataset is public: the wrong locale count, a target this artifact
does not claim to cover, or a resolved row that misreports where its term is
defined.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

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

    per_pack = Counter((r["locale"], r["python_version"]) for r in rows)
    for version in export_packs.VERSIONS:
        sizes = {n for (_, v), n in per_pack.items() if v == version}
        assert len(sizes) == 1, f"locales disagree at {version}: {sorted(sizes)}"


def test_inheritance_is_resolved_and_labelled(rows: list[dict]) -> None:
    """A 3.12 pack carries only a delta; the export must resolve the rest.

    ``for`` is defined in the 3.10 base and must still appear on 3.12, flagged
    as inherited and pointing at 3.10 — the delta structure preserved rather
    than erased by the flattening.
    """
    match = [
        r
        for r in rows
        if r["locale"] == "es"
        and r["python_version"] == "3.12"
        and r["source_term"] == "for"
    ]
    assert len(match) == 1
    assert match[0]["defined_at"] == "3.10"
    assert match[0]["inherited"] is True

    # ``except*`` arrives with PEP 654 in 3.11, so on 3.11 it is defined, not
    # inherited.
    star = [
        r
        for r in rows
        if r["locale"] == "es"
        and r["python_version"] == "3.11"
        and r["source_term"] == "except*"
    ]
    assert len(star) == 1
    assert star[0]["defined_at"] == "3.11"
    assert star[0]["inherited"] is False


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
        r["python_version"]: r
        for r in rows
        if r["locale"] == "si" and r["source_term"] == "True"
    }
    early, late = by_version["3.10"], by_version["3.13"]
    assert early["translation"] != late["translation"], (
        "fixture assumption broken: si no longer redefines True at 3.13"
    )
    assert early["defined_at"] == "3.10"
    assert early["inherited"] is False
    assert late["defined_at"] == "3.13"
    assert late["inherited"] is False


def test_defined_at_never_points_forward(rows: list[dict]) -> None:
    """A row can only inherit from a version at or below its own."""
    order = {v: i for i, v in enumerate(export_packs.VERSIONS)}
    bad = [r for r in rows if order[r["defined_at"]] > order[r["python_version"]]]
    assert not bad, f"{len(bad)} row(s) claim a future definition: {bad[:3]}"


def test_the_row_value_matches_the_version_it_claims(rows: list[dict]) -> None:
    """``defined_at`` must be checkable: that pack's row carries this value."""
    at = {
        (r["locale"], r["python_version"], r["category"], r["source_term"]): r[
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
            "python_versions": len(export_packs.VERSIONS),
            "terms_per_locale_by_version": dict.fromkeys(export_packs.VERSIONS, 1),
        },
        "locales": locales,
        "tiers_present": tiers,
        "tier_counts": tier_counts or {"experimental": len(locales)},
        "nfkc_unstable": _NFKC_BLOCK if nfkc is None else nfkc,
        "source": {"commit": "0" * 40, "tag": "(untagged)"},
    }


def test_card_states_the_tiers_the_artifact_actually_carries() -> None:
    """The card must not hard-code "everything is experimental".

    Promoting one locale would otherwise publish a card contradicting its own
    `tier` column — the failure generation exists to prevent.
    """
    locales = export_packs.pack_locales()
    all_experimental = export_packs.render_card(_manifest(locales), {"MIT": 1})
    assert "Nothing has been promoted yet" in all_experimental
    assert f"All {len(locales)} locales are stamped" in all_experimental

    mixed = export_packs.render_card(
        _manifest(
            locales,
            tiers=["experimental", "reviewed"],
            tier_counts={"experimental": len(locales) - 1, "reviewed": 1},
        ),
        {"MIT": 1},
    )
    assert "Nothing has been promoted yet" not in mixed
    assert "`reviewed`" in mixed
    assert f"**{len(locales) - 1}** `experimental`" in mixed


def test_card_language_codes_survive_a_yaml_parse() -> None:
    """``no`` unquoted is YAML boolean false, which drops Norwegian.

    The Hub parses this frontmatter to build the language facet, so an
    unquoted code is a locale that silently vanishes from discovery.
    """
    import yaml

    locales = export_packs.pack_locales()
    card = export_packs.render_card(_manifest(locales), {"MIT": 255})
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
    card = export_packs.render_card(_manifest(locales), {"Apache-2.0": 255})
    assert "Note on the licence field" not in card

    # ...and it still appears when they genuinely differ.
    mixed = export_packs.render_card(_manifest(locales), {"MIT": 255})
    assert "Note on the licence field" in mixed


# ---------------------------------------------------------------------------
# What the card has to say out loud
# ---------------------------------------------------------------------------


def test_the_card_states_how_the_vocabulary_was_reviewed() -> None:
    """The provenance paragraph is not optional decoration (CORE-1905).

    A reader deciding whether to depend on these words needs to know they are
    machine-drafted and maintainer-curated, and that no native speaker has
    signed a pack off. The `experimental` stamp means that; the card must say
    it in words too.
    """
    card = export_packs.render_card(_manifest(export_packs.pack_locales()), {"MIT": 1})
    assert "Who chose these words" in card
    assert "drafted by a language model" in card
    assert "no pack in this release has been signed off by a native" in card
    assert "contributor rung" in card


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


def test_the_card_scopes_the_artifact_against_the_corpus() -> None:
    """Two joins-and-scope facts a consumer gets wrong without being told.

    The corpus holds Arabic renderings of JavaScript concepts that this dataset
    does not cover, and pack ids are not locale tags — `no` here is `nb` there.
    Someone joining on `locale` silently drops exactly the rows that differ.
    """
    card = export_packs.render_card(_manifest(export_packs.pack_locales()), {"MIT": 1})
    assert "Arabic" in card and "JavaScript" in card
    assert "`target` is\n`python` on every row in this dataset." in card
    assert "Join this dataset to the corpus on `bcp47`" in card
    assert "`no` here is `nb` in the corpus" in card


def test_the_pack_ids_the_card_calls_out_really_do_differ_from_bcp47() -> None:
    """The join advice must stay true to the registry it describes."""
    registry = export_packs.load_registry()
    assert registry["no"]["bcp47"] == "nb"
    assert registry["zh"]["bcp47"] == "zh-Hans"


class TestTheNormalizationNote:
    """The NFKC caveat is measured from the rows, never written down."""

    def test_it_names_the_measured_count_locale_and_character(self) -> None:
        card = export_packs.render_card(
            _manifest(export_packs.pack_locales()), {"MIT": 1}
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
    """The rule reaches the card branches today's data never renders.

    :func:`test_no_published_file_cites_an_internal_ticket` runs the real
    export, so it only ever sees the card the CURRENT data produces: every
    locale `experimental`, every pack agreeing with the declared licence. Two
    sections are dark under that data -- the licence caveat and the
    promoted-tier paragraph -- so a ticket reference reintroduced into either
    would ship on the first promotion, or the first licence drift, with
    nothing having failed. They are rendered here from synthetic manifests.
    """
    locales = export_packs.pack_locales()

    # Rendered only when the packs' own metadata.license contradicts
    # DECLARED_LICENSE, which the shipped packs no longer do.
    caveat = export_packs.render_card(_manifest(locales), {"MIT": 255})
    assert "Note on the licence field" in caveat, "the caveat branch went dark"
    assert not TICKET.search(caveat)

    # Rendered only once something has been promoted off `experimental`,
    # which nothing yet has.
    promoted = export_packs.render_card(
        _manifest(
            locales,
            tiers=["experimental", "reviewed", "official"],
            tier_counts={
                "experimental": len(locales) - 3,
                "reviewed": 2,
                "official": 1,
            },
        ),
        {"Apache-2.0": 255},
    )
    assert "Nothing has been promoted yet" not in promoted, (
        "the promoted-tier branch went dark"
    )
    assert not TICKET.search(promoted)
