# Python Builtin: `ChildProcessError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`ChildProcessError` is a built-in exception raised when an operation on a child process fails — most commonly waiting for a child that does not exist or has already been reaped. It is a subclass of `OSError`, introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `ECHILD` ("No child processes").

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Waiting for a child when this process has none (POSIX)
import os

try:
    os.waitpid(-1, 0)  # "wait for any child" -- but there are no children
except ChildProcessError as exc:
    print(f"No children to wait for: {exc}")  # errno ECHILD
```

**What this does:** `os.waitpid(-1, 0)` asks the operating system to wait for any child process to finish. A process that never spawned children (or whose children were all already collected) has nothing to wait for, so the OS answers `ECHILD` and Python raises `ChildProcessError`.

### Example 2: Common Pattern

```python
# Reap children in a loop until the OS says there are none left (POSIX)
import os
import subprocess

procs = [subprocess.Popen(["sleep", "0.1"]) for _ in range(3)]

while True:
    try:
        pid, status = os.waitpid(-1, 0)
        print(f"Reaped child {pid} (status {status})")
    except ChildProcessError:
        print("All children reaped")
        break
```

**What this does:** Low-level process supervisors loop over `waitpid` to collect exit statuses; `ChildProcessError` is the natural loop terminator meaning "the nursery is empty." (In production code, prefer letting each `Popen` object do its own `wait()` — reaping a `Popen`'s child behind its back confuses the object's later bookkeeping. Here it demonstrates the OS-level pattern.)

### Example 3: Edge Case

```python
# Waiting twice for the same child: the second wait finds no such child (POSIX)
import os
import subprocess

proc = subprocess.Popen(["sleep", "0.1"])
proc.wait()  # Popen reaps the child; its exit status is now consumed

try:
    os.waitpid(proc.pid, 0)  # the child is already gone from the kernel's table
except ChildProcessError as exc:
    print(f"Already reaped: {exc}")
```

**What this shows:** A child process can be waited on exactly once. After `Popen.wait()` collects the exit status, the kernel forgets the child, and any further `waitpid` on that PID raises `ChildProcessError`. This "double reap" is the most common way real code encounters the exception — usually a sign that two components both think they own the child.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `ProcessLookupError` - Closest sibling: a *given* process does not exist (`ESRCH`); this class is about *child* processes specifically (`ECHILD`)
3. `InterruptedError` - Sibling PEP 3151 class: system call interrupted by a signal (`EINTR`)
4. `ConnectionError` - Sibling family: the connection-failure branch of the same PEP 3151 reorganization

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is "child" + "process" + "error" — translations attach the language's standard kinship-metaphor modifier for a spawned subprocess to its standard "process" word, plus the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Child" (Old English "cild") is the kinship metaphor Unix chose in the 1970s: when a process `fork()`s, the original is the "parent" and the copy is its "child." "Process" comes from Latin "processus" (a going forward) — a running instance of a program. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name mirrors the POSIX error string for `ECHILD`, "No child processes." PEP 3151 promoted that errno into a dedicated class so process-management code can catch "the child I tried to operate on is not there" by name instead of checking error numbers.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ChildProcessError` is raised when an operation that targets a child process fails because, from the kernel's point of view, no such child exists. In the Unix process model, a parent that spawns a child is responsible for "reaping" it — collecting its exit status with a wait call once it terminates. The wait family (`os.waitpid`, `os.wait`, `os.wait3`, `os.wait4`) raises this exception, mapped from `ECHILD`, when the calling process has no children matching the request.

The two everyday causes are waiting when nothing was spawned, and waiting *again* for a child that was already reaped — for example mixing `subprocess.Popen.wait()` with a manual `os.waitpid` on the same PID, or installing a SIGCHLD handler that reaps children a `Popen` object still expects to own. The exception is therefore usually a signal of double bookkeeping rather than of a crashed child: a child that fails still gets reaped normally; a child that *cannot be found* raises this.

The kinship metaphor matters for translation. "Child process" is a fixed term of art across operating-system literature, and most languages have already settled a conventional rendering — sometimes with a different kinship word (some traditions literally say "daughter process"). Translators should adopt the established local convention rather than inventing a new metaphor, and should keep it consistent with whatever the corpus uses for "parent process" contexts.

**Key behaviors:**

1. **Maps to `ECHILD`:** Any `OSError` raised with this errno becomes a `ChildProcessError` instance automatically. The symbolic constant `errno.ECHILD` is portable even though the number varies by platform.

