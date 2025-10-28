# Quick Start - Manual Testing in Claude Desktop

**Ready to test? Follow these 4 steps:**

---

## Step 1: Open Test Case File

Navigate to: `scripts/translate/test-cases/`

**Start with:**
- `01-def-spanish.md` - Easiest, ACTION keyword
- `02-true-spanish.md` - VALUE constant (different pattern)

---

## Step 2: Copy to Claude Desktop

1. Open the test case file (e.g., `01-def-spanish.md`)
2. **Select ALL content** (Cmd+A)
3. **Copy** (Cmd+C)
4. Open **Claude Desktop** or [claude.ai](https://claude.ai)
5. Start a **new conversation** (important: fresh context)
6. **Paste** the entire prompt (Cmd+V)
7. **Send**

**⏱️ Expected time:** Claude will think for 20-60 seconds

---

## Step 3: Save Claude's Response

1. Claude will respond with XML-structured translation
2. **Select and copy** Claude's entire response
3. Create new file: `test-results/01-def-spanish-response.md`
4. **Paste** Claude's response
5. Optional: Use `test-results/RESPONSE_TEMPLATE.md` for structured notes

---

## Step 4: Quick Evaluation

**Look for these quality indicators:**

✅ **Good signs:**
- Provided 3-5 translation options
- Clear reasoning for each option
- Explained why alternatives were rejected
- Referenced CS education usage
- HIGH confidence rating
- Checked consistency with related terms

❌ **Red flags:**
- Only 1 option considered
- No explanation of reasoning
- Literal word-for-word translation
- Didn't research CS education
- Translation is too long (>3 words)

---

## What's Next?

**After testing 2-3 terms:**

### If quality is EXCELLENT ✅
→ Prompts are ready! You can:
- **Option A:** Continue manually (free, 10-20 hours for all 420)
- **Option B:** Use API for automation ($7.56, 30 min setup)

### If quality is GOOD ⚠️
→ Minor tweaks needed:
- Identify what could be improved
- Adjust prompts slightly
- Test 1-2 more terms

### If quality is POOR ❌
→ Significant revision needed:
- Review what went wrong
- Update linguistic standards
- Add more examples
- Re-test

---

## Test Case Priority

**Recommended testing order:**

1. ✅ **`def` → Spanish** (EASY, ACTION keyword, test basic flow)
2. ✅ **`True` → Spanish** (EASY, VALUE constant, test different pattern)
3. **`isinstance` → Spanish** (MEDIUM, builtin, test compound terms)
4. **`return` → Arabic** (EASY, RTL language test)
5. **`lambda` → Chinese** (HARD, abstract concept, non-Latin script)

**Goal:** Test at least 2-3 to validate prompt quality

---

## Files You'll Create

```
test-results/
├── 01-def-spanish-response.md          ← Claude's XML response
├── 02-true-spanish-response.md         ← Claude's XML response
├── 03-isinstance-spanish-response.md   ← (if testing this one)
└── summary.md                          ← Your overall evaluation
```

---

## Tips for Success

**1. Fresh conversation each time**
- Start new conversation for each test
- Prevents Claude from being influenced by previous translations

**2. Copy the FULL prompt**
- Don't skip sections
- Examples and context are important

**3. Don't guide Claude**
- Let it work through the framework independently
- Don't say "I think it should be X"

**4. Save everything**
- You'll reference these later
- Successful translations inform the rest

**5. Look for patterns**
- After 2-3 tests, check:
  - Is reasoning consistent?
  - Are confidence ratings accurate?
  - Is CS education research happening?

---

## Need Help?

**If Claude's response is confusing:**
- Check that you copied the entire prompt
- Make sure you started a fresh conversation
- Review the example in the prompt template

**If you're unsure about translation quality:**
- Compare to the `def` → Spanish example in the prompt
- Check if reasoning is detailed and logical
- Verify that multiple options were considered

**If you want to test more terms:**
- Use the same format as `01-def-spanish.md`
- Fill in context for the new term
- Adjust linguistic guidance as needed

---

**Ready? Start with:** `test-cases/01-def-spanish.md` 🚀

Copy that file into Claude Desktop and see what you get!
