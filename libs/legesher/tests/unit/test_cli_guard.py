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
        (repo / "l.py").symlink_to("target\u202e.py")
        git(repo, "add", "l.py")
        result = run("--staged", "--language", "es")
        assert result.exit_code == 0, result.output

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
