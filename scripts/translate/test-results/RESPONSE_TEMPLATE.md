# Test Results - Response Template

Use this template to save Claude Desktop's responses.

---

## Test Case: {NUMBER} - `{TERM}` → {LANGUAGE}

**Date Tested:** {DATE}
**Claude Version:** Claude 3.5 Sonnet (Desktop)

### Claude's Full Response

```xml
[PASTE CLAUDE'S COMPLETE XML RESPONSE HERE]
```

### Quick Summary

**Recommended Translation:** {translation}
**Form:** {infinitive/noun/adjective/etc}
**Confidence:** {HIGH/MEDIUM/LOW}

### Key Points from Reasoning

**Options Considered:**
1. {option_1} - {brief rationale}
2. {option_2} - {brief rationale}
3. {option_3} - {brief rationale}

**Why This One Won:**
{1-2 sentence summary of final_decision}

**CS Education Research:**
{What Claude found about how this is taught in target language}

### Your Evaluation

**Quality Assessment:** {EXCELLENT | GOOD | NEEDS_WORK | POOR}

**What worked well:**
-
-

**Concerns or questions:**
-
-

**Action Items:**
- [ ] Accept translation as-is
- [ ] Request clarification on: ___
- [ ] Test alternative: ___
- [ ] Consult native speaker
- [ ] Revise prompt based on: ___

---

## Example (for reference)

## Test Case: 01 - `def` → Spanish

**Date Tested:** 2025-10-28
**Claude Version:** Claude 3.5 Sonnet (Desktop)

### Claude's Full Response

```xml
<translation_result>
  <term>def</term>
  <target_language>Spanish</target_language>
  <recommended_translation>
    <translation>definir</translation>
    <form>infinitive</form>
    <confidence>HIGH</confidence>
  </recommended_translation>
  [... rest of XML ...]
</translation_result>
```

### Quick Summary

**Recommended Translation:** definir
**Form:** infinitive
**Confidence:** HIGH

### Key Points from Reasoning

**Options Considered:**
1. definir - Direct translation of "define"
2. función - Names what it creates
3. crear - Means "to create"

**Why This One Won:**
Technically accurate, matches CS education usage across Spanish-speaking regions, consistent with ACTION keyword pattern (infinitive form).

**CS Education Research:**
Spanish CS textbooks consistently use "definir una función" (define a function). Standard across Spain, Mexico, Argentina.

### Your Evaluation

**Quality Assessment:** EXCELLENT

**What worked well:**
- Comprehensive reasoning with 3+ options
- Researched CS education usage
- Considered consistency with related terms
- Clear explanation of why alternatives were rejected

**Concerns or questions:**
- None - this is a strong, well-reasoned translation

**Action Items:**
- [x] Accept translation as-is
