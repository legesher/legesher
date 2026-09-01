"""The message-template generation lane (CORE-1881).

Messages are sentences with ``{slot}`` placeholders and grammar, not
identifiers — the term lane does not carry over. The lane builds a
placeholder-preserving prompt per locale, and every model suggestion passes
the mechanical gate on the way to the database: the write goes through
``add_message_locale.add_locale``, so placeholder parity, bidi hygiene,
coverage, and provenance are enforced by the same code for every writer.

Model calls are injected; nothing here talks to an API.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.activate_messages_partition import activate
from scripts.seed_message_templates import seed_database
from scripts.translate.generate_messages import (
    SOURCE,
    build_prompt,
    compose_addition,
    identity_id,
    load_templates,
    run_lane,
)


@pytest.fixture
def db(tmp_path: Path) -> Path:
    path = tmp_path / "translations.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (
            code TEXT PRIMARY KEY, name TEXT NOT NULL, native_name TEXT,
            has_yaml_pack BOOLEAN DEFAULT 0
        );
        INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES
            ('en', 'English', 'English', 1),
            ('es', 'Spanish', 'español', 1),
            ('fr', 'French', 'français', 1),
            ('am', 'Amharic', 'አማርኛ', 1),
            ('xx', 'No Pack', 'No Pack', 0);
        """
    )
    conn.commit()
    conn.close()
    activate(path)
    seed_database(
        path,
        {
            "implementation": "cpython",
            "version_added": "3.10",
            "templates": [
                {
                    "key": "ZeroDivisionError.division_by_zero",
                    "template_en": "division by zero",
                    "placeholders": [],
                    "matcher": "^division by zero$",
                    "translations": {
                        "es": {"template": "división por cero"},
                    },
                },
                {
                    "key": "NameError.not_defined",
                    "template_en": "name '{name}' is not defined",
                    "placeholders": [{"name": "name", "example": "x"}],
                    "matcher": "^name '(?P<name>[^']+)' is not defined$",
                    "translations": {
                        "es": {"template": "el nombre '{name}' no está definido"},
                    },
                },
            ],
        },
    )
    return path


