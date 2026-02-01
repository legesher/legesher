# Python Builtin Function: `vars` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (abbreviation)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `vars()` function returns the `__dict__` attribute of an object, module, class, or instance - a dictionary containing its attributes. With no arguments, returns `locals()` dictionary. Used for introspection, debugging, and dynamic attribute access. Provides writable dictionary view of object's namespace.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get instance variables
class Person:
def __init__(self, name, age):
self.name = name
self.age = age

person = Person("Alice", 30)
print(vars(person))  # Output: {'name': 'Alice', 'age': 30}

# Without arguments, returns locals()
def demo():
x = 10
y = 20
print(vars())  # Output: {'x': 10, 'y': 20}

demo()
```

**What this does:** `vars(object)` returns dictionary of object's attributes (its `__dict__`). Without arguments, `vars()` returns current local namespace like `locals()`. Shows all instance variables as dictionary.

### Example 2: Common Pattern

```python
# Debugging object state
class Config:
def __init__(self):
self.debug = True
self.timeout = 30
self.retry_count = 3

config = Config()
print("Current config:", vars(config))
# Output: {'debug': True, 'timeout': 30, 'retry_count': 3}

# Dynamic attribute modification
person = Person("Bob", 25)
person_vars = vars(person)
person_vars['city'] = "New York"  # Modifies object!
print(person.city)  # Output: New York

# Comparing objects
class Point:
def __init__(self, x, y):
self.x = x
self.y = y

p1 = Point(1, 2)
p2 = Point(1, 2)

print(vars(p1) == vars(p2))  # True - same attributes and values
print(p1 == p2)  # False - different objects

# Serialization helper
class User:
def __init__(self, username, email, age):
self.username = username
self.email = email
self.age = age

def to_dict(self):
return vars(self)

user = User("alice", "alice@example.com", 30)
data = user.to_dict()
print(data)  # {'username': 'alice', 'email': 'alice@example.com', 'age': 30}

# Inspecting module
import math
print(list(vars(math).keys())[:5])  # ['__name__', '__doc__', '__package__', ...]
```

**What this does:** `vars()` useful for debugging (see all object attributes), dynamic manipulation (modify via dictionary), comparison (check attribute values), serialization (convert object to dict). Provides mutable view - changes affect object.

### Example 3: Edge Case

```python
# vars() vs __dict__ directly
class Example:
def __init__(self):
self.x = 10

obj = Example()
print(vars(obj))  # {'x': 10}
print(obj.__dict__)  # {'x': 10} - same result
print(vars(obj) is obj.__dict__)  # True - same object!

# Objects without __dict__
class Slotted:
__slots__ = ['x', 'y']
def __init__(self, x, y):
self.x = x
self.y = y

slotted = Slotted(1, 2)
try:
vars(slotted)
except TypeError as e:
print(f"Error: {e}")  # TypeError: vars() argument must have __dict__ attribute

# Class vs instance
class MyClass:
class_var = "shared"

def __init__(self):
self.instance_var = "unique"

obj = MyClass()
print("Instance:", vars(obj))  # {'instance_var': 'unique'}
print("Class:", vars(MyClass))  # Contains methods, class_var, __dict__, etc.

# vars() without arguments vs locals()
def test():
a = 1
b = 2
print(vars() == locals())  # True - same when no argument

test()

# Modifying via vars()
class Counter:
def __init__(self):
self.count = 0

counter = Counter()
vars(counter)['count'] = 10  # Directly modifies object
print(counter.count)  # 10

# Can't use vars() on built-in types
try:
vars(42)
except TypeError as e:
print(f"Error: {e}")  # TypeError: vars() argument must have __dict__ attribute

