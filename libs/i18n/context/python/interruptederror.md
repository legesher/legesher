# Python Builtin: `InterruptedError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`InterruptedError` is a built-in exception raised when a system call is interrupted by an incoming signal before it can complete. It is a subclass of `OSError`, introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `EINTR`. Since Python 3.5 (PEP 475), the interpreter automatically retries interrupted system calls when the signal handler returns normally, so this exception rarely surfaces in modern code.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# OSError with errno EINTR automatically becomes InterruptedError
import errno
import os

try:
    raise OSError(errno.EINTR, os.strerror(errno.EINTR))
except InterruptedError as exc:
    print(f"Interrupted: {exc}")
    print(type(exc).__name__)  # InterruptedError -- errno mapping picked the subclass
```

**What this does:** Constructing an `OSError` with `errno.EINTR` yields an `InterruptedError` instance — the errno-to-subclass mapping is built into the exception machinery. This is also how the exception genuinely arises: a C-level function returns `EINTR`, and Python surfaces it as this class.

### Example 2: Common Pattern

```python
# The classic pre-3.5 retry loop (still correct, now mostly redundant)
import os

def read_exactly(fd, size):
    while True:
        try:
            return os.read(fd, size)
        except InterruptedError:
            continue  # a signal arrived mid-read; just try again

r, w = os.pipe()
os.write(w, b"hello")
print(read_exactly(r, 5))  # b'hello'
```

**What this does:** Before Python 3.5, any slow system call could fail with `InterruptedError` whenever a signal (like SIGCHLD from a finished subprocess) arrived, so robust code wrapped I/O in retry loops exactly like this. PEP 475 moved that retry into the interpreter itself; the loop remains harmless and is still seen in codebases that support older interpreters or call third-party C extensions.

### Example 3: Edge Case

```python
# PEP 475 in action: a signal arrives, the handler runs, and sleep RESUMES (POSIX)
import signal
import time

def handler(signum, frame):
    print("signal handled; the sleep call is retried, not interrupted")

signal.signal(signal.SIGALRM, handler)
signal.alarm(1)  # deliver SIGALRM in 1 second

start = time.monotonic()
time.sleep(2)  # NOT interrupted: Python retries after the handler returns
print(f"slept {time.monotonic() - start:.1f}s")  # ~2.0
```

**What this shows:** The signal fires halfway through `time.sleep(2)`, the handler runs — and no `InterruptedError` appears. Since PEP 475, Python recomputes the timeout and resumes the call. The exception now only surfaces when the signal handler itself raises an exception (in which case *that* exception propagates) or from code paths, such as some third-party C extensions, that do not implement the retry.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `BlockingIOError` - Sibling PEP 3151 class: operation would block on a non-blocking object (`EAGAIN`/`EWOULDBLOCK`)
3. `KeyboardInterrupt` - Conceptual cousin: Ctrl+C raises this *instead of* `InterruptedError`; the two must not share a translation
4. `ChildProcessError` - Sibling PEP 3151 class (`ECHILD`); signals like SIGCHLD are a classic source of interruptions

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is participle "interrupted" + "error" — translations attach a "cut in on / broken in upon" participle or verbal noun to the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin roots)

**Root meaning:** "Interrupt" comes from Latin "interrumpere" (inter- "between" + rumpere "to break") — to break in between, to cut something off mid-course. In computing, an interrupt is an asynchronous event that breaks into normal execution; a signal interrupting a system call is exactly that. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name mirrors the POSIX error string for `EINTR`, "Interrupted system call." PEP 3151 promoted the errno to a class; PEP 475 later made the interpreter absorb most occurrences, leaving the class chiefly as a compatibility and completeness feature.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`InterruptedError` reports that a system call — a read, write, wait, sleep, or similar kernel request — was cut short by the delivery of a signal before it could finish. On POSIX systems, when a signal arrives while a process is blocked in a slow system call, the kernel runs the signal handler and then makes the call return early with `EINTR`. Python maps that errno to this exception class.

Its practical importance has almost vanished by design. Historically, `EINTR` was a notorious source of flaky bugs: any signal (a resized terminal, a finished child process) could make unrelated I/O fail, so careful C and Python programmers wrapped every slow call in retry loops. PEP 475, adopted in Python 3.5, moved the retry into the interpreter: when a signal handler returns normally, functions in `os`, `io`, `socket`, `select`, `time`, and friends recompute their timeouts and resume automatically. Consequently, modern Python code almost never sees `InterruptedError` — if a signal handler raises (as the default SIGINT handler does with `KeyboardInterrupt`), the handler's exception propagates instead.

The class still exists for real reasons: the errno mapping must land somewhere (`OSError(EINTR, ...)` instances become this class), third-party C extensions may return `EINTR` without implementing the retry, and code targeting Python 3.3/3.4 semantics still catches it. A translation brief should present it as "the interrupted-system-call error that Python now mostly handles for you."

**Key behaviors:**

1. **Maps to `EINTR`:** Any `OSError` raised with this errno becomes an `InterruptedError` instance automatically. The symbolic constant `errno.EINTR` is portable.

2. **Rarely raised since Python 3.5 (PEP 475):** Interrupted standard-library system calls are retried automatically when the signal handler returns normally. The exception effectively surfaces only from code outside that machinery (e.g., some C extensions) or on pre-3.5 interpreters.

3. **Distinct from `KeyboardInterrupt`:** Ctrl+C delivers SIGINT, whose default Python handler raises `KeyboardInterrupt` — a `BaseException`, not an `OSError`. `InterruptedError` is about the *system call's* early return, not about the user's intent to stop the program.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (interrupted participle + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment the call returns early

### Recommended Form

**Primary recommendation:** Compound noun combining the language's standard computing term for "interrupt/interruption" (the same root used for hardware interrupts and interrupted calls in local CS literature) with the corpus "error" word. Verify the chosen root differs from the corpus translation of `KeyboardInterrupt` only in structure, not in root — the two *should* share the interruption root, since both descend from the same concept, but they must remain distinct terms.

**Forms to AVOID:**

- ❌ Verb forms ("InterrumpirError") - reads as a command to interrupt
- ❌ Words meaning "paused/suspended" - an interrupted call returned early; it is not waiting to resume by itself
- ❌ Words meaning "cancelled by the user" - user cancellation is `KeyboardInterrupt`; this class is mechanical, signal-level interruption

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Rudely cutting into a conversation ("don't interrupt me")
- ❌ Meaning 2: A temporary suspension of service ("power interruption")
- ❌ Meaning 3: The user aborting a program with Ctrl+C (that is `KeyboardInterrupt`)
- ✅ Meaning 4: **A SYSTEM CALL CUT SHORT BY A SIGNAL** (the kernel returned `EINTR` because a signal arrived mid-call)

**Example:**

English "interrupted" can mean:

1. "She interrupted the meeting" (conversational) ❌
2. "Service was interrupted for maintenance" (outage) ❌
3. "The user interrupted the script with Ctrl+C" (`KeyboardInterrupt`) ❌
4. "read() failed with 'Interrupted system call'" (signal broke into a kernel call) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a mechanical, signal-level interruption of a system call — NOT conversational rudeness, service outages, or user cancellation.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `InterruptedError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) and its siblings (connectionabortederror.md, connectionrefusederror.md, connectionreseterror.md, brokenpipeerror.md) - Same `OSError` family; the "error" suffix must be identical across all of them
- [ ] `BlockingIOError` (blockingioerror.md) - Sibling PEP 3151 class; parallel structure (condition + error)
- [ ] `KeyboardInterrupt` - Shares the interruption ROOT but must remain a distinct term (different class, different base)
- [ ] `ChildProcessError` (childprocesserror.md) - Sibling; SIGCHLD interruptions historically linked the two
- [ ] `TimeoutError` (timeouterror.md) - Sibling; both describe calls ending before completing their work, with different causes

