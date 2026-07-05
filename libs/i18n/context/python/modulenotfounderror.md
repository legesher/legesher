# Python Builtin: `ModuleNotFoundError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.6+
**Difficulty:** MEDIUM

---

## Quick Summary

`ModuleNotFoundError` is the exception raised when Python cannot locate the module an `import` statement asks for - the module genuinely is not there (not installed, misspelled, or not on the search path). Introduced in Python 3.6 as a subclass of `ImportError`, it produces the message beginners see more than any other: `No module named 'x'`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Importing a module that doesn't exist anywhere on the search path
import nosuchpackage
# Raises ModuleNotFoundError: No module named 'nosuchpackage'
```

**What this does:** Python searches its module locations (`sys.path`) for `nosuchpackage`, finds nothing, and raises `ModuleNotFoundError`. This is the exact error a beginner sees after misspelling a module name or forgetting to install a package.

### Example 2: Common Pattern

```python
# Turn the raw error into an actionable message
try:
    import pandas
except ModuleNotFoundError:
    raise SystemExit("This tool needs pandas. Install it with: pip install pandas")

# Optional feature, cleanly disabled when the package is absent
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None  # Plotting features will be skipped
```

**What this does:** Applications catch `ModuleNotFoundError` around imports of third-party packages to replace the terse "No module named 'pandas'" with instructions the user can act on, or to switch off optional features when their dependency is not installed.

### Example 3: Edge Case

```python
# ModuleNotFoundError vs its parent ImportError
import missing_module        # ModuleNotFoundError - the MODULE is absent

from math import cosine      # plain ImportError - math exists,
                             # but has no name 'cosine'

# Catching the parent also catches the child
try:
    import missing_module
except ImportError:          # Catches ModuleNotFoundError too
    print("import failed")

print(issubclass(ModuleNotFoundError, ImportError))  # True

