# JavaScript Member: `sqrt` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.sqrt(9)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** MEDIUM

---

## Quick Summary

`sqrt` is a static member method on the `Math` object that returns the **square root** of a number — the non-negative value that, multiplied by itself, gives the input. It is called as `Math.sqrt(x)`. `Math.sqrt(9)` is `3`. The name is short for "square root."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// The square root of 9
let n = Math.sqrt(9);  // 3
```

**What this does:** Reads the `sqrt` method on the `Math` object and calls it with `9`, giving `3` — the number that, squared, equals `9`.

### Example 2: Common Pattern

```javascript
// Distance via the Pythagorean theorem
let dx = 3;
let dy = 4;
let distance = Math.sqrt(dx * dx + dy * dy);  // 5
```

**What this does:** Uses `Math.sqrt` to finish a Pythagorean distance calculation — one of the most common real uses of square root in code.

### Example 3: Edge Case

```javascript
// A bare `sqrt` is NOT this member — only `Math.sqrt(...)` is
let sqrt = "not the method";  // an ordinary variable named sqrt
let m = Math.sqrt(-1);        // THIS is the member → NaN (no real square root)
```

**What this shows:** `sqrt` counts as this member **only** in property position on its receiver (`Math.sqrt(...)`). A standalone variable named `sqrt` is a different thing entirely — the AST decides, not the spelling. Note that a negative input has no real square root, so the result is `NaN`.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `pow` - The `Math` static for exponentiation; a square root is `Math.pow(x, 0.5)`
2. `abs` - Another `Math` static transforming a number
3. `round` - Another `Math` static operating on numbers

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** `sq` + `rt` — clipped from "square root"

**Root meaning:** A "square root" of `n` is the number whose *square* (itself times itself) is `n` — the inverse of squaring. "Square" comes from the geometric square, whose area is a side length multiplied by itself. The radical sign √ denotes it in mathematics.

**Why JavaScript uses this:** `sqrt` is the universal computing abbreviation for "square root," inherited from C and the wider math-library tradition. It sits on the `Math` object with the other concise math names.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.sqrt(x)` returns the non-negative square root of `x`: the value `r ≥ 0` such that `r * r === x`. `Math.sqrt(9)` is `3`, `Math.sqrt(2)` is about `1.414`, `Math.sqrt(0)` is `0`. Because no real number squares to a negative, `Math.sqrt(-1)` is `NaN`. It is the exact inverse of squaring and equals `Math.pow(x, 0.5)`.

`sqrt` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.sqrt(9)` is the member; a learner's own variable named `sqrt` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is to convey the full "square root" idea (not a clipped fragment) and to keep it coherent with `pow`, since a square root is a power of one half.

**Key behaviors:**

1. **Square root:** returns the non-negative `r` with `r * r === x`.
2. **NaN for negatives:** no real square root exists for `x < 0`.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `sqrt` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun/verb naming a mathematical function ("square root")
- **Action vs State:** OPERATION - maps a number to its non-negative square root
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's established math-class term for **"square root"** (the √ operation). Convey the full concept rather than the clipped English spelling `sqrt`.

**Forms to AVOID:**

- ❌ A word meaning **"square" (the shape or squaring)** alone - that is the *inverse*; a square root undoes squaring
- ❌ A word meaning **"root" (of a plant / of a word)** with no "square" qualifier - too generic; loses the ½-power meaning
- ❌ A generic "power" word - that is `pow`; `sqrt` is one specific power (½)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (chiefly through the word "root")

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Root" as the **underground part of a plant**
- ❌ Meaning 2: "Root" as an **origin / base** ("root of the problem," "root directory")
- ✅ Meaning 3: **MATHEMATICAL SQUARE ROOT** — the value whose square is x (√x)

**Example:**

"Root" in English can mean:

1. "The **root** of the tree" (plant) ❌
2. "The **root** of the problem" (origin) ❌
3. "`Math.sqrt(9)` returns 3" (square root, √9) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the mathematical square root (√x)** — the specific "square" root, not a generic root and not the plant/origin senses.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `sqrt`, check these translations:**

- [ ] `pow` - Exponentiation; a square root is a power of ½ — keep the two coherent
- [ ] `abs` - Sibling `Math` static
- [ ] `round` / `floor` / `ceil` - Sibling `Math` statics for family consistency

**Consistency rule:**

`sqrt` and `pow` are conceptually linked (√x = x^½), so their translations should live in the same mathematical vocabulary. Choose the "square root" term for `sqrt` so it reads as a natural companion to the "power" term for `pow`, not a disconnected word.

### Functional relationships

**This term works WITH:**

1. **`Math.sqrt` in distance formulas**: Pythagorean length

```javascript
let dist = Math.sqrt(a * a + b * b);
```

**Common pairing:**

```javascript
// sqrt is a power of one half
let r1 = Math.sqrt(16);      // 4
let r2 = Math.pow(16, 0.5);  // 4 (same value)
```

---

## Confidence Calibration

**Translation Difficulty: EASY-MEDIUM**

**For this term:** EASY-MEDIUM

**Rationale:** Square root is standard school mathematics with a settled term in nearly every language, which keeps it from HARD. The MEDIUM edge comes from the word "root," which is polysemous (plant, origin, word-root), and from the clipped English spelling `sqrt`: the translation must convey the *square* root specifically and stay coherent with `pow`.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (square root, √x)?
- [ ] Specifically the *square* root (not a generic root)?
- [ ] Avoids the "plant root / origin" senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (function name / "square root")?
- [ ] Conveys full "square root," not a clipped fragment?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Coherent with `pow` (power of ½)?
- [ ] Fits the `Math.*` static family?
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
term: sqrt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "square root (√x)" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays coherent with `pow`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any generic "root" or "square/squaring" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (polysemous "root," clipped spelling) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
