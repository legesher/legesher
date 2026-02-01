# Example Outputs - What You'll Get From Each Model

**Purpose:** Show what the API responses look like and how they're processed into final language packs

---

## Example: Translating `def` → Spanish

Let's walk through what you'd get from each of the 3 models when translating the keyword `def` to Spanish.

---

## 1. Claude Output (XML Format)

**Raw API Response:**

```xml
<translation_result>
  <term>def</term>
  <target_language>Spanish</target_language>

  <recommended_translation>
    <translation>definir</translation>
    <form>infinitive</form>
    <confidence>HIGH</confidence>
  </recommended_translation>

  <reasoning>
    <concept_analysis>
      The `def` keyword in Python creates a function definition. It's an ACTION keyword that tells Python "I am about to define a function." The English "def" is short for "define," meaning to establish or set bounds to something. In the context of full localization, Spanish-speaking developers will type this every time they create a function, so it needs to be natural, memorable, and align with how functions are taught in Spanish CS education.
    </concept_analysis>

    <translation_options>
      <option priority="1">
        <translation>definir</translation>
        <form>infinitive</form>
        <rationale>Direct translation of "define" - to establish, to set bounds. This is the standard term used in Spanish CS textbooks for "definir una función" (define a function).</rationale>
        <eliminated>no</eliminated>
      </option>
      <option priority="2">
        <translation>función</translation>
        <form>noun</form>
        <rationale>Names what it creates (a function). Developers would recognize this immediately.</rationale>
        <eliminated>yes</eliminated>
        <elimination_reason>Describes the result, not the action. Python keywords are actions/verbs for ACTION keywords. This would break the pattern with other ACTION keywords like return, break, continue.</elimination_reason>
      </option>
      <option priority="3">
        <translation>crear</translation>
        <form>infinitive</form>
        <rationale>Means "to create" - describes what you're doing when you use def.</rationale>
        <eliminated>yes</eliminated>
        <elimination_reason>Too generic - you "create" many things in programming (classes, variables, objects). Doesn't capture the specific concept of "defining" vs general "creation".</elimination_reason>
      </option>
      <option priority="4">
        <translation>declarar</translation>
        <form>infinitive</form>
        <rationale>Means "to declare" - similar to define, used in programming contexts.</rationale>
        <eliminated>yes</eliminated>
        <elimination_reason>While technically valid, "declarar" is more commonly used for variable declarations in Spanish CS education. "Definir" is the standard term specifically for function definitions across Spain, Mexico, Argentina, and other Spanish-speaking regions.</elimination_reason>
      </option>
    </translation_options>

    <priority_filtering>
      <technical_accuracy>
        ✅ "definir" (to define/establish) - correct, captures the concept of establishing a function
        ✅ "crear" (to create) - technically correct but too generic
        ✅ "declarar" (to declare) - correct but wrong context (used for variables)
        ❌ "función" (function) - wrong part of speech (noun instead of verb)
      </technical_accuracy>

      <cs_education_alignment>
        Research shows Spanish CS textbooks consistently use "definir una función" (define a function). This is standard across Spain, Mexico, Argentina, Colombia, and other Spanish-speaking regions. University courses in Spanish use "definir" when teaching function creation. Students already associate "definir" with function definitions from their coursework, making it the most intuitive choice for learners.
      </cs_education_alignment>

      <naturalness>
        "Definir" is natural, easy to pronounce (deh-fee-NEER), and commonly used in technical contexts in Spanish. It's a cognate with English "define," which helps bilingual learners connect concepts across languages. Spanish developers can comfortably say "vamos a definir una función" (let's define a function) in code reviews.
      </naturalness>

      <consistency_check>
        This is an ACTION keyword pattern. Other ACTION keywords should also use infinitive verbs for consistency:
        - `return` → "retornar" (infinitive) ✓
        - `break` → "romper" (infinitive) ✓
        - `continue` → "continuar" (infinitive) ✓
        Using "definir" (infinitive) maintains pattern consistency and makes the language predictable for developers.
      </consistency_check>
    </priority_filtering>

    <final_decision>
      "Definir" is the clear winner for multiple reinforcing reasons: (1) Technically accurate - captures the specific concept of establishing/defining rather than generic creation, (2) Aligns with CS education terminology used across all Spanish-speaking regions, (3) Natural for native speakers - easy to say, type, and remember, (4) Maintains consistency with the ACTION keyword pattern (infinitive verb form), (5) Optimized for daily use - developers will comfortably use this hundreds of times per day.
    </final_decision>
  </reasoning>

  <alternatives_considered>
    <alternative rank="2">
      <translation>declarar</translation>
      <form>infinitive</form>
      <why_not_chosen>While technically valid and used in programming contexts, "declarar" is more commonly associated with variable declarations (declarar una variable) rather than function definitions in Spanish CS education. "Definir" is the more precise and standard term for functions specifically.</why_not_chosen>
    </alternative>
    <alternative rank="3">
      <translation>crear</translation>
      <form>infinitive</form>
      <why_not_chosen>Too generic - doesn't capture the specific concept of "definition" vs general "creation". You "create" many things (classes, objects, instances), but you "define" functions. Less precise than "definir".</why_not_chosen>
    </alternative>
  </alternatives_considered>

  <validation_checklist>
    <item checked="true">Captures Python concept (defining a function)</item>
    <item checked="true">Correct part of speech (verb)</item>
    <item checked="true">Correct form (infinitive for ACTION keyword)</item>
    <item checked="true">Matches pattern (infinitive like other ACTION keywords)</item>
    <item checked="true">Short enough (1 word)</item>
    <item checked="true">Easy to pronounce ("deh-fee-NEER")</item>
    <item checked="true">No offensive meanings</item>
    <item checked="true">Renders in IDEs (standard Latin characters)</item>
    <item checked="true">CS education aligned (textbooks use "definir")</item>
    <item checked="true">Consistent with related terms (infinitive pattern)</item>
  </validation_checklist>

  <human_review_notes>
    High confidence. This is a straightforward translation with strong CS education backing across all Spanish-speaking regions. No regional variations or concerns identified. The cognate relationship with English "define" is an additional benefit for bilingual developers without being a crutch.
  </human_review_notes>

  <metadata>
    <difficulty>EASY</difficulty>
    <pattern>ACTION_KEYWORD</pattern>
    <python_version>3.10+</python_version>
  </metadata>
</translation_result>
```

