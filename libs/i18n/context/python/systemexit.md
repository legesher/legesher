# Python Builtin: `SystemExit` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class (control-flow signal)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`SystemExit` is the exception raised by `sys.exit()` to request a clean interpreter shutdown. It is a control-flow signal, not a failure: it inherits directly from `BaseException` (not `Exception`) so that ordinary `except Exception` handlers do not accidentally swallow it, and it carries the requested exit status in its `.code` attribute.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# sys.exit() raises SystemExit to request a clean shutdown
import sys

print("Work finished, shutting down")
sys.exit(0)  # Raises SystemExit(0) - exit status 0 means success
print("Never reached")
```

**What this does:** `sys.exit(0)` does not stop the interpreter by force. It raises a `SystemExit` exception that propagates upward like any other exception; when it reaches the top of the program unhandled, the interpreter exits with status 0 and prints no traceback. Code after the call never runs.

### Example 2: Common Pattern

```python
# Command-line tool: exit statuses signal outcomes to the shell
import sys

def main(args):
    if not args:
        print("usage: tool FILE", file=sys.stderr)
        sys.exit(2)  # Conventional "bad usage" exit status
    print(f"processing {args[0]}")

# Test harnesses catch SystemExit to inspect the requested status
try:
    main([])
except SystemExit as e:
    print(f"exit status requested: {e.code}")  # exit status requested: 2
```

**What this does:** Command-line programs call `sys.exit(status)` to communicate success (0) or failure categories (non-zero) to the calling shell. Because the shutdown travels as an exception, a test harness can catch `SystemExit` and read `e.code` to verify which status the program requested, without the test process actually terminating.

### Example 3: Edge Case

```python
# SystemExit is NOT caught by "except Exception"
import sys

try:
    sys.exit(1)
except Exception:
    print("Never reached - SystemExit does not inherit from Exception")

# A non-integer code is printed to stderr; the exit status becomes 1
try:
    sys.exit("fatal: configuration file missing")
except SystemExit as e:
    print(e.code)  # fatal: configuration file missing

