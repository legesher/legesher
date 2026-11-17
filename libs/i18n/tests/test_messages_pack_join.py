"""The message catalog joined with a language pack's ``messages`` (CORE-2630).

With no database, :func:`load_catalog` takes the English side from the seed
and the translations from the locale's pack. These tests hold the join rules
(a translation is used only for the English wording it was written for), the
order the sources are consulted in, and the placeholder kinds on the English
side.

The English side is the real tracked seed throughout: keys, templates and
fingerprints are read from it, never restated. Translations are vocalised
Arabic and Devanagari, whose combining marks do not survive a lossy step.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

import pytest
import yaml

import legesher_i18n
from legesher_i18n import messages
from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.messages import (
    load_catalog,
    match_message,
    pack_message_problems,
)
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.pack_messages import (
    ALLOWED_STATUSES,
    ENTRY_FIELDS,
    PLACEHOLDER_KINDS,
    entry_problem,
    message_fingerprint,
    used_placeholders,
)
from scripts.activate_messages_partition import activate
from scripts.seed_message_templates import seed_database, validate_seed
from tests.test_messages_seed_fallback import operational_db

SEED_PATH = (
    Path(legesher_i18n.__file__).parent / "db" / "seeds" / "cpython_messages.json"
)
SEED = json.loads(SEED_PATH.read_text(encoding="utf-8"))

#: Vocalised Arabic and Devanagari renderings of "name '{name}' is not defined".
ARABIC = "الاِسْمُ '{name}' غَيْرُ مُعَرَّفٍ"
DEVANAGARI = "नाम '{name}' परिभाषित नहीं है"
#: Renderings of the two UnboundLocalError wordings (3.10, then 3.11 on).
DEVANAGARI_OLD = "स्थानीय चर '{name}' का उपयोग मान देने से पहले किया गया"
DEVANAGARI_NEW = "स्थानीय चर '{name}' तक नहीं पहुँचा जा सकता, उसका कोई मान नहीं है"
ARABIC_HEADER = "التَّتَبُّعُ (آخِرُ اسْتِدْعَاءٍ فِي الأَسْفَلِ):"


def _version(text: str) -> tuple[int, int]:
    major, minor = text.split(".")[:2]
    return int(major), int(minor)


def english(key: str, version: str) -> dict:
    """The seed template for ``key`` that applies to ``version``.

    Derived here from the seed file, not through the module under test.
    """
    wanted = _version(version)
    candidates = [
        t
        for t in SEED["templates"]
        if t["key"] == key
        and _version(t.get("version_added", SEED["version_added"])) <= wanted
        and not (t.get("version_removed") and _version(t["version_removed"]) <= wanted)
    ]
    assert candidates, f"no seed row for {key} at {version}"
    return max(
        candidates,
        key=lambda t: _version(t.get("version_added", SEED["version_added"])),
    )


def src(key: str, version: str = "3.10") -> str:
    """The fingerprint of ``key``'s English template at ``version``, by hand."""
    template = unicodedata.normalize("NFC", english(key, version)["template_en"])
    return hashlib.sha256(template.encode("utf-8")).hexdigest()[:12]


def entry(text: str, key: str, version: str = "3.10", **extra: object) -> dict:
    return {"text": text, "src": src(key, version), **extra}


def rule(rules: list, key: str):
    (found,) = [r for r in rules if r.key == key]
    return found


@pytest.fixture
def no_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the default database at a path with nothing behind it."""
    path = tmp_path / "home" / ".legesher" / "translations.db"
    monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: path)
    return path


#: The versions a shipped pack has a file for.
PACK_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")


@pytest.fixture
def write_pack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Write a synthetic pack and make it the only pack the loader finds.

    The pack has a file for every version in :data:`PACK_VERSIONS`, each
    extending the one before it, as shipped packs do. ``files`` maps a
    version to what that file adds; a version it does not name adds nothing.
    """

    def _write(files: dict[str, dict[str, object]], language: str = "zz") -> Path:
        assert set(files) <= set(PACK_VERSIONS), files.keys()
        module = tmp_path / "packs" / language / f"legesher_i18n_python_{language}"
        packs = module / "packs"
        packs.mkdir(parents=True, exist_ok=True)
        previous: str | None = None
        for version in PACK_VERSIONS:
            data: dict[str, object] = {
                "language": language,
                "target": "python",
                "version": version,
            }
            if previous is not None:
                data["extends"] = f"{previous}.yml"
            else:
                data["keywords"] = {"def": "परिभाषा"}
            data.update(files.get(version, {}))
            (packs / f"{version}.yml").write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            previous = version
        monkeypatch.setattr(
            LanguagePackLoader,
            "_discover_packs",
            lambda self: {f"python-{language}": module},
        )
        return module

    return _write


