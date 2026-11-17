"""One config schema, one reader, and a save that keeps what it does not own.

``legesher init`` once wrote a shape nothing else read. These tests cover the
pieces every command now shares: reading a file in that old shape
(``normalize_config_data``), finding the project's config with or without a
git repository (``find_project_config``), merging the user's file under the
project's (``merge_config_data``), saying where the language came from
(``language_source``), and saving without dropping keys.

Paths and values use real scripts, with combining marks where the script
has them: a config is read and written as UTF-8, and a Latin-only fixture
would not show it.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from click.testing import CliRunner

from legesher.cli.main import cli
from legesher.config import (
    LegesherConfig,
    dump_config,
    find_project_config,
    home_is_the_repository,
    language_list,
    merge_config_data,
    normalize_config_data,
    project_root,
    read_config_file,
    shadowed_project_configs,
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

    @pytest.mark.parametrize("value", [7, None, "", "  ", ["es"], {"es": 1}])
    def test_a_language_that_is_not_a_code_is_no_language(self, value):
        assert "language" not in normalize_config_data({"language": value})
        filled = normalize_config_data({"language": value, "languages": ["hi"]})
        assert filled["language"] == "hi"

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


class TestProjectRoot:
    def test_the_repository_root_from_below(self, tmp_path):
        root = repository(tmp_path / "r")
        below = root / "स्रोत" / "गहरा"
        below.mkdir(parents=True)
        assert project_root(below) == root.resolve()

    def test_a_worktree_or_submodule_whose_git_is_a_file(self, tmp_path):
        root = tmp_path / "r"
        write(root / ".git", "gitdir: /elsewhere/.git/worktrees/r\n")
        (root / "src").mkdir()
        assert project_root(root / "src") == root.resolve()

    def test_the_directory_itself_outside_a_repository(self, tmp_path):
        plain = tmp_path / "โครงการ"
        plain.mkdir()
        assert project_root(plain) == plain.resolve()

    def test_the_directory_itself_inside_a_home_kept_in_git(self, home):
        # Home's root holds the user config, so it is never a project root.
        repository(home)
        below = home / "परियोजना" / "स्रोत"
        below.mkdir(parents=True)
        assert project_root(below) == below.resolve()
        assert project_root(home) == home.resolve()
        assert home_is_the_repository(below)
        assert not home_is_the_repository(repository(home / "अपना"))


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

    def test_outside_a_repository_the_nearest_one_wins(self, tmp_path):
        config_in(tmp_path / "p", "language: es\n")
        nearer = config_in(tmp_path / "p" / "פְּרוֹיֶקְט", "language: he\n")
        assert find_project_config(nearer.parent.parent) == nearer.resolve()

    def test_inside_a_repository_the_root_wins_over_a_nearer_one(self, tmp_path):
        # Git runs the filter and the guard hook at the root, so that is the
        # file every command reads, whatever directory it is run from.
        root = repository(tmp_path / "r")
        at_root = config_in(root, "language: es\n")
        nearer = config_in(root / "פְּרוֹיֶקְט", "language: he\n")
        assert find_project_config(nearer.parent.parent) == at_root.resolve()

    def test_a_repository_with_none_at_its_root_falls_back_to_a_nearer_one(
        self, tmp_path
    ):
        # Where an earlier `legesher init` run in a subdirectory left it.
        root = repository(tmp_path / "r")
        nested = config_in(root / "ऐप", "languages:\n  - hi\n")
        below = nested.parent.parent / "src"
        below.mkdir()
        assert find_project_config(below) == nested.resolve()
        assert find_project_config(root) is None

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

    @pytest.mark.parametrize("link", ["directory", "file"])
    def test_nor_is_it_one_through_a_symlink(self, home, tmp_path, link):
        # A dotfiles setup: ~/.legesher, or the file in it, is a symlink.
        real = write(
            tmp_path / "dotfiles" / "legesher" / "config.yml", "language: es\n"
        )
        try:
            if link == "directory":
                (home / ".legesher").symlink_to(real.parent, target_is_directory=True)
            else:
                (home / ".legesher").mkdir()
                (home / ".legesher" / "config.yml").symlink_to(real)
        except OSError:
            pytest.skip("this platform does not let the test create symlinks")
        work = home / "作業"
        work.mkdir()
        assert user_config_path().is_file()
        assert find_project_config(work) is None

    def test_a_project_below_a_home_that_is_a_repository(self, home):
        # Dotfiles kept in git make home a repository root; a project under
        # it is still found, and the user config is still not one.
        repository(home)
        config_in(home, "language: es\n")
        project = config_in(home / "परियोजना", "language: hi\n")
        assert find_project_config(project.parent.parent) == project.resolve()

    def test_a_directory_named_like_the_file_is_not_one(self, tmp_path):
        (tmp_path / ".legesher" / "config.yml").mkdir(parents=True)
        assert find_project_config(tmp_path) is None

    def test_none_anywhere(self, tmp_path):
        assert find_project_config(repository(tmp_path / "r")) is None

    def test_load_reads_it_outside_a_repository(self, tmp_path, monkeypatch):
        root = tmp_path / "p"
        config_in(root, "languages:\n  - si\n")
        monkeypatch.chdir(root)
        assert LegesherConfig.load().language == "si"


#: User and project files, the language the runtime uses, and whether the
#: project file is used at all.
CASES = [
    pytest.param(
        "language: he\n",
        "python_version: '3.13'\n",
        "he",
        True,
        id="project-names-none",
    ),
    pytest.param(
        "language: he\n", "languages: []\n", "he", True, id="project-list-empty"
    ),
    pytest.param("language: he\n", "", "he", True, id="project-empty"),
    pytest.param(
        "language: he\n", "# only a comment\n", "he", True, id="project-comment-only"
    ),
    pytest.param(
        "language: he\n", "- es\n- ar\n", "he", False, id="project-not-a-mapping"
    ),
    pytest.param(
        "language: he\n", "language: [unclosed\n", "he", False, id="project-unparsable"
    ),
    pytest.param(
        "language: he\n", "language: 7\n", "he", True, id="project-language-not-a-code"
    ),
    pytest.param(
        "language: he\n",
        "language: ar\nmetadata:\n  max_history_entries: -1\n",
        "he",
        False,
        id="project-fails-validation",
    ),
    pytest.param(
        "language: he\n", "language: ar\n", "ar", True, id="project-names-one"
    ),
    pytest.param(
        "languages:\n  - th\n",
        "git:\n  enabled: true\n",
        "th",
        True,
        id="old-shape-user",
    ),
    pytest.param("", "", "en", True, id="neither"),
]


class TestMerge:
    """One rule for the user's file under the project's, for every reader."""

    def test_a_key_the_project_does_not_name_is_the_users(self):
        merged = merge_config_data(
            {"language": "he", "python_version": "3.12"}, {"python_version": "3.13"}
        )
        assert merged["language"] == "he"
        assert merged["python_version"] == "3.13"

    def test_a_section_is_taken_whole_from_the_project(self):
        merged = merge_config_data(
            {"metadata": {"enabled": False, "max_history_entries": 7}},
            {"metadata": {"verbose_history": True}},
        )
        assert merged["metadata"] == {"verbose_history": True}

    def test_each_file_is_read_as_the_old_shape_is(self):
        merged = merge_config_data({"languages": ["th"]}, {"git": {"enabled": False}})
        assert merged["language"] == "th"
        assert merged["git"]["filter_enabled"] is False

    def test_telemetry_is_the_users_whatever_the_project_says(self):
        merged = merge_config_data(
            {"telemetry": {"enabled": False}}, {"telemetry": {"enabled": True}}
        )
        assert merged["telemetry"] == {"enabled": False, "repo_attribution": False}

    def test_no_default_is_filled_in(self):
        assert merge_config_data(None, None) == {
            "telemetry": {"enabled": True, "repo_attribution": False}
        }

    @pytest.mark.parametrize(("user", "project", "language", "used"), CASES)
    def test_the_loader_takes_the_language_by_the_same_rule(
        self, tmp_path, monkeypatch, home, user, project, language, used
    ):
        config_in(home, user)
        path = config_in(tmp_path / "p", project)
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        assert config.language == language
        assert (config.left_out == []) is used

    @pytest.mark.parametrize(("user", "project", "language", "used"), CASES)
    def test_config_get_reports_what_the_loader_uses(
        self, tmp_path, monkeypatch, home, user, project, language, used
    ):
        config_in(home, user)
        path = config_in(tmp_path / "p", project)
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        result = CliRunner().invoke(cli, ["config", "get", "language"])
        if not used:
            # The runtime leaves the project file out; `config` will not
            # report settings from it, and says why.
            assert result.exit_code == 1
            assert f"Cannot use {path.resolve()}" in result.output
        elif config.language_source is None:
            assert result.exit_code == 1
            assert "not found" in result.output
            assert config.language == "en"
        else:
            assert (result.exit_code, result.output) == (0, f"{config.language}\n")

    def test_a_user_file_that_fails_validation_still_carries_consent(
        self, tmp_path, monkeypatch, home
    ):
        config_in(
            home,
            "language: he\ntelemetry:\n  enabled: false\n"
            "metadata:\n  max_history_entries: -1\n",
        )
        monkeypatch.chdir(tmp_path)
        config = LegesherConfig.load()
        assert config.language == "en"
        assert config.telemetry_enabled is False


class TestLanguageSource:
    """``load()`` says which file the language came from."""

    def test_the_project_config(self, tmp_path, monkeypatch, home):
        config_in(home, "language: es\n")
        path = config_in(tmp_path / "p", "language: ar\n")
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("ar", path.resolve())

    def test_the_old_shape_counts_as_naming_one(self, tmp_path, monkeypatch):
        path = config_in(tmp_path / "p", "languages:\n  - hi\n")
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("hi", path.resolve())

    def test_the_user_config(self, tmp_path, monkeypatch, home):
        path = config_in(home, "language: th\n")
        monkeypatch.chdir(tmp_path)
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("th", path)

    def test_the_user_config_when_the_project_names_none(
        self, tmp_path, monkeypatch, home
    ):
        user = config_in(home, "language: es\n")
        path = config_in(tmp_path / "p", "python_version: '3.13'\n")
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("es", user)
        assert config.python_version == "3.13"

    def test_no_config_names_one(self, tmp_path, monkeypatch):
        monkeypatch.chdir(repository(tmp_path / "r"))
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("en", None)

    @pytest.mark.parametrize(
        "project",
        [
            "language: [unclosed\n",
            "- es\n",
            "language: ar\nmetadata:\n  max_history_entries: -1\n",
        ],
        ids=["unparsable", "not-a-mapping", "fails-validation"],
    )
    def test_a_project_file_that_is_left_out_is_never_the_source(
        self, tmp_path, monkeypatch, home, project
    ):
        user = config_in(home, "language: he\n")
        path = config_in(tmp_path / "p", project)
        monkeypatch.chdir(path.parent.parent)
        config = LegesherConfig.load()
        assert (config.language, config.language_source) == ("he", user)

    def test_an_explicit_root_is_read_as_given(self, tmp_path):
        root = repository(tmp_path / "r")
        path = config_in(root, "language: si\n")
        config = LegesherConfig.load(root)
        assert (config.language, config.language_source) == ("si", path)


class TestReadConfigFile:
    def test_no_file(self, tmp_path):
        assert read_config_file(None) == (None, None)
        assert read_config_file(tmp_path / "missing.yml") == (None, None)

    def test_an_empty_file_is_an_empty_mapping(self, tmp_path):
        assert read_config_file(write(tmp_path / "c.yml", "")) == ({}, None)

    def test_a_usable_file_is_read_as_the_old_shape_is(self, tmp_path):
        data, problem = read_config_file(write(tmp_path / "c.yml", "languages: [si]\n"))
        assert problem is None and data["language"] == "si"

    @pytest.mark.parametrize(
        ("text", "reason"),
        [
            ("language: [unclosed\n", "cannot be read as YAML"),
            ("- es\n", "not a YAML mapping (found list)"),
            ("just a scalar\n", "not a YAML mapping (found str)"),
            ("metadata:\n  max_history_entries: x\n", "not supported between"),
            ("language: " + "[" * 5000 + "]" * 5000 + "\n", "cannot be read as YAML"),
            ("metadata:\n  max_history_entries: -1\n", "must be >= 0"),
        ],
        ids=[
            "unparsable",
            "list",
            "scalar",
            "history-not-a-number",
            "nested-too-deeply",
            "negative-history",
        ],
    )
    def test_a_file_left_out_says_why(self, tmp_path, text, reason):
        data, problem = read_config_file(write(tmp_path / "c.yml", text))
        assert data is None and reason in problem

    def test_an_absolute_metadata_directory_is_left_out(self, tmp_path):
        # Built from tmp_path, so it is absolute on every platform: a rooted
        # POSIX path such as /var/x is not absolute on Windows.
        directory = (tmp_path / "meta").as_posix()
        text = f"metadata:\n  directory: '{directory}'\n"
        data, problem = read_config_file(write(tmp_path / "c.yml", text))
        assert data is None and "must be a relative path" in problem

    def test_saving_a_project_config_never_writes_the_user_config(self, home):
        repository(home)
        with pytest.raises(ValueError, match="user config"):
            LegesherConfig(language="es").save_project_config(home)
        assert not user_config_path().exists()


class TestShadowedConfigs:
    def test_one_below_the_root_is_reported_when_the_root_has_one(self, tmp_path):
        root = repository(tmp_path / "r")
        config_in(root, "language: es\n")
        nested = config_in(root / "ऐप", "language: hi\n")
        below = nested.parent.parent / "स्रोत"
        below.mkdir()
        assert shadowed_project_configs(below) == [nested.resolve()]

    def test_none_when_the_root_has_none(self, tmp_path):
        root = repository(tmp_path / "r")
        nested = config_in(root / "ऐप", "language: hi\n")
        assert shadowed_project_configs(nested.parent.parent) == []

    def test_none_outside_a_repository(self, tmp_path):
        config_in(tmp_path, "language: es\n")
        nested = config_in(tmp_path / "ऐप", "language: hi\n")
        assert shadowed_project_configs(nested.parent.parent) == []


class TestDump:
    def test_text_is_written_as_itself_in_the_order_given(self):
        text = dump_config({"नाम": "ශ්\u200dරී", "language": "si"})
        assert text == "नाम: ශ්\u200dරී\nlanguage: si\n"


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
