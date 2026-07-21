# JavaScript Builtin: `String` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor / type name)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

`String` is the global object that names JavaScript's text type and, called as `String(x)`, converts any value into its text form. It is capitalized because it is a global object (the constructor), distinct from the lowercase primitive text values it produces.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Convert a number to its text form
let text = String(42); // "42"
```

**What this does:** Calls the global `String` object as a function to turn the number `42` into the text `"42"`. Reaches the named type and asks it to represent the value as characters.

### Example 2: Common Pattern

```javascript
// Text is needed for display and joining
let age = 25;
let message = "Age: " + String(age); // "Age: 25"
```

**What this does:** The most common use of `String` is converting a non-text value so it can be shown or joined with other text. Here the number becomes text before being concatenated.

### Example 3: Edge Case

```javascript
// String names the type; the quoted value is a primitive of that type
let a = "hello";       // a text primitive
let b = String("hi");  // String() called as a converter
```

**What this shows:** `String` (capitalized) is the *name of the type / the converter object*, while `"hello"` is an actual text value belonging to that type. Translating `String` names the category and the conversion tool, not a single literal string.

---

## Pattern Classification

**This term is:** GLOBAL OBJECT (type name / constructor)

**Similar terms in this pattern:**

1. `Number` - Also a capitalized global naming a primitive type and converting to it (`Number(x)`)
2. `Boolean` - Also a capitalized global naming a primitive type and converting to it (`Boolean(x)`)
3. `Array` - Also a capitalized global object naming a built-in type

**Pattern rule:** Capitalized global type objects (`String`, `Number`, `Boolean`) are names of value *categories*. Translate them as nouns naming the type, kept consistent with each other in noun form and register.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** "String" comes from the image of characters strung together like beads on a thread. Early computing treated text as a sequence — a string — of individual characters.

**Why JavaScript uses this:** JavaScript follows the universal programming convention that the text type is called "string." Unlike Python's abbreviated `str`, JavaScript spells it in full and capitalizes it as a global object, signalling "the text type / the text converter."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`String` names JavaScript's text type — sequences of characters used for words, sentences, identifiers, and any human-readable data. Text values are usually written directly in quotes (`"hello"`, `'hi'`, `` `template` ``), and JavaScript treats those literals as text automatically. The `String` object itself matters chiefly as a *converter*: `String(x)` takes any value and returns its text representation.

As a converter, `String` is forgiving. `String(42)` gives `"42"`, `String(true)` gives `"true"`, `String(null)` gives `"null"`. This is how beginners turn numbers and other values into text for display or for joining with other text. Unlike some languages, JavaScript will also coerce values to text implicitly during `+` with a string, but calling `String(x)` makes the intent explicit and readable.

Conceptually, `String` names a *category of values* (text), and secondarily the *tool that produces text from other values*. It is capitalized precisely because it is a global object, one of a small family (`String`, `Number`, `Boolean`) that name JavaScript's primitive types.

**Key behaviors:**

1. **Names the text type:** `String` is the type of every quoted text value; the value `"hi"` is a string.
2. **Converts to text:** Called as `String(x)`, it returns the text form of any value — the beginner's explicit way to make text.
3. **Capitalized global:** `String` (uppercase) is the global object; it is distinct from the lowercase text primitives it describes and produces.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun naming a value type (and the converter that yields it)
- **Action vs State:** STATE/CATEGORY — names what a value IS (text), not an action
- **Temporal aspect:** Timeless — a type is a permanent classification

### Recommended Form

**Primary recommendation:** Use your target language's established CS-education term for "string" (the text data type) — typically "string," "character chain/sequence," or "text." Keep it a noun, consistent with the other type names (`Number`, `Boolean`).

**Forms to AVOID:**

- ❌ A verb form ("to string / to text") — this names a type, not an action
- ❌ The physical-cord meaning of "string" (rope, thread) — wrong sense (see Ambiguity Resolution)
- ❌ An overly literal or vague word for "text" that isn't the CS term in your language

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: Physical string (rope, cord, thread)
- ❌ Meaning 2: A series of events ("a string of wins")
- ✅ Meaning 3: **SEQUENCE OF CHARACTERS** — the text data type in computing

**Example:**

English "string" can mean:

1. "Tie it with string" (physical cord) ❌
2. "A string of pearls" (a series of objects) ⚠️ (closer, but not the computing sense)
3. "Store the name as a string" (character-sequence data type) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the text/character-sequence data type — not physical cord and not a series of events.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `String`, check these translations:**

- [ ] `Number` - Also a capitalized global type name; keep both as type nouns of one register
- [ ] `Boolean` - Also a capitalized global type name; consistent noun treatment
- [ ] `parseInt` / `parseFloat` - Parse *text* into numbers; the word for text here should match

**Consistency rule:**

All capitalized global type objects (`String`, `Number`, `Boolean`) name value categories and should read as nouns of one consistent technical register. Do not translate one as an everyday word and another as a formal coinage. Whatever word names "text" here should also be the "text" referenced by `parseInt`/`parseFloat`.

### Functional relationships

**This term works WITH:**

1. **`String` + a value**: converting any value to text

```javascript
String(3.14); // "3.14"
```

**Common pairing:**

```javascript
// Turn a value into text, then join it for display
let score = 100;
let line = "Score: " + String(score);
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** "String" (the text type) is a universal CS concept with established terminology in every language's programming education. The only judgment is whether to use a native term ("character chain/text") or the adopted loanword "string"; both are well documented. The physical-cord sense is an easily avoided distractor.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the TEXT / CHARACTER-SEQUENCE type (not physical string)?
- [ ] Would a native speaker understand this names the text type / text converter?
- [ ] Avoids misleading connotations (cord, series of events)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (type noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`String` is a global object)?

### 3. Consistency

- [ ] Matches the pattern of other type names (`Number`, `Boolean`)?
- [ ] Same noun register as similar builtins?
- [ ] Aligns with the "text" referenced by `parseInt`/`parseFloat`?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard CS term)?

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
term: String
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the text data type (and its converter) in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note whether you chose a native term or the "string" loanword.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (native term vs. loanword, competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
