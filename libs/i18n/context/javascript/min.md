# JavaScript Member: `min` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.min(3, 8)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** EASY

---

## Quick Summary

`min` is a static member method on the `Math` object that returns the **smallest** of its arguments. It is called as `Math.min(a, b, ...)` and accepts any number of numeric arguments. `Math.min(3, 8, 5)` is `3`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// The smaller of two numbers
let n = Math.min(3, 8);  // 3
```

**What this does:** Reads the `min` method on the `Math` object and calls it with `3` and `8`, giving `3` — the smallest of the arguments.

### Example 2: Common Pattern

```javascript
// Clamp a value so it never exceeds a ceiling
let input = 140;
let atMostHundred = Math.min(100, input);  // 100
```

**What this does:** Uses `Math.min` to enforce an upper bound — a common "don't let this go over the cap" guard.

### Example 3: Edge Case

```javascript
// A bare `min` is NOT this member — only `Math.min(...)` is
let min = "not the method";     // an ordinary variable named min
let m = Math.min(3, 8, 5, 12);  // THIS is the member → 3 (any number of arguments)
```

**What this shows:** `min` counts as this member **only** in property position on its receiver (`Math.min(...)`). A standalone variable named `min` is a different thing entirely — the AST decides, not the spelling. Note that `min` is variadic — it compares as many arguments as you pass.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `max` - The exact opposite `Math` static: the largest argument
2. `abs` - Another `Math` static transforming/selecting a numeric value
3. `round` - Another `Math` static operating on numbers

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin *minimus* — "smallest" (superlative of *parvus*, "small")

**Root meaning:** `min` abbreviates "minimum," the smallest value in a set. The `-imus` superlative marks "the least / the smallest."

**Why JavaScript uses this:** `min` is the universal mathematical/computing shorthand for "the minimum," paired with `max`. JS uses the clipped form on the `Math` object alongside its other concise math names.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.min(...args)` returns the smallest of the numbers passed to it. It is variadic: `Math.min(3, 8)` is `3`, `Math.min(3, 8, 5, 12)` is `3`. Called with no arguments it returns `+Infinity` (the identity for "smallest so far"), and any `NaN` argument makes the whole result `NaN`. Beyond finding a smallest value, it is frequently used to *clamp* — `Math.min(100, x)` guarantees a result no larger than `100`.

`min` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.min(3, 8)` is the member; a learner's own variable named `min` (say, a stored lower limit, or "minutes") is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is to choose the "minimum / least" term, keep it cleanly opposite `max`, and avoid the "minutes" abbreviation trap that `min` invites in some languages.

**Key behaviors:**

1. **Returns the smallest argument:** least of all values passed.
2. **Variadic:** accepts any number of numeric arguments.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `min` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun naming a selection ("the minimum / the smallest")
- **Action vs State:** SELECTION - picks the smallest of the inputs
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's standard math/computing term for **"minimum / the smallest value."** It should pair naturally as the opposite of `max`.

**Forms to AVOID:**

- ❌ A word meaning **"minute(s)"** (unit of time) - the English `min` abbreviates that too, but here it is "minimum"
- ❌ A word meaning **"round down / floor"** - that is `floor`, a different operation
- ❌ Reusing the `max` word or a non-opposite term - `max`/`min` must read as a matched pair

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (the abbreviation `min` is shared with "minute")

**If YES, identify the CORRECT meaning for JavaScript:**

- ✅ Meaning 1: **MINIMUM — the smallest of the given numbers**
- ❌ Meaning 2: "min" as **minute(s)** (unit of time)

**Example:**

The written form "min" can stand for:

1. "5 **min** left" (minutes) ❌
2. "`Math.min(3, 8)` returns 3" (the smallest argument) ✅ **This is the JavaScript meaning**

**Your translation should capture "the smallest of the given numbers," NOT "minutes."** Some languages abbreviate "minute" as *min* too — do not let that homograph steer the choice.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `min`, check these translations:**

- [ ] `max` - The exact opposite; `min`/`max` MUST be a matched pair
- [ ] `floor` - Keep `min` distinct from "round down"
- [ ] `round` / `ceil` - Sibling `Math` statics for family consistency

**Consistency rule:**

`min` and `max` are a symmetric pair and must be translated together, using the target language's standard "minimum" / "maximum" terms so the opposition is obvious. Keep both distinct from the rounding members (`floor`/`ceil`), which some languages describe with "up/down" words that could bleed into "largest/smallest."

### Functional relationships

**This term works WITH:**

1. **`Math.min` as an upper-clamp**: Enforce a ceiling

```javascript
let capped = Math.min(100, value);  // never above 100
```

**Common pairing:**

```javascript
// min and max bracket a value into a range (clamp)
let x = 137;
let clamped = Math.min(100, Math.max(0, x));  // 100
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** "Minimum" is a near-universal term in mathematics and computing with a stable meaning and an obvious opposite in `max`. Translation is direct; the only discipline is pairing it symmetrically with `max` and steering clear of the "minute" abbreviation homograph.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (the smallest of the arguments)?
- [ ] Understood as numeric minimum (not "minutes")?
- [ ] Distinct from `floor` (round down)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun / "minimum")?
- [ ] Uses the standard math/computing term?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Forms a matched pair with `max`?
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
term: min
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the smallest of the given numbers" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it pairs symmetrically with `max`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any "minutes" or "round down" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (max pairing, minute homograph) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
