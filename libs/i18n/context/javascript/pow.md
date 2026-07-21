# JavaScript Member: `pow` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.pow(2, 3)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** MEDIUM

---

## Quick Summary

`pow` is a static member method on the `Math` object that raises a **base** to an **exponent** (exponentiation). It is called as `Math.pow(base, exponent)`. `Math.pow(2, 3)` is `8` (2 × 2 × 2). The name is short for "power."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// 2 raised to the power 3
let n = Math.pow(2, 3);  // 8
```

**What this does:** Reads the `pow` method on the `Math` object and calls it with base `2` and exponent `3`, giving `8` — two multiplied by itself three times.

### Example 2: Common Pattern

```javascript
// Area of a square: side squared
let side = 5;
let area = Math.pow(side, 2);  // 25
```

**What this does:** Uses `Math.pow` with exponent `2` to square a value — the everyday "raise to a power" computation for areas, growth, and scaling.

### Example 3: Edge Case

```javascript
// A bare `pow` is NOT this member — only `Math.pow(...)` is
let pow = "not the method";   // an ordinary variable named pow
let m = Math.pow(9, 0.5);     // THIS is the member → 3 (a fractional exponent is a root)
```

**What this shows:** `pow` counts as this member **only** in property position on its receiver (`Math.pow(...)`). A standalone variable named `pow` is a different thing entirely — the AST decides, not the spelling. Note that a fractional exponent computes a root: `Math.pow(9, 0.5)` is `√9 = 3`.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `sqrt` - The `Math` static for square root — the inverse of squaring
2. `abs` - Another `Math` static transforming a number
3. `round` - Another `Math` static operating on numbers

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin *potentia* — "power, ability," via Old French

**Root meaning:** `pow` abbreviates "power." In mathematics, "raising to a power" means repeated multiplication — the exponent says how many times the base multiplies itself.

**Why JavaScript uses this:** `pow` is the standard math/computing shorthand for exponentiation (`xʸ`). It sits on the `Math` object with the other concise math names; JS also has the `**` operator for the same operation.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.pow(base, exponent)` returns `base` raised to `exponent`. For whole exponents this is repeated multiplication: `Math.pow(2, 3)` is `8`, `Math.pow(10, 4)` is `10000`. Exponent `0` gives `1` for any base. Negative exponents give reciprocals: `Math.pow(2, -1)` is `0.5`. Fractional exponents give roots: `Math.pow(9, 0.5)` is `3` (a square root), `Math.pow(27, 1/3)` is `3` (a cube root). It is equivalent to the `**` operator (`2 ** 3`).

`pow` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.pow(2, 3)` is the member; a learner's own variable named `pow` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is to pick the mathematical "power / exponentiation" term — the *operation*, distinct from the *exponent* (the `y` in `xʸ`) and from unrelated senses of "power" (strength, electricity, authority).

**Key behaviors:**

1. **Exponentiation:** `base` multiplied by itself `exponent` times (for whole exponents).
2. **Fractional/negative exponents:** roots and reciprocals, respectively.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `pow` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun/verb naming a mathematical operation ("power / raise to a power")
- **Action vs State:** OPERATION - raises a base to an exponent
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's standard math term for **exponentiation / "raise to a power."** It should name the operation, and ideally align with how the `**` operator is described in that language's mathematics.

**Forms to AVOID:**

- ❌ A word meaning **"exponent"** alone - that is the argument `y`, not the operation `xʸ`
- ❌ "Power" in the sense of **strength / electricity / authority** - wrong domain
- ❌ A word meaning **"multiply"** - power is *repeated* multiplication, a distinct operation

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Power" as **authority / control**
- ❌ Meaning 2: "Power" as **energy / electricity**
- ✅ Meaning 3: **MATHEMATICAL POWER** — exponentiation (xʸ)
- ❌ Meaning 4: "Power" as **strength / capability**

**Example:**

English "power" can mean:

1. "Political **power**" (authority) ❌
2. "Electrical **power**" (energy) ❌
3. "`Math.pow(2, 3)` returns 8" (mathematical exponentiation, 2³) ✅ **This is the JavaScript meaning**
4. "Physical **power**" (strength) ❌

**Your translation should capture meaning #3: the mathematical operation of raising a base to an exponent** — not strength, energy, or authority, and not the bare "exponent."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `pow`, check these translations:**

- [ ] `sqrt` - Square root is a special inverse (`Math.pow(x, 0.5)`); keep the relationship coherent
- [ ] `abs` - Sibling `Math` static
- [ ] `round` / `floor` / `ceil` - Sibling `Math` statics for family consistency

**Consistency rule:**

`pow` and `sqrt` are conceptually linked (a square root is a power of ½), so their translations should sit comfortably together in the same mathematical vocabulary. Choose the "power / exponentiation" term for `pow` such that "square root" for `sqrt` reads as a related, not conflicting, idea.

### Functional relationships

**This term works WITH:**

1. **`Math.pow` for squares and cubes**: Raise to small whole powers

```javascript
let cube = Math.pow(x, 3);
```

**Common pairing:**

```javascript
// pow with a fractional exponent equals a root
let root = Math.pow(16, 0.5);  // 4
let same = Math.sqrt(16);      // 4 (the sqrt member does the same)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** Exponentiation is a universal, school-taught operation, so a term almost always exists — that keeps it from HARD. The MEDIUM edge is the word "power": it is heavily overloaded (strength, energy, authority), and it must not collapse into "exponent" (the argument) or "multiply." The translator has to name the *operation* in the mathematical sense and align it with the `**` operator's description.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (raise a base to an exponent)?
- [ ] Names the OPERATION, not the "exponent" argument?
- [ ] Avoids "strength / energy / authority" senses of "power"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (operation name)?
- [ ] Uses the standard school-math term for exponentiation?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Coherent with `sqrt` (power of ½)?
- [ ] Aligns with the `**` operator's description?
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
term: pow
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "raise a base to an exponent" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it names the operation, not the exponent.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any "exponent," "strength," or "multiply" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (overloaded "power," operation-vs-exponent) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
