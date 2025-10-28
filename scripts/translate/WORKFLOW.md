# Translation Workflow - From API to Language Pack

**Visual guide:** How we go from AI model outputs to production-ready language packs

---

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT: Python Keywords                       │
│              (35 keywords + 70 builtins = 105 terms)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 1: Generate Context Documents             │
│                                                                  │
│  For each term:                                                 │
│  • Create Tier 1 context (1000-1500 words)                     │
│  • Include code examples, pattern info, linguistic guidance     │
│                                                                  │
│  Tools: context-template-tier1.md                              │
│  Output: 105 context documents                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: Submit to AI Models (3 models)             │
│                                                                  │
│  For each term × each language × each model:                   │
│  • Claude: context + claude-prompt.md → XML response           │
│  • GPT-4:  context + gpt4-prompt.json → JSON response          │
│  • Aya:    context + aya-prompt.md → Text response             │
│                                                                  │
│  Total requests: 105 terms × 4 languages × 3 models = 1,260    │
│  Cost: ~$21 for all 3 models                                   │
│  Time: 24-48 hours (batch processing)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 3: Parse Responses                        │
│                                                                  │
│  Claude (XML)  →  │                                            │
│  GPT-4 (JSON)  →  │ → Parse → Normalize → Internal format     │
│  Aya   (Text)  →  │                                            │
│                                                                  │
│  Output: Normalized data structure for each translation        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           STEP 4: Generate Review Documents (GitHub)            │
│                                                                  │
│  For each term:                                                 │
│  ┌────────────────────────────────────────────────────┐        │
│  │ # Review: `def` → Spanish                          │        │
│  │                                                     │        │
│  │ ## Claude: definir (HIGH confidence)               │        │
│  │ Reasoning: Standard CS education term...           │        │
│  │                                                     │        │
│  │ ## GPT-4: definir (HIGH confidence)                │        │
│  │ Reasoning: Natural for native speakers...          │        │
│  │                                                     │        │
│  │ ## Aya: definir (high confidence)                  │        │
│  │ Reasoning: Comfortable for daily use...            │        │
│  │                                                     │        │
│  │ ✅ Consensus: All 3 models agree on `definir`     │        │
│  │                                                     │        │
│  │ [ ] Accept  [ ] Alternative  [ ] Discuss          │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  Output: 420 review documents (105 terms × 4 languages)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 5: Community Review (1-2 weeks)               │
│                                                                  │
│  Post to GitHub Discussions or Linear:                         │
│                                                                  │
│  👥 Spanish speakers review Spanish translations               │
│  👥 Arabic speakers review Arabic translations                 │
│  👥 Chinese speakers review Chinese translations               │
│  👥 Hindi speakers review Hindi translations                   │
│                                                                  │
│  For each translation:                                          │
│  ✅ Accept (models agreed, sounds natural)                     │
│  🔄 Alternative (suggest different translation)                │
│  ❓ Discuss (needs native speaker debate)                      │
│                                                                  │
│  Decision types:                                                │
│  • Easy consensus: All 3 models agree → Quick approval         │
│  • Split decision: 2-1 vote → Community decides                │
│  • Disagreement: All different → Deeper discussion             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          STEP 6: Generate Language Pack YAML Files              │
│                                                                  │
│  es-ES/keywords.yml:                                           │
│  ┌────────────────────────────────────────────────────┐        │
│  │ language:                                           │        │
│  │   name: Spanish                                     │        │
│  │   code: es                                          │        │
│  │                                                     │        │
│  │ keywords:                                           │        │
│  │   def:                                              │        │
│  │     translation: definir                            │        │
│  │     form: infinitive                                │        │
│  │     confidence: HIGH                                │        │
│  │     reviewed_by: community                          │        │
│  │                                                     │        │
│  │   return:                                           │        │
│  │     translation: retornar                           │        │
│  │     ...                                             │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  Output: 4 language pack files (Spanish, Arabic, Chinese, Hindi)│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 7: Integration Tests                     │
│                                                                  │
│  Test that translations work in actual code:                   │
│                                                                  │
│  Spanish:                                                       │
│    definir saludar(): → def greet(): ✅                        │
│                                                                  │
│  Arabic:                                                        │
│    يعرف saludar(): → def greet(): ✅                           │
│                                                                  │
│  Test transformations, execution, IDE integration              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 8: Documentation                         │
│                                                                  │
│  For each language:                                             │
│  • Translation rationale document                               │
│  • Usage examples                                               │
│  • Regional considerations                                      │
│  • Teaching guide (for legesher.io/learn)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        STEP 9: Release! 🎉                      │
│                                                                  │
│  • Publish language packs to npm                                │
│  • Update VS Code extension                                     │
│  • Announce to community                                        │
│  • Share on social media                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step Breakdown

### Step 1: Generate Context Documents

**What happens:**

- For each of 105 terms, create a Tier 1 context document
- Fill in template with code examples, pattern info, etc.

