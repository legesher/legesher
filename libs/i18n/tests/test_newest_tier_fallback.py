"""On a Python newer than every tier of a pack, the loader serves that pack's newest tier.

Python 3.15 shipped before any pack had a ``3.15.yml``, and every surface that
takes the tier from the running interpreter (the import hook, ``legesher run``,
``translate``, the git filter, the traceback renderer) failed with
``PackNotFoundError`` in every language. The rule now lives in one
place, ``LanguagePackLoader.load``:

* A request newer than every tier a pack has is served that pack's newest tier.
  Tiers only grow, so a newer interpreter parses every older tier.
* Never downward. A request below a pack's floor raises
  ``UnsupportedInterpreterError``: an older interpreter never gets a newer
  tier (the ``si`` and ``ja`` 3.13 tiers would be a ``SyntaxError`` there).
* The newest tier is the pack's own, not the newest across all packs, so a
  pack that lags another is still served.
* Logged once per process, at INFO, naming the requested and the served tier.

The "newer" and "older" versions are derived from ``list_available_versions()``,
never written as literals, so the tests keep meaning the same thing when the
packs gain a tier.
"""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path

import pytest

from legesher_i18n import pack_loader
from legesher_i18n.exceptions import PackNotFoundError, UnsupportedInterpreterError
from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.schema_validator import SchemaValidator
from tests.interpreter_gaps import NEEDS_UNICODE_15_1

LOGGER = "legesher_i18n.pack_loader"


def _shift(version: str, minors: int) -> str:
    """``version`` moved by ``minors`` minor releases (``3.14`` + 1 is ``3.15``)."""
    major, minor = (int(part) for part in version.split("."))
    return f"{major}.{minor + minors}"


TIERS = LanguagePackLoader().list_available_versions("python")
NEWEST = TIERS[-1]
OLDEST = TIERS[0]
#: One minor release past every shipped tier (3.15 while the packs end at 3.14).
NEWER = _shift(NEWEST, 1)
#: One minor release below every shipped tier.
OLDER = _shift(OLDEST, -1)


def _needs_unicode_15_1(language: str) -> bool:
    """Whether ``language``'s pack files carry a character only CPython 3.13+ accepts.

    Read from the files themselves, so the marker follows the data: the
    validator checks identifiers with the running interpreter, and on 3.10 to
    3.12 it rejects those tiers (``tests/interpreter_gaps.py``).
    """
    packs_dir = LanguagePackLoader()._discover_packs()[f"python-{language}"] / "packs"
    text = "".join(path.read_text(encoding="utf-8") for path in packs_dir.glob("*.yml"))
    return any(ch in SchemaValidator._XID_ONLY_FROM_CPYTHON_313 for ch in text)


LANGUAGES = [
    pytest.param(code, marks=NEEDS_UNICODE_15_1) if _needs_unicode_15_1(code) else code
    for code in get_active_language_codes()
]


@pytest.fixture(autouse=True)
def _fresh_report_ledger(monkeypatch):
    """Each test starts with nothing logged yet; the ledger is per process."""
    monkeypatch.setattr(pack_loader, "_REPORTED_NEWER_REQUESTS", set())


def _sections(pack) -> dict[str, dict[str, str]]:
    return {
        "keywords": dict(pack.keywords),
        "builtins": dict(pack.builtins),
        "exceptions": dict(pack.exceptions),
        "implicit_params": dict(pack.implicit_params),
    }


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def _tier(
    language: str,
    version: str,
    *,
    floor: str | None = None,
    extends: str | None = None,
    declare_floor: bool = True,
) -> str:
    """A minimal valid pack file for one tier; ``declare_floor=False`` omits metadata."""
    lines = [
        f"language: {language}",
        "target: python",
        f"version: '{version}'",
    ]
    if extends:
        lines.append(f"extends: {extends}")
    lines += [
        "keywords:",
        f"  def: def_{version.replace('.', '_')}",
        "builtins: {}",
        "exceptions: {}",
    ]
    if declare_floor:
        lines += ["metadata:", f"  python_version_min: '{floor or version}'"]
    return "\n".join(lines) + "\n"


