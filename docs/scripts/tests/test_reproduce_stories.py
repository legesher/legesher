import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "tests"))
from _story_fixtures import FIXTURES, copy_story  # noqa: E402
from generate_snippets import load_packs  # noqa: E402
from reproduce_stories import (  # noqa: E402
    ReproductionFailed,
    main,
    reproduce_story,
    run_copy,
    supported_pythons,
)
from stories import load_story, runs_on, story_variants, variants_digest  # noqa: E402

PYTHONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@pytest.fixture(scope="module")
def story():
    return load_story(FIXTURES / "ok-playground")


@pytest.fixture(scope="module")
def variants(story):
    return story_variants(story, load_packs())


def fake(variants, differs=None, errors=None, calls=None):
    """A runner that prints each variant's expected output, except where told not to.

    differs/errors map a language to the Pythons on which it prints something else
    or exits 1. calls collects (lang, python) in call order."""
    differs, errors = differs or {}, errors or {}

    def runner(cmd, cwd, timeout):
        python, lang = cmd[3], cmd[-1]
        if calls is not None:
            calls.append((lang, python))
        if python in errors.get(lang, ()):
            return subprocess.CompletedProcess(
                cmd, 1, "", "Traceback ...\nNameError: name 'x' is not defined\n"
            )
        out = (
            "something else\n"
            if python in differs.get(lang, ())
            else variants[lang].output
        )
        return subprocess.CompletedProcess(cmd, 0, out, "")

    return runner


def never_called(cmd, cwd, timeout):
    raise AssertionError("the runner must not be called")


def test_supported_pythons_reads_the_en_pack_tiers():
    pythons = supported_pythons(REPO_ROOT)
    assert (
        pythons[0] == "3.10"
        and "3.14" in pythons
        and pythons == sorted(pythons, key=lambda v: tuple(map(int, v.split("."))))
    )


def test_command_is_the_reader_install(variants):
    seen = []

    def recording(cmd, cwd, timeout):
        seen.append(
            (cmd, (Path(cwd) / "divide.py").read_text(encoding="utf-8"), timeout)
        )
        return subprocess.CompletedProcess(cmd, 0, variants["ar"].output, "")

    result = run_copy(variants["ar"], "divide.py", "3.14", "0.25.1", runner=recording)
    assert result.status == "match"
    cmd, written, timeout = seen[0]
    assert cmd == [
        "uvx",
        "--quiet",
        "--python",
        "3.14",
        "--from",
        "legesher==0.25.1",
        "legesher",
        "run",
        "divide.py",
        "--lang",
        "ar",
    ]
    assert written == variants["ar"].copy_text and timeout == 300


def test_match_needs_exactly_the_expected_output(variants):
    extra = run_copy(
        variants["ar"],
        "divide.py",
        "3.14",
        "0.25.1",
        runner=lambda cmd, cwd, t: subprocess.CompletedProcess(
            cmd, 0, variants["ar"].output + "\n", ""
        ),
    )
    assert extra.status == "differs"


def test_nonzero_exit_is_an_error_with_the_last_stderr_line(variants):
    result = run_copy(
        variants["si"],
        "divide.py",
        "3.14",
        "0.25.1",
        runner=fake(variants, errors={"si": {"3.14"}}),
    )
    assert (
        result.status == "error"
        and result.detail == "NameError: name 'x' is not defined"
    )


