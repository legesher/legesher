# AI Translation Cost Analysis for Legesher Language Packs

**Date**: 2025-10-28
**Scope**: Python keywords + builtins across 48 dialects
**Purpose**: Compare multiple LLM models for community review

---

## Translation Volume Summary

Based on extraction from `legesher/legesher-translations`:

- **Total Languages**: 48 dialects
- **Python Keywords**: ~35 per language
- **Built-in Functions**: ~70 per language
- **Total Items per Language**: ~105 items
- **Total Translation Requests**: 48 languages × 105 items = **5,040 translations**

### Unique Languages Extracted

Arabic (ar), Bengali (bn), Dutch (nl), Finnish (fi), French (fr), Gaelic (ga), Greek (el), Gujarati (gu), Hebrew (he), Hindi (hi), Indonesian (id), Malayalam (ml), Nepali (ne), Polish (pl), Portuguese (pt), Russian (ru), Spanish (es), Swahili (sw), Tagalog (tl), Telugu (te), Ukrainian (uk), Urdu (ur), Welsh (cy), Xhosa (xh), and 24 more.

---

## Token Estimation

### Per Translation

**Prompt Template** (example):

```
Translate the following Python keyword to {LANGUAGE}:

Keyword: "def"
Context: Used to define a function in Python
Usage: def function_name(parameters):

Provide ONLY the translated keyword, considering:
1. Programming/technical context
2. Cultural appropriateness
3. Brevity (single word preferred)
4. Natural feel for native speakers

Translation:
```

**Token breakdown**:

- Prompt: ~100 tokens
- Response: ~10 tokens (usually a single word)
- **Total per translation**: ~110 tokens

### Total Volume

- **Total tokens (input)**: 5,040 translations × 100 tokens = **504,000 tokens**
- **Total tokens (output)**: 5,040 translations × 10 tokens = **50,400 tokens**
- **Combined total**: **554,400 tokens**

---

## Cost Analysis by Model

### 1. **Claude 3.5 Sonnet** (Anthropic)

**Best for**: High-quality cultural nuance, multilingual accuracy

- **Input**: $3.00 per million tokens
- **Output**: $15.00 per million tokens
- **Calculation**:
  - Input cost: 504,000 tokens × ($3.00 / 1M) = **$1.51**
  - Output cost: 50,400 tokens × ($15.00 / 1M) = **$0.76**
  - **Total: $2.27**

**Pros**:

- Excellent multilingual performance
- Cultural nuance awareness
- Longer context window (200k tokens)
- Can do batch processing

**Cons**:

- Higher output cost
- Slower than GPT-3.5

---

### 2. **GPT-4o** (OpenAI)

**Best for**: Balance of quality and speed

- **Input**: $2.50 per million tokens
- **Output**: $10.00 per million tokens
- **Calculation**:
  - Input cost: 504,000 tokens × ($2.50 / 1M) = **$1.26**
  - Output cost: 50,400 tokens × ($10.00 / 1M) = **$0.50**
  - **Total: $1.76**

**Pros**:

- Good multilingual support
- Fast inference
- JSON mode for structured output
- Batch API available (50% discount)

**Cons**:

- Sometimes less culturally aware than Claude
- May produce verbose outputs

---

### 3. **GPT-4o-mini** (OpenAI)

**Best for**: Cost-effective baseline

- **Input**: $0.15 per million tokens
- **Output**: $0.60 per million tokens
- **Calculation**:
  - Input cost: 504,000 tokens × ($0.15 / 1M) = **$0.08**
  - Output cost: 50,400 tokens × ($0.60 / 1M) = **$0.03**
  - **Total: $0.11**

**Pros**:

- Extremely cost-effective
- Very fast
- Good for simpler translation tasks
- Batch API (50% discount): **$0.055 total**

**Cons**:

- Lower quality for rare languages
- Less cultural awareness
- May need more prompting

---

### 4. **Claude 3 Haiku** (Anthropic)

**Best for**: Fast, cheap Anthropic option

- **Input**: $0.25 per million tokens
- **Output**: $1.25 per million tokens
- **Calculation**:
  - Input cost: 504,000 tokens × ($0.25 / 1M) = **$0.13**
  - Output cost: 50,400 tokens × ($1.25 / 1M) = **$0.06**
  - **Total: $0.19**

**Pros**:

- Fast and cheap
- Still maintains Anthropic's multilingual quality
- Good for batch processing

**Cons**:

- Lower quality than Sonnet
- Shorter context window (200k)

---

### 5. **Gemini 1.5 Flash** (Google)

**Best for**: Google's multilingual expertise

- **Input**: $0.075 per million tokens
- **Output**: $0.30 per million tokens
- **Calculation**:
  - Input cost: 504,000 tokens × ($0.075 / 1M) = **$0.04**
  - Output cost: 50,400 tokens × ($0.30 / 1M) = **$0.02**
  - **Total: $0.06**

