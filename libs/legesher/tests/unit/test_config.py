"""Unit tests for LegesherConfig class.

Tests configuration management for .legesher/config.yml files.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from legesher.config import (
    DEFAULT_CONFIG,
    LegesherConfig,
    get_language_for_git_filter,
    get_python_version,
)


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    return repo


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Create a temporary home directory."""
    home = tmp_path / "home"
    home.mkdir()
    # Set both HOME and USERPROFILE for cross-platform compatibility
    # Windows uses USERPROFILE, Unix uses HOME
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


class TestLegesherConfigInit:
    """Test LegesherConfig initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = LegesherConfig()
        assert config.language == "en"
        assert config.python_version is None
        assert config.git_canonical_language == "en"
        assert config.git_filter_enabled is True

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        config = LegesherConfig(
            language="es",
            python_version="3.13",
            git_canonical_language="en",
            git_filter_enabled=False,
        )
        assert config.language == "es"
        assert config.python_version == "3.13"
        assert config.git_canonical_language == "en"
        assert config.git_filter_enabled is False


class TestLegesherConfigFromDict:
    """Test creating config from dictionary."""

    def test_from_dict_minimal(self):
        """Test from_dict with minimal data."""
        data = {"language": "es"}
        config = LegesherConfig.from_dict(data)
        assert config.language == "es"
        assert config.python_version is None
        assert config.git_canonical_language == "en"

    def test_from_dict_complete(self):
        """Test from_dict with complete data."""
        data = {
            "language": "ar",
            "python_version": "3.12",
            "git": {
                "canonical_language": "en",
                "filter_enabled": False,
            },
        }
        config = LegesherConfig.from_dict(data)
        assert config.language == "ar"
        assert config.python_version == "3.12"
        assert config.git_canonical_language == "en"
        assert config.git_filter_enabled is False

    def test_from_dict_empty(self):
        """Test from_dict with empty dictionary."""
        config = LegesherConfig.from_dict({})
        assert config.language == "en"  # Default


class TestLegesherConfigToDict:
    """Test converting config to dictionary."""

    def test_to_dict(self):
        """Test to_dict conversion."""
        config = LegesherConfig(
            language="es",
            python_version="3.13",
            git_canonical_language="en",
            git_filter_enabled=True,
        )
        data = config.to_dict()
        assert data["language"] == "es"
        assert data["python_version"] == "3.13"
        assert data["git"]["canonical_language"] == "en"
        assert data["git"]["filter_enabled"] is True

    def test_to_dict_roundtrip(self):
        """Test to_dict and from_dict round trip."""
        original = LegesherConfig(language="ar", python_version="3.10")
        data = original.to_dict()
        restored = LegesherConfig.from_dict(data)
        assert restored.language == original.language
        assert restored.python_version == original.python_version


class TestProjectConfig:
    """Test project-level configuration."""

    def test_load_project_config_exists(self, temp_git_repo):
        """Test loading existing project config."""
        # Create config file
        legesher_dir = temp_git_repo / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text(
            yaml.safe_dump({"language": "es", "python_version": "3.13"})
        )

        config, exists = LegesherConfig.load_project_config(temp_git_repo)
        assert exists is True
        assert config is not None
        assert config.language == "es"
        assert config.python_version == "3.13"

    def test_load_project_config_not_exists(self, temp_git_repo):
        """Test loading project config when file doesn't exist."""
        config, exists = LegesherConfig.load_project_config(temp_git_repo)
        # Should return None when file doesn't exist
        assert exists is False
        assert config is None

    def test_save_project_config(self, temp_git_repo):
        """Test saving project config."""
        config = LegesherConfig(language="ar", python_version="3.12")
        config_path = config.save_project_config(temp_git_repo)

        # Verify file was created
        assert config_path.exists()
        assert config_path == temp_git_repo / ".legesher" / "config.yml"

        # Verify content
        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data["language"] == "ar"
        assert data["python_version"] == "3.12"

    def test_save_project_config_creates_directory(self, temp_git_repo):
        """Test saving config creates .legesher directory if needed."""
        config = LegesherConfig(language="es")
        config_path = config.save_project_config(temp_git_repo)

        assert (temp_git_repo / ".legesher").exists()
        assert config_path.exists()