@pytest.fixture(scope="module")
def seeded_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A database filled from the CPython seed by the real seeder."""
    locales = {tag for t in SEED["templates"] for tag in t.get("translations", {})}
    path = operational_db(
        tmp_path_factory.mktemp("seeded") / "translations.db", locales
    )
    activate(path)
    seed_database(path, SEED)
    return path


def cpython(**entries: dict) -> dict:
    """A ``messages`` section; ``NameError__not_defined`` is ``NameError.not_defined``."""
    return {
        "messages": {
            "cpython": {key.replace("__", "."): value for key, value in entries.items()}
        }
    }


# ---------------------------------------------------------------------------
# The fingerprint
# ---------------------------------------------------------------------------


class TestFingerprint:
    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("traceback.header", "5dd94ced5a2a"),
            ("traceback.frame", "fcb6c6422b34"),
            ("NameError.not_defined", "998720c0a4af"),
            ("StopIteration.no_value", "e3b0c44298fc"),
        ],
    )
    def test_known_values(self, key: str, expected: str) -> None:
        """Pins the algorithm: a change to it invalidates every shipped ``src``."""
        assert message_fingerprint(english(key, "3.10")["template_en"]) == expected

    def test_the_two_wordings_of_one_key_differ(self) -> None:
        key = "UnboundLocalError.before_assignment"
        old = message_fingerprint(english(key, "3.10")["template_en"])
        new = message_fingerprint(english(key, "3.11")["template_en"])
        assert old != new

    def test_it_is_twelve_lowercase_hex_digits(self) -> None:
        for template in SEED["templates"]:
            value = message_fingerprint(template["template_en"])
            assert re.fullmatch(r"[0-9a-f]{12}", value), template["key"]

    def test_a_decomposed_spelling_has_the_same_fingerprint(self) -> None:
        composed = "pointé '{name}' n'est pas défini"
        decomposed = unicodedata.normalize("NFD", composed)
        assert composed != decomposed
        assert message_fingerprint(composed) == message_fingerprint(decomposed)

    def test_the_seed_has_no_two_wordings_with_one_fingerprint(self) -> None:
        """Distinct English templates must not collide in twelve digits."""
        by_print: dict[str, set[str]] = {}
        for template in SEED["templates"]:
            by_print.setdefault(
                message_fingerprint(template["template_en"]), set()
            ).add(template["template_en"])
        assert [texts for texts in by_print.values() if len(texts) > 1] == []


# ---------------------------------------------------------------------------
# The join rules, one entry at a time
# ---------------------------------------------------------------------------


class TestEntryProblem:
    EN = "name '{name}' is not defined"

    def problem(self, candidate: object, template_en: str | None = None, names=None):
        template_en = self.EN if template_en is None else template_en
        return entry_problem(
            candidate,
            template_en=template_en,
            placeholders=used_placeholders(template_en) if names is None else names,
        )

    def good(self, text: str = DEVANAGARI, **extra: object) -> dict:
        return {"text": text, "src": message_fingerprint(self.EN), **extra}

    def test_a_usable_entry_has_no_problem(self) -> None:
        assert self.problem(self.good()) is None
        assert self.problem(self.good(ARABIC)) is None

    @pytest.mark.parametrize("status", ALLOWED_STATUSES)
    def test_every_review_rung_is_accepted(self, status: str) -> None:
        assert self.problem(self.good(status=status)) is None

    @pytest.mark.parametrize("status", ["not-a-status", "", None, 3, "Machine"])
    def test_an_unknown_status_is_named(self, status: object) -> None:
        problem = self.problem(self.good(status=status))
        assert problem is not None and "status" in problem and repr(status) in problem

    def test_a_field_this_release_does_not_know_is_named(self) -> None:
        problem = self.problem(self.good(plural={"few": ARABIC}))
        assert problem is not None and "plural" in problem

    def test_the_known_fields_are_the_documented_three(self) -> None:
        assert ENTRY_FIELDS == {"text", "src", "status"}

    def test_a_fingerprint_of_another_wording_is_named(self) -> None:
        stale = {"text": DEVANAGARI, "src": message_fingerprint("name is not defined")}
        problem = self.problem(stale)
        assert problem is not None
        assert stale["src"] in problem and message_fingerprint(self.EN) in problem

    @pytest.mark.parametrize(
        "text",
        [
            "नाम परिभाषित नहीं है",  # the placeholder is gone
            "नाम '{name}' '{module}' परिभाषित नहीं है",  # one too many
            "नाम '{nam}' परिभाषित नहीं है",  # misspelled
        ],
    )
    def test_placeholders_that_do_not_agree_are_named(self, text: str) -> None:
        problem = self.problem(self.good(text))
        assert problem is not None and "placeholders" in problem and "name" in problem

    def test_a_literal_brace_is_not_a_placeholder(self) -> None:
        """CPython's own message carries a stray ``}``; so may its translation."""
        template_en = english("SyntaxError.fstring_valid_expression", "3.12")[
            "template_en"
        ]
        assert "}" in template_en
        candidate = {
            "text": "f-string: '}' से पहले एक मान्य व्यंजक चाहिए",
            "src": message_fingerprint(template_en),
        }
        assert self.problem(candidate, template_en) is None

    def test_empty_text_is_usable_only_for_an_empty_template(self) -> None:
        empty = {"text": "", "src": message_fingerprint("")}
        assert self.problem(empty, "") is None
        # A template with no placeholders, so only the empty rule can object.
        template_en = "division by zero"
        problem = self.problem(
            {"text": "", "src": message_fingerprint(template_en)}, template_en
        )
        assert problem is not None and "empty" in problem

    @pytest.mark.parametrize("candidate", ["नाम", ["नाम"], None, 7])
    def test_an_entry_that_is_not_a_mapping_is_named(self, candidate: object) -> None:
        assert "not a mapping" in (self.problem(candidate) or "")

    def test_a_malformed_text_or_src_is_named(self) -> None:
        assert "'text'" in (self.problem({"text": 7, "src": "a" * 12}) or "")
        assert "'src'" in (self.problem({"text": DEVANAGARI, "src": "A" * 12}) or "")
        assert "'src'" in (self.problem({"text": DEVANAGARI}) or "")


