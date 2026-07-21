# JavaScript Member: `trim` - Translation Brief (Tier 1)

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

`trim` is a member method that returns a new string with leading and trailing whitespace removed. It is called as `value.trim()` with no arguments; the original string is unchanged and interior whitespace is left alone.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Strip surrounding spaces
let raw = "  hello  ";
let clean = raw.trim();   // "hello"
```

**What this does:** Calls the `trim` method on `"  hello  "`, returning a new string with the outer spaces removed. The middle is untouched.

### Example 2: Common Pattern

```javascript
// Normalize user input before checking it
let entry = "   yes ";
if (entry.trim() === "yes") {
  // treat as a clean "yes"
}
```

**What this does:** Uses `trim` to clean up stray whitespace from typed input before comparing — the everyday "tidy the edges" step.

### Example 3: Edge Case

```javascript
// A bare `trim` is NOT this member — only `x.trim()` is
let trim = true;                 // an ordinary variable named trim
let clean = "  hi  ".trim();     // THIS is the member
```

**What this shows:** `trim` counts as this member **only** in property position (`"  hi  ".trim()`). A standalone variable that happens to be named `trim` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `replace` - Also a non-mutating string cleanup member returning a new value
2. `slice` - Also returns a new string derived from the original
3. `toLowerCase` / `toUpperCase` - Also normalize a string and return a fresh copy

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Old English

**Root meaning:** Old English *trymman* — "to make firm, arrange, put in order." Modern "trim" means "to cut away excess so a thing is neat at the edges" (as in trimming hair or a hedge).

**Why JavaScript uses this:** JavaScript names the whitespace-cleanup operation `trim` — "cut the ragged blank space off the ends." The reading is *remove the surrounding whitespace*, not *decorate* or *reduce in size generally*.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`trim` is a method read from a value with the `receiver.trim()` shape. It returns a **new** string with all whitespace characters (spaces, tabs, newlines) removed from the **start and end** only; whitespace inside the string is preserved. It takes no arguments, and the receiver is not mutated. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `trim` is a **member**: it only means this concept when it sits in property position after a dot. `" x ".trim()` is the member; a learner's own variable named `trim` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition of the native word across receivers is never a collision; the pack scores `trim` under Rule 2 (reversibility), not Rule 1. The load-bearing sense is *strip the outer blank space* — specifically whitespace at the edges, not arbitrary trimming or shrinking.

**Key behaviors:**

1. **Edges only:** removes leading and trailing whitespace; interior spaces stay.
2. **Whitespace-specific:** it strips blank characters, not arbitrary content.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `trim` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a cleanup transform
- **Action vs State:** ACTION - it removes edge whitespace and returns a new string
- **Temporal aspect:** Present-tense operation — "clean the ends, now"

### Recommended Form

**Primary recommendation:** Use a verb meaning **strip / clean the surrounding whitespace from the ends** — the sense of removing blank space at the start and finish. If the language distinguishes "cut hair/hedge" from "clean up text," prefer the "remove surrounding blanks" reading.

**Forms to AVOID:**

- ❌ A word meaning **"cut / shorten in general"** - too broad; `trim` removes only edge *whitespace*, not arbitrary content
- ❌ A word meaning **"decorate / adorn"** (as "trim a tree") - a false friend of English "trim"
- ❌ A noun form - `trim` is the action of cleaning the ends, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Decorate / adorn" ("trim the Christmas tree")
- ❌ Meaning 2: "Cut to shorten generally" ("trim the budget")
- ✅ Meaning 3: **"REMOVE SURROUNDING WHITESPACE"** — strip blank space off both ends

**Example:**

English "trim" can mean:

1. "**Trim** the tree with lights" (decorate) ❌
2. "**Trim** the hedge" (cut to shape) — close, but not whitespace-specific ❌
3. "`'  hi  '.trim()`" (strip the outer spaces → `'hi'`) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: removing whitespace at the two ends of a string, NOT decorating or general cutting.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `trim`, check these translations:**

- [ ] `replace` - Also a non-mutating cleanup transform; keep "returns a new string" consistent
- [ ] `slice` - Also returns a derived substring (a piece); contrast "strip edges" vs "take a piece"
- [ ] `toLowerCase` / `toUpperCase` - Also normalize and return a fresh string

**Consistency rule:**

The string-normalizing members (`trim`, `replace`, `replaceAll`, `toLowerCase`, `toUpperCase`) all return a **new** string and leave the original alone. Translate them so this "returns a fresh, cleaned value" quality reads consistently; do not pick a word for `trim` that implies in-place editing.

### Functional relationships

**This term works WITH:**

1. **`trim` + comparison / storage**: The input-normalizer

```javascript
let username = "  admin ".trim();   // "admin"
```

**Common pairing:**

```javascript
// trim then test emptiness
let comment = "   ";
if (comment.trim().length === 0) {
  // effectively blank
}
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (strip edge whitespace) is common, but English "trim" is a rich word (decorate, cut, neaten) and few languages have a single verb that means *exactly* "remove surrounding whitespace." The translator must land on the "clean the blank ends" reading and avoid both the decorate false-friend and an over-broad "cut/shorten." That narrowing is the challenge.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (remove leading/trailing whitespace, new string)
- [ ] Reads as "strip surrounding blanks," not "decorate" or "cut generally"?
- [ ] Makes clear only the *ends* are affected, not interior spaces?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a whitespace-cleanup transform)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the normalizing family (`replace`, `toLowerCase`, `toUpperCase`)?
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
term: trim
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "remove surrounding whitespace" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it avoids the "decorate" and "general cut" readings.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any decorate/cut false friends.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (decorate false-friend, over-broad "cut") so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
