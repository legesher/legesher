# Python Builtin Function: `dir` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (abbreviation)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `dir()` function returns a sorted list of names (attributes, methods) in an object's namespace. Without arguments, returns names in current local scope. Essential debugging and introspection tool for discovering what attributes and methods an object has. Unlike `vars()` which returns values, `dir()` returns names only.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# List attributes of an object
class Person:
def __init__(self, name, age):
self.name = name
self.age = age

def greet(self):
return f"Hello, I'm {self.name}"

person = Person("Alice", 30)
print(dir(person))  # Output: [..., 'age', 'greet', 'name', ...]

# Without arguments, lists local namespace
def demo():
x = 10
y = 20
print(dir())  # Output: [..., 'x', 'y']

demo()
```

**What this does:** `dir(object)` returns sorted list of all attribute and method names on the object. Without arguments, `dir()` returns names in current local scope. Useful for exploration and debugging.

### Example 2: Common Pattern

```python
# Discovering object capabilities
class Calculator:
def add(self, x, y):
return x + y

def subtract(self, x, y):
return x - y

calc = Calculator()
methods = [name for name in dir(calc) if not name.startswith('_')]
print(methods)  # Output: ['add', 'subtract']

# Check if object has specific attribute
class Config:
debug = True
timeout = 30

config = Config()
if 'debug' in dir(config):
print("Config has debug setting")

# Exploring built-in types
print([x for x in dir(str) if not x.startswith('_')])
# Output: ['capitalize', 'casefold', 'center', 'count', ...]

# Comparing objects
class A:
x = 1
def method_a(self):
pass

class B:
y = 2
def method_b(self):
pass

a_attrs = set(dir(A()))
b_attrs = set(dir(B()))
unique_to_a = a_attrs - b_attrs
unique_to_b = b_attrs - a_attrs
```

**What this does:** `dir()` useful for discovering what methods/attributes object has. Filter with list comprehension to find non-special methods. Check membership to test if attribute exists. Compare attribute sets between objects.

### Example 3: Edge Case

```python
# dir() includes magic methods
class Example:
def normal_method(self):
pass

obj = Example()
all_names = dir(obj)
magic = [x for x in all_names if x.startswith('__')]
normal = [x for x in all_names if not x.startswith('_')]
print(f"Magic methods: {magic[:5]}...")  # ['__class__', '__delattr__', ...]
print(f"Normal attributes: {normal}")  # ['normal_method']

# dir() vs vars() - different information
class Person:
def __init__(self, name):
self.name = name

def greet(self):
pass

person = Person("Alice")
print("dir():", dir(person))  # Includes methods: [..., 'greet', 'name', ...]
print("vars():", vars(person))  # Only instance vars: {'name': 'Alice'}

# dir() on modules
import math
math_funcs = [x for x in dir(math) if not x.startswith('_')]
print(math_funcs[:5])  # ['acos', 'acosh', 'asin', 'asinh', 'atan']

# dir() on built-in types
print(dir(int)[:10])  # Shows int methods
print(dir(list)[:10])  # Shows list methods
print(dir(dict)[:10])  # Shows dict methods

# Custom __dir__ method
class CustomDir:
def __init__(self):
self.public = "visible"
self._private = "hidden"

def __dir__(self):
return ['public', 'custom_only']  # Override default behavior

obj = CustomDir()
print(dir(obj))  # Output: ['custom_only', 'public']
print(vars(obj))  # Output: {'public': 'visible', '_private': 'hidden'}

# dir() without arguments
x = 10
y = 20

def func():
pass

print(dir())  # Lists everything in current scope: [..., 'func', 'x', 'y']

# dir() always returns sorted list
class Unsorted:
def zebra(self):
pass
def apple(self):
pass
def middle(self):
pass

