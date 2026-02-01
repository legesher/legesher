# Python Builtin Function: `type` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (introspection function)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `type` function in Python returns the type/class of an object. It's used for type checking and introspection, telling you what kind of object you're working with (int, str, list, etc.).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Check the type of different objects
x = 42
print(type(x))  # <class 'int'>

name = "Alice"
print(type(name))  # <class 'str'>
```

**What this does:** Returns the type/class of the given object. Every Python object has a type, and `type()` reveals it.

### Example 2: Common Pattern

```python
# Type checking
value = 3.14
if type(value) == float:
    print("It's a float!")

# Better way using isinstance()
if isinstance(value, float):
    print("It's a float!")

# Check multiple objects
items = [42, "hello", 3.14, True, [1, 2, 3]]
for item in items:
    print(f"{item}: {type(item).__name__}")
# Output:
# 42: int
# hello: str
# 3.14: float
# True: bool
# [1, 2, 3]: list
```

**What this does:** Demonstrates type checking. Note: `isinstance()` is usually better than `type() ==` because it handles inheritance properly.

### Example 3: Edge Case

```python
# type() can also create new classes (advanced)
# Creating a new class dynamically
MyClass = type('MyClass', (), {'x': 5})
obj = MyClass()
print(obj.x)  # 5

# type() returns the class, not a string
result = type(42)
print(result)        # <class 'int'>
print(result == int) # True

# Everything has a type, even type itself
print(type(type))    # <class 'type'>
```

**What this shows:** `type()` can both inspect types and create new classes (metaclass functionality). Type objects are first-class objects that can be compared and manipulated.

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Query/Inspection)

**Similar terms in this pattern:**

1. `isinstance` - Checks if object is instance of class
2. `issubclass` - Checks if class is subclass of another
3. `id` - Returns unique identifier of object
4. `dir` - Lists attributes/methods of object

**Pattern rule:** Introspection functions should use noun forms or verb forms that suggest querying/examining rather than modifying. These functions inspect objects without changing them.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `isinstance` | es_instancia | هو_نموذج | 属于实例 | उदाहरण_है |
| `id` | identificador | معرّف | 标识 | पहचान |
| `type` | **tipo** | **نوع** | **类型** | **प्रकार** |

---

## Etymology (Brief)

**English Origin:** Greek/Latin

**Root meaning:** From Greek "typos" (impression, figure, type) through Latin "typus." Originally meant a physical impression or stamp. In computing, "type" refers to the category or kind of data (data type).

**Why Python uses this:** "Type" is the universal term in computer science for data classification (integer type, string type, etc.). Every programming language uses "type" or its translation to categorize data. Python's `type()` function reveals this classification.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `type()` function serves two purposes: (1) returning the type/class of an object (most common use), and (2) dynamically creating new classes (advanced metaclass programming). When called with one argument `type(obj)`, it returns the object's type as a type object. This is Python's built-in way to ask "what kind of object is this?"

Every object in Python has a type: `42` is type `int`, `"hello"` is type `str`, `[1,2,3]` is type `list`. The `type()` function returns the actual class object, not a string. You can compare it: `type(42) == int` is `True`.

While useful for debugging and introspection, for type checking it's usually better to use `isinstance()` instead because it respects inheritance. `type(obj) == list` only matches lists exactly, while `isinstance(obj, list)` also matches list subclasses.

**Key behaviors:**

1. **Returns type object:** `type()` returns the actual class/type object, not a string. `type(42)` returns `<class 'int'>`, which is the `int` class itself. You can use this object to create instances: `type(42)(100)` creates integer 100.

2. **Works on everything:** Every Python object has a type, including functions, modules, and types themselves. `type(type)` returns `<class 'type'>` (type is an instance of itself, as the metaclass).

3. **Exact matching:** `type(obj) == SomeClass` checks exact type match, not inheritance. For a list subclass, `type(obj) == list` is False even though it's list-like. Use `isinstance()` for inheritance-aware checks.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (represents a category/classification)
- **Action vs State:** STATE - describes what category something belongs to
- **Temporal aspect:** Instantaneous - queries current state

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "tipo", "type" - classification/kind |
| Germanic (de, nl, sv) | Noun | "Typ", "type" - kind/category |
| Slavic (ru, pl, uk) | Noun | "тип", "typ" - type/kind |
| Arabic | Noun | "نوع" - type/kind/species |
| Chinese | Noun compound | "类型" - category/type |
| Hindi | Noun | "प्रकार" - type/kind |

**Primary recommendation:** Use the standard word for "type," "kind," or "category" in the target language. This is a universal computing concept with established translations in all languages.

**Forms to AVOID:**

- ❌ Using verb "to type" (as in typing on keyboard)
- ❌ Using "typewrite" or "typography" meanings
- ❌ Using overly specific terms when general "type/kind" exists

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `tipo`
- **Form:** Noun (masculine)
- **Why it works:** Standard Spanish word for "type," "kind," or "category." Used universally in Spanish computer science for data types. Clear, concise, and immediately understood by Spanish programmers.

**Arabic:**

- **Translation:** `نوع` (nawʿ)
- **Form:** Noun (masculine)
- **Why it works:** Arabic word for type, kind, or species. Standard term in Arabic computing for data types. Used in Arabic CS education and technical documentation. Concise and clear.

**Chinese:**

- **Translation:** `类型` (lèixíng)
- **Form:** Noun compound
- **Why it works:** Two characters: 类 (category/class) + 型 (model/type). Standard Chinese computing term for "type." Used consistently in Chinese Python documentation and CS education.

**Hindi:**

- **Translation:** `प्रकार` (prakār)
- **Form:** Noun
- **Why it works:** Sanskrit-derived Hindi word meaning type, kind, or category. Standard term in Hindi CS education for data types. Clear technical term that aligns with formal Hindi computing vocabulary.

### ❌ Common Translation Mistakes

**Mistake 1: Confusing with "to type" (keyboard)**

- **Wrong:** `escribir` (Spanish - "to write/type on keyboard")
- **Why wrong:** This is the verb meaning to type on a keyboard, not the noun meaning category/classification. Wrong meaning entirely.
- **Right:** `tipo` (noun: type/kind/category)

**Mistake 2: Using overly specific biological term**

- **Wrong:** `especie` (Spanish - "species")
- **Why wrong:** While "type" and "species" are related concepts, "especie" is too biological. "Tipo" is the correct general computing term for data types.
- **Right:** `tipo` (general type/category)

**Mistake 3: Using "class" when "type" is more precise**

- **Wrong:** `clase` (Spanish - "class")
- **Why wrong:** While Python types are classes, `type()` is the function name and "tipo" is the standard term. "Clase" should be reserved for translating `class` keyword.
- **Right:** `tipo` (type, not class specifically)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "To type on a keyboard" (verb: input text)
- ❌ Meaning 2: "Typography" (printing/font styles)
- ❌ Meaning 3: "Type specimen" (biology: representative example)
- ✅ Meaning 4: **DATA TYPE / CATEGORY** (computing: classification of data)

**Example:**

English "type" can mean:

1. "Type your name here" (keyboard input) ❌
2. "Beautiful type design" (typography/fonts) ❌
3. "Type specimen in biology" (representative example) ❌
4. "`type(42)` returns `<class 'int'>`" ✅ **This is the Python meaning**

**Your translation should capture meaning #4: data type/category—the classification that determines what kind of data an object represents and what operations are valid.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `type`, check these translations:**

- [ ] `class` - Related concept; types and classes are closely related in Python
- [ ] `isinstance` - Type-checking function; should feel related
- [ ] `int`, `str`, `float` - These are all types; relationship should be clear
- [ ] `object` - Base type; should use compatible noun form

**Consistency rule:**

Type-related functions and type names should all use noun forms. They describe categories and classifications, not actions.

**Example:**

Spanish: `tipo`, `clase`, `entero`, `cadena` - all nouns ✅
NOT: `tipo` (noun) + `verificar_tipo` (verb phrase in function name) ❌

### Functional relationships

**This term works WITH:**

1. **Type checking**: Determining object types

```python
x = 42
if type(x) == int:  # Check exact type
    print("Integer")

