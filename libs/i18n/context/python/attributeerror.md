# Python Builtin: `AttributeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`AttributeError` is a built-in exception raised when attempting to access or assign an attribute that doesn't exist on an object. It signals that the requested attribute (method or property) is not found in the object's namespace, typically due to typos, incorrect object types, or missing definitions.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Accessing non-existent attribute raises AttributeError
class Person:
    def __init__(self, name):
        self.name = name

person = Person("Alice")
print(person.age)  # Raises AttributeError: 'Person' object has no attribute 'age'
```

**What this does:** Attempting to access an attribute that doesn't exist on an object raises an `AttributeError` exception. The error message shows which attribute was not found and on which object type.

### Example 2: Common Pattern

```python
# Catching AttributeError with try-except
class Car:
    def __init__(self, brand):
        self.brand = brand

car = Car("Toyota")

try:
    print(car.model)
except AttributeError:
    print("Model attribute not found, using default")
    car.model = "Unknown"

# Using hasattr() to check before accessing
if hasattr(car, "year"):
    print(car.year)
else:
    print("Year attribute doesn't exist")

# Using getattr() with default value
model = getattr(car, "model", "Not specified")
```

**What this does:** `try-except` blocks catch `AttributeError` to handle missing attributes gracefully. `hasattr()` checks if an attribute exists before accessing it. `getattr()` returns a default value instead of raising an exception.

### Example 3: Edge Case

```python
# AttributeError with wrong object type
text = "Hello"
text.append("!")  # Raises AttributeError: 'str' object has no attribute 'append'
# (strings don't have append method, lists do)

# AttributeError with None
result = None
result.count()  # Raises AttributeError: 'NoneType' object has no attribute 'count'

# AttributeError when setting read-only attribute
numbers = (1, 2, 3)
numbers.sort()  # Raises AttributeError: 'tuple' object has no attribute 'sort'
# (tuples are immutable, lists have sort)

