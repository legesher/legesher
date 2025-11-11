# Python Builtin: `classmethod` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** decorator
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`@classmethod` decorator creates a method that receives the class as its first argument instead of an instance, enabling class-level operations and alternative constructors.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic classmethod
class MyClass:
count = 0

@classmethod
def increment_count(cls):
cls.count += 1
return cls.count

MyClass.increment_count()  # Can call on class
print(MyClass.count)  # Output: 1

obj = MyClass()
obj.increment_count()  # Can also call on instance
print(MyClass.count)  # Output: 2
```

**What this does:** `@classmethod` makes a method receive the class (`cls`) as first argument instead of instance (`self`), allowing it to access class-level attributes and methods.

### Example 2: Common Pattern

```python
# Alternative constructor pattern
class Date:
def __init__(self, year, month, day):
self.year = year
self.month = month
self.day = day

@classmethod
def from_string(cls, date_string):
year, month, day = map(int, date_string.split('-'))
return cls(year, month, day)  # Create instance

@classmethod
def today(cls):
import datetime
today = datetime.date.today()
return cls(today.year, today.month, today.day)

# Usage
date1 = Date(2025, 1, 15)
date2 = Date.from_string('2025-01-15')  # Alternative constructor
date3 = Date.today()  # Another alternative constructor
```

**What this does:** Classmethods enable alternative constructors that create instances in different ways, providing clean factory methods instead of overloading `__init__`.

### Example 3: Edge Case

```python
# Classmethod with inheritance
class Animal:
species = "Unknown"

@classmethod
def get_species(cls):
return f"{cls.__name__}: {cls.species}"

class Dog(Animal):
species = "Canis familiaris"

class Cat(Animal):
species = "Felis catus"

print(Animal.get_species())  # Output: Animal: Unknown
print(Dog.get_species())  # Output: Dog: Canis familiaris
print(Cat.get_species())  # Output: Cat: Felis catus

