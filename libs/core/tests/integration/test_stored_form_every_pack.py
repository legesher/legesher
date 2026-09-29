"""The clean filter's normalizer holds for every pack, on every commit (CORE-1841).

For each active pack and each corpus file (all English), three properties:

* **keyword-only smudge renders**: ``smudge_text`` rewrites the file's hard
  keywords into the pack's language, and cleaning that rendering against the
  English stored file gives the English file back, byte for byte;
* **an English working copy returns to its stored form**: with the pack's
  rendering as what git stores, cleaning the English file yields exactly that
  rendering, every English keyword a stray;
* **clean is idempotent** on a block already in its stored form.

Known failures are strict xfails. A name that reads as one of the pack's
keywords (CORE-1840's ``y`` for Spanish ``and``) blocks the smudge on
purpose, because cleaning the rendering could not tell the name from the
keyword; the render is refused rather than written.
"""

from __future__ import annotations

import io
import sys
import tokenize

import pytest

from legesher_core.stored_form import (
    HARD_KEYWORDS,
    KeywordTable,
    clean_text,
    keyword_table,
    smudge_text,
)
from legesher_i18n import get_active_language_codes
from tests.corpus import CorpusFile, corpus_for
from tests.interpreter_gaps import PURE_PYTHON_TOKENIZER

RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

LANGUAGES: tuple[str, ...] = tuple(
    sorted(code for code in get_active_language_codes() if code != "en")
)

ENTRIES: tuple[CorpusFile, ...] = corpus_for(RUNNING_VERSION)

#: (language, corpus file) pairs where the keyword-only smudge is refused.
#: CORE-1840: the file uses a name spelled like one of the pack's keywords,
#: so the rendering cannot be cleaned back unambiguously.
KNOWN_REFUSED_RENDERS: dict[tuple[str, str], str] = {
    **{
        (language, "sample_english.py"): (
            "CORE-1840: identifier `e` reads as the pack's word for `and`, "
            "so the keyword-only smudge refuses the render"
        )
        for language in ("gl", "it", "pt")
    },
    ("es", "pattern_matching.py"): (
        "CORE-1840: identifier `y` reads as the pack's word for `and`, "
        "so the keyword-only smudge refuses the render"
    ),
}


def _names(source: str) -> list[str]:
    return [
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.NAME
    ]


#: Files with at least one hard keyword; the others have nothing to render.
WITH_KEYWORDS: tuple[CorpusFile, ...] = tuple(
    entry for entry in ENTRIES if HARD_KEYWORDS & set(_names(entry.source))
)
WITHOUT_KEYWORDS: tuple[CorpusFile, ...] = tuple(
    entry for entry in ENTRIES if entry not in WITH_KEYWORDS
)


def _fragmenting_spellings(table: KeywordTable, source: str) -> list[str]:
    """Spellings this file would render that the running tokenizer splits."""
    used = {name for name in _names(source) if name in HARD_KEYWORDS}
    fragmenting = []
    for english in sorted(used):
        spelling = table.spell(english)
        tokens = [
            token
            for token in tokenize.generate_tokens(io.StringIO(spelling + "\n").readline)
            if token.type not in (tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER)
        ]
        if len(tokens) != 1 or tokens[0].type != tokenize.NAME:
            fragmenting.append(spelling)
    return fragmenting


def _apply_ledgers(
    request: pytest.FixtureRequest, code: str, entry: CorpusFile
) -> None:
    known = KNOWN_REFUSED_RENDERS.get((code, entry.name))
    if known:
        request.applymarker(pytest.mark.xfail(strict=True, reason=known))
        return
    if PURE_PYTHON_TOKENIZER:
        fragments = _fragmenting_spellings(keyword_table(code), entry.source)
        if fragments:
            request.applymarker(
                pytest.mark.xfail(
                    strict=True,
                    reason=(
                        "pure-Python tokenize reads "
                        f"{', '.join(fragments)} as fragments, so the rendering "
                        "cannot be cleaned back and the smudge refuses it "
                        "(tests/interpreter_gaps.py, gap 1)"
                    ),
                )
            )


def test_sweep_is_not_vacuous():
    assert len(LANGUAGES) >= 50, LANGUAGES
    assert len(WITH_KEYWORDS) >= 8, [entry.name for entry in WITH_KEYWORDS]


def test_ledger_entries_are_reachable():
    reachable = {(code, entry.name) for code in LANGUAGES for entry in WITH_KEYWORDS}
    orphaned = sorted(set(KNOWN_REFUSED_RENDERS) - reachable)
    assert not orphaned, orphaned


@pytest.mark.parametrize("entry", WITHOUT_KEYWORDS, ids=lambda entry: entry.name)
@pytest.mark.parametrize("code", LANGUAGES)
def test_a_file_without_keywords_is_never_rewritten(code, entry):
    table = keyword_table(code)
    assert smudge_text(entry.source, reader=table) == entry.source
    assert clean_text(entry.source, local=table) == entry.source


@pytest.mark.parametrize("entry", WITH_KEYWORDS, ids=lambda entry: entry.name)
@pytest.mark.parametrize("code", LANGUAGES)
def test_keyword_smudge_renders_and_cleans_back(request, code, entry):
    _apply_ledgers(request, code, entry)
    table = keyword_table(code)
    rendered = smudge_text(entry.source, reader=table)
    assert rendered != entry.source, f"{code}: smudge refused {entry.name}"
    back = clean_text(rendered, local=table, stored=entry.source)
    assert back == entry.source


@pytest.mark.parametrize("entry", WITH_KEYWORDS, ids=lambda entry: entry.name)
@pytest.mark.parametrize("code", LANGUAGES)
def test_english_working_copy_returns_to_the_stored_form(request, code, entry):
    _apply_ledgers(request, code, entry)
    table = keyword_table(code)
    stored = smudge_text(entry.source, reader=table)
    assert stored != entry.source, f"{code}: no stored rendering for {entry.name}"
    assert clean_text(entry.source, local=table, stored=stored) == stored
    assert clean_text(stored, local=table, stored=stored) == stored