---

## 2. GPT-4 Output (JSON Format)

**Raw API Response:**

```json
{
  "term": "def",
  "target_language": "Spanish",
  "recommended_translation": {
    "translation": "definir",
    "form": "infinitive",
    "confidence": "HIGH"
  },
  "reasoning": {
    "concept_analysis": "The `def` keyword in Python creates a function definition. It tells Python to establish a new function with a given name and parameters. This is an ACTION keyword that developers will type every time they create a function, so it must be natural and align with how functions are taught in Spanish-speaking regions.",
    "translation_options": [
      {
        "translation": "definir",
        "form": "infinitive",
        "rationale": "Direct translation of 'define' - to establish or set bounds. Standard term in Spanish CS education.",
        "eliminated": false,
        "elimination_reason": null
      },
      {
        "translation": "función",
        "form": "noun",
        "rationale": "Names the result (a function) rather than the action.",
        "eliminated": true,
        "elimination_reason": "Wrong part of speech. ACTION keywords should be verbs, not nouns. Would break consistency with return, break, continue."
      },
      {
        "translation": "crear",
        "form": "infinitive",
        "rationale": "Means 'to create' - describes the action being performed.",
        "eliminated": true,
        "elimination_reason": "Too generic. You 'create' many things in programming. Doesn't capture the specific concept of 'defining' a function."
      },
      {
        "translation": "declarar",
        "form": "infinitive",
        "rationale": "Means 'to declare' - similar programming concept.",
        "eliminated": true,
        "elimination_reason": "More commonly used for variable declarations in Spanish CS. 'Definir' is standard for functions."
      }
    ],
    "priority_filtering": {
      "technical_accuracy": "✅ 'definir' - correct (to define/establish). ✅ 'crear' - correct but generic. ✅ 'declarar' - correct but wrong context. ❌ 'función' - wrong form (noun not verb).",
      "cs_education_alignment": "Spanish CS textbooks use 'definir una función' consistently across Spain, Latin America, and other Spanish-speaking regions. This is what students learn in university courses.",
      "naturalness": "'Definir' is natural for Spanish speakers, easy to pronounce, and commonly used in technical contexts. Cognate with English 'define' helps bilingual developers.",
      "consistency_check": "ACTION keywords use infinitive verbs: retornar, romper, continuar. 'Definir' maintains this pattern."
    },
    "final_decision": "'Definir' is the best choice because it's technically accurate, aligns with CS education across all Spanish regions, is natural for native speakers, and maintains consistency with other ACTION keywords."
  },
  "alternatives_considered": [
    {
      "rank": 2,
      "translation": "declarar",
      "form": "infinitive",
      "why_not_chosen": "More commonly used for variables. 'Definir' is the standard for functions specifically."
    },
    {
      "rank": 3,
      "translation": "crear",
      "form": "infinitive",
      "why_not_chosen": "Too generic - doesn't distinguish between creating different things."
    }
  ],
  "validation_checklist": {
    "captures_python_concept": true,
    "correct_part_of_speech": true,
    "correct_form": true,
    "matches_pattern": true,
    "short_enough": true,
    "easy_to_pronounce": true,
    "no_offensive_meanings": true,
    "renders_in_ides": true,
    "cs_education_aligned": true,
    "consistent_with_related": true
  },
  "human_review_notes": "High confidence. Strong CS education backing. No regional concerns.",
  "metadata": {
    "difficulty": "EASY",
    "pattern": "ACTION_KEYWORD",
    "python_version": "3.10+"
  }
}
```

