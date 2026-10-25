#!/usr/bin/env python3
"""
Language Pack Analysis Script

Analyzes every published Python language pack to detect:
- Multi-word translations (spaces)
- Punctuation in translations (/, -, :, ., ,, ;)
- Duplicate translations (same value for different terms)
- Untranslated/placeholder terms
- Capitalization issues (True/False/None)

Generates reports in libs/i18n/reports/ directory.
"""

import yaml
from pathlib import Path
from collections import defaultdict
import json
import unicodedata


# Language codes for every published pack, read from the registry rather than
# kept by hand (a hand-kept list here silently skipped uk and sw).
with open("libs/i18n/legesher_i18n/languages.json", encoding="utf-8") as _f:
    LANGUAGES = sorted(json.load(_f)["languages"])

# Known placeholders/untranslated markers
PLACEHOLDER_PATTERNS = [
    "el término traducido",
    "the translated term",
    "the global variables",
    "the classmethod",
]

# Scripts without uppercase/lowercase distinction
NON_CASE_SCRIPTS = {
    "am": "Amharic/Ge'ez",
    "ar": "Arabic",
    "bn": "Bengali",
    "fa": "Persian/Arabic",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi/Devanagari",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "ml": "Malayalam",
    "mn": "Mongolian/Cyrillic",
    "my": "Burmese",
    "si": "Sinhala",
    "te": "Telugu",
    "th": "Thai",
    "ur": "Urdu/Arabic",
    "zh": "Chinese",
}


def is_latin_script(text):
    """Check if text uses primarily Latin script."""
    if not text:
        return False
    # Sample first few characters
    sample = text[:3]
    for char in sample:
        if char.isalpha():
            script = unicodedata.name(char, "").split()[0]
            return script == "LATIN"
    return False


def has_punctuation(text):
    """Check for problematic punctuation in translation."""
    # Allow accents/diacritics, but flag /, -, :, .
    problematic = ["/", "-", ":", ".", ",", ";"]
    return any(p in text for p in problematic)


