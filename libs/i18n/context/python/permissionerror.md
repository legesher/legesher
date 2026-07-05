# Python Builtin: `PermissionError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound)
**Python Version:** 3.3+ (PEP 3151)
**Difficulty:** EASY

---

## Quick Summary

`PermissionError` is the built-in exception raised when an operation is attempted without adequate access rights — reading a protected file, writing into a system directory, or performing a privileged operation as an unprivileged user. It is the `OSError` subclass corresponding to `errno` `EACCES` ("Permission denied") and `EPERM` ("Operation not permitted"), the operating system's two ways of saying "you are not allowed to do that."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Reading a file whose permissions forbid it raises PermissionError
import os

open("secret.txt", "w").close()   # create a file...
os.chmod("secret.txt", 0o000)     # ...then remove all permissions

open("secret.txt")
# PermissionError: [Errno 13] Permission denied: 'secret.txt'
# (does not apply when running as root, which bypasses permission checks)
```

**What this does:** After `os.chmod` strips all access bits, the operating system refuses the `open` request with error code `EACCES` (errno 13), and Python raises `PermissionError` carrying that code, the OS message, and the path in its `errno`, `strerror`, and `filename` attributes.

### Example 2: Common Pattern

```python
# Degrade gracefully when a location is not writable
def save_log(line, path="/var/log/myapp.log"):
    try:
        with open(path, "a") as f:      # system path: usually root-only
            f.write(line + "\n")
    except PermissionError:
        fallback = "myapp.log"          # fall back to the current directory
        with open(fallback, "a") as f:
            f.write(line + "\n")
        print(f"No write access to {path}; logged to {fallback}")

save_log("service started")
```

**What this does:** Appending to a system location fails with `PermissionError` for ordinary users. Catching the specific subclass lets the program degrade gracefully (fall back, prompt for elevation, or explain the problem) instead of crashing — while genuinely unexpected OS errors still propagate.

### Example 3: Edge Case

```python
# Two errno values map here: EACCES (13) and EPERM (1)
import errno
import os

e1 = OSError(errno.EACCES, "Permission denied")
e2 = OSError(errno.EPERM, "Operation not permitted")
print(type(e1), type(e2))
# <class 'PermissionError'> <class 'PermissionError'>

# EPERM: a privileged operation, not a file-permission issue
os.setuid(0)   # as a non-root user:
# PermissionError: [Errno 1] Operation not permitted

