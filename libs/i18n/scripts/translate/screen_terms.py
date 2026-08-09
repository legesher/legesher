#!/usr/bin/env python
"""Term-screening sweep harness — offensive/unfortunate translations (CORE-401).

Screens every translated term across all pack sections for profanity,
slurs, and unfortunate collisions/connotations in the target language.
The screening itself is LLM-based (linguist framing, CORE-1305; prompt in
``prompts/term_screening_prompt.md``); this harness is the deterministic
scaffolding around it:

* ``--collect`` — emit the per-language term inventory as JSON, including a
  ``coverage_digest`` (sha256 over the sorted term surface). This is the
  screener's input; any capable multilingual LLM run with the prompt
  template produces a report file from it.
* Reports live at ``libs/i18n/reports/term-screening/<lang>.yml`` and embed
  the ``coverage_digest`` of the surface they screened.
* Triage lives at ``scripts/translate/term_screening_triage.yml``: every
  flag is either ``fixed`` (at the DB layer, per CORE-1400, then
  re-exported) or ``accepted`` with a rationale. Flag, don't auto-rewrite.
* ``--gate`` — the mechanical release gate (no LLM involved): every shipped
  language must have a report, the report's digest must match the current
  pack surface (a pack edit or regen invalidates the screen — this is how
  the 103 batch inherits screening at birth, CORE-674), and every flag must
  be triaged. Exits non-zero on any error. Stale triage entries (flags that
  no longer exist) are warnings.

Usage::

    python screen_terms.py --collect --lang es          # screener input
    python screen_terms.py --gate                       # release gate, all langs
    python screen_terms.py --gate --lang si             # per-new-pack gate step
    python screen_terms.py                              # summary report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

# Pack sections holding translated identifier surfaces — the schema's
# inventory, not a copy (post-merge review finding, 2026-08-09).
from legesher_i18n.schema_validator import TRANSLATION_SECTIONS as PARTITIONS

# Path to language packs (mirrors find_untranslated.py)
LANGUAGE_PACKS_DIR = Path(__file__).parent.parent.parent / "language-packs" / "python"

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports" / "term-screening"

TRIAGE_PATH = Path(__file__).parent / "term_screening_triage.yml"

# English is the reference surface, not a translation — never screened.
SKIP_LANGUAGES = {"en"}

FLAG_CATEGORIES = {
    "profanity",
    "slur",
    "sexual",
    "scatological",
    "unfortunate_connotation",
    "embarrassing_collision",
}

DISPOSITIONS = {"fixed", "accepted"}

_REQUIRED_REPORT_KEYS = {
    "language",
    "screener",
    "screened_at",
    "coverage_digest",
    "flags",
}

_REQUIRED_FLAG_KEYS = {"term", "english", "partition", "category", "note"}

Triple = tuple[str, str, str]  # (partition, english, localized)


def collect_terms(
    packs_dir: Path, lang_filter: str | None = None
) -> dict[str, list[Triple]]:
    """Collect the screened term surface per language.

    Unions ``(partition, english, localized)`` triples across every version
    file of a language's pack — the screen covers every surface a shipped
    pack can render, regardless of interpreter version.
    """
    surfaces: dict[str, set[Triple]] = {}
    for pack_file in sorted(packs_dir.glob("*/legesher_i18n_python_*/packs/*.yml")):
        lang = pack_file.parents[2].name
        if lang in SKIP_LANGUAGES:
            continue
        if lang_filter and lang != lang_filter:
            continue
        with open(pack_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            continue
        triples = surfaces.setdefault(lang, set())
        for partition in PARTITIONS:
            section = data.get(partition)
            if not isinstance(section, dict):
                continue
            for english, localized in section.items():
                if isinstance(english, str) and isinstance(localized, str):
                    triples.add((partition, english, localized))
    return {lang: sorted(triples) for lang, triples in surfaces.items()}


def coverage_digest(terms: list[Triple]) -> str:
    """sha256 over the sorted term surface; order-independent."""
    canonical = "\n".join("\x1f".join(triple) for triple in sorted(terms))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def flag_key(lang: str, partition: str, english: str, term: str) -> str:
    """Triage key for a flag: ``<lang>:<partition>:<english>:<term>``.

    The localized surface is part of the key on purpose: a regen can
    replace a flagged term with a *different* offensive word, and an
    acceptance recorded for the old surface must not green-light the new
    one — the new flag must arrive untriaged (post-merge review finding,
    2026-08-09). The superseded entry then surfaces as a stale-triage
    warning for pruning.
    """
    return f"{lang}:{partition}:{english}:{term}"


def load_report(path: Path) -> dict:
    """Load and validate one screening report; SystemExit on malformed."""
    try:
        with open(path, encoding="utf-8") as f:
            report = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Malformed screening report {path}: {exc}") from exc
    if not isinstance(report, dict) or not _REQUIRED_REPORT_KEYS <= set(report):
        raise SystemExit(
            f"Malformed screening report {path}: required keys "
            f"{sorted(_REQUIRED_REPORT_KEYS)}"
        )
    flags = report["flags"]
    if flags is None:
        flags = report["flags"] = []
    if not isinstance(flags, list):
        raise SystemExit(f"Malformed screening report {path}: 'flags' must be a list")
    for flag in flags:
        if not isinstance(flag, dict) or not _REQUIRED_FLAG_KEYS <= set(flag):
            raise SystemExit(
                f"Malformed flag in {path}: required keys "
                f"{sorted(_REQUIRED_FLAG_KEYS)}, got {flag!r}"
            )
        if flag["category"] not in FLAG_CATEGORIES:
            raise SystemExit(
                f"Unknown flag category {flag['category']!r} in {path}; "
                f"allowed: {sorted(FLAG_CATEGORIES)}"
            )
    return report


def load_triage(path: Path) -> dict[str, dict]:
    """Load the triage ledger; SystemExit on malformed entries."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Malformed triage file {path}: expected a mapping")
    for key, entry in data.items():
        if (
            not isinstance(entry, dict)
            or entry.get("disposition") not in DISPOSITIONS
            or not str(entry.get("rationale", "")).strip()
        ):
            raise SystemExit(
                f"Malformed triage entry {key!r} in {path}: needs "
                f"disposition in {sorted(DISPOSITIONS)} and a rationale"
            )
    return data


