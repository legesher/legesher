# JavaScript Member: `max` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.max(3, 8)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** EASY

---

## Quick Summary

`max` is a static member method on the `Math` object that returns the **largest** of its arguments. It is called as `Math.max(a, b, ...)` and accepts any number of numeric arguments. `Math.max(3, 8, 5)` is `8`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// The larger of two numbers
let n = Math.max(3, 8);  // 8
```

**What this does:** Reads the `max` method on the `Math` object and calls it with `3` and `8`, giving `8` — the greatest of the arguments.

### Example 2: Common Pattern

```javascript
// Clamp a value so it never drops below a floor
let input = -4;
let atLeastZero = Math.max(0, input);  // 0
```

**What this does:** Uses `Math.max` to enforce a lower bound — a common "don't let this go negative" guard.

### Example 3: Edge Case

```javascript
// A bare `max` is NOT this member — only `Math.max(...)` is
let max = "not the method";     // an ordinary variable named max
let m = Math.max(3, 8, 5, 12);  // THIS is the member → 12 (any number of arguments)
```

**What this shows:** `max` counts as this member **only** in property position on its receiver (`Math.max(...)`). A standalone variable named `max` is a different thing entirely — the AST decides, not the spelling. Note that `max` is variadic — it compares as many arguments as you pass.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `min` - The exact opposite `Math` static: the smallest argument
2. `abs` - Another `Math` static transforming/selecting a numeric value
3. `round` - Another `Math` static operating on numbers

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin *maximus* — "greatest" (superlative of *magnus*, "great")

**Root meaning:** `max` abbreviates "maximum," the largest value in a set. The `-imus` superlative marks "the most / the greatest."

**Why JavaScript uses this:** `max` is the universal mathematical/computing shorthand for "the maximum," paired with `min`. JS uses the clipped form on the `Math` object alongside its other concise math names.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.max(...args)` returns the largest of the numbers passed to it. It is variadic: `Math.max(3, 8)` is `8`, `Math.max(3, 8, 5, 12)` is `12`. Called with no arguments it returns `-Infinity` (the identity for "largest so far"), and any `NaN` argument makes the whole result `NaN`. Beyond finding a biggest value, it is frequently used to *clamp* — `Math.max(0, x)` guarantees a result no smaller than `0`.

`max` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.max(3, 8)` is the member; a learner's own variable named `max` (say, a stored upper limit) is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is to choose the "maximum / greatest" term and keep it cleanly opposite `min`, and distinct from directional rounding like `ceil`.

**Key behaviors:**

1. **Returns the largest argument:** greatest of all values passed.
2. **Variadic:** accepts any number of numeric arguments.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `max` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun naming a selection ("the maximum / the greatest")
- **Action vs State:** SELECTION - picks the largest of the inputs
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's standard math/computing term for **"maximum / the greatest value."** It should pair naturally as the opposite of `min`.

**Forms to AVOID:**

- ❌ A word meaning **"biggest in physical size"** if the language distinguishes that from numeric maximum
- ❌ A word meaning **"round up / ceiling"** - that is `ceil`, a different operation
- ❌ Reusing the `min` word or a non-opposite term - `max`/`min` must read as a matched pair

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (essentially unambiguous within mathematics/computing)

**If NO, confirm the single intended meaning for JavaScript:**

- ✅ Meaning: **MAXIMUM — the greatest of the given numbers**

**Example:**

"Maximum" in English is stable across contexts:

1. "The **maximum** temperature today" (the highest value) ✅
2. "`Math.max(3, 8)` returns 8" (the greatest argument) ✅ **This is the JavaScript meaning**

**Your translation should capture "the greatest of the given numbers."** The only care is to keep it distinct from "round up" (`ceil`) and to pair it as the opposite of `min` — not a meaning ambiguity, a family-consistency check.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `max`, check these translations:**

- [ ] `min` - The exact opposite; `max`/`min` MUST be a matched pair
- [ ] `ceil` - Keep `max` distinct from "round up"
- [ ] `round` / `floor` - Sibling `Math` statics for family consistency

**Consistency rule:**

`max` and `min` are a symmetric pair and must be translated together, using the target language's standard "maximum" / "minimum" terms so the opposition is obvious. Keep both distinct from the rounding members (`ceil`/`floor`), which some languages describe with "up/down" words that could bleed into "largest/smallest."

### Functional relationships

**This term works WITH:**

1. **`Math.max` as a lower-clamp**: Enforce a floor

```javascript
let safe = Math.max(0, value);  // never below 0
```

**Common pairing:**

```javascript
// max and min bracket a value into a range (clamp)
let x = 137;
let clamped = Math.min(100, Math.max(0, x));  // 100
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** "Maximum" is a near-universal loan/term in mathematics and computing, with a stable, unambiguous meaning and an obvious opposite in `min`. Translation is direct; the only discipline is pairing it symmetrically with `min` and not letting it drift into "round up."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (the greatest of the arguments)?
- [ ] Understood as numeric maximum (not physical "biggest")?
- [ ] Distinct from `ceil` (round up)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun / "maximum")?
- [ ] Uses the standard math/computing term?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Forms a matched pair with `min`?
- [ ] Distinct from the rounding members?
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
term: max
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the greatest of the given numbers" in the target language — grounded in this brief's Concept Explanation — and confirm it pairs symmetrically with `min`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "round up" or physical size.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (min pairing, ceil bleed) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
