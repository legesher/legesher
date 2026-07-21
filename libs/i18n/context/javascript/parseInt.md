# JavaScript Builtin: `parseInt` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`parseInt` is the global function that reads a string and extracts a whole-number `Number` from its leading digits — `parseInt("42")` → `42`. Unlike `Number`, it reads as far as the digits go and ignores trailing non-numeric text.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Read a whole number out of text
let n = parseInt("42"); // 42
```

**What this does:** Calls the global `parseInt` function to scan the text `"42"` and return the integer `42` as a `Number`.

### Example 2: Common Pattern

```javascript
// Extract leading digits, ignore the rest
let width = parseInt("42px");   // 42
let count = parseInt("7 items"); // 7
```

**What this does:** The common use of `parseInt` is pulling a whole number off the front of mixed text — reading digits until a non-digit, then stopping. This is why it succeeds on `"42px"` where `Number("42px")` fails.

### Example 3: Edge Case

```javascript
// parseInt truncates at the decimal point — it reads INTEGERS only
parseInt("3.99"); // 3   (stops at the dot, no rounding)
parseInt("abc");  // NaN (no leading digits at all)
```

**What this shows:** `parseInt` extracts an *integer*: it reads leading digits and stops at the decimal point, discarding the fraction (no rounding). With no leading digits it returns `NaN`. For a fractional result use `parseFloat` (see Cross-References).

---

## Pattern Classification

**This term is:** GLOBAL FUNCTION (text-to-number parser)

**Similar terms in this pattern:**

1. `parseFloat` - Sibling parser; reads a *decimal* number from text instead of an integer
2. `Number` - Also converts to a number, but the whole value must be numeric (no leading-digit extraction)
3. `String` - The inverse direction: turns a value into text rather than reading a number out of text

**Pattern rule:** Global functions name *actions* — translate `parseInt` as a verb phrase ("parse/read an integer from text"), consistent with `parseFloat`. It is an action, unlike the type nouns `Number`/`String`.

---

## Etymology (Brief)

**English Origin:** "parse" (Latin *pars* = "part") + "int" (Latin *integer* = "whole")

**Root meaning:** "Parse" originally meant to break a sentence into its parts of speech (*pars orationis*); in computing it means to analyze text and extract structured meaning. "Int" is short for "integer," a whole number.

**Why JavaScript uses this:** The name says exactly what the function does — it *parses* text to pull out an *integer*. The verb "parse" signals an analytical read of the characters, not a wholesale type conversion.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`parseInt` is a global function that reads a string from the left and builds a whole number out of the leading digit characters. It scans character by character: as long as it sees digits it keeps going, and at the first non-digit it stops and returns the integer gathered so far. So `parseInt("42px")` returns `42`, and `parseInt("7 items")` returns `7`. If the string has no leading digits, it returns `NaN` (not-a-number).

Two facts define it against its neighbors. First, it is a *parser*, not a whole-value converter: where `Number("42px")` yields `NaN` because the entire text is not a clean number, `parseInt("42px")` happily returns `42` from the front. Second, it produces an *integer*: it stops at a decimal point, so `parseInt("3.99")` is `3` — it truncates the fraction with no rounding. For a fractional value you use the sibling `parseFloat`.

Conceptually `parseInt` names an *action*: "read/extract a whole number from text." It is a verb, which sets it apart from the type nouns `Number` and `String`. The result it returns is a `Number` (JavaScript's one numeric type), but the function's own meaning is the act of parsing.

**Key behaviors:**

1. **Leading-digit extraction:** reads digits from the start and stops at the first non-digit, returning what it gathered (or `NaN` if none).
2. **Integer result:** stops at the decimal point and discards the fraction — no rounding; contrast `parseFloat`.
3. **An action, not a type:** `parseInt` names the parsing operation; it *returns* a `Number` but is itself a verb.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase — commands an action ("parse an integer from text")
- **Action vs State:** ACTION — it does something (reads and extracts), it does not name a value
- **Temporal aspect:** One-time operation performed on the given text

### Recommended Form

**Primary recommendation:** Translate as a verb phrase combining "parse/read/extract" with the word for "integer / whole number" — the same "integer" sense used elsewhere in your CS terminology. Keep the *verb* nature explicit so it contrasts with the noun `Number`, and keep the "parse" element consistent with `parseFloat`.

**Forms to AVOID:**

- ❌ A bare type noun ("integer") — that is `Number`'s territory; `parseInt` is an action
- ❌ A generic "convert to number" that loses the *integer* and *parse-from-text* senses
- ❌ A word implying rounding — `parseInt` truncates at the decimal, it does not round

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (in the "parse" element)

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "parse" as grammatical analysis of a sentence (school grammar)
- ❌ Meaning 2: "integer" as a general word for "whole/complete/intact"
- ✅ Meaning 3: **READ/EXTRACT A WHOLE NUMBER FROM TEXT** — analyze the characters and pull out an integer

**Example:**

English "parse the integer" can suggest:

1. "Parse the sentence into subject and verb" (grammar) ❌
2. "Keep the loaf whole/intact" (general "whole") ❌
3. "Read the number out of the string" (extract an integer from text) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the act of reading an integer out of text — not sentence grammar and not the general sense of "whole/intact."**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `parseInt`, check these translations:**

- [ ] `parseFloat` - Sibling parser; the "parse" element MUST match, differing only in integer vs. decimal
- [ ] `Number` - The value type this returns; keep `parseInt` a verb distinct from that noun
- [ ] `String` - The input is text; the "text" idea should match your `String` translation

**Consistency rule:**

`parseInt` and `parseFloat` are a matched pair. Whatever word you choose for "parse/read from text" must be identical in both, so the only difference a learner sees is "integer" vs. "decimal." Keep both as verb phrases, clearly distinct from the type noun `Number`.

### Functional relationships

**This term works WITH:**

1. **`parseInt` + text**: reading a whole number out of a string

```javascript
parseInt("100 dollars"); // 100
```

**Common pairing:**

```javascript
// Parse user text, then compute with the resulting Number
let entered = "20 units";
let doubled = parseInt(entered) * 2; // 40
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** Both parts ("parse," "integer") have known equivalents, but combining them into a natural, compact verb phrase — while (a) keeping it a verb distinct from the `Number` noun, (b) matching `parseFloat` exactly on the shared "parse" element, and (c) preserving the truncation (not rounding) nuance — is a genuine composition task. Some languages lack a crisp single verb for "parse," making phrasing a judgment worth review.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures READING/EXTRACTING a whole number FROM TEXT (not grammar, not "intact")?
- [ ] Conveys the integer result (truncates at the decimal, no rounding)?
- [ ] Distinct from whole-value `Number` conversion?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb phrase, not a bare noun)?
- [ ] Correct form (action, one-time operation)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`parseInt` is lowercase-initial)?

### 3. Consistency

- [ ] "parse" element identical to `parseFloat`?
- [ ] Kept a verb, distinct from the `Number` noun?
- [ ] "integer" sense matches your CS terminology elsewhere?

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
term: parseInt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended verb phrase captures "read/extract an integer from text" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm the "parse" element matches `parseFloat` and the whole stays distinct from the `Number` noun.

**Alternatives considered:**

List the candidate phrasings weighed (verbs for "parse," words for "integer") and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no crisp verb for "parse," compactness, truncation nuance) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
