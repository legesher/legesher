"""Guard for every ``[tool.semantic_release]`` config in the workspace (CORE-1852).

python-semantic-release resolves every configured path against the git root:
it finds ``repo_dir`` by walking up to ``.git/`` and never looks at the config
file's own directory or the working directory. A pack config that said
``version_toml = "pyproject.toml:project.version"`` therefore read, and on a
real run would have rewritten, the ROOT ``pyproject.toml``. PSR 10 also
rejects that bare-string form outright, and it ignores keys it does not know
(``version_variable``, a top-level ``upload_to_vcs_release``), so a config can
look complete and move nothing. No pack had ever been released, which is why
none of it had surfaced.

Each config is loaded through PSR's own ``RawConfig`` model, and then checked
for what the model cannot see: every path lies inside the package that owns
the config and exists; the release commit's subject matches the
``chore(release)`` skip the workflows use; tag formats cannot collide; nothing
is spelled in a way PSR ignores. The configs come from the ``pyproject.toml``
files under git, never from a list.

Two release-hygiene rules ride the same configs. Each train counts only the
commits that change its own packages (CORE-2627), checked by running PSR's own
parser over probe commits in a scratch repository. The foundation release
attaches only the three packages, never the root workspace package, and no
commit a train writes names a ticket (CORE-2604).

The workflows that run the trains are checked here too. Each train pushes once
(CORE-2933): ``semantic-release version --no-push`` commits and tags in the
runner, the lock and changelog commits join them, and one ``git push --atomic``
sends the commits and the tag together. semantic-release's own push sends the
commit and then the tag; when GitHub refused the tag, main kept a version no
tag matched, and the train could not run again. Without its push
semantic-release creates no GitHub release, so each train posts the release
for its tag after the push.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml
from git import Repo
from semantic_release.cli.config import RawConfig
from semantic_release.commit_parser import (
    ConventionalCommitMonorepoParser,
    ConventionalCommitMonorepoParserOptions,
    ParsedCommit,
)
from semantic_release.enums import LevelBump

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"
SKIP_MARKER = "chore(release)"
STAMP_SUBJECT = "docs(changelog): stamp release"
STAMP_SKIP = "docs(changelog): stamp"
TICKET = re.compile(r"\[[A-Z]+-\d+\]")
FOUNDATION = "pyproject.toml"


def _tracked_pyprojects() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z", "--", "pyproject.toml", "*/pyproject.toml"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    return [REPO / p for p in output.decode().split("\0") if p]


def _section(pyproject: Path) -> dict[str, Any] | None:
    document = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return document.get("tool", {}).get("semantic_release")


CONFIGS = {
    pyproject.relative_to(REPO).as_posix(): section
    for pyproject in _tracked_pyprojects()
    if (section := _section(pyproject)) is not None
}
RELEASE_WORKFLOWS = sorted(p.name for p in WORKFLOWS.glob("release-*.yml"))

configs = pytest.mark.parametrize("config", sorted(CONFIGS), ids=str)


def _owner(config: str) -> Path:
    """The directory whose package this config releases, relative to the root."""
    return Path(config).parent


def _inside(path: str, owner: Path) -> bool:
    """True when ``path`` stays inside ``owner`` without climbing out.

    ``is_relative_to`` does not normalise ``..``, so a path that climbs to the
    root through the owner's directory is rejected by name.
    """
    candidate = Path(path)
    if ".." in candidate.parts or candidate.is_absolute():
        return False
    return owner == Path(".") or candidate.is_relative_to(owner)


def _package_dirs(config: str) -> list[str]:
    """The directories of the packages a config versions, read from its version_toml.

    The root config versions the root ``pyproject.toml`` too, but the root
    workspace package is never published, so the root itself is not one of them.
    """
    dirs = {
        Path(entry.partition(":")[0]).parent.as_posix()
        for entry in CONFIGS[config].get("version_toml", [])
    }
    dirs.discard(".")
    return sorted(dirs)


def test_the_discovery_found_every_train() -> None:
    assert len(CONFIGS) >= 4, f"only {sorted(CONFIGS)} carry a semantic-release config"
    assert "pyproject.toml" in CONFIGS, "the foundation (root) config is missing"


@configs
def test_psr_10_loads_the_config(config: str) -> None:
    RawConfig.model_validate(CONFIGS[config])


@configs
def test_no_key_psr_ignores(config: str) -> None:
    """A key PSR does not read is a setting that is not in force.

    ``version_variable`` (singular) and the top-level ``upload_to_vcs_release``
    and ``upload_to_pypi`` were all silently dropped by PSR 10.
    """
    unknown = sorted(set(CONFIGS[config]) - set(RawConfig.model_fields))
    assert not unknown, f"{config}: PSR 10 ignores {unknown}"


@configs
def test_version_files_belong_to_the_owner(config: str) -> None:
    section = CONFIGS[config]
    owner = _owner(config)
    toml_entries = section.get("version_toml")
    assert isinstance(toml_entries, list) and toml_entries, (
        f"{config}: version_toml must be a non-empty list, got {toml_entries!r}"
    )
    assert f"{config}:project.version" in toml_entries, (
        f"{config}: version_toml does not name this file's own project.version"
    )
    for entry in [*toml_entries, *section.get("version_variables", [])]:
        path, _, key = entry.partition(":")
        assert key, f"{config}: {entry!r} has no :key"
        assert _inside(path, owner), f"{config}: {entry!r} lies outside {owner}/"
        assert (REPO / path).is_file(), f"{config}: {entry!r} does not exist"
    for entry in section.get("version_variables", []):
        path, _, key = entry.partition(":")
        # PSR's own search accepts `=` or `:` after the key, so a JSON file
        # (`"version": "x.y.z"`, key spelled with its quotes) qualifies as
        # well as a Python or TOML `__version__ = "x.y.z"`.
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*[:=]\s*['\"]", re.M)
        assert pattern.search((REPO / path).read_text(encoding="utf-8")), (
            f"{config}: {path} declares no {key}"
        )


@configs
def test_changelog_and_dist_belong_to_the_owner(config: str) -> None:
    section = CONFIGS[config]
    owner = _owner(config)
    loaded = RawConfig.model_validate(section)
    changelog = loaded.changelog.default_templates.changelog_file
    if owner != Path("."):
        assert "default_templates" in section.get("changelog", {}), (
            f"{config}: changelog_file is not set, so a run without --no-changelog "
            "rewrites the repo-root CHANGELOG.md"
        )
    assert _inside(changelog, owner), f"{config}: changelog_file {changelog!r} lies outside {owner}/"
    assert (REPO / changelog).is_file(), f"{config}: changelog_file {changelog!r} does not exist"
    for pattern in loaded.publish.dist_glob_patterns:
        assert _inside(pattern, owner), (
            f"{config}: dist_glob_patterns entry {pattern!r} lies outside {owner}/, "
            "so the GitHub release would get no wheel"
        )


@configs
def test_release_commit_matches_the_workflow_skip(config: str) -> None:
    message = CONFIGS[config].get("commit_message", "")
    assert message.startswith(f"{SKIP_MARKER}:"), (
        f"{config}: commit_message {message!r} does not start with '{SKIP_MARKER}:', "
        "so the release commit retriggers its own train and ci.yml"
    )
    assert "{version}" in message, f"{config}: commit_message carries no {{version}}"


@configs
def test_release_commit_author_is_an_email_address(config: str) -> None:
    """PSR's default author is a bare word with no ``@``, which author-validating
    tooling downstream rejects."""
    author = CONFIGS[config].get("commit_author", "")
    assert "@" in author, f"{config}: commit_author {author!r} is not an email address"


@configs
def test_parser_is_conventional_with_pinned_defaults(config: str) -> None:
    section = CONFIGS[config]
    assert section.get("commit_parser") == "conventional-monorepo", (
        f"{config}: commit_parser {section.get('commit_parser')!r}; the plain 'conventional' "
        "parser counts every commit in the repository, and 'angular' is removed in PSR 11"
    )
    options = section.get("commit_parser_options", {})
    for key in ("parse_squash_commits", "ignore_merge_commits"):
        assert options.get(key) is False, (
            f"{config}: commit_parser_options.{key} must be pinned to false; "
            "the conventional parser's default differs from angular's"
        )


@configs
def test_path_filters_name_the_packages_the_config_versions(config: str) -> None:
    filters = CONFIGS[config].get("commit_parser_options", {}).get("path_filters")
    assert filters, (
        f"{config}: commit_parser_options.path_filters is not set, so the train counts "
        "every commit in the repository"
    )
    assert sorted(filters) == _package_dirs(config), (
        f"{config}: path_filters {filters!r} differ from the packages it versions, "
        f"{_package_dirs(config)!r}"
    )


@pytest.fixture(scope="module")
def probe_repo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    """A scratch repository with one ``fix:`` commit per package directory.

    Returns its root and the commit sha for each directory, plus ``"."`` for a
    commit that changes only a root file.
    """
    root = tmp_path_factory.mktemp("probe-repo")
    repo = Repo.init(root)
    writer = repo.config_writer()
    writer.set_value("user", "name", "probe")
    writer.set_value("user", "email", "probe@example.invalid")
    writer.release()
    shas: dict[str, str] = {}
    dirs = sorted({d for config in CONFIGS for d in _package_dirs(config)})
    for directory in [".", *dirs]:
        target = root / directory / "probe.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(directory, encoding="utf-8")
        repo.index.add([target.relative_to(root).as_posix()])
        shas[directory] = repo.index.commit(f"fix: probe {directory}").hexsha
    return root, shas


@configs
def test_a_train_counts_only_its_own_packages_commits(
    config: str,
    probe_repo: tuple[Path, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``fix:`` in the config's own package bumps it; one anywhere else does not.

    PSR resolves ``path_filters`` against the working directory, and every
    train runs from the repository root, so the probe runs from the scratch
    repository's root.
    """
    root, shas = probe_repo
    monkeypatch.chdir(root)
    loaded = RawConfig.model_validate(CONFIGS[config])
    parser = ConventionalCommitMonorepoParser(
        ConventionalCommitMonorepoParserOptions(**loaded.commit_parser_options)
    )
    repo = Repo(root)

    def bump(directory: str) -> LevelBump:
        [result] = parser.parse(repo.commit(shas[directory]))
        return result.bump if isinstance(result, ParsedCommit) else LevelBump.NO_RELEASE

    own = _package_dirs(config)
    elsewhere = [".", next(d for d in ("libs/core", "libs/mcp") if d not in own)]
    for directory in own:
        assert bump(directory) == LevelBump.PATCH, (
            f"{config}: a fix: under {directory}/ does not bump it"
        )
    for directory in elsewhere:
        assert bump(directory) == LevelBump.NO_RELEASE, (
            f"{config}: a fix: under {directory}/ bumps it, though it versions only {own}"
        )


