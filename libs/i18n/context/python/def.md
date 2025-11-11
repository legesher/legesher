# Python Keyword: `def` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `def` keyword in Python introduces a function definition, declaring a reusable block of code with a name, optional parameters, and a body. It's short for "define" and creates a function object that can be called multiple times with different arguments.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Define a simple function
def greet():
    print("Hello!")

greet()  # Call the function - Output: Hello!
```

**What this does:** `def` declares a function named `greet` with no parameters. The indented block is the function body. The function object is created and bound to the name `greet`, which can then be called using `greet()`.

### Example 2: Common Pattern

```python
# Function with parameters and return value
def add(a, b):
    result = a + b
    return result

total = add(5, 3)  # total = 8
```

**What this does:** Defines `add` function taking two parameters. The body computes their sum and returns it. Parameters `a` and `b` are local variables receiving values when the function is called. This demonstrates the complete function pattern: parameters, computation, return.

### Example 3: Edge Case

```python
# Function with default arguments and docstring
def power(base, exponent=2):
    """Calculate base raised to exponent (default: square)."""
    return base ** exponent

print(power(5))      # 25 (uses default exponent=2)
print(power(5, 3))   # 125 (overrides default)
```

**What this shows:** Functions can have default parameter values, making them optional. The first string in the function body (docstring) documents the function's purpose. Default arguments provide flexibility: callers can omit them or provide explicit values.

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Definition/Declaration)

**Similar terms in this pattern:**

1. `class` - Defines a class (similar structure: definition keyword + name + body)
2. `lambda` - Defines anonymous function (expression form of def)
3. `async def` - Defines asynchronous function (variation of def)

**Pattern rule:** Definition keywords should use verb forms (infinitive) suggesting creation or declaration. They perform the action of bringing something into existence.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `class` | clase | صنف | 类 | वर्ग |
| `lambda` | lambda | لامدا | λ | लैम्डा |
| `def` | **definir** | **تعريف** | **定义** | **परिभाषित** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "definire" meant "to limit, determine, explain." Through Old French "definer," it became English "define" - to state the meaning or nature of something, to establish boundaries or characteristics.

**Why Python uses this:** "Def" abbreviates "define," clearly expressing the action: we're defining/creating a function. Most languages use keywords like "function" or "def" for this purpose. Python chose the terse "def" to reduce verbosity while remaining clear - matching Python's philosophy of concise readability.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `def` statement creates a function object and binds it to a name in the current scope. The syntax is `def name(parameters): body`. When Python encounters `def`, it compiles the function body into executable code, wraps it in a function object with the specified name and parameters, and assigns that object to the name in the namespace.

Function definition happens at runtime, not compile time. When `def` executes, Python creates the function object at that moment. This means functions can be defined conditionally (inside `if` statements) or repeatedly (inside loops), and they capture their definition-time environment (closures).

Parameters can have default values, type hints, and special forms (`*args` for variable positional arguments, `**kwargs` for keyword arguments). The function body can contain any statements, including nested `def` statements (inner functions). Functions are first-class objects - they can be assigned to variables, passed as arguments, and returned from other functions.

**Key behaviors:**

1. **Creates callable object:** `def` doesn't just reserve a name; it creates an actual function object with attributes like `__name__`, `__doc__`, and `__code__`. The function is a value that can be manipulated.

2. **Local scope creation:** Each function call creates a new local namespace. Parameters and variables defined inside the function are local (unless declared `global` or `nonlocal`). This isolation prevents naming conflicts.

3. **First-class functions:** The function object created by `def` can be reassigned, passed to other functions, stored in data structures, or returned from functions. `def func(): ...` is roughly equivalent to `func = lambda: ...` (though `def` is more powerful).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Transitive verb (takes object - what to define)
- **Action vs State:** Pure ACTION - performs creation/definition
- **Temporal aspect:** Instantaneous/resultative - creates something that then exists

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "definir", "définir" - to define |
| Germanic (de, nl, sv) | Infinitive verb | "definieren", "definiëren" - to define |
| Slavic (ru, pl, uk) | Infinitive verb | "определить", "zdefiniować" - to define |
| Arabic | Masdar (verbal noun) | "تعريف" (definition/defining) - standard for declarations |
| Chinese | Verb compound | "定义" - define/determine meaning |
| Hindi | Verbal adjective/infinitive | "परिभाषित" (defined) or "परिभाषित करना" (to define) |

**Primary recommendation:** Use infinitive verb form meaning "to define" or "to declare." This should be the same word used in mathematics or dictionaries for defining terms.

**Forms to AVOID:**

- ❌ Using noun "definition" - should be verb "to define"
- ❌ Using "function" - that's what you're creating, not the action
- ❌ Using "declare" if your language has "define" - "define" is more precise

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `definir`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish verb "to define." Used in mathematics, dictionaries, and programming for establishing definitions. Natural in constructions like "definir una función" (define a function). Universally recognized in Spanish CS education.

**Arabic:**

- **Translation:** `تعريف` (taʿrīf)
- **Form:** Masdar (verbal noun)
- **Why it works:** Root ع-ر-ف (ʿ-r-f) means "to know/recognize." Masdar "تعريف" means "definition/defining." Standard Arabic term for declarations and definitions in programming. Used in CS textbooks across Arabic-speaking regions.

**Chinese:**

- **Translation:** `定义` (dìngyì)
- **Form:** Verb compound
- **Why it works:** Two characters: 定 (determine/fix) + 义 (meaning/righteousness). Standard Chinese term for "define" used in mathematics, logic, and programming. Universally recognized in Chinese CS education.

**Hindi:**

- **Translation:** `परिभाषित` (paribhāṣita) or `परिभाषित_करना` (paribhāṣita karnā)
- **Form:** Verbal adjective or infinitive compound
- **Why it works:** Sanskrit-derived term for "defined" or "to define." Formal register appropriate for programming. `परिभाषित करना` is full infinitive form; `परिभाषित` alone may be acceptable as shortened form.

### ❌ Common Translation Mistakes

**Mistake 1: Using noun "definition" instead of verb "define"**

- **Wrong:** `definición` (Spanish - "definition" - noun)
- **Why wrong:** Keywords are actions (verbs), not concepts (nouns). We're performing the action of defining, not referring to the concept of definition.
- **Right:** `definir` (verb infinitive)

**Mistake 2: Using "function" instead of "define"**

- **Wrong:** `función` (Spanish - "function")
- **Why wrong:** "Function" is what we're creating (the object), not the action. Like saying "create" vs. "thing being created." The keyword performs definition, doesn't name the result.
- **Right:** `definir` (the action of creating a function)

**Mistake 3: Using "declare" when "define" is more specific**

- **Wrong:** `declarar` (Spanish - "to declare")
- **Why wrong:** "Declare" can mean announcing existence without providing content ("declare variable"). "Define" means providing the complete specification (name, parameters, body). "Def" does the latter.
- **Right:** `definir` (provides complete function specification)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (but parent word "define" does)

**"Define" English context:**

English "define" can mean:

1. "Define the boundaries" (establish limits) ⚠️
2. "Define a word" (state meaning) ⚠️
3. "Define a function" (create with complete specification) ✅ **This is the Python meaning**

All meanings share the core concept of "establishing what something is," but in programming, "define" specifically means "create with complete specification."

**Your translation should capture the programming sense: creating/establishing a function with its name, parameters, and behavior.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `def`, check these translations:**

- [ ] `class` - Similar definition structure; should use compatible verb form
- [ ] `lambda` - Alternative function definition; relationship should be clear
- [ ] `return` - Functions defined with `def` use `return`; both should be verbs

**Consistency rule:**

All definition keywords (`def`, `class`) and function-related keywords (`return`, `yield`) should use verb forms. They're all actions in the function lifecycle.

**Example:**

Spanish: `definir` (def), `clase` (class), `retornar` (return) - verbs for actions, nouns for objects ✅

### Functional relationships

**This term works WITH:**

1. **`def` + parameters + `return`**: Complete function pattern
```python
def calculate(x, y):
    return x + y