# Typos cause AttributeError
person = Person("Bob")
person.nmae = "Robert"  # Creates wrong attribute
print(person.name)  # Still "Bob" - typo created separate attribute
```

**What this shows:** `AttributeError` occurs when calling methods on wrong types, accessing attributes on `None`, or trying to use methods that don't exist on a type. Typos in attribute names create new attributes instead of modifying existing ones, which can cause confusing bugs.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `KeyError` - Raised when dictionary key doesn't exist
2. `IndexError` - Raised when sequence index is out of range
3. `NameError` - Raised when variable name not found
4. `TypeError` - Raised when operation applied to wrong type

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (attribute, key, index, etc.).


---

## Etymology (Brief)

**English Origin:** Compound word (Latin + Latin-derived)

**Root meaning:** "Attribute" comes from Latin "attributus" meaning "assigned, granted, bestowed." In programming, an "attribute" is a property or method belonging to an object. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** `AttributeError` clearly identifies the problem: an attempt to access or modify an object's attribute failed because that attribute doesn't exist. The name follows Python's convention of combining the problem domain ("Attribute") with "Error" to create descriptive exception names that immediately communicate what went wrong.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`AttributeError` is raised by Python when code attempts to access or modify an attribute (property or method) that doesn't exist on an object. In Python's object-oriented system, objects have namespaces containing their attributes. When you use dot notation (`object.attribute`) and the attribute isn't in that namespace, Python raises `AttributeError` to signal the access failed.

This exception is fundamental to Python's dynamic nature. Unlike statically-typed languages that catch missing attributes at compile time, Python discovers attribute errors at runtime. This makes `AttributeError` one of the most common exceptions, often caused by typos, incorrect object types, or attempting to use methods that don't exist on a particular type.

Understanding `AttributeError` is crucial for debugging object-oriented Python code. The exception message tells you exactly which attribute is missing and on what type of object, helping you quickly identify whether it's a typo, wrong object type, or genuinely missing attribute. Learning to use `hasattr()`, `getattr()`, and `try-except` to handle potential `AttributeError` situations is essential for writing robust code.

**Key behaviors:**

1. **Raised on missing attribute access:** The primary trigger is using dot notation (`object.attribute`) when the attribute doesn't exist. This applies to both data attributes (properties) and method attributes (functions).

2. **Includes object type in message:** The exception message specifies which type of object caused the error (e.g., "'str' object has no attribute 'append'"), helping you quickly identify type mismatches or incorrect assumptions about object capabilities.

3. **Occurs with wrong method calls:** A common cause is calling a method that exists on one type but not another (e.g., trying to use list methods on strings, or string methods on lists). This often happens when a function returns an unexpected type.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at moment of failed attribute access

### Recommended Form

**Primary recommendation:** Use compound noun combining the concept of "attribute" with "error." Maintain capitalization that matches Python's convention (PascalCase for exception classes in English).

**Forms to AVOID:**

- ❌ Using verb forms ("AttributeMissing") - exceptions are nouns, not actions
- ❌ Generic "error" without specifying "attribute" - loses important context
- ❌ Overly long descriptions - should be concise, 1-3 words maximum

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Quality or characteristic (courage is a positive attribute)
- ❌ Meaning 2: HTML attribute (the href attribute of a link)
- ❌ Meaning 3: Grammar attribute (adjective attributing quality to noun)
- ✅ Meaning 4: **OBJECT PROPERTY/METHOD** (member of an object's namespace)

**Example:**

English "attribute" can mean:

1. "Honesty is an important attribute" (personal quality) ❌
2. `<a href="...">` where href is an HTML attribute ❌
3. "Red is an attribute describing the car" (grammar) ❌
4. `person.name` where name is an object attribute ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a property or method belonging to an object, NOT personal qualities, HTML attributes, or grammatical descriptions.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `AttributeError`, check these translations:**

- [ ] `getattr` - Built-in function to get attributes
- [ ] `setattr` - Built-in function to set attributes
- [ ] `hasattr` - Built-in function to check for attributes
- [ ] `KeyError` - Similar exception for dictionaries (should follow same error naming pattern)
- [ ] `NameError` - Similar exception for undefined variables

**Consistency rule:**

All exception classes ending in "Error" should use the same structure in translations. Whatever compound pattern `AttributeError` uses, `KeyError` and `NameError` must follow it with the same error word and the same compound order - maintaining consistent pattern.


### Functional relationships

**This term works WITH:**

1. **Attribute access operations**:

```python
obj.attribute  # Raises AttributeError if not found
```

2. **Exception handling**:

```python
try:
    value = obj.attribute
except AttributeError:
    print("Attribute not found")
```

**Common pairing:**

```python
# AttributeError with object attribute access
class Dog:
    def __init__(self, name):
        self.name = name

dog = Dog("Rex")
print(dog.breed)  # Raises AttributeError

# Catching AttributeError
try:
    print(dog.breed)
except AttributeError:
    print("Breed attribute not found")
    dog.breed = "Unknown"

# Using hasattr() to prevent AttributeError
if hasattr(dog, "age"):
    print(dog.age)
else:
    print("Age not set")

# Using getattr() with default
age = getattr(dog, "age", 0)

# AttributeError with wrong method
text = "Hello"
text.append("!")  # Raises AttributeError (strings don't have append)

# AttributeError with None
result = None
result.method()  # Raises AttributeError: 'NoneType' object has no attribute 'method'
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `AttributeError`

- "Attribute" has multiple meanings (quality, HTML attribute, object property)
- Need to convey compound concept (attribute + error)
- Must maintain consistency with other exception names
- Technical term that may vary by region's CS education

**For this term:** MEDIUM

**Rationale:** While the concept is well-established in object-oriented programming, translating "attribute" requires understanding the object property/method context. Different languages may use different words for object attributes. The compound structure needs to feel natural while maintaining technical clarity and consistency with other exception translations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures OBJECT ATTRIBUTE concept (not personal quality or HTML attribute)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer understand this is about missing object properties/methods?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations?
- [ ] Same structure as `KeyError`, `IndexError` translations?
- [ ] Aligns with `getattr`, `hasattr`, `setattr` terminology?

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
term: AttributeError
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
