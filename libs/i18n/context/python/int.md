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

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `float` | flotante | عدد_عشري | 浮点数 | दशमलव |
| `str` | cadena | سلسلة | 字符串 | स्ट्रिंग |
| `int` | **entero** | **عدد_صحيح** | **整数** | **पूर्णांक** |

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

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun or adjective-as-noun | "entero" (whole/integer) - mathematical term |
| Germanic (de, nl, sv) | Noun | "ganz" or "ganzzahl" (whole number) |
| Slavic (ru, pl, uk) | Noun | "целое" (whole number) |
| Arabic | Noun phrase | "عدد صحيح" (whole number) or abbreviated |
| Chinese | Noun compound | "整数" (whole number) - standard math term |
| Hindi | Noun | "पूर्णांक" (complete number) - Sanskrit math term |

**Primary recommendation:** Use the mathematical term for "integer" or "whole number" in your target language. This should be the same term taught in mathematics education. Avoid abbreviating unless the abbreviation is universally recognized in that language's CS education.

**Forms to AVOID:**

- ❌ Verb form - "to make whole" (wrong part of speech)
- ❌ English loanword "int" spelled in target script - unless universally adopted
- ❌ Overly technical terms not used in education

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `entero`
- **Form:** Noun (masculine)
- **Why it works:** Standard Spanish mathematical term for integer. "Número entero" is taught in schools. Natural, widely recognized, appropriate length. Used consistently in Spanish programming materials.

**Arabic:**

- **Translation:** `عدد_صحيح` (ʿadad ṣaḥīḥ) or `صحيح` (ṣaḥīḥ)
- **Form:** Noun phrase (number + adjective) or shortened form
- **Why it works:** "عدد صحيح" literally means "whole/correct number" - the standard Arabic mathematical term. Could be abbreviated to just `صحيح` for brevity while maintaining clarity.

**Chinese:**

- **Translation:** `整数` (zhěngshù)
- **Form:** Noun compound
- **Why it works:** Standard Chinese mathematical term. Two characters: 整 (whole/complete) + 数 (number). Universally used in Chinese education and programming. Concise and clear.

**Hindi:**

- **Translation:** `पूर्णांक` (pūrṇāṅka)
- **Form:** Noun (Sanskrit compound)
- **Why it works:** Sanskrit-derived mathematical term: पूर्ण (complete) + अंक (digit/number). Standard in Hindi mathematics education. Formal register appropriate for programming. Alternative: `इंट` (int - transliteration) less preferred but understood.

### ❌ Common Translation Mistakes

**Mistake 1: Using only "number" without "whole/integer" qualifier**

- **Wrong:** `número` (Spanish - just "number")
- **Why wrong:** Too general - doesn't distinguish integers from floats or other numeric types. Python has multiple number types; must be specific.
- **Right:** `entero` (integer/whole number)

**Mistake 2: Using verb "to convert" or "to make integer"**

- **Wrong:** `enterar` (Spanish - invented verb)
- **Why wrong:** Type names are nouns, not verbs. While `int()` can be used as a function, the fundamental concept is a noun - a category of numbers.
- **Right:** `entero` (noun)

**Mistake 3: Abbreviation without context**

- **Wrong:** `ent` (Spanish abbreviation)
- **Why wrong:** Unclear abbreviation not standard in Spanish CS education. While English uses "int" (universally recognized abbreviation), this doesn't translate well. Use full word unless abbreviation is standard.
- **Right:** `entero` (full word, or `int` if adopted as loanword)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (but parent word "integer" does)

**"Integer" English context:**

English "integer" is unambiguous in mathematics/CS - it means whole number. The abbreviation "int" in programming specifically refers to this type.

**Target language considerations:**

Some languages have multiple words for "whole":

1. **Whole (complete/entire)** - totalidad, completo
2. **Whole (unbroken/intact)** - intacto
3. **Whole (integer - mathematical)** ✅ **This is the meaning**

**Example (Spanish):**

- "entero" - whole/integer (mathematical term) ✅
- "completo" - whole/complete (full, not partial)
- "todo" - whole/all (entire)

Use the mathematical term, not general words for "whole" or "complete."

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

**Example:**

Spanish: `entero`, `flotante`, `cadena`, `booleano` - all nouns ✅
NOT: `entero` (noun) + `convertir_cadena` (verb phrase) ❌

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
language: es
translation: entero
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "entero" is the standard mathematical term for integer, taught universally in Spanish education. It clearly distinguishes integers from floats and maintains consistency with mathematical terminology. Natural, concise, and widely recognized across Spanish-speaking programming communities.

**Alternatives considered:**

1. `int` (English loanword) - Not necessary; Spanish has clear equivalent
2. `número_entero` (full phrase) - Too verbose; `entero` sufficient in context
3. `integral` - Adjective form; noun preferred for type names

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Integer is a universal mathematical concept with well-established translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