```

2. **`def` + default arguments**: Flexible functions
```python
def greet(name="World"):
    return f"Hello, {name}"
```

**Common pairing:**

```python
# basic function definition
def say_hello():
    print("Hello")

# function with parameters
def add(a, b):
    return a + b

# function with default arguments
def power(base, exp=2):
    return base ** exp

# function with type hints
def divide(a: float, b: float) -> float:
    return a / b

# nested function
def outer():
    def inner():
        return "nested"
    return inner
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `def`:

- Universal programming concept (all languages define functions)
- "Define" is standard mathematical/logical term
- Well-established translations globally
- Clear distinction from similar concepts (declare, create)

**For this term:** EASY

**Rationale:** The concept of defining functions is fundamental to programming. The word "define" exists in mathematics, logic, and programming across all languages. Standard translations are well-documented and universally recognized in CS education.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The main question is whether to use the full word "define" or abbreviate. Follow your target language's conventions - if abbreviations are common in programming keywords, abbreviate; otherwise, use full word.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FUNCTION DEFINITION concept (creating with specification)?
- [ ] Emphasizes action of defining, not the resulting function?
- [ ] Understood as creating executable code block?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive, not conjugated)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other definition keywords (`class`)?
- [ ] Uses verb form like other action keywords?
- [ ] Aligns with how functions are discussed in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (ideally, common word)?

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
term: def
language: es
translation: definir
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "definir" is the standard verb for defining functions, used universally in mathematics, logic, and programming. It clearly expresses the action of creating a function with complete specification (name, parameters, body). Recognized across all Spanish-speaking CS education systems.

**Alternatives considered:**

1. `def` (keep English abbreviation) - Possible if English loanwords common, but translation preferred
2. `función` (function - noun) - Wrong part of speech; names the object, not the action
3. `declarar` (declare) - Less specific; "define" includes providing the body, not just announcing

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Function definition is universal in programming, and "define" is a standard mathematical/logical term with clear translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
