"""Every shipped pack round-trips and compiles, on every commit (CORE-2128).

The MCP suite's all-packs sweep (``libs/mcp/tests/test_roundtrip_sweep.py``)
is scheduled rather than per commit because it goes through an MCP session
and validates both forms. At the engine layer the same sweep is cheap:
translate -> reverse -> compile of the whole corpus through every
non-English pack measured under two seconds when this sweep was added, so it runs here on every
commit. Same corpus (``tests/corpus.py``), same ledger shape, so a fix that
turns a known failure into a pass is reported by both sweeps as "remove me".

What every pack is held to, with the pack code (and the corpus file) in
the test id so a failure is reproducible from the name alone:

* every shipped grammar version loads, with keywords, builtins and
  exceptions populated;
* EN -> X -> EN is byte-identical, and ``first_divergence`` names the line;
* the EN result compiles under the running interpreter;
* the X rendering is NFC, the store-NFC half of the text-identity contract;
* the X rendering carries no bidi control, no invisible/format character
  and no default-ignorable character beyond what the language's script
  policy allows (ZWJ for si, ZWNJ for fa and ur);
* the corpus names every keyword, builtin and exception key of the running
  version's en pack. ``vocabulary.py`` is generated from those keys, so a
  new pack term fails the suite until the file is regenerated, and no
  pack's rendering of any term goes unexercised.

Known failures are ledgered as strict xfails in the same dict shape as the
MCP sweep. Fixing one turns it into an XPASS failure that says "remove me";
a new failure is never hidden.

Two interpreter gaps are pinned in ``tests/interpreter_gaps.py``: on
CPython 3.10 and 3.11 the return hop is inert for renderings the
pure-Python tokenizer fragments (marked xfail(strict) from the rendering
itself; the compile check skips and points at that pin), and before
Unicode 15.1 (CPython 3.13) the si and ja 3.13/3.14 pack files fail
schema validation and cannot load.
"""

from __future__ import annotations

import functools
import io
import sys
import tokenize
import unicodedata

import pytest

from legesher_core import create_translator_from_language_pack
from legesher_core.round_trip import first_divergence
from legesher_core.unicode_guard import scan_text
from legesher_core.utils import merge_exception_translations
from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.script_policy import policy_for
from tests.corpus import CORPUS_DIR, CorpusFile, corpus_for, load_manifest
from tests.interpreter_gaps import (
    skip_if_return_hop_is_inert,
    xfail_if_return_hop_is_inert,
    xfail_if_unloadable_here,
)

#: The interpreter running the suite; packs and corpus are selected for it.
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

#: Every active pack except the pivot itself.
LANGUAGES: tuple[str, ...] = tuple(
    sorted(code for code in get_active_language_codes() if code != "en")
)

#: Every grammar version some pack ships, discovered rather than listed.
PYTHON_VERSIONS: tuple[str, ...] = tuple(
    LanguagePackLoader().list_available_versions("python")
)

#: Grammar versions this sweep must at least cover; a discovery that drops
#: one of these is a broken install, not a shorter matrix.
SHIPPED_VERSIONS_FLOOR = frozenset({"3.10", "3.11", "3.12", "3.13", "3.14"})

#: Corpus entries the running grammar can express.
ENTRIES: tuple[CorpusFile, ...] = corpus_for(RUNNING_VERSION)

#: Round-trip failures the sweep knows about, keyed (language, corpus file).
#: Each is a strict xfail: the corpus keeps exercising it, and a fix turns
#: it into an XPASS failure that says "remove me". Same shape and same
#: cases as ``KNOWN_ROUND_TRIP_FAILURES`` in the MCP sweep.
#:
#: CORE-1840: an identifier spelled like a native keyword (``e`` = "and" in
#:   it/pt/gl, ``y`` = "and" in es) is rewritten into the keyword on the way
#:   back, so ``except KeyError as e:`` returns as ``except KeyError as and:``
#:   and ``case ["move", x, y]`` as ``case ["move", x, and]``. Both the
#:   byte-identity and the compile check fail on the same rewrite.
KNOWN_ROUND_TRIP_FAILURES: dict[tuple[str, str], str] = {
    **{
        (language, "sample_english.py"): (
            "CORE-1840: identifier `e` collides with the pack's word for `and`"
        )
        for language in ("gl", "it", "pt")
    },
    ("es", "pattern_matching.py"): (
        "CORE-1840: identifier `y` collides with the pack's word for `and`"
    ),
}


