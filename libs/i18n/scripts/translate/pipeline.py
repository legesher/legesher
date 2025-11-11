"""Main translation pipeline orchestrator for CORE-394.

This module coordinates the entire translation process:
1. Load context documents and linguistic standards
2. Generate translations using multiple AI models (Claude, Aya)
3. Track costs and progress
4. Store results in database
5. Export to YAML format
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)

from legesher_i18n.db import TranslationDatabase

from .context_loader import ContextLoader, LinguisticStandardsLoader, load_term_manifest
from .models.base import TranslationRequest, TranslationModel
from .models.claude_model import ClaudeModel
from .models.aya_model import AyaModel
from .yaml_exporter import YAMLExporter

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class PipelineConfig:
    """Configuration for translation pipeline.

    Attributes:
        models: List of models to use ('claude', 'aya', or both)
        languages: List of target language codes
        terms: List of terms to translate (if None, use all from manifest)
        dry_run: If True, don't make real API calls
        max_budget: Maximum budget in USD (safety limit)
        context_dir: Directory with context documents
        standards_file: Path to linguistic standards file
        output_db: Path to output SQLite database
        skip_existing: If True, skip terms that already have translations
    """

    models: List[str] = None  # ['claude', 'aya']
    languages: List[str] = None  # ['es', 'ar', 'fr', ...]
    terms: Optional[List[str]] = None  # If None, use all from manifest
    dry_run: bool = False
    max_budget: float = 100.0  # Stop at $100 (safety margin)
    context_dir: Optional[Path] = None
    standards_file: Optional[Path] = None
    output_db: Optional[Path] = None
    skip_existing: bool = True

    def __post_init__(self):
        """Set defaults."""
        if self.models is None:
            self.models = ["claude", "aya"]
        if self.languages is None:
            # Default to 24 languages from CORE-394
            self.languages = [
                "es",
                "ar",
                "fr",
                "zh",
                "hi",
                "ru",
                "pt",
                "de",
                "ja",
                "ko",
                "it",
                "pl",
                "tr",
                "vi",
                "th",
                "nl",
                "sv",
                "no",
                "da",
                "fi",
                "el",
                "he",
                "id",
                "ms",
            ]


@dataclass
class PipelineStats:
    """Statistics for pipeline execution.

    Tracks progress, costs, and success rates.
    """

    total_translations: int = 0
    successful_translations: int = 0
    failed_translations: int = 0
    total_cost: float = 0.0
    cost_by_model: Dict[str, float] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None

    def __post_init__(self):
        """Initialize nested dicts."""
        if self.cost_by_model is None:
            self.cost_by_model = {}
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)

    def record_success(self, model: str, cost: float):
        """Record a successful translation."""
        self.successful_translations += 1
        self.total_translations += 1
        self.total_cost += cost
        if model not in self.cost_by_model:
            self.cost_by_model[model] = 0.0
        self.cost_by_model[model] += cost

    def record_failure(self):
        """Record a failed translation."""
        self.failed_translations += 1
        self.total_translations += 1

    def finish(self):
        """Mark pipeline as finished."""
        self.end_time = datetime.now(timezone.utc)

    def get_duration(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    def print_summary(self):
        """Print summary to console."""
        console.print("\n[bold green]Pipeline Complete![/bold green]\n")
        console.print(f"Total translations: {self.total_translations}")
        console.print(f"  ✓ Successful: {self.successful_translations}")
        console.print(f"  ✗ Failed: {self.failed_translations}")
        console.print(f"\nTotal cost: [bold]${self.total_cost:.2f}[/bold]")

        for model, cost in self.cost_by_model.items():
            console.print(f"  {model}: ${cost:.2f}")

        duration = self.get_duration()
        console.print(f"\nDuration: {duration:.1f}s ({duration / 60:.1f} minutes)")


class TranslationPipeline:
    """Main translation pipeline orchestrator."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.stats = PipelineStats()

        # Initialize loaders
        self.context_loader = ContextLoader(context_dir=config.context_dir)
        self.standards_loader = LinguisticStandardsLoader(
            standards_file=config.standards_file
        )

        # Initialize database
        self.db = TranslationDatabase(
            db_path=str(config.output_db)
            if config.output_db
            else ".legesher/translations.db"
        )

        # Initialize YAML exporter
        self.yaml_exporter = YAMLExporter(db=self.db)

        # Initialize models
        self.models: Dict[str, TranslationModel] = {}
        if "claude" in config.models:
            self.models["claude"] = ClaudeModel(dry_run=config.dry_run)
        if "aya" in config.models:
            self.models["aya"] = AyaModel(dry_run=config.dry_run)

        logger.info(f"Pipeline initialized with models: {list(self.models.keys())}")
        logger.info(f"Target languages: {config.languages}")
        logger.info(f"Dry run: {config.dry_run}")
        logger.info(f"Database: {self.db.db_path}")

    async def run(self) -> PipelineStats:
        """Run the full translation pipeline.

        Returns:
            Pipeline statistics
        """
        console.print("\n[bold blue]Starting Translation Pipeline[/bold blue]")
        console.print(f"Models: {', '.join(self.config.models)}")
        console.print(f"Languages: {len(self.config.languages)}")
        console.print(f"Dry run: {self.config.dry_run}\n")

        # Get list of terms to translate
        terms = self._get_terms_to_translate()
        console.print(f"Terms to translate: {len(terms)}\n")

        # Calculate total work
        total_tasks = len(terms) * len(self.config.languages) * len(self.models)
        console.print(f"Total translations to generate: {total_tasks}\n")

        # Run translations with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Translating...", total=total_tasks)

            for term in terms:
                for language in self.config.languages:
                    for model_name, model in self.models.items():
                        # Check budget before each translation
                        if self.stats.total_cost >= self.config.max_budget:
                            console.print(
                                f"\n[bold red]Budget limit reached: ${self.stats.total_cost:.2f}[/bold red]"
                            )
                            console.print("Stopping pipeline.")
                            self.stats.finish()
                            return self.stats

                        try:
                            await self._translate_one(term, language, model_name, model)
                            progress.advance(task)
                        except Exception as e:
                            logger.error(
                                f"Failed to translate '{term}' to {language} with {model_name}: {e}"
                            )
                            self.stats.record_failure()
                            progress.advance(task)

        self.stats.finish()

        # Export YAML language packs if not dry-run
        if not self.config.dry_run:
            console.print("\n[bold blue]Exporting YAML language packs...[/bold blue]")
            try:
                exported_files = self.yaml_exporter.export_all_languages(overwrite=True)
                console.print(
                    f"[green]✓ Exported {len(exported_files)} language packs[/green]"
                )
            except Exception as e:
                logger.error(f"Failed to export YAML: {e}")
                console.print(f"[yellow]⚠ YAML export failed: {e}[/yellow]")

        self.stats.print_summary()
        return self.stats

    async def _translate_one(
        self, term: str, language: str, model_name: str, model: TranslationModel
    ):
        """Translate a single term with one model.

        Args:
            term: Python term to translate
            language: Target language code
            model_name: Name of model ('claude', 'aya')
            model: Model instance
        """
        # Load context and standards
        context = self.context_loader.load_context(term)
        standards = self.standards_loader.load_standards(language)

        # Create request
        request = TranslationRequest(
            term=term,
            target_language=language,
            context=context,
            linguistic_standards=standards,
        )

        # Translate
        translation = await model.translate(request)

        # Record stats
        self.stats.record_success(model_name, translation.cost)

        # Store in database (CORE-399 integration)
        if not self.config.dry_run:
            try:
                import json

                translation_id = self.db.add_translation(
                    language_code=language,
                    term=term,
                    term_type="keyword",  # Default to keyword; can be improved later
                    translation=translation.translation,
                    source=model_name,
                    word_type=translation.word_type,
                    word_form=translation.form,
                    model_rationale=translation.rationale,
                    alternatives_considered=json.dumps(translation.alternatives),
                    confidence="high"
                    if translation.confidence >= 0.8
                    else "medium"
                    if translation.confidence >= 0.5
                    else "low",
                    created_by=f"ai-{model_name}",
                )
                logger.debug(f"Stored translation in database with ID {translation_id}")
            except Exception as e:
                logger.warning(f"Failed to store translation in database: {e}")

        logger.debug(
            f"Translated '{term}' -> '{translation.translation}' ({language}, {model_name})"
        )

    def _get_terms_to_translate(self) -> List[str]:
        """Get list of terms to translate.

        Returns:
            List of term strings
        """
        if self.config.terms is not None:
            # Use provided list
            return self.config.terms

        # Load from manifest
        manifest = load_term_manifest()
        terms = [t["term"] for t in manifest.get("terms", [])]

        if not terms:
            # Fallback: get all terms with context documents
            terms = self.context_loader.get_term_list()

        return terms


async def main_async():
    """Main entry point for async execution."""
    # Example usage
    config = PipelineConfig(
        models=["claude", "aya"],
        languages=["es", "ar", "fr"],  # Just 3 languages for testing
        terms=["def", "return", "print"],  # Just 3 terms for testing
        dry_run=True,  # Safe mode - no real API calls
    )

    pipeline = TranslationPipeline(config)
    stats = await pipeline.run()

    return stats


def main():
    """Main entry point for synchronous execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
