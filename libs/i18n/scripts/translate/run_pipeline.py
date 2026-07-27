#!/usr/bin/env python3
"""CLI script to run the translation pipeline.

Usage:
    # Dry run (no real API calls)
    python run_pipeline.py --dry-run

    # Translate specific terms to specific languages
    python run_pipeline.py --terms def return print --languages es ar fr

    # Full run (all terms, all languages)
    python run_pipeline.py --models claude aya

    # Budget control
    python run_pipeline.py --max-budget 50.00
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.translate.pipeline import TranslationPipeline, PipelineConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run AI translation pipeline for Python terms"
    )

    parser.add_argument(
        "--models",
        nargs="+",
        choices=[
            "claude",
            "aya",
            "aya101-hf",
            "aya-api",
            "ollama",
            "hf",
            "hf-api",
            "tiny-aya",
            "tiny-aya-api",
        ],
        default=["claude", "aya"],
        help="AI models to use for translation. "
        "hf/tiny-aya: generic HuggingFace local model (requires transformers/torch). "
        "hf-api/tiny-aya-api: HuggingFace Inference API (requires HF_TOKEN). "
        "Use --hf-profile or --tiny-aya-variant to select the model.",
    )

    parser.add_argument(
        "--target",
        type=str,
        default="python",
        help="Programming-language target (CORE-1371). 'python' keeps the "
        "historical behavior exactly; other targets (e.g. 'javascript') "
        "source their term inventory from the seeded DB terms table and "
        "season prompts via the target's spec profile (CORE-1608).",
    )

    parser.add_argument(
        "--hf-profile",
        type=str,
        default=None,
        help="HuggingFace model profile name (e.g., 'tiny-aya-earth'). "
        "Use with --models hf or --models hf-api. "
        "Also overrides the default profile for --models tiny-aya / tiny-aya-api.",
    )

    parser.add_argument(
        "--tiny-aya-variant",
        choices=["earth", "fire", "water", "global"],
        default="earth",
        help="Tiny Aya regional variant. Default: earth (West Asian/African languages). "
        "fire: South Asian, water: European/Asia Pacific, global: balanced.",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help="Target language codes (e.g., es ar fr). If not specified, uses all 24 languages",
    )

    parser.add_argument(
        "--terms",
        nargs="+",
        default=None,
        help="Specific terms to translate. If not specified, translates all terms from manifest",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't make real API calls",
    )

    parser.add_argument(
        "--max-budget",
        type=float,
        default=100.0,
        help="Maximum budget in USD (safety limit). Default: 100.00",
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="Directory with context documents. Default: libs/i18n/context/python/",
    )

    parser.add_argument(
        "--output-db",
        type=Path,
        default=None,
        help="Output database path. Default: .legesher/translations.db",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging",
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip translations that already exist in the database",
    )

    return parser.parse_args()


async def main_async(args):
    """Main async entry point."""
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Create config from args
    config = PipelineConfig(
        models=args.models,
        languages=args.languages,
        terms=args.terms,
        target=args.target,
        dry_run=args.dry_run,
        max_budget=args.max_budget,
        context_dir=args.context_dir,
        output_db=args.output_db,
        skip_existing=args.skip_existing,
        hf_profile=args.hf_profile,
        tiny_aya_variant=args.tiny_aya_variant,
    )

    logger.info("Starting translation pipeline...")

    # Run pipeline
    pipeline = TranslationPipeline(config)
    stats = await pipeline.run()

    # Exit with appropriate code
    if stats.failed_translations > 0:
        logger.warning(f"Pipeline completed with {stats.failed_translations} failures")
        return 1
    else:
        logger.info("Pipeline completed successfully")
        return 0


def main():
    """Main entry point."""
    args = parse_args()

    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
