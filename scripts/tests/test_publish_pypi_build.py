"""Guard for the "Build packages" step of ``publish-pypi.yml`` (CORE-2313).

The workflow runs only on a manual dispatch, and it had never been dispatched.
Its ``foundation`` and ``vs-code`` branches built a member's path and then
copied from ``libs/<dir>/dist/``, which uv 0.11 never creates for those
members. A path build lands wherever uv's project discovery puts it: the
workspace root's ``dist/`` for ``libs/core``, but the pack's own ``dist/`` for
a pack under ``libs/i18n``. Both branches would have failed on their first
real run, and ``legesher-mcp`` had no target at all.

The step now names every distribution with ``--package`` and its output with
``--out-dir``. This module runs the step's script, as written in the workflow,
once for every target the dispatch form offers, with ``ALL_LANGS`` from the
workflow's own "Load language list" step. A stub ``uv`` stands in for the real
one. For the forms it models it writes where uv 0.11 writes (``--out-dir`` when
given, otherwise the workspace root's ``dist/``, plus the ``.gitignore`` uv
adds there) and refuses what uv refuses (an unknown distribution, a repeated
``--package``). It refuses a path build outright, because where that lands
depends on project discovery the stub does not model. Each target must leave
exactly its own wheel and sdist in ``dist/``. Nothing is built and nothing is
uploaded.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "publish-pypi.yml"
LANGUAGES = REPO / "libs" / "i18n" / "legesher_i18n" / "languages.json"

# CORE-626's publish set, by dispatch option. `foundation` carries i18n, core
# and the CLI.
PUBLISH_SET = frozenset({"foundation", "mcp", "language-server"})

# GitHub runs a `run:` block on Linux as `bash --noprofile --norc -eo pipefail`.
BASH = ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c"]

# -I -S: the stub needs only the standard library, and skipping site setup
# takes each of the ~140 starts per run from about 90 ms to about 55 ms.
STUB_UV = '''#!{python} -IS
"""Stand-in for `uv build`. Builds nothing; writes where uv 0.11 writes."""
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if args[:1] != ["build"]:
    sys.exit(f"stub uv: only `uv build` is modelled, got {{args}}")
packages, out_dir, source = [], None, None
rest = args[1:]
while rest:
    arg = rest.pop(0)
    if arg == "--package":
        packages.append(rest.pop(0))
    elif arg == "--out-dir":
        out_dir = rest.pop(0)
    elif arg.startswith("-"):
        sys.exit(f"stub uv: option {{arg}} is not modelled")
    else:
        source = arg
if len(packages) > 1:
    print(
        "error: the argument '--package <PACKAGE>' cannot be used multiple times",
        file=sys.stderr,
    )
    sys.exit(2)
if not packages:
    sys.exit(
        f"stub uv: a path build ({{source or '.'}}) lands wherever uv's project "
        "discovery puts it (the root dist/ for libs/core, its own dist/ for a "
        "pack under libs/i18n), which this stub does not model; name the "
        "distribution with --package"
    )
name = packages[0]
if name not in json.loads(os.environ["STUB_UV_MEMBERS"]):
    print(f"error: Package `{{name}}` not found in workspace", file=sys.stderr)
    sys.exit(2)
if name == os.environ.get("STUB_UV_FAIL"):
    print(f"stub uv: the build of {{name}} failed (injected)", file=sys.stderr)
    sys.exit(1)
target = Path(out_dir) if out_dir else Path("dist")
target.mkdir(parents=True, exist_ok=True)
(target / ".gitignore").write_text("*")
stem = name.replace("-", "_")
for filename in (f"{{stem}}-0.0.0-py3-none-any.whl", f"{{stem}}-0.0.0.tar.gz"):
    (target / filename).write_text("")
'''


def _workflow() -> dict[Any, Any]:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _dispatch_options(document: dict[Any, Any]) -> list[str]:
    # YAML 1.1 reads the bare key `on` as the boolean True.
    triggers = document["on"] if "on" in document else document[True]
    return list(triggers["workflow_dispatch"]["inputs"]["package"]["options"])


def _step_script(document: dict[Any, Any], name: str) -> str:
    steps = document["jobs"]["publish"]["steps"]
    matches = [step["run"] for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"publish-pypi.yml has no single {name!r} step"
    return str(matches[0])


def _workspace_members() -> list[str]:
    """Every distribution name the root workspace globs reach."""
    root = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"\[tool\.uv\.workspace\]\s*members\s*=\s*\[(.*?)\]", root, re.S)
    assert block, "root pyproject.toml has no [tool.uv.workspace] members list"
    names: list[str] = []
    for pattern in re.findall(r'"([^"]+)"', block.group(1)):
        for directory in sorted(REPO.glob(pattern)):
            pyproject = directory / "pyproject.toml"
            if not pyproject.is_file():
                continue
            name = re.search(
                r'^name\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M
            )
            assert name, f"{pyproject} has no project name"
            names.append(name.group(1))
    return names


def _expected(option: str, languages: list[str]) -> set[str]:
    if option == "foundation":
        return {"legesher-core", "legesher-i18n", "legesher"}
    if option == "all-language-packs":
        return {f"legesher-i18n-python-{lang}" for lang in languages}
    return {f"legesher-{option}"}


def _built(workspace: Path) -> list[str]:
    # What `twine check dist/*` and the upload see: the shell glob skips the
    # .gitignore uv writes.
    return sorted(
        p.name for p in (workspace / "dist").iterdir() if not p.name.startswith(".")
    )


DOCUMENT = _workflow()
OPTIONS = _dispatch_options(DOCUMENT)
MEMBERS = json.dumps(_workspace_members())

needs_bash = pytest.mark.skipif(
    shutil.which("bash") is None, reason="the workflow steps are bash scripts"
)


@pytest.fixture(scope="module")
def stub_bin(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A directory holding the stub ``uv``, written once for the module.

    Once, because macOS checks every newly written executable on its first
    run, at about 0.3 s each.
    """
    stub_dir = tmp_path_factory.mktemp("bin")
    stub = stub_dir / "uv"
    stub.write_text(STUB_UV.format(python=sys.executable), encoding="utf-8")
    stub.chmod(0o755)
    return stub_dir