def test_the_foundation_release_carries_no_root_package() -> None:
    """The root config builds and uploads only the three foundation packages.

    ``build_command = "uv build"`` at the root built the root workspace
    package, and ``dist/*`` uploaded it to every foundation GitHub release.
    """
    loaded = RawConfig.model_validate(CONFIGS[FOUNDATION])
    packages = _package_dirs(FOUNDATION)
    steps = re.split(r"&&|\|\||[;\n]", loaded.build_command or "")
    for step in filter(None, (s.strip() for s in steps)):
        assert "--package" in step or any(d in step for d in packages), (
            f"{FOUNDATION}: build_command step {step!r} builds the root workspace package"
        )
    # Checked whatever upload_to_vcs_release says: PSR 10.6.1 stores that flag
    # and never reads it, so `semantic-release publish` uploads every glob.
    for pattern in loaded.publish.dist_glob_patterns:
        assert any(_inside(pattern, Path(d)) for d in packages), (
            f"{FOUNDATION}: publish.dist_glob_patterns entry {pattern!r} lies outside "
            f"{packages}, so the GitHub release attaches the root workspace package"
        )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS, ids=str)
def test_train_commits_name_no_ticket(workflow: str) -> None:
    """A train's own commits land on main and in every release; a ticket id there
    names whatever ticket wrote the line, long after it closed."""
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    for message in re.findall(r"git commit\b[^\n]*?-m\s+\"([^\"]+)\"", text):
        assert not TICKET.search(message), f"{workflow}: the train commits {message!r}"


