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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)

from legesher_i18n.db import TranslationDatabase

from .context_loader import ContextLoader, LinguisticStandardsLoader
from .term_classifier import get_all_terms_by_category, classify_term
from .models.base import TranslationRequest, TranslationModel
from .models.claude_model import ClaudeModel
from .models.aya_model import AyaModel
from .models.hf_profiles import get_profile
from .yaml_exporter import YAMLExporter
from .validators import TranslationValidator

# Optional: Aya-101 Hugging Face model (requires transformers/torch)
try:
    from .models.aya101_hf_model import Aya101HuggingFaceModel

    HAS_AYA101_HF = True
except ImportError:
    HAS_AYA101_HF = False

# Optional: Aya-101 via Hugging Face Inference API (cloud-based, no local RAM needed)
try:
    from .models.aya_inference_api_model import AyaInferenceAPIModel

    HAS_AYA_API = True
except ImportError:
    HAS_AYA_API = False

# Optional: Ollama for local LLM inference (requires Ollama installed)
try:
    from .models.ollama_model import OllamaModel

    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

# Generic HuggingFace models — always importable (they defer heavy deps to runtime)
from .models.huggingface_model import HuggingFaceModel
from .models.huggingface_api_model import HuggingFaceAPIModel


logger = logging.getLogger(__name__)
console = Console()


