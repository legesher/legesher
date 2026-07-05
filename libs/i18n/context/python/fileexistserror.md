# Python Builtin: `FileExistsError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (noun compound)
**Python Version:** 3.3+ (PEP 3151)
**Difficulty:** MEDIUM

---

## Quick Summary

`FileExistsError` is the built-in exception raised when an operation tries to *create* a file or directory at a path where one already exists — `os.mkdir` on an existing directory, `open(..., "x")` on an existing file. It is the `OSError` subclass corresponding to `errno` `EEXIST` ("File exists"), and the mirror image of `FileNotFoundError`: there, the path was unexpectedly absent; here, it is unexpectedly present.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Creating a directory that already exists raises FileExistsError
import os

os.mkdir("reports")
os.mkdir("reports")
# FileExistsError: [Errno 17] File exists: 'reports'
```

**What this does:** The second `os.mkdir` asks the operating system to create a directory at a path that is already taken; the OS answers with error code `EEXIST` (errno 17), and Python raises `FileExistsError` carrying that code, the OS message, and the path in its `errno`, `strerror`, and `filename` attributes.

### Example 2: Common Pattern

```python
# Exclusive-create mode "x": refuse to overwrite an existing file
def save_new_report(path, content):
    try:
        with open(path, "x") as f:   # "x" = create, fail if it exists
            f.write(content)
    except FileExistsError:
        print(f"{path} already exists — refusing to overwrite")

save_new_report("report.txt", "Q3 numbers")
save_new_report("report.txt", "oops")  # second call hits the except branch
```

**What this does:** Open mode `"x"` creates the file and raises `FileExistsError` if the path is already taken — the safe way to guarantee you never silently overwrite data (mode `"w"` would truncate the existing file without a word). Catching the exception turns "already exists" into a handled case.

### Example 3: Edge Case

```python
# Race-free creation, and the exist_ok escape hatch
import os

# Check-then-create is racy: another process can create the path
# between the check and the mkdir. EAFP style closes the gap:
try:
    os.mkdir("cache")
except FileExistsError:
    pass  # someone (maybe us, earlier) already created it — fine

# The same idea built in: exist_ok=True suppresses the error
os.makedirs("cache/images", exist_ok=True)  # never raises FileExistsError

# Note: on POSIX, mkdir over an existing FILE also raises FileExistsError
```

**What this shows:** The classic use of `FileExistsError` is making creation idempotent. Checking `os.path.exists()` first has a race window; catching the exception (or passing `exist_ok=True` to `os.makedirs`) is atomic. The `errno` is `EEXIST` regardless of whether the occupying object is a file or a directory.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (`OSError` subclass, errno `EEXIST`)

**Similar terms in this pattern:**

1. `OSError` - The parent class; carries the errno/strerror/filename machinery this subclass inherits
2. `FileNotFoundError` - The mirror-image sibling: path unexpectedly absent (`ENOENT`) instead of unexpectedly present
3. `PermissionError` - Sibling subclass: the OS refuses access (`EACCES`/`EPERM`)
4. `IsADirectoryError` - Sibling subclass: wrong kind of object at the path (`EISDIR`)

**Pattern rule:** Exception classes are noun compounds ending in "Error." This one embeds a present-tense predicate ("exists"); translations should render it as a compact nominal — typically with a participle/adjective meaning "existing/already present" — never as a conjugated sentence.


---

## Etymology (Brief)

**English Origin:** Latin compound

**Root meaning:** "File" comes from Latin "filum" (thread) — documents strung on a wire for safekeeping. "Exist" comes from Latin "existere" (to stand forth, to emerge, to be). "Error" derives from Latin "errare" (to wander).

**Why Python uses this:** "File exists" is the literal text of the POSIX `EEXIST` error message that operating systems have returned for decades. PEP 3151 lifted the OS message directly into a class name, so `except FileExistsError:` reads like the error it handles — no `errno.EEXIST` lookup required.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`FileExistsError` is raised when code asks the operating system to *create* something at a path that is already occupied. The two everyday triggers are `os.mkdir`/`os.makedirs` (directory already there) and `open(path, "x")` — exclusive-create mode, which exists precisely to fail rather than overwrite. Lower-level triggers include `os.symlink`, `os.link`, and `os.rename` on platforms/cases where the target must not exist.

The exception embodies a Python idiom: EAFP ("easier to ask forgiveness than permission"). Checking `os.path.exists(path)` before creating is tempting but racy — between the check and the creation, another process can claim the path. Attempting the creation and catching `FileExistsError` is atomic: the OS itself arbitrates who got there first. This is why the exception appears in well-written code not as a failure signal but as expected control flow for idempotent setup ("create the cache directory if needed").

As an `OSError` subclass (PEP 3151, Python 3.3), it inherits `errno` (17/`EEXIST`), `strerror`, and `filename`. Its semantic mirror is `FileNotFoundError`: one fires when a path you need is missing, the other when a path you want to claim is taken. Translations should preserve that mirror relationship — same "file" word, opposite predicate.

**Key behaviors:**

1. **Maps errno EEXIST:** The subclass corresponds to `errno` 17 (`EEXIST`, "File exists"). Constructing `OSError(errno.EEXIST, msg)` returns a `FileExistsError` instance.

2. **Fires on creation, not access:** Reading or writing an existing file is normal; only *exclusive creation* operations (`mkdir`, mode `"x"`, `os.symlink`, ...) raise it. The error means "you asked for a fresh path and it was taken."

3. **Suppressible where tolerated:** `os.makedirs(..., exist_ok=True)` swallows the case internally; otherwise `try/except FileExistsError: pass` is the idiomatic way to make creation idempotent without race conditions.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (domain "file" + existence predicate + error concept)
- **Action vs State:** STATE - describes the condition "the target path is already occupied"
- **Temporal aspect:** Instantaneous - raised at the moment the OS reports EEXIST

### Recommended Form

**Primary recommendation:** Reuse the target language's **established "file already exists" phrase** — the one shown by localized operating systems — compacted into a noun compound with the pack's standard "error" word. Render "exists" as a participle or adjective ("existing/present/already there"), not a conjugated verb. Keep the "file" word identical to `FileNotFoundError`'s, so the mirror pair differs only in its predicate — several languages can even make the pair a minimal contrast ("present" / "not present").

**Forms to AVOID:**

- ❌ Conjugated-verb sentences ("TheFileAlreadyExists"-style) - exception names are nouns, not narration
- ❌ Inverted semantics (a "missing file" compound) - that is `FileNotFoundError`; this error means the OPPOSITE
- ❌ Generic "creation error" - loses the specific cause (path already occupied)
- ❌ A different "file" word than `FileNotFoundError` uses - the mirror pair must share the root

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — both content words carry risk:

- ❌ Meaning 1: "File" as a metal filing tool, or a dossier/paper folder (many languages use unrelated words for these)
- ❌ Meaning 2: "Exists" in the philosophical/abstract sense (existence as a property of being)
- ❌ Meaning 3: A neutral report that a file exists (like `os.path.exists` returning `True` — no error implied)
- ✅ Meaning 4: **A creation attempt failed because the target path is already occupied** (errno EEXIST)

**Example:**

English "file exists" contexts:

1. "Does the file exist?" — a neutral query (`os.path.exists`) ❌
2. "The file exists, therefore someone created it" — inference ❌
3. `os.mkdir('reports')` when `reports` is already there → the OS refuses ✅ **This is the Python meaning**

**Your translation should capture meaning #4: existence as an OBSTACLE to creation — the "already" nuance matters, and the word must be the computing "file," shared with `FileNotFoundError`.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `FileExistsError`, check these translations:**

- [ ] `OSError` - Parent class; same "error" word and family structure
- [ ] `FileNotFoundError` - Mirror sibling; MUST share the exact same "file" word, differing only in the predicate
- [ ] `IsADirectoryError` / `NotADirectoryError` - Siblings; same structural pattern
- [ ] `PermissionError` - Sibling; same "error" word and pattern
- [ ] `open` - Mode `"x"` documentation will collocate with this name

**Consistency rule:**

The os_io family must read as a family. The "file" word fixed here and in `FileNotFoundError` must be one and the same; the existence predicate here should, where the language allows, be the direct affirmative counterpart of the negation used there ("present" / "not present").


### Functional relationships

**This term works WITH:**

1. **`open(path, "x")` + `except FileExistsError`**: Safe never-overwrite file creation

2. **`os.mkdir` / `os.makedirs`**: Directory creation; `exist_ok=True` suppresses this exact exception

**Common pairing:**

```python
import os