@functools.cache
def translators(code: str):
    """Forward and reverse translators for ``code``, built once per process.

    The token backend is pinned: the deterministic layer is what this
    sweep certifies, whatever ``LEGESHER_USE_TREE_SITTER`` says.
    """
    forward = create_translator_from_language_pack(
        "python", code, use_tree_sitter=False
    )
    return forward, forward.reverse()


@functools.cache
def round_trip(code: str, name: str) -> tuple[str, str]:
    """``(native, back)`` for one (pack, corpus file), computed once."""
    entry = next(entry for entry in ENTRIES if entry.name == name)
    forward, reverse = translators(code)
    native = forward.translate_code(entry.source, "en", code)
    back = reverse.translate_code(native, code, "en")
    return native, back


def _apply_ledger(request: pytest.FixtureRequest, code: str, entry: CorpusFile) -> None:
    known = KNOWN_ROUND_TRIP_FAILURES.get((code, entry.name))
    if known:
        request.applymarker(pytest.mark.xfail(strict=True, reason=known))


def _entry_id(entry: CorpusFile) -> str:
    return entry.name


# -- guards: the sweep must never pass by testing nothing --------------------


def test_sweep_is_not_vacuous():
    assert len(LANGUAGES) >= 50, LANGUAGES
    assert SHIPPED_VERSIONS_FLOOR <= set(PYTHON_VERSIONS), PYTHON_VERSIONS
    assert len(ENTRIES) >= 8, [entry.name for entry in ENTRIES]
    assert all(entry.source.strip() for entry in ENTRIES)


def test_manifest_matches_directory():
    """A construct file dropped in without a manifest row would be skipped."""
    on_disk = sorted(path.name for path in CORPUS_DIR.glob("*.py"))
    assert on_disk == sorted(load_manifest())


def test_ledger_entries_are_reachable():
    """A ledger row nothing parametrizes over is an xfail that never fires."""
    reachable = {(code, entry.name) for code in LANGUAGES for entry in ENTRIES}
    orphaned = sorted(set(KNOWN_ROUND_TRIP_FAILURES) - reachable)
    assert not orphaned, orphaned


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_corpus_is_valid_python(entry: CorpusFile):
    """The corpus has to compile, or the sweep is testing broken input."""
    compile(entry.source, entry.name, "exec", dont_inherit=True)


# -- coverage: the corpus names every term the en pack maps ------------------


def _name_tokens(source: str) -> set[str]:
    return {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.NAME
    }


def _entry(name: str) -> CorpusFile:
    return next(entry for entry in ENTRIES if entry.name == name)


def _newest(versions: tuple[str, ...]) -> str:
    return max(versions, key=lambda version: tuple(map(int, version.split("."))))


@pytest.fixture(scope="module")
def en_pack(loader: LanguagePackLoader):
    return loader.load("en", "python", RUNNING_VERSION)


def test_vocabulary_names_every_builtin_and_exception(en_pack):
    """``vocabulary.py`` is generated from the en pack keys; a term the pack
    gained since is reported here until the file is regenerated.

    Builtins are compared as the keys are spelled, because the token
    translator matches keys exactly. Exceptions go through the engine's own
    canonicalization (``merge_exception_translations``), so the file has to
    carry the name the translator will actually replace, ``ValueError``
    rather than the pack's ``valueerror``.
    """
    names = _name_tokens(_entry("vocabulary.py").source)
    canonical_exceptions = merge_exception_translations(
        {}, {key: key for key in en_pack.exceptions}
    )
    expected = set(en_pack.builtins) | set(canonical_exceptions)
    missing = sorted(expected - names)
    assert not missing, f"regenerate vocabulary.py; missing: {missing}"


def test_vocabulary_names_nothing_the_pack_does_not_map(loader: LanguagePackLoader):
    """The other direction: a misspelled name in the file would never be
    translated by any pack and the sweep would pass over it silently.
    Checked against the newest shipped en pack, case-insensitively, since
    the file is generated from the newest keys.
    """
    pack = loader.load("en", "python", _newest(PYTHON_VERSIONS))
    known = {key.lower() for key in pack.builtins} | set(pack.exceptions)
    unknown = sorted(
        name
        for name in _name_tokens(_entry("vocabulary.py").source)
        if name.lower() not in known
    )
    assert not unknown, unknown


