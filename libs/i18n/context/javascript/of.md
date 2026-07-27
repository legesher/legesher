# JavaScript Keyword: `of` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** operator-like particle (iteration-source marker)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes (CORE-1571 widening; reference.md § For-Of Loops)
**Difficulty:** MEDIUM

---

## Quick Summary

The `of` keyword appears in exactly one JEJ construct — the `for…of` statement — where it marks the **iterable whose values the loop walks**. `for (const item of items)` reads "for each item of items": the loop takes the *values* of the collection, one at a time, in order. It is the value-iteration counterpart to `in`, which tests *keys* and is a different keyword with a different meaning.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Visit every value in an array, in order
const items = [10, 20, 30];
for (const item of items) {
  console.log(item); // 10, then 20, then 30
}
```

**What this does:** `of` sits between the loop variable and the collection. Each pass of the loop binds the next *value* from `items` to `item`. The loop ends when the values run out.

### Example 2: Common Pattern

```javascript
// Strings are iterable: walk the characters
const word = "hi";
for (const letter of word) {
  console.log(letter); // "h", then "i"
}
```

**What this does:** `for…of` works on any iterable. Over a string it yields one character per pass — the values of the string, not its indices.

### Example 3: Edge Case

```javascript
// of yields VALUES; in tests KEYS — different keywords, different questions
const list = ["a", "b"];
for (const value of list) {
  console.log(value); // "a", then "b"  (the values)
}
console.log(0 in list);   // true  (the KEY/index 0 exists)
console.log("a" in list); // false ("a" is a value, not a key)
```

**What this shows:** `of` and `in` must never blur together. `of` drives value iteration inside a `for…of` head; `in` is a standalone operator testing key presence. A translation that reuses one word for both destroys the distinction JEJ teaches.

---

## Pattern Classification

**This term is:** ITERATION-SOURCE MARKER

**Similar terms in this pattern:**

1. `for` - `of` exists only inside the `for…of` head; the two must read as one natural phrase
2. `in` - The contrast case: keys (`in`) versus values (`of`); keep the two words clearly distinct
3. `includes` (member) - Also about values in a collection, but as a yes/no test, not iteration

**Pattern rule:** An iteration-source marker should read as a preposition drawing elements *from/out of* a source: "for each x **of** xs." It marks provenance of the values, not possession and not location.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *of*, from Proto-Germanic *ab* meaning "away from, off" — the preposition of source and origin, later also partitive ("one of them") and possessive ("the roof of the house").

**Why JavaScript uses this:** The committee wanted `for (x of xs)` to read as natural English: each `x` is drawn *of/from* `xs`. The partitive reading — an element taken from among a collection — is the operative one. (JavaScript could not reuse `in` because `for…in` already existed with key semantics.)

---

## Concept Explanation (Intermediate Level)

**What it does:**

Inside a `for…of` statement, `of` separates the per-iteration binding from the iterable expression. The loop asks the iterable for its values in order and runs the body once per value. In JEJ this is the canonical way to visit every element of an array or every character of a string.

The crucial cross-language trap: **Python spells this concept with "in"** (`for x in xs`). A translator carrying Python instincts will reach for the target language's "in" word — but JavaScript already uses `in` for a *different* concept (key/property presence), and both keywords live in the same partition, where **one native term cannot serve two concepts** (Rule 1) and two concepts cannot share one term (the collision gate throws). The `of` translation must therefore be a word clearly distinct from the `in` translation.

**Key behaviors:**

1. **Values, in order:** `for…of` yields the elements themselves — never indices, never keys.
2. **One construct only:** in JEJ, `of` appears only in the `for…of` head. It is not a general-purpose preposition elsewhere in code.
3. **Contextual keyword:** in full JavaScript, `of` is reserved only in this position — a variable may legally be named `of`. The engine translates the keyword by its position; learner identifiers are never touched.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Preposition/particle expressing source — "drawn from among"
- **Action vs State:** RELATION - marks where the loop's values come from
- **Temporal aspect:** Distributive - applies once per element, over the whole iteration

### Recommended Form

**Primary recommendation:** Use the target language's preposition for "from / from among / of (partitive)" — the word that reads naturally in "for each element **of** the collection." It must compose with the `for` translation into one fluent loop-head phrase.

**Forms to AVOID:**

- ❌ The word already chosen for `in` — the key/value distinction collapses and the keywords partition collides
- ❌ A possessive/genitive-only form ("belonging to") if it reads as ownership rather than source
- ❌ A verb ("take", "extract") — this is a particle inside a phrase, not an action

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: Possessive/genitive — "the color of the sky" (ownership/attribution)
- ✅ Meaning 2: **PARTITIVE/SOURCE** — "one of them," each element drawn from among the collection
- ❌ Meaning 3: Material — "made of wood"
- ⚠️ Meaning 4: Locative "in" — this is Python's spelling of the same loop concept; in JavaScript that word belongs to the `in` keyword and must not be reused

**Example:**

English "of" can mean:

1. "The roof of the house" (possession) ❌
2. "`for (const item of items)`" (each item drawn from among items) ✅ **This is the JavaScript meaning**
3. "A ring of gold" (material) ❌
4. Python's `for x in xs` (locative habit) ⚠️ — right concept, wrong word for JavaScript

**Your translation should capture meaning #2: values drawn one-by-one from a source collection.**

If the target language's most natural loop phrasing would reuse its "in" word, choose the next-most-natural source/partitive preposition instead — distinctness from `in` outranks micro-fluency, because both words are load-bearing keywords in the same partition.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `of`, check these translations:**

- [ ] `for` - The pair must read as one natural phrase: "for-each … of …"
- [ ] `in` - MUST be a different word; `in` = key presence, `of` = value iteration
- [ ] `includes` (member) - Related value-membership concept on the member axis; no collision risk (different partition) but the conceptual kinship should feel consistent

**Consistency rule:**

Read the full loop head aloud in the target language: `for (const x of xs)` must sound like a sentence a teacher would say. Then read `"key" in obj` aloud — if the same preposition appears in both, pick again for `of`.

### Functional relationships

**This term works WITH:**

1. **`of` with `const` bindings**:

```javascript
for (const item of items) {
  console.log(item);
}
```

2. **`of` over a string**:

```javascript
for (const ch of "abc") {
  console.log(ch);
}
```

**Common pairing:**

```javascript
// of iterates values; in tests keys — keep the words distinct
const pair = ["x", "y"];
for (const v of pair) {
  console.log(v); // "x", "y"
}
console.log(1 in pair); // true (index 1 exists)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- The partitive/source preposition is common in most languages (the easy part)
- The Python habit pulls hard toward the `in` word (the trap)
- Must compose fluently with the `for` translation as one phrase
- **AI confidence should be MEDIUM — verify distinctness from `in` explicitly**

