"""AI translation models for CORE-394 pipeline."""

from .base import Translation, TranslationModel, TranslationRequest

__all__ = [
    "Translation",
    "TranslationModel",
    "TranslationRequest",
]

# Optional: Aya-101 HuggingFace model (local, requires transformers/torch)
try:
    from .aya101_hf_model import Aya101HuggingFaceModel  # noqa: F401

    __all__.append("Aya101HuggingFaceModel")
except ImportError:
    pass  # transformers/torch not installed - model unavailable

# Optional: Aya-101 via HF Inference API (cloud-based, no local RAM needed)
try:
    from .aya_inference_api_model import AyaInferenceAPIModel  # noqa: F401

    __all__.append("AyaInferenceAPIModel")
except ImportError:
    pass  # huggingface_hub not installed - model unavailable
