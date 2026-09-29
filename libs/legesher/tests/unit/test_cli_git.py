"""``legesher git setup`` and ``legesher git status`` (CORE-1841).

Setup configures the clean filter only; the keyword-only smudge is an
opt-in; and the guard's pre-commit hook is on by default. Real git
repositories throughout, with the global and system git config isolated so
no test can touch the developer's own.
"""

import os
import stat
import subprocess
import sys

import pytest
import yaml
from click.testing import CliRunner

from legesher.cli.git import _create_gitattributes, git_setup, git_status

CLEAN = "legesher-filter --clean --path %f"
SMUDGE = "legesher-filter --smudge --path %f"


@pytest.fixture(autouse=True)
def isolated_git_config(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return home


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=check
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def config(repo, key, scope="--local"):
    result = git(repo, "config", scope, "--get", key, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def hook(repo):
    return repo / ".git" / "hooks" / "pre-commit"


def setup(*args, **kwargs):
    return CliRunner().invoke(git_setup, list(args), catch_exceptions=False, **kwargs)


class TestSetup:
    def test_configures_the_clean_filter_only(self, repo):
        result = setup("--language", "es")
        assert result.exit_code == 0, result.output
        assert config(repo, "filter.legesher.clean") == CLEAN
        assert config(repo, "filter.legesher.smudge") is None
        assert config(repo, "filter.legesher.required") == "false"
        assert "*.py filter=legesher" in (repo / ".gitattributes").read_text()
        saved = yaml.safe_load((repo / ".legesher" / "config.yml").read_text())
        assert saved["language"] == "es"

    def test_saves_the_python_version(self, repo):
        assert setup("--language", "es", "--python-version", "3.13").exit_code == 0
        saved = yaml.safe_load((repo / ".legesher" / "config.yml").read_text())
        assert saved["python_version"] == "3.13"

    def test_the_keyword_smudge_is_an_opt_in(self, repo):
        assert setup("--language", "es", "--keyword-smudge").exit_code == 0
        assert config(repo, "filter.legesher.smudge") == SMUDGE

    def test_a_plain_rerun_turns_the_smudge_off(self, repo):
        setup("--language", "es", "--keyword-smudge")
        result = setup("--language", "es")
        assert config(repo, "filter.legesher.smudge") is None
        assert "smudge" in result.output.lower()

    def test_installs_the_guard_hook(self, repo):
        setup("--language", "es")
        script = hook(repo).read_text()
        assert "legesher guard --staged" in script
        assert os.stat(hook(repo)).st_mode & stat.S_IXUSR

    def test_a_rerun_leaves_the_hook_as_it_was(self, repo):
        setup("--language", "es")
        first = hook(repo).read_text()
        setup("--language", "es")
        assert hook(repo).read_text() == first

    def test_an_existing_pre_commit_hook_is_never_overwritten(self, repo):
        hook(repo).parent.mkdir(parents=True, exist_ok=True)
        hook(repo).write_text("#!/bin/sh\necho mine\n")
        result = setup("--language", "es")
        assert result.exit_code == 0
        assert hook(repo).read_text() == "#!/bin/sh\necho mine\n"
        assert "legesher guard --staged" in result.output

    def test_no_hook_removes_the_guard_hook(self, repo):
        setup("--language", "es")
        setup("--language", "es", "--no-hook")
        assert not hook(repo).exists()

    def test_a_hook_that_only_mentions_the_marker_is_not_ours(self, repo):
        # Security review of CORE-1841: a substring match took over a team
        # hook that merely quoted the marker.
        team = (
            "#!/bin/sh\n"
            "# legesher-guard-hook: installed by `legesher git setup`.\n"
            "echo team\n"
        )
        hook(repo).parent.mkdir(parents=True, exist_ok=True)
        hook(repo).write_text(team)
        setup("--language", "es")
        assert hook(repo).read_text() == team
        setup("--language", "es", "--no-hook")
        assert hook(repo).read_text() == team

    def test_a_symlinked_hook_is_never_written_through(self, repo, tmp_path):
        target = tmp_path / "outside" / "pre-commit"
        target.parent.mkdir()
        hook(repo).parent.mkdir(parents=True, exist_ok=True)
        hook(repo).symlink_to(target)
        result = setup("--language", "es")
        assert result.exit_code == 0, result.output
        assert hook(repo).is_symlink()
        assert not target.exists()

    def test_a_global_smudge_is_reported_not_claimed_off(self, repo):
        git(
            repo,
            "config",
            "--global",
            "filter.legesher.smudge",
            "legesher-filter --smudge",
        )
        result = setup("--language", "es")
        assert "global" in result.output
        assert "Smudge filter turned off" not in result.output

    def test_no_hook_leaves_someone_elses_hook(self, repo):
        hook(repo).parent.mkdir(parents=True, exist_ok=True)
        hook(repo).write_text("#!/bin/sh\necho mine\n")
        setup("--language", "es", "--no-hook")
        assert hook(repo).read_text() == "#!/bin/sh\necho mine\n"

    def test_core_hooks_path_is_respected(self, repo):
        git(repo, "config", "core.hooksPath", ".githooks")
        setup("--language", "es")
        assert (
            "legesher guard --staged" in (repo / ".githooks" / "pre-commit").read_text()
        )
        assert not hook(repo).exists()

    def test_global_writes_global_config_and_no_hook(self, repo):
        result = setup("--language", "es", "--global")
        assert result.exit_code == 0, result.output
        assert config(repo, "filter.legesher.clean", "--global") == CLEAN
        assert config(repo, "filter.legesher.clean") is None
        assert not hook(repo).exists()

    def test_an_unknown_language(self, repo):
        result = setup("--language", "xx-nope")
        assert result.exit_code == 1
        assert "Language 'xx-nope' not found" in result.output

    def test_outside_a_repository(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = setup("--language", "es")
        assert result.exit_code == 1
        assert "Run this command from within a git repository" in result.output

    def test_prompts_for_the_language(self, repo):
        result = setup(input="es\n")
        assert result.exit_code == 0
        assert "Default language:" in result.output


class TestTheHookRefusesACommit:
    """The whole path: setup, the real filter, the real hook, the real guard."""

    @pytest.fixture
    def on_path(self, monkeypatch):
        bin_dir = os.path.dirname(sys.executable)
        monkeypatch.setenv("PATH", bin_dir + os.pathsep + os.environ.get("PATH", ""))

    def test_a_trojan_source_commit_is_refused(self, repo, on_path):
        assert setup("--language", "es").exit_code == 0
        (repo / "t.py").write_text('definir f():\n    x = "user\u202e"\n')
        git(repo, "add", "t.py", ".gitattributes")
        result = git(repo, "commit", "-m", "trojan", check=False)
        assert result.returncode != 0
        assert "t.py:2:14: unicode: U+202E" in result.stdout + result.stderr
        assert git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode != 0

    def test_the_hook_runs_without_legesher_on_path(self, repo, monkeypatch):
        # The hook names the legesher that installed it, so a commit from a
        # shell where the project environment is not active is still checked.
        assert setup("--language", "es").exit_code == 0
        (repo / "t.py").write_text('x = "user\u202e"\n')
        git(repo, "add", "t.py", ".gitattributes")
        monkeypatch.setenv("PATH", "/usr/bin:/bin")
        result = git(repo, "commit", "-m", "trojan", check=False)
        assert result.returncode != 0, result.stdout + result.stderr
        assert "t.py:1:10: unicode: U+202E" in result.stdout + result.stderr

    def test_a_clean_commit_goes_through_with_strays_normalized(self, repo, on_path):
        assert setup("--language", "es").exit_code == 0
        (repo / "m.py").write_text("definir f(x):\n    if x:\n        devolver 1\n")
        git(repo, "add", "m.py", ".gitattributes", ".legesher")
        assert git(repo, "commit", "-q", "-m", "ok", check=False).returncode == 0
        assert git(repo, "show", "HEAD:m.py").stdout == (
            "definir f(x):\n    si x:\n        devolver 1\n"
        )


class TestStatus:
    def status(self):
        return CliRunner().invoke(git_status, catch_exceptions=False)

    def test_after_setup(self, repo):
        setup("--language", "es")
        result = self.status()
        assert result.exit_code == 0
        assert "Language: es" in result.output
        assert f"✓ Clean filter: {CLEAN}" in result.output
        assert "Smudge filter: off" in result.output
        assert "✓ Guard hook: installed" in result.output
        assert "✓ .gitattributes configured" in result.output

    def test_with_the_keyword_smudge(self, repo):
        setup("--language", "es", "--keyword-smudge")
        assert f"Keyword-only smudge: {SMUDGE}" in self.status().output

    def test_without_setup(self, repo):
        result = self.status()
        assert "✗ Clean filter: Not configured" in result.output
        assert "✗ Guard hook: not installed" in result.output
        assert "✗ .gitattributes not found" in result.output

    def test_outside_a_repository(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = self.status()
        assert result.exit_code == 0
        assert "Not in a git repository" in result.output


class TestCreateGitattributes:
    def test_new_file(self, tmp_path):
        _create_gitattributes(tmp_path)
        content = (tmp_path / ".gitattributes").read_text()
        assert "*.py filter=legesher" in content

    def test_existing_file_is_kept(self, tmp_path):
        (tmp_path / ".gitattributes").write_text("*.txt text\n")
        _create_gitattributes(tmp_path)
        content = (tmp_path / ".gitattributes").read_text()
        assert "*.txt text" in content and "*.py filter=legesher" in content

    def test_not_duplicated(self, tmp_path):
        (tmp_path / ".gitattributes").write_text("*.py filter=legesher\n")
        _create_gitattributes(tmp_path)
        assert (tmp_path / ".gitattributes").read_text().count(
            "*.py filter=legesher"
        ) == 1