**Consistency rule:**

The "error" suffix comes verbatim from the exception corpus (anchored by connectionerror.md and its family). The interruption root should match the root inside the corpus's `KeyboardInterrupt` translation while the overall terms stay distinct — same concept family, different exceptions.


### Functional relationships

**This term works WITH:**

1. **`signal` handlers + slow system calls**: The mechanism that produces (or, post-PEP 475, absorbs) the interruption:

```python
signal.signal(signal.SIGALRM, handler)
os.read(fd, n)  # a signal here is retried internally since Python 3.5
```

2. **Retry loops (legacy compatibility)**:

```python
while True:
    try:
        data = os.read(fd, 4096)
        break
    except InterruptedError:
        continue
```

**Common pairing:**

```python
# Demonstrating both worlds: automatic retry vs. a handler that raises
import errno
import os
import signal

# World 1 (modern): handler returns normally -> call is retried, no exception
signal.signal(signal.SIGALRM, lambda s, f: None)
signal.alarm(1)
r, w = os.pipe()
os.write(w, b"x")
print(os.read(r, 1))  # b'x' -- the alarm did not disturb the read

# World 2 (mapping): EINTR from any source still becomes InterruptedError
try:
    raise OSError(errno.EINTR, "interrupted system call")
except InterruptedError:
    print("errno.EINTR maps to InterruptedError")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `InterruptedError`

- "Interrupt" is core CS vocabulary with a settled translation in most languages (hardware interrupts guarantee it)
- The chosen root must coordinate with `KeyboardInterrupt` without colliding
- Everyday senses (conversational interruption, outage) must be excluded, but code context does most of that work
- The behavioral subtlety (PEP 475 makes it rare) affects documentation, not the name itself

**For this term:** MEDIUM

**Rationale:** Every language with CS curriculum has a standard "interrupt" term, and the compound is structurally simple. The single coordination point — sharing a root with `KeyboardInterrupt` while remaining distinct — is mechanical once both terms are on the table.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SIGNAL-INTERRUPTED SYSTEM CALL (not conversation, outage, or Ctrl+C)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Uses the language's standard CS "interrupt" root?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] Interruption root consistent with (but term distinct from) `KeyboardInterrupt`?
- [ ] Parallel in structure to sibling OS-error terms (`BlockingIOError`, `ChildProcessError`)?

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
term: InterruptedError
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
