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
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
from semantic_release.cli.config import RawConfig

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"
SKIP_MARKER = "chore(release)"


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
        pattern = re.compile(rf"^{re.escape(key)}\s*=\s*['\"]", re.M)
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
    assert section.get("commit_parser") == "conventional", (
        f"{config}: commit_parser {section.get('commit_parser')!r}; 'angular' is removed in PSR 11"
    )
    options = section.get("commit_parser_options", {})
    for key in ("parse_squash_commits", "ignore_merge_commits"):
        assert options.get(key) is False, (
            f"{config}: commit_parser_options.{key} must be pinned to false; "
            "the conventional parser's default differs from angular's"
        )


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