# Better with isinstance (handles inheritance)
if isinstance(x, int):
    print("Integer")
```

2. **Type introspection**: Exploring object types

```python
items = [1, "hello", 3.14, [], {}]
for item in items:
    print(type(item))
```

**Common pairing:**

```python
# Basic type checking
x = 42
print(type(x))  # <class 'int'>
print(type(x) == int)  # True

# Get type name as string
print(type(x).__name__)  # 'int'

# Check multiple types
data = [42, "hello", 3.14, True, [1, 2]]
for item in data:
    t = type(item)
    print(f"{item} is {t.__name__}")

# Type comparison
a = [1, 2, 3]
b = [4, 5, 6]
print(type(a) == type(b))  # True (both lists)

# isinstance is usually better for type checking
value = 42
if isinstance(value, int):  # Preferred
    print("It's an integer")

# Checking multiple types
if isinstance(value, (int, float)):  # int OR float
    print("It's a number")

# type() with classes you define
class MyClass:
    pass

obj = MyClass()
print(type(obj))  # <class '__main__.MyClass'>
print(type(obj) == MyClass)  # True

# Advanced: type() can create classes (metaclass usage)
# type(name, bases, dict) creates a new class
NewClass = type('NewClass', (), {'x': 10})
instance = NewClass()
print(instance.x)  # 10
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Universal computing concept
- Standard term in all programming languages
- Clear meaning in technical contexts
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Type" as a data classification is a fundamental concept in computer science, used identically across all programming languages. Every language with a technical/computing vocabulary has a standard word for "type" in the context of data types. The concept is taught consistently in CS education worldwide.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures DATA TYPE/CATEGORY concept (not keyboard typing)?
- [ ] Would a native speaker understand this as classification?
- [ ] Distinguishes from other meanings of "type"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun for classification)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other introspection functions?
- [ ] Uses noun form like other type-related terms?
- [ ] Aligns with how "data type" is discussed in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard computing term)?

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
term: type
language: es
translation: tipo
form: noun (masculine)
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "tipo" is the universal standard term for "type" in computing contexts, used consistently to describe data types across all Spanish programming documentation and CS education. It clearly conveys the concept of category or classification. The term is immediately recognizable and used naturally in phrases like "tipo de datos" (data type).

**Alternatives considered:**

1. `clase` (class) - Related but "clase" should be reserved for `class` keyword
2. `categoría` (category) - Too generic; "tipo" is the established computing term
3. `type` (English loan) - Not standard in Spanish; native term exists and is preferred

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Tipo" is the universal standard term for "type" in Spanish computing, recognized across all Spanish-speaking technical communities and educational systems.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
