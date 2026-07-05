# Python Keyword: `continue` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control_flow (loop control)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `continue` keyword skips the rest of the current loop iteration and immediately proceeds to the next iteration. Unlike `break` which exits the loop entirely, `continue` just skips to the next cycle. The loop condition is re-evaluated for the next iteration.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Skip even numbers
for i in range(6):
    if i % 2 == 0:
        continue  # Skip rest of iteration for even numbers
    print(i)
# Output: 1, 3, 5 (even numbers skipped)
```

**What this does:** `continue` skips the remaining code in the current iteration and jumps to the next iteration. When `i` is even, `print(i)` never executes - loop immediately moves to next value of `i`.

### Example 2: Common Pattern

```python
# Process only valid items
items = ["apple", None, "banana", "", "orange", None]

for item in items:
    if not item:  # Skip None and empty strings
        continue
    print(f"Processing: {item}")
# Output:
# Processing: apple
# Processing: banana
# Processing: orange

# Skip errors, process rest
for file in files:
    if not file.exists():
        continue  # Skip missing files
    process(file)
```

**What this does:** Common pattern: filter out invalid items and process only valid ones. `continue` provides early return from iteration without nesting all processing logic in an `else` block. Cleaner than deep nesting.

### Example 3: Edge Case

```python
# Continue in nested loops
for i in range(3):
    for j in range(3):
        if j == 1:
            continue  # Skips only inner iteration
        print(f"i={i}, j={j}")
# Output:
# i=0, j=0
# i=0, j=2
# i=1, j=0
# i=1, j=2
# i=2, j=0
# i=2, j=2

# Continue in while loop
count = 0
while count < 5:
    count += 1
    if count == 3:
        continue  # Skip printing 3
    print(count)
# Output: 1, 2, 4, 5
```

**What this shows:** `continue` only affects the innermost loop containing it. In nested loops, outer loop unaffected. Works in both `for` and `while` loops. Important: in `while` loops, make sure to update loop variable before `continue`, or risk infinite loop.

---

## Pattern Classification

**This term is:** CONTROL FLOW KEYWORD (Loop Control)

**Similar terms in this pattern:**

1. `break` - Exit loop entirely (terminates loop)
2. `return` - Exit function entirely
3. `pass` - Do nothing (placeholder, doesn't affect flow)

**Pattern rule:** Loop control keywords should use verb forms expressing the control action. "Continue" means to proceed to the next iteration, skipping the current one.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "continuare" meant "join together, make continuous." Through Old French "continuer," it became English "continue" - to keep going, persist, resume. In programming, "continue" means to proceed with the next cycle, maintaining the loop's continuation.

**Why Python uses this:** "Continue" naturally expresses proceeding to the next iteration. Borrowed from C and other languages. Reading "continue" as "continue to next iteration" is intuitive. Alternative terms like "skip" or "next" are less standard across programming languages.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `continue` statement skips the remainder of the current loop iteration and immediately jumps to the loop's condition check for the next iteration. In `for` loops, this means getting the next item from the iterable. In `while` loops, this means re-evaluating the while condition.

`continue` is commonly used for: filtering out unwanted items (process only valid items, skip invalid ones), error handling (skip items that cause errors, continue with rest), optimization (skip expensive processing for items that don't meet criteria), and code clarity (avoid deep nesting by handling special cases early).

Important: `continue` only affects the innermost loop. In nested loops, outer loops are unaffected. Unlike `break` which exits the loop, `continue` stays in the loop but skips to next iteration. The loop's `else` clause still executes after all iterations complete (unless `break` is used).

**Key behaviors:**

1. **Skips to next iteration:** Remaining code in current iteration never executes. Control immediately jumps to next iteration. Loop continues running (unlike `break` which exits entirely).

2. **Works with loop condition:** In `for` loops, next item from iterable is fetched. In `while` loops, condition is re-evaluated. This means `while` loops must update their condition before `continue`, or risk infinite loop.

3. **Affects innermost loop only:** In nested loops, `continue` only skips the current iteration of the innermost loop. Outer loops continue normally. For multi-level skip, need different approach.

4. **Doesn't affect else clause:** Loop's `else` clause executes normally after all iterations (even if some used `continue`). Only `break` causes `else` to be skipped.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (imperative - command to continue)
- **Action vs State:** ACTION - command to proceed to next iteration
- **Temporal aspect:** Instantaneous - immediate jump to next iteration

### Recommended Form

**Primary recommendation:** Use verb form meaning "to continue" or "to proceed" (imperative or infinitive depending on language conventions for commands). This should convey proceeding forward or maintaining momentum.

**Forms to AVOID:**

- ❌ Using "next" when "continue" is more standard
- ❌ Using "skip" which emphasizes skipping over continuing
- ❌ Using noun "continuation" instead of verb "continue"

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (minor ambiguity)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Resume after pause" (continue after lunch break)
- ✅ Meaning 2: **PROCEED TO NEXT ITERATION** (skip rest of current cycle, continue loop)
- ❌ Meaning 3: "Persist/keep going" (continue trying)

**Example:**

English "continue" can mean:

1. "We'll continue after a break" (resume) ❌
2. "Continue to next loop iteration" (skip rest, proceed) ✅ **This is the Python meaning**
3. "Continue working hard" (persist) ❌

**Your translation should capture meaning #2: proceeding to the next iteration of a loop, skipping the remainder of the current iteration.**

Use the verb for continuing or proceeding forward in the context of repetition/cycles.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `continue`, check these translations:**

- [ ] `break` - Related loop control; should feel related but distinct (exit vs skip)
- [ ] `return` - Function exit; should be distinguished
- [ ] `for`/`while` - Loop keywords that `continue` operates within
- [ ] `pass` - Another control flow keyword (do nothing)

**Consistency rule:**

Loop control keywords (`break`, `continue`) should use action verbs. They should be distinct from each other: `break` exits loop entirely, `continue` skips to next iteration. Both are distinct from `return` (exit function).


### Functional relationships

**This term works WITH:**

1. **`continue` in for loop**:

```python
for item in items:
    if should_skip(item):
        continue
    process(item)
