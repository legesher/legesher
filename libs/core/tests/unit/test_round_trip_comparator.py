"""The pure comparator: two strings in, located divergences out.

The v1 comparator was built on str.splitlines() without keepends, which
discards terminators and splits on eight boundaries beyond \\n — it reported
CRLF-vs-LF as a clean round trip. Every test in TestNonVacuity exists
because of that hole.
"""

import pytest

from legesher_core.round_trip import (
    DivergenceKind,
    Layer,
    all_divergences,
    first_divergence,
)


class TestFirstDivergence:
    def test_identical_sources_return_none(self):
        source = "def greet():\n    print('hi')\n"
        assert first_divergence(source, source) is None

    def test_reports_line_and_column_of_first_difference(self):
        divergence = first_divergence(
            "def greet():\n    return 42\n", "def greet():\n    return 43\n"
        )
        assert divergence is not None
        assert (divergence.line, divergence.offset) == (2, 13)
        assert divergence.expected == "    return 42"
        assert divergence.actual == "    return 43"
        assert divergence.kind is DivergenceKind.CONTENT

    def test_offset_is_one_based(self):
        divergence = first_divergence("abc", "xbc")
        assert divergence is not None and divergence.offset == 1

    def test_except_star_regression_is_located_at_the_asterisk(self):
        # CORE-1839: the column is what makes this readable at a glance.
        divergence = first_divergence(
            "try:\n    pass\nexcept* OSError:\n    pass\n",
            "try:\n    pass\nexcept** OSError:\n    pass\n",
        )
        assert divergence is not None
        assert (divergence.line, divergence.offset) == (3, 8)

    def test_extra_trailing_line_reports_line_count(self):
        divergence = first_divergence("a\nb\n", "a\nb\nc\n")
        assert divergence is not None
        assert divergence.kind is DivergenceKind.LINE_COUNT
        assert divergence.line == 3
        assert (divergence.expected, divergence.actual) == ("", "c")

    def test_missing_trailing_newline_reports_trailing_whitespace(self):
        divergence = first_divergence("a\n", "a")
        assert divergence is not None
        assert divergence.kind is DivergenceKind.TRAILING_WHITESPACE
        assert (divergence.expected, divergence.actual) == ("\n", "")

    def test_comparison_is_byte_exact_not_normalised(self):
        # Storage is NFC. A pack that emitted NFD must FAIL the round trip;
        # normalising here would hide a real defect. Do not "fix" to
        # compare_key.
        composed = "x = 'e\u0301'\n"
        precomposed = "x = '\u00e9'\n"
        assert first_divergence(precomposed, composed) is not None

    def test_layer_is_unset_from_the_bare_comparator(self):
        divergence = first_divergence("a", "b")
        assert divergence is not None and divergence.layer is None

    def test_str_renders_the_two_line_report_shape(self):
        divergence = first_divergence("a\n", "b\n")
        rendered = str(divergence)
        assert "line 1:" in rendered
        assert "expected: 'a'" in rendered
        assert "actual:   'b'" in rendered


class TestNonVacuity:
    """all_divergences must be non-empty whenever the strings differ.

    v1 reported every one of these as a clean round trip: splitlines()
    without keepends throws the differing bytes away. This class is the
    regression gate for the exact hole.
    """

    @pytest.mark.parametrize(
        "expected,actual",
        [
            pytest.param("a\r\nb\r\n", "a\nb\n", id="crlf-whole-file"),
            pytest.param("a\r\nb\n", "a\nb\n", id="crlf-mixed"),
            pytest.param("a\rb\n", "a\nb\n", id="lone-cr"),
            pytest.param("a\n", "a", id="missing-trailing-newline"),
            pytest.param("a", "a\n", id="added-trailing-newline"),
            pytest.param("a\n\n\n", "a\n", id="extra-trailing-newlines"),
            pytest.param("x = 'a\u2028b'\n", "x = 'a\nb'\n", id="u2028-in-string"),
            pytest.param("a\x0cb\n", "a\x0bb\n", id="formfeed-vs-vtab"),
            pytest.param("a\x85b\n", "a\u2028b\n", id="nel-vs-ls"),
            pytest.param("", "x", id="empty-vs-content"),
            pytest.param("x", "", id="content-vs-empty"),
        ],
    )
    def test_differing_strings_always_yield_a_divergence(self, expected, actual):
        assert expected != actual, "bad fixture"
        assert all_divergences(expected, actual) != []
        assert first_divergence(expected, actual) is not None

    @pytest.mark.parametrize(
        "expected,actual",
        [
            ("a\r\nb\r\n", "a\nb\n"),
            ("a\rb\n", "a\nb\n"),
            ("a\n", "a"),
            ("a\n\n\n", "a\n"),
        ],
    )
    def test_a_divergence_never_shows_two_identical_values(self, expected, actual):
        # A located divergence whose expected == actual denies itself — and
        # flows into a verdict the agent quotes.
        for divergence in all_divergences(expected, actual):
            assert divergence.expected != divergence.actual


class TestAllDivergences:
    def test_returns_one_entry_per_differing_line(self):
        found = all_divergences("a\nb\nc\n", "a\nX\nY\n")
        assert [d.line for d in found] == [2, 3]

    def test_identical_sources_return_empty(self):
        assert all_divergences("a\n", "a\n") == []

    def test_limit_bounds_the_list(self):
        expected = "".join(f"a{n}\n" for n in range(100))
        actual = "".join(f"b{n}\n" for n in range(100))
        assert len(all_divergences(expected, actual, limit=5)) == 5

    def test_agrees_with_first_divergence_on_the_first_entry(self):
        expected, actual = "a\nb\n", "a\nX\n"
        assert all_divergences(expected, actual)[0] == first_divergence(
            expected, actual
        )


class TestLayerVocabulary:
    def test_pack_layers_match_the_canonical_category_names(self):
        from legesher_i18n.term_definitions import YAML_SECTION_CATEGORIES

        pack_layers = {
            Layer.KEYWORDS,
            Layer.BUILTINS,
            Layer.EXCEPTIONS,
            Layer.RESERVED_WORDS,
        }
        assert {layer.value for layer in pack_layers} == set(YAML_SECTION_CATEGORIES)

    def test_layers_are_plain_str_for_the_310_floor(self):
        # (str, Enum), not StrEnum: StrEnum is 3.11+ and this module is
        # re-exported from __init__, so getting it wrong breaks the whole
        # package import on the declared floor.
        assert isinstance(Layer.KEYWORDS, str)
        assert Layer.KEYWORDS.value == "keywords"


class TestComparatorEdges:
    def test_prefix_line_divergence_points_past_the_shorter_text(self):
        # One line is a strict prefix of the other: the difference starts
        # just past the common text, and the column says so.
        divergence = first_divergence("abc\n", "abcdef\n")
        assert divergence is not None
        assert divergence.offset == 4

    def test_line_count_reports_when_expected_is_the_longer_side(self):
        # The reversed direction of the extra-line case: expected has the
        # extra content, actual ran short.
        divergence = first_divergence("a\nb\nc\n", "a\nb\n")
        assert divergence is not None
        assert divergence.kind is DivergenceKind.LINE_COUNT
        assert divergence.line == 3
        assert (divergence.expected, divergence.actual) == ("c", "")
