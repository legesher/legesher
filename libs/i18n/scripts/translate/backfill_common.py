"""Shared selection machinery for the per-language backfill scripts.

A language backfill (``backfill_core<NNNN>.py``) owns its seed data and the
mapping from decision flags to values. Everything else is the same for every
language and lives here, so a fix lands once:

  * every combination of the decision flags is checked against the two
    refusals ``set_selected`` can raise (the publish gate, including the
    language's forbidden letters, and the cross-term collision guard) before
    anything is written, so no run and no later flip can stop halfway;
  * every value any branch selects is written as a provenanced candidate row,
    the recommended values included, whichever flags the run was given;
  * selections are set in two passes (clear the changed terms, then set
    them), so a flip that swaps two values never collides with its own
    previous state;
  * the diff against the current selections reads Python rows only.

Seeds are written with their word boundaries (``word_one_word_two``).
:func:`surface` derives the shipped identifier from that separated form, and
the separated form is recorded in each rationale, so the database keeps the
separation whatever surface ships (decision 2026-10-25, CORE-2181).

``backfill_core1644.py`` (uk) and ``backfill_core2478.py`` (sw) predate this
module and carry their own copy; porting them is CORE-2482.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

HERE = Path(__file__).resolve()
I18N_ROOT = HERE.parents[2]  # libs/i18n
sys.path.insert(0, str(I18N_ROOT))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.selection import is_valid_pack_value  # noqa: E402

DB_PATH = I18N_ROOT / "legesher_i18n" / "db" / "translations.db"

#: (category, term, value, word_type, confidence, rationale)
Row = tuple[str, str, str, str, str, str]


def surface(words: str, joiner: str) -> str:
    """The shipped identifier for a separated value.

    ``none`` mirrors how Python spells its own reserved words: the words run
    together (getattr, isinstance). ``underscore`` keeps the separator. A
    dunder keeps its own underscores either way (``__x__``).
    """
    if joiner == "underscore":
        return words
    if words.startswith("__") and words.endswith("__"):
        return "__" + words[2:-2].replace("_", "") + "__"
    return words.replace("_", "")


def separated_note(words: str) -> str:
    """The rationale suffix that records a multi-word value's word boundaries."""
    return f" Separated form: {words}." if "_" in words.strip("_") else ""


def branch_rationale(flags: str, recommended: str, words: str, reasoning: str) -> str:
    """The rationale for a value a flag changes from the recommended one."""
    return (
        f"Branch {flags}: in place of the recommended {recommended!r}."
        f"{separated_note(words)} The recommended value's reasoning: {reasoning}"
    )


def check_target_state(lang: str, wanted: dict[tuple[str, str], str]) -> list[str]:
    """Every reason the chosen values could not all be selected together.

    Mirrors the two refusals ``set_selected`` can raise (the publish gate,
    including the language's forbidden letters, and the cross-term collision
    guard, under which same-name terms such as ``type`` may share a value).
    """
    problems = [
        f"refused by the publish gate: {category} {name} -> {value!r}"
        for (category, name), value in wanted.items()
        if not is_valid_pack_value(name, value, lang)
    ]
    owners: dict[str, set[str]] = {}
    for (_, name), value in wanted.items():
        owners.setdefault(value, set()).add(name)
    problems += [
        f"collision: {value!r} would be selected for {sorted(names)}"
        for value, names in owners.items()
        if len(names) > 1
    ]
    return problems


def run(
    *,
    lang: str,
    selected_by: str,
    model: str,
    description: str,
    flag_choices: dict[str, Sequence[str]],
    resolve: Callable[..., list[Row]],
    argv: Sequence[str] | None = None,
) -> int:
    """Parse the flags and select the language's vocabulary, DB-first.

    ``resolve(**flags)`` returns the rows for one branch, keyed by the flag
    names in ``flag_choices``; the first choice of each flag is its default.
    """
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    for flag, choices in flag_choices.items():
        ap.add_argument(f"--{flag}", choices=list(choices), default=choices[0])
    args = ap.parse_args(argv)

    if not args.db.exists():
        print(
            f"no database at {args.db}; copy it in from the data home first",
            file=sys.stderr,
        )
        return 2
    db = TranslationDatabase(db_path=str(args.db))

    branches = [
        dict(zip(flag_choices, combo))
        for combo in itertools.product(*flag_choices.values())
    ]
    rows = resolve(**{flag: getattr(args, flag) for flag in flag_choices})

    term_ids = {}
    for category, name, *_ in rows:
        term = db.get_term_by_name(name, "python", category=category)
        if term is None or term["category"] != category:
            print(f"missing term row: {category} {name}", file=sys.stderr)
            return 1
        term_ids[(category, name)] = term["id"]

    # set_selected commits per call, so check every branch before writing
    # anything: a refusal mid-pass would leave terms with no selection, or a
    # refused value in the candidate pool, and a later flip must not either.
    problems = []
    for branch in branches:
        found = check_target_state(
            lang, {(c, n): v for c, n, v, *_ in resolve(**branch)}
        )
        problems += [f"[{' '.join(branch.values())}] {p}" for p in found]
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    # Every value any branch selects becomes a candidate row, so each side of
    # every decision is in the pool whichever flags this run was given. One
    # read of the pool per term.
    pool = {
        term_id: {r["translation"] for r in db.get_translations(term_id, lang)}
        for term_id in term_ids.values()
    }
    seen: set[tuple[str, str, str]] = set()
    added = 0
    for branch in branches:
        for category, name, value, word_type, confidence, rationale in resolve(
            **branch
        ):
            if (category, name, value) in seen:
                continue
            seen.add((category, name, value))
            term_id = term_ids[(category, name)]
            if value in pool[term_id]:
                continue
            added += 1
            pool[term_id].add(value)
            if not args.dry_run:
                db.add_translation(
                    term_id=term_id,
                    language_code=lang,
                    translation=value,
                    source="claude",
                    model_version=model,
                    word_type=word_type,
                    confidence=confidence,
                    model_rationale=rationale,
                    created_by=selected_by,
                )

    # Selections in two passes: clear this language's selections for the
    # terms below, then set them, so a branch flip that swaps two values can
    # never trip the collision guard against its own previous state.
    current = {
        (r["term_category"], r["term_name"]): r["translation"]
        for r in db.get_all_selected(language_code=lang)
        if r["programming_language"] == "python"
    }
    wanted = {(c, n): (v, r) for c, n, v, _, _, r in rows}
    changed = {k for k, (v, _) in wanted.items() if current.get(k) != v}
    unchanged = len(wanted) - len(changed)
    if not args.dry_run:
        for key in changed:
            if key in current:
                db.remove_selected(term_ids[key], lang)
        for key in sorted(changed):
            value, rationale = wanted[key]
            db.set_selected(
                term_id=term_ids[key],
                language_code=lang,
                translation=value,
                selected_by=selected_by,
                selection_reason=rationale,
            )

    mode = "dry run, nothing written" if args.dry_run else "written"
    print(
        f"{lang}: {len(wanted)} terms; {added} candidate rows added, "
        f"{len(changed)} selections set, {unchanged} already selected ({mode})"
    )
    return 0
