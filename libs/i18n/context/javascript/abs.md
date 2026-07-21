# JavaScript Member: `abs` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.abs(-5)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** EASY

---

## Quick Summary

`abs` is a static member method on the `Math` object that returns the **absolute value** of a number — its distance from zero, ignoring sign. It is called as `Math.abs(x)`. A negative input comes back positive; a positive input (and zero) is unchanged.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Absolute value of a negative number
let n = Math.abs(-5);  // 5
```

**What this does:** Reads the `abs` method on the `Math` object and calls it with `-5`, giving `5` — the magnitude, with the sign removed.

### Example 2: Common Pattern

```javascript
// Distance between two values, always non-negative
let a = 10;
let b = 25;
let distance = Math.abs(a - b);  // 15
```

**What this does:** Uses `Math.abs` so the difference is positive regardless of subtraction order — the everyday "how far apart are these?" computation.

### Example 3: Edge Case

```javascript
// A bare `abs` is NOT this member — only `Math.abs(...)` is
let abs = "not the method";   // an ordinary variable named abs
let m = Math.abs(-3.7);       // THIS is the member → 3.7
```

**What this shows:** `abs` counts as this member **only** in property position on its receiver (`Math.abs(...)`). A standalone variable named `abs` is a different thing entirely — the AST decides (a non-computed `MemberExpression.property`), not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `round` - Also a `Math` static transforming a single number
2. `floor` - Also a `Math` static returning a related integer value
3. `sqrt` - Also a `Math` static computing a mathematical function

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin *absolutus* — "freed, unrestricted," from *ab-* (away from) + *solvere* (to loosen). In mathematics, the "absolute value" is the value *freed from its sign* — the pure magnitude.

**Why JavaScript uses this:** `abs` abbreviates "absolute (value)," the universal mathematical term for magnitude without sign. It joins the `Math` object's family of concise, standard mathematical names (`abs`, `sqrt`, `pow`).

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.abs(x)` returns the non-negative magnitude of `x`: `|x| = x` when `x ≥ 0`, and `-x` when `x < 0`. `Math.abs(-5)` is `5`, `Math.abs(5)` is `5`, and `Math.abs(0)` is `0`. It is used constantly for distances and deviations, where only the size of a difference matters and its direction does not.

`abs` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.abs(-3.7)` is the member; a learner's own variable named `abs` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, the same native word could legitimately name a member of some other receiver without any collision — that is expected and correct, never lossy. Here the receiver is fixed as `Math`, so there is no receiver-widening to plan for; the translator only needs the standard mathematical term for absolute value.

**Key behaviors:**

1. **Non-negative result:** always returns a value `≥ 0`; the sign is discarded.
2. **Static on `Math`:** called as `Math.abs(x)`; the receiver is the `Math` object, not an instance.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `abs` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun/adjective naming a mathematical function ("absolute value")
- **Action vs State:** TRANSFORMATION - maps a number to its magnitude
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the standard mathematical term for **absolute value** in the target language — the adjective "absolute" or the compound "absolute value" as used in school mathematics.

**Forms to AVOID:**

- ❌ A word meaning **"positive"** - inaccurate; `abs` yields non-negative (includes zero), and it is about magnitude, not sign-flipping to positive
- ❌ "Absolute" in the sense of **complete / total / unconditional** - wrong domain
- ❌ A bare "magnitude" if the language reserves that for vectors/physics and has a distinct math-class term for absolute value

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Absolute" as **complete / total** ("absolute power")
- ✅ Meaning 2: **MATHEMATICAL ABSOLUTE VALUE** — magnitude without sign
- ❌ Meaning 3: "Absolute" as **unconditional** ("absolute truth")

**Example:**

English "absolute" can mean:

1. "**Absolute** power corrupts" (complete, unlimited) ❌
2. "`Math.abs(-5)` returns 5" (absolute value, magnitude) ✅ **This is the JavaScript meaning**
3. "**Absolute** truth" (unconditional) ❌

**Your translation should capture meaning #2: the mathematical absolute value — the distance from zero, written |x|** — not "complete" and not "positive."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `abs`, check these translations (the `Math` static family):**

- [ ] `round` - Sibling `Math` static; align the "standard math term" style
- [ ] `sqrt` - Sibling `Math` static (square root)
- [ ] `pow` - Sibling `Math` static (power)
- [ ] `floor` / `ceil` - Sibling rounding statics

**Consistency rule:**

The `Math.*` methods should read as a coherent family, each using the term a learner met in school mathematics. `abs`, `sqrt`, `pow`, `floor`, `ceil`, `round`, `max`, `min` should all favor the established native math word over an invented coinage.

### Functional relationships

**This term works WITH:**

1. **`Math.abs` for distance**: Difference magnitude

```javascript
let d = Math.abs(x1 - x2);  // always non-negative
```

**Common pairing:**

```javascript
// Compare magnitudes, ignoring sign
let a = -15;
let b = 10;
let biggerMagnitude = Math.abs(a) > Math.abs(b);  // true (15 > 10)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** Absolute value is a fundamental concept taught in school mathematics worldwide, and nearly every language has an established, unambiguous term for it. The only care needed is to pick the math-class term rather than a general "positive" or "complete" word, and to keep it consistent with the rest of the `Math.*` family.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (absolute value, magnitude without sign)?
- [ ] Distinguished from "positive" (result includes zero)?
- [ ] Avoids the "complete / unconditional" senses of "absolute"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/adjective naming the function)?
- [ ] Uses the standard school-math term?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the `Math.*` static family (`sqrt`, `pow`, `round`, …)?
- [ ] Uses mathematical terminology standard in the target language?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (max ~3 words for members)?
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
term: abs
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "absolute value / magnitude without sign" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it fits the `Math.*` family.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "positive" or "complete."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (competing regional math terms, magnitude-vs-absolute wording) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