def gate(
    packs_dir: Path,
    reports_dir: Path,
    triage_path: Path,
    lang_filter: str | None = None,
) -> tuple[list[str], list[str]]:
    """Run the mechanical release gate. Returns (errors, warnings)."""
    surfaces = collect_terms(packs_dir, lang_filter)
    triage = load_triage(triage_path)
    errors: list[str] = []
    warnings: list[str] = []
    live_flag_keys: set[str] = set()

    for lang, terms in sorted(surfaces.items()):
        report_path = reports_dir / f"{lang}.yml"
        if not report_path.exists():
            errors.append(
                f"{lang}: no screening report at {report_path} — language is "
                "unscreened (CORE-401)"
            )
            continue
        report = load_report(report_path)
        current = coverage_digest(terms)
        if report["coverage_digest"] != current:
            errors.append(
                f"{lang}: screening report is stale — pack surface changed "
                f"since the screen (digest {report['coverage_digest'][:12]}… "
                f"vs current {current[:12]}…). Re-run the screen (CORE-401)."
            )
        for flag in report["flags"]:
            key = flag_key(lang, flag["partition"], flag["english"], flag["term"])
            live_flag_keys.add(key)
            if key not in triage:
                errors.append(
                    f"{lang}: untriaged flag {key} "
                    f"('{flag['term']}', {flag['category']}) — every flag "
                    "must be fixed at the DB layer or accepted with "
                    "rationale (CORE-401)"
                )

    prefixes = tuple(f"{lang}:" for lang in surfaces)
    for key in sorted(triage):
        if key.startswith(prefixes) and key not in live_flag_keys:
            warnings.append(
                f"stale triage entry {key}: no current flag matches "
                "(translation changed or flag cleared) — prune when convenient"
            )
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 == clean)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collect", action="store_true", help="Emit screener input JSON"
    )
    parser.add_argument("--gate", action="store_true", help="Run the release gate")
    parser.add_argument("--lang", default=None, help="Limit to one language code")
    parser.add_argument("--packs-dir", type=Path, default=LANGUAGE_PACKS_DIR)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--triage", type=Path, default=TRIAGE_PATH)
    parser.add_argument("--quiet", action="store_true", help="Summary only")
    args = parser.parse_args(argv)

    if args.collect:
        payload = {
            lang: {
                "coverage_digest": coverage_digest(terms),
                "terms": [
                    {"partition": p, "english": en, "term": loc} for p, en, loc in terms
                ],
            }
            for lang, terms in collect_terms(args.packs_dir, args.lang).items()
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    errors, warnings = gate(args.packs_dir, args.reports_dir, args.triage, args.lang)
    if not args.quiet:
        for error in errors:
            print(f"  [error] {error}")
        for warning in warnings:
            print(f"  [warning] {warning}")
    print("\n--- Term-screening summary (CORE-401) ---")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if args.gate:
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
