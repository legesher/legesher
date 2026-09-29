"""The clean filter's keyword normalizer: each block keeps its stored form.

Expected values are pack literals checked by hand against the ``3.10.yml``
base packs, never computed by the code under test.
"""

import unicodedata

import pytest

from legesher_core.stored_form import (
    block_language,
    clean_text,
    keyword_table,
    smudge_text,
)

ES = keyword_table("es")
AR = keyword_table("ar")
AM = keyword_table("am")
HI = keyword_table("hi")
FR = keyword_table("fr")
CS = keyword_table("cs")
EN = keyword_table("en")


class TestEnglishStraysJoinTheirBlock:
    def test_an_english_keyword_in_a_spanish_file_becomes_spanish(self):
        text = "definir f(x):\n    if x:\n        devolver 1\n"
        assert clean_text(text, local=ES) == (
            "definir f(x):\n    si x:\n        devolver 1\n"
        )

    def test_an_english_keyword_in_an_arabic_file_becomes_arabic(self):
        text = "تعريف f(x):\n    إذا x:\n        return x\n"
        assert (
            clean_text(text, local=AR) == "تعريف f(x):\n    إذا x:\n        إرجاع x\n"
        )

    def test_an_english_keyword_in_an_amharic_file_becomes_amharic(self):
        text = "ግለጽ f(x):\n    ከሆነ x:\n        አልፍ\n    return None\n"
        assert clean_text(text, local=AM) == (
            "ግለጽ f(x):\n    ከሆነ x:\n        አልፍ\n    መልስ ምንም\n"
        )

    def test_an_english_keyword_in_a_hindi_file_becomes_hindi(self):
        text = "परिभाषितकरना f(x):\n    जबतककि x:\n        pass\n"
        assert clean_text(text, local=HI) == (
            "परिभाषितकरना f(x):\n    जबतककि x:\n        कोईकार्रवाईनहीं\n"
        )

    def test_the_compound_except_star_keeps_its_star(self):
        text = "probar:\n    pasar\nexcept* ValueError:\n    pasar\n"
        assert clean_text(text, local=ES) == (
            "probar:\n    pasar\nexcepto* ValueError:\n    pasar\n"
        )


class TestNothingElseMoves:
    def test_an_english_file_is_left_byte_for_byte(self):
        # `y` is the Spanish pack's `and`; in an English file it is a name.
        text = "def f(x, y):\n    if x:\n        return y\n    return None\n"
        assert clean_text(text, local=ES) == text

    def test_strings_and_comments_are_never_touched(self):
        text = 'definir f():\n    # return here\n    devolver "if not"\n'
        assert clean_text(text, local=ES) == text

    def test_soft_keywords_are_left_as_written(self):
        # match/case/type are names outside their statements; only hard
        # keywords, which can never be names, are normalized.
        text = (
            "definir f(x):\n"
            "    type = 1\n"
            "    match x:\n"
            "        case 1:\n"
            "            devolver type\n"
        )
        assert clean_text(text, local=ES) == text

    def test_builtins_are_left_as_written(self):
        text = "definir f(x):\n    devolver print(len(x))\n"
        assert clean_text(text, local=ES) == text

    def test_crlf_tabs_and_trailing_space_survive(self):
        text = "definir f(x):\r\n\tif x:  \r\n\t\tdevolver 1\r\n"
        assert clean_text(text, local=ES) == (
            "definir f(x):\r\n\tsi x:  \r\n\t\tdevolver 1\r\n"
        )

    def test_a_leading_bom_is_kept(self):
        text = "\ufeffdefinir f(x):\n    si x:\n        return 1\n"
        assert clean_text(text, local=ES) == (
            "\ufeffdefinir f(x):\n    si x:\n        devolver 1\n"
        )

    @pytest.mark.parametrize("text", ["", "\n", "   \n\t\n"])
    def test_empty_input_is_returned_as_is(self, text):
        assert clean_text(text, local=ES) == text

    def test_source_that_cannot_be_tokenized_is_returned_as_is(self):
        # The `return` would be a stray, but without tokens there are no
        # safe offsets to rewrite at.
        text = 'definir f():\n    return "unterminated\n'
        assert clean_text(text, local=ES, stored="definir f():\n    pasar\n") == text

    def test_an_nfd_spelled_keyword_still_identifies_the_block(self):
        nfd_def = unicodedata.normalize("NFD", "défini")
        assert nfd_def != "défini"
        text = f"{nfd_def} f(x):\n    si x:\n        return 1\n"
        # The NFD keyword itself is the block's own form, so it is kept.
        assert clean_text(text, local=FR) == (
            f"{nfd_def} f(x):\n    si x:\n        retourner 1\n"
        )


