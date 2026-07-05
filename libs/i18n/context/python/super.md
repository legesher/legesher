# Python Builtin Function: `super` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `super()` function in Python returns a proxy object that delegates method calls to a parent or sibling class. Used primarily in inheritance to call parent class methods without hardcoding parent names, enabling proper method resolution order (MRO) in single and multiple inheritance scenarios.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic parent method call
class Animal:
def __init__(self, name):
self.name = name

class Dog(Animal):
def __init__(self, name, breed):
super().__init__(name)
self.breed = breed

dog = Dog("Buddy", "Golden Retriever")
print(dog.name)  # Output: Buddy
```

**What this does:** `super().__init__(name)` calls the parent class's `__init__` method. This initializes the parent class attributes before adding child-specific ones. Cleaner than `Animal.__init__(self, name)`.

### Example 2: Common Pattern

```python
# Method override with parent call
class Employee:
def work(self):
return "Working"

class Manager(Employee):
def work(self):
parent_work = super().work()
return f"{parent_work} and managing team"

manager = Manager()
print(manager.work())  # Output: Working and managing team

# Multiple methods
class Vehicle:
def start(self):
return "Engine starting"
def status(self):
return "Ready"

class ElectricCar(Vehicle):
def start(self):
return f"{super().start()} silently"
def status(self):
return f"{super().status()} - Battery charged"

car = ElectricCar()
print(car.start())  # Output: Engine starting silently
print(car.status())  # Output: Ready - Battery charged
```

**What this does:** `super()` lets you extend parent methods rather than completely replacing them. Call `super().method()` to get parent behavior, then add child-specific behavior. Common for customization with inheritance.

### Example 3: Edge Case

```python
# Multiple inheritance (diamond problem)
class A:
def process(self):
return "A"

class B(A):
def process(self):
return f"B -> {super().process()}"

class C(A):
def process(self):
return f"C -> {super().process()}"

class D(B, C):
def process(self):
return f"D -> {super().process()}"

d = D()
print(d.process())  # Output: D -> B -> C -> A
print(D.__mro__)  # Method Resolution Order: D, B, C, A, object

# Cooperative multiple inheritance
class LogMixin:
def save(self):
print(f"Logging: {self.__class__.__name__}")
return super().save()

class DatabaseMixin:
def save(self):
print("Saving to database")
return "Saved"

class Model(LogMixin, DatabaseMixin):
pass

