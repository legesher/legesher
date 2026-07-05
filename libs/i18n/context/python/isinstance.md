# Python Builtin: `isinstance` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`isinstance()` checks if an object is an instance of a class or tuple of classes, returning True or False, the preferred way to check object types in Python.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic type checking
x = 42
print(isinstance(x, int))  # Output: True
print(isinstance(x, str))  # Output: False

name = "Alice"
print(isinstance(name, str))  # Output: True
```

**What this does:** `isinstance(object, class)` checks if an object is an instance of a specific class, returning True if it is, False otherwise.

### Example 2: Common Pattern

```python
# Multiple type checking with tuple
def process_value(value):
if isinstance(value, (int, float)):
return value * 2
elif isinstance(value, str):
return value.upper()
elif isinstance(value, list):
return len(value)
else:
return None

print(process_value(10))  # Output: 20
print(process_value("hello"))  # Output: HELLO
print(process_value([1, 2, 3]))  # Output: 3
```

**What this does:** Pass a tuple of classes to check if an object is an instance of any of them, cleaner than multiple `or` conditions.

### Example 3: Edge Case

```python
# Works with inheritance
class Animal:
pass

class Dog(Animal):
pass

dog = Dog()
print(isinstance(dog, Dog))  # Output: True
print(isinstance(dog, Animal))  # Output: True (inheritance!)
print(isinstance(dog, object))  # Output: True (everything inherits from object)

# Difference from type()
print(type(dog) == Dog)  # Output: True
print(type(dog) == Animal)  # Output: False (type() doesn't consider inheritance)

# Use isinstance, not type checking
if isinstance(dog, Animal):  # ✅ Correct - considers inheritance
print("It's an animal")

if type(dog) == Animal:  # ❌ Wrong - doesn't consider inheritance
print("This won't print")
```

**What this shows:** `isinstance()` respects inheritance - subclass instances are considered instances of parent classes. This is why `isinstance()` is preferred over `type()` comparisons.

---

## Pattern Classification

**This term is:** TYPE CHECKING FUNCTION (Compound term)

**Similar terms in this pattern:**

1. `issubclass` - Checks if a class is a subclass of another
2. `type` - Returns the type of an object
3. `hasattr` - Checks if object has an attribute

**Pattern rule:** Introspection functions using "is" + noun pattern should indicate what they check. The "is" suggests a boolean return.


---

## Etymology (Brief)

**English Origin:** "is" + "instance" (compound)

**Root meaning:** "Instance" from Latin "instantia" (presence, example). In OOP, an "instance" is a concrete occurrence of a class.

**Why Python uses this:** The name is self-explanatory - checks if something "is" an "instance" of a class. The compound verb-noun structure makes the function's purpose immediately clear. Replaces older type-checking patterns with a more object-oriented approach.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`isinstance()` checks whether an object is an instance of a specified class or any class in a tuple of classes. It returns a boolean (True/False) and is the recommended way to perform type checking in Python because it respects inheritance.

Unlike `type()` which returns the exact type, `isinstance()` considers the entire inheritance hierarchy. If you check `isinstance(dog, Animal)` where Dog inherits from Animal, it returns True. This is crucial for polymorphism - code should work with any subclass, not just the exact type.

The function accepts either a single class or a tuple of classes. When given a tuple, it returns True if the object is an instance of any of the classes, equivalent to `isinstance(obj, Class1) or isinstance(obj, Class2)` but more efficient and readable.

**Key behaviors:**

1. **Respects inheritance:** Returns True for parent classes, making it work correctly with polymorphism and subclassing.
2. **Tuple support:** Can check multiple classes at once with `isinstance(obj, (Class1, Class2, Class3))`, cleaner than multiple `or` conditions.
3. **Preferred over type():** `isinstance()` is the Pythonic way to check types because it works with inheritance, while `type(obj) == Class` fails for subclasses.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb+noun functioning as function name
- **Action vs State:** QUERY - asks a question and returns boolean
- **Temporal aspect:** Instantaneous check

### Recommended Form

**Primary recommendation:** Create compound from "is" (verb) + "instance" (noun), maintaining the verb-noun structure. Should read naturally as "is [an] instance [of]".

**Forms to AVOID:**

- ❌ Reversing to "instance is" - wrong word order
- ❌ Using only "is" or only "instance" - both parts needed
- ❌ Not matching the `is` keyword translation - should be consistent

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "isinstance" is unambiguous in Python

**Single technical meaning:**

✅ **Python meaning:** A function that checks if an object is an instance of a specified class or classes, returning a boolean.

The compound term is Python-specific with one clear meaning. Your translation should clearly compound "is" + "instance" in natural word order for the target language.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `isinstance`, check these translations:**

- [ ] `is` - MUST use same verb in compound
- [ ] `issubclass` - Parallel function, should use same "is" + different noun pattern
- [ ] `class` - For understanding what "instance" relates to
- [ ] `type` - Related type-checking function

**Consistency rule:**

The "is*" functions (`isinstance`, `issubclass`) MUST use the same verb translation as the `is` keyword:

- Whatever copula/verb the pack chose for `is`, `isinstance` must reuse it verbatim - if the language distinguishes several "to be" verbs, do not switch to a different one
- Do not substitute a "check/verify" verb - the name asserts identity of kind, not the act of checking

**Example:**

✅ **Consistent:**

- `is` → the pack's copula
- `isinstance` → that copula + "instance" noun
- `issubclass` → that copula + "subclass" noun
- All use the same verb ✅

❌ **Inconsistent:**

- `is` → the pack's copula
- `isinstance` → a "verify"-verb compound (different verb!)
- Inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **`isinstance` + class names**: Checks against specific classes
2. **`isinstance` + tuple of classes**: Checks multiple types
3. **`isinstance` vs `type`**: isinstance preferred for inheritance

**Common pairing:**

```python
# Type checking pattern
if isinstance(obj, (int, float)):
# Handle numeric types

# Inheritance-aware checking
if isinstance(obj, BaseClass):
# Works for BaseClass and all subclasses
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Compound term requiring two parts
- Must align with `is` keyword translation
- Must parallel `issubclass` pattern
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While conceptually straightforward, creating a natural compound that maintains consistency with both the `is` keyword and the parallel `issubclass` function requires careful attention to linguistic patterns and OOP terminology.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clear compound of "is" + "instance"?
- [ ] Conveys type-checking concept?
- [ ] Would OOP developers understand this checks instance membership?

### 2. Linguistic Correctness

- [ ] Uses same verb as `is` keyword?
- [ ] Natural compound structure for target language?
- [ ] Proper word order (typically verb-noun)?

### 3. Consistency

- [ ] Matches `is` keyword translation?
- [ ] Parallel structure to `issubclass`?
- [ ] Compatible with OOP terminology?

### 4. Usability

- [ ] Concise (1-2 words, compound acceptable)?
- [ ] Easy to remember?
- [ ] Clear what it checks?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues with compound structure?

---

## Translation Output Format

**Your translation:**

```yaml
term: isinstance
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
