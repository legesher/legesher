"""``legesher guard``: the refusal the clean filter cannot make (CORE-1841).

Real git repositories throughout: what the guard reads is what git stages,
so a mocked ``subprocess.run`` would test nothing but the mock.
"""

import subprocess

import pytest
from click.testing import CliRunner

from legesher.cli.guard import guard


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository whose .py files are Legesher's, with no filter configured.

    No filter is the case the guard exists for: a file that reached the
    index from a machine without Legesher.
    """
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / ".gitattributes").write_text("*.py filter=legesher\n")
    git(tmp_path, "add", ".gitattributes")
    git(tmp_path, "commit", "-q", "-m", "attributes")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def stage(repo, name, text):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", name)


def run(*args):
    return CliRunner().invoke(guard, list(args))


class TestStaged:
    def test_a_clean_file_passes(self, repo):
        stage(repo, "m.py", "definir f(x):\n    si x:\n        devolver 1\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 0, result.output

    def test_a_trojan_source_file_is_refused(self, repo):
        stage(repo, "src/t.py", 'definir f():\n    x = "user\u202e"\n')
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1
        assert "src/t.py:2:14: unicode: U+202E" in result.output

    def test_an_english_stray_that_skipped_the_filter_is_refused(self, repo):
        stage(repo, "m.py", "definir f(x):\n    if x:\n        devolver 1\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1
        assert "m.py:2:5: keyword: `if`" in result.output
        assert "git add --renormalize" in result.output

    def test_what_is_checked_is_the_staged_version(self, repo):
        stage(repo, "m.py", 'x = "\u202e"\n')
        (repo / "m.py").write_text("x = 1\n")  # clean on disk, not in the index
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1
        assert "m.py:1:6: unicode: U+202E" in result.output

    def test_the_committed_version_decides_the_block(self, repo):
        stage(repo, "e.py", "def f(x):\n    return x\n")
        git(repo, "commit", "-q", "-m", "e")
        stage(repo, "e.py", "def f(x):\n    si x:\n        return x\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1
        assert "e.py:2:5: keyword: `si`" in result.output

    def test_files_git_does_not_give_to_legesher_are_not_checked(self, repo):
        stage(repo, "notes.txt", "user\u202e\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 0, result.output

    def test_unstaged_and_deleted_files_are_not_checked(self, repo):
        stage(repo, "gone.py", "x = 1\n")
        git(repo, "commit", "-q", "-m", "gone")
        git(repo, "rm", "-q", "gone.py")
        (repo / "loose.py").write_text('x = "\u202e"\n')
        result = run("--staged", "--language", "es")
        assert result.exit_code == 0, result.output

    def test_the_language_comes_from_the_project_config(self, repo):
        (repo / ".legesher").mkdir()
        (repo / ".legesher" / "config.yml").write_text("language: es\n")
        stage(repo, "m.py", "definir f(x):\n    if x:\n        devolver 1\n")
        result = run("--staged")
        assert result.exit_code == 1
        assert "`si`" in result.output


class TestSecurityReviewRegressions:
    """Bypasses found in the security review of CORE-1841."""

    def stage_bytes(self, repo, name, data):
        (repo / name).write_bytes(data)
        git(repo, "add", name)

    def test_bytes_that_are_not_utf8_are_refused_not_skipped(self, repo):
        self.stage_bytes(repo, "cp.py", b"# coding: cp1256\nx\xdc = 1\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "cp.py:1:1: encoding: declares its encoding as cp1256" in result.output

    def test_a_utf7_declaration_is_refused(self, repo):
        self.stage_bytes(repo, "u7.py", b"# coding: utf-7\ns = 'a+ACI- ; t = 1'\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "u7.py:1:1: encoding:" in result.output

    def test_a_symlink_turned_into_a_file_is_checked(self, repo):
        (repo / "f.py").symlink_to("elsewhere.py")
        git(repo, "add", "f.py")
        git(repo, "commit", "-q", "-m", "link")
        (repo / "f.py").unlink()
        stage(repo, "f.py", 'x = "\u202e"\n')
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "f.py:1:6: unicode: U+202E" in result.output

    def test_a_staged_symlink_is_not_read_as_source(self, repo):
        # Its blob is the target's name; that is never read as code. The link
        # itself is refused (a Legesher-marked symlink, CORE-1323).
        (repo / "l.py").symlink_to("target\u202e.py")
        git(repo, "add", "l.py")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "l.py:1:1: artifact: a symlink" in result.output
        assert "unicode" not in result.output

    def test_an_untracked_gitattributes_still_marks_the_files(
        self, tmp_path, monkeypatch
    ):
        # Right after `legesher git setup`, .gitattributes is written but not
        # staged; the staged attributes alone would check nothing.
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        git(fresh, "init", "-q")
        (fresh / ".gitattributes").write_text("*.py filter=legesher\n")
        monkeypatch.chdir(fresh)
        stage(fresh, "lf.py", "b\U00013000 = 2\n")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "lf.py:1:2: unicode:" in result.output

    def test_the_staged_gitattributes_decide(self, repo):
        (repo / ".gitattributes").write_text("*.py -filter\n")  # not staged
        stage(repo, "w.py", 'x = "\u202e"\n')
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1, result.output
        assert "w.py:1:6: unicode: U+202E" in result.output


class TestPaths:
    def test_named_files_are_read_from_disk(self, repo):
        (repo / "a.py").write_text("definir f(x):\n    si x:\n        return 1\n")
        result = run("--language", "es", "a.py")
        assert result.exit_code == 1
        assert "a.py:3:9: keyword: `return`" in result.output

    def test_a_named_file_that_is_not_utf8_is_a_finding(self, repo):
        (repo / "a.py").write_bytes(b"x = '\xff'\n")
        result = run("--language", "es", "a.py")
        assert result.exit_code == 1
        assert "a.py:1:1: encoding:" in result.output

    def test_a_clean_named_file_passes(self, repo):
        (repo / "a.py").write_text("definir f():\n    devolver 1\n")
        result = run("--language", "es", "a.py")
        assert result.exit_code == 0, result.output


class TestCannotRun:
    def test_staged_outside_a_repository(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert run("--staged", "--language", "es").exit_code == 2

    def test_an_unknown_language(self, repo):
        assert run("--staged", "--language", "xx-nope").exit_code == 2


def head(repo):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def commit(repo, name, text, message="c"):
    stage(repo, name, text)
    git(repo, "commit", "-q", "-m", message)


class TestDiff:
    """CORE-1323: `--diff BASE` checks only what changed between BASE and HEAD,
    read from HEAD's tree and judged against BASE's version of each file:
    what the pull-request check runs."""

    def test_only_changed_files_are_checked(self, repo):
        commit(repo, "old.py", 'x = "\u202e"\n', "old finding, not in this change")
        base = head(repo)
        commit(repo, "new.py", 'y = "\u202e"\n')
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1
        assert "new.py:1:6: unicode: U+202E" in result.output
        assert "old.py" not in result.output

    def test_content_comes_from_head_not_the_disk(self, repo):
        base = head(repo)
        commit(repo, "m.py", 'x = "\u202e"\n')
        (repo / "m.py").write_text("x = 1\n")
        assert run("--diff", base, "--language", "es").exit_code == 1

    def test_the_base_version_decides_the_block(self, repo):
        # Mid-edit, the head version parses under no reading, so only the
        # base version can say the block is Spanish.
        commit(repo, "m.py", "definir f(x):\n    devolver x\n")
        base = head(repo)
        commit(repo, "m.py", "definir f(x)\n    return x\n")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1
        assert "m.py:2:5: keyword: `return`" in result.output

    def test_a_clean_change_passes(self, repo):
        base = head(repo)
        commit(repo, "m.py", "definir f(x):\n    si x:\n        devolver 1\n")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 0, result.output

    def test_deleted_files_are_not_checked_and_renames_are(self, repo):
        commit(repo, "gone.py", 'x = "\u202e"\n')
        commit(repo, "moved.py", "x = 1\n")
        base = head(repo)
        git(repo, "rm", "-q", "gone.py")
        git(repo, "mv", "moved.py", "renamed.py")
        (repo / "renamed.py").write_text('x = "\u202e"\n')
        git(repo, "add", "renamed.py")
        git(repo, "commit", "-q", "-m", "c")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1
        assert "renamed.py:1:6" in result.output and "gone.py" not in result.output

    def test_a_legesher_artifact_is_checked_whatever_its_attributes(self, repo):
        base = head(repo)
        commit(repo, ".legesher/config.yml", "metadata:\n  directory: ../../outside\n")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1
        assert ".legesher/config.yml:1:1: artifact: metadata.directory" in result.output

    def test_a_base_that_is_not_a_commit(self, repo):
        result = run("--diff", "no-such-ref", "--language", "es")
        assert result.exit_code == 2
        assert "is not a commit" in result.output

    def test_diff_and_staged_are_exclusive(self, repo):
        result = run("--diff", head(repo), "--staged", "--language", "es")
        assert result.exit_code == 2
        assert "takes no --staged" in result.output


class TestStagedArtifacts:
    def test_a_staged_symlink_under_legesher_is_refused(self, repo):
        (repo / ".legesher").mkdir()
        (repo / ".legesher" / "config.yml").symlink_to("/etc/hosts")
        git(repo, "add", ".legesher/config.yml")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 1
        assert ".legesher/config.yml:1:1: artifact: a symlink" in result.output


class TestGithubFormat:
    """`--format github` prints workflow commands, so each finding is an
    annotation on the pull request's diff (CORE-1323)."""

    def test_findings_become_error_annotations(self, repo):
        base = head(repo)
        commit(repo, "src/t.py", 'x = "\u202e"\n')
        result = run("--diff", base, "--language", "es", "--format", "github")
        assert result.exit_code == 1
        assert (
            "::error file=src/t.py,line=1,col=6,title=legesher guard (unicode)::"
            "U+202E RIGHT-TO-LEFT OVERRIDE" in result.output
        )

    def test_properties_and_messages_are_escaped(self):
        from legesher.cli.guard import github_annotation
        from legesher_core.guard import Finding

        finding = Finding("a,b:c%.py", 2, 3, "artifact", "50% of\nthis, ok")
        assert github_annotation(finding) == (
            "::error file=a%2Cb%3Ac%25.py,line=2,col=3,title=legesher guard (artifact)"
            "::50%25 of%0Athis, ok"
        )

    def test_the_default_format_is_unchanged(self, repo):
        base = head(repo)
        commit(repo, "t.py", 'x = "\u202e"\n')
        result = run("--diff", base, "--language", "es")
        assert "t.py:1:6: unicode: U+202E" in result.output
        assert "::error" not in result.output