STAMPING_WORKFLOWS = [
    name
    for name in RELEASE_WORKFLOWS
    if "stamp-changelog-release.py" in (WORKFLOWS / name).read_text(encoding="utf-8")
]


def test_the_discovery_found_every_stamping_train() -> None:
    assert len(STAMPING_WORKFLOWS) >= 4, f"only {STAMPING_WORKFLOWS} stamp a changelog"


@pytest.mark.parametrize("workflow", STAMPING_WORKFLOWS, ids=str)
def test_stamp_commits_match_the_skip(workflow: str) -> None:
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    subjects = re.findall(r"git commit\b[^\n]*?-m\s+\"(docs\(changelog\)[^\"]*)\"", text)
    assert subjects, f"{workflow}: stamps a changelog but commits no {STAMP_SUBJECT!r}"
    assert set(subjects) == {STAMP_SUBJECT}, f"{workflow}: stamp subjects {subjects}"
    assert STAMP_SKIP in text, f"{workflow}: no {STAMP_SKIP!r} skip for its stamp commit"


def test_tag_formats_cannot_collide() -> None:
    formats = {config: section.get("tag_format", "") for config, section in CONFIGS.items()}
    for config, tag_format in formats.items():
        assert "{version}" in tag_format, f"{config}: tag_format {tag_format!r} has no {{version}}"
    duplicates = {
        tag_format: [c for c, f in formats.items() if f == tag_format]
        for tag_format in set(formats.values())
        if list(formats.values()).count(tag_format) > 1
    }
    assert not duplicates, f"two trains share a tag_format: {duplicates}"


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS, ids=str)
def test_release_trains_skip_their_own_release_commit(workflow: str) -> None:
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    assert SKIP_MARKER in text, (
        f"{workflow}: no '{SKIP_MARKER}' skip, so a release commit retriggers the train"
    )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS, ids=str)
