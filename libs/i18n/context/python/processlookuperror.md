# Python Builtin: `ProcessLookupError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`ProcessLookupError` is a built-in exception raised when a given process doesn't exist — an operation targeted a process ID (PID) that names no living process. It is a subclass of `OSError`, introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `ESRCH` ("No such process").

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Signaling a process that has already exited (POSIX)
import os
import signal
import subprocess

proc = subprocess.Popen(["sleep", "0.1"])
proc.wait()  # the child has exited and been reaped; its PID is free

try:
    os.kill(proc.pid, signal.SIGTERM)
except ProcessLookupError as exc:
    print(f"No such process: {exc}")  # errno ESRCH
```

**What this does:** After the child exits and `wait()` collects it, no process with that PID exists any longer. Sending it a signal makes the kernel answer `ESRCH`, which Python raises as `ProcessLookupError`. (In principle the OS could reuse the PID for a new process; in this short window that is vanishingly unlikely.)

### Example 2: Common Pattern

```python
# Liveness probe: "signal 0" checks existence without disturbing the process (POSIX)
import os

def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)  # signal 0: no signal sent, only existence + permission check
    except ProcessLookupError:
        return False     # no process with this PID
    except PermissionError:
        return True      # exists, but belongs to another user
    return True

print(pid_alive(os.getpid()))  # True -- we exist
```

**What this does:** The idiomatic Unix liveness check sends signal number 0, which performs the lookup and permission check without delivering anything. `ProcessLookupError` is the definitive "not running" answer; `PermissionError` paradoxically confirms life. Daemon managers use exactly this pattern to validate stale PID files.

### Example 3: Edge Case

```python
# Other process-targeting calls raise it too, not just kill() (POSIX)
import os
import subprocess

proc = subprocess.Popen(["sleep", "0.1"])
proc.wait()

try:
    os.getpgid(proc.pid)  # look up the process group of a dead PID
except ProcessLookupError as exc:
    print(f"Group lookup failed: {exc}")
```

**What this shows:** Any system call that must first *find* the process by PID — `os.kill`, `os.getpgid`, `os.setpriority`, and relatives — raises `ProcessLookupError` when the PID matches nothing. The class is about the failed lookup itself, regardless of what the caller intended to do after finding the process.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `ChildProcessError` - Closest sibling: an operation on a *child* process failed (`ECHILD`); this class covers *any* PID that does not exist (`ESRCH`)
3. `FileNotFoundError` - Structural cousin from the same PEP 3151 batch: "looked for X, X does not exist" (files instead of processes)
4. `KeyError` / `LookupError` family - The in-interpreter lookup-failure pattern; same "not found" concept in a different domain

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is "process" + "lookup" + "error" — translations attach a "search/find" verbal noun to the language's standard "process" word, plus the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin-derived + Germanic)

**Root meaning:** "Process" comes from Latin "processus" (a going forward) — in computing, a running instance of a program. "Lookup" is a Germanic compound ("look" + "up") meaning to search for something by its identifier, as in looking a word up in a dictionary. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The underlying errno string is "No such process" (`ESRCH`), but a class named `NoSuchProcessError` would break Python's noun-compound conventions. PEP 3151 instead named the *failed action*: the lookup of a process by PID. The name parallels the interpreter's own `LookupError` family, though this class descends from `OSError`, not `LookupError`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ProcessLookupError` is raised when a system call must locate a process by its PID and finds nothing. Operating systems track running processes in a table keyed by PID; calls like `os.kill(pid, sig)`, `os.getpgid(pid)`, and `os.setpriority(...)` begin by looking the PID up in that table. When the entry is missing — the process exited, or the PID was never allocated — the kernel returns `ESRCH`, and Python raises this exception.

The most common real-world encounter is signaling a process that has already died: daemon stop-scripts reading stale PID files, supervisors racing against a child that crashed on its own, or health checks probing with signal 0. In each case, `ProcessLookupError` is the authoritative "that process is not running" answer, and mature code treats it as an expected, benign outcome ("already stopped — fine") rather than a crash-worthy failure.

The precise boundary with `ChildProcessError` matters: `ESRCH` (this class) means "no process with that PID exists at all, anywhere in the system"; `ECHILD` (`ChildProcessError`) means "the process you tried to wait on is not a child of yours (any longer)." A PID can be alive and still raise `ChildProcessError` from `waitpid` if it is not your child, while `ProcessLookupError` requires the PID to name nothing at all. Translations must keep the two class names clearly distinct while sharing their "process" root.

**Key behaviors:**

1. **Maps to `ESRCH`:** Any `OSError` raised with this errno becomes a `ProcessLookupError` instance automatically. The symbolic constant `errno.ESRCH` is portable.

