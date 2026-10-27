"""``import-review-file`` and ``check-review-files`` (CORE-2508).

The files sit in a throwaway language-packs git checkout (``reference/<tag>.md``
on ``main``, review files committed the way merges land them), because both
commands read from git: the import at the commit a pull request merged, the
check against the base ref's templates.
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from legesher_i18n.cli import cli
from legesher_i18n.intake.commands import _reply_steps
from legesher_i18n.intake.pipeline import ImportResult
from tests.review_fixtures import (
    CODES,
    PACKS_DIR,
    PR_URL,
    fill,
    pull_request,
    review_db,
    review_path,
    template_text,
)

SI = template_text("si")
GOOD = {"keywords.and": ("", "✓"), "keywords.if": ("`හොත්`", "නම් also means names")}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for relative, text in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        git(repo, "add", relative)
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "language-packs"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    commit(root, {"reference/si.md": SI}, "templates")
    return root


@pytest.fixture()
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LEGESHER_CONTRIBUTOR_SALT", "review-cli-test-salt")
    return review_db(tmp_path / "review.db", CODES)


def merge(
    repo: Path, text: str, tmp_path: Path, url: str = PR_URL
) -> tuple[Path, Path]:
    """Land *text* as a merged pull request; return the review path and the PR payload file."""
    base = git(repo, "rev-parse", "HEAD")
    sha = commit(repo, {review_path("si"): text}, f"merge {url}")
    payload = pull_request(
        url=url, merge_commit=sha, base=base, files=[review_path("si")]
    )
    pr = tmp_path / f"pr-{url.rsplit('/', 1)[1]}.json"
    pr.write_text(json.dumps(payload), encoding="utf-8")
    return repo / review_path("si"), pr


def import_args(review: Path, pr: Path, db: Path, *extra: str) -> list[str]:
    return [
        "import-review-file",
        str(review),
        "--pull-request",
        str(pr),
        "--packs-root",
        str(PACKS_DIR),
        "--db",
        str(db),
        *extra,
    ]


def endorsed(db: Path) -> set[str]:
    conn = sqlite3.connect(db)
    try:
        return {
            s
            for (s,) in conn.execute(
                "SELECT o.surface_form FROM endorsements e JOIN options o ON o.uid = e.option_uid"
            )
        }
    finally:
        conn.close()


def test_a_merged_review_imports_and_reimport_is_a_duplicate(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    review, pr = merge(repo, fill(SI, GOOD), tmp_path)
    first = runner.invoke(cli, import_args(review, pr, db))
    assert first.exit_code == 0, first.output
    assert "status:  accepted" in first.output
    again = runner.invoke(cli, import_args(review, pr, db))
    assert again.exit_code == 0, again.output
    assert "status:  duplicate" in again.output
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM review_sessions").fetchone()[0] == 1
    conn.close()


def test_the_import_reads_what_the_pull_request_merged_not_the_checkout(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    review, first_pr = merge(repo, fill(SI, GOOD), tmp_path)
    # A second review pull request by the same reviewer updates the same file.
    later = fill(SI, {"keywords.or": ("", "✓")})
    merge(
        repo, later, tmp_path, url="https://github.com/legesher/language-packs/pull/401"
    )
    result = runner.invoke(cli, import_args(review, first_pr, db))
    assert result.exit_code == 0, result.output
    assert "හොත්" in endorsed(db)  # the first PR's suggestion, not the later file


def test_an_unmerged_pull_request_is_refused(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, GOOD), tmp_path)
    pr = tmp_path / "open.json"
    pr.write_text(json.dumps(pull_request(merged=False, files=[review_path("si")])))
    result = runner.invoke(cli, import_args(review, pr, db))
    assert result.exit_code != 0
    assert "Merging is the acceptance" in result.output


def test_before_merge_reads_the_head_commit_and_never_replies_or_syncs(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, {review_path("si"): fill(SI, GOOD)}, "open PR head")
    pr = tmp_path / "open.json"
    pr.write_text(
        json.dumps(
            pull_request(merged=False, head=head, base=base, files=[review_path("si")])
        )
    )
    review = repo / review_path("si")
    dry = runner.invoke(cli, import_args(review, pr, db, "--before-merge"))
    assert dry.exit_code == 0, dry.output
    for flag in ("--sync", "--reply"):
        refused = runner.invoke(
            cli, import_args(review, pr, db, "--before-merge", flag)
        )
        assert refused.exit_code != 0
        assert "dry run" in refused.output


def test_before_merge_refuses_a_fingerprinted_database(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO build_meta(key, value) VALUES ('salt_fingerprint', 'abc')"
    )
    conn.commit()
    conn.close()
    review, pr = merge(repo, fill(SI, GOOD), tmp_path)
    result = runner.invoke(cli, import_args(review, pr, db, "--before-merge"))
    assert result.exit_code != 0
    assert "salt_fingerprint" in result.output


def test_a_refused_file_imports_nothing_and_names_the_row(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    text = fill(SI, GOOD).replace(
        "| `keywords.or` | `or` |", "| `keywords.or` | `OR` |", 1
    )
    review, pr = merge(repo, text, tmp_path)
    result = runner.invoke(cli, import_args(review, pr, db))
    assert result.exit_code != 0
    assert "keywords.or" in result.output and "nothing imported" in result.output
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM review_sessions").fetchone()[0] == 0
    conn.close()


@pytest.mark.parametrize("files", [[], ["reviews/si/si-someone-else.md"]])
def test_a_file_the_pull_request_did_not_list_is_refused(
    files: list[str], runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, GOOD), tmp_path)
    sha = git(repo, "rev-parse", "HEAD")
    pr = tmp_path / "pr.json"
    pr.write_text(json.dumps(pull_request(merge_commit=sha, base=sha, files=files)))
    result = runner.invoke(cli, import_args(review, pr, db))
    assert result.exit_code != 0
    assert "is not one of the files" in result.output


def test_a_symlinked_review_file_is_refused(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    review, pr = merge(repo, fill(SI, GOOD), tmp_path)
    link = repo / "reviews" / "si" / "link.md"
    link.symlink_to(review)
    result = runner.invoke(cli, import_args(link, pr, db))
    assert result.exit_code != 0
    assert "symlink" in result.output


def gate(runner: CliRunner, review: Path, *extra: str):
    return runner.invoke(
        cli,
        [
            "check-review-files",
            str(review),
            "--author",
            "native-reviewer",
            "--base-ref",
            "main",
            *extra,
        ],
    )


def test_the_gate_writes_a_report_and_passes_a_clean_file(
    runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, GOOD), tmp_path)
    report = tmp_path / "gate.md"
    result = gate(runner, review, "--report", str(report))
    assert result.exit_code == 0, result.output
    assert "**Passes.**" in report.read_text(encoding="utf-8")


def test_the_gate_fails_and_names_the_row(
    runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, {"builtins.print": ("`list`", "short")}), tmp_path)
    result = gate(runner, review)
    assert result.exit_code == 1
    assert "`builtins.print`" in result.output


def test_the_gate_reads_the_template_from_the_base_not_the_pull_request(
    runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    git(repo, "checkout", "-q", "-b", "pr")
    forged = SI.replace("pack_version=0.0.3", "pack_version=9.9.9", 1)
    commit(repo, {"reference/si.md": forged, review_path("si"): fill(forged)}, "forged")
    result = gate(runner, repo / review_path("si"))
    assert result.exit_code == 1
    assert "9.9.9" in result.output


def test_the_gate_reads_a_review_pinned_before_a_version_bump(
    runner: CliRunner, tmp_path: Path
) -> None:
    root = tmp_path / "bumped"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    older = SI.replace("pack_version=0.0.3", "pack_version=0.0.2", 1)
    commit(root, {"reference/si.md": older}, "0.0.2 template")
    commit(root, {"reference/si.md": SI}, "0.0.3 template")
    review = root / "reviews" / "si" / "si-native-reviewer-0.0.2.md"
    review.parent.mkdir(parents=True)
    review.write_text(fill(older, GOOD), encoding="utf-8")
    result = gate(runner, review)
    assert result.exit_code == 0, result.output


def test_the_gate_refuses_a_file_kind_it_has_no_checker_for(
    runner: CliRunner, repo: Path
) -> None:
    bundle = repo / "reviews" / "si" / "bundle.json"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    bundle.write_text("{}", encoding="utf-8")
    result = runner.invoke(cli, ["check-review-files", str(bundle), "--author", "x"])
    assert result.exit_code == 1
    assert "no checker" in result.output


def test_a_pull_request_reply_comments_and_labels_but_never_closes() -> None:
    result = ImportResult(session_uid="ses_" + "0" * 24, status="accepted", report={})
    steps = [what for _, what in _reply_steps(result, PR_URL)]
    assert steps == ["comment", "label"]
    argv = [argv for argv, _ in _reply_steps(result, PR_URL)]
    assert argv[0][:3] == ["gh", "pr", "comment"]


@pytest.mark.parametrize("url", [PR_URL + "\n", PR_URL + "/files", "-" + PR_URL])
def test_a_pull_request_url_is_matched_whole(url: str) -> None:
    from legesher_i18n.intake.commands import validated_pull_request_url

    with pytest.raises(ValueError):
        validated_pull_request_url(url)


# --- second review pass ---------------------------------------------------------------


@pytest.mark.parametrize("tag", ["../README", "s?", "si*"])
def test_a_hostile_tag_is_a_failing_report_and_never_reaches_git(
    tag: str, runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    hostile = fill(SI).replace("bcp47=si ", f"bcp47={tag} ", 1)
    bad = repo / "reviews" / "si" / "si-hostile.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(hostile, encoding="utf-8")
    good, _ = merge(repo, fill(SI, GOOD), tmp_path)
    report = tmp_path / "gate.md"
    result = gate(runner, bad, str(good), "--report", str(report))
    assert result.exit_code == 1, result.output
    text = report.read_text(encoding="utf-8")
    assert "disagrees with the registry" in text
    assert "**Passes.**" in text  # the clean file in the same run still got its report


def test_a_ref_that_looks_like_an_option_is_refused(
    runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, GOOD), tmp_path)
    result = runner.invoke(
        cli,
        [
            "check-review-files",
            str(review),
            "--author",
            "native-reviewer",
            "--base-ref",
            "--output=/tmp/x",
        ],
    )
    assert result.exit_code == 1
    assert "is not a git ref" in result.output


def test_a_rebase_merged_pull_request_cannot_supply_its_own_template(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    current = "`" + SI.split("| `keywords.if` | `if` | `", 1)[1].split("`", 1)[0] + "`"
    forged = SI.replace(
        f"| `keywords.if` | `if` | {current} |",
        "| `keywords.if` | `if` | `forged` |",
        1,
    )
    # Two commits replayed onto main by a rebase merge: the template edit, then the review.
    commit(repo, {"reference/si.md": forged}, "PR commit 1")
    merged = commit(repo, {review_path("si"): fill(forged, GOOD)}, "PR commit 2")
    pr = tmp_path / "rebased.json"
    pr.write_text(
        json.dumps(
            pull_request(
                merge_commit=merged,
                base=base,
                files=[review_path("si"), "reference/si.md"],
            )
        )
    )
    result = runner.invoke(cli, import_args(repo / review_path("si"), pr, db))
    assert result.exit_code != 0
    assert "keywords.if" in result.output and "current word" in result.output


def test_a_review_that_is_not_utf8_is_refused(
    runner: CliRunner, repo: Path, db: Path, tmp_path: Path
) -> None:
    path = repo / review_path("si")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fill(SI, GOOD).encode("utf-8") + b"\xff\xfe")
    git(repo, "add", review_path("si"))
    git(repo, "commit", "-q", "-m", "bad bytes")
    sha = git(repo, "rev-parse", "HEAD")
    pr = tmp_path / "pr.json"
    pr.write_text(
        json.dumps(pull_request(merge_commit=sha, base=sha, files=[review_path("si")]))
    )
    result = runner.invoke(cli, import_args(path, pr, db))
    assert result.exit_code != 0
    assert "not UTF-8" in result.output


# --- third review pass ----------------------------------------------------------------


def test_an_older_same_pin_template_of_another_shape_is_skipped_not_fatal(
    runner: CliRunner, tmp_path: Path
) -> None:
    root = tmp_path / "reshaped"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    # An older template with the same metadata line and one box fewer: the
    # digest covers the pack's words, not the template's wording.
    research_box = next(line for line in SI.split("\n") if "research datasets" in line)
    older = SI.replace(research_box + "\n", "", 1)
    commit(root, {"reference/si.md": older}, "older wording")
    commit(root, {"reference/si.md": SI}, "current wording")
    unticked = root / "reviews" / "si" / "si-native-reviewer.md"
    unticked.parent.mkdir(parents=True)
    unticked.write_text(fill(SI, GOOD, ticked=range(4)), encoding="utf-8")
    clean = root / "reviews" / "si" / "si-native-reviewer-0.0.3.md"
    clean.write_text(fill(SI, GOOD), encoding="utf-8")
    report = tmp_path / "gate.md"
    result = gate(runner, unticked, str(clean), "--report", str(report))
    assert result.exit_code == 1, result.output
    text = report.read_text(encoding="utf-8")
    assert "CONTRIBUTOR_PRIVACY.md" in text  # the unticked file got its own report
    assert "**Passes.**" in text  # and the run went on to the next file


def test_a_file_whose_check_raises_is_a_failing_report_and_the_run_continues(
    runner: CliRunner, repo: Path, tmp_path: Path
) -> None:
    review, _ = merge(repo, fill(SI, GOOD), tmp_path)
    link = repo / "reviews" / "si" / "x@legesher ![p](https:" / "si-link.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(review)
    report = tmp_path / "gate.md"
    result = gate(runner, link, str(review), "--report", str(report))
    assert result.exit_code == 1, result.output
    text = report.read_text(encoding="utf-8")
    assert "is a symlink" in text and "**Passes.**" in text
    for line in text.splitlines():
        stripped = re.sub(r"(`+).*?\1", "", line)
        assert "@legesher" not in stripped and "![p]" not in stripped, line