# Windows note: opening a directory as a file, or deleting an
# open file, also surfaces as PermissionError there.
```

**What this shows:** `PermissionError` covers two distinct OS refusals: `EACCES` (filesystem access rights forbid it) and `EPERM` (the operation itself requires privileges you lack, like `os.setuid`). Both construct `PermissionError` through `OSError`'s errno mapping. Windows maps several of its own refusals (directory opens, in-use file deletion) onto this same class.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (`OSError` subclass, errno `EACCES`/`EPERM`)

**Similar terms in this pattern:**

1. `OSError` - The parent class; carries the errno/strerror/filename machinery this subclass inherits
2. `FileNotFoundError` - Sibling subclass: the path is absent (`ENOENT`); here the path exists but is off-limits
3. `FileExistsError` - Sibling subclass: the path is unexpectedly occupied (`EEXIST`)
4. `IsADirectoryError` - Sibling subclass: wrong kind of object at the path (`EISDIR`)

**Pattern rule:** Exception classes are noun compounds ending in "Error." Translations combine the target language's standard computing word for "permission" (the one used in file-permission and app-permission UI) with the pack's "error" word — never a verb, never "denied" narration.


---

## Etymology (Brief)

**English Origin:** Latin compound

**Root meaning:** "Permission" comes from Latin "permissio," from "permittere" (to let pass, to allow — literally "to send through"). "Error" derives from Latin "errare" (to wander).

**Why Python uses this:** "Permission denied" is the literal text of the POSIX `EACCES` message, and "permissions" is the universal name for Unix file access rights (read/write/execute bits). PEP 3151 named the class after the concept every programmer already associates with errno 13, folding `EPERM` ("Operation not permitted") into the same class because both mean "the OS refused for lack of rights."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`PermissionError` is raised when the operating system refuses an operation because the requesting process lacks the necessary rights. The everyday cause is file permissions: opening a file without read access, writing to a file or directory without write access, executing without execute permission, or touching system paths (`/etc`, `/var/log`, `C:\Program Files`) as an ordinary user. The OS reports `EACCES` and Python raises this subclass.

The second, less common cause is privileged operations: calls like `os.setuid`, binding to low-numbered network ports, or killing another user's process fail with `EPERM` ("Operation not permitted") when attempted without sufficient privileges. PEP 3151 mapped both `EACCES` and `EPERM` onto `PermissionError`, since the programmer-facing meaning is the same: not allowed. Code that must distinguish them can still inspect `e.errno`.

Handling follows the usual pattern: where a refusal is anticipated (probing for a writable location, optional access to protected data), catch `PermissionError` and degrade gracefully; where access is required, let it propagate — its message names the path, which is the diagnostic an operator needs. Note that permission checks depend on who runs the process: the same code that raises `PermissionError` for a normal user may succeed silently as root/Administrator, which is why tests for this exception can behave differently in privileged CI environments.

**Key behaviors:**

1. **Maps two errno values:** `EACCES` (13, access rights forbid it) and `EPERM` (1, operation requires privileges) both construct `PermissionError` via `OSError`'s errno mapping. Check `e.errno` if the distinction matters.

2. **About rights, not existence:** The path exists and the request is well-formed — the OS simply refuses. This cleanly separates it from `FileNotFoundError` (absent) and `FileExistsError` (unexpectedly present).

3. **Caller-dependent:** Whether it is raised depends on the process's user, group, and privileges, not just on the code. Root/Administrator processes may never see it for file operations that fail for everyone else.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (rights concept "permission" + error concept)
- **Action vs State:** STATE - describes the condition "access rights are insufficient"
- **Temporal aspect:** Instantaneous - raised at the moment the OS refuses the request

### Recommended Form

**Primary recommendation:** Use the target language's **established computing word for "permission"** — the term that appears in its localized file-properties dialogs and app-permission prompts — in singular form, plus the pack's "error" word. Name the missing *thing* (permission), not the act of refusal ("denied"): the class name is a noun compound, and "denial" phrasings drift into sentence territory.

**Forms to AVOID:**

- ❌ "License/permit" vocabulary - legal-document sense, not access rights
- ❌ "Denied" narration ("AccessDenied"-style calques) - describes the event as a sentence, breaks the noun-compound family pattern
- ❌ "Prohibition/forbidden" over-translation - the OS did not outlaw the action; the process lacks rights
- ❌ Plural where the language's compound convention is singular - keep the compact singular head

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Social consent ("she gave me permission to leave early")
- ❌ Meaning 2: A permit or license document (driving permit, software license)
- ❌ Meaning 3: App-store style permissions as a feature ("manage app permissions") — related register, but this error is about a *refusal*, not the settings screen
- ✅ Meaning 4: **Operating-system access rights that the current process lacks** for the attempted operation (EACCES/EPERM)

**Example:**

English "permission" contexts:

1. "May I have permission to speak?" (social) ❌
2. "A fishing permit" (document) ❌
3. `open('/etc/shadow')` as a normal user → the OS refuses for lack of access rights ✅ **This is the Python meaning**

**Your translation should capture meaning #4: OS-level access rights — using the same word your target language's file-properties and permission dialogs use, in its computing register.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `PermissionError`, check these translations:**

- [ ] `OSError` - Parent class; same "error" word and family structure
- [ ] `FileNotFoundError` / `FileExistsError` - Siblings; same structural pattern
- [ ] `IsADirectoryError` / `NotADirectoryError` - Siblings; same structural pattern
- [ ] `open` - Frequently documented alongside this exception
- [ ] Any future `os.chmod`-related vocabulary - the "permission" word must match

**Consistency rule:**

Use one "permission" word across the entire pack: this exception, any `os` module documentation, and any UI strings. If the pack later translates `os.access` or `chmod`-related helpers, they must reuse the same root chosen here.


### Functional relationships

**This term works WITH:**

1. **`open()` / file writes + `except PermissionError`**: The classic protected-path handler

2. **`os.chmod` / `os.setuid` / privileged calls**: The operations that create or trigger permission refusals

**Common pairing:**

```python
import os

# Probe for a writable location
def writable_dir(candidates):
    for d in candidates:
        probe = os.path.join(d, ".write_test")
        try:
            open(probe, "w").close()
            os.remove(probe)
            return d
        except PermissionError:
            continue                  # not writable — try the next one
    raise RuntimeError("no writable directory available")

# Distinguish the two errno sources when it matters
import errno
try:
    os.setuid(0)
except PermissionError as e:
    assert e.errno == errno.EPERM    # privileged operation, not file rights

# Pre-3.3 style still seen in old code (avoid in new code)
try:
    open("/etc/shadow")
except OSError as e:
    if e.errno == errno.EACCES:
        print("no read access")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `PermissionError`

- Every localized OS ships an established "permission" word — the mapping is one-to-one
- The compound is structurally identical to `KeyError`-style two-part names
- The only traps (license/social senses) are closed by choosing the OS-dialog register

**For this term:** EASY

**Rationale:** Unlike its siblings, this name has no participles, no negation, and no clause structure — just domain word + error. The "permission" concept is uniformly established in every target language's computing vocabulary because users meet it constantly in OS and app dialogs. Pick the dialog-register word, attach the family's "error" head, done.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Uses the ACCESS-RIGHTS sense (not license, permit, or social consent)?
- [ ] Same word the target language's permission dialogs use?
- [ ] Clearly an error condition, not a settings feature?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Singular/plural choice matches the language's compound convention?
- [ ] Follows target language grammar for compounds?

### 3. Consistency

- [ ] Same "error" word and position as `OSError` and the rest of the pack?
- [ ] Structure parallels the other os_io subclasses?
- [ ] Permission root reserved for reuse in future `os`-module vocabulary?

### 4. Usability

- [ ] Short (2 content morphemes)?
- [ ] Easy to type on the target language's standard keyboard?
- [ ] Recognizable at a glance in a stack trace?

### 5. Cultural Appropriateness

- [ ] Register matches technical writing (not conversational or legalistic)?
- [ ] No unintended connotations?

### 6. Technical Compatibility

- [ ] Single script throughout?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: PermissionError
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
