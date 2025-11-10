# Python Keyword: `def` - Comprehensive Reference (Tier 2)

**Category:** keyword
**Type:** verb (action keyword)
**Python Version:** 1.0+ (all versions)
**Related Terms:** `return`, `class`, `lambda`, `async def`

**Note:** This is the Tier 2 comprehensive reference example. For AI translation, use the Tier 1 brief
template.

**Purpose:** Complete reference for human translators, beta testers, and future educational content
(legesher.io/learn).

---

## Quick Summary

The `def` keyword is used to define (create) a function in Python. It marks the beginning of a function
definition, followed by the function name, parameters in parentheses, and a colon.

---

## Etymology & History

### English Etymology

**Origin:** Latin
**Root Words:** Latin *dēfīnīre*, from *dē-* (completely) + *fīnīre* (to limit, set bounds),
from *fīnis* (boundary, end)
**Meaning Evolution:** The word "define" originally meant "to set bounds or limits to something."
In programming, it means to give something a name and specify what it does — essentially setting the
"boundaries" of what a function is and does.

**Example:**
> The word "define" comes from Latin *dēfīnīre*, meaning "to set bounds or limits to." When we "define" a
> function, we're setting the boundaries of what that function is and does.

### Why Python Chose This Term

**Designer Intent:** Guido van Rossum chose `def` as an abbreviation of "define" to keep function definitions
concise while remaining readable. The term emphasizes that you're creating something new (defining it into
existence).

**Alternatives Considered:** Other languages use `function` (JavaScript), `fun` (Kotlin), `fn` (Rust),
`func` (Go). Python chose `def` as a middle ground — shorter than `function` but more meaningful than `fn`.

**Historical Context:** Introduced in Python 1.0 (1994). The choice of `def` was influenced by Lisp and
Scheme, which use `defun` (define function). Python shortened it to just `def` for brevity.

**PEP References:**

- Original design predates the PEP process
- PEP 3107 (Function Annotations) extended `def` syntax in Python 3.0
- PEP 484 (Type Hints) further extended function definitions

### Cross-Language Comparison

How other programming languages handle the same concept:

| Language | Term | Notes |
|----------|------|-------|
| JavaScript | `function` | Full word, more verbose |
| Ruby | `def` | Same as Python |
| Go | `func` | Abbreviation of "function" |
| Rust | `fn` | Even shorter abbreviation |
| PHP | `function` | Full word |
| Kotlin | `fun` | Playful abbreviation |
| Swift | `func` | Same as Go |
| Java | No keyword | Uses method syntax in classes |

**Python's Approach:** The 3-letter `def` balances brevity (faster to type) with clarity (clearly means
"define"). It's short enough to not clutter code but long enough to be immediately recognizable.

---

## Concept Explanation (Multi-Level)

### For a 5-Year-Old 🧒

Imagine you have a recipe for making chocolate chip cookies. The recipe has a name ("Grandma's Cookies") and
tells you step-by-step what to do.

In Python, `def` is like writing the title of your recipe. When you write `def make_cookies():`, you're saying
"Here's my recipe called 'make_cookies', and here's what you do to make them!"

Just like you can use the same recipe over and over, once you define a function with `def`, you can use it
again and again by just saying its name.

### For a Beginner Programmer 📚

**What it does:**
The `def` keyword creates a reusable block of code called a function. A function is like a mini-program inside
your program that performs a specific task.

**Simple Example:**

```python
# Define a function that greets someone
def greet(name):
    print(f"Hello, {name}!")

# Now we can use this function anytime
greet("Alice")  # Prints: Hello, Alice!
greet("Bob")    # Prints: Hello, Bob!
```

**Key Points:**

- `def` must be followed by the function name and parentheses `()`
- Parameters (inputs) go inside the parentheses
- The function body must be indented
- Once defined, call the function by using its name followed by `()`
- Functions can be called multiple times with different inputs

### For Intermediate Programmers 💻

**Technical Definition:**
The `def` keyword is a compound statement that creates a function object and binds it to a name in the current
namespace. It defines the function's signature (name and parameters) and its body (the code it executes).

**How It Works:**
When Python encounters a `def` statement:

1. **Compile time:** The function body is compiled to bytecode
2. **Runtime:** A function object is created
3. **Binding:** The function object is bound to the specified name
4. **Scope:** The function can access variables in enclosing scopes (closure)

**Example with Context:**

```python
def calculate_tax(income, rate=0.25):
    """Calculate tax based on income and rate.

    Args:
        income: Annual income in dollars
        rate: Tax rate as decimal (default 0.25 = 25%)

    Returns:
        Tax amount owed
    """
    if income <= 0:
        return 0
    return income * rate

# Call with required argument only
basic_tax = calculate_tax(50000)  # Uses default rate 0.25

# Call with both arguments
high_tax = calculate_tax(100000, rate=0.35)
```

