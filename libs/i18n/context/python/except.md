# Python Keyword: `except` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** exception_handling (error catching)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `except` keyword catches and handles exceptions raised in a `try` block. Specifies which exception types to catch and what code to execute when they occur. Allows programs to recover from errors gracefully instead of crashing.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic exception handling
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
    result = 0
```

**What this does:** `except` catches specific exception type (ZeroDivisionError) from `try` block. When error occurs, `except` block executes instead of crash. Provides error recovery code.

### Example 2: Common Pattern

```python
# Multiple except clauses
try:
    value = int(input("Enter number: "))
    result = 100 / value
except ValueError:
    print("Invalid number format")
except ZeroDivisionError:
    print("Cannot divide by zero")

# Binding exception to variable
try:
    risky_operation()
except Exception as e:
    print(f"Error occurred: {e}")
    log_error(e)

# Multiple exception types in one clause
except (ValueError, TypeError, KeyError) as e:
    handle_error(e)
```

**What this does:** Can have multiple `except` blocks for different error types. `except Exception as e` binds exception object to variable `e` for inspection. Can catch multiple exception types in one `except` using tuple.

### Example 3: Edge Case

```python
# Bare except (catches everything - not recommended)
try:
    operation()
except:
    print("Something went wrong")  # Dangerous - catches even KeyboardInterrupt

# Except with else
try:
    data = load_file()
except FileNotFoundError:
    data = None
else:
    # Runs only if no exception
    process(data)

# Exception hierarchy (order matters)
try:
    operation()
except ValueError:  # More specific first
    handle_value_error()
except Exception:   # More general last
    handle_generic_error()
```

**What this shows:** Bare `except:` catches all exceptions (dangerous - even catches Ctrl+C). `except` works with `else` clause (runs if no exception). Order matters - specific exceptions before general ones (first match wins).

---

## Pattern Classification

**This term is:** EXCEPTION HANDLING KEYWORD (Error Catching)

**Similar terms in this pattern:**

1. `try` - Begins protected code block (paired with except)
2. `finally` - Cleanup code after try-except
3. `raise` - Throws exceptions that except catches
4. `as` - Binds exception to variable

**Pattern rule:** Exception catching keywords should express exclusion or interception. "Except" means "excluding/catching this case." Handles specific error conditions.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "exceptus" (past participle of "excipere" - to take out, exclude) from "ex-" (out) + "capere" (to take). Through Old French "excepter" to English "except" - meaning to exclude, leave out, or make an exception for. In programming, adapted to mean "catch/handle this exceptional case."

**Why Python uses this:** "Except" naturally expresses handling exceptional cases - errors that are "taken out" of normal flow. Reading "except ValueError" as "except for ValueError (handle it specially)" is intuitive. Alternative terms like "catch" (Java/C++) possible, but Python chose "except" to parallel try-except with if-else structure.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `except` keyword defines exception handler blocks. When exception is raised in `try` block, Python searches `except` clauses top-to-bottom for matching exception type. First matching `except` executes; others are skipped. If no match, exception propagates to caller.

Exception matching: Python checks if raised exception is instance of (or subclass of) the exception type in `except` clause. `except ValueError` catches ValueError and its subclasses. `except Exception` catches most exceptions (Exception is base class for most errors).

`except` enables: specific error responses (different handlers for different errors), error recovery (fix problem and continue), error logging (record error details), graceful degradation (provide fallback when operation fails).

**Key behaviors:**

1. **Type matching:** `except ExceptionType` catches that type and subclasses. Exception hierarchy matters - `ValueError` is subclass of `Exception`, so `except Exception` catches ValueError. Order matters - place specific exceptions before general ones.

2. **First match wins:** Multiple `except` blocks evaluated sequentially. First matching type handles the exception. Remaining `except` blocks skipped. Like elif in conditionals - mutually exclusive.

3. **Binding with as:** `except Exception as e` binds exception object to name `e`. Can access error message (`str(e)`), exception type (`type(e)`), traceback, etc. Variable `e` scoped to `except` block only.

4. **Bare except danger:** `except:` without type catches ALL exceptions, including KeyboardInterrupt (Ctrl+C) and SystemExit. Almost always wrong - prevents graceful shutdown. Use `except Exception` if you need broad catch (excludes system-exiting exceptions).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Preposition/conjunction (expressing exception/exclusion)
- **Action vs State:** CONDITIONAL HANDLING - catches specific cases
- **Temporal aspect:** Reactive - responds to exceptions

### Recommended Form

**Primary recommendation:** Use the target language's word for "except" or "excluding" - expressing exception from a general rule. Should convey "in this exceptional case, do this."

**Forms to AVOID:**

- ❌ Using "catch" (Java/C++ term - Python uses "except")
- ❌ Using "when" (too general - need exception-specific)
- ❌ Using "if error" (verbose - should be single keyword)

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Everyone except John" (exclusion from group)
- ✅ Meaning 2: **HANDLE THIS EXCEPTION** (catch error type, execute handler)
- ❌ Meaning 3: "I can't, except if you insist" (unless)

**Example:**

English "except" can mean:

1. "All except one" (exclusion) ✅ Related concept
2. "except ValueError:" (catch this error type) ✅ **This is the Python meaning**
3. "Except if conditions change" (unless/but if) ❌

**Your translation should capture meanings #1 and #2: excluding from general case or handling exceptional (error) case.**

Use the word for "except/excluding" - expressing exception from normal flow, specifically for error handling.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `except`, check these translations:**

- [ ] `try` - Paired; try-except work together
- [ ] `raise` - Throws exceptions that except catches
- [ ] `as` - Binds exception to variable
- [ ] `finally` - Cleanup after try-except
- [ ] `else` - Success path (no exception)
- [ ] `except*` - 3.11 exception-groups form; rendered as this translation plus untranslated `*`, byte-identical base

**Consistency rule:**

`try`-`except` form the core error handling pair. Must work together grammatically. `except ExceptionType as var:` should read naturally in target language.


### Functional relationships

**This term works WITH:**

1. **Basic try-except**:

```python
try:
    code()
