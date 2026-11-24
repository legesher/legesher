"""The ``messages`` section of a language pack: shape and loading (CORE-2630).

Covers what a pack load does with the section: the structural rules, the
schema field, the per-key merge along the inheritance chain, and the rule
that an entry the catalog will not use still leaves the pack loadable.
Whether an entry is USED is the catalog's decision, tested with the catalog.

Slot-carrying text is vocalised Arabic and Devanagari throughout. A Latin
template survives any byte-mangling step; combining marks do not.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from legesher_i18n import pack_messages
from legesher_i18n.data_contract import ALLOWED_TOP_LEVEL_KEYS
from legesher_i18n.exceptions import PackValidationError
from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.pack_messages import messages_structure_errors
from legesher_i18n.schema_validator import (
    TRANSLATION_SECTIONS,
    VOCABULARY_SECTIONS,
    LanguagePackSchema,
    interpreter_needed_for_identifier,
)
from legesher_i18n.script_policy import BIDI_CONTROLS
from tests.interpreter_gaps import needs_identifier_rules_of

LIB_ROOT = Path(__file__).parent.parent

#: Vocalised Arabic: every word carries harakat (combining marks).
ARABIC = "الاِسْمُ '{name}' غَيْرُ مُعَرَّفٍ"
#: Devanagari: vowel signs, a virama conjunct and a nukta-free anusvara.
DEVANAGARI = "नाम '{name}' परिभाषित नहीं है"
#: A reworded Devanagari template, for override tests.
DEVANAGARI_REWORDED = "स्थानीय चर '{name}' का कोई मान नहीं है"

SRC_A = "998720c0a4af"
SRC_B = "2ba5fbdd7304"
SRC_C = "6716c6784981"


def entry(text: str, src: str = SRC_A, **extra: object) -> dict[str, object]:
    return {"text": text, "src": src, **extra}


def section(**entries: dict[str, object]) -> dict[str, dict[str, dict[str, object]]]:
    """A ``messages`` section with the given entries under ``cpython``.

    Keys are passed with ``__`` for the dot: ``NameError__not_defined``.
    """
    return {
        "cpython": {key.replace("__", "."): value for key, value in entries.items()}
    }


def make_schema(**overrides: object) -> LanguagePackSchema:
    data: dict[str, object] = {
        "language": "zz",
        "target": "python",
        "version": "3.10",
        "keywords": {"def": "परिभाषा"},
    }
    data.update(overrides)
    return LanguagePackSchema(**data)


# ---------------------------------------------------------------------------
# Structural rules
# ---------------------------------------------------------------------------


class TestStructureRules:
    def test_a_well_formed_section_has_no_errors(self) -> None:
        messages = section(
            NameError__not_defined=entry(ARABIC),
            traceback__frame=entry(DEVANAGARI, SRC_B),
        )
        assert messages_structure_errors(messages) == []

    def test_an_empty_section_has_no_errors(self) -> None:
        assert messages_structure_errors({}) == []
        assert messages_structure_errors({"cpython": {}}) == []

    def test_empty_text_is_well_formed(self) -> None:
        """Three CPython messages are the empty string; so is their translation."""
        messages = section(StopIteration__no_value=entry("", "e3b0c44298fc"))
        assert messages_structure_errors(messages) == []

    @pytest.mark.parametrize("control", sorted(BIDI_CONTROLS))
    def test_every_bidi_control_in_text_is_named(self, control: str) -> None:
        text = ARABIC.replace("{name}", control + "{name}")
        errors = messages_structure_errors(section(NameError__not_defined=entry(text)))
        assert len(errors) == 1
        assert "messages.cpython.NameError.not_defined" in errors[0]
        assert f"U+{ord(control):04X}" in errors[0]

    def test_the_bidi_set_is_the_twelve_the_package_forbids(self) -> None:
        assert pack_messages.FORBIDDEN_BIDI == {ord(ch) for ch in BIDI_CONTROLS}
        assert len(pack_messages.FORBIDDEN_BIDI) == 12

    def test_the_seeder_applies_the_same_bidi_rule(self) -> None:
        """One definition: the script re-exports the package's function."""
        sys.path.insert(0, str(LIB_ROOT / "scripts"))
        try:
            import seed_message_templates
        finally:
            sys.path.remove(str(LIB_ROOT / "scripts"))
        assert seed_message_templates.bidi_controls is pack_messages.bidi_controls
        assert seed_message_templates.FORBIDDEN_BIDI is pack_messages.FORBIDDEN_BIDI

    @pytest.mark.parametrize(
        "src",
        [
            "998720c0a4a",  # eleven digits
            "998720c0a4af0",  # thirteen
            "998720C0A4AF",  # uppercase
            "998720c0a4ag",  # not hex
            "998720c0a4af\n",  # a trailing newline is not part of twelve digits
            "",
            123456789012,  # what YAML makes of an unquoted all-digit value
            None,
        ],
    )
    def test_a_malformed_src_is_named(self, src: object) -> None:
        errors = messages_structure_errors(
            section(NameError__not_defined={"text": DEVANAGARI, "src": src})
        )
        assert len(errors) == 1
        assert "messages.cpython.NameError.not_defined" in errors[0]
        assert "'src'" in errors[0]

    def test_a_missing_src_is_named(self) -> None:
        errors = messages_structure_errors(
            section(NameError__not_defined={"text": DEVANAGARI})
        )
        assert len(errors) == 1
        assert "'src'" in errors[0]

    @pytest.mark.parametrize("text", [None, 7, ["नाम"], {"ar": ARABIC}])
    def test_a_text_that_is_not_a_string_is_named(self, text: object) -> None:
        errors = messages_structure_errors(
            section(NameError__not_defined={"text": text, "src": SRC_A})
        )
        assert len(errors) == 1
        assert "'text'" in errors[0]

    @pytest.mark.parametrize(
        "key",
        [
            "NameError",  # no dot: the renderer routes on the part before it
            "1NameError.not_defined",
            "NameError.",
            ".not_defined",
            "NameError.not defined",
            "NameError.not_defined\n",
            "नाम.परिभाषित",  # keys are the catalog's, never localized
            "",
            3,
        ],
    )
    def test_a_key_that_is_not_a_catalog_key_is_named(self, key: object) -> None:
        errors = messages_structure_errors({"cpython": {key: entry(DEVANAGARI)}})
        assert len(errors) == 1
        assert "messages.cpython" in errors[0]
        assert repr(key) in errors[0]

    @pytest.mark.parametrize(
        "implementation", ["CPython", "c-python", "c python", "", 3]
    )
    def test_a_malformed_implementation_name_is_named(
        self, implementation: object
    ) -> None:
        errors = messages_structure_errors(
            {implementation: {"NameError.not_defined": entry(DEVANAGARI)}}
        )
        assert len(errors) == 1
        assert repr(implementation) in errors[0]

    @pytest.mark.parametrize("value", ["text", ["a"], 3])
    def test_a_section_that_is_not_a_mapping_is_named(self, value: object) -> None:
        errors = messages_structure_errors(value)
        assert len(errors) == 1
        assert "messages: must be a mapping" in errors[0]

    def test_entries_that_are_not_a_mapping_are_named(self) -> None:
        errors = messages_structure_errors({"cpython": [entry(DEVANAGARI)]})
        assert errors == [
            "messages.cpython: must be a mapping of message key to entry, got list"
        ]

    def test_a_plain_string_entry_is_named(self) -> None:
        """The plain ``key: text`` shape was considered and is not the format."""
        errors = messages_structure_errors(
            {"cpython": {"NameError.not_defined": DEVANAGARI}}
        )
        assert len(errors) == 1
        assert "messages.cpython.NameError.not_defined" in errors[0]
        assert "'text' and 'src'" in errors[0]

    def test_every_problem_is_reported_not_only_the_first(self) -> None:
        messages = {
            "cpython": {
                "NameError.not_defined": {"text": 7, "src": "nope"},
                "bad key": entry(DEVANAGARI),
            },
            "PyPy": {},
        }
        errors = messages_structure_errors(messages)
        assert len(errors) == 4

    def test_problems_after_the_first_bad_name_are_still_reported(self) -> None:
        """The bad items come first here, so stopping at one would show."""
        messages = {
            "Bad_One": {"NameError.not_defined": entry(DEVANAGARI)},
            "Bad-Two": {"NameError.not_defined": entry(DEVANAGARI)},
            "cpython": {
                "bad key": entry(ARABIC),
                "also bad": entry(ARABIC),
                "NameError.not_defined": {"text": 7, "src": SRC_A},
            },
        }
        errors = messages_structure_errors(messages)
        assert len(errors) == 5
        assert sum("'Bad_One'" in e or "'Bad-Two'" in e for e in errors) == 2
        assert sum("'bad key'" in e or "'also bad'" in e for e in errors) == 2

    def test_a_missing_text_is_named_with_its_path(self) -> None:
        errors = messages_structure_errors(
            section(NameError__not_defined={"src": SRC_A})
        )
        assert errors == [
            "messages.cpython.NameError.not_defined: 'text' must be a string, "
            "got NoneType"
        ]

    @pytest.mark.parametrize("implementation", ["c_python", "py3_13"])
    def test_an_underscore_in_an_implementation_name_is_named(
        self, implementation: str
    ) -> None:
        errors = messages_structure_errors(
            {implementation: {"NameError.not_defined": entry(DEVANAGARI)}}
        )
        assert len(errors) == 1 and repr(implementation) in errors[0]

    @pytest.mark.parametrize("key", ["NameError.not-defined", "Name-Error.not_defined"])
    def test_a_hyphen_in_a_key_is_named(self, key: str) -> None:
        errors = messages_structure_errors({"cpython": {key: entry(DEVANAGARI)}})
        assert len(errors) == 1 and repr(key) in errors[0]

    @pytest.mark.parametrize("control", sorted(BIDI_CONTROLS))
    def test_a_bidi_control_at_either_end_of_text_is_named(self, control: str) -> None:
        for text in (control + ARABIC, ARABIC + control, f" {control} "):
            errors = messages_structure_errors(
                section(NameError__not_defined=entry(text))
            )
            assert len(errors) == 1, (text, errors)
            assert f"U+{ord(control):04X}" in errors[0]

    def test_an_error_never_echoes_a_huge_value(self) -> None:
        """Aliases can build an enormous value from a small file."""
        huge = ["नाम" * 1000] * 1000
        errors = messages_structure_errors(
            {
                "X" * 10_000: {},
                "cpython": {
                    "y" * 10_000: entry(DEVANAGARI),
                    "NameError.not_defined": {"text": huge, "src": huge},
                },
            }
        )
        assert len(errors) == 4
        assert all(len(error) < 400 for error in errors), [len(e) for e in errors]
        assert any("got list" in error for error in errors)

    def test_fields_beyond_text_and_src_are_not_examined(self) -> None:
        """The catalog decides what an entry means; the load checks shape."""
        messages = section(
            NameError__not_defined=entry(
                ARABIC, status="not-a-status", plural={"few": ARABIC}, note=3
            )
        )
        assert messages_structure_errors(messages) == []


