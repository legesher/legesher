# Aya-101 Hugging Face Model Integration

This document explains how to use the Aya-101 model from Cohere via Hugging Face for translating Python
terms into **101 languages**.

## Overview

The `Aya101HuggingFaceModel` provides access to Cohere's Aya-101 massively multilingual model, which
supports **101 languages** compared to the Ollama-based Aya model's 23 languages.

### Comparison

| Feature               | Aya (Ollama)             | Aya-101 (Hugging Face)     |
| --------------------- | ------------------------ | -------------------------- |
| Languages             | 23                       | **101**                    |
| Model Size            | ~7B parameters           | **13B parameters**         |
| Setup                 | `ollama pull aya:latest` | Install transformers/torch |
| RAM Required          | ~8GB                     | **~16GB** recommended      |
| Disk Space            | ~10GB                    | **~20GB** (model weights)  |
| GPU                   | Optional                 | **Highly recommended**     |
| Cost                  | Free (local)             | Free (local)               |
| First Run             | Fast                     | Slow (downloads ~20GB)     |
| Inference Speed (CPU) | ~2-5s per translation    | ~5-10s per translation     |
| Inference Speed (GPU) | N/A                      | ~100-500ms per translation |

## Installation

### Step 1: Install ML Dependencies

The Aya-101 model requires PyTorch and Transformers libraries. These are optional dependencies to keep the core package lightweight.

```bash
# From the project root
cd libs/i18n

# Install with UV (recommended)
uv pip install -e ".[ml]"

# Or with pip
pip install -e ".[ml]"
```

This installs:

- `transformers>=4.30.0` - Hugging Face transformers library
- `torch>=2.0.0` - PyTorch (CPU version by default)
- `accelerate>=0.20.0` - For efficient model loading
- `sentencepiece>=0.1.99` - Required tokenizer

### Step 2: GPU Support (Optional but Recommended)

For **much faster** inference, install PyTorch with CUDA support:

```bash
# For CUDA 11.8 (check your CUDA version with `nvcc --version`)
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# For Apple Silicon (M1/M2/M3)
# MPS backend is automatically detected, no additional install needed
```

The model will automatically detect and use:

- **CUDA** if available (NVIDIA GPU)
- **MPS** if available (Apple Silicon)
- **CPU** as fallback

## Usage

### Running the Translation Pipeline

Use the `--models aya101-hf` flag to use the Aya-101 Hugging Face model:

```bash
cd libs/i18n

# Translate to specific languages
uv run python scripts/translate/run_pipeline.py \
  --models aya101-hf \
  --languages de ja ko hi bn \
  --verbose

# Translate specific terms only
uv run python scripts/translate/run_pipeline.py \
  --models aya101-hf \
  --languages de ja \
  --terms def return print class

# Dry run (test without loading model)
uv run python scripts/translate/run_pipeline.py \
  --models aya101-hf \
  --languages de ja \
  --dry-run

# Use both Ollama Aya and HF Aya-101 for comparison
uv run python scripts/translate/run_pipeline.py \
  --models aya aya101-hf \
  --languages es fr
```

### First Run Behavior

**Important:** The first time you run the pipeline with `aya101-hf`, it will:

1. Download ~20GB of model weights from Hugging Face
2. Cache them in `~/.cache/huggingface/hub/`
3. Load the model into memory (~16GB RAM)

This can take **10-30 minutes** depending on your internet speed. Subsequent runs will be much faster
as the model is cached locally.

### Environment Variables

You can customize the model behavior with environment variables:

```bash
# Use specific cache directory
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache

# Disable progress bars
export HF_HUB_DISABLE_PROGRESS_BARS=1

# Use offline mode (requires model already downloaded)
export HF_HUB_OFFLINE=1
```

## Supported Languages

The Aya-101 model supports **101 languages** using ISO 639-3 codes:

### Major Languages (High Developer Population)

- **ar** (Arabic), **zh** (Chinese), **en** (English), **fr** (French), **de** (German)
- **hi** (Hindi), **id** (Indonesian), **it** (Italian), **ja** (Japanese), **ko** (Korean)
- **pt** (Portuguese), **ru** (Russian), **es** (Spanish), **tr** (Turkish), **vi** (Vietnamese)

### Additional European Languages

- **nl** (Dutch), **pl** (Polish), **sv** (Swedish), **da** (Danish), **no** (Norwegian)
- **fi** (Finnish), **el** (Greek), **cs** (Czech), **hu** (Hungarian), **ro** (Romanian)
- **uk** (Ukrainian), **bg** (Bulgarian), **hr** (Croatian), **sk** (Slovak), **sl** (Slovenian)
- **et** (Estonian), **lv** (Latvian), **lt** (Lithuanian), **ga** (Irish), **mt** (Maltese)

