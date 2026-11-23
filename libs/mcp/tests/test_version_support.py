"""Python-version handling: the derived enum, non-default versions end to end.

The suite's default version is 3.13 everywhere else; this module is the one
that leaves it, so version-specific pack inheritance is exercised at the MCP
surface rather than only at the engine layer (CORE-1806).
"""

from __future__ import annotations

import json

import pytest
from legesher_i18n.pack_loader import LanguagePackLoader
from mcp import ClientSession, McpError
from pydantic import AnyUrl

from legesher_mcp.schemas import DEFAULT_PYTHON_VERSION, SUPPORTED_PYTHON_VERSIONS
from legesher_mcp.versions import _FALLBACK_VERSIONS, discover_python_versions
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio

#: Every supported version except the default — the untested territory.
NON_DEFAULT_VERSIONS = [v for v in SUPPORTED_PYTHON_VERSIONS if v != DEFAULT_PYTHON_VERSION]

SAMPLE = "def greet(name):\n    print(name)\n"


def test_version_index_comes_from_the_packs_on_disk() -> None:
    """The enum is derived, not hand-maintained: it equals the pack index."""
    on_disk = LanguagePackLoader().list_available_versions("python")
    assert list(SUPPORTED_PYTHON_VERSIONS) == on_disk
    assert DEFAULT_PYTHON_VERSION in SUPPORTED_PYTHON_VERSIONS


def test_version_index_is_numerically_sorted() -> None:
    """3.9 must precede 3.10 — string sort gets this backwards."""
    as_tuples = [tuple(int(p) for p in v.split(".")) for v in SUPPORTED_PYTHON_VERSIONS]
    assert as_tuples == sorted(as_tuples)


def test_discovery_falls_back_when_no_packs_are_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pack-less install still publishes a usable enum instead of an empty one."""
    monkeypatch.setattr(LanguagePackLoader, "list_available_versions", lambda self, target: [])
    assert discover_python_versions() == _FALLBACK_VERSIONS


def test_discovery_always_includes_the_default_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The tools' default must be a member or pydantic rejects it at import."""
    monkeypatch.setattr(
        LanguagePackLoader, "list_available_versions", lambda self, target: ["3.14"]
    )
    discovered = discover_python_versions()
    assert DEFAULT_PYTHON_VERSION in discovered
    assert "3.14" in discovered


def test_discovery_survives_a_broken_pack_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Import must not fail because the filesystem scan blew up."""

    def explode(self: LanguagePackLoader, target: str) -> list[str]:
        raise OSError("pack root unreadable")

    monkeypatch.setattr(LanguagePackLoader, "list_available_versions", explode)
    assert discover_python_versions() == _FALLBACK_VERSIONS


@pytest.mark.parametrize("python_version", NON_DEFAULT_VERSIONS)
async def test_translate_round_trip_on_every_supported_version(
    client: ClientSession, python_version: str
) -> None:
    """en→es→en is byte-identical on every version, not just the default."""
    native = await call_ok(
        client,
        "translate_to_native",
        {"source": SAMPLE, "target_lang": "es", "python_version": python_version},
    )
    assert native["python_version"] == python_version
    back = await call_ok(
        client,
        "translate_to_source",
        {
            "source": native["translated_source"],
            "source_lang": "es",
            "python_version": python_version,
        },
    )
    assert back["translated_source"] == SAMPLE


@pytest.mark.parametrize("python_version", NON_DEFAULT_VERSIONS)
async def test_lookup_on_every_supported_version(
    client: ClientSession, python_version: str
) -> None:
    """Version-specific pack inheritance resolves through the MCP layer."""
    result = await call_ok(
        client,
        "lookup_keyword_mapping",
        {"language": "es", "terms": ["def"], "python_version": python_version},
    )
    assert result["python_version"] == python_version
    assert result["mappings"]["keywords"]["def"]
    assert result["unmatched_terms"] == []


async def test_unsupported_version_is_rejected_by_the_schema(client: ClientSession) -> None:
    """A version outside the published enum never reaches the pack loader."""
    message = await call_err(
        client,
        "lookup_keyword_mapping",
        {"language": "es", "python_version": "2.7"},
    )
    assert_sanitized(message)


@pytest.mark.parametrize("python_version", NON_DEFAULT_VERSIONS)
async def test_terms_resource_accepts_an_explicit_version(
    client: ClientSession, python_version: str
) -> None:
    result = await client.read_resource(AnyUrl(f"legesher://languages/es/terms/{python_version}"))
    (content,) = result.contents
    terms = json.loads(str(content.text))
    assert terms["language"] == "es"
    assert terms["python_version"] == python_version
    assert terms["keywords"]


async def test_terms_resource_defaults_to_the_current_version(client: ClientSession) -> None:
    """The unversioned URI keeps working and means "the default version"."""
    plain = await client.read_resource(AnyUrl("legesher://languages/es/terms"))
    explicit = await client.read_resource(
        AnyUrl(f"legesher://languages/es/terms/{DEFAULT_PYTHON_VERSION}")
    )
    assert json.loads(str(plain.contents[0].text)) == json.loads(str(explicit.contents[0].text))


async def test_terms_resource_rejects_an_unsupported_version(client: ClientSession) -> None:
    """Gated before the loader — the version is joined into a filename."""
    with pytest.raises(McpError) as excinfo:
        await client.read_resource(AnyUrl("legesher://languages/es/terms/9.9"))
    message = str(excinfo.value)
    assert "unsupported_python_version" in message
    assert_sanitized(message)


async def test_terms_resource_version_cannot_traverse_paths(client: ClientSession) -> None:
    """A crafted version is refused by the allowlist, not by the filesystem."""
    with pytest.raises(McpError) as excinfo:
        await client.read_resource(AnyUrl("legesher://languages/es/terms/..%2F..%2Fetc"))
    assert_sanitized(str(excinfo.value))


def _as_numbers(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def test_the_fallback_list_reaches_the_newest_release_the_term_inventory_registers() -> None:
    """A pack-less install offers every Python release the engine knows the words of.

    The fallback list is kept by hand, so a new release has to be added to it.
    The term inventory is where a release is registered first; tied to it, the
    list cannot be left behind.
    """
    from legesher_i18n.term_definitions import VERSION_ADDITIONS

    registered = [_as_numbers(version) for version in VERSION_ADDITIONS]
    assert registered, "the term inventory registers no release"
    assert _as_numbers(_FALLBACK_VERSIONS[-1]) >= max(registered)


def test_the_fallback_list_is_every_minor_in_order() -> None:
    """No release is skipped or repeated, and the list is oldest first."""
    as_numbers = [_as_numbers(version) for version in _FALLBACK_VERSIONS]
    major, first_minor = as_numbers[0]
    assert as_numbers == [(major, minor) for minor in range(first_minor, as_numbers[-1][1] + 1)]


def test_the_fallback_list_covers_every_tier_the_packs_ship() -> None:
    """With no packs installed the server must not offer less than it does with them."""
    on_disk = LanguagePackLoader().list_available_versions("python")
    assert on_disk, "no pack tier was discovered"
    assert set(on_disk) <= set(_FALLBACK_VERSIONS)
    assert DEFAULT_PYTHON_VERSION in _FALLBACK_VERSIONS
