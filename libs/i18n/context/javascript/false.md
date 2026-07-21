# JavaScript Keyword: `false` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** constant (boolean literal)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

`false` is a boolean literal representing the logical value "false." It is one of the two `boolean` values (the other being `true`) and is fundamental to conditional logic, comparisons, and control flow. Note the lowercase spelling — JavaScript writes `false`, not `False`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Boolean literal
let isValid = false;
if (isValid) {
  console.log("Valid!"); // does NOT run
} else {
  console.log("Invalid!"); // runs
}
```

**What this does:** `false` is a built-in constant. In a condition, `false` causes the `if` block to be skipped and the `else` block (if present) to run.

### Example 2: Common Pattern

```javascript
// Comparisons produce false
let age = 15;
let isAdult = age >= 18; // evaluates to false
console.log(isAdult);    // Output: false
```

**What this does:** Comparison operators produce `false` when the condition is not met. Code commonly stores such a result to indicate failure, invalidity, or an unmet condition.

### Example 3: Edge Case

```javascript
// false coerces to 0 in a numeric context
console.log(false + 10);   // Output: 10
console.log(Number(false)); // Output: 0

// Many values are "falsy" but are not the literal false
console.log(!0);   // true (0 is falsy)
console.log(!"");  // true (empty string is falsy)
console.log(0 === false); // false — falsy is not the same as false
```

**What this shows:** In arithmetic, `false` coerces to `0`. Separately, several values are "falsy" (behave like `false` in a condition): `0`, `""`, `null`, `undefined`, `NaN`, and `false` itself. But a falsy value is not strictly equal to `false` — `0 === false` is `false`.

---

## Pattern Classification

**This term is:** BOOLEAN LITERAL / CONSTANT

**Similar terms in this pattern:**

1. `true` - The other boolean value (logical true)
2. `null` - The intentional-absence value (neither true nor false)
3. Falsy values (`0`, `""`, `null`, `undefined`, `NaN`) - values that behave like `false`

**Pattern rule:** Boolean literals should use a noun or adjective form representing falsehood/incorrectness. It must be the natural opposite of the `true` translation, and spelled **lowercase** to match JavaScript convention.

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin *falsus* meant "deceived, erroneous." Through Old French *fals* it became English "false," meaning "not true, incorrect, deceptive." In logic, "false" marks statements that fail to correspond to reality or do not satisfy a condition.

**Why JavaScript uses this:** "False" is the standard English word for logical falsehood, the opposite of "true." JavaScript, following the C/Java family, spells it **lowercase** `false` as a reserved literal — unlike Python's capitalized `False`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`false` is one of JavaScript's two boolean literals, representing logical falsehood. It is a reserved word — immutable and unusable as a variable name. Its type is `"boolean"`.

In boolean logic, `false` represents negation: a condition is not met, a comparison fails, a state is inactive. Comparison operators produce `false` when their condition does not hold. Logical operators (`&&`, `||`, `!`) combine or negate boolean values.

JavaScript's truthiness system means several non-boolean values behave like `false` in a condition: `0`, `-0`, `""`, `null`, `undefined`, and `NaN`. These are "falsy" values. But the literal `false` is the explicit, canonical false value — the opposite of `true`. A falsy value is not strictly equal to `false` (`"" === false` is `false`).

**Key behaviors:**

1. **Reserved literal:** `false` cannot be reassigned or shadowed as a variable name; it is fixed by the language.
2. **Numeric coercion:** In arithmetic or with `Number()`, `false` coerces to `0`. This is rarely relied upon in practice.
3. **Distinct from falsiness:** Many values are falsy, but only the literal `false` (and expressions that evaluate to it) is strictly equal to `false`.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Adjective-as-noun or constant
- **Action vs State:** STATE - represents a truth value
- **Temporal aspect:** Timeless - falsehood is absolute

### Recommended Form

**Primary recommendation:** Use an adjective meaning "false" or "untrue." It must be the natural antonym of the `true` translation. Spell it **lowercase** to match JavaScript's boolean-literal convention.

**Forms to AVOID:**

- ❌ A "no" particle — too conversational
- ❌ "wrong" when "false" is more logical
- ❌ "0" or "zero" — booleans are logical, not numeric

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Fake, counterfeit" (false diamonds)
- ❌ Meaning 2: "Disloyal, unfaithful" (a false friend)
- ✅ Meaning 3: **LOGICAL FALSEHOOD** (a statement does not correspond to reality)

**Example:**

English "false" can mean:

1. "False teeth" (fake/artificial) ❌
2. "False accusations" (untrue/incorrect) ✅ (closer)
3. "`5 > 10` evaluates to `false`" (logical falsehood) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: logical or factual falsehood — statements that do not correspond to reality or fail conditions.**

Use the word for logical/factual falsehood, not fakery or disloyalty.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `false`, check these translations:**

- [ ] `true` - The opposite value; must use the antonym
- [ ] `null` - Another constant; same lowercase form, distinct meaning
- [ ] `!` (logical not) - Negates `true`/`false`

**Consistency rule:**

`false` and `true` MUST be opposites in the target language, using the same grammatical form and the same (lowercase) capitalization.

### Functional relationships

**This term works WITH:**

1. **Comparisons return `false`**:

```javascript
let result = 5 > 10; // false
```

2. **Boolean operators use `false`**:

```javascript
console.log(true && false); // false
console.log(false || false); // false
console.log(!false);         // true
```

**Common pairing:**

```javascript
// false as an initial flag toggled later
let done = false;
while (!done) {
  done = step();
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

### Why EASY for `false`

- Universal concept (falsehood exists in all cultures)
- Natural opposite of "true"
- Well-established in programming
- Standard logical term globally

**For this term:** EASY

**Rationale:** Falsehood is the universal opposite of truth; every language has words for true/false, with standard programming translations. The main requirement: ensure `false` is the natural antonym of your `true` translation and shares its lowercase form.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOGICAL FALSEHOOD (not fakery)?
- [ ] Understood as a boolean value (not numeric 0)?
- [ ] Natural opposite/antonym of `true`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective/noun for falsehood)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization matches JavaScript convention (lowercase)?

### 3. Consistency

- [ ] Opposite/antonym of the `true` translation?
- [ ] Same grammatical form as `true`?
- [ ] Same lowercase form as `true` and `null`?

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
term: false
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "logical/factual falsehood" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward "fake" or "disloyal."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, capitalization convention) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
