"""Keep each block's keywords in its stored form (CORE-1841).

The stored form of a file is its author's language, not English. The git
clean filter only normalizes: it rewrites a stray keyword to the language its
block is stored in, and it never refuses. Refusal belongs to the guard
(:mod:`legesher_core.guard`), which the pre-commit hook runs.

What moves, and why it is safe:

- **English hard keywords** (``def``, ``if``, ``True``) inside a block stored
  in another language are rewritten to that language. A hard keyword can
  never be a name, an attribute or a keyword argument, so rewriting one cannot
  touch anything the author named. Soft keywords (``match``, ``case``,
  ``type``, ``_``) are names outside their statements and are left alone.
- **The local user's own keywords** typed into a block stored in another
  language are rewritten only when a parse confirms they are keywords: the
  block does not parse with them read as names, and does parse with them read
  as keywords. Otherwise they may be the author's names, and nothing moves.

Nothing else moves: names, builtins, strings, comments, whitespace, line
endings and a leading byte-order mark are returned byte for byte.

Which language a block is stored in: until in-file region markers (CORE-1542)
and the file header (CORE-1539) make it explicit, a file is one block. Its
language is read from the committed version (the caller passes it) or, for a
new file, from the text itself, among English and the local language. A
reading counts only when the text parses under it, and then the language with
the most keywords wins; a tie, or no reading that parses, decides nothing and
the text is returned unchanged. A file in a third language is left as written
unless every keyword it uses is spelled the same in the local language, which
bytes alone cannot tell apart.

The keyword-only smudge (:func:`smudge_text`) is the opt-in inverse for
terminal editors: it renders an English block's hard keywords in the reader's
language using open pack terms only, and it renders only when cleaning the
result gives back exactly what cleaning the stored text gives.
"""

from __future__ import annotations

import ast
import io
import keyword
import re
import sys
import tokenize
import unicodedata
import warnings
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache

ENGLISH = "en"
HARD_KEYWORDS: frozenset[str] = frozenset(keyword.kwlist)
_BOM = "﻿"


def _nfc(text: str) -> str:
    return text if text.isascii() else unicodedata.normalize("NFC", text)


@dataclass(frozen=True)
class KeywordTable:
    """One language's keyword spellings, keyed both ways.

    Attributes:
        language: Language code (``"en"`` for Python's own keywords).
        from_english: English hard keyword to this language's spelling.
        hard_to_english: This language's hard-keyword spelling (NFC) to the
            English keyword.
        to_english: Every keyword spelling, soft ones included (NFC), to
            English. Used only to test whether a block parses.
        except_star: The spelling of ``except`` when ``*`` follows it.
    """

    language: str
    from_english: Mapping[str, str] = field(default_factory=dict)
    hard_to_english: Mapping[str, str] = field(default_factory=dict)
    to_english: Mapping[str, str] = field(default_factory=dict)
    except_star: str = "except"

    def spell(self, english: str, before_star: bool = False) -> str:
        """Return this language's spelling of an English hard keyword."""
        if self.language == ENGLISH:
            return english
        if english == "except" and before_star:
            return self.except_star
        return self.from_english.get(english, english)


_ENGLISH_TABLE = KeywordTable(
    language=ENGLISH,
    from_english={kw: kw for kw in HARD_KEYWORDS},
    hard_to_english={kw: kw for kw in HARD_KEYWORDS},
    to_english={kw: kw for kw in HARD_KEYWORDS},
)


@lru_cache(maxsize=None)
def keyword_table(language: str, python_version: str | None = None) -> KeywordTable:
    """Load a language's keyword table from its pack (cached per process).

    Args:
        language: Language code. ``"en"`` needs no pack.
        python_version: Pack version; defaults to the running interpreter.

    Raises:
        Whatever the pack loader raises when the pack cannot be loaded.
    """
    if language == ENGLISH:
        return _ENGLISH_TABLE

    from legesher_i18n import LanguagePackLoader

    version = python_version or f"{sys.version_info.major}.{sys.version_info.minor}"
    pack = LanguagePackLoader().load(language, target="python", version=version)
    return _build_table(language, pack.keywords)


def _build_table(language: str, keywords: Mapping[str, str]) -> KeywordTable:
    """A keyword table from a pack's ``keywords`` mapping.

    A spelling two English keywords share is kept for rendering but never read
    back: there is no telling which keyword it meant.
    """
    from_english = {k: _nfc(v) for k, v in keywords.items() if k in HARD_KEYWORDS}
    uses = Counter(from_english.values())
    hard_to_english = {v: k for k, v in from_english.items() if uses[v] == 1}
    star = keywords.get("except*")
    except_star = from_english.get("except", "except")
    if star and star.endswith("*"):
        except_star = _nfc(star[:-1])
        hard_to_english.setdefault(except_star, "except")
    to_english = dict(hard_to_english)
    for english in keyword.softkwlist:
        if english in keywords:
            to_english.setdefault(_nfc(keywords[english]), english)
    return KeywordTable(
        language=language,
        from_english=from_english,
        hard_to_english=hard_to_english,
        to_english=to_english,
        except_star=except_star,
    )


