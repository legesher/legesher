"""Every writer of ``.legesher/config.yml`` saves the same bytes on every platform.

A file opened in text mode without ``newline=`` turns each ``\\n`` into
``os.linesep``, so on Windows the config was saved with ``\\r\\n``. YAML reads
both, but a project's config shared between Windows and macOS or Linux then
shows as a whole-file diff, and ``legesher config set`` after ``legesher init``
rewrote every line of the file.

On macOS and Linux ``os.linesep`` is already ``\\n``, so the real ``open`` can
never show the defect. The ``windows_text_mode`` fixture swaps in the pure
Python ``_pyio`` implementation, which reads ``os.linesep`` when a file is
opened, and sets ``os.linesep`` to ``\\r\\n``: a text-mode write without
``newline=`` then behaves as it does on Windows, wherever the test runs.
``TestTheSimulation`` proves the fixture still does that, so these tests
cannot pass because the simulation stopped working.
"""

from __future__ import annotations

import _pyio
import builtins
import io
import os
import pathlib
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from legesher.cli.main import cli
from legesher.config import LegesherConfig


@pytest.fixture(autouse=True)
def home(tmp_path_factory, monkeypatch) -> Path:
    """A temporary home, so no test touches ~/.legesher."""
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # Path.home() on Windows
    return home


@pytest.fixture
def windows_text_mode(monkeypatch):
    """Make text-mode writes without ``newline=`` write ``\\r\\n``, as on Windows."""
    monkeypatch.setattr(os, "linesep", "\r\n")
    monkeypatch.setattr(builtins, "open", _pyio.open)
    monkeypatch.setattr(io, "open", _pyio.open)
    # Python 3.10's Path.open goes through an accessor that captured
    # io.open when pathlib was imported; 3.11 and later call io.open.
    accessor = getattr(pathlib, "_NormalAccessor", None)
    if accessor is not None:
        monkeypatch.setattr(accessor, "open", staticmethod(_pyio.open))


def assert_line_feeds_only(raw: bytes, expected: str) -> None:
    assert expected.encode("utf-8") in raw, raw
    assert b"\r" not in raw, raw


class TestTheSimulation:
    """The fixture really produces Windows line endings, or nothing here counts."""

    def test_open_without_newline_writes_crlf(self, tmp_path, windows_text_mode):
        path = tmp_path / "plain.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("एक\nदो\n")
        assert path.read_bytes() == "एक\r\nदो\r\n".encode()

    def test_write_text_without_newline_writes_crlf(self, tmp_path, windows_text_mode):
        path = tmp_path / "plain.txt"
        path.write_text("ශ්‍රී\nලංකා\n", encoding="utf-8")
        assert path.read_bytes() == "ශ්‍රී\r\nලංකා\r\n".encode()


class TestConfigSet:
    def test_a_project_set_writes_line_feeds(
        self, tmp_path, monkeypatch, windows_text_mode
    ):
        config_file = tmp_path / ".legesher" / "config.yml"
        config_file.parent.mkdir()
        config_file.write_bytes(b"language: hi\n")
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(cli, ["config", "set", "दल.नाम", "लेगेशर"])
        assert result.exit_code == 0, result.output
        assert_line_feeds_only(config_file.read_bytes(), "दल:\n  नाम: लेगेशर\n")

    def test_a_global_set_writes_line_feeds(
        self, home, tmp_path, monkeypatch, windows_text_mode
    ):
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            cli, ["config", "set", "--global", "language", "si"]
        )
        assert result.exit_code == 0, result.output
        raw = (home / ".legesher" / "config.yml").read_bytes()
        assert_line_feeds_only(raw, "language: si\n")


class TestSaveProjectConfig:
    def test_saving_writes_line_feeds(self, tmp_path, windows_text_mode):
        (tmp_path / ".git").mkdir()
        directory = ".legesher/ශ්‍රී"
        path = LegesherConfig(
            language="si", metadata_directory=directory
        ).save_project_config(tmp_path)
        assert_line_feeds_only(path.read_bytes(), directory)


@patch("legesher.cli.init.LanguagePackLoader")
@patch("legesher.cli.init.AIContextGenerator")
class TestInit:
    def test_init_writes_line_feeds(
        self, mock_ai_gen, mock_loader, tmp_path, monkeypatch, windows_text_mode
    ):
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            cli,
            ["init", "-l", "hi", "-p", "3.13", "--no-git", "--no-ai-context"],
            input="",
        )
        assert result.exit_code == 0, result.output
        raw = (tmp_path / ".legesher" / "config.yml").read_bytes()
        assert_line_feeds_only(raw, "language: hi\n")