def test_per_package_trains_run_from_the_root_without_a_changelog(workflow: str) -> None:
    """A per-package `version` names its config with -c and passes --no-changelog.

    Changelogs here are hand-written and stamped, never generated, and the
    foundation's root changelog must not be rewritten by another package's
    release.
    """
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    runs_semantic_release = False
    for line in text.splitlines():
        if re.search(r"semantic[-_]release\b.*\bversion\b", line) and " -c " in line:
            assert "--no-changelog" in line, f"{workflow}: {line.strip()!r} lacks --no-changelog"
        if re.search(r"semantic[-_]release\b", line) and not line.lstrip().startswith("#"):
            runs_semantic_release = True
    if runs_semantic_release:
        assert "working-directory:" not in text, (
            f"{workflow}: a step runs from a working-directory; semantic-release "
            "resolves paths against the git root regardless, so every train runs "
            "from the root with an explicit -c (CORE-1852)"
        )


# One atomic push per train (CORE-2933). Every workflow is read, not only the
# release-*.yml files, so a release cut from anywhere is held to the same rule.
VERSION_CALL = re.compile(
    r"\bsemantic[-_]release\b(?:\s+(?:-c|--config)\s+\S+|\s+-[-\w]+)*\s+version\b"
)
# `version` flags that only print or rehearse: such a call commits, tags and
# pushes nothing.
PRINT_ONLY = re.compile(r"\s--(?:print\S*|noop)\b")
RELEASE_POST = re.compile(r"\bsemantic[-_]release\b.*\schangelog\s+--post-to-release-tag\b")
TAG_FROM_VERSION_STEP = "${{ steps.semantic-release.outputs.tag }}"
MAIN_REFSPECS = {"main", "main:main", "HEAD:main", "HEAD:refs/heads/main", "refs/heads/main"}


def _commands(script: str) -> list[str]:
    """A step's ``run`` as commands: continuation lines joined, comments and
    blank lines dropped, so a flag on a continuation line still counts."""
    commands: list[str] = []
    pending = ""
    for raw in script.splitlines():
        line = raw.strip()
        if not pending and (not line or line.startswith("#")):
            continue
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        commands.append(pending + line)
        pending = ""
    if pending:
        commands.append(pending.strip())
    return commands


def _jobs(workflow: str) -> dict[str, list[dict[str, Any]]]:
    document = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    return {name: job.get("steps") or [] for name, job in (document.get("jobs") or {}).items()}


def _step_commands(steps: list[dict[str, Any]]) -> list[tuple[int, str]]:
    """Every command of a job, with the index of the step that runs it."""
    return [
        (index, command)
        for index, step in enumerate(steps)
        for command in _commands(step.get("run") or "")
    ]


def _cuts_a_release(command: str) -> bool:
    return bool(VERSION_CALL.search(command)) and not PRINT_ONLY.search(command)


def _config_flag(command: str) -> str | None:
    """The config a semantic-release command names with -c, or None for the root's."""
    tokens = shlex.split(command)
    for flag in ("-c", "--config"):
        if flag in tokens[:-1]:
            return tokens[tokens.index(flag) + 1]
    return None