**Pros**:

- Extremely cheap
- Google's translation expertise
- Fast inference
- Good multilingual support (built on Google Translate technology)

**Cons**:

- Less established for programming contexts
- Variable quality across languages

---

## Cost Comparison Summary

| Model | Provider | Input Cost | Output Cost | **Total Cost** | Speed | Quality |
|-------|----------|------------|-------------|----------------|-------|---------|
| Claude 3.5 Sonnet | Anthropic | $1.51 | $0.76 | **$2.27** | Medium | ⭐⭐⭐⭐⭐ |
| GPT-4o | OpenAI | $1.26 | $0.50 | **$1.76** | Fast | ⭐⭐⭐⭐ |
| GPT-4o (Batch) | OpenAI | $0.63 | $0.25 | **$0.88** | Slow | ⭐⭐⭐⭐ |
| GPT-4o-mini | OpenAI | $0.08 | $0.03 | **$0.11** | Very Fast | ⭐⭐⭐ |
| GPT-4o-mini (Batch) | OpenAI | $0.04 | $0.015 | **$0.055** | Very Slow | ⭐⭐⭐ |
| Claude 3 Haiku | Anthropic | $0.13 | $0.06 | **$0.19** | Fast | ⭐⭐⭐⭐ |
| Gemini 1.5 Flash | Google | $0.04 | $0.02 | **$0.06** | Very Fast | ⭐⭐⭐ |

---

## Local/Open-Source Models Analysis

### Option: **Ollama + Open Models** (Free!)

**Models to consider**:

1. **Llama 3.1 70B** (Meta)
2. **Mistral Large 2** (24B)
3. **Qwen 2.5 72B** (Alibaba)
4. **Aya 23** (Cohere - specifically trained for multilingual)

**Cost**:

- **API/Inference**: $0 (FREE!)
- **Hardware**: Depends on what you have

**Hardware Requirements**:

| Model | Size | VRAM Needed | Speed (on M-series Mac) |
|-------|------|-------------|------------------------|
| Llama 3.1 8B | ~8GB | 8GB | Fast (~10 tok/s) |
| Llama 3.1 70B (quantized) | ~40GB | 48GB+ | Slow (~2 tok/s) |
| Mistral Large 2 | ~24GB | 32GB | Medium (~5 tok/s) |
| Qwen 2.5 32B | ~32GB | 40GB | Medium (~4 tok/s) |
| Aya 23 8B | ~8GB | 8GB | Fast (~10 tok/s) |

### Your Options with Local Models

#### If You Have: Apple Silicon (M1/M2/M3 Max/Ultra)

**64GB+ RAM**:

- ✅ Can run Llama 3.1 70B quantized
- ✅ Can run Qwen 2.5 72B quantized
- **Speed**: ~2-5 tokens/second
- **Time for 5,040 translations**: ~3-5 hours
- **Cost**: $0

**32-64GB RAM**:

- ✅ Can run Mistral Large 2 (24B)
- ✅ Can run Qwen 2.5 32B
- **Speed**: ~5-8 tokens/second
- **Time**: ~2-3 hours
- **Cost**: $0

**16-32GB RAM**:

- ✅ Can run Llama 3.1 8B
- ✅ Can run Aya 23 8B
- **Speed**: ~10-20 tokens/second
- **Time**: ~1-2 hours
- **Cost**: $0

#### If You Have: NVIDIA GPU

**RTX 4090 (24GB VRAM)**:

- ✅ Llama 3.1 70B (quantized)
- ✅ Qwen 2.5 32B
- **Speed**: Very fast (~20-30 tok/s for smaller models)
- **Time**: 30min - 2 hours
- **Cost**: Electricity (~$0.50 for 2 hours)

**RTX 3090/4080 (16GB)**:

- ✅ Llama 3.1 8B
- ✅ Mistral 7B
- ✅ Aya 23 8B
- **Cost**: $0 (electricity negligible)

### Pros of Local Models

#### 1. **Free** (after initial setup)

- No API costs
- Unlimited generations
- Can iterate/experiment without worrying about budget

#### 2. **Privacy**

- Translation data never leaves your machine
- Good for sensitive projects
- No concerns about data retention policies

#### 3. **Customization**

- Can fine-tune models on community translations
- Can adjust temperature/sampling for better results
- Full control over prompts

#### 4. **No Rate Limits**

- Process as fast as your hardware allows
- No waiting for API quotas
- Can run 24/7

#### 5. **Educational**

- Learn about LLM deployment
- Understand model behavior
- Experiment with different models

### Cons of Local Models

#### 1. **Quality (Usually Lower)**

