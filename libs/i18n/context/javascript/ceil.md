# JavaScript Member: `ceil` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.ceil(3.2)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** MEDIUM

---

## Quick Summary

`ceil` is a static member method on the `Math` object that rounds a number **UP** to the nearest integer — toward positive infinity. It is called as `Math.ceil(x)`. `Math.ceil(3.2)` is `4`; and `Math.ceil(-3.7)` is `-3`, because "up" means toward the larger value, not away from zero. The name is short for "ceiling."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Round up to the nearest whole number
let n = Math.ceil(3.2);  // 4
```

**What this does:** Reads the `ceil` method on the `Math` object and calls it with `3.2`, giving `4` — the smallest integer not less than the input.

### Example 2: Common Pattern

```javascript
// How many containers are needed to hold everything?
let items = 17;
let perBox = 5;
let boxes = Math.ceil(items / perBox);  // 4 (a partial box still counts)
```

**What this does:** Uses `Math.ceil` so any leftover forces an extra whole unit — the classic "round up to fit" calculation for pages, boxes, or batches.

### Example 3: Edge Case

```javascript
// A bare `ceil` is NOT this member — only `Math.ceil(...)` is
let ceil = "not the method";  // an ordinary variable named ceil
let m = Math.ceil(-3.7);      // THIS is the member → -3 (rounds UP, toward positive infinity)
```

**What this shows:** `ceil` counts as this member **only** in property position on its receiver (`Math.ceil(...)`). A standalone variable named `ceil` is a different thing entirely — the AST decides, not the spelling. Note the sign trap: `-3.7` ceils to `-3`, because "up" is toward positive infinity.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `floor` - The opposite `Math` static: rounds DOWN
2. `round` - The `Math` static that rounds to the *nearest* integer
3. `abs` - Another `Math` static transforming a single number

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** `ceil` ← "ceiling," from Latin *caelum* (sky, heaven) via Old French

**Root meaning:** A "ceiling" is the *upper* boundary of a room — the top. In mathematics, the "ceiling function" ⌈x⌉ is the least integer **≥ x** — you step *up* to the integer above the value, as if to the ceiling overhead.

**Why JavaScript uses this:** `ceil` is the standard mathematical abbreviation for the ceiling function, paired with `floor`. JS borrows the established math-notation terms directly; the clipped spelling `ceil` mirrors `⌈x⌉`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.ceil(x)` returns the least integer that is greater than or equal to `x` — it rounds **toward positive infinity**. For positive numbers this means "bump any fraction up to the next whole number": `Math.ceil(3.2)` is `4`, `Math.ceil(3.0)` is `3`. For negative numbers it is *not* "round away from zero": `Math.ceil(-3.7)` is `-3`, because `-3` is the smallest integer that is still `≥ -3.7`. This up-toward-larger behavior is the defining property and the main source of confusion.

`ceil` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.ceil(-3.7)` is the member; a learner's own variable named `ceil` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is semantic: the chosen word must mean "round UP / toward the larger integer," and must sit correctly opposite `floor` ("round down"). A further trap is the clipped English spelling — the translation should convey "ceiling," not a fragment.

**Key behaviors:**

1. **Rounds up:** returns the least integer `≥ x`, toward positive infinity.
2. **Not "away from zero" for negatives:** `Math.ceil(-3.7)` is `-3`, not `-4`.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `ceil` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun/verb naming a mathematical function ("ceiling function" / "round up")
- **Action vs State:** TRANSFORMATION - maps a real number to the integer above it
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's established math-class term for the **ceiling function** — "round up" / "least integer ≥ x." Prefer whatever pairs naturally as the opposite of `floor`, and convey the full "ceiling" idea rather than the truncated English spelling.

**Forms to AVOID:**

- ❌ A word meaning **"maximum / upper limit"** in a general sense - `ceil` is a rounding operation, distinct from `max`
- ❌ A word meaning **"round away from zero"** - wrong for negatives (`-3.7` ceils to `-3`)
- ❌ A generic "round" - that is `round` (nearest), not `ceil` (up)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Ceiling" as the **top surface of a room**
- ❌ Meaning 2: "Ceiling" as a **maximum allowed value** ("debt ceiling") — related but not the operation
- ✅ Meaning 3: **MATHEMATICAL CEILING FUNCTION** — round up to the least integer ≥ x

**Example:**

English "ceiling" can mean:

1. "The **ceiling** was high" (top of a room) ❌
2. "A spending **ceiling**" (an upper cap) ❌
3. "`Math.ceil(3.2)` returns 4" (round up to nearest integer) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: rounding UP to the nearest integer (toward positive infinity)** — not a room's ceiling and not a maximum cap.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ceil`, check these translations (the `Math` rounding family):**

- [ ] `floor` - The exact opposite; `ceil`/`floor` must read as an UP/DOWN pair
- [ ] `round` - Rounds to nearest; keep clearly distinct from `ceil`
- [ ] `max` - Do NOT let `ceil` collapse into "maximum"

**Consistency rule:**

`ceil`, `floor`, and `round` form a rounding trio and must stay mutually distinguishable: up, down, nearest. Translate `ceil` and `floor` as a matched opposite pair, using the same metaphor family the target language's mathematics uses for ⌈x⌉ and ⌊x⌋, and keep `ceil` separate from `max`.

### Functional relationships

**This term works WITH:**

1. **`Math.ceil` on a division**: Fit with a partial unit

```javascript
let pages = Math.ceil(records / pageSize);
```

**Common pairing:**

```javascript
// ceil and floor bracket a fractional value
let x = 4.3;
let high = Math.ceil(x);   // 5
let low = Math.floor(x);   // 4
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The ceiling function is standard in mathematics and most languages have a settled term, but `ceil` carries three traps at once: the clipped English spelling hides "ceiling," the negative-number rule surprises learners, and the word risks collapsing into "maximum / upper cap." The translator must convey the full ceiling-function idea, pair it opposite `floor`, and keep it distinct from `max`.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (round UP, toward positive infinity)?
- [ ] Correct for negatives (`-3.7` → `-3`, not `-4`)?
- [ ] Avoids the "room ceiling / spending cap / maximum" senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (function name / "round up")?
- [ ] Conveys full "ceiling," not a clipped fragment?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Forms a matched UP/DOWN pair with `floor`?
- [ ] Distinct from `round` (nearest) and `max` (maximum)?
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
term: ceil
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "round up to the least integer ≥ x" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it pairs as the opposite of `floor` and stays distinct from `max`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any "maximum" or literal "ceiling of a room" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (clipped spelling, negative-number rule, max collision) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
