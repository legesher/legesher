# JavaScript Builtin: `NaN` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** constant (numeric value)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`NaN` stands for "Not a Number" — the special numeric value you get when a math operation has no valid numeric result, such as `0/0` or turning the word `"hello"` into a number. It is a *number-typed* value that means "this is not a usable number."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Invalid numeric conversion yields NaN
let n = Number("hello");
console.log(n);   // NaN
```

**What this does:** Trying to read `"hello"` as a number fails, so JavaScript returns `NaN` — "not a number."

### Example 2: Common Pattern

```javascript
// Meaningless arithmetic produces NaN
let result = 0 / 0;
console.log(result);   // NaN
```

**What this does:** `0/0` has no meaningful numeric answer, so the result is the `NaN` value rather than an error.

### Example 3: Edge Case

```javascript
// NaN is never equal to anything, not even itself
console.log(NaN === NaN);   // false
let x = NaN;
console.log(Number.isNaN(x));   // true — the correct way to test
```

**What this shows:** `NaN` is famously not equal to itself, so you cannot check for it with `===`. Use `Number.isNaN(...)`. This oddity is part of the concept the translation must respect.

---

## Pattern Classification

**This term is:** VALUE CONSTANT (numeric "invalid result")

**Similar terms in this pattern:**

1. `Infinity` - Also a special numeric constant (beyond the largest number)
2. `undefined` - Also a special value constant, though for "unset" rather than "invalid number"
3. `null` - Also a special value constant for absence

**Pattern rule:** The special value constants (`NaN`, `Infinity`, `undefined`, `null`) name particular values. Translate them as labels for the value. `NaN` specifically labels "a result that is not a valid number," and belongs to the same number vocabulary as `Infinity`.

---

## Etymology (Brief)

**English Origin:** English acronym

**Root meaning:** `NaN` is an initialism for "**N**ot **a** **N**umber." It comes from the IEEE 754 floating-point standard, which defines `NaN` as the result of undefined or unrepresentable numeric operations.

**Why JavaScript uses this:** JS numbers follow IEEE 754, which mandates a "Not a Number" value for operations with no numeric answer. JS surfaces it under the standard's name, `NaN`, so it matches how numeric computing describes this state everywhere.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`NaN` is a special value in the number type that represents "the result of a numeric operation that has no valid number as its answer." You encounter it when converting non-numeric text to a number, or when arithmetic is mathematically undefined (like `0/0`). Crucially, `NaN` is still *of type number* — it lives in the numeric domain — but it flags that the number is not usable.

In the JEJ teaching subset, `NaN` teaches learners that arithmetic can fail *without* throwing an error: instead of crashing, JS produces a placeholder number that means "invalid." Learners must then check for it. The name — an acronym meaning "Not a Number" — is itself a small paradox: a number-typed value whose meaning is "not a number."

Conceptually, `NaN` is a *noun-like label for a specific value* in the number system. Its most surprising behavior is that it is not equal to anything, including itself, so it can only be detected with `Number.isNaN(...)`. A good translation should convey "not a (valid) number / invalid numeric result," not "zero" and not "no value at all."

**Key behaviors:**

1. **Type number, meaning "invalid":** `NaN` is a numeric value that signals an unusable numeric result.
2. **Not equal to itself:** `NaN === NaN` is false; detect it with `Number.isNaN(...)`.
3. **Propagates:** Arithmetic involving `NaN` generally yields `NaN`, carrying the "invalid" flag forward.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Name/label for the "not a valid number" value
- **Action vs State:** STATE - names a value/condition, does not perform an action
- **Temporal aspect:** None - it is a fixed constant value

### Recommended Form

**Primary recommendation:** Since `NaN` is a standardized acronym for "Not a Number," the safest treatment is to keep the established `NaN` token or a locally recognized equivalent, optionally with a native gloss meaning "not a number / invalid numeric result." Whatever is chosen must read as a *value label in the number domain*, consistent with `Infinity`.

**Forms to AVOID:**

- ❌ "Zero" or a number word - `NaN` is not a quantity
- ❌ The same word as `undefined` / `null` - those are "unset/absent," not "invalid number"
- ❌ A verb - `NaN` names a value, it does not act

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO

**If NO, note any translation subtlety:**

- ✅ Single meaning: **"THE 'NOT A NUMBER' VALUE — AN INVALID NUMERIC RESULT"**

`NaN` is an acronym with one technical meaning, so there is no everyday-sense trap. The subtlety is twofold. First, it must be distinguished from *other* kinds of "nothing": `NaN` is an *invalid number*, not an *absent value* (`undefined`/`null`) and not zero. Second, because `NaN` is a widely recognized standard token, a translator must decide whether to keep the acronym as-is (common in practice) or expand it to a native "not a number" phrase — a display/convention choice more than a meaning choice.

**Example:**

English "NaN" reads as:

1. "`Number("abc")` gives **NaN**" (an invalid numeric result) ✅ **This is the JavaScript meaning**

**Your translation should label the "not a valid number" numeric value — distinct from absence (`undefined`/`null`) and from zero.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `NaN`, check these translations:**

- [ ] `Infinity` - Fellow numeric constant; keep both in one consistent number-value register
- [ ] `undefined` - Keep DISTINCT; `NaN` = invalid number, `undefined` = unset value
- [ ] `null` - Keep DISTINCT; `NaN` = invalid number, `null` = deliberate absence

**Consistency rule:**

`NaN` and `Infinity` are the two special *numeric* constants and should share a register (both are exceptional values within the number domain). Keep `NaN` clearly separate from `undefined`/`null`, which are about *absence*, not *invalid arithmetic*. If you expand the acronym, do so in a way consistent with how `Infinity` is presented.

### Functional relationships

**This term works WITH:**

1. **`NaN` from failed conversion**:

```javascript
let n = Number("oops");
if (Number.isNaN(n)) {
  // conversion failed
}
```

**Common pairing:**

```javascript
// NaN checked before use
let value = parseInt("12x", 10);   // 12 here, but "x" alone → NaN
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept "not a valid number" is clear and universal, and the acronym `NaN` is widely recognized across programming cultures, which lowers ambiguity. The judgment call is presentational: keep the standard `NaN` token or render a native "not a number" gloss, and keep it distinct from absence values. That convention choice, plus the not-equal-to-itself quirk, is worth a native reviewer's confirmation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (an invalid numeric result — "not a number")
- [ ] Distinct from zero and from absence (`undefined`/`null`)?
- [ ] Would a native speaker read it as a number-domain value?

### 2. Linguistic Correctness

- [ ] Correct part of speech (value label, not a verb)?
- [ ] Correct form (value constant / recognized token)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (`NaN` case preserved in JS)?

### 3. Consistency

- [ ] Shares a number-value register with `Infinity`?
- [ ] Kept distinct from `undefined` and `null`?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (token or 1-3 word gloss)?
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
term: NaN
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term (kept token or native gloss) labels the "not a valid number" value in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and state whether you kept the standard acronym or expanded it.

**Alternatives considered:**

List the candidate treatments weighed and why each was rejected or kept, especially any rejected for meaning "zero" or "absent."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (keep-token vs expand, distinctness from absence values) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
