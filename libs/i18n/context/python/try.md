# Python Keyword: `try` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** exception_handling (error handling)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `try` keyword begins an exception handling block where risky code is executed. If an exception occurs in the `try` block, execution jumps to the appropriate `except` block. Used with `except`, `else`, and `finally` for comprehensive error handling.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic try-except
try:
    result = 10 / 0  # Raises ZeroDivisionError
except ZeroDivisionError:
    print("Cannot divide by zero")
# Output: Cannot divide by zero
```

**What this does:** `try` marks code that might raise exceptions. If error occurs, Python jumps to matching `except` block. Program continues instead of crashing. Allows graceful error handling.

### Example 2: Common Pattern

```python
# File handling with error recovery
try:
    with open("config.txt") as f:
        config = f.read()
except FileNotFoundError:
    config = get_default_config()

# Multiple exception types
try:
    value = int(user_input)
    result = 100 / value
except ValueError:
    print("Invalid number")
except ZeroDivisionError:
    print("Cannot divide by zero")
```

**What this does:** `try` wraps operations that might fail (file access, type conversion, division). Different `except` blocks handle different error types. Allows specific responses to different failures.

### Example 3: Edge Case

```python
# try-except-else-finally (complete form)
try:
    risky_operation()
except Exception as e:
    handle_error(e)
else:
    # Runs if no exception
    success_action()
finally:
    # Always runs (cleanup)
    cleanup()

# Nested try blocks
try:
    outer_operation()
    try:
        inner_operation()
    except ValueError:
        handle_inner_error()
except Exception:
    handle_outer_error()

# Empty except (not recommended)
try:
    operation()
except:
    pass  # Catches everything - dangerous