obj = Unsorted()
methods = [m for m in dir(obj) if not m.startswith('_')]
print(methods)  # Output: ['apple', 'middle', 'zebra'] - sorted!
```

**What this shows:** `dir()` includes magic methods (double underscore). Different from `vars()` - dir shows names (including methods), vars shows instance attribute values. Can override with `__dir__` method. Always returns sorted list. Works on modules, classes, instances, built-in types.

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Reflection/Debugging)

**Similar terms in this pattern:**

1. `vars` - Returns attribute dictionary (values, not just names)
2. `locals` - Returns local namespace dictionary
3. `globals` - Returns global namespace dictionary
4. `help` - Displays documentation (uses dir internally)

**Pattern rule:** Introspection functions that examine object state. `dir` and `vars` are complimentary - `dir()` returns names, `vars()` returns name-value dictionary. Translations should convey listing/directory concept.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `vars` | variables | متغيرات | 变量 | चर |
| `help` | ayuda | مساعدة | 帮助 | सहायता |
| `dir` | **directorio** | **دليل** | **目录** | **निर्देशिका** |

---

## Etymology (Brief)

**English Origin:** English abbreviation

**Root meaning:** Abbreviation of "directory" - a listing of contents. In computing, a directory lists files/folders. `dir()` lists the "contents" (attributes/methods) of an object. Command name borrowed from shell `dir` command (Windows) / `ls` command (Unix).

**Why Python uses this:** Short, memorable name for listing object contents. "dir" evokes "directory listing" - showing what's inside. Part of Python's concise introspection API. Parallel to shell commands that show directory contents.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `dir()` function returns a sorted list of strings representing all attribute and method names accessible on an object. For classes and instances, includes magic methods, regular methods, and attributes. For modules, lists all defined names. Without arguments, lists names in current local scope.

Internally, `dir()` calls the object's `__dir__()` method if defined. If not, constructs list from `__dict__` and class hierarchy. The list includes inherited attributes - walks up the Method Resolution Order (MRO) collecting names. Always sorted alphabetically for consistent output.

Common use cases: exploration (what methods does this object have?), debugging (inspect object capabilities), testing if attribute exists (check membership in `dir()` result), discovering API (what can I call on this module?), comparing objects (what attributes differ?), documentation generation (list public methods).

**Key behaviors:**

1. **Sorted output:** Always returns alphabetically sorted list. Makes output consistent and predictable. Unlike `vars()` (dictionary with arbitrary order), `dir()` output always in same order.

2. **Names only, not values:** Returns list of strings (names), not values. To get values, use `getattr(obj, name)` for each name. Complementary to `vars()` which returns name:value dictionary.

3. **Includes methods and inherited attributes:** Unlike `vars()` (instance attributes only), `dir()` includes methods, class attributes, and inherited members. Comprehensive view of object's interface from user perspective.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (abbreviated - "directory")
- **Action vs State:** REFERENCE - refers to listing/contents
- **Temporal aspect:** Snapshot of current attributes

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "directorio" - directory/listing |
| Germanic (de, nl, sv) | Noun | "Verzeichnis" - directory |
| Slavic (ru, pl, uk) | Noun | "директория" - directory |
| Arabic | Noun | "دليل" - directory/guide/listing |
| Chinese | Noun | "目录" - directory/catalog |
| Hindi | Noun | "निर्देशिका" - directory |

**Primary recommendation:** Use noun meaning "directory," "listing," or "catalog" - conveys listing of contents. Can abbreviate if natural in target language, but full word often clearer. Should suggest "list of names" concept.

**Forms to AVOID:**

- ❌ Action verbs - dir is noun, not action
- ❌ Unrelated computing terms - should relate to listing/directory concept
- ❌ Too generic terms like "list" - should be specific to directory/catalog

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `directorio` or `dir`
- **Form:** Noun
- **Why it works:** "Directorio" means directory/listing - clear analogy to file system directories. Can abbreviate to "dir" matching English. Both understood in Spanish programming contexts.

**Arabic:**

- **Translation:** `دليل` (dalīl)
- **Form:** Noun
- **Why it works:** "دليل" means directory/guide/listing. Standard Arabic for directory in computing contexts. Clear reference to listing contents.

**Chinese:**

- **Translation:** `目录` (mùlù)
- **Form:** Noun
- **Why it works:** "目录" means directory/catalog/table of contents. Standard Chinese for file directories. Natural for listing object contents.

**Hindi:**

- **Translation:** `निर्देशिका` (nirdeshika)
- **Form:** Noun
- **Why it works:** "निर्देशिका" means directory/catalog. Technical term used for file directories in Hindi computing. Clear listing concept.

### ❌ Common Translation Mistakes

**Mistake 1: Using generic "list"**

- **Wrong:** `lista` (Spanish - just "list")
- **Why wrong:** Too generic. Many things are lists. "Directory" specifically means listing of contents/names. More precise term better.
- **Right:** `directorio` (directory - more specific)

**Mistake 2: Using verb form**

- **Wrong:** `dirigir` (Spanish - "to direct/manage")
- **Why wrong:** "dir" is noun (directory), not verb (to direct). Part of speech matters. Should be noun meaning listing.
- **Right:** `directorio` (noun)

**Mistake 3: Using unrelated abbreviation**

- **Wrong:** `desc` (Spanish abbreviation of "descripción" - description)
- **Why wrong:** Not related to directory/listing concept. "dir" specifically about listing names. Should maintain directory metaphor.
- **Right:** `dir` or `directorio` (maintains directory concept)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (abbreviation can mean different things)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Direction (north, south, east, west) - spatial direction
- ❌ Meaning 2: Direct (verb - to direct/manage) - action
- ✅ Meaning 3: Directory (listing of contents) - **This is the Python meaning**

**Example:**

"dir" can be interpreted as:

1. Direction/direct (action or spatial) ❌
2. Abbreviation of "directive" (instruction) ❌
3. Abbreviation of "directory" (listing) ✅ **This is the Python meaning**

**Your translation should capture meaning #3 (directory/listing), NOT the others.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `dir`, check these translations:**

- [ ] `vars` - Related introspection function, compatible terminology
- [ ] `help` - Uses dir internally, compatible documentation function
- [ ] `locals`/`globals` - Related namespace functions

**Consistency rule:**

Introspection functions should use compatible terminology. If translating introspection/reflection terms consistently, helps learners understand the family of functions. All should feel like debugging/exploration tools.

**Example:**

✅ **Consistent (conceptual):**
- `dir` → `directorio` (listing of names)
- `vars` → `variables` (dictionary of variables)
- `help` → `ayuda` (help/assistance)
Related introspection tools ✅

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Clear concept but requires abbreviation decision
- "Directory" has standard translations
- Some languages may prefer full word vs abbreviation
- Programming metaphor (directory) universal
- **AI confidence should be HIGH with context**

**For this term:** MEDIUM

**Rationale:** "dir" as abbreviation of "directory" is clear metaphor. Main decision: use abbreviation matching English, or full word. Both acceptable. "Directory" concept universal in computing, has standard translations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Check if target language commonly uses abbreviations in code. If yes, "dir" acceptable. If no, use full "directory" word.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures DIRECTORY/LISTING concept?
- [ ] Understood as listing of names?
- [ ] Conveys introspection purpose?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Standard term for "directory" if using full word?
- [ ] Appropriate abbreviation if abbreviating?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Compatible with vars() terminology?
- [ ] Aligns with introspection function family?
- [ ] Matches help() pattern?

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
term: dir
language: es
translation: directorio
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "directorio" is the full word for "directory" - standard computing term for file directories and listings. While "dir" abbreviation could work, "directorio" is more explicit and widely understood. Conveys the listing/catalog concept clearly.

**Alternatives considered:**

1. `dir` (keep English abbreviation) - Could work but "directorio" more explicit
2. `lista` (list) - Too generic, "directorio" more specific
3. `indice` (index) - Could work but "directorio" more standard for this purpose

**If confidence is not HIGH, explain:**

N/A - Confidence HIGH. "Directory" is standard computing metaphor with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
