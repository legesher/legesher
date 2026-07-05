# Python Keyword: `raise` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** exception_handling (error throwing)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `raise` keyword throws (raises) an exception, interrupting normal program flow. Can raise new exceptions, re-raise caught exceptions, or chain exceptions. Used to signal errors, validate inputs, or enforce preconditions.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Raise exception
if x < 0:
    raise ValueError("x must be non-negative")

# Raise without message
if not valid:
    raise RuntimeError()
```

**What this does:** `raise` creates and throws an exception. Program execution stops and exception propagates up call stack until caught by `except` or crashes program. Can include error message describing the problem.

### Example 2: Common Pattern

```python
# Input validation
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b

# Re-raise caught exception
try:
    risky_operation()
except Exception:
    log_error()
    raise  # Re-raise same exception

# Raise different exception
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON: {e}") from e
```

**What this does:** Common to `raise` for input validation - check preconditions, raise if invalid. Bare `raise` in `except` block re-raises the caught exception. `raise ... from ...` chains exceptions (shows cause).

### Example 3: Edge Case

```python
# Exception chaining
try:
    operation()
except KeyError as e:
    raise ValueError("Invalid key") from e
# Shows both exceptions in traceback

# Suppress exception context
try:
    operation()
except Exception:
    raise RuntimeError("Failed") from None
# Hides original exception

# Raise without being in except
def validate(value):
    if value < 0:
        raise ValueError("Negative value")
# Can raise anywhere, not just in except
```

**What this shows:** `raise ... from original` chains exceptions - traceback shows both. `raise ... from None` suppresses original exception. Can `raise` anywhere (not just in except blocks) to signal errors.

---

## Pattern Classification

**This term is:** EXCEPTION HANDLING KEYWORD (Error Throwing)

**Similar terms in this pattern:**

1. `except` - Catches exceptions that raise throws
2. `try` - Protects code that might raise
3. `assert` - Raises AssertionError if condition false
4. Exception classes - Objects that raise throws

**Pattern rule:** Exception throwing keywords should use verb forms expressing elevation or signaling. "Raise" means to lift up or bring to attention - bringing error to surface.


---

## Etymology (Brief)

**English Origin:** Old Norse via Middle English

**Root meaning:** Old Norse "reisa" (to raise, erect) through Middle English "raisen." Means to lift up, elevate, or bring to higher position. Metaphorically extended to "raise an issue" or "raise attention" - bringing something to notice. In programming, "raise an exception" means to signal an error condition, bringing it to attention.

**Why Python uses this:** "Raise" naturally expresses bringing error to surface. "Raise an exception" parallels "raise an issue" or "raise a concern" - making problem visible. Alternative terms like "throw" (Java/C++), "throw" emphasizes discarding; "raise" emphasizes elevating to attention. Python chose "raise" for clarity.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `raise` statement creates an exception object and throws it, interrupting normal execution. Program stops at `raise` point and exception propagates up the call stack. If caught by `except`, that handler executes. If never caught, program terminates with traceback.

Three forms of `raise`:

1. `raise ExceptionType("message")` - Create and throw new exception
2. `raise` (bare) - Re-raise currently handled exception (only in except block)
3. `raise NewException(...) from original` - Chain exceptions (show causation)

Raising enables: input validation (reject invalid data), precondition enforcement (require state before operation), error signaling (notify caller of failure), assertion failures (assert conditions during development).

**Key behaviors:**

1. **Creates exception object:** `raise ValueError("msg")` creates ValueError instance with message. Exception types are classes - raising instantiates and throws them. Can raise any class inheriting from BaseException (usually Exception subclass).

2. **Interrupts execution:** Immediately stops current function. Doesn't return - propagates exception up call stack. Remaining code in function doesn't execute. Like early return but for errors.

3. **Bare raise (re-raise):** `raise` without arguments re-raises currently handled exception. Only valid in `except` block. Common pattern: catch exception, log it, then re-raise for caller to handle. Preserves exception info and traceback.

4. **Exception chaining:** `raise NewException() from original` chains exceptions. Traceback shows both exceptions and their relationship. `from None` suppresses context (hides original exception - use sparingly). Chaining clarifies causation.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (imperative - command to raise exception)
- **Action vs State:** ACTION - command to throw error
- **Temporal aspect:** Instantaneous - immediate exception throwing

### Recommended Form

**Primary recommendation:** Use verb form meaning "to raise" or "to lift up" (imperative or infinitive). Should convey elevating or bringing to attention. Express signaling error or bringing problem to surface.

**Forms to AVOID:**

- ❌ Using "throw" (Java/C++ term - Python uses "raise")
- ❌ Using noun "exception" instead of verb "raise"
- ❌ Using "create" (too general - need "raise" specifically)

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Raise your hand" (physical elevation)
- ❌ Meaning 2: "Raise children" (bring up/rear)
- ❌ Meaning 3: "Raise awareness" (increase)
- ✅ Meaning 4: **RAISE AN EXCEPTION/ISSUE** (signal error, bring to attention)

**Example:**

English "raise" can mean:

1. "Raise the flag" (physical lift) ❌ Related metaphor
2. "Raise kids" (bring up) ❌
3. "Raise money" (collect) ❌
4. "raise ValueError" (signal exception) ✅ **This is the Python meaning**
5. "Raise an issue" (bring to attention) ✅ Related concept

**Your translation should capture meanings #4 and #5: signaling an error or bringing a problem to attention (the "raise an issue" sense).**

Use the verb for raising/elevating, especially in context of raising issues or concerns.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `raise`, check these translations:**

- [ ] `try` - Protects code that might raise
- [ ] `except` - Catches exceptions that raise throws
- [ ] `assert` - Raises AssertionError; related concept
- [ ] Exception class names (ValueError, TypeError, etc.)

**Consistency rule:**

`raise` should be recognizable as exception-throwing keyword. Works with exception class names. Forms natural phrases like "raise ValueError" in target language.


### Functional relationships

**This term works WITH:**

1. **Raise with exception type**:

```python
raise ValueError("Invalid input")
```

2. **Bare raise (re-raise)**:

```python
try:
    operation()
