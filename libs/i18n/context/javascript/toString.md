# JavaScript Member: `toString` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String, Number, Boolean, Array, Date, RegExp, Object, Function
**Receivers (live in JEJ today):** String, Number — Boolean, Array, Date, RegExp, Object, and Function are not in the JEJ subset yet
**Ships in JEJ:** yes (member; String + Number today, but choose a word that survives widening across a very broad receiver set)
**Difficulty:** HARD

---

## Quick Summary

`toString` is a member method that returns a **text representation** of its receiver — the digits of a number as text, the characters of a string, and (once they arrive) a date rendered as date-text, an array joined by commas, and so on. It is called as `value.toString()`. **This term is flagged for native review:** English hides a real semantic gap — `Number.toString(2)` performs a *base/radix conversion* while `Date.toString()` produces *human-readable date text*, yet both wear the same English label.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Turn a number into its text form
let count = 42;
let text = count.toString();   // "42"
```

**What this does:** Calls `toString` on the number `42`, producing the string `"42"`. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// Number-to-text with an explicit base (radix)
let n = 255;
let hex = n.toString(16);   // "ff"
let bin = n.toString(2);    // "11111111"
```

**What this does:** With an argument, `Number.toString` converts the number into text **in a different base** — hex or binary. This is a *conversion*, not merely "describe as words," which is exactly the gap flagged for review.

### Example 3: Edge Case

```javascript
// A bare `toString` is NOT this member — only `x.toString()` is
let toString = "label";        // an ordinary variable named toString
let real = (255).toString();   // THIS is the member
```

**What this shows:** `toString` counts as this member **only** in property position before the call (`(255).toString()`). A standalone variable happening to be named `toString` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `valueOf` - The mirror member: returns the *primitive value* rather than its text form
2. `charAt` - Also a String member returning text
3. `slice` - Also a member that widens beyond String

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound — "to" + "string"

**Root meaning:** "Produce (convert) *to* a string." "String" here is the computing sense: an ordered sequence of characters, from the older sense of items threaded in a line.

**Why JavaScript uses this:** Every value can be asked to render itself as text for display, logging, or concatenation. `toString` is the universal "give me your text form" hook. Note that the *kind* of text differs wildly by receiver: decimal digits, a comma-joined list, a formatted date, or `[object Object]`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`toString` is a method read from a value with the `receiver.toString()` shape. It returns a **string representation** of the receiver. On a number it yields the digits as text (optionally in another base); on a string it yields the same characters; on a date it yields human-readable date text; on an array it yields the elements joined by commas.

Critically, `toString` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `(42).toString()` is the member; a learner's own variable named `toString` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `toString` attaches to. That is a feature — English uses one word for all of them. **But this member stretches that further than most.** The action is genuinely different per receiver: `Number.toString(2)` is a *radix conversion* (a computation that re-encodes the number in base 2), whereas `Date.toString()` merely *formats* an existing value as readable text. English papers over that difference; the native word should aim for the umbrella meaning ("render as text") and the reviewer should confirm it does not accidentally read as only "convert the base of" or only "describe in words."

**Key behaviors:**

1. **Method, not property:** called as `x.toString()` with `()`.
2. **Qualified binding:** identified by receiver + dot position; repetition across receivers is expected and correct.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `toString` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action that produces a result
- **Action vs State:** ACTION - it computes and returns a text form
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"render as text / produce the text form of"** — an umbrella word broad enough to cover a number's digits, a date's readable text, and a list's joined form. Prefer "to-text / represent-as-text" over any word that fixes a single receiver.

**Forms to AVOID:**

- ❌ A word meaning **"convert the base / change radix"** - true only of `Number.toString(radix)`; wrong for every other receiver
- ❌ A word meaning **only "describe in words / narrate"** - too loose; misses the numeric and structural receivers
- ❌ A noun form - `toString` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Convert to another number base" (only `Number.toString(2)`)
- ❌ Meaning 2: "String things together / thread" (the physical origin of "string")
- ✅ Meaning 3: **"PRODUCE THE TEXT REPRESENTATION OF A VALUE"** — the umbrella meaning across all receivers

**Example:**

English "toString" can suggest:

1. "`n.toString(16)` — re-encode 255 in base 16" (radix conversion) ❌ *only one receiver*
2. "string up the lights" (thread physically) ❌
3. "give me the text form of this value" (render as text) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: render-as-text, NOT base-conversion or physical threading** — because the *same* member serves numbers, dates, arrays, and objects, and "change the base of a date" is nonsense.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `toString`, check these translations:**

- [ ] `valueOf` - Its mirror; must be a DISTINCT native word (primitive value vs text form) or reversibility breaks
- [ ] `charAt` - Another String member returning text
- [ ] `charCodeAt` - Returns a numeric code, not text — keep clearly different from `toString`

**Consistency rule:**

`toString` and `valueOf` are a matched pair and both live in JEJ today. Under Rule 2 (reversibility within the members partition) they must map to two clearly different native words — one for "text form," one for "primitive value." Do not let them collapse into the same word.

### Functional relationships

**This term works WITH:**

1. **`toString` + concatenation / display**: turning a value into text for output

```javascript
let score = 7;
let line = "Score: " + score.toString();
```

**Common pairing:**

```javascript
// explicit base conversion, then display
let color = (255).toString(16);   // "ff"
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

**For this term:** HARD — flagged for native review

**Rationale:** The receiver set is the broadest in the batch (eight types), and the *action itself changes meaning* across them: a radix conversion for numbers-with-argument versus plain text formatting for dates and objects. English collapses these into one label, so a naive native word risks encoding only one branch. The translator must find an umbrella "render as text" verb and the reviewer must confirm it does not read as base-conversion-only or narration-only.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (render as text), not just "convert base"?
- [ ] Reads correctly for the live receivers (String, Number) AND survives widening (Date, Array, Object, …)?
- [ ] Avoids the "radix conversion only" and "narrate in words" traps?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form (umbrella "to-text" verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `valueOf` (text form vs primitive value)?
- [ ] Chosen for the full receiver set, not numbers alone?
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
term: toString
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Number, Boolean, Array, Date, RegExp, Object, Function]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "render as text" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for every receiver in the set, not just Number, and does not collapse into "base conversion."

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward radix conversion or narration.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (radix-vs-text-form gap, very broad receiver set) so review can prioritize it. This term is pre-flagged for native review.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
