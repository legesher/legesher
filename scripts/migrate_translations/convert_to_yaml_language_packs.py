#!/usr/bin/env python3
"""
Convert extracted JSON translations to YAML language pack format.

This script takes the extracted translations from legesher-translations repository
and converts them to the new YAML language pack format for legesher v2.

Usage:
    python convert_to_yaml_language_packs.py
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any


# Language metadata mapping
# Using 2-letter base codes (es, ar, hi) rather than dialect codes (es-ES, ar-SA, hi-IN)
# Dialect distinctions will be added later with native speaker input
LANGUAGE_METADATA = {
    "es": {
        "code": "es",
        "name": "Spanish",
        "native_name": "Español",
        "family": "Romance",
        "direction": "ltr",
    },
    "ar": {
        "code": "ar",
        "name": "Arabic",
        "native_name": "العربية",
        "family": "Semitic",
        "direction": "rtl",
    },
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "family": "Indo-Aryan",
        "direction": "ltr",
    },
}


def load_json_translation(language_code: str) -> Dict[str, Any]:
    """Load extracted JSON translation file."""
    json_path = Path(__file__).parent / "migration_data" / "extracted_translations" / f"{language_code}_python.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert_to_yaml_format(language_code: str, translation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON translation data to YAML language pack format."""

    metadata = LANGUAGE_METADATA[language_code]
    keywords_dict = translation_data["keywords"]
    builtins_dict = translation_data["builtins"]

    # Build keywords section
    keywords = {}
    for term, translation in sorted(keywords_dict.items()):
        # Determine pattern based on term type
        pattern = determine_pattern(term, "keyword")
        form = determine_form(term, translation, pattern, language_code)

        keywords[term] = {
            "translation": translation,
            "form": form,
            "pattern": pattern,
            "confidence": "COMMUNITY",  # Migrated from community translations
            "notes": f"Migrated from legesher-translations repository",
        }

    # Build builtins section
    builtins = {}
    for term, translation in sorted(builtins_dict.items()):
        builtins[term] = {
            "translation": translation,
            "confidence": "COMMUNITY",
            "notes": f"Migrated from legesher-translations repository",
        }

    # Build complete YAML structure
    yaml_data = {
        "language": {
            "code": metadata["code"],
            "name": metadata["name"],
            "native_name": metadata["native_name"],
            "family": metadata["family"],
            "direction": metadata["direction"],
        },
        "metadata": {
            "status": "migrated",
            "version": "0.1.0-community",
            "source": "legesher-translations repository",
            "branch": translation_data["branch"],
            "review_count": translation_data["stats"]["review_count"],
            "notes": (
                "Migrated from legesher-translations community contributions. "
                "These translations were created by the community and may need "
                "review and refinement using the new linguistic standards."
            ),
        },
        "keywords": keywords,
        "builtins": builtins,
    }

    return yaml_data


def determine_pattern(term: str, category: str) -> str:
    """Determine the pattern classification for a term."""
    if category != "keyword":
        return "N/A"

    # ACTION keywords (verbs)
    action_keywords = ["def", "del", "return", "break", "continue", "pass",
                      "raise", "yield", "import", "assert", "await"]

    # STATE keywords (conjunctions, conditionals)
    state_keywords = ["if", "elif", "else", "for", "while", "with", "try",
                     "except", "finally", "in", "is", "from", "as", "async"]

    # VALUE constants
    value_constants = ["True", "False", "None"]

    # OPERATOR keywords
    operator_keywords = ["and", "or", "not"]

    if term in action_keywords:
        return "ACTION_KEYWORD"
    elif term in state_keywords:
        return "STATE_KEYWORD"
    elif term in value_constants:
        return "VALUE_CONSTANT"
    elif term in operator_keywords:
        return "OPERATOR_KEYWORD"
    elif term in ["class", "lambda", "global", "nonlocal"]:
        return "DECLARATION_KEYWORD"
    else:
        return "KEYWORD"


def determine_form(term: str, translation: str, pattern: str, language_code: str) -> str:
    """Determine the grammatical form of the translation."""

    # For VALUE_CONSTANT, use adjective
    if pattern == "VALUE_CONSTANT":
        if language_code == "es":
            return "adjective"
        elif language_code == "ar":
            return "adjective"
        elif language_code == "hi":
            return "adjective"

    # For ACTION_KEYWORD, use infinitive (for Romance languages)
    if pattern == "ACTION_KEYWORD":
        if language_code == "es":
            return "infinitive"
        elif language_code == "ar":
            return "masdar"  # Arabic verbal noun
        elif language_code == "hi":
            return "infinitive"

    # For OPERATOR_KEYWORD, typically conjunction
    if pattern == "OPERATOR_KEYWORD":
        return "conjunction"

    # For STATE_KEYWORD, typically conjunction or preposition
    if pattern == "STATE_KEYWORD":
        if term in ["if", "elif", "else"]:
            return "conjunction"
        elif term in ["for", "while"]:
            return "conjunction"
        elif term in ["with", "in", "from", "as"]:
            return "preposition"
        else:
            return "conjunction"

    # Default
    return "varies"


def write_yaml_language_pack(language_code: str, yaml_data: Dict[str, Any]) -> Path:
    """Write YAML data to language pack file."""

    # Determine output path
    pack_code = yaml_data["language"]["code"]
    output_dir = Path(__file__).parent.parent.parent / "libs" / "i18n" / "language-packs" / pack_code
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "keywords.yml"

    # Write YAML file
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=1000,  # Prevent line wrapping
        )

    print(f"✓ Created {output_file}")
    print(f"  - {len(yaml_data['keywords'])} keywords")
    print(f"  - {len(yaml_data['builtins'])} builtins")
    print(f"  - {yaml_data['metadata']['review_count']} community reviews")

    return output_file


def main():
    """Main conversion function."""
    print("Converting JSON translations to YAML language packs...\n")

    # Languages to convert
    languages = ["es", "ar", "hi"]

    for lang_code in languages:
        print(f"Processing {LANGUAGE_METADATA[lang_code]['name']} ({lang_code})...")

        # Load JSON data
        translation_data = load_json_translation(lang_code)

        # Convert to YAML format
        yaml_data = convert_to_yaml_format(lang_code, translation_data)

        # Write YAML file
        write_yaml_language_pack(lang_code, yaml_data)
        print()

    print("✓ All language packs converted successfully!")
    print("\nNext steps:")
    print("1. Review the generated YAML files")
    print("2. Test with the legesher-core transformer")
    print("3. Update language-packs README with migration notes")


if __name__ == "__main__":
    main()
