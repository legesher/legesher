# Python Builtin: `IsADirectoryError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound with embedded predicate)
**Python Version:** 3.3+ (PEP 3151)
**Difficulty:** HARD

---

## Quick Summary

`IsADirectoryError` is the built-in exception raised when a file operation is applied to a path that turns out to be a directory — most commonly `open()` on a directory path. It is the `OSError` subclass corresponding to `errno` `EISDIR` ("Is a directory"): the operation expected a regular file, and the operating system objects that the path *is a directory* instead. Its exact opposite is `NotADirectoryError` (`ENOTDIR`).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Opening a directory as if it were a file raises IsADirectoryError
import os

os.mkdir("logs")
open("logs")
# IsADirectoryError: [Errno 21] Is a directory: 'logs'
# (POSIX behavior; on Windows this case raises PermissionError instead)
```

**What this does:** `open()` reads regular files; "logs" is a directory. The operating system refuses with error code `EISDIR` (errno 21), and Python raises `IsADirectoryError` carrying that code, the OS message "Is a directory," and the path. On Windows, the OS reports this particular refusal as an access error, so Python raises `PermissionError` there instead.

### Example 2: Common Pattern

```python
# Process every file in a folder, skipping subdirectories
import os

def read_all(folder):
    contents = {}
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        try:
            with open(path) as f:
                contents[name] = f.read()
        except IsADirectoryError:
            continue        # it's a subdirectory — skip it
    return contents
```

**What this does:** `os.listdir` returns files and directories mixed together. Attempting `open()` on each entry and catching `IsADirectoryError` for the directories is an EAFP alternative to checking `os.path.isfile()` first — the exception is expected control flow, not a failure. (Portable code often prefers the `isfile` check because of the Windows difference noted above.)

### Example 3: Edge Case

```python
# Writing is also blocked, and platforms disagree on os.remove
import errno

try:
    open("logs", "w")     # try to overwrite a directory with a file
except IsADirectoryError as e:
    print(e.errno == errno.EISDIR)   # True
    print(e.strerror)                # 'Is a directory'

# os.remove("logs") on a directory:
#   Linux  → IsADirectoryError  (EISDIR)
#   macOS  → PermissionError    (EPERM)  — POSIX allows either code
# Use os.rmdir / shutil.rmtree for directories instead.
```

**What this shows:** Write mode hits the same wall — a directory cannot be truncated into a file. The `os.remove` case shows why this family maps errno codes rather than operations: the same logical mistake yields `EISDIR` on Linux but `EPERM` on macOS, so the raised subclass differs by platform. Portable code catches `OSError` when it must handle both.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (`OSError` subclass, errno `EISDIR`)

**Similar terms in this pattern:**

1. `OSError` - The parent class; carries the errno/strerror/filename machinery this subclass inherits
2. `NotADirectoryError` - The exact mirror sibling (`ENOTDIR`): expected a directory, got something else
3. `FileNotFoundError` - Sibling subclass: the path is absent rather than of the wrong kind
4. `PermissionError` - Sibling subclass; also what Windows raises for this situation's most common trigger

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is unusual: it embeds a whole predicate ("is a directory") — the OS message turned into an identifier. Translations must compress "the path is a directory (when a file was expected)" into a nominal compound, and must form a recognizable minimal pair with `NotADirectoryError`.


---

## Etymology (Brief)

**English Origin:** Latin compound wrapped around an English copular clause

**Root meaning:** "Directory" comes from Latin "directorium," from "dirigere" (to guide, to direct) — originally a book that directs you to names and addresses; in computing, the structure that directs you to files. "Is a" is the plain English copula. "Error" derives from Latin "errare" (to wander).

**Why Python uses this:** "Is a directory" is the verbatim POSIX `EISDIR` message that Unix systems have printed for decades. PEP 3151 turned the message into the class name, clause and all — which is why this identifier, uniquely in the family, reads as a sentence fragment. The name optimizes for recognition by programmers who have seen `cat: logs: Is a directory` in a terminal.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`IsADirectoryError` is raised when an operation that needs a *regular file* is pointed at a *directory*. The canonical trigger is `open()` — reading or writing a directory path is meaningless, so the OS refuses with `EISDIR` and Python raises this subclass. Other triggers include `os.unlink`/`os.remove` on a directory (on Linux) and any lower-level call that passes a directory where a file descriptor for regular data is required.

The exception is one half of a matched pair introduced by PEP 3151. `IsADirectoryError` (`EISDIR`) fires when you treat a directory as a file; `NotADirectoryError` (`ENOTDIR`) fires when you treat a file as a directory. Together they cover both directions of the same category mistake: filesystem objects have kinds, and the operation must match the kind. Keeping the pair's names parallel — in English and in every translation — is what makes the two errors instantly tellable apart in a stack trace.

Practically, this exception often appears while iterating mixed directory listings (skip subdirectories), or as the symptom of a path-construction bug (a variable held `"data"` when it should have held `"data/values.csv"`). One portability caveat: the mapping from mistake to errno is looser than the mapping from errno to class. Windows reports opening a directory as a permission problem (`PermissionError`), and macOS reports unlinking a directory as `EPERM` — so cross-platform code treats this subclass as the POSIX-typical, not universal, spelling of the mistake.

**Key behaviors:**

1. **Maps errno EISDIR:** The subclass corresponds to `errno` 21 (`EISDIR`, "Is a directory"). Constructing `OSError(errno.EISDIR, msg)` returns an `IsADirectoryError` instance.

2. **Fires on file operations, not directory operations:** `open("logs")` raises it; `os.listdir("logs")` succeeds. The error condition is a *mismatch* — file-expecting operation, directory-shaped argument.

3. **Platform variance at the edges:** The common `open()`-on-directory trigger raises `PermissionError` on Windows, and `os.remove()`-on-directory raises `PermissionError` (EPERM) on macOS. Only the errno→class mapping is guaranteed; which errno the OS picks can vary.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun with an embedded copular predicate ("[it] is a directory" + error)
- **Action vs State:** STATE - describes the condition "the path is a directory (but should not be)"
- **Temporal aspect:** Instantaneous - raised at the moment the OS reports EISDIR

### Recommended Form

**Primary recommendation:** Preserve the predicate. The whole meaning of this name lives in the tiny copula: not "directory error" (any problem with a directory) but "**is** a directory" (the path unexpectedly turned out to be one). Build the compound from the target language's localized `EISDIR` message where one exists — many OS translations render "Is a directory" natively — and keep the "directory" word identical to `NotADirectoryError`'s, so the two names form a visible minimal pair: affirmation vs. negation of the same head.

**Forms to AVOID:**

- ❌ Generic "directory error" - loses the predicate; reads as any directory-related failure and destroys the contrast with `NotADirectoryError`
- ❌ "Folder" vocabulary where the pack standardizes on "directory" - the family root must be one word
- ❌ Full narrative sentences ("ThePathIsADirectory"-style) - too long; compress to the minimal predicate + error
- ❌ Describing the fix ("UseADirectoryFunction") - names state conditions, not advice

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — "directory" is the risky word:

- ❌ Meaning 1: A phone/address directory (a book or list of names)
- ❌ Meaning 2: An organizational directory (staff directory, business directory)
- ❌ Meaning 3: A generic "error involving a directory" (any failure near a folder)
- ✅ Meaning 4: **The path refers to a filesystem directory when the operation required a regular file** (errno EISDIR)

**Example:**

English "directory" contexts:

1. "Look her up in the phone directory" (list of names) ❌
2. "The company directory lists all employees" (organizational) ❌
3. `open('logs')` where `logs` is a folder → the OS says "Is a directory" ✅ **This is the Python meaning**

**Your translation should capture meaning #4 — the filesystem sense of "directory," with the copular predicate intact: the path IS one, and that is precisely the problem. The affirmative here and the negation in `NotADirectoryError` must read as two halves of one contrast.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `IsADirectoryError`, check these translations:**

- [ ] `NotADirectoryError` - The mirror sibling; MUST share the exact "directory" word and differ only by affirmation/negation
- [ ] `OSError` - Parent class; same "error" word and family structure
- [ ] `FileNotFoundError` / `FileExistsError` - Siblings; same structural pattern
- [ ] `PermissionError` - Sibling; also the Windows-side surface of this trigger — the two must not blur together
- [ ] `open` - The builtin whose documentation collocates with this name

**Consistency rule:**

Fix one "directory" word for the whole pack and use it in both halves of the pair. The affirmation/negation devices should be the language's most natural minimal contrast (affirmative copula vs. its negated form) so that the pair reads as opposites at a glance.


### Functional relationships

**This term works WITH:**

1. **`open()` + `except IsADirectoryError`**: The canonical trigger and its handler

2. **`os.path.isfile` / `os.path.isdir`**: The LBYL alternatives that avoid raising it

**Common pairing:**

```python
import os

