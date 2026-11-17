"""The numeral-system data model: one identifier per language, digits derived.

Three layers, each checked against an outside authority rather than itself:

- the zero code points in ``legesher_i18n.numerals`` against the Unicode
  character database;
- the registry's ``numeral_system`` and ``decimal_separator`` against the
  identifiers that module knows, for every language the registry publishes;
- the registry against each style guide's ``supports.native_digits`` flag and
  its "Digits: ... natively uses ..." note, which name the digits a native
  reader expects.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest

from legesher_i18n import language_registry
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_decimal_separator,
    get_native_digits,
    get_numeral_system,
)
from legesher_i18n.numerals import (
    LATIN,
    NUMERAL_SYSTEM_ZEROS,
    is_known_numeral_system,
    numeral_system_digits,
)
from legesher_i18n.style_guides import StyleGuideLoader

STYLE_GUIDES = Path(__file__).parent.parent / "style-guides"


class TestDerivation:
    @pytest.mark.parametrize("system", sorted(NUMERAL_SYSTEM_ZEROS))
    def test_zero_starts_a_unicode_decimal_digit_block(self, system: str) -> None:
        digits = numeral_system_digits(system)
        assert len(digits) == 10
        for value, char in enumerate(digits):
            assert unicodedata.category(char) == "Nd", (system, f"U+{ord(char):04X}")
            assert unicodedata.digit(char) == value, (system, f"U+{ord(char):04X}")
        assert unicodedata.name(digits[0]).endswith("DIGIT ZERO"), system

    @pytest.mark.parametrize(
        ("system", "expected"),
        [
            ("latn", "0123456789"),
            ("arab", "٠١٢٣٤٥٦٧٨٩"),
            ("arabext", "۰۱۲۳۴۵۶۷۸۹"),
            ("deva", "०१२३४५६७८९"),
            ("beng", "০১২৩৪৫৬৭৮৯"),
            ("thai", "๐๑๒๓๔๕๖๗๘๙"),
            ("mymr", "၀၁၂၃၄၅၆၇၈၉"),
        ],
    )
    def test_shared_vectors(self, system: str, expected: str) -> None:
        # The same strings the JavaScript engine's digit maps must produce.
        assert numeral_system_digits(system) == expected

    def test_arabic_and_extended_arabic_differ_in_every_digit(self) -> None:
        arab, arabext = numeral_system_digits("arab"), numeral_system_digits("arabext")
        assert all(a != b for a, b in zip(arab, arabext, strict=True))

    @pytest.mark.parametrize("system", ["arabic_indic", "Arab", "", "hanidec"])
    def test_unknown_identifier_raises_and_names_it(self, system: str) -> None:
        assert not is_known_numeral_system(system)
        with pytest.raises(ValueError, match=re.escape(repr(system))):
            numeral_system_digits(system)


class TestRegistry:
    @pytest.mark.parametrize("code", get_active_language_codes())
    def test_every_language_names_a_known_system_and_one_separator(
        self, code: str
    ) -> None:
        system = get_numeral_system(code)
        assert is_known_numeral_system(system), (code, system)
        assert len(get_decimal_separator(code)) == 1, code

    @pytest.mark.parametrize("code", get_active_language_codes())
    def test_native_digits_read_as_their_values(self, code: str) -> None:
        digits = get_native_digits(code)
        if digits is None:
            assert get_numeral_system(code) == LATIN
            return
        assert digits != "0123456789"
        assert int(digits) == 123456789
        assert float(digits[1] + "." + digits[5]) == 1.5

    @pytest.mark.parametrize(
        ("code", "system", "separator"),
        [
            ("ar", "arab", "٫"),
            # Persian and Urdu write Extended Arabic-Indic, not Arabic-Indic.
            ("fa", "arabext", "٫"),
            ("ur", "arabext", "٫"),
            ("my", "mymr", "."),
            ("hi", "deva", "."),
            ("es", "latn", "."),
        ],
    )
    def test_recorded_facts(self, code: str, system: str, separator: str) -> None:
        assert get_numeral_system(code) == system
        assert get_decimal_separator(code) == separator

    def test_unknown_code_writes_ascii(self) -> None:
        assert get_numeral_system("xx") == LATIN
        assert get_decimal_separator("xx") == "."
        assert get_native_digits("xx") is None

    def test_registry_without_the_fields_still_loads(self, tmp_path, monkeypatch):
        # The generator imports this module, so a registry from before the
        # fields existed must load (as ASCII digits) to be regenerated at all.
        old = tmp_path / "languages.json"
        old.write_text(
            json.dumps(
                {
                    "canonical_language": "en",
                    "languages": {
                        "ar": {
                            "name": "Arabic",
                            "native": "العربية",
                            "iso639_2": "ara",
                            "bcp47": "ar",
                            "rtl": True,
                            "status": "experimental",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(language_registry, "_LANGUAGES_JSON", old)
        languages, _ = language_registry._load_languages()
        assert languages["ar"]["numeral_system"] == LATIN
        assert languages["ar"]["decimal_separator"] == "."


#: "Digits: Urdu natively uses ۰۱۲۳; code uses ASCII 0-9 today."
_DIGIT_NOTE = re.compile(r"Digits: .*? natively uses (?:fullwidth )?(\S+?);")


def _style_guide_codes() -> list[str]:
    return [
        code
        for code in get_active_language_codes()
        if (STYLE_GUIDES / f"{code}.yml").exists()
    ]


class TestStyleGuidesAgree:
    """``supports.native_digits`` is the human profile; the registry is the data.

    A language whose registry names a native digit block must carry the flag.
    The converse does not hold: Chinese, Japanese, Korean, Amharic and Sinhala
    profile native numerals (algorithmic, fullwidth or archaic) and write
    their programs with ASCII digits, so their registry entry is ``latn``.
    """

    @pytest.fixture(scope="class")
    def loader(self) -> StyleGuideLoader:
        return StyleGuideLoader(STYLE_GUIDES)

    def test_every_published_language_has_a_style_guide(self) -> None:
        assert len(_style_guide_codes()) == len(get_active_language_codes())

    @pytest.mark.parametrize("code", _style_guide_codes())
    def test_native_digit_block_carries_the_flag(
        self, code: str, loader: StyleGuideLoader
    ) -> None:
        flag = loader.load(code).get("supports", {}).get("native_digits")
        if get_native_digits(code) is not None:
            assert flag is True, (
                f"{code}: the registry names {get_numeral_system(code)!r} but "
                f"style-guides/{code}.yml has supports.native_digits {flag!r}"
            )
        if flag is not True:
            assert get_numeral_system(code) == LATIN, code

    @pytest.mark.parametrize("code", _style_guide_codes())
    def test_note_digits_belong_to_the_registry_block(
        self, code: str, loader: StyleGuideLoader
    ) -> None:
        digits = get_native_digits(code)
        if digits is None:
            return
        constraints = loader.load(code).get("script", {}).get("constraints", [])
        examples = [
            m.group(1) for note in constraints if (m := _DIGIT_NOTE.search(note))
        ]
        assert examples, f"{code}: no 'Digits: ... natively uses ...' note"
        for example in examples:
            for char in example:
                assert char in digits, (
                    f"{code}: the style guide writes {char!r} "
                    f"(U+{ord(char):04X}), which is not in the registry's "
                    f"{get_numeral_system(code)!r} digits {digits}"
                )
