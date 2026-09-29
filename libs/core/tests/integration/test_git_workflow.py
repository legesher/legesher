"""The clean filter under real git (CORE-1841).

Git runs the filter exactly as ``legesher git setup`` wires it, pointed at
this interpreter (``python -m legesher_core``) so the test never depends on
what is on PATH. What is asserted is what git stores (``git cat-file``) and
what ``git status`` reports, never the filter called directly.
"""

import os
import shlex
import subprocess
import sys

import pytest

FILTER = f"{shlex.quote(sys.executable)} -m legesher_core"


def git(repo, *args, stdin=None):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        input=stdin,
    ).stdout


def stored(repo, path):
    return git(repo, "cat-file", "blob", f":0:{path}").decode()


def status(repo):
    return git(repo, "status", "--porcelain").decode()


def make_repo(tmp_path, language, smudge=False):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "core.autocrlf", "false")
    for mode in ("clean", "smudge") if smudge else ("clean",):
        git(
            repo,
            "config",
            f"filter.legesher.{mode}",
            f"{FILTER} --{mode} --language {language} --path %f",
        )
    git(repo, "config", "filter.legesher.required", "false")
    (repo / ".gitattributes").write_text("*.py filter=legesher\n")
    git(repo, "add", ".gitattributes")
    git(repo, "commit", "-q", "-m", "attributes")
    return repo


@pytest.fixture
def spanish_repo(tmp_path):
    return make_repo(tmp_path, "es")


def commit(repo, name, text, message="c"):
    (repo / name).write_bytes(text.encode())
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", message)


class TestCleanUnderGit:
    def test_git_add_stores_english_strays_in_the_blocks_language(self, spanish_repo):
        text = "definir f(x):\n    if x:\n        devolver 1\n"
        (spanish_repo / "m.py").write_text(text)
        git(spanish_repo, "add", "m.py")
        assert stored(spanish_repo, "m.py") == (
            "definir f(x):\n    si x:\n        devolver 1\n"
        )
        # The working tree is the author's; the filter never writes it.
        assert (spanish_repo / "m.py").read_text() == text

    def test_the_committed_version_decides_the_block(self, spanish_repo):
        commit(spanish_repo, "e.py", "def f(x):\n    return x\n")
        (spanish_repo / "e.py").write_text("def f(x):\n    si x:\n        return x\n")
        git(spanish_repo, "add", "e.py")
        assert stored(spanish_repo, "e.py") == (
            "def f(x):\n    if x:\n        return x\n"
        )

    def test_an_english_file_is_stored_as_written(self, spanish_repo):
        text = "def f(x, y):\n    return y\n"
        commit(spanish_repo, "e.py", text)
        assert stored(spanish_repo, "e.py") == text

    def test_status_stays_clean_after_a_touch(self, spanish_repo):
        commit(spanish_repo, "m.py", "definir f(x):\n    if x:\n        devolver 1\n")
        os.utime(spanish_repo / "m.py", (1, 1))
        # Git re-runs clean on a stat-dirty file; a stable filter reports
        # nothing to commit.
        assert status(spanish_repo) == ""

    def test_crlf_is_stored_as_written(self, spanish_repo):
        commit(
            spanish_repo, "m.py", "definir f(x):\r\n    si x:\r\n        return 1\r\n"
        )
        assert stored(spanish_repo, "m.py") == (
            "definir f(x):\r\n    si x:\r\n        devolver 1\r\n"
        )

    def test_the_filter_does_not_refuse_the_guard_does(self, spanish_repo):
        text = 'x = "user\u202e"\n'
        commit(spanish_repo, "t.py", text)
        assert stored(spanish_repo, "t.py") == text

    def test_a_file_in_a_third_language_is_left_alone(self, spanish_repo):
        text = "défini f(x):\n    return x\n"  # French keywords, Spanish repo
        commit(spanish_repo, "fr.py", text)
        assert stored(spanish_repo, "fr.py") == text

    def test_arabic(self, tmp_path):
        repo = make_repo(tmp_path, "ar")
        commit(repo, "m.py", "تعريف f(x):\n    إذا x:\n        return x\n")
        assert stored(repo, "m.py") == "تعريف f(x):\n    إذا x:\n        إرجاع x\n"


class TestReviewRegressions:
    """Reproductions from the review of CORE-1841, under real git."""

    ENGLISH = (
        "import os\n\n"
        "def main():\n"
        "    for name in os.listdir('.'):\n"
        "        if name.endswith('.py'):\n"
        "            print(name)\n"
        "    return None\n"
    )
    SLIP = ENGLISH.replace("if name", "si name")

    def test_a_staged_wip_slip_does_not_spread_to_the_whole_file(self, spanish_repo):
        commit(spanish_repo, "app.py", self.ENGLISH)
        broken = self.SLIP.replace(
            "    return None", "    total = 1 +\n    return None"
        )
        (spanish_repo / "app.py").write_text(broken)
        git(spanish_repo, "add", "app.py")
        (spanish_repo / "app.py").write_text(broken.replace("1 +", "1 + 2"))
        git(spanish_repo, "add", "app.py")
        assert stored(spanish_repo, "app.py") == self.ENGLISH.replace(
            "    return None", "    total = 1 + 2\n    return None"
        )

    def test_renormalizing_a_file_staged_without_the_filter(self, spanish_repo):
        commit(spanish_repo, "app.py", self.ENGLISH)
        blob = (
            git(
                spanish_repo,
                "hash-object",
                "-w",
                "--no-filters",
                "--stdin",
                stdin=self.SLIP.encode(),
            )
            .decode()
            .strip()
        )
        git(spanish_repo, "update-index", "--cacheinfo", f"100644,{blob},app.py")
        (spanish_repo / "app.py").write_text(self.SLIP)
        git(spanish_repo, "add", "--renormalize", "app.py")
        assert stored(spanish_repo, "app.py") == self.ENGLISH

    def test_status_stays_clean_after_staging_a_broken_edit(self, spanish_repo):
        commit(spanish_repo, "m.py", "definir f(x):\n    si x:\n        devolver 1\n")
        (spanish_repo / "m.py").write_text(
            "definir f(x):\n    if x:\n        devolver 2 +\n"
        )
        git(spanish_repo, "add", "m.py")
        os.utime(spanish_repo / "m.py", (1, 1))
        assert status(spanish_repo) == "M  m.py\n"


class TestKeywordOnlySmudgeUnderGit:
    def test_checkout_renders_keywords_and_status_stays_clean(self, tmp_path):
        repo = make_repo(tmp_path, "es", smudge=True)
        english = "def f(x):\n    for i in x:\n        print(i)\n    return None\n"
        commit(repo, "e.py", english)
        (repo / "e.py").unlink()
        git(repo, "checkout", "--", "e.py")
        assert (repo / "e.py").read_text() == (
            "definir f(x):\n    por i en x:\n        print(i)\n    devolver nulo\n"
        )
        assert stored(repo, "e.py") == english
        os.utime(repo / "e.py", (1, 1))
        assert status(repo) == ""

    def test_an_edit_in_the_rendering_is_stored_in_english(self, tmp_path):
        repo = make_repo(tmp_path, "es", smudge=True)
        commit(repo, "e.py", "def f(x):\n    return x\n")
        (repo / "e.py").unlink()
        git(repo, "checkout", "--", "e.py")
        (repo / "e.py").write_text("definir f(x):\n    si x:\n        devolver x\n")
        git(repo, "add", "e.py")
        assert stored(repo, "e.py") == "def f(x):\n    if x:\n        return x\n"