def test_timeout_is_an_error(variants):
    def slow(cmd, cwd, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    assert (
        run_copy(variants["ar"], "divide.py", "3.14", "0.25.1", runner=slow).status
        == "error"
    )


def test_arabic_runs_first_on_every_python(story, variants):
    calls = []
    reproduce_story(
        story,
        variants,
        PYTHONS,
        "0.25.1",
        "2026-11-17",
        runner=fake(variants, calls=calls),
    )
    assert calls[: len(PYTHONS)] == [("ar", p) for p in PYTHONS]
    assert [lang for lang, _ in calls[len(PYTHONS) :: len(PYTHONS)]][:2] == ["en", "es"]


def test_arabic_failure_stops_before_any_other_language(story, variants):
    calls = []
    with pytest.raises(ReproductionFailed, match=r"ar.*3\.11"):
        reproduce_story(
            story,
            variants,
            PYTHONS,
            "0.25.1",
            "2026-11-17",
            runner=fake(variants, differs={"ar": {"3.11"}}, calls=calls),
        )
    assert {lang for lang, _ in calls} == {"ar"}


def test_partial_support_fails_for_page_languages(story, variants):
    with pytest.raises(ReproductionFailed, match=r"\bes\b.*3\.13"):
        reproduce_story(
            story,
            variants,
            PYTHONS,
            "0.25.1",
            "2026-11-17",
            runner=fake(variants, errors={"es": {"3.13"}}),
        )


def test_partial_support_is_recorded_for_other_languages(story, variants):
    rec = reproduce_story(
        story,
        variants,
        PYTHONS,
        "0.25.1",
        "2026-11-17",
        runner=fake(variants, errors={"si": {"3.13", "3.14"}}),
    )
    assert (
        runs_on(rec, "si") == ["3.10", "3.11", "3.12"] and runs_on(rec, "ar") == PYTHONS
    )
    assert rec["results"]["si"]["3.13"] == "error"


def test_language_matching_nowhere_fails(story, variants):
    with pytest.raises(ReproductionFailed, match=r"\bhi\b"):
        reproduce_story(
            story,
            variants,
            PYTHONS,
            "0.25.1",
            "2026-11-17",
            runner=fake(variants, differs={"hi": set(PYTHONS)}),
        )


def test_record_shape(story, variants):
    rec = reproduce_story(
        story, variants, PYTHONS, "0.25.1", "2026-11-17", runner=fake(variants)
    )
    assert (
        rec["story"] == story.id
        and rec["legesher"] == "0.25.1"
        and rec["checked"] == "2026-11-17"
    )
    assert rec["python"] == PYTHONS and rec["digest"] == variants_digest(variants)
    assert set(rec["results"]) == set(variants)


def test_editor_story_is_skipped():
    editor = load_story(FIXTURES / "ok-editor")
    assert (
        reproduce_story(
            editor, {}, PYTHONS, "0.25.1", "2026-11-17", runner=never_called
        )
        is None
    )


def test_cli_writes_the_record_on_success(tmp_path, variants):
    d = copy_story(tmp_path, "ok-playground")
    code = main(
        [
            "--legesher",
            "0.25.1",
            "--stories",
            str(tmp_path),
            "--python",
            ",".join(PYTHONS),
        ],
        runner=fake(variants),
        today="2026-11-17",
    )
    assert code == 0
    text = (d / "reproduced.json").read_text(encoding="utf-8")
    assert text.endswith("\n") and json.loads(text)["checked"] == "2026-11-17"
    assert list(json.loads(text)) == sorted(json.loads(text))


def test_runner_failure_writes_no_record(tmp_path):
    d = copy_story(tmp_path, "no-uvx")

    def missing(cmd, cwd, timeout):
        raise OSError("uvx not found")

    code = main(
        ["--legesher", "0.25.1", "--stories", str(tmp_path)],
        runner=missing,
        today="2026-11-17",
    )
    assert code == 1 and not (d / "reproduced.json").exists()


def test_cli_story_filter_and_editor_stories(tmp_path, variants):
    copy_story(tmp_path, "ok-editor", source="ok-editor")
    other = copy_story(tmp_path, "other")
    code = main(
        ["--legesher", "0.25.1", "--stories", str(tmp_path), "--story", "ok-editor"],
        runner=never_called,
        today="2026-11-17",
    )
    assert code == 0 and not (other / "reproduced.json").exists()
    assert not (tmp_path / "ok-editor" / "reproduced.json").exists()


ARABIC_ON_OLD_PYTHONS = {"ar": {"3.10": "CORE-2192", "3.11": "CORE-2192"}}


def test_ledgered_failure_does_not_block_the_record(story, variants):
    rec = reproduce_story(
        story,
        variants,
        PYTHONS,
        "0.25.1",
        "2026-11-17",
        runner=fake(variants, errors={"ar": {"3.10", "3.11"}}),
        known=ARABIC_ON_OLD_PYTHONS,
    )
    assert runs_on(rec, "ar") == ["3.12", "3.13", "3.14"]
    assert rec["results"]["ar"]["3.10"] == "error"


def test_unledgered_arabic_failure_still_stops(story, variants):
    calls = []
    with pytest.raises(ReproductionFailed, match=r"ar.*3\.12"):
        reproduce_story(
            story,
            variants,
            PYTHONS,
            "0.25.1",
            "2026-11-17",
            runner=fake(variants, errors={"ar": {"3.10", "3.12"}}, calls=calls),
            known=ARABIC_ON_OLD_PYTHONS,
        )
    assert {lang for lang, _ in calls} == {"ar"}


def test_known_failures_ledger_names_tickets():
    from reproduce_stories import KNOWN_FAILURES

    for story_id, langs in KNOWN_FAILURES.items():
        for lang, pythons in langs.items():
            for python, ticket in pythons.items():
                assert re.fullmatch(r"CORE-\d+", ticket), (
                    story_id,
                    lang,
                    python,
                    ticket,
                )