2. **Raised by PID-targeting calls:** `os.kill`, `os.killpg`, `os.getpgid`, `os.setpriority`, and similar calls that resolve a PID first. It concerns the lookup step — the intended operation never happens.

3. **Often an expected outcome:** In stop-scripts and liveness probes, catching it and proceeding ("already gone") is the normal control flow. Alongside `PermissionError`, it forms the standard signal-0 existence-check idiom.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (process noun + lookup verbal noun + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment the failed lookup returns

### Recommended Form

**Primary recommendation:** Compound noun combining the language's standard "process" word (identical to the one in the `ChildProcessError` translation) with a "search/lookup" verbal noun, plus the corpus "error" word. A "search failure" framing is preferred over a literal "no such process" sentence, matching the English class name rather than the errno string.

**Forms to AVOID:**

- ❌ Sentence-like forms ("ProcesoNoExiste") - errno prose, not a class-name compound; breaks the corpus pattern
- ❌ Verb forms ("BuscarProceso") - reads as a command to search
- ❌ "Process" words that differ from the `ChildProcessError` translation - the pair must share their root

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: To look upward ("look up at the sky")
- ❌ Meaning 2: To improve ("things are looking up")
- ❌ Meaning 3: To visit someone ("look me up when you're in town")
- ✅ Meaning 4: **SEARCH BY IDENTIFIER** (resolving a PID against the kernel's process table, like looking a word up in a dictionary)

**Example:**

English "look up / lookup" can mean:

1. "She looked up from her book" (gaze upward) ❌
2. "The economy is looking up" (improving) ❌
3. "Look up an old friend" (pay a visit) ❌
4. "Look up the PID in the process table" (search by key) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a search for a process by its identifier that found nothing — NOT gazing, improving, or visiting.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ProcessLookupError`, check these translations:**

- [ ] `ChildProcessError` (childprocesserror.md) - Sibling; MUST use the identical word for "process" so the pair reads as related
- [ ] `ConnectionError` (connectionerror.md) and its siblings (connectionabortederror.md, connectionrefusederror.md, connectionreseterror.md, brokenpipeerror.md) - Same `OSError` family; the "error" suffix must be identical across all of them
- [ ] `KeyError` - Corpus lookup-failure exception; the "search/lookup" vocabulary should feel related without being identical
- [ ] `PermissionError` - The contrasting outcome of the signal-0 idiom; the two must never share their distinguishing word
- [ ] `TimeoutError` (timeouterror.md) - Sibling OS-error; parallel compound structure

**Consistency rule:**

Two components are fixed by other terms: the "process" word (identical to `ChildProcessError`) and the "error" suffix (identical to the whole exception corpus, anchored by connectionerror.md and its family). Only the "lookup/search" component is new, and it must not read as permission or access vocabulary.


### Functional relationships

**This term works WITH:**

1. **`os.kill()` + `ProcessLookupError`**: The canonical raise site:

```python
try:
    os.kill(pid, signal.SIGTERM)
except ProcessLookupError:
    pass  # already gone -- which is what we wanted
```

2. **`PermissionError` + `ProcessLookupError`**: The signal-0 existence probe:

```python
try:
    os.kill(pid, 0)
except ProcessLookupError:
    alive = False
except PermissionError:
    alive = True  # exists, owned by someone else
else:
    alive = True
```

**Common pairing:**

```python
# Graceful stop with a stale-PID-file guard (POSIX)
import os
import signal

def stop_daemon(pid_file: str) -> str:
    try:
        with open(pid_file) as fh:
            pid = int(fh.read().strip())
    except FileNotFoundError:
        return "not running (no PID file)"

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        os.remove(pid_file)  # stale file: process died without cleanup
        return "not running (stale PID file removed)"
    return f"sent SIGTERM to {pid}"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ProcessLookupError`

- "Process" is settled CS vocabulary in most languages, and the sibling `ChildProcessError` already fixes it
- "Lookup" needs a search-by-identifier word, with several candidates per language (search, find, query, consult)
- Three-component compound pushes against length limits in some languages
- The lookup-vs-permission distinction must survive for the signal-0 idiom to make sense

**For this term:** MEDIUM

**Rationale:** The frame is inherited (process word, error suffix), and every language has serviceable "search" vocabulary; the judgment is picking the search word that reads as *resolving an identifier* rather than physically hunting. Length is the secondary concern for the Romance noun-phrase forms.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FAILED SEARCH FOR A PROCESS BY PID (not gaze, improvement, or visiting senses of "look up")?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Distinguishable from permission-denied and child-process errors?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] "Process" word identical to the `ChildProcessError` translation?
- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] "Search/lookup" word related to (but distinct from) the corpus `KeyError` vocabulary?

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
term: ProcessLookupError
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
