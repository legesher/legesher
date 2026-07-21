# JavaScript Builtin: `Infinity` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** constant (numeric value)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`Infinity` is the numeric value that lies beyond the largest number JavaScript can represent — "endlessly large." You get it from operations like `1/0` or from arithmetic that overflows the number range. It also has a negative form, `-Infinity`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Dividing a positive number by zero gives Infinity
let big = 1 / 0;
console.log(big);   // Infinity
```

**What this does:** `1/0` has no finite answer, so JavaScript returns `Infinity` — the "beyond all finite numbers" value.

### Example 2: Common Pattern

```javascript
// Infinity as a starting point for finding a minimum
let smallest = Infinity;
for (let n of [4, 2, 9]) {
  if (n < smallest) smallest = n;
}
console.log(smallest);   // 2
```

**What this does:** Uses `Infinity` as an initial value guaranteed to be larger than any real data, a common "find the smallest" pattern.

### Example 3: Edge Case

```javascript
// Infinity has a negative counterpart, and overflow reaches it
console.log(-1 / 0);          // -Infinity
console.log(1e308 * 10);      // Infinity (overflow past the max)
```

**What this shows:** `Infinity` is directional (`+`/`-`) and is also what you hit when a number grows past the representable maximum — not only from division by zero.

---

## Pattern Classification

**This term is:** VALUE CONSTANT (numeric "beyond all finite numbers")

**Similar terms in this pattern:**

1. `NaN` - Also a special numeric constant (an invalid numeric result)
2. `undefined` - Also a special value constant, for "unset" rather than a numeric extreme
3. `null` - Also a special value constant, for absence

**Pattern rule:** The special value constants (`Infinity`, `NaN`, `undefined`, `null`) name particular values. Translate them as labels for the value. `Infinity` specifically labels "endlessly large," in the same number vocabulary as `NaN`.

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin *infinitas* — *in-* ("not") + *finis* ("end, boundary"). Literally "without end / boundless." It is the long-established mathematical term for the unbounded.

**Why JavaScript uses this:** IEEE 754 floating-point defines a value for results beyond the finite range, and mathematics already calls the boundless "infinity." JS adopts the familiar mathematical name so the value reads the same way it does in math class.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Infinity` is a special value in the number type representing a quantity larger than any finite number JavaScript can store. It arises from dividing a positive number by zero, and from arithmetic overflow — when a computation grows past the maximum representable value (~1.8 × 10^308). It is directional: there is `Infinity` and `-Infinity`. Unlike `NaN`, `Infinity` behaves in ordered comparisons: it is greater than every finite number.

In the JEJ teaching subset, `Infinity` gives learners a concrete value for "endlessly large," useful both as a real arithmetic outcome and as a sentinel (a value guaranteed bigger than any data, handy when searching for a minimum). Because "infinity" is a standard mathematical idea taught worldwide, the concept transfers cleanly across languages.

Conceptually, `Infinity` is a *noun-like label for a specific value* in the number system — the boundless, endless magnitude. A good translation should carry the mathematical "without end / boundless" sense, distinct from `NaN` ("invalid number") and from mere "a very big number."

**Key behaviors:**

1. **Beyond all finite numbers:** `Infinity` is greater than every finite value and orders correctly in comparisons.
2. **Directional:** `Infinity` and `-Infinity` are both available.
3. **From division-by-zero and overflow:** Both `1/0` and past-max arithmetic produce it.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Name/label for the "endlessly large" value
- **Action vs State:** STATE - names a value, does not perform an action
- **Temporal aspect:** None - it is a fixed constant value

### Recommended Form

**Primary recommendation:** Translate as the established mathematical noun for "infinity / the boundless / without end." Use the target language's standard math term, and keep it in the same value-label register as `NaN`. It should read as a *magnitude beyond all finite numbers*, not "a very big number."

**Forms to AVOID:**

- ❌ "A very large number" - `Infinity` is *beyond* every finite number, not just big
- ❌ The same word as `NaN` - `Infinity` is a valid ordered value; `NaN` is invalid
- ❌ A verb or an abstract "eternity/forever" (time) sense - it is a numeric magnitude

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Forever / eternity" (an endlessness of *time*)
- ❌ Meaning 2: A vague "a huge amount" in casual speech
- ✅ Meaning 3: **"THE MATHEMATICAL INFINITY — A MAGNITUDE BEYOND ALL FINITE NUMBERS"**

**Example:**

English "infinity" can mean:

1. "I'll love you to **infinity**" (endless time/feeling) ❌
2. "There were **infinity** people there" (casual hyperbole for "a lot") ❌
3. "`1/0` evaluates to **Infinity**" (the boundless numeric magnitude) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the mathematical, numeric notion of the boundless — greater than every finite number — not endless time or casual exaggeration.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Infinity`, check these translations:**

- [ ] `NaN` - Fellow numeric constant; keep both in one consistent number-value register
- [ ] `undefined` - Keep DISTINCT; `Infinity` = boundless magnitude, `undefined` = unset value
- [ ] `null` - Keep DISTINCT; `Infinity` = boundless magnitude, `null` = deliberate absence

**Consistency rule:**

`Infinity` and `NaN` are the two special *numeric* constants and should share a register. Keep `Infinity` distinct from the absence values (`undefined`/`null`) and from `NaN` — it is a valid, ordered magnitude, whereas `NaN` is an invalid result. Use the standard math term for infinity, matching how it is taught in the target language.

### Functional relationships

**This term works WITH:**

1. **`Infinity` from division by zero**:

```javascript
let r = 5 / 0;   // Infinity
```

**Common pairing:**

```javascript
// Infinity as a min-finding sentinel
let min = Infinity;
if (3 < min) min = 3;
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** "Infinity" is a universal mathematical concept with an established term in essentially every language, so the core translation is reliable. The judgment calls are choosing the *mathematical* term (not the "eternity/forever" time sense), keeping it distinct from `NaN`, and matching the register of the other numeric constant. Those are modest but real, warranting a native reviewer's confirmation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (a magnitude beyond all finite numbers)
- [ ] Uses the mathematical "infinity," not "eternity/forever" (time)?
- [ ] Distinct from "a very big number" and from `NaN`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (value label / math noun, not a verb)?
- [ ] Correct form (standard mathematical term)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (`Infinity` case preserved in JS)?

### 3. Consistency

- [ ] Shares a number-value register with `NaN`?
- [ ] Kept distinct from `undefined` and `null`?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words)?
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
term: Infinity
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the mathematical "boundless magnitude beyond all finite numbers" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it is the math sense, not "eternity/forever."

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for the time/eternity sense or for meaning merely "very big."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (math-vs-time sense, register match with `NaN`) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
