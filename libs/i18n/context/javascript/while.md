# JavaScript Keyword: `while` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `while` keyword creates a loop that repeatedly executes a block as long as a condition stays truthy. It is condition-based iteration: the loop continues until the condition becomes falsy, making it ideal when the number of passes is not known in advance.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Count down from 5
let count = 5;
while (count > 0) {
  console.log(count);
  count = count - 1;
}
// Output: 5, 4, 3, 2, 1
```

**What this does:** Tests `count > 0` before each pass. While true, it runs the block (log, then decrement). When `count` reaches 0 the condition is false and the loop exits.

### Example 2: Common Pattern

```javascript
// Keep processing until a sentinel value
let value = 1;
while (value !== 0) {
  console.log("Processing " + value);
  value = value - 1;
}
// Stops when value becomes 0
```

**What this does:** The loop continues until the condition becomes false. The condition is checked at the start of each pass, so the loop exits cleanly the moment `value` is `0`.

### Example 3: Edge Case

```javascript
// Intentional infinite loop with a break exit
while (true) {
  let done = checkStatus();
  if (done) {
    break;
  }
}
```

**What this shows:** `while (true)` is an always-true condition — a deliberate infinite loop. It exits via `break` based on logic inside the body. This pattern is common when the exit condition is complex or discovered mid-loop.

---

## Pattern Classification

**This term is:** STATE KEYWORD (Conditional Loop)

**Similar terms in this pattern:**

1. `if` - Tests a condition once, with no repetition
2. `for` - Counter-controlled loop with explicit init/step clauses
3. `break` - Exits a `while` or `for` loop early

**Pattern rule:** Loop keywords should use a conjunction or verb form suggesting ongoing/repeated action. "While" expresses duration — "during the time that" — making it a temporal conjunction.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *hwīl* meant "a period of time." The conjunction "while" came to mean "during the time that" or "as long as," expressing temporal duration together with a condition.

**Why JavaScript uses this:** "While" naturally expresses condition-based repetition: "while X is true, do Y." JavaScript inherited it from the C family, keeping the same `while (condition) { … }` shape. It reads clearly as both conditional and repeating, distinct from the counter-driven `for`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `while` loop implements condition-based repetition. Unlike `for`, which carries explicit counter clauses, `while` simply repeats its block for as long as the parenthesized condition stays truthy. The condition is evaluated before each pass (a pre-test loop); if it is falsy at the very start, the body never runs.

The engine evaluates the expression after `while` and coerces it with JavaScript truthiness (`0`, `""`, `null`, `undefined`, `NaN`, `false` are falsy). When the condition becomes falsy, the loop ends and execution continues after the `{ }` block.

`while` is the right tool when the number of passes depends on runtime conditions: waiting for input, consuming data until a sentinel, retrying an operation, or running a game/update loop. The body can exit early with `break` or skip to the next test with `continue`. JavaScript's `while` has no `else` clause — unlike Python, there is no while-else.

**Key behaviors:**

1. **Pre-test condition:** Checked before each pass, including the first. If false initially, the body runs zero times. (JavaScript's separate `do…while` runs at least once, but that is not part of the JEJ subset.)
2. **Infinite-loop risk:** If nothing in the body moves the condition toward falsy, the loop runs forever. Always ensure progress toward the exit.
3. **No else clause:** JavaScript's `while` cannot carry an `else`; the loop simply ends when the condition is falsy.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Temporal/conditional conjunction
- **Action vs State:** STATE - expresses an ongoing condition across a duration
- **Temporal aspect:** Continuous/durative - "during the time that" or "as long as"

### Recommended Form

**Primary recommendation:** Use the target language's natural word for "while" or "as long as" — a temporal conjunction expressing duration together with a condition, not a bare conditional like "if."

**Forms to AVOID:**

- ❌ The same word chosen for "if" - `while` adds the temporal duration that "if" lacks
- ❌ A word meaning "until" (negative condition) - `while` continues *while* true, not *until* true
- ❌ A verb form - `while` is not an action command

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "A period of time" (noun — "wait a while")
- ❌ Meaning 2: "Whereas, although" (contrastive — "I like tea while she likes coffee")
- ✅ Meaning 3: **TEMPORAL-CONDITIONAL** — "during the time that [condition is true]"

**Example:**

English "while" can mean:

1. "Let's rest for a while" (duration — noun) ❌
2. "I work while you sleep" (simultaneous actions — contrast) ⚠️
3. "While count > 0, log count" (conditional duration — loop) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: continuous repetition during the time that a condition is true.**

Some languages distinguish temporal-simultaneous "while" (two things at once) from conditional-durative "while" (repeat as long as it holds). Use the CONDITIONAL DURATIVE form. In many languages these are the same word, which is fine.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `while`, check these translations:**

- [ ] `if` - Related conditional form, but `while` must add temporal duration
- [ ] `for` - Both are loops; they should use compatible loop-introducer forms
- [ ] `break` / `continue` - Loop-control keywords that operate inside `while`

**Consistency rule:**

The two loops (`for`, `while`) and the conditionals (`if`, `else`) are all control-flow structures and should feel cohesive. Crucially, `while` must be distinct from `if`: `if` tests once, `while` repeats.

### Functional relationships

**This term works WITH:**

1. **`while (true)` + `break`**: Infinite loop with an internal exit

```javascript
while (true) {
  if (shouldExit) {
    break;
  }
}
```

2. **`while` + counter**: A hand-managed counting loop

```javascript
let i = 0;
while (i < 10) {
  console.log(i);
  i = i + 1;
}
```

**Common pairing:**

```javascript
// while driven by a changing flag
let done = false;
while (!done) {
  done = step();
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have a direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `while`

- Universal programming concept
- Every language has a temporal-conditional expression
- Well-established translations globally
- Clearly distinct from "if" and "for" in most languages

**For this term:** EASY

**Rationale:** "Repeat while a condition is true" exists in every programming and natural language. Every language can express "during the time that X, do Y." Use the temporal conjunction for "while."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The only consideration: capture the DURATIVE aspect (ongoing repetition), not just a single conditional test like "if."

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures REPEATED EXECUTION while a condition is true?
- [ ] Expresses DURATION/CONTINUITY (not just a single test)?
- [ ] Clearly different from "if" (single test) and "for" (counter loop)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (temporal conjunction)?
- [ ] Expresses duration + condition (not just condition)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Distinct from the `if` translation (different words for different concepts)?
- [ ] Compatible with the other loop keyword (`for`) and loop controls?
- [ ] Aligns with how loops are expressed in the target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common temporal word)?

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
term: while
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "temporal-conditional repetition" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that collapsed into the "if" or "until" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