@pytest.fixture(scope="module")
def all_langs(tmp_path_factory: pytest.TempPathFactory) -> str:
    """``ALL_LANGS`` as the workflow's "Load language list" step writes it."""
    if shutil.which("bash") is None:
        pytest.skip("the workflow steps are bash scripts")
    output = tmp_path_factory.mktemp("github") / "output"
    output.write_text("")
    subprocess.run(
        [*BASH, _step_script(DOCUMENT, "Load language list from source of truth")],
        cwd=REPO,
        env={**os.environ, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=True,
    )
    values = dict(
        line.split("=", 1) for line in output.read_text().splitlines() if "=" in line
    )
    return values["list"]


def _run_build(
    option: str, stub_bin: Path, all_langs: str, workspace: Path, fail: str = ""
) -> subprocess.CompletedProcess[str]:
    workspace.mkdir()
    env = {
        **os.environ,
        "PATH": f"{stub_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "PACKAGE": option,
        "ALL_LANGS": all_langs,
        "STUB_UV_MEMBERS": MEMBERS,
        "STUB_UV_FAIL": fail,
    }
    return subprocess.run(
        [*BASH, _step_script(DOCUMENT, "Build packages")],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_every_publish_set_package_has_a_target() -> None:
    missing = sorted(PUBLISH_SET - set(OPTIONS))
    assert not missing, f"publish-pypi.yml offers no dispatch option for {missing}"


@needs_bash
def test_the_language_list_is_every_registry_language(all_langs: str) -> None:
    registry = sorted(json.loads(LANGUAGES.read_text(encoding="utf-8"))["languages"])
    assert all_langs.split() == registry, f"the step wrote ALL_LANGS={all_langs!r}"


@needs_bash
@pytest.mark.parametrize("option", OPTIONS)
def test_target_builds_into_dist(
    option: str, stub_bin: Path, all_langs: str, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    proc = _run_build(option, stub_bin, all_langs, workspace)

    assert proc.returncode == 0, (
        f"'Build packages' failed for target {option!r}:\n{proc.stdout}{proc.stderr}"
    )
    built = _built(workspace)
    stems = {name.split("-0.0.0", 1)[0] for name in built}
    expected = {name.replace("-", "_") for name in _expected(option, all_langs.split())}
    assert stems == expected, f"target {option!r} left {built} in dist/"
    assert len(built) == 2 * len(expected), f"target {option!r} left {built} in dist/"


@needs_bash
def test_a_failed_pack_build_fails_the_step(
    stub_bin: Path, all_langs: str, tmp_path: Path
) -> None:
    languages = all_langs.split()
    failing = languages[len(languages) // 2]
    workspace = tmp_path / "workspace"
    proc = _run_build(
        "all-language-packs",
        stub_bin,
        all_langs,
        workspace,
        fail=f"legesher-i18n-python-{failing}",
    )

    assert proc.returncode != 0, "a failed pack build left the step green"
    assert f"Failed to build: {failing}" in proc.stdout, proc.stdout
    # The loop reports every failure rather than stopping at the first one.
    assert len(_built(workspace)) == 2 * (len(languages) - 1)
