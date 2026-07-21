# JavaScript Member: `slice` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String, Array
**Receivers (live in JEJ today):** String — arrays are not in the JEJ subset yet
**Ships in JEJ:** yes (member; String-only today, but choose a word that survives widening to Array)
**Difficulty:** MEDIUM

---

## Quick Summary

`slice` is a member method that **extracts a sub-range** of its receiver and returns it as a new value — a substring of a string, and (once arrays arrive) a sub-array of an array. It is called as `value.slice(start, end)`, taking the characters/elements from `start` up to but not including `end`. The original value is unchanged.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Take characters 0..3 (not including 3)
let word = "javascript";
let part = word.slice(0, 3);   // "jav"
```

**What this does:** Calls `slice` with `start = 0` and `end = 3`, returning the sub-range `"jav"`. The end index is exclusive. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// Drop the first character (from index 1 to the end)
let handle = "@ada";
let name = handle.slice(1);   // "ada"
```

**What this does:** With only a `start`, `slice` runs to the end of the value — the everyday "take everything from position N onward" pattern.

### Example 3: Edge Case

```javascript
// A bare `slice` is NOT this member — only `x.slice(...)` is
let slice = "label";              // an ordinary variable named slice
let real = "hello".slice(1, 3);   // THIS is the member  -> "el"
```

**What this shows:** `slice` counts as this member **only** in property position before the call (`"hello".slice(1, 3)`). A standalone variable happening to be named `slice` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `substring` - Very close cousin: also extracts a sub-range of a string (must stay DISTINCT)
2. `indexOf` - Also a String/Array member that widens; finds a position
3. `length` - Also widens String → Array

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Middle Dutch / Middle Low German *slice* — "a thin flat piece cut off."

**Root meaning:** "A piece cut from a larger whole" (as a slice of bread). Generalized to any extracted contiguous portion.

**Why JavaScript uses this:** Extracting a contiguous run of characters (or elements) is "cutting a slice" from the sequence. The cut metaphor works equally for a string and an array, which is exactly why `slice` serves both receivers.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`slice` is a method read from a value with the `receiver.slice(start, end)` shape. It returns a **new value containing a contiguous sub-range** — from `start` up to (but not including) `end`. On a string it returns a substring; on an array (outside the current JEJ subset) it returns a sub-array. Negative indices count from the end, and the original is never modified.

Critically, `slice` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"hello".slice(1, 3)` is the member; a learner's own variable named `slice` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `slice` attaches to — and here that matters concretely: `slice` **widens to Array**. The chosen word must read for cutting a piece of *text* and a piece of a *list* alike. Pick a "cut a section / take a portion" verb that is not text-specific, so it still reads the day arrays are taught. Do not optimize the word for strings alone.

**Key behaviors:**

1. **Method, not property:** called as `x.slice(a, b)` with `()`.
2. **Widens String → Array:** choose a word that survives receiver-widening.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `slice` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning a sub-range
- **Action vs State:** ACTION - it extracts and returns a portion
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb meaning **"extract / take a contiguous portion (section) of"** — a general "cut a piece / take a slice" word that reads for both text and lists. Prefer "portion / section" framing over anything that only makes sense for strings.

**Forms to AVOID:**

- ❌ A word meaning **"cut / delete"** in the sense of *removing from* the original - `slice` does not modify the receiver
- ❌ A word that only reads for **text** ("substring") - wrong the day arrays arrive
- ❌ A noun form - `slice` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Cut off / remove" (destructive cutting)
- ❌ Meaning 2: "A slice of bread" (a literal food portion)
- ✅ Meaning 3: **"EXTRACT A CONTIGUOUS SUB-RANGE (NON-DESTRUCTIVELY)"** — take a portion, leaving the original intact

**Example:**

English "slice" can mean:

1. "**slice** off the end" (cut away / remove) ❌
2. "a **slice** of cake" (a food portion) ❌
3. "take a **slice** of this string / array" (extract a contiguous portion) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: extract a contiguous portion without altering the original, for BOTH text and lists.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `slice`, check these translations:**

- [ ] `substring` - Extracts a string sub-range too; must be a DISTINCT native word or reversibility breaks
- [ ] `indexOf` - Companion widening member; keep positional language consistent
- [ ] `length` - Companion widening member; same String → Array survival requirement

**Consistency rule:**

`slice` and `substring` both extract a sub-range of a string and both live in JEJ today. Under Rule 2 (reversibility within the members partition) they must map to two clearly different native words — otherwise a reader cannot tell which member was meant. Choose `slice` as the general "take a section" (widening to arrays) and reserve a different word for `substring`.

### Functional relationships

**This term works WITH:**

1. **`slice` + `indexOf`**: find a position, then cut from it

```javascript
let path = "src/app.js";
let ext = path.slice(path.indexOf(".") );   // ".js"
```

**Common pairing:**

```javascript
// take a fixed-width prefix
let code = "AB1234";
let letters = code.slice(0, 2);   // "AB"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept ("take a contiguous portion") is concrete, but there are two real traps: the String → Array widening (the word must read for lists, not just text) and the collision risk with `substring`, which does almost the same thing to strings and must receive a distinct word. Neither is severe alone, but together they keep this above EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (extract a contiguous sub-range)?
- [ ] Reads correctly for BOTH receivers (String, Array), not just String?
- [ ] Avoids the "destructive cut / remove" connotation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("take a section / portion")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `substring` (or reversibility breaks)?
- [ ] Chosen for the full receiver set, not strings alone?
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
term: slice
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Array]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "extract a contiguous sub-range" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for both String and Array and stays distinct from `substring`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward destructive cutting or were text-only.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (String → Array widening, `substring` collision risk) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