@dataclass(frozen=True)
class _Name:
    start: int
    end: int
    string: str
    key: str
    before_star: bool


def _split_bom(text: str) -> tuple[str, str]:
    if text.startswith(_BOM):
        return _BOM, text[1:]
    return "", text


_LONE_CR = re.compile(r"\r(?!\n)")


def tokenizer_view(text: str) -> str:
    """``text`` with every lone CR as LF, the same length.

    Python reads a lone CR as a line break; ``tokenize`` over
    ``io.StringIO`` does not, and reads ``"\\rif"`` as an operator token
    ``"\\ri"`` followed by a name ``"f"``. Replacing one character with one
    keeps every offset valid in the original text.
    """
    return _LONE_CR.sub("\n", text) if "\r" in text else text


def _name_tokens(text: str) -> list[_Name] | None:
    """Every NAME token with its character offsets, or ``None``.

    ``None`` means the text cannot be tokenized, or a token's reported
    position does not land on its own spelling. Either way there are no
    offsets it is safe to rewrite at.
    """
    # io.StringIO's readline breaks lines at "\n" only, so the line table is
    # built the same way; "\r\n" stays inside its line, and a lone CR has
    # already become "\n" in the view.
    text = tokenizer_view(text)
    line_starts = [0]
    index = text.find("\n")
    while index != -1:
        line_starts.append(index + 1)
        index = text.find("\n", index + 1)

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, ValueError):
        return None

    names: list[_Name] = []
    for position, tok in enumerate(tokens):
        if tok.type != tokenize.NAME:
            continue
        (start_row, start_col), (end_row, end_col) = tok.start, tok.end
        if not (0 < start_row <= len(line_starts) and 0 < end_row <= len(line_starts)):
            return None
        start = line_starts[start_row - 1] + start_col
        end = line_starts[end_row - 1] + end_col
        if text[start:end] != tok.string:
            return None
        following = tokens[position + 1] if position + 1 < len(tokens) else None
        before_star = (
            following is not None
            and following.type == tokenize.OP
            and following.string == "*"
        )
        names.append(_Name(start, end, tok.string, _nfc(tok.string), before_star))
    return names


def _splice(text: str, edits: Iterable[tuple[_Name, str]]) -> str:
    parts: list[str] = []
    cursor = 0
    for name, replacement in sorted(edits, key=lambda edit: edit[0].start):
        parts.append(text[cursor : name.start])
        parts.append(replacement)
        cursor = name.end
    parts.append(text[cursor:])
    return "".join(parts)


def _parses(source: str) -> bool:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            ast.parse(tokenizer_view(source))
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            return False
    return True


def _english_view(
    text: str, names: Sequence[_Name], tables: Sequence[KeywordTable]
) -> str:
    """The text with every keyword the tables know read as English."""
    edits = []
    for name in names:
        if name.string in HARD_KEYWORDS:
            continue
        for table in tables:
            english = table.to_english.get(name.key)
            if english is not None:
                edits.append((name, english))
                break
    return _splice(text, edits)


def _detect(
    text: str, names: Sequence[_Name], tables: Sequence[KeywordTable]
) -> str | None:
    english_hits = sum(1 for name in names if name.string in HARD_KEYWORDS)
    hits = {
        table.language: count
        for table in tables
        if table.language != ENGLISH
        and (
            count := sum(
                1
                for name in names
                if name.string not in HARD_KEYWORDS
                and name.key in table.hard_to_english
            )
        )
    }
    if not hits:
        return ENGLISH if english_hits else None

    by_language = {table.language: table for table in tables}
    fitting = [
        language
        for language in hits
        if _parses(_english_view(text, names, [by_language[language]]))
    ]
    if not fitting:
        # No reading of the localized spellings as keywords parses, so they
        # are names (an English author's `y` is not Spanish `and`).
        return ENGLISH if english_hits and _parses(text) else None
    # Every fitting reading parses; the language with the most keywords is
    # the block's, so one slip never outvotes the file around it. A keyword a
    # pack spells as English does (cs `lambda`) is evidence for neither side.
    winners = []
    for language in fitting:
        table = by_language[language]
        english_votes = sum(
            1
            for name in names
            if name.string in HARD_KEYWORDS
            and table.spell(name.string, name.before_star) != name.string
        )
        if hits[language] > english_votes:
            winners.append(language)
        elif hits[language] == english_votes:
            return None
    if not winners:
        return ENGLISH
    best = max(hits[language] for language in winners)
    leaders = [language for language in winners if hits[language] == best]
    return leaders[0] if len(leaders) == 1 else None


