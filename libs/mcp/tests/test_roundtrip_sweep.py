"""Round-trip property sweep across packs, at the MCP surface (CORE-1745).

The round-trip guarantee — native → canonical → native, byte-identical — is
the deterministic layer's core promise and rule 8 of the AGENTS.md policy.
It is asserted at the engine layer for single files elsewhere; here it is
asserted through an MCP client session, which is the surface users touch,
against a corpus of real Python covering the whole construct space.

Two tiers, because all packs × the whole corpus is slow:

- **Per commit**: a fixed three-pack sample (see ``SAMPLE_PACKS``), part of
  the standard run.
- **Scheduled**: every active pack, marked ``scheduled`` and deselected by
  default. Run it with ``uv run pytest -m scheduled`` (or ``make
  test-mcp-scheduled``) before a release or after a pack change.

A failure names the language, the file, and the first line that diverged.
"""

from __future__ import annotations

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from legesher_mcp.engine import get_engine
from legesher_mcp.schemas import DEFAULT_PYTHON_VERSION
from legesher_mcp.server import mcp as server
from tests.conftest import call_ok
from tests.corpus import CorpusFile, corpus_for

pytestmark = pytest.mark.anyio

#: The per-commit sample: three packs chosen for script and direction spread
#: rather than at random, so a failure is reproducible from the name alone.
#: es — Latin script; ar — RTL, Arabic script; hi — Devanagari.
SAMPLE_PACKS = ("es", "ar", "hi")

#: Round-trip failures this sweep found on its first run — pre-existing
#: engine/pack defects, none of them in the MCP layer. Listed rather than
#: hidden: the corpus keeps exercising them, and each is a strict xfail, so
#: fixing one turns it into an XPASS failure that says "remove me".
#:
#: CORE-1839 is gone from this list — the nine packs whose `except*`
#: translation omitted the mirrored asterisk were corrected at the source
#: (the selection layer) and regenerated, and the identifier check now
#: refuses an unmirrored value outright, so the state cannot return.
#:
#: CORE-1840 — an identifier spelled like a native keyword (`e` = "and" in
#:   it/pt/gl, `y` = "and" in es) is rewritten into the keyword on the way
#:   back, so `except KeyError as e:` returns as `except KeyError as and:`.
KNOWN_ROUND_TRIP_FAILURES: dict[tuple[str, str], str] = {
    **{
        (language, "libs/core/tests/fixtures/sample_english.py"): (
            "CORE-1840: identifier `e` collides with the pack's word for `and`"
        )
        for language in ("gl", "it", "pt")
    },
    ("es", "pattern_matching.py"): (
        "CORE-1840: identifier `y` collides with the pack's word for `and`"
    ),
}


def all_pack_languages() -> list[str]:
    """Every language with a Python pack installed, minus the pivot itself."""
    return sorted(
        info.code
        for info in get_engine().list_languages()
        if info.pack_available and info.code != "en"
    )


def first_divergence(left: str, right: str) -> str:
    """Human-readable report of where two sources stop matching."""
    left_lines = left.splitlines()
    right_lines = right.splitlines()
    for number, (before, after) in enumerate(zip(left_lines, right_lines), start=1):
        if before != after:
            return f"line {number}:\n  expected: {before!r}\n  actual:   {after!r}"
    if len(left_lines) != len(right_lines):
        return f"line count differs: expected {len(left_lines)}, got {len(right_lines)}"
    return "sources differ only in trailing whitespace"


