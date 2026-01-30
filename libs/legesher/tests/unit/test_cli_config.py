"""Unit tests for legesher config command (CORE-563).

Tests verify:
- config list displays all values
- config get retrieves dotted-key values
- config set writes values correctly with type coercion
- Error handling when no config exists
"""

from pathlib import Path

from click.testing import CliRunner

from legesher.cli.main import cli

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
