#!/usr/bin/env python3
"""Generate localized error-message templates for a locale (CORE-1881).

The message-template side of the corpus (``message_templates`` /
``message_translations``) is the second data class: **sentences with
grammar and ``{slot}`` placeholders, not identifiers** — so the term lane
does not carry over. This lane mirrors the term lane's contract (budget,
dry-run, DB store) with message-specific machinery:

* **Placeholder-preserving prompts.** The prompt states the mechanical
  contract: every ``{slot}`` must survive translation byte-for-byte —
  never translated, renamed, or dropped. A slot may MOVE within the
  sentence as the language's grammar requires: slots are named, and the
  renderer substitutes by name, so position is free (the "reorder" failure
  class belongs to positional systems; see ``prompts/messages_prompt.md``).
* **Mechanical validation, not review.** Every suggestion is written
  through ``scripts/add_message_locale.py``'s :func:`add_locale`, so
  placeholder parity (the Scratch-style CI gate, per the CORE-1356
  prior-art review), bidi hygiene, all-or-nothing coverage, idempotence,
  and provenance are enforced by the same code for every writer. A locale
  with ANY invalid rendering writes nothing — a half-written locale is the
  state the coverage rule exists to prevent.
* **Provenance per rendering** (CORE-1881): rows carry
  ``source='claude_agent'``, the model id, and this script's name, at the
  ``machine`` review rung. Review posture is the standing policy:
  best-effort native and non-blocking; the gate blocks on mechanical
  errors only.
* **One call per locale.** 55 short sentences fit one response;
  a per-message call is the economics leak (CORE-1805).
* **English is never generated** — ``template_en`` IS the English surface.
* **Nothing is published.** ``message_translations`` stays outside the HF
  one-way door until content-addressed keys (CORE-1565) land.

Requires ``ANTHROPIC_API_KEY`` for real runs; ``--dry-run`` renders the
prompts and writes nothing.

Usage:
    # inspect the prompts, spend nothing
    python scripts/translate/generate_messages.py --db <db> --locales fr am --dry-run

    # generate for two locales
    python scripts/translate/generate_messages.py --db <db> --locales fr am

    # every pack language that has no message translations yet
    python scripts/translate/generate_messages.py --db <db> --all-missing

Afterwards: the durable-home push (libs/i18n/CLAUDE.md, "Durable home &
sync ritual").
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))
sys.path.insert(0, str(_SCRIPT_DIR.parent))

from legesher_i18n.api.rates import cost_for_tokens, format_cost  # noqa: E402
from legesher_i18n.model_config import anthropic_model  # noqa: E402

try:  # imported as part of the `scripts.translate` package (tests)
    from ..add_message_locale import add_locale
except ImportError:  # run as a script: scripts/ was put on sys.path above
    from add_message_locale import add_locale  # noqa: E402

try:  # imported as part of the `scripts.translate` package (tests)
    from .generate_vocabulary import (
        call_model,
        parse_json_response,
        render_style_profile,
    )
except ImportError:  # run as a script
    from generate_vocabulary import (  # noqa: E402
        call_model,
        parse_json_response,
        render_style_profile,
    )

logger = logging.getLogger(__name__)

#: Provenance label — the ``selection.SOURCE_TRUST`` ``claude_agent`` rung:
#: linguist-framed agent output, above single-shot ``claude``.
SOURCE = "claude_agent"

#: The language whose messages are definitional (``template_en``).
SEED_LANGUAGE = "en"

CREATED_BY = "generate_messages.py"


def identity_id(template: dict) -> str:
    """The prompt/response id of one template row: ``key@version_added``."""
    return f"{template['key']}@{template['version_added'] or ''}"


def load_templates(connection: sqlite3.Connection, implementation: str) -> list[dict]:
    """The implementation's template rows, placeholders parsed."""
    rows = connection.execute(
        "SELECT key, version_added, template_en, placeholders "
        "FROM message_templates WHERE implementation = ? ORDER BY id",
        (implementation,),
    ).fetchall()
    return [
        {
            "key": key,
            "version_added": version_added,
            "template_en": template_en,
            "placeholders": json.loads(placeholders_json or "[]"),
        }
        for key, version_added, template_en, placeholders_json in rows
    ]


def render_template_inventory(templates: list[dict]) -> str:
    """The template table as prompt text, ids included."""
    lines = ["| id | English template | placeholders |", "| --- | --- | --- |"]
    for t in templates:
        slots = ", ".join(f"`{{{p['name']}}}`" for p in t["placeholders"]) or "(none)"
        template_en = t["template_en"].replace("|", "\\|") or "(empty message)"
        lines.append(f"| {identity_id(t)} | {template_en} | {slots} |")
    return "\n".join(lines)


