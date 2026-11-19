"""The message catalog picks its pack tier by the loader's rule, and no other.

``load_catalog`` used to choose the pack file for messages itself: the newest
file at or below the interpreter's version. The loader has the rule every other
surface uses (``test_newest_tier_fallback.py``), and the two differed: the
catalog filled a tier missing from the middle of a pack and read the newest
tier on the next major version, where the loader serves neither. Now the
catalog asks the loader for the interpreter's version, so the pack localizes
messages exactly where it localizes words:

* newer than every tier the pack has, within the major version: the newest tier;
* a tier missing from the middle: not filled;
* the next major version, or below the pack's oldest tier: nothing.

Versions are derived from the tiers the test pack is given, never written as
the answer. The test locale has no translations in the seed, so a message the
pack does not supply is not localized at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from legesher_i18n.exceptions import LanguagePackError
from legesher_i18n.messages import load_catalog, pack_message_problems
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.pack_messages import message_fingerprint
from tests.test_pack_messages import _shipped_tiers

LOCALE = "zz"
KEY = "traceback.header"

#: Devanagari and vocalised Arabic renderings of the traceback header.
OLDEST_TEXT = "ट्रेसबैक (सबसे हाल की कॉल सबसे नीचे):"
NEWEST_TEXT = "التَّتَبُّعُ (آخِرُ اسْتِدْعَاءٍ فِي الأَسْفَلِ):"

SHIPPED = LanguagePackLoader().list_available_versions("python")


def _xy(version: str) -> tuple[int, int]:
    major, minor = version.split(".")[:2]
    return int(major), int(minor)


def _shift(version: str, minors: int) -> str:
    major, minor = _xy(version)
    return f"{major}.{minor + minors}"


def _next_major(version: str) -> str:
    return f"{_xy(version)[0] + 1}.0"


#: The test pack starts one tier later than the shipped packs, so "below its
#: oldest tier" is still a version the catalog has English rows for, and it
#: lacks one tier in the middle.
BELOW = SHIPPED[0]
MISSING = SHIPPED[len(SHIPPED) // 2]
TIERS = [version for version in SHIPPED[1:] if version != MISSING]
OLDEST, NEWEST = TIERS[0], TIERS[-1]


@pytest.fixture
def no_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the default database at a path with nothing behind it."""
    path = tmp_path / "home" / ".legesher" / "translations.db"
    monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: path)


def _english(version: str) -> str:
    """The header's English template at ``version``, from the catalog's seed."""
    (found,) = [r for r in load_catalog("qq", version) if r.key == KEY]
    return found.template_en


def _entry(text: str, version: str, **extra: object) -> dict[str, object]:
    return {"text": text, "src": message_fingerprint(_english(version)), **extra}