def _fake_pack(root: Path, language: str, tiers: dict[str, str]) -> Path:
    """A pack directory holding ``tiers`` ({version: yaml}); returns its package dir."""
    package = root / f"legesher_i18n_python_{language}"
    for version, body in tiers.items():
        _write(package / "packs" / f"{version}.yml", body)
    return package


def _loader_with(**packs: Path) -> LanguagePackLoader:
    loader = LanguagePackLoader()
    loader._discovered_packs = {f"python-{code}": path for code, path in packs.items()}
    return loader


class TestShippedPacks:
    """Every active language, through the real pack files."""

    def test_the_tiers_are_derived_not_written(self):
        # Guards the derivation itself: if the index were empty or unsorted the
        # tests below would compare nothing.
        assert len(TIERS) >= 2
        assert TIERS == sorted(TIERS, key=lambda v: tuple(int(p) for p in v.split(".")))
        assert NEWER not in TIERS and OLDER not in TIERS

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_a_newer_interpreter_is_served_the_newest_tier(self, language):
        served = LanguagePackLoader().load(language, "python", NEWER)
        newest = LanguagePackLoader().load(language, "python", NEWEST)
        # The served pack says which file it is, so nothing downstream can
        # mistake it for a NEWER tier that does not exist.
        assert served.version == NEWEST
        assert _sections(served) == _sections(newest)
        assert served.inheritance_chain == newest.inheritance_chain

    @pytest.mark.parametrize("language", get_active_language_codes())
    def test_a_request_below_the_floor_is_refused_not_served_upward(self, language):
        with pytest.raises(UnsupportedInterpreterError) as raised:
            LanguagePackLoader().load(language, "python", OLDER)
        message = str(raised.value)
        assert f"'{language}'" in message
        assert OLDER in message and OLDEST in message

    @pytest.mark.parametrize("language", ["ar", "he", "hi", "si"])
    def test_tooling_that_bypasses_the_floor_still_gets_no_older_file(self, language):
        # The exporters and the auditor pass enforce_min_interpreter=False to
        # read raw packs. There is no OLDER file, and none is invented.
        with pytest.raises(PackNotFoundError):
            LanguagePackLoader().load(
                language, "python", OLDER, enforce_min_interpreter=False
            )

    def test_the_fallback_is_logged_once_at_info(self, caplog):
        caplog.set_level(logging.DEBUG, logger=LOGGER)
        for language in ("ar", "he", "hi"):
            LanguagePackLoader().load(language, "python", NEWER)
        reports = [
            r for r in caplog.records if r.name == LOGGER and NEWER in r.getMessage()
        ]
        assert len(reports) == 1, [r.getMessage() for r in reports]
        assert reports[0].levelno == logging.INFO
        assert NEWEST in reports[0].getMessage()

    def test_an_existing_tier_is_served_as_is_and_not_logged(self, caplog):
        caplog.set_level(logging.DEBUG, logger=LOGGER)
        pack = LanguagePackLoader().load("ar", "python", NEWEST)
        assert pack.version == NEWEST
        assert not [
            r for r in caplog.records if r.name == LOGGER and r.levelno >= logging.INFO
        ]


