# Python Builtin: `OSError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound)
**Python Version:** 3.x+ (unified semantics since 3.3, PEP 3151)
**Difficulty:** MEDIUM

---

## Quick Summary

`OSError` is the built-in exception raised when a system function returns a system-related error — failed file operations, missing paths, permission denials, socket failures, and other conditions the operating system reports through error codes. Since Python 3.3 (PEP 3151) it is the single base class for the entire OS/IO exception family, carrying `errno`, `strerror`, and `filename` attributes that describe exactly what the operating system rejected.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A failed file operation raises an OSError carrying OS-level details
try:
    f = open("no_such_file.txt")
except OSError as e:
    print(e.errno)     # 2
    print(e.strerror)  # 'No such file or directory'
    print(e.filename)  # 'no_such_file.txt'
```

**What this does:** Opening a file that does not exist fails at the operating-system level. Python raises an `OSError` (here, its subclass `FileNotFoundError`) whose attributes expose the OS error code (`errno`), the OS error message (`strerror`), and the path that caused the failure (`filename`).

### Example 2: Common Pattern

```python
# Catching OSError as the umbrella for any OS-level failure
import errno

def read_config(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError as e:
        if e.errno == errno.ENOENT:
            return ""  # missing config is fine, use defaults
        if e.errno == errno.EACCES:
            raise RuntimeError(f"No permission to read {path}") from e
        raise  # anything else is unexpected: re-raise
```

**What this does:** Because every file/OS exception (`FileNotFoundError`, `PermissionError`, `IsADirectoryError`, ...) is a subclass of `OSError`, a single `except OSError` handler catches all of them. Code that needs to distinguish causes can check `e.errno` against the symbolic constants in the `errno` module — although since Python 3.3 catching the specific subclass directly is the preferred style.

### Example 3: Edge Case

```python
# Constructing OSError with a known errno returns the matching subclass
import errno

e = OSError(errno.ENOENT, "No such file or directory")
print(type(e))               # <class 'FileNotFoundError'>
print(isinstance(e, OSError))  # True

# IOError and EnvironmentError are the SAME class as OSError since 3.3
print(IOError is OSError)          # True
print(EnvironmentError is OSError)  # True
```

**What this shows:** `OSError` has constructor magic: calling it with an `errno` that maps to a dedicated subclass (`ENOENT` → `FileNotFoundError`, `EACCES` → `PermissionError`, ...) returns an instance of that subclass, not of bare `OSError`. It also shows that `IOError` and `EnvironmentError` are not separate classes — they are legacy aliases bound to the very same `OSError` object, kept only for backward compatibility.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (base class of the OS/IO exception family)

**Similar terms in this pattern:**

1. `FileNotFoundError` - Subclass of `OSError` raised for `errno` `ENOENT` (path does not exist)
2. `PermissionError` - Subclass of `OSError` raised for `errno` `EACCES`/`EPERM` (access denied)
3. `FileExistsError` - Subclass of `OSError` raised for `errno` `EEXIST` (path already exists)
4. `RuntimeError` - Sibling built-in exception; same "domain + Error" naming convention

**Pattern rule:** Exception classes are noun compounds ending in "Error" in English. Translations must be compound nouns that name the problem domain ("operating system") plus the error concept — never verbs, never sentences.


---

## Etymology (Brief)

**English Origin:** Initialism + Latin-derived noun

**Root meaning:** "OS" abbreviates "operating system." "Operate" comes from Latin "operari" (to work, to labor); an operating system is the software that makes the machine work. "Error" derives from Latin "errare" (to wander, to go astray).

**Why Python uses this:** The name says precisely where the failure happened: not in your Python logic, but in a request the operating system refused or could not complete. Before Python 3.3 the same territory was split across `OSError`, `IOError`, `WindowsError`, `socket.error`, and others; PEP 3151 merged them all into `OSError` because the distinction had become arbitrary — the OS is the single source of these errors.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`OSError` is raised whenever Python asks the operating system to do something — open a file, create a directory, connect a socket, change permissions — and the operating system answers with an error code instead of a result. Python wraps that error code into an `OSError` instance whose attributes preserve the OS-level detail: `errno` (the numeric POSIX error code), `strerror` (the human-readable message from the OS), `filename` and `filename2` (the path or paths involved), and, on Windows, `winerror` (the native Windows error code).

Since Python 3.3 and PEP 3151, `OSError` is the root of a family of more specific subclasses: `FileNotFoundError`, `FileExistsError`, `PermissionError`, `IsADirectoryError`, `NotADirectoryError`, `BlockingIOError`, `ChildProcessError`, `ConnectionError` (and its own subclasses), `InterruptedError`, `ProcessLookupError`, and `TimeoutError`. Each subclass corresponds to particular `errno` values, so modern code writes `except FileNotFoundError:` instead of catching `OSError` and inspecting `e.errno`. Catching `OSError` itself remains the right move when any OS-level failure should be handled the same way.

The same PEP also collapsed the old parallel names: `IOError`, `EnvironmentError`, `WindowsError` (Windows only), `socket.error`, `select.error`, and `mmap.error` all became aliases of `OSError`. They still exist so old code keeps running, but they are the same class — new code should write `OSError`.

**Key behaviors:**

1. **Carries OS-level diagnostics:** Every `OSError` exposes `errno`, `strerror`, and (when a path is involved) `filename`/`filename2`. The exception message you see — e.g. `[Errno 13] Permission denied: 'secret.txt'` — is assembled from these attributes.

2. **Constructor maps errno to subclasses:** `OSError(errno_value, message)` returns an instance of the matching subclass when one exists (`OSError(errno.EEXIST, ...)` is a `FileExistsError`). This keeps `raise OSError(...)` code and `except FileExistsError:` handlers compatible.

3. **Base class of the whole OS/IO family:** `except OSError:` catches every subclass in the family, and also everything raised under the legacy names `IOError` and `EnvironmentError`, because those names point at the same class.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain "operating system" + error concept)
- **Action vs State:** STATE - names an error condition reported by the OS, not an action
- **Temporal aspect:** Instantaneous - raised at the moment the OS rejects a system call

### Recommended Form

**Primary recommendation:** Use a compound noun built from **the target language's own established computing term for "operating system"** plus the same "error" word used across all exception translations. Two legitimate strategies exist, and the rule for choosing between them is: follow what the language's CS education and OS localization already use.

- **Translate the concept** when the language has a native term for "operating system" in everyday technical use.
- **Use the localized abbreviation/initialism** when THAT is the established vocabulary. This means not raw Latin "OS" — the abbreviation as the language itself writes it, in its own script.

What is NOT acceptable is embedding raw Latin-script "OS" inside a non-Latin identifier: it breaks script consistency, harms RTL rendering, and violates the pack's single-script rule.

**Forms to AVOID:**

- ❌ Verb forms ("FailOnSystem") - exception classes are noun compounds, never verbs or clauses
- ❌ Generic "system error" - collides with `SystemError`, a different Python exception (internal interpreter error)
- ❌ Raw Latin "OS" mixed into non-Latin scripts - script mixing breaks rendering and the pack's consistency rules
- ❌ Long descriptive phrases ("the computer's operating system's error") - identifiers must stay at 1-3 words

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "OS" as any random initialism (open source, out of stock, etc.)
- ❌ Meaning 2: "System error" in the loose sense of "something broke somewhere"
- ❌ Meaning 3: Python's `SystemError` (internal interpreter malfunction — a different exception)
- ✅ Meaning 4: **An error reported BY the operating system** through its error-code mechanism (errno) when a system call fails

**Example:**

English "OS/system error" can suggest:

1. "The system is down" (vague, any failure anywhere) ❌
2. `SystemError: internal error in the Python interpreter` ❌
3. `OSError: [Errno 13] Permission denied` — the OS refused a concrete request ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the operating system, as a named component, reported a failure — NOT a vague "system problem" and NOT Python's own `SystemError`.**

One more disambiguation is unique to this term: `IOError` and `EnvironmentError` are the same class as `OSError` (aliases since 3.3). Their entries in the pack must receive the IDENTICAL translation to whatever you choose here — see their own briefs.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `OSError`, check these translations:**

- [ ] `IOError` - Legacy alias; its translation must be IDENTICAL to this one
- [ ] `EnvironmentError` - Legacy alias; its translation must be IDENTICAL to this one
- [ ] `FileNotFoundError` / `FileExistsError` - Subclasses; must reuse the same "error" word and file vocabulary
- [ ] `PermissionError` / `IsADirectoryError` / `NotADirectoryError` - Subclasses; same "error" word and structure
- [ ] `SystemError` - Must remain clearly DISTINCT from this translation (different exception, interpreter-internal)

**Consistency rule:**

`OSError` anchors the whole os_io family. The "error" word chosen here must be the same one used in every subclass translation, and the structural pattern (error-first or error-last, per the language's compounding convention) must be identical across the family. Decide the "operating system" rendering once (native term vs. localized abbreviation) and never revisit it per-file.


### Functional relationships

**This term works WITH:**

1. **`try`/`except` + `OSError`**: The umbrella handler for any OS-level failure

```python
try:
    os.makedirs(path)
except OSError:
    ...
```

2. **`errno` module + `OSError`**: Symbolic names for the `errno` attribute values

```python
try:
    save_results(path)
except OSError as e:
    if e.errno == errno.ENOSPC:  # disk full — no dedicated subclass exists
        ...
```

**Common pairing:**

```python
import errno
import os

# OSError as the family base: one handler for all OS failures
try:
    with open("data/report.txt") as f:
        content = f.read()
except FileNotFoundError:      # specific subclass first
    content = ""
except PermissionError:        # another subclass
    raise SystemExit("Access denied")
except OSError as e:           # anything else the OS reported
    print(f"OS failure {e.errno}: {e.strerror} ({e.filename})")

# Subclass mapping via the constructor
assert type(OSError(errno.EACCES, "denied")) is PermissionError

# Legacy aliases point at the same class
assert IOError is OSError and EnvironmentError is OSError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `OSError`

- The "operating system" rendering forces a real decision: native term vs. localized abbreviation
- Must stay distinct from `SystemError` in every language
- The choice cascades into seven-plus subclass translations and two alias entries
- Localized abbreviations vary in familiarity by region

**For this term:** MEDIUM

**Rationale:** The concept is universally taught and every language has an established term for "operating system," so this is not HARD. But the translator must (a) choose between the full term and the localized abbreviation based on the target language's actual computing usage, (b) avoid the `SystemError` collision, and (c) understand that this single choice anchors the entire os_io exception family. Those cascading stakes justify MEDIUM rather than EASY.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Names the OPERATING SYSTEM specifically (not a vague "system")?
- [ ] Clearly indicates an ERROR condition?
- [ ] Cannot be confused with `SystemError` in the target language?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Abbreviation (if used) is the target language's own, written in the target script?
- [ ] Follows target language grammar for compounds?

### 3. Consistency

- [ ] Uses the same "error" word as `KeyError`, `IndexError`, and the rest of the pack?
- [ ] Same structural pattern (error-first or error-last) as other exceptions?
- [ ] `IOError` and `EnvironmentError` entries carry the IDENTICAL translation?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on the target language's standard keyboard?
- [ ] Easy to pronounce and remember?

### 5. Cultural Appropriateness

- [ ] No offensive or comical readings in the target culture?
- [ ] Matches how local CS education actually names the operating system?

### 6. Technical Compatibility

- [ ] Single script throughout (no Latin "OS" embedded in non-Latin text)?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: OSError
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