# You can raise it directly, without importing sys
raise SystemExit(0)  # Equivalent to sys.exit(0)
```

**What this shows:** `SystemExit` inherits from `BaseException`, deliberately outside the `Exception` branch, so blanket `except Exception` handlers let shutdown requests pass through. The `.code` attribute holds whatever was passed: `None` means status 0, an integer becomes the exit status, and any other object is printed to `stderr` with exit status 1. `raise SystemExit(...)` is the exception-level equivalent of `sys.exit(...)`.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (control-flow signal, not a failure)

**Similar terms in this pattern:**

1. `KeyboardInterrupt` - The other `BaseException` control-flow signal (user pressed Ctrl-C)
2. `StopIteration` - Signals iterator exhaustion, another non-failure exception
3. `BaseException` - Direct parent class; root of the exception hierarchy
4. `GeneratorExit` - Signals generator cleanup, also inherits from `BaseException`

**Pattern rule:** Python deliberately names control-flow signals WITHOUT the word "Error" (`SystemExit`, `KeyboardInterrupt`, `StopIteration`, `GeneratorExit`). Translations must preserve this distinction: use a compound noun naming the event, and do NOT add the target language's word for "error" or "failure."


---

## Etymology (Brief)

**English Origin:** Compound word (Greek-derived + Latin-derived)

**Root meaning:** "System" comes from Greek "systema" meaning "an organized whole, composition." Here it refers to the running interpreter/process. "Exit" comes from Latin "exitus" meaning "a going out, departure" (from "exire," to go out).

**Why Python uses this:** The name describes the event, not a problem: the system (the interpreter process) is exiting. Unlike `KeyError` or `TypeError`, there is deliberately no "Error" in the name, because a program ending on request is normal behavior. Modeling shutdown as an exception lets `finally` blocks and context managers run their cleanup before the process ends.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`SystemExit` is how Python turns "please stop this program" into an object that flows through the normal exception machinery. When code calls `sys.exit(status)` (or the interactive helpers `exit()`/`quit()`, or `raise SystemExit(status)` directly), Python raises a `SystemExit` instance. It propagates outward through every enclosing frame, running `finally` clauses and closing context managers on the way. If nothing catches it, the interpreter terminates with the requested exit status - and, uniquely among unhandled exceptions, prints no traceback, because nothing went wrong.

Its position in the class hierarchy is the important design decision: `SystemExit` inherits directly from `BaseException`, not from `Exception`. Almost all real errors live under `Exception`, so the idiomatic handler `except Exception:` catches genuine failures while letting shutdown requests pass through. Code that writes `except BaseException:` or a bare `except:` will intercept `SystemExit` and can accidentally prevent a program from ever exiting - a classic bug this hierarchy exists to avoid.

The `.code` attribute carries the argument given to `sys.exit()`. By Unix convention, `0` (or `None`) means success and non-zero values encode failure categories for the calling shell or process supervisor. Passing a string is a shorthand: the string is printed to `stderr` and the process exits with status 1. Note that `sys.exit()` is cooperative - cleanup runs and callers may catch it - unlike `os._exit()`, which terminates immediately with no cleanup at all.

**Key behaviors:**

1. **Raised by `sys.exit()`, catchable like any exception:** `sys.exit()` only raises `SystemExit`; it does not force termination. Any enclosing `try` can catch it (useful in test harnesses and application servers), and `finally` blocks always run as it propagates.

2. **Bypasses `except Exception`:** Because it subclasses `BaseException` directly, `except Exception:` does not catch it. Only `except SystemExit:`, `except BaseException:`, or a bare `except:` will - and the latter two are discouraged precisely because they trap shutdown signals.

3. **`.code` determines the exit status:** `None` exits with status 0, an integer exits with that status, and any other object is printed to `stderr` followed by exit status 1. When unhandled, `SystemExit` produces no traceback, signaling to the user that the termination was intentional.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (agent/system + departure event)
- **Action vs State:** EVENT - names a deliberate shutdown event, not an error condition and not a command
- **Temporal aspect:** Instantaneous - the moment shutdown is requested

### Recommended Form

**Primary recommendation:** Use a compound noun meaning "system exit" or "program exit" built from your language's neutral word for departing/leaving. It must read as an event name, matching Python's convention (PascalCase in English) - and it must NOT contain the word your language uses for "error" in `TypeError`/`ValueError` translations.

**Forms to AVOID:**

- ❌ Adding the "error" word ("ErrorDeSalida") - `SystemExit` is not an error; Python deliberately omits "Error" from the name
- ❌ Words implying crash, failure, or abort ("FalloDelSistema", "AbortoDelSistema") - this is a clean, requested shutdown
- ❌ Verb forms ("SalirDelSistema" - "to exit the system") - exception classes are nouns, not commands; the verb form belongs to `sys.exit()`, not to the exception name

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A physical exit (the exit door of a building)
- ❌ Meaning 2: Failure/abort ("the process died") - `SystemExit` is NOT a failure
- ❌ Meaning 3: "System" as the operating system or "the establishment" broadly
- ✅ Meaning 4: **REQUESTED CLEAN TERMINATION of the running program** (a control-flow event)

**Example:**

English "exit" can mean:

1. "Use the emergency exit" (physical door) ❌
2. "The app crashed and exited" (failure) ❌ - wrong connotation for this term
3. "Exit the highway" (leave a route) ❌
4. `sys.exit(0)` - the program asks to end cleanly ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a deliberate, orderly departure of the running program - and "system" means the interpreter process, not the operating system. This is the single most important point for this term: choose words that imply an intentional shutdown, never a malfunction.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `SystemExit`, check these translations:**

- [ ] `KeyboardInterrupt` - The sibling `BaseException` signal; both must read as events, not errors
- [ ] `BaseException` - Direct parent class; hierarchy vocabulary must match
- [ ] `Exception` - The branch `SystemExit` deliberately does NOT belong to
- [ ] `StopIteration` - Another non-error signal; same "no error word" convention
- [ ] `raise` - The keyword used in `raise SystemExit(...)`

**Consistency rule:**

Keep two naming families visibly distinct: failure exceptions carry the "error" word (`TypeError` → "ErrorDeTipo"), control-flow signals do not (`SystemExit` → "SalidaDelSistema", `KeyboardInterrupt` → "InterrupciónDeTeclado"). If your `SystemExit` translation contains the error word but `KeyboardInterrupt` does not, the hierarchy's design becomes invisible to learners.


### Functional relationships

**This term works WITH:**

1. **`sys.exit()` + `SystemExit`**: The function raises the exception; they are two faces of one mechanism

```python
import sys
sys.exit(3)  # Internally: raise SystemExit(3)
```

2. **`try`/`finally` + `SystemExit`**: Cleanup runs while the shutdown request propagates

```python
try:
    sys.exit(0)
finally:
    print("cleanup still runs")  # Always executes before the process ends
```

**Common pairing:**

```python
import sys

# Requesting shutdown with a status code
def main():
    if not validate_config():
        sys.exit(1)  # Non-zero: tell the shell something failed
    run()
    sys.exit(0)      # Zero: success

# Catching SystemExit (test harness / supervisor pattern)
try:
    main()
except SystemExit as e:
    print(f"program requested exit status {e.code}")

# The hierarchy in action
try:
    sys.exit(1)
except Exception:
    print("not reached")          # SystemExit is not an Exception
except SystemExit:
    print("shutdown intercepted")  # This branch runs

# Raising directly, without sys
raise SystemExit("fatal: missing credentials")  # Message to stderr, status 1
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `SystemExit`

- "Exit" and "system" both translate readily in most languages
- The trap is connotation: many candidate words imply failure, crash, or logout
- Must coordinate with the signal-vs-error naming convention across the whole exception set
- "System" must be read as "the running program," not the operating system

**For this term:** MEDIUM

**Rationale:** The component words are easy; the discipline is hard. The translation must name a deliberate shutdown event with zero failure connotation, omit the target language's "error" word, and stay parallel with `KeyboardInterrupt` as the other control-flow signal. Watch for false friends: in several languages the obvious "system exit" phrase colloquially means "logging out of an account," which is the wrong image.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures DELIBERATE CLEAN SHUTDOWN (not crash, not failure, not logout)?
- [ ] Contains NO "error" word - matching Python's deliberate naming?
- [ ] Would a developer understand this is the exception behind `sys.exit()`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun, not verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Visibly different from "Error"-family translations (`TypeError`, `ValueError`)?
- [ ] Parallel in structure to `KeyboardInterrupt` translation (both are signals)?
- [ ] Hierarchy vocabulary aligns with `BaseException` and `Exception`?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: SystemExit
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
**Last Updated:** 2026-07-04
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
