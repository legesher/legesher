# Python Builtin Function: `delattr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** compound_verb
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `delattr()` function deletes a named attribute from an object. Signature: `delattr(object, name)` where name is a string. Equivalent to `del object.attribute` but allows dynamic attribute names. Part of Python's reflection API family along with `getattr`, `setattr`, and `hasattr`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic attribute deletion
class Person:
def __init__(self, name, age):
self.name = name
self.age = age

person = Person("Alice", 30)
print(hasattr(person, "age"))  # True
delattr(person, "age")
print(hasattr(person, "age"))  # False
# print(person.age)  # Would raise AttributeError
```

**What this does:** `delattr(object, "attribute_name")` removes the named attribute from the object. After deletion, accessing that attribute raises `AttributeError`. Dynamic alternative to `del object.attribute`.

### Example 2: Common Pattern

```python
# Dynamic attribute removal
class Config:
def __init__(self):
self.debug = True
self.verbose = False
self.log_level = "INFO"

config = Config()

# Remove attributes based on conditions
attrs_to_remove = ["verbose", "log_level"]
for attr in attrs_to_remove:
if hasattr(config, attr):
delattr(config, attr)

print(hasattr(config, "debug"))  # True - kept
print(hasattr(config, "verbose"))  # False - removed
print(hasattr(config, "log_level"))  # False - removed

# Cleanup temporary attributes
class TempData:
def process(self):
self._temp_cache = []  # Temporary attribute
# ... processing ...
if hasattr(self, "_temp_cache"):
delattr(self, "_temp_cache")

# Dynamic cleanup from list
class DynamicObject:
pass

obj = DynamicObject()
obj.attr1 = "value1"
obj.attr2 = "value2"
obj.attr3 = "value3"

# Remove based on pattern
for attr_name in dir(obj):
if attr_name.startswith("attr") and attr_name.endswith("2"):
delattr(obj, attr_name)

print(hasattr(obj, "attr1"))  # True
print(hasattr(obj, "attr2"))  # False
print(hasattr(obj, "attr3"))  # True
```

**What this does:** `delattr()` enables dynamic attribute removal when attribute names are in variables. Common for cleanup operations, removing temporary attributes, and dynamic object modification. Safer to check with `hasattr()` before deleting.

### Example 3: Edge Case

```python
# Difference from del statement
class Example:
def __init__(self):
self.value = 42

obj = Example()

# These are equivalent:
del obj.value  # Static deletion
# vs
obj2 = Example()
delattr(obj2, "value")  # Dynamic deletion

# But delattr allows variables:
attr_name = "value"
obj3 = Example()
delattr(obj3, attr_name)  # Can't do: del obj3.attr_name

# Triggers __delattr__ magic method
class TrackedObject:
def __delattr__(self, name):
print(f"Deleting attribute: {name}")
super().__delattr__(name)

obj = TrackedObject()
obj.x = 10
delattr(obj, "x")  # Output: Deleting attribute: x

# Attempting to delete non-existent attribute
class Demo:
pass

demo = Demo()
try:
delattr(demo, "nonexistent")
except AttributeError as e:
print(f"Error: {e}")  # Error: nonexistent

# Cannot delete class attributes from instance
class MyClass:
class_attr = "shared"

obj = MyClass()
try:
delattr(obj, "class_attr")  # Raises AttributeError
except AttributeError:
print("Cannot delete class attribute from instance")