### Why MEDIUM for `of`

- Lexically simple: nearly every language has a short "from/of" preposition
- Conceptually entangled: the same loop concept is spelled `in` in Python, and JavaScript's `in` is a sibling keyword in the same partition
- The collision gate makes reuse a hard error, so the model must reason about the *pair* of choices, not this word alone

**For this term:** MEDIUM

**Rationale:** The word itself is easy; the constraint system around it is not. A correct translation is chosen jointly with `in` — distinct words, each natural in its own construct. That pairwise reasoning is what lifts this above EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures VALUE iteration from a source collection?
- [ ] Reads naturally inside the loop head with the `for` translation?
- [ ] Avoids the possessive/ownership reading?

### 2. Linguistic Correctness

- [ ] Correct part of speech (preposition/particle)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] DIFFERENT word from the `in` translation?
- [ ] Composes with `for` into one natural phrase?
- [ ] No collision with any other keywords-partition term?

### 4. Usability

- [ ] Short enough (1-2 characters/words ideal)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common source preposition)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: of
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "each value drawn from the collection" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice. State explicitly that it differs from the word chosen for `in`, and quote both words side by side.

**Alternatives considered:**

List the candidate prepositions weighed in the target language and why each was rejected or kept — especially any candidate rejected for colliding with, or shading into, the `in` translation.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (in/of entanglement, loop-phrase fluency, competing regional prepositions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-27
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
