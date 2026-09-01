"""Content contract of the seeded CPython message catalog (CORE-1679).

These run against the REAL committed ``translations.db`` — the database is
the source of truth for the catalog, so the invariants (matcher discipline,
placeholder preservation in every es/ar translation, version tiering) are
asserted on the shipped rows, not on a fixture.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db.database import default_db_path
from legesher_i18n.messages import MessageRule, load_catalog, match_message

DB_PATH = Path(__file__).parents[1] / "legesher_i18n" / "db" / "translations.db"

#: The database is an untracked working copy since CORE-1794 — a fresh clone
#: does not have it until it is copied in from the private data home (see
#: libs/i18n/CLAUDE.md, "Durable home & sync ritual").
pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason=(
        "translations.db is an untracked working copy (CORE-1794); copy it in "
        "from the private data home — libs/i18n/CLAUDE.md, 'Durable home & "
        "sync ritual'"
    ),
)

SEEDED_LOCALES = ("es", "ar")

#: Message families the CORE-1679 catalog promises to cover.
REQUIRED_KEY_PREFIXES = (
    "traceback.",
    "SyntaxError.",
    "NameError.",
    "TypeError.",
    "AttributeError.",
    "ImportError.",
    "ModuleNotFoundError.",
    "IndexError.",
    "KeyError.",
    "ValueError.",
    "ZeroDivisionError.",
    "IndentationError.",
    "TabError.",
    "FileNotFoundError.",
    "RecursionError.",
    "UnboundLocalError.",
    "StopIteration.",
    "KeyboardInterrupt.",
    "AssertionError.",
)

PLACEHOLDER = re.compile(r"\{(\w+)\}")


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    fetched = conn.execute(
        "SELECT id, key, template_en, placeholders, matcher, version_added, "
        "version_removed FROM message_templates WHERE implementation = 'cpython'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in fetched]


@pytest.fixture(scope="module")
def translations() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    fetched = conn.execute(
        "SELECT t.key, t.template_en, tr.locale, tr.template, tr.status "
        "FROM message_translations tr "
        "JOIN message_templates t ON t.id = tr.template_id "
        "WHERE t.implementation = 'cpython'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in fetched]


class TestCatalogShape:
    def test_at_least_forty_templates(self, rows):
        assert len(rows) >= 40

    def test_every_required_family_is_present(self, rows):
        keys = {r["key"] for r in rows}
        for prefix in REQUIRED_KEY_PREFIXES:
            assert any(k.startswith(prefix) for k in keys), f"no {prefix}* template"

    def test_every_template_is_fully_translated(self, rows, translations):
        by_locale: dict[str, set[str]] = {loc: set() for loc in SEEDED_LOCALES}
        for tr in translations:
            by_locale.setdefault(tr["locale"], set()).add(tr["key"])
        all_keys = {r["key"] for r in rows}
        for locale in SEEDED_LOCALES:
            assert by_locale[locale] == all_keys

    def test_translations_enter_at_machine_rung(self, translations):
        assert {tr["status"] for tr in translations} == {"machine"}

    def test_every_translation_carries_provenance(self):
        """CORE-1881: renderings do not sit unattributed.

        Rows written since the provenance columns landed carry write-time
        provenance; the pre-migration ar/es rows were backfilled
        ``source='seed'`` by ``scripts/add_message_provenance.py``. A NULL
        here means the working copy predates the migration — re-run it (see
        libs/i18n/CLAUDE.md, messages formation ritual).
        """
        conn = sqlite3.connect(DB_PATH)
        unattributed = conn.execute(
            "SELECT COUNT(*) FROM message_translations WHERE source IS NULL"
        ).fetchone()[0]
        conn.close()
        assert unattributed == 0

    def test_version_tiering_unboundlocalerror_rewording(self, rows):
        tiers = {
            r["version_added"]: r
            for r in rows
            if r["key"] == "UnboundLocalError.before_assignment"
        }
        assert set(tiers) == {"3.10", "3.11"}
        assert tiers["3.10"]["version_removed"] == "3.11"
        assert tiers["3.11"]["version_removed"] is None


class TestMatcherDiscipline:
    def test_every_matcher_compiles_anchored_with_placeholder_groups(self, rows):
        for row in rows:
            assert row["matcher"], f"{row['key']}: no matcher"
            rx = re.compile(row["matcher"])
            assert row["matcher"].startswith("^") and row["matcher"].endswith("$"), (
                f"{row['key']}: matcher not anchored"
            )
            declared = {p["name"] for p in json.loads(row["placeholders"] or "[]")}
            assert set(rx.groupindex) == declared, (
                f"{row['key']}: group/placeholder drift"
            )

    def test_every_matcher_round_trips_its_template(self, rows):
        """template_en rendered with the examples fullmatches, slots survive."""
        for row in rows:
            placeholders = json.loads(row["placeholders"] or "[]")
            examples = {p["name"]: p["example"] for p in placeholders}
            rendered = row["template_en"]
            for name, example in examples.items():
                rendered = rendered.replace("{" + name + "}", example)
            match = re.compile(row["matcher"]).fullmatch(rendered)
            assert match, f"{row['key']}: matcher misses its own example: {rendered!r}"
            assert match.groupdict() == examples, f"{row['key']}: slots did not survive"

    def test_every_translation_preserves_named_slots(self, translations):
        for tr in translations:
            slots_en = set(PLACEHOLDER.findall(tr["template_en"]))
            slots_tr = set(PLACEHOLDER.findall(tr["template"]))
            assert slots_tr == slots_en, (
                f"{tr['key']} [{tr['locale']}]: slots {slots_tr} != {slots_en}"
            )


class TestLoader:
    def test_default_db_path_is_the_committed_database(self):
        assert default_db_path() == DB_PATH

    def test_load_catalog_es(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        assert len(rules) >= 40
        assert all(isinstance(r, MessageRule) for r in rules)
        assert all(r.localized for r in rules)

    def test_one_rule_per_key_after_tiering(self):
        for version in ("3.10", "3.11", "3.13"):
            rules = load_catalog("es", version, db_path=DB_PATH)
            keys = [r.key for r in rules]
            assert len(keys) == len(set(keys))

    def test_unboundlocalerror_tier_flips_at_3_11(self):
        def wording(version: str) -> str:
            (rule,) = [
                r
                for r in load_catalog("es", version, db_path=DB_PATH)
                if r.key == "UnboundLocalError.before_assignment"
            ]
            return rule.template_en

        assert "referenced before assignment" in wording("3.10")
        assert "not associated with a value" in wording("3.11")

    def test_3_12_additions_absent_at_3_11(self):
        keys_311 = {r.key for r in load_catalog("es", "3.11", db_path=DB_PATH)}
        keys_312 = {r.key for r in load_catalog("es", "3.12", db_path=DB_PATH)}
        assert "NameError.forgot_import" not in keys_311
        assert "NameError.forgot_import" in keys_312

    def test_unknown_locale_falls_back_to_english(self):
        rules = load_catalog("xx", "3.12", db_path=DB_PATH)
        assert rules and all(not r.localized for r in rules)
        assert all(r.template == r.template_en for r in rules)

    def test_missing_partition_yields_empty_catalog(self, tmp_path):
        bare = tmp_path / "old.db"
        conn = sqlite3.connect(bare)
        conn.execute("CREATE TABLE languages (code TEXT)")
        conn.commit()
        conn.close()
        assert load_catalog("es", "3.12", db_path=bare) == []

    def test_match_and_render_substitution(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        name_rules = [r for r in rules if r.key.startswith("NameError.")]
        localized = match_message(name_rules, "name 'contador' is not defined")
        assert localized == "el nombre 'contador' no está definido"

    def test_match_and_render_arabic_preserves_slot_value(self):
        rules = load_catalog("ar", "3.12", db_path=DB_PATH)
        zd = [r for r in rules if r.key.startswith("ZeroDivisionError.")]
        assert match_message(zd, "division by zero") == "القسمة على صفر"
        ne = [r for r in rules if r.key == "NameError.not_defined"]
        assert "contador" in match_message(ne, "name 'contador' is not defined")

    def test_unmatched_message_returns_none(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        assert (
            match_message(
                rules, "some exotic message nobody templated", key_prefix="TypeError"
            )
            is None
        )

    def test_key_prefix_scopes_matching(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        # Scoped to the right type: localizes.
        assert (
            match_message(rules, "division by zero", key_prefix="ZeroDivisionError")
            == "división por cero"
        )
        # Scoped to the wrong type: no match, even though a ZeroDivisionError
        # rule would have matched.
        assert match_message(rules, "division by zero", key_prefix="NameError") is None

    def test_unscoped_match_never_echoes_english_via_catch_all(self):
        # Review repro: KeyError.key's ^(?P<key>.+)$ fullmatches ANY
        # single-line message; unscoped matching used to return the ENGLISH
        # text through it, indistinguishable from a real localization.
        rules = load_catalog("es", "3.13", db_path=DB_PATH)
        assert match_message(rules, "division by zero") == "división por cero"
        # And a message only the catch-all would swallow matches nothing.
        assert match_message(rules, "an arbitrary unknown message") is None

    def test_catch_all_rule_works_when_scoped_to_its_type(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        (key_rule,) = [r for r in rules if r.key == "KeyError.key"]
        assert key_rule.catch_all
        assert match_message(rules, "'edad'", key_prefix="KeyError") == "'edad'"

    def test_only_the_intended_rule_is_a_catch_all(self):
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        assert [r.key for r in rules if r.catch_all] == ["KeyError.key"]

    def test_specific_suggestion_rules_match_before_generic_did_you_mean(self):
        # NameError.self_suggestion is seeded BEFORE not_defined_did_you_mean
        # (whose '{suggestion}' group would also swallow "self.x"); rule
        # order is contractual (ORDER BY id = seed order).
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        message = "name 'valor' is not defined. Did you mean: 'self.valor'?"
        name_rules = [r for r in rules if r.key.startswith("NameError.")]
        first_match = next(r for r in name_rules if r.matcher.fullmatch(message))
        assert first_match.key == "NameError.self_suggestion"

    def test_missing_db_path_returns_empty_and_creates_no_file(self, tmp_path):
        # Review repro: a plain sqlite3.connect silently CREATED an empty
        # 0-byte database file at the wrong path.
        missing = tmp_path / "nope" / "translations.db"
        assert load_catalog("es", "3.12", db_path=missing) == []
        assert not missing.exists()
        assert not missing.parent.exists()

    def test_stray_brace_template_renders_without_format_error(self):
        """CPython's f-string message carries a bare '}' — str.format would raise."""
        rules = load_catalog("es", "3.12", db_path=DB_PATH)
        (rule,) = [r for r in rules if r.key == "SyntaxError.fstring_valid_expression"]
        assert "'}'" in rule.render({})
