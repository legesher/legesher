# JavaScript Member: `round` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (static function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Math (static) — the receiver is the `Math` object, as in `Math.round(2.5)`
**Receivers (live in JEJ today):** Math — a static method with a single fixed receiver; no receiver-widening
**Ships in JEJ:** yes (member; receiver is the `Math` object)
**Difficulty:** EASY

---

## Quick Summary

`round` is a static member method on the `Math` object that rounds a number to the **nearest integer**. It is called as `Math.round(x)`. A fractional part of `0.5` or more rounds up, below `0.5` rounds down: `Math.round(2.4)` is `2`, `Math.round(2.5)` is `3`. Note the half-up tie rule: `Math.round(-2.5)` is `-2`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Round to the nearest whole number
let n = Math.round(2.5);  // 3
```

**What this does:** Reads the `round` method on the `Math` object and calls it with `2.5`, giving `3` — the nearest integer, with a `.5` tie going up.

### Example 2: Common Pattern

```javascript
// Round a computed average for display
let scores = 271;
let count = 4;
let average = Math.round(scores / count);  // 68 (from 67.75)
```

**What this does:** Uses `Math.round` to present a fractional result as the nearest whole number — the everyday "clean up this figure" step.

### Example 3: Edge Case

```javascript
// A bare `round` is NOT this member — only `Math.round(...)` is
let round = "not the method";  // an ordinary variable named round
let m = Math.round(-2.5);      // THIS is the member → -2 (ties round toward +∞)
```

**What this shows:** `round` counts as this member **only** in property position on its receiver (`Math.round(...)`). A standalone variable named `round` is a different thing entirely — the AST decides, not the spelling. Note the tie rule: `-2.5` rounds to `-2`, because half-values always round toward positive infinity.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `floor` - The `Math` static that rounds DOWN
2. `ceil` - The `Math` static that rounds UP
3. `abs` - Another `Math` static transforming a single number

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (here the `Math` object) and syntactically by the dot, **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin *rotundus* (round, wheel-shaped) via Old French *rond*

**Root meaning:** "Round" originally meant circular. The numeric sense — "to make a number *round*, i.e. neat / whole" — grew from the idea of a tidy figure without awkward fractions.

**Why JavaScript uses this:** `round` is the ordinary mathematical term for adjusting a number to the nearest whole (or nearest place value). It sits alongside `floor` and `ceil` as the "nearest" member of the rounding trio.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math.round(x)` returns the integer nearest to `x`. When the fractional part is exactly `0.5`, JavaScript's rule is "round half toward positive infinity": `Math.round(2.5)` is `3`, but `Math.round(-2.5)` is `-2` (not `-3`). Away from ties it behaves as everyone expects: `Math.round(2.4)` is `2`, `Math.round(2.6)` is `3`. This makes it the general-purpose rounder, in contrast to `floor` (always down) and `ceil` (always up).

`round` is a **member** on the `Math` object: it only means this concept when it sits in property position after a dot on its receiver. `Math.round(-2.5)` is the member; a learner's own variable named `round` (say, a game round counter) is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The receiver is fixed as `Math`, so there is no receiver-widening to plan for. The care here is to pick the "round to nearest" math term and keep it distinct from the directional `floor`/`ceil`, and from the everyday "round" that can mean a circle or a repetition.

**Key behaviors:**

1. **Rounds to nearest:** below `.5` down, `.5` and above up.
2. **Half-up tie rule:** ties round toward positive infinity (`-2.5` → `-2`).
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `round` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a mathematical operation ("round to nearest")
- **Action vs State:** TRANSFORMATION - maps a real number to the nearest integer
- **Temporal aspect:** None - an on-demand computation

### Recommended Form

**Primary recommendation:** Use the target language's standard math term for **"round to the nearest (whole number)."** It should read as the neutral, non-directional rounder that `floor` and `ceil` are the directional variants of.

**Forms to AVOID:**

- ❌ A word meaning **"circle / circular"** - the geometric sense of "round," wrong domain
- ❌ A word meaning **"a round / a repetition / a turn"** ("round 2 of a game")
- ❌ Reusing the exact `floor` or `ceil` word - `round` is *nearest*, not directional

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Round" as **circular / a shape**
- ❌ Meaning 2: "Round" as **a repetition / a turn** ("the next round")
- ✅ Meaning 3: **MATHEMATICAL ROUNDING** — adjust to the nearest whole number

**Example:**

English "round" can mean:

1. "A **round** table" (circular shape) ❌
2. "**Round** two of the contest" (a stage / turn) ❌
3. "`Math.round(2.5)` returns 3" (round to nearest integer) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: rounding to the NEAREST integer** — not a shape and not a repetition/turn.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `round`, check these translations (the `Math` rounding family):**

- [ ] `floor` - Directional DOWN; keep `round` distinct as "nearest"
- [ ] `ceil` - Directional UP; keep `round` distinct as "nearest"
- [ ] `abs` - Sibling `Math` static

**Consistency rule:**

`round`, `floor`, and `ceil` form a rounding trio and must stay mutually distinguishable: nearest, down, up. Choose the plain "round to nearest" term for `round` so that `floor`/`ceil` clearly read as its directional cousins, not synonyms.

### Functional relationships

**This term works WITH:**

1. **`Math.round` for display figures**: Nearest whole

```javascript
let percent = Math.round(ratio * 100);
```

**Common pairing:**

```javascript
// The trio on one value
let x = 2.5;
let near = Math.round(x);  // 3
let down = Math.floor(x);  // 2
let up = Math.ceil(x);     // 3
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** "Round to the nearest number" is a universal, early-taught idea with a settled term in essentially every language, so this maps cleanly. The only care is choosing the math sense (not "circle" or "a turn") and keeping it distinct from the directional `floor`/`ceil` — routine work that rarely needs review.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (round to NEAREST integer)?
- [ ] Not directional (distinct from floor/ceil)?
- [ ] Avoids the "circle" and "a turn / repetition" senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / operation name)?
- [ ] Uses the standard school-math "round to nearest" term?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Distinct from `floor` (down) and `ceil` (up)?
- [ ] Reads as the neutral rounder of the trio?
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
term: round
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Math]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "round to the nearest integer" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays distinct from `floor` and `ceil`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any "circle" or "turn/repetition" candidates.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (circle/turn homonyms, directional collision) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