class TestUserConfig:
    """Test user-level configuration."""

    def test_load_user_config_exists(self, temp_home):
        """Test loading existing user config."""
        # Create user config
        legesher_dir = temp_home / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text(yaml.safe_dump({"language": "ar"}))

        config, exists = LegesherConfig.load_user_config()
        assert exists is True
        assert config is not None
        assert config.language == "ar"

    def test_load_user_config_not_exists(self):
        """Test loading user config when file doesn't exist."""
        config, exists = LegesherConfig.load_user_config()
        # Should return None when file doesn't exist
        assert exists is False
        assert config is None

    def test_save_user_config(self, temp_home):
        """Test saving user config."""
        config = LegesherConfig(language="es", python_version="3.11")
        config_path = config.save_user_config()

        # Verify file was created
        assert config_path.exists()
        assert ".legesher" in str(config_path)

        # Verify content
        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data["language"] == "es"


class TestConfigPrecedence:
    """Test configuration precedence (project > user > defaults)."""

    def test_load_with_project_only(self, temp_git_repo):
        """Test loading with only project config."""
        # Create project config
        legesher_dir = temp_git_repo / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text(yaml.safe_dump({"language": "es"}))

        config = LegesherConfig.load(temp_git_repo)
        assert config.language == "es"

    def test_load_with_user_only(self, temp_home, temp_git_repo):
        """Test loading with only user config."""
        # Create user config
        legesher_dir = temp_home / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text(yaml.safe_dump({"language": "ar"}))

        config = LegesherConfig.load(temp_git_repo)
        assert config.language == "ar"

    def test_load_project_overrides_user(self, temp_home, temp_git_repo):
        """Test that project config overrides user config."""
        # Create user config
        user_dir = temp_home / ".legesher"
        user_dir.mkdir()
        user_file = user_dir / "config.yml"
        user_file.write_text(yaml.safe_dump({"language": "ar"}))

        # Create project config (should take precedence)
        project_dir = temp_git_repo / ".legesher"
        project_dir.mkdir()
        project_file = project_dir / "config.yml"
        project_file.write_text(yaml.safe_dump({"language": "es"}))

        config = LegesherConfig.load(temp_git_repo)
        assert config.language == "es"  # Project config wins

    def test_load_defaults_when_no_configs(self, temp_git_repo):
        """Test loading with no config files uses defaults."""
        config = LegesherConfig.load(temp_git_repo)
        assert config.language == DEFAULT_CONFIG["language"]


class TestFindRepoRoot:
    """Test git repository root detection."""

    def test_find_repo_root_at_root(self, temp_git_repo):
        """Test finding repo root when already at root."""
        root = LegesherConfig._find_repo_root(temp_git_repo)
        assert root == temp_git_repo

    def test_find_repo_root_in_subdirectory(self, temp_git_repo):
        """Test finding repo root from subdirectory."""
        subdir = temp_git_repo / "src" / "deep" / "nested"
        subdir.mkdir(parents=True)

        root = LegesherConfig._find_repo_root(subdir)
        assert root == temp_git_repo

    def test_find_repo_root_not_in_repo(self, tmp_path):
        """Test finding repo root when not in a git repository."""
        not_a_repo = tmp_path / "not_a_repo"
        not_a_repo.mkdir()

        with pytest.raises(ValueError, match="Not in a git repository"):
            LegesherConfig._find_repo_root(not_a_repo)

    def test_find_repo_root_current_directory(self, temp_git_repo, monkeypatch):
        """Test finding repo root from current directory."""
        monkeypatch.chdir(temp_git_repo)
        root = LegesherConfig._find_repo_root()
        assert root == temp_git_repo


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch("legesher.config.LegesherConfig.load")
    def test_get_language_for_git_filter(self, mock_load):
        """Test get_language_for_git_filter function."""
        mock_config = LegesherConfig(language="es")
        mock_load.return_value = mock_config

        language = get_language_for_git_filter()

        assert language == "es"
        mock_load.assert_called_once()

    @patch("legesher.config.LegesherConfig.load")
    def test_get_python_version(self, mock_load):
        """Test get_python_version function."""
        mock_config = LegesherConfig(python_version="3.13")
        mock_load.return_value = mock_config

        version = get_python_version()

        assert version == "3.13"
        mock_load.assert_called_once()

    @patch("legesher.config.LegesherConfig.load")
    def test_get_python_version_none(self, mock_load):
        """Test get_python_version when version is None (auto-detect)."""
        mock_config = LegesherConfig(python_version=None)
        mock_load.return_value = mock_config

        version = get_python_version()

        assert version is None


