"""The git clean filter normalizes and never refuses (CORE-1841).

The normalizer's own behavior is covered in ``test_stored_form.py``; these
tests cover what the filter adds around it: streams, the stored-version
lookup by path, the keyword-only smudge, and never failing git.
"""

import io
import subprocess
from unittest.mock import patch

import pytest

from legesher_core.git_filter import (
    GitFilter,
    clean_filter,
    read_stored_blob,
    smudge_filter,
)


def no_stored(path):
    return None


@pytest.fixture
def spanish_filter():
    return GitFilter(language="es", python_version="3.13", stored_reader=no_stored)


def run_clean(git_filter, text, path=None):
    out = io.StringIO()
    code = git_filter.clean(io.StringIO(text), out, path=path)
    return code, out.getvalue()


def run_smudge(git_filter, text, path=None):
    out = io.StringIO()
    code = git_filter.smudge(io.StringIO(text), out, path=path)
    return code, out.getvalue()


class TestInit:
    def test_language_and_version(self):
        git_filter = GitFilter(language="es", python_version="3.10")
        assert (git_filter.language, git_filter.python_version) == ("es", "3.10")

    def test_an_unknown_language_is_a_value_error(self):
        with pytest.raises(ValueError, match="Could not load language pack"):
            GitFilter(language="invalid-lang")


class TestClean:
    def test_an_english_stray_joins_its_spanish_block(self, spanish_filter):
        code, out = run_clean(
            spanish_filter, "definir f(x):\n    if x:\n        devolver 1\n"
        )
        assert code == 0
        assert out == "definir f(x):\n    si x:\n        devolver 1\n"

    def test_an_english_file_is_stored_as_written(self, spanish_filter):
        text = "def f(x, y):\n    return y\n"
        assert run_clean(spanish_filter, text) == (0, text)

    def test_the_stored_version_at_the_path_decides_the_block(self):
        seen = []

        def reader(path):
            seen.append(path)
            return "def f(x):\n    return x\n"

        git_filter = GitFilter(language="es", stored_reader=reader)
        code, out = run_clean(
            git_filter, "def f(x):\n    si x:\n        return x\n", path="pkg/m.py"
        )
        assert (code, out) == (0, "def f(x):\n    if x:\n        return x\n")
        assert seen == ["pkg/m.py"]

    def test_without_a_path_the_text_decides(self):
        def reader(path):
            raise AssertionError("no path, so nothing to look up")

        git_filter = GitFilter(language="es", stored_reader=reader)
        assert run_clean(
            git_filter, "definir f(x):\n    si x:\n        return 1\n"
        ) == (
            0,
            "definir f(x):\n    si x:\n        devolver 1\n",
        )

    @pytest.mark.parametrize(
        "text",
        [
            'x = "user\u202e"\nprint(x)\n',
            "ad\u200bmin = True\n",
            f"to{chr(0x2D7F)}tal = 1\n",
        ],
        ids=["bidi", "zero-width", "tifinagh-joiner"],
    )
    def test_never_refuses_the_guard_does(self, spanish_filter, text):
        # A refusing clean filter is a silent passthrough in git, so the
        # filter does not pretend to refuse; `legesher guard` does.
        assert run_clean(spanish_filter, text) == (0, text)

    def test_an_internal_error_passes_the_text_through(self, spanish_filter):
        text = "definir f():\n    return 1\n"
        with patch("legesher_core.git_filter.clean_text", side_effect=RuntimeError):
            assert run_clean(spanish_filter, text) == (0, text)

    def test_a_failing_stored_lookup_falls_back_to_the_text(self):
        def reader(path):
            raise OSError("git is gone")

        git_filter = GitFilter(language="es", stored_reader=reader)
        text = "definir f(x):\n    si x:\n        return 1\n"
        assert run_clean(git_filter, text, path="a.py") == (
            0,
            "definir f(x):\n    si x:\n        devolver 1\n",
        )

    def test_is_idempotent(self, spanish_filter):
        _, once = run_clean(spanish_filter, "definir f(x):\n    if x:\n        pass\n")
        assert run_clean(spanish_filter, once) == (0, once)


class TestKeywordOnlySmudge:
    def test_renders_keywords_and_leaves_builtins(self, spanish_filter):
        assert run_smudge(spanish_filter, "def f(x):\n    return len(x)\n") == (
            0,
            "definir f(x):\n    devolver len(x)\n",
        )

    def test_a_render_it_cannot_clean_back_is_not_written(self, spanish_filter):
        text = "def f(y):\n    return y\n"
        assert run_smudge(spanish_filter, text) == (0, text)

    def test_an_internal_error_passes_the_text_through(self, spanish_filter):
        text = "def f():\n    return 1\n"
        with patch("legesher_core.git_filter.smudge_text", side_effect=RuntimeError):
            assert run_smudge(spanish_filter, text) == (0, text)


def git(repo, *args, stdin=None):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, input=stdin
    )


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    return tmp_path


class TestReadStoredBlob:
    def test_head_wins_over_a_staged_version(self, repo):
        # A staged blob can be a half-edited, mixed version; the committed
        # one is the stable reference (review of CORE-1841).
        (repo / "m.py").write_text("committed\n")
        git(repo, "add", "m.py")
        git(repo, "commit", "-q", "-m", "c")
        (repo / "m.py").write_text("staged\n")
        git(repo, "add", "m.py")
        assert read_stored_blob("m.py", cwd=repo) == "committed\n"

    def test_the_index_when_the_path_was_never_committed(self, repo):
        (repo / "m.py").write_text("staged\n")
        git(repo, "add", "m.py")
        assert read_stored_blob("m.py", cwd=repo) == "staged\n"

    def test_an_untracked_path_has_no_stored_version(self, repo):
        (repo / "new.py").write_text("x = 1\n")
        assert read_stored_blob("new.py", cwd=repo) is None

    def test_outside_a_repository_there_is_none(self, tmp_path):
        assert read_stored_blob("m.py", cwd=tmp_path) is None


class TestConvenienceFunctions:
    @patch("legesher_core.git_filter.GitFilter")
    def test_clean_filter(self, filter_class):
        filter_class.return_value.clean.return_value = 0
        assert clean_filter(language="es") == 0
        filter_class.assert_called_once_with(language="es", python_version=None)

    @patch("legesher_core.git_filter.GitFilter")
    def test_smudge_filter(self, filter_class):
        filter_class.return_value.smudge.return_value = 0
        assert smudge_filter(language="ar", python_version="3.13") == 0
        filter_class.assert_called_once_with(language="ar", python_version="3.13")
