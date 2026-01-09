#!/usr/bin/env python3
"""Generate TypeScript language definitions from languages.json.

This script reads the canonical languages.json and generates:
1. TypeScript module for VS Code extension (libs/vs-code/src/generated/languages.ts)

Usage:
    python -m legesher_i18n.scripts.generate_languages
    # or from repo root:
    uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
"""

import json
import sys
from pathlib import Path

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).parent
I18N_DIR = SCRIPT_DIR.parent
REPO_ROOT = I18N_DIR.parent.parent.parent
LANGUAGES_JSON = I18N_DIR / "languages.json"
VSCODE_GENERATED_DIR = REPO_ROOT / "libs" / "vs-code" / "src" / "generated"


def load_languages() -> dict:
    """Load languages.json source file."""
    with open(LANGUAGES_JSON, encoding="utf-8") as f:
        return json.load(f)


def generate_typescript(data: dict) -> str:
    """Generate TypeScript module from language data."""
    languages = data["languages"]
    canonical = data["canonical_language"]

    # Build the TypeScript file
    lines = [
        "/**",
        " * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY",
        " *",
        " * This file is generated from libs/i18n/legesher_i18n/languages.json",
        " * Run: uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py",
        " */",
        "",
        "export type LanguageStatus = 'available' | 'experimental' | 'deprecated';",
        "",
        "export interface LanguageMetadata {",
        "    name: string;",
        "    native: string;",
        "    iso639_2: string;",
        "    bcp47: string;",
        "    rtl: boolean;",
        "    status: LanguageStatus;",
        "}",
        "",
        "export type LanguageCode = ",
    ]

    # Add union type of all language codes
    # Format: 'code1' | 'code2' | ... | 'codeN';
    codes = sorted(languages.keys())
    for i, code in enumerate(codes):
        is_last = i == len(codes) - 1
        terminator = ";" if is_last else " |"
        lines.append(f"    '{code}'{terminator}")

    lines.extend(
        [
            "",
            f"export const CANONICAL_LANGUAGE: LanguageCode = '{canonical}';",
            "",
            "export const LANGUAGE_METADATA: Record<LanguageCode, LanguageMetadata> = {",
        ]
    )

    # Add each language
    for code in codes:
        lang = languages[code]
        name = lang["name"]
        native = lang["native"]
        iso639_2 = lang["iso639_2"]
        bcp47 = lang["bcp47"]
        rtl = "true" if lang["rtl"] else "false"
        status = lang["status"]
        lines.append(
            f"    '{code}': {{ name: '{name}', native: '{native}', iso639_2: '{iso639_2}', bcp47: '{bcp47}', rtl: {rtl}, status: '{status}' }},"
        )

    lines.extend(
        [
            "};",
            "",
            "/**",
            " * Get all available language codes.",
            " */",
            "export function getAvailableLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => LANGUAGE_METADATA[code as LanguageCode].status === 'available') as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get all active (non-deprecated) language codes.",
            " * Returns both 'available' and 'experimental' status languages.",
            " */",
            "export function getActiveLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => {",
            "            const status = LANGUAGE_METADATA[code as LanguageCode].status;",
            "            return status === 'available' || status === 'experimental';",
            "        }) as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get all RTL (right-to-left) language codes.",
            " */",
            "export function getRtlLanguageCodes(): LanguageCode[] {",
            "    return Object.keys(LANGUAGE_METADATA)",
            "        .filter(code => LANGUAGE_METADATA[code as LanguageCode].rtl) as LanguageCode[];",
            "}",
            "",
            "/**",
            " * Get the English name for a language code.",
            " */",
            "export function getLanguageName(code: string): string {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.name ?? code.toUpperCase();",
            "}",
            "",
            "/**",
            " * Get the native name for a language code.",
            " */",
            "export function getLanguageNativeName(code: string): string {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.native ?? code.toUpperCase();",
            "}",
            "",
            "/**",
            " * Check if a language code uses RTL script.",
            " */",
            "export function isRtlLanguage(code: string): boolean {",
            "    return LANGUAGE_METADATA[code as LanguageCode]?.rtl ?? false;",
            "}",
            "",
            "/**",
            " * Check if a language code is supported.",
            " */",
            "export function isSupportedLanguage(code: string): boolean {",
            "    return code in LANGUAGE_METADATA;",
            "}",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Generate TypeScript from languages.json."""
    print(f"Loading {LANGUAGES_JSON}...")

    if not LANGUAGES_JSON.exists():
        print(f"ERROR: {LANGUAGES_JSON} not found")
        return 1

    data = load_languages()
    languages = data["languages"]
    print(f"Found {len(languages)} languages")

    # Generate TypeScript
    ts_content = generate_typescript(data)

    # Ensure output directory exists
    VSCODE_GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    ts_output = VSCODE_GENERATED_DIR / "languages.ts"
    with open(ts_output, "w", encoding="utf-8") as f:
        f.write(ts_content)
    print(f"Generated {ts_output}")

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