# ---------------------------------------------------------------------------
# The join, through a pack on disk
# ---------------------------------------------------------------------------


class TestJoin:
    def test_a_matching_entry_localizes_its_rule(self, no_database, write_pack):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(DEVANAGARI, "NameError.not_defined")
                )
            }
        )
        rules = load_catalog("zz", "3.12")
        found = rule(rules, "NameError.not_defined")
        assert found.localized
        assert found.template.encode() == DEVANAGARI.encode()
        assert found.status == "machine"
        assert (
            found.template_en == english("NameError.not_defined", "3.12")["template_en"]
        )

    def test_the_rest_of_the_catalog_stays_english(self, no_database, write_pack):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(DEVANAGARI, "NameError.not_defined")
                )
            }
        )
        rules = load_catalog("zz", "3.12")
        others = [r for r in rules if r.key != "NameError.not_defined"]
        assert others and all(not r.localized for r in others)
        assert all(r.template == r.template_en and r.status is None for r in others)

    def test_the_catalog_keeps_every_rule_and_its_order(self, no_database, write_pack):
        """First-match-wins depends on rule order; a pack must not change it."""
        english_only = [r.key for r in load_catalog("xx", "3.12")]
        write_pack(
            {
                "3.10": cpython(
                    traceback__header=entry(ARABIC_HEADER, "traceback.header"),
                    NameError__not_defined=entry(ARABIC, "NameError.not_defined"),
                )
            }
        )
        assert [r.key for r in load_catalog("zz", "3.12")] == english_only

    @pytest.mark.parametrize("status", [s for s in ALLOWED_STATUSES if s != "machine"])
    def test_a_stated_status_is_carried(self, no_database, write_pack, status):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(
                        ARABIC, "NameError.not_defined", status=status
                    )
                )
            }
        )
        assert (
            rule(load_catalog("zz", "3.12"), "NameError.not_defined").status == status
        )

    @pytest.mark.parametrize(
        ("name", "text", "expected"),
        [
            ("عَدَّادٌ", ARABIC, "الاِسْمُ 'عَدَّادٌ' غَيْرُ مُعَرَّفٍ"),
            ("गिनती", DEVANAGARI, "नाम 'गिनती' परिभाषित नहीं है"),
            ("ශ්‍රී", DEVANAGARI, "नाम 'ශ්‍රී' परिभाषित नहीं है"),  # Sinhala with ZWJ
        ],
    )
    def test_slot_values_survive_byte_for_byte(
        self, no_database, write_pack, name, text, expected
    ):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(text, "NameError.not_defined")
                )
            }
        )
        rendered = match_message(
            load_catalog("zz", "3.12"),
            f"name '{name}' is not defined",
            key_prefix="NameError",
        )
        assert rendered is not None
        assert rendered.encode("utf-8") == expected.encode("utf-8")

    def test_a_stale_fingerprint_leaves_the_message_as_printed(
        self, no_database, write_pack
    ):
        stale = {"text": DEVANAGARI, "src": message_fingerprint("name is not defined")}
        write_pack({"3.10": cpython(NameError__not_defined=stale)})
        found = rule(load_catalog("zz", "3.12"), "NameError.not_defined")
        assert not found.localized
        assert found.template == found.template_en
        assert found.status is None

    def test_a_translation_of_the_old_wording_is_not_used_for_the_new(
        self, no_database, write_pack
    ):
        """The 3.11 rewording shares its key and its placeholders with 3.10's.

        A pack with only the 3.10 translation must not render the old
        sentence for the new message; nothing but the fingerprint tells the
        two apart.
        """
        key = "UnboundLocalError.before_assignment"
        assert used_placeholders(english(key, "3.10")["template_en"]) == (
            used_placeholders(english(key, "3.11")["template_en"])
        )
        write_pack(
            {
                "3.10": cpython(
                    UnboundLocalError__before_assignment=entry(
                        DEVANAGARI_OLD, key, "3.10"
                    )
                ),
                "3.11": {},
                "3.12": {},
            }
        )
        old = rule(load_catalog("zz", "3.10"), key)
        assert old.localized and old.template == DEVANAGARI_OLD
        for version in ("3.11", "3.12"):
            new = rule(load_catalog("zz", version), key)
            assert not new.localized, version
            assert new.template == english(key, version)["template_en"]

    def test_each_wording_gets_its_own_translation(self, no_database, write_pack):
        key = "UnboundLocalError.before_assignment"
        write_pack(
            {
                "3.10": cpython(
                    UnboundLocalError__before_assignment=entry(
                        DEVANAGARI_OLD, key, "3.10"
                    )
                ),
                "3.11": cpython(
                    UnboundLocalError__before_assignment=entry(
                        DEVANAGARI_NEW, key, "3.11"
                    )
                ),
                "3.12": {},
            }
        )
        assert rule(load_catalog("zz", "3.10"), key).template == DEVANAGARI_OLD
        for version in ("3.11", "3.12"):
            found = rule(load_catalog("zz", version), key)
            assert found.localized and found.template == DEVANAGARI_NEW, version

    def test_placeholders_that_do_not_agree_leave_the_message_as_printed(
        self, no_database, write_pack
    ):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(
                        "नाम परिभाषित नहीं है", "NameError.not_defined"
                    )
                )
            }
        )
        assert not rule(load_catalog("zz", "3.12"), "NameError.not_defined").localized

    def test_an_empty_translation_of_an_empty_message_is_used(
        self, no_database, write_pack
    ):
        key = "StopIteration.no_value"
        assert english(key, "3.10")["template_en"] == ""
        write_pack({"3.10": cpython(StopIteration__no_value=entry("", key))})
        found = rule(load_catalog("zz", "3.12"), key)
        assert found.localized and found.template == ""

    def test_an_empty_translation_of_a_real_message_is_not_used(
        self, no_database, write_pack
    ):
        key = "ZeroDivisionError.division_by_zero"
        assert used_placeholders(english(key, "3.10")["template_en"]) == set()
        write_pack(
            {"3.10": cpython(ZeroDivisionError__division_by_zero=entry("", key))}
        )
        assert not rule(load_catalog("zz", "3.12"), key).localized

    def test_a_key_the_catalog_does_not_know_is_ignored(self, no_database, write_pack):
        """A pack may be newer than the catalog it is read with."""
        write_pack(
            {
                "3.10": cpython(
                    NoSuchError__never_raised={"text": ARABIC, "src": "a" * 12},
                    NameError__not_defined=entry(ARABIC, "NameError.not_defined"),
                )
            }
        )
        rules = load_catalog("zz", "3.12")
        assert "NoSuchError.never_raised" not in {r.key for r in rules}
        assert rule(rules, "NameError.not_defined").localized

    def test_a_message_added_later_is_used_from_its_version_on(
        self, no_database, write_pack
    ):
        key = "NameError.forgot_import"
        assert english(key, "3.12")["version_added"] == "3.12"
        text = "नाम '{name}' परिभाषित नहीं है। क्या आप '{module}' आयात करना भूल गए?"
        write_pack(
            {
                "3.10": {},
                "3.11": {},
                "3.12": cpython(NameError__forgot_import=entry(text, key, "3.12")),
            }
        )
        assert key not in {r.key for r in load_catalog("zz", "3.11")}
        found = rule(load_catalog("zz", "3.12"), key)
        assert found.localized and found.template == text

    @pytest.mark.parametrize(
        "extra", [{"plural": {"few": ARABIC}}, {"status": "not-a-status"}]
    )
    def test_an_entry_this_release_cannot_read_is_not_used(
        self, no_database, write_pack, extra
    ):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined=entry(
                        DEVANAGARI, "NameError.not_defined", **extra
                    )
                )
            }
        )
        assert not rule(load_catalog("zz", "3.12"), "NameError.not_defined").localized

    def test_one_unusable_entry_does_not_cost_the_others(self, no_database, write_pack):
        write_pack(
            {
                "3.10": cpython(
                    traceback__header=entry(ARABIC_HEADER, "traceback.header"),
                    NameError__not_defined={"text": DEVANAGARI, "src": "0" * 12},
                )
            }
        )
        rules = load_catalog("zz", "3.12")
        assert rule(rules, "traceback.header").template == ARABIC_HEADER
        assert not rule(rules, "NameError.not_defined").localized

    def test_a_skipped_entry_is_logged_with_its_key_and_reason(
        self, no_database, write_pack, caplog
    ):
        write_pack(
            {
                "3.10": cpython(
                    NameError__not_defined={"text": DEVANAGARI, "src": "0" * 12}
                )
            }
        )
        with caplog.at_level(logging.DEBUG, logger="legesher_i18n.messages"):
            load_catalog("zz", "3.12")
        assert any(
            "NameError.not_defined" in record.getMessage()
            and "000000000000" in record.getMessage()
            for record in caplog.records
        )

    def test_the_packs_minimum_interpreter_is_not_enforced(
        self, no_database, write_pack
    ):
        """Rendering a message runs no translated identifier."""
        write_pack(
            {
                "3.10": {
                    "metadata": {"python_version_min": "3.13"},
                    **cpython(
                        NameError__not_defined=entry(ARABIC, "NameError.not_defined")
                    ),
                }
            }
        )
        with pytest.raises(Exception, match="3.13"):
            LanguagePackLoader().load("zz", "python", "3.10")
        assert rule(load_catalog("zz", "3.10"), "NameError.not_defined").localized


