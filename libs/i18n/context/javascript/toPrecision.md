# JavaScript Member: `toPrecision` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (function)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Number
**Receivers (live in JEJ today):** Number — `toPrecision` is a Number method in full JS too, so there is no widening beyond Number
**Ships in JEJ:** yes (member; Number-only, but still qualified — bounded by its receiver)
**Difficulty:** MEDIUM

---

## Quick Summary

`toPrecision` is a member method on numbers that formats a number to a given total count of **significant digits** and returns the result as a **string**. It is called as `value.toPrecision(n)`, where `n` is how many significant figures to keep. Contrast `toFixed`, which fixes the count of digits *after the decimal point*; `toPrecision` fixes the count of *significant* digits across the whole number.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Keep 3 significant digits
let x = 12.345;
let s = x.toPrecision(3);  // "12.3"
```

**What this does:** Reads the `toPrecision` method on the number `12.345` and calls it with `3`, producing the string `"12.3"` — three significant digits, counted from the first non-zero digit.

### Example 2: Common Pattern

```javascript
// Display a measurement with a fixed number of significant figures
let reading = 0.0045678;
let shown = reading.toPrecision(2);  // "0.0046"
```

**What this does:** Uses `toPrecision` to report a lab-style reading to two significant figures. Leading zeros do not count as significant, so the two figures are `4` and `6`.

### Example 3: Edge Case

```javascript
// A bare `toPrecision` is NOT this member — only `x.toPrecision(...)` is
let toPrecision = "not the method";  // an ordinary variable
let s = (255).toPrecision(2);        // THIS is the member → "2.6e+2"
```

**What this shows:** `toPrecision` counts as this member **only** in property position after a dot (`(255).toPrecision(2)`). A standalone variable that happens to be named `toPrecision` is a different thing entirely — the AST decides (a non-computed `MemberExpression.property`), not the spelling. Note too that when the requested precision is fewer digits than the integer part needs, the result switches to exponential notation (`"2.6e+2"`).

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `toFixed` - The sibling Number-formatting method; fixes decimal places, not significant digits
2. `toString` - Also a Number member that produces a string representation
3. `valueOf` - Also a Number member returning the underlying value

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** `to` + Latin *praecisio*

**Root meaning:** Latin *praecidere* — "to cut off" (*prae-* "before" + *caedere* "to cut"). "Precision" came to mean exactness, the number of digits to which a value is expressed. The `to` prefix marks a conversion — "produce, as a value, the number rendered *to* this precision."

**Why JavaScript uses this:** The method converts a number *to* a string carrying a specified **precision** — a fixed count of significant digits. It follows JS's `toX` naming family (`toString`, `toFixed`, `toPrecision`), all meaning "render this value as X."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`toPrecision(n)` renders a number as a string with exactly `n` significant digits. Significant digits are counted from the first non-zero digit, regardless of the decimal point's position. `(12.345).toPrecision(3)` is `"12.3"`; `(0.0045678).toPrecision(2)` is `"0.0046"`. If `n` demands more digits than the number has, the result is padded with zeros (`(1.5).toPrecision(4)` → `"1.500"`). If `n` is too small to show the integer part in fixed notation, JavaScript falls back to exponential notation (`(255).toPrecision(2)` → `"2.6e+2"`).

This is the key contrast with `toFixed`: `toFixed(2)` fixes **two digits after the decimal point** (`(12.345).toFixed(2)` → `"12.35"`), while `toPrecision(2)` fixes **two significant digits total** (`(12.345).toPrecision(2)` → `"12"`). One counts decimal places; the other counts significant figures. A translation that blurs the two will read wrong next to `toFixed`.

`toPrecision` is a **member**: it only means this concept when it sits in property position after a dot. `(255).toPrecision(2)` is the member; a learner's own variable named `toPrecision` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

**Key behaviors:**

1. **Returns a string:** the output is text, not a number — for display, not further arithmetic.
2. **Counts significant digits, not decimal places:** the defining contrast with `toFixed`.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `toPrecision` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase / method name — "render to a precision"
- **Action vs State:** ACTION - it produces a formatted string from the number
- **Temporal aspect:** None - an on-demand conversion

### Recommended Form

**Primary recommendation:** Use a verb or verb phrase meaning **"render to N significant digits"** — ideally echoing the `to…` conversion family so it pairs cleanly with `toFixed` and `toString`. The core semantic to carry is **significant digits / precision**, distinct from decimal places.

**Forms to AVOID:**

- ❌ A word meaning **"round to N decimal places"** - that is `toFixed`, not `toPrecision`; the two must stay distinguishable
- ❌ A pure noun "precision" with no conversion sense - the member is a method that *produces* a string, an action
- ❌ A word meaning **"accuracy / correctness"** - "precision" here is a digit count, not truthfulness

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Precision" as **accuracy / being correct** ("surgical precision")
- ❌ Meaning 2: "Precision" as **decimal places** (the `toFixed` reading)
- ✅ Meaning 3: **"COUNT OF SIGNIFICANT DIGITS"** — how many significant figures to render

**Example:**

English "precision" can mean:

1. "She answered with **precision**" (exactness / accuracy) ❌
2. "Two decimal places of **precision**" (decimal places — the `toFixed` sense) ❌
3. "Express the value to 3 significant figures" (significant digits) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: significant-digit count, NOT accuracy and NOT decimal places** — because `toFixed` already owns the decimal-places idea, and the two members must not collapse into one word.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `toPrecision`, check these translations (the Number-formatting / conversion family):**

- [ ] `toFixed` - The sibling that fixes decimal places; keep it clearly DISTINCT from significant digits
- [ ] `toString` - Same `to…` conversion family; align the "render as" framing
- [ ] `valueOf` - Number member returning the underlying value

**Consistency rule:**

Keep the `to…` conversion family recognizable as a family, but make sure `toPrecision` and `toFixed` remain **distinguishable** — one carries "significant digits," the other "decimal places." If a language collapses both into a single "round" word, the reversibility guarantee (Rule 2) breaks.

### Functional relationships

**This term works WITH:**

1. **`toPrecision` + display**: Show a value to a set number of significant figures

```javascript
let v = 3.14159;
let label = v.toPrecision(3);  // "3.14"
```

**Common pairing:**

```javascript
// Contrast the two formatters side by side
let n = 12.345;
let a = n.toPrecision(2);  // "12"    (2 significant digits)
let b = n.toFixed(2);      // "12.35" (2 decimal places)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** "Significant digits / precision" is a real concept in every school mathematics tradition, so a term usually exists. The difficulty is the collision risk with `toFixed`: many languages have one everyday "round to N places" word, and reaching for it here erases the significant-digits distinction. The translator must pick a term that reads as *significant figures* and stays separable from `toFixed`, ideally within the `to…` conversion family.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (significant digits, returns a string)?
- [ ] Clearly DISTINCT from `toFixed` (decimal places)?
- [ ] Avoids the "accuracy / correctness" connotation of "precision"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / method phrase)?
- [ ] Correct form (conversion "render to N figures")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Fits the `to…` conversion family (`toString`, `toFixed`)?
- [ ] Stays reversibly distinct from `toFixed`?
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
term: toPrecision
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Number]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "render to N significant digits" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays distinct from `toFixed`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "decimal places" or "accuracy."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (toFixed collision, precision-as-accuracy bias) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