# Can delete from class itself
delattr(MyClass, "class_attr")  # Works - deletes from class
```

**What this shows:** `delattr()` is dynamic version of `del` statement - use when attribute name is in a variable. Triggers `__delattr__` magic method. Raises `AttributeError` if attribute doesn't exist. Can delete from classes, but instance can't delete class attributes.

---

## Pattern Classification

**This term is:** ATTRIBUTE MANIPULATION FUNCTION (Reflection/Introspection)

**Similar terms in this pattern:**

1. `getattr` - Gets attribute value by name
2. `setattr` - Sets attribute value by name
3. `hasattr` - Checks if attribute exists by name

**Pattern rule:** Attribute manipulation functions are compound: verb + "attr" (attribute). Family pattern: get/set/has/del + attr. These four form complete CRUD operations on object attributes. Must maintain family consistency across translations.


---

## Etymology (Brief)

**English Origin:** Compound abbreviation (English/Latin)

**Root meaning:** "del" (abbreviation of "delete" from Latin "delere" - to destroy, erase) + "attr" (abbreviation of "attribute" from Latin "attributus" - assigned). In programming, "delete" means remove/erase, and "attribute" means property of an object.

**Why Python uses this:** Compound function name matches pattern with `getattr`, `setattr`, `hasattr`. Python's reflection API uses consistent naming for attribute operations. "delattr" completes the CRUD pattern: get (read), set (create/update), has (check), del (delete).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `delattr()` function removes a named attribute from an object at runtime. Signature: `delattr(object, name)` where name is a string. It's the dynamic equivalent of the `del object.attribute` statement - use when attribute name is in a variable or computed at runtime.

Internally, `delattr(obj, name)` is equivalent to `del obj.__dict__[name]` for instance attributes (triggers `__delattr__` if defined). After deletion, the attribute no longer exists on the object - accessing it raises `AttributeError`. Cannot undo deletion without re-creating the attribute.

Common use cases include dynamic cleanup (remove temporary attributes), attribute lifecycle management, freeing memory by removing large cached values, implementing attribute protocols, and dynamic object manipulation based on configuration or user input.

**Key behaviors:**

1. **Triggers **delattr**:** Calls object's `__delattr__(name)` magic method if defined. Allows custom deletion behavior. Default behavior removes from instance `__dict__`. Can be overridden for logging, validation, or side effects.

2. **Raises AttributeError:** If attribute doesn't exist, raises `AttributeError`. Always check with `hasattr()` first for safe deletion. Exception includes attribute name in message for debugging.

3. **Instance vs class attributes:** Deleting from instance affects only that instance. Cannot delete class attributes through instance - must delete from class itself: `delattr(MyClass, "attr")`. Instance deletion doesn't affect class or other instances.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb (performs action)
- **Action vs State:** ACTION - removes/deletes attribute
- **Temporal aspect:** One-time action with permanent effect

### Recommended Form

**Primary recommendation:** Compound following attr-family pattern: verb meaning "delete/remove" + same noun for "attribute" used in getattr/setattr/hasattr. CRITICAL: Must use exact same "attribute" word as other attr-family functions.

**Forms to AVOID:**

- ❌ Different "attribute" word than getattr/setattr/hasattr - breaks family consistency
- ❌ Using "destroy" if too violent - "delete/remove" more standard
- ❌ Missing verb component - need complete action description

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specialized compound term)

**The term is unambiguous:**

"delattr" is programming-specific abbreviation of "delete attribute." While "delete" has general meaning (remove/erase), in programming context combined with "attribute" it unambiguously means "remove a named property from an object."

**Translation consideration:**

Use standard programming term for "delete/remove" + exact same "attribute" word as getattr/setattr/hasattr. Deletion vocabulary should be technical, not colloquial. Ensure the verb clearly means "remove permanently" not just "hide temporarily."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `delattr`, check these translations:**

- [ ] `getattr` - Must use SAME "attribute" word
- [ ] `setattr` - Must use SAME "attribute" word
- [ ] `hasattr` - Must use SAME "attribute" word

**Consistency rule:**

The attr-family (`getattr`, `setattr`, `hasattr`, `delattr`) MUST use identical word for "attribute" across all four. Only the verb changes (get/set/has/del). This linguistic parallelism is CRITICAL for pattern recognition and learning.


### Functional relationships

**This term works WITH:**

1. **`hasattr` + `delattr`**: Safe deletion pattern

```python
if hasattr(obj, "temp"):
delattr(obj, "temp")
```

2. **`delattr` + cleanup**: Remove temporary attributes

```python
for attr in temp_attrs:
delattr(obj, attr)
```

**Common pairing:**

```python
# Basic deletion
class Person:
def __init__(self):
self.name = "Alice"
self.temp = "temporary"

person = Person()
delattr(person, "temp")

# Safe deletion with hasattr
if hasattr(person, "temp"):
delattr(person, "temp")

# Dynamic cleanup
class Cache:
def clear_cache(self):
cache_attrs = [attr for attr in dir(self) if attr.startswith("_cache")]
for attr in cache_attrs:
if hasattr(self, attr):
delattr(self, attr)

# Attribute lifecycle
class Session:
def __init__(self):
self.user = "Alice"
self._temp_data = []

def cleanup(self):
# Remove temporary attributes
temp_attrs = [a for a in dir(self) if a.startswith("_temp")]
for attr in temp_attrs:
try:
delattr(self, attr)
except AttributeError:
pass

# Custom __delattr__
class TrackedObject:
def __init__(self):
self.deletions = []

def __delattr__(self, name):
self.deletions.append(name)
super().__delattr__(name)

obj = TrackedObject()
obj.x = 10
delattr(obj, "x")
print(obj.deletions)  # ['x']

# Comparison with del
class Example:
def __init__(self):
self.static_name = "value"
self.dynamic_name = "value"

obj = Example()
del obj.static_name  # Static - attribute name hardcoded

attr_name = "dynamic_name"
delattr(obj, attr_name)  # Dynamic - attribute name in variable

# Pattern: Complete CRUD on attributes
class DynamicObject:
pass

obj = DynamicObject()

# Create
setattr(obj, "name", "Alice")

# Read
value = getattr(obj, "name")

# Check
exists = hasattr(obj, "name")

# Delete
delattr(obj, "name")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Clear concept but must coordinate with attr-family
- "Delete" has straightforward translations
- Key challenge is maintaining family consistency
- Must use exact same "attribute" word
- **AI confidence should be MEDIUM-HIGH with context**

**For this term:** MEDIUM

**Rationale:** "delattr" translation is straightforward conceptually, but requires strict coordination with getattr/setattr/hasattr. The "attribute" component must be identical across all four. Main challenge is choosing appropriate "delete" verb while maintaining family pattern.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

CRITICAL: Check getattr/setattr/hasattr translations first. Copy their "attribute" word exactly. Only translate the "del" verb component differently.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ATTRIBUTE DELETION concept?
- [ ] Understood as removing named property?
- [ ] Conveys permanent removal (not hiding)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound: verb + noun)?
- [ ] Uses appropriate "delete/remove" verb?
- [ ] Uses EXACT SAME "attribute" word as getattr/setattr/hasattr?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Uses IDENTICAL "attribute" word as getattr/setattr/hasattr?
- [ ] Matches grammatical pattern with attr-family?
- [ ] Aligns with OOP terminology?

### 4. Usability

- [ ] Short enough (2-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear action structure?

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
term: delattr
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
