# Python Keyword: `class` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** noun/verb
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `class` keyword in Python defines a new class - a blueprint for creating objects that bundles data (attributes) and behavior (methods) together. Classes are fundamental to object-oriented programming, enabling code organization through encapsulation, inheritance, and polymorphism.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Define a simple class
class Dog:
    def bark(self):
        print("Woof!")

my_dog = Dog()
my_dog.bark()  # Output: Woof!
```

**What this does:** `class` creates a new type called `Dog` with one method `bark()`. You can create instances (objects) of the class using `Dog()`. Each instance has access to the class's methods.

### Example 2: Common Pattern

```python
# Class with initialization and attributes
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hi, I'm {self.name}, {self.age} years old"

person = Person("Alice", 30)
print(person.greet())  # Output: Hi, I'm Alice, 30 years old
```

**What this does:** The `__init__` method initializes new instances with data. `self` refers to the instance being created. Attributes like `self.name` store data on each object. Methods can access and use this data.

### Example 3: Edge Case

```python
# Class with inheritance
class Animal:
    def __init__(self, species):
        self.species = species

class Cat(Animal):
    def meow(self):
        print(f"The {self.species} says meow")

cat = Cat("feline")
cat.meow()  # Output: The feline says meow
```

**What this shows:** Classes can inherit from other classes (shown in parentheses). `Cat` inherits attributes and methods from `Animal`, allowing code reuse and hierarchical organization.

---

## Pattern Classification

**This term is:** DEFINITION KEYWORD (Object-Oriented)

**Similar terms in this pattern:**

1. `def` - Defines functions (similar structure: keyword + name + body)
2. `object` - Base class all classes inherit from
3. `type` - Metaclass (class of a class)

**Pattern rule:** Definition keywords can use verb forms (action of defining) or noun forms (the thing being defined). For `class`, noun form is often more natural since "class" is both the action and the result.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `def` | definir | تعريف | 定义 | परिभाषित |
| `object` | objeto | كائن | 对象 | वस्तु |
| `class` | **clase** | **صنف** | **类** | **वर्ग** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "classis" meant "a group/division of people." Through French "classe," it became English "class" - a category or group sharing common characteristics. In programming, a class groups related data and functions.

**Why Python uses this:** "Class" is the standard term in object-oriented programming, borrowed from mathematical set theory and biological taxonomy. A class is a category/template; objects are specific instances of that category. Established by Simula and Smalltalk, most OOP languages use "class."

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `class` statement creates a new type in Python. It's a template that defines what attributes (data) and methods (functions) instances of that class will have. When you write `class Name:`, Python creates a class object that can be used to instantiate individual objects.

Classes enable object-oriented programming by bundling state and behavior. Attributes store data specific to each instance. Methods are functions that operate on that data. The special `__init__` method initializes new instances, and `self` parameter represents the instance being worked on.

Classes support inheritance: a class can inherit from parent classes, reusing their code. Multiple inheritance is allowed. Classes can override parent methods, call parent methods with `super()`, and define class variables (shared across all instances) vs. instance variables (unique per object).

**Key behaviors:**

1. **Creates new type:** `class` doesn't just group code; it creates an actual type. `isinstance(obj, MyClass)` checks if an object is an instance of a class. The class becomes a type in Python's type system.

2. **Instance vs. class scope:** Methods defined in a class receive `self` (the instance) as first parameter. Class methods use `@classmethod` decorator and receive the class. Static methods use `@staticmethod` and receive neither.

3. **Everything is an object:** In Python, classes themselves are objects (instances of `type`). You can assign classes to variables, pass them as arguments, and even modify them at runtime. This "classes as objects" principle is core to Python's object model.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (names a category/type)
- **Action vs State:** Primarily STATE (describes a category), though also ACTION (defines/creates)
- **Temporal aspect:** Timeless/definitional - a class is a permanent category

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "clase", "classe" - category/group |
| Germanic (de, nl, sv) | Noun | "Klasse", "klasse" - category (often capitalized in German) |
| Slavic (ru, pl, uk) | Noun | "класс", "klasa" - category/class |
| Arabic | Noun | "صنف" or "فئة" - category/type |
| Chinese | Noun | "类" - category/type |
| Hindi | Noun | "वर्ग" - class/category |

**Primary recommendation:** Use noun form meaning "class" or "category." This should be the same word used in social contexts (social class) or academic contexts (classroom, classification). The noun form is preferred because "class" names what's being created.

**Forms to AVOID:**

- ❌ Using verb "classify" - `class` names the category, not the action of categorizing
- ❌ Using "type" - while related, "type" is a separate Python concept
- ❌ Using "object" - objects are instances OF classes

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `clase`
- **Form:** Noun (feminine)
- **Why it works:** Standard Spanish noun for "class" - used in social classification, education, and programming. "Clase de objetos" (class of objects) is natural. Universally recognized in Spanish OOP contexts.

**Arabic:**

- **Translation:** `صنف` (ṣinf) or `فئة` (fi'ah)
- **Form:** Noun
- **Why it works:** "صنف" means category/type/class - standard in Arabic programming. "فئة" also means class/category. Both acceptable; `صنف` more common in CS. Clearly distinguishes from `كائن` (object - instance).

**Chinese:**

- **Translation:** `类` (lèi)
- **Form:** Noun
- **Why it works:** Standard Chinese for "category/class/type." Single character, concise. Established in Chinese OOP terminology. Related to `分类` (classification) but `类` alone is standard for programming classes.

**Hindi:**

- **Translation:** `वर्ग` (varga)
- **Form:** Noun
- **Why it works:** Sanskrit-derived noun meaning "class/category/group." Used in mathematics (sets), social contexts (social class), and programming. Formal register appropriate for technical contexts.

### ❌ Common Translation Mistakes

**Mistake 1: Using verb "classify" instead of noun "class"**

- **Wrong:** `clasificar` (Spanish - "to classify" - verb)
- **Why wrong:** The keyword creates a class (noun), not performs classification (verb). Though `class` involves categorization, the keyword names the category itself.
- **Right:** `clase` (noun)

**Mistake 2: Using "object" instead of "class"**

- **Wrong:** `objeto` (Spanish - "object")
- **Why wrong:** Objects are instances OF classes. Classes are templates; objects are specific instances. These are distinct concepts in OOP.
- **Right:** `clase` (the template/category)

**Mistake 3: Using "type" when class is more specific**

- **Wrong:** `tipo` (Spanish - "type")
- **Why wrong:** While classes create types, "type" is a separate Python concept (metaclass). "Class" is more specific for OOP contexts. Some languages might accept both, but distinguish if possible.
- **Right:** `clase` (specifically OOP class concept)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Social class" (economic group)
- ❌ Meaning 2: "Classroom" (physical space)
- ❌ Meaning 3: "Course/lesson" (educational session)
- ✅ Meaning 4: **CATEGORY/TEMPLATE** for creating objects (OOP)

**Example:**

English "class" can mean:

1. "Middle class family" (socioeconomic status) ❌
2. "Go to class tomorrow" (educational session) ❌
3. "`class Animal:` defines object template" (OOP category) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a blueprint/template/category for creating objects in object-oriented programming.**

Most languages use the same word for social class and OOP class, which is acceptable. Context makes the meaning clear.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `class`, check these translations:**

- [ ] `def` - Both define structures; should use compatible forms
- [ ] `object` - Classes create objects; relationship should be clear
- [ ] `type` - Related but distinct concept; avoid confusion

**Consistency rule:**

`class` and `def` are both definition keywords with similar structure: `keyword name: body`. They should feel cohesive. If `def` uses verb form, consider whether `class` should too (or whether noun form is more natural).

**Example:**

Spanish: `definir` (def - verb), `clase` (class - noun) - acceptable because "class" works better as noun ✅

### Functional relationships

**This term works WITH:**

1. **`class` + `__init__`**: Class with initialization

```python
class Person:
    def __init__(self, name):
        self.name = name
