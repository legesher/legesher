import re
import sys
import tokenize
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _story_fixtures import FIXTURES, copy_story, edit_words  # noqa: E402
from _tokens import token_stream  # noqa: E402
from generate_snippets import load_packs  # noqa: E402
from stories import (  # noqa: E402
    StoryError,
    copy_text_issues,
    language_digests,
    load_story,
    story_variants,
)


@pytest.fixture(scope="module")
def bundles():
    return load_packs()


@pytest.fixture(scope="module")
def story():
    return load_story(FIXTURES / "ok-playground")


def test_arabic_variant_has_no_latin_left(story, bundles):
    v = story_variants(story, bundles)["ar"]
    assert v.rtl and v.draft
    assert not re.search(r"[A-Za-z]", v.copy_text)
    assert v.copy_text.startswith(
        bundles["ar"]["keywords"]["def"] + " اقسم(بسط, مقام):"
    )
    assert v.output == (FIXTURES / "ok-playground" / "output.ar.txt").read_text(
        encoding="utf-8"
    )


def test_spanish_variant_uses_names_and_strings(story, bundles):
    v = story_variants(story, bundles)["es"]
    assert not v.rtl and v.draft
    assert "dividir(numerador, denominador)" in v.copy_text
    assert (
        '"no se puede dividir"' in v.copy_text and '"cannot divide"' not in v.copy_text
    )
    assert v.output.startswith("se intentó 10 / 2\n")


def test_language_without_word_list_keeps_names_and_english_output(story, bundles):
    v = story_variants(story, bundles)["hi"]
    assert "divide(" in v.copy_text and '"cannot divide"' in v.copy_text
    assert v.output == story.outputs["en"] and v.draft is False


def test_every_language_gets_a_variant_english_first(story, bundles):
    variants = story_variants(story, bundles)
    assert set(variants) == set(bundles)
    assert next(iter(variants)) == "en"
    assert variants["en"].copy_text == story.sample


def test_spans_join_to_the_copy_text(story, bundles):
    for v in story_variants(story, bundles).values():
        assert "".join(t for t, _ in v.spans) == v.copy_text


def test_editor_story_variants_carry_no_output(bundles):
    variants = story_variants(load_story(FIXTURES / "ok-editor"), bundles)
    assert all(v.output is None and v.draft is False for v in variants.values())


def test_unused_word_entry_fails(tmp_path, bundles):
    d = copy_story(tmp_path, "single-quoted")
    edit_words(
        d,
        "ar",
        lambda w: w["strings"].update({"'by zero'": w["strings"].pop('"by zero"')}),
    )
    with pytest.raises(
        StoryError, match=r"^stories/single-quoted/words\.ar\.yml: .*'by zero'"
    ):
        story_variants(load_story(d), bundles)


def test_unused_name_fails(tmp_path, bundles):
    d = copy_story(tmp_path, "unused-name")
    edit_words(d, "es", lambda w: w["names"].update(quotient="cociente"))
    with pytest.raises(
        StoryError, match=r"^stories/unused-name/words\.es\.yml: .*quotient"
    ):
        story_variants(load_story(d), bundles)


def test_word_value_that_is_not_a_string_literal_fails(tmp_path, bundles):
    d = copy_story(tmp_path, "unquoted")
    edit_words(d, "ar", lambda w: w["strings"].update({'"by zero"': "على صفر"}))
    with pytest.raises(
        StoryError, match=r"^stories/unquoted/words\.ar\.yml: .*string literal"
    ):
        story_variants(load_story(d), bundles)


def test_name_colliding_with_a_pack_word_fails(tmp_path, bundles):
    d = copy_story(tmp_path, "collides")
    print_word = bundles["ar"]["builtins"]["print"]
    edit_words(d, "ar", lambda w: w["names"].update(divide=print_word))
    with pytest.raises(SystemExit):
        story_variants(load_story(d), bundles)


def test_bidi_control_in_copy_text_is_refused(tmp_path, bundles):
    d = copy_story(tmp_path, "bidi")
    edit_words(d, "ar", lambda w: w["strings"].update({'"by zero"': '"على‮صفر"'}))
    with pytest.raises(StoryError, match=r"^stories/bidi/words\.ar\.yml: .*U\+202E"):
        story_variants(load_story(d), bundles)


def test_copy_text_issues_reports_bidi_and_bom():
    found = copy_text_issues("﻿a‮b")
    assert any("U+202E" in f for f in found) and any("U+FEFF" in f for f in found)


def test_zwj_is_allowed_in_copy_text():
    assert copy_text_issues("ශ්‍රී") == []


def test_digests_are_per_language_and_follow_output(tmp_path, story, bundles):
    first = language_digests(story_variants(story, bundles))
    assert set(first) == set(bundles)
    assert first == language_digests(story_variants(story, bundles))
    d = copy_story(tmp_path, "changed-output")
    (d / "output.ar.txt").write_text(
        (d / "output.ar.txt").read_text(encoding="utf-8").replace("None", "لاشيء"),
        encoding="utf-8",
    )
    changed = language_digests(story_variants(load_story(d), bundles))
    assert changed["ar"] != first["ar"]
    assert {k: v for k, v in changed.items() if k != "ar"} == {
        k: v for k, v in first.items() if k != "ar"
    }


@pytest.mark.parametrize("lang", ["ar", "es"])
def test_round_trip_restores_the_sample(lang, story, bundles):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "libs" / "core"))
    core = pytest.importorskip(
        "legesher_core"
    )  # tree-sitter; skips in docs CI as test_engine_drift does
    v = story_variants(story, bundles)[lang]
    # The direction legesher run uses: an en->lang translator, reversed.
    translator = core.TokenTranslator.from_language_pack(
        lang, python_version="3.12"
    ).reverse()
    back = translator.translate_code(v.copy_text)
    names = {b: a for a, b in story.words[lang].names.items()}
    strings = {b: a for a, b in story.words[lang].strings.items()}

    def restore(kind, text):
        if kind == tokenize.NAME:
            return names.get(text, text)
        if kind == tokenize.STRING:
            return strings.get(text, text)
        return text

    assert [restore(k, s) for k, s in token_stream(back)] == [
        s for _, s in token_stream(story.sample)
    ]
