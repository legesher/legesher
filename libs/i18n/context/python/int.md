# Python Builtin Type: `int` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (type constructor)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `int` type in Python represents integer numbers (whole numbers without decimal points). It supports unlimited precision (arbitrary size) and serves both as a type name and a constructor function to convert other values to integers.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Creating an integer
x = int(42)
# or simply:
y = 42  # Python infers this is an int
```

**What this does:** The `int()` function creates an integer object. When you write a number without a decimal point, Python automatically treats it as an `int`. Calling `int()` explicitly is usually for type conversion.

### Example 2: Common Pattern

```python
# Converting string to integer
user_input = "123"
number = int(user_input)
print(number + 10)  # Output: 133

# Converting float to integer (truncates decimal)
pi_approx = int(3.14159)  # Result: 3
```

**What this does:** The most common use of `int()` is converting strings or floats to integers. String conversion requires the string to contain a valid number. Float conversion truncates (removes) the decimal part without rounding.

### Example 3: Edge Case

```python
# Base conversion - parsing binary, octal, hex
binary_str = "1010"
decimal = int(binary_str, 2)  # Result: 10 (binary to decimal)

hex_str = "FF"
decimal2 = int(hex_str, 16)  # Result: 255 (hex to decimal)
```

**What this shows:** `int()` accepts an optional second argument specifying the number base (2-36). This allows parsing strings in binary, octal, hexadecimal, or any base. Without the base argument, it assumes base 10 (decimal).

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR / PRIMITIVE TYPE

**Similar terms in this pattern:**

1. `float` - Floating-point (decimal) numbers
2. `str` - String (text) type
3. `bool` - Boolean (True/False) type

**Pattern rule:** Type constructors should use noun forms in target language. They name a category/class of values, not actions. Think "integer" (noun) not "make integer" (verb).


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "integer" meant "whole, complete, untouched" - from "in-" (not) + "tangere" (to touch). An integer is a number that hasn't been "touched" or divided - it remains whole with no fractional part.

**Why Python uses this:** Abbreviated from "integer," the mathematical term for whole numbers. Most programming languages use `int` as shorthand since it's typed frequently. Python follows this convention, though the full mathematical term is "integer."

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `int` type represents whole numbers in Python - positive, negative, or zero, without fractional components. Unlike many languages (C, Java) where integers have fixed sizes (32-bit, 64-bit), Python 3's `int` has unlimited precision. It can represent arbitrarily large numbers, limited only by available memory (e.g., `10**1000` is valid).

Python's `int()` serves dual purposes: it's both the type name and a constructor function. As a constructor, it converts other types to integers: strings are parsed (`int("42")`), floats are truncated (`int(3.9)` → 3), and booleans convert to 0/1 (`int(True)` → 1). The constructor also supports base conversion for strings, enabling parsing of binary, octal, hex, or custom bases.

Integers support all standard arithmetic operations: `+`, `-`, `*`, `/`, `//` (floor division), `%` (modulo), `**` (power). Division `/` always returns a float, even for whole results (`6/2` → `3.0`). Use `//` for integer division (`7//2` → `3`).

**Key behaviors:**

1. **Unlimited precision:** Python integers can grow infinitely large. No overflow errors - `999**999` computes successfully (though may take time/memory). This differs from fixed-size integers in C/Java.

2. **Immutable:** Integers are immutable objects. Operations create new integers rather than modifying existing ones. `x = 5; x += 1` creates a new integer 6, doesn't modify the original 5.

3. **Constructor flexibility:** `int()` can parse strings in various bases, convert floats (truncating), convert booleans, or be called with no arguments (returns 0). Custom objects can define `__int__()` method for conversion.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun - names a type/category of values
- **Action vs State:** STATE/CATEGORY - describes what something IS, not an action
- **Temporal aspect:** Timeless - a type is a permanent classification

### Recommended Form

**Primary recommendation:** Use the mathematical term for "integer" or "whole number" in your target language. This should be the same term taught in mathematics education. Avoid abbreviating unless the abbreviation is universally recognized in that language's CS education.

**Forms to AVOID:**

- ❌ Verb form - "to make whole" (wrong part of speech)
- ❌ English loanword "int" spelled in target script - unless universally adopted
- ❌ Overly technical terms not used in education

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (but parent word "integer" does)

**"Integer" English context:**

English "integer" is unambiguous in mathematics/CS - it means whole number. The abbreviation "int" in programming specifically refers to this type.

**Target language considerations:**

Some languages have multiple words for "whole":

1. **Whole (complete/entire)**
2. **Whole (unbroken/intact)**
3. **Whole (integer - mathematical)** ✅ **This is the meaning**

Use the mathematical term, not general words for "whole," "complete," or "all/entire."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `int`, check these translations:**

- [ ] `float` - Must use similar noun structure (both are numeric types)
- [ ] `str` - Must use noun form (type name)
- [ ] `bool` - Must use noun form (type name)
- [ ] `type` - Should use noun ("type" concept)

**Consistency rule:**

All type constructors (`int`, `float`, `str`, `bool`, `list`, `dict`, `set`, `tuple`) must use the same grammatical category - all nouns. Don't mix noun types with verb types.


### Functional relationships

**This term works WITH:**

1. **Type checking:** `isinstance(x, int)`, `type(x) == int`
2. **Type conversion:** `int("123")`, `int(3.14)`, `int(True)`
3. **Arithmetic operations:** `x + y`, `x * y`, `x // y` (integer operators)

**Common pairing:**

```python
# int used for type conversion
num = int(input("Enter number: "))

# int used in type hints
def calculate(x: int, y: int) -> int:
    return x + y

# int in isinstance checks
if isinstance(value, int):
    process_integer(value)

# int with base conversion
binary_num = int("1010", 2)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `int`

- "Integer" is a universal mathematical concept
- Every language teaches integers in basic mathematics
- Standard translations exist in all educational systems
- Well-documented in CS contexts globally

**For this term:** EASY

**Rationale:** The concept of whole numbers (integers) predates computers and appears in every culture's mathematics. The term "integer" or its equivalent is taught in elementary education worldwide. Translation is straightforward: use the mathematical term for "integer" or "whole number."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The only minor consideration: whether to abbreviate (like English "int") or use full word ("integer"). Follow your target language's CS education conventions.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures INTEGER/WHOLE NUMBER concept (not just "number")?
- [ ] Distinguishes from floating-point (decimal) numbers?
- [ ] Matches mathematical definition of integer?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (singular noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other type names (`float`, `str`, `bool`)?
- [ ] All type names use same grammatical form (nouns)?
- [ ] Aligns with mathematical terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (ideally, standard math term)?

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
term: int
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
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
