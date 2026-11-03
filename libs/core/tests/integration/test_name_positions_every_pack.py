"""Every pack keeps a builtin's name where it cannot be the builtin (CORE-2237).

Two sweeps over every active pack, in both directions:

* English to native: ``builtin_named_positions.py`` in the corpus puts names
  spelled like builtins after a dot and as keyword arguments. Each one must
  come out exactly as written, and the corpus must actually exercise the
  pack (at least one kept name is a term this pack renders differently).
* Native to English: every rendering of every builtin, exception and
  implicit parameter in the pack, after a dot, as a keyword argument and as
  a module path, must come back exactly as written. These inputs come from
  the pack itself, so a new term is covered the day it ships.

Renderings that the running tokenizer cannot read whole (CPython 3.10 and
3.11, ``tests/interpreter_gaps.py`` gap 1) are left out of the native sweep:
the return hop never sees them, so they would pass without testing anything.
"""

from __future__ import annotations

import functools
import io
import sys
import tokenize

import pytest

from legesher_core import create_translator_from_language_pack
from legesher_core.name_positions import name_roles
from legesher_core.utils import merge_exception_translations
from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from tests.corpus import CORPUS_DIR
from tests.interpreter_gaps import (
    fragmenting_renderings,
    skip_if_return_hop_is_inert,
    xfail_if_unloadable_here,
)

RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

LANGUAGES: tuple[str, ...] = tuple(
    sorted(code for code in get_active_language_codes() if code != "en")
)

CORPUS_FILE = "builtin_named_positions.py"


@functools.cache
def translators(code: str, tree_sitter: bool):
    forward = create_translator_from_language_pack(
        "python", code, RUNNING_VERSION, use_tree_sitter=tree_sitter
    )
    return forward, forward.reverse()


@functools.cache
def pack(code: str):
    return LanguagePackLoader().load(code, target="python", version=RUNNING_VERSION)


def tokens_of(source: str) -> list[tokenize.TokenInfo]:
    return list(tokenize.generate_tokens(io.StringIO(source).readline))


def renderings(code: str) -> dict[str, str]:
    """``{english: native}`` for every name a pack renders that is not a
    keyword, as the engine sees them (exceptions in Python's spelling)."""
    loaded = pack(code)
    names = {
        **merge_exception_translations(loaded.builtins, loaded.exceptions or {}),
        **(loaded.implicit_params or {}),
    }
    return {english: native for english, native in names.items() if native != english}


@pytest.fixture(autouse=True)
def _loadable(request):
    code = request.node.callspec.params.get("code")
    if code:
        xfail_if_unloadable_here(request, code, RUNNING_VERSION)


@pytest.mark.parametrize("tree_sitter", [False, True], ids=["token", "tree-sitter"])
@pytest.mark.parametrize("code", LANGUAGES)
def test_english_names_survive_the_forward_hop(code, tree_sitter):
    source = (CORPUS_DIR / CORPUS_FILE).read_text(encoding="utf-8")
    forward, _ = translators(code, tree_sitter)
    native = forward.translate_code(source)
    # Gap 1 splits the native rendering when it is read back, so the two
    # token lists no longer line up; the round trip of the same file is the
    # strict pin.
    skip_if_return_hop_is_inert(
        source,
        native,
        pinned_by=f"test_every_pack.py::test_round_trip_is_byte_identical[{code}-{CORPUS_FILE}]",
    )
    before, after = tokens_of(source), tokens_of(native)
    assert len(before) == len(after), f"{code}: the forward hop changed the token count"

    kept = name_roles(before, forward.mapper.get_keyword).kept
    rendered = renderings(code)
    exercised = [
        before[index].string for index in kept if before[index].string in rendered
    ]
    assert exercised, f"{code}: the corpus keeps no name this pack renders"
    for index, role in kept.items():
        assert after[index].string == before[index].string, (
            f"{code}: line {before[index].start[0]}: {role} "
            f"{before[index].string!r} became {after[index].string!r}"
        )


@pytest.mark.parametrize("tree_sitter", [False, True], ids=["token", "tree-sitter"])
@pytest.mark.parametrize("code", LANGUAGES)
def test_native_names_survive_the_return_hop(code, tree_sitter):
    rendered = renderings(code)
    loaded = pack(code)
    keyword_renderings = set(loaded.keywords.values())
    unreadable = set(fragmenting_renderings(rendered.values()))
    natives = sorted(
        {
            native
            for native in rendered.values()
            # A rendering that is also one of the pack's keywords is the
            # identifier/keyword collision class (CORE-2151), not this one.
            if native.isidentifier()
            and native not in keyword_renderings
            and native not in unreadable
        }
    )
    if not natives and unreadable:
        pytest.skip(
            f"{code}: every rendering is split by pure-Python tokenize "
            "(tests/interpreter_gaps.py, gap 1; CORE-2192)"
        )
    assert natives, f"{code}: no rendering to test"
    _, reverse = translators(code, tree_sitter)
    for native in natives:
        # ``import q4.{native}`` binds ``q4``, not the rendering, so
        # the attribute and keyword-argument rows are kept on their own
        # rule. The other names carry a digit so no pack's word can match
        # them (cs and pl spell ``from`` as ``z``).
        source = (
            f"q1.{native}\nq2({native}=1)\n"
            f"from {native}.{native} import q3\nimport q4.{native}\n"
        )
        assert reverse.translate_code(source) == source, f"{code}: {native!r}"