class TestTheRule:
    """The rule's edges, on packs written for the test."""

    def test_the_newest_tier_is_the_packs_own_not_the_union(self, tmp_path):
        # xx has a 3.11 tier and yy does not. A union rule would see 3.11 as
        # "the newest tier", find no yy/3.11.yml and fail; yy is served its own.
        xx = _fake_pack(
            tmp_path,
            "xx",
            {
                "3.10": _tier("xx", "3.10"),
                "3.11": _tier("xx", "3.11", extends="3.10.yml"),
            },
        )
        yy = _fake_pack(tmp_path, "yy", {"3.10": _tier("yy", "3.10")})
        loader = _loader_with(xx=xx, yy=yy)
        assert loader.list_available_versions() == ["3.10", "3.11"]
        assert loader.load("yy", "python", "3.11").version == "3.10"
        assert loader.load("xx", "python", "3.12").version == "3.11"

    def test_the_served_tier_keeps_its_floor(self, tmp_path):
        # Never downward, even through the fallback: a tier whose declared
        # floor is above the request is refused, as it is without the fallback.
        zz = _fake_pack(tmp_path, "zz", {"3.10": _tier("zz", "3.10", floor="3.13")})
        loader = _loader_with(zz=zz)
        with pytest.raises(UnsupportedInterpreterError, match="3.13"):
            loader.load("zz", "python", "3.12")
        assert loader.load("zz", "python", "3.13").version == "3.10"

    def test_a_request_below_the_oldest_tier_names_its_floor(self, tmp_path):
        zz = _fake_pack(
            tmp_path,
            "zz",
            {
                "3.13": _tier("zz", "3.13"),
                "3.14": _tier("zz", "3.14", extends="3.13.yml"),
            },
        )
        loader = _loader_with(zz=zz)
        with pytest.raises(UnsupportedInterpreterError) as raised:
            loader.load("zz", "python", "3.12")
        assert "requires Python >= 3.13" in str(raised.value)

    def test_a_pack_that_declares_no_floor_is_floored_at_its_oldest_tier(
        self, tmp_path
    ):
        # The one case where only the explicit floor check stops a downward
        # serve: no tier declares python_version_min, so nothing else refuses.
        zz = _fake_pack(
            tmp_path,
            "zz",
            {
                "3.12": _tier("zz", "3.12", declare_floor=False),
                "3.13": _tier("zz", "3.13", extends="3.12.yml", declare_floor=False),
            },
        )
        loader = _loader_with(zz=zz)
        with pytest.raises(UnsupportedInterpreterError) as raised:
            loader.load("zz", "python", "3.11")
        message = str(raised.value)
        assert "requires Python >= 3.12" in message
        assert "its oldest tier is 3.12" in message
        assert "declares" not in message  # it declared nothing
        assert loader.load("zz", "python", "3.14").version == "3.13"

    def test_another_major_version_is_not_served_a_3x_tier(self, tmp_path):
        # "Tiers only grow" holds across 3.x minor releases; nothing says a
        # Python 4 parses a 3.x tier, so the rule stops at the major version.
        zz = _fake_pack(tmp_path, "zz", {"3.10": _tier("zz", "3.10")})
        loader = _loader_with(zz=zz)
        with pytest.raises(PackNotFoundError):
            loader.load("zz", "python", "4.0")

    def test_a_gap_inside_the_pack_is_not_filled(self, tmp_path):
        # Only a request past the newest tier is served something else. A
        # missing middle tier is a broken pack and still says so.
        zz = _fake_pack(
            tmp_path,
            "zz",
            {
                "3.10": _tier("zz", "3.10"),
                "3.12": _tier("zz", "3.12", extends="3.10.yml"),
            },
        )
        loader = _loader_with(zz=zz)
        with pytest.raises(PackNotFoundError):
            loader.load("zz", "python", "3.11")

    def test_a_language_with_no_pack_is_still_not_found(self, tmp_path):
        zz = _fake_pack(tmp_path, "zz", {"3.10": _tier("zz", "3.10")})
        loader = _loader_with(zz=zz)
        with pytest.raises(PackNotFoundError) as raised:
            loader.load("qq", "python", "3.99")
        assert "'qq'" in str(raised.value)

    def test_no_version_means_no_tier_rule(self, tmp_path):
        # ``None`` asks for default.yml, which this pack lacks; nothing to compare.
        zz = _fake_pack(tmp_path, "zz", {"3.10": _tier("zz", "3.10")})
        loader = _loader_with(zz=zz)
        with pytest.raises(PackNotFoundError):
            loader.load("zz", "python", None)
        with pytest.raises(PackNotFoundError):
            loader.load("zz", "python", "default")
