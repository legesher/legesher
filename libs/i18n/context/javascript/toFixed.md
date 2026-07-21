# JavaScript Member: `toFixed` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** Number
**Receivers (live in JEJ today):** Number — Number-only in full JS too; there is no widening for this member
**Ships in JEJ:** yes (member; Number-only)
**Difficulty:** MEDIUM

---

## Quick Summary

`toFixed` is a member method on numbers that formats the number using a fixed number of decimal places and returns the result as a **string**. It is called as `value.toFixed(digits)`; it rounds to that many decimals and always yields text, not a number.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Two decimal places
let price = 3.1;
let shown = price.toFixed(2);   // "3.10" (a string)
```

**What this does:** Calls `toFixed` on `3.1`, formatting it with exactly two decimal places and returning the **string** `"3.10"` — note the padded zero.

### Example 2: Common Pattern

```javascript
// Format a computed amount for display
let total = 19.9975;
let label = "$" + total.toFixed(2);   // "$20.00"
```

**What this does:** Uses `toFixed` to round and pad a number to a fixed number of decimals for display — the everyday "show this as money / a tidy figure" step. It rounds (`19.9975` → `"20.00"`).

### Example 3: Edge Case

```javascript
// A bare `toFixed` is NOT this member — only `x.toFixed(...)` is
let toFixed = true;              // an ordinary variable named toFixed
let shown = (2.5).toFixed(1);   // THIS is the member → "2.5"
```

**What this shows:** `toFixed` counts as this member **only** in property position (`(2.5).toFixed(...)`). A standalone variable that happens to be named `toFixed` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `toPrecision` - The sibling Number-formatting member (significant digits rather than decimals)
2. `toString` - Also converts a value to text (the general Number→string member)
3. `repeat` - Also a member that returns a string built by a formatting/producing rule

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** English (compound: "to" + "fixed")

**Root meaning:** "to" (convert/toward) + "fixed" (Latin *fixus*, "fastened, set, unchanging"). "Fixed" here is the technical sense of *fixed-point notation* — a set, unvarying number of decimal places.

**Why JavaScript uses this:** JavaScript names the operation `toFixed` — "render this number in **fixed**-point notation with N decimals." The "fixed" refers to a *fixed count of decimal places*, not to *repairing* anything.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`toFixed` is a method read from a value with the `receiver.toFixed(digits)` shape. It rounds the number to `digits` decimal places, pads with trailing zeros if needed, and returns the result as a **string** (e.g., `3.1 .toFixed(2)` → `"3.10"`). Two facts define it: it produces *text*, and it uses *fixed-point* notation (a set number of decimals). This member is Number-only, even in full JavaScript; there is no string or array form, so no receiver-widening to worry about.

Critically, `toFixed` is a **member**: it only means this concept when it sits in property position after a dot. `(2.5).toFixed(1)` is the member; a learner's own variable named `toFixed` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition of the native word across receivers is never a collision; the pack scores `toFixed` under Rule 2 (reversibility), not Rule 1. The load-bearing senses to carry are *format to a fixed number of decimals* and *return text* — the word must not read as "repair/fix" and should not imply the result is still a number.

**Key behaviors:**

1. **Fixed decimals:** the argument is *how many decimal places* to show.
2. **Returns a string:** the output is text, even though the input is a number; it also rounds.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `toFixed` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a number-formatting transform
- **Action vs State:** ACTION - it formats a number and returns a string
- **Temporal aspect:** Present-tense operation — "format to N decimals, now"

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **format to a fixed number of decimal places** — the "fixed-point / N decimals" sense. Where the language allows, signal that the result is *displayable text*. Prefer "format / round to N decimals" over a bare "round."

**Forms to AVOID:**

- ❌ A word meaning **"fix / repair / mend"** - a false friend of English "fixed"; nothing is being repaired
- ❌ A word meaning **"fasten / attach in place"** - the other sense of "fix"; wrong here
- ❌ A word implying the result stays a **number** - the output is a string; avoid a purely arithmetic reading
- ❌ A noun form - `toFixed` is the formatting action

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Repair / mend" ("fix the bug")
- ❌ Meaning 2: "Fasten in place / make unmovable" ("fix the shelf to the wall")
- ✅ Meaning 3: **"FIXED-POINT: FORMAT TO N DECIMAL PLACES (AS TEXT)"**

**Example:**

English "fixed" can mean:

1. "I **fixed** the leak" (repaired) ❌
2. "The post is **fixed** in concrete" (fastened) ❌
3. "Show it in **fixed**-point with 2 decimals → `'3.10'`" (a set number of decimals, as text) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: formatting a number to a fixed count of decimals and returning text, NOT repairing or fastening.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `toFixed`, check these translations:**

- [ ] `toPrecision` - The other Number-formatting member; keep the "format a number for display" family consistent (decimals vs significant digits)
- [ ] `toString` - The general "convert to text" member; `toFixed` is a decimals-specific formatting case
- [ ] `repeat` - Another member returning a produced/formatted string

**Consistency rule:**

`toFixed` and `toPrecision` are both Number→string formatters and should read as a family (both "format this number as text"), while remaining distinguishable — `toFixed` counts *decimal places*, `toPrecision` counts *significant digits*. Keep the "produces text" quality consistent with `toString`.

### Functional relationships

**This term works WITH:**

1. **`toFixed` + display / concatenation**: The presenter

```javascript
let avg = 4.6667;
let text = "Average: " + avg.toFixed(1);   // "Average: 4.7"
```

**Common pairing:**

```javascript
// toFixed formats a number into a string used in output
let pct = 0.256;
let shown = (pct * 100).toFixed(1) + "%";   // "25.6%"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (format to N decimals as text) is well-defined, but "fixed" is a strong false friend — in many languages the nearest word means *repair* or *fasten*, both wrong. The translator must reach the *fixed-point / set number of decimals* sense and, ideally, signal that the result is a string, not a number. Escaping the "repair" reading is the main challenge.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (format to N decimal places, return text)
- [ ] Reads as "fixed-point / set decimals," not "repair" or "fasten"?
- [ ] Conveys (or at least does not contradict) that the result is a string?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a number-formatting transform)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the Number-formatting family (`toPrecision`, `toString`)?
- [ ] Distinguishable from `toPrecision` (decimals vs significant digits)?
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
term: toFixed
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [Number]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "format to a fixed number of decimal places (as text)" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it avoids the "repair / fasten" readings.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any "fix / repair" false friends.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (the "fixed" false-friend, signaling a string result, contrast with `toPrecision`) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
