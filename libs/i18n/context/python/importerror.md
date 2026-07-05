# Python Builtin: `ImportError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`ImportError` is a built-in exception raised when an `import` statement fails to load a module, or when `from module import name` cannot find the requested name inside a module that does exist. It carries `.name` (the module that was being imported) and `.path` (the file, if any, that triggered the failure), and it is the parent class of `ModuleNotFoundError`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# from-import of a name that doesn't exist in the module
from math import cosine
# Raises ImportError: cannot import name 'cosine' from 'math'
# (the math module exists - the function is called 'cos', not 'cosine')
```

**What this does:** The `math` module loads fine, but it contains no name `cosine`, so the `from ... import ...` statement raises `ImportError`. This is the plain-`ImportError` case: the module was found, the requested name was not. (A missing *module* raises the subclass `ModuleNotFoundError` instead.)

### Example 2: Common Pattern

```python
# Optional dependency with a fallback
try:
    import ujson as json  # Fast third-party JSON library, if installed
except ImportError:
    import json           # Fall back to the standard library

# Feature detection at import time
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
```

**What this does:** The try/except-ImportError idiom makes dependencies optional: attempt the preferred import, and on failure fall back to an alternative or record that the feature is unavailable. Because `ModuleNotFoundError` subclasses `ImportError`, this handler catches missing modules and missing names alike.

### Example 3: Edge Case

```python
# The exception carries .name and .path attributes
try:
    import does_not_exist
except ImportError as e:
    print(e.name)  # 'does_not_exist' - the module that was being imported
    print(e.path)  # None - no file on disk triggered the failure

# ModuleNotFoundError is a subclass of ImportError
print(issubclass(ModuleNotFoundError, ImportError))  # True

# Circular imports surface as ImportError too
# a.py: from b import helper_b
# b.py: from a import helper_a
# Running a.py raises ImportError: cannot import name 'helper_a'
# from partially initialized module 'a'
```

**What this shows:** `ImportError` instances expose `.name` (the module name involved) and `.path` (the path of any file that triggered the exception), useful for diagnostics. The subclass relationship means `except ImportError:` covers `ModuleNotFoundError` as well. Circular imports - two modules importing from each other - raise `ImportError` with a "partially initialized module" message, a distinct failure mode where both modules exist.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ModuleNotFoundError` - Subclass: the module itself could not be located (Python 3.6+)
2. `AttributeError` - Related failure: `import math; math.cosine` fails with AttributeError, while `from math import cosine` fails with ImportError
3. `NameError` - Related failure for undefined names outside the import system
4. `OSError` - Underlying I/O problems that can surface during importing

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain - here, the import operation - and MUST reuse the exact root chosen for the `import` keyword.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin via French + Latin-derived)

**Root meaning:** "Import" comes from Latin "importare," "to bring in, convey" ("in-" + "portare," to carry) - originally bringing goods in from abroad, extended in programming to bringing external code into a program. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name is simply the failing operation plus "Error": the `import` statement could not do its job. Keeping the exception's name literally derived from the keyword (`import` → `ImportError`) lets programmers connect the error to the statement instantly - a connection every translation must preserve by reusing the `import` keyword's translated root.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ImportError` is raised when Python's import machinery fails to complete an import. Two everyday situations produce it. First, `from module import name` succeeds in loading `module` but finds no `name` inside it - a typo (`from math import cosine`), a version mismatch (the name exists only in a newer release of the library), or a circular import where the other module is only partially initialized. Second, the module itself cannot be located at all - since Python 3.6 that specific case raises `ModuleNotFoundError`, a subclass, so it still lands in any `except ImportError:` handler.

The exception carries structured information: `.name` holds the name of the module that was being imported, and `.path` holds the path to any file that triggered the exception (often `None` when nothing was found on disk). The message usually explains the failure well - "cannot import name 'x' from 'y'" even suggests near-miss spellings in recent Python versions.

`ImportError` is unusual among exceptions in how often it is caught *deliberately as part of normal control flow*. The `try: import fast_library / except ImportError: import fallback` idiom is standard practice for optional dependencies, platform-specific modules, and version compatibility shims. Understanding it also means knowing its boundary with `AttributeError`: after a successful `import math`, accessing `math.cosine` raises `AttributeError`; only failures *of the import statement itself* raise `ImportError`.

**Key behaviors:**

1. **Raised for both missing modules and missing names:** A module that cannot be found raises `ModuleNotFoundError` (subclass); a `from`-import of a name absent from an existing module raises plain `ImportError`. `except ImportError:` catches both.

2. **Carries `.name` and `.path`:** Diagnostic attributes identify which module was involved and which file, if any, triggered the failure. Tools and error reporters use these instead of parsing the message string.

3. **Signals circular imports:** When module A imports from module B while B is still importing from A, the second import finds a partially initialized module and raises `ImportError` naming it - a message worth recognizing, because both files exist and the fix is restructuring, not installing anything.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + failed operation: the import)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment the import statement fails

### Recommended Form

**Primary recommendation:** Use a compound noun built from the *noun form of the exact word chosen for the `import` keyword* plus the family's "error" word. The keyword→exception derivation (`import` → `ImportError`) is part of what the name teaches; if `import` is "importar," this must be "ErrorDeImportación," never a synonym like "carga" (loading).

**Forms to AVOID:**

- ❌ A different root than the `import` keyword translation ("ErrorDeCarga" - "loading error") - severs the visible link between the statement and its exception
- ❌ Generic "error" without the import domain - loses what failed
- ❌ Verb forms ("ImportarFalló" - "importing failed") - exceptions are noun compounds, not sentences

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: International trade ("import tariffs on goods")
- ❌ Meaning 2: Significance ("a matter of great import" - archaic)
- ❌ Meaning 3: Data import in applications ("import your contacts from CSV")
- ✅ Meaning 4: **MODULE-LOADING FAILURE** (the `import` statement could not load a module or find a requested name)

**Example:**

English "import" can mean:

1. "The country imports coffee" (trade) ❌ Related metaphor only
2. "News of great import" (significance) ❌
3. "Import a spreadsheet into the app" (data transfer) ❌ Related, wrong grain
4. `import math` failing raises `ImportError` ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a failure of Python's module-loading statement. Whatever word your language uses for the `import` keyword defines this meaning - the exception name simply attaches the error word to it.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ImportError`, check these translations:**

