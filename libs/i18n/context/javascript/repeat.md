# JavaScript Member: `repeat` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String
**Receivers (live in JEJ today):** String — String-only in full JS too; there is no widening for this member
**Ships in JEJ:** yes (member; String-only)
**Difficulty:** MEDIUM

---

## Quick Summary

`repeat` is a member method that returns a new string made of the original repeated a given number of times. It is called as `value.repeat(n)` and yields a fresh string; the original is unchanged.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Repeat "ab" three times
let unit = "ab";
let line = unit.repeat(3);   // "ababab"
```

**What this does:** Calls the `repeat` method on `"ab"`, building a new string that is `"ab"` concatenated with itself three times.

### Example 2: Common Pattern

```javascript
// Build a divider row
let bar = "-".repeat(20);
```

**What this does:** Uses `repeat` to produce a run of the same character — the everyday "give me N copies joined together" pattern.

### Example 3: Edge Case

```javascript
// A bare `repeat` is NOT this member — only `x.repeat(...)` is
let repeat = 3;                  // an ordinary variable named repeat
let dots = ".".repeat(repeat);  // THIS (the .repeat call) is the member
```

**What this shows:** `repeat` counts as this member **only** in property position (`".".repeat(...)`). A standalone variable that happens to be named `repeat` is a different thing entirely — the AST decides, not the spelling. (Note both appear on one line here: the variable and the member are still distinct nodes.)

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `concat` - Also builds a new string by joining copies/pieces together
2. `slice` - Also returns a new string derived from the original (a piece rather than copies)
3. `replace` - Also returns a new string, leaving the original untouched

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin (via Old French)

**Root meaning:** Latin *repetere* — "to seek again, do again" (*re-* "again" + *petere* "to seek, aim for"). Modern English "repeat" means "to do or produce again."

**Why JavaScript uses this:** JavaScript names the copy-and-join operation `repeat` — "give me this string, done again N times." The reading is *produce N copies concatenated*, not *say something again aloud*.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`repeat` is a method read from a value with the `receiver.repeat(n)` shape. It returns a **new** string consisting of the receiver joined to itself `n` times; `n` is a count. The receiver is not mutated — like most JS string methods, it produces a fresh value. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `repeat` is a **member**: it only means this concept when it sits in property position after a dot. `"x".repeat(3)` is the member; a learner's own variable named `repeat` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition of the native word across receivers is never a collision; the pack scores `repeat` under Rule 2 (reversibility), not Rule 1. The load-bearing sense is *make N joined copies* — a productive, count-driven operation, not the conversational "say it again."

**Key behaviors:**

1. **Returns a new string:** the original is left unchanged.
2. **Count-driven:** the argument is *how many times* to repeat.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `repeat` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a transform (produce copies)
- **Action vs State:** ACTION - it builds and returns a new string
- **Temporal aspect:** Present-tense operation — "repeat it N times, now"

### Recommended Form

**Primary recommendation:** Use a verb meaning **repeat / duplicate N times** — the sense of producing multiple joined copies of the same string. A word that pairs naturally with a count ("repeat 3 times") reads best.

**Forms to AVOID:**

- ❌ A word meaning **"say/tell again"** (verbal repetition) - wrong register; this produces text, it does not speak
- ❌ A word meaning **"loop / iterate"** - `repeat` does not loop over items; it multiplies one string
- ❌ A noun form ("a repetition") - `repeat` is the action of producing copies

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Say again aloud" ("please repeat that")
- ❌ Meaning 2: "Recur / happen again" ("the error repeats")
- ✅ Meaning 3: **"PRODUCE N JOINED COPIES"** — build a new string of N repetitions

**Example:**

English "repeat" can mean:

1. "Could you **repeat** the question?" (say again aloud) ❌
2. "The pattern **repeats** every week" (recurs over time) ❌
3. "`'ab'.repeat(3)`" (produce `'ababab'`) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: producing N joined copies of a string, NOT speaking again or recurring over time.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `repeat`, check these translations:**

- [ ] `concat` - Also joins strings to build a new value; keep the "produce a new string" framing consistent
- [ ] `slice` - Also returns a derived new string (a piece); contrast copies vs excerpt
- [ ] `replace` - Also non-mutating string transform returning a new value

**Consistency rule:**

The string-producing members (`repeat`, `concat`, `slice`, `replace`, `replaceAll`, `trim`) all return a **new** string and leave the original alone. Translate them so that this "returns a fresh value" quality reads consistently across the family; do not pick a word for `repeat` that implies in-place mutation.

### Functional relationships

**This term works WITH:**

1. **`repeat` + a count**: The copy-builder

```javascript
let indent = " ".repeat(4);   // four spaces
```

**Common pairing:**

```javascript
// repeat feeds a larger string being assembled
let ruler = "=".repeat(30);
let header = ruler + "\nTITLE\n" + ruler;
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (make N joined copies) is universal, but "repeat" in most languages first evokes *saying something again* or *an event recurring*, neither of which is the JS sense. The translator must pick the *productive / duplicate-N-times* reading and keep it distinct from "loop/iterate." The verbal-repetition bias is the main trap.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (produce N joined copies as a new string)
- [ ] Reads as "duplicate N times," not "say again"?
- [ ] Avoids the "loop / recur" connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a count-driven "repeat" transform)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the new-string family (`concat`, `slice`, `replace`, `trim`)?
- [ ] Reads as returning a fresh value, not mutating in place?
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
term: repeat
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "produce N joined copies" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it avoids the "say again / recur" readings.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward verbal repetition or looping.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (verbal-repetition bias, loop/iterate overlap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