# ---------------------------------------------------------------------------
# Which source is read
# ---------------------------------------------------------------------------


class TestPrecedence:
    """The synthetic pack here is ``es``, a locale the seed also translates."""

    SEED_HEADER = "Rastreo (llamada más reciente al final):"

    def header_only(self) -> dict:
        return cpython(traceback__header=entry(ARABIC_HEADER, "traceback.header"))

    def test_the_seed_translates_the_header(self) -> None:
        (template,) = [t for t in SEED["templates"] if t["key"] == "traceback.header"]
        assert template["translations"]["es"]["template"] == self.SEED_HEADER

    def test_the_pack_supplies_translations_when_there_is_no_database(
        self, no_database, write_pack
    ):
        write_pack({"3.10": self.header_only()}, language="es")
        assert rule(load_catalog("es", "3.12"), "traceback.header").template == (
            ARABIC_HEADER
        )

    def test_a_pack_with_messages_is_the_only_source_of_translations(
        self, no_database, write_pack
    ):
        """A partial pack is partial: the seed does not fill its gaps."""
        write_pack({"3.10": self.header_only()}, language="es")
        found = rule(load_catalog("es", "3.12"), "NameError.not_defined")
        assert not found.localized
        assert found.template == found.template_en

    def test_an_explicit_database_is_read_alone(
        self, no_database, write_pack, seeded_db
    ):
        write_pack({"3.10": self.header_only()}, language="es")
        rules = load_catalog("es", "3.12", db_path=seeded_db)
        assert rule(rules, "traceback.header").template == self.SEED_HEADER

    def test_an_explicit_database_without_rows_is_an_empty_catalog(
        self, no_database, write_pack, tmp_path
    ):
        write_pack({"3.10": self.header_only()}, language="es")
        assert load_catalog("es", "3.12", db_path=tmp_path / "missing.db") == []

    def test_rows_in_the_default_database_win_over_the_pack(
        self, write_pack, seeded_db, monkeypatch
    ):
        monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: seeded_db)
        write_pack({"3.10": self.header_only()}, language="es")
        assert rule(load_catalog("es", "3.12"), "traceback.header").template == (
            self.SEED_HEADER
        )

    def test_a_pack_without_messages_reads_the_seeds_translations(
        self, no_database, write_pack
    ):
        write_pack({"3.10": {}}, language="es")
        assert rule(load_catalog("es", "3.12"), "traceback.header").template == (
            self.SEED_HEADER
        )

    def test_messages_for_another_implementation_do_not_count(
        self, no_database, write_pack
    ):
        write_pack(
            {
                "3.10": {
                    "messages": {
                        "pypy": {
                            "traceback.header": entry(ARABIC_HEADER, "traceback.header")
                        }
                    }
                }
            },
            language="es",
        )
        assert rule(load_catalog("es", "3.12"), "traceback.header").template == (
            self.SEED_HEADER
        )

    def test_a_pack_that_does_not_load_reads_the_seeds_translations(
        self, no_database, write_pack
    ):
        module = write_pack({"3.10": self.header_only()}, language="es")
        (module / "packs" / "3.10.yml").write_text(
            "language: es\ntarget: python\nversion: '3.10'\nnot_a_section: {}\n",
            encoding="utf-8",
        )
        with pytest.raises(Exception, match="not_a_section"):
            LanguagePackLoader().load("es", "python", "3.10")
        assert rule(load_catalog("es", "3.10"), "traceback.header").template == (
            self.SEED_HEADER
        )

    def test_no_pack_file_for_the_interpreter_reads_the_seeds_translations(
        self, no_database, write_pack
    ):
        write_pack({"3.10": self.header_only()}, language="es")
        assert rule(load_catalog("es", "3.99"), "traceback.header").template == (
            self.SEED_HEADER
        )

    def test_a_locale_with_no_pack_and_no_seed_translation_is_english(
        self, no_database, write_pack
    ):
        write_pack({"3.10": self.header_only()}, language="es")
        rules = load_catalog("xx", "3.12")
        assert rules and all(not r.localized for r in rules)

    def test_an_implementation_without_a_pack_target_never_loads_a_pack(
        self, no_database, monkeypatch
    ):
        def refuse(self, *args, **kwargs):
            raise AssertionError("a pack was loaded")

        monkeypatch.setattr(LanguagePackLoader, "load", refuse)
        assert "v8" not in messages._IMPLEMENTATION_TARGETS
        load_catalog("ar", implementation="v8")
        assert pack_message_problems("ar", implementation="v8") == []

    def test_reading_a_pack_creates_no_database(self, no_database, write_pack):
        write_pack({"3.10": self.header_only()}, language="es")
        load_catalog("es", "3.12")
        assert not no_database.exists()
        assert not no_database.parent.exists()


