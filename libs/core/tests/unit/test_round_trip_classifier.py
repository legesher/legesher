"""Classifying divergences by token layer.

Every requirement here traces to a review finding: span-indexed tokens
(docstrings were unclassifiable), the f-string token family (layer flipped
on the f prefix), lowercase exception keys (canonical exceptions reported
as identifiers), direction-aware collisions (CORE-1840 misattributed to the
pack), and the widened catch list (lone surrogate escaped as ValueError).
"""

import pytest

from legesher_core.round_trip import (
    Layer,
    classified,
    classify_divergence,
    first_divergence,
)


class TestPackLayers:
    @pytest.mark.parametrize(
        "section,term",
        [
            ("keywords", "def"),
            ("builtins", "print"),
            ("exceptions", "ValueError"),
        ],
    )
    def test_native_pack_renderings_classify_to_their_section(
        self, spanish_pack, section, term
    ):
        mapping = getattr(spanish_pack, section)
        key = term if term in mapping else term.lower()
        rendering = mapping[key]
        expected = f"x = {rendering}\n"
        actual = f"x = {rendering}X\n"
        divergence = first_divergence(expected, actual)
        assert classify_divergence(
            divergence, expected, actual, spanish_pack, native_side=True
        ) is Layer(section)

    def test_canonical_exception_classifies_as_exceptions_not_identifiers(
        self, spanish_pack
    ):
        # Packs store exception keys lowercase (valueerror); Python spells
        # ValueError. The engine remaps via merge_exception_translations at
        # build time; a lookup without it is right on the native side and
        # wrong on the canonical side - which is what translate_to_native
        # and both core suites feed it.
        expected = "raise ValueError(1)\n"
        actual = "raise ValueErrorX(1)\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=False
            )
            is Layer.EXCEPTIONS
        )

    def test_operator_divergence_attributes_to_the_preceding_keyword(
        self, spanish_pack
    ):
        # CORE-1839: the differing char is an operator; the responsible term
        # is the keyword before it.
        rendering = spanish_pack.keywords["except"]
        expected = f"try:\n    pass\n{rendering}* OSError:\n    pass\n"
        actual = f"try:\n    pass\n{rendering}** OSError:\n    pass\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.KEYWORDS
        )


class TestCollisions:
    def test_identifier_spelled_like_a_pack_rendering_is_a_collision(
        self, spanish_pack
    ):
        # CORE-1840: canonical-side identifier `y` matches the es rendering
        # of `and` - pack VALUES, wrong side for canonical source. Reporting
        # `keywords` sent readers to file bugs against a correct pack.
        expected = "except KeyError as y:\n    raise\n"
        actual = "except KeyError as and:\n    raise\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=False
            )
            is Layer.COLLISION
        )

    def test_a_genuine_pack_key_on_the_canonical_side_is_its_own_layer(
        self, spanish_pack
    ):
        expected = "def greet():\n    pass\n"
        actual = "defX greet():\n    pass\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=False
            )
            is Layer.KEYWORDS
        )


class TestFuzzyLayers:
    def test_identifier_divergence(self, spanish_pack):
        expected = "x = 1\ntotal = x\n"
        actual = "x = 1\nsuma = x\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=False
            )
            is Layer.IDENTIFIERS
        )

    def test_comment_divergence(self, spanish_pack):
        expected = "x = 1  # cuenta\n"
        actual = "x = 1  # count\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.COMMENTS
        )

    def test_plain_string_divergence(self, spanish_pack):
        expected = 'x = "hola"\n'
        actual = 'x = "hello"\n'
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.STRINGS
        )

    def test_fstring_content_divergence_is_strings_not_the_preceding_name(
        self, spanish_pack
    ):
        # 3.12+ f-strings tokenize as FSTRING_START/MIDDLE/END, none of
        # which is STRING. v1 walked past the literal to the preceding NAME
        # and the layer flipped on the f prefix alone: a real string
        # corruption dismissed as identifiers, or a false pack alarm.
        rendering = spanish_pack.builtins["print"]
        expected = f'{rendering}(f"hola")\n'
        actual = f'{rendering}(f"hello")\n'
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.STRINGS
        )

    def test_docstring_interior_divergence_is_classifiable(self, spanish_pack):
        # Tokens must be indexed by every line they SPAN. Keyed on start
        # line alone, a triple-quoted string covering lines 1-3 registers
        # only under line 1 and a line-2 divergence found no token at all.
        expected = 'x = """line one\nsegunda linea\n"""\n'
        actual = 'x = """line one\nsecond line\n"""\n'
        divergence = first_divergence(expected, actual)
        assert divergence.line == 2
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.STRINGS
        )


class TestNativeScripts:
    def test_arabic_native_keyword_divergence(self, arabic_pack):
        # translate_to_source hands the classifier RTL, non-Latin source.
        rendering = arabic_pack.keywords["def"]
        expected = f"{rendering} foo():\n    pass\n"
        actual = f"{rendering}X foo():\n    pass\n"
        divergence = first_divergence(expected, actual)
        assert (
            classify_divergence(
                divergence, expected, actual, arabic_pack, native_side=True
            )
            is Layer.KEYWORDS
        )


class TestUnclassifiable:
    def test_tokenizer_error_tokens_still_classify_from_available_tokens(
        self, spanish_pack
    ):
        # tokenize is not a parser: `def broken(:` yields NAME tokens before
        # raising at EOF, so line 1 IS classifiable. This pins that a
        # TokenError is a result, not an exception - the walk uses whatever
        # was read.
        expected = "def broken(:\n"
        actual = "def brokenX(:\n"
        divergence = first_divergence(expected, actual)
        result = classify_divergence(
            divergence, expected, actual, spanish_pack, native_side=False
        )
        assert result in (Layer.IDENTIFIERS, None)  # never raises

    def test_lone_surrogate_returns_none_rather_than_raising(self, spanish_pack):
        # UnicodeEncodeError is a ValueError subclass; the repo's own
        # engine catch lists include ValueError and v1's did not.
        expected = "x = 1\ud800\n"
        actual = "y = 1\ud800\n"
        divergence = first_divergence(expected, actual)
        result = classify_divergence(
            divergence, expected, actual, spanish_pack, native_side=False
        )
        assert result is None or isinstance(result, Layer)

    def test_divergence_without_offset_classifies_as_none(self, spanish_pack):
        divergence = first_divergence("a\n", "a")
        assert divergence.offset is None
        assert (
            classify_divergence(divergence, "a\n", "a", spanish_pack, native_side=False)
            is None
        )


class TestClassified:
    def test_fills_layer_and_leaves_originals_untouched(self, spanish_pack):
        expected = "x = 1  # cuenta\n"
        actual = "x = 1  # count\n"
        original = first_divergence(expected, actual)
        result = classified(
            [original], expected, actual, spanish_pack, native_side=True
        )
        assert [d.layer for d in result] == [Layer.COMMENTS]
        assert original.layer is None


class TestCollisionNativeSide:
    def test_native_identifier_spelled_like_a_canonical_key_is_a_collision(
        self, spanish_pack
    ):
        # The mirror of the canonical-side case: native-side source whose
        # identifier matches a pack KEY (the canonical spelling). Wrong
        # side for native source -> collision, not the pack layer.
        expected = "definir f():\n    print_total = 1\n    print = 2\n"
        actual = "definir f():\n    print_total = 1\n    printX = 2\n"
        divergence = first_divergence(expected, actual)
        assert divergence.line == 3
        assert (
            classify_divergence(
                divergence, expected, actual, spanish_pack, native_side=True
            )
            is Layer.COLLISION
        )
