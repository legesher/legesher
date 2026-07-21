# JavaScript Member: `indexOf` - Translation Brief (Tier 1)

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

`indexOf` is a member method that returns the **first position (index) at which a search value occurs** in its receiver — a character/substring inside a string, and (once arrays arrive) an element inside an array. It is called as `value.indexOf(search)`. If the value is not found it returns **`-1`**. The result is a number: a position, not the value itself.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Where does "b" first appear?
let word = "abc";
let pos = word.indexOf("b");   // 1
```

**What this does:** Calls `indexOf` with `"b"`, returning `1` — the zero-based position of the first match. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// "Not found" is signalled by -1
let email = "ada@site.com";
let has_at = email.indexOf("@") !== -1;   // true
```

**What this does:** Uses the `-1` sentinel to test presence — the everyday "does this contain X?" check built on position. A non-`-1` result means "found, at this index."

### Example 3: Edge Case

```javascript
// A bare `indexOf` is NOT this member — only `x.indexOf(...)` is
let indexOf = "label";              // an ordinary variable named indexOf
let real = "hello".indexOf("l");    // THIS is the member  -> 2
```

**What this shows:** `indexOf` counts as this member **only** in property position before the call (`"hello".indexOf("l")`). A standalone variable happening to be named `indexOf` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `slice` - Companion widening member (String → Array); often used together with `indexOf`
2. `length` - Also widens String → Array; also returns a number
3. `charAt` - Also positional on strings, but takes a position and returns a character (the inverse direction)

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound — "index" + "of."

**Root meaning:** "The *index* (position) *of* a thing." "Index" from Latin *index*, "pointer / that which points out." Here it points to a position in a sequence.

**Why JavaScript uses this:** Searching a sequence and reporting *where* a value sits is a core operation. `indexOf` answers "at what position does this first occur?" and works the same way for a string's characters and an array's elements — which is why it serves both receivers.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`indexOf` is a method read from a value with the `receiver.indexOf(search)` shape. It scans from the start and returns the **zero-based index of the first occurrence** of `search`, or **`-1`** if there is none. On a string it finds a character or substring; on an array (outside the current JEJ subset) it finds an element. The return is always a number — a position.

Critically, `indexOf` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `"hello".indexOf("l")` is the member; a learner's own variable named `indexOf` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `indexOf` attaches to — and here that matters concretely: `indexOf` **widens to Array**. The chosen word must read for finding a position *in text* and *in a list* alike. Two nuances to preserve: (1) the result is a *position* (a number), not the found value and not a yes/no answer — do not translate it as "contains"; and (2) the `-1` "not found" convention is part of the concept. Pick a "position of / where X occurs" verb that survives receiver-widening; do not optimise for strings alone.

**Key behaviors:**

1. **Method, not property:** called as `x.indexOf(v)` with `()`.
2. **Returns a position or `-1`:** a number, not the value and not a boolean.
3. **Widens String → Array:** choose a word that survives receiver-widening.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning a position
- **Action vs State:** ACTION - it searches and returns an index
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"the position of / find where X first occurs"** — a "locate the index" framing that reads for both text and lists. Keep the *position* sense explicit so it is not confused with a containment yes/no.

**Forms to AVOID:**

- ❌ A word meaning **"contains / includes"** - that is a boolean question; `indexOf` returns a *position* (and belongs to `includes`)
- ❌ A word that only reads for **text search** - wrong the day arrays arrive
- ❌ A noun form - `indexOf` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Index" as in a book's back-of-book listing
- ❌ Meaning 2: "Contains this value?" (a yes/no answer)
- ✅ Meaning 3: **"THE POSITION OF THE FIRST OCCURRENCE"** — a numeric index, or `-1`

**Example:**

English "index of" can suggest:

1. "look it up in the **index**" (a reference listing) ❌
2. "does it **contain** '@'?" (a boolean) ❌ *that is `includes`*
3. "the **position** of '@' is 3" (a numeric index) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the numeric position of the first match (with `-1` for none), NOT a book index and NOT a contains/boolean** — and it must read for both strings and arrays.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `indexOf`, check these translations:**

- [ ] `slice` - Companion widening member; commonly paired with `indexOf`; keep positional wording consistent
- [ ] `length` - Companion widening member returning a number; keep "position" ≠ "count"
- [ ] `charAt` - The inverse (position → character); keep "position of a value" ≠ "value at a position"

**Consistency rule:**

`indexOf` is one of the String → Array widening family (`length`, `slice`, `indexOf`, `includes`, `concat`). Translate it as part of that family, each with a word that survives receiver-widening. Keep it clearly distinct from `includes` (containment / boolean) and from `charAt` (which goes position → character, the opposite direction).

### Functional relationships

**This term works WITH:**

1. **`indexOf` + `slice`**: find a boundary, then cut at it

```javascript
let file = "report.pdf";
let dot = file.indexOf(".");     // 6
let ext = file.slice(dot);       // ".pdf"
```

**Common pairing:**

```javascript
// presence test via the -1 sentinel
let text = "hello world";
let found = text.indexOf("world") !== -1;   // true
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept ("position of the first match") is concrete, but there are three real traps: the String → Array widening (the word must read for lists too), the pull toward "contains / includes" (a boolean, which is a *different* member), and the `-1` "not found" convention that belongs to the concept. None is severe alone, but together they keep this above EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (position of the first occurrence)?
- [ ] Reads correctly for BOTH receivers (String, Array), not just String?
- [ ] Avoids the "contains / includes" (boolean) reading?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("position of / find where")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `includes` (position vs boolean)?
- [ ] Chosen for the full receiver set, not strings alone?
- [ ] Aligns with the widening family (`length`, `slice`) and inverse `charAt`?

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
term: indexOf
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Array]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the position of the first occurrence" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for both String and Array and stays distinct from `includes`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "contains" or were text-only.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (String → Array widening, contains-vs-position pull, `-1` convention) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