async def assert_round_trips(
    client: ClientSession, language: str, entry: CorpusFile, python_version: str
) -> None:
    """Both directions byte-identical, and both forms statically valid."""
    context = f"[{language}] {entry.name} (py{python_version})"

    native = (
        await call_ok(
            client,
            "translate_to_native",
            {
                "source": entry.source,
                "target_lang": language,
                "python_version": python_version,
            },
        )
    )["translated_source"]

    # canonical → native → canonical
    back_to_canonical = (
        await call_ok(
            client,
            "translate_to_source",
            {
                "source": native,
                "source_lang": language,
                "python_version": python_version,
            },
        )
    )["translated_source"]
    assert back_to_canonical == entry.source, (
        f"{context}: canonical→native→canonical diverged at "
        f"{first_divergence(entry.source, back_to_canonical)}"
    )

    # native → canonical → native
    back_to_native = (
        await call_ok(
            client,
            "translate_to_native",
            {
                "source": back_to_canonical,
                "target_lang": language,
                "python_version": python_version,
            },
        )
    )["translated_source"]
    assert back_to_native == native, (
        f"{context}: native→canonical→native diverged at {first_divergence(native, back_to_native)}"
    )

    # Static validation passes on the canonical form...
    canonical_check = await call_ok(
        client,
        "explain_in_language",
        {
            "source": entry.source,
            "explain_in": language,
            "python_version": python_version,
        },
    )
    assert canonical_check["validation"]["valid"] is True, (
        f"{context}: canonical form failed validation: {canonical_check['validation']['issue']}"
    )

    # ...and on the native form, read back through its own language.
    native_check = await call_ok(
        client,
        "explain_in_language",
        {
            "source": native,
            "explain_in": "en",
            "code_lang": language,
            "python_version": python_version,
        },
    )
    assert native_check["validation"]["valid"] is True, (
        f"{context}: native form failed validation: {native_check['validation']['issue']}"
    )


# -- per-commit sample -----------------------------------------------------


@pytest.mark.parametrize("language", SAMPLE_PACKS)
@pytest.mark.parametrize("entry", corpus_for(DEFAULT_PYTHON_VERSION), ids=lambda e: e.name)
async def test_round_trip_sample(
    client: ClientSession, language: str, entry: CorpusFile, request: pytest.FixtureRequest
) -> None:
    """The three-pack sample that runs on every commit."""
    known = KNOWN_ROUND_TRIP_FAILURES.get((language, entry.name))
    if known:
        request.applymarker(pytest.mark.xfail(strict=True, reason=known))
    await assert_round_trips(client, language, entry, DEFAULT_PYTHON_VERSION)


async def test_sample_packs_are_actually_installed() -> None:
    """A sample pointing at a missing pack would pass by testing nothing."""
    available = set(all_pack_languages())
    missing = [language for language in SAMPLE_PACKS if language not in available]
    assert not missing, f"sample packs not installed: {missing}"


async def test_corpus_is_not_silently_empty() -> None:
    """Guards the version gate: a bad comparison could filter everything out."""
    entries = corpus_for(DEFAULT_PYTHON_VERSION)
    assert len(entries) >= len(SAMPLE_PACKS)
    assert all(entry.source.strip() for entry in entries)


def test_corpus_is_valid_python() -> None:
    """The corpus has to compile, or the sweep is testing broken input."""
    for entry in corpus_for(DEFAULT_PYTHON_VERSION):
        compile(entry.source, entry.name, "exec", dont_inherit=True)


# -- scheduled: every pack -------------------------------------------------


@pytest.mark.scheduled
async def test_round_trip_every_pack() -> None:
    """All active packs × the whole corpus. Deselected by default.

    One session for the whole sweep (the translator cache is the expensive
    part), and every pack is attempted before failing so one broken pack
    does not hide the others.
    """
    languages = all_pack_languages()
    assert languages, "no packs discovered — the sweep would pass vacuously"
    entries = corpus_for(DEFAULT_PYTHON_VERSION)

    failures: list[str] = []
    fixed: list[str] = []
    async with create_connected_server_and_client_session(server) as client:
        for language in languages:
            for entry in entries:
                known = KNOWN_ROUND_TRIP_FAILURES.get((language, entry.name))
                try:
                    await assert_round_trips(client, language, entry, DEFAULT_PYTHON_VERSION)
                except AssertionError as exc:
                    if known is None:
                        failures.append(str(exc))
                else:
                    if known is not None:
                        fixed.append(f"({language}, {entry.name}) — {known}")

    assert not failures, "\n\n".join(
        [f"{len(failures)} new round-trip failures across {len(languages)} packs:", *failures]
    )
    assert not fixed, "\n".join(
        [
            "These are listed in KNOWN_ROUND_TRIP_FAILURES but now pass — remove them:",
            *fixed,
        ]
    )
