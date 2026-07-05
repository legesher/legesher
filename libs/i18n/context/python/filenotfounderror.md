# Python Builtin: `FileNotFoundError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound)
**Python Version:** 3.3+ (PEP 3151)
**Difficulty:** MEDIUM

---

## Quick Summary

`FileNotFoundError` is the built-in exception raised when a file or directory is requested at a path where nothing exists — opening a missing file, deleting a nonexistent path, or entering a directory that isn't there. It is the `OSError` subclass corresponding to `errno` `ENOENT` ("No such file or directory") and is one of the most frequently encountered exceptions in everyday Python.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Opening a path that does not exist raises FileNotFoundError
open("no_such_file.txt")
# FileNotFoundError: [Errno 2] No such file or directory: 'no_such_file.txt'
```

**What this does:** `open()` asks the operating system for the file; the OS answers with error code `ENOENT` (errno 2), and Python raises `FileNotFoundError` carrying that code, the OS message, and the offending path in its `errno`, `strerror`, and `filename` attributes.

### Example 2: Common Pattern

```python
# Fall back to defaults when an optional file is missing
import json

def load_settings(path="settings.json"):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # no settings file yet — start with defaults

settings = load_settings()
```

**What this does:** The "optional file" pattern: try to read, and treat a missing file as a normal, expected situation rather than a crash. Catching `FileNotFoundError` specifically (instead of broad `OSError`) means a `PermissionError` or `IsADirectoryError` at the same path still surfaces loudly, as it should.

### Example 3: Edge Case

```python
# Deleting or renaming a missing path raises it too — and it can be suppressed
import contextlib
import os

os.remove("stale.lock")
# FileNotFoundError: [Errno 2] No such file or directory: 'stale.lock'

# Idiomatic "delete if present":
with contextlib.suppress(FileNotFoundError):
    os.remove("stale.lock")

# Two-path operations report which path failed via filename/filename2
try:
    os.rename("missing.txt", "renamed.txt")
except FileNotFoundError as e:
    print(e.errno)      # 2
    print(e.filename)   # 'missing.txt'
```

**What this shows:** The exception is not only about `open()` — any OS operation needing an existing path (`os.remove`, `os.rename`, `os.chdir`, `os.listdir`, ...) raises it when the path is absent. `contextlib.suppress(FileNotFoundError)` is the idiomatic "delete if present." For two-path operations, `filename` (and `filename2`) identify which side failed.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (`OSError` subclass, errno `ENOENT`)

**Similar terms in this pattern:**

1. `OSError` - The parent class; carries the errno/strerror/filename machinery this subclass inherits
2. `FileExistsError` - The mirror-image sibling: path unexpectedly present (`EEXIST`) instead of unexpectedly absent
3. `PermissionError` - Sibling subclass: path exists but access is denied (`EACCES`/`EPERM`)
4. `KeyError` - The same "requested thing is not there" concept, in the dictionary domain

**Pattern rule:** Exception classes are noun compounds ending in "Error." This one embeds a past participle ("not found"); translations should render the target language's standard "file not found" phrase — the one users already see in their localized OS dialogs — as a compact noun compound, never as a full sentence with a conjugated verb.


---

## Etymology (Brief)

**English Origin:** Latin + Germanic compound

**Root meaning:** "File" comes from Latin "filum" (thread) — documents were once strung on a wire or thread for safekeeping. "Found" is the past participle of Old English "findan" (to find, come upon). "Error" derives from Latin "errare" (to wander).

**Why Python uses this:** "File not found" is the most famous error message in computing — operating systems have printed it for decades, and every localized OS ships an established translation of it. PEP 3151 turned that exact phrase into a class name so that `except FileNotFoundError:` reads like the error message it replaces, instead of forcing programmers to memorize `errno.ENOENT`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`FileNotFoundError` is raised when an operation requires something to exist at a path and the operating system reports that nothing does. The canonical trigger is `open()` in read mode, but any path-consuming OS call can raise it: `os.remove`, `os.rename`, `os.chdir`, `os.listdir`, `os.stat`, `shutil` operations, and so on. Despite the name saying "file," a missing *directory* raises it too — the underlying OS code, `ENOENT`, literally means "No such file or directory."

As an `OSError` subclass (introduced by PEP 3151 in Python 3.3), it inherits the diagnostic attributes: `errno` (always 2/`ENOENT` — on Windows, native codes like `ERROR_FILE_NOT_FOUND` are mapped onto it, with the original preserved in `winerror`), `strerror` (the OS message), and `filename` (the path that failed). Before 3.3, code had to catch `IOError`/`OSError` and check `e.errno == errno.ENOENT`; the subclass made the common case a one-line `except`.

Two handling styles dominate real code. Where a missing file is *expected* (optional config, first run, cache miss), catch it and fall back — this is ordinary control flow, not disaster recovery. Where the file is *required*, let the exception propagate: its message already names the missing path, which is exactly the diagnostic a user needs. A related idiom, `contextlib.suppress(FileNotFoundError)`, expresses "do it if the path exists, otherwise never mind" for cleanup operations.

**Key behaviors:**

1. **Maps errno ENOENT:** The subclass corresponds to `errno` 2 (`ENOENT`). Constructing `OSError(errno.ENOENT, msg)` returns a `FileNotFoundError` instance; catching `OSError` and checking `errno` still works but is pre-3.3 style.

2. **Covers directories too:** `os.chdir("missing_dir")` and `os.listdir("missing_dir")` raise `FileNotFoundError`, not a directory-specific exception — "file" in the name follows the OS convention where "file" includes directories.

3. **Names the missing path:** The `filename` attribute (and `filename2` for two-path operations like `os.rename`) carries the path, so handlers and error messages can report exactly what was not found.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (domain "file" + negated participle "not found" + error concept)
- **Action vs State:** STATE - describes the condition "the requested path does not exist"
- **Temporal aspect:** Instantaneous - raised at the moment the OS reports ENOENT

### Recommended Form

**Primary recommendation:** Reuse the target language's **established "file not found" phrase** — the wording users have seen in their localized operating system for decades — compacted into a noun compound with the pack's standard "error" word. Do not invent a new phrasing when a canonical one exists; recognition is the entire value of this name. Keep the "file" word identical to the one used in `FileExistsError`, and the negation strategy natural to the language (negated participle, negating particle, or negation prefix).

**Forms to AVOID:**

- ❌ Conjugated-verb sentences ("TheFileWasNotFound"-style) - exception names are nouns, not narration
- ❌ "Lost/deleted file" vocabulary - the file was never necessarily there; "lost" implies it existed and vanished
- ❌ A different "file" word than `FileExistsError` uses - the sibling pair must share the root
- ❌ Bare "missing error" without "file" - loses the domain that makes the name self-explanatory

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — both content words carry risk:

- ❌ Meaning 1: "File" as a metal filing tool, or a dossier/paper folder (many languages use unrelated words for these)
- ❌ Meaning 2: "Not found" as "lost/misplaced" (implies prior existence)
- ❌ Meaning 3: "Not found" as "search returned no results" (database/web 404 sense — related but broader)
- ✅ Meaning 4: **The operating system reports that no filesystem object exists at the requested path** (errno ENOENT)

**Example:**

English "file not found" contexts:

1. "The file went missing from my desk" (physical, lost) ❌
2. "Search found no matching records" (query result) ❌
3. `open('config.json')` → the OS says nothing exists at that path ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a filesystem-level absence reported by the OS — using the computing word for "file," and a negation that does not imply the file previously existed.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `FileNotFoundError`, check these translations:**

- [ ] `OSError` - Parent class; same "error" word and family structure
- [ ] `FileExistsError` - Mirror sibling; MUST share the exact same "file" word, differing only in exists/not-found
- [ ] `IsADirectoryError` / `NotADirectoryError` - Siblings; same structural pattern
- [ ] `PermissionError` - Sibling; same "error" word and pattern
- [ ] `open` - The builtin that most often raises this; its docs will collocate with this name

**Consistency rule:**

The os_io family must read as a family. Fix the "error" word and position (from `OSError`), fix one "file" word (used here and in `FileExistsError`), fix one "directory" word (used in `IsADirectoryError`/`NotADirectoryError`), and apply them without exception.


### Functional relationships

**This term works WITH:**

1. **`open()` + `except FileNotFoundError`**: The single most common pairing in Python error handling

2. **`os` / `shutil` path operations**: `os.remove`, `os.rename`, `os.listdir`, `shutil.copy` all raise it for missing paths

**Common pairing:**

```python
import contextlib
import os

