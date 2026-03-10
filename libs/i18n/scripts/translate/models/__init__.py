"""AI translation models for CORE-394 pipeline."""

from .base import Translation, TranslationModel, TranslationRequest
from .hf_profiles import HF_PROFILES, HFModelProfile, get_profile, list_profiles

__all__ = [
    "Translation",
    "TranslationModel",
    "TranslationRequest",
    "HFModelProfile",
    "HF_PROFILES",
    "get_profile",
    "list_profiles",
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

# Generic HuggingFace models — always importable.
# Heavy dependencies (transformers, torch, huggingface_hub) are deferred to runtime.
# Use HuggingFaceModel.check_dependencies() / HuggingFaceAPIModel.check_dependencies()
# to verify availability before instantiation.
from .huggingface_model import HuggingFaceModel  # noqa: F401
from .huggingface_api_model import HuggingFaceAPIModel  # noqa: F401

__all__.extend(["HuggingFaceModel", "HuggingFaceAPIModel"])
