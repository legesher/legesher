#!/usr/bin/env python3
"""
Smart translation of Python content for language packs.

This script leverages existing translations from previous Python versions
to minimize translation work. It identifies new items and only translates those,
achieving a 95%+ reuse rate across versions.

Usage:
    # Translate new Python 3.14 content to Spanish
    python translate_content.py --version 3.14 --language es

    # Translate with specific API
    python translate_content.py --version 3.14 --language es --api deepl --api-key xxx

    # Dry run (no API calls)
    python translate_content.py --version 3.14 --language es --dry-run
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print(
        "Warning: 'pyyaml' not available. Cannot load existing language packs.",
        file=sys.stderr,
    )


@dataclass
class TranslationResult:
    """Result of translation operation."""

    item: str
    translation: str
    source: str  # 'reused' or 'translated'
    confidence: str  # 'high', 'medium', 'low'
    similar_to: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MockTranslator:
    """Mock translator for testing without API calls."""

    def __init__(self, target_language: str):
        """
        Initialize mock translator.

        Args:
            target_language: Target language code
        """
        self.target_language = target_language

    def translate(
        self,
        item: str,
        context: str | None = None,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """
        Mock translation (returns {item}__{language}).

        Args:
            item: English term to translate
            context: Additional context (unused in mock)
            glossary: Existing translations (unused in mock)

        Returns:
            Mock translated term
        """
        return f"{item}__{self.target_language}"


class DeepLTranslator:
    """DeepL translator integration."""

    def __init__(self, api_key: str, target_language: str):
        """
        Initialize DeepL translator.

        Args:
            api_key: DeepL API key
            target_language: Target language code
        """
        try:
            import deepl

            self.translator = deepl.Translator(api_key)
            self.target_language = target_language.upper()
        except ImportError:
            raise RuntimeError(
                "deepl library required for DeepL translation. Install with: pip install deepl"
            )

    def translate(
        self,
        item: str,
        context: str | None = None,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """
        Translate using DeepL API.

        Args:
            item: English term to translate
            context: Additional context
            glossary: Existing translations for reference

        Returns:
            Translated term
        """
        # Prepare context if available
        text_to_translate = item
        if context:
            text_to_translate = f"{item}\n\nContext: {context}"

        # Translate
        result = self.translator.translate_text(
            text_to_translate, target_lang=self.target_language
        )

        # Extract just the term (first line if context was added)
        translation = result.text.split("\n")[0] if context else result.text

        return translation.strip()


class GoogleTranslator:
    """Google Translate integration."""

    def __init__(self, api_key: str, target_language: str):
        """
        Initialize Google translator.

        Args:
            api_key: Google API key
            target_language: Target language code
        """
        try:
            from google.cloud import translate_v2 as translate

            self.translator = translate.Client()
            self.target_language = target_language
        except ImportError:
            raise RuntimeError(
                "google-cloud-translate required for Google translation. "
                "Install with: pip install google-cloud-translate"
            )

    def translate(
        self,
        item: str,
        context: str | None = None,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """
        Translate using Google Translate API.

        Args:
            item: English term to translate
            context: Additional context
            glossary: Existing translations for reference

        Returns:
            Translated term
        """
        text_to_translate = item
        if context:
            text_to_translate = f"{item} ({context})"

        result = self.translator.translate(
            text_to_translate, target_language=self.target_language
        )

        # Extract translation
        translation = result["translatedText"]

        # Clean up if context was added
        if context and "(" in translation:
            translation = translation.split("(")[0].strip()

        return translation


class SmartTranslator:
    """Intelligently translate Python content with high reuse rate."""

    def __init__(
        self,
        target_language: str,
        api_provider: str = "mock",
        api_key: str | None = None,
    ):
        """
        Initialize translator.

        Args:
            target_language: Target language code (e.g., 'es', 'ar', 'hi')
            api_provider: Translation API provider ('mock', 'deepl', 'google')
            api_key: API key for translation service
        """
        self.target_language = target_language
        self.api_provider = api_provider

        # Initialize translator backend
        if api_provider == "mock":
            self.translator = MockTranslator(target_language)
        elif api_provider == "deepl":
            if not api_key:
                raise ValueError("API key required for DeepL translation")
            self.translator = DeepLTranslator(api_key, target_language)
        elif api_provider == "google":
            if not api_key:
                raise ValueError("API key required for Google translation")
            self.translator = GoogleTranslator(api_key, target_language)
        else:
            raise ValueError(f"Unknown API provider: {api_provider}")

    def load_previous_pack(
        self, version: str, language_pack_dir: Path
    ) -> dict[str, str]:
        """
        Load language pack from previous Python version.

        Args:
            version: Python version (e.g., "3.14")
            language_pack_dir: Directory containing language packs

        Returns:
            Dict mapping English terms to translations
        """
        if not YAML_AVAILABLE:
            raise RuntimeError(
                "pyyaml required to load language packs. Install with: pip install pyyaml"
            )

        # Try to find the most recent previous version
        pack_dir = language_pack_dir / self.target_language

        if not pack_dir.exists():
            print(
                f"No existing language pack found for {self.target_language}",
                file=sys.stderr,
            )
            return {}

        # Look for keywords.yml (current format)
        keywords_file = pack_dir / "keywords.yml"
        if keywords_file.exists():
            return self._load_keywords_yaml(keywords_file)

        # Look for version-specific files (legacy format)
        version_files = list(pack_dir.glob("python-*.yml"))
        if version_files:
            # Use the most recent one
            latest_file = max(version_files, key=lambda p: p.name)
            print(f"Loading previous pack from: {latest_file}")
            return self._load_keywords_yaml(latest_file)

        print(f"No previous language pack found in {pack_dir}", file=sys.stderr)
        return {}

    def _load_keywords_yaml(self, yaml_path: Path) -> dict[str, str]:
        """
        Load keywords from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Dict mapping English terms to translations
        """
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        translations = {}

        # Extract keywords section
        keywords = data.get("keywords", {})
        for english_term, term_data in keywords.items():
            if isinstance(term_data, dict):
                translation = term_data.get("translation")
                if translation:
                    translations[english_term] = translation
            elif isinstance(term_data, str):
                translations[english_term] = term_data

        return translations

    def identify_new_items(
        self, new_content: dict[str, Any], existing_pack: dict[str, str]
    ) -> list[str]:
        """
        Identify items not in existing pack.

        Args:
            new_content: New Python content (from extract_python_content.py)
            existing_pack: Existing language pack

        Returns:
            List of new items needing translation
        """
        new_items = []
        existing_terms = set(existing_pack.keys())

        # Check keywords
        if "keywords" in new_content:
            keywords_data = new_content["keywords"]

            # Handle both formats: list or dict with 'all' key
            if isinstance(keywords_data, dict):
                all_keywords = keywords_data.get("all", [])
            else:
                all_keywords = keywords_data

            for keyword in all_keywords:
                if keyword not in existing_terms:
                    new_items.append(keyword)

        # Check builtins
        if "builtins" in new_content:
            for builtin_name in new_content["builtins"].keys():
                if builtin_name not in existing_terms:
                    new_items.append(builtin_name)

        # Check types
        if "types" in new_content:
            for type_name in new_content["types"].keys():
                if type_name not in existing_terms:
                    new_items.append(type_name)

        return sorted(set(new_items))

    def find_similar_items(self, item: str, existing_pack: dict[str, str]) -> list[str]:
        """
        Find similar items in existing pack for context.

        Uses simple string similarity (edit distance, substring matching)
        to find related terms.

        Args:
            item: New item to translate
            existing_pack: Existing translations

        Returns:
            List of similar items (max 3)
        """
        if not existing_pack:
            return []

        similarities = []

        for existing_item in existing_pack.keys():
            # Calculate similarity ratio
            ratio = SequenceMatcher(None, item.lower(), existing_item.lower()).ratio()

            # Boost score if one is substring of other
            if (
                item.lower() in existing_item.lower()
                or existing_item.lower() in item.lower()
            ):
                ratio += 0.2

            similarities.append((existing_item, ratio))

        # Sort by similarity and return top 3
        similarities.sort(key=lambda x: x[1], reverse=True)

        return [item for item, ratio in similarities[:3] if ratio > 0.3]

    def translate_item(
        self,
        item: str,
        context: str | None = None,
        glossary: dict[str, str] | None = None,
    ) -> str:
        """
        Translate a single item using translation API.

        Args:
            item: English term to translate
            context: Additional context for translation
            glossary: Existing translations to use as reference

        Returns:
            Translated term
        """
        # Build context from glossary if available
        if glossary:
            context_parts = []
            if context:
                context_parts.append(context)

            # Add similar terms from glossary
            similar_terms = []
            for key, value in list(glossary.items())[:3]:
                similar_terms.append(f"{key} -> {value}")

            if similar_terms:
                context_parts.append("Similar terms: " + ", ".join(similar_terms))

            full_context = "; ".join(context_parts) if context_parts else None
        else:
            full_context = context

        return self.translator.translate(item, context=full_context, glossary=glossary)

    def generate_translations(
        self,
        version: str,
        content: dict[str, Any],
        language_pack_dir: Path,
        dry_run: bool = False,
    ) -> dict[str, TranslationResult]:
        """
        Generate translations for all content.

        Main algorithm:
        1. Load previous version's language pack
        2. For each item in new content:
           a. If exists in previous pack: reuse
           b. If new: translate with API (using context from similar items)
        3. Return all translations with metadata

        Args:
            version: Python version (e.g., "3.14")
            content: Extracted Python content
            language_pack_dir: Directory containing language packs
            dry_run: If True, don't make actual API calls

        Returns:
            Dict mapping items to TranslationResult
        """
        print(f"\n{'=' * 60}")
        print(f"Smart Translation: Python {version} -> {self.target_language}")
        print(f"{'=' * 60}\n")

        # Load previous pack
        print("Loading previous language pack...")
        existing_pack = self.load_previous_pack(version, language_pack_dir)
        print(f"  Loaded {len(existing_pack)} existing translations")

        # Identify all items to translate
        all_items = set()

        # Extract all keywords
        if "keywords" in content:
            keywords_data = content["keywords"]
            if isinstance(keywords_data, dict):
                all_items.update(keywords_data.get("all", []))
            else:
                all_items.update(keywords_data)

        # Extract builtins
        if "builtins" in content:
            all_items.update(content["builtins"].keys())

        # Extract types
        if "types" in content:
            all_items.update(content["types"].keys())

        print(f"  Found {len(all_items)} total items in Python {version}")

        # Identify new items
        new_items = self.identify_new_items(content, existing_pack)
        print(f"  Identified {len(new_items)} new items needing translation")

        if new_items:
            print(f"\n  New items: {', '.join(new_items[:10])}")
            if len(new_items) > 10:
                print(f"             ... and {len(new_items) - 10} more")

        # Generate translations
        results = {}
        api_calls = 0

        print("\nProcessing translations...")

        for item in sorted(all_items):
            if item in existing_pack:
                # Reuse existing translation
                results[item] = TranslationResult(
                    item=item,
                    translation=existing_pack[item],
                    source="reused",
                    confidence="high",
                    notes="Reused from previous Python version",
                )
            else:
                # Need to translate
                similar = self.find_similar_items(item, existing_pack)

                if dry_run:
                    # Don't make API call in dry run
                    translation = f"{item}__{self.target_language}_dryrun"
                    confidence = "medium"
                else:
                    # Build context from similar items
                    context = "Python keyword or built-in function"
                    glossary = {
                        s: existing_pack[s] for s in similar if s in existing_pack
                    }

                    translation = self.translate_item(
                        item, context=context, glossary=glossary
                    )
                    api_calls += 1
                    confidence = "medium"

                results[item] = TranslationResult(
                    item=item,
                    translation=translation,
                    source="translated",
                    confidence=confidence,
                    similar_to=similar[0] if similar else None,
                    notes=f"Newly translated for Python {version}",
                )

        print(f"  ✓ Processed {len(results)} translations")
        if not dry_run:
            print(f"  ✓ Made {api_calls} API calls")

        return results

    def calculate_statistics(
        self, results: dict[str, TranslationResult]
    ) -> dict[str, Any]:
        """
        Calculate statistics about translation operation.

        Returns:
            Dict with:
            - total_items
            - reused_count
            - translated_count
            - reuse_rate
            - api_calls_made
            - estimated_cost
        """
        total = len(results)
        reused = sum(1 for r in results.values() if r.source == "reused")
        translated = sum(1 for r in results.values() if r.source == "translated")

        reuse_rate = (reused / total * 100) if total > 0 else 0

        # Estimate cost (rough estimate: $0.00005 per character for DeepL)
        if self.api_provider == "deepl":
            total_chars = sum(
                len(r.item) for r in results.values() if r.source == "translated"
            )
            estimated_cost = total_chars * 0.00005
        else:
            estimated_cost = 0.0

        return {
            "total_items": total,
            "reused_count": reused,
            "translated_count": translated,
            "reuse_rate": f"{reuse_rate:.1f}%",
            "api_calls_made": translated,
            "estimated_cost": f"${estimated_cost:.4f}",
        }


def save_translations(results: dict[str, TranslationResult], output_path: Path) -> None:
    """
    Save translation results to JSON.

    Args:
        results: Translation results
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert results to serializable format
    output_data = {item: result.to_dict() for item, result in results.items()}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved translations to: {output_path}")


