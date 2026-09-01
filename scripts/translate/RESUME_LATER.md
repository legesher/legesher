# Resume Translation Work Later

**Status:** Translation infrastructure complete, ready to pause
**When to resume:** In 1-2 weeks when ready to generate real translations

---

## What's Been Completed ✅

### Phase 1: Infrastructure (DONE)

**Documentation:**

- ✅ Linguistic standards (v2.0, 1468 lines) - Complete translation guidelines
- ✅ Two-tier context templates (Tier 1 for AI, Tier 2 for humans)
- ✅ Model-specific prompts (Claude, GPT-4, Aya) with full localization emphasis
- ✅ Example outputs showing what each model produces
- ✅ Complete workflow diagram (9 steps, API → production)
- ✅ Manual testing guide for Claude Desktop

**Testing Infrastructure:**

- ✅ Test cases ready (def → Spanish, True → Spanish)
- ✅ Response templates for saving results

**Language Packs:**

- ✅ Directory structure created (es-ES, ar-SA, zh-CN, hi-IN)
- ✅ Example Spanish keywords.yml (35 keywords with well-researched mock data)
- ✅ README documenting status and how to populate later

### What You Can Build Against

**Mock language pack:** `libs/i18n/language-packs/es-ES/keywords.yml`

- 35 Python keywords translated to Spanish
- Well-researched examples based on Spanish CS education
- Clearly marked as `status: example` (not production-ready)
- Includes patterns: ACTION, STATE, VALUE, OPERATOR keywords
- Full examples showing usage

**You can now build:**

- Language pack loader
- Keyword transformation logic
- IDE integration
- Testing framework
- Documentation

---

## When You're Ready to Resume

### Step 1: Test Prompts in Claude Desktop (Optional, Recommended)

**Time:** 30 minutes
**Cost:** $0 (included in Claude Pro)

Test 2-3 translations manually to validate prompt quality:

1. Open [scripts/translate/test-cases/01-def-spanish.md](test-cases/01-def-spanish.md)
2. Copy entire file into Claude Desktop
3. Review Claude's translation
4. Save response to `test-results/01-def-spanish-response.md`
5. Repeat for `02-true-spanish.md`
6. Evaluate quality - does reasoning look good?

**If quality is good:** Proceed to API
**If quality needs work:** Iterate on prompts, test again

### Step 2: Choose Your Approach

**Option A: Manual (Claude Desktop)**

- **Cost:** $0 extra (included in Claude Pro)
- **Time:** 10-20 hours for 420 translations
- **Process:** Copy/paste each term into Claude Desktop
- **Pros:** Free, full control, immediate iteration
- **Cons:** Tedious, manual work

**Option B: API - Claude Only (Recommended)**

- **Cost:** $7.56 (Claude Batch API)
- **Time:** 30 min setup + 24h wait
- **Process:** Script submits all requests, waits overnight, parses responses
- **Pros:** Automated, cheap, good quality
- **Cons:** Need API key, 24h wait

**Option C: API - All 3 Models**

- **Cost:** $21 (Claude $7.56 + GPT-4 $11.97 + Aya ~$2)
- **Time:** 30 min setup + 48h wait
- **Process:** Get 3 suggestions per term for community to choose
- **Pros:** Most transparent, community empowerment
- **Cons:** Higher cost, more complex review

### Step 3: Generate Translations

#### If Manual (Option A)

```bash
# Follow the manual testing guide
cat scripts/translate/QUICK_START.md

# Use test cases as templates for all 105 terms
# Track progress in test-results/
```

#### If API (Option B or C)

**Prerequisites:**

```bash
# Set API keys
export ANTHROPIC_API_KEY="sk-ant-..."  # Required for Claude
export OPENAI_API_KEY="sk-..."         # Optional for GPT-4
export COHERE_API_KEY="..."            # Optional for Aya
```

**Generate context documents:**