def default_languages() -> list[str]:
    """Default 24 target languages from CORE-394."""
    return [
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
        target: Programming-language target (CORE-1371). ``"python"`` keeps
            the historical behavior exactly (term_classifier inventory,
            python term rows). Any other target sources its inventory from
            the DB ``terms`` table (seeded, e.g. ``scripts/seed_js_terms.py``)
            and seasons prompts via the target's spec profile (CORE-1608).
    """

    models: list[str] = field(default_factory=lambda: ["claude", "aya"])
    languages: list[str] = field(default_factory=default_languages)
    terms: list[str] | None = None  # If None, use all from manifest
    target: str = "python"  # Programming-language target (CORE-1371)
    dry_run: bool = False
    max_budget: float = 100.0  # Stop at $100 (safety margin)
    context_dir: Path | None = None
    standards_file: Path | None = None
    output_db: Path | None = None
    skip_existing: bool = True
    ollama_model: str = "aya"  # Ollama model name (aya, command-r, qwen2.5, etc.)
    hf_profile: str | None = None  # HuggingFace model profile name
    tiny_aya_variant: str = "earth"  # Tiny Aya variant (earth, fire, water, global)


@dataclass
class PipelineStats:
    """Statistics for pipeline execution.

    Tracks progress, costs, and success rates.
    """

    total_translations: int = 0
    successful_translations: int = 0
    failed_translations: int = 0
    skipped_translations: int = 0
    validation_errors: int = 0
    validation_warnings: int = 0
    total_cost: float = 0.0
    cost_by_model: dict[str, float] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None

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

    def record_skip(self):
        """Record a skipped translation (already exists)."""
        self.skipped_translations += 1

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
        console.print(f"  ⏭ Skipped: {self.skipped_translations}")
        console.print(f"  ✗ Failed: {self.failed_translations}")

        if self.validation_errors > 0 or self.validation_warnings > 0:
            console.print("\nValidation:")
            console.print(f"  ⚠ Errors: {self.validation_errors}")
            console.print(f"  ⚠ Warnings: {self.validation_warnings}")

        console.print(f"\nTotal cost: [bold]${self.total_cost:.2f}[/bold]")

        for model, cost in self.cost_by_model.items():
            console.print(f"  {model}: ${cost:.2f}")

        duration = self.get_duration()
        console.print(f"\nDuration: {duration:.1f}s ({duration / 60:.1f} minutes)")


def resolve_read_category(db: TranslationDatabase, term: str) -> str | None:
    """Pick the category the skip-existing read must query the term with.

    The read has to land on the row ``_translate_one`` writes to, or the
    skip check consults one row while the write files under another and
    the term is re-translated (and re-billed) every run — CORE-1400.

    The write calls ``get_or_create_term(category=classify_term(term))``,
    which resolves in three ways, so the read mirrors all three:

    * a row carries the classified category — both sides pick that row;
    * the name has exactly one row whose category differs (``classmethod``,
      ``property``, ``staticmethod`` and ``super`` are stored
      ``builtin_func`` but classify as ``builtin_type``) — the write reuses
      that single row, so the read drops the category and does the same;
    * the name has several rows and none carries the classified category —
      the write raises, so the read stays strict rather than silently
      resolving to the lowest id. Empty set on the shipped database; the
      warning marks it if a future row split creates one.

    Args:
        db: Translation database instance
        term: Python term about to be translated

    Returns:
        The category to pass to the read, or ``None`` to read the term's
        only row whatever its stored category
    """
    category = classify_term(term, python_version="3.13")
    if db.get_term_by_name(term, "python", category=category) is not None:
        return category

    # No row carries the classified category. Count the name's rows to tell
    # the reusable single-row case from the ambiguous one. (A public
    # ``get_terms(name=...)`` filter would make this a lookup instead of a
    # scan; ``_get_terms_by_name`` is private, so filter the public list.)
    rows = [
        row
        for row in db.get_terms(programming_language="python")
        if row["name"] == term
    ]
    if len(rows) == 1:
        return None
    if len(rows) > 1:
        logger.warning(
            f"Term '{term}' has {len(rows)} rows "
            f"({', '.join(str(row['category']) for row in rows)}) and none is "
            f"'{category}': the skip-existing read finds nothing and the write "
            f"will raise. Add the missing row or fix the stored category "
            f"(CORE-1400)."
        )
    return category


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
            db_path=str(config.output_db) if config.output_db else None
        )

        # Initialize YAML exporter
        self.yaml_exporter = YAMLExporter(db=self.db)

        # Initialize validator
        self.validator = TranslationValidator()

        # Initialize models
        self.models: dict[str, TranslationModel] = {}
        if "claude" in config.models:
            self.models["claude"] = ClaudeModel(
                dry_run=config.dry_run, target=config.target
            )
        if "aya" in config.models:
            self.models["aya"] = AyaModel(dry_run=config.dry_run)
        if "aya101-hf" in config.models:
            if not HAS_AYA101_HF:
                raise ImportError(
                    "Aya-101 HuggingFace model requires transformers and torch. "
                    "Install with: uv pip install 'legesher-i18n[ml]'"
                )
            self.models["aya101-hf"] = Aya101HuggingFaceModel(
                dry_run=config.dry_run,
                device="cpu",  # Force CPU to avoid MPS memory issues
            )
        if "aya-api" in config.models:
            if not HAS_AYA_API:
                raise ImportError(
                    "Aya Inference API model requires huggingface_hub. "
                    "Install with: pip install huggingface_hub"
                )
            self.models["aya-api"] = AyaInferenceAPIModel(
                dry_run=config.dry_run,
            )
        if "ollama" in config.models:
            if not HAS_OLLAMA:
                raise ImportError(
                    "Ollama model requires httpx. Install with: pip install httpx"
                )
            self.models["ollama"] = OllamaModel(
                model=config.ollama_model,
                dry_run=config.dry_run,
            )

        # Generic HuggingFace local model (profile-based)
        wants_hf = "hf" in config.models
        wants_tiny_aya = "tiny-aya" in config.models
        if wants_hf or wants_tiny_aya:
            if not config.dry_run:
                HuggingFaceModel.check_dependencies()
            # Explicit hf selection: always requires --hf-profile
            if wants_hf:
                if not config.hf_profile:
                    raise ValueError(
                        "--models hf requires --hf-profile to specify which model "
                        "to use. Example: --models hf --hf-profile tiny-aya-earth"
                    )
                hf_profile = get_profile(config.hf_profile)
                self.models["hf"] = HuggingFaceModel(
                    profile=hf_profile,
                    dry_run=config.dry_run,
                )
            # Tiny Aya: default to tiny-aya-{variant} if no explicit profile
            if wants_tiny_aya:
                if config.hf_profile:
                    tiny_aya_profile = get_profile(config.hf_profile)
                else:
                    profile_name = f"tiny-aya-{config.tiny_aya_variant}"
                    tiny_aya_profile = get_profile(profile_name)
                self.models["tiny-aya"] = HuggingFaceModel(
                    profile=tiny_aya_profile,
                    dry_run=config.dry_run,
                )

        # Generic HuggingFace API model (profile-based)
        wants_hf_api = "hf-api" in config.models
        wants_tiny_aya_api = "tiny-aya-api" in config.models
        if wants_hf_api or wants_tiny_aya_api:
            if not config.dry_run:
                HuggingFaceAPIModel.check_dependencies()
            # Explicit hf-api selection: always requires --hf-profile
            if wants_hf_api:
                if not config.hf_profile:
                    raise ValueError(
                        "--models hf-api requires --hf-profile to specify which "
                        "model to use. "
                        "Example: --models hf-api --hf-profile tiny-aya-earth"
                    )
                hf_api_profile = get_profile(config.hf_profile)
                self.models["hf-api"] = HuggingFaceAPIModel(
                    profile=hf_api_profile,
                    dry_run=config.dry_run,
                )
            # Tiny Aya API: default to tiny-aya-{variant} if no explicit profile
            if wants_tiny_aya_api:
                if config.hf_profile:
                    tiny_aya_api_profile = get_profile(config.hf_profile)
                else:
                    profile_name = f"tiny-aya-{config.tiny_aya_variant}"
                    tiny_aya_api_profile = get_profile(profile_name)
                self.models["tiny-aya-api"] = HuggingFaceAPIModel(
                    profile=tiny_aya_api_profile,
                    dry_run=config.dry_run,
                )

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
                # CORE-1400: the slot a term lives in does not vary by
                # language or model, so resolve it once per term. Python-only:
                # the resolver rides classify_term and python rows. Non-python
                # targets carry exactly one seeded row per term (the seeder
                # enforces it), so the uncategorised read already lands on the
                # row the write uses (CORE-1371).
                read_category = (
                    resolve_read_category(self.db, term)
                    if self.config.skip_existing and self.config.target == "python"
                    else None
                )

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

                        # Check if translation already exists (skip_existing).
                        # Scoped to the run's target (CORE-1371): without it,
                        # a javascript run would skip every keyword whose
                        # spelling Python shares (in/for/if/while/break/
                        # continue/return) because their PYTHON translations
                        # exist.
                        if self.config.skip_existing:
                            # CORE-1400: read the same slot _translate_one
                            # writes to. 'type' holds two term rows (the
                            # 3.10 builtin_type and the PEP 695 keyword);
                            # an uncategorised read resolves to the lowest
                            # id, so the check consulted one row while the
                            # write filed under the other and could never
                            # converge — re-billing the term every run.
                            existing = self.db.get_translations_for_term(
                                term_name=term,
                                language_code=language,
                                programming_language=self.config.target,
                                category=read_category,
                            )
                            # Filter to check if this specific model already contributed
                            model_existing = [
                                t for t in existing if t["source"] == model_name
                            ]
                            if model_existing:
                                logger.debug(
                                    f"Skipping '{term}' ({language}, {model_name}) - already exists"
                                )
                                self.stats.record_skip()
                                progress.advance(task)
                                continue

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

        # Validate translation
        term_type = classify_term(term, python_version="3.13")
        validation_result = self.validator.validate(
            term=term,
            translation=translation.translation,
            language_code=language,
            term_type=term_type,
        )

        # Record validation stats
        if not validation_result.is_valid:
            self.stats.validation_errors += len(validation_result.errors)
            logger.warning(
                f"Validation failed for '{term}' -> '{translation.translation}': {validation_result.errors}"
            )
        if validation_result.warnings:
            self.stats.validation_warnings += len(validation_result.warnings)
            logger.info(
                f"Validation warnings for '{term}' -> '{translation.translation}': {validation_result.warnings}"
            )

        # Record stats
        self.stats.record_success(model_name, translation.cost)

        # Store in database (CORE-399 integration)
        if not self.config.dry_run:
            try:
                # Get or create the term in the terms table
                if self.config.target == "python":
                    term_type = classify_term(term, python_version="3.13")
                    term_id = self.db.get_or_create_term(
                        name=term,
                        programming_language="python",
                        category=term_type,
                    )
                else:
                    # Non-python targets: the seeded row carries the
                    # category, so generation never guesses one. Fail loud
                    # rather than invent a term row (CORE-1371).
                    existing = self.db.get_term_by_name(term, self.config.target)
                    if existing is None:
                        raise ValueError(
                            f"term '{term}' is not seeded for target "
                            f"'{self.config.target}' — run the target's seeder first"
                        )
                    term_id = existing["id"]

                translation_id = self.db.add_translation(
                    term_id=term_id,
                    language_code=language,
                    translation=translation.translation,
                    source=model_name,
                    word_type=translation.word_type,
                    word_form=translation.form,
                    model_rationale=translation.rationale,
                    confidence=(
                        "high"
                        if translation.confidence >= 0.8
                        else "medium"
                        if translation.confidence >= 0.5
                        else "low"
                    ),
                    created_by=f"ai-{model_name}",
                )
                logger.debug(f"Stored translation in database with ID {translation_id}")
            except Exception as e:
                logger.warning(f"Failed to store translation in database: {e}")

        logger.debug(
            f"Translated '{term}' -> '{translation.translation}' ({language}, {model_name})"
        )

    def _get_terms_to_translate(self) -> list[str]:
        """Get list of terms to translate.

        Uses term_classifier as the source of truth for all Python terms.
        This includes keywords, built-in functions, built-in types, exceptions,
        special constants, and helper terms.

        Returns:
            List of term strings
        """
        if self.config.terms is not None:
            # Use provided list
            return self.config.terms

        if self.config.target != "python":
            # Non-python targets are DB-inventoried (CORE-1371): the seeded
            # terms table is the target-neutral source of truth, categories
            # included. term_classifier below is the python-profile legacy
            # path; migrating python onto the same road rides CORE-1503.
            rows = self.db.get_terms(programming_language=self.config.target)
            terms = [row["name"] for row in rows]
            if not terms:
                raise ValueError(
                    f"No terms seeded for target '{self.config.target}' — "
                    "run scripts/seed_js_terms.py (or the target's seeder) first"
                )
            logger.info(
                f"Loaded {len(terms)} terms from the DB inventory "
                f"(target={self.config.target})"
            )
            return terms

        # Get all terms from term_classifier (source of truth)
        # This includes keywords, builtins, exceptions, etc.
        terms_by_category = get_all_terms_by_category(python_version="3.13")

        # Flatten all categories into a single list (excluding helper terms)
        terms = []
        for category, category_terms in terms_by_category.items():
            if category != "helper":  # Skip helper terms like README, underscore
                terms.extend(category_terms)

        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        logger.info(f"Loaded {len(unique_terms)} terms from term_classifier")
        return unique_terms


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
