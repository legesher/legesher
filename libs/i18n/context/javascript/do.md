# JavaScript Keyword: `do` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control flow
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

The `do` keyword begins a `do...while` loop: it runs the loop body once *before* the condition is ever tested, then keeps repeating while the condition holds. It guarantees at least one execution, which is what distinguishes it from a plain `while` loop.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// The body runs once, then the condition is checked
let n = 0;
do {
  n = n + 1;
} while (n < 3);
// n is now 3
```

**What this does:** `do` runs the block first, incrementing `n`, and only afterward tests `n < 3`. The body always runs at least once.

### Example 2: Common Pattern

```javascript
// Run the action first, repeat while more work remains
let remaining = 5;
do {
  remaining = remaining - 1;
} while (remaining > 0);
```

**What this does:** The block executes, then `while (remaining > 0)` decides whether to loop again. `do` marks the "run first" body.

### Example 3: Edge Case

```javascript
// Even when the condition is false from the start, the body runs ONCE
let x = 100;
do {
  x = x + 1;
} while (x < 10);
// x is 101 — the body ran once despite 100 < 10 being false
```

**What this shows:** Unlike `while`, which may run zero times, `do...while` always runs its body at least once because the test comes *after* the body.

---

## Pattern Classification

**This term is:** LOOP / CONTROL-FLOW KEYWORD

**Similar terms in this pattern:**

1. `while` - The condition partner of `do`; tests before each pass (`do` tests after the first)
2. `for` - Another looping keyword, with initializer/condition/update in one header
3. `if` - Also gates a block on a condition, but runs it at most once, never repeats

**Pattern rule:** Loop keywords should read as verbs of *repeating / running*. `do` specifically means "run this body first, then check," so its translation must convey the *action of running the body*, distinct from `while`, which conveys the *condition of continuing*. Translate `do` and `while` as a coordinated pair.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *dōn* — "to perform, to act, to carry out." "Do" is the most general English verb of action: to make something happen.

**Why JavaScript uses this:** `do...while` reads as an English imperative: "**do** { this } **while** (that is true)." The `do` marks the action to perform; the `while` supplies the condition. The keyword deliberately evokes the plain-English instruction "do this, while the condition holds."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`do` introduces the body of a `do...while` loop. The body between the braces runs first, unconditionally. Only after it finishes does the loop evaluate the `while (...)` condition. If the condition is true, the body runs again; the cycle repeats until the condition becomes false.

The behavioral signature of `do` is the guarantee of *at least one* execution. A regular `while` loop checks its condition before the first pass and may therefore run its body zero times. A `do...while` loop inverts this: it acts first, asks later. This "run-then-test" ordering is the entire reason the keyword exists.

For translation, the important idea is the *action of running the body first*. `do` is not a condition, not a decision — it is the marker of "perform this block." The word should read as "do / run / perform," matched with a `while` that reads as "while / as long as."

**Key behaviors:**

1. **Body-first:** The block runs before the condition is ever evaluated.
2. **At least once:** The body always executes a minimum of one time.
3. **Paired with `while`:** `do` never appears alone; it always closes with a `while (...)` test.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Imperative loop-body marker ("perform this block")
- **Action vs State:** ACTION - it commands the body to run
- **Temporal aspect:** Repeated, but with the first pass guaranteed before any test

### Recommended Form

**Primary recommendation:** Use a short imperative verb meaning "do / perform / run," in a form that pairs naturally with the target-language translation of `while`. The reader should hear "do { … } while ( … )" as a coherent instruction.

**Forms to AVOID:**

- ❌ An auxiliary "do" (as in English question-forming "do you…") - the wrong grammatical sense (see Ambiguity Resolution)
- ❌ A noun form ("a deed / a task") - `do` marks an action, it is not a thing
- ❌ A word disconnected from the `while` translation - the pair must cohere as one construct

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: Auxiliary "do" that forms questions/negations ("**Do** you know?")
- ❌ Meaning 2: "Do" as a noun ("a hair-do," "the dos and don'ts")
- ✅ Meaning 3: **"PERFORM / RUN this block of work"** — the main-verb imperative sense

**Example:**

English "do" can mean:

1. "**Do** you understand?" (grammatical auxiliary, no meaning of its own) ❌
2. "That was a fancy **do**" (an event/thing — noun) ❌
3. "**Do** your homework" (perform this action) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the imperative "perform / run this," NOT the auxiliary or noun senses.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `do`, check these translations:**

- [ ] `while` - Its required partner; `do { } while ( )` must read as one coherent construct
- [ ] `for` - Another loop keyword; keep the register of loop verbs consistent
- [ ] `if` - Condition-gated block; ensure `do` reads as *action*, not *condition*

**Consistency rule:**

`do` and `while` form a single construct and must be translated so they read together. The `do` translation supplies the "perform this" verb; the `while` translation supplies the "as long as" condition. If the two are chosen independently, the loop reads as two unrelated words instead of one instruction.

**Example:**

If you translate `while` as "as-long-as," then:

- `do` should be an imperative that flows into it: "do { … } as-long-as ( … )"
- NOT: `do` as an auxiliary particle + `while` as a noun (incoherent ❌)

### Functional relationships

**This term works WITH:**

1. **`do` + `while`**: The mandatory pairing — body first, test after

```javascript
do {
  // work
} while (condition);
```

2. **`do` + a counter**: Run-then-decrement patterns

```javascript
let i = 3;
do {
  i = i - 1;
} while (i > 0);
```

**Common pairing:**

```javascript
// do...while guarantees the prompt-body runs at least once
let value = 0;
do {
  value = value + 1;
} while (value < 1);
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (run-then-test loop) is clear, but "do" is an extremely general English word with an auxiliary sense that carries no independent meaning in many languages. The translator must pick the main-verb "perform" sense and ensure it reads as a coherent pair with `while`. The risk is picking a bland or auxiliary "do" that does not signal "run the body."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (perform the body, then test to repeat)
- [ ] Would a native speaker read "do { } while ( )" as "run this, as long as …"?
- [ ] Avoids the auxiliary / noun senses of "do"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (imperative action verb, not auxiliary or noun)?
- [ ] Correct form (pairs with `while`)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Matches the pattern of other loop keywords?
- [ ] Reads coherently alongside `while`?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1 word ideally)?
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
term: do
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "perform / run this body first, then test" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, and coherent as a pair with `while`.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the auxiliary or noun senses of "do."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (over-general verb, auxiliary-sense risk, pairing with `while`, competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
