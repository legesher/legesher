# Python Builtin: `isinstance` - Comprehensive Reference (Tier 2)

**Category:** builtin (function)
**Type:** compound term (verb + noun: "is" + "instance")
**Python Version:** All versions (1.5+)
**Related Terms:** `issubclass`, `type`, `hasattr`, `getattr`, `setattr`, `delattr`, `class`

**Note:** This is the Tier 2 comprehensive reference demonstrating **COMPLEX COMPOUND TERM** translation
strategies.

**Purpose:** Complete reference for human translators, beta testers, and future educational content
(legesher.io/learn).

**Translation Challenge:** This term exemplifies the critical compound term translation challenge -
demonstrating all four translation strategies from linguistic-standards.md and the consistency requirements
across related compound terms.

---

## Quick Summary

The `isinstance` builtin function checks whether an object is an instance of a specified class or tuple of
classes. It returns `True` if the object is an instance of the class(es), `False` otherwise. This is Python's
standard way to perform type checking at runtime.

---

## Etymology & History

### English Etymology

**Origin:** Compound English term
**Root Words:**

- **"is"** - Old English *is*, from Proto-Germanic *isti* (to be, to exist)
- **"instance"** - Latin *instantia* (being present, standing near), from *instare* (to stand upon,
  be present)

**Compound Formation:** "is" + "instance" = "is an instance"

**Meaning Evolution:**
In philosophy and logic, an "instance" means a specific example or case of something. In programming, an
"instance" is a specific realization of a class - a concrete object created from a class template.

**Example:**
> "Instance" comes from Latin *instantia* meaning "being present" or "standing near." When we ask
> "is instance?", we're literally asking "does this object stand as a present example of this class?"

### Why Python Chose This Term

**Designer Intent:**
Python creators chose `isinstance` to clearly express the question "Is this object an instance of this class?"
The compound verb+noun structure mirrors natural English questioning.

**Alternatives Considered:**

