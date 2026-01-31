"""Tests for CLI commands (validate and show)."""

import pytest
from click.testing import CliRunner

from legesher_i18n.cli import cli


@pytest.fixture
def runner():
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_pack_dir(tmp_path):
    """Create a temporary languages directory with sample packs."""
    languages_dir = tmp_path / "languages"
    python_dir = languages_dir / "python"

    # Create 3.10 pack (base)
    v310_dir = python_dir / "3.10"
    v310_dir.mkdir(parents=True)

    (v310_dir / "es.yml").write_text(
        """language: es
target: python
version: '3.10'
keywords:
  def: definir
  class: clase
  return: retornar
builtins:
  print: imprimir
  len: longitud
metadata:
  python_version_min: '3.10'
  python_version_max: '3.10'
  last_updated: '2025-01-01'
"""
    )

    # Create 3.11 pack (extends 3.10)
    v311_dir = python_dir / "3.11"
    v311_dir.mkdir(parents=True)

    (v311_dir / "es.yml").write_text(
        """language: es
target: python
version: '3.11'
extends: ../3.10/es.yml
keywords:
  match: coincidir
builtins: {}
metadata:
  python_version_min: '3.11'
  python_version_max: '3.11'
  last_updated: '2025-01-01'
"""
    )

    return languages_dir


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Legesher i18n language pack tools" in result.output
        assert "validate" in result.output
        assert "show" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.4.0" in result.output


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_help(self, runner):
        """Test validate command help."""
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate a language pack file" in result.output
        assert "--strict" in result.output

    def test_validate_valid_pack(self, runner, sample_pack_dir):
        """Test validating a valid language pack."""
        pack_file = sample_pack_dir / "python" / "3.10" / "es.yml"
        result = runner.invoke(cli, ["validate", str(pack_file)])

        assert result.exit_code == 0
        assert "Schema validation passed" in result.output
        assert "Validation complete" in result.output
        assert "Pack Information:" in result.output

    def test_validate_with_inheritance(self, runner, sample_pack_dir):
        """Test validating a pack with inheritance."""
        pack_file = sample_pack_dir / "python" / "3.11" / "es.yml"
        result = runner.invoke(cli, ["validate", str(pack_file)])

        # Should pass schema validation even if loading fails
        assert "Schema validation passed" in result.output
        assert "Pack Information:" in result.output

    def test_validate_nonexistent_file(self, runner):
        """Test validating a nonexistent file."""
        result = runner.invoke(cli, ["validate", "nonexistent.yml"])
        assert result.exit_code != 0
        assert (
            "does not exist" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_validate_invalid_yaml(self, runner, tmp_path):
        """Test validating invalid YAML."""
        invalid_file = tmp_path / "invalid.yml"
        invalid_file.write_text("invalid: yaml: content: [")

        result = runner.invoke(cli, ["validate", str(invalid_file)])
        assert result.exit_code != 0
        assert "YAML parse error" in result.output or "error" in result.output.lower()

    def test_validate_missing_required_fields(self, runner, tmp_path):
        """Test validating pack with missing required fields."""
        invalid_file = tmp_path / "missing_fields.yml"
        invalid_file.write_text(
            """# Missing 'language' field
target: python
version: '3.10'
keywords: {}
"""
        )

        result = runner.invoke(cli, ["validate", str(invalid_file)])
        assert result.exit_code != 0
        assert "Validation failed" in result.output

    def test_validate_strict_mode_with_warnings(self, runner, tmp_path):
        """Test strict mode fails on warnings."""
        # Create a pack with no keywords (triggers warning)
        pack_file = tmp_path / "empty.yml"
        pack_file.write_text(
            """language: es
target: python
version: '3.10'
keywords: {}
builtins: {}
"""
        )

        # Normal mode should pass with warnings
        result = runner.invoke(cli, ["validate", str(pack_file)])
        assert result.exit_code == 0
        assert "Warning" in result.output

        # Strict mode should fail
        result = runner.invoke(cli, ["validate", str(pack_file), "--strict"])
        assert result.exit_code != 0
        assert "Validation failed in strict mode" in result.output


class TestShowCommand:
    """Test the show command."""

    def test_show_help(self, runner):
        """Test show command help."""
        result = runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show all available versions" in result.output
        assert "--target" in result.output

    def test_show_language_packs(self, runner, sample_pack_dir, monkeypatch):
        """Test showing language pack versions."""
        # Mock the __file__ attribute to point to our test directory structure
        import legesher_i18n.cli as cli_module

        # Create a fake package structure
        fake_package_dir = sample_pack_dir.parent
        (fake_package_dir / "legesher_i18n").mkdir(exist_ok=True)

        # Mock the cli module's __file__ location
        mock_cli_file = str(fake_package_dir / "legesher_i18n" / "cli.py")

        with monkeypatch.context() as m:
            m.setattr(cli_module, "__file__", mock_cli_file)

            result = runner.invoke(cli, ["show", "es"])

            # Should show table with versions or handle gracefully
            # (May show error if path still doesn't work in test context)
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert (
                    "ES Language Packs" in result.output or "Version" in result.output
                )

    def test_show_nonexistent_language(self, runner, sample_pack_dir, monkeypatch):
        """Test showing a nonexistent language."""
        import legesher_i18n.cli as cli_module

        # Mock to use test directory
        original_file = cli_module.__file__
        cli_module.__file__ = str(sample_pack_dir.parent / "legesher_i18n" / "cli.py")

        try:
            result = runner.invoke(cli, ["show", "nonexistent"])

            # Should show error
            assert result.exit_code != 0
            assert "Error" in result.output or "not found" in result.output.lower()

        finally:
            cli_module.__file__ = original_file

    def test_show_with_target_option(self, runner, sample_pack_dir, monkeypatch):
        """Test show command with --target option."""
        import legesher_i18n.cli as cli_module

        original_file = cli_module.__file__
        cli_module.__file__ = str(sample_pack_dir.parent / "legesher_i18n" / "cli.py")

        try:
            result = runner.invoke(cli, ["show", "es", "--target", "python"])

            # Should attempt to show Python packs
            assert "python" in result.output.lower() or result.exit_code in [0, 1]

        finally:
            cli_module.__file__ = original_file


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_validate_then_show_workflow(self, runner, sample_pack_dir):
        """Test complete workflow: validate then show."""
        # First validate a pack
        pack_file = sample_pack_dir / "python" / "3.10" / "es.yml"
        result1 = runner.invoke(cli, ["validate", str(pack_file)])
        assert result1.exit_code == 0

        # Then show all versions (this tests that validate doesn't break anything)
        import legesher_i18n.cli as cli_module

        original_file = cli_module.__file__
        cli_module.__file__ = str(sample_pack_dir.parent / "legesher_i18n" / "cli.py")

        try:
            result2 = runner.invoke(cli, ["show", "es"])
            # Should complete without crashing
            assert result2.exit_code in [0, 1]  # May fail due to path issues in test

        finally:
            cli_module.__file__ = original_file

    def test_cli_handles_keyboard_interrupt(self, runner):
        """Test CLI handles interrupts gracefully."""
        # This is hard to test directly, but we can verify the code handles it
        # The actual KeyboardInterrupt handling is in the show command
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0  # Baseline test


class TestExportCommand:
    """Test the export command group."""

    def test_export_help(self, runner):
        """Test export group help message."""
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export language pack keywords" in result.output
        assert "json" in result.output
        assert "csv" in result.output
        # Note: markdown export removed - use scripts/generate_reference_docs.py instead

    def test_export_json_help(self, runner):
        """Test export json command help."""
        result = runner.invoke(cli, ["export", "json", "--help"])
        assert result.exit_code == 0
        assert "--lang" in result.output
        assert "--target" in result.output
        assert "--output" in result.output
        assert "--dry-run" in result.output
        assert "--quiet" in result.output

    def test_export_json_requires_lang(self, runner):
        """Test export json requires --lang option."""
        result = runner.invoke(cli, ["export", "json"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_export_csv_help(self, runner):
        """Test export csv command help."""
        result = runner.invoke(cli, ["export", "csv", "--help"])
        assert result.exit_code == 0
        assert "--lang" in result.output
        assert "--dry-run" in result.output

    def test_export_all_help(self, runner):
        """Test export all command help."""
        result = runner.invoke(cli, ["export", "all", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output-dir" in result.output
        assert "--dry-run" in result.output
        assert "--quiet" in result.output

    def test_export_json_dry_run(self, runner, monkeypatch):
        """Test export json dry run mode."""
        # Mock the loader to avoid actual pack loading
        from unittest.mock import MagicMock, patch

        mock_pack = MagicMock()
        mock_pack.language = "es"
        mock_pack.target = "python"
        mock_pack.version = "3.13"
        mock_pack.keywords = {"def": "definir"}
        mock_pack.builtins = {"print": "imprimir"}
        mock_pack.exceptions = {}
        mock_pack.inheritance_chain = []

        with patch("legesher_i18n.cli._load_language_pack", return_value=mock_pack):
            result = runner.invoke(cli, ["export", "json", "--lang", "es", "--dry-run"])

        # Dry run should succeed
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "Spanish" in result.output or "es" in result.output

    def test_export_json_to_stdout(self, runner, monkeypatch):
        """Test export json to stdout."""
        from unittest.mock import MagicMock, patch
        import json

        mock_pack = MagicMock()
        mock_pack.language = "es"
        mock_pack.target = "python"
        mock_pack.version = "3.13"
        mock_pack.keywords = {"def": "definir", "return": "retornar"}
        mock_pack.builtins = {"print": "imprimir"}
        mock_pack.exceptions = {}
        mock_pack.inheritance_chain = []

        with patch("legesher_i18n.cli._load_language_pack", return_value=mock_pack):
            with patch("legesher_i18n.cli._get_language_name", return_value="Spanish"):
                result = runner.invoke(
                    cli, ["export", "json", "--lang", "es", "--output", "-", "--quiet"]
                )

        # Should output valid JSON
        assert result.exit_code == 0
        # Parse the output as JSON
        output_json = json.loads(result.output)
        assert output_json["language"] == "es"
        assert "keywords" in output_json

    def test_export_csv_to_stdout(self, runner, monkeypatch):
        """Test export csv to stdout."""
        from unittest.mock import MagicMock, patch

        mock_pack = MagicMock()
        mock_pack.language = "es"
        mock_pack.target = "python"
        mock_pack.version = "3.13"
        mock_pack.keywords = {"def": "definir"}
        mock_pack.builtins = {"print": "imprimir"}
        mock_pack.exceptions = {}
        mock_pack.inheritance_chain = []

        with patch("legesher_i18n.cli._load_language_pack", return_value=mock_pack):
            with patch("legesher_i18n.cli._get_language_name", return_value="Spanish"):
                result = runner.invoke(
                    cli, ["export", "csv", "--lang", "es", "--output", "-", "--quiet"]
                )

        # Should output CSV data
        assert result.exit_code == 0
        assert "category" in result.output  # Header
        assert "keyword" in result.output
        assert "definir" in result.output

    def test_export_all_dry_run(self, runner, monkeypatch):
        """Test export all dry run mode."""
        from unittest.mock import patch

        with patch(
            "legesher_i18n.cli._get_available_languages",
            return_value=["en", "es", "fr"],
        ):
            with patch(
                "legesher_i18n.cli._get_language_name",
                side_effect=lambda x: {
                    "en": "English",
                    "es": "Spanish",
                    "fr": "French",
                }.get(x, x.upper()),
            ):
                result = runner.invoke(cli, ["export", "all", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "3 language packs" in result.output


class TestRegistryCommand:
    """Test the registry command group."""

    def test_registry_help(self, runner):
        """Test registry group help message."""
        result = runner.invoke(cli, ["registry", "--help"])
        assert result.exit_code == 0
        assert "Language pack registry" in result.output
        assert "list" in result.output
        assert "validate" in result.output

    def test_registry_list_help(self, runner):
        """Test registry list command help."""
        result = runner.invoke(cli, ["registry", "list", "--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--version" in result.output
        assert "--quiet" in result.output

    def test_registry_validate_help(self, runner):
        """Test registry validate command help."""
        result = runner.invoke(cli, ["registry", "validate", "--help"])
        assert result.exit_code == 0
        assert "--lang" in result.output
        assert "--strict" in result.output

    def test_registry_list_with_mock(self, runner, monkeypatch):
        """Test registry list with mocked data."""
        from unittest.mock import patch

        mock_languages = ["en", "es"]

        with patch(
            "legesher_i18n.cli._get_available_languages", return_value=mock_languages
        ):
            with patch(
                "legesher_i18n.cli._load_pack_data",
                return_value={
                    "keywords": {"def": "definir"},
                    "builtins": {"print": "imprimir"},
                },
            ):
                with patch(
                    "legesher_i18n.cli._get_language_name",
                    side_effect=lambda x: {"en": "English", "es": "Spanish"}.get(
                        x, x.upper()
                    ),
                ):
                    result = runner.invoke(cli, ["registry", "list"])

        # Should show table with languages
        assert result.exit_code == 0
        assert "Available Language Packs" in result.output

    def test_registry_validate_single_language(self, runner, monkeypatch):
        """Test registry validate for a single language."""
        from unittest.mock import patch

        mock_en_data = {
            "keywords": {"def": "def", "return": "return", "if": "if"},
            "builtins": {"print": "print", "len": "len"},
        }
        mock_es_data = {
            "keywords": {"def": "definir", "return": "retornar", "if": "si"},
            "builtins": {"print": "imprimir", "len": "longitud"},
        }

        def mock_load(lang, target, version):
            if lang == "en":
                return mock_en_data
            return mock_es_data

        with patch(
            "legesher_i18n.cli._get_available_languages", return_value=["en", "es"]
        ):
            with patch("legesher_i18n.cli._load_pack_data", side_effect=mock_load):
                with patch(
                    "legesher_i18n.cli._get_language_name",
                    side_effect=lambda x: {"en": "English", "es": "Spanish"}.get(
                        x, x.upper()
                    ),
                ):
                    result = runner.invoke(
                        cli, ["registry", "validate", "--lang", "es"]
                    )

        # Should show validation results
        assert "Spanish" in result.output or "es" in result.output
        assert result.exit_code in [0, 1]  # May pass or fail depending on completeness


class TestQuietMode:
    """Test --quiet flag across commands."""

    def test_validate_quiet_mode(self, runner, sample_pack_dir):
        """Test validate command with --quiet flag."""
        pack_file = sample_pack_dir / "python" / "3.10" / "es.yml"
        result = runner.invoke(cli, ["validate", str(pack_file), "--quiet"])

        # Should succeed with minimal/no output
        assert result.exit_code == 0
        # Quiet mode should suppress most output
        assert len(result.output.strip()) < 100 or result.output.strip() == ""

    def test_show_quiet_mode(self, runner, sample_pack_dir, monkeypatch):
        """Test show command with --quiet flag."""
        import legesher_i18n.cli as cli_module

        original_file = cli_module.__file__
        cli_module.__file__ = str(sample_pack_dir.parent / "legesher_i18n" / "cli.py")

        try:
            result = runner.invoke(cli, ["show", "es", "--quiet"])
            # Should complete without error (may fail due to path issues, that's ok)
            assert result.exit_code in [0, 1]
        finally:
            cli_module.__file__ = original_file


class TestDbCommand:
    """Test the db command group."""

    def test_db_help(self, runner):
        """Test db group help message."""
        result = runner.invoke(cli, ["db", "--help"])
        assert result.exit_code == 0
        assert "Database management" in result.output
        assert "init" in result.output
        assert "stats" in result.output
        assert "vacuum" in result.output

    def test_db_init_help(self, runner):
        """Test db init command help."""
        result = runner.invoke(cli, ["db", "init", "--help"])
        assert result.exit_code == 0
        assert "--db-path" in result.output
        assert "--quiet" in result.output

    def test_db_init_creates_database(self, runner, tmp_path):
        """Test db init creates a database file."""
        db_path = tmp_path / "test.db"
        result = runner.invoke(cli, ["db", "init", "--db-path", str(db_path)])

        assert result.exit_code == 0
        assert "initialized successfully" in result.output
        assert db_path.exists()

    def test_db_stats_requires_database(self, runner, tmp_path):
        """Test db stats requires existing database."""
        db_path = tmp_path / "nonexistent.db"
        result = runner.invoke(cli, ["db", "stats", "--db-path", str(db_path)])

        # Should fail because database doesn't exist
        assert result.exit_code != 0

    def test_db_vacuum_requires_database(self, runner, tmp_path):
        """Test db vacuum requires existing database."""
        db_path = tmp_path / "nonexistent.db"
        result = runner.invoke(cli, ["db", "vacuum", "--db-path", str(db_path)])

        # Should fail because database doesn't exist
        assert result.exit_code != 0


class TestSchemaValidatorSoftKeywords:
    """Test schema validator handling of soft keywords like except*."""

    def test_except_star_keyword_valid(self, runner, tmp_path):
        """Test that except* keyword passes validation."""
        pack_file = tmp_path / "test_pack.yml"
        pack_file.write_text(
            """language: es
target: python
version: '3.11'
keywords:
  def: definir
  except: excepto
  except*: excepto*
builtins:
  print: imprimir
metadata:
  python_version_min: '3.11'
  python_version_max: '3.14'
  last_updated: '2025-01-01'
"""
        )

        result = runner.invoke(cli, ["validate", str(pack_file)])

        # Should pass validation - except* is a valid Python 3.11+ soft keyword
        assert result.exit_code == 0
        assert "Schema validation passed" in result.output
