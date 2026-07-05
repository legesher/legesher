# Python Keyword: `elif` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control_flow (conditional)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `elif` keyword (contraction of "else if") provides additional conditional branches in if-elif-else chains. It tests an alternative condition only if previous conditions were false. Allows multiple mutually exclusive conditions without deep nesting.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic if-elif-else
x = 5
if x < 0:
    print("Negative")
elif x == 0:
    print("Zero")
else:
    print("Positive")
# Output: Positive
```

**What this does:** `elif` provides a second condition to test if the first `if` was false. Checks `x == 0` only if `x < 0` was false. More readable than nested if-else. Only one branch executes.

### Example 2: Common Pattern

```python
# Multiple elif branches
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

# elif without final else
age = 15
if age < 13:
    category = "child"
elif age < 18:
    category = "teen"
elif age < 65:
    category = "adult"
# If none match, nothing happens (no else branch)
```

**What this does:** Can have multiple `elif` branches - tests them sequentially until one is true. Final `else` is optional. Common for categorization or range checking. First matching condition wins - remaining branches skipped.

### Example 3: Edge Case

```python
# Short-circuit evaluation in elif
x = 10
if x > 20:
    result = "large"
elif x > 15:
    result = "medium"  # Not tested - previous would catch it
elif x > 5:
    result = "small"   # This executes
# First true condition wins - rest not evaluated

# elif vs nested if
# With elif (flat structure)
if condition1:
    action1()
elif condition2:
    action2()
elif condition3:
    action3()

# Without elif (nested structure - harder to read)
if condition1:
    action1()
else:
    if condition2:
        action2()
    else:
        if condition3:
            action3()
```

**What this shows:** `elif` short-circuits - first true condition executes, rest are skipped. Even if multiple conditions could be true, only first wins. `elif` avoids deeply nested if-else structures - keeps code flat and readable.

---

## Pattern Classification

**This term is:** CONTROL FLOW KEYWORD (Conditional Branching)

**Similar terms in this pattern:**

1. `if` - Primary condition (always first)
2. `else` - Final fallback (catches everything else)
3. Ternary expression (`x if condition else y`) - Single-line conditional

**Pattern rule:** Conditional keywords should express testing/checking. "Elif" is compound of "else" + "if" - alternative condition. Creates chain of mutually exclusive branches.


---

## Etymology (Brief)

**English Origin:** Compound (else + if)

**Root meaning:** "Elif" is a Python-specific contraction of "else if" - meaning "otherwise, if (this other condition)." Combines two English words: "else" (otherwise, if not) + "if" (conditional test). Created to avoid deep nesting while maintaining readability.

**Why Python uses this:** Many languages use "else if" (two words) or "elseif" (one word). Python chose `elif` as short, memorable contraction. Saves horizontal space and typing while being clear. Alternative was requiring nested if-else (verbose) or allowing dangling else (ambiguous like C).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `elif` keyword creates additional conditional branches in an if-elif-else chain. It combines "else" (if previous conditions failed) with "if" (test new condition). Each `elif` is evaluated only if all previous conditions (if and earlier elif) were false.

Execution flow: Python evaluates `if` condition. If true, executes that block and skips all `elif` and `else`. If false, tries first `elif`. If that's true, executes and skips remaining. Continues down the chain until finding true condition or reaching `else` (or end of chain).

Key advantage: `elif` keeps conditionals flat instead of nested. Without `elif`, you'd need nested if-else blocks (harder to read, increasing indentation). With `elif`, all alternatives are at the same indentation level - more readable.

**Key behaviors:**

1. **Sequential evaluation:** Conditions tested in order from top to bottom. First true condition wins. Remaining conditions not evaluated (short-circuit). Only one branch ever executes in an if-elif-else chain.

2. **Requires preceding if:** Cannot use `elif` without `if` first. `elif` is continuation of if-statement, not standalone. Can have many `elif` clauses (no limit) but must start with `if`.

3. **Optional else:** Can end with `else` (catches everything not matched) or end with `elif` (nothing happens if all false). `else` is fallback but not required. If no conditions match and no `else`, execution continues after the chain.

4. **Mutually exclusive:** Only one branch executes, even if multiple conditions could be true. This is different from separate `if` statements (each tested independently). Use `elif` when conditions are alternatives; use separate `if`s when conditions are independent.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound conjunction (else + if)
- **Action vs State:** CONDITIONAL - tests alternative condition
- **Temporal aspect:** Conditional - depends on previous failure

### Recommended Form

**Primary recommendation:** Use compound form combining "else" and "if" translations. This should express "otherwise, if (alternative condition)." May use underscore, compound word, or space depending on language conventions.

**Forms to AVOID:**

- ❌ Using completely new word unrelated to "else" + "if"
- ❌ Using only "if" without "else" component
- ❌ Creating confusing compound that doesn't parse as "else if"

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (in Python context)

**"Elif" is unambiguous:**

"Elif" is Python-specific keyword with no other meanings. It's a contraction of "else if" created for Python. Always means: test alternative condition if previous conditions were false.

Note: Some languages use "elsif" (Perl, Ruby) or "elseif" (PHP) - slightly different spellings but same concept.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `elif`, check these translations:**

- [ ] `if` - Primary condition; elif builds on it
- [ ] `else` - Final fallback; elif combines this with if
- [ ] Logical operators (`and`, `or`) - Used in compound conditions

**Consistency rule:**

`elif` should be recognizable compound of `else` + `if` translations. If translating `else` as "sino" and `if` as "si", then `elif` should be something like "si_no_si" or "sino_si". Keep the relationship clear.


### Functional relationships

**This term works WITH:**

1. **if-elif-else chain**:

```python
if condition1:
    action1()
