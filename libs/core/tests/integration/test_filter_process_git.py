"""The long-running filter process under real git (CORE-2297).

Git drives ``python -m legesher_core --process`` exactly as it would drive
the configured ``legesher-filter --process``. What is asserted is what git
stores and how many filter processes one git command starts, counted from
git's own trace2 events, never from a hook in the code under test.
"""

import json
import os
import shlex
import subprocess
import sys

import pytest

from legesher_core.filter_process import BatchStoredReader
from legesher_core.git_filter import GitFilter
from legesher_core.stored_form import keyword_table, smudge_text
from tests.corpus import corpus_for
from tests.interpreter_gaps import PURE_PYTHON_TOKENIZER

FILTER = f"{shlex.quote(sys.executable)} -m legesher_core"
RUNNING = f"{sys.version_info.major}.{sys.version_info.minor}"


def git(repo, *args, env=None, stdin=None):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, env=env, input=stdin
    ).stdout


def make_repo(tmp_path, language="es", process=True):
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "core.autocrlf", "false")
    if process:
        git(
            repo,
            "config",
            "filter.legesher.process",
            f"{FILTER} --process --language {language}",
        )
    else:
        git(
            repo,
            "config",
            "filter.legesher.clean",
            f"{FILTER} --clean --language {language} --path %f",
        )
    git(repo, "config", "filter.legesher.required", "false")
    (repo / ".gitattributes").write_text("*.py filter=legesher\n")
    git(repo, "add", ".gitattributes")
    git(repo, "commit", "-q", "-m", "attributes")
    return repo


def filter_starts(trace) -> int:
    count = 0
    for line in trace.read_text().splitlines():
        event = json.loads(line)
        if event.get("event") == "child_start" and any(
            "legesher_core" in arg for arg in event.get("argv", [])
        ):
            count += 1
    return count


class TestUnderGit:
    def test_one_process_serves_every_file_in_a_git_add(self, tmp_path):
        repo = make_repo(tmp_path)
        for index in range(12):
            (repo / f"m{index}.py").write_text(
                f"definir f{index}(x):\n    si x:\n        return {index}\n"
            )
        trace = tmp_path / "trace.json"
        env = dict(os.environ, GIT_TRACE2_EVENT=str(trace))
        git(repo, "add", ".", env=env)
        assert filter_starts(trace) == 1
        assert git(repo, "cat-file", "blob", ":0:m7.py").decode() == (
            "definir f7(x):\n    si x:\n        devolver 7\n"
        )

    def test_status_after_a_touch_is_clean_and_uses_one_process(self, tmp_path):
        repo = make_repo(tmp_path)
        for index in range(8):
            (repo / f"m{index}.py").write_text(
                f"definir f{index}(x):\n    si x:\n        return {index}\n"
            )
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "files")
        for index in range(8):
            os.utime(repo / f"m{index}.py", (1, 1))
        trace = tmp_path / "trace.json"
        env = dict(os.environ, GIT_TRACE2_EVENT=str(trace))
        assert git(repo, "status", "--porcelain", env=env) == b""
        assert filter_starts(trace) == 1

    def test_the_committed_version_decides_the_block(self, tmp_path):
        # Mid-edit, the text parses under no reading, so only the committed
        # version can say the block is Spanish; the stray must still move.
        repo = make_repo(tmp_path)
        (repo / "m.py").write_text("definir f(x):\n    devolver x\n")
        git(repo, "add", "m.py")
        git(repo, "commit", "-q", "-m", "spanish")
        (repo / "m.py").write_text("definir f(x)\n    return x\n")
        git(repo, "add", "m.py")
        assert git(repo, "cat-file", "blob", ":0:m.py") == (
            "definir f(x)\n    devolver x\n".encode()
        )


#: On CPython 3.10/3.11 the pure-Python tokenizer reads a Hindi keyword (a
#: virama or vowel sign) as fragments, so no block is identified and both
#: filters store every file unchanged: equal, and vacuous (interpreter_gaps.py
#: gap 1). The ``nothing was normalized`` checks below catch exactly that.
HINDI_KEYWORDS_FRAGMENT = pytest.mark.xfail(
    PURE_PYTHON_TOKENIZER,
    strict=True,
    reason="CORE-2192: pure-Python tokenize fragments Hindi keywords, so the "
    "filter normalizes nothing (interpreter_gaps.py gap 1)",
)

LANGUAGES = (
    "es",
    "ar",
    pytest.param("hi", marks=HINDI_KEYWORDS_FRAGMENT),
    "zh",
    "am",
)


def corpus_with_strays(language: str) -> dict[str, bytes]:
    """Every corpus file rendered in the pack's keywords, then with each
    rendered ``return`` put back in English, so clean has strays to fix."""
    table = keyword_table(language)
    texts = {}
    for entry in corpus_for(RUNNING):
        rendered = smudge_text(entry.source, reader=table)
        texts[entry.name] = rendered.replace(table.spell("return"), "return").encode()
    return texts


def stored_through_git(tmp_path, language, texts, *, process):
    repo = make_repo(tmp_path, language=language, process=process)
    for name, data in texts.items():
        (repo / name).write_bytes(data)
    git(repo, "add", ".")
    return {name: git(repo, "cat-file", "blob", f":0:{name}") for name in texts}


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_process_stores_what_the_single_file_filter_computes(tmp_path, language):
    """Through git and the process, against the single-file filter's own
    function (``GitFilter.clean_text``, which ``legesher-filter --clean``
    wraps) on the same bytes. New files have no stored version."""
    texts = corpus_with_strays(language)
    stored = stored_through_git(tmp_path, language, texts, process=True)
    single = GitFilter(language=language, stored_reader=lambda path: None)
    expected = {
        name: single.clean_text(data.decode(), name).encode()
        for name, data in texts.items()
    }
    assert stored == expected
    assert any(stored[name] != texts[name] for name in texts), "nothing was normalized"


