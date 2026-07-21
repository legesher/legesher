# JavaScript Member: `length` - Translation Brief (Tier 1)

**Category:** member
**Type:** property (noun)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String, Array, Function
**Receivers (live in JEJ today):** String — arrays and functions are not in the JEJ subset yet
**Ships in JEJ:** yes (member; String-only today, but choose a word that survives widening)
**Difficulty:** MEDIUM

---

## Quick Summary

`length` is a member property that reports how many units a value contains — the count of characters in a string, and (once arrays are taught) the count of elements in an array. It is read as `value.length`, never called with `()`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// How many characters are in this string?
let word = "hello";
let n = word.length;
```

**What this does:** Reads the `length` property of the string `"hello"`, giving `5`. `length` is accessed with a dot and no parentheses.

### Example 2: Common Pattern

```javascript
// Guard against an empty input
let name = "";
if (name.length === 0) {
  // treat as empty
}
```

**What this does:** Uses `length` to test whether a string has any characters — the everyday "is this empty?" check.

### Example 3: Edge Case

```javascript
// A bare `length` is NOT this member — only `x.length` is
let length = 42;      // an ordinary variable named length
let count = "hi".length;  // THIS is the member
```

**What this shows:** `length` counts as this member **only** in property position (`"hi".length`). A standalone variable happening to be named `length` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER PROPERTY (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `slice` - Also a member that will widen from String to Array as the subset grows
2. `indexOf` - Also a String/Array member reporting a position/count-like value
3. `includes` - Also a String/Array member; a count/containment reading

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Old English

**Root meaning:** Old English *lengþu* — "the quality of being long; extent." Generalized from physical length to any measured extent or count.

**Why JavaScript uses this:** JavaScript names the count of a string's characters (and an array's elements) `length` — the "extent" of the collection. Note this is *how many units*, not a spatial distance.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`length` is a property read from a value with the `receiver.length` shape. On a string it yields the number of characters; on an array (outside the current JEJ subset) it yields the number of elements. It is a property access, not a method call — there are no parentheses.

Critically, `length` is a **member**: it only means this concept when it sits in property position after a dot. `"abc".length` is the member; a learner's own variable named `length` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `length` attaches to. That is a feature: English uses one word "length" for strings, arrays, and functions, and the native translation should too — *provided the chosen word reads correctly for all of them*, not just the one the translator happens to picture.

**Key behaviors:**

1. **Property, not method:** read as `x.length` with no `()`.
2. **Qualified binding:** it is identified by receiver + dot position; repetition across receivers is expected and correct.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `length` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun naming a count/quantity property
- **Action vs State:** STATE - it reports a quantity, it does not act
- **Temporal aspect:** None - it is a current measured value

### Recommended Form

**Primary recommendation:** Use a noun meaning **count / quantity / number-of-units** — a word that reads correctly for characters in a string *and* elements in an array (and, ideally, a function's parameter count). Prefer "count / how many" over "how long in space."

**Forms to AVOID:**

- ❌ A word meaning **physical/spatial length** ("how long a road is") - wrong the day arrays arrive; you cannot speak of an array's spatial length
- ❌ A word meaning **only "number of characters"** - too narrow; breaks when the same member counts array elements
- ❌ A verb form - `length` is a property (a thing read), not an action

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Physical/spatial extent" ("the length of the river")
- ❌ Meaning 2: "Duration" ("the length of the film")
- ✅ Meaning 3: **"COUNT OF UNITS IN A COLLECTION"** — how many characters/elements

**Example:**

English "length" can mean:

1. "The **length** of the rope is 3 metres" (spatial) ❌
2. "The **length** of the meeting" (duration) ❌
3. "The string's **length** is 5" (count of characters) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a count of units, NOT spatial length or duration** — because the *same* member counts array elements once arrays are taught, and "spatial length of an array" is nonsense.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `length`, check these translations (all members that widen String→Array):**

- [ ] `slice` - Same receiver-widening story; keep member nouns/verbs consistent
- [ ] `indexOf` - Position/count member across String and Array
- [ ] `includes` - Containment member across String and Array
- [ ] `concat` - Joining member across String and Array

**Consistency rule:**

Members that share receivers should be translated as a family, each with a word that survives receiver-widening. Choose the count/quantity noun for `length` knowing that `slice`, `indexOf`, `includes`, and `concat` face the same String→Array widening — do not optimize any of them for strings alone.

### Functional relationships

**This term works WITH:**

1. **`length` + comparison**: The emptiness / size check

```javascript
let s = "abc";
if (s.length > 0) {
  // non-empty
}
```

**Common pairing:**

```javascript
// length is read, then used in a numeric test
let password = "secret";
let long_enough = password.length >= 8;
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (a count) is universal, but the English word "length" biases toward *spatial* length, which is the wrong reading and actively breaks when the member widens to arrays. The translator must pick a count/quantity noun and verify it reads for every receiver in the full set (String, Array, Function), not just strings. The receiver-widening trap makes this more than trivial.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (count of units, not spatial length)
- [ ] Reads correctly for ALL receivers (String, Array, Function), not just String?
- [ ] Avoids the "spatial length / duration" connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (count/quantity noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the family of widening members (`slice`, `indexOf`, `includes`, `concat`)?
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
term: length
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Array, Function]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "count of units" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for every receiver in the set, not just String.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward spatial length.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (spatial-length bias, receiver-widening risk) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