```

2. **`class` + inheritance**: Extending classes

```python
class Student(Person):
    pass
```

**Common pairing:**

```python
# basic class
class Animal:
    pass

# class with methods
class Dog:
    def bark(self):
        print("Woof")

# class with __init__
class Person:
    def __init__(self, name):
        self.name = name

# class with inheritance
class Employee(Person):
    def work(self):
        pass

# class with class variables
class Config:
    debug = True
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `class`

- Universal OOP concept
- "Class" is standard term across all OOP languages
- Well-established translations globally
- Same word often used in non-programming contexts

**For this term:** EASY

**Rationale:** Object-oriented programming classes are a universal concept. The word "class" (meaning category/group) exists in all languages from social and educational contexts. CS simply adopted this existing word, so translations are straightforward and well-established.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures OOP CLASS concept (template for objects)?
- [ ] Understood as category/blueprint, not instance?
- [ ] Distinct from "object" (instance) and "type" (metaclass)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun preferred)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python, unless language capitalizes nouns)?

### 3. Consistency

- [ ] Compatible with `def` and other definition keywords?
- [ ] Clear relationship to `object` (classes create objects)?
- [ ] Aligns with OOP terminology in target language?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word from other contexts)?

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
term: class
language: es
translation: clase
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "clase" is the standard noun for class in OOP, mathematics, and social contexts. It clearly represents a category/template for creating objects. Universally recognized in Spanish programming education and OOP literature.

**Alternatives considered:**

1. `clasificar` (to classify - verb) - Wrong part of speech; verb vs. noun
2. `tipo` (type) - Related but distinct concept in Python
3. `categoría` (category) - Too general; "clase" is established OOP term

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. OOP classes are universal, and "class" (category/group) is a common word in all languages with clear, established translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