```

**What this shows:** `try` can combine with `except`, `else` (runs if no exception), and `finally` (always runs). Can nest `try` blocks for granular error handling. Bare `except:` catches all exceptions (discouraged - hides bugs).

---

## Pattern Classification

**This term is:** EXCEPTION HANDLING KEYWORD (Error Management)

**Similar terms in this pattern:**

1. `except` - Handles exceptions from try block (paired)
2. `finally` - Cleanup code that always runs
3. `else` - Runs if try succeeds (no exception)
4. `raise` - Throws exceptions

**Pattern rule:** Exception handling keywords should express attempting or testing. "Try" means "attempt this, be prepared for failure." Creates protected execution context.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `except` | excepto | إلا | 除了 | सिवाय |
| `finally` | finalmente | أخيرا | 最后 | अंततः |
| `raise` | elevar | ارفع | 引发 | उठाओ |
| `try` | **intentar** | **حاول** | **尝试** | **प्रयास** |

---

## Etymology (Brief)

**English Origin:** Old French via Latin

**Root meaning:** Old French "trier" (to pick out, cull) from Late Latin "tritare" (to grind). Evolved to mean "test, attempt, make an effort." In English, "try" means to attempt something that might fail. In programming, borrowed to mean "attempt execution with possibility of failure."

**Why Python uses this:** "Try" naturally expresses attempting risky operations. "Try this code, if it fails, handle the error" reads like English. Standard across many languages (try-catch in Java/C++, try-except in Python). Alternative terms like "attempt" possible but "try" shorter and established.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `try` statement creates an exception-handling context. Code in the `try` block executes normally unless an exception occurs. If exception is raised, Python immediately stops executing the `try` block and searches for a matching `except` block. If found, the except block handles the error; if not, the exception propagates up.

Exception handling structure:

- `try:` - Protected code that might fail
- `except ExceptionType:` - Handle specific exception (required, at least one)
- `else:` - Runs if try succeeds (optional)
- `finally:` - Cleanup code that always runs (optional)

`try` enables: graceful error recovery (handle errors without crashing), resource cleanup (with finally), specific error responses (different except blocks for different errors), error logging (catch, log, re-raise).

**Key behaviors:**

1. **Exception propagation:** If `try` block raises exception, remaining `try` code skips. Python searches `except` blocks top-to-bottom for matching exception type. First match handles it. If no match, exception propagates to caller.

2. **Must have except:** `try` requires at least one `except` (or `finally`). Can't use `try` alone - must specify what to do with exceptions. Python enforces this syntactically.

3. **Else clause:** Optional `else` block runs if `try` completes without exceptions. Useful for code that should only run on success. Distinguishes success path from exception handling.

4. **Finally guarantee:** Optional `finally` block always executes - whether exception occurred or not, whether exception was handled or not, even if `try`/`except` has `return` statement. Guarantees cleanup.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (imperative - command to attempt)
- **Action vs State:** ACTION - command to attempt execution
- **Temporal aspect:** Initiation - begins protected execution

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb (imperative/infinitive) | "intentar", "essayer", "tentar" - to try/attempt |
| Germanic (de, nl, sv) | Verb (infinitive) | "versuchen", "proberen" - to try/attempt |
| Slavic (ru, pl, uk) | Verb (imperative) | "попробовать", "spróbować" - to try/attempt |
| Arabic | Verb (imperative) | "حاول" - ḥāwil (try/attempt) |
| Chinese | Verb | "尝试" - chángshì (try/attempt) |
| Hindi | Verb/noun | "प्रयास" - prayās (try/attempt) or "कोशिश" - koshish (try) |

**Primary recommendation:** Use verb form meaning "to try" or "to attempt" (imperative or infinitive). Should convey making an effort that might fail. Express testing or attempting with possibility of error.

**Forms to AVOID:**

- ❌ Using "test" when "try" is more natural
- ❌ Using "attempt" (noun) when need verb
- ❌ Using "check" (too passive, need active attempt)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `intentar`
- **Form:** Verb (infinitive)
- **Why it works:** "Intentar" means "to try/attempt" in Spanish. Natural for expressing attempting risky code. Standard verb form. Clear meaning of making effort that might fail.

**Arabic:**

- **Translation:** `حاول` (ḥāwil)
- **Form:** Verb (imperative)
- **Why it works:** "Ḥāwil" means "try/attempt" (imperative command). Natural command to attempt execution. Standard Arabic verb. Used in Arabic programming contexts.

**Chinese:**

- **Translation:** `尝试` (chángshì)
- **Form:** Verb
- **Why it works:** "Chángshì" means "try/attempt." Two characters. Standard Chinese term for attempting. Clear meaning. Universal in Chinese programming.

**Hindi:**

- **Translation:** `प्रयास` (prayās) or `कोशिश` (koshish)
- **Form:** Noun/verb
- **Why it works:** "Prayās" means "attempt/try" (more formal). "Koshish" means "try/effort" (more colloquial). Either acceptable. Both convey attempting with possibility of failure. Used in Hindi programming.

### ❌ Common Translation Mistakes

**Mistake 1: Using "test" instead of "try"**

- **Wrong:** `probar` (Spanish - "to test/prove")
- **Why wrong:** "Test" emphasizes checking/verifying. "Try" emphasizes attempting with possible failure. Different nuance. "Try" is standard programming term. Use "try" not "test."
- **Right:** `intentar` (to try/attempt)

**Mistake 2: Using noun "attempt"**

- **Wrong:** `intento` (Spanish - "attempt" - noun)
- **Why wrong:** Need verb form for keyword, not noun. "Try" is verb (command). Can't replace with noun. Wrong part of speech.
- **Right:** `intentar` (verb - to try)

**Mistake 3: Using "check" (too passive)**

- **Wrong:** `verificar` (Spanish - "to verify/check")
- **Why wrong:** "Check" is passive examination. "Try" is active attempt with risk. "Try" implies execution that might fail, not just checking. Different concepts.
- **Right:** `intentar` (active attempt)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Try on clothes" (test fit)
- ✅ Meaning 2: **ATTEMPT WITH POSSIBLE FAILURE** (execute code, be ready for errors)
- ❌ Meaning 3: "Try in court" (legal trial)
- ❌ Meaning 4: "Give it a try" (casual attempt)

**Example:**

English "try" can mean:

1. "Try on this shirt" (test fit) ❌
2. "try: risky_code()" (attempt execution, handle errors) ✅ **This is the Python meaning**
3. "Try the case" (legal) ❌
4. "Give it a try" (casual attempt) ✅ Related concept

**Your translation should capture meaning #2: attempting to execute code with awareness it might fail and errors must be handled.**

Use the verb for trying/attempting, emphasizing possibility of failure.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `try`, check these translations:**

- [ ] `except` - Paired with try; handles exceptions from try
- [ ] `finally` - Optional; cleanup after try
- [ ] `else` - Optional; success path after try
- [ ] `raise` - Throws exceptions that try catches

**Consistency rule:**

`try`-`except`-`else`-`finally` form a cohesive error handling structure. Translations should work together naturally. All should be recognizable as error handling keywords.

**Example:**

Spanish: `intentar` (try), `excepto` (except), `sino` (else), `finalmente` (finally) - cohesive set ✅

### Functional relationships

**This term works WITH:**

1. **Basic try-except**:

```python
try:
    risky_code()