# ---------------------------------------------------------------------------
# Schema field
# ---------------------------------------------------------------------------


class TestSchemaField:
    def test_defaults_empty(self) -> None:
        assert make_schema().messages == {}

    def test_a_null_section_is_empty(self) -> None:
        assert make_schema(messages=None).messages == {}

    def test_text_survives_validation_byte_for_byte(self) -> None:
        schema = make_schema(
            messages=section(
                NameError__not_defined=entry(ARABIC),
                traceback__frame=entry(DEVANAGARI, SRC_B),
            )
        )
        entries = schema.messages["cpython"]
        assert entries["NameError.not_defined"]["text"].encode() == ARABIC.encode()
        assert entries["traceback.frame"]["text"].encode() == DEVANAGARI.encode()
        assert entries["traceback.frame"]["src"] == SRC_B

    def test_a_structural_problem_fails_validation_and_names_the_path(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            make_schema(
                messages=section(NameError__not_defined=entry(DEVANAGARI, "nope"))
            )
        assert "messages.cpython.NameError.not_defined" in str(excinfo.value)

    def test_the_load_error_names_every_problem(self) -> None:
        """A contributor fixes all of them in one pass, not one per load."""
        with pytest.raises(ValidationError) as excinfo:
            make_schema(
                messages={
                    "cpython": {
                        "NameError.not_defined": {"text": DEVANAGARI, "src": "nope"},
                        "traceback.frame": {"text": 7, "src": SRC_B},
                        "bad key": entry(ARABIC),
                    }
                }
            )
        message = str(excinfo.value)
        assert "messages.cpython.NameError.not_defined: 'src'" in message
        assert "messages.cpython.traceback.frame: 'text'" in message
        assert "'bad key'" in message

    @pytest.mark.parametrize("value", [[], "", 0, False])
    def test_a_falsy_section_that_is_not_a_mapping_fails_validation(
        self, value: object
    ) -> None:
        with pytest.raises(ValidationError, match="messages: must be a mapping"):
            make_schema(messages=value)

    @pytest.mark.parametrize("field", [True, False, 1, None, 3.5])
    def test_an_entry_field_name_that_is_not_a_string_is_not_examined(
        self, field: object
    ) -> None:
        """YAML reads ``on:``, ``yes:``, ``1:`` and ``null:`` as non-strings."""
        schema = make_schema(
            messages=section(
                NameError__not_defined=entry(ARABIC, **{"_": 0}) | {field: 1}
            )
        )
        assert schema.messages["cpython"]["NameError.not_defined"][field] == 1

    def test_extra_entry_fields_are_kept(self) -> None:
        schema = make_schema(
            messages=section(NameError__not_defined=entry(ARABIC, status="reviewed"))
        )
        assert schema.messages["cpython"]["NameError.not_defined"]["status"] == (
            "reviewed"
        )

    def test_unknown_top_level_keys_are_still_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_schema(message={"cpython": {}})

    def test_the_data_contract_allows_the_key(self) -> None:
        assert pack_messages.MESSAGES_SECTION in ALLOWED_TOP_LEVEL_KEYS

    def test_messages_are_neither_translations_nor_vocabulary(self) -> None:
        """So no identifier, script or round-trip check ever runs on prose."""
        assert pack_messages.MESSAGES_SECTION not in TRANSLATION_SECTIONS
        assert pack_messages.MESSAGES_SECTION not in VOCABULARY_SECTIONS


# ---------------------------------------------------------------------------
# Merge along the inheritance chain
# ---------------------------------------------------------------------------


class TestMerge:
    def test_a_section_only_in_the_overlay_survives(self) -> None:
        """The base has no ``messages``; the overlay's must not be dropped."""
        merged = LanguagePackLoader()._merge_packs(
            base={"keywords": {"def": "परिभाषा"}},
            override={"messages": section(NameError__not_defined=entry(DEVANAGARI))},
        )
        assert merged["messages"] == section(NameError__not_defined=entry(DEVANAGARI))

    def test_a_section_only_in_the_base_is_inherited(self) -> None:
        merged = LanguagePackLoader()._merge_packs(
            base={"messages": section(NameError__not_defined=entry(ARABIC))},
            override={"keywords": {"match": "मिलान"}},
        )
        assert merged["messages"] == section(NameError__not_defined=entry(ARABIC))

    def test_the_override_wins_per_key(self) -> None:
        merged = LanguagePackLoader()._merge_packs(
            base={
                "messages": section(
                    NameError__not_defined=entry(ARABIC),
                    UnboundLocalError__before_assignment=entry(DEVANAGARI, SRC_B),
                )
            },
            override={
                "messages": section(
                    UnboundLocalError__before_assignment=entry(
                        DEVANAGARI_REWORDED, SRC_C
                    )
                )
            },
        )
        assert merged["messages"] == section(
            NameError__not_defined=entry(ARABIC),
            UnboundLocalError__before_assignment=entry(DEVANAGARI_REWORDED, SRC_C),
        )

    def test_an_entry_is_replaced_whole_not_field_by_field(self) -> None:
        """A reworded entry must not inherit the old wording's review status."""
        merged = LanguagePackLoader()._merge_packs(
            base={
                "messages": section(
                    NameError__not_defined=entry(ARABIC, SRC_A, status="reviewed")
                )
            },
            override={
                "messages": section(NameError__not_defined=entry(DEVANAGARI, SRC_B))
            },
        )
        assert merged["messages"]["cpython"]["NameError.not_defined"] == entry(
            DEVANAGARI, SRC_B
        )

    def test_implementations_merge_independently(self) -> None:
        merged = LanguagePackLoader()._merge_packs(
            base={"messages": {"cpython": {"NameError.not_defined": entry(ARABIC)}}},
            override={
                "messages": {"pypy": {"NameError.not_defined": entry(DEVANAGARI)}}
            },
        )
        assert merged["messages"] == {
            "cpython": {"NameError.not_defined": entry(ARABIC)},
            "pypy": {"NameError.not_defined": entry(DEVANAGARI)},
        }

    def test_the_merge_does_not_change_its_inputs(self) -> None:
        base = {"messages": section(NameError__not_defined=entry(ARABIC))}
        override = {"messages": section(traceback__frame=entry(DEVANAGARI, SRC_B))}
        LanguagePackLoader()._merge_packs(base, override)
        assert base == {"messages": section(NameError__not_defined=entry(ARABIC))}
        assert override == {
            "messages": section(traceback__frame=entry(DEVANAGARI, SRC_B))
        }

    def test_a_null_implementation_in_the_base_is_not_hidden_by_an_overlay(
        self,
    ) -> None:
        merged = LanguagePackLoader()._merge_packs(
            base={"messages": {"cpython": None}},
            override={"messages": section(NameError__not_defined=entry(ARABIC))},
        )
        assert merged["messages"] == {"cpython": None}
        assert messages_structure_errors(merged["messages"]) != []

    def test_a_null_implementation_in_the_overlay_is_not_inherit(self) -> None:
        merged = LanguagePackLoader()._merge_packs(
            base={"messages": section(NameError__not_defined=entry(ARABIC))},
            override={"messages": {"cpython": None}},
        )
        assert merged["messages"] == {"cpython": None}
        assert messages_structure_errors(merged["messages"]) != []

    @pytest.mark.parametrize(
        ("base", "override"),
        [
            (["not", "a", "mapping"], section(NameError__not_defined=entry(ARABIC))),
            (section(NameError__not_defined=entry(ARABIC)), "not a mapping"),
            (
                {"cpython": "not a mapping"},
                section(NameError__not_defined=entry(ARABIC)),
            ),
            (section(NameError__not_defined=entry(ARABIC)), {"cpython": ["x"]}),
        ],
    )
    def test_a_malformed_side_reaches_validation(
        self, base: object, override: object
    ) -> None:
        """The merge must not repair or hide a section the schema would refuse."""
        merged = LanguagePackLoader()._merge_packs(
            base={"messages": base}, override={"messages": override}
        )
        assert messages_structure_errors(merged["messages"]) != []


# ---------------------------------------------------------------------------
# Loading from disk
# ---------------------------------------------------------------------------


def write_pack_tree(
    root: Path, files: dict[str, dict[str, object]]
) -> LanguagePackLoader:
    """Write version files for a synthetic ``zz`` pack and return a loader on it."""
    packs = root / "legesher_i18n_python_zz" / "packs"
    packs.mkdir(parents=True)
    previous: str | None = None
    for version, body in files.items():
        data: dict[str, object] = {
            "language": "zz",
            "target": "python",
            "version": version,
        }
        if previous is not None:
            data["extends"] = f"{previous}.yml"
        data.update(body)
        (packs / f"{version}.yml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        previous = version
    loader = LanguagePackLoader()
    loader._discovered_packs = {"python-zz": packs.parent}
    return loader


class TestLoading:
    def test_an_overlay_only_section_loads(self, tmp_path: Path) -> None:
        """3.10 carries no messages; a message added in 3.11 lives in 3.11.yml."""
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {"keywords": {"def": "परिभाषा"}},
                "3.11": {
                    "messages": section(
                        UnboundLocalError__before_assignment=entry(DEVANAGARI, SRC_C)
                    )
                },
            },
        )
        assert loader.load("zz", version="3.10").messages == {}
        pack = loader.load("zz", version="3.11")
        assert pack.messages == section(
            UnboundLocalError__before_assignment=entry(DEVANAGARI, SRC_C)
        )
        assert pack.keywords == {"def": "परिभाषा"}

    def test_each_version_sees_its_own_tier(self, tmp_path: Path) -> None:
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {
                    "keywords": {"def": "परिभाषा"},
                    "messages": section(
                        NameError__not_defined=entry(ARABIC),
                        UnboundLocalError__before_assignment=entry(DEVANAGARI, SRC_B),
                    ),
                },
                "3.11": {
                    "messages": section(
                        UnboundLocalError__before_assignment=entry(
                            DEVANAGARI_REWORDED, SRC_C
                        )
                    )
                },
                "3.12": {"keywords": {"type": "प्रकार"}},
            },
        )
        key = "UnboundLocalError.before_assignment"
        old = loader.load("zz", version="3.10").messages["cpython"]
        assert old[key] == entry(DEVANAGARI, SRC_B)
        for version in ("3.11", "3.12"):
            entries = loader.load("zz", version=version).messages["cpython"]
            assert entries[key] == entry(DEVANAGARI_REWORDED, SRC_C)
            assert entries["NameError.not_defined"] == entry(ARABIC)

    def test_text_survives_a_load_byte_for_byte(self, tmp_path: Path) -> None:
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {
                    "keywords": {"def": "परिभाषा"},
                    "messages": section(
                        NameError__not_defined=entry(ARABIC),
                        traceback__frame=entry(DEVANAGARI, SRC_B),
                    ),
                }
            },
        )
        entries = loader.load("zz", version="3.10").messages["cpython"]
        assert entries["NameError.not_defined"]["text"].encode() == ARABIC.encode()
        assert entries["traceback.frame"]["text"].encode() == DEVANAGARI.encode()

    def test_an_entry_the_catalog_will_not_use_leaves_the_pack_loadable(
        self, tmp_path: Path
    ) -> None:
        """Unknown key, unknown status, an extra field: none is a load error."""
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {
                    "keywords": {"def": "परिभाषा"},
                    "exceptions": {"nameerror": "नामत्रुटि"},
                    "messages": section(
                        NoSuchError__never_raised=entry(ARABIC),
                        NameError__not_defined=entry(
                            DEVANAGARI, status="not-a-status", plural={"few": ARABIC}
                        ),
                    ),
                }
            },
        )
        pack = loader.load("zz", version="3.10")
        assert pack.keywords == {"def": "परिभाषा"}
        assert pack.exceptions == {"nameerror": "नामत्रुटि"}
        assert set(pack.messages["cpython"]) == {
            "NoSuchError.never_raised",
            "NameError.not_defined",
        }

    def test_a_bidi_control_in_an_overlay_fails_the_load(self, tmp_path: Path) -> None:
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {"keywords": {"def": "परिभाषा"}},
                "3.11": {
                    "messages": section(NameError__not_defined=entry("‮" + ARABIC))
                },
            },
        )
        assert loader.load("zz", version="3.10").keywords == {"def": "परिभाषा"}
        with pytest.raises(PackValidationError) as excinfo:
            loader.load("zz", version="3.11")
        assert "messages.cpython.NameError.not_defined" in str(excinfo.value)
        assert "U+202E" in str(excinfo.value)

    def test_the_repr_counts_the_entries(self, tmp_path: Path) -> None:
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {
                    "keywords": {"def": "परिभाषा"},
                    "messages": section(NameError__not_defined=entry(ARABIC)),
                }
            },
        )
        pack = loader.load("zz", version="3.10")
        assert "messages=1" in repr(pack)

    def test_the_repr_counts_entries_across_implementations(
        self, tmp_path: Path
    ) -> None:
        loader = write_pack_tree(
            tmp_path,
            {
                "3.10": {
                    "keywords": {"def": "परिभाषा"},
                    "messages": {
                        "cpython": {
                            "NameError.not_defined": entry(ARABIC),
                            "traceback.frame": entry(DEVANAGARI, SRC_B),
                        },
                        "pypy": {"NameError.not_defined": entry(ARABIC)},
                    },
                }
            },
        )
        assert "messages=3" in repr(loader.load("zz", version="3.10"))


