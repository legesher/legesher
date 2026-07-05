# Python Builtin: `ImportWarning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`ImportWarning` is the warning category for probable mistakes in module imports - situations where an import technically succeeds (or proceeds) but the import machinery noticed something suspicious, such as a package with malformed metadata. It subclasses `Warning`, is emitted via `warnings.warn()`, and is ignored (hidden) by default; developers enable it with filters, the `-W` flag, or Python's development mode.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A build/plugin tool warning about a suspicious import situation
import warnings

def load_plugin(name):
    module = __import__(name)
    if not hasattr(module, "PLUGIN_API"):
        warnings.warn(
            f"module {name!r} imported but defines no PLUGIN_API",
            ImportWarning,
            stacklevel=2,
        )
    return module

# The plugin loads either way - the warning flags a PROBABLE mistake,
# and under default filters it is not even printed.
```

**What this does:** The import itself works; the warning marks a situation that *smells* like a mistake (a plugin missing its expected interface). Because `ImportWarning` is ignored by default, only developers who opt in will see it - it is diagnostic plumbing, not user-facing messaging.

### Example 2: Common Pattern

```python
# Opting in to import diagnostics
import warnings

warnings.simplefilter("default", ImportWarning)   # un-hide the category

# Or without touching code:
#   python -W default::ImportWarning script.py
#   python -X dev script.py     (dev mode also displays ImportWarning)

import some_package    # any import-machinery warnings now print
```

**What this does:** Three equivalent opt-ins: a filter call in code, the `-W` command-line flag, or Python Development Mode (`-X dev`), which changes the default filters so that `ImportWarning`, `DeprecationWarning`, `PendingDeprecationWarning`, and `ResourceWarning` are displayed. Developers debugging mysterious import behavior turn these on to see what the machinery noticed.

### Example 3: Edge Case

```python
# CPython's own import system emits ImportWarning for malformed packages,
# e.g. when a module's __spec__/__package__ metadata is missing:
#
#   ImportWarning: can't resolve package from __spec__ or __package__,
#   falling back on __name__ and __path__
#
# Reproduce the mechanics explicitly:
import warnings

warnings.simplefilter("error", ImportWarning)     # promote to exception
try:
    warnings.warn("suspicious import layout", ImportWarning)
except ImportWarning as exc:
    print(f"caught: {exc}")
```

**What this shows:** The interpreter itself uses this category when import metadata is inconsistent but it can still proceed via a fallback. Note the contrast with `ImportError`: when an import actually *fails*, Python raises `ImportError` (an error, execution stops); `ImportWarning` covers imports that proceed despite something being off.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY)

**Similar terms in this pattern:**

1. `Warning` - The base class supplying the shared root
2. `ImportError` - The ERROR counterpart: the import actually failed (different root, same qualifier)
3. `RuntimeWarning` - Sibling: dubious behavior noticed at runtime
4. `SyntaxWarning` - Sibling: dubious syntax noticed at compile time

**Pattern rule:** Qualifier + shared "warning" root. The qualifier "import" must be the same word your language pack uses for the `import` keyword's concept (loading a module), so that `ImportWarning` and `ImportError` visibly describe the same domain at two severities.


---

## Etymology (Brief)

**English Origin:** Latin + Germanic

**Root meaning:** "Import" from Latin "importare," "to carry in" (in- "into" + portare "to carry"). In programming: to bring a module's names into the current program. "Warning" from Old English "warnian," to caution.

**Why Python uses this:** Python's `import` statement is the front door for all code reuse, and its machinery (finders, loaders, package metadata) can encounter conditions that are legal but probably unintended. `ImportWarning` names that channel: cautions from the import system, distinct from `ImportError`, which is the import system's hard failure.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ImportWarning` is the diagnostic channel of Python's import machinery. When the interpreter imports a module it consults metadata (`__spec__`, `__package__`, `__path__`); if that metadata is inconsistent or missing but a fallback lets the import proceed, CPython emits an `ImportWarning` rather than failing. Historically this category has flagged package-layout problems - the classic educational example being directories that look like packages but are missing pieces the machinery expects.

The category is hidden by default (`ignore::ImportWarning` is in the default filter list). The reasoning mirrors `DeprecationWarning`'s: an application's end user cannot fix a library's package layout, so surfacing these to everyone would be noise. The intended audience is developers actively diagnosing import problems - they enable the category via `warnings.simplefilter("default", ImportWarning)`, `-W default::ImportWarning`, or development mode (`-X dev`), which displays this category among others.

The essential contrast for translators is `ImportWarning` vs `ImportError`. Same domain qualifier, opposite severities: the error means the import failed and execution cannot proceed down that path; the warning means the import went through, but the machinery suspects a mistake. A translation must keep the "warning" root advisory so this contrast survives.

**Key behaviors:**

