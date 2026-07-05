# Python Keyword: `assert` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** debugging (assertion statement)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `assert` keyword tests a condition and raises `AssertionError` if the condition is false. Used for debugging and development - checking assumptions and invariants. Assertions can be disabled globally with Python's `-O` (optimize) flag, so they're for internal checks, not input validation.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic assertion
x = 5
assert x > 0  # Passes - no error

y = -1
assert y > 0  # Fails - raises AssertionError
```

**What this does:** `assert condition` checks if condition is true. If false, raises `AssertionError` and crashes. If true, execution continues normally. Simple way to check assumptions.

### Example 2: Common Pattern

```python
# Assert with message
def divide(a, b):
    assert b != 0, "Divisor cannot be zero"
    return a / b

# Multiple assertions
def process(data):
    assert isinstance(data, list), "data must be list"
    assert len(data) > 0, "data cannot be empty"
    assert all(isinstance(x, int) for x in data), "all items must be int"
    return sum(data)

# Assert for type checking (development)
def calculate(x: float) -> float:
    assert isinstance(x, float), f"Expected float, got {type(x)}"
    result = x * 2
    assert result >= 0, "Result should be non-negative"
    return result
```

**What this does:** `assert condition, message` provides error description. Common to assert preconditions (input requirements), postconditions (result requirements), and invariants (conditions that should always hold). Helps catch bugs during development.

### Example 3: Edge Case

```python
# Assertions can be disabled
# python -O script.py  # Disables all asserts
assert expensive_check(), "This might not run in production"

# Assert vs raise for validation
# For internal checks (developers):
assert len(data) > 0, "Internal: data should not be empty"

# For input validation (users):
if len(data) == 0:
    raise ValueError("User input cannot be empty")

# Assert on type (runtime check)
x: int = calculate()
assert isinstance(x, int), f"calculate() should return int, got {type(x)}"

# Assertion always True (useless)
assert True  # Always passes - no point
assert 1 == 1  # Always passes - debugging/testing only
```

**What this shows:** Assertions disabled with `-O` flag (optimization mode). Use `assert` for internal checks (developer errors), `raise` for user input validation (user errors). Assertions verify assumptions during development but can be turned off in production for performance.

---

## Pattern Classification

**This term is:** DEBUGGING KEYWORD (Assertion Statement)

**Similar terms in this pattern:**

1. `raise` - Throws exceptions (assert raises AssertionError)
2. `if` + `raise` - Alternative to assert for user validation
3. `__debug__` - Global constant controlling assertions

**Pattern rule:** Debugging keywords should express verification or confirmation. "Assert" means to state confidently - declaring something must be true.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "asserere" (to claim, affirm) from "ad-" (to) + "serere" (to join). Through Old French "asserter" to English "assert" - meaning to state confidently, declare positively, maintain as true. In programming, "assert" means to declare that a condition must be true.

**Why Python uses this:** "Assert" naturally expresses declaring something must be true. "Assert that x > 0" reads as "I claim x is greater than 0." Common in programming - C, Java, JavaScript all use "assert" for similar purpose. Borrowed from logic/mathematics where assertions declare truths.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `assert` statement checks a condition. If true, nothing happens (execution continues). If false, raises `AssertionError` with optional message. Equivalent to:

```python
if not condition:
    raise AssertionError(message)
