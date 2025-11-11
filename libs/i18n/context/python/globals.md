# Python Builtin Function: `globals` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `globals()` function returns a dictionary of the current global symbol table (module-level variables). It provides access to all globally-scoped variables, useful for introspection, debugging, and dynamic variable access.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# View global variables
x = 10
y = 20

print(globals()['x'])  # 10
print('y' in globals())  # True
```

**What this does:** `globals()` returns a dictionary containing all global (module-level) variables. Keys are variable names (strings), values are their current values. Includes built-in names and imported modules.

### Example 2: Common Pattern

```python
# Global vs local scope
global_var = "I'm global"

def my_function():
    local_var = "I'm local"
    print("global_var in globals():", 'global_var' in globals())  # True
    print("local_var in globals():", 'local_var' in globals())    # False
    print("local_var in locals():", 'local_var' in locals())      # True

my_function()

# At module level, globals() == locals()
print(globals() == locals())  # True (at module scope)
```

**What this does:** Shows difference between global and local scope. `globals()` contains module-level variables accessible everywhere. Inside functions, `locals()` and `globals()` differ.

### Example 3: Edge Case

```python
# Dynamic variable access
variable_name = "x"
globals()[variable_name] = 100
print(x)  # 100 - modification affects actual variable!

# Unlike locals(), globals() is read-write
globals()['new_var'] = "dynamically created"
print(new_var)  # "dynamically created"

# Access imported modules
import math
print('math' in globals())  # True
print(globals()['math'].pi)  # 3.14159...

# Useful for plugins/dynamic loading
def load_plugin(plugin_name, plugin_code):
    exec(plugin_code, globals())  # Execute in global namespace
    return globals()[plugin_name]

plugin_code = "def my_plugin(): return 'Hello from plugin'"
load_plugin('my_plugin', plugin_code)
print(my_plugin())  # Works! Function added to globals
```

**What this shows:** Unlike `locals()`, modifying `globals()` dictionary DOES affect actual variables. Used for dynamic variable creation/access. Contains imported modules. Can execute code in global namespace with `exec()`.

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Scope Access)

**Similar terms in this pattern:**

1. `locals` - Returns local symbol table (function-level variables)
2. `vars` - Returns `__dict__` of object or locals if no argument
3. `dir` - Lists names in current scope or object

**Pattern rule:** Introspection functions that access scope/namespace should use plural nouns representing the collection of items being accessed.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `locals` | locales | محلية | 局部变量 | लोकल्स |
| `vars` | variables | متغيرات | 变量 | वेरिएबल्स |
| `globals` | **globales** | **عمومية** | **全局变量** | **ग्लोबल्स** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** "Global" from Latin "globus" (sphere, ball), extended to mean "worldwide, universal." In programming, "global" means variables accessible from anywhere in the module (entire scope), as opposed to "local" (limited scope).

**Why Python uses this:** "Globals" (plural noun) represents the collection of all global variables. Mirrors "locals" for parallel naming. Emphasizes module-wide accessibility.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `globals()` function returns a dictionary representing the module's global namespace. Keys are variable names (strings), values are their current values. This includes module-level variables, imported modules, functions defined at module level, and built-in names.

Global scope in Python means module level - variables assigned at the top level of a file, outside any function or class. These are accessible from anywhere in the module (hence "global"). `globals()` provides direct access to this namespace as a dictionary.

Unlike `locals()`, the dictionary returned by `globals()` is "live" - modifying it DOES affect actual global variables. You can add, change, or delete global variables by manipulating this dictionary. This makes `globals()` powerful for metaprogramming, dynamic loading, and debugging.

**Key behaviors:**

1. **Returns module namespace:** Contains all module-level names: variables, functions, classes, imported modules. Also includes `__name__`, `__file__`, `__doc__` and other module attributes.

2. **Read-write dictionary:** Modifying `globals()` dictionary affects actual variables. `globals()['x'] = 10` creates/updates global variable `x`. This differs from `locals()` which is read-only in function scopes.

3. **Same everywhere in module:** Unlike `locals()` which changes based on scope, `globals()` returns the same dictionary everywhere within a module. At module level, `globals() == locals()`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Plural noun (collection of global variables)
- **Action vs State:** STATE/COLLECTION - represents the set of global variables
- **Temporal aspect:** Current state (live/mutable)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Plural adjective as noun | "globales", "globaux" - global ones |
| Germanic (de, nl, sv) | Plural adjective as noun | "globale", "globalen" - global ones |
| Slavic (ru, pl, uk) | Plural adjective as noun | "глобальные", "globalne" - global ones |
| Arabic | Plural adjective | "عمومية" (public/global ones) |
| Chinese | Compound noun | "全局变量" - global variables |
| Hindi | Loanword plural | "ग्लोबल्स" - globals |

**Primary recommendation:** Use plural form of "global" as a noun (the global variables). Should parallel translation of `locals` for consistency.

**Forms to AVOID:**

- ❌ Singular "global" - need plural to match English
- ❌ Verb form "globalize" - this is a noun, not action
- ❌ "Globe" or "world" - different concept

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `globales`
- **Form:** Plural adjective as noun
- **Why it works:** "Globales" means "global ones" (variables understood from context). Parallel to "locales" for `locals`. Natural and clear.

**Arabic:**

- **Translation:** `عمومية` ('umūmīya) or `كلّية` (kullīya)
- **Form:** Plural adjective
- **Why it works:** "عمومية" means "public/general ones" (commonly used for globals). Parallels translation of `locals`. Standard technical term.

**Chinese:**

- **Translation:** `全局变量` (quán jú biàn liàng)
- **Form:** Compound noun
- **Why it works:** 全局 (global/whole scope) + 变量 (variables). Clear and explicit. Standard term in Chinese programming, parallels `locals` translation.

**Hindi:**

- **Translation:** `वैश्विक` (vaishvik) or `ग्लोबल्स` (globals)
- **Form:** Adjective plural or loanword
- **Why it works:** "वैश्विक" means global/worldwide. "ग्लोबल्स" is common transliteration. Either works, should match `locals` style.

### ❌ Common Translation Mistakes

**Mistake 1: Using singular form**

- **Wrong:** `global` (Spanish - singular)
- **Why wrong:** English uses plural "globals" to indicate collection. Should maintain plural in translation.
- **Right:** `globales` (plural)

**Mistake 2: Inconsistent with locals**

- **Wrong:** Using "globales" when `locals` translated as "variables_locales"
- **Why wrong:** `locals` and `globals` are parallel functions; translations must mirror each other's structure.
- **Right:** Match the pattern used for `locals`

**Mistake 3: Using "globe" or "world"**

- **Wrong:** `mundo` (Spanish - "world")
- **Why wrong:** "Global" in programming means module-wide scope, not geographical world.
- **Right:** `globales` (global variables)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Worldwide, international" (geographical/political)
- ❌ Meaning 2: "Global warming" (climate context)
- ✅ Meaning 3: **GLOBAL VARIABLES** (module-wide scope in programming)

**Example:**

English "globals" can mean:

1. "Think globally" (worldwide perspective) ❌
2. "Global issues" (international problems) ❌
3. "`globals()` returns global variables" (programming) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: variables accessible throughout the entire module scope, as opposed to local (function-level) variables.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `globals`, check these translations:**

- [ ] `locals` - Opposite/complement; MUST use parallel structure
- [ ] `global` (keyword) - Related concept; terminology should align
- [ ] `vars` - Related introspection function; should feel connected

**Consistency rule:**

`globals` and `locals` are complementary functions. Their translations MUST use parallel structure: if `locals` is plural adjective, `globals` should be too. Same grammatical form. This is CRITICAL.

**Example:**

✅ **Consistent:**
Spanish: `globales`/`locales` (both plural adjectives)

❌ **Inconsistent:**
Spanish: `variable_global`/`locales` (different structures)

### Functional relationships

**This term works WITH:**

1. **`globals` + `locals`**: Compare scopes
```python
x = "global"