def build_prompt(
    locale: str, language_name: str, native_name: str, templates: list[dict]
) -> str:
    """The placeholder-preserving prompt for one locale.

    The inventory is generated from the database rows, so the prompt cannot
    ask for an id the validator will not accept, nor omit one the coverage
    rule requires. Spec: ``prompts/messages_prompt.md``.
    """
    return f"""[[locale:{locale}]]
You are localizing Python error messages for people learning to program \
who read their tracebacks in {language_name} ({native_name}). These are \
the actual sentences a learner sees when their program fails, so clarity \
for a beginner outranks literal fidelity to the English wording.

## The mechanical contract (checked by machine, not negotiable)

- Every `{{slot}}` placeholder must survive EXACTLY as written — the same \
braces, the same English slot name, byte-for-byte. Never translate a slot \
name, never rename it, never drop it. `{{name}}` stays `{{name}}`, even in \
Arabic script, even mid-sentence.
- You MAY move a placeholder to wherever the sentence's grammar needs it. \
Slots are substituted by name, so their order is free.
- Any brace character that is NOT one of the listed placeholders is \
literal text (some messages talk about braces); keep it verbatim.
- Plain text only: no directional control characters (LRM, RLM, isolates, \
embeddings) — display isolation is handled at render time, not in the \
stored string.
- An empty English template means "this message has no text"; return an \
empty string for it.

## Register

Neutral, clear, and idiomatic for a beginner reading an error. Keep the \
technical meaning exact. Exception class names (like ZeroDivisionError) \
are NOT part of these templates — translate only the message text given.

## The templates

{render_template_inventory(templates)}

## Script and formatting profile for {language_name}

{render_style_profile(locale)}

## Output format

Return ONE JSON object and nothing else:

{{
  "translations": {{"<id>": "<template in {language_name}>", ...}},
  "notes": "<2-3 sentences: which renderings you were least sure of>"
}}

Every id listed above must appear exactly once. Do not add ids that were \
not listed.
"""


def compose_addition(
    implementation: str,
    locale: str,
    model: str,
    payload: dict,
    templates: list[dict],
) -> tuple[dict, list[str]]:
    """Turn a model payload into an ``add_locale`` addition.

    Returns ``(addition, problems)``; the addition is only meaningful when
    ``problems`` is empty. Structural checks happen here (every id exactly
    once, values are strings); the content gates (placeholder parity, bidi,
    coverage against the database) belong to :func:`add_locale` and are not
    duplicated.
    """
    problems: list[str] = []
    suggested = payload.get("translations")
    if not isinstance(suggested, dict):
        return {}, ["response has no 'translations' object"]

    by_id = {identity_id(t): t for t in templates}
    missing = [i for i in by_id if i not in suggested]
    unknown = sorted(set(suggested) - set(by_id))
    if missing:
        problems.append(f"missing {len(missing)} id(s): {missing[:5]}")
    if unknown:
        problems.append(f"unknown id(s): {unknown[:5]}")

    entries = []
    for id_, template in by_id.items():
        value = suggested.get(id_)
        if value is None:
            continue
        if not isinstance(value, str):
            problems.append(f"{id_}: value is not a string ({value!r})")
            continue
        entries.append(
            {
                "key": template["key"],
                "version_added": template["version_added"],
                "template": value,
            }
        )

    addition = {
        "implementation": implementation,
        "locale": locale,
        "source": SOURCE,
        "model_version": model,
        "created_by": CREATED_BY,
        "translations": entries,
    }
    return addition, problems


def _locale_names(connection: sqlite3.Connection) -> dict[str, tuple[str, str]]:
    return {
        code: (name, native or name)
        for code, name, native in connection.execute(
            "SELECT code, name, native_name FROM languages"
        )
    }