@pytest.fixture
def gapped_pack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_database):
    """A pack with a file for each of ``TIERS``: none for ``BELOW`` or ``MISSING``.

    The oldest file carries the header in Devanagari and the newest overrides
    it in Arabic, so the text says which file a message came from. Returns a
    function that rewrites the newest file's entry, for the cases that need a
    faulty one.
    """
    module = tmp_path / "packs" / LOCALE / f"legesher_i18n_python_{LOCALE}"
    packs = module / "packs"
    packs.mkdir(parents=True)

    def write(version: str, previous: str | None, entry: dict | None) -> None:
        data: dict[str, object] = {
            "language": LOCALE,
            "target": "python",
            "version": version,
        }
        if previous is None:
            data["keywords"] = {"def": "परिभाषा"}
        else:
            data["extends"] = f"{previous}.yml"
        if entry is not None:
            data["messages"] = {"cpython": {KEY: entry}}
        (packs / f"{version}.yml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    previous: str | None = None
    for version in TIERS:
        entry = None
        if version == OLDEST:
            entry = _entry(OLDEST_TEXT, OLDEST)
        elif version == NEWEST:
            entry = _entry(NEWEST_TEXT, NEWEST)
        write(version, previous, entry)
        previous = version
    monkeypatch.setattr(
        LanguagePackLoader,
        "_discover_packs",
        lambda self: {f"python-{LOCALE}": module},
    )
    return lambda entry: write(NEWEST, TIERS[-2], entry)


def _header(version: str):
    (found,) = [r for r in load_catalog(LOCALE, version) if r.key == KEY]
    return found


def _loader_serves(version: str) -> bool:
    try:
        LanguagePackLoader().load(
            LOCALE, "python", version, enforce_min_interpreter=False
        )
    except LanguagePackError:
        return False
    return True


#: Below the oldest tier, every tier, the missing one, past the newest, the
#: next major version.
SWEEP = [
    *SHIPPED,
    _shift(NEWEST, 1),
    _shift(NEWEST, 2),
    _next_major(NEWEST),
]


class TestTheCatalogFollowsTheLoadersRule:
    def test_the_test_pack_has_a_tier_missing_from_the_middle(self, gapped_pack):
        assert _xy(BELOW) < _xy(OLDEST) < _xy(MISSING) < _xy(NEWEST)
        assert _shift(MISSING, -1) in TIERS
        assert _loader_serves(OLDEST) and _loader_serves(NEWEST)
        assert not _loader_serves(MISSING) and not _loader_serves(BELOW)

    @pytest.mark.parametrize("version", SWEEP)
    def test_messages_are_localized_exactly_where_the_loader_serves_a_tier(
        self, gapped_pack, version
    ):
        assert _header(version).localized is _loader_serves(version)

    def test_a_python_newer_than_the_pack_reads_its_newest_tier(self, gapped_pack):
        for version in (_shift(NEWEST, 1), _shift(NEWEST, 2)):
            assert _header(version).template == NEWEST_TEXT, version

    def test_a_tier_missing_from_the_middle_is_not_filled(self, gapped_pack):
        # The file just below the missing one has the message.
        assert _header(_shift(MISSING, -1)).template == OLDEST_TEXT
        missing = _header(MISSING)
        assert not missing.localized
        assert missing.template == missing.template_en

    def test_the_next_major_version_is_not_served(self, gapped_pack):
        beyond = _header(_next_major(NEWEST))
        assert not beyond.localized
        assert beyond.template == beyond.template_en

    def test_below_the_oldest_tier_nothing_is_localized(self, gapped_pack):
        assert not _header(BELOW).localized


class TestPackMessageProblemsOnANewerPython:
    """A version past the newest tier is checked as that tier, never waved through."""

    def test_the_newest_tiers_entries_are_checked(self, gapped_pack):
        assert pack_message_problems(LOCALE, _shift(NEWEST, 1)) == []
        gapped_pack({"text": NEWEST_TEXT, "src": "0" * 12})
        (problem,) = pack_message_problems(LOCALE, _shift(NEWEST, 1))
        assert problem.startswith(f"{KEY}:"), problem

    def test_where_the_loader_serves_nothing_the_report_is_empty(self, gapped_pack):
        gapped_pack({"text": NEWEST_TEXT, "src": "0" * 12})
        assert pack_message_problems(LOCALE, MISSING) == []
        assert pack_message_problems(LOCALE, _next_major(NEWEST)) == []


def _shipped_newest_tiers() -> list[object]:
    """Every shipped pack at one minor past the newest tier.

    The marks are the ones its newest tier carries: where that tier needs
    Unicode 15.1 identifiers, an older interpreter cannot load it, at its own
    version or as the tier served to a newer one.
    """
    newest, newer = SHIPPED[-1], _shift(SHIPPED[-1], 1)
    return [
        pytest.param(
            param.values[0],
            newer,
            marks=param.marks,
            id=f"{param.values[0]}-{newer}",
        )
        for param in _shipped_tiers()
        if param.values[1] == newest
    ]


@pytest.mark.parametrize(("language", "version"), _shipped_newest_tiers())
def test_every_shipped_pack_entry_joins_on_a_python_newer_than_the_packs(
    language: str, version: str
) -> None:
    """What a Python newer than the packs would skip is reported here, by name."""
    assert pack_message_problems(language, version) == []
