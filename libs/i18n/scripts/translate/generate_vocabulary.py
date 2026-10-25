#!/usr/bin/env python3
"""Generate the pack vocabulary partition for a language (CORE-1396).

Fills ``symbols`` (what a Python symbol is CALLED) and
``variable_conventions`` (the idiomatic short names) for one or more
languages, using the linguist-framed prompt specified in
``prompts/vocabulary_prompt.md``.

Design notes worth knowing before running it
--------------------------------------------
* **One call per language, both sections together.** They share the
  script/formatting profile and the framing, so batching keeps a full run
  at one call per language rather than one per entry (CORE-1805's economics rule: a per-item
  call is the leak).
* **English is never generated.** ``scripts/seed_vocabulary.py`` seeds it
  from the canonical inventory — the English name of a symbol IS the
  inventory entry, so a model call would be paying to reproduce a constant.
  ``en`` is skipped with a note rather than silently.
* **All-or-nothing per language.** A response with ANY invalid value, or
  any missing slug, is reported and nothing is written for that language.
  The alternative — writing the good half — creates exactly the partial
  state the exporter then refuses to ship, with no record of why.
* **Candidates and selections both.** Values land in
  ``vocabulary_translations`` (the dirty-tolerant pool) AND in
  ``selected_vocabulary`` (the publish-gated layer the exporter reads), so
  a later re-generation can be compared against this one instead of
  overwriting it blind.
* **Packs are not written here.** Regeneration is a separate deliberate
  step (``scripts/export_packs.py``): pack writes are authoritative, and a
  generation script must never be the thing that rewrites shipped files.

Requires ``ANTHROPIC_API_KEY``. Run ``--dry-run`` to render and inspect the
prompts without spending anything.

Usage:
    # inspect what would be sent, no API key needed
    python scripts/translate/generate_vocabulary.py --languages es ar --dry-run

    # generate for two languages
    python scripts/translate/generate_vocabulary.py --languages es ar

    # the full run: every pack language that has no vocabulary yet
    python scripts/translate/generate_vocabulary.py --all --skip-complete

Afterwards, in order:
    python scripts/export_packs.py                      # regenerate packs
    python scripts/verify_pack_regen.py --db <db>       # the regen gate
    python scripts/audit_collisions.py                  # expect "all N expected"
    ... then the durable-home push (libs/i18n/CLAUDE.md).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))

from legesher_i18n.api.rates import cost_for_tokens, format_cost  # noqa: E402
from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.language_registry import (  # noqa: E402
    get_language_name,
    get_native_name,
)
from legesher_i18n.model_config import anthropic_model  # noqa: E402
from legesher_i18n.selection import vocabulary_value_error  # noqa: E402
from legesher_i18n.style_guides import StyleGuideLoader  # noqa: E402
from legesher_i18n.vocabulary_definitions import (  # noqa: E402
    SYMBOLS,
    VARIABLE_CONVENTIONS,
    VOCABULARY_SECTIONS,
    slugs_for_section,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

#: Provenance label. Matches ``selection.SOURCE_TRUST``'s ``claude_agent``
#: rung — linguist-framed agent output, above single-shot ``claude``.
SOURCE = "claude_agent"

#: The one language whose vocabulary is definitional, not generated.
SEED_LANGUAGE = "en"

#: Generous: the response is ~48 short values plus a few sentences.
MAX_OUTPUT_TOKENS = 4096


def render_symbol_inventory() -> str:
    """The symbol table as prompt text, generated from the inventory."""
    lines = ["| slug | symbol | English name | role |", "| --- | --- | --- | --- |"]
    for entry in SYMBOLS:
        glyph = f"`{entry.glyph}`" if entry.glyph else "(no printable form)"
        lines.append(
            f"| {entry.slug} | {glyph} | {entry.english_name} | {entry.role} |"
        )
    return "\n".join(lines)


def render_convention_inventory() -> str:
    """The variable-role table as prompt text."""
    lines = ["| slug | English idiom | role |", "| --- | --- | --- |"]
    for entry in VARIABLE_CONVENTIONS:
        lines.append(f"| {entry.slug} | `{entry.english_value}` | {entry.role} |")
    return "\n".join(lines)


def render_style_profile(language_code: str) -> str:
    """The language's script/formatting facts, from its style guide.

    Rules only — which is all a style guide holds. The guide is read, never
    written: CORE-1396 moves nothing out of it (see
    ``style-guides/README.md``, which already points at the packs for
    vocabulary).

    A language with no guide gets an explicit "not available" line rather
    than a silent omission, so a thin prompt is visible in the log.
    """
    try:
        guide = StyleGuideLoader().load(language_code)
    except Exception as exc:  # noqa: BLE001 - a missing guide must not abort
        return f"(no style guide available for '{language_code}': {exc})"

    script = guide.get("script", {}) or {}
    naming = guide.get("naming", {}) or {}
    supports = guide.get("supports", {}) or {}

    lines = [
        f"- Script: {script.get('name', 'unknown')}, "
        f"direction {script.get('direction', 'unknown')}.",
        f"- Letter case: {'yes' if supports.get('case_distinction') else 'no'}.",
        f"- Native digit forms: "
        f"{'yes' if supports.get('native_digits') else 'no'} "
        "(code uses ASCII 0-9 regardless).",
    ]
    if naming.get("detail"):
        lines.append(f"- Identifier formation: {str(naming['detail']).strip()}")
    for constraint in script.get("constraints", []) or []:
        lines.append(f"- Constraint: {constraint}")
    return "\n".join(lines)


def build_prompt(language_code: str) -> str:
    """Render the linguist-framed prompt for one language.

    The inventory blocks are generated from
    :mod:`legesher_i18n.vocabulary_definitions`, so the prompt cannot ask
    for a slug the schema does not accept, nor omit one it requires.
    """
    language_name = get_language_name(language_code) or language_code
    native_name = get_native_name(language_code) or language_name

    return f"""You are a linguist documenting how programmers who speak \
{language_name} ({native_name}) talk about Python code. You are not \
translating: you are reporting what speakers of this language actually say \
and write.