def read_templates(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        return load_templates(conn, "cpython")
    finally:
        conn.close()


def fr_payload(templates: list[dict]) -> dict:
    translations = {
        identity_id(t): {
            "ZeroDivisionError.division_by_zero": "division par zéro",
            "NameError.not_defined": "le nom '{name}' n'est pas défini",
        }[t["key"]]
        for t in templates
    }
    return {"translations": translations, "notes": "sure of both"}


def fake_call_factory(payload_by_locale: dict[str, dict], calls: list[str]):
    """A ``call_model``-shaped fake; records which locale prompts were sent."""

    def call(prompt: str, model: str) -> tuple[str, int, int]:
        for locale, payload in payload_by_locale.items():
            if f"[[locale:{locale}]]" in prompt:
                calls.append(locale)
                return json.dumps(payload, ensure_ascii=False), 1000, 500
        raise AssertionError("prompt for an unexpected locale")

    return call


def stored_locales(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    rows = dict(
        conn.execute(
            "SELECT locale, COUNT(*) FROM message_translations GROUP BY locale"
        )
    )
    conn.close()
    return rows


class TestPrompt:
    def test_prompt_names_every_template_and_the_preservation_rule(self, db: Path):
        templates = read_templates(db)
        prompt = build_prompt("fr", "French", "français", templates)
        for t in templates:
            assert identity_id(t) in prompt
            assert t["template_en"] in prompt
        assert "French" in prompt
        assert "{name}" in prompt
        assert "exactly" in prompt.lower()
        # the machine-checkable locale marker the fake keys on is also how
        # operators grep a dry-run dump
        assert "[[locale:fr]]" in prompt


class TestComposeAddition:
    def test_complete_payload_composes_a_provenanced_addition(self, db: Path):
        templates = read_templates(db)
        addition, problems = compose_addition(
            "cpython", "fr", "model-x", fr_payload(templates), templates
        )
        assert problems == []
        assert addition["source"] == SOURCE
        assert addition["model_version"] == "model-x"
        assert addition["created_by"] == "generate_messages.py"
        assert len(addition["translations"]) == 2

    def test_missing_identity_is_a_problem(self, db: Path):
        templates = read_templates(db)
        payload = fr_payload(templates)
        del payload["translations"][identity_id(templates[0])]
        _, problems = compose_addition("cpython", "fr", "model-x", payload, templates)
        assert any("missing" in p for p in problems)

    def test_unknown_identity_is_a_problem(self, db: Path):
        templates = read_templates(db)
        payload = fr_payload(templates)
        payload["translations"]["OverflowError.too_large@3.10"] = "trop grand"
        _, problems = compose_addition("cpython", "fr", "model-x", payload, templates)
        assert any("OverflowError" in p for p in problems)

    def test_non_string_value_is_a_problem(self, db: Path):
        templates = read_templates(db)
        payload = fr_payload(templates)
        payload["translations"][identity_id(templates[0])] = 42
        _, problems = compose_addition("cpython", "fr", "model-x", payload, templates)
        assert any("string" in p for p in problems)


class TestRunLane:
    @pytest.fixture(autouse=True)
    def configured_rates(self, monkeypatch):
        """Real (non-dry) runs enforce the budget, which needs rates."""
        from legesher_i18n.api import rates

        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", "3.0")
        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", "15.0")
        rates.reset_cache()
        yield
        rates.reset_cache()

    def test_generates_and_stores_with_provenance(self, db: Path):
        templates = read_templates(db)
        calls: list[str] = []
        written, failures, skipped = run_lane(
            db,
            locales=["fr"],
            model="model-x",
            call=fake_call_factory({"fr": fr_payload(templates)}, calls),
        )
        assert calls == ["fr"]
        assert written == {"fr": 2}
        assert failures == {}
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT source, model_version, created_by, status "
            "FROM message_translations WHERE locale = 'fr'"
        ).fetchone()
        conn.close()
        assert row == (SOURCE, "model-x", "generate_messages.py", "machine")

    def test_mangled_placeholder_writes_nothing_for_the_locale(self, db: Path):
        templates = read_templates(db)
        payload = fr_payload(templates)
        payload["translations"][identity_id(templates[1])] = (
            "le nom '{nom}' n'est pas défini"
        )
        written, failures, _ = run_lane(
            db,
            locales=["fr"],
            model="model-x",
            call=fake_call_factory({"fr": payload}, []),
        )
        assert written == {}
        assert "fr" in failures
        assert any("placeholder" in p for p in failures["fr"])
        assert "fr" not in stored_locales(db)

    def test_populated_and_english_locales_are_skipped(self, db: Path):
        templates = read_templates(db)
        calls: list[str] = []
        written, failures, skipped = run_lane(
            db,
            locales=["en", "es", "fr"],
            model="model-x",
            call=fake_call_factory({"fr": fr_payload(templates)}, calls),
        )
        assert calls == ["fr"]
        assert sorted(skipped) == ["en", "es"]
        assert written == {"fr": 2}

    def test_all_missing_targets_pack_languages_only(self, db: Path):
        templates = read_templates(db)
        calls: list[str] = []
        run_lane(
            db,
            locales=None,  # --all-missing
            model="model-x",
            call=fake_call_factory(
                {"fr": fr_payload(templates), "am": fr_payload(templates)}, calls
            ),
        )
        # en (seed language), es (populated), xx (no pack) are all excluded
        assert sorted(calls) == ["am", "fr"]

    def test_dry_run_calls_nothing_and_writes_nothing(self, db: Path):
        calls: list[str] = []
        written, failures, _ = run_lane(
            db,
            locales=["fr"],
            model="model-x",
            call=fake_call_factory({}, calls),
            dry_run=True,
        )
        assert calls == []
        assert written == {}
        assert "fr" not in stored_locales(db)

    def test_budget_stops_the_run_before_the_next_call(self, db: Path):
        templates = read_templates(db)
        calls: list[str] = []
        written, failures, _ = run_lane(
            db,
            locales=["fr", "am"],
            model="model-x",
            call=fake_call_factory(
                {"fr": fr_payload(templates), "am": fr_payload(templates)}, calls
            ),
            max_budget=0.000001,
        )
        # the first call is allowed (budget not yet spent); the second is not
        assert len(calls) == 1
        assert any("budget" in p for locale in failures.values() for p in locale)


class TestFailureIsolation:
    @pytest.fixture(autouse=True)
    def configured_rates(self, monkeypatch):
        from legesher_i18n.api import rates

        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", "3.0")
        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", "15.0")
        rates.reset_cache()
        yield
        rates.reset_cache()

    def test_one_locale_failing_does_not_end_the_run(self, db: Path):
        templates = read_templates(db)
        good = fake_call_factory({"am": fr_payload(templates)}, [])

        def call(prompt, model):
            if "[[locale:fr]]" in prompt:
                raise ConnectionError("socket dropped")
            return good(prompt, model)

        written, failures, _ = run_lane(
            db, locales=["fr", "am"], model="model-x", call=call
        )
        assert written == {"am": 2}
        assert "socket dropped" in failures["fr"][0]

    def test_runtime_error_aborts_the_whole_run(self, db: Path):
        """RuntimeError is the configuration channel (no API key / no SDK)."""

        def call(prompt, model):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        with pytest.raises(RuntimeError, match="API_KEY"):
            run_lane(db, locales=["fr", "am"], model="model-x", call=call)

    def test_unparseable_response_is_a_per_locale_failure(self, db: Path):
        def call(prompt, model):
            return "I am not JSON", 10, 10

        written, failures, _ = run_lane(db, locales=["fr"], model="model-x", call=call)
        assert written == {}
        assert any("unparseable" in p for p in failures["fr"])


class TestMessageShapedContent:
    """The contracts the 'sentences, not identifiers' framing rests on."""

    @pytest.fixture
    def braces_db(self, tmp_path: Path) -> Path:
        path = tmp_path / "translations.db"
        conn = sqlite3.connect(path)
        conn.executescript(
            """
            CREATE TABLE languages (
                code TEXT PRIMARY KEY, name TEXT NOT NULL, native_name TEXT,
                has_yaml_pack BOOLEAN DEFAULT 0
            );
            INSERT INTO languages (code, name, native_name, has_yaml_pack)
            VALUES ('fr', 'French', 'français', 1);
            """
        )
        conn.commit()
        conn.close()
        activate(path)
        seed_database(
            path,
            {
                "implementation": "cpython",
                "version_added": "3.12",
                "templates": [
                    {
                        "key": "SyntaxError.fstring_valid_expression",
                        "template_en": (
                            "f-string: valid expression required before '}'"
                        ),
                        "placeholders": [],
                        "matcher": ("^f-string: valid expression required before '}'$"),
                        "translations": {},
                    },
                    {
                        "key": "KeyboardInterrupt.interrupt",
                        "template_en": "",
                        "placeholders": [],
                        "matcher": "^$",
                        "translations": {},
                    },
                ],
            },
        )
        return path

    def test_literal_brace_and_empty_template_flow_through(self, braces_db: Path):
        templates = read_templates(braces_db)
        prompt = build_prompt("fr", "French", "français", templates)
        assert "'}'" in prompt
        assert "(empty message)" in prompt

        payload = {
            "translations": {
                "SyntaxError.fstring_valid_expression@3.12": (
                    "f-string : expression valide requise avant '}'"
                ),
                "KeyboardInterrupt.interrupt@3.12": "",
            },
            "notes": "",
        }
        written, failures, _ = run_lane(
            braces_db,
            locales=["fr"],
            model="model-x",
            call=lambda prompt, model: (json.dumps(payload), 10, 10),
            max_budget=None,
        )
        assert failures == {}
        assert written == {"fr": 2}
        assert stored_locales(braces_db) == {"fr": 2}


class TestBudgetWaivers:
    def test_no_budget_with_unconfigured_rates_proceeds(self, db: Path, monkeypatch):
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        rates.reset_cache()
        try:
            templates = read_templates(db)
            written, failures, _ = run_lane(
                db,
                locales=["fr"],
                model="model-x",
                call=fake_call_factory({"fr": fr_payload(templates)}, []),
                max_budget=None,
            )
            assert written == {"fr": 2}
            assert failures == {}
        finally:
            rates.reset_cache()

    def test_dry_run_needs_no_rates(self, db: Path, monkeypatch):
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        rates.reset_cache()
        try:
            written, failures, _ = run_lane(
                db,
                locales=["fr"],
                model="model-x",
                call=fake_call_factory({}, []),
                dry_run=True,
            )
            assert (written, failures) == ({}, {})
        finally:
            rates.reset_cache()


class TestCli:
    def test_locales_and_all_missing_are_mutually_exclusive(self, db: Path):
        from scripts.translate.generate_messages import main

        with pytest.raises(SystemExit):
            main(["--db", str(db), "--locales", "fr", "--all-missing"])
        with pytest.raises(SystemExit):
            main(["--db", str(db)])

    def test_missing_database_is_refused(self, tmp_path: Path):
        from scripts.translate.generate_messages import main

        with pytest.raises(SystemExit, match="not found"):
            main(["--db", str(tmp_path / "nope.db"), "--locales", "fr"])


class TestBudgetNeedsRates:
    def test_enforced_budget_with_unconfigured_rates_is_refused(
        self, db: Path, monkeypatch
    ):
        """A ceiling that cannot be measured must fail loud, not silently."""
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", raising=False)
        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        rates.reset_cache()
        try:
            with pytest.raises(SystemExit, match="rates"):
                run_lane(
                    db,
                    locales=["fr"],
                    model="model-x",
                    call=fake_call_factory({}, []),
                )
        finally:
            rates.reset_cache()
