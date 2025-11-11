# Python Builtin: `__import__` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`__import__()` is the low-level function that the `import` statement calls internally to dynamically import modules at runtime, rarely used directly except in advanced scenarios requiring programmatic module loading.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic dynamic import
math_module = __import__('math')
print(math_module.pi)  # Output: 3.141592653589793

# Equivalent to: import math
```

**What this does:** Dynamically imports the math module at runtime and returns the module object, allowing you to import modules when the module name is stored in a variable or determined at runtime.

### Example 2: Common Pattern

```python
# Import from package with fromlist
# __import__('package.module', fromlist=['attr'])
datetime = __import__('datetime', fromlist=['datetime'])
now = datetime.datetime.now()
print(now)

# Without fromlist, returns top-level package
os_path = __import__('os.path')  # Returns 'os' module
print(type(os_path))  # <class 'module'> (os, not os.path!)

# With fromlist, returns submodule
os_path = __import__('os.path', fromlist=[''])
print(hasattr(os_path, 'join'))  # True
```

**What this does:** Shows how `fromlist` parameter changes behavior - without it, returns top-level package; with it, returns the actual submodule requested. Critical for importing from packages correctly.

### Example 3: Edge Case

```python
# Plugin system using dynamic imports
plugin_names = ['json', 'csv', 'xml.etree.ElementTree']

plugins = {}
for name in plugin_names:
try:
# Import with proper fromlist for submodules
parts = name.split('.')
fromlist = [parts[-1]] if len(parts) > 1 else []
module = __import__(name, fromlist=fromlist)
plugins[name] = module
print(f"Loaded: {name}")
except ImportError as e:
print(f"Failed to load {name}: {e}")

# Access loaded plugins
if 'json' in plugins:
data = plugins['json'].dumps({'key': 'value'})
print(data)  # Output: {"key": "value"}
```

**What this shows:** Real-world usage in plugin systems where module names come from configuration or user input. Demonstrates error handling and the complexity of properly importing both top-level modules and nested submodules dynamically.

---

## Pattern Classification

**This term is:** LOW-LEVEL IMPORT FUNCTION

**Similar terms in this pattern:**

1. `import` - High-level import statement (keyword)
2. `importlib.import_module()` - Recommended alternative to `__import__`
3. `from` - Import specific attributes (keyword)

**Pattern rule:** Import-related terms should convey the concept of loading/bringing in external code. `__import__` is the underlying mechanism, rarely used directly.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `import` | importar | استيراد | 导入 | आयात |
| `from` | desde | من | 从 | से |
| `__import__` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Latin "importare" = to bring in

**Root meaning:** From Latin "im-" (into) + "portare" (to carry). Literally "to carry into" - bringing something from outside into the current scope.

**Why Python uses this:** Uses "import" to describe loading external modules into the program's namespace. The double underscore `__import__` marks it as a special low-level function (dunder convention) that's called by the `import` statement internally. Not meant for direct use by programmers in most cases.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`__import__()` is the function that Python's `import` statement calls under the hood. When you write `import math`, Python actually calls `__import__('math')` internally. This builtin exists to provide programmatic access to the import mechanism, enabling dynamic imports where the module name is determined at runtime.

The function is low-level and has complex semantics, especially the `fromlist` parameter which changes its return value behavior. Without `fromlist`, it returns the top-level package even when importing a submodule. With `fromlist`, it returns the actual requested submodule. This complexity is why `importlib.import_module()` is recommended instead for dynamic imports.

Most Python programmers never use `__import__` directly. It's primarily for Python itself, import hooks, and advanced scenarios like implementing custom import systems. The standard `import` statement and `importlib` module provide cleaner interfaces for normal use cases.

**Key behaviors:**

1. **Low-level import mechanism:** Called by `import` statement internally; exposes Python's import machinery but with complex parameters that are easy to misuse.
2. **fromlist complexity:** Behavior changes dramatically based on `fromlist` parameter - returns different module objects, making it error-prone for submodule imports.
3. **Rarely used directly:** Python documentation recommends using `importlib.import_module()` instead, which provides a cleaner interface without the `fromlist` gotchas.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Function name (action verb)
- **Action vs State:** ACTION - performs the import operation
- **Temporal aspect:** Instantaneous action (loads module when called)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb (same as `import`) | Should align with how `import` is translated |
| Germanic (de, nl, sv) | Infinitive verb | Import action, consistent with `import` keyword |
| Slavic (ru, pl, uk) | Infinitive verb | Import action, matches `import` |
| Arabic | Verbal noun (masdar) like `import` | Consistent with import terminology |
| Chinese | Verb form matching `import` | Should be consistent with import statement |
| Hindi | Infinitive matching `import` | Action of importing |

**Primary recommendation:** Translate exactly the same as the `import` keyword but preserve the `__` (dunder) prefix to mark it as a low-level special function. The core concept is identical - both mean "to import" - but the double underscore signals "internal/advanced."

**Forms to AVOID:**

- ❌ Different verb than `import` - creates inconsistency
- ❌ Dropping the `__` prefix - loses the dunder convention signaling
- ❌ Noun forms - this is an action (function), not a thing

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `__importar__`
- **Form:** Infinitive verb with dunder prefix
- **Why it works:** Matches translation of `import` keyword ("importar") while preserving the `__` markers that indicate it's a special low-level function

**Arabic:**

- **Translation:** `__استيراد__` (__istīrād__)
- **Form:** Verbal noun (masdar) with dunder
- **Why it works:** Uses same term as `import` keyword with double underscores, maintaining consistency and special function marking

**Chinese:**

- **Translation:** `__导入__` (__dǎorù__)
- **Form:** Verb with dunder markers
- **Why it works:** Same term as `import` (导入) with preserved underscores, clear it's the low-level version of import

**Hindi:**

- **Translation:** `__आयात__` (__āyāt__)
- **Form:** Infinitive with dunder
- **Why it works:** Matches `import` translation with special markers, consistent terminology

### ❌ Common Translation Mistakes

**Mistake 1: Using different verb than `import`**

- **Wrong:** `__cargar__` (Spanish - "load") while `import` = "importar"
- **Why wrong:** Creates inconsistency - both refer to the same concept (importing), must use same verb
- **Right:** `__importar__` (matches `import`)

**Mistake 2: Dropping the double underscores**

- **Wrong:** `importar` (same as regular import)
- **Why wrong:** Loses the dunder convention that signals this is a special low-level function
- **Right:** `__importar__` (preserves special marking)

**Mistake 3: Adding explanatory text**

- **Wrong:** `__importar_bajo_nivel__` (Spanish - "__import_low_level__")
- **Why wrong:** Function names should be concise; explanatory text belongs in documentation, not the identifier
- **Right:** `__importar__` (concise, relies on `__` to signal special nature)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO in Python context, but YES in general English

**General English meanings:**

- Import goods (trade/commerce) ❌
- Import data (general computing) ❌
- Have significance ("of great import") ❌

**Python-specific meaning:**

✅ **Load a module into the program's namespace** - This is the Python meaning

The `__import__` function has only one meaning in Python - it's the low-level function for importing modules. Your translation should match whatever term is used for the `import` statement.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `__import__`, check these translations:**

- [ ] `import` - MUST use exact same verb (this is the low-level version of import)
- [ ] `from` - Related import syntax, should use compatible preposition
- [ ] Other dunder functions like `__init__`, `__str__` - maintain dunder convention

**Consistency rule:**

`__import__` must be linguistically identical to `import` except for the double underscores. If `import` is translated as "importar" in Spanish, then `__import__` must be `__importar__`, not a different verb.

**Example:**

✅ **Consistent:**

- `import` → `importar`
- `__import__` → `__importar__`
- Same verb root ✅

❌ **Inconsistent:**

- `import` → `importar`
- `__import__` → `__cargar__` (different verb!)
- Inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **`__import__` is called by `import`**: Internal relationship
2. **`__import__` + module names**: Takes string names of modules

**Common pairing:**

```python
# import statement calls __import__ internally
import math  # Calls __import__('math') internally

