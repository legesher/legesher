# JavaScript Member: `endsWith` - Translation Brief (Tier 1)

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

`endsWith` is a member method that answers a yes/no question: does this string end with the given suffix? It is called as `value.endsWith(suffix)` and returns a boolean.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Does this string end with "lo"?
let word = "hello";
let ok = word.endsWith("lo");
```

**What this does:** Calls the `endsWith` method on `"hello"`, asking whether it ends with `"lo"`. Returns `true`.

### Example 2: Common Pattern

```javascript
// Check a file extension
let file = "report.pdf";
if (file.endsWith(".pdf")) {
  // handle as a PDF
}
```

**What this does:** Uses `endsWith` as a suffix test — the everyday "does this close with…?" check that drives a branch.

### Example 3: Edge Case

```javascript
// A bare `endsWith` is NOT this member — only `x.endsWith(...)` is
let endsWith = true;               // an ordinary variable named endsWith
let ok = "hello".endsWith("o");    // THIS is the member
```

**What this shows:** `endsWith` counts as this member **only** in property position (`"hello".endsWith(...)`). A standalone variable that happens to be named `endsWith` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `startsWith` - The mirror-image member: tests the *prefix* instead of the suffix
2. `includes` - Tests containment *anywhere*, not just at the end
3. `indexOf` - Reports *where* a substring sits, rather than *whether* it closes the string

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Old English (compound)

**Root meaning:** "end" (Old English *ende*, "the far limit or conclusion") + "with." The compound reads "ends with," i.e., the closing segment matches.

**Why JavaScript uses this:** JavaScript names the suffix test `endsWith` — "does the string *end with* this?" The reading is *concludes with at the back*, a positional test anchored to the tail of the string.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`endsWith` is a method read from a value with the `receiver.endsWith(suffix)` shape. It returns `true` when the string's closing characters exactly match the argument, and `false` otherwise. It always yields a boolean — a yes/no answer anchored to the **back** of the string. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `endsWith` is a **member**: it only means this concept when it sits in property position after a dot. `"abc".endsWith("c")` is the member; a learner's own variable named `endsWith` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition is never a collision here: even though `endsWith` has one receiver today, the pack still scores it under Rule 2 (reversibility within the members partition), not Rule 1. The key semantic load is *back-anchored*: it is not "contains," it is "contains **at the end**."

**Key behaviors:**

1. **Returns a boolean:** it answers a yes/no suffix question.
2. **Back-anchored:** the match must be at the very end, not just anywhere inside.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `endsWith` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase (a predicate — "does it end with?")
- **Action vs State:** TEST - it queries the suffix and returns true/false
- **Temporal aspect:** Present-tense query — "does it end with this now?"

### Recommended Form

**Primary recommendation:** Use a verb (or verb phrase) meaning **ends-with / finishes-with** — the sense of matching at the **back** of the string. The "with" / suffix relationship should be preserved so it reads as a test against a closing segment.

**Forms to AVOID:**

- ❌ A word meaning **generic "finish / terminate a process"** - `endsWith` does not end anything; it *tests* the closing
- ❌ A word meaning **"contains anywhere"** - loses the back-anchoring that distinguishes it from `includes`
- ❌ A noun form - `endsWith` is a test being performed, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Finish / terminate an activity" ("end the call")
- ❌ Meaning 2: "Contain somewhere" (that is `includes`, not back-anchored)
- ✅ Meaning 3: **"ENDS WITH THIS SUFFIX"** — the closing segment matches

**Example:**

English "ends with" can mean:

1. "The show **ends with** a song" (the last thing that happens) — close, but eventing ❌
2. "End the process" (terminate an action) ❌
3. "The file **ends with** '.pdf'" (its last characters are '.pdf') ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a back-anchored suffix test, NOT terminating an action** — and it must stay distinct from `includes`, which tests containment anywhere.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `endsWith`, check these translations:**

- [ ] `startsWith` - The exact mirror; translate the two as a matched pair (back vs front)
- [ ] `includes` - Containment anywhere; must stay distinct from back-anchored
- [ ] `indexOf` - Position of a match; the "where" to this "whether-at-back"

**Consistency rule:**

`endsWith` and `startsWith` are a matched pair and must be translated together: whatever construction expresses "ends with X" should invert cleanly to "begins with X." Keep both distinct from `includes` (anywhere) so a reader can tell front, back, and anywhere apart.

### Functional relationships

**This term works WITH:**

1. **`endsWith` + condition**: The suffix gate

```javascript
let name = "photo.PNG";
if (name.endsWith(".PNG")) {
  // handle as an image
}
```

**Common pairing:**

```javascript
// endsWith returns a boolean, then drives a branch
let host = "mail.example.com";
let is_example = host.endsWith("example.com");
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (a suffix test) is universal, but two traps make it non-trivial: (1) many languages use the same verb for "end an action" as for "end with a suffix," and only the latter is meant; (2) the translation must stay clearly distinct from `includes` (anywhere) and invert cleanly to `startsWith`. The back-anchoring is the load-bearing nuance.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (back-anchored suffix test, true/false)
- [ ] Reads as "ends with," not "terminate an action"?
- [ ] Stays distinct from `includes` (contains anywhere)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb phrase, not noun)?
- [ ] Correct form (an "ends with" predicate)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Inverts cleanly to `startsWith` (matched pair)?
- [ ] Preserves the "with / suffix" relationship?
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
term: endsWith
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "ends with this suffix" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays back-anchored and distinct from `includes`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "terminate an action."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (end-an-action drift, overlap with `includes`, pairing with `startsWith`) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
