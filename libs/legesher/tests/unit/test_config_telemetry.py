"""Telemetry consent comes from the user config only (CORE-1784).

``LegesherConfig.load()`` merges the project config over the user config,
section by section. Telemetry is the exception: a project config, which is
usually committed, must not opt every collaborator into repo attribution or
switch a user's telemetry back on, and must not reset the user's choice by
merely existing. ``legesher config get`` reports what the runtime uses.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from legesher.cli.main import cli
from legesher.config import LegesherConfig
from legesher_core.repo_attribution import repo_label, telemetry_enabled

ENV: dict[str, str] = {}  # no kill switches: only the config decides


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "home"
    (path / ".legesher").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(path))
    monkeypatch.setenv("USERPROFILE", str(path))
    for name in ("LEGESHER_TELEMETRY_DISABLED", "DO_NOT_TRACK"):
        monkeypatch.delenv(name, raising=False)
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "remote",
            "add",
            "origin",
            "https://github.com/acme/app.git",
        ],
        check=True,
    )
    return path


def _write(path: Path, text: str | None) -> None:
    if text is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _runtime(repo: Path, home: Path) -> tuple[dict, str | None]:
    merged = LegesherConfig.load(repo).to_dict()
    return merged, repo_label(repo, config=merged, env=ENV, home=home)


def _cli_get(repo: Path, key: str, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.chdir(repo)
    result = CliRunner().invoke(cli, ["config", "get", key])
    assert result.exit_code == 0, result.output
    return result.output.strip()


@pytest.mark.parametrize(
    ("user_yaml", "project_yaml", "enabled", "attribution", "labelled"),
    [
        pytest.param(
            "telemetry:\n  repo_attribution: true\n",
            "language: es\n",
            True,
            True,
            True,
            id="A: the user's opt-in survives a project config without telemetry",
        ),
        pytest.param(
            "telemetry:\n  enabled: false\n",
            "language: es\n",
            False,
            False,
            False,
            id="B: the user's opt-out survives a project config without telemetry",
        ),
        pytest.param(
            "telemetry:\n  enabled: false\n",
            "telemetry:\n  repo_attribution: true\n",
            False,
            False,
            False,
            id="C: a committed project config cannot opt a user in",
        ),
        pytest.param(
            None,
            "telemetry:\n  enabled: true\n  repo_attribution: true\n",
            True,
            False,
            False,
            id="D: with no user config, the project's opt-in is ignored",
        ),
        pytest.param(
            "telemetry:\n  enabled: true\n  repo_attribution: true\n",
            "telemetry:\n  enabled: false\n",
            True,
            True,
            True,
            id="E: a project config cannot switch a user's choice off either",
        ),
    ],
)
def test_telemetry_is_read_from_the_user_config_only(
    home: Path,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    user_yaml: str | None,
    project_yaml: str,
    enabled: bool,
    attribution: bool,
    labelled: bool,
) -> None:
    _write(home / ".legesher" / "config.yml", user_yaml)
    _write(repo / ".legesher" / "config.yml", project_yaml)

    merged, label = _runtime(repo, home)
    assert merged["telemetry"] == {"enabled": enabled, "repo_attribution": attribution}
    assert telemetry_enabled(merged, env=ENV) is enabled
    assert (label is not None) is labelled
    if project_yaml.startswith("language"):
        assert merged["language"] == "es", "the rest of the project config still wins"

    # `legesher config get` reports exactly what the runtime uses.
    assert _cli_get(repo, "telemetry.enabled", monkeypatch) == str(enabled).lower()
    assert (
        _cli_get(repo, "telemetry.repo_attribution", monkeypatch)
        == str(attribution).lower()
    )


@pytest.mark.parametrize("word", ["off", "no", "false", "OFF"])
def test_a_false_word_in_the_user_config_switches_telemetry_off(
    home: Path, repo: Path, word: str
) -> None:
    _write(
        home / ".legesher" / "config.yml",
        f"telemetry:\n  enabled: {word!r}\n  repo_attribution: true\n",
    )
    merged, label = _runtime(repo, home)
    assert telemetry_enabled(merged, env=ENV) is False
    assert label is None


@pytest.mark.parametrize("word", ["true", "yes", "on", "off"])
def test_a_string_never_opts_in(home: Path, repo: Path, word: str) -> None:
    _write(
        home / ".legesher" / "config.yml",
        f"telemetry:\n  repo_attribution: {word!r}\n",
    )
    _merged, label = _runtime(repo, home)
    assert label is None


@pytest.mark.parametrize("where", ["user", "project"])
def test_a_null_telemetry_section_reads_as_empty(
    home: Path, repo: Path, where: str
) -> None:
    target = home if where == "user" else repo
    _write(target / ".legesher" / "config.yml", "language: ar\ntelemetry: null\n")
    config = LegesherConfig.load(repo)
    assert config.language == "ar", "the rest of the file still loads"
    assert config.telemetry_enabled is True
    assert config.telemetry_repo_attribution is False
    assert LegesherConfig.from_dict({"telemetry": None}).telemetry_enabled is True


def test_telemetry_false_as_a_whole_section_is_off(home: Path, repo: Path) -> None:
    _write(home / ".legesher" / "config.yml", "telemetry: false\n")
    merged, label = _runtime(repo, home)
    assert telemetry_enabled(merged, env=ENV) is False
    assert label is None


def test_config_set_refuses_telemetry_in_the_project_config(
    home: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = repo / ".legesher" / "config.yml"
    _write(project, "language: es\n")
    monkeypatch.chdir(repo)
    runner = CliRunner()

    refused = runner.invoke(
        cli, ["config", "set", "telemetry.repo_attribution", "true"]
    )
    assert refused.exit_code != 0
    assert "--global" in refused.output
    assert project.read_text(encoding="utf-8") == "language: es\n"

    accepted = runner.invoke(
        cli, ["config", "set", "--global", "telemetry.repo_attribution", "true"]
    )
    assert accepted.exit_code == 0, accepted.output
    _merged, label = _runtime(repo, home)
    assert label is not None


def test_saving_the_user_config_keeps_the_users_telemetry_choice(home: Path) -> None:
    user_file = home / ".legesher" / "config.yml"
    _write(user_file, "language: ar\ntelemetry:\n  enabled: false\n")
    LegesherConfig(language="es").save_user_config()
    data = yaml.safe_load(user_file.read_text(encoding="utf-8"))
    assert data["language"] == "es"
    assert data["telemetry"] == {"enabled": False}


def test_saving_a_project_config_writes_no_telemetry(repo: Path) -> None:
    path = LegesherConfig(language="es").save_project_config(repo)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["language"] == "es"
    assert "telemetry" not in data
