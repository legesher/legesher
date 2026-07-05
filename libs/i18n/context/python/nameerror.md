# Python Builtin: `NameError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`NameError` is a built-in exception raised when attempting to use a variable, function, or class name that hasn't been defined in the current scope. It signals that Python cannot find the name you're trying to reference, typically due to typos, incorrect scope, or using a name before it's defined.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Using undefined variable raises NameError
print(unknown_variable)  # Raises NameError: name 'unknown_variable' is not defined
```

**What this does:** Attempting to use a variable that hasn't been defined raises a `NameError` exception. The error message shows which name was not found.

### Example 2: Common Pattern

```python
# NameError due to typo
message = "Hello"
print(mesage)  # Raises NameError: name 'mesage' is not defined (typo in variable name)

# NameError due to using variable before definition
print(result)
result = 42  # Raises NameError: name 'result' is not defined

# NameError with function call
greet()  # Raises NameError: name 'greet' is not defined

def greet():
    print("Hello")

# Catching NameError
try:
    print(undefined_var)
except NameError:
    print("Variable not defined, using default")
    undefined_var = 0
```

**What this does:** `NameError` commonly occurs from typos in variable names, using variables before they're defined, or calling functions before they're declared. `try-except` blocks can catch `NameError` to handle undefined names gracefully.

### Example 3: Edge Case

```python
# NameError with scope issues
def my_function():
    local_var = 10

my_function()
print(local_var)  # Raises NameError: name 'local_var' is not defined
# (local_var only exists inside function scope)

# NameError with deleted names
x = 5
del x
print(x)  # Raises NameError: name 'x' is not defined

# NameError vs AttributeError
import math
print(math.sqrt(4))  # Works fine
print(math.squrt(4))  # Raises AttributeError: module 'math' has no attribute 'squrt'
print(maht.sqrt(4))  # Raises NameError: name 'maht' is not defined

# NameError in comprehensions
result = [x for x in range(10)]
print(x)  # Raises NameError in Python 3 (x is local to comprehension)
```

**What this shows:** `NameError` occurs with scope issues (accessing local variables outside their scope), after deleting names, and is distinct from `AttributeError` (which is for object attributes). Variable names in comprehensions don't leak into outer scope in Python 3.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `AttributeError` - Raised when attribute doesn't exist on object
2. `KeyError` - Raised when dictionary key doesn't exist
3. `UnboundLocalError` - Subclass of NameError for local variable issues
4. `TypeError` - Raised when operation applied to wrong type

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (name, attribute, key, etc.).


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Name" comes from Old English "nama" meaning "identifier, designation." In programming, a "name" is an identifier for variables, functions, classes, or other objects. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** `NameError` clearly identifies the problem: an attempt to use a name (identifier) that Python cannot find in the current namespace. The exception name follows Python's convention of combining the problem domain ("Name") with "Error" to create descriptive exception names that immediately communicate what went wrong.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`NameError` is raised by Python when code attempts to use a name (variable, function, class, or module) that doesn't exist in any accessible scope. Python maintains namespaces that map names to objects. When you reference a name, Python searches through local, enclosing, global, and built-in namespaces (LEGB rule). If the name isn't found in any of these scopes, Python raises `NameError`.

This exception is fundamental to Python's dynamic nature and is one of the most common errors, especially for beginners. It typically indicates one of several issues: typos in variable names, using variables before they're defined, scope problems (trying to access local variables from outside their function), or forgetting to import modules.

Understanding `NameError` is crucial for debugging Python code. The error message tells you exactly which name Python cannot find, helping you quickly identify whether it's a typo, incorrect scope, or genuinely missing definition. Learning Python's scoping rules (LEGB: Local, Enclosing, Global, Built-in) helps prevent `NameError` by ensuring names are defined in the correct scope before use.

**Key behaviors:**

1. **Raised on undefined name reference:** The primary trigger is using any name (variable, function, class) that hasn't been defined in an accessible scope. Python must be able to find the name in its namespace lookup process.

2. **Includes the undefined name:** The exception message specifies which name was not found (e.g., "name 'x' is not defined"), making it easy to identify and fix typos or missing definitions.

3. **Distinct from AttributeError:** `NameError` is for undefined names in namespaces, while `AttributeError` is for missing attributes on objects. Understanding this distinction helps in debugging: `math.sqrt` vs `maht.sqrt` (NameError) vs `math.squrt` (AttributeError).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at moment of name lookup failure

### Recommended Form

**Primary recommendation:** Use compound noun combining the concept of "name" (identifier) with "error." Maintain capitalization that matches Python's convention (PascalCase for exception classes in English).

**Forms to AVOID:**

- ❌ Using verb forms ("NameNotFound") - exceptions are nouns, not actions
- ❌ Generic "error" without specifying "name" - loses important context
- ❌ Overly long descriptions - should be concise, 1-3 words maximum

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Personal name (first name, last name)
- ❌ Meaning 2: Brand name or product name
- ❌ Meaning 3: Reputation (make a name for yourself)
- ✅ Meaning 4: **IDENTIFIER/VARIABLE NAME** (symbol in code referring to an object)

**Example:**

English "name" can mean:

1. "Her name is Alice" (personal name) ❌
2. "Nike is a well-known brand name" (product name) ❌
3. "He made a name for himself" (reputation) ❌
4. `print(message)` where "message" is a variable name ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an identifier (variable, function, class name) in code, NOT personal names, brand names, or reputation.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `NameError`, check these translations:**

- [ ] `UnboundLocalError` - Subclass of NameError for local variables
- [ ] `AttributeError` - Similar exception for missing attributes
- [ ] `KeyError` - Similar exception for missing dictionary keys
- [ ] `globals()` - Function returning global names
- [ ] `locals()` - Function returning local names

**Consistency rule:**

All exception classes ending in "Error" should use the same structure in translations. `NameError`, `AttributeError`, and `KeyError` must share the same "error" word and the same compound pattern - maintaining consistent pattern.


### Functional relationships

**This term works WITH:**

1. **Name lookup operations**:

```python
print(variable_name)  # Raises NameError if not defined
```

2. **Exception handling**:

```python
try:
    value = undefined_name
except NameError:
    print("Name not defined")
```

**Common pairing:**

```python
# NameError with undefined variable
print(x)  # Raises NameError: name 'x' is not defined

# NameError with typo
count = 10
print(coun)  # Raises NameError (typo)

# Catching NameError
try:
    result = undefined_variable
except NameError:
    print("Variable not found")
    result = None

# NameError with function before definition
greet()  # Raises NameError

def greet():
    print("Hello")

# NameError with scope issues
def function():
    local_var = 5

function()
print(local_var)  # Raises NameError (not in scope)

# NameError after deletion
y = 10
del y
print(y)  # Raises NameError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `NameError`

- "Name" has multiple meanings (personal, brand, reputation, identifier)
- Need to convey compound concept (name + error)
- Must maintain consistency with other exception names
- Technical term that may vary by region's CS education

**For this term:** MEDIUM

**Rationale:** While the concept is well-established in programming, translating "name" requires understanding the identifier/variable context. Different languages may use different words for code identifiers. The compound structure needs to feel natural while maintaining technical clarity and consistency with other exception translations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures IDENTIFIER/VARIABLE NAME concept (not personal name)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer understand this is about undefined names in code?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations?
- [ ] Same structure as `AttributeError`, `KeyError` translations?
- [ ] Aligns with `globals()`, `locals()` terminology?

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
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: NameError
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
