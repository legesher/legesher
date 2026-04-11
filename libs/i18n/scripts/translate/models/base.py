"""Base models and interfaces for AI translation pipeline.

This module defines the core data structures and abstract interfaces for
translation models used in CORE-394.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Translation:
    """Represents a single translation result from an AI model.

    Attributes:
        translation: The translated term (e.g., "definir" for "def" in Spanish)
        alternatives: Alternative translations considered
        rationale: Explanation of why this translation was chosen
        word_type: Linguistic classification (verb, noun, etc.)
        form: Grammatical form (infinitive, imperative, etc.)
        model_name: Name of the model that generated this translation
        timestamp: When this translation was generated
        cost: Cost in USD for this translation
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        confidence: Confidence score 0.0-1.0 (1.0 = highest)
    """

    translation: str
    alternatives: list[str] = field(default_factory=list)
    rationale: str = ""
    word_type: str = ""
    form: str = ""
    model_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "translation": self.translation,
            "alternatives": self.alternatives,
            "rationale": self.rationale,
            "word_type": self.word_type,
            "form": self.form,
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "cost": self.cost,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "confidence": self.confidence,
        }


@dataclass
class TranslationRequest:
    """Request to translate a Python term.

    Attributes:
        term: Python term to translate (e.g., "def", "return")
        target_language: Target language code (e.g., "es", "ar")
        context: Deep context document content
        linguistic_standards: Language-specific translation guidelines
    """

    term: str
    target_language: str
    context: str | None = None
    linguistic_standards: str | None = None


class TranslationModel(ABC):
    """Abstract base class for AI translation models.

    Subclasses must implement the translate() method to provide
    translations using their specific AI model (Claude, Aya, etc.).
    """

    @abstractmethod
    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term to the target language.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation object with result and metadata

        Raises:
            Exception: If translation fails
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of this model (e.g., 'claude-3.5-sonnet', 'aya23')."""
        pass

    @abstractmethod
    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate the cost in USD for this translation request.

        Args:
            request: Translation request to estimate

        Returns:
            Estimated cost in USD
        """
        pass