# ---------------------------------------------------------------------------
# Version tiers and rule order on the English side
# ---------------------------------------------------------------------------


class TestTiers:
    def test_rules_keep_the_seed_order(self, no_database) -> None:
        """First-match-wins means the seed's order is part of the contract."""
        for version in ("3.10", "3.11", "3.12"):
            wanted = _version(version)
            expected: list[str] = []
            for template in SEED["templates"]:
                added = _version(template.get("version_added", SEED["version_added"]))
                removed = template.get("version_removed")
                applies = added <= wanted and not (
                    removed and _version(removed) <= wanted
                )
                if applies and template["key"] not in expected:
                    expected.append(template["key"])
            assert len(expected) > 40, version
            assert [r.key for r in load_catalog("xx", version)] == expected, version

    def test_a_message_removed_without_a_replacement_disappears(
        self, no_database, write_pack, tmp_path, monkeypatch
    ):
        seed = {
            "implementation": "cpython",
            "version_added": "3.10",
            "templates": [
                {
                    "key": "ZeroDivisionError.division_by_zero",
                    "template_en": "division by zero",
                    "placeholders": [],
                    "matcher": "^division by zero$",
                },
                {
                    "key": "SyntaxError.retired",
                    "template_en": "a message Python stopped printing",
                    "placeholders": [],
                    "matcher": "^a message Python stopped printing$",
                    "version_removed": "3.11",
                },
            ],
        }
        seeds = tmp_path / "seeds"
        seeds.mkdir()
        (seeds / "one.json").write_text(json.dumps(seed), encoding="utf-8")
        monkeypatch.setattr(messages, "SEED_DIR", seeds)
        retired = {
            "text": "एक संदेश जो अब नहीं छपता",
            "src": message_fingerprint("a message Python stopped printing"),
        }
        write_pack({"3.10": cpython(SyntaxError__retired=retired)})
        assert rule(load_catalog("zz", "3.10"), "SyntaxError.retired").localized
        for version in ("3.11", "3.12"):
            keys = [r.key for r in load_catalog("zz", version)]
            assert keys == ["ZeroDivisionError.division_by_zero"], version
            (problem,) = pack_message_problems("zz", version)
            assert problem.startswith("SyntaxError.retired: no English message")