def _shipped_tiers() -> list[object]:
    """Every (language, version) the packs ship, from the registry and the loader.

    A tier whose merged values carry a character that a newer CPython added
    to identifiers is marked with the interpreter-gap ledger for the release
    it needs: on an older interpreter the schema rejects its identifiers
    before ``messages`` is reached. The release comes from the per-release
    tables, so a tier that one day needs 3.14 or 3.15 is ledgered on the
    older legs without a list of languages.
    """
    loader = LanguagePackLoader()
    tiers: list[object] = []
    for language in get_active_language_codes():
        for version in loader.list_available_versions():
            path = loader._get_pack_path(language, "python", version)
            data, _ = loader._resolve_inheritance(path, set())
            values = "".join(
                str(value)
                for name in (*TRANSLATION_SECTIONS, *VOCABULARY_SECTIONS)
                for value in (data.get(name) or {}).values()
            )
            needed = interpreter_needed_for_identifier(values)
            marks = [] if needed is None else [needs_identifier_rules_of(needed)]
            tiers.append(
                pytest.param(language, version, marks=marks, id=f"{language}-{version}")
            )
    return tiers


def test_the_tier_list_covers_every_shipped_pack_file() -> None:
    """The parametrization below is only as wide as this list."""
    on_disk = {
        (path.parents[2].name, path.stem)
        for path in (LIB_ROOT / "language-packs" / "python").glob(
            "*/legesher_i18n_python_*/packs/3.*.yml"
        )
    }
    listed = {tuple(tier.values) for tier in _shipped_tiers()}
    assert on_disk and listed == on_disk


@pytest.mark.parametrize(("language", "version"), _shipped_tiers())
def test_every_shipped_pack_loads_with_a_well_formed_section(
    language: str, version: str
) -> None:
    """Holds before and after packs carry messages: the section, when present,
    passes the structural rules at every version the pack ships."""
    pack = LanguagePackLoader().load(
        language, version=version, enforce_min_interpreter=False
    )
    assert messages_structure_errors(pack.messages) == []
