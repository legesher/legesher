# Python Builtin: `NotADirectoryError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound with negated predicate)
**Python Version:** 3.3+ (PEP 3151)
**Difficulty:** MEDIUM

---

## Quick Summary

`NotADirectoryError` is the built-in exception raised when a directory operation is applied to a path that is *not* a directory — listing a file's "contents," changing into a file, or using a file as an intermediate path component. It is the `OSError` subclass corresponding to `errno` `ENOTDIR` ("Not a directory"), and the exact opposite of `IsADirectoryError` (`EISDIR`): that one fires when a directory appears where a file was expected; this one, when something else appears where a directory was expected.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Listing a regular file as if it were a directory raises NotADirectoryError
import os

open("notes.txt", "w").close()   # create a regular file
os.listdir("notes.txt")
# NotADirectoryError: [Errno 20] Not a directory: 'notes.txt'
```

**What this does:** `os.listdir` needs a directory to enumerate; "notes.txt" is a regular file. The operating system refuses with error code `ENOTDIR` (errno 20), and Python raises `NotADirectoryError` carrying that code, the OS message "Not a directory," and the path.

### Example 2: Common Pattern

```python
# Validate a user-supplied "folder" argument the EAFP way
import os

def count_entries(folder):
    try:
        return len(os.listdir(folder))
    except NotADirectoryError:
        raise ValueError(f"{folder!r} is a file, not a folder") from None
    except FileNotFoundError:
        raise ValueError(f"{folder!r} does not exist") from None

print(count_entries("."))          # works
print(count_entries("notes.txt"))  # ValueError: 'notes.txt' is a file, not a folder
```

**What this does:** Instead of pre-checking with `os.path.isdir`, the function attempts the directory operation and converts the two specific failure kinds into a friendly message. The `NotADirectoryError` branch catches exactly the wrong-kind case, cleanly separated from the missing-path case (`FileNotFoundError`).

### Example 3: Edge Case

```python
# A file in the MIDDLE of a path also triggers it
open("config.json", "w").close()

open("config.json/nested.txt")
# NotADirectoryError: [Errno 20] Not a directory: 'config.json/nested.txt'
# (POSIX behavior; Windows may report this mid-path case as a
#  different OSError subclass, e.g. FileNotFoundError)

import errno
try:
    os.chdir("config.json")      # cd into a file
except NotADirectoryError as e:
    print(e.errno == errno.ENOTDIR)   # True
```

**What this shows:** Every intermediate component of a path must be a directory. When "config.json" — a regular file — appears where a directory is needed mid-path, the OS reports `ENOTDIR` even though the operation itself was `open`. This is the subtle trigger that surprises learners: the error is about a *component* of the path, not necessarily its last element. Platform note: the mid-path case is POSIX-typical; Windows may surface it under a different subclass.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (`OSError` subclass, errno `ENOTDIR`)

**Similar terms in this pattern:**

1. `OSError` - The parent class; carries the errno/strerror/filename machinery this subclass inherits
2. `IsADirectoryError` - The exact mirror sibling (`EISDIR`): a directory appeared where a file was expected
3. `FileNotFoundError` - Sibling subclass: nothing exists at the path (vs. the wrong KIND of thing existing here)
4. `FileExistsError` - Sibling subclass; another "the path's state contradicts the operation" error

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name embeds a negated predicate ("not a directory") — the OS message turned into an identifier. Translations must express "the path is not a directory (though one was required)" as a nominal compound, using the language's most natural negation device, and must form a recognizable minimal pair with `IsADirectoryError`.


---

## Etymology (Brief)

**English Origin:** Latin compound wrapped around a negated English clause

**Root meaning:** "Directory" comes from Latin "directorium," from "dirigere" (to guide, to direct) — in computing, the structure that directs you to files. "Not a" is plain English negation of the copular clause. "Error" derives from Latin "errare" (to wander).

**Why Python uses this:** "Not a directory" is the verbatim POSIX `ENOTDIR` message that Unix systems have printed for decades (`cd: notes.txt: Not a directory`). PEP 3151 turned the message into the class name, negation and all, so the exception reads exactly like the terminal error programmers already know — and so it visibly pairs with `IsADirectoryError`, its `EISDIR` opposite.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`NotADirectoryError` is raised when an operation that requires a *directory* is pointed at something else — almost always a regular file. Direct triggers include `os.listdir` (enumerate a directory), `os.chdir` (enter a directory), `os.scandir`, and `os.rmdir`. The OS reports `ENOTDIR` and Python raises this subclass with the offending path in `filename`.

The subtler trigger is path traversal. In a path like `config.json/nested.txt`, every component before the last must be a directory the OS can walk through. If `config.json` is a regular file, traversal stops with `ENOTDIR` — so even a plain `open()` can raise `NotADirectoryError` when a *middle* component of the path is a file. This makes the exception a frequent symptom of path-construction bugs: a variable that should have held a folder path held a file path, and something was joined onto it.

The exception is one half of a matched pair introduced by PEP 3151: `NotADirectoryError` (`ENOTDIR`) versus `IsADirectoryError` (`EISDIR`). Together they cover both directions of the same kind mismatch. Note that this exception is NOT about absence — the path component *exists*; it is just the wrong kind of object. "Directory not found" would be `FileNotFoundError`; conflating the two is the classic misreading of this name.

**Key behaviors:**

1. **Maps errno ENOTDIR:** The subclass corresponds to `errno` 20 (`ENOTDIR`, "Not a directory"). Constructing `OSError(errno.ENOTDIR, msg)` returns a `NotADirectoryError` instance.

2. **Fires on directory operations and path traversal:** `os.listdir(file)`, `os.chdir(file)`, `os.rmdir(file)` raise it directly; any operation whose path contains a file as an intermediate component can raise it during traversal (POSIX-typical behavior).

3. **The thing exists — it's the wrong kind:** Unlike `FileNotFoundError`, the path resolves to a real object; the OS objects only that the object is not a directory. The `filename` attribute names the path involved.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun with a negated predicate ("[it is] not a directory" + error)
- **Action vs State:** STATE - describes the condition "the path is not a directory (but should be)"
- **Temporal aspect:** Instantaneous - raised at the moment the OS reports ENOTDIR

### Recommended Form

**Primary recommendation:** Negate the exact form chosen for `IsADirectoryError` — same "directory" word, same structure, with the language's most natural nominal negation device. The two names must read as a designed pair: affirmation and negation of one head. And keep the negation attached to "directory," not to "found" — this error is about *kind*, not absence.

**Forms to AVOID:**

- ❌ "Directory not found" phrasings - WRONG SEMANTICS: the object exists; it is simply not a directory. That phrasing describes `FileNotFoundError`
- ❌ Generic "directory error" - loses the negation entirely and collides with the sibling
- ❌ "Folder" vocabulary where the pack standardizes on "directory" - the pair must share one root
- ❌ Double or ambiguous negation - the negation must be single and clearly scoped over "directory"

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — both the negation scope and "directory" carry risk:

- ❌ Meaning 1: "Directory not found" — the directory is missing (that is `FileNotFoundError`)
- ❌ Meaning 2: "No directory error" — the absence of any directory error (negation scoped over "error")
- ❌ Meaning 3: "Directory" as a phone book or staff list
- ✅ Meaning 4: **The path resolves to something that is not a filesystem directory, where a directory was required** (errno ENOTDIR)

**Example:**

English "not a directory" contexts:

1. "The folder you asked for doesn't exist" (absence — FileNotFoundError) ❌
2. "There were no directory errors in the scan" (negated error count) ❌
3. `os.listdir('notes.txt')` where notes.txt is a file → the OS says "Not a directory" ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the negation applies to "directory" (the object's KIND), never to "found" (its existence) and never to "error." The object is there; it just isn't a directory.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `NotADirectoryError`, check these translations:**

- [ ] `IsADirectoryError` - The mirror sibling; MUST share the exact "directory" word, differing only by affirmation/negation
- [ ] `FileNotFoundError` - MUST remain clearly distinct: that one negates existence, this one negates kind
- [ ] `OSError` - Parent class; same "error" word and family structure
- [ ] `FileExistsError` / `PermissionError` - Siblings; same structural pattern
- [ ] Any pack terms using the "directory" root (e.g. future `os` module vocabulary) - one root everywhere

**Consistency rule:**

Design this entry and `IsADirectoryError` as one decision: same directory root, matched affirmation/negation devices. Then verify the result against `FileNotFoundError` in the same language — if a reader could mistake this name for "directory not found," the negation is mis-scoped and must be reworked.


### Functional relationships

**This term works WITH:**

1. **`os.listdir` / `os.chdir` / `os.rmdir` + `except NotADirectoryError`**: The direct directory-operation triggers

2. **Path traversal in any `open`/`os` call**: A file as an intermediate path component raises it too

**Common pairing:**

```python
import os

