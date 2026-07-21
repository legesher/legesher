# JavaScript Keyword: `continue` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control_flow (loop control)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `continue` keyword skips the rest of the current loop pass and immediately proceeds to the next one. Unlike `break`, which exits the loop entirely, `continue` stays in the loop and jumps ahead to its next iteration, where the condition (and, in a `for` loop, the step) is re-evaluated.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Skip even numbers
for (let i = 0; i < 6; i = i + 1) {
  if (i % 2 === 0) {
    continue; // skip the rest of this pass for even numbers
  }
  console.log(i);
}
// Output: 1, 3, 5 (even numbers skipped)
```

**What this does:** `continue` skips the remaining code in the current pass and jumps to the next one. When `i` is even, `console.log(i)` never runs — the loop moves straight to the next value of `i`.

### Example 2: Common Pattern

```javascript
// Process only valid items
let items = ["apple", "", "banana", "", "orange"];
for (let i = 0; i < items.length; i = i + 1) {
  if (!items[i]) { // skip empty strings (falsy)
    continue;
  }
  console.log("Processing " + items[i]);
}
// Output: Processing apple, Processing banana, Processing orange
```

**What this does:** A common pattern — filter out invalid entries and process only the valid ones. `continue` gives an early exit from the pass without deeply nesting the processing logic in an `else`.

### Example 3: Edge Case

```javascript
// continue in a while loop — advance the counter FIRST
let count = 0;
while (count < 5) {
  count = count + 1;
  if (count === 3) {
    continue; // skip logging 3
  }
  console.log(count);
}
// Output: 1, 2, 4, 5
```

**What this shows:** In a `while` loop, `continue` jumps back to the condition test. If you have not already advanced the loop variable before `continue`, you risk an infinite loop. In a `for` loop this is safer, because the step clause still runs on the way to the next pass.

---

## Pattern Classification

**This term is:** CONTROL FLOW KEYWORD (Loop Control)

**Similar terms in this pattern:**

1. `break` - Exits the loop entirely (terminates it)
2. `return` - Exits an entire function
3. `for` / `while` - The loops that `continue` operates within

**Pattern rule:** Loop-control keywords should use verb forms expressing the control action. "Continue" means to proceed to the next pass, skipping the current one.

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin *continuare* meant "join together, make continuous." Through Old French *continuer* it became English "continue" — to keep going, persist, resume. In programming, `continue` means to proceed with the next pass, keeping the loop going.

**Why JavaScript uses this:** "Continue" naturally expresses proceeding to the next pass. JavaScript inherited it from C. Reading `continue` as "continue to the next iteration" is intuitive; alternatives like "skip" or "next" are less standard across languages.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `continue` statement skips the remainder of the current loop pass and jumps ahead to the loop's next pass. In a `for` loop, that means running the step clause and then re-testing the condition. In a `while` loop, it means re-evaluating the condition directly.

`continue` is commonly used for: filtering (process only valid items, skip the rest), guarding against bad data (skip entries that would cause errors), and code clarity (handle special cases early instead of nesting the main logic in an `else`).

Important: `continue` only affects the innermost loop. In nested loops, outer loops are unaffected. Unlike `break`, which leaves the loop, `continue` stays in it — it merely skips ahead. (JavaScript supports labeled `continue` to target an outer loop, but labels are outside the JEJ subset.)

**Key behaviors:**

1. **Skips to the next pass:** The remaining code in the current pass never runs; control jumps ahead. The loop keeps going (unlike `break`).
2. **Re-enters the loop machinery:** In a `for` loop, the step clause runs before the next condition test; in a `while` loop, the condition is re-tested directly — so a `while` loop must advance its variable before `continue` or risk looping forever.
3. **Affects the innermost loop only:** In nested loops, `continue` skips only the current pass of the innermost loop; outer loops proceed normally.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb (imperative — a command to continue)
- **Action vs State:** ACTION - a command to proceed to the next pass
- **Temporal aspect:** Instantaneous - immediate jump to the next pass

### Recommended Form

**Primary recommendation:** Use a verb meaning "to continue" or "to proceed" (imperative or infinitive per the language's convention for commands). It should convey moving forward or keeping the loop's momentum.

**Forms to AVOID:**

- ❌ "next" where "continue" is the more standard verb
- ❌ "skip" — it emphasizes skipping over continuing
- ❌ A noun like "continuation" instead of the verb "continue"

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (minor ambiguity)

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Resume after a pause" (continue after lunch)
- ✅ Meaning 2: **PROCEED TO THE NEXT PASS** (skip the rest of this pass, continue the loop)
- ❌ Meaning 3: "Persist / keep trying" (continue working hard)

**Example:**

English "continue" can mean:

1. "We'll continue after a break" (resume) ❌
2. "Continue to the next loop pass" (skip the rest, proceed) ✅ **This is the JavaScript meaning**
3. "Continue working hard" (persist) ❌

**Your translation should capture meaning #2: proceeding to the next pass of a loop, skipping the remainder of the current pass.**

Use the verb for continuing or proceeding forward in the context of repetition/cycles.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `continue`, check these translations:**

- [ ] `break` - Related loop control; should feel related but distinct (skip vs exit)
- [ ] `return` - Function exit; must be distinguished
- [ ] `for` / `while` - The loops that `continue` operates within

**Consistency rule:**

Loop-control keywords (`break`, `continue`) should use action verbs and be clearly distinct: `break` leaves the loop, `continue` skips to the next pass. Both differ from `return` (exit function).

### Functional relationships

**This term works WITH:**

1. **`continue` in a `for` loop**:

```javascript
for (let i = 0; i < items.length; i = i + 1) {
  if (shouldSkip(items[i])) {
    continue;
  }
  process(items[i]);
}
```

2. **`continue` in a `while` loop** (advance first):

```javascript
let i = 0;
while (i < 10) {
  i = i + 1; // advance BEFORE continue
  if (i % 2 === 0) {
    continue;
  }
  console.log(i);
}
```

**Common pairing:**

```javascript
// continue vs break in the same loop
for (let i = 0; i < items.length; i = i + 1) {
  if (isInvalid(items[i])) {
    continue; // skip this item, process others
  }
  if (isFatal(items[i])) {
    break;    // stop processing entirely
  }
  process(items[i]);
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (skip to the next pass)
- Most languages have an equivalent
- Universal in programming
- **AI confidence should be HIGH**

### Why EASY for `continue`

- Universal concept (loop continuation)
- The verb "continue" exists in most languages
- Standard in programming globally
- Direct semantic mapping

**For this term:** EASY

**Rationale:** Continuing to the next pass is universal in programming, and the verb "continue" (proceed, keep going) exists in most languages and maps directly. Use that verb.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SKIP-TO-NEXT-PASS (not exit loop)?
- [ ] Conveys continuation of the loop, not termination?
- [ ] Distinct from `break` (exit) and `return` (exit function)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb — imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Distinguished from `break` and `return`?
- [ ] All control-flow keywords use verb forms?
- [ ] Natural complement to `break`?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common verb)?

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
term: continue
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "proceed to the next pass" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward "resume" or "persist."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