class TestTheStoredBlobDecidesTheBlock:
    def test_a_file_stored_in_english_stays_english(self):
        stored = "def f(x):\n    return x\n"
        text = "def f(x):\n    return x + 1\n"
        assert clean_text(text, local=ES, stored=stored) == text

    def test_a_file_stored_in_spanish_takes_back_english_strays(self):
        stored = "definir f(x):\n    devolver x\n"
        text = "definir f(x):\n    if x:\n        return x\n    devolver 0\n"
        assert clean_text(text, local=ES, stored=stored) == (
            "definir f(x):\n    si x:\n        devolver x\n    devolver 0\n"
        )

    def test_strays_are_normalized_even_while_the_file_does_not_parse(self):
        stored = "definir f():\n    devolver 1\n"
        text = "definir f()\n    return 1\n"  # missing colon, mid-edit
        assert clean_text(text, local=ES, stored=stored) == (
            "definir f()\n    devolver 1\n"
        )

    def test_local_keywords_typed_into_an_english_block_become_english(self):
        stored = "def f(x):\n    return x\n"
        text = "def f(x):\n    si x:\n        return x\n    devolver 0\n"
        assert clean_text(text, local=ES, stored=stored) == (
            "def f(x):\n    if x:\n        return x\n    return 0\n"
        )

    def test_local_keywords_are_kept_when_one_of_them_is_a_name(self):
        # `y` is Spanish `and`, but here it is the English author's
        # parameter. Reading every Spanish token as a keyword does not
        # parse, so nothing is rewritten; the guard reports the mixed block.
        stored = "def f(y):\n    return y\n"
        text = "def f(y):\n    si y:\n        return y\n"
        assert clean_text(text, local=ES, stored=stored) == text

    def test_a_local_word_that_parses_as_a_name_is_kept(self):
        # `nulo` is Spanish `None`, but this English block parses with it as
        # a name the author imported, and it parses with it read as `None`
        # too. Only a block that fails to parse as written confirms a keyword.
        text = "from .constants import *\n\ndef f():\n    return nulo\n"
        assert clean_text(text, local=ES, stored=text) == text

    def test_a_block_in_a_language_nobody_here_reads_is_left_alone(self):
        stored = "definir f(x):\n    devolver x\n"  # Spanish; local is French
        text = "definir f(x):\n    return x\n"
        assert clean_text(text, local=FR, stored=stored) == text


class TestTheMajorityDecides:
    """A keyword reading has to parse, and then the majority of keywords wins.

    Regression for the review of CORE-1841: one Spanish slip in an English
    file made the whole file read as Spanish, and every English keyword was
    rewritten.
    """

    ENGLISH_WITH_A_SLIP = (
        "import os\n\n"
        "def main():\n"
        "    for name in os.listdir('.'):\n"
        "        si name.endswith('.py'):\n"
        "            print(name)\n"
        "    return None\n"
    )

    def test_one_local_slip_in_an_english_file_is_fixed_not_spread(self):
        assert clean_text(self.ENGLISH_WITH_A_SLIP, local=ES) == (
            self.ENGLISH_WITH_A_SLIP.replace("si name", "if name")
        )

    def test_a_tie_decides_nothing(self):
        text = "definir f():\n    return 1\n"
        assert clean_text(text, local=ES) == text

    CZECH_LAMBDAS = (
        "sq = lambda x: x * x\n"
        "inc = lambda x: x + 1\n"
        "dbl = lambda x: x * 2\n\n"
        "definuj f(x):\n"
        "    vrať sq(inc(x))\n"
    )

    def test_a_spelling_a_pack_shares_with_english_is_no_vote(self):
        # cs spells `lambda` as `lambda`; three of them must not outvote the
        # author's own `definuj` and `vrať` (re-review of CORE-1841).
        assert block_language(self.CZECH_LAMBDAS, [EN, CS]) == "cs"
        text = self.CZECH_LAMBDAS + "\ndefinuj g(x):\n    return x\n"
        assert clean_text(text, local=CS, stored=self.CZECH_LAMBDAS) == (
            self.CZECH_LAMBDAS + "\ndefinuj g(x):\n    vrať x\n"
        )

    def test_without_parse_evidence_nothing_moves(self):
        # Neither reading parses (mid-edit), so a count alone decides nothing.
        text = "definir f(x):\n    si x:\n        return 1 +\n"
        assert clean_text(text, local=ES) == text


