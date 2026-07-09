"""Extends-chain resolution for style guides (CORE-1354).

The loader resolves each guide's declared ``extends`` chain in full — base →
direction → script-family → language — so a language guide is assembled from
its whole ancestry. Since CORE-1398 the base and family overlays are
content-free structural nodes (all rules/profile content lives in the leaf
guide), so these tests assert:

  1. the chain resolves gap-free, base-first, for every language;
  2. the merged guide carries the leaf's rules/profile slots (``supports``
     flag set, ``naming.case_substitute``, ``script.direction``, font);
  3. the loader's merge semantics — last file wins, cycle detection, and the
     base+direction fallback when a language has no dedicated guide — via
     synthetic fixtures, since the real overlays no longer carry values to
     override.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legesher_i18n.style_guides import StyleGuideLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"
_LANGUAGES_JSON = Path(__file__).parent.parent / "legesher_i18n" / "languages.json"

# The exact ``supports`` flag set every merged guide must resolve (CORE-1393
# rules/profile schema).
_SUPPORTS_FLAGS = frozenset(
    {
        "case_distinction",
        "snake_case",
        "upper_snake_case",
        "pascal_case",
        "camel_case",
        "native_digits",
        "combining_marks",
        "requires_word_separator",
        "diacritics_in_identifiers",
        "cursive_joining",
    }
)


def _all_languages() -> dict[str, dict]:
    data = json.loads(_LANGUAGES_JSON.read_text(encoding="utf-8"))
    return data["languages"]


@pytest.fixture
def loader() -> StyleGuideLoader:
    return StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)


class TestChainResolvesForEveryLanguage:
    """Every language in languages.json resolves a gap-free chain."""

    @pytest.mark.parametrize("code", sorted(_all_languages()))
    def test_chain_is_gap_free(self, loader: StyleGuideLoader, code: str) -> None:
        chain = loader._resolve_hierarchy(code)
        assert chain, f"{code}: empty chain"
        assert chain[0].name == "python.yml", f"{code}: chain must start at python.yml"
        missing = [p.name for p in chain if not p.exists()]
        assert not missing, f"{code}: chain references missing files {missing}"

    @pytest.mark.parametrize("code", sorted(_all_languages()))
    def test_merged_guide_carries_leaf_content(
        self, loader: StyleGuideLoader, code: str
    ) -> None:
        # Overlays are content-free (CORE-1398), so every rules/profile slot in
        # the merged guide comes from the leaf. Assert they resolve through the
        # chain rather than coming back empty.
        guide = loader.load(code)
        assert set(guide.get("supports", {})) == _SUPPORTS_FLAGS, (
            f"{code}: supports flag set unresolved"
        )
        assert all(isinstance(v, bool) for v in guide["supports"].values()), (
            f"{code}: supports flags must all be booleans"
        )
        assert guide.get("naming", {}).get("case_substitute"), (
            f"{code}: naming.case_substitute unresolved"
        )
        assert guide.get("script", {}).get("direction") in ("ltr", "rtl"), (
            f"{code}: script.direction unresolved"
        )
        assert (guide.get("rendering") or {}).get("noto_font"), (
            f"{code}: rendering.noto_font unresolved"
        )

    @pytest.mark.parametrize("code,meta", sorted(_all_languages().items()))
    def test_case_substitute_agrees_with_languages_json(
        self, loader: StyleGuideLoader, code: str, meta: dict
    ) -> None:
        # New schema: ``naming.case_substitute`` is a string enum
        # (``morphology`` | ``not_needed``), not a nested ``{strategy: ...}``.
        substitute = loader.load(code).get("naming", {}).get("case_substitute")
        if meta["has_case_distinction"]:
            assert substitute == "not_needed", (
                f"{code}: bicameral language needs no case substitute "
                f"(got {substitute!r})"
            )
        else:
            assert substitute == "morphology", (
                f"{code}: caseless language must substitute case via morphology "
                f"(got {substitute!r})"
            )


class TestFourDeepChainResolves:
    """The deepest real chains (through a family overlay) resolve in order."""

    def test_zh_resolves_cjk_chain(self, loader: StyleGuideLoader) -> None:
        chain = [p.name for p in loader._resolve_hierarchy("zh")]
        assert chain == ["python.yml", "_ltr.yml", "_cjk.yml", "zh.yml"]
        guide = loader.load("zh")
        # Leaf (caseless CJK) profile resolves through the 4-deep chain.
        assert guide["supports"]["case_distinction"] is False
        assert guide["naming"]["case_substitute"] == "morphology"
        assert guide["script"]["direction"] == "ltr"

    def test_ur_resolves_arabic_chain(self, loader: StyleGuideLoader) -> None:
        chain = [p.name for p in loader._resolve_hierarchy("ur")]
        assert chain == ["python.yml", "_rtl.yml", "_arabic.yml", "ur.yml"]
        guide = loader.load("ur")
        # ur's leaf profile: Nastaliq font, RTL, cursive Arabic script, caseless.
        assert guide["rendering"]["noto_font"] == "Noto Nastaliq Urdu"
        assert guide["script"]["direction"] == "rtl"
        assert guide["supports"]["cursive_joining"] is True
        assert guide["naming"]["case_substitute"] == "morphology"


class TestMergeSemantics:
    """Loader merge rules, exercised with synthetic guides (schema-agnostic).

    The real overlays are content-free, so last-wins and deep-merge behaviour
    is verified here against fixtures rather than the shipped guides.
    """

    def test_later_file_overrides_earlier(self, tmp_path: Path) -> None:
        sg = tmp_path / "style-guides"
        sg.mkdir()
        (sg / "python.yml").write_text(
            "language: python\nextends: []\n"
            "rendering:\n  noto_font: Base\n  editor: shared\n"
        )
        (sg / "_ltr.yml").write_text("language: _ltr\nextends: [python.yml]\n")
        (sg / "xx.yml").write_text(
            "language: xx\nextends: [_ltr.yml]\nrendering:\n  noto_font: Leaf\n"
        )
        loader = StyleGuideLoader(style_guides_dir=sg)
        rendering = loader.load("xx")["rendering"]
        # Leaf value wins on the conflicting key ...
        assert rendering["noto_font"] == "Leaf"
        # ... and a non-conflicting sibling from the base survives the merge.
        assert rendering["editor"] == "shared"


class TestCycleDetection:
    def test_cyclic_extends_raises(self, tmp_path: Path) -> None:
        sg = tmp_path / "style-guides"
        sg.mkdir()
        (sg / "python.yml").write_text("language: python\nextends: []\n")
        (sg / "ab.yml").write_text("language: ab\nextends: [cd.yml]\n")
        (sg / "cd.yml").write_text("language: cd\nextends: [ab.yml]\n")
        loader = StyleGuideLoader(style_guides_dir=sg)
        with pytest.raises(ValueError, match="[Cc]yclic"):
            loader.load("ab")


class TestFallbackWithoutGuide:
    """A language with no dedicated guide still resolves base + direction."""

    def test_no_guide_falls_back(self, tmp_path: Path) -> None:
        sg = tmp_path / "style-guides"
        sg.mkdir()
        (sg / "python.yml").write_text("language: python\nextends: []\nk: base\n")
        (sg / "_ltr.yml").write_text("language: _ltr\nextends: [python.yml]\n")
        (sg / "_rtl.yml").write_text("language: _rtl\nextends: [python.yml]\n")
        loader = StyleGuideLoader(style_guides_dir=sg)
        chain = [p.name for p in loader._resolve_hierarchy("xx")]
        assert chain == ["python.yml", "_ltr.yml"]
        assert loader.load("xx")["k"] == "base"