Two questions, answered for {language_name}.

## Question 1 - what these symbols are CALLED

For each symbol below, give the name speakers of {language_name} use for \
that mark when reading code or prose aloud.

Report what people SAY. Do not calque the English name. English calls '#' a \
"hash sign"; many languages call it a grid, a lattice, or the musical sharp. \
English calls '_' an "underscore" (a typewriter word); Spanish says "guion \
bajo", German "Unterstrich".

If {language_name} genuinely uses the English loanword for a symbol, give the \
loanword. An honest loan is a real answer; an invented native-sounding \
coinage that nobody uses is not.

Give a NAME, not a definition - a short noun phrase, at most 60 characters. \
The 'role' column is context for you, never the answer.

{render_symbol_inventory()}

## Question 2 - the short variable names programmers actually type

For each ROLE below, give the short variable name a programmer writing \
{language_name} would habitually type.

'i' is very often the correct answer and you should say so when it is: the \
loop counter 'i' comes from mathematical index notation, not from the English \
word "index", and programmers in most languages use it. We are looking for \
the roles where {language_name} genuinely DIVERGES. Renaming every role into \
native abbreviations would describe no real codebase.

Each value must be a valid Python identifier, must not be a Python keyword, \
and must parse on CPython 3.10 (avoid characters that only became \
identifier-legal in CPython 3.13). Keep them short - brevity is the whole \
point of these names.

{render_convention_inventory()}

## Script and formatting profile for {language_name}

{render_style_profile(language_code)}

## Output format

Return ONE JSON object and nothing else:

{{
  "symbols": {{"<slug>": "<name in {language_name}>", ...}},
  "variable_conventions": {{"<slug>": "<identifier>", ...}},
  "notes": "<2-3 sentences: which answers you were least sure of, and any \
role where the language genuinely diverges>"
}}

Every slug listed above must appear exactly once in its section. Do not add \
slugs that were not listed.
"""


def validate_response(payload: dict[str, Any]) -> tuple[dict[str, dict], list[str]]:
    """Check a model response against the inventory and the publish gate.

    Returns ``(values, problems)``. ``values`` is
    ``{section: {slug: value}}``; ``problems`` is empty only when the
    response is complete and every value is publishable. The caller writes
    nothing unless ``problems`` is empty — a half-written language is the
    state the all-or-nothing rule exists to prevent.
    """
    values: dict[str, dict] = {}
    problems: list[str] = []

    for section in VOCABULARY_SECTIONS:
        section_payload = payload.get(section)
        if not isinstance(section_payload, dict):
            problems.append(f"response has no '{section}' object")
            continue

        expected = slugs_for_section(section)
        missing = [slug for slug in expected if slug not in section_payload]
        unknown = sorted(set(section_payload) - set(expected))
        if missing:
            problems.append(f"{section}: missing {len(missing)} slug(s) {missing[:8]}")
        if unknown:
            problems.append(f"{section}: unknown slug(s) {unknown[:8]}")

        clean: dict[str, str] = {}
        for slug in expected:
            value = section_payload.get(slug)
            if value is None:
                continue
            if not isinstance(value, str):
                problems.append(f"{section}.{slug}: value is not a string ({value!r})")
                continue
            value = value.strip()
            error = vocabulary_value_error(section, slug, value)
            if error is not None:
                problems.append(error)
                continue
            clean[slug] = value
        values[section] = clean

    return values, problems


def parse_json_response(text: str) -> dict[str, Any]:
    """Parse the model's JSON, tolerating a ```json fence around it.

    Raises:
        ValueError: If no JSON object can be recovered.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[: -len("```")]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object in response: {text[:200]!r}")
    return json.loads(stripped[start : end + 1])