# A missing SUBmodule reports the full dotted name
import os.nonexistent
# Raises ModuleNotFoundError: No module named 'os.nonexistent';
# 'os' is not a package
```

**What this shows:** The division of labor: `ModuleNotFoundError` means the module itself could not be located; plain `ImportError` covers other import failures such as a missing name in an existing module. Because it is a subclass, every `except ImportError:` handler written before Python 3.6 still catches it. Dotted imports report which part of the path failed.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (specific subclass)

**Similar terms in this pattern:**

1. `ImportError` - Parent class: any failure of the import statement
2. `FileNotFoundError` - Structural twin: same "X not found" naming shape, for files instead of modules
3. `NameError` - Related "cannot find it" failure, for identifiers in code rather than modules on disk
4. `AttributeError` - Related failure when accessing a missing attribute on an already-imported module

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. "NotFound"-style names add a participial "not found" between the domain noun and "Error"; translations should render this as a compact "module-not-found" compound while reusing the parent's module/import vocabulary exactly.


---

## Etymology (Brief)

**English Origin:** Compound phrase (Latin + Germanic + Latin-derived)

**Root meaning:** "Module" comes from Latin "modulus," a small measure or unit - in programming, a self-contained unit of code. "Found" is the past participle of "find" (Old English "findan"); "not found" is the standard computing phrase for a failed search. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Before 3.6, every import failure was a bare `ImportError`, and programs could not reliably distinguish "the package is not installed" from "the package broke while loading." Python 3.6 split out the not-located case under a name that states the diagnosis plainly: the module was not found. The name mirrors `FileNotFoundError`, adopting the familiar "not found" idiom from file systems and HTTP 404s.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ModuleNotFoundError` is raised when the import system finishes searching and concludes the requested module does not exist in any location it knows about. Python walks the finders on `sys.meta_path`, checking `sys.path` locations (the script's directory, installed packages, the standard library); if no finder can locate the module, the import fails with `No module named 'x'`. The same exception is raised in one subtle extra case: when `sys.modules` contains `None` for that name, which marks a module as deliberately unavailable.

For beginners, this is the single most-encountered exception message in Python, and its causes are almost always mundane: the package is not installed (`pip install` was never run, or ran against a different interpreter or virtual environment than the one executing the script), the module name is misspelled, the install name differs from the import name (`pip install Pillow`, but `import PIL`), or a local file shadows/moves the expected path. The message names exactly which module - and for dotted imports, which segment of the path - could not be found.

The class exists to make error handling precise. As a subclass of `ImportError` it changes nothing for old code (`except ImportError:` still catches it), but new code can distinguish "genuinely not there - tell the user to install it" from other import failures such as a missing name inside an existing module or a circular import, which continue to raise plain `ImportError`. When translating documentation, keep this parent-child relationship legible: `ModuleNotFoundError` is the *more specific* diagnosis within the import-error family.

**Key behaviors:**

1. **Raised only when the module cannot be located:** Search exhausted, nothing found (or the module is marked `None` in `sys.modules`). Failures *inside* a found module - errors while executing it, or a `from`-import of a missing name - raise other exceptions.

2. **Subclass of `ImportError` (since 3.6):** `except ImportError:` catches it; `except ModuleNotFoundError:` catches only the not-located case. `.name` holds the module name that was not found.

3. **Reports the failing segment of dotted imports:** `import package.missing_sub` names the full dotted path and explains which parent made the resolution fail, which is essential for debugging package layouts.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (domain noun + negated participle + error type)
- **Action vs State:** STATE - describes the outcome of a failed search, not an action
- **Temporal aspect:** Instantaneous - occurs when the import search is exhausted

### Recommended Form

**Primary recommendation:** Build a three-part compound: [module word] + [your language's natural "not found / not present" participle] + [family error word]. The module word must be whatever your language's `import`/module documentation already uses, and the whole name must visibly extend the `ImportError` translation - a reader should see "same family, more specific."

**Forms to AVOID:**

- ❌ A module word different from the one in `ImportError`/import documentation - breaks the parent-child relationship
- ❌ Dropping "not found" ("ErrorDeMódulo" - "module error") - collapses this back into a generic import failure and loses the diagnosis
- ❌ Full sentences ("ErrorElMóduloNoPudoSerEncontrado") - exception names are compact identifiers, not messages

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A course module (unit of a curriculum)
- ❌ Meaning 2: A hardware or furniture module (modular shelf, RAM module, lunar module)
- ❌ Meaning 3: A generic "component" of any system
- ✅ Meaning 4: **A PYTHON CODE MODULE** - a file (or package) of Python code that `import` loads

**Example:**

English "module" can mean:

1. "Complete module 3 of the course" (education) ❌
2. "The lunar module landed" (hardware) ❌
3. "A modular sofa" (furniture) ❌
4. `import requests` - `requests` is a module Python must locate ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an importable unit of Python code. And "not found" means the search genuinely came up empty - the module is absent from every location Python checked, usually because it was never installed or the name is misspelled. It does NOT mean the module is broken, corrupt, or failed while running.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ModuleNotFoundError`, check these translations:**

- [ ] `ImportError` - Parent class; this name must visibly extend it (same module/import vocabulary, same error word)
- [ ] `import` - The keyword whose failure this reports
- [ ] `from` - The statement's other half; `from x import y` with missing `x` raises this class
- [ ] `FileNotFoundError` - Structural twin; use the same "not found" participle in both
- [ ] `NameError` - The neighboring "cannot find it" error for identifiers; keep the boundary clear in documentation

**Consistency rule:**

Subclass names must read as "parent + added specificity." If `ImportError` is "ErrorDeImportación," this class keeps the family's error word and the import ecosystem's module word, adding only the "not found" diagnosis. The "not found" phrase itself should be identical to the one used in `FileNotFoundError` so the idiom is learned once.


### Functional relationships

**This term works WITH:**

1. **`import` + `ModuleNotFoundError`**: The statement and its most common failure

```python
import package_that_is_not_installed  # ModuleNotFoundError
```

2. **`except ImportError` + `ModuleNotFoundError`**: Parent handlers catch the child

```python
try:
    import optional_dep
except ImportError:      # Also catches ModuleNotFoundError
    optional_dep = None
```

**Common pairing:**

```python
import sys

# The beginner experience, made helpful
try:
    import requests
except ModuleNotFoundError:
    sys.exit(
        "Missing dependency 'requests'.\n"
        "Install it with:  python -m pip install requests"
    )

# Distinguishing the two import failures
def try_import(module_name):
    try:
        __import__(module_name)
    except ModuleNotFoundError as e:
        return f"not installed: {e.name}"
    except ImportError as e:
        return f"found but failed to import: {e}"
    return "ok"

# Environment debugging: which interpreter, which search path?
try:
    import mypackage
except ModuleNotFoundError:
    print(f"interpreter: {sys.executable}")
    print(f"search path: {sys.path}")
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

### Why MEDIUM for `ModuleNotFoundError`

- Three-part compound (module + not-found + error) is longer than the usual two-part exception name
- "Module" is a loanword in many languages; the choice must match existing import documentation
- The "not found" participle must be natural, compact, and shared with `FileNotFoundError`
- Tight consistency constraints with the parent `ImportError`

**For this term:** MEDIUM

**Rationale:** Every component translates readily - "module," "not found," and "error" are all established technical vocabulary - but assembling them into a compact identifier tests each language's compounding tolerance. This is also the error message beginners meet first, so clarity here has outsized pedagogical value: a learner should be able to read the translated name and immediately think "I need to install or correctly name that module."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MODULE COULD NOT BE LOCATED (not "module is broken" or "import crashed")?
- [ ] "Not found" component present and natural?
- [ ] Would a beginner connect this name to "No module named 'x'"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun with participle, not a sentence)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Extends the `ImportError` translation (same error word, same import/module vocabulary)?
- [ ] Same "not found" idiom as `FileNotFoundError`?
- [ ] Module word matches `import` documentation?

### 4. Usability

- [ ] As short as the three-part meaning allows (aim for 3 words / one compound)?
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
term: ModuleNotFoundError
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
