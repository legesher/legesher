# JavaScript Keyword: `for` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction/preposition
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `for` keyword creates a counter-controlled loop that repeats a block of code. JavaScript's canonical form is the C-style `for (init; condition; step)`: an initializer runs once, a condition is tested before each pass, and a step runs after each pass. It is the primary way to repeat an action a controlled number of times.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Count from 0 up to 2
for (let i = 0; i < 3; i = i + 1) {
  console.log(i);
}
// Output: 0, 1, 2 (each on its own line)
```

**What this does:** `let i = 0` runs once. Before each pass the engine tests `i < 3`; if true it runs the block, then runs `i = i + 1`. When the test becomes false the loop ends.

### Example 2: Common Pattern

```javascript
// Sum the numbers 1 through 5
let total = 0;
for (let n = 1; n <= 5; n = n + 1) {
  total = total + n;
}
console.log(total); // 15
```

**What this does:** The three clauses — start at 1, continue while `n <= 5`, increment by 1 — drive a running sum. The loop variable `n` is scoped to the loop.

### Example 3: Edge Case

```javascript
// The condition can be false from the start: the body never runs
for (let i = 5; i < 5; i = i + 1) {
  console.log("never reached");
}
console.log("after loop"); // only this logs
```

**What this shows:** The condition is a pre-test, checked before the first pass. If it is false immediately, the body executes zero times. This is JavaScript's mechanical, C-style loop — distinct from Python's `for x in y`, which walks the elements of a collection.

---

## Pattern Classification

**This term is:** ITERATION KEYWORD

**Similar terms in this pattern:**

1. `while` - Condition-based loop with no built-in counter clauses
2. `break` - Exits a `for` or `while` loop early
3. `continue` - Skips to the next pass of a `for` or `while` loop

**Pattern rule:** Iteration keywords may use a preposition or verb form depending on the target language's natural loop phrasing. The word should suggest "repeating" or "going through" a controlled sequence of passes.

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin *pro* meant "for, on behalf of, instead of." Through Old French *por* it became English "for" with senses including "in place of," "because of," and "in respect to." In loop contexts, "for each step" evolved from "in respect to each step."

**Why JavaScript uses this:** JavaScript inherited the C-family `for (init; condition; step)` construct wholesale. The word "for" heads a loop that repeats "for" as long as its condition holds. Unlike Python's readable "for each item in list," JavaScript's `for` is the mechanical three-clause counter loop, so the word functions more as a bare loop-introducer than as a distributive "for each."

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `for` loop implements counter-controlled repetition. Its header has three semicolon-separated clauses inside parentheses: an **initializer** (run once, before anything else — typically `let i = 0`), a **condition** (tested before every pass; the loop continues while it is truthy), and a **step** (run after every pass — typically `i = i + 1`). The `{ }` block is the loop body.

This is fundamentally different from Python's `for`. Python's `for x in iterable:` is a "foreach" that walks each element of a collection and never exposes a counter. JavaScript's `for` is the traditional C-style loop: you manage the counter, the bound, and the increment yourself. To visit each element of an array in the JEJ subset, you drive an index counter and read `arr[i]`.

The condition uses JavaScript truthiness (`0`, `""`, `null`, `undefined`, `NaN`, `false` are falsy). Because you control the step, a `for` loop that never advances its counter toward the bound will run forever — the same infinite-loop hazard as `while`.

**Key behaviors:**

1. **Three explicit clauses:** initializer, condition, step. Any clause may be empty, but the two semicolons are required.
2. **Pre-test condition:** The condition is checked before each pass, including the first; a false condition at the start means zero passes.
3. **Block-scoped counter:** A counter declared with `let` in the initializer is scoped to the loop and is not visible after it.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Preposition (in English) heading a loop clause, though this varies by language
- **Action vs State:** Hybrid - it initiates repeated action but the framing is prepositional ("for … repeat")
- **Temporal aspect:** Repeated/iterative - the body runs multiple times, once per pass

### Recommended Form

**Primary recommendation:** Use the target language's natural word for heading a repetition/loop — the equivalent of "for" as a loop introducer. Depending on the language this may be a preposition, a short compound, or a verb of repeating.

**Forms to AVOID:**

- ❌ A duration word ("for hours") - wrong sense of "for"
- ❌ "to" instead of "for" - wrong prepositional meaning
- ❌ Overly verbose phrases (>3 words) - reduces readability

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Because, since" (causal — "I stayed home **for** I was sick")
- ❌ Meaning 2: "In favor of" (support — "Are you **for** or against?")
- ❌ Meaning 3: "Intended to benefit" (purpose — "This gift is **for** you")
- ❌ Meaning 4: "Duration" (time — "We talked **for** hours")
- ✅ Meaning 5: **ITERATIVE/LOOP** — "repeat, for as long as this condition holds"

**Example:**

English "for" has many meanings:

1. "I voted **for** the proposal" (in favor) ❌
2. "I've lived here **for** ten years" (duration) ❌
3. "**For** each step from 0 while i < n, do this" (looping/repetition) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #5: controlled repetition of a block of code.**

In many languages the word for "duration" differs from the word that heads a loop. Use the loop/iterative form, not the temporal "during" form.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `for`, check these translations:**

- [ ] `while` - Both are loop keywords; they should use compatible loop-introducer forms
- [ ] `break` - Exits the loop; keep the control-flow register consistent
- [ ] `continue` - Skips to the next pass; keep it cohesive with `for`

**Consistency rule:**

`for` and `while` are the two loops in the JEJ subset. They should feel like siblings — both readable as "start a loop" — so a learner recognizes them as members of the same family. Note that JavaScript's `for` is NOT paired with `in` the way Python's is: JavaScript `in` is a separate property-test operator (see `in`).

### Functional relationships

**This term works WITH:**

1. **`for` + counter**: The standard counting loop

```javascript
for (let i = 0; i < 10; i = i + 1) {
  console.log(i);
}
```

2. **`for` + `break` / `continue`**: Loop control

```javascript
for (let i = 0; i < 10; i = i + 1) {
  if (i === 5) {
    break; // exit the loop early
  }
}
```

**Common pairing:**

```javascript
// Walk an array by index in the JEJ subset
let items = [10, 20, 30];
for (let i = 0; i < items.length; i = i + 1) {
  console.log(items[i]);
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have a direct equivalent
- No ambiguity once the loop sense is fixed
- **AI confidence should be HIGH**

### Why EASY for `for`

- Universal iteration concept
- Most languages have a standard word to head a loop
- Well-established in programming across languages
- JavaScript's `for` stands alone (no `for … in` pairing to coordinate), simplifying the choice

**For this term:** EASY

**Rationale:** Every language can express repetition, and the loop-heading "for" has well-documented precedents in CS education. Because JavaScript's `for` is the mechanical C-style loop rather than Python's "for each," the translator should pick the loop-introducer sense, not a "for each item" phrase.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Main question: "Does the chosen word naturally head a repetition/loop in the target language?" If yes, confidence should be HIGH.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the ITERATION/REPETITION concept (a controlled counter loop)?
- [ ] Conveys "repeat" rather than "for each element of a collection"?
- [ ] Avoids temporal "during" or causal "because" meanings?

### 2. Linguistic Correctness

- [ ] Correct part of speech (preposition or appropriate loop-introducer)?
- [ ] Correct form (iterative/looping, not temporal/causal)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Compatible with the `while` translation (both read as loops)?
- [ ] Distinct from `in`, which is a separate operator in JS?
- [ ] Aligns with how loops are expressed in target-language programming?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

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
term: for
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "controlled repetition / loop" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the duration or "for each" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