- **Multilingual Gap**: Open models generally lag GPT-4/Claude in rare languages
- **Cultural Nuance**: Less training on cultural programming contexts
- **Consistency**: More variable outputs across languages

**Quality Comparison** (rough estimate):

- Claude 3.5 Sonnet: ⭐⭐⭐⭐⭐ (95% good translations)
- GPT-4o: ⭐⭐⭐⭐ (90% good)
- Llama 3.1 70B: ⭐⭐⭐ (75-80% good)
- Mistral Large 2: ⭐⭐⭐ (70-75%)
- Llama 3.1 8B: ⭐⭐ (60-70%)
- **Exception**: Aya 23 trained specifically for multilingual, might match GPT-4o for some languages

#### 2. **Setup Complexity**

- Need to install Ollama
- Download large model files (8-70GB)
- Configure hardware acceleration
- Debug if things break

#### 3. **Speed (Can Be Slow)**

- **5,040 translations** could take hours
- Depends heavily on hardware
- No parallel processing (one translation at a time)

#### 4. **Hardware Requirements**

- Need decent RAM/VRAM
- Storage space for models (8-100GB per model)
- Possible fan noise/heat

#### 5. **No Support**

- If it doesn't work, you troubleshoot
- No guaranteed uptime
- Updates might break things

### Best Local Model: **Aya 23 8B**

**Why**: Specifically optimized for multilingual tasks by Cohere

- Trained on 23 languages (including many of ours!)
- Small enough to run on modest hardware (8GB)
- Designed for translation/multilingual understanding
- Free and open-source

**Setup**:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull Aya model
ollama pull aya:8b