def block_language(text: str, candidates: Sequence[KeywordTable]) -> str | None:
    """Return the language a block is written in, or ``None``.

    Only the candidates are considered. A candidate is accepted when the text
    parses with its keywords read as keywords; English wins when the text
    already parses as English and uses at least one English keyword.
    ``None`` means no keywords, no candidate that parses, or a tie.
    """
    _, body = _split_bom(text)
    names = _name_tokens(body)
    if names is None:
        return None
    return _detect(body, names, candidates)


def _candidates(local: KeywordTable) -> list[KeywordTable]:
    if local.language == ENGLISH:
        return [_ENGLISH_TABLE]
    return [_ENGLISH_TABLE, local]


@dataclass(frozen=True)
class Stray:
    """A keyword that is not in its block's stored form.

    Attributes:
        offset: Character offset into the text as given (a leading byte-order
            mark counts).
        found: The keyword as written.
        stored: The spelling the block stores it as.
        language: The language the block is stored in.
    """

    offset: int
    found: str
    stored: str
    language: str


def _plan(
    text: str, local: KeywordTable, stored: str | None
) -> tuple[str, str, list[tuple[_Name, str]], str | None]:
    """``(bom, body, edits, block language)`` for one text."""
    bom, body = _split_bom(text)
    if not body.strip():
        return bom, body, [], None
    names = _name_tokens(body)
    if names is None:
        return bom, body, [], None

    tables = _candidates(local)
    language = block_language(stored, tables) if stored is not None else None
    if language is None:
        language = _detect(body, names, tables)
    if language is None:
        return bom, body, [], None
    block = next(table for table in tables if table.language == language)

    edits: list[tuple[_Name, str]] = []
    if language != ENGLISH:
        for name in names:
            if name.string in HARD_KEYWORDS:
                spelling = block.spell(name.string, name.before_star)
                if spelling != name.string:
                    edits.append((name, spelling))

    if local.language not in (language, ENGLISH):
        strays = [
            name
            for name in names
            if name.string not in HARD_KEYWORDS
            and name.key in local.hard_to_english
            and name.key not in block.to_english
        ]
        if (
            strays
            and not _parses(_english_view(body, names, [block]))
            and _parses(_english_view(body, names, [block, local]))
        ):
            for name in strays:
                english = local.hard_to_english[name.key]
                edits.append((name, block.spell(english, name.before_star)))

    edits.sort(key=lambda edit: edit[0].start)
    return bom, body, edits, language


def find_strays(
    text: str, *, local: KeywordTable, stored: str | None = None
) -> list[Stray]:
    """The keywords :func:`clean_text` would rewrite, in text order."""
    bom, _, edits, language = _plan(text, local, stored)
    if language is None:
        return []
    return [
        Stray(len(bom) + name.start, name.string, spelling, language)
        for name, spelling in edits
    ]


def clean_text(text: str, *, local: KeywordTable, stored: str | None = None) -> str:
    """Normalize stray keywords to their block's stored form.

    Never raises for any input and never changes anything but keyword tokens.
    ``clean_text(clean_text(x)) == clean_text(x)`` for the same arguments.

    Args:
        text: The working-tree text git hands the clean filter.
        local: The keyword table of the language this machine writes in.
        stored: The version git currently stores for this path, when there is
            one. It decides the block's language; a new file decides it from
            its own text.
    """
    bom, body, edits, _ = _plan(text, local, stored)
    if not edits:
        return text
    return bom + _splice(body, edits)


def smudge_text(stored: str, *, reader: KeywordTable) -> str:
    """Render an English block's hard keywords in the reader's language.

    The opt-in keyword-only smudge. Open pack keywords only: builtins, names
    and library vocabulary are never rendered. The rendering is returned only
    when cleaning it gives exactly what cleaning ``stored`` gives, so
    ``smudge -> clean`` never changes what git stores; otherwise ``stored`` is
    returned unchanged.
    """
    if reader.language == ENGLISH:
        return stored
    bom, body = _split_bom(stored)
    if not body.strip():
        return stored
    names = _name_tokens(body)
    if names is None:
        return stored
    if _detect(body, names, _candidates(reader)) != ENGLISH:
        return stored

    edits = [
        (name, reader.spell(name.string, name.before_star))
        for name in names
        if name.string in HARD_KEYWORDS
    ]
    rendered = bom + _splice(body, [e for e in edits if e[1] != e[0].string])
    if clean_text(rendered, local=reader, stored=stored) != clean_text(
        stored, local=reader, stored=stored
    ):
        return stored
    return rendered


__all__ = [
    "ENGLISH",
    "HARD_KEYWORDS",
    "KeywordTable",
    "Stray",
    "block_language",
    "clean_text",
    "find_strays",
    "keyword_table",
    "smudge_text",
]