---

## 3. Aya Output (Plain Text Format)

**Raw API Response:**

```text
TRANSLATION: definir
FORM: infinitive
CONFIDENCE: high

OPTIONS CONSIDERED:
1. definir - Direct translation of "define", standard term in Spanish CS education
2. función - Names what it creates (a function)
3. crear - Means "to create", generic action verb
4. declarar - Means "to declare", used in programming

WHY THIS IS BEST:
"Definir" is the best translation because it captures the specific programming concept of defining a function, not just creating something generic. Spanish CS textbooks across Spain, Mexico, Argentina, and Latin America use "definir una función" as the standard term. Since developers will type this hundreds of times per day in fully localized codebases, it needs to be natural and memorable - "definir" satisfies both requirements.

- Does it capture the Python concept? Yes - "def" defines a function, "definir" means to define
- Is it used in CS education? Yes - standard term in Spanish CS textbooks and courses
- Does it match the pattern of similar terms? Yes - ACTION keywords use infinitive verbs (retornar, romper, continuar)
- Is it short and easy to type? Yes - one word, 7 letters, easy to pronounce

ALTERNATIVES:
- Second best: declarar - Why not chosen: More commonly used for variable declarations rather than function definitions in Spanish CS
- Third best: crear - Why not chosen: Too generic, doesn't capture the specific concept of "definition"

NOTES FOR REVIEWERS:
High confidence. This is straightforward with strong backing from CS education across all Spanish-speaking regions. The term is natural for native speakers and will be comfortable for daily use.
```

---

## Side-by-Side Comparison