```

2. **`continue` in while loop**:

```python
while condition:
    value = get_value()
    if value.is_invalid():
        continue
    process(value)
```

**Common pairing:**

```python
# Filter items with continue
for item in items:
    if not item.is_valid():
        continue  # Skip invalid items
    process(item)

# Skip empty/None values
for value in values:
    if not value:
        continue
    print(value)

# Error handling with continue
for file in files:
    try:
        data = load(file)
    except FileNotFoundError:
        continue  # Skip missing files
    process(data)

# Multiple skip conditions
for item in items:
    if item.is_expired():
        continue
    if item.is_empty():
        continue
    if item.is_invalid():
        continue
    process(item)  # Only valid items reach here

# Continue in nested loops
for i in range(5):
    for j in range(5):
        if j % 2 == 0:
            continue  # Skip even j values
        print(f"{i},{j}")

# Continue in while loop (careful with updates!)
i = 0
while i < 10:
    i += 1  # Update BEFORE continue!
    if i % 2 == 0:
        continue
    print(i)

# Continue vs break comparison
for item in items:
    if item.is_invalid():
        continue  # Skip this item, process others
    if item.is_critical_error():
        break     # Stop processing entirely
    process(item)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (skip to next iteration)
- Most languages have equivalent
- Universal in programming
- **AI confidence should be HIGH**

### Why EASY for `continue`

- Universal concept (loop continuation)
- "Continue" verb exists in most languages
- Standard in programming globally
- Direct semantic mapping

**For this term:** EASY

**Rationale:** The concept of continuing to the next iteration is universal in programming. The verb "continue" (proceed, keep going) exists in most languages and translates directly. Translation is straightforward: use the verb for continuing or proceeding.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SKIP TO NEXT ITERATION concept (not exit loop)?
- [ ] Conveys continuation of loop, not termination?
- [ ] Distinct from `break` (exit) and `return` (exit function)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb - imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Distinguished from `break` (exit) and `return` (exit function)?
- [ ] All control flow keywords use verb forms?
- [ ] Natural opposite/complement to `break`?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
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

Explain why the recommended term carries this concept's semantic components in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.


---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