def test_corpus_names_every_keyword(en_pack):
    """Every keyword key of the running version's en pack is written somewhere
    in the corpus the running grammar admits. ``except*`` is a compound key
    (NAME then OP), so it is looked for as text rather than as a token.
    """
    names = set().union(*(_name_tokens(entry.source) for entry in ENTRIES))
    text = "\n".join(entry.source for entry in ENTRIES)
    missing = sorted(
        keyword
        for keyword in en_pack.keywords
        if (keyword in text if keyword.endswith("*") else keyword in names) is False
    )
    assert not missing, f"no corpus file uses: {missing}"


# -- (a) every pack, every shipped grammar -----------------------------------


@pytest.fixture(scope="module")
def loader() -> LanguagePackLoader:
    return LanguagePackLoader()


@pytest.mark.parametrize("version", PYTHON_VERSIONS)
@pytest.mark.parametrize("code", LANGUAGES)
def test_pack_loads_for_every_shipped_version(
    loader: LanguagePackLoader, code: str, version: str, request: pytest.FixtureRequest
):
    xfail_if_unloadable_here(request, code, version)
    pack = loader.load(code, "python", version)
    assert pack.language == code
    assert pack.target == "python"
    assert pack.version == version
    assert pack.keywords, f"{code} {version}: no keywords"
    assert pack.builtins, f"{code} {version}: no builtins"
    assert pack.exceptions, f"{code} {version}: no exceptions"


# -- (b) byte-identical, (c) compiles ----------------------------------------


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("code", LANGUAGES)
def test_round_trip_is_byte_identical(
    code: str, entry: CorpusFile, request: pytest.FixtureRequest
):
    _apply_ledger(request, code, entry)
    native, back = round_trip(code, entry.name)
    xfail_if_return_hop_is_inert(request, entry.source, native)

    # A translator that changed nothing would round-trip vacuously.
    assert native != entry.source, f"[{code}] {entry.name}: nothing translated"
    assert back == entry.source, (
        f"[{code}] {entry.name}: EN->{code}->EN diverged at "
        f"{first_divergence(entry.source, back)}"
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("code", LANGUAGES)
def test_round_trip_result_compiles(
    code: str, entry: CorpusFile, request: pytest.FixtureRequest
):
    _apply_ledger(request, code, entry)
    native, back = round_trip(code, entry.name)
    skip_if_return_hop_is_inert(
        entry.source,
        native,
        pinned_by=f"test_round_trip_is_byte_identical[{code}-{entry.name}]",
    )

    compile(back, f"{entry.name} via {code}", "exec", dont_inherit=True)


# -- (d) NFC, (e) no invisible or bidi characters ----------------------------


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("code", LANGUAGES)
def test_native_rendering_is_nfc(code: str, entry: CorpusFile):
    native, _ = round_trip(code, entry.name)
    composed = unicodedata.normalize("NFC", native)
    assert composed == native, (
        f"[{code}] {entry.name}: rendering is not NFC at "
        f"{first_divergence(composed, native)}"
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("code", LANGUAGES)
def test_native_rendering_has_no_invisible_or_bidi_characters(
    code: str, entry: CorpusFile
):
    """``scan_text`` is the engine's own net: BIDI_CONTROLS (never
    suppressed), INVISIBLE_FORMAT (category Cf), DEFAULT_IGNORABLE, plus
    tatweel and an interior BOM, minus the format characters the
    language's script policy licenses.

    Bidi controls cannot reach this test: they are category Cf and never
    pass ``str.isidentifier()``, so a pack value carrying one fails schema
    validation and the pack does not load (``test_pack_loads_for_every_
    shipped_version`` fails first). This test's own value is the joiners:
    ZWJ and ZWNJ are identifier characters from Unicode 15.1, so a pack
    value carrying one loads, and only the per-language script policy says
    which language may use which (ZWJ for si, ZWNJ for fa and ur). A joiner
    in any other pack's rendering, or the wrong joiner, is caught here and
    nowhere earlier.
    """
    native, _ = round_trip(code, entry.name)
    allowed = policy_for(code).allowed_format_chars
    issues = scan_text(native, allowed_format_chars=allowed)
    assert not issues, f"[{code}] {entry.name}:\n" + "\n".join(
        f"  {issue.kind} {issue.codepoint} {issue.char_name} at offset {issue.offset}"
        for issue in issues
    )