def call_model(prompt: str, model: str) -> tuple[str, int, int]:
    """One Anthropic call. Returns ``(text, input_tokens, output_tokens)``.

    Raises:
        RuntimeError: If the SDK is unavailable or no API key is set. Both
            fail loudly rather than degrading to a stub — an invented
            vocabulary is worse than no vocabulary.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Vocabulary values are never "
            "fabricated locally; set the key or use --dry-run."
        )
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "The 'anthropic' package is not installed; install the API "
            "extra (pip install legesher-i18n[api])."
        ) from exc

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )
    return text, response.usage.input_tokens, response.usage.output_tokens


def write_language(
    db: TranslationDatabase,
    language_code: str,
    values: dict[str, dict],
    model_version: str,
    notes: str,
) -> int:
    """Write one language's validated vocabulary. Returns values written."""
    written = 0
    for section, slug_values in values.items():
        entries = {
            row["slug"]: row["id"] for row in db.get_vocabulary_entries(section=section)
        }
        for slug, value in slug_values.items():
            entry_id = entries.get(slug)
            if entry_id is None:
                raise RuntimeError(
                    f"No vocabulary entry for {section}.{slug}; run "
                    "scripts/seed_vocabulary.py first."
                )
            db.add_vocabulary_translation(
                entry_id=entry_id,
                language_code=language_code,
                value=value,
                source=SOURCE,
                model_version=model_version,
                confidence="medium",
                model_rationale=notes or None,
                created_by="generate_vocabulary.py",
            )
            db.set_selected_vocabulary(
                entry_id=entry_id,
                language_code=language_code,
                value=value,
                selected_by="generate_vocabulary.py",
                selection_reason=f"{SOURCE}:{model_version}",
            )
            written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=None, help="Path to translations.db")
    parser.add_argument("--languages", nargs="+", help="Language codes to generate")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Every language with a YAML pack (English excluded — it is seeded)",
    )
    parser.add_argument(
        "--skip-complete",
        action="store_true",
        help="Skip languages whose vocabulary sections are already complete",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render prompts and print them; make no API call and no write",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Anthropic model id (default: legesher_i18n.model_config)",
    )
    args = parser.parse_args(argv)

    if not args.languages and not args.all:
        parser.error("pass --languages or --all")

    model = args.model or anthropic_model()
    expected_totals = {
        section: len(slugs_for_section(section)) for section in VOCABULARY_SECTIONS
    }

    with TranslationDatabase(db_path=args.db) as db:
        if args.all:
            languages = [
                row["code"] for row in db.get_languages() if row.get("has_yaml_pack")
            ]
        else:
            languages = list(args.languages)

        skipped_english = SEED_LANGUAGE in languages
        languages = [code for code in languages if code != SEED_LANGUAGE]
        if skipped_english:
            logger.info(
                "Skipping '%s': English vocabulary is seeded from the canonical "
                "inventory (scripts/seed_vocabulary.py), never generated.",
                SEED_LANGUAGE,
            )

        if args.skip_complete:
            coverage = db.get_vocabulary_coverage()
            languages = [
                code for code in languages if coverage.get(code, {}) != expected_totals
            ]

        if not languages:
            logger.info("Nothing to generate.")
            return 0

        total_in = total_out = 0
        failures: dict[str, list[str]] = {}
        written_by_language: dict[str, int] = {}

        for language_code in languages:
            prompt = build_prompt(language_code)
            if args.dry_run:
                print(f"\n{'=' * 70}\n{language_code}\n{'=' * 70}\n{prompt}")
                continue

            logger.info("Generating vocabulary for '%s'…", language_code)
            try:
                text, input_tokens, output_tokens = call_model(prompt, model)
            except RuntimeError:
                raise  # configuration problem: abort the whole run
            except Exception as exc:  # noqa: BLE001 - one language must not end the run
                failures[language_code] = [f"model call failed: {exc}"]
                continue

            total_in += input_tokens
            total_out += output_tokens

            try:
                payload = parse_json_response(text)
            except (ValueError, json.JSONDecodeError) as exc:
                failures[language_code] = [f"unparseable response: {exc}"]
                continue

            values, problems = validate_response(payload)
            if problems:
                failures[language_code] = problems
                logger.warning(
                    "'%s' rejected (%d problem(s)); nothing written for it.",
                    language_code,
                    len(problems),
                )
                continue

            written_by_language[language_code] = write_language(
                db,
                language_code,
                values,
                model_version=model,
                notes=str(payload.get("notes") or ""),
            )
            logger.info(
                "'%s': wrote %d values",
                language_code,
                written_by_language[language_code],
            )

        if args.dry_run:
            print(
                f"\nRendered {len(languages)} prompt(s); nothing sent, nothing written."
            )
            return 0

        print(f"\nGenerated vocabulary for {len(written_by_language)} language(s).")
        print(
            f"Tokens: {total_in} in / {total_out} out — "
            f"{format_cost(cost_for_tokens('anthropic', total_in, total_out))}"
        )
        if failures:
            print(f"\n{len(failures)} language(s) written for NONE of their values:")
            for language_code, problems in sorted(failures.items()):
                print(f"  {language_code}:")
                for problem in problems[:6]:
                    print(f"    - {problem}")
                if len(problems) > 6:
                    print(f"    … and {len(problems) - 6} more")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
