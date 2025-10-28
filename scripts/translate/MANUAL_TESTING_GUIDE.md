# Manual Testing Guide - Claude Desktop

**Purpose:** Test translation prompts in Claude Desktop before committing to API costs
**Estimated Time:** 5-10 minutes per translation
**Cost:** $0 (included in Claude Pro)

---

## Testing Workflow

### Step 1: Choose a Test Term

Start with these recommended test terms (in order):

1. **`def`** - EASY, ACTION keyword (Spanish)
2. **`True`** - EASY, VALUE constant (Spanish)
3. **`isinstance`** - MEDIUM, builtin function (Spanish)
4. **`return`** - EASY, ACTION keyword (Arabic) - test RTL language
5. **`lambda`** - HARD, abstract concept (Chinese) - test non-Latin script

### Step 2: Get the Prompt

Each prompt is in `test-cases/` directory:
- `test-cases/01-def-spanish.md` - Complete prompt ready to copy
- `test-cases/02-true-spanish.md`
- `test-cases/03-isinstance-spanish.md`
- etc.

### Step 3: Copy to Claude Desktop

1. Open Claude Desktop (or claude.ai)
2. Start a new conversation
3. Copy the ENTIRE content of the test case file
4. Paste into Claude Desktop
5. Send

### Step 4: Review Claude's Response

Claude will respond with XML-structured translation. Look for:

**Quality Indicators:**
- ✅ Did it provide 3-5 translation options?
- ✅ Did it explain reasoning clearly?
- ✅ Is the recommended translation sensible?
- ✅ High/Medium/Low confidence rating?
- ✅ Did it consider CS education usage?

**Red Flags:**
- ❌ Only 1 option considered
- ❌ No explanation of reasoning
- ❌ Literal word-for-word translation (not concept-based)
- ❌ Didn't check consistency with related terms
- ❌ Translation is too long (>3 words)

### Step 5: Save the Response

1. Copy Claude's entire response
2. Save to `test-results/01-def-spanish-response.xml`
3. Mark test as complete in tracking checklist

### Step 6: Parse Key Information

From Claude's XML response, extract:

```
Term: def
Language: Spanish
Recommended: {translation}
Form: {infinitive/noun/etc}
Confidence: {HIGH/MEDIUM/LOW}
Rationale: {brief summary}
```

Save to `test-results/summary.md`

---

## Tracking Checklist

**Test Cases Completed:**

- [ ] 01 - `def` → Spanish (ACTION keyword, EASY)
- [ ] 02 - `True` → Spanish (VALUE constant, EASY)
- [ ] 03 - `isinstance` → Spanish (builtin, MEDIUM)
- [ ] 04 - `return` → Arabic (ACTION keyword, RTL test)
- [ ] 05 - `lambda` → Chinese (abstract concept, non-Latin)

**Goal:** Complete at least 2-3 to validate prompt quality

---

## What You're Testing

1. **Prompt clarity** - Does Claude understand what we're asking?
2. **Reasoning depth** - Does it think through options systematically?
3. **Output format** - Does XML structure work correctly?
4. **Translation quality** - Are recommendations sensible?
5. **Consistency guidance** - Does it reference pattern matching?

---

## Decision Points After Testing

After completing 2-3 test translations:

**If quality is HIGH:**
- ✅ Prompts are ready for production
- ✅ Can proceed with API batch processing ($7.56)
- ✅ Or continue manually if preferred

**If quality is MEDIUM:**
- ⚠️ Iterate on prompts (adjust examples, guidance)
- ⚠️ Test 2-3 more terms
- ⚠️ Identify what's missing

**If quality is LOW:**
- ❌ Prompts need significant revision
- ❌ Review linguistic standards
- ❌ Add more detailed examples

---

## Next Steps After Manual Testing

**Option A: Continue Manually (Free)**
- Use this same approach for all 420 translations
- Time: 10-20 hours total
- Cost: $0

**Option B: Switch to API (Automated)**
- Prompts validated, run batch processing
- Time: 30 min setup + 24h wait
- Cost: $7.56

**Option C: Hybrid**
- Do Spanish/Arabic manually (already done, no new costs)
- Use API for Chinese/Hindi
- Cost: ~$4 (half the batch)

---

## Tips for Manual Testing

1. **One conversation per term** - Start fresh conversation for each test
   - Prevents Claude from being influenced by previous translations
   - Ensures consistent prompt interpretation

2. **Copy the FULL prompt** - Don't skip sections
   - The examples and context are important
   - Complete prompt ensures best quality

3. **Don't guide Claude** - Let it work through the framework
   - Don't say "I think it should be X"
   - See what it comes up with independently

4. **Look for patterns** - After 2-3 tests, check:
   - Is Claude consistently using the priority framework?
   - Are confidence ratings accurate?
   - Is reasoning clear and helpful?

5. **Save everything** - You'll want to reference these later
   - Successful translations inform the rest
   - Failed attempts help us fix prompts

---

Ready to test! Start with `test-cases/01-def-spanish.md` 👇
