# Python Builtin: `property` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** decorator / descriptor
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`property()` creates a managed attribute using getter/setter/deleter methods, enabling computed properties and attribute access control through Python's descriptor protocol.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic property with getter
class Circle:
def __init__(self, radius):
self._radius = radius

@property
def radius(self):
return self._radius

@radius.setter
def radius(self, value):
if value < 0:
raise ValueError("Radius cannot be negative")
self._radius = value

circle = Circle(5)
print(circle.radius)  # Output: 5 (calls getter)
circle.radius = 10  # Calls setter
```

**What this does:** `@property` decorator makes a method accessible like an attribute, calling the getter function when accessed and setter when assigned, enabling validation and computed values.

### Example 2: Common Pattern

```python
# Computed property
class Rectangle:
def __init__(self, width, height):
self.width = width
self.height = height

@property
def area(self):
return self.width * self.height

rect = Rectangle(5, 10)
print(rect.area)  # Output: 50 (computed, not stored)
rect.width = 3
print(rect.area)  # Output: 30 (recomputed automatically)
```

**What this does:** Properties can be computed on-the-fly rather than stored, automatically updating when dependent attributes change, keeping derived data consistent.

### Example 3: Edge Case

```python
# Full property with getter, setter, deleter
class Temperature:
def __init__(self):
self._celsius = 0

@property
def celsius(self):
return self._celsius

@celsius.setter
def celsius(self, value):
if value < -273.15:
raise ValueError("Below absolute zero")
self._celsius = value

@celsius.deleter
def celsius(self):
print("Deleting temperature")
del self._celsius

temp = Temperature()
temp.celsius = 25
print(temp.celsius)  # Output: 25
del temp.celsius  # Calls deleter
```

**What this shows:** Properties support full attribute protocol with getter, setter, and deleter methods, providing complete control over attribute access, modification, and deletion.

---

## Pattern Classification

**This term is:** DESCRIPTOR / DECORATOR

**Similar terms in this pattern:**

1. `classmethod` - Method decorator for class-level methods
2. `staticmethod` - Method decorator for static methods
3. `@` - Decorator syntax operator

**Pattern rule:** Descriptors and decorators that modify class behavior should use noun forms indicating what they create or modify.


---

## Etymology (Brief)

**English Origin:** Latin "proprietas" = ownership, characteristic

**Root meaning:** From Latin "proprius" (one's own, special). In programming, a "property" is an attribute that belongs to an object with special behavior.

**Why Python uses this:** "Property" in OOP means an attribute with controlled access. Python's `property()` creates managed attributes that look like simple attributes but execute code when accessed. Chosen because these are "properties" of objects that appear as attributes but behave as methods.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`property()` implements Python's descriptor protocol to create managed attributes. When used as a decorator, it transforms methods into properties that are accessed like attributes but execute getter/setter functions. This enables data validation, computed values, and encapsulation without changing the interface.

The power of `property()` is it makes method calls look like attribute access. Instead of `obj.get_value()` and `obj.set_value(x)`, you write `obj.value` and `obj.value = x`. The syntax is cleaner while maintaining full control over what happens during access.

Properties are fundamental to Python's "consenting adults" philosophy - attributes are public by default, but properties let you add validation or computation later without breaking code that uses simple attribute syntax. They're descriptors, which means they intercept attribute access at the class level.

**Key behaviors:**

1. **Descriptor protocol:** Implements `__get__`, `__set__`, and `__delete__` methods that are called on attribute access, providing interception points.
2. **Decorator chaining:** Can use `@property`, `@name.setter`, and `@name.deleter` to build full attribute control progressively.
3. **Transparent to users:** Accessed like normal attributes (`obj.attr`), but execute functions, enabling validation and computation without syntax changes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (refers to an object characteristic/attribute)
- **Action vs State:** STATE/CHARACTERISTIC - describes what an object has
- **Temporal aspect:** Persistent state (exists as part of object)

### Recommended Form

**Primary recommendation:** Use a noun meaning "characteristic," "attribute," or "property" in the sense of "a feature that belongs to something." Should convey ownership/belonging.

**Forms to AVOID:**

- ❌ Action verbs - property is not an action, it's a characteristic
- ❌ "Real estate property" translations - programming property, not land ownership
- ❌ Generic "thing" - should be specific to attributes/characteristics

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**Identify the CORRECT meaning for Python:**

- ❌ Real estate property (land, building ownership)
- ❌ Property rights (legal ownership)
- ✅ **Object characteristic/attribute** (programming) - This is the Python meaning

**Example:**

English "property" can mean:

1. Real estate ("buy property") ❌
2. Possessions ("personal property") ❌
3. Characteristic/attribute ("a property of the object") ✅ **This is the Python meaning**

**Your translation should capture meaning #3, the programming sense of object characteristic.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `property`, check these translations:**

- [ ] `class` - Properties belong to classes, compatible terminology needed
- [ ] `classmethod` - Related decorator, should use compatible style
- [ ] `staticmethod` - Related decorator, consistent pattern

**Consistency rule:**

Class-related decorators (`@property`, `@classmethod`, `@staticmethod`) should form a cohesive family with consistent naming patterns and formality levels.

**Example:**

✅ **Consistent:**

- `class` → `clase`
- `property` → `propiedad`
- `classmethod` → `método_clase`
- Related OOP terms ✅

### Functional relationships

**This term works WITH:**

1. **`@property` + getter**: Default usage for read-only property
2. **`@name.setter` + setter**: Add write capability
3. **`@name.deleter` + deleter**: Add delete capability

**Common pairing:**

```python
# Full property usage
class Example:
@property
def value(self):  # Getter
return self._value

@value.setter
def value(self, v):  # Setter
self._value = v

@value.deleter
def value(self):  # Deleter
del self._value
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Advanced OOP concept (descriptor protocol)
- Multiple meanings of "property" in English
- Must check OOP terminology in target language
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While the concept of object properties is universal in OOP, the specific implementation as a decorator/descriptor is advanced. Must ensure translation captures "object characteristic" meaning, not real estate. Requires checking OOP educational materials in target language.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "object characteristic/attribute" concept?
- [ ] Distinguishable from real estate property?
- [ ] Recognized in OOP contexts?

### 2. Linguistic Correctness

- [ ] Noun form (not verb)?
- [ ] Appropriate for object attributes?
- [ ] Technical register?

### 3. Consistency

- [ ] Compatible with `class` terminology?
- [ ] Consistent with other decorators?
- [ ] Used in target language OOP materials?

### 4. Usability

- [ ] Concise (1-2 words)?
- [ ] Clear meaning?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues?

---

## Translation Output Format

**Your translation:**

```yaml
term: property
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