- `is_instance(obj, class)` - More explicit but longer
- `instanceOf(obj, class)` - Java-style, less Pythonic
- `type(obj) == class` - Not recommended due to inheritance issues
- `check_type(obj, class)` - Less precise (doesn't convey instance relationship)

**Historical Context:**

- **Python 1.5 (1997):** `isinstance()` introduced alongside new-style classes
- **Python 2.2 (2001):** Enhanced to work with new-style class system
- **Python 2.6+:** Extended to accept tuple of classes (multiple checks)
- **Python 3.0+:** All classes are new-style, `isinstance` is universal

**Why Compound Term:**
The compound structure "is" + "instance" was chosen because:

1. Reads naturally in English code
2. Clearly expresses the type-checking concept
3. Mirrors natural language question: "Is this an instance?"
4. Distinguishes from `type()` which returns type object

**PEP References:**

- PEP 252: Making Types Look More Like Classes (Python 2.2)
- PEP 3119: Introducing Abstract Base Classes (affects `isinstance` behavior)

### Cross-Language Comparison

How other programming languages handle instance checking:

| Language | Syntax | Notes |
|----------|--------|-------|
| Java | `obj instanceof Class` | Operator, not function |
| JavaScript | `obj instanceof Class` | Same operator pattern |
| C# | `obj is Type` | Keyword operator |
| Ruby | `obj.is_a?(Class)` | Method call |
| PHP | `$obj instanceof Class` | Operator |
| Rust | `type_of(&obj)` | Different approach |
| Swift | `obj is Type` | Keyword operator |
| Kotlin | `obj is Type` | Keyword operator |

**Python's Approach:** Python uses a builtin function rather than operator/keyword, making it consistent with
other type-checking utilities like `hasattr`, `getattr`, `type`. This functional approach is more flexible
(can be passed as argument, overridden in custom metaclasses).

---

## Concept Explanation (Multi-Level)

### For a 5-Year-Old 🧒

Imagine you have a box of toy animals. Some are dogs, some are cats, some are birds.

**Using isinstance is like asking:**
"Is this toy a dog?"

You pick up a toy and check: Does it have 4 legs? Does it bark? Does it wag its tail? If yes to all,
it's a dog!

In Python, `isinstance(my_toy, Dog)` asks: "Is my_toy one of the Dog toys?"

**Real-life example:**

```python
# Imagine toys
stuffed_dog = Dog()
stuffed_cat = Cat()

isinstance(stuffed_dog, Dog)  # True - yes, it's a dog!
isinstance(stuffed_cat, Dog)  # False - no, it's a cat!
```

### For a Beginner Programmer 📚

**What it does:**
`isinstance(object, classinfo)` checks if an object is an instance of a class. It returns `True` or `False`.

**Simple Example:**

```python
# Create some objects
my_list = [1, 2, 3]
my_string = "hello"
my_number = 42

# Check their types
isinstance(my_list, list)    # True - it IS a list
isinstance(my_string, str)   # True - it IS a string
isinstance(my_number, int)   # True - it IS an integer
isinstance(my_list, str)     # False - it's NOT a string
```

**Key Points:**

- First argument: the object you're checking
- Second argument: the class (or tuple of classes) you're checking against
- Returns: `True` or `False`
- Works with inheritance: if object is from a subclass, returns `True`

**Why use isinstance instead of type()?**

```python
class Animal:
    pass

class Dog(Animal):
    pass

buddy = Dog()

# BAD: Using type() for checking
type(buddy) == Animal  # False - type is Dog, not Animal

# GOOD: Using isinstance() - respects inheritance
isinstance(buddy, Animal)  # True - Dog inherits from Animal!
```

### For Intermediate Programmers 💻

**Technical Definition:**
`isinstance(object, classinfo)` returns `True` if the object argument is an instance of the classinfo argument,
or of a (direct, indirect, or virtual) subclass thereof. If classinfo is a tuple of type objects, return `True`
if object is an instance of any of the types.

**How It Works:**

```python
# Signature
isinstance(object, classinfo) -> bool

# classinfo can be:
# 1. A single class
isinstance(obj, int)

# 2. A tuple of classes (checks if instance of ANY)
isinstance(obj, (int, float, str))

# 3. Abstract Base Class (ABC)
from collections.abc import Iterable
isinstance([1, 2, 3], Iterable)  # True
```

**Under the hood:**

1. `isinstance` checks object's `__class__` attribute
2. Walks up the Method Resolution Order (MRO) chain
3. Compares against classinfo (or each class in tuple)
4. Calls `__instancecheck__()` method if defined on class's metaclass
5. Returns `True` on first match, `False` if no matches

**Example with Context:**

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

def make_sound(animal):
    # Type checking with isinstance
    if isinstance(animal, Animal):
        print(animal.speak())
    else:
        raise TypeError(f"Expected Animal, got {type(animal)}")

buddy = Dog()
whiskers = Cat()

make_sound(buddy)      # Woof!
make_sound(whiskers)   # Meow!
make_sound("hello")    # TypeError
```

**Important Behaviors:**

1. **Respects Inheritance:** Child class instances return `True` for parent class checks

   ```python
   class Parent:
       pass

   class Child(Parent):
       pass

   c = Child()
   isinstance(c, Parent)  # True - Child inherits from Parent
   ```

2. **Tuple Support:** Check against multiple types at once

   ```python
   x = 42
   isinstance(x, (int, float))  # True - x is int (one of the types)
   ```

3. **Abstract Base Classes:** Works with ABCs for duck typing

   ```python
   from collections.abc import Sequence
   isinstance([1, 2], Sequence)  # True - list implements Sequence
   ```

4. **Custom Metaclass Hook:** Classes can customize `isinstance` behavior

   ```python
   class CustomMeta(type):
       def __instancecheck__(cls, instance):
           # Custom logic here
           return hasattr(instance, 'special_attribute')
   ```

**Common Patterns:**

```python
# Pattern 1: Type validation in function
def process_data(data):
    if not isinstance(data, (list, tuple)):
        raise TypeError("data must be list or tuple")
    return [x * 2 for x in data]

# Pattern 2: Polymorphic function handling
def display(item):
    if isinstance(item, str):
        print(f"String: {item}")
    elif isinstance(item, int):
        print(f"Number: {item}")
    elif isinstance(item, list):
        print(f"List with {len(item)} items")

# Pattern 3: Safe attribute access
def get_name(obj):
    if isinstance(obj, dict):
        return obj.get('name', 'Unknown')
    elif hasattr(obj, 'name'):
        return obj.name
    else:
        return str(obj)
```

### For Expert Developers 🎓

**Implementation Details:**

At the CPython level, `isinstance()` is implemented in `Objects/abstract.c` as `PyObject_IsInstance()`.
The function:

1. Handles special case for `type` objects and metaclasses
2. Calls `__instancecheck__()` on the class's metaclass if defined (PEP 3119)
3. Falls back to checking `__class__` attribute and MRO
4. For tuples, recursively checks each element

**Bytecode:**

```python
import dis

def check_type(obj):
    return isinstance(obj, int)

dis.dis(check_type)
```

Output:

```text
  2           0 LOAD_GLOBAL              0 (isinstance)
              2 LOAD_FAST                0 (obj)
              4 LOAD_GLOBAL              1 (int)
              6 CALL_FUNCTION            2
              8 RETURN_VALUE
```

**Performance Considerations:**

- **Speed:** `isinstance` is highly optimized in CPython (~100-200ns for simple checks)
- **vs type():** `isinstance` is actually faster than `type(obj) == cls` due to C-level optimization
- **Tuple checks:** Linear search through tuple - O(n) where n is tuple length
- **ABC checks:** Slightly slower due to virtual subclass registry lookups
- **Metaclass hooks:** Custom `__instancecheck__` can be arbitrarily slow

**Benchmark:**

```python
import timeit

obj = 42

# isinstance: ~100ns
timeit.timeit('isinstance(obj, int)', globals=globals(), number=1000000)

# type comparison: ~120ns
timeit.timeit('type(obj) == int', globals=globals(), number=1000000)

# isinstance with tuple: ~150ns
timeit.timeit('isinstance(obj, (int, float))', globals=globals(), number=1000000)
```

**Advanced Usage:**

```python
# Advanced 1: Virtual Subclasses (PEP 3119)
from abc import ABC

class MyABC(ABC):
    pass

class NotSubclass:
    pass

# Register virtual subclass
MyABC.register(NotSubclass)

obj = NotSubclass()
isinstance(obj, MyABC)  # True - virtual subclass!

# Advanced 2: Custom isinstance via metaclass
class SingletonMeta(type):
    _instances = {}

    def __instancecheck__(cls, instance):
        # Only return True for THE instance
        return instance is cls._instances.get(cls)

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(metaclass=SingletonMeta):
    pass

s1 = Singleton()
s2 = Singleton()
isinstance(s1, Singleton)  # True
isinstance(s2, Singleton)  # True
s1 is s2  # True - same instance

# Advanced 3: Protocol checking (Python 3.8+)
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None:
        ...

class Circle:
    def draw(self):
        print("Drawing circle")

isinstance(Circle(), Drawable)  # True - structural typing!
```

**Related PEPs:**

- [PEP 252](https://peps.python.org/pep-0252/): Making Types Look More Like Classes
- [PEP 3119](https://peps.python.org/pep-3119/): Introducing Abstract Base Classes
- [PEP 544](https://peps.python.org/pep-0544/): Protocols: Structural subtyping (affects isinstance)
- [PEP 560](https://peps.python.org/pep-0560/): Core support for typing module

---

## Linguistic Form Recommendation

### Part of Speech Analysis

**English Term Category:** Compound term (verb + noun)

**Components:**

- **"is"** - verb (to be, identity/existence)
- **"instance"** - noun (specific example, realization of a class)

**In Python Context:**

- **Grammatical Role:** Question/check — "Is [this object] [an instance of class]?"
- **Action vs State:** Both — performs check (action) and tests state (identity)
- **Temporal Aspect:** Present tense — checking current state

### Recommended Translation Form

**Primary Recommendation:** Maintain compound structure (verb + noun) in target language

**THE CRITICAL CHALLENGE:**

`isinstance` is a **COMPOUND TERM** combining two concepts:

1. **Identity/existence check** ("is")
2. **Type membership** ("instance")

This creates the core translation challenge: Should translations be:

- Single compound word? (German: `istInstanz`)
- Two separate words? (Spanish: `es instancia`)
- Reversed order? (Hindi: `उदाहरण है` - instance is)
- Idiomatic rephrasing? (Chinese: `属于类` - belongs to class)

**Rationale:**
The translation must preserve BOTH components while sounding natural in the target language. Different language
families have different optimal strategies.

### THE FOUR COMPOUND TERM STRATEGIES (from linguistic-standards.md)

This is the PERFECT example to demonstrate all four strategies:

#### Strategy 1: Single Compound Word (Germanic Languages)

**Best for:** Languages with natural compounding (German, Dutch, Swedish)

**Pattern:** Combine "is" + "instance" into single token

**Examples:**

| Language | Translation | Literal | Notes |
|----------|-------------|---------|-------|
| German | `istInstanz` | is-instance | Single word, noun capitalized |
| Dutch | `isInstantie` | is-instance | Single compound |
| Swedish | `ärInstans` | is-instance | Natural Swedish compound |
| Norwegian | `erInstans` | is-instance | Bokmål form |

**Advantages:**

- Mirrors English structure closely
- Single token (no spaces, easier parsing)
- Natural in Germanic languages where compounds are common
- Consistent with other compound patterns

**Implementation Note:**

```python
# German example
istInstanz(obj, Klasse)  # Single word, reads naturally
```

#### Strategy 2: Two Separate Words (Romance Languages)

**Best for:** Languages where compounds sound awkward (Spanish, French, Portuguese, Italian)

**Pattern:** Keep "is" and "instance" as separate words

**Examples:**

| Language | Translation | Literal | Notes |
|----------|-------------|---------|-------|
| Spanish | `es instancia` | is instance | Two words, natural phrasing |
| French | `est instance` | is instance | Two words |
| Portuguese | `é instância` | is instance | Two words |
| Italian | `è istanza` | is instance | Two words |

**Advantages:**

- More natural phrasing in Romance languages
- Clearer meaning — easier to parse mentally
- Each word keeps its grammatical role
- Easier for learners to understand

**Disadvantage:**

- Two tokens (space in keyword) - may require special parser handling
- Slightly longer

**Implementation Note:**

```python
# Spanish example
es instancia(obj, clase)  # Two words with space
```

#### Strategy 3: Verb + Noun Natural Order (SOV/OVS Languages)

**Best for:** Languages with different word order than English

**Pattern:** Rearrange to match natural language order

**Examples:**

| Language | Translation | Literal | Word Order |
|----------|-------------|---------|------------|
| Hindi | `उदाहरण है` | instance is | Noun-Verb (SOV) |
| Japanese | `インスタンスである` | instance is | Noun-Verb |
| Korean | `인스턴스이다` | instance is | Noun-Verb |
| Turkish | `örnek mi` | instance question | Noun-Question |

**Advantages:**

- Natural word order for the language
- Clear grammatical structure
- Familiar phrasing to native speakers

**Rationale:**
Many languages naturally put verb after noun. Forcing English order ("is instance") would sound backwards.

**Implementation Note:**

```python
# Hindi example
उदाहरण है(obj, वर्ग)  # Noun-verb order, natural Hindi
```

#### Strategy 4: Idiomatic Rephrasing (East Asian Languages)

**Best for:** Languages where literal translation sounds unnatural

**Pattern:** Rephrase the concept idiomatically while preserving meaning

**Examples:**

| Language | Translation | Literal | Conceptual Meaning |
|----------|-------------|---------|-------------------|
| Chinese | `属于类` | belongs-to-class | membership check |
| Japanese | `型である` | type is | type checking |
| Korean | `형식이다` | form is | form checking |

**Advantages:**

- Sounds most natural to native speakers
- May be clearer than literal translation
- Aligns with how concept is taught in that language

**Disadvantage:**

- Further from English structure
- May be harder for bilingual developers to map
- Could diverge too far from original meaning if not careful

**Rationale:**
Chinese "是实例" (literal "is instance") sounds awkward. "属于类" (belongs to class) captures the
membership-checking concept more naturally.

**Implementation Note:**

```python
# Chinese example
属于类(obj, 类)  # "belongs to class" - idiomatic
```

### Consistency Requirements (CRITICAL)

**RULE: Whatever strategy you choose, apply it consistently to ALL related compound terms**

If you use Strategy 1 (single compound) for `isinstance`, you MUST use it for:

- `issubclass` → same "is" + noun pattern
- `hasattr` → same verb + noun pattern
- `getattr` → same verb + noun pattern
- `setattr` → same verb + noun pattern
- `delattr` → same verb + noun pattern

**Examples of CORRECT consistency:**

✅ **German (Strategy 1 - Compound):**

```text
isinstance  → istInstanz
issubclass  → istUnterklasse
hasattr     → hatAttribut
getattr     → gibAttribut
setattr     → setzAttribut
```

All use single compound words ✅

✅ **Spanish (Strategy 2 - Two Words):**

```text
isinstance  → es instancia
issubclass  → es subclase
hasattr     → tiene atributo
getattr     → obtener atributo
setattr     → establecer atributo
```

All use two separate words ✅

✅ **Chinese (Strategy 4 - Idiomatic):**

```text
isinstance  → 属于类 (belongs to class)
issubclass  → 是子类 (is subclass)
hasattr     → 有属性 (has attribute)
getattr     → 取属性 (get attribute)
setattr     → 设属性 (set attribute)
```

All use idiomatic Chinese phrasing ✅

**Examples of INCORRECT inconsistency:**

❌ **BAD - Mixed Strategies:**

```text
isinstance  → istInstanz     (compound)
hasattr     → hat Attribut   (two words) ← INCONSISTENT!
getattr     → getAttribute   (camelCase) ← WRONG PATTERN!
```

This mixing confuses learners and looks unprofessional.

### Examples Across Language Families

| Language Family | Strategy | isinstance | issubclass | hasattr | Rationale |
|-----------------|----------|------------|------------|---------|-----------|
| Germanic (de) | Strategy 1 | istInstanz | istUnterklasse | hatAttribut | Natural compounds |
| Romance (es) | Strategy 2 | es instancia | es subclase | tiene atributo | Two words clearer |
| Slavic (ru) | Strategy 1/2 | является экземпляром | является подклассом | имеет атрибут | Verb + noun |
| Arabic | Strategy 2 | هو نموذج | هو فئة فرعية | له سمة | Two word phrases |
| Chinese | Strategy 4 | 属于类 | 是子类 | 有属性 | Idiomatic Chinese |
| Hindi | Strategy 3 | उदाहरण है | उपवर्ग है | विशेषता है | Noun-verb order |
| Japanese | Strategy 3/4 | インスタンスである | サブクラスである | 属性がある | Natural Japanese |
| Korean | Strategy 3 | 인스턴스이다 | 서브클래스이다 | 속성있다 | Natural Korean |

---

## Syntax Role in Python

### Grammar Position

**Where it appears:**
As a builtin function call, can appear anywhere an expression is valid.

**Syntax Pattern:**

```python
isinstance(object, classinfo)
isinstance(object, (class1, class2, ...))  # Tuple of classes
```

**Full signature:**

```python
isinstance(
    object: Any,
    classinfo: type | UnionType | tuple[type | UnionType | tuple, ...]
) -> bool
```

### What It Creates/Does

**Primary Function:**
Checks object identity against class(es) and returns boolean.

**Returns:**

- `bool` - `True` if object is instance of classinfo, `False` otherwise

**Side Effects:**

- None (pure function)
- May call `__instancecheck__()` on metaclass if defined

### Common Use Cases

**Use Case 1: Type Validation**

```python
def process_list(data):
    if not isinstance(data, list):
        raise TypeError(f"Expected list, got {type(data).__name__}")
    # Process data...
```

**Use Case 2: Polymorphic Handling**

```python
def serialize(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, (int, float)):
        return str(obj)
    elif isinstance(obj, dict):
        return json.dumps(obj)
    else:
        raise ValueError(f"Cannot serialize {type(obj)}")
```

**Use Case 3: Duck Typing Validation**

```python
from collections.abc import Iterable

def process_items(items):
    if not isinstance(items, Iterable):
        raise TypeError("items must be iterable")
    for item in items:
        print(item)
```

### Related Syntax Components

**Works with:**

- `type()` - Returns the type; `isinstance` checks against type
- `issubclass()` - Similar but for class relationships, not instances
- `hasattr()` - Checks attribute existence (another compound term)
- `class` - Defines the classes that isinstance checks against

**Often paired with:**

```python
# isinstance + if (type checking)
if isinstance(obj, MyClass):
    obj.my_method()

# isinstance + raise (validation)
if not isinstance(x, int):
    raise TypeError("x must be integer")

# isinstance + or (multiple types)
if isinstance(value, (int, float, str)):
    # Handle numeric or string
    pass
```

---

## Related Concepts

### Similar Builtins (The Compound Term Family)

**These MUST be translated consistently with isinstance:**

#### Family 1: "is" + Type Pattern

- **`isinstance(obj, class)`** - Is [object] an instance?
- **`issubclass(cls, class)`** - Is [class] a subclass?

**Translation Note:** Both use "is" + type concept. Must use same "is" translation and same strategy.

#### Family 2: Attribute Operations Pattern

- **`hasattr(obj, name)`** - Has [object got] attribute?
- **`getattr(obj, name)`** - Get attribute [from object]
- **`setattr(obj, name, value)`** - Set attribute [on object]
- **`delattr(obj, name)`** - Delete attribute [from object]

**Translation Note:** All use verb + "attr" (attribute). Must use consistent pattern.

### Conceptual Relationships

**isinstance vs type():**

| Feature | `isinstance(obj, cls)` | `type(obj) == cls` |
|---------|----------------------|-------------------|
| Checks inheritance | Yes ✅ | No ❌ |
| Accepts tuple | Yes ✅ | No ❌ |
| Works with ABCs | Yes ✅ | No ❌ |
| Exact type only | No | Yes |
| Recommended | Yes ✅ | Rarely |

**Example showing difference:**

```python
class Animal:
    pass

class Dog(Animal):
    pass

buddy = Dog()

isinstance(buddy, Animal)  # True ✅ - respects inheritance
type(buddy) == Animal      # False ❌ - exact type is Dog

# isinstance is almost always the right choice
```

**isinstance vs duck typing:**

```python
# Old style: duck typing without isinstance
def process(data):
    try:
        for item in data:  # Just try to iterate
            print(item)
    except TypeError:
        print("Not iterable")

# Modern: explicit isinstance with ABC
from collections.abc import Iterable

def process(data):
    if isinstance(data, Iterable):
        for item in data:
            print(item)
    else:
        raise TypeError("data must be iterable")
```

### Common Patterns

**Pattern 1: Multiple Type Check**

```python
def flexible_input(value):
    """Accept int, float, or string representation."""
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to number")
    else:
        raise TypeError(f"Expected number or string, got {type(value)}")
```

**Pattern 2: Inheritance-Aware Dispatch**

```python
class Handler:
    def handle(self, obj):
        if isinstance(obj, SpecialCase):
            return self.handle_special(obj)
        elif isinstance(obj, BaseCase):
            return self.handle_base(obj)
        else:
            return self.handle_default(obj)
```

**Pattern 3: Abstract Base Class Validation**

```python
from collections.abc import Mapping, Sequence

def merge_data(data):
    if isinstance(data, Mapping):
        # Handle dict-like objects
        return dict(data)
    elif isinstance(data, Sequence):
        # Handle list-like objects
        return list(data)
    else:
        raise TypeError("data must be mapping or sequence")
```

---

## Common Misconceptions

### Misconception 1: "isinstance and type() are the same"

**What People Think:**
`isinstance(obj, cls)` and `type(obj) == cls` do the same thing.

**What Actually Happens:**
`isinstance` respects inheritance; `type()` checks exact type only.

**Example Showing the Truth:**

```python
class Animal:
    pass

class Dog(Animal):
    pass

buddy = Dog()

# isinstance respects inheritance
isinstance(buddy, Animal)  # True ✅ - Dog inherits from Animal
isinstance(buddy, Dog)     # True ✅ - exact type

# type() checks exact type only
type(buddy) == Animal      # False ❌ - type is Dog, not Animal
type(buddy) == Dog         # True ✅ - exact match

# ALWAYS prefer isinstance for type checking
```

**Why this matters:** Using `type()` breaks when dealing with inheritance hierarchies.

### Misconception 2: "isinstance is slow, avoid it"

**What People Think:**
Type checking with `isinstance` slows down code, should use duck typing instead.

**What Actually Happens:**
`isinstance` is highly optimized and extremely fast (~100ns). Duck typing (try/except) is often slower.

**Example:**

```python
import timeit

obj = [1, 2, 3]

# isinstance: ~100ns
timeit.timeit('isinstance(obj, list)', globals=globals(), number=1000000)

# Duck typing try/except: ~150ns (SLOWER)
def duck_type_check():
    try:
        iter(obj)
        return True
    except TypeError:
        return False

timeit.timeit('duck_type_check()', globals=globals(), number=1000000)
```

**Conclusion:** `isinstance` is fast and explicit. Use it.

### Misconception 3: "Can't use isinstance with generics"

**What People Think:**
Cannot use `isinstance` with type hints like `list[int]`.

**What Actually Happens:**
At runtime, generic type hints are erased. Check base type instead.

**Example:**

```python
from typing import List

# This doesn't work:
# isinstance(obj, List[int])  # TypeError!

# This works:
isinstance(obj, list)  # Check base type ✅

# For stricter checking, use runtime validators
from typing import get_args, get_origin

def is_list_of_ints(obj):
    if not isinstance(obj, list):
        return False
    return all(isinstance(item, int) for item in obj)
```

### Edge Cases to Know

1. **Old-style classes (Python 2):** `isinstance` behaved differently

   ```python
   # Python 2 (old-style class)
   class OldStyle:
       pass

   # Behaved oddly - don't worry about this in Python 3+
   ```

2. **Tuple must be tuple of types:** Cannot pass list

   ```python
   isinstance(obj, [int, float])  # TypeError! Must be tuple
   isinstance(obj, (int, float))  # Correct ✅
   ```

3. **None is not instance of NoneType directly:**

   ```python
   isinstance(None, type(None))  # True
   # NoneType is not directly accessible
   ```

---

## Educational Context Research

### How is isinstance taught across different regions?

#### In English-speaking countries

**Teaching approach:**
Educators introduce `isinstance` after covering:

- Basic types (int, str, list)
- Classes and objects
- Inheritance

**Common analogies/metaphors:**

- "Membership test" - is this object a member of this class?
- "Family tree" - is this person part of this family?
- "Shape matching" - does this shape fit this template?

**Resources checked:**

- MIT 6.0001: Teaches isinstance for type validation
- UC Berkeley CS61A: Covers isinstance with OOP
- Real Python: "isinstance() in Python: Type Checking"

**Terminology:** Universally called "instance checking" or "type checking"

#### In Spanish-speaking countries

**Research findings:**
Spanish CS education translates concepts descriptively:

- "instancia" = instance (direct cognate)
- "es instancia de" = is instance of

**Educational resources:**

- **Spanish Python docs:** Use "isinstance" in code, explain as "verificar si es instancia"
- **University courses:**
  - Universidad Complutense de Madrid: "comprobar instancia"
  - UNAM Mexico: "verificar tipo"
- **Stack Overflow ES:** Mix of "isinstance" and "es instancia"

**Regional variations:**
No major differences. Both Spain and Latin America use "instancia" consistently.

**Teaching pattern:**

```python
# Explained as: "verificar si objeto es instancia de clase"
isinstance(objeto, Clase)
```

**Consensus:** Keep `isinstance` in code, explain as "es instancia de" or "verificar instancia"

#### In Arabic-speaking countries

**Research findings:**
Programming mostly taught in English, including `isinstance`.

**Terminology when translated:**

- نموذج (namūdhaj) = instance/example
- هو نموذج (huwa namūdhaj) = is instance

**Educational approach:**

- Code: Keep `isinstance` (English)
- Explanations: Arabic concept translation
- Pattern: "يفحص إذا كان الكائن نموذجا من الصنف" (checks if object is instance of class)

**Resources checked:**

- Arabic programming forums: Keep `isinstance` in code
- University materials: English-medium with Arabic explanations

#### In Chinese-speaking regions

**Research findings:**
Chinese CS has established terminology for instance checking.

**Common textbook terminology:**

- 实例 (shílì) = instance
- 是实例 (shì shílì) = is instance
- 属于类 (shǔyú lèi) = belongs to class (more natural)

**Established translations:**

- Official Chinese Python docs: `isinstance` in code, "检查实例" in explanations
- University textbooks: "类型检查" (type checking) or "实例判断" (instance judgment)

**Teaching approach:**

```python
# Explained as: "检查对象是否是某个类的实例"
# (check if object is instance of class)
isinstance(对象, 类)
```

**Preference:** "属于类" sounds more natural than literal "是实例"

#### In Hindi-speaking regions (India)

**Research findings:**
CS education primarily English-medium, even in Hindi-speaking states.

**Terminology preferences:**

- उदाहरण (udāharan) = instance/example
- उदाहरण है (udāharan hai) = is instance

**Popular resources:**

- IIT courses: English with occasional Hindi explanations
- Hindi programming tutorials: Mix English keywords with Hindi explanations

**Teaching pattern:**

```python
# If explained in Hindi: "जांच करें कि वस्तु वर्ग का उदाहरण है या नहीं"
# (check if object is instance of class or not)
isinstance(वस्तु, वर्ग)
```

### Synthesis

**Most common approach across languages:**

- **Code:** Keep `isinstance` in English (international consistency)
- **Documentation:** Translate concept ("check if object is instance of class")
- **Teaching:** Explain as type/instance checking in native language

**Key vocabulary alignment:**

| Language | "instance" term | "is instance" phrase | Teaching approach |
|----------|----------------|---------------------|------------------|
| Spanish | instancia | es instancia | Keep isinstance, explain in Spanish |
| Arabic | نموذج | هو نموذج | Keep isinstance, explain in Arabic |
| Chinese | 实例 | 属于类 (idiomatic) | Keep isinstance, explain in Chinese |
| Hindi | उदाहरण | उदाहरण है | Keep isinstance, explain in Hindi |
| German | Instanz | ist Instanz | Keep isinstance, explain in German |

**Recommendation:**
Given international usage and compound term complexity, **two approaches** are valid:

**Approach A (Recommended for initial releases):**

- Keep `isinstance` untranslated in code
- Provide native language explanations in docs/comments
- Reason: Compound term translation is complex; English is universal

**Approach B (For mature language packs):**

- Translate using appropriate strategy for language family
- Ensure consistency across entire compound term family
- Requires careful review and community consensus

---

## Enhanced Cross-References

### Functional Relationships

**How isinstance works WITH other terms:**

#### Relationship 1: `isinstance` + `issubclass` (PAIRED CONCEPTS)

**Context:** Both check type relationships, but different subjects

```python
class Animal:
    pass

class Dog(Animal):
    pass

buddy = Dog()

# isinstance: check if OBJECT is instance of class
isinstance(buddy, Animal)  # True - buddy is instance

# issubclass: check if CLASS is subclass of class
issubclass(Dog, Animal)    # True - Dog is subclass
```

**Translation note:** These are a pair. Both use "is" + type concept.

- If `isinstance` → "es instancia"
- Then `issubclass` → "es subclase"

**Consistency requirement:** Same "is" translation, same compound strategy.

#### Relationship 2: `isinstance` + `type` (RELATED OPERATIONS)

**Context:** Both deal with type information, different purposes

```python
obj = "hello"

# type() returns the type
type(obj)           # <class 'str'>

# isinstance() checks against type
isinstance(obj, str)  # True
```

**Translation note:** `type` is simpler (single word), `isinstance` is compound. Not direct parallels, but conceptually related.

#### Relationship 3: `isinstance` + `hasattr` (OBJECT INTROSPECTION FAMILY)

**Context:** Both inspect object properties

```python
class MyClass:
    attr = 42

obj = MyClass()

# isinstance: checks class membership
isinstance(obj, MyClass)  # True

# hasattr: checks attribute existence
hasattr(obj, 'attr')      # True
```

**Translation note:** Both are compound terms (verb + noun). Must use consistent strategy:

- isinstance: "is" + "instance"
- hasattr: "has" + "attribute"

**If using German Strategy 1:**

- isinstance → `istInstanz`
- hasattr → `hatAttribut`

**If using Spanish Strategy 2:**

- isinstance → `es instancia`
- hasattr → `tiene atributo`

### Conceptual Hierarchy

**Where isinstance sits in Python's mental model:**

```text
Python Type System
├── Type Information
│   ├── type() - Returns type object
│   └── __class__ - Object's class attribute
├── Type Checking ← isinstance is HERE
│   ├── isinstance(obj, class) - Instance checking
│   ├── issubclass(cls, class) - Subclass checking
│   └── type(obj) == class - Exact type (not recommended)
├── Object Introspection
│   ├── hasattr(obj, name) - Attribute existence
│   ├── getattr(obj, name) - Attribute retrieval
│   ├── setattr(obj, name, val) - Attribute setting
│   └── delattr(obj, name) - Attribute deletion
└── Duck Typing
    ├── Abstract Base Classes (ABCs)
    └── Protocols (PEP 544)
```

**What this hierarchy means for translation:**

`isinstance` is part of Python's type checking system. Related terms that should have linguistic alignment:

1. **Type checking family:** isinstance, issubclass (both "is" + type concept)
2. **Attribute family:** hasattr, getattr, setattr, delattr (all verb + "attr")
3. **All compound terms should use same strategy** within a language pack

### Translation Consistency Requirements (CRITICAL)

**Terms that MUST align linguistically with isinstance:**

When translating `isinstance`, you MUST ensure consistency with:

- [ ] **`issubclass`** - Same "is" + type pattern
  - If isinstance = "es instancia", then issubclass = "es subclase"
  - If isinstance = "istInstanz", then issubclass = "istUnterklasse"

- [ ] **`hasattr`** - Same compound strategy (verb + noun)
  - If isinstance = compound word, then hasattr = compound word
  - If isinstance = two words, then hasattr = two words

- [ ] **`getattr`, `setattr`, `delattr`** - Same family, same strategy
  - All attribute operations must follow same pattern

- [ ] **All compound terms** - Consistent across language pack
  - Don't mix strategies (compound vs two words vs idiomatic)

**Consistency Checklist:**

```yaml
# Example: Spanish language pack consistency
isinstance: es instancia        # Strategy 2: Two words
issubclass: es subclase         # ✅ Same strategy
hasattr: tiene atributo         # ✅ Same strategy
getattr: obtener atributo       # ✅ Same strategy
setattr: establecer atributo    # ✅ Same strategy
delattr: eliminar atributo      # ✅ Same strategy

# BAD example: Inconsistent strategies
isinstance: es instancia        # Strategy 2: Two words
issubclass: esSubclase          # ❌ Strategy 1: Compound (INCONSISTENT!)
hasattr: tieneAtributo          # ❌ Strategy 1: Compound (INCONSISTENT!)
```

**Good example (German - consistent Strategy 1):**

```python
istInstanz(obj, Klasse)
istUnterklasse(Dog, Animal)
hatAttribut(obj, 'name')
gibAttribut(obj, 'name')
setzAttribut(obj, 'name', 'value')
```

All use single compound words ✅

**Bad example (mixing strategies - INCONSISTENT):**

```python
istInstanz(obj, Klasse)          # Compound
ist Unterklasse(Dog, Animal)     # Two words ❌ INCONSISTENT
hat_attribut(obj, 'name')        # snake_case ❌ WRONG PATTERN
```

---

## Cognitive Load & Learning Considerations

### Memory Load

**Is this translation easy to remember?**

**Compound term challenge:**

- Single concept split into two parts ("is" + "instance")
- Each language handles differently

**Mnemonic potential:**

**If keeping English "isinstance":**

- International consistency helps (JavaScript developers know it)
- But compound nature may confuse native speakers

**If translating:**

- Strategy 1 (compound): One word to remember, but may look long
- Strategy 2 (two words): Easier to parse mentally, two pieces
- Strategy 3 (reordered): Matches native thought patterns
- Strategy 4 (idiomatic): Most natural, but diverges from English

**Cognitive cognate advantage:**

For Romance languages:

- "instance" → "instancia" (Spanish/Portuguese)
- "instance" → "instance" (French)
- Cognate helps, but "is instance" vs "es instancia" split adds complexity

### Disambiguation

**Potential ambiguity:**

**English "instance":**

- Can mean "example" (general sense)
- Or "object realization of class" (programming sense)

**In target languages:**

**Spanish "instancia":**

- Also means "application/request" (legal term)
- In programming context: unambiguous

**Chinese "实例" (shílì):**

- Unambiguous - technical term for instance
- "属于类" (belongs to class) even clearer

**Arabic "نموذج" (namūdhaj):**

- Can mean "model" or "example"
- Programming context makes it clear

**Test:** Would a learner confuse this?

- In code context with class names: No confusion
- The compound "is instance" structure makes purpose clear

### Pronunciation

**Can developers say this term out loud easily?**

**As English "isinstance":**

- Three syllables: "iz-IN-stəns"
- Easy for English speakers
- May be awkward for non-English speakers

**As translations:**

| Language | Translation | Syllables | Ease |
|----------|-------------|-----------|------|
| Spanish | es instancia | 5 (es in-STAN-si-a) | Easy ✅ |
| German | istInstanz | 3 (ist-in-STANTS) | Easy ✅ |
| Chinese | 属于类 | 4 (shǔ-yú-lèi) | Easy ✅ |
| Arabic | هو نموذج | 4 (hu-wa na-MŪ-dhaj) | Easy ✅ |
| Hindi | उदाहरण है | 5 (u-DĀ-ha-ran hai) | Medium ⚠️ |

**Test:** Try saying "check if obj is instance of class" in target language

- Spanish: "verificar si obj es instancia de clase" ✅ flows well
- German: "prüfen ob obj ist Instanz von Klasse" ✅ natural
- Chinese: "检查 obj 属于类 class" ✅ natural

### Visual Recognition

**Can learners quickly spot isinstance when scanning code?**

**English "isinstance":**

- 10 characters - longer than most keywords
- Distinctive pattern (starts with "is")
- Easy to spot: `isinstance(obj, cls)`

**Translations:**

**Strategy 1 (compound):**

- German "istInstanz" (10 chars) - similar length
- Distinctive pattern
- Quick to scan ✅

**Strategy 2 (two words):**

- Spanish "es instancia" (12 chars with space)
- Very distinctive (only keyword with space?)
- Actually EASIER to spot due to uniqueness ✅

**Strategy 4 (idiomatic):**

- Chinese "属于类" (3 characters)
- Shorter than English!
- Very quick to scan ✅

**Recommendation:** All strategies can work well visually if consistent.

### Cross-Language Transfer

**Many programmers are multilingual:**

**Challenge with isinstance:**

- Compound structure doesn't translate 1:1
- "is instance" → "instance is" (some languages reverse order)
- "is instance" → "belongs to class" (idiomatic rephrasing)

**Benefits of keeping "isinstance" untranslated:**

- Same across Python/JavaScript (both have similar concepts)
- Stack Overflow examples work directly
- No mental translation needed
- International consistency

**Benefits of translating:**

- More accessible to pure beginners
- Sounds natural in target language
- Aligns with local CS education terminology

**Recommendation:**
For `isinstance` specifically, the compound term complexity suggests:

- **Phase 1:** Keep English `isinstance` with excellent native documentation
- **Phase 2:** Introduce native translations once compound strategy is established
- **Reason:** Compound terms require consistent family-wide strategy

---

## Translation Validation Criteria

### For Human Reviewers & Beta Testers

**Use this checklist to evaluate isinstance translation:**

#### Concept Accuracy (CRITICAL)

- [ ] Does translation capture "check if object is instance of class"?
- [ ] Is it clear this checks type membership?
- [ ] Does it avoid confusion with other type operations (type(), issubclass())?
- [ ] Is the compound nature ("is" + "instance") preserved?

**Test:** Show translation to native programmer. Can they guess it means "check if object is instance of
class"?

#### Linguistic Correctness

- [ ] Is the compound structure handled appropriately for the language?
- [ ] Does word order match language's natural patterns?
- [ ] Is verb form correct?
- [ ] Is noun form correct?
- [ ] For languages with case/gender: Are forms appropriate?

#### Compound Term Strategy Consistency (CRITICAL FOR isinstance)

- [ ] **MOST IMPORTANT:** Does this match the strategy used for related terms?
  - Same strategy as `issubclass`? (both "is" + type)
  - Same strategy as `hasattr`? (both verb + noun compound)
  - Same strategy as `getattr`, `setattr`? (all attribute family)

- [ ] Is strategy consistent throughout language pack?
  - Strategy 1 (compound) used everywhere?
  - Strategy 2 (two words) used everywhere?
  - Strategy 3 (reordered) used everywhere?
  - Strategy 4 (idiomatic) used everywhere?

**THIS IS THE CRITICAL TEST FOR isinstance:**

If your language pack has:

```text
isinstance: istInstanz (compound)
hasattr: hat Attribut (two words)
```

**FAIL** - Inconsistent strategies ❌

Correct version:

```text
isinstance: istInstanz (compound)
hasattr: hatAttribut (compound)
```

**PASS** - Consistent strategy ✅

#### Usability

- [ ] Short enough? (Ideally 1-2 words, max 3)
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce when reading code aloud?
- [ ] Easy to remember?
- [ ] Visually distinctive in code?

**isinstance is longer than average - acceptable if natural:**

- German: `istInstanz` (10 chars) - Natural compound ✅
- Spanish: `es instancia` (12 chars) - Clear two-word phrase ✅
- Chinese: `属于类` (3 chars) - Concise idiomatic ✅

#### Cultural Appropriateness

- [ ] No offensive meanings?
- [ ] Not childish or unprofessional?
- [ ] Appropriate technical register?
- [ ] Respects regional sensitivities?

#### CS Education Alignment

- [ ] Matches terminology in target language CS courses?
- [ ] Would students recognize this from textbooks?
- [ ] Aligns with how "instance" is taught?

**For isinstance, check:**

- Does your region teach "instance" concept in native language?
- What term do local CS textbooks use for "instance"?
- How do local programmers talk about type checking?

#### Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Renders in VS Code, PyCharm, terminals?
- [ ] For RTL languages: Tested bidirectional rendering?
- [ ] Syntax highlighting works?

### Severity Levels for isinstance

**P0 (Blocker - Must fix):**

- Doesn't convey instance-checking concept
- Confused with `type()` or `issubclass()`
- INCONSISTENT with related compound terms (different strategy for hasattr, etc.)
- Breaks in major IDEs

**P1 (High - Should fix):**

- Awkward compound structure for the language
- Too long (>15 characters or >3 words)
- Wrong verb or noun form
- Doesn't match CS education terminology

**P2 (Medium - Nice to fix):**

- Slightly unnatural phrasing
- Could be more concise
- Minor pronunciation difficulty
- Doesn't align with JavaScript developers' expectations

**P3 (Low - Optional):**

- Alternative might be 5% more natural
- Slightly different from textbook term
- Could be shorter by 1-2 characters

### Special Validation for Compound Terms

**Additional checklist specifically for isinstance and compound term family:**

- [ ] **Family consistency:** All "is" + type terms use same "is" translation?
- [ ] **Family consistency:** All verb + noun compounds use same strategy?
- [ ] **Strategy clarity:** Is it obvious which strategy (1-4) was chosen?
- [ ] **Strategy rationale:** Is there documented reason for strategy choice?
- [ ] **Community input:** Did native speakers review compound strategy?

**Example documentation:**

```yaml
term: isinstance
translation: es instancia
strategy: Strategy 2 (two separate words)
rationale: |
  Spanish naturally separates verb and noun. Compound words sound
  Germanic/awkward in Romance languages. Two-word strategy chosen
  for all compound terms in Spanish language pack.

  Consistency:
  - isinstance → es instancia
  - issubclass → es subclase
  - hasattr → tiene atributo
  - getattr → obtener atributo

  All follow Strategy 2 (two words).

alternatives_considered:
  - esInstancia: Rejected - sounds unnatural in Spanish
  - es_instancia: Rejected - snake_case not appropriate for keywords
  - pertenece_a_clase: Rejected - too idiomatic, diverges too much
```

---

## For Native Speakers of Non-English Languages

### Conceptual Understanding (Language-Agnostic)

**The Core Concept:**

`isinstance` answers one question: "Is this object a member of this class family?"

**Think of it as:**

You have a box of objects. You want to know: "Is this particular object one of the dogs? Or one of the
animals? Or one of the living things?"

`isinstance` checks membership in a class hierarchy.

**What mental model should you have?**

1. **Classes are categories** (Dog, Animal, LivingThing)
2. **Objects are members** (buddy the dog, whiskers the cat)
3. **isinstance asks:** "Is this object in this category (or any parent category)?"

**Key insight:**
Unlike exact type checking, `isinstance` respects inheritance:

- buddy is a Dog ✓
- buddy is an Animal ✓ (Dog inherits from Animal)
- buddy is a LivingThing ✓ (Animal inherits from LivingThing)

### Translation Considerations (THE COMPOUND TERM CHALLENGE)

**Key Aspects to Preserve:**

1. **Two-part concept:** "is" (identity check) + "instance" (type membership)
2. **Question nature:** This is asking a yes/no question
3. **Inheritance respect:** Not just exact type, but family membership

**Questions to Ask Yourself:**

1. **How does my language handle compound terms?**
   - Does it naturally make compound words? (like German)
   - Does it prefer separate words? (like Spanish)
   - Does it reverse word order? (like Hindi)
   - Does it use idiomatic phrases? (like Chinese)

2. **What strategy should I use?**
   - **Strategy 1:** Single compound word (if your language makes natural compounds)
   - **Strategy 2:** Two separate words (if compounds sound awkward)
   - **Strategy 3:** Natural word order (if verb comes after noun)
   - **Strategy 4:** Idiomatic rephrasing (if literal sounds unnatural)

3. **Am I being consistent?**
   - Will I use the SAME strategy for `issubclass`?
   - Will I use the SAME strategy for `hasattr`?
   - Will I use the SAME strategy for all compound terms?

**CRITICAL RULE:** Whatever strategy you choose, use it for ALL compound terms in your language pack.

**The Compound Term Family you must keep consistent:**

```text
isinstance  → "is" + "instance"
issubclass  → "is" + "subclass"
hasattr     → "has" + "attribute"
getattr     → "get" + "attribute"
setattr     → "set" + "attribute"
delattr     → "delete" + "attribute"
```

### Decision Framework for Your Language

**Step 1: Identify Your Language Family Pattern**

**If Germanic language (German, Dutch, Swedish):**
Use Strategy 1 (single compound word)
Example: isinstance → `istInstanz`

**If Romance language (Spanish, French, Portuguese, Italian):**
Use Strategy 2 (two separate words)
Example: isinstance → `es instancia`

**If SOV language (Hindi, Japanese, Korean, Turkish):**
Use Strategy 3 (natural word order, often reversed)
Example: isinstance → `उदाहरण है` (instance is)

**If East Asian with idiomatic preference (Chinese):**
Consider Strategy 4 (idiomatic rephrasing)
Example: isinstance → `属于类` (belongs to class)

**Step 2: Test Your Choice**

Ask native speakers:

1. "Does this sound natural?"
2. "Can you guess what this means?"
3. "Is this how you'd say 'check if object is instance of class'?"

**Step 3: Apply Consistently**

Once you choose a strategy for `isinstance`, apply it to:

- `issubclass` (same "is" + type pattern)
- `hasattr` (verb + noun pattern)
- All other compound terms

### Cultural Context

**English speakers think of isinstance as:**

- A type-checking utility
- Essential for polymorphism
- Preferred over `type()` for instance checks

**Consider translating the concept as:**

- Whatever phrase naturally asks "is this object a member of this class?"
- In your language's natural word order
- Using your language's natural compound strategy
- Staying consistent with related terms

### Action-Oriented vs Result-Oriented

`isinstance` is a **question/check** - it asks and returns answer.

In your language:

- **If question words come first:** "is instance" order might work
- **If question words come last:** "instance is" order might be better
- **If questions use particles:** Include appropriate particle

**Example:**

- English: "Is [this] an instance?" (question word first)
- Hindi: "[This] instance is?" (question structure different)
- Chinese: "Belongs to class" (rephrased as statement/check)

---

## Translation Mistakes to Avoid

### Mistake 1: Inconsistent Compound Strategy

**WRONG:**

```yaml
isinstance: istInstanz      # Strategy 1: compound
hasattr: hat Attribut       # Strategy 2: two words ❌
getattr: get_attribut       # Wrong: snake_case ❌
```

**RIGHT:**

```yaml
isinstance: istInstanz      # Strategy 1: compound
hasattr: hatAttribut        # Strategy 1: compound ✅
getattr: gibAttribut        # Strategy 1: compound ✅
```

**Why this is critical:** Mixing strategies looks unprofessional and confuses learners.

### Mistake 2: Translating "is" Inconsistently

**WRONG:**

```yaml
isinstance: es instancia    # "es" for "is"
issubclass: está subclase   # "está" for "is" ❌ Different verb!
```

**RIGHT:**

```yaml
isinstance: es instancia    # "es" for "is"
issubclass: es subclase     # "es" for "is" ✅ Consistent!
```

### Mistake 3: Over-Translating

**WRONG:**

```yaml
isinstance: comprueba_si_es_instancia_de_la_clase  # Way too long! ❌
```

**RIGHT:**

```yaml
isinstance: es instancia    # Concise ✅
```

**Rule:** Keep it under 3 words, preferably 2.

### Mistake 4: Ignoring Language's Natural Word Order

**WRONG (for Hindi):**

```yaml
isinstance: है उदाहरण       # "is instance" - backwards in Hindi! ❌
```

**RIGHT:**

```yaml
isinstance: उदाहरण है       # "instance is" - natural Hindi order ✅
```

### Mistake 5: Mixing Translation and Transliteration

**WRONG:**

```yaml
isinstance: es instance     # Mixed Spanish + English ❌
```

**RIGHT:**

```yaml
isinstance: es instancia    # Pure Spanish ✅
```

---

## Usage Examples

### Basic Usage

```python
# Example 1: Simple type check
my_list = [1, 2, 3]
my_string = "hello"

isinstance(my_list, list)    # True
isinstance(my_string, str)   # True
isinstance(my_list, str)     # False
```

**What this does:**
Checks if object is instance of specified class. Returns boolean.

**Output:**

```text
True
True
False
```

### Intermediate Usage

```python
# Example 2: Checking multiple types with tuple
def process_input(value):
    """Accept int, float, or string."""
    if isinstance(value, (int, float, str)):
        print(f"Valid input: {value}")
        return value
    else:
        raise TypeError(f"Expected number or string, got {type(value)}")

process_input(42)        # Valid input: 42
process_input(3.14)      # Valid input: 3.14
process_input("hello")   # Valid input: hello
process_input([1, 2])    # TypeError!
```

**What this does:**
Checks if value is any of the specified types (int, float, or str).

### Advanced Usage

```python
# Example 3: Inheritance-aware checking
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

buddy = Dog()
whiskers = Cat()

# isinstance respects inheritance
isinstance(buddy, Dog)      # True - exact type
isinstance(buddy, Animal)   # True - parent class
isinstance(whiskers, Dog)   # False - different subclass

# Polymorphic function
def make_sound(animal):
    if isinstance(animal, Animal):
        print(animal.speak())
    else:
        raise TypeError("Expected Animal instance")

make_sound(buddy)     # Woof!
make_sound(whiskers)  # Meow!
```

**What this does:**
Demonstrates isinstance with inheritance - Dog is instance of both Dog and Animal.

### Real-World Example

```python
# Example 4: Practical API input validation
from typing import Union
from collections.abc import Iterable

class DataProcessor:
    def process(self, data: Union[dict, list, str]):
        """
        Process different data types appropriately.

        Args:
            data: Can be dict, list, or string
        """
        if isinstance(data, dict):
            # Handle dictionary
            return {k: self._transform(v) for k, v in data.items()}

        elif isinstance(data, str):
            # Handle string
            return self._transform(data)

        elif isinstance(data, Iterable):
            # Handle any iterable (list, tuple, set, etc.)
            return [self._transform(item) for item in data]

        else:
            raise TypeError(
                f"Expected dict, list, or string, got {type(data).__name__}"
            )

    def _transform(self, value):
        """Transform individual value."""
        if isinstance(value, str):
            return value.upper()
        elif isinstance(value, (int, float)):
            return value * 2
        else:
            return value

# Usage
processor = DataProcessor()

processor.process({"name": "alice"})           # {"name": "ALICE"}
processor.process(["hello", "world"])          # ["HELLO", "WORLD"]
processor.process("test")                      # "TEST"
processor.process((1, 2, 3))                   # [2, 4, 6]
```

**Context:**
Real API that needs to handle multiple input types gracefully. isinstance enables type-specific handling.

---

## Common Pitfalls

### Pitfall 1: Using type() Instead of isinstance

**Problem:**

```python
class Animal:
    pass

class Dog(Animal):
    pass

buddy = Dog()

# WRONG: Using type() breaks inheritance
if type(buddy) == Animal:  # False! ❌
    print("It's an animal")

# This never prints because type(buddy) is Dog, not Animal
```

**Solution:**

```python
# CORRECT: Using isinstance respects inheritance
if isinstance(buddy, Animal):  # True! ✅
    print("It's an animal")

# This prints because Dog inherits from Animal
```

**Why this happens:**
`type()` returns exact type; `isinstance()` checks class hierarchy.

### Pitfall 2: Passing List Instead of Tuple

**Problem:**

```python
# WRONG: Passing list for multiple types
isinstance(obj, [int, float])  # TypeError! ❌
```

**Solution:**

```python
# CORRECT: Must use tuple
isinstance(obj, (int, float))  # Works! ✅
```

**Why this happens:**
Second argument must be class or tuple of classes. Lists are not valid.

### Pitfall 3: Checking Against Generic Types

**Problem:**

```python
from typing import List

# WRONG: Can't check against generic type
isinstance(obj, List[int])  # TypeError! ❌
```

**Solution:**

```python
# CORRECT: Check base type only
isinstance(obj, list)  # Works! ✅

# For stricter checking, iterate
if isinstance(obj, list) and all(isinstance(x, int) for x in obj):
    print("List of ints")
```

**Why this happens:**
Generic type hints are erased at runtime. Can only check base type.

---

## Best Practices

1. **Prefer isinstance over type() checking**
   - Respects inheritance
   - More Pythonic
   - Better for polymorphism

2. **Use tuple for multiple type checks**

   ```python
   if isinstance(value, (int, float, str)):
       # Handle multiple types
   ```

3. **Combine with Abstract Base Classes for duck typing**

   ```python
   from collections.abc import Iterable
   if isinstance(obj, Iterable):
       for item in obj:
           process(item)
   ```

4. **Don't over-use - embrace duck typing when appropriate**

   ```python
   # Sometimes better to just try:
   try:
       for item in obj:
           process(item)
   except TypeError:
       # Handle non-iterable
   ```

5. **Document expected types clearly**

   ```python
   def process(data):
       """
       Process data.

       Args:
           data: Must be list, tuple, or set
       """
       if not isinstance(data, (list, tuple, set)):
           raise TypeError("data must be list, tuple, or set")
   ```

---

## Further Reading

### Official Documentation

- [Python Built-in Functions: isinstance](https://docs.python.org/3/library/functions.html#isinstance)
- [Python Language Reference: Data Model](https://docs.python.org/3/reference/datamodel.html)
- [Python Library: Abstract Base Classes](https://docs.python.org/3/library/abc.html)

### Python Enhancement Proposals (PEPs)

- [PEP 252: Making Types Look More Like Classes](https://peps.python.org/pep-0252/)
- [PEP 3119: Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [PEP 544: Protocols - Structural Subtyping](https://peps.python.org/pep-0544/)
- [PEP 560: Core Support for typing module](https://peps.python.org/pep-0560/)

### Historical Context

- [Python 2.2 Release Notes: Type/Class Unification](https://docs.python.org/3/whatsnew/2.2.html)
- [History of type() and isinstance()](https://docs.python.org/3/whatsnew/2.2.html#peps-252-and-253-type-and-class-changes)

### Tutorials & Guides

- [Real Python: Python Type Checking](https://realpython.com/python-type-checking/)
- [Real Python: Duck Typing in Python](https://realpython.com/lessons/duck-typing/)
- [Python.org Tutorial: Classes](https://docs.python.org/3/tutorial/classes.html)

### Related Concepts

- [Stack Overflow: isinstance vs type() comparison](https://stackoverflow.com/questions/1549801/what-are-the-differences-between-type-and-isinstance)
- [Python Docs: ABC - Abstract Base Classes](https://docs.python.org/3/library/collections.abc.html)

---

**Document Version:** 1.0 (Compound Term Example)
**Created:** 2025-11-10
**Maintained by:** Legesher Team
**Target Audience:** Human translators, beta testers, future educational platform
**For AI Translation:** Use Tier 1 brief template

**Translation Recommendations Summary:**

| Language | Strategy | isinstance | issubclass | hasattr | Consistency |
|----------|----------|------------|------------|---------|-------------|
| Spanish | Strategy 2 | es instancia | es subclase | tiene atributo | HIGH ✅ |
| French | Strategy 2 | est instance | est sous-classe | a attribut | HIGH ✅ |
| German | Strategy 1 | istInstanz | istUnterklasse | hatAttribut | HIGH ✅ |
| Dutch | Strategy 1 | isInstantie | isSubklasse | heeftAttribuut | HIGH ✅ |
| Portuguese | Strategy 2 | é instância | é subclasse | tem atributo | HIGH ✅ |
| Italian | Strategy 2 | è istanza | è sottoclasse | ha attributo | HIGH ✅ |
| Arabic | Strategy 2 | هو نموذج | هو فئة فرعية | له سمة | MEDIUM ⚠️ |
| Chinese | Strategy 4 | 属于类 | 是子类 | 有属性 | HIGH ✅ |
| Japanese | Strategy 3 | インスタンスである | サブクラスである | 属性がある | HIGH ✅ |
| Korean | Strategy 3 | 인스턴스이다 | 서브클래스이다 | 속성있다 | HIGH ✅ |
| Hindi | Strategy 3 | उदाहरण है | उपवर्ग है | विशेषता है | MEDIUM ⚠️ |
| Russian | Strategy 2 | является экземпляром | является подклассом | имеет атрибут | HIGH ✅ |

**Key Insights for Translators:**

1. **isinstance is THE compound term challenge** - it demonstrates all four translation strategies
2. **Consistency is CRITICAL** - whatever strategy you choose must apply to entire compound term family
3. **Language families naturally gravitate to certain strategies:**
   - Germanic → Strategy 1 (compounds)
   - Romance → Strategy 2 (two words)
   - SOV languages → Strategy 3 (natural order)
   - East Asian → Strategy 3 or 4 (natural order or idiomatic)
4. **Test your choice** with native speakers and CS educators
5. **Document your strategy** clearly so future translators maintain consistency

**Community Review Priority:** HIGH
**Reason:** Compound term decisions affect entire language pack consistency
