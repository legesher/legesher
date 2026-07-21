# JavaScript Builtin: `BigInt` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** HARD

---

## Quick Summary

`BigInt` is the global for *arbitrary-precision integers* — whole numbers that can grow beyond the safe range of ordinary JavaScript numbers without losing accuracy. It is used as `BigInt(123)` or with the `n` suffix (`123n`). In JEJ it names the "big whole-number" value type.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Make a big integer from a number
let big = BigInt(9007199254740993);
```

**What this does:** Calls `BigInt` to produce an arbitrary-precision integer that keeps every digit exactly, even past the normal safe-integer limit.

### Example 2: Common Pattern

```javascript
// The n suffix is the literal form of a BigInt
let huge = 9007199254740993n;
console.log(huge + 1n);   // exact, no rounding
```

**What this does:** Uses a `BigInt` literal and arithmetic that stays exact where regular numbers would round.

### Example 3: Edge Case

```javascript
// BigInt and regular numbers are different types; don't mix directly
let a = 10n;
let b = 3;
// a + b;          // TypeError: cannot mix BigInt and Number
console.log(a + BigInt(b));   // 13n — convert first
```

**What this shows:** A `BigInt` is its own value type, distinct from ordinary numbers. You must convert before combining them — the name marks a *separate* kind of number.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (global object name)

**Similar terms in this pattern:**

1. `Date` - Also a global constructor naming a value type
2. `RegExp` - Also a global naming a specialized value type
3. `NaN` / `Infinity` - Also numeric-domain names, though constants rather than constructors

**Pattern rule:** Global constructors (`BigInt`, `Date`, `RegExp`) are *names of the kinds of value you create*. Translate them as nouns naming the thing, consistent with each other, never as verbs.

---

## Etymology (Brief)

**English Origin:** English "big" + Latin *integer* (coined term)

**Root meaning:** "Big" (Germanic, "large") + "integer" from Latin *integer* ("whole, untouched"). The compound is a modern coinage meaning "large whole number" — a big integer.

**Why JavaScript uses this:** When JS gained arbitrary-precision integers (ES2020), it needed a name distinguishing them from the existing floating-point `Number`. "BigInt" plainly says "a whole number that can be arbitrarily big" — descriptive rather than borrowed from math tradition.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`BigInt` is a global that creates *arbitrary-precision integers* — whole numbers with no fixed size limit, so they stay exact no matter how many digits they have. Ordinary JavaScript numbers are 64-bit floating point and lose precision past about 9 quadrillion; `BigInt` values do not. You create them with the `BigInt(...)` function or the literal `n` suffix (`42n`).

In the JEJ teaching subset, `BigInt` names this "big whole number" type. It matters wherever exactness on large integers is required — counting beyond the safe range, cryptography-style math, precise IDs. It is an object-like global: a *type of value you create and compute with*, not an action.

Conceptually, `BigInt` is a *noun naming a numeric type*. The key idea to carry into the translation is the pair "whole number" + "unbounded/big/exact-precision." It is a technical coinage; many languages will assemble a compound ("large integer" / "arbitrary-precision integer") or loan the term. The word must read as a *kind of number*, distinct from the ordinary `Number`.

**Key behaviors:**

1. **Names a value type:** A `BigInt` *is* a number; it is a thing, not an operation.
2. **Whole numbers only:** No fractions — it is an integer type, arbitrarily large.
3. **Distinct from `Number`:** Cannot be freely mixed with ordinary numbers; conversion is explicit.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Proper-noun-like name for the big-integer value type
- **Action vs State:** STATE/thing - names a kind of value, does not perform an action
- **Temporal aspect:** None - it is a persistent type name

### Recommended Form

**Primary recommendation:** Translate as a compound noun meaning "big / arbitrary-precision **integer**" — the "whole number without a size limit" idea. Keep it a technical noun consistent with the other global constructors (`Date`, `RegExp`). Preserve both halves: it is *big* and it is an *integer* (whole number).

**Forms to AVOID:**

- ❌ A verb - `BigInt` names a value, it does not act
- ❌ A word for a large *decimal/real* number - it is strictly a whole-number type
- ❌ Dropping the "big/unbounded" sense and using the plain word for "integer" - loses the point

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO

**If NO, note any translation subtlety:**

- ✅ Single meaning: **"AN ARBITRARY-PRECISION (UNBOUNDED) WHOLE NUMBER"**

`BigInt` is a coined technical compound with essentially one meaning, so there is no everyday-sense trap to avoid. The subtlety is compositional, not ambiguous: the translation must carry *both* "big / unbounded / exact" *and* "integer / whole number." Using only "big number" loses the whole-number constraint; using only "integer" loses the unbounded-precision point that distinguishes it from `Number`.

**Example:**

English "BigInt" reads as:

1. "A **big integer** that never rounds" (arbitrary-precision whole number) ✅ **This is the JavaScript meaning**

**Your translation should compose both parts — "large/unbounded" and "whole number" — into one technical noun for the value type.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `BigInt`, check these translations:**

- [ ] `Date` - Also a global constructor noun; keep both as type-naming nouns of one register
- [ ] `RegExp` - Also a global constructor for a technical value type; consistent noun treatment
- [ ] `NaN` / `Infinity` - Other numeric-domain names; keep the number vocabulary coherent

**Consistency rule:**

`BigInt`, `Date`, and `RegExp` are all names of value types the program creates. Treat them as one consistent set of technical nouns. Additionally, keep `BigInt`'s "integer/number" wording coherent with the numeric constants `NaN` and `Infinity`, which live in the same number vocabulary.

### Functional relationships

**This term works WITH:**

1. **`BigInt` + arithmetic**: Exact large-number math

```javascript
let x = BigInt(2) ** BigInt(64);   // exact
```

**Common pairing:**

```javascript
// BigInt literal and exact addition
let count = 9007199254740993n;
console.log(count + 1n);
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

**For this term:** HARD

**Rationale:** `BigInt` is a recent technical coinage with no everyday word and a two-part meaning ("unbounded" + "integer") that must both survive translation. Languages vary in whether they loan "BigInt," calque it as "large integer," or spell out "arbitrary-precision integer," and the plain word for "integer" alone is insufficient. This compositional demand plus community variation makes it genuinely hard — flag for a native reviewer versed in local CS/math vocabulary.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (an unbounded, exact whole number)
- [ ] Does it convey BOTH "big/arbitrary-precision" AND "integer/whole number"?
- [ ] Distinct from the ordinary `Number` type?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun naming a type, not a verb)?
- [ ] Correct form (technical compound noun / accepted loan)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (`BigInt` case preserved in JS)?

### 3. Consistency

- [ ] Matches the pattern of other global constructors (`Date`, `RegExp`)?
- [ ] Coherent with the number vocabulary of `NaN` / `Infinity`?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words, or an accepted compound)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember for learners?

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
term: BigInt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names an arbitrary-precision whole-number type in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it carries both the "big/unbounded" and "integer" senses.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for dropping either half of the compound.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (recent coinage, two-part meaning, loan-vs-calque) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