model = Model()
model.save()
# Output: Logging: Model
# Output: Saving to database
```

**What this shows:** `super()` follows Python's Method Resolution Order (MRO) for multiple inheritance. In diamond patterns, it ensures each parent is called exactly once. Enables cooperative multiple inheritance where mixins call the next class in the chain.

---

## Pattern Classification

**This term is:** PROXY FUNCTION (Inheritance/Object-Oriented)

**Similar terms in this pattern:**

1. `class` - Defines classes that can be inherited
2. `isinstance` - Checks if object is instance of class
3. `issubclass` - Checks if class inherits from another

**Pattern rule:** Inheritance-related terms should convey hierarchical relationships. "super" implies "above" or "parent" in hierarchy. Translations should capture upward relationship in class hierarchy.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "super" meaning "above, over, beyond." In OOP context, refers to the parent class "above" the current class in the inheritance hierarchy.

**Why Python uses this:** "super" conveys the hierarchical relationship - parent classes are conceptually "above" child classes. Short, intuitive term borrowed from mathematical/academic notation. Python 3 simplified syntax from `super(ClassName, self)` to just `super()`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `super()` function returns a temporary proxy object that allows you to call methods from a parent class. It uses Python's Method Resolution Order (MRO) to determine which parent method to call, crucial for proper multiple inheritance behavior.

Without `super()`, you'd hardcode parent names: `ParentClass.method(self)`. Problems: breaks when changing inheritance, doesn't work well with multiple inheritance, tightly couples child to parent. With `super()`, Python automatically handles the lookup, follows MRO correctly, and supports cooperative multiple inheritance.

Common use cases: calling parent `__init__` to initialize inherited attributes, extending parent methods (call parent, then add behavior), cooperative multiple inheritance with mixins, avoiding hardcoded parent class names for flexibility.

**Key behaviors:**

1. **Follows MRO:** Doesn't just call immediate parent - follows Method Resolution Order. In multiple inheritance, calls next class in MRO chain, not necessarily direct parent. View MRO with `ClassName.__mro__`.

2. **Parameterless in Python 3:** `super()` with no arguments works inside methods. Python automatically determines class and instance. Legacy: `super(ClassName, self)` still works but unnecessary.

3. **Returns proxy object:** Doesn't return parent class directly - returns proxy that delegates to next in MRO. Enables cooperative multiple inheritance where each class calls super, forming chain.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (refers to parent/superior class)
- **Action vs State:** REFERENCE - points to parent class
- **Temporal aspect:** Instantaneous - resolves parent at call time

### Recommended Form

**Primary recommendation:** Use term meaning "above," "parent," or "superior" - captures hierarchical relationship. Can keep English "super" if widely adopted in target language's CS education.

**Forms to AVOID:**

- ❌ Action verbs - "super" is not an action, it's a reference
- ❌ Terms meaning "better" without hierarchy implication
- ❌ Long phrases - should be short and memorable

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Excellent or outstanding ("super cool") - informal quality
- ❌ Meaning 2: Superhero prefix ("Superman") - fictional enhancement
- ✅ Meaning 3: Above or over ("supervisor") - **This is the Python meaning** - hierarchical position

**Example:**

English "super" can mean:

1. Excellent/great quality ("That's super!") ❌
2. Enhanced powers ("superhero") ❌
3. Above in hierarchy ("supervisor", "superstructure") ✅ **This is the Python meaning**

**Your translation should capture meaning #3 (hierarchical above), NOT the others.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `super`, check these translations:**

- [ ] `class` - Super refers to parent class, should use related terminology
- [ ] `isinstance` - Related OOP introspection, should align in register
- [ ] `issubclass` - Related inheritance checking, compatible hierarchy terms

**Consistency rule:**

Object-oriented terms should use consistent metaphors. If "class" uses formal OOP terminology, "super" should too. If using hierarchical terms ("parent," "above"), be consistent across inheritance-related functions.


### Functional relationships

**This term works WITH:**

1. **`super()` + `__init__`**: Initialize parent class

```python
class Child(Parent):
def __init__(self):
super().__init__()
```

2. **`super()` + method override**: Extend parent method

```python
class Child(Parent):
def method(self):
result = super().method()
return result + " extended"
```

**Common pairing:**

```python
# Initialization pattern
class Animal:
def __init__(self, name):
self.name = name

class Dog(Animal):
def __init__(self, name, breed):
super().__init__(name)  # Common pairing
self.breed = breed

# Method extension pattern
class Employee:
def work(self):
return "Working"

class Manager(Employee):
def work(self):
return f"{super().work()} and managing"  # Common pairing

# Multiple inheritance
class A:
def process(self):
return "A"

class B(A):
def process(self):
return f"B-{super().process()}"  # Cooperative inheritance

class C(A):
def process(self):
return f"C-{super().process()}"

class D(B, C):
def process(self):
return f"D-{super().process()}"  # Follows MRO
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options available
- Context helps decide
- May need to choose between cognates
- Some languages have direct equivalent, others need construction
- **AI confidence should be MEDIUM-HIGH with context**

**For this term:** MEDIUM

**Rationale:** "super" has clear hierarchical meaning but multiple translation strategies. Some languages can use "super" directly (loanword), others need native terms for "above/parent." Must balance technical accuracy, brevity, and CS education alignment.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key considerations: Check if "super" is used in target language CS education. If so, may keep English term. If not, find short native term conveying hierarchical "above" relationship.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures PARENT CLASS REFERENCE concept?
- [ ] Conveys hierarchical "above" relationship?
- [ ] Understood as accessing parent methods?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/adjective, not verb)?
- [ ] Appropriate form for referring to parent class?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Aligns with `class` terminology?
- [ ] Compatible with inheritance-related terms?
- [ ] Matches OOP vocabulary in target language?

### 4. Usability

- [ ] Short (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Memorable?

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
term: super
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