### Asian & Pacific Languages

- **bn** (Bengali), **te** (Telugu), **mr** (Marathi), **ta** (Tamil), **gu** (Gujarati)
- **kn** (Kannada), **ml** (Malayalam), **pa** (Punjabi), **ur** (Urdu), **ne** (Nepali)
- **si** (Sinhala), **th** (Thai), **km** (Khmer), **lo** (Lao), **my** (Burmese)
- **tl** (Filipino), **jv** (Javanese), **su** (Sundanese), **ms** (Malay)

### African Languages

- **sw** (Swahili), **ha** (Hausa), **yo** (Yoruba), **ig** (Igbo), **zu** (Zulu)
- **xh** (Xhosa), **am** (Amharic), **so** (Somali), **af** (Afrikaans)

### Middle Eastern & Central Asian

- **fa** (Persian), **he** (Hebrew), **az** (Azerbaijani), **kk** (Kazakh), **uz** (Uzbek)
- **ky** (Kyrgyz), **tg** (Tajik), **ps** (Pashto), **ku** (Kurdish)

### And Many More

See the full list of 101 languages in the [Aya-101 model card](https://huggingface.co/CohereLabs/aya-101).

## Performance Tips

### 1. Use GPU

GPU inference is **50-100x faster** than CPU:

- CPU: ~5-10 seconds per translation
- GPU: ~100-500ms per translation

### 2. Batch Translations

The pipeline automatically batches translations for efficiency.

### 3. Pre-download Model

Download the model ahead of time to avoid delays:

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# This will download and cache the model
model = AutoModelForSeq2SeqLM.from_pretrained("CohereLabs/aya-101")
tokenizer = AutoTokenizer.from_pretrained("CohereLabs/aya-101")
```

### 4. Reduce Memory Usage

If you have limited RAM:

```python
# Load model in 8-bit precision (requires bitsandbytes)
pip install bitsandbytes

# Then modify aya101_hf_model.py to use:
model = AutoModelForSeq2SeqLM.from_pretrained(
    "CohereLabs/aya-101",
    load_in_8bit=True,  # Reduces memory from 16GB to 8GB
    device_map="auto",
)
```

## Troubleshooting

### ImportError: No module named 'transformers'

Install the ML dependencies:

```bash
uv pip install -e ".[ml]"
```

### OutOfMemoryError (OOM)

You need more RAM or a GPU:

- **CPU**: At least 16GB RAM required
- **GPU**: At least 8GB VRAM required (12GB recommended)

Solutions:

1. Use a smaller model (Ollama Aya with 23 languages)
2. Use 8-bit precision (see Performance Tips above)
3. Close other applications to free up RAM
4. Use Google Colab or cloud GPU

### Model Download Fails

If the download is interrupted:

```bash
# Clear the cache and retry
rm -rf ~/.cache/huggingface/hub/models--CohereForAI--aya-101
```

### Slow CPU Inference

This is expected. Solutions:

1. Use GPU (recommended)
2. Reduce number of translations
3. Use Ollama Aya instead (faster on CPU)

## Architecture

The `Aya101HuggingFaceModel` class follows the same interface as other translation models:

```python
class Aya101HuggingFaceModel(TranslationModel):
    async def translate(self, request: TranslationRequest) -> Translation
    def get_model_name(self) -> str
    def estimate_cost(self, request: TranslationRequest) -> float
```

It uses:

- **Lazy loading**: Model is only loaded when first translation is requested
- **Async inference**: Uses `asyncio.to_thread()` to avoid blocking
- **Retry logic**: Exponential backoff for transient errors
- **JSON parsing**: Multiple fallback strategies for robust parsing
- **Device auto-detection**: Automatically uses best available device

## Examples

### Translate to Rare Languages

```bash
# Translate to languages not supported by Ollama Aya
uv run python scripts/translate/run_pipeline.py \
  --models aya101-hf \
  --languages bn te ta kn ml gu \
  --terms def return print
```

### Compare Quality

```bash
# Use both models and compare results in database
uv run python scripts/translate/run_pipeline.py \
  --models aya aya101-hf \
  --languages es fr de
```

### Translation for African Languages

```bash
# Translate to African languages
uv run python scripts/translate/run_pipeline.py \
  --models aya101-hf \
  --languages sw ha yo ig zu xh am so
```

## References

- **Model Card**: <https://huggingface.co/CohereLabs/aya-101>
- **Research Paper**: [Aya: A Massively Multilingual Model](https://cohere.com/research/aya)
- **Transformers Docs**: <https://huggingface.co/docs/transformers>
- **PyTorch**: <https://pytorch.org/get-started/locally/>

## License

The Aya-101 model is released under Apache 2.0 license by Cohere For AI.