1. **Flags probable mistakes, not failures:** The import proceeds. If an import cannot proceed, Python raises `ImportError`/`ModuleNotFoundError` instead - a different class on the error side of the hierarchy.

2. **Ignored by default:** `ignore::ImportWarning` is part of the default filter list. Nothing prints unless a developer opts in with filters, `-W`, `PYTHONWARNINGS`, or `-X dev` (development mode).

3. **Emitted mainly by the interpreter and tooling:** Unlike `UserWarning`, application code rarely emits this category; it belongs to the import machinery and to tools (plugin loaders, packagers) that extend it.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (qualifier "import" + root "warning")
- **Action vs State:** STATE - names a category of advisory diagnostic
- **Temporal aspect:** Instantaneous - emitted during the import operation

### Recommended Form

**Primary recommendation:** Use the same "import" word your language pack chose for the `import` keyword, plus the family's warning root. Cross-language pairing with `ImportError` matters as much as pairing within the warning family.

**Forms to AVOID:**

- ❌ A different "import" word than the `import` keyword translation - breaks keyword/exception alignment
- ❌ Words limited to commercial importing (customs, trade goods) if your language separates that sense from "bring in"
- ❌ "Failed import" phrasings - the import did NOT fail; that is `ImportError`
- ❌ Any error/failure word for the root - execution continues

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Commercial importing (customs duties, trade goods)
- ❌ Meaning 2: "Import" as importance/significance ("a matter of great import")
- ❌ Meaning 3: A failed import (that is `ImportError`)
- ✅ Meaning 4: **A CAUTION FROM THE MODULE-IMPORT MACHINERY** - the import proceeds, but something about it is probably a mistake

**Example:**

English "import" can mean:

1. "Steel import tariffs" (trade) ❌
2. "Words of great import" (significance) ❌
3. `import missing_module` raising `ImportError` (failure - different class) ❌
4. The import machinery printing a caution about package metadata while the program continues ✅ **This is the Python meaning**

**Your translation should capture meaning #4. The family rule is decisive here because a natural error-side twin exists: `ImportError` is the failure; `ImportWarning` is the advisory. The root word must say "warning," never "error," or the two classes become indistinguishable in translation.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ImportWarning`, check these translations:**

- [ ] `import` (keyword) - the qualifier must come from the same lexical family
- [ ] `from` (keyword) - partner of `import` in import statements; conceptual neighborhood
- [ ] `Warning` - root must match exactly
- [ ] `ImportError` (when added to the pack) - same qualifier + the error root; the pair must differ only in root

**Consistency rule:**

Two alignments at once: within the warning family (shared "warning" root across all 12 categories) and across the severity pair (`ImportWarning` / `ImportError` share the "import" qualifier, differ only in root). Translate the qualifier once and reuse it in both.


### Functional relationships

**This term works WITH:**

1. **`import` statements + `ImportWarning`**: the machinery that emits it

```python
import package_with_odd_layout   # may emit ImportWarning (hidden by default)
```

2. **Filters / dev mode + `ImportWarning`**: opt-in diagnostics

```python
warnings.simplefilter("default", ImportWarning)   # or: python -X dev
```

**Common pairing:**

```python
import warnings

# Diagnosing a plugin system
warnings.simplefilter("default", ImportWarning)

def load_plugins(names):
    loaded = []
    for name in names:
        try:
            module = __import__(name)
        except ImportError as exc:            # hard failure: module absent
            print(f"skipped {name}: {exc}")
            continue
        if not hasattr(module, "register"):   # soft problem: probable mistake
            warnings.warn(
                f"{name} has no register(); is it really a plugin?",
                ImportWarning,
                stacklevel=2,
            )
        loaded.append(module)
    return loaded
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ImportWarning`

- "Import" already has an established translation in every serious language pack (it is a keyword), so the qualifier is usually predetermined
- Residual risk: languages where the natural "import" word is strongly commercial, or where the keyword was translated with a different word than the docs use
- The double alignment (warning family root + `ImportError` qualifier pair) requires a consistency check, not new invention

**For this term:** MEDIUM

**Rationale:** Mostly mechanical once two anchors exist: the `import` keyword translation supplies the qualifier, and the `Warning` brief supplies the root. The judgment call is confirming the keyword's translation also works as a noun/qualifier in the compound (some languages translate the keyword as a verb form and need its nominalization here).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "advisory from the import machinery," not "import failed"?
- [ ] Root word means "warning" (advisory, non-fatal), never "error"?
- [ ] "Import" reads as module loading, not trade/customs?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Keyword's verb form correctly nominalized if needed?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Uses the exact root chosen for `Warning`?
- [ ] Qualifier from the same lexical family as the `import` keyword translation?
- [ ] Will pair cleanly with `ImportError` (same qualifier, error root)?

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
term: ImportWarning
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