# Note: cls is the actual calling class, not always Animal
```

**What this shows:** Classmethods receive the actual class that called them, not the class where they're defined, making them work correctly with inheritance and polymorphism.

---

## Pattern Classification

**This term is:** METHOD DECORATOR

**Similar terms in this pattern:**

1. `staticmethod` - Related decorator for static methods
2. `property` - Descriptor decorator for managed attributes
3. `def` - Regular method definition

**Pattern rule:** Method decorators should indicate the type of method they create, using compound terms or clear technical vocabulary.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `class` | clase | صنف | 类 | वर्ग |
| `def` | definir | تعريف | 定义 | परिभाषित |
| `classmethod` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** "class" + "method" (compound)

**Root meaning:** A method that belongs to/operates on the class itself rather than instances.

**Why Python uses this:** The name clearly describes what it is - a method for the class. Unlike instance methods (which operate on `self`), classmethods operate on `cls` (the class). The compound name makes this distinction explicit.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`@classmethod` is a decorator that transforms a regular method into a class method. While instance methods receive `self` (the instance) as their first argument, classmethods receive `cls` (the class) as their first argument. This lets them access class-level data and create instances.

The most common use case is alternative constructors - methods that create instances in different ways than `__init__`. For example, `from_string()`, `from_dict()`, `today()` etc. These are cleaner than trying to handle multiple scenarios in `__init__` or using different class names.

Classmethods work correctly with inheritance because `cls` refers to the actual class that called the method, not the class where the method was defined. This makes them useful for factory patterns and class-level operations that need to work with subclasses.

**Key behaviors:**

1. **Receives class as first argument:** `cls` parameter is automatically passed as the calling class, enabling class-level operations.
2. **Callable on class or instance:** Can be called as `Class.method()` or `instance.method()`, both receive the class.
3. **Inheritance-aware:** `cls` is the actual calling class, making classmethods work correctly in inheritance hierarchies.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (type of method)
- **Action vs State:** DESCRIPTOR - describes what kind of method this is
- **Temporal aspect:** N/A (it's a type descriptor)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound: class + method | Método de clase, méthode de classe |
| Germanic (de, nl, sv) | Compound noun | Klassenmethode (natural compounds) |
| Slavic (ru, pl, uk) | Compound with class + method | Technical compound |
| Arabic | Compound: class + method | Descriptive compound |
| Chinese | Compound noun | 类方法 (class method) |
| Hindi | Compound | वर्ग विधि (class method) |

**Primary recommendation:** Create a compound combining translations of "class" and "method". The relationship should be clear - this is a method that belongs to/operates on the class level.

**Forms to AVOID:**

- ❌ Just "method" - needs "class" qualifier
- ❌ Just "class" - needs "method" specification
- ❌ Verb forms - this is a noun (type of method)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `método_clase` or `métodoclase`
- **Form:** Compound noun
- **Why it works:** Clear compound of "método" (method) + "clase" (class), immediately understood as class-level method

**Arabic:**

- **Translation:** `دالة_صنف` (dāllat ṣinf - class function/method)
- **Form:** Compound noun
- **Why it works:** Technical compound combining class + method concepts, clear in CS context

**Chinese:**

- **Translation:** `类方法` (lèi fāngfǎ - class method)
- **Form:** Compound noun
- **Why it works:** Standard CS term for classmethod, widely used in Chinese Python documentation

**Hindi:**

- **Translation:** `वर्ग_विधि` (varga vidhi - class method)
- **Form:** Compound noun
- **Why it works:** Clear Sanskrit-derived compound, professional and precise

### ❌ Common Translation Mistakes

**Mistake 1: Using just "method"**

- **Wrong:** `método` (Spanish - just "method")
- **Why wrong:** Doesn't distinguish from regular instance methods
- **Right:** `método_clase` (class method)

**Mistake 2: Wrong word order or relationship**

- **Wrong:** `clase_de_método` (Spanish - "type of method")
- **Why wrong:** Sounds like a category/type rather than a class-level method
- **Right:** `método_clase` (method of/for class)

**Mistake 3: Too verbose**

- **Wrong:** `método_que_pertenece_a_clase` (Spanish - "method that belongs to class")
- **Why wrong:** Way too long for a frequently used decorator
- **Right:** `método_clase` (concise)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "classmethod" is unambiguous in Python

**Single technical meaning:**

✅ **Python meaning:** A method decorator that makes the method receive the class as its first argument instead of an instance.

The term is a Python-specific compound with one clear meaning. Your translation should be a clear compound of "class" + "method" in the target language.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `classmethod`, check these translations:**

- [ ] `class` - MUST use the same class translation in compound
- [ ] `def` / method - Should use consistent term for "method"
- [ ] `staticmethod` - Parallel decorator, should use same compound pattern
- [ ] `property` - Related decorator, compatible style

**Consistency rule:**

The method decorators (`@classmethod`, `@staticmethod`, `@property`) should follow consistent naming patterns. If using compounds, use compounds for all. If using underscores, use consistently.

**Example:**

✅ **Consistent:**

- `class` → `clase`
- `classmethod` → `método_clase`
- `staticmethod` → `método_estático`
- Consistent compound pattern ✅

❌ **Inconsistent:**

- `classmethod` → `método_clase` (underscore compound)
- `staticmethod` → `metodoestático` (no underscore)
- Inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **`@classmethod` + `cls` parameter**: Always receives class as first argument
2. **`class` definition**: Classmethods defined within classes

**Common pairing:**

```python
# Always used with cls parameter
class Example:
@classmethod
def method(cls):  # cls is the class
pass
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Advanced OOP concept
- Compound term requiring consistent parts
- Must align with `class` and method terminology
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While the concept is straightforward (class-level method), creating a natural compound in the target language requires understanding of both "class" and "method" translations and ensuring consistency with `staticmethod` and other decorators.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clearly a compound of "class" + "method"?
- [ ] Distinguishable from instance methods?
- [ ] Recognized in OOP contexts?

### 2. Linguistic Correctness

- [ ] Proper compound structure for target language?
- [ ] Uses correct "class" translation?
- [ ] Uses correct "method" term?

### 3. Consistency

- [ ] Matches `class` translation?
- [ ] Parallel structure to `staticmethod`?
- [ ] Compatible with other decorators?

### 4. Usability

- [ ] Reasonably concise (2-3 words max)?
- [ ] Easy to understand?
- [ ] Clear class-level meaning?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] Works with @ decorator syntax?

---

## Translation Output Format

**Your translation:**

```yaml
term: classmethod
language: {es|ar|zh|hi}
translation: {your_translation}
form: {compound_noun}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you created a compound from "class" + "method" translations. Mention if this pattern is used in OOP education in target language.}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Need to verify compound structure, check consistency with `staticmethod`}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