# Idempotent setup: create-or-accept
try:
    os.mkdir("output")
except FileExistsError:
    pass                       # already there — that's fine

# Built-in equivalent
os.makedirs("output/img", exist_ok=True)

# Never clobber user data
def write_once(path, data):
    try:
        with open(path, "x") as f:   # exclusive create
            f.write(data)
        return True
    except FileExistsError:
        return False               # caller decides what to do

# Pre-3.3 style still seen in old code (avoid in new code)
import errno
try:
    os.mkdir("output")
except OSError as e:
    if e.errno != errno.EEXIST:
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

### Why MEDIUM for `FileExistsError`

- The inversion trap: careless translation flips it into "file missing"
- "Exists" needs a participle/adjective nominalization, chosen per language
- Some languages require an "already" marker to convey obstacle-existence
- Must lock the "file" root and mirror structure with `FileNotFoundError`

**For this term:** MEDIUM

**Rationale:** Every target language has an established "already exists" dialog phrase, so raw material is abundant. The difficulty is relational: the translation must be built as one half of a mirror pair with `FileNotFoundError`, must not drift into "creation failed" genericity, and must keep the counterintuitive polarity (existence as the *problem*) unambiguous.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Polarity correct — the file's PRESENCE is the problem?
- [ ] "Already" nuance present where the language needs it?
- [ ] Uses the COMPUTING word for "file"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun with participle/adjective, not a sentence)?
- [ ] Follows target language compound-formation rules?
- [ ] Predicate form natural for the language?

### 3. Consistency

- [ ] Same "file" word as `FileNotFoundError`?
- [ ] Predicate is the affirmative counterpart of `FileNotFoundError`'s negation, where possible?
- [ ] Same "error" word and position as the rest of the pack?

### 4. Usability

- [ ] Short enough (identifier-usable)?
- [ ] Easy to type on the target language's standard keyboard?
- [ ] Instantly distinguishable from `FileNotFoundError` in a stack trace?

### 5. Cultural Appropriateness

- [ ] Matches the phrase local users see in localized software?
- [ ] No unintended connotations?

### 6. Technical Compatibility

- [ ] Single script throughout?
- [ ] Renders properly in IDEs, including RTL contexts?
- [ ] No characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: FileExistsError
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