class TestLoneCarriageReturn:
    """Python reads a lone CR as a line break; so must the normalizer."""

    def test_a_stray_right_after_a_lone_cr_is_found(self):
        # tokenize over StringIO reads "\rif" as an OP token "\ri" plus a
        # NAME "f", so the `if` is invisible unless the CR is a line break.
        text = "definir f(x):\r    devolver x\rif verdadero:\r    pasar\r"
        assert clean_text(text, local=ES) == (
            "definir f(x):\r    devolver x\rsi verdadero:\r    pasar\r"
        )


class TestAmbiguousPackSpellings:
    def test_a_spelling_two_keywords_share_is_never_read_back(self):
        from legesher_core.stored_form import _build_table

        table = _build_table("xx", {"if": "a", "is": "a", "def": "d"})
        assert dict(table.hard_to_english) == {"d": "def"}
        assert table.spell("if") == "a"


class TestIdempotence:
    @pytest.mark.parametrize(
        ("text", "local", "stored"),
        [
            ("definir f(x):\n    if x:\n        return 1\n", ES, None),
            ("تعريف f(x):\n    إذا x:\n        return x\n", AR, None),
            (
                "def f(x):\n    si x:\n        return x\n",
                ES,
                "def f(x):\n    return x\n",
            ),
            ("def f(x, y):\n    return y\n", ES, None),
        ],
    )
    def test_clean_of_clean_is_clean(self, text, local, stored):
        once = clean_text(text, local=local, stored=stored)
        assert clean_text(once, local=local, stored=stored) == once


class TestBlockLanguage:
    def test_english(self):
        assert block_language("def f():\n    return 1\n", [EN, ES]) == "en"

    def test_spanish_with_english_strays(self):
        text = "definir f():\n    if x:\n        devolver 1\n"
        assert block_language(text, [EN, ES]) == "es"

    def test_english_whose_names_collide_with_spanish_keywords(self):
        assert block_language("x, y = 1, 2\nif y:\n    pass\n", [EN, ES]) == "en"

    def test_no_keywords_at_all(self):
        assert block_language("x = 1\nprint(x)\n", [EN, ES]) is None

    def test_a_language_outside_the_candidates(self):
        text = "definir f(x):\n    devolver x\n"
        assert block_language(text, [EN, FR]) is None


class TestKeywordOnlySmudge:
    def test_renders_keywords_only(self):
        stored = "def f(x):\n    if x:\n        return print(x)\n"
        assert smudge_text(stored, reader=ES) == (
            "definir f(x):\n    si x:\n        devolver print(x)\n"
        )

    def test_the_rendering_cleans_back_to_the_stored_form(self):
        stored = "def f(x):\n    for i in x:\n        pass\n    return None\n"
        rendered = smudge_text(stored, reader=AR)
        assert rendered != stored
        assert clean_text(rendered, local=AR, stored=stored) == stored

    def test_a_name_that_would_read_as_a_reader_keyword_blocks_the_render(self):
        # `y` would come back as `and`, so the file is left as stored.
        stored = "def f(y):\n    return y\n"
        assert smudge_text(stored, reader=ES) == stored

    def test_a_block_already_in_the_readers_language_is_left_alone(self):
        stored = "definir f():\n    devolver 1\n"
        assert smudge_text(stored, reader=ES) == stored

    def test_never_renders_into_a_file_it_cannot_identify(self):
        stored = "x = 1\n"
        assert smudge_text(stored, reader=ES) == stored