**Important Behaviors:**

1. **Default Parameters:** Functions can have default values for parameters
2. **Return Values:** Functions can return values using `return` (implicit `None` if no return)
3. **Docstrings:** First string in function body becomes `__doc__` attribute
4. **Closures:** Functions can capture variables from enclosing scopes
5. **First-Class Objects:** Functions are objects and can be passed around

**Common Patterns:**

```python
# Pattern 1: Function with no parameters
def print_header():
    print("=" * 40)
    print("Welcome to My Program")
    print("=" * 40)

# Pattern 2: Function with multiple returns
def divide(a, b):
    if b == 0:
        return None  # Return early for error case
    return a / b

# Pattern 3: Function returning multiple values
def get_coordinates():
    return 10, 20  # Returns a tuple

x, y = get_coordinates()  # Tuple unpacking

# Pattern 4: Nested function definition
def outer():
    def inner():
        print("Inner function")
    inner()

# Pattern 5: Function as decorator target
@log_calls
def important_operation():
    pass
```

### For Expert Developers 🎓

**Implementation Details:**
At the bytecode level, `def` compiles the function body and creates a code object. The `MAKE_FUNCTION` bytecode
instruction creates the function object with:

- `co_code`: compiled bytecode
- `co_consts`: constants used in function
- `co_names`: names referenced
- `co_varnames`: local variable names
- `co_freevars`: variables from enclosing scope (closure)

**Bytecode:**

```python
import dis

def example(x):
    return x * 2

dis.dis(example)
```

Output shows:

```text
  2           0 LOAD_FAST                0 (x)
              2 LOAD_CONST               1 (2)
              4 BINARY_MULTIPLY
              6 RETURN_VALUE
```

**Performance Considerations:**

- **Function call overhead:** ~100-200ns per call on modern CPython
- **Closure performance:** Accessing free variables is slightly slower than locals
- **Recursion limit:** Default recursion limit is 1000 (changeable with `sys.setrecursionlimit()`)
- **Optimization:** `@functools.lru_cache` can memoize expensive function calls

**Advanced Usage:**

```python
# Metaprogramming: Create functions dynamically
def make_multiplier(n):
    def multiplier(x):
        return x * n
    return multiplier

times_three = make_multiplier(3)
print(times_three(10))  # 30

# Introspection: Inspect function metadata
def annotated_func(x: int, y: str) -> bool:
    pass

print(annotated_func.__annotations__)  # {'x': int, 'y': str, 'return': bool}
print(annotated_func.__name__)         # 'annotated_func'
print(annotated_func.__code__.co_argcount)  # 2

# Advanced: Modify function attributes
def greet():
    pass

greet.call_count = 0  # Add custom attribute

# Descriptor protocol: Functions as descriptors
class MyClass:
    def method(self):  # Functions become bound methods
        pass

obj = MyClass()
print(type(obj.method))  # <class 'method'>
```

**Related PEPs:**