2. **Raised by the wait family:** `os.waitpid` and relatives are the canonical sources. The distinction from `ProcessLookupError` (`ESRCH`) is precise: `ESRCH` means "no process with that PID at all"; `ECHILD` means "that process is not a child of yours (anymore)."

3. **Children are reaped exactly once:** After a successful wait, the kernel discards the child's record; later waits on the same PID raise this exception. High-level APIs (`subprocess`) do the reaping internally, which is why manual wait calls alongside them misfire.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (child modifier + process noun + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment the failed process operation returns

### Recommended Form

**Primary recommendation:** Use the target language's *established* term of art for "child process" — kinship metaphor, sub-process construction, or whatever local OS literature has standardized — plus the corpus "error" word. Do not translate "child" in isolation; translate the fixed phrase "child process" as a unit.

**Forms to AVOID:**

- ❌ Literal "small child / infant" vocabulary - reads as a program for children, not a spawned process
- ❌ Verb forms ("SpawnProcess"-style compounds) - exceptions are nouns, not actions
- ❌ Inventing a new metaphor where the language already has one - breaks recognition against existing OS documentation

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A human child ("the child is asleep")
- ❌ Meaning 2: Offspring in genealogy or data structures generally ("child node of a tree")
- ❌ Meaning 3: A product of something ("a child of the sixties")
- ✅ Meaning 4: **A SPAWNED SUBPROCESS** (a process created by another process, which the parent must wait on; OS code `ECHILD`)

**Example:**

English "child" can mean:

1. "The child is learning to read" (human) ❌
2. "Each tree node has two children" (data structure) ❌
3. "Jazz is a child of the blues" (figurative descent) ❌
4. "fork() returns 0 in the child process" (spawned process) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the operating-system parent/child process relationship — NOT human children, tree nodes, or figurative offspring.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ChildProcessError`, check these translations:**

- [ ] `ProcessLookupError` (processlookuperror.md) - Sibling; MUST use the identical word for "process" so the pair reads as related
- [ ] `ConnectionError` (connectionerror.md) and its siblings (connectionabortederror.md, connectionrefusederror.md, connectionreseterror.md, brokenpipeerror.md) - Same `OSError` family; the "error" suffix must be identical across all of them
- [ ] `InterruptedError` (interruptederror.md) - Sibling PEP 3151 class; parallel compound structure
- [ ] `TimeoutError` (timeouterror.md) - Sibling; `subprocess` timeouts appear in the same code paths

**Consistency rule:**

Two components are shared with other terms and must match exactly: the "process" word (identical to `ProcessLookupError`) and the "error" suffix (identical to the whole exception corpus, anchored by the connectionerror.md family). Only the "child" modifier is unique to this term — and it should come from the language's existing OS literature.


### Functional relationships

**This term works WITH:**

1. **`os.waitpid()` + `ChildProcessError`**: The canonical raise site:

```python
try:
    pid, status = os.waitpid(-1, 0)
except ChildProcessError:
    pass  # no children left
```

2. **`subprocess.Popen` + manual waits**: The double-reap hazard:

```python
proc.wait()               # Popen reaps the child
os.waitpid(proc.pid, 0)   # raises ChildProcessError: already reaped
```

**Common pairing:**

```python
# A tiny supervisor: spawn workers, reap them all, stop when none remain (POSIX)
import os
import subprocess

def run_workers(commands):
    for cmd in commands:
        subprocess.Popen(cmd)

    finished = []
    while True:
        try:
            pid, status = os.waitpid(-1, 0)
        except ChildProcessError:
            break  # every child reaped
        finished.append((pid, os.waitstatus_to_exitcode(status)))
    return finished

print(run_workers([["sleep", "0.1"], ["sleep", "0.2"]]))
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ChildProcessError`

- "Child process" is a fixed term of art with an established rendering in most languages — but the renderings differ in metaphor (child, daughter, sub-process), so the local convention must be looked up, not guessed
- The "process" word is constrained by the `ProcessLookupError` sibling
- Literal "infant" mistranslations are tempting and embarrassing
- Concept (process trees, reaping) is standard CS curriculum worldwide

**For this term:** MEDIUM

**Rationale:** The pieces are all conventional: most languages teach "child process" with one settled phrase, and the "process" and "error" components are inherited from siblings. The single judgment call is matching the local kinship-or-subprocess convention instead of translating "child" word-for-word.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SPAWNED SUBPROCESS relationship (not human child, tree node, or figurative offspring)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Matches the language's established "child process" term from OS literature?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] "Process" word identical to the `ProcessLookupError` translation?
- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] Kinship/sub-process metaphor consistent with any other parent/child process references in the corpus?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional (no literal "infant" vocabulary)?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: ChildProcessError
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
