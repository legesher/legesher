"""One config schema, one reader, and a save that keeps what it does not own.

``legesher init`` once wrote a shape nothing else read. These tests cover the
pieces every command now shares: reading a file in that old shape
(``normalize_config_data``), finding the project's config with or without a
git repository (``find_project_config``), saying where the language came
from (``LegesherConfig.language_source``), and saving without dropping keys.

Paths and values use real scripts, with combining marks where the script
has them: a config is read and written as UTF-8, and a Latin-only fixture
would not show it.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from legesher.config import (
    LegesherConfig,
    find_project_config,
    language_list,
    normalize_config_data,
    user_config_path,
)


@pytest.fixture(autouse=True)
def home(tmp_path_factory, monkeypatch) -> Path:
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # Path.home() on Windows
    return home


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def config_in(root: Path, text: str) -> Path:
    return write(root / ".legesher" / "config.yml", text)


def repository(root: Path) -> Path:
    (root / ".git").mkdir(parents=True)
    return root


class TestLanguageList:
    def test_codes_in_order_without_repeats(self):
        assert language_list(["hi", "ar", "hi", "si"]) == ["hi", "ar", "si"]

    @pytest.mark.parametrize(
        "value",
        [None, "es", {"es": True}, 7, [], [7, None, "", "  ", ["es"]]],
        ids=["none", "scalar", "mapping", "number", "empty", "no-strings"],
    )
    def test_what_names_no_language(self, value):
        assert language_list(value) == []


class TestNormalize:
    def test_the_old_init_shape(self):
        old = {
            "languages": ["he", "ar"],
            "python_version": "3.13",
            "git": {"enabled": False, "canonical_language": "en"},
            "editor": {"lsp_hover": True},
        }
        assert normalize_config_data(old) == {
            "language": "he",
            "languages": ["he", "ar"],
            "python_version": "3.13",
            "git": {
                "enabled": False,
                "canonical_language": "en",
                "filter_enabled": False,
            },
            "editor": {"lsp_hover": True},
        }

    def test_the_input_is_left_alone(self):
        old = {"languages": ["th"], "git": {"enabled": True}}
        before = copy.deepcopy(old)
        normalize_config_data(old)
        assert old == before

    def test_a_language_the_file_names_wins(self):
        data = {"language": "ar", "languages": ["es"]}
        assert normalize_config_data(data)["language"] == "ar"

    def test_a_filter_switch_the_file_names_wins(self):
        data = {"git": {"enabled": False, "filter_enabled": True}}
        assert normalize_config_data(data)["git"]["filter_enabled"] is True

    def test_the_current_shape_is_unchanged(self):
        data = LegesherConfig(language="si", languages=["si"]).file_dict()
        assert normalize_config_data(data) == data

    @pytest.mark.parametrize(
        "data",
        [
            {"languages": []},
            {"languages": "es"},
            {"languages": [7]},
            {"language": None, "languages": [""]},
            {"git": {"enabled": "yes"}},
            {"git": ["enabled"]},
        ],
    )
    def test_nothing_is_invented(self, data):
        result = normalize_config_data(data)
        assert not isinstance(result.get("language"), str)
        git = result.get("git")
        assert not (isinstance(git, dict) and "filter_enabled" in git)

    @pytest.mark.parametrize("data", [None, [], "language: es", 7])
    def test_what_is_not_a_mapping_reads_as_empty(self, data):
        assert normalize_config_data(data) == {}


class TestLoadingTheOldShape:
    def test_from_dict(self):
        config = LegesherConfig.from_dict(
            {"languages": ["zh", "th"], "git": {"enabled": False}}
        )
        assert config.language == "zh"
        assert config.languages == ["zh", "th"]
        assert config.git_filter_enabled is False

    def test_a_null_section_does_not_stop_the_file_loading(self, tmp_path):
        root = repository(tmp_path / "r")
        config_in(root, "language: hi\ngit:\nmetadata:\nruntime:\n")
        config, exists = LegesherConfig.load_project_config(root)
        assert exists and config.language == "hi"

    def test_languages_round_trip_through_a_file(self, tmp_path):
        root = repository(tmp_path / "r")
        LegesherConfig(language="ar", languages=["ar", "he"]).save_project_config(root)
        config, _exists = LegesherConfig.load_project_config(root)
        assert config.language == "ar" and config.languages == ["ar", "he"]

    def test_no_list_is_written_when_there_is_none(self, tmp_path):
        root = repository(tmp_path / "r")
        path = LegesherConfig(language="ar").save_project_config(root)
        assert "languages" not in yaml.safe_load(path.read_text(encoding="utf-8"))


class TestFindProjectConfig:
    def test_without_a_git_repository(self, tmp_path):
        root = tmp_path / "परियोजना"
        path = config_in(root, "language: hi\n")
        assert find_project_config(root) == path.resolve()

    def test_from_a_directory_below(self, tmp_path):
        root = tmp_path / "โครงการ"
        path = config_in(root, "language: th\n")
        below = root / "แพ็กเกจ" / "ย่อย"
        below.mkdir(parents=True)
        assert find_project_config(below) == path.resolve()

    def test_the_nearest_one_wins(self, tmp_path):
        root = repository(tmp_path / "r")
        config_in(root, "language: es\n")
        nearer = config_in(root / "פְּרוֹיֶקְט", "language: he\n")
        assert find_project_config(nearer.parent.parent) == nearer.resolve()

    def test_the_search_stops_at_the_repository_root(self, tmp_path):
        config_in(tmp_path, "language: es\n")
        root = repository(tmp_path / "r")
        (root / "src").mkdir()
        assert find_project_config(root / "src") is None
        assert find_project_config(root) is None

    def test_the_repository_root_itself_is_searched(self, tmp_path):
        root = repository(tmp_path / "r")
        path = config_in(root, "language: es\n")
        (root / "src").mkdir()
        assert find_project_config(root / "src") == path.resolve()

    def test_the_user_config_is_not_a_project_config(self, home):
        config_in(home, "language: es\n")
        work = home / "作業"
        work.mkdir()
        assert user_config_path().is_file()
        assert find_project_config(work) is None
        assert find_project_config(home) is None

    def test_a_directory_named_like_the_file_is_not_one(self, tmp_path):
        (tmp_path / ".legesher" / "config.yml").mkdir(parents=True)
        assert find_project_config(tmp_path) is None

    def test_none_anywhere(self, tmp_path):
        assert find_project_config(tmp_path) is None

    def test_load_reads_it_outside_a_repository(self, tmp_path, monkeypatch):
        root = tmp_path / "p"
        config_in(root, "languages:\n  - si\n")
        monkeypatch.chdir(root)
        assert LegesherConfig.load().language == "si"


class TestLanguageSource:
    def test_the_project_config(self, tmp_path, monkeypatch, home):
        config_in(home, "language: es\n")
        path = config_in(tmp_path / "p", "language: ar\n")
        monkeypatch.chdir(path.parent.parent)
        assert LegesherConfig.language_source() == path.resolve()
        assert LegesherConfig.load().language == "ar"

    def test_the_old_shape_counts_as_naming_one(self, tmp_path, monkeypatch):
        path = config_in(tmp_path / "p", "languages:\n  - hi\n")
        monkeypatch.chdir(path.parent.parent)
        assert LegesherConfig.language_source() == path.resolve()

    def test_the_user_config(self, tmp_path, monkeypatch, home):
        path = config_in(home, "language: th\n")
        monkeypatch.chdir(tmp_path)
        assert LegesherConfig.language_source() == path
        assert LegesherConfig.load().language == "th"

    def test_no_config_names_one(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert LegesherConfig.language_source() is None
        assert LegesherConfig.load().language == "en"

    def test_it_agrees_with_load_when_the_project_names_none(
        self, tmp_path, monkeypatch, home
    ):
        # A project config that loads stands in front of the user's for every
        # setting, so the language is the default and no file is its source.
        config_in(home, "language: es\n")
        path = config_in(tmp_path / "p", "python_version: '3.13'\n")
        monkeypatch.chdir(path.parent.parent)
        assert LegesherConfig.load().language == "en"
        assert LegesherConfig.language_source() is None

    def test_an_unreadable_project_file_is_skipped_as_load_skips_it(
        self, tmp_path, monkeypatch, home
    ):
        user = config_in(home, "language: he\n")
        path = config_in(tmp_path / "p", "language: [unclosed\n")
        monkeypatch.chdir(path.parent.parent)
        assert LegesherConfig.load().language == "he"
        assert LegesherConfig.language_source() == user


class TestSavingKeepsOtherKeys:
    def test_a_section_this_class_does_not_own(self, tmp_path):
        root = repository(tmp_path / "r")
        path = config_in(root, "language: es\nदल:\n  नाम: लेगेशर\n")
        LegesherConfig(language="hi").save_project_config(root)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["language"] == "hi"
        assert data["दल"] == {"नाम": "लेगेशर"}

    def test_a_key_inside_a_section_it_does_own(self, tmp_path):
        root = repository(tmp_path / "r")
        path = config_in(root, "git:\n  enabled: true\nruntime:\n  cache_size: 9\n")
        LegesherConfig(language="ar").save_project_config(root)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["git"] == {
            "enabled": True,
            "canonical_language": "en",
            "filter_enabled": True,
        }
        assert data["runtime"] == {"cache_size": 9}

    def test_text_is_written_as_itself(self, tmp_path):
        root = repository(tmp_path / "r")
        directory = ".legesher/ශ්‍රී"
        path = LegesherConfig(
            language="si", metadata_directory=directory
        ).save_project_config(root)
        raw = path.read_bytes()
        assert directory.encode("utf-8") in raw
        assert b"\\u" not in raw
        config, _exists = LegesherConfig.load_project_config(root)
        assert config.metadata_directory == directory

    def test_a_file_that_is_not_a_mapping_is_replaced(self, tmp_path):
        root = repository(tmp_path / "r")
        path = config_in(root, "- es\n- ar\n")
        LegesherConfig(language="ar").save_project_config(root)
        assert yaml.safe_load(path.read_text(encoding="utf-8"))["language"] == "ar"

    def test_the_user_config_keeps_its_own_keys_and_telemetry(self, home):
        path = config_in(home, "language: es\ntelemetry:\n  enabled: false\nयंत्र: घर\n")
        LegesherConfig(language="hi").save_user_config()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["language"] == "hi"
        assert data["telemetry"] == {"enabled": False}
        assert data["यंत्र"] == "घर"

    def test_a_project_file_never_gains_a_telemetry_section(self, tmp_path):
        root = repository(tmp_path / "r")
        path = LegesherConfig(language="es").save_project_config(root)
        assert "telemetry" not in yaml.safe_load(path.read_text(encoding="utf-8"))
