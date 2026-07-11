"""Unit tests for legesher config command (CORE-563, CORE-574).

Tests verify:
- config list displays all values
- config get retrieves dotted-key values (user-level merged with project)
- config set writes values correctly with type coercion
- config set --global writes to user-level config (~/.legesher/config.yml)
- Error handling when no config exists
"""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from legesher.cli.main import cli


@pytest.fixture(autouse=True)
def temp_home(tmp_path_factory, monkeypatch):
    """Create a temporary home directory so tests never touch ~/.legesher."""
    home = tmp_path_factory.mktemp("home")
    # Set both HOME and USERPROFILE for cross-platform compatibility
    # Windows uses USERPROFILE, Unix uses HOME
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


SAMPLE_CONFIG = """\
languages:
  - es
  - ar
python_version: "3.13"
git:
  enabled: true
  canonical_language: en
translation:
  default_source: en
  default_target: es
  preserve_comments: true
"""


class TestConfigList:
    def test_list_shows_all_values(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "list"])
            assert result.exit_code == 0, result.output
            assert "languages" in result.output
            assert "git.enabled" in result.output
            assert "translation.default_target" in result.output

    def test_list_booleans_lowercase(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "list"])
            assert result.exit_code == 0
            assert "git.enabled = true" in result.output
            assert "True" not in result.output

    def test_list_no_config_errors(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "list"])
            assert result.exit_code != 0
            assert "No .legesher/config.yml found" in result.output


