#!/usr/bin/env python
"""Translate only untranslated entries in language packs.

This script reads the output from find_untranslated.py and runs the translation
pipeline only for terms that are still in English (key == value).

Usage:
    # Dry run to see what would be translated
    python translate_untranslated.py --dry-run

    # Translate all untranslated terms (excluding unsupported languages)
    python translate_untranslated.py

    # Translate specific languages only
    python translate_untranslated.py --languages es fr de

    # Use a specific model
    python translate_untranslated.py --model aya
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.translate.find_untranslated import scan_all_languages
from scripts.translate.pipeline import PipelineConfig, TranslationPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Languages NOT supported by Aya-23 (must use different model)
# Based on Aya-23 documentation: https://huggingface.co/CohereForAI/aya-23-8B
AYA_UNSUPPORTED = {
    "hu",  # Hungarian
    "da",  # Danish
    "no",  # Norwegian
    "sv",  # Swedish
    "fi",  # Finnish
}

# All languages that Aya-23 supports (23 languages total)
AYA_SUPPORTED = {
    "ar",  # Arabic
    "de",  # German
    "el",  # Greek
    "es",  # Spanish
    "fr",  # French
    "he",  # Hebrew
    "hi",  # Hindi
    "id",  # Indonesian
    "it",  # Italian
    "ja",  # Japanese
    "ko",  # Korean
    "ms",  # Malay
    "nl",  # Dutch
    "pl",  # Polish
    "pt",  # Portuguese
    "ru",  # Russian
    "th",  # Thai
    "tr",  # Turkish
    "vi",  # Vietnamese
    "zh",  # Chinese
}


async def translate_language(
    language: str,
    terms: list[str],
    model: str = "ollama",
    ollama_model: str = "command-r",
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Translate specific terms for a single language.

    Args:
        language: Target language code
        terms: List of terms to translate
        model: Model to use (aya, claude, etc.)
        dry_run: If True, don't make real API calls
        verbose: Enable verbose logging

    Returns:
        Dictionary with translation results
    """
    if not terms:
        logger.info(f"No untranslated terms for {language}, skipping")
        return {"language": language, "translated": 0, "skipped": True}

    logger.info(f"Translating {len(terms)} terms for {language} using {model}")

    if dry_run:
        logger.info(
            f"  [DRY RUN] Would translate: {terms[:5]}{'...' if len(terms) > 5 else ''}"
        )
        return {"language": language, "translated": 0, "dry_run": True, "terms": terms}

    # Create pipeline config for this language
    config = PipelineConfig(
        models=[model],
        languages=[language],
        terms=terms,
        dry_run=dry_run,
        skip_existing=False,  # We want to overwrite the untranslated entries
        ollama_model=ollama_model,
    )

    # Initialize and run pipeline
    pipeline = TranslationPipeline(config)

    try:
        stats = await pipeline.run()
        return {
            "language": language,
            "translated": stats.successful_translations,
            "failed": stats.failed_translations,
            "total_cost": stats.total_cost,
        }
    except Exception as e:
        logger.error(f"Error translating {language}: {e}")
        return {"language": language, "error": str(e)}


async def main():
    parser = argparse.ArgumentParser(
        description="Translate only untranslated entries in language packs"
    )
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        help="Specific languages to translate (default: all with untranslated terms)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="ollama",
        choices=["aya", "claude", "ollama"],
        help="Model backend to use for translation (default: ollama)",
    )
    parser.add_argument(
        "--ollama-model",
        default="command-r",
        help="Ollama model name when using --model ollama (default: command-r)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be translated without making API calls",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--include-unsupported",
        action="store_true",
        help="Include languages not supported by Aya-23 (will likely fail or return English)",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export untranslated terms to JSON, don't translate",
    )
    parser.add_argument(
        "--terms",
        "-t",
        nargs="+",
        help="Specific terms to translate (default: all untranslated terms)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Scan for untranslated entries
    logger.info("Scanning language packs for untranslated entries...")
    reports = scan_all_languages()

    # Build list of languages to translate
    if args.languages:
        languages_to_translate = args.languages
    else:
        # All languages with untranslated terms
        languages_to_translate = [
            lang for lang, report in reports.items() if not report.is_complete
        ]

    # Filter out unsupported languages if using Aya
    if args.model == "aya" and not args.include_unsupported:
        skipped = [lang for lang in languages_to_translate if lang in AYA_UNSUPPORTED]
        if skipped:
            logger.warning(
                f"Skipping languages not supported by Aya-23: {skipped}. "
                "Use --model claude or --include-unsupported for these languages."
            )
        languages_to_translate = [
            lang for lang in languages_to_translate if lang not in AYA_UNSUPPORTED
        ]

    # Build translation tasks per language
    translation_tasks = {}
    total_terms = 0

    for language in languages_to_translate:
        if language not in reports:
            logger.warning(f"Language {language} not found in reports")
            continue

        report = reports[language]
        if report.is_complete:
            logger.info(f"{language}: Already complete (100%)")
            continue

        # Get list of untranslated terms
        terms = [entry.term for entry in report.untranslated]

        # Filter by specific terms if provided
        if args.terms:
            terms = [t for t in terms if t in args.terms]
            if not terms:
                logger.debug(f"{language}: No matching terms from --terms filter")
                continue

        translation_tasks[language] = terms
        total_terms += len(terms)

        logger.info(
            f"{language}: {len(terms)} untranslated terms "
            f"({report.completion_percentage:.1f}% complete)"
        )

    if args.export_only:
        # Export to JSON and exit
        output = {
            lang: {"terms": terms, "count": len(terms)}
            for lang, terms in translation_tasks.items()
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if not translation_tasks:
        logger.info("No untranslated terms found!")
        return

    logger.info(
        f"\nTotal: {total_terms} terms across {len(translation_tasks)} languages"
    )
    logger.info(f"Model: {args.model}")

    if args.dry_run:
        logger.info("\n[DRY RUN MODE - No actual translations will be made]")

    # Confirm before proceeding (unless dry-run)
    if not args.dry_run:
        print(f"\nReady to translate {total_terms} terms. Continue? [y/N] ", end="")
        response = input().strip().lower()
        if response != "y":
            logger.info("Aborted by user")
            return

    # Translate each language sequentially to avoid overwhelming the model
    results = []
    for language, terms in translation_tasks.items():
        result = await translate_language(
            language=language,
            terms=terms,
            model=args.model,
            ollama_model=args.ollama_model,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        results.append(result)

        # Brief pause between languages to avoid rate limiting
        if not args.dry_run:
            await asyncio.sleep(1)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TRANSLATION SUMMARY")
    logger.info("=" * 60)

    total_translated = 0
    total_failed = 0
    total_cost = 0.0

    for result in results:
        lang = result["language"]
        if result.get("skipped"):
            logger.info(f"  {lang}: Skipped (no untranslated terms)")
        elif result.get("dry_run"):
            logger.info(
                f"  {lang}: Would translate {len(result.get('terms', []))} terms"
            )
        elif result.get("error"):
            logger.error(f"  {lang}: ERROR - {result['error']}")
        else:
            translated = result.get("translated", 0)
            failed = result.get("failed", 0)
            cost = result.get("total_cost", 0.0)
            total_translated += translated
            total_failed += failed
            total_cost += cost
            logger.info(
                f"  {lang}: {translated} translated, {failed} failed, ${cost:.4f}"
            )

    if not args.dry_run:
        logger.info("-" * 60)
        logger.info(f"  Total: {total_translated} translated, {total_failed} failed")
        logger.info(f"  Cost: ${total_cost:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