elif condition2:
    action2()
else:
    action3()
```

2. **Multiple elif branches**:

```python
if condition1:
    action1()
elif condition2:
    action2()
elif condition3:
    action3()
elif condition4:
    action4()
```

**Common pairing:**

```python
# Simple if-elif-else
x = 10
if x < 0:
    print("Negative")
elif x == 0:
    print("Zero")
else:
    print("Positive")

# Multiple elif for categorization
age = 25
if age < 13:
    category = "child"
elif age < 18:
    category = "teenager"
elif age < 65:
    category = "adult"
else:
    category = "senior"

# Grade calculation
score = 87
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

# elif with complex conditions
if user.is_admin and user.is_active:
    grant_full_access()
elif user.is_moderator and user.is_active:
    grant_moderate_access()
elif user.is_active:
    grant_basic_access()
else:
    deny_access()

# elif without final else
value = 15
if value > 100:
    category = "high"
elif value > 50:
    category = "medium"
elif value > 10:
    category = "low"
# If none match, category undefined

# elif with continue/break
for item in items:
    if item.is_invalid():
        continue
    elif item.is_complete():
        break
    elif item.needs_processing():
        process(item)

# Nested if-elif
if outer_condition:
    if inner_condition:
        action1()
    elif another_inner:
        action2()
elif other_outer:
    action3()
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (else + if)
- Simple compound of existing keywords
- Universal pattern in programming
- **AI confidence should be HIGH**

### Why EASY for `elif`

- Compound of two simple concepts (else + if)
- Both components have clear translations
- Universal conditional pattern
- Logical composition

**For this term:** EASY

**Rationale:** Since `elif` is simply "else" + "if," translation is straightforward: combine the translations of those two keywords. The concept (alternative condition after previous failure) is universal in programming. Most languages with similar feature use "else if" or variants.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ALTERNATIVE CONDITION concept?
- [ ] Recognizable as "else" + "if" compound?
- [ ] Distinct from plain `if` and plain `else`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound conditional)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Combines `else` and `if` translations logically?
- [ ] Works in if-elif-else chains naturally?
- [ ] Clear relationship to `if` and `else`?

### 4. Usability

- [ ] Short enough (1-2 words, possibly connected)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (obvious compound)?

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
term: elif
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