# Direct trigger: directory operation on a file
try:
    os.chdir("notes.txt")
except NotADirectoryError:
    print("that path is a file — cannot enter it")

# Traversal trigger: file used as a path component
try:
    open("notes.txt/extra.txt")
except NotADirectoryError as e:
    print(f"path component is not a directory: {e.filename}")

# The mirror pair, side by side
try:
    open("logs")                  # logs is a directory
except IsADirectoryError:
    print("expected a file, got a directory")

try:
    os.listdir("notes.txt")       # notes.txt is a file
except NotADirectoryError:
    print("expected a directory, got a file")

# LBYL alternative
if os.path.isdir(path):
    entries = os.listdir(path)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `NotADirectoryError`

- Negated nominals are well-supported in most languages — easier than the sibling's affirmative clause
- But the negation must be scoped over "directory," never over "found"/"error"
- Must be designed together with `IsADirectoryError` as a minimal pair
- The `FileNotFoundError` confusion ("directory not found") is a real and damaging trap

**For this term:** MEDIUM

**Rationale:** Languages negate categories more readily than they nominalize affirmative clauses, so this half of the pair is genuinely easier than `IsADirectoryError` (rated HARD) — most targets have a standard "non-X" device that produces a clean compound. The remaining difficulty is relational: scoping the negation correctly, locking the shared root with the sibling, and keeping visible distance from `FileNotFoundError`.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Negation scoped over "directory" (kind), NOT over existence or "error"?
- [ ] Cannot be misread as "directory not found"?
- [ ] Uses the FILESYSTEM sense of "directory"?

### 2. Linguistic Correctness

- [ ] Negation device is the language's standard nominal negator?
- [ ] Compound formation is grammatical with the negation inside?
- [ ] Correct part of speech overall (nominal, not a sentence)?

### 3. Consistency

- [ ] EXACT same "directory" word as `IsADirectoryError`?
- [ ] Forms a natural minimal pair with the sibling's affirmative?
- [ ] Same "error" word and position as the rest of the pack?
- [ ] Verified against `FileNotFoundError` for confusability?

### 4. Usability

- [ ] Short enough to type and read in a stack trace?
- [ ] The pair is instantly distinguishable at a glance?

### 5. Cultural Appropriateness

- [ ] Negation register matches technical writing (not conversational)?
- [ ] No unintended readings of the compressed clause?

### 6. Technical Compatibility

- [ ] Single script throughout?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: NotADirectoryError
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