- [ ] `import` - The keyword; this exception MUST reuse its root
- [ ] `from` - The other half of `from ... import ...`, the statement that raises the missing-name case
- [ ] `ModuleNotFoundError` - Subclass; must read as a more specific version of this name
- [ ] `__import__` - The low-level function behind the statement
- [ ] `AttributeError` - The neighboring failure (`module.name` access after import); the boundary must stay clear in documentation

**Consistency rule:**

Derive, don't invent: keyword root + family error word. If `import` is "importar" and `ValueError` is "ErrorDeValor," then `ImportError` can only be "ErrorDeImportación." Additionally, `ModuleNotFoundError` must nest naturally under this name - readers should see it is the same family with an added "module not found" specificity.


### Functional relationships

**This term works WITH:**

1. **`import` + `ImportError`**: The statement and its failure mode

```python
import missing_or_broken_module  # May raise ImportError
```

2. **`try`/`except` + `ImportError`**: Optional-dependency control flow

```python
try:
    import fast_impl as impl
except ImportError:
    import slow_impl as impl
```

**Common pairing:**

```python
# Optional dependency with graceful degradation
try:
    import numpy as np
except ImportError:
    np = None

def mean(values):
    if np is not None:
        return float(np.mean(values))
    return sum(values) / len(values)

# Missing name vs missing module
try:
    from math import cosine          # ImportError (name missing)
except ImportError as e:
    print(f"import problem: {e}")

try:
    import not_installed_package     # ModuleNotFoundError (module missing)
except ImportError as e:             # Parent class catches the subclass
    print(f"module involved: {e.name}")

# Version compatibility shim
try:
    from importlib.metadata import version   # Python 3.8+
except ImportError:
    from importlib_metadata import version   # Backport package

# ImportError vs AttributeError boundary
import math
# math.cosine        -> AttributeError (module loaded; attribute access failed)
# from math import cosine -> ImportError (the import statement itself failed)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ImportError`

- The root is fixed by the already-translated `import` keyword, which removes most freedom
- Remaining choices are structural: noun form of the verb, compound order, error-word placement
- Must coordinate three ways: with `import`/`from`, with `ModuleNotFoundError`, and with the error family
- The missing-name vs missing-module split must survive in documentation phrasing

**For this term:** MEDIUM

**Rationale:** This is one of the more constrained exception names: the `import` keyword translation dictates the root, and the error family dictates the frame. The main risks are drift (choosing a synonym for the root) and the relationship to `ModuleNotFoundError`, which must read as a more specific member of the same family, not as an unrelated name.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures IMPORT-STATEMENT FAILURE (module loading / from-import name missing)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Distinguishable from data-import and trade meanings in context?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Reuses the exact root of the `import` keyword translation?
- [ ] Same error word and structure as `TypeError`, `ValueError` translations?
- [ ] `ModuleNotFoundError` translation nests naturally under this one?

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
term: ImportError
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