# EAFP: try as file, fall back if it's a directory
def line_count(path):
    try:
        with open(path) as f:
            return sum(1 for _ in f)
    except IsADirectoryError:
        # sum the files inside instead
        return sum(
            line_count(os.path.join(path, name))
            for name in os.listdir(path)
        )

# LBYL: check the kind first (more portable across platforms)
for name in os.listdir("."):
    if os.path.isfile(name):
        process(name)

# The mirror pair in one place
try:
    open("logs")                  # logs is a directory
except IsADirectoryError:
    print("expected a file, got a directory")

try:
    os.listdir("notes.txt")       # notes.txt is a file
except NotADirectoryError:
    print("expected a directory, got a file")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `IsADirectoryError`

- The English name embeds a copular clause — most languages resist clause-shaped identifiers
- Dropping the copula (the easy way out) silently destroys the meaning and the sibling contrast
- The affirmative/negative pair must be designed together, as one decision
- Word order of copulas varies across languages (verb-final, pronoun-copula, ...), stressing compound formation

**For this term:** HARD

**Rationale:** This is the one name in the os_io family that is not a plain noun compound in English — it is a sentence fragment promoted to an identifier. Each language needs a deliberate, reviewed decision on how to nominalize "is a directory" without collapsing into generic "directory error," and that decision is only correct if it simultaneously produces a natural negated twin for `NotADirectoryError`. Native-speaker review of the pair is strongly recommended before finalization.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Uses the FILESYSTEM sense of "directory" (not phone book or staff list)?
- [ ] The copular predicate ("is a") survives in some form?
- [ ] Cannot be misread as a generic "directory-related error"?

### 2. Linguistic Correctness

- [ ] The embedded predicate follows the language's word order?
- [ ] Compound formation is grammatical, even with the copula inside?
- [ ] Correct part of speech overall (nominal, not a full sentence)?

### 3. Consistency

- [ ] EXACT same "directory" word as `NotADirectoryError`?
- [ ] Affirmation here and negation there form a natural minimal pair?
- [ ] Same "error" word and position as the rest of the pack?

### 4. Usability

- [ ] Short enough to type and read in a stack trace?
- [ ] The pair is instantly distinguishable at a glance?

### 5. Cultural Appropriateness

- [ ] Register matches technical writing?
- [ ] No unintended readings of the compressed clause?

### 6. Technical Compatibility

- [ ] Single script throughout?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: IsADirectoryError
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