def run_lane(
    db_path: Path,
    *,
    locales: list[str] | None,
    model: str,
    call=call_model,
    implementation: str = "cpython",
    dry_run: bool = False,
    max_budget: float | None = 20.0,
) -> tuple[dict[str, int], dict[str, list[str]], list[str]]:
    """Generate and store message translations for the requested locales.

    Args:
        locales: Explicit locale list, or ``None`` for every pack language
            that has no message translations yet.
        call: The model-call function (injected in tests); the
            ``call_model`` contract — ``(prompt, model) -> (text, in, out)``.
        max_budget: USD ceiling, or ``None`` to run without one (the CLI's
            ``--no-budget``). Checked before each call against the spend so
            far; the lane stops requesting once reached. A ceiling that
            cannot be measured is refused up front: enforcing it needs
            configured rates (``LEGESHER_RATE_ANTHROPIC_*`` /
            ``LEGESHER_RATES_FILE``), and a guard that silently cannot
            measure is worse than none.

    Returns:
        ``(written_by_locale, failures_by_locale, skipped)``. A locale
        appears in exactly one of the three.
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        templates = load_templates(connection, implementation)
        if not templates:
            raise SystemExit(
                f"no message_templates rows for {implementation!r} in {db_path}"
            )
        populated = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT tr.locale FROM message_translations tr "
                "JOIN message_templates t ON t.id = tr.template_id "
                "WHERE t.implementation = ?",
                (implementation,),
            )
        }
        names = _locale_names(connection)
        if locales is None:
            # The per-locale loop is the single authority on skipping (the
            # seed language and populated locales land in `skipped` either way)
            candidates = [
                row[0]
                for row in connection.execute(
                    "SELECT code FROM languages WHERE has_yaml_pack ORDER BY code"
                )
            ]
        else:
            candidates = list(locales)
    finally:
        connection.close()

    def assert_budget_measurable() -> None:
        """Fail loud before the FIRST real call, not before a call-free run.

        An enforced ceiling that cannot be measured is worse than none —
        but a run where every locale is skipped spends nothing and needs
        no rates.
        """
        if cost_for_tokens("anthropic", 1, 1) is None:
            raise SystemExit(
                "cost rates are not configured, so --max-budget cannot be "
                "enforced — set LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK and "
                "LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK (or "
                "LEGESHER_RATES_FILE), or pass --no-budget to waive the "
                "ceiling explicitly"
            )

    written: dict[str, int] = {}
    failures: dict[str, list[str]] = {}
    skipped: list[str] = []
    total_in = total_out = 0

    for locale in candidates:
        if locale == SEED_LANGUAGE:
            skipped.append(locale)
            logger.info(
                "Skipping '%s': template_en IS the English surface; "
                "it is never generated.",
                locale,
            )
            continue
        if locale in populated:
            skipped.append(locale)
            logger.info(
                "Skipping '%s': it already carries message translations "
                "for %r (revisions are not locale additions).",
                locale,
                implementation,
            )
            continue

        language_name, native_name = names.get(locale, (locale, locale))
        prompt = build_prompt(locale, language_name, native_name, templates)
        if dry_run:
            print(f"\n{'=' * 70}\n{locale}\n{'=' * 70}\n{prompt}")
            continue

        if max_budget is not None:
            assert_budget_measurable()
            spent = cost_for_tokens("anthropic", total_in, total_out)
            if spent >= max_budget:
                failures[locale] = [
                    f"budget reached ({format_cost(spent)} of "
                    f"{format_cost(max_budget)}) before this locale; "
                    "not requested"
                ]
                continue

        logger.info("Generating messages for '%s'…", locale)
        try:
            text, input_tokens, output_tokens = call(prompt, model)
        except RuntimeError:
            raise  # configuration problem: abort the whole run
        except Exception as exc:  # noqa: BLE001 — one locale must not end the run
            failures[locale] = [f"model call failed: {exc}"]
            continue
        total_in += input_tokens
        total_out += output_tokens

        try:
            payload = parse_json_response(text)
        except (ValueError, json.JSONDecodeError) as exc:
            failures[locale] = [f"unparseable response: {exc}"]
            continue

        addition, problems = compose_addition(
            implementation, locale, model, payload, templates
        )
        if problems:
            failures[locale] = problems
            continue

        try:
            written[locale] = add_locale(db_path, addition)
        except SystemExit as exc:
            # add_locale is the mechanical gate: placeholder parity, bidi,
            # coverage, provenance. Nothing was written for this locale.
            failures[locale] = [str(exc)]
            continue

    if not dry_run:
        print(
            f"\nGenerated messages for {len(written)} locale(s); "
            f"{len(skipped)} skipped."
        )
        print(
            f"Tokens: {total_in} in / {total_out} out — "
            f"{format_cost(cost_for_tokens('anthropic', total_in, total_out))}"
        )
        for locale, problems in sorted(failures.items()):
            print(f"  {locale}: NOTHING written —")
            for problem in problems[:4]:
                print(f"    - {problem}")
            if len(problems) > 4:
                print(f"    … and {len(problems) - 4} more")
    return written, failures, skipped


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db", type=Path, required=True, help="translations database to write"
    )
    parser.add_argument("--locales", nargs="+", help="locale codes to generate")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="every pack language with no message translations yet",
    )
    parser.add_argument(
        "--implementation", default="cpython", help="message_templates.implementation"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Anthropic model id (default: legesher_i18n.model_config)",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        default=20.0,
        help="USD ceiling for the run (default 20); needs configured rates",
    )
    parser.add_argument(
        "--no-budget",
        action="store_true",
        help="run without a cost ceiling (explicit waiver)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="render prompts and print them; no API call, no write",
    )
    args = parser.parse_args(argv)

    if bool(args.locales) == args.all_missing:
        parser.error("pass exactly one of --locales or --all-missing")
    if not args.db.exists():
        raise SystemExit(f"database not found: {args.db}")

    written, failures, _ = run_lane(
        args.db,
        locales=None if args.all_missing else list(args.locales),
        model=args.model or anthropic_model(),
        implementation=args.implementation,
        dry_run=args.dry_run,
        max_budget=None if args.no_budget else args.max_budget,
    )
    if not args.dry_run and written:
        print(
            "\nRemember the durable-home push (libs/i18n/CLAUDE.md, "
            "'Durable home & sync ritual')."
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