class TestConfigRepr:
    """Test configuration string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        config = LegesherConfig(language="es", python_version="3.13")
        repr_str = repr(config)
        assert "LegesherConfig" in repr_str
        assert "es" in repr_str
        assert "3.13" in repr_str


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_load_project_config_invalid_yaml(self, temp_git_repo):
        """Test loading project config with invalid YAML."""
        legesher_dir = temp_git_repo / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text("invalid: yaml: content: {}")

        # Should handle gracefully and return None
        config, exists = LegesherConfig.load_project_config(temp_git_repo)
        assert exists is False
        assert config is None

    def test_load_project_config_empty_file(self, temp_git_repo):
        """Test loading project config with empty file."""
        legesher_dir = temp_git_repo / ".legesher"
        legesher_dir.mkdir()
        config_file = legesher_dir / "config.yml"
        config_file.write_text("")

        config, exists = LegesherConfig.load_project_config(temp_git_repo)
        # Empty file is treated as valid but with defaults
        assert exists is True
        assert config is not None
        assert config.language == DEFAULT_CONFIG["language"]

    def test_save_project_config_permission_error(self, temp_git_repo, monkeypatch):
        """Test saving config when directory creation fails."""

        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Cannot create directory")

        config = LegesherConfig(language="es")

        # This test is tricky - just verify it doesn't crash silently
        # In real use, the error would propagate
        with pytest.raises(PermissionError):
            with patch.object(Path, "mkdir", side_effect=mock_mkdir):
                config.save_project_config(temp_git_repo)

    def test_config_with_special_characters(self, temp_git_repo):
        """Test config with special characters in language."""
        config = LegesherConfig(language="zh-CN")
        config.save_project_config(temp_git_repo)

        # Load it back
        loaded, exists = LegesherConfig.load_project_config(temp_git_repo)
        assert exists is True
        assert loaded.language == "zh-CN"

    def test_multiple_saves_overwrites(self, temp_git_repo):
        """Test that multiple saves overwrite previous config."""
        # Save first config
        config1 = LegesherConfig(language="es")
        config1.save_project_config(temp_git_repo)

        # Save second config
        config2 = LegesherConfig(language="ar")
        config2.save_project_config(temp_git_repo)

        # Load and verify second config
        loaded, exists = LegesherConfig.load_project_config(temp_git_repo)
        assert exists is True
        assert loaded.language == "ar"


class TestConfigIntegration:
    """Test configuration integration scenarios."""

    def test_full_workflow(self, temp_git_repo):
        """Test complete workflow: create, save, load, modify, save."""
        # Create and save initial config
        config = LegesherConfig(language="es", python_version="3.13")
        config.save_project_config(temp_git_repo)

        # Load it back
        loaded, exists = LegesherConfig.load_project_config(temp_git_repo)
        assert exists is True
        assert loaded.language == "es"
        assert loaded.python_version == "3.13"

        # Modify and save
        loaded.language = "ar"
        loaded.save_project_config(temp_git_repo)

        # Load again and verify
        final, final_exists = LegesherConfig.load_project_config(temp_git_repo)
        assert final_exists is True
        assert final.language == "ar"
        assert final.python_version == "3.13"  # Preserved
