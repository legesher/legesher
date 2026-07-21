# JavaScript Keyword: `else` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `else` keyword introduces an alternative code block that executes when the preceding `if` condition is falsy. It represents the "otherwise" case in control flow — the branch taken when the `if` test does not hold. Chained as `else if`, it also builds multi-way decisions.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Basic if / else
let x = 10;
if (x > 20) {
  console.log("Greater than 20");
} else {
  console.log("20 or less");
}
// Output: 20 or less
```

**What this does:** When the `if` condition is false, the `else` block runs. Exactly one branch executes — either the `if` block or the `else` block, never both. This is binary decision making: do X or do Y.

### Example 2: Common Pattern

```javascript
// else if chain for multi-way branching
let score = 72;
if (score >= 90) {
  console.log("A");
} else if (score >= 70) {
  console.log("B");
} else {
  console.log("C or below");
}
// Output: B
```

**What this does:** `else if` tests a further condition only when earlier ones failed. The final bare `else` is the catch-all. Exactly one branch in the chain runs.

### Example 3: Edge Case

```javascript
// else binds to the nearest unmatched if
let a = 1;
let b = 0;
if (a > 0) {
  if (b > 0) {
    console.log("both positive");
  } else {
    console.log("a positive, b not");
  }
}
// Output: a positive, b not
```

**What this shows:** An `else` attaches to the closest preceding `if` that lacks one. Braces make this pairing explicit and unambiguous, which is why the JEJ subset always uses them.

---

## Pattern Classification

**This term is:** ALTERNATIVE CLAUSE KEYWORD

**Similar terms in this pattern:**

1. `if` - The condition that `else` provides the alternative to
2. `while` - Shares the conditional control-flow family
3. `break` - Another control-flow keyword used inside branches

**Pattern rule:** Alternative-clause keywords should use a conjunction or particle expressing contrast or alternative. "Else" means "otherwise" or "in the other case".

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *elles* meant "otherwise, in another way." It is the genitive of *el-* (other/else), related to Latin *alius* (other). "Else" fundamentally expresses "the other case."

**Why JavaScript uses this:** "Else" is the natural English word for presenting an alternative: "if X, do Y, else do Z." JavaScript inherited the C-family `if … else …` shape. Unlike Python, JavaScript uses `else if` (two words) rather than a fused `elif`, so `else` always stands as its own token.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `else` keyword introduces the alternative execution path of an `if` statement. It always means "in the other case" or "otherwise": when the `if` condition is falsy, control passes to the `else` block instead.

In an `if / else if / else` chain, the conditions are tested top to bottom; the first truthy one runs its block and the rest are skipped. A final bare `else` — with no condition — runs only when every preceding test failed. It is the default/fallback branch.

Unlike Python, JavaScript has no loop-`else` or `try`-`else` construct. `else` in JavaScript exists solely as the companion of `if`. This makes its role narrower and more predictable than the Python keyword it corresponds to: it is purely the conditional alternative.

**Key behaviors:**

1. **Mutually exclusive execution:** In an `if / else` pair, exactly one block runs. `else` is the default taken when the condition is falsy.
2. **Chains via `else if`:** Multi-way branching is written as `else if (…)`. This is `else` followed by a new `if`, not a distinct keyword.
3. **Always optional:** Every `if` may stand without an `else`. Adding `else` provides explicit handling for the "otherwise" case.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Adversative/alternative conjunction
- **Action vs State:** Neither - it is a structural marker introducing an alternative branch
- **Temporal aspect:** Immediate - introduces the alternative that executes when the condition fails

### Recommended Form

**Primary recommendation:** Use your language's word for "otherwise" or "if not." It should be a conjunction or particle that introduces an alternative scenario and reads as the natural opposite of "if."

**Forms to AVOID:**

- ❌ Bare negation "not" alone - `else` needs the alternative sense, not just negation
- ❌ "or" (logical disjunction) - `else` is a conditional alternative, not logical OR
- ❌ "then" - that pairs with "if", not with the alternative

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Additional, more" (adjective — "what else do you want?")
- ❌ Meaning 2: "Different" (adjective — "someone else")
- ✅ Meaning 3: **CONDITIONAL ALTERNATIVE** — "otherwise, if not, in the other case"

**Example:**

English "else" can mean:

1. "What else happened?" (additional/more) ❌
2. "Someone else did it" (different/other) ❌
3. "If not X, else do Y" (conditional alternative) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the alternative action when a condition is not met.**

Many languages have separate words for "else" as "other/different" (adjective) and "else" as "otherwise" (conditional alternative). Use the CONDITIONAL ALTERNATIVE form (otherwise / if not), not the adjective "other."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `else`, check these translations:**

- [ ] `if` - `else` is the natural opposite/alternative to `if`; they must read as a pair
- [ ] `while` - Shares the control-flow register
- [ ] `for` - Another control-flow keyword; keep register consistent

**Consistency rule:**

`if` and `else` are read side by side constantly. `else` must be the natural complement of your `if` translation, and `else if` must read as a smooth compound of the two words (JavaScript keeps them as two tokens, so they need not fuse, but they must sit together naturally).

**Example:**

Whatever word is chosen for `if`, `else` should be its "otherwise" complement, and `else if` should read naturally as that complement followed by the `if` word — not an unrelated third word ✅

### Functional relationships

**This term works WITH:**

1. **`if` + `else`**: Basic binary branching

```javascript
if (condition) {
  doSomething();
} else {
  doAlternative();
}
```

2. **`if` + `else if` + `else`**: Multi-way branching

```javascript
if (x > 0) {
  console.log("positive");
} else if (x < 0) {
  console.log("negative");
} else {
  console.log("zero");
}
```

**Common pairing:**

```javascript
// else as the fallback of a validity check
if (isValid) {
  process();
} else {
  reject();
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

### Why EASY for `else`

- Universal conditional-logic concept
- Every language expresses "otherwise / if not"
- Well-documented in programming globally
- Role is even simpler in JS than Python (no loop-else or try-else)

**For this term:** EASY

**Rationale:** The concept of "otherwise" or "in the other case" exists in all human languages; it is fundamental to conditional reasoning. Find the word meaning "otherwise" in conditional contexts.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The only consideration: distinguish "else" (conditional alternative) from "or" (logical disjunction) and "but" (contrast). Use the "otherwise" concept.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the ALTERNATIVE/OTHERWISE concept?
- [ ] Works in conditional context (if not X, do Y)?
- [ ] Distinct from "or" (options) and "but" (contrast)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adversative conjunction/particle)?
- [ ] Expresses conditional alternative (not mere difference)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Natural opposite/complement of the `if` translation?
- [ ] Reads naturally in an `else if` compound?
- [ ] Compatible with the other control-flow keywords?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common conditional word)?

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
term: else
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "conditional alternative / otherwise" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the adjective "other/different" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
