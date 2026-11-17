"""The numeral-system data model: one identifier per language, digits derived.

Three layers:

- the zero code points in ``legesher_i18n.numerals`` against the Unicode
  character database, by value and by character name;
- the registry's ``numeral_system`` and ``decimal_separator`` for every
  published language: a known identifier, an allowed separator, and the
  values that were once recorded wrong (Urdu as Arabic-Indic; Persian and
  Burmese empty) pinned;
- the registry against each style guide, both ways: a native digit block
  needs ``supports.native_digits``, a flag needs a native block unless the
  language is listed as profiling numerals that are not one, and the guide's
  "Digits: ... natively uses ..." note must show digits from the block.
  The validator owns that check; this runs it.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest
import yaml

from legesher_i18n import language_registry
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_decimal_separator,
    get_native_digits,
    get_numeral_system,
)
from legesher_i18n.numerals import (
    DECIMAL_SEPARATORS,
    LATIN,
    NUMERAL_SYSTEM_ZEROS,
    decimal_separator_for,
    is_known_numeral_system,
    numeral_system_digits,
)
from legesher_i18n.scripts import validate_style_guides as V

STYLE_GUIDES = Path(__file__).parent.parent / "style-guides"
LANGUAGES_JSON = Path(__file__).parent.parent / "legesher_i18n" / "languages.json"

#: The Unicode name of each system's zero, typed from the Unicode character
#: database: an authority independent of the code points in ``numerals``.
ZERO_NAMES = {
    "latn": "DIGIT ZERO",
    "arab": "ARABIC-INDIC DIGIT ZERO",
    "arabext": "EXTENDED ARABIC-INDIC DIGIT ZERO",
    "beng": "BENGALI DIGIT ZERO",
    "deva": "DEVANAGARI DIGIT ZERO",
    "gujr": "GUJARATI DIGIT ZERO",
    "knda": "KANNADA DIGIT ZERO",
    "mlym": "MALAYALAM DIGIT ZERO",
    "mymr": "MYANMAR DIGIT ZERO",
    "telu": "TELUGU DIGIT ZERO",
    "thai": "THAI DIGIT ZERO",
}


class TestDerivation:
    @pytest.mark.parametrize("system", sorted(NUMERAL_SYSTEM_ZEROS))
    def test_zero_starts_a_unicode_decimal_digit_block(self, system: str) -> None:
        digits = numeral_system_digits(system)
        assert len(digits) == 10
        for value, char in enumerate(digits):
            assert unicodedata.category(char) == "Nd", (system, f"U+{ord(char):04X}")
            assert unicodedata.digit(char) == value, (system, f"U+{ord(char):04X}")
        assert unicodedata.name(digits[0]) == ZERO_NAMES[system], system

    def test_every_system_has_a_named_zero(self) -> None:
        assert set(NUMERAL_SYSTEM_ZEROS) == set(ZERO_NAMES)

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
    def test_known_vectors(self, system: str, expected: str) -> None:
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

    @pytest.mark.parametrize("code", get_active_language_codes())
    def test_ascii_digits_take_the_ascii_point(self, code: str) -> None:
        # A numeric literal in code uses ".", whatever the prose convention.
        if get_numeral_system(code) == LATIN:
            assert get_decimal_separator(code) == "."

    @pytest.mark.parametrize("code", get_active_language_codes())
    def test_separator_is_the_one_its_system_is_written_with(self, code: str) -> None:
        assert get_decimal_separator(code) == decimal_separator_for(
            get_numeral_system(code)
        )

    def test_schema_allows_exactly_the_module_separators(self) -> None:
        schema = json.loads(
            (LANGUAGES_JSON.parent / "languages.schema.json").read_text(
                encoding="utf-8"
            )
        )
        allowed = schema["$defs"]["languageMetadata"]["properties"][
            "decimal_separator"
        ]["enum"]
        assert set(allowed) == DECIMAL_SEPARATORS

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


class TestStyleGuidesAgree:
    """``supports.native_digits`` is the human profile; the registry is the data.

    The check lives in the style-guide validator (the blocking pre-commit
    gate); this runs it over every published language, so the test suite and
    the hook cannot disagree.
    """

    @pytest.mark.parametrize("code", get_active_language_codes())
    def test_validator_finds_no_digit_problem(self, code: str) -> None:
        guide = yaml.safe_load(
            (STYLE_GUIDES / f"{code}.yml").read_text(encoding="utf-8")
        )
        meta = json.loads(LANGUAGES_JSON.read_text(encoding="utf-8"))["languages"][code]
        assert V._digit_problems(code, guide, meta) == []

    def test_exceptions_are_published_languages(self) -> None:
        assert V.NATIVE_NUMERALS_WITHOUT_A_DIGIT_BLOCK <= set(
            get_active_language_codes()
        )
