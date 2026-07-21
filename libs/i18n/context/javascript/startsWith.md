# JavaScript Member: `startsWith` - Translation Brief (Tier 1)

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

`startsWith` is a member method that answers a yes/no question: does this string begin with the given prefix? It is called as `value.startsWith(prefix)` and returns a boolean.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Does this string begin with "he"?
let word = "hello";
let ok = word.startsWith("he");
```

**What this does:** Calls the `startsWith` method on `"hello"`, asking whether it begins with `"he"`. Returns `true`.

### Example 2: Common Pattern

```javascript
// Route on a prefix
let url = "https://example.com";
if (url.startsWith("https")) {
  // treat as secure
}
```

**What this does:** Uses `startsWith` as a prefix test — the everyday "does this open with…?" check that drives a branch.

### Example 3: Edge Case

```javascript
// A bare `startsWith` is NOT this member — only `x.startsWith(...)` is
let startsWith = true;                 // an ordinary variable named startsWith
let ok = "hello".startsWith("h");      // THIS is the member
```

**What this shows:** `startsWith` counts as this member **only** in property position (`"hello".startsWith(...)`). A standalone variable that happens to be named `startsWith` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `endsWith` - The mirror-image member: tests the *suffix* instead of the prefix
2. `includes` - Tests containment *anywhere*, not just at the start
3. `indexOf` - Reports *where* a substring begins, rather than *whether* it begins there

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Old English (compound)

**Root meaning:** "start" (Old English *styrtan*, "to leap, begin") + "with." The compound reads "begins with," i.e., the opening segment matches.

**Why JavaScript uses this:** JavaScript names the prefix test `startsWith` — "does the string *start with* this?" The reading is *begins with at the front*, a positional test anchored to the head of the string.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`startsWith` is a method read from a value with the `receiver.startsWith(prefix)` shape. It returns `true` when the string's opening characters exactly match the argument, and `false` otherwise. It always yields a boolean — a yes/no answer anchored to the **front** of the string. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `startsWith` is a **member**: it only means this concept when it sits in property position after a dot. `"abc".startsWith("a")` is the member; a learner's own variable named `startsWith` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition is never a collision here: even though `startsWith` has one receiver today, the pack still scores it under Rule 2 (reversibility within the members partition), not Rule 1. The key semantic load is *front-anchored*: it is not "contains," it is "contains **at the beginning**."

**Key behaviors:**

1. **Returns a boolean:** it answers a yes/no prefix question.
2. **Front-anchored:** the match must be at the very start, not just anywhere inside.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `startsWith` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase (a predicate — "does it begin with?")
- **Action vs State:** TEST - it queries the prefix and returns true/false
- **Temporal aspect:** Present-tense query — "does it begin with this now?"

### Recommended Form

**Primary recommendation:** Use a verb (or verb phrase) meaning **begins-with / starts-with** — the sense of matching at the **front** of the string. The "with" / prefix relationship should be preserved so it reads as a test against an opening segment.

**Forms to AVOID:**

- ❌ A word meaning **generic "start / launch a process"** - `startsWith` does not start anything; it *tests* the opening
- ❌ A word meaning **"contains anywhere"** - loses the front-anchoring that distinguishes it from `includes`
- ❌ A noun form - `startsWith` is a test being performed, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Begin / launch an activity" ("start the engine")
- ❌ Meaning 2: "Contain somewhere" (that is `includes`, not front-anchored)
- ✅ Meaning 3: **"BEGINS WITH THIS PREFIX"** — the opening segment matches

**Example:**

English "starts with" can mean:

1. "The meeting **starts with** a prayer" (the first thing that happens) — close, but eventing ❌
2. "Start the car" (initiate an action) ❌
3. "The word **starts with** 'h'" (its first characters are 'h') ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a front-anchored prefix test, NOT initiating an action** — and it must stay distinct from `includes`, which tests containment anywhere.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `startsWith`, check these translations:**

- [ ] `endsWith` - The exact mirror; translate the two as a matched pair (front vs back)
- [ ] `includes` - Containment anywhere; must stay distinct from front-anchored
- [ ] `indexOf` - Position of a match; the "where" to this "whether-at-front"

**Consistency rule:**

`startsWith` and `endsWith` are a matched pair and must be translated together: whatever construction expresses "begins with X" should invert cleanly to "ends with X." Keep both distinct from `includes` (anywhere) so a reader can tell front, back, and anywhere apart.

### Functional relationships

**This term works WITH:**

1. **`startsWith` + condition**: The prefix gate

```javascript
let path = "/admin/users";
if (path.startsWith("/admin")) {
  // require elevated access
}
```

**Common pairing:**

```javascript
// startsWith returns a boolean, then drives a branch
let file = "IMG_2043.jpg";
let is_image = file.startsWith("IMG");
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (a prefix test) is universal, but two traps make it non-trivial: (1) many languages use the same verb for "begin an action" as for "begin with a prefix," and only the latter is meant; (2) the translation must stay clearly distinct from `includes` (anywhere) and invert cleanly to `endsWith`. The front-anchoring is the load-bearing nuance.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (front-anchored prefix test, true/false)
- [ ] Reads as "begins with," not "initiate an action"?
- [ ] Stays distinct from `includes` (contains anywhere)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb phrase, not noun)?
- [ ] Correct form (a "begins with" predicate)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Inverts cleanly to `endsWith` (matched pair)?
- [ ] Preserves the "with / prefix" relationship?
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
term: startsWith
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "begins with this prefix" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays front-anchored and distinct from `includes`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "initiate an action."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (start-an-action drift, overlap with `includes`, pairing with `endsWith`) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