except Exception:
    log()
    raise
```

**Common pairing:**

```python
# Basic raise
def validate(x):
    if x < 0:
        raise ValueError("x must be non-negative")

# Raise with formatted message
if len(password) < 8:
    raise ValueError(f"Password too short: {len(password)} chars")

# Raise without message
if not condition:
    raise RuntimeError()

# Re-raise in except
try:
    risky_operation()
except Exception as e:
    log_error(e)
    raise  # Re-raise same exception

# Raise different exception
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON: {e}")

# Exception chaining (from)
try:
    process_data()
except KeyError as e:
    raise ValueError("Missing required field") from e
# Traceback shows both exceptions

# Suppress exception context
try:
    operation()
except Exception:
    raise CustomError("Operation failed") from None
# Hides original exception

# Raise in validation
def divide(a, b):
    if not isinstance(a, (int, float)):
        raise TypeError(f"a must be number, got {type(a)}")
    if not isinstance(b, (int, float)):
        raise TypeError(f"b must be number, got {type(b)}")
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b

# Raise with custom exception
class ValidationError(Exception):
    pass

if not is_valid(data):
    raise ValidationError("Data validation failed")

# Conditional raise
result = compute()
if result is None:
    raise RuntimeError("Computation returned None")

# Raise in assert alternative
if __debug__:
    if not condition:
        raise AssertionError("Condition must be true")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (throw exception)
- Universal "raise" or "throw" verb
- Standard error handling pattern
- **AI confidence should be HIGH**

### Why EASY for `raise`

- Universal concept (signaling errors)
- "Raise" or "throw" verb exists in most languages
- Standard exception handling worldwide
- Clear semantic mapping

**For this term:** EASY

**Rationale:** Every language has verbs for "raise," "lift," or "throw" - elevating or throwing something. Exception throwing is universal in programming. Translation is straightforward: use the language's verb for raising/lifting/throwing, preferably matching "raise" metaphor.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures EXCEPTION THROWING concept?
- [ ] Conveys signaling error or bringing to attention?
- [ ] Distinguished from catching exceptions?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb - imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works with exception class names naturally?
- [ ] Compatible with try-except error handling?
- [ ] Distinct from `except` (catch) and `try` (attempt)?

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
term: raise
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
