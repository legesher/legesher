"""Check that each feature story's copied code prints what its page says, as a reader runs it.

For every language variant of a story, the exact text the page's Copy button gives
is saved under the story's file name in an empty directory and run with the
released Legesher, installed the way a reader installs it (uvx, never this
checkout's libs/), on every Python version Legesher supports. Arabic runs first.

The result is docs/stories/<id>/reproduced.json: which Pythons each language's
copied code printed its expected output on. It is written only when the policy
holds: Arabic, English and Spanish match on every Python, and every other
language on at least one. The docs generator folds the record into the story's
page data, and a test fails while any record is missing or out of date.

Usage:
    uv run python docs/scripts/reproduce_stories.py --legesher 0.25.1 [--story ID] [--python 3.10,3.11]

This makes network calls (PyPI, Python downloads through uv); the tests never do.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from generate_snippets import REPO_ROOT, load_packs
from stories import (
    RECORD_FILE,
    Story,
    Variant,
    load_stories,
    runs_on,
    story_variants,
    variants_digest,
)

DOCS = REPO_ROOT / "docs"
EN_PACKS = (
    REPO_ROOT / "libs/i18n/language-packs/python/en/legesher_i18n_python_en/packs"
)
# Languages that must match on every supported Python: Arabic first, then the
# other page languages. Every other language needs at least one match.
FULL_SUPPORT = ("ar", "en", "es")
TIMEOUT_SECONDS = 300

# Known failures: story id -> language -> Python -> the ticket that tracks it.
# A ledgered run may fail without blocking the record; the gate in
# test_story_records.py marks each entry strict-xfail, so it goes red the day
# the bug is fixed and the entry must come out. Never ledger a failure to get
# a page published without a ticket that will fix it.
KNOWN_FAILURES: dict[str, dict[str, dict[str, str]]] = {
    # CPython 3.10 and 3.11 tokenize stops a name at a combining mark, so the
    # engine cannot reverse Arabic keywords with diacritics (finally, print).
    "handle-errors-in-your-words": {"ar": {"3.10": "CORE-2192", "3.11": "CORE-2192"}},
}

Runner = Callable[[list[str], Path, int], "subprocess.CompletedProcess[str]"]


def subprocess_runner(
    cmd: list[str], cwd: Path, timeout: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )


@dataclass(frozen=True)
class RunResult:
    status: str  # "match" | "differs" | "error"
    detail: str


class ReproductionFailed(Exception):
    """A language's copied code did not print its expected output where the policy requires it."""


def supported_pythons(repo_root: Path = REPO_ROOT) -> list[str]:
    """The Python versions Legesher's packs cover: the tiers of the English pack."""
    packs = repo_root / EN_PACKS.relative_to(REPO_ROOT)
    return sorted(
        (p.stem for p in packs.glob("*.yml")),
        key=lambda v: tuple(int(x) for x in v.split(".")),
    )


def run_copy(
    variant: Variant,
    file_name: str,
    python: str,
    legesher: str,
    runner: Runner = subprocess_runner,
) -> RunResult:
    """Run variant.copy_text as file_name with the released Legesher on one Python."""
    cmd = [
        "uvx", "--quiet", "--python", python, "--from", f"legesher=={legesher}",
        "legesher", "run", file_name, "--lang", variant.lang,
    ]  # fmt: skip
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        (cwd / file_name).write_text(variant.copy_text, encoding="utf-8", newline="")
        try:
            proc = runner(cmd, cwd, TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            return RunResult("error", f"no result within {TIMEOUT_SECONDS} seconds")
        except OSError as exc:
            return RunResult("error", str(exc))
    if proc.returncode != 0:
        lines = [line for line in (proc.stderr or "").splitlines() if line.strip()]
        return RunResult(
            "error", lines[-1].strip() if lines else f"exit code {proc.returncode}"
        )
    if proc.stdout != variant.output:
        return RunResult("differs", "printed something other than the expected output")
    return RunResult("match", "")


def _order(variants: dict[str, Variant]) -> list[str]:
    first = [lang for lang in FULL_SUPPORT if lang in variants]
    return first + sorted(lang for lang in variants if lang not in FULL_SUPPORT)


def reproduce_story(
    story: Story,
    variants: dict[str, Variant],
    pythons: list[str],
    legesher: str,
    today: str,
    runner: Runner = subprocess_runner,
    known: dict[str, dict[str, str]] | None = None,
) -> dict | None:
    """Run every variant on every Python and return the record; None for editor stories,
    which print nothing. Raises ReproductionFailed as soon as a language breaks the policy.
    known maps a language to the Pythons (and tickets) on which it may fail without
    breaking the policy; see KNOWN_FAILURES."""
    known = known or {}
    if story.surface == "editor":
        return None
    results: dict[str, dict[str, str]] = {}
    for lang in _order(variants):
        outcomes = {
            python: run_copy(variants[lang], story.file_name, python, legesher, runner)
            for python in pythons
        }
        results[lang] = {python: r.status for python, r in outcomes.items()}
        matched = [python for python, r in outcomes.items() if r.status == "match"]
        excused = known.get(lang, {})
        if lang in FULL_SUPPORT:
            broken = [
                p
                for p, r in outcomes.items()
                if r.status != "match" and p not in excused
            ]
        else:
            broken = [] if matched else list(outcomes)
        if broken:
            detail = "; ".join(
                f"{python}: {r.status}" + (f" ({r.detail})" if r.detail else "")
                for python, r in outcomes.items()
                if python in broken
            )
            need = "every Python" if lang in FULL_SUPPORT else "at least one Python"
            raise ReproductionFailed(
                f"stories/{story.id}: {lang} must match on {need}; {detail}"
            )
        print(f"{story.id} {lang}: runs on {', '.join(matched)}", flush=True)
    return {
        "story": story.id,
        "legesher": legesher,
        "checked": today,
        "digest": variants_digest(variants),
        "python": list(pythons),
        "results": results,
    }


def main(
    argv: list[str] | None = None,
    runner: Runner = subprocess_runner,
    today: str | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--legesher",
        required=True,
        help="released legesher version to install, e.g. 0.25.1",
    )
    parser.add_argument("--story", help="only this story id")
    parser.add_argument(
        "--python", help="comma-separated Pythons (default: every supported one)"
    )
    parser.add_argument("--stories", type=Path, default=DOCS / "stories")
    args = parser.parse_args(argv)
    pythons = args.python.split(",") if args.python else supported_pythons()
    today = today or datetime.date.today().isoformat()

    stories = [s for s in load_stories(args.stories) if args.story in (None, s.id)]
    if not stories:
        print(
            f"error: no story {args.story or ''} under {args.stories}", file=sys.stderr
        )
        return 1
    bundles = load_packs()
    for story in stories:
        try:
            record = reproduce_story(
                story,
                story_variants(story, bundles),
                pythons,
                args.legesher,
                today,
                runner,
                KNOWN_FAILURES.get(story.id),
            )
        except ReproductionFailed as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if record is None:
            print(f"{story.id}: editor story, nothing to run")
            continue
        (story.path / RECORD_FILE).write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        partial = {lang: runs_on(record, lang) for lang in record["results"]}
        partial = {lang: on for lang, on in partial.items() if on != pythons}
        note = f"; partial: {partial}" if partial else ""
        print(f"{story.id}: wrote {RECORD_FILE}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
