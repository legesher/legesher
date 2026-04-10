# Translation Prompts - Model-Specific Approaches

**Version:** 1.0
**Last Updated:** 2025-10-28
**Purpose:** Model-optimized prompts for translating Python keywords and builtins

---

## Overview

This directory contains three model-specific prompts for AI-assisted translation of Python terms into multiple languages. Each prompt is optimized for the strengths and API capabilities of different models.

**Translation Flow:**

1. Generate context document (Tier 1 template) for each Python term
2. Feed context + linguistic standards to AI model using appropriate prompt
3. Collect translations from all 3 models
4. Present all suggestions to human reviewers for final decision

---

## Prompt Files

### 1. Claude Translation Prompt

**File:** `claude-translation-prompt.md`
**Model:** Claude 3.5 Sonnet or Claude 3 Opus
**Temperature:** 0.3 (low for consistency)

**Key Features:**

- XML-structured reasoning framework
- Emphasis on step-by-step thinking
- Comprehensive validation checklist
- Detailed reasoning sections
- Human review notes

**Why Claude:**

- Excels at complex reasoning tasks
- Strong at following detailed instructions
- Good at multilingual understanding
- Handles long-form reasoning well

**Output Format:** XML with nested reasoning tags

**API Cost (estimated):**

- Input: ~3,500 tokens (Tier 1 context + prompt)
- Output: ~1,500 tokens (detailed reasoning)
- Per translation: $0.018 (Batch API)
- Total for 4 languages × 105 terms: **$7.56**

---

### 2. GPT-4 Translation Prompt

**File:** `gpt4-translation-prompt.json`
**Model:** GPT-4o
**Temperature:** 0.3 (low for consistency)

**Key Features:**

- JSON schema for structured output
- JSON mode enabled (guaranteed valid JSON)
- System + user message pattern
- Comprehensive example included
- Clear field documentation

**Why GPT-4:**

- Strong JSON mode capabilities
- Fast inference speed
- Excellent multilingual performance
- Good at structured tasks

**Output Format:** Valid JSON matching specified schema

**API Cost (estimated):**

- Input: ~3,500 tokens (Tier 1 context + prompt)
- Output: ~1,500 tokens (JSON response)
- Per translation: $0.0285
- Total for 4 languages × 105 terms: **$11.97**

---

### 3. Aya Translation Prompt

**File:** `aya-translation-prompt.md`
**Model:** Aya Expanse 32B or 8B
**Temperature:** 0.5 (slightly higher for multilingual creativity)

**Key Features:**

- Simple, clear structure
- 4 detailed few-shot examples
- Less complex reasoning framework
- Language-specific reminders
- Plain text output format

**Why Aya:**

- Specialized for multilingual tasks
- Trained on 101 languages
- Strong non-English performance
- May capture cultural nuances others miss

**Output Format:** Simple structured text (not XML/JSON)

**API Cost (estimated):**

- Input: ~3,200 tokens (simpler prompt)
- Output: ~800 tokens (concise response)
- Per translation: TBD (Cohere API pricing)
- Total estimate: **~$1-2** (significantly cheaper)

---

## Comparative Analysis

| Feature                   | Claude                | GPT-4                  | Aya           |
| ------------------------- | --------------------- | ---------------------- | ------------- |
| **Reasoning Depth**       | ⭐⭐⭐⭐⭐            | ⭐⭐⭐⭐               | ⭐⭐⭐        |
| **Structured Output**     | ⭐⭐⭐⭐ (XML)        | ⭐⭐⭐⭐⭐ (JSON mode) | ⭐⭐⭐ (text) |
| **Multilingual Strength** | ⭐⭐⭐⭐              | ⭐⭐⭐⭐               | ⭐⭐⭐⭐⭐    |
| **Cost Efficiency**       | ⭐⭐⭐⭐ (Batch API)  | ⭐⭐⭐                 | ⭐⭐⭐⭐⭐    |
| **Speed**                 | ⭐⭐⭐ (12-24h batch) | ⭐⭐⭐⭐⭐             | ⭐⭐⭐⭐      |
| **Cultural Nuance**       | ⭐⭐⭐⭐              | ⭐⭐⭐⭐               | ⭐⭐⭐⭐⭐    |

---

## Usage

### Claude (Batch API)

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

# Read prompt template
with open("claude-translation-prompt.md") as f:
    prompt_template = f.read()

# Fill in variables
prompt = prompt_template.format(
    TERM="def",
    TARGET_LANGUAGE="Spanish",
    TIER_1_CONTEXT_DOCUMENT=tier1_context,
    LINGUISTIC_STANDARDS_EXCERPT=standards,
    # ... other variables
)

# Create batch request
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"translate-def-es",
            "params": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}]
            }
        }
    ]
)