def analyze_language_pack(lang_code):
    """Analyze a single language pack."""
    pack_path = Path(
        f"libs/i18n/language-packs/python/{lang_code}/legesher_i18n_python_{lang_code}/packs/3.10.yml"
    )

    if not pack_path.exists():
        return None

    with open(pack_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    issues = {
        "multiword": [],
        "punctuation": [],
        "duplicates": [],
        "untranslated": [],
        "capitalization": [],
    }

    # Track all translations to find duplicates
    translation_map = defaultdict(list)

    # Analyze each section
    for section in ["keywords", "builtins", "exceptions"]:
        if section not in data:
            continue

        for term, translation in data[section].items():
            # Convert to string (some might be quoted)
            translation_str = str(translation)

            # Track for duplicate detection
            translation_map[translation_str].append((section, term))

            # Check for spaces (multi-word)
            if " " in translation_str and section in ["keywords", "builtins"]:
                issues["multiword"].append(
                    {
                        "section": section,
                        "term": term,
                        "translation": translation_str,
                        "word_count": len(translation_str.split()),
                    }
                )

            # Check for punctuation
            if has_punctuation(translation_str):
                punct_found = [
                    p for p in ["/", "-", ":", ".", ",", ";"] if p in translation_str
                ]
                issues["punctuation"].append(
                    {
                        "section": section,
                        "term": term,
                        "translation": translation_str,
                        "punctuation": punct_found,
                    }
                )

            # Check for untranslated/placeholder
            if any(
                pattern.lower() in translation_str.lower()
                for pattern in PLACEHOLDER_PATTERNS
            ):
                issues["untranslated"].append(
                    {
                        "section": section,
                        "term": term,
                        "translation": translation_str,
                        "reason": "placeholder_detected",
                    }
                )
            # Check for fully English phrases in non-English packs
            elif (
                lang_code != "en"
                and translation_str.replace(" ", "").replace("-", "").isascii()
            ):
                # Simple heuristic: if it's multi-word ASCII in non-English pack, flag it
                if " " in translation_str and len(translation_str.split()) >= 2:
                    # Check if it looks like English words
                    words = translation_str.lower().split()
                    common_english = [
                        "the",
                        "a",
                        "an",
                        "is",
                        "are",
                        "of",
                        "to",
                        "in",
                        "for",
                        "on",
                    ]
                    if any(w in common_english for w in words):
                        issues["untranslated"].append(
                            {
                                "section": section,
                                "term": term,
                                "translation": translation_str,
                                "reason": "appears_english",
                            }
                        )

            # Check capitalization for True/False/None
            if term in ["True", "False", "None"]:
                is_latin = is_latin_script(translation_str)
                if (
                    is_latin
                    and translation_str
                    and translation_str[0].isalpha()
                    and translation_str[0].islower()
                ):
                    issues["capitalization"].append(
                        {
                            "section": section,
                            "term": term,
                            "translation": translation_str,
                            "issue": "should_be_capitalized",
                            "script": "latin",
                        }
                    )
                elif not is_latin and lang_code in NON_CASE_SCRIPTS:
                    # Note: this is fine, just track for comment addition
                    issues["capitalization"].append(
                        {
                            "section": section,
                            "term": term,
                            "translation": translation_str,
                            "issue": "no_case_system",
                            "script": NON_CASE_SCRIPTS[lang_code],
                        }
                    )

    # Find duplicates
    for translation, occurrences in translation_map.items():
        if len(occurrences) > 1:
            issues["duplicates"].append(
                {
                    "translation": translation,
                    "terms": [(section, term) for section, term in occurrences],
                }
            )

    return issues


def generate_reports(all_issues):
    """Generate markdown reports from analysis."""
    reports_dir = Path("libs/i18n/reports")
    reports_dir.mkdir(exist_ok=True)

    # DUPLICATES REPORT
    with open(reports_dir / "DUPLICATES_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Critical: Duplicate Translations\n\n")
        f.write("**Priority**: CRITICAL - These break functionality!\n\n")
        f.write(
            "Same translation used for multiple different terms. Each term must have unique translation.\n\n"
        )

        has_duplicates = False
        for lang, issues in sorted(all_issues.items()):
            if issues["duplicates"]:
                has_duplicates = True
                f.write(f"## {lang.upper()} ({get_language_name(lang)})\n\n")
                for dup in issues["duplicates"]:
                    terms_str = ", ".join(
                        [f"`{term}`" for section, term in dup["terms"]]
                    )
                    f.write(f'- **Translation**: "{dup["translation"]}"\n')
                    f.write(f"  - **Terms**: {terms_str}\n")
                    f.write("  - **Action**: Keep first term, re-translate others\n\n")

        if not has_duplicates:
            f.write("✅ No duplicates found!\n")

    # UNTRANSLATED REPORT
    with open(reports_dir / "UNTRANSLATED_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Untranslated/Placeholder Terms\n\n")
        f.write("**Priority**: HIGH - Need pipeline re-runs\n\n")
        f.write("Terms that appear to be placeholders or untranslated English.\n\n")

        has_untranslated = False
        for lang, issues in sorted(all_issues.items()):
            if issues["untranslated"]:
                has_untranslated = True
                f.write(f"## {lang.upper()} ({get_language_name(lang)})\n\n")
                for item in issues["untranslated"]:
                    f.write(f'- `{item["term"]}`: "{item["translation"]}"\n')
                    f.write(f"  - Reason: {item['reason']}\n")
                    f.write(f"  - Section: {item['section']}\n\n")

        if not has_untranslated:
            f.write("✅ No untranslated terms found!\n")

    # MULTIWORD REPORT
    with open(reports_dir / "MULTIWORD_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Multi-word Translations (Spaces)\n\n")
        f.write("**Priority**: MEDIUM - Will be auto-fixed\n\n")
        f.write("Translations with spaces that need to be concatenated.\n\n")

        total_count = 0
        for lang, issues in sorted(all_issues.items()):
            if issues["multiword"]:
                count = len(issues["multiword"])
                total_count += count
                f.write(
                    f"## {lang.upper()} ({get_language_name(lang)}) - {count} issues\n\n"
                )

                # Show first 5 examples
                for item in issues["multiword"][:5]:
                    f.write(
                        f'- `{item["term"]}`: "{item["translation"]}" ({item["word_count"]} words)\n'
                    )

                if len(issues["multiword"]) > 5:
                    f.write(f"\n... and {len(issues['multiword']) - 5} more\n\n")
                else:
                    f.write("\n")

        f.write(
            f"\n**Total**: {total_count} multi-word translations across all packs\n"
        )

    # PUNCTUATION REPORT
    with open(reports_dir / "PUNCTUATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Translations with Punctuation\n\n")
        f.write("**Priority**: MEDIUM - Will be auto-fixed\n\n")
        f.write("Translations containing /, -, :, . or other punctuation.\n\n")

        total_count = 0
        for lang, issues in sorted(all_issues.items()):
            if issues["punctuation"]:
                count = len(issues["punctuation"])
                total_count += count
                f.write(
                    f"## {lang.upper()} ({get_language_name(lang)}) - {count} issues\n\n"
                )

                # Show first 5 examples
                for item in issues["punctuation"][:5]:
                    punct_str = ", ".join(f'"{p}"' for p in item["punctuation"])
                    f.write(f'- `{item["term"]}`: "{item["translation"]}"\n')
                    f.write(f"  - Punctuation: {punct_str}\n")

                if len(issues["punctuation"]) > 5:
                    f.write(f"\n... and {len(issues['punctuation']) - 5} more\n\n")
                else:
                    f.write("\n")

        f.write(f"\n**Total**: {total_count} translations with punctuation\n")

    # CAPITALIZATION REPORT
    with open(reports_dir / "CAPITALIZATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Capitalization Issues\n\n")
        f.write("**Priority**: LOW - Needs review\n\n")
        f.write("True/False/None capitalization issues and non-case scripts.\n\n")

        f.write("## Latin Scripts - Need Capitalization Fix\n\n")
        has_latin = False
        for lang, issues in sorted(all_issues.items()):
            latin_issues = [
                i for i in issues["capitalization"] if i.get("script") == "latin"
            ]
            if latin_issues:
                has_latin = True
                f.write(f"### {lang.upper()} ({get_language_name(lang)})\n\n")
                for item in latin_issues:
                    f.write(
                        f'- `{item["term"]}`: "{item["translation"]}" → Should start with capital\n'
                    )
                f.write("\n")

        if not has_latin:
            f.write("✅ No issues found\n\n")

        f.write("## Non-Case Scripts - Add Comment\n\n")
        f.write("These are fine, but should have comment noting no case system.\n\n")
        has_noncase = False
        for lang, issues in sorted(all_issues.items()):
            noncase_issues = [
                i
                for i in issues["capitalization"]
                if i.get("issue") == "no_case_system"
            ]
            if noncase_issues:
                has_noncase = True
                f.write(
                    f"### {lang.upper()} ({get_language_name(lang)}) - {noncase_issues[0]['script']}\n\n"
                )
                for item in noncase_issues:
                    f.write(f'- `{item["term"]}`: "{item["translation"]}"\n')
                f.write("\n")

        if not has_noncase:
            f.write("✅ No non-case scripts detected\n")

    # Summary JSON
    summary = {}
    for lang, issues in all_issues.items():
        summary[lang] = {
            "duplicates": len(issues["duplicates"]),
            "untranslated": len(issues["untranslated"]),
            "multiword": len(issues["multiword"]),
            "punctuation": len(issues["punctuation"]),
            "capitalization": len(issues["capitalization"]),
        }

    with open(reports_dir / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def get_language_name(code):
    """Get full language name from code, as the registry names it."""
    with open("libs/i18n/legesher_i18n/languages.json", encoding="utf-8") as f:
        names = {k: v["name"] for k, v in json.load(f)["languages"].items()}
    return names.get(code, code)


def main():
    """Main analysis function."""
    print(f"🔍 Analyzing {len(LANGUAGES)} Python language packs...\n")

    all_issues = {}

    for lang in LANGUAGES:
        print(f"Analyzing {lang}...", end=" ")
        issues = analyze_language_pack(lang)
        if issues:
            all_issues[lang] = issues

            # Print summary
            total = sum(len(v) for v in issues.values())
            print(f"✓ ({total} issues found)")
        else:
            print("⚠️  Pack not found")

    print("\n📊 Generating reports in libs/i18n/reports/...\n")
    generate_reports(all_issues)

    print("✅ Analysis complete!\n")
    print("Reports generated:")
    print("  - DUPLICATES_REPORT.md (CRITICAL)")
    print("  - UNTRANSLATED_REPORT.md (HIGH)")
    print("  - MULTIWORD_REPORT.md (MEDIUM)")
    print("  - PUNCTUATION_REPORT.md (MEDIUM)")
    print("  - CAPITALIZATION_REPORT.md (LOW)")
    print("  - analysis_summary.json (overview)")


if __name__ == "__main__":
    main()