class TestConfigGet:
    def test_get_top_level(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "python_version"])
            assert result.exit_code == 0
            assert "3.13" in result.output

    def test_get_nested_key(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "git.canonical_language"])
            assert result.exit_code == 0
            assert "en" in result.output

    def test_get_nonexistent_key(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "nonexistent.key"])
            assert result.exit_code != 0
            assert "not found" in result.output

    def test_get_null_value(self, tmp_path):
        """Getting a key with null value should print 'null', not 'not found'."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(
                "python_version: null\nlanguages:\n  - es\n"
            )

            result = runner.invoke(cli, ["config", "get", "python_version"])
            assert result.exit_code == 0
            assert "null" in result.output
            assert "not found" not in result.output

    def test_get_boolean_prints_lowercase(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "git.enabled"])
            assert result.exit_code == 0
            assert result.output.strip() == "true"

    def test_get_list_value(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "languages"])
            assert result.exit_code == 0
            assert "es" in result.output
            assert "ar" in result.output


class TestConfigSet:
    def test_set_nested_value(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(
                cli, ["config", "set", "translation.default_target", "ar"]
            )
            assert result.exit_code == 0
            assert "Set translation.default_target = ar" in result.output

            # Verify the file was updated
            import yaml

            with open(".legesher/config.yml") as f:
                data = yaml.safe_load(f)
            assert data["translation"]["default_target"] == "ar"

    def test_set_boolean_value(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "git.enabled", "false"])
            assert result.exit_code == 0

            import yaml

            with open(".legesher/config.yml") as f:
                data = yaml.safe_load(f)
            assert data["git"]["enabled"] is False

    def test_set_integer_value(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "runtime.cache_size", "256"])
            assert result.exit_code == 0

            import yaml

            with open(".legesher/config.yml") as f:
                data = yaml.safe_load(f)
            assert data["runtime"]["cache_size"] == 256

    def test_set_empty_key_errors(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "", "value"])
            assert result.exit_code != 0
            assert "empty" in result.output.lower()

    def test_set_dotted_empty_segment_errors(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "git..enabled", "true"])
            assert result.exit_code != 0
            assert "empty segment" in result.output.lower()

    def test_set_inf_stays_string(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "some_key", "inf"])
            assert result.exit_code == 0

            import yaml

            with open(".legesher/config.yml") as f:
                data = yaml.safe_load(f)
            assert data["some_key"] == "inf"

    def test_set_no_config_errors(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "language", "fr"])
            assert result.exit_code != 0
            assert "No .legesher/config.yml found" in result.output

    def test_set_reports_project_path(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "set", "language", "fr"])
            assert result.exit_code == 0
            assert str(Path(".legesher/config.yml").resolve()) in result.output


class TestConfigSetGlobal:
    """Tests for config set --global (CORE-574)."""

    def test_global_writes_user_config(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "--global", "language", "es"])
            assert result.exit_code == 0, result.output
            assert "Set language = es" in result.output

            user_config = temp_home / ".legesher" / "config.yml"
            assert user_config.exists()
            data = yaml.safe_load(user_config.read_text())
            assert data["language"] == "es"

    def test_global_reports_user_path(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "--global", "language", "es"])
            assert result.exit_code == 0
            assert str(temp_home / ".legesher" / "config.yml") in result.output

    def test_global_does_not_touch_project_config(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(
                cli, ["config", "set", "--global", "translation.default_target", "ar"]
            )
            assert result.exit_code == 0

            # Project config is unchanged
            assert Path(".legesher/config.yml").read_text() == SAMPLE_CONFIG

            # User config got the value
            user_config = temp_home / ".legesher" / "config.yml"
            data = yaml.safe_load(user_config.read_text())
            assert data["translation"]["default_target"] == "ar"

    def test_global_preserves_existing_user_values(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            legesher_dir = temp_home / ".legesher"
            legesher_dir.mkdir()
            (legesher_dir / "config.yml").write_text("language: ar\n")

            result = runner.invoke(
                cli, ["config", "set", "--global", "git.enabled", "false"]
            )
            assert result.exit_code == 0

            data = yaml.safe_load((legesher_dir / "config.yml").read_text())
            assert data["language"] == "ar"
            assert data["git"]["enabled"] is False

    def test_global_empty_key_errors(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "--global", "", "value"])
            assert result.exit_code != 0
            assert "empty" in result.output.lower()
            # Invalid key must not create the user config directory
            assert not (temp_home / ".legesher").exists()

    def test_get_reads_merged_result(self, temp_home, tmp_path):
        """config get sees user-level values, with project taking precedence."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(
                cli, ["config", "set", "--global", "runtime.cache_size", "256"]
            )
            assert result.exit_code == 0

            # Key set only in user config is visible to config get
            result = runner.invoke(cli, ["config", "get", "runtime.cache_size"])
            assert result.exit_code == 0
            assert result.output.strip() == "256"

            # Project config wins for overlapping keys
            result = runner.invoke(
                cli, ["config", "set", "--global", "translation.default_target", "fr"]
            )
            assert result.exit_code == 0
            result = runner.invoke(cli, ["config", "get", "translation.default_target"])
            assert result.exit_code == 0
            assert result.output.strip() == "es"

    def test_get_works_with_only_user_config(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "--global", "language", "es"])
            assert result.exit_code == 0

            result = runner.invoke(cli, ["config", "get", "language"])
            assert result.exit_code == 0
            assert result.output.strip() == "es"

    def test_project_section_masks_user_section(self, temp_home, tmp_path):
        """Merging is top-level, matching LegesherConfig.load(): a project
        section replaces the user section of the same name entirely."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            legesher_dir = temp_home / ".legesher"
            legesher_dir.mkdir()
            (legesher_dir / "config.yml").write_text(
                "translation:\n  user_only_key: keepme\n"
            )
            Path(".legesher").mkdir()
            Path(".legesher/config.yml").write_text(SAMPLE_CONFIG)

            result = runner.invoke(cli, ["config", "get", "translation.user_only_key"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_global_set_rejects_non_mapping_user_config(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            legesher_dir = temp_home / ".legesher"
            legesher_dir.mkdir()
            (legesher_dir / "config.yml").write_text("- just\n- a list\n")

            result = runner.invoke(cli, ["config", "set", "--global", "language", "es"])
            assert result.exit_code != 0
            assert "not a YAML mapping" in result.output
            # The corrupt file must not be overwritten
            assert (legesher_dir / "config.yml").read_text() == "- just\n- a list\n"

    def test_get_rejects_non_mapping_user_config(self, temp_home, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            legesher_dir = temp_home / ".legesher"
            legesher_dir.mkdir()
            (legesher_dir / "config.yml").write_text("just a scalar\n")

            result = runner.invoke(cli, ["config", "get", "language"])
            assert result.exit_code != 0
            assert "not a YAML mapping" in result.output
