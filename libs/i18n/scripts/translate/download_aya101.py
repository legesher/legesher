#!/usr/bin/env python3
"""Pre-download Aya-101 model from Hugging Face.

This script downloads the Aya-101 model to avoid issues during pipeline execution.
"""

import sys

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
except ImportError:
    print("ERROR: transformers or torch not installed")
    print("Run: uv pip install -e '.[ml]'")
    sys.exit(1)


def download_model(model_name: str = "CohereLabs/aya-101", cache_dir: str = None):
    """Download Aya-101 model and tokenizer.

    Args:
        model_name: Hugging Face model identifier
        cache_dir: Optional cache directory (default: ~/.cache/huggingface)
    """
    print(f"Downloading Aya-101 model: {model_name}")
    print("This will download ~20GB of model weights...")
    print()

    # Download tokenizer
    print("Step 1/2: Downloading tokenizer...")
    _ = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        resume_download=True,  # Resume if interrupted
    )
    print("✓ Tokenizer downloaded successfully")
    print()

    # Download model
    print("Step 2/2: Downloading model weights (~20GB)...")
    print("This may take 10-30 minutes depending on your internet speed...")
    _ = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        resume_download=True,  # Resume if interrupted
        local_files_only=False,  # Force download from HF
    )
    print("✓ Model downloaded successfully")
    print()

    # Check device availability
    if torch.cuda.is_available():
        device = "cuda"
        print("✓ CUDA detected - GPU acceleration available")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
        print("✓ Apple Silicon detected - MPS acceleration available")
    else:
        device = "cpu"
        print("ℹ Using CPU (no GPU detected)")

    print()
    print("=" * 60)
    print("Model download complete!")
    print(f"Model: {model_name}")
    print(f"Device: {device}")
    print(f"Cache: {cache_dir or '~/.cache/huggingface/hub/'}")
    print("=" * 60)
    print()
    print("You can now run the translation pipeline:")
    print(
        "  uv run python scripts/translate/run_pipeline.py --models aya101-hf --languages <lang>"
    )
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-download Aya-101 model from Hugging Face"
    )
    parser.add_argument(
        "--model",
        default="CohereLabs/aya-101",
        help="Hugging Face model identifier (default: CohereLabs/aya-101)",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Cache directory for model weights (default: ~/.cache/huggingface)",
    )

    args = parser.parse_args()

    try:
        download_model(model_name=args.model, cache_dir=args.cache_dir)
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