@HINDI_KEYWORDS_FRAGMENT
def test_byte_identical_to_the_single_file_command_under_git(tmp_path):
    """Both filters driven by git, Devanagari (combining marks) end to end."""
    texts = corpus_with_strays("hi")
    by_process = stored_through_git(tmp_path / "process", "hi", texts, process=True)
    by_command = stored_through_git(tmp_path / "single", "hi", texts, process=False)
    assert by_process == by_command
    assert any(by_process[name] != texts[name] for name in texts), (
        "nothing was normalized"
    )


class TestBatchStoredReader:
    @pytest.fixture
    def repo(self, tmp_path):
        git(tmp_path, "init", "-q")
        git(tmp_path, "config", "user.email", "test@example.com")
        git(tmp_path, "config", "user.name", "Test")
        return tmp_path

    def test_head_wins_over_a_staged_version(self, repo):
        (repo / "a b.py").write_text("committed\n")
        git(repo, "add", "a b.py")
        git(repo, "commit", "-q", "-m", "c")
        (repo / "a b.py").write_text("staged\n")
        git(repo, "add", "a b.py")
        reader = BatchStoredReader(cwd=str(repo))
        try:
            assert reader("a b.py") == "committed\n"
        finally:
            reader.close()

    def test_the_index_for_a_path_never_committed(self, repo):
        (repo / "new.py").write_text("staged\n")
        git(repo, "add", "new.py")
        reader = BatchStoredReader(cwd=str(repo))
        try:
            assert reader("new.py") == "staged\n"
            assert reader("absent.py") is None
        finally:
            reader.close()

    def test_answers_match_the_per_file_lookup(self, repo):
        from legesher_core.git_filter import read_stored_blob

        for name, text in {
            "x.py": "x = 1\n",
            "d/ñ.py": "ñ = 2\n",
            ":c.py": "c = 3\n",
        }.items():
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_text(text)
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "c")
        reader = BatchStoredReader(cwd=str(repo))
        try:
            for name in ("x.py", "d/ñ.py", ":c.py", "missing.py"):
                assert reader(name) == read_stored_blob(name, cwd=repo), name
        finally:
            reader.close()

    @pytest.mark.skipif(sys.platform == "win32", reason="a CR in a file name")
    def test_a_path_ending_in_cr_is_not_read_as_another_path(self, repo):
        # Review of CORE-2297: cat-file --batch strips a trailing CR from its
        # input line, so "m\r" was answered with "m"'s committed version.
        from legesher_core.git_filter import read_stored_blob

        (repo / "m").write_text("plain\n")
        (repo / "m\r").write_text("with cr\n")
        git(repo, "add", "m", "m\r")
        git(repo, "commit", "-q", "-m", "c")
        reader = BatchStoredReader(cwd=str(repo))
        try:
            assert reader("m\r") == read_stored_blob("m\r", cwd=repo) == "with cr\n"
        finally:
            reader.close()

    def test_falls_back_to_the_per_file_lookup_when_the_batch_dies(self, repo):
        (repo / "x.py").write_text("x = 1\n")
        git(repo, "add", "x.py")
        git(repo, "commit", "-q", "-m", "c")
        reader = BatchStoredReader(cwd=str(repo))
        try:
            assert reader("x.py") == "x = 1\n"
            reader._process.kill()
            reader._process.wait()
            reader._process.stdin.close()
            assert reader("x.py") == "x = 1\n"
        finally:
            reader.close()


def test_the_entry_point_speaks_the_protocol(tmp_path):
    """``legesher-filter --process`` over real pipes: handshake and one file."""

    def pkt(data: bytes) -> bytes:
        return f"{len(data) + 4:04x}".encode() + data

    session = (
        pkt(b"git-filter-client\n")
        + pkt(b"version=2\n")
        + b"0000"
        + pkt(b"capability=clean\n")
        + pkt(b"capability=smudge\n")
        + b"0000"
        + pkt(b"command=clean\n")
        + pkt(b"pathname=m.py\n")
        + b"0000"
        + pkt("definir f(x):\n    si x:\n        return 1\n".encode())
        + b"0000"
    )
    result = subprocess.run(
        [sys.executable, "-m", "legesher_core", "--process", "--language", "es"],
        input=session,
        capture_output=True,
        cwd=tmp_path,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert b"capability=clean\n" in result.stdout
    assert b"capability=smudge\n" not in result.stdout
    assert b"status=success\n" in result.stdout
    assert "devolver 1".encode() in result.stdout


def test_the_entry_point_offers_smudge_only_when_opted_in(tmp_path):
    def pkt(data: bytes) -> bytes:
        return f"{len(data) + 4:04x}".encode() + data

    session = (
        pkt(b"git-filter-client\n")
        + pkt(b"version=2\n")
        + b"0000"
        + pkt(b"capability=clean\n")
        + pkt(b"capability=smudge\n")
        + b"0000"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "legesher_core",
            "--process",
            "--keyword-smudge",
            "--language",
            "es",
        ],
        input=session,
        capture_output=True,
        cwd=tmp_path,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert b"capability=smudge\n" in result.stdout


def test_git_filter_stays_importable_for_old_callers():
    assert GitFilter(language="es").stored_version(None) is None