| Aspect | Claude (XML) | GPT-4 (JSON) | Aya (Text) |
|--------|--------------|--------------|------------|
| **Recommended** | definir | definir | definir |
| **Confidence** | HIGH | HIGH | high |
| **Options Considered** | 4 options | 4 options | 4 options |
| **Reasoning Depth** | Very detailed | Detailed | Concise |
| **CS Research** | ✅ Mentioned regions | ✅ Mentioned regions | ✅ Mentioned regions |
| **Consistency Check** | ✅ Explicit | ✅ Explicit | ✅ Explicit |
| **Format** | XML (structured) | JSON (structured) | Plain text |
| **Parsability** | Easy (XML parser) | Easy (JSON parser) | Moderate (regex) |

**Key Observation:** All 3 models agree on **definir** with high confidence!
This is a great sign - when models converge, it's usually the right answer.

---

## What Happens Next: Processing Workflow

### Step 1: Parse Raw Responses

Each model's response gets parsed into a common internal format:

```python
# Internal format (normalized)
{
    "term": "def",
    "language": "Spanish",
    "model": "claude",  # or "gpt4" or "aya"
    "translation": "definir",
    "form": "infinitive",
    "confidence": "HIGH",
    "reasoning_summary": "Technically accurate, aligns with CS education...",
    "alternatives": ["declarar", "crear"],
    "validation_passed": True
}
```

### Step 2: Generate Review Document

All 3 translations are presented side-by-side for community review:

```markdown
# Translation Review: `def` → Spanish

**Pattern:** ACTION_KEYWORD
**Difficulty:** EASY

---

## Model Recommendations

### 🤖 Claude (Confidence: HIGH)
**Translation:** `definir`
**Form:** infinitive
**Key reasoning:** Standard term in Spanish CS textbooks across all regions. Maintains ACTION keyword pattern (infinitive verb).

**Alternatives considered:**
- declarar (more for variables)
- crear (too generic)

---

### 🤖 GPT-4 (Confidence: HIGH)
**Translation:** `definir`
**Form:** infinitive
**Key reasoning:** Aligns with CS education, natural for native speakers, maintains consistency.

**Alternatives considered:**
- declarar (used for variables)
- crear (doesn't distinguish function definition)

---

### 🤖 Aya (Confidence: high)
**Translation:** `definir`
**Form:** infinitive
**Key reasoning:** Standard in Spanish CS education, comfortable for daily use, matches ACTION keyword pattern.

**Alternatives considered:**
- declarar (variable declarations)
- crear (generic)

---

## Consensus Analysis

✅ **All 3 models agree:** `definir`
✅ **All recommend same form:** infinitive
✅ **All have high confidence**

**Recommendation:** Accept `definir` as the translation for `def`

---

## Community Review

**Your decision:**
- [ ] ✅ Accept: `definir` (recommended)
- [ ] 🔄 Alternative: `___________` (specify which and why)
- [ ] ❓ Needs discussion (explain concerns)

**Native speaker input:**
- Does `definir` sound natural when spoken aloud?
- Is this term used in your region's CS education?
- Can you comfortably type this hundreds of times per day?

**Regional considerations:**
- Spain: _____
- Mexico: _____
- Argentina: _____
- Other: _____

---

## Final Decision

**Approved translation:** `___________`
**Approved by:** `___________`
**Date:** `___________`
```

### Step 3: Community Review Process

1. **Post to GitHub Discussions** or **Linear issue** for each term
2. **Native speakers** from different regions provide input
3. **Edge cases** get flagged for deeper discussion
4. **Consensus is reached** (or tie-breaker vote if needed)

### Step 4: Generate Language Pack YAML

Once approved, the translation goes into the language pack file:

```yaml
# es-ES/keywords.yml (Spanish language pack)
# Generated from community-reviewed AI translations
# Review issue: https://github.com/legesher/legesher/issues/XXX

language:
  name: Spanish
  code: es
  family: Romance

keywords:
  # Control Flow - Function Definition
  def:
    translation: definir
    form: infinitive
    pattern: ACTION_KEYWORD
    confidence: HIGH
    reviewed_by: community
    reviewed_date: 2025-10-28
    notes: Standard term in Spanish CS education across all regions

  # (other keywords follow same format)
  return:
    translation: retornar
    form: infinitive
    pattern: ACTION_KEYWORD
    confidence: HIGH
    # ...

  True:
    translation: Verdadero
    form: adjective
    pattern: VALUE_CONSTANT
    confidence: HIGH
    # ...
```

