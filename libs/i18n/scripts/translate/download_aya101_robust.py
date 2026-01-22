#!/usr/bin/env python3
"""Robust Aya-101 model downloader with retry logic and optimization.

This script handles the download of the Aya-101 model with:
- Automatic resume of partial downloads
- Retry logic for network failures
- Smart detection of already-downloaded files
- Progress tracking
"""

import sys
import time

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
except ImportError:
    print("ERROR: transformers or torch not installed")
    print("Run: uv pip install -e '.[ml]'")
    sys.exit(1)


def download_model_robust(
    model_name: str = "CohereLabs/aya-101",  # Using correct repository name
    cache_dir: str = None,
    max_retries: int = 5,
    retry_delay: float = 10.0,
):
    """Download Aya-101 model with robust error handling.

    Args:
        model_name: Hugging Face model identifier
        cache_dir: Optional cache directory
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
    """
    print("=" * 70)
    print("Robust Aya-101 Model Download")
    print("=" * 70)
    print(f"Model: {model_name}")
    print(f"Cache: {cache_dir or '~/.cache/huggingface/hub/'}")
    print(f"Max retries: {max_retries}")
    print()

    # Step 1: Try to load from cache first
    print("Step 1: Checking for cached model...")
    try:
        print("Attempting to load model from local cache (no download)...")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            local_files_only=True,  # Try cache first
        )
        print("✓ Model loaded successfully from cache!")
        print()
        print("=" * 70)
        print("SUCCESS: Model is ready to use!")
        print("=" * 70)
        return model
    except Exception as e:
        print(f"ℹ Model not in cache or incomplete: {e}")
        print("Proceeding with download...")
        print()

    # Step 2: Download tokenizer (small, usually succeeds)
    print("Step 2: Downloading tokenizer...")
    for attempt in range(max_retries):
        try:
            _ = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
            )
            print("✓ Tokenizer downloaded successfully")
            print()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                print(
                    f"✗ Tokenizer download failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                print(f"  Retrying in {wait_time:.0f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"✗ Tokenizer download failed after {max_retries} attempts")
                raise

    # Step 3: Download model with retries
    print("Step 3: Downloading model weights...")
    print("This will download ~20GB (may resume partial downloads)")
    print()

    for attempt in range(max_retries):
        try:
            print(f"Download attempt {attempt + 1}/{max_retries}...")
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                local_files_only=False,
                low_cpu_mem_usage=True,  # More efficient loading
                torch_dtype=torch.float16,  # Use FP16 to save memory
            )
            print()
            print("✓ Model downloaded successfully!")
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
            print("=" * 70)
            print("SUCCESS: Model download complete!")
            print(f"Model: {model_name}")
            print(f"Device: {device}")
            print(f"Cache: {cache_dir or '~/.cache/huggingface/hub/'}")
            print("=" * 70)
            print()
            print("You can now run the translation pipeline:")
            print(
                "  uv run python scripts/translate/run_pipeline.py --models aya101-hf --languages de ja ko"
            )
            print()
            return model

        except KeyboardInterrupt:
            print("\n\nDownload interrupted by user")
            raise
        except Exception as e:
            error_str = str(e)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                print(f"✗ Download failed (attempt {attempt + 1}/{max_retries})")
                print(f"  Error: {error_str[:200]}")
                print(f"  Retrying in {wait_time:.0f} seconds...")
                time.sleep(wait_time)
            else:
                print()
                print("=" * 70)
                print(f"ERROR: Download failed after {max_retries} attempts")
                print("=" * 70)
                print()
                print("Possible solutions:")
                print("1. Check your internet connection")
                print("2. Try again later (Hugging Face servers may be busy)")
                print("3. Clear cache and retry:")
                print("   rm -rf ~/.cache/huggingface/hub/models--CohereLabs--aya-101")
                print("4. Use a VPN if network restrictions exist")
                print(
                    "5. Download manually from: https://huggingface.co/CohereLabs/aya-101"
                )
                print()
                raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Robust Aya-101 model downloader with retry logic"
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
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Maximum number of retry attempts (default: 5)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=10.0,
        help="Initial retry delay in seconds (default: 10.0)",
    )

    args = parser.parse_args()

    try:
        download_model_robust(
            model_name=args.model,
            cache_dir=args.cache_dir,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
        )
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