except Exception:
    handle()
```

2. **Except with binding**:

```python
try:
    code()
except Exception as e:
    handle(e)
```

**Common pairing:**

```python
# Single except clause
try:
    result = int(input())
except ValueError:
    print("Invalid number")

# Multiple except clauses
try:
    operation()
except FileNotFoundError:
    print("File not found")
except PermissionError:
    print("Permission denied")
except Exception:
    print("Other error")

# Except with binding
try:
    risky_operation()
except Exception as e:
    log_error(e)
    print(f"Error: {e}")

# Multiple exception types
try:
    process_data(data)
except (ValueError, TypeError, KeyError) as e:
    print(f"Data error: {e}")

# Specific before general
try:
    convert_and_process()
except ValueError:
    handle_value_error()
except TypeError:
    handle_type_error()
except Exception:
    handle_generic_error()

# Except with else
try:
    data = load_data()
except FileNotFoundError:
    data = default_data
else:
    # Runs only if no exception
    validate_data(data)

# Re-raising exceptions
try:
    operation()
except Exception as e:
    log_error(e)
    raise  # Re-raise same exception

# Exception hierarchy
try:
    operation()
except OSError:  # Parent class
    handle_os_error()
# FileNotFoundError is subclass of OSError
# Would be caught by except OSError above

# Bare except (not recommended)
try:
    plugin_code()
except:  # Catches everything, even Ctrl+C - dangerous!
    print("Plugin failed")

# Better: except Exception
try:
    plugin_code()
except Exception:  # Catches errors, not system exits
    print("Plugin failed")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (catch exceptions)
- Universal "except/excluding" word
- Standard error handling pattern
- **AI confidence should be HIGH**

### Why EASY for `except`

- Universal concept (exception handling)
- "Except" or "excluding" exists in most languages
- Standard programming pattern worldwide
- Clear semantic mapping

**For this term:** EASY

**Rationale:** Every language has a word for "except" or "excluding" - making exception from general rule. Exception handling is universal in programming. Translation is straightforward: use the language's word for except/excluding.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures EXCEPTION HANDLING concept?
- [ ] Conveys catching/handling errors?
- [ ] Distinguished from regular conditionals (if)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (preposition/conjunction)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works with `try` naturally?
- [ ] Works with `as` for exception binding?
- [ ] Forms cohesive error handling vocabulary?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word)?

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
term: except
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