# Test translation
ollama run aya:8b "Translate 'def' to Spanish in programming context: "
```

**Expected Performance**:

- Speed: ~10-15 tokens/sec on M2 Mac
- Time for 5,040 translations: ~90 minutes
- Quality: ⭐⭐⭐½ (probably 75-85% good, especially for common languages)

---

## Hybrid Strategy: Local + Cloud

**Best of Both Worlds**: **$1-2 total**

1. **Run Aya 23 8B locally** for ALL languages (FREE!)
   - Takes 1-2 hours
   - Establishes baseline

2. **Use Claude 3.5 Sonnet** for languages where Aya struggles (10-15 languages)
   - Re-run challenging languages (Arabic, Hebrew, rare languages)
   - Cost: ~$0.70
   - Fills quality gaps

3. **Compare**: Aya vs Claude for those 15 languages
   - See where local model fails
   - Learn which languages need premium models
   - Research value!

**Total Cost**: <$1.00
**Total Time**: 2-3 hours
**Result**: Free baseline + premium fill-in for hard cases

---

## Local vs Cloud Decision Matrix

| Factor | Local (Aya 23 8B) | Cloud (Claude Sonnet) | Winner |
|--------|-------------------|----------------------|--------|
| **Cost** | $0 | $2.27 | 🏆 Local |
| **Quality** | ⭐⭐⭐½ | ⭐⭐⭐⭐⭐ | 🏆 Cloud |
| **Speed** | 1-2 hours | 5-10 minutes | 🏆 Cloud |
| **Privacy** | 100% private | Sent to API | 🏆 Local |
| **Setup** | 30min-1hr | 2 minutes | 🏆 Cloud |
| **Learning** | High | None | 🏆 Local |
| **Consistency** | Variable | Very consistent | 🏆 Cloud |
| **Rare Languages** | Struggles | Excellent | 🏆 Cloud |

---

## My Recommendation for Your Use Case

### **Hybrid Approach**: **$1-2**

1. **Run Aya 23 8B locally** (FREE, 1-2 hours)
   - Get baseline for all 48 languages
   - Learn which languages it handles well
   - Zero cost, full privacy

2. **Review Aya's output** (30 minutes)
   - Identify problematic translations
   - Flag unclear/wrong translations
   - Probably 10-15 languages need improvement

3. **Re-run with Claude Sonnet** (15 languages, ~$0.70)
   - Focus on languages where Aya struggled
   - Get premium quality where it matters
   - Keep Aya results for comparison

4. **Compare and Document** (1 hour)
   - Create comparison report
   - "When is local good enough?"
   - "Which languages need premium models?"
   - Publish findings!

**Benefits**:

- 💰 Saves ~$1.50 vs all-Claude
- 🔬 Research value (local vs cloud comparison)
- 🎓 Learning experience
- 📊 Data for future decisions
- 🏆 Best quality where it matters

**Drawbacks**:

- Takes 3-4 hours total vs 10 minutes
- Need to set up Ollama
- More complex workflow

---

## Recommended Multi-Model Strategy

### Option A: Quality Tier + Budget Tier (Recommended)

**Total Cost: ~$2.50**

1. **Claude 3.5 Sonnet** for RTL languages + rare dialects (~20 languages)
   - Arabic, Hebrew, Urdu, Bengali, Hindi, Gujarati, Malayalam, Telugu, Nepali, etc.
   - Cost: ~$1.00

2. **GPT-4o-mini (Batch)** for common European/Latin languages (~28 languages)
   - Spanish, French, Portuguese, Italian, German, Dutch, Polish, Russian, etc.
   - Cost: ~$0.03

**Rationale**: Use premium model for languages where cultural nuance matters most, cheap model for well-resourced European languages.

---

### Option B: Three-Tier Approach

**Total Cost: ~$3.50**

1. **Claude 3.5 Sonnet** - RTL & South Asian (15 langs) - **$0.70**
2. **GPT-4o** - European languages (20 langs) - **$0.73**
3. **Gemini 1.5 Flash** - Others (13 langs) - **$0.02**

**Rationale**: Match model strengths to language families.

---

### Option C: All Premium (Gold Standard)

**Total Cost: ~$2.27**

Use **Claude 3.5 Sonnet** for all 48 languages for consistency and maximum quality.

**Rationale**: Best quality, enables direct comparison, cost still very low (<$3 total).

---

## Comparison Value Analysis

### For Community Review

If you want the community to compare:

- **AI Model A vs AI Model B**: Run 2 models = 2× cost
- **AI Model A vs B vs C**: Run 3 models = 3× cost
- **All 5 models**: 5× cost

**Examples**:

- **Compare Claude Sonnet vs GPT-4o**: $2.27 + $1.76 = **$4.03 total**
- **Compare all models**: $2.27 + $1.76 + $0.11 + $0.19 + $0.06 = **$4.39 total**

**Value**: For < $5, you get comprehensive comparison across top models for ALL 48 languages.

---

## Batch Processing Savings

OpenAI's Batch API offers **50% discount**:

- GPT-4o: $1.76 → **$0.88**
- GPT-4o-mini: $0.11 → **$0.055**

**Trade-off**: 24-hour processing time vs real-time
**Best for**: Non-urgent bulk translation generation

---

## Hidden Costs to Consider

### 1. Error Handling & Retries

- Estimate: +10-20% for failed requests
- Budget: Add $0.50 safety margin

### 2. Prompt Engineering Iteration

- Testing prompts on small sample (100 translations)
- Cost: ~$0.05-0.20 per test iteration
- Budget: 5-10 iterations = $0.50-2.00

### 3. Multi-Language Validation

- Having AI generate + explain translation reasoning
- Increases output tokens 10x
- Example: Claude Sonnet with explanations: $2.27 → **$9.00**

---

## Final Recommendations

### Budget-Conscious Approach: **$0.055**

- Use GPT-4o-mini Batch API for all languages
- Accept lower quality for rare languages
- Community reviews will catch issues

### Balanced Approach: **$2.50**

- Claude Sonnet for challenging languages
- GPT-4o-mini Batch for well-resourced languages
- Best quality/cost ratio

### Research/Comparison Approach: **$5-10**

- Run 2-3 models for all languages
- Generate detailed comparison reports
- Publish research on "Which AI is best for multilingual programming translation?"
- Could be a great blog post/paper!

### Premium/Gold Standard: **$2.27**

- Claude 3.5 Sonnet for everything
- Maximum consistency
- Best quality

---

## Implementation Notes

### Batch Processing Script

```python
# scripts/migrate_translations/generate_ai_translations.py
async def generate_translations_batch(
    languages: list[str],
    model: str = "claude-3-5-sonnet-20241022",
    use_batch_api: bool = True
):
    # For each language, for each keyword/builtin
    # Generate translation via API
    # Save results with model attribution
    pass
```

### Cost Tracking

```python
total_cost = 0
for lang in languages:
    response = await call_api(...)
    cost = calculate_cost(response.usage)
    total_cost += cost
    print(f"{lang}: ${cost:.4f}")

print(f"Total: ${total_cost:.2f}")
```

---

## Questions for Decision

1. **Budget**: What's your total budget for this experiment?
2. **Comparison**: Do you want to compare multiple models, or just get one high-quality set?
3. **Timeline**: Okay with 24h batch processing for 50% savings?
4. **Quality vs Cost**: Premium model (Claude) or budget (GPT-4o-mini)?
5. **Research Output**: Planning to publish findings on model comparison?

---

## Next Steps

1. Decide on model strategy
2. Set up API keys for chosen providers
3. Run generation script on pilot languages (3-5)
4. Review quality
5. Run full batch
6. Generate comparison reports
7. Share with community for review

---

**Bottom Line**: For **less than $10**, you can generate translations with **ALL major LLM models** for **ALL 48 languages** and let your community compare which AI does best. This is incredibly cost-effective for the research value!