- [PEP 3107](https://peps.python.org/pep-3107/): Function Annotations (Python 3.0)
- [PEP 484](https://peps.python.org/pep-0484/): Type Hints (Python 3.5+)
- [PEP 526](https://peps.python.org/pep-0526/): Syntax for Variable Annotations
- [PEP 570](https://peps.python.org/pep-0570/): Positional-Only Parameters (Python 3.8)
- [PEP 3102](https://peps.python.org/pep-3102/): Keyword-Only Arguments (Python 3.0)

---

## Linguistic Form Recommendation

### Part of Speech Analysis

**English Term Category:** verb (action keyword)

**In Python Context:**

- **Grammatical Role:** Command/action — instructs Python to create a function
- **Action vs State:** Action (actively creates something new)
- **Temporal Aspect:** One-time action (define once, use many times)

### Recommended Translation Form

**Primary Recommendation:** Infinitive verb form

**Rationale:**
`def` is an action keyword that performs the action of defining/creating. In most languages, commands and
actions are best expressed using the infinitive form (the "to do" form). This matches git commit conventions
(use infinitive: "add feature" not "adding feature").

**Why infinitive, not imperative?**

- Infinitive is neutral and universal (works in any context)
- Imperative can sound too commanding (like giving orders)
- Infinitive matches mathematical/technical language style
- Consistent with how technical documentation is written

**Alternative Forms to Consider:**

1. **Imperative form:** Valid but feels more commanding ("Define this function now!")
2. **Gerund form (-ing):** Too verbose and unclear ("defining" suggests ongoing action)
3. **Noun form:** Wrong — `def` is an action, not a thing

**Forms to Avoid:**

- ❌ **Gerund (-ing form):** "definiendo", "defining" — too wordy, suggests continuous action
- ❌ **Past tense:** "defined", "definido" — suggests already done, not a command
- ❌ **Noun:** "definition", "definición" — `def` is an action, not a thing

### Examples Across Language Families

| Language Family | Recommended Form | Example Translation | Rationale |
|-----------------|------------------|---------------------|-----------|
| Romance (es, fr, pt) | Infinitive verb | es: definir, fr: définir, pt: definir | Infinitive is standard for commands in Romance |
| Germanic (de, nl) | Infinitive verb | de: definieren, nl: definiëren | Germanic languages use infinitive for neutral commands |
| Slavic (ru, pl) | Infinitive verb | ru: определить, pl: zdefiniować | Infinitive is the dictionary form, neutral |
| Arabic | Verbal noun (masdar) | تعريف (ta'rīf) | Masdar form captures the concept of "defining" |
| Chinese | Dictionary form | 定义 (dìngyì) | Standard CS terminology for "define" |
| Hindi | Verb root/infinitive | परिभाषित करना (paribhaashit karna) | Infinitive form (करना ending) is neutral |
| Japanese | Dictionary form | 定義する (teigi suru) | Neutral dictionary form, no politeness |
| Korean | Dictionary form | 정의하다 (jeong-uihada) | Neutral -하다 form |

---

## Syntax Role in Python

### Grammar Position

**Where it appears:**
At the beginning of a function definition statement, typically at the start of a line (at current indentation
level).

**Syntax Pattern:**

```python
def <function_name>(<parameters>):
    <function_body>
```

Full pattern with all options:

```python
[@decorators]
[async] def <name>([params][, *args][, **kwargs]) [-> return_type]:
    ["""docstring"""]
    <statements>
    [return <value>]
```

### What It Creates/Does

**Primary Function:**
Creates a function object and binds it to a name in the current scope.

**Creates:**

- A callable function object (`types.FunctionType`)
- A binding in the current namespace (module, class, or local scope)
- A closure (if the function references variables from enclosing scopes)
- Metadata: `__name__`, `__doc__`, `__annotations__`, `__defaults__`

### Scope Behavior

**Scope Rules:**

- The function name is bound in the **current scope** (where `def` appears)
- Variables inside the function create a **local scope**
- Functions can access **enclosing scopes** (LEGB rule: Local, Enclosing, Global, Built-in)
- Functions create closures by capturing variables from enclosing scopes

**Example:**

```python
# Global scope
x = 10

def outer():
    # Enclosing scope
    y = 20

    def inner():
        # Local scope
        z = 30
        print(x)  # Accesses global scope
        print(y)  # Accesses enclosing scope (closure)
        print(z)  # Accesses local scope

    return inner

func = outer()
func()  # Prints: 10, 20, 30
```

### Related Syntax Components

**Works with:**

- `return` - Returns a value from the function (almost always used together)
- `class` - Defines methods inside classes (functions in class scope)
- `lambda` - Alternative way to create small anonymous functions
- `async` - Prefix for asynchronous functions (`async def`)
- `@decorator` - Decorates the function before it's bound to the name

**Often paired with:**

```python
# def + return
def square(x):
    return x ** 2

# def inside class
class MyClass:
    def method(self):
        pass

# async def
async def fetch_data():
    await some_operation()

# def + decorator
@staticmethod
def utility_function():
    pass
```

---

## Related Concepts

### Similar Keywords/Builtins

**Conceptually Similar:**

- `class` - Defines a class (structure similar to function definition)
- `lambda` - Creates anonymous function (alternative to `def` for simple functions)
- `async def` - Defines async function (variation of `def`)

**Key Differences:**

| Feature | `def` | `lambda` | `class` |
|---------|-------|----------|---------|
| Can have statements | Yes | No (expression only) | Yes |
| Can have docstring | Yes | No | Yes |
| Can be async | Yes (async def) | No | N/A (methods can be async) |
| Creates | Named function | Anonymous function | Class object |
| Typical length | Multiple lines | Single expression | Multiple lines |

### Associated Keywords

**Frequently Used Together:**

- `def` + `return` - Almost every function returns a value
- `def` + `if`/`for`/`while` - Functions often contain control flow
- `class` + `def` - Methods are defined inside classes
- `@decorator` + `def` - Decorators modify function behavior
- `async` + `def` - Creates coroutine functions

### Common Patterns

**Pattern 1: Basic Function**

```python
def greet(name):
    """Print a greeting."""
    print(f"Hello, {name}!")
```

**Pattern 2: Function with Default Arguments**

```python
def power(base, exponent=2):
    """Calculate base raised to exponent power."""
    return base ** exponent
```

**Pattern 3: Function Returning Multiple Values**

```python
def min_max(numbers):
    """Return minimum and maximum of a list."""
    return min(numbers), max(numbers)
```

**Pattern 4: Closure (Function Returning Function)**

```python
def make_multiplier(factor):
    """Create a multiplier function."""
    def multiplier(x):
        return x * factor
    return multiplier
```

**Pattern 5: Decorator Function**

```python
def log_calls(func):
    """Decorator that logs function calls."""
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

---

## Common Misconceptions

### Misconception 1: "def executes the function body immediately"

**What People Think:**
When Python sees `def my_function():`, it runs the code inside the function right away.

**What Actually Happens:**
`def` only *creates* the function object. The function body doesn't run until you *call* the function.

**Example Showing the Truth:**

```python
# This defines the function but doesn't run it
def greet():
    print("Hello!")  # This doesn't print yet

# Function is defined but nothing printed yet
# Only when we call it:
greet()  # NOW it prints "Hello!"
```

**Why this matters:** Understanding this prevents confusion about when code executes.

### Misconception 2: "def creates a copy of variables it references"

**What People Think:**
Functions make copies of variables from the outer scope.

**What Actually Happens:**
Functions create a closure that references (not copies) variables from enclosing scopes. Changes to mutable
objects are visible in both scopes.

**Example:**

```python
numbers = [1, 2, 3]

def add_number(n):
    numbers.append(n)  # Modifies the original list

add_number(4)
print(numbers)  # [1, 2, 3, 4] — list was modified, not copied
```

### Misconception 3: "def and lambda are completely interchangeable"

**What People Think:**
`lambda` is just a shorter way to write `def`.

**What Actually Happens:**
`lambda` can only contain a single expression (no statements), while `def` can have multiple statements,
docstrings, and complex logic.

**Example:**

```python
# This works with def
def complex_func(x):
    if x > 0:
        return x * 2
    else:
        return x * 3

# This CANNOT be written with lambda (multiple statements)
# lambda can only do: lambda x: x * 2 if x > 0 else x * 3
```

### Edge Cases to Know

1. **Default argument mutation:** Default arguments are created once at function definition, not each
   call

   ```python
   def append_to(element, lst=[]):  # Dangerous!
       lst.append(element)
       return lst

   print(append_to(1))  # [1]
   print(append_to(2))  # [1, 2] — same list!
   ```

2. **Name binding timing:** Function name is bound after the entire definition is processed

   ```python
   def func():
       return func  # This works — 'func' is bound after def completes
   ```

3. **Scope capture in loops:** Loop variables in closures capture references, not values

   ```python
   functions = [lambda: i for i in range(3)]
   print([f() for f in functions])  # [2, 2, 2] — all capture final i value
   ```

---

## Educational Context Research

### How is `def` taught across different regions?

#### In English-speaking countries

**Teaching approach:**
Educators typically introduce `def` as "defining a function" or "creating a function." The emphasis is on:

- The function as a reusable block of code
- Analogy to mathematical functions or recipes
- The concept of input → processing → output

**Common analogies/metaphors:**

- Recipe (inputs = ingredients, output = dish)
- Machine (inputs go in, output comes out)
- Math function: f(x) = x² (same concept, different notation)

**Resources checked:**

- MIT OpenCourseWare (6.0001): Uses "define" terminology
- UC Berkeley CS61A: Emphasizes "function definition"
- Python.org tutorial: "Defining Functions" (official)

#### In Spanish-speaking countries

**Research findings:**
Searched "Python tutorial def español" and reviewed:

- Spanish Python documentation (es.python.org)
- University courses from Spain and Latin America
- Popular Spanish tutorial sites

**Educational resources:**

- **Textbook terms:** "definir función" (define function)
- **University courses:**
  - Universidad Complutense de Madrid: uses "definir"
  - UNAM (Mexico): uses "definir"
  - Universidad de Buenos Aires: uses "definir"
- **Online tutorials:**
  - Python en Español: translates as "definir"
  - Aprendiendo Python: uses "def" with explanation "definir"

**Regional variations:**
No significant regional differences. Both Spain and Latin America use "definir" consistently for `def`.

**Consensus:** "definir" (infinitive form) is the universally accepted term across Spanish-speaking CS education.

#### In Arabic-speaking countries

**Research findings:**
Programming in Arabic-speaking countries is predominantly taught in English, with Arabic commentary/explanation.

**Educational approach:**

- Code uses English keywords (including `def`)
- Explanations and lectures may be in Arabic
- When Arabic is used, Modern Standard Arabic (MSA) is preferred

**Terminology when translated:**

- تعريف (ta'rīf) - verbal noun (masdar) meaning "definition"
- This aligns with MSA technical vocabulary

**Resources checked:**

- Egyptian universities (Cairo University): English medium
- Saudi universities (KAUST): English medium
- Arabic programming forums: Mix of English code with Arabic discussion

**Recommendation:** تعريف (ta'rīf) aligns with how "define" would be expressed in Arabic technical contexts.

#### In Chinese-speaking regions

**Research findings:**
Checked Simplified Chinese resources (mainland China focus):

**Common textbook terminology:**

- 定义 (dìngyì) - standard translation for "define"
- This is used consistently across:
  - Chinese Python documentation (docs.python.org/zh-cn/)
  - Tsinghua University CS courses
  - Peking University materials

**Established translations:**

- All major Chinese Python tutorials use 定义 (dìngyì) for "define"
- This is the established CS education term

**Taiwan/Singapore:** Also use 定义 (same characters, Traditional vs Simplified)

**Consensus:** 定义 (dìngyì) is the standard term across all Chinese-speaking regions.

#### In Hindi-speaking regions (India)

**Research findings:**
CS education in India is predominantly English-medium, even in Hindi-speaking regions.

**Terminology preferences:**
When Hindi is used:

- परिभाषित करना (paribhaashit karna) - infinitive form meaning "to define"
- This is Sanskrit-derived, formal technical vocabulary

**Popular resources:**

- IITs (Indian Institutes of Technology): English medium
- Hindi programming tutorials: Use परिभाषित करना when explaining in Hindi

**Language reality:** Most Indian programmers code in English but may discuss concepts in Hindi. The term
परिभाषित (paribhaashit) is well-understood in technical contexts.

### Synthesis

**Most common approach across languages:**
All regions teach `def` as "define a function" or equivalent. The concept is universal:

- You're creating/declaring a function
- The function is a reusable block of code
- It's like a recipe, machine, or mathematical function

**Key vocabulary alignment:**

- Spanish: "definir" (infinitive)
- Arabic: "تعريف" (masdar/verbal noun)
- Chinese: "定义" (dictionary form)
- Hindi: "परिभाषित करना" (infinitive)

**Recommendation:**
All languages converge on the concept of "to define" in infinitive or neutral form. This aligns perfectly with
the linguistic standard recommendation of using infinitive for action keywords.

---

## Enhanced Cross-References

### Functional Relationships

**How `def` works WITH other terms:**

#### Relationship 1: `def` + `return`

**Context:** Almost every function (except those with side effects only) returns a value

```python
def calculate_total(price, tax_rate):  # def creates function
    total = price + (price * tax_rate)
    return total  # return sends back the result
```

**Translation note:** Both should use infinitive form. If `def` is translated as infinitive ("definir"),
then `return` should also be infinitive ("retornar", not noun "devolución").

**Why they must align:** They appear together in 90%+ of functions. Inconsistent forms would look unnatural:

- ✅ Consistent: `definir ... retornar` (both infinitive)
- ❌ Inconsistent: `definir ... devolución` (infinitive + noun)

#### Relationship 2: `def` + `class`

**Context:** Functions defined inside classes become methods

```python
class Calculator:
    def add(self, x, y):  # def creates method
        return x + y
```

**Translation note:** Both `def` and `class` are structure-creating keywords. They should use parallel
forms:

- If `def` = infinitive verb ("definir")
- Then `class` should match structure ("clase" as noun is OK because it's a type definition, not action)

#### Relationship 3: `def` + `lambda`

**Context:** Both create functions, but different styles

```python
# Full function with def
def square(x):
    return x ** 2

# Anonymous function with lambda
square_lambda = lambda x: x ** 2
```

**Translation note:** `lambda` is a special case (Greek letter, mathematical term). Most languages keep
"lambda" untranslated. `def` should still be translated as action verb.

### Conceptual Hierarchy

**Where `def` sits in Python's mental model:**

```text
Python Statement Types
├── Simple Statements
│   ├── pass
│   ├── return
│   └── break
└── Compound Statements
    ├── Function Definitions
    │   ├── def ← THIS KEYWORD
    │   ├── async def
    │   └── lambda (expression, not statement)
    ├── Class Definitions
    │   └── class
    └── Control Flow
        ├── if/elif/else
        ├── for/while
        └── with
```

**What this hierarchy means for translation:**
`def` belongs to the "compound statement" family. All compound statements (def, class, if, for, while, with)
should use consistent grammatical forms in the target language. If action keywords like `def` use infinitive,
other action keywords should too.

### Translation Consistency Requirements

**Terms that MUST align linguistically with `def`:**

When translating `def`:

- [ ] Check your `return` translation (both are action keywords in function context)
- [ ] Check your `class` translation (both create named objects)
- [ ] Check your `break`/`continue` translations (all action keywords)
- [ ] Check your `pass` translation (action/state keyword)

**Consistency rule:**
All **action keywords** (keywords that DO something) should use the same verb form. Don't mix infinitive,
gerund, and imperative forms.

**Good example (consistent):**

Spanish:

- `def` → "definir" (infinitive)
- `return` → "retornar" (infinitive)
- `break` → "romper" (infinitive)
- `continue` → "continuar" (infinitive)

All action verbs use infinitive ✅

**Bad example (inconsistent):**

Spanish:

- `def` → "definir" (infinitive)
- `return` → "devolviendo" (gerund) ❌
- `break` → "rompe" (imperative) ❌
- `continue` → "continuación" (noun) ❌

Mixed forms look unprofessional and confusing.

---

## Cognitive Load & Learning Considerations

### Memory Load

**Is this translation easy to remember?**
Yes, "define" is a universal programming concept. Most languages have a cognate or well-established
equivalent:

- Spanish: definir (cognate)
- French: définir (cognate)
- German: definieren (cognate)
- Arabic: تعريف (standard CS term)
- Chinese: 定义 (established CS term)

**Mnemonic potential:**
Strong. The concept of "defining" is familiar from mathematics (define variables), dictionaries (define words),
and everyday language.

**Cognitive cognate advantage:**
For Romance and Germanic languages, "define" → "definir"/"définir"/"definieren" provides immediate recognition
for bilingual developers. This reduces cognitive load when switching between languages.

### Disambiguation

**If this term has multiple meanings in target language:**
In English, "define" has one clear meaning in programming contexts. No ambiguity.

In other languages:

- Spanish "definir" is unambiguous in technical contexts
- Chinese 定义 is standard CS term, no confusion
- Arabic تعريف could mean "introduction" in non-technical contexts, but in programming it clearly means
  "define"

**Test:** Would a learner confuse this with another meaning?
No. In the context of code, "define function" is universally understood.

### Pronunciation

**Can developers say this term out loud easily?**
Yes. All recommended translations are common words:

- "definir" — easy to say in Spanish
- "définir" — easy in French
- "定义" (dìngyì) — two syllables, common Chinese word
- "تعريف" (ta'rīf) — common Arabic word

**Why this matters:** Developers verbalize code during pair programming, code reviews, and teaching.
"We define a function here..." should flow naturally.

**Test:** Try saying "define a function" with your translation

- Spanish: "definir una función" ✅ flows naturally
- French: "définir une fonction" ✅ natural
- German: "eine Funktion definieren" ✅ natural

### Visual Recognition

**Can learners quickly spot `def` when scanning code?**
`def` is extremely recognizable:

- Short (3 letters)
- Distinctive (starts most function definitions)
- Always at start of line (at current indentation)
- Followed by function name (easy pattern)

Translations should preserve this quick-scan quality:

- Keep translation short (1 word preferred)
- Distinctive from other keywords
- Easy to spot at a glance

**Good:** "definir" (7 letters, still short, distinctive)
**Avoid:** "crear una función llamada" (way too long, hard to scan)

### Cross-Language Transfer

**Many programmers are multilingual:**

**Balance needed:**

- Native clarity: "definir" is immediately clear to Spanish speakers
- English resource compatibility: Spanish developers can easily map "definir" → "def" when reading English
  docs

**Advantage of cognates:**
Languages with cognates (Romance, Germanic) get the best of both worlds:

- "definir" is natural Spanish
- Spanish→English mapping is trivial (definir ≈ define)

**For non-cognate languages:**
Document the mapping clearly:

- Chinese 定义 (dìngyì) = English "define"
- Arabic تعريف (ta'rīf) = English "define"

This helps developers navigate Stack Overflow, official docs, and English resources.

---

## Translation Validation Criteria

### For Human Reviewers & Beta Testers

Use this checklist to evaluate the translation of `def`:

#### Concept Accuracy (CRITICAL)

- [ ] Does this translation capture what `def` DOES? (creates a function)
- [ ] Would a native speaker understand its function in code?
- [ ] Does it avoid misleading connotations?
- [ ] Is it technically precise?

**Test:** Show the translation to a native speaker programmer without context. Can they guess it means
"define a function"?

#### Linguistic Correctness

- [ ] Is the part of speech correct? (Should be verb)
- [ ] Is the form correct? (Should be infinitive or equivalent neutral form)
- [ ] Does it follow target language grammar rules?
- [ ] Is capitalization appropriate? (Should be all lowercase: `definir`, not `Definir`)
- [ ] For RTL languages: No unnecessary diacritics?
- [ ] For gendered languages: N/A (verbs typically don't have gender)

#### Consistency with Pattern

- [ ] Matches other action keywords? (`return`, `break`, `continue` should use same form)
- [ ] Uses same verb form as similar action keywords?
- [ ] Aligns with `class` (both create named objects)?

#### Usability

- [ ] Short enough? (1 word ideal, 2 words maximum)
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?
- [ ] Visually scannable in code?

**Test:** Type it 10 times quickly. Does it flow?

#### Cultural Appropriateness

- [ ] No offensive meanings?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?
- [ ] Appropriate register? (Technical/formal, not slang)

#### CS Education Alignment

- [ ] Matches terminology used in target language CS education?
- [ ] Checked against textbooks/tutorials in target language?
- [ ] Would students recognize this term from their classes?

**For `def`, the answer should be YES for all major languages:**

- Spanish: "definir" is standard CS term ✅
- Arabic: "تعريف" is standard technical term ✅
- Chinese: "定义" is established CS term ✅

#### Technical Compatibility

- [ ] Uses correct character set (Unicode block) for language?
- [ ] Will render in common fonts?
- [ ] Will display in VS Code/PyCharm/terminals?
- [ ] For RTL: Tested bidirectional text rendering?
- [ ] No special characters that break syntax highlighting?

### Severity Levels

**P0 (Blocker - Must fix):**

- Translation doesn't mean "define" (wrong concept)
- Offensive or culturally inappropriate
- Impossible to type on standard keyboard

**P1 (High - Should fix):**

- Wrong verb form (gerund instead of infinitive)
- Inconsistent with `return` or other action keywords
- Too long (>2 words)

**P2 (Medium - Nice to fix):**

- Doesn't align with regional CS education (use non-standard term)
- Slightly awkward pronunciation
- Missing cognate advantage when cognate exists

**P3 (Low - Optional):**

- Could use a slightly shorter synonym
- Alternative might be 5% more natural

---

## For Native Speakers of Non-English Languages

### Conceptual Understanding (Language-Agnostic)

**The Core Concept:**
`def` marks the creation of a reusable piece of code. You're telling the computer: "Here's a set of
instructions I want to use multiple times. Remember this with a specific name."

**Think of it as:**
Creating a recipe, naming a tool, or defining a word in a dictionary. You're making something official and
reusable.

**What mental model should you have?**
When you see `def`:

1. A new code block is being created
2. This block will have a name
3. It can accept inputs (parameters)
4. It can produce outputs (return values)
5. Once created, you can use it over and over

### Translation Considerations

**Key Aspects to Preserve:**

1. **Creation/Definition aspect:** The translation should convey that you're creating something new
2. **Naming aspect:** Emphasize that the function gets a name
3. **Action aspect:** This is a command/action, not a description

**Questions to Ask Yourself:**

1. Does my translation capture the **action** of creating a function?
2. Would a programmer in my language immediately understand this?
3. Is this consistent with how "define" is taught in programming courses in my region?
4. Does this follow my language's technical terminology patterns?

**Action-Oriented vs Result-Oriented:**
`def` is action-oriented — it's the act of defining. Your translation should be an action verb (infinitive
form), not a noun (result).

✅ Good: "to define", "to create", "to declare"
❌ Bad: "definition", "creation", "declaration"

**Verb vs Noun Preference:**
Must be a verb. `def` is a command that does something.

**Cultural Context:**

- **English speakers think of this as:** The act of defining/creating a function
- **Consider translating the concept as:** The equivalent action verb in your language that means "to define",
  "to create", or "to declare"

**If your language has multiple words for "define":**
Choose the one used in technical/educational contexts, not casual conversation.

Example:

- Spanish has "definir" (technical) and "explicar" (explain, casual)
- Use "definir" (technical) ✅

---

## Usage Examples

### Basic Usage

```python
# Example 1: Simple function with no parameters
def say_hello():
    print("Hello, world!")

say_hello()  # Call the function
```

**What this does:**
Defines a function named `say_hello` that prints "Hello, world!" when called.

**Output:**

```text
Hello, world!
```

### Intermediate Usage

```python
# Example 2: Function with parameters and return value
def add_numbers(a, b):
    """Add two numbers and return the result."""
    result = a + b
    return result

total = add_numbers(5, 3)
print(total)  # 8
```

**What this does:**
Defines a function that takes two parameters, adds them, and returns the sum.

### Advanced Usage

```python
# Example 3: Function with default parameters and type hints
def greet(name: str, greeting: str = "Hello") -> str:
    """
    Generate a personalized greeting.

    Args:
        name: The person's name
        greeting: The greeting word (default: "Hello")

    Returns:
        Formatted greeting string
    """
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Hello, Alice!
print(greet("Bob", "Hi"))          # Hi, Bob!
print(greet("Charlie", greeting="Hey"))  # Hey, Charlie!
```

**What this does:**
Defines a function with type hints, default parameter, docstring, and returns formatted string.

### Real-World Example

```python
# Example 4: Practical real-world use - data processing
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculate final price after applying discount.

    Args:
        price: Original price
        discount_percent: Discount as percentage (e.g., 20 for 20%)

    Returns:
        Final price after discount

    Example:
        >>> calculate_discount(100.0, 20.0)
        80.0
    """
    if price < 0 or discount_percent < 0:
        raise ValueError("Price and discount must be non-negative")

    if discount_percent > 100:
        raise ValueError("Discount cannot exceed 100%")

    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    return round(final_price, 2)

# Usage in e-commerce system
original_price = 149.99
discount = 15  # 15% off
final_price = calculate_discount(original_price, discount)
print(f"Original: ${original_price:.2f}")
print(f"Discount: {discount}%")
print(f"Final: ${final_price:.2f}")
```

**Context:**
This is how you'd use `def` in a real e-commerce system to calculate discounted prices with proper validation
and error handling.

---

## Common Pitfalls

### Pitfall 1: Forgetting the colon

**Problem:**

```python
# Missing colon after function signature
def greet(name)  # ❌ SyntaxError
    print(f"Hello, {name}")
```

**Solution:**

```python
# Must include colon
def greet(name):  # ✅ Correct
    print(f"Hello, {name}")
```

**Why this happens:**
New programmers forget that Python uses colons to mark the start of code blocks.

### Pitfall 2: Incorrect indentation

**Problem:**

```python
# Function body not indented
def greet(name):
print(f"Hello, {name}")  # ❌ IndentationError
```

**Solution:**

```python
# Function body must be indented
def greet(name):
    print(f"Hello, {name}")  # ✅ Correct (4 spaces)
```

**Why this happens:**
Python uses indentation to define code blocks, unlike languages that use braces `{}`.

### Pitfall 3: Mutable default arguments

**Problem:**

```python
# Dangerous: list created once at definition time
def add_item(item, items=[]):  # ❌ Surprising behavior
    items.append(item)
    return items

print(add_item(1))  # [1]
print(add_item(2))  # [1, 2] — reuses same list!
print(add_item(3))  # [1, 2, 3]
```

**Solution:**

```python
# Use None and create new list each time
def add_item(item, items=None):  # ✅ Correct
    if items is None:
        items = []
    items.append(item)
    return items

print(add_item(1))  # [1]
print(add_item(2))  # [2] — new list each time
print(add_item(3))  # [3]
```

**Why this happens:**
Default arguments are created once when the function is defined, not each time it's called.

---

## Best Practices

1. **Use descriptive function names:** `calculate_total()` not `calc()` or `ct()`
2. **Include docstrings:** Document what the function does, its parameters, and return value
3. **Keep functions focused:** One function should do one thing well (Single Responsibility Principle)
4. **Use type hints:** Help other developers (and tools) understand what types are expected
5. **Avoid mutable default arguments:** Use `None` and create inside function
6. **Return early for error cases:** Check conditions at start and return/raise early

---

## Further Reading

### Official Documentation

- [Python Tutorial: Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [Python Language Reference: Function Definitions](https://docs.python.org/3/reference/compound_stmts.html#function-definitions)
- [Built-in Functions: Python Functions](https://docs.python.org/3/library/functions.html)

### Python Enhancement Proposals (PEPs)

- [PEP 3107: Function Annotations](https://peps.python.org/pep-3107/)
- [PEP 484: Type Hints](https://peps.python.org/pep-0484/)
- [PEP 570: Positional-Only Parameters](https://peps.python.org/pep-0570/)

### Historical Context

- [Python History Blog: Origin of Functions](https://python-history.blogspot.com/)
- [Guido van Rossum's Essays on Python Design](https://www.python.org/doc/essays/)

### Tutorials & Guides

- [Real Python: Defining Your Own Functions](https://realpython.com/defining-your-own-python-function/)
- [Python.org Tutorial: More on Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions)

---

**Document Version:** 1.0 (Example)
**Created:** 2025-11-10
**Maintained by:** Legesher Team
**Target Audience:** Human translators, beta testers, future educational platform
**For AI Translation:** Use Tier 1 brief template (`context-template-tier1.md`)

**Translation Recommendations Summary:**

| Language | Translation | Form | Confidence |
|----------|-------------|------|------------|
| Spanish | definir | Infinitive | HIGH |
| French | définir | Infinitive | HIGH |
| German | definieren | Infinitive | HIGH |
| Arabic | تعريف | Masdar | HIGH |
| Chinese | 定义 | Dictionary form | HIGH |
| Hindi | परिभाषित करना | Infinitive | HIGH |
| Japanese | 定義する | Dictionary form | HIGH |
| Korean | 정의하다 | Dictionary form | HIGH |

All recommendations align with CS education terminology in respective languages.