except Exception:
    handle_error()
```

2. **Complete try-except-else-finally**:

```python
try:
    code()
except Exception:
    handle()
else:
    success()
finally:
    cleanup()
```

**Common pairing:**

```python
# Basic try-except
try:
    result = 10 / x
except ZeroDivisionError:
    result = 0

# Multiple exceptions
try:
    value = int(input())
    result = 100 / value
except ValueError:
    print("Invalid input")
except ZeroDivisionError:
    print("Cannot divide by zero")

# Catch with binding
try:
    risky_operation()
except Exception as e:
    print(f"Error: {e}")
    log_error(e)

# try-else pattern
try:
    data = load_data()
except FileNotFoundError:
    data = None
else:
    # Only runs if no exception
    process_data(data)

# try-finally (cleanup)
try:
    file = open("data.txt")
    process(file)
finally:
    file.close()  # Always runs

# Complete form
try:
    result = compute()
except ValueError as e:
    log_error(e)
    result = default_value
else:
    save_result(result)
finally:
    cleanup()

# Nested try blocks
try:
    connect()
    try:
        transfer_data()
    except NetworkError:
        retry()
except ConnectionError:
    reconnect()

# Re-raising exceptions
try:
    operation()
except Exception as e:
    log_error(e)
    raise  # Re-raise same exception

# Generic exception handler
try:
    plugin.execute()
except Exception:
    print("Plugin failed")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (attempt with error handling)
- Universal verb "try/attempt"
- Standard programming pattern
- **AI confidence should be HIGH**

### Why EASY for `try`

- Universal concept (attempting with possible failure)
- "Try" or "attempt" verb exists in every language
- Standard exception handling across languages
- Clear semantic mapping

**For this term:** EASY

**Rationale:** Every language has a verb meaning "try" or "attempt" - making effort with possibility of failure. Exception handling with try-catch/try-except is universal in modern programming. Translation is straightforward: use the language's verb for trying/attempting.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ATTEMPT WITH ERROR HANDLING concept?
- [ ] Conveys protected execution with possible failure?
- [ ] Distinguished from simple testing or checking?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb - imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works with `except`, `else`, `finally`?
- [ ] Forms cohesive error handling vocabulary?
- [ ] Natural pairing with exception terminology?

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
term: try
language: es
translation: intentar
form: verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "intentar" means "to try/attempt," expressing attempting execution with possible failure. Natural verb form for command. Works in try-except-finally error handling structures. Standard Spanish programming terminology.

**Alternatives considered:**

1. `probar` (to test) - Emphasizes testing over attempting; "try" more accurate
2. `intento` (attempt - noun) - Wrong part of speech; need verb
3. `tratar` (to try) - Also valid; "intentar" more formal and clear

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Try/attempt verbs are universal with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
