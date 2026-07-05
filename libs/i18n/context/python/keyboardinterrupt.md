# Python Builtin: `KeyboardInterrupt` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class (control-flow signal)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`KeyboardInterrupt` is the exception raised when the user interrupts a running program from the keyboard, normally by pressing Ctrl-C (which delivers the SIGINT signal). It is a user action, not a program failure: it inherits directly from `BaseException` (not `Exception`), which is the canonical reason to write `except Exception:` instead of a bare `except:` - so users can always stop your program.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Ctrl-C during input() raises KeyboardInterrupt
try:
    name = input("Your name: ")  # User presses Ctrl-C here
except KeyboardInterrupt:
    print("\nCancelled by user")
```

**What this does:** While the program waits for input, pressing Ctrl-C makes Python raise `KeyboardInterrupt` at that point in the code. Catching it lets the program acknowledge the cancellation and end politely instead of printing a traceback.

### Example 2: Common Pattern

```python
# Graceful shutdown of a long-running loop
import time

try:
    while True:
        process_next_item()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Interrupted - saving progress before exit")
    save_progress()
```

**What this does:** Long-running programs (servers, watchers, batch jobs) conventionally run until the user presses Ctrl-C. Catching `KeyboardInterrupt` at the top level turns the interruption into a clean shutdown: the program saves its state and exits on the user's terms.

### Example 3: Edge Case

```python
# "except Exception" deliberately does NOT catch KeyboardInterrupt
try:
    long_running_task()
except Exception as e:
    print(f"task failed: {e}")
# Ctrl-C still stops the program - the interrupt passes straight through

# A bare "except" is the classic anti-pattern
while True:
    try:
        risky_work()
    except:            # Catches KeyboardInterrupt too!
        continue       # User can never stop this loop with Ctrl-C
```

**What this shows:** `KeyboardInterrupt` inherits from `BaseException`, deliberately outside the `Exception` branch. `except Exception:` handles genuine errors while letting the user's Ctrl-C terminate the program. A bare `except:` swallows the interrupt as well, producing programs that cannot be stopped from the keyboard - the standard textbook example of why bare `except` is dangerous.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (control-flow signal, not a failure)

**Similar terms in this pattern:**

1. `SystemExit` - The other `BaseException` control-flow signal (requested shutdown via `sys.exit()`)
2. `BaseException` - Direct parent class; root of the exception hierarchy
3. `StopIteration` - Another non-failure exception, signaling iterator exhaustion
4. `GeneratorExit` - Signals generator cleanup, also inherits from `BaseException`

**Pattern rule:** Python deliberately names control-flow signals WITHOUT the word "Error" (`KeyboardInterrupt`, `SystemExit`, `StopIteration`). Translations must preserve this: use a compound noun naming the event (keyboard + interruption), and do NOT add the target language's word for "error" or "failure."


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic compound + Latin-derived)

**Root meaning:** "Keyboard" is a Germanic compound: "key" (Old English "cǣg") + "board" (Old English "bord"), the panel of keys. "Interrupt" comes from Latin "interrumpere" meaning "to break apart, break in between" ("inter-" between + "rumpere" to break).

**Why Python uses this:** The name records exactly what happened: the user, at the keyboard, broke into the program's execution. It borrows "interrupt" from hardware/OS vocabulary (Ctrl-C delivers the SIGINT "interrupt" signal), and deliberately omits "Error" - a person choosing to stop a program is not a malfunction.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`KeyboardInterrupt` is Python's representation of "the user asked this program to stop." When the user presses Ctrl-C in a terminal, the operating system delivers the SIGINT signal to the process. Python's default SIGINT handler responds by raising `KeyboardInterrupt` in the main thread, at whatever point the code happens to be executing. From there it behaves like any exception: it propagates outward, running `finally` blocks and closing context managers, until something catches it or the interpreter reports it and terminates.

Its place in the hierarchy is the load-bearing design decision. `KeyboardInterrupt` inherits directly from `BaseException`, not from `Exception`, so the idiomatic handler `except Exception:` does not intercept it. This is the canonical teaching example for exception hygiene: write `except Exception:` (or something narrower), never a bare `except:`, precisely so that Ctrl-C keeps working. A program that traps `KeyboardInterrupt` inside a retry loop becomes unstoppable from the keyboard.

Because the interrupt can arrive between almost any two operations, code that catches it must assume work was cut off mid-step. Well-behaved programs catch it once, near the top level, to save state and exit cleanly. It is also worth knowing that this exception is about the *interrupt signal*, not about typing: ordinary key presses never raise it, and programs receiving SIGINT from other sources (such as `kill -INT`) raise `KeyboardInterrupt` without any keyboard involved.

**Key behaviors:**

1. **Raised by Ctrl-C / SIGINT in the main thread:** The default signal handler converts SIGINT into a `KeyboardInterrupt` raised in the main thread at the current execution point. The program does not need to be reading input - a busy loop or a `sleep()` can be interrupted too.

2. **Bypasses `except Exception`:** As a direct `BaseException` subclass, it passes through `except Exception:` handlers. Only `except KeyboardInterrupt:`, `except BaseException:`, or a bare `except:` catch it - and the last two are discouraged because they block user interruption.

3. **Signals cancellation, not failure:** When unhandled, the interpreter prints a short traceback ending in `KeyboardInterrupt` and terminates. Nothing in the program was wrong; the correct response when catching it is cleanup and exit (or a deliberate cancellation of the current operation), not error recovery or retries.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (source of the interruption + interruption event)
- **Action vs State:** EVENT - names a user-initiated interruption event, not an error condition
- **Temporal aspect:** Instantaneous - the moment the interrupt signal arrives

### Recommended Form

**Primary recommendation:** Use a compound noun meaning "keyboard interruption." Prefer your language's established computing word for "interrupt" (the same root used for hardware/signal interrupts) - it is neutral about blame, which is exactly right. Do NOT include the word used for "error" in `TypeError`/`ValueError` translations.

**Forms to AVOID:**

- ❌ Adding the "error" word ("ErrorDeTeclado" - "keyboard error") - this names a user action, not a malfunction; "keyboard error" also wrongly suggests broken hardware
- ❌ Words implying failure or crash ("FalloDeTeclado") - the user chose to stop the program
- ❌ Verb forms ("InterrumpirTeclado" - "to interrupt keyboard") - exception classes are noun compounds naming events

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Rude conversational interruption (cutting someone off mid-sentence)
- ❌ Meaning 2: A keyboard hardware fault or a stuck key
- ❌ Meaning 3: A hardware IRQ generated by keystrokes in general (typing does not raise this)
- ✅ Meaning 4: **USER-INITIATED CANCELLATION SIGNAL** (Ctrl-C / SIGINT asking the program to stop)

**Example:**

English "interrupt" can mean:

1. "Sorry to interrupt your meeting" (social) ❌
2. "The keyboard is broken" (hardware fault) ❌
3. "Every keystroke triggers an interrupt" (low-level IRQ) ❌ Related lineage, wrong grain
4. User presses Ctrl-C and the program raises `KeyboardInterrupt` ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the user deliberately interrupting program execution from the keyboard. This is a control-flow signal - a person's choice - never a malfunction. Choose words that keep the user's agency and drop any implication that something failed.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `KeyboardInterrupt`, check these translations:**

- [ ] `SystemExit` - The sibling `BaseException` signal; both must read as events, not errors
- [ ] `BaseException` - Direct parent class; hierarchy vocabulary must match
- [ ] `Exception` - The branch this class deliberately does NOT belong to
- [ ] `except` - The keyword in `except KeyboardInterrupt:` must pair naturally
- [ ] `KeyError` - Shares the "key/keyboard" root in some languages; keep the key vocabulary consistent

**Consistency rule:**

Keep the two naming families visibly distinct: failures carry the "error" word (`TypeError` → "ErrorDeTipo"), control-flow signals do not (`KeyboardInterrupt` → "InterrupciónDeTeclado", `SystemExit` → "SalidaDelSistema"). If one signal gains an error word and the other does not, the `BaseException`-vs-`Exception` design becomes invisible in translation.


### Functional relationships

**This term works WITH:**

1. **`try`/`except` + `KeyboardInterrupt`**: Top-level handlers turn Ctrl-C into a graceful shutdown

```python
try:
    run_forever()
