"""The style-guide schema, template, and validator agree (CORE-1392).

These lock the merge-first schema layer before any guide is regenerated onto it:
the template is a structurally-valid example, the ``supports`` flag set is the
same in the template and the schema, and the validator enforces the
languages.json cross-checks.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from legesher_i18n.scripts import validate_style_guides as V
from legesher_i18n.style_guides import StyleGuideLoader

_SG = Path(__file__).parent.parent / "style-guides"
_SCHEMA = json.loads((_SG / "_schema.json").read_text(encoding="utf-8"))
_TEMPLATE = yaml.safe_load((_SG / "_template.yml").read_text(encoding="utf-8"))


class TestTemplateMatchesSchema:
    def test_template_has_all_required_keys(self) -> None:
        for key in _SCHEMA["required"]:
            assert key in _TEMPLATE, f"_template.yml missing required key {key!r}"

    def test_supports_flag_set_matches_schema(self) -> None:
        assert set(_TEMPLATE["supports"]) == set(
            _SCHEMA["properties"]["supports"]["required"]
        )
        assert all(isinstance(v, bool) for v in _TEMPLATE["supports"].values())

    def test_template_enums_are_valid(self) -> None:
        assert _TEMPLATE["status"] in _SCHEMA["properties"]["status"]["enum"]
        assert (
            _TEMPLATE["naming"]["case_substitute"]
            in _SCHEMA["properties"]["naming"]["properties"]["case_substitute"]["enum"]
        )
        assert (
            _TEMPLATE["script"]["direction"]
            in _SCHEMA["properties"]["script"]["properties"]["direction"]["enum"]
        )
        assert (
            _TEMPLATE["formatting"]["programming_punctuation"]
            in _SCHEMA["properties"]["formatting"]["properties"][
                "programming_punctuation"
            ]["enum"]
        )


def _tmp_guides(tmp_path: Path) -> Path:
    sg = tmp_path / "style-guides"
    sg.mkdir()
    (sg / "python.yml").write_text("language: python\nextends: []\n")
    (sg / "_ltr.yml").write_text("language: _ltr\nextends: [python.yml]\n")
    (sg / "_schema.json").write_text((_SG / "_schema.json").read_text())
    return sg


def _guide(**over) -> dict:
    g = {
        "language": "xx",
        "extends": ["python.yml", "_ltr.yml"],
        "version": "0.1.0",
        "status": "experimental",
        "supports": {
            "case_distinction": False,
            "snake_case": True,
            "upper_snake_case": False,
            "pascal_case": False,
            "camel_case": False,
            "native_digits": False,
            "combining_marks": False,
            "requires_word_separator": False,
            "diacritics_in_identifiers": False,
            "cursive_joining": False,
        },
        "naming": {"case_substitute": "morphology"},
        "script": {"name": "Test", "direction": "ltr", "constraints": []},
        "formatting": {"comment_prefix": "#", "programming_punctuation": "ascii_only"},
        "rendering": {"noto_font": "Noto Sans"},
    }
    g.update(over)
    return g


class TestValidatorCrossChecks:
    def _loader(self, tmp_path: Path, code: str, guide: dict) -> StyleGuideLoader:
        sg = _tmp_guides(tmp_path)
        (sg / f"{code}.yml").write_text(yaml.safe_dump(guide))
        return StyleGuideLoader(style_guides_dir=sg)

    def test_consistent_caseless_guide_passes(self, tmp_path: Path) -> None:
        g = _guide()
        loader = self._loader(tmp_path, "xx", g)
        meta = {"has_case_distinction": False, "rtl": False}
        assert V._validate_guide("xx", g, _SCHEMA, meta, loader) == []

    def test_caseless_with_upper_snake_true_is_flagged(self, tmp_path: Path) -> None:
        g = _guide()
        g["supports"]["upper_snake_case"] = True
        loader = self._loader(tmp_path, "xx", g)
        meta = {"has_case_distinction": False, "rtl": False}
        problems = V._validate_guide("xx", g, _SCHEMA, meta, loader)
        assert any("upper_snake_case must be false" in p for p in problems)

    def test_case_distinction_mismatch_is_flagged(self, tmp_path: Path) -> None:
        g = _guide()  # supports.case_distinction == False
        loader = self._loader(tmp_path, "xx", g)
        meta = {"has_case_distinction": True, "rtl": False}  # languages.json says True
        problems = V._validate_guide("xx", g, _SCHEMA, meta, loader)
        assert any("case_distinction" in p for p in problems)

    def test_direction_mismatch_is_flagged(self, tmp_path: Path) -> None:
        g = _guide()  # direction ltr
        loader = self._loader(tmp_path, "xx", g)
        meta = {"has_case_distinction": False, "rtl": True}  # languages.json says rtl
        problems = V._validate_guide("xx", g, _SCHEMA, meta, loader)
        assert any("direction" in p for p in problems)

    def test_unknown_supports_flag_is_flagged(self, tmp_path: Path) -> None:
        g = _guide()
        g["supports"]["made_up_flag"] = True
        loader = self._loader(tmp_path, "xx", g)
        meta = {"has_case_distinction": False, "rtl": False}
        problems = V._validate_guide("xx", g, _SCHEMA, meta, loader)
        assert any("unknown flags" in p for p in problems)


class TestValidatorDigitChecks:
    """``supports.native_digits`` and the Digits note against ``numeral_system``."""

    _NOTE = "Digits: Arabic natively uses ٠١٢٣; code note."

    def _guide(self, flag: bool, note: str | None = None) -> dict:
        g = _guide()
        g["supports"]["native_digits"] = flag
        g["script"]["constraints"] = [note] if note else []
        return g

    def _meta(self, system: str) -> dict:
        return {"has_case_distinction": False, "rtl": False, "numeral_system": system}

    def test_native_block_with_flag_and_note_passes(self) -> None:
        g = self._guide(True, self._NOTE)
        assert V._digit_problems("xx", g, self._meta("arab")) == []

    def test_native_block_without_the_flag_is_flagged(self) -> None:
        g = self._guide(False, self._NOTE)
        problems = V._digit_problems("xx", g, self._meta("arab"))
        assert any("supports.native_digits is False" in p for p in problems)

    def test_flag_without_a_native_block_is_flagged(self) -> None:
        # The direction a single-sided check missed: a native-digit language
        # whose registry entry slipped back to latn.
        g = self._guide(True, self._NOTE)
        problems = V._digit_problems("xx", g, self._meta("latn"))
        assert any("numeral_system is 'latn'" in p for p in problems)

    def test_listed_exception_with_latn_passes(self) -> None:
        g = self._guide(True, "Digits: Chinese natively uses 一二三; x.")
        assert V._digit_problems("zh", g, self._meta("latn")) == []

    def test_stale_exception_is_flagged(self) -> None:
        g = self._guide(False)
        problems = V._digit_problems("zh", g, self._meta("latn"))
        assert any("remove it from the list" in p for p in problems)

    def test_note_from_another_block_is_flagged(self) -> None:
        # Urdu's note shows Extended Arabic-Indic; a registry naming the
        # Arabic-Indic block, as the registry once did, contradicts it.
        g = self._guide(True, "Digits: Urdu natively uses ۰۱۲۳; x.")
        problems = V._digit_problems("xx", g, self._meta("arab"))
        assert any("U+06F0" in p for p in problems)

    def test_native_block_without_a_note_is_flagged(self) -> None:
        g = self._guide(True)
        problems = V._digit_problems("xx", g, self._meta("arab"))
        assert any("no 'Digits:" in p for p in problems)

    def test_unknown_identifier_is_flagged(self) -> None:
        g = self._guide(True, self._NOTE)
        problems = V._digit_problems("xx", g, self._meta("arabic_indic"))
        assert any("not a known identifier" in p for p in problems)
