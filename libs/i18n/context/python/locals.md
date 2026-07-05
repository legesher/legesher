# Python Builtin Function: `locals` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `locals()` function returns a dictionary of the current local symbol table (local variables). It provides access to all variables defined in the current scope, useful for introspection and debugging.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# View local variables
def my_function():
    x = 10
    y = 20
    print(locals())  # {'x': 10, 'y': 20}

my_function()
```

**What this does:** `locals()` returns a dictionary containing all local variables in the current scope. Keys are variable names (strings), values are their current values.

### Example 2: Common Pattern

```python
# Track variables during execution
def calculate(a, b, c):
    result = a + b * c
    intermediate = b * c
    print("Local variables:", locals())
    # Output: {'a': 5, 'b': 3, 'c': 2, 'result': 11, 'intermediate': 6}
    return result

calculate(5, 3, 2)

# At module level, locals() == globals()
x = 100
print(locals() == globals())  # True (at module scope)
```

**What this does:** Shows `locals()` includes function parameters and all locally defined variables. At module level (outside functions), `locals()` returns the same dictionary as `globals()`.

### Example 3: Edge Case

```python
# locals() is read-only (modifications may not affect actual variables)
def test():
    x = 10
    local_dict = locals()
    local_dict['x'] = 20  # Modify dictionary
    print(x)  # Still 10 - modification doesn't affect actual variable

test()

# Useful for string formatting
def greet(name, age):
    message = "Hello, {name}! You are {age} years old."
    print(message.format(**locals()))  # Use locals as kwargs

greet("Alice", 30)

# Debug helper
def debug_point():
    var1 = "test"
    var2 = 42
    print("DEBUG:", locals())  # See all local state

debug_point()
```

**What this shows:** Modifying the dictionary returned by `locals()` doesn't change actual variables (implementation-dependent). Often used with `**locals()` to pass all local variables as keyword arguments. Useful debugging tool to inspect scope.

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Scope Access)

**Similar terms in this pattern:**

1. `globals` - Returns global symbol table (module-level variables)
2. `vars` - Returns `__dict__` of object or locals if no argument
3. `dir` - Lists names in current scope or object

**Pattern rule:** Introspection functions that access scope/namespace should use plural nouns representing the collection of items being accessed.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** "Local" from Latin "localis" (pertaining to a place), from "locus" (place). In programming, "local" means variables confined to a specific scope/place (function, block) as opposed to "global" (everywhere).

**Why Python uses this:** "Locals" (plural noun) represents the collection of all local variables. Mirrors "globals" for parallel naming. Emphasizes that these are scope-specific variables.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `locals()` function returns a dictionary representing the current local namespace. The keys are variable names (as strings) and values are their current values. In a function, this includes parameters, local variables, and any names bound in that function's scope.

Scope in Python is determined by where variables are assigned. Function parameters and variables assigned inside a function are "local" to that function. `locals()` captures this function-level namespace. At module level (outside any function), local scope equals global scope, so `locals()` returns the same as `globals()`.

The returned dictionary is a snapshot. Modifying it generally doesn't affect actual variables (CPython doesn't guarantee variable assignment from modified `locals()` dict in function scopes). It's primarily for reading/inspection, not modification. Use cases include debugging, introspection, and passing local state as keyword arguments.

**Key behaviors:**

1. **Returns dictionary:** Keys are variable names (str), values are their current values. Includes function parameters, local assignments, and loop variables within the current scope.

2. **Scope-specific:** In functions, returns only that function's locals. At module level, returns module namespace (same as `globals()`). Nested functions have their own separate local namespaces.

3. **Read-only in practice:** While you can modify the returned dictionary, changes generally don't propagate to actual variables in function scopes. This is implementation detail, but don't rely on modifying `locals()` to change variables.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Plural noun (collection of local variables)
- **Action vs State:** STATE/COLLECTION - represents the set of local variables
- **Temporal aspect:** Current state snapshot

### Recommended Form

**Primary recommendation:** Use plural form of "local" as a noun (the local variables). Should parallel translation of `globals` for consistency.

**Forms to AVOID:**

- ❌ Singular "local" - need plural to match English
- ❌ Verb form "localize" - this is a noun, not action
- ❌ "Location" - different concept

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Local residents" (people from an area)
- ❌ Meaning 2: "Local pub/restaurant" (neighborhood establishment)
- ✅ Meaning 3: **LOCAL VARIABLES** (scope-confined variables in programming)

**Example:**

English "locals" can mean:

1. "The locals were friendly" (local people) ❌
2. "Let's go to the local" (local bar) ❌
3. "`locals()` returns local variables" (programming) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: variables defined in the current local scope, as opposed to global variables.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `locals`, check these translations:**

- [ ] `globals` - Opposite/complement; MUST use parallel structure
- [ ] `vars` - Related introspection function; should feel connected
- [ ] `local` (if used in documentation) - terminology should align

**Consistency rule:**

`locals` and `globals` are complementary functions. Their translations MUST use parallel structure: if `globals` is plural adjective, `locals` should be too. Same grammatical form.


### Functional relationships

**This term works WITH:**

1. **`locals` + `globals`**: Compare scopes

```python
x = "global"

def func():
    x = "local"
    print("Local x:", locals()['x'])   # "local"
    print("Global x:", globals()['x']) # "global"

func()
```

2. **`locals` + `**kwargs`**: Pass locals as arguments

```python
def format_message(name, age, city):
    template = "{name} is {age} years old from {city}"
    return template.format(**locals())

print(format_message("Alice", 30, "NYC"))
```

**Common pairing:**

```python
# Introspection and debugging
def debug_function(a, b):
    result = a + b
    print("Locals:", locals())
    # {'a': 5, 'b': 3, 'result': 8}

debug_function(5, 3)

# Dynamic variable access
def get_var_value(var_name):
    x = 10
    y = 20
    return locals().get(var_name)

print(get_var_value('x'))  # 10

# String formatting with all locals
def report(name, age, score):
    print("Name: {name}, Age: {age}, Score: {score}".format(**locals()))

report("Bob", 25, 95)

# Module vs function scope
module_var = "module"

def show_scopes():
    func_var = "function"
    print("Are locals and globals same?", locals() == globals())  # False

print("At module level:", locals() == globals())  # True
show_scopes()
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `locals`

- "Local" has multiple meanings (people, place, scope)
- Need plural form which varies by language
- MUST parallel `globals` translation (critical)
- Some languages may need explicit "variables" qualifier

**For this term:** MEDIUM

**Rationale:** While "local" in programming is well-established, ensuring plural form and parallel structure with `globals` requires attention. The complementary relationship between these functions is essential to preserve in translation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOCAL VARIABLES concept (scope-specific)?
- [ ] Distinguished from "location" or "local people"?
- [ ] Related to scope and namespace in programming?

### 2. Linguistic Correctness

- [ ] Correct part of speech (plural noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] **CRITICAL:** Parallels `globals` translation structure?
- [ ] Uses plural form like English?
- [ ] Aligns with scope terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear relationship to "global"?

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
term: locals
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
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
