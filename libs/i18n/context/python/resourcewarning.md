# Python Builtin: `ResourceWarning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category)
**Python Version:** 3.x+ (added in 3.2)
**Difficulty:** MEDIUM

---

## Quick Summary

`ResourceWarning` is the warning category for resource-usage problems - above all, operating-system resources like files and sockets that were opened but never explicitly closed and are being cleaned up by the garbage collector instead. It subclasses `Warning`, is ignored (hidden) by default, and is typically enabled during development via Python's development mode (`-X dev`) or a warning filter.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Run as:  python -X dev example.py
def read_first_line(path):
    f = open(path, encoding="utf-8")
    return f.readline()          # f is never closed!

line = read_first_line("data.txt")
# Later, when the garbage collector reclaims f:
#   ResourceWarning: unclosed file <_io.TextIOWrapper name='data.txt' ...>
```

**What this does:** The file object goes out of scope without `close()`. CPython's garbage collector eventually closes it during finalization and - if the category is enabled - emits `ResourceWarning` identifying the leaked object. The program's result is unaffected; the warning flags a hygiene bug that can exhaust file descriptors in bigger programs.

### Example 2: Common Pattern

```python
# The fix the warning is asking for: deterministic cleanup with `with`
def read_first_line(path):
    with open(path, encoding="utf-8") as f:    # closed on block exit
        return f.readline()                    # no ResourceWarning

# Enabling the category (it is ignored by default):
#   python -X dev script.py                    (development mode)
#   python -W default::ResourceWarning script.py
import warnings
warnings.simplefilter("default", ResourceWarning)
```

**What this does:** A `with` block closes the file deterministically, which is the idiomatic resolution for nearly every `ResourceWarning`. Because the category is in the default ignore list, developers must opt in; development mode (`-X dev`) is the standard switch and also enables other debug checks.

### Example 3: Edge Case

```python
# Finding WHERE the leaked object was created: enable tracemalloc
# Run as:  python -X dev -X tracemalloc=5 example.py
import socket

def probe():
    s = socket.socket()          # never closed
    return s.fileno()

probe()
# ResourceWarning: unclosed <socket.socket ...>
# with tracemalloc, the warning includes "Object allocated at (traceback)":
#   the exact lines that created the leaked socket
```

**What this shows:** The warning fires at garbage-collection time, which may be far from the buggy line; `-X tracemalloc` attaches the allocation traceback so the leak's origin is visible. Sockets, files, and other OS-resource wrappers all participate. Timing is not guaranteed - finalization may happen late or, at interpreter shutdown, in unusual orders - so the warning is a development aid, not a runtime contract.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY)

**Similar terms in this pattern:**

1. `Warning` - The base class supplying the shared root
2. `RuntimeWarning` - Sibling: dubious behavior noticed while running
3. `EncodingWarning` - Sibling: another code-hygiene audit, also quiet unless requested
4. `open` - The builtin that creates the most commonly leaked resource (files)

**Pattern rule:** Qualifier + shared "warning" root. The qualifier "resource" should be your language's general word for system resources (as in "system resources," "resource management") - not money, not natural resources specifically.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** "Resource" from Old French "resourdre" (to rise again, recover), ultimately Latin "resurgere" - a source one can draw on. In computing: finite assets the operating system lends a process - file descriptors, sockets, handles, memory.

**Why Python uses this:** File descriptors and sockets are borrowed from the OS and must be returned. Python 3.2 added `ResourceWarning` (see the `devmode`/GC work around that era) to make silent failures-to-return visible during development, without punishing production code where relying on GC cleanup sometimes suffices.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ResourceWarning` polices the gap between garbage collection and resource management. Python's GC reclaims *memory* automatically, and as a side effect it also finalizes objects - closing a file when its object dies. Many programs therefore "work" without ever calling `close()`. But OS resources are finite (a process may be limited to ~1024 open file descriptors), reclamation timing is unpredictable (especially on non-refcounting implementations like PyPy), and unflushed buffers can even lose data. Relying on GC for cleanup is a latent bug, and `ResourceWarning` is the tool that surfaces it.

When an object wrapping an OS resource - a file from `open()`, a `socket.socket`, and similar - is finalized without having been explicitly closed, CPython emits `ResourceWarning` naming the unclosed object. The category is ignored by default (it is in the default filter list), because end users running applications can't act on it and finalization-time warnings would alarm them. Developers enable it with development mode (`-X dev`), `-W default::ResourceWarning`, or a `filterwarnings` call in test setup; pairing with `-X tracemalloc` adds the allocation traceback that points at the leak's origin.

The fix is almost always structural: `with` blocks (context managers) for deterministic cleanup, or explicit `close()` in `finally`. Test suites often promote the category to an error so leaks fail CI. For translators, "resource" here is the OS/system-assets sense - the same word used in "system resources" in your language's OS terminology.

**Key behaviors:**

1. **Fires on finalization of unclosed resources:** Emitted when the GC finalizes an object like an unclosed file or socket - possibly long after the leak, possibly at interpreter shutdown. The object still gets closed; the warning reports that cleanup happened implicitly.

