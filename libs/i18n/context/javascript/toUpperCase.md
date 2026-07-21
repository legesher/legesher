# JavaScript Member: `toUpperCase` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String
**Receivers (live in JEJ today):** String — this member is String-only in full JS too, so no widening is expected
**Ships in JEJ:** yes (member; String-only)
**Difficulty:** MEDIUM

---

## Quick Summary

`toUpperCase` is a member method that returns a **new string with every letter converted to its uppercase form**. It is called as `text.toUpperCase()`. Characters with no case (digits, punctuation, and letters in non-cased scripts) are returned unchanged. **Casing caveat:** many writing systems — Arabic, Hebrew, most Indic and East Asian scripts — have no upper/lower distinction, so "uppercase" is a concept that only fully applies to bicameral scripts; flag this for the reviewer.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Convert to uppercase
let word = "hello";
let loud = word.toUpperCase();   // "HELLO"
```

**What this does:** Calls `toUpperCase` on `"hello"`, returning a new string `"HELLO"`. The original is unchanged. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// Case-insensitive comparison
let input = "Yes";
let matches = input.toUpperCase() === "YES";   // true
```

**What this does:** Normalises case before comparing — the everyday "compare ignoring case" pattern. Uppercasing both sides removes case differences.

### Example 3: Edge Case

```javascript
// A bare `toUpperCase` is NOT this member — only `x.toUpperCase()` is
let toUpperCase = "label";           // an ordinary variable named toUpperCase
let real = "hi".toUpperCase();       // THIS is the member  -> "HI"
```

**What this shows:** `toUpperCase` counts as this member **only** in property position before the call (`"hi".toUpperCase()`). A standalone variable happening to be named `toUpperCase` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `toLowerCase` - The mirror member: converts to lowercase (must stay DISTINCT)
2. `charAt` - Also a String member returning text
3. `slice` - Also a String member returning a new string

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound — "to" + "upper case."

**Root meaning:** "Convert *to* upper case." "Upper case" comes from typesetting: capital letters were stored in the *upper* type case, small letters in the *lower* case.

**Why JavaScript uses this:** Text often needs normalising to capitals for display or comparison. `toUpperCase` is the "make it all capitals" transform. The name carries a Latin-script printing metaphor that does not transfer to every writing system — see the caveat below.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`toUpperCase` is a method read from a string with the `string.toUpperCase()` shape. It returns a **new string** in which each cased letter is replaced by its uppercase equivalent, following Unicode case rules. Uncased characters pass through unchanged, and the original string is not modified.

Critically, `toUpperCase` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"hi".toUpperCase()` is the member; a learner's own variable named `toUpperCase` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The translation challenge is **conceptual, not receiver-based** (String-only, no widening). "Uppercase" is a property of *bicameral* scripts — Latin, Greek, Cyrillic, Armenian. **Unicameral scripts (Arabic, Hebrew, Chinese, Japanese, Korean, Devanagari, Thai, and many more) have no case at all**, so a literal "big letters" translation may be meaningless or misleading for a speaker of those languages. The native term still needs to name the *operation* (the same one English calls uppercasing), even though it is a no-op on that speaker's own script. Reviewers for non-cased-script languages should confirm the chosen word names the transform sensibly (often via a borrowed or descriptive phrase) rather than implying their script has capitals.

**Key behaviors:**

1. **Method, not property:** called as `x.toUpperCase()` with `()`.
2. **Returns a new string:** the original is unchanged; uncased characters pass through.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `toUpperCase` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning an uppercased string
- **Action vs State:** ACTION - it transforms and returns text
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"convert to capital / uppercase form"** — the transform to majuscule letters. For non-cased-script languages, use the established descriptive or borrowed phrase for "uppercase" rather than inventing a "big letters" reading.

**Forms to AVOID:**

- ❌ A word meaning **"louder / shouting"** - a connotation of caps, not the operation
- ❌ The **same word chosen for `toLowerCase`** - they must stay distinct under Rule 2
- ❌ A noun form - `toUpperCase` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

MILD

**If MILD, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Upper" as in higher / above
- ❌ Meaning 2: "Case" as in a legal case or a container
- ✅ Meaning 3: **"CONVERT LETTERS TO THEIR CAPITAL FORM"** — majuscule text

**Example:**

English "to upper case" can suggest:

1. "move it to the **upper** shelf" (higher position) ❌
2. "the **case** goes to court" (a legal matter) ❌
3. "turn `hello` into `HELLO`" (capitalise the letters) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: convert letters to their capital form — while acknowledging that for non-cased scripts this names an operation with no visible effect on that script.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `toUpperCase`, check these translations:**

- [ ] `toLowerCase` - The exact mirror; must be a DISTINCT native word (and ideally a symmetric pair) or reversibility breaks
- [ ] `charAt` - Another String member returning text
- [ ] `slice` - Another String member returning a new string

**Consistency rule:**

`toUpperCase` and `toLowerCase` are a matched pair and both live in JEJ today. Under Rule 2 they must map to two clearly different native words. Ideally they form a visible pair (the same base word with an "upper" vs "lower" / "capital" vs "small" modifier), so learners see them as opposites — but the two forms must never collide.

### Functional relationships

**This term works WITH:**

1. **`toUpperCase` + comparison**: case-insensitive matching

```javascript
let a = "OK";
let b = "ok";
let same = a.toUpperCase() === b.toUpperCase();   // true
```

**Common pairing:**

```javascript
// display a heading in caps
let title = "chapter one";
let heading = title.toUpperCase();   // "CHAPTER ONE"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The operation is simple and String-only (no widening), but the *concept* of case does not exist in many target languages' own scripts, so the native term must name a transform that is a no-op for its own speakers — a genuine cross-cultural mismatch. Add the requirement to pair symmetrically with, yet stay distinct from, `toLowerCase`, and this sits solidly at MEDIUM.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.** (Non-cased-script languages should be reviewed with extra care.)

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (convert letters to capital form)?
- [ ] Reads correctly for the String receiver?
- [ ] For non-cased scripts, names the operation sensibly (no false "capitals" claim)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("to capital / uppercase")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `toLowerCase`, ideally a symmetric pair?
- [ ] Aligns with related String members?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (max ~3 words for members)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities (esp. non-cased scripts)?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL scripts)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: toUpperCase
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "convert to capital / uppercase form" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and, for non-cased scripts, note how the term names the operation without implying the script has capitals.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "louder / bigger" or collided with `toLowerCase`.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (case absent from the target script, symmetric-pairing requirement) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
