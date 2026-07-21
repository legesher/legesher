# JavaScript Builtin: `parseFloat` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`parseFloat` is the global function that reads a string and extracts a decimal `Number` from its leading numeric characters — `parseFloat("3.14")` → `3.14`. It is the sibling of `parseInt`, differing only in that it keeps the fractional part.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Read a decimal number out of text
let x = parseFloat("3.14"); // 3.14
```

**What this does:** Calls the global `parseFloat` function to scan the text `"3.14"` and return the decimal value `3.14` as a `Number`.

### Example 2: Common Pattern

```javascript
// Extract a leading decimal, ignore the rest
let price = parseFloat("3.99 USD"); // 3.99
let temp = parseFloat("36.6°C");    // 36.6
```

**What this does:** The common use of `parseFloat` is pulling a decimal number off the front of mixed text — reading digits and one decimal point until the number ends, then stopping. It succeeds on `"3.99 USD"` where `Number("3.99 USD")` fails.

### Example 3: Edge Case

```javascript
// parseFloat KEEPS the fraction — this is the difference from parseInt
parseFloat("3.99"); // 3.99  (parseInt("3.99") would be 3)
parseFloat("abc");  // NaN   (no leading number at all)
```

**What this shows:** `parseFloat` reads a full decimal number, including the part after the point — the one behavior that distinguishes it from `parseInt`, which stops at the decimal. With no leading number it returns `NaN`.

---

## Pattern Classification

**This term is:** GLOBAL FUNCTION (text-to-number parser)

**Similar terms in this pattern:**

1. `parseInt` - Sibling parser; reads a *whole number* from text and drops the fraction
2. `Number` - Also converts to a number, but the whole value must be numeric (no leading extraction)
3. `String` - The inverse direction: turns a value into text rather than reading a number out of text

**Pattern rule:** Global functions name *actions* — translate `parseFloat` as a verb phrase ("parse/read a decimal from text"), consistent with `parseInt`. It is an action, unlike the type nouns `Number`/`String`.

---

## Etymology (Brief)

**English Origin:** "parse" (Latin *pars* = "part") + "float" (short for "floating-point")

**Root meaning:** "Parse" originally meant to break a sentence into its parts of speech; in computing it means to analyze text and extract structured meaning. "Float" is short for "floating-point," the standard representation of decimal numbers where the point "floats" to suit the magnitude.

**Why JavaScript uses this:** The name says what the function does — it *parses* text to pull out a *floating-point* (decimal) number. "Parse" signals an analytical, character-by-character read rather than a wholesale conversion.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`parseFloat` is a global function that reads a string from the left and builds a decimal number out of the leading numeric characters — digits, a single decimal point, and scientific notation like `1.5e3`. It scans until the number ends, then stops and returns what it gathered. So `parseFloat("3.99 USD")` returns `3.99`, and `parseFloat("36.6°C")` returns `36.6`. With no leading number it returns `NaN`.

It sits between its two neighbors. Against `Number`: `parseFloat` is a *parser* that extracts a leading number and tolerates trailing junk, whereas `Number("3.99 USD")` yields `NaN` because the whole text must be numeric. Against `parseInt`: they are the same operation except `parseFloat` *keeps the fractional part* while `parseInt` stops at the decimal point. `parseFloat("3.99")` is `3.99`; `parseInt("3.99")` is `3`. This single difference — decimal vs. integer — is the whole distinction a learner must hold.

Conceptually `parseFloat` names an *action*: "read/extract a decimal number from text." It is a verb, unlike the type nouns `Number` and `String`. The value it returns is a `Number` (JavaScript's one numeric type), but the function's own meaning is the act of parsing.

**Key behaviors:**

1. **Leading-number extraction:** reads digits, a decimal point, and exponent notation from the start; stops when the number ends (or `NaN` if none).
2. **Keeps the fraction:** returns the full decimal value — the defining contrast with `parseInt`.
3. **An action, not a type:** `parseFloat` names the parsing operation; it *returns* a `Number` but is itself a verb.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase — commands an action ("parse a decimal from text")
- **Action vs State:** ACTION — it does something (reads and extracts), it does not name a value
- **Temporal aspect:** One-time operation performed on the given text

### Recommended Form

**Primary recommendation:** Translate as a verb phrase combining "parse/read/extract" with the word for "decimal / floating-point number." Keep the *verb* nature explicit so it contrasts with the noun `Number`, and keep the "parse" element **identical** to your `parseInt` translation so the only visible difference is decimal vs. integer.

**Forms to AVOID:**

- ❌ A bare type noun ("decimal / float") — that loses the *parse-from-text* action
- ❌ A generic "convert to number" that erases the *decimal* and *extract-from-text* senses
- ❌ A "parse" word that differs from the one used in `parseInt` — the pair must match

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (in both elements)

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "parse" as grammatical analysis of a sentence
- ❌ Meaning 2: "float" as staying on water, or a parade float
- ✅ Meaning 3: **READ/EXTRACT A DECIMAL NUMBER FROM TEXT** — analyze the characters and pull out a floating-point number

**Example:**

English "parse the float" can suggest:

1. "Parse the sentence into parts of speech" (grammar) ❌
2. "The boat floats on the lake" (staying on water) ❌
3. "Read the decimal number out of the string" (extract a float from text) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the act of reading a decimal number out of text — not sentence grammar and not any water/parade sense of "float."**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `parseFloat`, check these translations:**

- [ ] `parseInt` - Sibling parser; the "parse" element MUST match, differing only in decimal vs. integer
- [ ] `Number` - The value type this returns; keep `parseFloat` a verb distinct from that noun
- [ ] `String` - The input is text; the "text" idea should match your `String` translation

**Consistency rule:**

`parseFloat` and `parseInt` are a matched pair. The word for "parse/read from text" must be identical in both, so the only difference a learner sees is "decimal" vs. "integer." Keep both as verb phrases, clearly distinct from the type noun `Number`. However you rendered "floating-point" here should also be recognizable against the `float`-family sense used across your CS terms.

### Functional relationships

**This term works WITH:**

1. **`parseFloat` + text**: reading a decimal number out of a string

```javascript
parseFloat("19.99 each"); // 19.99
```

**Common pairing:**

```javascript
// Parse user text, then compute with the resulting Number
let entered = "3.5 hours";
let doubled = parseFloat(entered) * 2; // 7
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** Like `parseInt`, this is a composition task: pairing a verb for "parse" with a word for "decimal/floating-point," keeping it a verb distinct from the `Number` noun, and matching the shared "parse" element to `parseInt` exactly. "Floating-point" has less settled native wording than "integer" in some languages (often a loanword or "decimal"), which nudges the phrasing decision toward review.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures READING/EXTRACTING a decimal number FROM TEXT (not grammar, not water/parade)?
- [ ] Conveys that the fraction is kept (the contrast with `parseInt`)?
- [ ] Distinct from whole-value `Number` conversion?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb phrase, not a bare noun)?
- [ ] Correct form (action, one-time operation)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`parseFloat` is lowercase-initial)?

### 3. Consistency

- [ ] "parse" element identical to `parseInt`?
- [ ] Kept a verb, distinct from the `Number` noun?
- [ ] "decimal / floating-point" sense matches your CS terminology elsewhere?

### 4. Usability

- [ ] Short enough (verb phrase, not a sentence)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL scripts)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: parseFloat
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended verb phrase captures "read/extract a decimal from text" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm the "parse" element matches `parseInt` and the whole stays distinct from the `Number` noun.

**Alternatives considered:**

List the candidate phrasings weighed (verbs for "parse," words for "decimal/floating-point") and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no settled "floating-point" word, matching `parseInt`, compactness) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
