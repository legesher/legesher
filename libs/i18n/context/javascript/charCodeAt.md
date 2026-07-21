# JavaScript Member: `charCodeAt` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String
**Receivers (live in JEJ today):** String — this member is String-only in full JS too, so no widening is expected
**Ships in JEJ:** yes (member; String-only)
**Difficulty:** HARD

---

## Quick Summary

`charCodeAt` is a member method that returns **the numeric character code** (the UTF-16 code unit, a number) of the character at a given index in a string. It is called as `text.charCodeAt(index)`. Unlike `charAt`, which hands back the visible character, `charCodeAt` hands back a *number* — its underlying UTF-16 code unit.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Get the numeric code of the character at position 0
let word = "ABC";
let code = word.charCodeAt(0);   // 65  (the code for "A")
```

**What this does:** Calls `charCodeAt` with index `0`, returning the number `65` — the character code for `"A"`. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// Compare characters by their codes
let ch = "a";
let is_lowercase_letter = ch.charCodeAt(0) >= 97 && ch.charCodeAt(0) <= 122;
```

**What this does:** Reads the numeric code and tests a range — the classic "is this in the a–z code band?" pattern. The result of `charCodeAt` is always a number, so it can be compared arithmetically.

### Example 3: Edge Case

```javascript
// A bare `charCodeAt` is NOT this member — only `x.charCodeAt(...)` is
let charCodeAt = "label";              // an ordinary variable named charCodeAt
let real = "A".charCodeAt(0);          // THIS is the member  -> 65
```

**What this shows:** `charCodeAt` counts as this member **only** in property position before the call (`"A".charCodeAt(0)`). A standalone variable happening to be named `charCodeAt` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `charAt` - Sibling member: returns the *character* (text), not its numeric code
2. `indexOf` - Also returns a number (a position), but a position, not a code
3. `substring` - Also index-based

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound abbreviation — "char" (character) + "code" + "at"

**Root meaning:** "The numeric *code* of the *character* *at* this position." "Code" here is the character-encoding sense: the integer a character is assigned in a character set.

**Why JavaScript uses this:** Every character has an underlying numeric code (its UTF-16 code unit). `charCodeAt` exposes that number so code can do arithmetic, ordering, and encoding on characters. It is the numeric counterpart to `charAt`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`charCodeAt` is a method read from a string with the `string.charCodeAt(index)` shape. It returns the **numeric code** — the UTF-16 code unit, an integer — of the character at the zero-based index. Out-of-range indices return `NaN`.

Critically, `charCodeAt` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"A".charCodeAt(0)` is the member; a learner's own variable named `charCodeAt` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

The difficulty is conceptual layering: `charCodeAt` returns **not the character but the *number that encodes it***. The native word must convey "code / numeric code of a character," a more abstract idea than `charAt`'s plain "character." Many languages have a natural word for "character" but a less settled word for "character code / code point," so the translator may need a two-word phrase and must keep it visibly distinct from `charAt`. String-only in full JS, so there is no widening trap — the whole difficulty is the code-vs-character abstraction.

**Key behaviors:**

1. **Method, not property:** called as `x.charCodeAt(i)` with `()`.
2. **Returns a number:** the code, not the visible character.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `charCodeAt` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning a numeric code
- **Action vs State:** ACTION - it retrieves and returns a number
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"the numeric code of the character at (a position)"** — combining a "character" noun with a "code / number" noun and the "at position" sense. Make the *code* element explicit so it reads as a number, not the character itself.

**Forms to AVOID:**

- ❌ A word meaning **just "character"** - that is `charAt`; this returns the *code*, keep them distinct
- ❌ A word meaning **"position / index"** - the argument is a position, but the *return* is a code, not a position
- ❌ A noun form - `charCodeAt` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Code" as in program source / a cipher
- ❌ Meaning 2: The visible character itself (that is `charAt`)
- ✅ Meaning 3: **"THE NUMERIC ENCODING VALUE OF A CHARACTER"** — the integer that represents it

**Example:**

English "char code" can suggest:

1. "write some **code**" (program source) ❌
2. "the **character** at index 0" (the visible symbol) ❌ *that is `charAt`*
3. "the numeric **code** `65` for `'A'`" (the encoding value) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the numeric encoding value of a character, NOT program source and NOT the visible character** — the return is a number.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `charCodeAt`, check these translations:**

- [ ] `charAt` - Sibling member; must be DISTINCT (numeric code vs the character itself) or reversibility breaks
- [ ] `indexOf` - Also returns a number, but a position; keep "code" ≠ "position"
- [ ] `toString` - Also concerns representation; keep "code" ≠ "text form"

**Consistency rule:**

`charCodeAt` and `charAt` are a near-pair differing only in *what* they return. Under Rule 2 they must map to clearly different native words: keep the plain "character" for `charAt` and add the explicit "code / numeric" element for `charCodeAt`. Do not let them blur.

### Functional relationships

**This term works WITH:**

1. **`charCodeAt` + numeric comparison**: classifying characters by code range

```javascript
let ch = "5";
let code = ch.charCodeAt(0);   // 53
```

**Common pairing:**

```javascript
// read a code, then test a range
let c = "Z";
let is_upper = c.charCodeAt(0) >= 65 && c.charCodeAt(0) <= 90;
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

**For this term:** HARD (upper end of medium)

**Rationale:** Beyond the "at a position" idea, this member adds an abstraction — it returns the *numeric code* of a character, not the character. Many target languages lack a crisp single word for "character code / code point," so a two-word phrase is often needed, and it must stay clearly distinct from the sibling `charAt`. The encoding concept and the sibling contrast together push this above the plain-MEDIUM members.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (the numeric code of a character at an index)?
- [ ] Reads correctly for the String receiver?
- [ ] Makes clear the return is a NUMBER, not the character?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("numeric code of the character at position")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `charAt` (numeric code vs the character)?
- [ ] "Code" distinguished from "position" (`indexOf`) and "text form" (`toString`)?
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
term: charCodeAt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the numeric code of a character at a position" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm the return reads as a number and stays distinct from `charAt`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that blurred into "character" or "program code."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (code-vs-character abstraction, thin native vocabulary for "code point," sibling contrast) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