```

But `assert` is cleaner and can be globally disabled. Running Python with `-O` (optimize) flag sets `__debug__` to False and removes all `assert` statements from bytecode (as if they don't exist).

Use assertions for: developer errors (internal logic bugs), preconditions (requirements before function runs), postconditions (requirements after function runs), invariants (conditions that should always hold), type checking in development.

**Don't use assertions for:** user input validation (can be disabled), error handling (use try-except), production checks (can be disabled), security checks (can be disabled).

**Key behaviors:**

1. **Raises AssertionError:** If condition false, `assert` raises `AssertionError`. This is exception like any other - can be caught with `except AssertionError` (though usually shouldn't). Message becomes exception's string.

2. **Can be disabled:** `python -O script.py` runs in optimize mode, removing all asserts. Code runs as if asserts don't exist. This means assertions unsuitable for essential checks - they might not run in production.

3. **Short-circuit evaluation:** `assert` uses short-circuit logic. `assert x and y, "msg"` only evaluates `y` if `x` is true. `assert condition, expensive_message()` only calls `expensive_message()` if assertion fails.

4. **Development tool:** Assertions are for catching bugs during development, not handling user errors. Use `raise` for actual error handling. Think: assertions check developer's assumptions; raises handle user's mistakes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (imperative - command to assert/affirm)
- **Action vs State:** ACTION - command to verify condition
- **Temporal aspect:** Instantaneous - immediate check

### Recommended Form

**Primary recommendation:** Use verb form meaning "to assert," "to affirm," or "to claim" (imperative or infinitive). Should convey declaring something as true or verifying a condition.

**Forms to AVOID:**

- ❌ Using "check" (too passive - assert is active declaration)
- ❌ Using "verify" when "assert" more standard
- ❌ Using noun "assertion" instead of verb "assert"

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Assert dominance" (establish authority)
- ❌ Meaning 2: "Assert rights" (claim entitlement)
- ✅ Meaning 3: **DECLARE CONDITION MUST BE TRUE** (verify assumption, raise error if false)

**Example:**

English "assert" can mean:

1. "Assert dominance" (establish authority) ❌
2. "Assert your rights" (claim) ❌
3. "assert x > 0" (declare must be true, verify) ✅ **This is the Python meaning**
4. "Make an assertion" (state confidently) ✅ Related concept

**Your translation should capture meaning #3 and #4: declaring a condition must be true and verifying it, stating something confidently.**

Use the verb for asserting/affirming - declaring truth and verifying it.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `assert`, check these translations:**

- [ ] `raise` - Assert raises AssertionError when fails
- [ ] `True`/`False` - Conditions that assert checks
- [ ] `if` - Alternative to assert for user validation
- [ ] `__debug__` - Controls whether asserts run

**Consistency rule:**

`assert` should be recognizable as debugging/verification keyword. Works with boolean conditions. Forms natural phrases like "assert x > 0" in target language.


### Functional relationships

**This term works WITH:**

1. **Basic assert**:

```python
assert condition
```

2. **Assert with message**:

```python
assert condition, "Error message"
```

**Common pairing:**

```python
# Basic assertion
x = 10
assert x > 0

# Assert with message
def divide(a, b):
    assert b != 0, "Cannot divide by zero"
    return a / b

# Multiple assertions (preconditions)
def process(data):
    assert isinstance(data, list), "data must be list"
    assert len(data) > 0, "data must not be empty"
    assert all(isinstance(x, int) for x in data), "items must be int"

# Assert postcondition
def calculate(x):
    result = complex_calculation(x)
    assert result >= 0, "Result should be non-negative"
    return result

# Assert invariant
class BankAccount:
    def withdraw(self, amount):
        old_balance = self.balance
        self.balance -= amount
        assert self.balance == old_balance - amount, "Balance invariant"

# Assert type checking
def add(x: int, y: int) -> int:
    assert isinstance(x, int), f"x must be int, got {type(x)}"
    assert isinstance(y, int), f"y must be int, got {type(y)}"
    result = x + y
    assert isinstance(result, int), "result must be int"
    return result

# Assert vs raise (internal vs external)
# Internal check (developer error):
assert len(cache) <= MAX_SIZE, "Cache size invariant violated"

# External validation (user error):
if len(user_input) == 0:
    raise ValueError("Input cannot be empty")

# Assert with complex condition
assert (
    user.is_authenticated and
    user.has_permission('write') and
    not user.is_banned
), "User must be authenticated, have write permission, and not be banned"

# Assert in tests
def test_addition():
    result = add(2, 3)
    assert result == 5, f"Expected 5, got {result}"

# Assert disabled in production
# python -O runs without asserts
assert validate_internal_state(), "Debug check"
# In production (-O), this line effectively doesn't exist
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (verify condition)
- Universal "assert/affirm" verb
- Standard debugging pattern
- **AI confidence should be HIGH**

### Why EASY for `assert`

- Universal concept (declaring truth)
- "Assert" or "affirm" verb exists in most languages
- Standard debugging tool in programming
- Clear semantic mapping

**For this term:** EASY

**Rationale:** Every language has verbs for "assert," "affirm," or "claim" - stating something confidently as true. Assertions are universal in programming for debugging. Translation is straightforward: use the language's verb for asserting/affirming/claiming.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ASSERTION/VERIFICATION concept?
- [ ] Conveys declaring condition must be true?
- [ ] Distinguished from user input validation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb - imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works with boolean conditions naturally?
- [ ] Compatible with debugging/testing context?
- [ ] Distinct from `raise` (though related)?

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
term: assert
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