### Step 5: Integration Testing

The language pack gets tested:

```python
# Test file: test_es_language_pack.py

def test_def_keyword_spanish():
    """Test that 'definir' works as 'def' replacement"""
    code = """
    definir saludar():
        print("Hola!")
    """
    # Run through Legesher transformer
    result = legesher.transform(code, from_lang="es", to_lang="en")
    assert "def greet():" in result

def test_full_spanish_function():
    """Test fully localized Spanish code"""
    spanish_code = """
    definir calcular_total(precio, impuesto):
        retornar precio + impuesto
    """
    # Execute as Python
    result = legesher.execute(spanish_code, lang="es")
    assert result is not None
```

### Step 6: Documentation

Each translation gets documented:

```markdown
# Translation: `def` → `definir`

**Language:** Spanish (es-ES)
**Category:** Control Flow - Function Definition
**Pattern:** ACTION_KEYWORD

## Translation Rationale

The keyword `def` is translated to `definir` (infinitive verb meaning "to define") in Spanish.

**Why this translation:**
- ✅ Standard term in Spanish CS education
- ✅ Maintains ACTION keyword pattern (infinitive)
- ✅ Natural for native speakers
- ✅ Easy to type and pronounce
- ✅ Consistent across all Spanish-speaking regions

**Example usage:**

```python
# English
def calculate_total(price, tax):
    return price + tax

# Spanish (Legesher)
definir calcular_total(precio, impuesto):
    retornar precio + impuesto
```

## Community Review

- **Consensus:** All 3 AI models recommended `definir`
- **Native speaker verification:** ✅ Approved
- **Regional testing:** Spain, Mexico, Argentina ✅
- **Final approval:** 2025-10-28

---

## Summary: The Complete Flow

```text
1. API Requests (420 translations)
   ↓
2. Raw Responses (XML, JSON, Text)
   ↓
3. Parse & Normalize (common format)
   ↓
4. Generate Review Documents (side-by-side comparison)
   ↓
5. Community Review (GitHub/Linear)
   ↓
6. Approve Translations (consensus or vote)
   ↓
7. Generate Language Pack YAML
   ↓
8. Integration Tests (verify it works)
   ↓
9. Documentation (explain choices)
   ↓
10. Release! 🎉

```

---

## Timeline Estimate

**With API (automated):**

- Day 1: Submit batch API requests (30 min)
- Day 2-3: Wait for responses (24-48 hours)
- Day 4: Parse responses, generate review docs (2 hours)
- Day 5-10: Community review (depends on engagement)
- Day 11: Generate language packs (1 hour)
- Day 12: Testing and documentation (4 hours)

**Total: ~2 weeks** (mostly waiting for community review)

**With Claude Desktop (manual):**

- Day 1-5: Generate 420 translations manually (10-20 hours)
- Day 6-10: Community review
- Day 11-12: Same as above

**Total: ~2 weeks** (same timeline, but more manual work upfront)

---

## Next Steps for You

**Right now (testing phase):**

1. Test 2-3 translations in Claude Desktop
2. See what quality you get
3. Decide if prompts need refinement

**Once prompts are validated:**

- **Option A:** Continue manually (free, 10-20 hours)
- **Option B:** Use API ($7.56, automated)

**Either way, you'll get:**

- 3 model suggestions per term
- Community review process
- Final language pack YAML files
- Full documentation

---

**Want to see more examples?** I can show you what the output might look like for:

- `True` (VALUE_CONSTANT - different pattern)
- `isinstance` (builtin - compound term)
- Arabic keyword (RTL language challenges)
