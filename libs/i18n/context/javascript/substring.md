# JavaScript Member: `substring` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String
**Receivers (live in JEJ today):** String — this member is String-only in full JS too, so no widening is expected
**Ships in JEJ:** yes (member; String-only)
**Difficulty:** MEDIUM

---

## Quick Summary

`substring` is a member method that returns the **portion of a string between two indices** — the characters from `start` up to (but not including) `end`. It is called as `text.substring(start, end)`. It is very close in behaviour to `slice` on strings; the two must be translated to *different* native words so a reader can tell them apart.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Take characters 0..3 (not including 3)
let word = "javascript";
let part = word.substring(0, 3);   // "jav"
```

**What this does:** Calls `substring` with `start = 0` and `end = 3`, returning `"jav"`. The end index is exclusive. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// From position 4 to the end
let email = "ada@site.com";
let domain = email.substring(4);   // "site.com"
```

**What this does:** With only a `start`, `substring` runs to the end of the string — the "take everything from position N onward" pattern.

### Example 3: Edge Case

```javascript
// A bare `substring` is NOT this member — only `x.substring(...)` is
let substring = "label";               // an ordinary variable named substring
let real = "hello".substring(1, 3);    // THIS is the member  -> "el"
```

**What this shows:** `substring` counts as this member **only** in property position before the call (`"hello".substring(1, 3)`). A standalone variable happening to be named `substring` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `slice` - Very close cousin: also extracts a sub-range of a string (must stay DISTINCT)
2. `charAt` - Also index-based on a string; returns a single character
3. `indexOf` - Also positional; finds where a value sits

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound — "sub-" (under, part of) + "string."

**Root meaning:** "A string that is a part of another string" — a contiguous piece of the whole. "Sub-" from Latin, "below / part of."

**Why JavaScript uses this:** The result is literally a *substring* — a slice of text between two positions. The name is the noun for the thing produced, used here as the verb that produces it.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`substring` is a method read from a string with the `string.substring(start, end)` shape. It returns the **characters between two indices** — from `start` up to (but not including) `end`. If `start > end`, `substring` swaps them; negative arguments are treated as `0`. The original string is never modified.

Critically, `substring` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"hello".substring(1, 3)` is the member; a learner's own variable named `substring` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

`substring` is String-only in full JavaScript, so there is no widening trap. The central challenge is **overlap with `slice`**: on strings the two produce nearly identical results (they differ only in edge-case argument handling — negative and swapped indices). English gives them two distinct names, and the native pack must too. Under Rule 2, two live members cannot share a word, or a reader could not reverse-map the native form to the right member. Choose a word here that reads as "the portion / part of the string between positions" and reserve the more general "cut a section" reading for `slice`.

**Key behaviors:**

1. **Method, not property:** called as `x.substring(a, b)` with `()`.
2. **String-only receiver:** no widening to arrays.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `substring` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning a portion of text
- **Action vs State:** ACTION - it extracts and returns a portion
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"take the part of the text between two positions"** — a "portion / part of a string" framing. It is text-specific (String-only), so a word tied to text is acceptable here, unlike `slice`.

**Forms to AVOID:**

- ❌ The **same word chosen for `slice`** - they must stay distinct under Rule 2
- ❌ A word meaning **"cut off / remove"** - `substring` does not modify the original
- ❌ A noun form - `substring` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

MILD

**If MILD, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Sub-string" as in a lesser cord / a physical string underneath another
- ✅ Meaning 2: **"A CONTIGUOUS PORTION OF TEXT BETWEEN TWO POSITIONS"** — a piece of the string

**Example:**

English "substring" can suggest:

1. a literal secondary "string" / cord ❌
2. "the **substring** from index 1 to 3 is `'el'`" (a piece of the text) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #2: a contiguous portion of the string between two positions — distinct from `slice`, and non-destructive.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `substring`, check these translations:**

- [ ] `slice` - Near-identical on strings; must be a DISTINCT native word or reversibility breaks
- [ ] `charAt` - Also index-based on strings; keep positional language consistent
- [ ] `indexOf` - Positional companion; align "position / index" wording

**Consistency rule:**

`substring` and `slice` both extract a sub-range of a string and both live in JEJ today. Under Rule 2 (reversibility within the members partition) they MUST map to two clearly different native words — this is the single most important check for this term. Reserve the general "take a section (also arrays)" word for `slice` and use a distinct "part-of-the-text between positions" word here.

### Functional relationships

**This term works WITH:**

1. **`substring` + `indexOf`**: find a boundary, then take the part before/after it

```javascript
let file = "report.pdf";
let base = file.substring(0, file.indexOf("."));   // "report"
```

**Common pairing:**

```javascript
// fixed-window extraction
let stamp = "2026-07-21";
let year = stamp.substring(0, 4);   // "2026"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept ("a piece of the string between two positions") is concrete and String-only, so there is no widening trap. The whole difficulty is the near-synonymy with `slice`: the translator must deliberately choose a *different* native word from `slice` while both still read as "extract a portion." That forced-distinction, plus the non-destructive nuance, keeps this at MEDIUM rather than EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (portion of text between two indices)?
- [ ] Reads correctly for the String receiver?
- [ ] Avoids the "cut off / remove" connotation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("part of the text between positions")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `slice` (the critical check)?
- [ ] Positional wording aligned with `charAt` / `indexOf`?
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
term: substring
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "a portion of the string between two positions" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it is clearly distinct from the word chosen for `slice`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that collided with `slice` or implied destructive cutting.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (near-synonymy with `slice`, forced-distinction requirement) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
