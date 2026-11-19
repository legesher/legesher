"""The gate: every runnable story has a reproduction record that meets the policy.

The record (docs/stories/<id>/reproduced.json) comes from reproduce_stories.py, which
runs each language's copied code with the released Legesher. These tests make no
network calls; they fail when a record is missing, or when it shows Arabic, English
or Spanish failing on a Python (unless ledgered in KNOWN_FAILURES with a ticket, as
strict xfail) or any language matching nowhere.

A language whose copy text or expected output changed since the run (a pack change,
say) is not a failure: only the next release can be run on the new text, so a pull
request could never fix it. The page data drops that language's results (see
story_payload) and this file warns, naming the languages and the re-run to do once
the change is released.
"""

import sys
import warnings
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
from generate_snippets import load_packs  # noqa: E402
from reproduce_stories import FULL_SUPPORT, KNOWN_FAILURES, supported_pythons  # noqa: E402
from stories import (  # noqa: E402
    load_stories,
    read_record,
    runs_on,
    story_variants,
    unchecked_languages,
)

RUNNABLE = [
    s for s in load_stories(REPO_ROOT / "docs" / "stories") if s.surface != "editor"
]
RERUN = "re-run: uv run python docs/scripts/reproduce_stories.py --legesher <released version> --story {id}"


@pytest.fixture(scope="module")
def bundles():
    return load_packs()


@pytest.mark.parametrize("story", RUNNABLE, ids=lambda s: s.id)
def test_story_has_a_record(story, bundles):
    record = read_record(story)
    assert record is not None, (
        f"stories/{story.id}: no reproduced.json; " + RERUN.format(id=story.id)
    )
    unchecked = unchecked_languages(record, story_variants(story, bundles))
    if unchecked or record["python"] != supported_pythons(REPO_ROOT):
        warnings.warn(
            f"stories/{story.id}: not checked against the current text or Pythons "
            f"({', '.join(unchecked) or 'Python list'}); the page shows no result for "
            "them until the next release is run; " + RERUN.format(id=story.id),
            stacklevel=1,
        )


def _full_support_cases():
    """(story, lang, python) for every page language on every supported Python; a
    ledgered known failure is strict-xfail with its ticket, so it fails once fixed."""
    cases = []
    for story in RUNNABLE:
        ledger = KNOWN_FAILURES.get(story.id, {})
        for lang in FULL_SUPPORT:
            for python in supported_pythons(REPO_ROOT):
                ticket = ledger.get(lang, {}).get(python)
                marks = (
                    [pytest.mark.xfail(strict=True, reason=f"{ticket}: known failure")]
                    if ticket
                    else []
                )
                cases.append(
                    pytest.param(
                        story,
                        lang,
                        python,
                        marks=marks,
                        id=f"{story.id}-{lang}-{python}",
                    )
                )
    return cases


@pytest.mark.parametrize(("story", "lang", "python"), _full_support_cases())
def test_page_language_matches_on_every_python(story, lang, python):
    record = read_record(story)
    assert record is not None, f"stories/{story.id}: no reproduced.json"
    status = record["results"].get(lang, {}).get(python)
    assert status == "match", (
        f"stories/{story.id}: {lang} on Python {python} is {status}"
    )


@pytest.mark.parametrize("story", RUNNABLE, ids=lambda s: s.id)
def test_every_language_matches_somewhere(story):
    record = read_record(story)
    assert record is not None, f"stories/{story.id}: no reproduced.json"
    nowhere = sorted(lang for lang in record["results"] if not runs_on(record, lang))
    assert not nowhere, (
        f"stories/{story.id}: matches on no Python: {', '.join(nowhere)}"
    )