2. **Ignored by default:** `ignore::ResourceWarning` is in the default filter list. Development mode (`-X dev`), `-W`, `PYTHONWARNINGS`, or explicit filters reveal it; `-X tracemalloc` enriches it with the allocation site.

3. **Advisory about hygiene, not correctness of results:** The program's output is typically unaffected; the warning flags descriptor exhaustion risk, unpredictable timing, and possible data loss from unflushed buffers - reasons to switch to `with`/`close()`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (qualifier "resource" + root "warning")
- **Action vs State:** STATE - names a category of advisory diagnostic
- **Temporal aspect:** Deferred - emitted at finalization time, about an omission earlier

### Recommended Form

**Primary recommendation:** Your language's word for *system/computing resources* - the one used in OS documentation for "system resources" and "resource manager" - plus the family's warning root. Singular vs plural should follow whatever reads most naturally as a category name in your language (English uses singular "Resource").

**Forms to AVOID:**

- ❌ Words limited to natural resources (minerals, water) if your language separates that sense
- ❌ Words meaning funds/means/wealth - "recursos" in the financial sense, for example
- ❌ Narrowing to "file warning" - files are the most common case but sockets and other OS handles are equally covered
- ❌ Any error/failure word for the root - the resource WAS cleaned up; the program did not fail

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Natural resources (water, minerals, forests)
- ❌ Meaning 2: Financial means, funds, assets
- ❌ Meaning 3: Human resources / personnel
- ✅ Meaning 4: **OPERATING-SYSTEM RESOURCES** - finite assets a process borrows (file descriptors, sockets, handles) that must be returned by closing

**Example:**

English "resource" can mean:

1. "Renewable resource management" (natural) ❌
2. "We lack the resources to fund this" (financial) ❌
3. "Resource allocation across teams" (personnel) ❌
4. "ResourceWarning: unclosed file ..." - an OS file handle cleaned up implicitly ✅ **This is the Python meaning**

**Your translation should capture meaning #4. And the family rule is especially instructive here: this warning fires when cleanup *succeeded* - just implicitly, via the garbage collector, instead of explicitly via `close()`/`with`. Nothing failed at all. A root word meaning "error/failure" would be flatly false; the root must be your family's "warning" word.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ResourceWarning`, check these translations:**

- [ ] `Warning` - root must match exactly
- [ ] `open` - the builtin creating the most-leaked resource; docs cross-reference each other
- [ ] `with` - the keyword whose usage resolves most of these warnings; explanatory texts pair them
- [ ] `RuntimeWarning` / `EncodingWarning` - siblings; keep qualifiers distinct
- [ ] "system resources" phrasing in any OS-related docs of the pack - same "resource" word

**Consistency rule:**

Use the same "resource" word wherever the pack discusses system resources, and keep the warning root identical to the rest of the family. The conceptual trio in teaching material - `open` (acquire), `with` (release deterministically), `ResourceWarning` (you forgot) - should share vocabulary so the story reads as one narrative.


### Functional relationships

**This term works WITH:**

1. **`open()` / `socket` + `ResourceWarning`**: the acquirers of warnable resources

```python
f = open("data.txt")   # if never closed → ResourceWarning at finalization
```

2. **`with` + `ResourceWarning`**: the idiom that prevents it

```python
with open("data.txt") as f: ...   # deterministic close, no warning
```

**Common pairing:**

```python
import warnings

# Test-suite recipe: leaked resources fail the build
warnings.simplefilter("error", ResourceWarning)

def leaky():
    f = open("data.txt", encoding="utf-8")
    return f.readline()               # forgot to close

def clean():
    with open("data.txt", encoding="utf-8") as f:
        return f.readline()           # closed on exit

clean()                                # fine
# leaky() would eventually raise ResourceWarning (at finalization)
# when the GC reclaims the file object under the "error" filter.

# Development-mode equivalents (no code changes):
#   python -X dev script.py
#   python -X dev -X tracemalloc=5 script.py   (adds allocation traceback)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ResourceWarning`

- "Resource" is polysemous everywhere (natural/financial/human/system), though the system sense is well established in OS localization
- Singular-vs-plural and loanword-vs-native choices vary by language
- The concept (deterministic cleanup vs GC finalization) is subtle, but the NAME doesn't need to carry that subtlety - just the right "resource" sense

**For this term:** MEDIUM

**Rationale:** Every major language has an established "system resources" term from decades of OS localization, and that word is the correct qualifier here. The main verification is sense-selection (system, not financial/natural) plus the family-root check. The behavioral subtleties (finalization timing, dev-mode enablement) belong to documentation, not to the name.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "advisory about system-resource cleanup," not "resource failure/exhaustion"?
- [ ] Root word means "warning" (advisory, non-fatal), never "error"?
- [ ] "Resource" is the OS/system sense, not financial or natural?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Number (singular/plural) natural for a category name in the target language?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Uses the exact root chosen for `Warning`?
- [ ] Same "resource" word as any "system resources" phrasing in the pack?
- [ ] Distinct from sibling qualifiers (runtime, encoding, ...)?

### 4. Usability

- [ ] Short enough (1-3 words)?
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
term: ResourceWarning
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