except KeyboardInterrupt:
    shutdown_cleanly()
```

2. **`except Exception` + `KeyboardInterrupt`**: The contrast that defines exception hygiene

```python
try:
    work()
except Exception:      # Catches errors...
    recover()          # ...but Ctrl-C still passes through
```

**Common pairing:**

```python
import time

# The canonical long-running-program skeleton
def main():
    print("Running - press Ctrl-C to stop")
    try:
        while True:
            poll_sensors()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping on user request")
        flush_buffers()

# Why "except Exception", not bare "except"
try:
    fragile_operation()
except Exception as e:   # GOOD: real errors handled, Ctrl-C still works
    log(e)

try:
    fragile_operation()
except:                  # BAD: also swallows KeyboardInterrupt and SystemExit
    pass

# Cleanup still runs when interrupted
try:
    while True:
        time.sleep(1)
finally:
    print("finally block runs even on Ctrl-C")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `KeyboardInterrupt`

- "Keyboard" and "interrupt" both have established technical translations in most languages
- The compound can get long where "keyboard" is itself a multi-word phrase
- Must choose the neutral, technical "interrupt" word rather than a social or fault-implying one
- Must coordinate with the signal-vs-error naming convention

**For this term:** MEDIUM

**Rationale:** Most languages already have a hardware/computing word for "interrupt," which is the right choice and keeps the SIGINT lineage. The main risks are connotation (picking a word that implies rudeness or malfunction) and length (in languages where "keyboard" is a phrase, the compound may need abbreviation - handle this deliberately, not by dropping the interruption component).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures USER-INITIATED INTERRUPTION (Ctrl-C), not typing, not hardware faults?
- [ ] Contains NO "error" word - matching Python's deliberate naming?
- [ ] Neutral connotation - no rudeness, no malfunction?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun, not verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Parallel in structure to `SystemExit` translation (both are signals)?
- [ ] Visibly different from "Error"-family translations (`TypeError`, `ValueError`)?
- [ ] "Keyboard/key" vocabulary consistent with `KeyError` translation where roots overlap?

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
term: KeyboardInterrupt
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
