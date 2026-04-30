"""Unit tests for language pack YAML validator.

Tests the LanguagePackValidator from validate_language_pack_yaml.py,
focusing on the collision detection (duplicate translation) rules
upgraded from warnings to errors in CORE-605.
"""

import sys
from pathlib import Path

import pytest

# Import from scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from validate_language_pack_yaml import LanguagePackValidator


@pytest.mark.unit
class TestLanguagePackValidator:
    """Test LanguagePackValidator collision detection."""

    @pytest.fixture
    def validator(self):
        return LanguagePackValidator()

    def _write_yaml(self, tmp_path: Path, content: str) -> Path:
        """Write YAML content to a temp file in a language-packs/packs/ path."""
        # Validator requires "language-packs" and "packs" in path
        pack_dir = tmp_path / "language-packs" / "python" / "test" / "packs"
        pack_dir.mkdir(parents=True)
        file_path = pack_dir / "3.10.yml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_validator_errors_on_duplicate_translations(self, validator, tmp_path):
        """Test that duplicate translations within a file cause errors (not warnings)."""
        yaml_content = """\
language: fi
target: python
version: '3.10'
keywords:
  and: ja
  or: ja
builtins: {}
exceptions: {}
metadata:
  python_version_min: '3.10'
  python_version_max: '3.14'
"""
        file_path = self._write_yaml(tmp_path, yaml_content)

        is_valid = validator.validate_file(file_path)

        assert is_valid is False
        assert len(validator.errors) >= 1
        collision_errors = [e for e in validator.errors if "Collision" in e]
        assert len(collision_errors) == 1
        assert "ja" in collision_errors[0]
        assert "keywords.and" in collision_errors[0]
        assert "keywords.or" in collision_errors[0]

    def test_validator_no_error_on_unique_translations(self, validator, tmp_path):
        """Test that unique translations pass validation without errors."""
        yaml_content = """\
language: fi
target: python
version: '3.10'
keywords:
  and: ja
  or: tai
  if: jos
builtins:
  all: kaikki
  any: mikätahansa
exceptions:
  exception: poikkeus
metadata:
  python_version_min: '3.10'
  python_version_max: '3.14'
"""
        file_path = self._write_yaml(tmp_path, yaml_content)

        is_valid = validator.validate_file(file_path)

        assert is_valid is True
        assert len(validator.errors) == 0

    def test_validator_cross_section_collision(self, validator, tmp_path):
        """Test that collisions across sections (keywords vs builtins) are detected."""
        yaml_content = """\
language: fi
target: python
version: '3.10'
keywords:
  and: sama
builtins:
  all: sama
exceptions: {}
metadata:
  python_version_min: '3.10'
  python_version_max: '3.14'
"""
        file_path = self._write_yaml(tmp_path, yaml_content)

        is_valid = validator.validate_file(file_path)

        assert is_valid is False
        collision_errors = [e for e in validator.errors if "Collision" in e]
        assert len(collision_errors) == 1

    def test_no_duplicate_error_for_keyword_builtin_cross_collision(
        self, validator, tmp_path
    ):
        """Regression for Copilot review on PR #237: a value appearing in
        keywords AND builtins must produce exactly ONE error message,
        not two (the previous in-script duplicate pass + the schema
        validator's cross-section pass were both firing for the same
        finding).
        """
        yaml_content = """\
language: fi
target: python
version: '3.10'
keywords:
  and: sama
builtins:
  all: sama
exceptions: {}
metadata:
  python_version_min: '3.10'
  python_version_max: '3.14'
"""
        file_path = self._write_yaml(tmp_path, yaml_content)
        is_valid = validator.validate_file(file_path)

        assert is_valid is False
        # Filter to errors mentioning "sama" (the colliding value) so we
        # don't accidentally count unrelated errors.
        sama_errors = [e for e in validator.errors if "sama" in e]
        assert len(sama_errors) == 1, (
            f"Expected exactly one error mentioning the colliding value 'sama', "
            f"got {len(sama_errors)}: {sama_errors}"
        )

    def test_validator_multiple_collisions(self, validator, tmp_path):
        """Test that multiple collision groups are all reported."""
        yaml_content = """\
language: fi
target: python
version: '3.10'
keywords:
  and: ja
  or: ja
  if: kun
  elif: kun
builtins: {}
exceptions: {}
metadata:
  python_version_min: '3.10'
  python_version_max: '3.14'
"""
        file_path = self._write_yaml(tmp_path, yaml_content)

        is_valid = validator.validate_file(file_path)

        assert is_valid is False
        collision_errors = [e for e in validator.errors if "Collision" in e]
        assert len(collision_errors) == 2
