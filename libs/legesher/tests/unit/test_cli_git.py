"""Unit tests for CLI git commands.

Tests the legesher git-setup and git-status commands.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from legesher.cli.git import (
    _configure_git_filters,
    _create_gitattributes,
    _verify_git_setup,
    git_setup,
    git_status,
)
from legesher.config import LegesherConfig


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    return repo


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_find_repo_root(temp_git_repo):
    """Mock LegesherConfig._find_repo_root to return temp repo."""
    with patch.object(
        LegesherConfig, "_find_repo_root", return_value=temp_git_repo
    ) as mock:
        yield mock


@pytest.fixture
def mock_translator():
    """Mock TokenTranslator for testing."""
    with patch("legesher.cli.git.TokenTranslator") as mock:
        # Mock list_available_languages
        mock.list_available_languages.return_value = [
            ("es", "Spanish"),
            ("ar", "Arabic"),
            ("en", "English"),
        ]

        # Mock from_language_pack
        mock_instance = Mock()
        mock_instance.get_pack_info.return_value = {
            "keyword_count": 35,
            "builtin_count": 69,
        }
        mock.from_language_pack.return_value = mock_instance

        yield mock


class TestGitSetupCommand:
    """Test legesher git-setup command."""

    def test_git_setup_basic(
        self, cli_runner, temp_git_repo, mock_find_repo_root, mock_translator
    ):
        """Test basic git setup with valid language."""
        # Mock subprocess calls for git config
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = cli_runner.invoke(
                git_setup,
                ["--language", "es"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "✓ Found git repository" in result.output
            assert "✓ Loaded language pack: es" in result.output
            assert "✓ Saved project config" in result.output
            assert "✓ Git filter setup complete!" in result.output

            # Verify config file was created
            config_path = temp_git_repo / ".legesher" / "config.yml"
            assert config_path.exists()

            # Verify .gitattributes was created
            gitattributes = temp_git_repo / ".gitattributes"
            assert gitattributes.exists()
            assert "*.py filter=legesher" in gitattributes.read_text()

    def test_git_setup_with_python_version(
        self, cli_runner, temp_git_repo, mock_find_repo_root, mock_translator
    ):
        """Test git setup with explicit Python version."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = cli_runner.invoke(
                git_setup,
                ["--language", "es", "--python-version", "3.13"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

            # Verify config has correct Python version
            config_path = temp_git_repo / ".legesher" / "config.yml"
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            assert config_data["python_version"] == "3.13"

    def test_git_setup_invalid_language(
        self, cli_runner, temp_git_repo, mock_find_repo_root, mock_translator
    ):
        """Test git setup with invalid language."""
        result = cli_runner.invoke(
            git_setup,
            ["--language", "invalid-lang"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "✗ Language 'invalid-lang' not found" in result.output
        assert "Available languages:" in result.output
        assert "es: Spanish" in result.output

    def test_git_setup_not_in_repo(self, cli_runner, tmp_path):
        """Test git setup when not in a git repository."""
        with patch.object(
            LegesherConfig,
            "_find_repo_root",
            side_effect=ValueError("Not in a git repository"),
        ):
            result = cli_runner.invoke(
                git_setup,
                ["--language", "es"],
                catch_exceptions=False,
            )

            assert result.exit_code == 1
            assert "✗ Error: Not in a git repository" in result.output
            assert (
                "Hint: Run this command from within a git repository" in result.output
            )

    def test_git_setup_global(self, cli_runner, mock_translator, tmp_path):
        """Test git setup with --global flag."""
        # Create a temp home directory
        test_home = tmp_path / "home"
        test_home.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = test_home

                result = cli_runner.invoke(
                    git_setup,
                    ["--language", "es", "--global"],
                    catch_exceptions=False,
                )

                assert result.exit_code == 0
                assert "✓ Saved global config" in result.output
                assert "Git filters configured globally" in result.output

                # Verify --global flag was passed to git config
                git_config_calls = [
                    call for call in mock_run.call_args_list if call[0][0][0] == "git"
                ]
                assert any("--global" in call[0][0] for call in git_config_calls), (
                    "Expected --global flag in git config calls"
                )

    def test_git_setup_prompt_for_language(
        self, cli_runner, temp_git_repo, mock_find_repo_root, mock_translator
    ):
        """Test git setup prompts for language if not provided."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = cli_runner.invoke(
                git_setup,
                input="es\n",  # Provide language via stdin
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "Default language:" in result.output


class TestGitStatusCommand:
    """Test legesher git-status command."""

    def test_git_status_with_config(
        self, cli_runner, temp_git_repo, mock_find_repo_root
    ):
        """Test git status when configuration exists."""
        # Create config file
        config = LegesherConfig(language="es", python_version="3.13")
        config.save_project_config(temp_git_repo)

        # Mock git config commands
        with patch("subprocess.run") as mock_run:

            def git_config_side_effect(args, **kwargs):
                if "filter.legesher.clean" in args:
                    return Mock(
                        returncode=0, stdout="legesher-filter --clean\n", stderr=""
                    )
                elif "filter.legesher.smudge" in args:
                    return Mock(
                        returncode=0, stdout="legesher-filter --smudge\n", stderr=""
                    )
                return Mock(returncode=1, stdout="", stderr="")

            mock_run.side_effect = git_config_side_effect

            # Create .gitattributes
            gitattributes = temp_git_repo / ".gitattributes"
            gitattributes.write_text("*.py filter=legesher\n")

            result = cli_runner.invoke(git_status, catch_exceptions=False)

            assert result.exit_code == 0
            assert f"Repository: {temp_git_repo}" in result.output
            assert "Language: es" in result.output
            assert "Python version: 3.13" in result.output
            assert "✓ Clean filter:" in result.output
            assert "✓ Smudge filter:" in result.output
            assert "✓ .gitattributes configured" in result.output

    def test_git_status_no_config(self, cli_runner, temp_git_repo, mock_find_repo_root):
        """Test git status when no configuration exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="")

            result = cli_runner.invoke(git_status, catch_exceptions=False)

            assert result.exit_code == 0
            # When no config file exists, LegesherConfig.load() returns defaults
            # So we should see default values, not an error message
            assert "Language: en" in result.output  # Default language
            assert "✗ Clean filter: Not configured" in result.output
            assert "✗ Smudge filter: Not configured" in result.output
            assert "✗ .gitattributes not found" in result.output

    def test_git_status_not_in_repo(self, cli_runner):
        """Test git status when not in a git repository."""
        with patch.object(
            LegesherConfig,
            "_find_repo_root",
            side_effect=ValueError("Not in a git repository"),
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1, stdout="", stderr="")

                result = cli_runner.invoke(git_status, catch_exceptions=False)

                assert result.exit_code == 0
                assert "Not in a git repository" in result.output


class TestConfigureGitFilters:
    """Test _configure_git_filters helper function."""

    def test_configure_git_filters_local(self):
        """Test configuring git filters for local repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = _configure_git_filters(use_global=False)

            assert result is True

            # Verify correct commands were called
            calls = mock_run.call_args_list
            assert len(calls) == 3  # clean, smudge, required

            # Check clean filter
            assert any(
                "filter.legesher.clean" in call[0][0] and "--local" in call[0][0]
                for call in calls
            )

            # Check smudge filter
            assert any(
                "filter.legesher.smudge" in call[0][0] and "--local" in call[0][0]
                for call in calls
            )

            # Check required flag
            assert any(
                "filter.legesher.required" in call[0][0] and "--local" in call[0][0]
                for call in calls
            )

    def test_configure_git_filters_global(self):
        """Test configuring git filters globally."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = _configure_git_filters(use_global=True)

            assert result is True

            # Verify --global flag was used
            calls = mock_run.call_args_list
            assert all("--global" in call[0][0] for call in calls)

    def test_configure_git_filters_failure(self):
        """Test handling of git config failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git config")

            result = _configure_git_filters(use_global=False)

            assert result is False


class TestCreateGitattributes:
    """Test _create_gitattributes helper function."""

    def test_create_gitattributes_new_file(self, temp_git_repo):
        """Test creating new .gitattributes file."""
        _create_gitattributes(temp_git_repo)

        gitattributes = temp_git_repo / ".gitattributes"
        assert gitattributes.exists()

        content = gitattributes.read_text()
        assert "# Legesher multilingual code translation" in content
        assert "*.py filter=legesher" in content

    def test_create_gitattributes_existing_file(self, temp_git_repo):
        """Test updating existing .gitattributes file."""
        gitattributes = temp_git_repo / ".gitattributes"
        gitattributes.write_text("*.txt text\n")

        _create_gitattributes(temp_git_repo)

        content = gitattributes.read_text()
        assert "*.txt text" in content  # Preserved existing content
        assert "*.py filter=legesher" in content

    def test_create_gitattributes_already_configured(self, temp_git_repo):
        """Test when .gitattributes already has legesher filter."""
        gitattributes = temp_git_repo / ".gitattributes"
        gitattributes.write_text("*.py filter=legesher\n")

        _create_gitattributes(temp_git_repo)

        content = gitattributes.read_text()
        # Should not duplicate the entry
        assert content.count("*.py filter=legesher") == 1


class TestVerifyGitSetup:
    """Test _verify_git_setup helper function."""

    def test_verify_git_setup_success(self):
        """Test successful verification."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = _verify_git_setup(use_global=False)

            assert result is True

    def test_verify_git_setup_failure(self):
        """Test failed verification."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = _verify_git_setup(use_global=False)

            assert result is False

    def test_verify_git_setup_exception(self):
        """Test exception handling during verification."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git command failed")

            result = _verify_git_setup(use_global=False)

            assert result is False


class TestCLIIntegration:
    """Test CLI command integration scenarios."""

    def test_setup_then_status(
        self, cli_runner, temp_git_repo, mock_find_repo_root, mock_translator
    ):
        """Test running setup followed by status."""
        # Run setup
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            setup_result = cli_runner.invoke(
                git_setup,
                ["--language", "es"],
                catch_exceptions=False,
            )

            assert setup_result.exit_code == 0

        # Run status
        with patch("subprocess.run") as mock_run:

            def git_config_side_effect(args, **kwargs):
                if "filter.legesher.clean" in args:
                    return Mock(returncode=0, stdout="legesher-filter --clean\n")
                elif "filter.legesher.smudge" in args:
                    return Mock(returncode=0, stdout="legesher-filter --smudge\n")
                return Mock(returncode=1)

            mock_run.side_effect = git_config_side_effect

            status_result = cli_runner.invoke(git_status, catch_exceptions=False)

            assert status_result.exit_code == 0
            assert "Language: es" in status_result.output
            assert "✓ Clean filter:" in status_result.output
            assert "✓ Smudge filter:" in status_result.output
