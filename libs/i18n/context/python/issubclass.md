# Python Builtin: `issubclass` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`issubclass()` checks if a class is a subclass of another class or tuple of classes, returning True or False, used for checking class inheritance relationships.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic subclass checking
class Animal:
pass

class Dog(Animal):
pass

print(issubclass(Dog, Animal))  # Output: True
print(issubclass(Animal, Dog))  # Output: False
print(issubclass(Dog, Dog))  # Output: True (class is subclass of itself)
```

**What this does:** `issubclass(Class1, Class2)` checks if Class1 is a subclass of Class2, returning True if it is (including if they're the same class).

### Example 2: Common Pattern

```python
# Multiple class checking with tuple
class Mammal:
pass

class Bird:
pass

class Dog(Mammal):
pass

class Cat(Mammal):
pass

class Eagle(Bird):
pass

# Check if subclass of any in tuple
print(issubclass(Dog, (Mammal, Bird)))  # Output: True (Dog is Mammal)
print(issubclass(Eagle, (Mammal, Bird)))  # Output: True (Eagle is Bird)
print(issubclass(int, (str, list)))  # Output: False

# Useful for plugin systems
def register_plugin(plugin_class):
if issubclass(plugin_class, (Mammal, Bird)):
print(f"Registered: {plugin_class.__name__}")
else:
raise TypeError("Must inherit from Mammal or Bird")

register_plugin(Dog)  # Works
register_plugin(Cat)  # Works
```

**What this does:** Pass a tuple of classes to check if a class inherits from any of them, useful for validation and plugin systems.

### Example 3: Edge Case

```python
# All classes inherit from object
class MyClass:
pass

print(issubclass(MyClass, object))  # Output: True
print(issubclass(int, object))  # Output: True
print(issubclass(str, object))  # Output: True

# Difference between isinstance and issubclass
dog_instance = Dog()
print(isinstance(dog_instance, Animal))  # True (instance check)
print(issubclass(Dog, Animal))  # True (class check)

# issubclass requires classes, not instances
try:
issubclass(dog_instance, Animal)  # TypeError!
except TypeError as e:
print(f"Error: {e}")  # issubclass() arg 1 must be a class

# Use isinstance for objects, issubclass for classes
```

**What this shows:** `issubclass()` checks class relationships (is one class derived from another), while `isinstance()` checks object membership (is an object an instance of a class). All classes inherit from `object` in Python 3.

---

## Pattern Classification

**This term is:** TYPE CHECKING FUNCTION (Compound term)

**Similar terms in this pattern:**

1. `isinstance` - Checks if object is instance of class
2. `type` - Returns the type of an object
3. `hasattr` - Checks if object has an attribute

**Pattern rule:** Introspection functions using "is" + noun pattern should indicate what they check. Must be parallel to `isinstance`.


---

## Etymology (Brief)

**English Origin:** "is" + "subclass" (compound)

**Root meaning:** "Subclass" from "sub" (under, below) + "class". In OOP, a subclass is a class derived from another class (the parent/base class).

**Why Python uses this:** Parallel to `isinstance()` - checks if something "is" a "subclass" of another class. The compound verb-noun structure matches `isinstance` and makes the function's purpose immediately clear. Essential for checking inheritance hierarchies.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`issubclass()` checks whether one class is derived from another class (or any class in a tuple of classes). It returns True if the first class is a subclass of the second, including the case where they're the same class. A class is considered a subclass of itself.

This is the class-level equivalent of `isinstance()`. While `isinstance()` checks if an object is an instance of a class, `issubclass()` checks if a class inherits from another class. This is crucial for understanding inheritance relationships without needing to create instances.

The function accepts a tuple of classes for the second argument, returning True if the first class is a subclass of any class in the tuple. This is useful in plugin systems, factory patterns, and anywhere you need to validate that a class has the correct inheritance structure before using it.

**Key behaviors:**

1. **Class relationships only:** Both arguments must be classes (not instances). Passing an instance raises TypeError.
2. **Reflexive:** A class is considered a subclass of itself - `issubclass(X, X)` is always True.
3. **Tuple support:** Can check multiple parent classes at once with `issubclass(Child, (Parent1, Parent2))`, returning True if Child inherits from any of them.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb+noun functioning as function name
- **Action vs State:** QUERY - asks a question and returns boolean
- **Temporal aspect:** Instantaneous check

### Recommended Form

**Primary recommendation:** Create compound from "is" (verb) + "subclass" (noun), maintaining exact parallel structure to `isinstance`. Should use same "is" verb and similar compound pattern.

**Forms to AVOID:**

- ❌ Different pattern from `isinstance` - MUST be parallel
- ❌ Using different verb than `is` keyword - inconsistent
- ❌ Reversing to "subclass is" - wrong word order

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "issubclass" is unambiguous in Python

**Single technical meaning:**

✅ **Python meaning:** A function that checks if one class is a subclass of another class or classes, returning a boolean.

The compound term is Python-specific with one clear meaning. Your translation should clearly compound "is" + "subclass" in natural word order, parallel to `isinstance`.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `issubclass`, check these translations:**

- [ ] `is` - MUST use exact same verb as in `isinstance`
- [ ] `isinstance` - MUST have parallel structure (same verb, similar pattern)
- [ ] `class` - For understanding what "subclass" relates to
- [ ] `super` - Related to inheritance hierarchy

**Consistency rule:**

CRITICAL: `isinstance` and `issubclass` MUST use identical verb translation (the `is` part) and parallel structure:

- Whatever form `isinstance` takes, `issubclass` must mirror it exactly, swapping only the noun
- Same verb, same structure, different noun

**Example:**

✅ **Consistent (Perfect parallel):**

- `is` → the pack's copula
- `isinstance` → that copula + "instance" noun
- `issubclass` → that copula + "subclass" noun
- Perfect parallel structure ✅

❌ **Inconsistent:**

- `isinstance` → copula + "instance" noun
- `issubclass` → a "verify"-verb compound
- Different verbs ❌

### Functional relationships

**This term works WITH:**

1. **`issubclass` + class names**: Checks class inheritance
2. **`isinstance` for comparison**: Different but related checking
3. **`super` in context**: Both relate to inheritance

**Common pairing:**

```python
# Class hierarchy checking
if issubclass(MyClass, BaseClass):
# MyClass inherits from BaseClass

# Validation before use
def factory(cls):
if not issubclass(cls, RequiredBase):
raise TypeError("Must inherit from RequiredBase")
return cls()
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Compound term requiring two parts
- MUST be perfectly parallel to `isinstance`
- Must align with `is` keyword translation
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** Must maintain perfect parallelism with `isinstance` while correctly translating "subclass". The consistency requirement is absolute - any deviation from the `isinstance` pattern creates confusion.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clear compound of "is" + "subclass"?
- [ ] Conveys inheritance checking concept?
- [ ] Distinguishable from `isinstance` (checks classes not instances)?

### 2. Linguistic Correctness

- [ ] Uses EXACT same verb as `isinstance`?
- [ ] PERFECTLY parallel structure to `isinstance`?
- [ ] Proper word order for target language?

### 3. Consistency

- [ ] Matches `is` keyword translation?
- [ ] PERFECT parallel to `isinstance` structure?
- [ ] Compatible with OOP/inheritance terminology?

### 4. Usability

- [ ] Concise (1-2 words, compound acceptable)?
- [ ] Easy to remember alongside `isinstance`?
- [ ] Clear what it checks?

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
term: issubclass
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