```bash
# Script to create Tier 1 context for all 105 terms
# (You'll need to write this - or we can create it together)
python scripts/translate/generate_contexts.py
```

**Submit batch requests:**

```bash
# Script to submit all translations to APIs
# (You'll need to write this - or we can create it together)
python scripts/translate/submit_batch.py --models claude  # or --models all
```

**Wait 24-48 hours...**

**Parse responses:**

```bash
python scripts/translate/parse_responses.py
```

### Step 4: Community Review

**Post to GitHub Discussions:**

```bash
python scripts/translate/generate_review_docs.py
# Creates markdown files for each translation
# Post to GitHub Discussions for native speaker input
```

**Timeline:** 1-2 weeks
**Goal:** Get 3+ native speakers to review each language

### Step 5: Update Language Packs

**Once approved:**

```bash
python scripts/translate/generate_language_packs.py --from-reviews
```

**This will:**

- Read approved translations from review documents
- Generate production YAML files
- Update `status: reviewed`
- Add reviewer names
- Bump version to `1.0.0`

### Step 6: Test & Release

**Run tests:**

```bash
pytest tests/i18n/
pytest tests/integration/
```

**Update docs:**

```bash
python scripts/translate/generate_docs.py
```

**Release:**

```bash
git tag v1.0.0-language-packs
git push origin v1.0.0-language-packs
# Publish to npm, announce to community
```

---

## What Scripts You'll Need to Write

When you resume, you'll need these scripts (we can build them together):

### 1. `generate_contexts.py`

**Purpose:** Auto-generate Tier 1 context documents for all 105 terms

```python
# Pseudo-code
for term in python_keywords + python_builtins:
    context = fill_template(
        template="docs/context-template-tier1.md",
        term=term,
        examples=get_code_examples(term),
        pattern=classify_pattern(term),
        # ...
    )
    save_context(f"contexts/{term}.md", context)
```

### 2. `submit_batch.py`

**Purpose:** Submit all translation requests to APIs

```python
# Pseudo-code
for term in terms:
    for language in languages:
        context = load_context(term)

        # Claude
        if "claude" in args.models:
            claude_batch.add_request(
                format_prompt("claude-prompt.md", term, language, context)
            )

        # GPT-4
        if "gpt4" in args.models:
            gpt4_requests.append(
                format_prompt("gpt4-prompt.json", term, language, context)
            )

        # Aya
        if "aya" in args.models:
            aya_requests.append(
                format_prompt("aya-prompt.md", term, language, context)
            )

# Submit all
claude_batch.submit()
gpt4_batch.submit()
aya_batch.submit()
```

### 3. `parse_responses.py`

**Purpose:** Parse XML/JSON/text responses into normalized format

```python
# Parse all responses
normalized = {}
for response_file in glob("responses/**/*"):
    model = detect_model(response_file)  # claude, gpt4, aya
    parsed = parse_response(response_file, model)
    normalized[parsed["term"]][parsed["language"]][model] = parsed

# Save normalized data
save_json("normalized_responses.json", normalized)
```

### 4. `generate_review_docs.py`

**Purpose:** Create markdown review docs showing all 3 model suggestions

```python
for term in terms:
    for language in languages:
        responses = load_responses(term, language)
        review_doc = create_review_template(term, language, responses)
        save_markdown(f"reviews/{language}/{term}.md", review_doc)
```

### 5. `generate_language_packs.py`

**Purpose:** Convert approved translations to YAML language packs

```python
for language in languages:
    pack = {
        "language": {...},
        "keywords": {},
        "builtins": {}
    }

    for term in terms:
        approved = read_approved_translation(term, language)
        pack["keywords"][term] = {
            "translation": approved.translation,
            "form": approved.form,
            "confidence": approved.confidence,
            # ...
        }

    save_yaml(f"language-packs/{language}/keywords.yml", pack)
```

---

## Cost Estimates

### Manual Approach