def print_statistics(stats: dict[str, Any]) -> None:
    """
    Print statistics summary.

    Args:
        stats: Statistics dictionary
    """
    print(f"\n{'=' * 60}")
    print("Translation Statistics")
    print(f"{'=' * 60}")
    print(f"  Total items:        {stats['total_items']}")
    print(f"  Reused:             {stats['reused_count']}")
    print(f"  Newly translated:   {stats['translated_count']}")
    print(f"  Reuse rate:         {stats['reuse_rate']}")
    print(f"  API calls made:     {stats['api_calls_made']}")
    print(f"  Estimated cost:     {stats['estimated_cost']}")
    print(f"{'=' * 60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart translation of Python content")

    parser.add_argument("--version", required=True, help="Python version (e.g., 3.14)")

    parser.add_argument(
        "--language", required=True, help="Target language code (e.g., es, ar, zh)"
    )

    parser.add_argument(
        "--content",
        type=Path,
        help="Path to extracted content JSON (from extract_python_content.py)",
    )

    parser.add_argument(
        "--language-packs",
        type=Path,
        help="Path to language-packs directory",
    )

    parser.add_argument(
        "--api",
        choices=["deepl", "google", "mock"],
        default="mock",
        help="Translation API provider (default: mock for testing)",
    )

    parser.add_argument("--api-key", help="API key for translation service")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate translation without API calls",
    )

    parser.add_argument("--output", type=Path, help="Output file for translations")

    args = parser.parse_args()

    # Determine paths
    if args.content:
        content_path = args.content
    else:
        content_path = Path(f"python-content-{args.version}.json")

    if args.language_packs:
        language_pack_dir = args.language_packs
    else:
        # Default to language-packs in current directory or parent
        if (Path.cwd() / "language-packs").exists():
            language_pack_dir = Path.cwd() / "language-packs"
        elif (Path.cwd().parent / "language-packs").exists():
            language_pack_dir = Path.cwd().parent / "language-packs"
        else:
            language_pack_dir = Path("language-packs")

    if args.output:
        output_path = args.output
    else:
        output_path = Path(f"translations-{args.version}-{args.language}.json")

    # Load content
    if not content_path.exists():
        print(f"Error: Content file not found: {content_path}", file=sys.stderr)
        print(
            "\nRun extract_python_content.py first to extract content:", file=sys.stderr
        )
        print(
            f"  python extract_python_content.py --version {args.version}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading content from: {content_path}")
    with open(content_path, encoding="utf-8") as f:
        content = json.load(f)

    # Initialize translator
    try:
        translator = SmartTranslator(
            target_language=args.language,
            api_provider=args.api,
            api_key=args.api_key,
        )
    except Exception as e:
        print(f"Error initializing translator: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate translations
    try:
        results = translator.generate_translations(
            version=args.version,
            content=content,
            language_pack_dir=language_pack_dir,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"Error generating translations: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Calculate and print statistics
    stats = translator.calculate_statistics(results)
    print_statistics(stats)

    # Save results
    save_translations(results, output_path)

    print("✓ Translation complete!")

    if args.dry_run:
        print("\n  Note: This was a dry run. No actual API calls were made.")


if __name__ == "__main__":
    main()
