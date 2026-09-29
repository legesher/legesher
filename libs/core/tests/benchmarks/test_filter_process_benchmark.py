"""`git add` over a few hundred files: one Python per file, then one process.

CORE-2297. The single-file filter starts Python, imports the engine and loads
a pack for every file; the long-running process does that once per git
command. Timing runs only under ``make bench``: in the default run these
benchmarks are skipped rather than run once, because the single-file case
starts Python three hundred times. The per-commit guarantee is structural
instead (one filter process per git command, counted from git's trace2
events in ``tests/integration/test_filter_process_git.py``).
"""

import shlex
import subprocess
import sys

import pytest

FILES = 300
FILTER = f"{shlex.quote(sys.executable)} -m legesher_core"
COMMANDS = {
    "single-file": ("clean", f"{FILTER} --clean --language es --path %f"),
    "process": ("process", f"{FILTER} --process --language es"),
}


@pytest.fixture
def timing_on(request):
    config = request.config
    if config.getoption("benchmark_disable") and not config.getoption(
        "benchmark_enable"
    ):
        pytest.skip("timing runs only under make bench")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.mark.parametrize("mode", list(COMMANDS))
def test_git_add_of_300_files(benchmark, timing_on, tmp_path, mode):
    key, command = COMMANDS[mode]
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", f"filter.legesher.{key}", command)
    git(repo, "config", "filter.legesher.required", "false")
    (repo / ".gitattributes").write_text("*.py filter=legesher\n")
    for index in range(FILES):
        (repo / f"m{index:03}.py").write_text(
            f"definir f{index}(x):\n    si x:\n        return {index}\n"
        )

    def unstage():
        subprocess.run(
            ["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", "."],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        return (), {}

    benchmark.extra_info["files"] = FILES
    benchmark.pedantic(
        lambda: git(repo, "add", "."), setup=unstage, rounds=3, iterations=1
    )
    stored = subprocess.run(
        ["git", "cat-file", "blob", ":0:m007.py"],
        cwd=repo,
        capture_output=True,
        check=True,
    ).stdout.decode()
    assert stored == "definir f7(x):\n    si x:\n        devolver 7\n"