# ---------------------------------------------------------------------------
# Placeholder kinds on the English side
# ---------------------------------------------------------------------------

#: Number-shaped placeholders that are deliberately copied verbatim: neither
#: is a line number or a count. An errno is an identifier that happens to be
#: numeric, and the base of an integer literal names a notation.
VERBATIM_NUMBERS = {
    ("FileNotFoundError.enoent", "errno"),
    ("ValueError.int_literal", "base"),
}


def _number_groups(matcher: str) -> set[str]:
    """Named groups of ``matcher`` that accept digits and nothing else."""
    return set(re.findall(r"\(\?P<(\w+)>\\d\+\)", matcher))


class TestPlaceholderKinds:
    def test_the_seed_marks_kinds(self) -> None:
        kinds = {
            p["kind"]
            for t in SEED["templates"]
            for p in t.get("placeholders", [])
            if "kind" in p
        }
        assert kinds == set(PLACEHOLDER_KINDS)

    @pytest.mark.parametrize(
        "template",
        SEED["templates"],
        ids=lambda t: f"{t['key']}@{t.get('version_added')}",
    )
    def test_every_number_placeholder_is_marked_or_listed(self, template: dict) -> None:
        """A new numeric slot must be given a kind, or be listed as verbatim."""
        numeric = _number_groups(template["matcher"])
        for placeholder in template.get("placeholders", []):
            name = placeholder["name"]
            listed = (template["key"], name) in VERBATIM_NUMBERS
            if name in numeric:
                assert ("kind" in placeholder) != listed, (template["key"], name)
            else:
                assert "kind" not in placeholder and not listed, (template["key"], name)

    def test_the_verbatim_list_names_real_placeholders(self) -> None:
        declared = {
            (t["key"], p["name"])
            for t in SEED["templates"]
            for p in t.get("placeholders", [])
        }
        assert VERBATIM_NUMBERS <= declared

    def test_a_frame_line_number_is_a_line(self, no_database) -> None:
        frame = rule(load_catalog("xx", "3.12"), "traceback.frame")
        assert frame.kind_of("line") == "line"
        assert frame.kind_of("file") is None
        assert frame.kind_of("name") is None
        assert frame.kind_of("no_such_placeholder") is None

    def test_argument_counts_are_counts(self, no_database) -> None:
        arg_count = rule(load_catalog("xx", "3.12"), "TypeError.arg_count")
        assert dict(arg_count.slot_kinds) == {"expected": "count", "given": "count"}
        assert arg_count.kind_of("func") is None

    def test_kinds_do_not_depend_on_the_locale_or_the_source(
        self, no_database, write_pack, seeded_db
    ):
        english_only = {r.key: r.slot_kinds for r in load_catalog("xx", "3.12")}
        assert any(english_only.values())
        from_seed = {r.key: r.slot_kinds for r in load_catalog("es", "3.12")}
        from_db = {
            r.key: r.slot_kinds for r in load_catalog("es", "3.12", db_path=seeded_db)
        }
        write_pack(
            {
                "3.10": cpython(
                    traceback__frame=entry(
                        'الْمِلَفُّ "{file}"، السَّطْرُ {line}، فِي {name}', "traceback.frame"
                    )
                )
            }
        )
        from_pack = {r.key: r.slot_kinds for r in load_catalog("zz", "3.12")}
        assert from_seed == from_db == from_pack == english_only

    def test_a_database_seeded_before_kinds_reads_as_verbatim(
        self, tmp_path: Path
    ) -> None:
        legacy = json.loads(json.dumps(SEED))
        for template in legacy["templates"]:
            for placeholder in template.get("placeholders", []):
                placeholder.pop("kind", None)
        path = operational_db(tmp_path / "legacy" / "translations.db", {"es", "ar"})
        activate(path)
        seed_database(path, legacy)
        rules = load_catalog("es", "3.12", db_path=path)
        assert rules and all(r.slot_kinds == () for r in rules)

    def test_a_kind_this_release_does_not_know_reads_as_verbatim(
        self, seeded_db: Path, tmp_path: Path
    ) -> None:
        path = tmp_path / "translations.db"
        path.write_bytes(seeded_db.read_bytes())
        connection = sqlite3.connect(path)
        connection.execute(
            "UPDATE message_templates SET placeholders = ? WHERE key = ?",
            (
                json.dumps(
                    [
                        {"name": "file", "example": "a.py"},
                        {"name": "line", "example": "7", "kind": "ordinal"},
                        {"name": "name", "example": "f"},
                    ]
                ),
                "traceback.frame",
            ),
        )
        connection.execute(
            "UPDATE message_templates SET placeholders = 'not json' WHERE key = ?",
            ("traceback.frame_no_scope",),
        )
        connection.commit()
        connection.close()
        rules = load_catalog("es", "3.12", db_path=path)
        assert rule(rules, "traceback.frame").slot_kinds == ()
        assert rule(rules, "traceback.frame_no_scope").slot_kinds == ()

    def test_the_seeder_refuses_an_unknown_kind(self) -> None:
        seed = json.loads(json.dumps(SEED))
        (frame,) = [t for t in seed["templates"] if t["key"] == "traceback.frame"]
        frame["placeholders"][1]["kind"] = "ordinal"
        problems = validate_seed(seed)
        assert len(problems) == 1
        assert "traceback.frame" in problems[0] and "'ordinal'" in problems[0]

    def test_the_seeder_refuses_a_kind_on_a_value_that_is_not_a_number(self) -> None:
        seed = json.loads(json.dumps(SEED))
        (frame,) = [t for t in seed["templates"] if t["key"] == "traceback.frame"]
        assert frame["placeholders"][0]["name"] == "file"
        frame["placeholders"][0]["kind"] = "count"
        problems = validate_seed(seed)
        assert len(problems) == 1
        assert "traceback.frame" in problems[0] and "'file'" in problems[0]