**Tools:**

- `context-template-tier1.md` (template)
- Script to auto-generate from Python AST

**Example output:**

```
contexts/
├── keywords/
│   ├── def.md
│   ├── return.md
│   ├── True.md
│   └── ...
└── builtins/
    ├── isinstance.md
    ├── print.md
    └── ...
```

**Time:** 2-4 hours (mostly automated)

---

### Step 2: Submit to AI Models

**What happens:**

- Combine context + prompt for each model
- Submit to respective APIs
- Wait for responses

**API Calls:**

```python
# Pseudo-code for batch submission

for term in terms:  # 105 terms
    for language in languages:  # 4 languages
        context = load_context(term)
        standards = load_standards(language)

        # Claude
        claude_prompt = format_prompt(
            template="claude-translation-prompt.md",
            term=term,
            language=language,
            context=context
        )
        claude_batch.add_request(claude_prompt)

        # GPT-4
        gpt4_prompt = format_prompt(
            template="gpt4-translation-prompt.json",
            term=term,
            language=language,
            context=context
        )
        gpt4_requests.append(gpt4_prompt)

        # Aya
        aya_prompt = format_prompt(
            template="aya-translation-prompt.md",
            term=term,
            language=language,
            context=context
        )
        aya_requests.append(aya_prompt)

# Submit all at once
claude_batch.submit()  # 420 requests → 12-24h wait
gpt4_batch.submit()    # 420 requests → 2-4h wait
aya_batch.submit()     # 420 requests → 2-4h wait
```

**Output:**

```
responses/
├── claude/
│   ├── def-spanish.xml
│   ├── def-arabic.xml
│   ├── return-spanish.xml
│   └── ...
├── gpt4/
│   ├── def-spanish.json
│   ├── def-arabic.json
│   └── ...
└── aya/
    ├── def-spanish.txt
    ├── def-arabic.txt
    └── ...
```

**Time:** 24-48 hours (mostly waiting)

---

### Step 3: Parse Responses

**What happens:**

- Parse XML, JSON, and text formats
- Extract key information
- Normalize into common structure

**Script:**

```python
# parse_responses.py

def parse_claude_response(xml_file):
    """Parse Claude's XML response"""
    tree = ET.parse(xml_file)
    return {
        "model": "claude",
        "translation": tree.find(".//translation").text,
        "form": tree.find(".//form").text,
        "confidence": tree.find(".//confidence").text,
        "reasoning": tree.find(".//final_decision").text,
        "alternatives": [
            alt.find("translation").text
            for alt in tree.findall(".//alternative")
        ]
    }

def parse_gpt4_response(json_file):
    """Parse GPT-4's JSON response"""
    with open(json_file) as f:
        data = json.load(f)
    return {
        "model": "gpt4",
        "translation": data["recommended_translation"]["translation"],
        "form": data["recommended_translation"]["form"],
        "confidence": data["recommended_translation"]["confidence"],
        "reasoning": data["reasoning"]["final_decision"],
        "alternatives": [
            alt["translation"]
            for alt in data["alternatives_considered"]
        ]
    }

def parse_aya_response(text_file):
    """Parse Aya's text response"""
    with open(text_file) as f:
        content = f.read()

    translation = re.search(r"TRANSLATION: (.+)", content).group(1)
    confidence = re.search(r"CONFIDENCE: (.+)", content).group(1)
    # ... extract other fields

    return {
        "model": "aya",
        "translation": translation,
        "confidence": confidence,
        # ...
    }
```

**Output:**

```python
# normalized_responses.json
{
    "def": {
        "spanish": {
            "claude": {
                "translation": "definir",
                "confidence": "HIGH",
                "reasoning": "...",
                "alternatives": ["declarar", "crear"]
            },
            "gpt4": {
                "translation": "definir",
                "confidence": "HIGH",
                # ...
            },
            "aya": {
                "translation": "definir",
                "confidence": "high",
                # ...
            }
        },
        "arabic": { ... },
        # ...
    },
    "return": { ... },
    # ...
}
```

**Time:** 1-2 hours (scripted)

---

### Step 4: Generate Review Documents

**What happens:**

- Create markdown review doc for each term+language
- Show all 3 model suggestions side-by-side
- Highlight consensus or disagreements

**Script:**

