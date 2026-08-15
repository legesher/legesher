#!/usr/bin/env python3
"""Manual testing script for error handling in language pack loading.

This script demonstrates the various error scenarios and how they're handled.
Run with: uv run python test_error_handling_manual.py
"""

import logging
import tempfile
from pathlib import Path

import yaml

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy
from legesher_language_server.utils.keyword_docs import KeywordDocumentation

# Set up logging to see the diagnostic messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

logger = logging.getLogger(__name__)


def test_scenario(name: str, test_func):
    """Run a test scenario and print results."""
    print("\n" + "=" * 70)
    print(f"SCENARIO: {name}")
    print("=" * 70)
    try:
        test_func()
        print("✅ Scenario completed successfully")
    except Exception as e:
        print(f"❌ Scenario failed: {e}")


def scenario_1_nonexistent_language():
    """Test loading a language pack that doesn't exist."""
    print("\n📋 Testing: Loading non-existent language pack")
    print("Expected: Warning message, graceful fallback\n")

    keyword_docs = KeywordDocumentation()
    result = keyword_docs.get_keyword_translation("def", "nonexistent_lang")

    print(f"\n📊 Result: {result}")
    print("Expected: None (graceful failure)")


def scenario_2_invalid_yaml():
    """Test loading a language pack with invalid YAML syntax."""
    print("\n📋 Testing: Loading language pack with invalid YAML")
    print("Expected: Error message with details, graceful fallback\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a pack with invalid YAML
        pack_dir = Path(tmpdir) / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        pack_file = pack_subdir / "3.10.yml"
        with open(pack_file, "w") as f:
            f.write("keywords:\n  def: definir\n  class: [unclosed bracket")

        keyword_docs = KeywordDocumentation()
        # Temporarily override the package path
        import legesher_i18n_python_es

        original_path = legesher_i18n_python_es.__path__
        legesher_i18n_python_es.__path__ = [str(pack_dir / "legesher_i18n_python_es")]

        try:
            result = keyword_docs.get_keyword_translation("def", "es")
            print(f"\n📊 Result: {result}")
            print("Expected: None (invalid YAML)")
        finally:
            legesher_i18n_python_es.__path__ = original_path


def scenario_3_mixed_valid_invalid():
    """Test loading a pack with both valid and invalid translations."""
    print("\n📋 Testing: Language pack with mixed valid/invalid entries")
    print("Expected: Skip invalid entries, load valid ones, log warnings\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a pack with mixed valid/invalid entries
        pack_dir = Path(tmpdir) / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        pack_file = pack_subdir / "3.10.yml"
        mixed_pack = {
            "keywords": {
                "def": "definir",  # Valid
                "class": 123,  # Invalid - int
                "if": "si",  # Valid
                "for": None,  # Invalid - None
                "while": ["bucle"],  # Invalid - list
            }
        }

        with open(pack_file, "w") as f:
            yaml.dump(mixed_pack, f)

        # Test with EnhancedIntelligenceProxy
        from unittest.mock import patch

        config = LanguageServerConfig(source_language="en", target_language="es")

        with patch.object(EnhancedIntelligenceProxy, "_find_language_pack", return_value=pack_dir):
            proxy = EnhancedIntelligenceProxy(config)

        result = proxy.translator.keyword_map
        print(f"\n📊 Result: {result}")
        print("Expected: {'definir': 'def', 'si': 'if'}")
        print(f"Match: {result == {'definir': 'def', 'si': 'if'}}")


def scenario_4_version_fallback():
    """Test version fallback when specific version not found."""
    print("\n📋 Testing: Python version fallback (3.10 → 3.11 → 3.12 → 3.13)")
    print("Expected: Try multiple versions until one is found\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create only 3.12.yml, not 3.10.yml
        pack_dir = Path(tmpdir) / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        # Create 3.12.yml
        pack_file = pack_subdir / "3.12.yml"
        pack_data = {
            "keywords": {
                "def": "definir",
                "class": "clase",
            }
        }

        with open(pack_file, "w") as f:
            yaml.dump(pack_data, f)

        print("Created: 3.12.yml (skipping 3.10, 3.11)")
        print("Attempting to load for Python 3.10...\n")

        from unittest.mock import patch

        config = LanguageServerConfig(source_language="en", target_language="es")

        with patch.object(EnhancedIntelligenceProxy, "_find_language_pack", return_value=pack_dir):
            proxy = EnhancedIntelligenceProxy(config)

        result = proxy.translator.keyword_map
        print(f"\n📊 Result: {result}")
        print("Expected: Successfully loaded from 3.12.yml as fallback")


def scenario_5_successful_load():
    """Test successful loading with proper logging."""
    print("\n📋 Testing: Successful language pack load")
    print("Expected: Info message with translation count\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        pack_dir = Path(tmpdir) / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        pack_file = pack_subdir / "3.10.yml"
        pack_data = {
            "keywords": {
                "def": "definir",
                "class": "clase",
                "if": "si",
                "elif": "sinoentonces",
                "else": "sino",
            }
        }

        with open(pack_file, "w") as f:
            yaml.dump(pack_data, f)

        from unittest.mock import patch

        config = LanguageServerConfig(source_language="en", target_language="es")

        with patch.object(EnhancedIntelligenceProxy, "_find_language_pack", return_value=pack_dir):
            proxy = EnhancedIntelligenceProxy(config)

        result = proxy.translator.keyword_map
        print(f"\n📊 Result: {result}")
        print(f"Translation count: {len(result)}")
        print("Expected: 5 translations loaded successfully")


def main():
    """Run all test scenarios."""
    print("\n" + "🧪" * 35)
    print("LANGUAGE PACK ERROR HANDLING - MANUAL TEST SUITE")
    print("🧪" * 35)
    print("\nThis script demonstrates the error handling features added in CORE-447")
    print("Watch for emoji-prefixed diagnostic messages: ⚠️ (warning), ❌ (error), ℹ️ (info)")

    test_scenario("1. Non-existent Language Pack", scenario_1_nonexistent_language)
    test_scenario("2. Invalid YAML Syntax", scenario_2_invalid_yaml)
    test_scenario("3. Mixed Valid/Invalid Entries", scenario_3_mixed_valid_invalid)
    test_scenario("4. Version Fallback", scenario_4_version_fallback)
    test_scenario("5. Successful Load", scenario_5_successful_load)

    print("\n" + "=" * 70)
    print("✅ ALL SCENARIOS COMPLETED")
    print("=" * 70)
    print("\nCheck the log messages above for emoji-prefixed diagnostics!")


if __name__ == "__main__":
    main()
