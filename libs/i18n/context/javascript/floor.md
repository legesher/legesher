# JavaScript Member: `floor` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.floor(3.7)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** MEDIUM

---

## Quick Summary

`floor` is a static member method on the `Math` object that rounds a number **DOWN** to the nearest integer — toward negative infinity. It is called as `Math.floor(x)`. `Math.floor(3.7)` is `3`; crucially, `Math.floor(-3.2)` is `-4`, because "down" means toward the smaller value, not toward zero.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Round down to the nearest whole number
let n = Math.floor(3.7);  // 3
```

**What this does:** Reads the `floor` method on the `Math` object and calls it with `3.7`, giving `3` — the largest integer not greater than the input.

### Example 2: Common Pattern

```javascript
// Turn a fractional index or count into a whole number of items
let total = 17;
let perPage = 5;
let fullPages = Math.floor(total / perPage);  // 3
```

**What this does:** Uses `Math.floor` to drop the fractional part so a division becomes a count of complete groups — a very common paging / bucketing pattern.

### Example 3: Edge Case

```javascript
// A bare `floor` is NOT this member — only `Math.floor(...)` is
let floor = "ground level";   // an ordinary variable named floor
let m = Math.floor(-3.2);     // THIS is the member → -4 (rounds DOWN, not toward zero)
```

**What this shows:** `floor` counts as this member **only** in property position on its receiver (`Math.floor(...)`). A standalone variable named `floor` is a different thing entirely — the AST decides, not the spelling. Note the sign trap: `-3.2` floors to `-4`, because "down" is toward negative infinity.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `ceil` - The opposite `Math` static: rounds UP
2. `round` - The `Math` static that rounds to the *nearest* integer
3. `abs` - Another `Math` static transforming a single number

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Old English / Latin metaphor

**Root meaning:** English "floor" — the lower surface of a room, the *bottom* boundary. In mathematics, the "floor function" ⌊x⌋ is the greatest integer **≤ x** — you step *down* to the integer beneath the value, as if to the floor below.

**Why JavaScript uses this:** `floor` is the standard mathematical name for rounding down to the nearest integer, paired with `ceil` (ceiling). JS borrows the established math-notation terms directly.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.floor(x)` returns the greatest integer that is less than or equal to `x` — it rounds **toward negative infinity**. For positive numbers this looks like "drop the fractional part": `Math.floor(3.7)` is `3`, `Math.floor(3.0)` is `3`. For negative numbers it is *not* truncation: `Math.floor(-3.2)` is `-4`, because `-4` is the largest integer that does not exceed `-3.2`. This down-toward-smaller behavior is the defining property and the most common source of confusion.

`floor` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.floor(-3.2)` is the member; a learner's own variable named `floor` (say, a building's floor number) is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is semantic: the chosen word must mean "round DOWN / toward the smaller integer," and must sit correctly opposite `ceil` ("round up").

**Key behaviors:**

1. **Rounds down:** returns the greatest integer `≤ x`, toward negative infinity.
2. **Not truncation for negatives:** `Math.floor(-3.2)` is `-4`, not `-3`.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `floor` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun/verb naming a mathematical function ("floor function" / "round down")
- **Action vs State:** TRANSFORMATION - maps a real number to the integer beneath it
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's established math-class term for the **floor function** — "round down" / "greatest integer ≤ x." Prefer whatever pairs naturally as the opposite of `ceil`.

**Forms to AVOID:**

- ❌ A word meaning **"the floor of a room / ground"** unless the language genuinely reuses that metaphor in mathematics — pick the math term, not the architectural one
- ❌ A word meaning **"truncate / drop decimals"** - wrong for negatives (`-3.2` floors to `-4`, truncation gives `-3`)
- ❌ A generic "round" - that is `round` (nearest), not `floor` (down)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Floor" as the **surface of a room / storey of a building**
- ❌ Meaning 2: "Floor" as a **lower limit** in a general sense ("price floor") — related but not the operation
- ✅ Meaning 3: **MATHEMATICAL FLOOR FUNCTION** — round down to the greatest integer ≤ x

**Example:**

English "floor" can mean:

1. "The **floor** was wet" (surface of a room) ❌
2. "A price **floor**" (a lower bound) ❌
3. "`Math.floor(3.7)` returns 3" (round down to nearest integer) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: rounding DOWN to the nearest integer (toward negative infinity)** — not a room's floor and not truncation.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `floor`, check these translations (the `Math` rounding family):**

- [ ] `ceil` - The exact opposite; `floor`/`ceil` must read as a DOWN/UP pair
- [ ] `round` - Rounds to nearest; keep clearly distinct from `floor`
- [ ] `abs` - Sibling `Math` static

**Consistency rule:**

`floor`, `ceil`, and `round` form a rounding trio and must stay mutually distinguishable: down, up, nearest. In particular, translate `floor` and `ceil` as a matched opposite pair, using the same metaphor family the target language's mathematics uses for ⌊x⌋ and ⌈x⌉.

### Functional relationships

**This term works WITH:**

1. **`Math.floor` on a division**: Whole groups

```javascript
let groups = Math.floor(items / size);
```

**Common pairing:**

```javascript
// floor and ceil bracket a fractional value
let x = 4.3;
let low = Math.floor(x);  // 4
let high = Math.ceil(x);  // 5
```

---

## Confidence Calibration

**Translation Difficulty: EASY-MEDIUM**

**For this term:** EASY-MEDIUM

**Rationale:** The floor function is standard in school and university mathematics and most languages have a settled term for it, which keeps this from being HARD. The MEDIUM edge comes from two traps: the English word "floor" invites the architectural/ground metaphor, and a "truncate" reading is subtly wrong for negatives. The translator must land on the math-class "round down" term and pair it cleanly with `ceil`.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (round DOWN, toward negative infinity)?
- [ ] Correct for negatives (not plain truncation)?
- [ ] Avoids the "room floor / building storey" sense?

### 2. Linguistic Correctness

- [ ] Correct part of speech (function name / "round down")?
- [ ] Uses the standard school-math term for the floor function?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Forms a matched DOWN/UP pair with `ceil`?
- [ ] Distinct from `round` (nearest)?
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
term: floor
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "round down to the greatest integer ≤ x" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it pairs as the opposite of `ceil`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any architectural "floor" or "truncate" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (metaphor mismatch, truncate-vs-floor for negatives) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