```python
# generate_review_docs.py

def generate_review_doc(term, language, responses):
    """Generate review document for community"""

    # Check for consensus
    translations = [r["translation"] for r in responses.values()]
    has_consensus = len(set(translations)) == 1

    template = f"""
# Translation Review: `{term}` → {language}

**Pattern:** {responses["claude"]["pattern"]}
**Difficulty:** {responses["claude"]["difficulty"]}

---

## Model Recommendations

### 🤖 Claude (Confidence: {responses["claude"]["confidence"]})
**Translation:** `{responses["claude"]["translation"]}`
**Form:** {responses["claude"]["form"]}
**Key reasoning:** {responses["claude"]["reasoning"][:200]}...

**Alternatives:** {", ".join(responses["claude"]["alternatives"])}

---

### 🤖 GPT-4 (Confidence: {responses["gpt4"]["confidence"]})
**Translation:** `{responses["gpt4"]["translation"]}`
**Form:** {responses["gpt4"]["form"]}
**Key reasoning:** {responses["gpt4"]["reasoning"][:200]}...

**Alternatives:** {", ".join(responses["gpt4"]["alternatives"])}

---

### 🤖 Aya (Confidence: {responses["aya"]["confidence"]})
**Translation:** `{responses["aya"]["translation"]}`
**Form:** {responses["aya"]["form"]}
**Key reasoning:** {responses["aya"]["reasoning"][:200]}...

**Alternatives:** {", ".join(responses["aya"]["alternatives"])}

---

## Consensus Analysis

{"✅ **All 3 models agree:** `" + translations[0] + "`" if has_consensus else "⚠️ **Models disagree** - needs community review"}

---

## Community Review

**Your decision:**
- [ ] ✅ Accept: `{translations[0] if has_consensus else "___"}` (recommended)
- [ ] 🔄 Alternative: `___________` (specify)
- [ ] ❓ Needs discussion

**Native speaker input:**
- Does this sound natural?
- Used in your region's CS education?
- Comfortable for daily use?

---

## Final Decision

**Approved translation:** `___________`
**Approved by:** `___________`
**Date:** `___________`
"""

    return template
```

**Output:**

```
reviews/
├── spanish/
│   ├── def.md
│   ├── return.md
│   ├── True.md
│   └── ...
├── arabic/
│   └── ...
└── ...
```

**Time:** 1 hour (automated)

---

### Step 5: Community Review

**What happens:**

- Post review docs to GitHub Discussions or Linear
- Native speakers provide input
- Reach consensus on each translation

**Categories:**

1. **Easy Consensus** (70-80% of translations)
   - All 3 models agree
   - High confidence from all
   - Quick approval ✅

2. **Minor Disagreement** (15-20%)
   - 2 models agree, 1 differs
   - Community picks the better option
   - Moderate discussion 🔄

3. **Major Disagreement** (5-10%)
   - All 3 models suggest different translations
   - Needs deep native speaker discussion
   - May require regional variants ❓

**Example discussion:**

```markdown
## Thread: `isinstance` → Spanish

**Models suggest:**
- Claude: "es instancia"
- GPT-4: "es instancia"
- Aya: "es_instancia" (underscore)

**Discussion:**

@maria_es_spain: I prefer "es_instancia" (one word with underscore).
Looks cleaner in code and follows Python naming conventions.

@juan_mx: Agreed, but should we follow the 2-word pattern that
Hindi uses? "es instancia" feels more natural when speaking.

@carlos_ar: As a CS professor, I teach "instancia de" not "es instancia".
Should we use "instancia_de"?

**Resolution:** After 3 days discussion, consensus reached on
"es_instancia" (follows Python conventions, cleaner in code).
```

**Time:** 1-2 weeks (depends on community engagement)

---

### Steps 6-9: Generate, Test, Document, Release

These are mostly automated/straightforward:

- **Step 6:** Script generates YAML from approved translations (1 hour)
- **Step 7:** Integration tests verify everything works (2 hours)
- **Step 8:** Generate documentation (2 hours)
- **Step 9:** Publish and announce (1 hour)

---

## Total Timeline

```
Week 1: Generation & Processing
├─ Day 1:  Generate contexts, submit to APIs (4 hours work)
├─ Day 2:  Wait for API responses (passive)
├─ Day 3:  Parse responses (2 hours)
└─ Day 4:  Generate review docs (1 hour)

Week 2-3: Community Review
├─ Day 5:  Post reviews, invite community (1 hour)
├─ Day 6-14: Community discussion (passive, moderation)
└─ Day 15: Finalize decisions (2 hours)

Week 4: Production
├─ Day 16: Generate language packs (1 hour)
├─ Day 17: Integration tests (2 hours)
├─ Day 18: Documentation (2 hours)
└─ Day 19: Release! (1 hour)
```

**Total active work:** ~20 hours
**Total calendar time:** ~3-4 weeks (mostly waiting for community)

---

## Key Success Metrics

**Translation Quality:**

- ✅ 90%+ consensus (all 3 models agree)
- ✅ Native speaker approval
- ✅ Passes integration tests

**Community Engagement:**

- ✅ 3+ native speakers review each language
- ✅ Regional diversity (Spain, Mexico, Argentina, etc.)
- ✅ Active discussion on unclear cases

**Production Ready:**

- ✅ All 105 terms translated
- ✅ YAML files generated
- ✅ Tests passing
- ✅ Documentation complete

---

**Questions?** Let me know what part of the workflow you want to explore more!
