# JavaScript Member: `charAt` - Translation Brief (Tier 1)

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

`charAt` is a member method that returns **the single character at a given index** in a string — position `0` is the first character. It is called as `text.charAt(index)`. If the index is out of range it returns an empty string. The returned character is text (a one-character string), not a number.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Get the character at position 1
let word = "hello";
let c = word.charAt(1);   // "e"
```

**What this does:** Calls `charAt` with index `1`, returning the second character `"e"` (indexing starts at `0`). The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// Read the first character
let name = "Ada";
let initial = name.charAt(0);   // "A"
```

**What this does:** Uses `charAt(0)` to grab the first character — the everyday "get the initial / leading character" pattern.

### Example 3: Edge Case

```javascript
// A bare `charAt` is NOT this member — only `x.charAt(...)` is
let charAt = "label";           // an ordinary variable named charAt
let real = "hi".charAt(0);      // THIS is the member  -> "h"
```

**What this shows:** `charAt` counts as this member **only** in property position before the call (`"hi".charAt(0)`). A standalone variable happening to be named `charAt` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `charCodeAt` - Sibling member: returns the numeric *code* at an index instead of the character
2. `indexOf` - Also position-oriented: finds where a value sits
3. `substring` - Also index-based: extracts a range of characters

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound abbreviation — "char" (character) + "at"

**Root meaning:** "The *character* located *at* this position." "Char" is the standard programming clip of "character"; "at" marks the index.

**Why JavaScript uses this:** Strings are indexed sequences of characters, and `charAt` is the classic "reach into position N and hand me that character" accessor. It reads text out; its sibling `charCodeAt` reads the numeric code out.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`charAt` is a method read from a string with the `string.charAt(index)` shape. It returns the **character** sitting at the zero-based index — a one-character string. Out-of-range indices return `""` (empty string) rather than an error.

Critically, `charAt` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"hi".charAt(0)` is the member; a learner's own variable named `charAt` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

`charAt` is String-only in full JavaScript — there is no array or number version — so the translator does not face the widening trap here. The main care points are (1) the returned thing is a *character* (text), which should read naturally even for scripts whose "characters" are syllables or ideographs, and (2) "character" must not narrow to "letter," since digits, spaces, and punctuation are all valid characters. Because the member is bounded by its receiver, repetition of the native word elsewhere in the member partition would still be fine — but here the receiver is simply always a string.

**Key behaviors:**

1. **Method, not property:** called as `x.charAt(i)` with `()`.
2. **Qualified binding:** identified by receiver + dot position; String-only receiver.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `charAt` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning a character
- **Action vs State:** ACTION - it retrieves and returns a character
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"the character at (a position)"** — pairing a general "character / symbol" noun with an "at position" sense. Prefer "character" over "letter" so digits and punctuation are covered.

**Forms to AVOID:**

- ❌ A word meaning **"letter"** specifically - too narrow; characters include digits, spaces, and symbols
- ❌ A word meaning **"numeric code"** - that is `charCodeAt`; keep them distinct
- ❌ A noun form - `charAt` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

MILD

**If MILD, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Character" as in a person in a story / personality
- ✅ Meaning 2: **"A SINGLE TEXT CHARACTER AT A POSITION"** — one symbol from the string

**Example:**

English "character" can mean:

1. "the main **character** in the novel" (a persona) ❌
2. "the **character** at index 0 is `'h'`" (a text symbol) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #2: a single text symbol at a given position, NOT a persona and NOT specifically a "letter."**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `charAt`, check these translations:**

- [ ] `charCodeAt` - Sibling member; must be DISTINCT (character vs numeric code) or reversibility breaks
- [ ] `indexOf` - Also positional; keep the "position / at index" language consistent
- [ ] `substring` / `slice` - Also index-based extraction

**Consistency rule:**

`charAt` and `charCodeAt` are a near-pair differing only in *what* they return (the character vs its numeric code). Under Rule 2 they must map to clearly different native words. Keep the "character" noun in `charAt` and the "code" noun in `charCodeAt` visibly separate.

### Functional relationships

**This term works WITH:**

1. **`charAt` + a loop / index**: walking a string character by character

```javascript
let s = "abc";
let first = s.charAt(0);   // "a"
```

**Common pairing:**

```javascript
// read a character, then compare it
let word = "yes";
let starts_with_y = word.charAt(0) === "y";
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept ("the character at position N") is concrete and universal, and there is no receiver-widening trap (String-only). The two live risks are narrowing "character" to "letter" and colliding with the sibling `charCodeAt`. Neither is severe, but both need a deliberate choice, keeping this above EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (the character at an index)?
- [ ] Reads correctly for the String receiver?
- [ ] Avoids narrowing "character" to "letter"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("character at position")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `charCodeAt` (character vs numeric code)?
- [ ] Positional language aligned with `indexOf` / `substring`?
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
term: charAt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the character at a position" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it does not narrow to "letter" and stays distinct from `charCodeAt`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "letter" or "persona."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (character-vs-letter, sibling contrast with `charCodeAt`) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