# ---------------------------------------------------------------------------
# Checking a pack before it ships
# ---------------------------------------------------------------------------


class TestPackMessageProblems:
    def test_a_pack_whose_entries_all_join_has_no_problems(
        self, no_database, write_pack
    ):
        write_pack(
            {
                "3.10": cpython(
                    traceback__header=entry(ARABIC_HEADER, "traceback.header"),
                    NameError__not_defined=entry(DEVANAGARI, "NameError.not_defined"),
                )
            }
        )
        assert pack_message_problems("zz", "3.12") == []

    def test_every_unusable_entry_is_reported_with_its_key(
        self, no_database, write_pack
    ):
        write_pack(
            {
                "3.10": cpython(
                    traceback__header=entry(ARABIC_HEADER, "traceback.header"),
                    NameError__not_defined={"text": DEVANAGARI, "src": "0" * 12},
                    KeyError__key=entry("कुंजी", "KeyError.key"),
                    NoSuchError__never_raised={"text": ARABIC, "src": "a" * 12},
                )
            }
        )
        problems = pack_message_problems("zz", "3.12")
        assert [line.split(":")[0] for line in problems] == [
            "KeyError.key",
            "NameError.not_defined",
            "NoSuchError.never_raised",
        ]
        assert "placeholders" in problems[0]
        assert "000000000000" in problems[1]
        assert "no English message" in problems[2]

    def test_an_entry_visible_before_its_message_exists_is_reported(
        self, no_database, write_pack
    ):
        """A 3.12 message written into 3.10.yml is visible where it cannot join."""
        key = "NameError.forgot_import"
        text = "नाम '{name}' परिभाषित नहीं है। क्या आप '{module}' आयात करना भूल गए?"
        write_pack(
            {
                "3.10": cpython(NameError__forgot_import=entry(text, key, "3.12")),
                "3.11": {},
                "3.12": {},
            }
        )
        assert pack_message_problems("zz", "3.12") == []
        for version in ("3.10", "3.11"):
            (problem,) = pack_message_problems("zz", version)
            assert problem.startswith(key), version

    def test_the_english_side_is_the_seed_even_with_a_database(
        self, write_pack, seeded_db, monkeypatch
    ):
        monkeypatch.setattr("legesher_i18n.messages.default_db_path", lambda: seeded_db)
        write_pack(
            {"3.10": cpython(NameError__not_defined={"text": ARABIC, "src": "0" * 12})}
        )
        assert len(pack_message_problems("zz", "3.12")) == 1

    def test_no_pack_and_no_messages_are_both_clean(self, no_database, write_pack):
        write_pack({"3.10": {}})
        assert pack_message_problems("zz", "3.12") == []
        assert pack_message_problems("qq", "3.12") == []
        assert pack_message_problems("zz", "3.99") == []

    def test_a_pack_that_does_not_load_is_an_error_not_a_clean_report(
        self, no_database, write_pack
    ):
        module = write_pack({"3.10": {}})
        (module / "packs" / "3.10.yml").write_text(
            "language: zz\ntarget: python\nversion: '3.10'\nnot_a_section: {}\n",
            encoding="utf-8",
        )
        with pytest.raises(Exception, match="not_a_section"):
            pack_message_problems("zz", "3.10")


@pytest.mark.parametrize("language", get_active_language_codes())
def test_every_shipped_pack_entry_joins_at_every_version(language: str) -> None:
    """No shipped message is skipped by the join, at any version it is visible on.

    At run time an entry that fails a join rule is skipped without an error,
    so a stale fingerprint or a dropped placeholder in a shipped pack would
    only ever show as a message that quietly stayed in English. This is
    where it fails instead.
    """
    loader = LanguagePackLoader()
    versions = loader.list_available_versions()
    assert versions, "no pack versions discovered"
    for version in versions:
        problems = pack_message_problems(language, version, loader=loader)
        assert problems == [], (language, version)