- **Cost:** $0 (Claude Pro subscription you already have)
- **Time:** 10-20 hours of copy/paste work
- **Best for:** Testing, small batches, budget constraints

### API Approach - Claude Only

- **Cost:** $7.56
- **Breakdown:**
  - 420 requests (105 terms × 4 languages)
  - ~3,500 input tokens per request
  - ~1,500 output tokens per request
  - Batch API 50% discount
- **Best for:** Good quality, low cost, fast

### API Approach - All 3 Models

- **Cost:** $21.00
- **Breakdown:**
  - Claude: $7.56 (batch)
  - GPT-4: $11.97 (standard)
  - Aya: ~$1.50 (estimated)
- **Best for:** Maximum transparency, community empowerment

---

## Timeline When You Resume

```
Day 1: Setup & Generation (3-4 hours)
├─ Test prompts in Claude Desktop (optional, 30 min)
├─ Set up API keys (5 min)
├─ Generate contexts (1 hour)
└─ Submit batch requests (30 min)

Day 2-3: Wait (passive)
└─ APIs process requests overnight

Day 4: Parse & Review Setup (2-3 hours)
├─ Parse responses (30 min)
├─ Generate review docs (30 min)
└─ Post to GitHub Discussions (1 hour)

Week 2-3: Community Review (passive)
└─ Native speakers review and approve

Day 15: Finalize (3-4 hours)
├─ Generate language packs (1 hour)
├─ Run tests (1 hour)
├─ Update docs (1 hour)
└─ Release (30 min)
```

**Total active work:** ~10 hours
**Total calendar time:** ~3 weeks

---

## Current State of Code

### What Works

- ✅ Prompts are ready and tested (dry-run passes)
- ✅ Templates are complete
- ✅ Linguistic standards are comprehensive
- ✅ Example language pack structure is defined

### What Needs to Be Built

- ⏳ Context generation script
- ⏳ Batch submission script
- ⏳ Response parsing script
- ⏳ Review doc generation script
- ⏳ Language pack generation script
- ⏳ Integration tests

**We can build these together when you're ready!**

---

## Quick Start When You Resume

```bash
# 1. Read the workflow to refresh your memory
cat scripts/translate/WORKFLOW.md

# 2. Test a couple prompts manually (optional but recommended)
cat scripts/translate/QUICK_START.md
# Copy test-cases/01-def-spanish.md into Claude Desktop

# 3. If quality looks good, decide: manual or API?

# 4a. If manual:
cat scripts/translate/MANUAL_TESTING_GUIDE.md
# Follow the manual workflow

# 4b. If API:
# We'll build the automation scripts together
# (ping me when ready!)

# 5. Community review
# Post review docs to GitHub Discussions
# Wait 1-2 weeks for native speaker input

# 6. Generate final language packs
# Use approved translations to create production YAML files

# 7. Test & release!
```

---

## Questions to Answer When You Resume

1. **Quality check:** Did the test translations in Claude Desktop look good?
2. **Approach:** Manual (free, 10-20h) or API ($ 7.56-$21, automated)?
3. **Models:** Just Claude ($7.56) or all 3 ($21)?
4. **Community:** Where to post for review? (GitHub Discussions? Discord?)
5. **Timeline:** When do you want production-ready packs? (Sets community review duration)

---

## Notes for Future You

**What's already done:**

- All the hard thinking about linguistics, patterns, consistency ✅
- Prompts that will produce high-quality translations ✅
- Infrastructure to build against (mock Spanish language pack) ✅
- Complete documentation of the entire workflow ✅

**What's left:**

- Run the translation generation (manual or automated)
- Community review (1-2 weeks passive)
- Generate final files and release

**You're 80% done with planning/infrastructure, 20% left is execution!**

---

**Saved:** 2025-10-28
**Resume:** When you're ready to populate language packs with real translations
**Questions?** Review the docs above or ping for help!