# Wait for batch to complete (12-24 hours)
# Then retrieve results
```

### GPT-4 (JSON Mode)

```python
from openai import OpenAI
import json

client = OpenAI(api_key="...")

# Load prompt template
with open("gpt4-translation-prompt.json") as f:
    prompt_config = json.load(f)

# Fill in user message template
user_message = prompt_config["user_message_template"].format(
    term="def",
    term_type="keyword",
    target_language="Spanish",
    tier1_context=tier1_context,
    # ... other variables
)

# Call API with JSON mode
response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.3,
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": prompt_config["system_message"]},
        {"role": "user", "content": user_message}
    ]
)

# Parse JSON response
translation = json.loads(response.choices[0].message.content)
```

### Aya (Cohere API)

```python
import cohere

client = cohere.Client(api_key="...")

# Read prompt template
with open("aya-translation-prompt.md") as f:
    prompt_template = f.read()

# Fill in variables
prompt = prompt_template.format(
    TERM="def",
    TARGET_LANGUAGE="Spanish",
    TIER_1_CONTEXT_SUMMARY=tier1_summary,
    # ... other variables
)

# Call API
response = client.chat(
    model="aya-expanse-32b",
    message=prompt,
    temperature=0.5
)

# Parse text response
translation_text = response.text
```

---

## Testing Strategy

Before running full batch translations:

1. **Test on 5 sample terms** (different patterns):
   - `def` - ACTION keyword, easy
   - `return` - ACTION keyword, easy
   - `True` - VALUE constant, easy
   - `isinstance` - Builtin function (compound), medium
   - `lambda` - Abstract concept, hard

2. **Test each model** with each sample term

3. **Validate output format**:
   - Claude: Check XML is well-formed and complete
   - GPT-4: Check JSON is valid and matches schema
   - Aya: Check text format is parseable

4. **Compare quality**:
   - Do all 3 models provide reasonable translations?
   - Are reasoning explanations helpful for reviewers?
   - Any model consistently better/worse for certain languages?

5. **Adjust prompts** based on test results

---

## Expected Timeline

**With all 3 models (4 languages, 105 terms each):**

| Model               | Processing Time | Cost     |
| ------------------- | --------------- | -------- |
| Claude Batch API    | 12-24 hours     | $7.56    |
| GPT-4o Standard API | 2-4 hours       | $11.97   |
| Aya (Cohere)        | 2-4 hours       | ~$1-2    |
| **Total**           | **24-48 hours** | **~$21** |

**Parallelization:**

- Run all 3 models in parallel
- Claude batch processes overnight
- GPT-4 and Aya complete during work day
- Results ready for review within 24-48 hours

---

## Output Processing

Each model will generate translations that need to be:

1. **Parsed** - Extract from XML/JSON/text format
2. **Normalized** - Convert to common internal format
3. **Presented** - Show all 3 suggestions side-by-side for human review
4. **Reviewed** - Community reviewers choose best option
5. **Compiled** - Selected translations → YAML language pack files

**Review Format (for each term):**

```
Term: `def` (keyword)
Language: Spanish
Pattern: ACTION_KEYWORD

┌─────────────────────────────────────────────────────────────┐
│ Claude Suggestion                                            │
├─────────────────────────────────────────────────────────────┤
│ Translation: definir                                         │
│ Form: infinitive                                             │
│ Confidence: HIGH                                             │
│ Rationale: Direct translation, used in CS textbooks...      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ GPT-4 Suggestion                                             │
├─────────────────────────────────────────────────────────────┤
│ Translation: definir                                         │
│ Form: infinitive                                             │
│ Confidence: HIGH                                             │
│ Rationale: Standard CS education term, consistent with...   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Aya Suggestion                                               │
├─────────────────────────────────────────────────────────────┤
│ Translation: definir                                         │
│ Form: infinitive                                             │
│ Confidence: high                                             │
│ Rationale: Captures "defining" concept, natural for...      │
└─────────────────────────────────────────────────────────────┘

[ ] Select Claude   [ ] Select GPT-4   [x] Select Aya
[ ] Use different translation: _____________
```

---

## Next Steps

1. ✅ Create model-specific prompts (DONE)
2. ⏳ Test prompts on 5 sample terms
3. ⏳ Build batch processing scripts
4. ⏳ Create output parser for each model format
5. ⏳ Build review interface for presenting suggestions
6. ⏳ Run full batch translations
7. ⏳ Community review process
8. ⏳ Generate final YAML language packs

---

**Maintained by:** Legesher Team
**Related Issues:** CORE-354
**See also:**

- [../i18n/docs/linguistic-standards.md](../i18n/docs/linguistic-standards.md)
- [../i18n/docs/context-template-tier1.md](../i18n/docs/context-template-tier1.md)
- [../i18n/docs/context-template-tier2.md](../i18n/docs/context-template-tier2.md)
