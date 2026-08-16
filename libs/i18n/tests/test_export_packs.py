"""Guards on the canon-packs export (CORE-1043).

The properties tested here are the ones whose failure would be discovered
after the dataset is public: the wrong locale count, a target this artifact
does not claim to cover, or a resolved row that misreports where its term is
defined.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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


def _manifest(
    locales: list[str],
    tiers: list[str] | None = None,
    tier_counts: dict[str, int] | None = None,
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