# Required file: let it propagate with a clear message
def load_data(path):
    with open(path) as f:       # missing path → FileNotFoundError
        return f.read()

# Optional file: absence is normal control flow
def load_cache(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None

# Cleanup: delete if present
with contextlib.suppress(FileNotFoundError):
    os.remove("temp.lock")

# Pre-3.3 style still seen in old code (avoid in new code)
import errno
try:
    open("config.json")
except OSError as e:
    if e.errno != errno.ENOENT:
        raise
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `FileNotFoundError`

- Every language HAS an established "file not found" phrase — the task is finding and compacting it, not inventing
- The negated participle must compress into a noun compound, which some languages resist
- "Not found" vs "lost" vs "missing" connotations need care
- Must lock the "file" root together with `FileExistsError`

**For this term:** MEDIUM

**Rationale:** The concept is universal and the localized phrase almost always exists — that pulls toward EASY. What keeps it MEDIUM is the compression problem: turning a negated verb phrase into an identifier-friendly compound has several defensible solutions per language (participle, negation prefix, "unavailable"-style adjective), and the choice must be made once, in step with `FileExistsError`, and never revisited.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Uses the COMPUTING word for "file" (not tool/dossier senses)?
- [ ] Negation states "not found at lookup," without implying the file once existed?
- [ ] Recognizable as the target language's classic "file not found" phrase?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun, not a sentence)?
- [ ] Negation strategy natural for the language (participle/particle/prefix)?
- [ ] Follows target language compound-formation rules?

### 3. Consistency

- [ ] Same "file" word as `FileExistsError`?
- [ ] Same "error" word and position as `OSError` and the rest of the pack?
- [ ] Structure parallels the other os_io subclasses?

### 4. Usability

- [ ] Short enough (identifier-usable, even with the negation)?
- [ ] Easy to type on the target language's standard keyboard?
- [ ] Recognizable at a glance in a stack trace?

### 5. Cultural Appropriateness

- [ ] Matches the phrase local users actually see in localized software?
- [ ] No unintended connotations of blame or loss?

### 6. Technical Compatibility

- [ ] Single script throughout?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: FileNotFoundError
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