# Direct usage (rare)
math = __import__('math')

# With packages
from os.path import join  # Calls __import__('os.path', fromlist=['join'])
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Technical low-level concept
- Must align perfectly with `import` translation
- Dunder naming convention must be preserved
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While the core concept is simple (same as `import`), the requirement for perfect consistency with `import` translation and preservation of Python's dunder convention makes this HIGH complexity. The term is rarely used and highly technical, requiring understanding of Python's import system internals.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Uses EXACT same verb as `import` translation?
- [ ] Preserves the `__` (double underscore) markers?
- [ ] Would Python developers recognize this as the low-level import function?

### 2. Linguistic Correctness

- [ ] Matches `import` grammatical form (infinitive, masdar, etc.)?
- [ ] Double underscores properly placed (before and after)?
- [ ] Follows target language grammar while preserving dunder convention?

### 3. Consistency

- [ ] MUST match `import` translation exactly (except for underscores)?
- [ ] Consistent with other dunder functions' naming pattern?
- [ ] Compatible with import-related terminology?

### 4. Usability

- [ ] Recognizable as the low-level version of `import`?
- [ ] Double underscores clearly visible?
- [ ] Easy to type (within reason for dunder functions)?

### 5. Cultural Appropriateness

- [ ] Uses same professional register as `import`?
- [ ] No offensive meanings?
- [ ] Respects technical conventions?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Underscores render properly in IDEs?
- [ ] No syntax highlighting issues with double underscores?

---

## Translation Output Format

**Your translation:**

```yaml
term: __import__
language: {es|ar|zh|hi}
translation: __{your_import_translation}__
form: {infinitive_verb|masdar|verb}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you used the EXACT same translation as `import` with double underscores added. This maintains consistency since both refer to the same operation, with `__import__` being the low-level implementation. The dunder markers indicate it's a special internal function.}

**Alternatives considered:**

1. `Different verb` - ❌ Rejected because MUST match `import` translation
2. `Without underscores` - ❌ Rejected because loses dunder convention
3. `{your actual alternative}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{If you're unsure how `import` is translated in your target language, you need to research that first. `__import__` cannot be translated independently - it MUST match `import`.}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
