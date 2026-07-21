# JavaScript Keyword: `true` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** constant (boolean literal)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

`true` is a boolean literal representing the logical value "true." It is one of the two `boolean` values (the other being `false`) and is fundamental to conditional logic, comparisons, and control flow. Note the lowercase spelling — JavaScript writes `true`, not `True`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Boolean literal
let isValid = true;
if (isValid) {
  console.log("Valid!"); // this runs
}
```

**What this does:** `true` is a built-in constant. Assigning it creates a boolean value; in a condition, `true` causes the `if` block to run.

### Example 2: Common Pattern

```javascript
// Comparisons produce true
let age = 25;
let isAdult = age >= 18; // evaluates to true
console.log(isAdult);    // Output: true
```

**What this does:** Comparison operators (`>`, `>=`, `===`, etc.) produce `true` or `false`. Code commonly stores such a result to indicate success, validity, or a satisfied condition.

### Example 3: Edge Case

```javascript
// true coerces to 1 in a numeric context
console.log(true + true); // Output: 2
console.log(Number(true)); // Output: 1

// but it is a boolean, not a number
console.log(typeof true);  // Output: "boolean"
```

**What this shows:** In arithmetic, `true` coerces to `1` (and `false` to `0`), so `true + true` is `2`. Despite that, `true` is genuinely of type `"boolean"` — using it in arithmetic is possible but uncommon and usually a code smell.

---

## Pattern Classification

**This term is:** BOOLEAN LITERAL / CONSTANT

**Similar terms in this pattern:**

1. `false` - The other boolean value (logical false)
2. `null` - The intentional-absence value (neither true nor false)
3. Boolean literals in other languages (often lowercase: `true`, `false`)

**Pattern rule:** Boolean literals should use a noun or adjective form representing truth/correctness. JavaScript spells its boolean literals in **lowercase** (`true`/`false`); follow that convention.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *trēowe* meant "faithful, trustworthy, honest." It became "true," meaning "in accordance with fact, genuine, accurate." In logic, "true" marks statements that correspond to reality or satisfy conditions.

**Why JavaScript uses this:** "True" is the standard English word for logical truth. JavaScript, following the C/Java family, spells it **lowercase** `true` as a reserved literal — unlike Python's capitalized `True`. The lowercase form distinguishes it as a primitive literal baked into the language.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`true` is one of JavaScript's two boolean literals, representing logical truth. It is a reserved word — you cannot assign to it or use it as a variable name. Its type is `"boolean"`.

In boolean logic, `true` represents affirmation: a condition is met, a comparison holds, a state is active. Comparison operators like `===`, `>`, `<` produce `true` when their condition is satisfied. Logical operators (`&&`, `||`, `!`) combine or negate boolean values.

JavaScript also has "truthiness": many non-boolean values behave like `true` in a condition — non-zero numbers, non-empty strings, objects, and arrays are all "truthy." But the literal `true` is the explicit, canonical true value. Note that a truthy value is not equal to `true`: `1 === true` is `false` under strict equality, even though `if (1)` runs.

**Key behaviors:**

1. **Reserved literal:** `true` cannot be reassigned or shadowed as a variable name; it is fixed by the language.
2. **Numeric coercion:** In arithmetic or with `Number()`, `true` coerces to `1`. This is rarely relied upon in practice.
3. **Distinct from truthiness:** Many values are truthy, but only the literal `true` (and expressions that evaluate to it) is strictly equal to `true`.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Adjective-as-noun or constant
- **Action vs State:** STATE - represents a truth value, not an action
- **Temporal aspect:** Timeless - truth is absolute, not time-dependent

### Recommended Form

**Primary recommendation:** Use an adjective meaning "true" or "truthful." Spell it **lowercase** to match JavaScript's boolean-literal convention, unless the target language has a strong counter-convention.

**Forms to AVOID:**

- ❌ A verb "to be true" — should be an adjective/state
- ❌ "yes" — related, but "true" is more formal/logical
- ❌ "1" or "one" — booleans are logical, not numeric

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Genuine, authentic" (this is true gold)
- ❌ Meaning 2: "Loyal, faithful" (a true friend)
- ✅ Meaning 3: **LOGICAL/FACTUAL TRUTH** (a statement corresponds to reality)

**Example:**

English "true" can mean:

1. "This is true leather" (genuine/authentic) ❌
2. "He's a true friend" (loyal/faithful) ❌
3. "`5 > 3` evaluates to `true`" (logical truth) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: logical or factual truth — statements that correspond to reality or satisfy conditions.**

Most languages distinguish these senses. Use the word for logical/factual truth, not loyalty or authenticity.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `true`, check these translations:**

- [ ] `false` - The opposite value; must use the antonym in the target language
- [ ] `null` - Another constant; keep the same lowercase form, but distinct in meaning
- [ ] Comparison results generally return `true`/`false`

**Consistency rule:**

`true` and `false` are opposites and must use antonym words with the same grammatical form and the same (lowercase) capitalization. If `true` is an adjective, `false` should be too.

### Functional relationships

**This term works WITH:**

1. **Comparisons return `true`**:

```javascript
let result = 5 > 3; // true
```

2. **Boolean operators use `true`**:

```javascript
console.log(true && false); // false
console.log(true || false); // true
console.log(!true);         // false
```

**Common pairing:**

```javascript
// true as a loop condition and a return-like flag
while (true) {
  if (done) {
    break;
  }
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have a direct equivalent
- No ambiguity in a logical context
- **AI confidence should be HIGH**

### Why EASY for `true`

- Universal concept (truth exists in all cultures)
- "True" is a standard logical term
- Well-established in programming
- Clear opposition to "false"

**For this term:** EASY

**Rationale:** Truth (versus falsehood) is universal across languages and cultures; every language has words for true/false, with well-established programming translations. The one nuance: match JavaScript's **lowercase** spelling convention.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOGICAL TRUTH (not loyalty or authenticity)?
- [ ] Understood as a boolean value (not numeric 1)?
- [ ] Pairs naturally with `false` (opposite)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective/noun for truth)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization matches JavaScript convention (lowercase)?

### 3. Consistency

- [ ] Opposite/antonym of the `false` translation?
- [ ] Same grammatical form as `false`?
- [ ] Same lowercase form as `false` and `null`?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: true
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "logical/factual truth" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward "genuine" or "loyal."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, capitalization convention) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
