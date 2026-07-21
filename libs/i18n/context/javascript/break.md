# JavaScript Keyword: `break` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control_flow (loop control)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `break` keyword immediately exits the innermost enclosing loop (`for` or `while`), terminating it regardless of the loop's condition. Execution continues with the first statement after the loop. It is used to leave a loop early once a condition is met.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Break out of a for loop
for (let i = 0; i < 10; i = i + 1) {
  if (i === 5) {
    break; // exit when i reaches 5
  }
  console.log(i);
}
// Output: 0, 1, 2, 3, 4 (stops at 5)
```

**What this does:** `break` terminates the loop immediately. When `i` reaches 5 the loop exits entirely; the remaining passes never run. Control jumps to the statement after the loop.

### Example 2: Common Pattern

```javascript
// Search and stop when found
let items = ["apple", "banana", "orange", "grape"];
let target = "orange";
for (let i = 0; i < items.length; i = i + 1) {
  if (items[i] === target) {
    console.log("Found: " + items[i]);
    break; // no need to keep searching
  }
}

// while (true) with break as the exit
while (true) {
  let cmd = nextCommand();
  if (cmd === "quit") {
    break;
  }
}
```

**What this does:** A common pattern — scan a list and leave once the item is found. Also used with `while (true)` to build a loop whose exit is decided inside the body. Avoids unnecessary passes.

### Example 3: Edge Case

```javascript
// break exits only the innermost loop
for (let i = 0; i < 3; i = i + 1) {
  for (let j = 0; j < 3; j = j + 1) {
    if (j === 1) {
      break; // exits the inner loop only
    }
    console.log("i=" + i + ", j=" + j);
  }
}
// Output: i=0 j=0, i=1 j=0, i=2 j=0
```

**What this shows:** `break` leaves only the innermost loop that contains it. In nested loops, the outer loop keeps running. To leave several levels at once you restructure the code or use a flag.

---

## Pattern Classification

**This term is:** CONTROL FLOW KEYWORD (Loop Control)

**Similar terms in this pattern:**

1. `continue` - Skips the current pass, then continues with the next
2. `return` - Exits an entire function (loop-independent)
3. `for` / `while` - The loops that `break` exits from

**Pattern rule:** Loop-control keywords should use verb forms expressing interruption or termination. "Break" means to stop or interrupt the loop.

---

## Etymology (Brief)

**English Origin:** Germanic/Old English

**Root meaning:** Old English *brecan* meant "to break, shatter, burst," from Proto-Germanic *brekan*. Metaphorically extended to "interrupt, stop" — as in "break the silence." In programming, `break` interrupts the normal flow of a loop.

**Why JavaScript uses this:** "Break" is an intuitive metaphor for exiting a loop — you "break out" of the cycle. JavaScript inherited it from C, where the same keyword serves the same role. Breaking the loop's pattern is a natural image shared across many languages.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `break` statement immediately terminates the innermost `for` or `while` loop that contains it. The loop's condition is ignored — even if it would allow more passes, the loop ends. Control flow jumps to the first statement after the loop block.

`break` is commonly used for: early exit once a condition is met (a search finds its item), infinite loops that exit on an internal condition (`while (true)` with a conditional `break`), and optimization (stop looping once the goal is achieved).

Important: `break` only affects the innermost loop. In nested loops the outer loops keep running. To leave multiple levels you use flags or restructure the code. (JavaScript also supports labeled `break` to target an outer loop, but labels are outside the JEJ subset.)

**Key behaviors:**

1. **Exits the innermost loop only:** In nested loops, `break` leaves only the loop directly containing it; outer loops continue.
2. **Skips remaining passes:** Once `break` runs, all remaining passes are abandoned and the condition is not checked again — immediate exit to the code after the loop.
3. **Pairs with `while (true)`:** The idiom `while (true) { … break; }` creates an infinite loop with a conditional exit inside the body.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb (imperative — a command to break/exit)
- **Action vs State:** ACTION - a command to terminate the loop
- **Temporal aspect:** Instantaneous - immediate effect

### Recommended Form

**Primary recommendation:** Use a verb meaning "to break" or "to interrupt" (imperative or infinitive per the language's convention for commands). It should convey stopping or exiting forcefully.

**Forms to AVOID:**

- ❌ A noun like "breakage" instead of the verb "break"
- ❌ "stop" when "break" captures a more forceful exit
- ❌ "exit" without distinguishing it from function exit (`return`)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Physical breaking" (break a glass)
- ❌ Meaning 2: "Rest period" (take a break)
- ✅ Meaning 3: **INTERRUPT/EXIT LOOP** (break out of the cycle)
- ❌ Meaning 4: "Malfunction" (the car broke)

**Example:**

English "break" can mean:

1. "Break a window" (physical breaking) ❌
2. "Coffee break" (rest period) ❌
3. "Break out of the loop" (exit/interrupt) ✅ **This is the JavaScript meaning**
4. "The machine broke" (malfunction) ❌

**Your translation should capture meaning #3: interrupting or exiting a loop forcefully.**

Use the word for breaking out of or interrupting a pattern, not physical breaking or resting.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `break`, check these translations:**

- [ ] `continue` - Related loop control; should feel related but clearly distinct
- [ ] `return` - Function exit; must be distinguished from loop exit
- [ ] `for` / `while` - The loops that `break` exits from

**Consistency rule:**

Loop-control keywords (`break`, `continue`) should use action verbs, distinct from each other and from `return` (function exit). All three are commands but affect different scopes.

### Functional relationships

**This term works WITH:**

1. **`break` in a `for` loop**:

```javascript
for (let i = 0; i < items.length; i = i + 1) {
  if (condition) {
    break;
  }
}
```

2. **`break` in a `while` loop**:

```javascript
while (condition) {
  if (exitCondition) {
    break;
  }
}
```

**Common pairing:**

```javascript
// break vs continue side by side
for (let i = 0; i < items.length; i = i + 1) {
  if (isInvalid(items[i])) {
    continue; // skip this one, keep looping
  }
  if (isCriticalError(items[i])) {
    break;    // stop looping entirely
  }
  process(items[i]);
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (exit the loop)
- Most languages have an equivalent
- Universal in programming
- **AI confidence should be HIGH**

### Why EASY for `break`

- Universal concept (loop termination)
- The "break" metaphor translates well across languages
- Standard in programming globally
- Clear verb form in most languages

**For this term:** EASY

**Rationale:** Exiting a loop early is universal, and "breaking out" of a cycle translates naturally. Most languages have a verb for breaking or interrupting. Use that verb.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOOP EXIT (not function exit)?
- [ ] Conveys immediate termination?
- [ ] Distinct from `continue` (skip pass) and `return` (exit function)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb — imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Distinguished from `continue` and `return`?
- [ ] All control-flow keywords use verb forms?
- [ ] Keeps the "break" metaphor if natural in the target language?

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
term: break
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "interrupt/exit the loop" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward "rest," "physical breaking," or "malfunction."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