# Module introspection
import sys
module_attrs = vars(sys)
print(type(module_attrs))  # <class 'dict'>
print('version' in vars(sys))  # True
```

**What this shows:** `vars(obj)` is equivalent to `obj.__dict__` and returns same object reference. Objects with `__slots__` don't have `__dict__`, so `vars()` raises `TypeError`. Built-in types (int, str) also don't have `__dict__`. Modifying vars() return value modifies the object. Without arguments, vars() equals locals().

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Reflection/Debugging)

**Similar terms in this pattern:**

1. `dir` - Lists all attributes/methods of object (names only)
2. `locals` - Returns current local namespace as dictionary
3. `globals` - Returns global namespace as dictionary
4. `getattr` - Gets attribute value by name

**Pattern rule:** Introspection functions that examine object state. `vars` and `dir` are related - `vars()` returns attribute dictionary, `dir()` returns attribute names list. Translations should convey inspection/variables concept.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `dir` | directorio | دليل | 目录 | निर्देशिका |
| `locals` | locales | محلي | 本地 | स्थानीय |
| `vars` | **variables** | **متغيرات** | **变量** | **चर** |

---

## Etymology (Brief)

**English Origin:** English abbreviation

**Root meaning:** Abbreviation of "variables" - refers to variable attributes of an object. In programming, "variables" are named storage locations. `vars()` exposes an object's variables (instance attributes) as a dictionary.

**Why Python uses this:** Short, memorable name for common introspection operation. "vars" clearly suggests "variables" or "attributes." Parallel to `dir()` (directory) for listing names. Part of Python's philosophy of readable introspection.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `vars()` function provides access to an object's namespace dictionary (`__dict__`). For objects with `__dict__` attribute, returns that dictionary directly (not a copy). This enables inspecting all instance attributes, dynamically adding/modifying attributes, serializing objects, and debugging object state.

Without arguments, `vars()` behaves like `locals()` - returns current local namespace. This form useful in interactive debugging but rarely used in production code. The object form (`vars(obj)`) is far more common.

Common use cases: debugging (inspect all attributes at once), serialization (convert object to dictionary for JSON/storage), dynamic attribute manipulation (add/modify via dictionary interface), object comparison (compare attribute values), introspection tools, and object dumping for logs.

**Key behaviors:**

1. **Returns **dict** directly:** `vars(obj)` returns `obj.__dict__`, not a copy. Modifications to returned dictionary modify the object. This is mutable view, not snapshot. `vars(obj)['new'] = value` adds attribute to object.

2. **Requires **dict**:** Only works on objects with `__dict__` attribute. Objects with `__slots__`, built-in types (int, str, list), and some C extension objects don't have `__dict__`. Raises `TypeError` if no `__dict__`.

3. **Class vs instance:** Calling `vars(obj)` on instance returns instance attributes only (not class attributes). Calling `vars(MyClass)` returns class namespace (methods, class variables, special attributes). Different dictionaries, different purposes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (plural - "variables")
- **Action vs State:** STATE - represents collection of variables
- **Temporal aspect:** Snapshot of current variables

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun (plural) | "variables" - variables/attributes |
| Germanic (de, nl, sv) | Noun (plural) | "Variablen" - variables |
| Slavic (ru, pl, uk) | Noun (plural) | "переменные" - variables |
| Arabic | Noun (plural) | "متغيرات" - variables |
| Chinese | Noun | "变量" - variables |
| Hindi | Noun (plural) | "चर" - variables |

**Primary recommendation:** Use noun form meaning "variables" or "attributes" (plural if language has plurals). Should be abbreviation or short form if natural in target language. Conveys collection of variables.

**Forms to AVOID:**

- ❌ Full word if abbreviation is natural (like English "vars" vs "variables")
- ❌ Singular form - implies one variable, not collection
- ❌ Verb form - vars is noun, not action

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `variables` or `vars`
- **Form:** Noun (plural)
- **Why it works:** "Variables" is standard programming term. Could abbreviate to "vars" matching English style, or keep full "variables." Both clear. Plural form indicates collection.

**Arabic:**

- **Translation:** `متغيرات` (mutaghayyirāt)
- **Form:** Noun (plural)
- **Why it works:** "متغيرات" is plural of "متغير" (variable). Standard Arabic for variables in programming. Clear technical term. Plural form appropriate.

**Chinese:**

- **Translation:** `变量` (biànliàng)
- **Form:** Noun
- **Why it works:** "变量" means "variable(s)" - Chinese doesn't distinguish plural morphologically. Standard CS term. Concise two-character compound. Widely understood.

**Hindi:**

- **Translation:** `चर` (char) or `वेरिएबल` (veriebal)
- **Form:** Noun
- **Why it works:** "चर" is Sanskrit-derived term for variables. Concise, one syllable. "वेरिएबल" is transliteration also acceptable. Both used in Indian CS education.

### ❌ Common Translation Mistakes

**Mistake 1: Using singular form**

- **Wrong:** `variable` (Spanish singular)
- **Why wrong:** Function returns collection of variables, not single variable. Plural form more accurate. "vars" is abbreviation of "variables" (plural), not "variable."
- **Right:** `variables` (plural)

**Mistake 2: Using verb form**

- **Wrong:** `variar` (Spanish - "to vary")
- **Why wrong:** "vars" is noun (variables), not verb (to vary). Function doesn't perform action of varying - it accesses variable collection. Part of speech matters.
- **Right:** `variables` (noun)

**Mistake 3: Being too verbose when abbreviation natural**

- **Wrong:** `diccionario_de_variables` (Spanish - "dictionary of variables")
- **Why wrong:** Over-explains. English "vars" is concise abbreviation. While "variables" is clear, don't add extra words. Keep concise like English.
- **Right:** `variables` or `vars` (concise)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (clear abbreviation)

**The term is unambiguous:**

"vars" is unambiguous abbreviation of "variables" in programming contexts. While "var" can mean variation in statistics, in programming it clearly means variables. Plural form ("vars" not "var") indicates collection.

**Translation consideration:**

Use standard programming term for "variables" in plural form. If target language commonly abbreviates "variables" in code, can use abbreviation. Otherwise full word acceptable. Should clearly indicate collection/dictionary of attributes.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `vars`, check these translations:**

- [ ] `dir` - Related introspection function, compatible pattern
- [ ] `locals` - Related namespace function, should use compatible terminology
- [ ] `globals` - Related namespace function
- [ ] `getattr` - Related attribute access, compatible "attribute" terminology

**Consistency rule:**

Introspection functions should use related terminology. If translating "attribute" certain way in getattr/setattr, "vars" (which returns attributes) should be compatible. All should feel like introspection family.

**Example:**

✅ **Consistent (conceptual):**

- `vars` → `variables` (collection of attributes)
- `dir` → `directorio` (listing of attributes)
- Related concepts, compatible terms ✅

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Clear concept but requires decision on abbreviation
- "Variables" has straightforward translations
- Some languages may prefer full word vs abbreviation
- Context of introspection important
- **AI confidence should be HIGH with context**

**For this term:** MEDIUM

**Rationale:** "vars" is clear abbreviation of "variables." Main decision is whether to abbreviate in target language (like "vars") or use full word ("variables"). Both can be correct depending on language conventions. Most languages use full word.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Check if target language commonly abbreviates "variables" in code. If yes, can use abbreviation. If no, use full word. Both acceptable if clear.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures VARIABLE COLLECTION concept?
- [ ] Understood as attribute dictionary accessor?
- [ ] Conveys introspection purpose?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Plural form if language has plurals?
- [ ] Standard programming term for "variables"?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Compatible with dir() terminology?
- [ ] Aligns with locals/globals pattern?
- [ ] Matches attribute-related terms?

### 4. Usability

- [ ] Short (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear meaning?

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
term: vars
language: es
translation: variables
form: noun_plural
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "variables" is the full form of the English abbreviation "vars." Standard programming term widely understood in Spanish CS education. Plural form correctly indicates collection of variables/attributes. Clear and unambiguous.

**Alternatives considered:**

1. `vars` (keep English abbreviation) - Could work but "variables" more explicit
2. `atributos` (attributes) - Accurate but "variables" more standard for this function
3. `diccionario` (dictionary) - Too generic, doesn't specify variables

**If confidence is not HIGH, explain:**

N/A - Confidence HIGH. Standard programming terminology with clear meaning.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
