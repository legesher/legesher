# JavaScript Keyword: `if` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `if` keyword tests a condition and executes a block of code only when that condition is truthy. It is the fundamental building block for conditional logic in JavaScript, letting a program make decisions and branch its execution based on runtime values.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Check whether a number is positive
let x = 5;
if (x > 0) {
  console.log("Positive number");
}
```

**What this does:** Evaluates whether `x` is greater than `0`. If true, logs "Positive number". If false, the block is skipped and execution continues after it.

### Example 2: Common Pattern

```javascript
// Validate an age before granting access
let age = 18;
if (age >= 18) {
  console.log("Access granted");
  let allowEntry = true;
}
```

**What this does:** Tests whether `age` meets the minimum. When the condition is true, both statements inside the `{ }` block run. This shows how one `if` can guard several lines.

### Example 3: Edge Case

```javascript
// Empty and zero values are "falsy" in a condition
let data = [];
if (data.length) {
  console.log("Has data");
}
// This does not log: data.length is 0, which is falsy
```

**What this shows:** JavaScript's `if` does not require an explicit boolean. `0`, `""`, `null`, `undefined`, `NaN`, and `false` are all "falsy"; everything else is "truthy". This truthiness evaluation is a core idiom.

---

## Pattern Classification

**This term is:** STATE KEYWORD

**Similar terms in this pattern:**

1. `else` - The alternative clause paired with `if`
2. `while` - Conditional loop that repeats while a condition holds
3. `for` - Loop whose middle clause is a condition tested each pass

**Pattern rule:** All conditional-test keywords should use a conjunction or present-tense form in the target language, NOT an imperative verb form. They describe a state/condition, not a command.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *gif* meant "if, whether, though" — expressing condition or supposition. Related to German *ob* (whether) and Dutch *of* (if/whether).

**Why JavaScript uses this:** `if` is the universal English conditional particle, immediately recognizable and shared with C, Java, and Python. JavaScript inherited the C-family `if (condition) { … }` shape, keeping the plain English word rather than a cryptic symbol for basic conditionals.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `if` keyword implements conditional branching in JavaScript's control flow. It evaluates the parenthesized expression (the "condition"), coerces it to a boolean, and — when the result is truthy — executes the `{ }` block that follows. When the result is falsy, the engine skips that block entirely and resumes with the next statement.

The condition can be any expression that produces a value. JavaScript uses "truthiness": `0`, `-0`, `""`, `null`, `undefined`, `NaN`, and `false` are falsy and behave like `false` in a condition. Every other value — non-zero numbers, non-empty strings, objects, arrays — is truthy.

An `if` can stand alone or combine with `else` (and chained `else if`) to build multi-branch decisions. Unlike Python, JavaScript marks the conditional body with `{ }` braces rather than indentation, and requires the condition itself to be wrapped in parentheses.

**Key behaviors:**

1. **Evaluated once:** The condition is evaluated a single time when the `if` line runs. If falsy, the whole block is skipped without executing anything inside it.
2. **Truthiness coercion:** Any value may be used as a condition; the engine coerces it to `true` or `false` following the falsy-value rules above.
3. **Brace-delimited block:** The statements inside `{ }` belong to the conditional. (A single statement may omit braces in full JS, but the JEJ subset uses braces for clarity.)

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Subordinating conjunction introducing a conditional clause
- **Action vs State:** STATE - tests and describes a condition, does not perform an action
- **Temporal aspect:** Immediate present - evaluates the condition at the moment of execution

### Recommended Form

**Primary recommendation:** Use the target language's natural conditional word/particle — the everyday equivalent of "if". This is NOT a verb and should NOT take verb forms (infinitive or imperative).

**Forms to AVOID:**

- ❌ Imperative verb form - `if` is not a command
- ❌ Infinitive verb - `if` does not express an action "to do"
- ❌ Question form - `if` states a condition, it does not ask a query

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Provided that, on condition that" (formal permission)
- ❌ Meaning 2: "Whether" (introducing an indirect question — "I don't know if…")
- ✅ Meaning 3: **HYPOTHETICAL CONDITIONAL** — "in the case that X is true, then Y happens"

**Example:**

English "if" can mean:

1. "Come to the party **if** you want" (permission/option) ❌
2. "Tell me **if** you see John" (whether — interrogative) ❌
3. "**If** temperature > 100, turn off heater" (conditional logic) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: hypothetical conditional testing, NOT permission or an indirect question.**

Many languages distinguish conditional "if" (if X then Y) from interrogative "if/whether" (I wonder if X). Use the CONDITIONAL form. Where the two are homonyms but grammatically different, make sure the conditional reading is the one your choice conveys.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `if`, check these translations:**

- [ ] `else` - Must be its natural alternative/opposite ("otherwise")
- [ ] `while` - Should share the conditional particle/conjunction structure
- [ ] `for` - Its middle clause is a condition; keep the control-flow register consistent

**Consistency rule:**

All conditional/test keywords (`if`, `while`) should use the same grammatical category in your target language. If `if` is a conjunction, keep the others conjunction-like. Do NOT mix verb forms with conjunction forms.

**Example:**

If you translate `if` as a conjunction, then:

- `else` should read as its natural complement
- `while` should use a conjunction form
- NOT: `if` conjunction + `while` verb form (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`if` + `else`**: The complete two-branch conditional

```javascript
let x = 5;
if (x > 0) {
  console.log("positive");
} else {
  console.log("zero or negative");
}
```

2. **`if` + boolean operators** (`&&`, `||`, `!`): Compound conditions

```javascript
let age = 20;
let hasLicense = true;
if (age >= 18 && hasLicense) {
  console.log("Can drive");
}
```

**Common pairing:**

```javascript
// if frequently appears with comparison operators
let x = 5;
if (x === 5) { /* strict equality */ }
if (x !== 0) { /* strict inequality */ }
if (x > 10)  { /* greater than */ }
if (!x)      { /* negation of truthiness */ }
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have a direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `if`

- Universal programming concept
- Every natural language has a conditional particle or conjunction
- Well-established in CS education globally
- Minimal cultural or linguistic complexity

**For this term:** EASY

**Rationale:** The conditional "if" concept exists in every human language. No language lacks a way to express "if X is true, then do Y." Translation is straightforward: find the target language's standard conditional word. Low risk of error.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

If you're uncertain, you may be overthinking it or reaching for the wrong word type (a verb instead of a conjunction). Confirm you are using the natural conditional particle.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (conditional test, not question or action)
- [ ] Would a native speaker understand this introduces a conditional block?
- [ ] Avoids misleading connotations (not interrogative, not optative)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (conjunction/particle, NOT verb)?
- [ ] Correct form (conditional, not interrogative or imperative)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Matches the pattern of similar keywords (`while`, `for`)?
- [ ] Same grammatical category as other conditional keywords?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1 word ideally)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common everyday word)?

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
term: if
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "hypothetical conditional" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the interrogative "whether" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