ALL_WORKFLOWS = sorted(p.name for p in [*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
VERSIONING_JOBS = [
    (workflow, job)
    for workflow in ALL_WORKFLOWS
    for job, steps in _jobs(workflow).items()
    if any(_cuts_a_release(command) for _, command in _step_commands(steps))
]
versioning_jobs = pytest.mark.parametrize(
    ("workflow", "job"), VERSIONING_JOBS, ids=[f"{w}:{j}" for w, j in VERSIONING_JOBS]
)


def test_the_discovery_found_every_versioning_job() -> None:
    # Foundation, MCP and language server have one job each; the pack train has
    # two, the push-triggered matrix and the manual dispatch. Every train that
    # stamps a changelog cuts its version in one of them.
    assert len(VERSIONING_JOBS) >= 5, f"only {VERSIONING_JOBS} run semantic-release version"
    versioning = {workflow for workflow, _ in VERSIONING_JOBS}
    assert set(STAMPING_WORKFLOWS) <= versioning, (
        f"{sorted(set(STAMPING_WORKFLOWS) - versioning)} stamp a changelog but no job "
        "in them was recognised as running semantic-release version"
    )


@versioning_jobs
def test_trains_version_without_pushing(workflow: str, job: str) -> None:
    """``version`` leaves the commit and the tag in the runner; the job pushes them."""
    for _, command in _step_commands(_jobs(workflow)[job]):
        if not _cuts_a_release(command):
            continue
        tokens = shlex.split(command)
        assert "--no-push" in tokens and "--push" not in tokens, (
            f"{workflow} job {job!r}: {command!r} lets semantic-release push the release "
            "commit and then its tag, so a refused tag leaves a version on main that no "
            "tag matches (CORE-2933); pass --no-push and push once, with --atomic"
        )


@versioning_jobs
def test_each_train_pushes_once_atomically(workflow: str, job: str) -> None:
    """One push, after every commit and tag the job makes, carrying main and the tag."""
    steps = _jobs(workflow)[job]
    commands = _step_commands(steps)
    pushes = [(index, command) for index, command in commands if command.startswith("git push")]
    assert len(pushes) == 1, (
        f"{workflow} job {job!r} pushes {len(pushes)} times {[c for _, c in pushes]}; "
        "a train sends its commits and its tag in one atomic push (CORE-2933)"
    )
    push_index, push = pushes[0]
    tokens = shlex.split(push)
    assert "--atomic" in tokens, (
        f"{workflow} job {job!r}: {push!r} is not atomic, so GitHub can take main and "
        "refuse the tag"
    )
    refspecs = [t for t in tokens[2:] if not t.startswith("-") and t != "origin"]
    assert MAIN_REFSPECS & set(refspecs), f"{workflow} job {job!r}: {push!r} does not push main"
    assert [r for r in refspecs if r.startswith("refs/tags/")] == ["refs/tags/${TAG}"], (
        f"{workflow} job {job!r}: {push!r} must push exactly the release tag, refs/tags/${{TAG}}"
    )
    assert (steps[push_index].get("env") or {}).get("TAG") == TAG_FROM_VERSION_STEP, (
        f"{workflow} job {job!r}: the push step's TAG is not {TAG_FROM_VERSION_STEP}, the "
        "tag the version step made and checked"
    )
    late = [
        command
        for index, command in commands
        if index >= push_index
        and (command.startswith(("git commit", "git tag")) or _cuts_a_release(command))
    ]
    assert not late, (
        f"{workflow} job {job!r}: {late} run at or after the push, so what they make "
        "never reaches main in it"
    )


@versioning_jobs
def test_each_train_posts_its_release_after_the_push(workflow: str, job: str) -> None:
    """Without its push semantic-release creates no GitHub release, so the job
    posts the release for the tag itself: after the push, from the same config."""
    steps = _jobs(workflow)[job]
    commands = _step_commands(steps)
    push_index = next(
        (index for index, command in commands if command.startswith("git push")), None
    )
    assert push_index is not None, f"{workflow} job {job!r} never pushes"
    configs = {_config_flag(command) for _, command in commands if _cuts_a_release(command)}
    posts = [(index, command) for index, command in commands if RELEASE_POST.search(command)]
    assert posts, (
        f"{workflow} job {job!r} never runs `semantic-release changelog "
        "--post-to-release-tag`, so its releases would have no GitHub release"
    )
    for index, command in posts:
        assert index > push_index, (
            f"{workflow} job {job!r}: {command!r} runs before the push, for a tag "
            "GitHub does not have yet"
        )
        assert _config_flag(command) in configs, (
            f"{workflow} job {job!r}: {command!r} posts with another config than the "
            f"version call ({sorted(map(str, configs))})"
        )
        assert shlex.split(command)[-1] == "${TAG}", (
            f"{workflow} job {job!r}: {command!r} must post for the pushed tag, ${{TAG}}"
        )
        assert (steps[index].get("env") or {}).get("TAG") == TAG_FROM_VERSION_STEP, (
            f"{workflow} job {job!r}: the release step's TAG is not {TAG_FROM_VERSION_STEP}"
        )