def func():
    x = "local"
    print("Global x:", globals()['x'])  # "global"
    print("Local x:", locals()['x'])    # "local"

func()
```

2. **`globals` + dynamic access**: Create/modify variables
```python
# Create variable dynamically
globals()['dynamic_var'] = "created at runtime"
print(dynamic_var)  # Works!

# Access variable by name string
var_name = "x"
print(globals()[var_name])
```

**Common pairing:**

```python
# Introspection and debugging
x = 10
y = 20

print("Global variables:", globals().keys())
print("Value of x:", globals()['x'])

# Dynamic variable modification
globals()['z'] = 30
print(z)  # 30 - actually created the variable

# Access imported modules
import math
print(globals()['math'].pi)  # 3.14159...

# Execute code in global scope
code = "result = 2 + 2"
exec(code, globals())
print(result)  # 4

# Plugin/extension system
def register_plugin(name, func):
    globals()[name] = func

register_plugin('my_plugin', lambda: "Hello!")
print(my_plugin())  # "Hello!"

# Difference from locals
def show_difference():
    local_var = "local"
    print("locals has local_var:", 'local_var' in locals())   # True
    print("globals has local_var:", 'local_var' in globals()) # False

show_difference()

# At module level, they're the same
print("At module level:", globals() == locals())  # True
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `globals`:

- "Global" has multiple meanings (worldwide, scope)
- Need plural form which varies by language
- MUST parallel `locals` translation (CRITICAL)
- Some languages may need explicit "variables" qualifier

**For this term:** MEDIUM

**Rationale:** While "global" in programming is well-established, ensuring plural form and parallel structure with `locals` requires attention. The complementary relationship is essential. "Global" in other contexts (worldwide) creates potential ambiguity.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures GLOBAL VARIABLES concept (module-wide scope)?
- [ ] Distinguished from "worldwide" or geographical meaning?
- [ ] Related to scope and namespace in programming?

### 2. Linguistic Correctness

- [ ] Correct part of speech (plural noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] **CRITICAL:** Parallels `locals` translation structure?
- [ ] Uses plural form like English?
- [ ] Aligns with scope terminology in target language?
- [ ] Matches `global` keyword translation if applicable?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear relationship to "local"?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: globals
language: es
translation: globales
form: plural adjective as noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "globales" (plural of "global") naturally represents global variables. Parallels "locales" for `locals()`, maintaining the local/global distinction. Clear and standard in Spanish programming contexts.

**Alternatives considered:**

1. `variables_globales` - More explicit but longer; "globales" sufficient
2. `global` - Singular form; should be plural
3. `mundial` - Means "worldwide"; wrong context (geographical not scope)

**If confidence is not HIGH, explain:**

N/A - "Global" is standard programming term. Main consideration is ensuring parallel structure with `locals` translation, which is critical.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