class TestDiffReviewRegressions:
    """Bypasses from the review of CORE-1323, each a pull request that
    passed its own check."""

    def test_a_pull_request_cannot_unmark_its_own_file(self, repo):
        base = head(repo)
        stage(repo, "evil.py", 'x = "\u202e"\n')
        (repo / ".gitattributes").write_text("*.py filter=legesher\nevil.py -filter\n")
        git(repo, "add", ".gitattributes")
        git(repo, "commit", "-q", "-m", "unmark")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "evil.py:1:6: unicode: U+202E" in result.output

    def test_nor_through_a_nested_gitattributes(self, repo):
        base = head(repo)
        stage(repo, "pkg/evil.py", 'x = "\u202e"\n')
        stage(repo, "pkg/.gitattributes", "*.py !filter\n")
        git(repo, "commit", "-q", "-m", "unmark")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "pkg/evil.py:1:6" in result.output

    @pytest.mark.parametrize(
        "base_config",
        [None, "metadata:\n  enabled: true\n"],
        ids=["no-config", "no-language"],
    )
    def test_a_base_without_a_language_is_judged_as_english(self, repo, base_config):
        # Re-review of CORE-1323: the guard fell back to the pull request's
        # own config when the base named no language.
        if base_config is not None:
            commit(repo, ".legesher/config.yml", base_config)
        base = head(repo)
        stage(repo, ".legesher/config.yml", "language: fa\n")
        stage(repo, "z.py", "is\u200cadmin = True\n")
        git(repo, "commit", "-q", "-m", "switch")
        result = run("--diff", base)
        assert result.exit_code == 1, result.output
        assert "z.py:1:3: unicode: U+200C" in result.output

    def test_the_language_comes_from_the_base(self, repo):
        commit(repo, ".legesher/config.yml", "language: es\n")
        base = head(repo)
        # fa allows ZWNJ in names; es does not. The pull request switches.
        stage(repo, ".legesher/config.yml", "language: fa\n")
        stage(repo, "z.py", "is\u200cadmin = True\n")
        git(repo, "commit", "-q", "-m", "switch")
        result = run("--diff", base)
        assert result.exit_code == 1, result.output
        assert "z.py:1:3: unicode: U+200C" in result.output

    def test_legesher_replaced_by_a_symlink(self, repo):
        commit(repo, ".legesher/config.yml", "language: es\n")
        base = head(repo)
        git(repo, "rm", "-q", "-r", ".legesher")
        (repo / ".legesher").symlink_to("../outside")
        git(repo, "add", ".legesher")
        git(repo, "commit", "-q", "-m", "link")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert ".legesher:1:1: artifact: a symlink" in result.output

    def test_a_case_variant_of_legesher(self, repo):
        base = head(repo)
        commit(repo, ".LEGESHER/config.yml", "metadata:\n  directory: ../../outside\n")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert ".LEGESHER/config.yml:1:1: artifact: metadata.directory" in result.output

    def test_a_symlinked_source_file_is_refused(self, repo):
        # Re-review of CORE-1323: following links could not be made complete
        # (chains, directory links, a pull request editing only the target),
        # so a Legesher-marked symlink is refused outright.
        base = head(repo)
        stage(repo, "helper.txt", 'x = "\u202e"\n')
        (repo / "helper.py").symlink_to("helper.txt")
        git(repo, "add", "helper.py")
        git(repo, "commit", "-q", "-m", "link")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "helper.py:1:1: artifact: a symlink" in result.output

    def test_a_chain_of_symlinks_is_refused(self, repo):
        base = head(repo)
        stage(repo, "c.txt", 'x = "\u202e"\n')
        (repo / "b.txt").symlink_to("c.txt")
        (repo / "a.py").symlink_to("b.txt")
        git(repo, "add", "a.py", "b.txt")
        git(repo, "commit", "-q", "-m", "chain")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "a.py:1:1: artifact: a symlink" in result.output

    def test_an_existing_symlink_is_refused_when_only_its_target_changes(self, repo):
        (repo / "s.py").symlink_to("t.txt")
        stage(repo, "t.txt", "x = 1\n")
        git(repo, "add", "s.py")
        git(repo, "commit", "-q", "-m", "link")
        base = head(repo)
        commit(repo, "t.txt", 'x = "\u202e"\n')
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "s.py:1:1: artifact: a symlink" in result.output

    def test_a_symlink_the_base_marks_is_refused_when_the_head_unmarks_it(self, repo):
        (repo / "s.py").symlink_to("t.txt")
        stage(repo, "t.txt", "x = 1\n")
        git(repo, "add", "s.py")
        git(repo, "commit", "-q", "-m", "link")
        base = head(repo)
        attributes = (repo / ".gitattributes").read_text()
        stage(repo, ".gitattributes", attributes + "s.py -filter\n")
        commit(repo, "t.txt", 'x = "\u202e"\n')
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "s.py:1:1: artifact: a symlink" in result.output

    @pytest.mark.parametrize("kind", ["symlink", "submodule"])
    def test_an_unchanged_link_under_legesher_is_refused(self, repo, kind):
        # Third review: a link the base already holds (added before the guard,
        # or by a direct push) would let a pull request point
        # metadata.directory through it without touching the link itself.
        if kind == "symlink":
            (repo / ".legesher").mkdir()
            (repo / ".legesher" / "cache").symlink_to("../../outside")
            git(repo, "add", ".legesher/cache")
        else:
            gitlink = f"160000,{head(repo)},.legesher/cache"
            git(repo, "update-index", "--add", "--cacheinfo", gitlink)
        git(repo, "commit", "-q", "-m", "link")
        base = head(repo)
        commit(
            repo,
            ".legesher/config.yml",
            "metadata:\n  directory: .legesher/cache/sub\n",
        )
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert (
            f".legesher/cache:1:1: artifact: a {kind} under .legesher/" in result.output
        )

    @pytest.mark.parametrize("changed", [True, False], ids=["changed", "unchanged"])
    def test_a_marked_symlink_under_legesher_is_reported_once(self, repo, changed):
        base = head(repo)
        (repo / ".legesher").mkdir()
        (repo / ".legesher" / "hook.py").symlink_to("../elsewhere.txt")
        git(repo, "add", ".legesher/hook.py")
        git(repo, "commit", "-q", "-m", "link")
        if not changed:
            base = head(repo)
            commit(repo, "other.py", "x = 1\n")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert result.output.count(".legesher/hook.py:") == 1, result.output

    def test_a_symlinked_source_file_pointing_outside(self, repo):
        base = head(repo)
        (repo / "helper.py").symlink_to("../../outside.py")
        git(repo, "add", "helper.py")
        git(repo, "commit", "-q", "-m", "link")
        result = run("--diff", base, "--language", "es")
        assert result.exit_code == 1, result.output
        assert "helper.py:1:1: artifact: a symlink" in result.output

    def test_files_the_guard_does_not_own_are_never_loaded(self, repo, monkeypatch):
        from legesher.cli import guard as guard_cli

        base = head(repo)
        commit(repo, ".legesher/map.bin", "opaque\n")
        loaded = []
        real = guard_cli._blob_bytes
        monkeypatch.setattr(
            guard_cli,
            "_blob_bytes",
            lambda repo_, revision: loaded.append(revision) or real(repo_, revision),
        )
        assert run("--diff", base, "--language", "es").exit_code == 0
        assert not any("map.bin" in revision for revision in loaded)
