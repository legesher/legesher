# Python Builtin Type: `float` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (numeric type)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `float` type in Python represents floating-point numbers (decimals). It stores approximate real numbers using IEEE 754 double-precision format, supporting decimal fractions and scientific notation.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create a float
price = 19.99
temperature = -3.5
print(type(price))  # <class 'float'>
```

**What this does:** Creates floating-point numbers with decimal points. Any number with a decimal point is automatically a float in Python.

### Example 2: Common Pattern

```python
# Convert integer to float
whole_number = 42
decimal_number = float(whole_number)  # 42.0

# Scientific notation
speed_of_light = 3.0e8  # 3.0 × 10^8 = 300000000.0
atom_size = 1.5e-10     # 0.00000000015

# Division always returns float
result = 10 / 4  # 2.5 (not 2)
```

**What this does:** Demonstrates type conversion, scientific notation syntax, and that division always produces floats even with integer operands.

### Example 3: Edge Case

```python
# Floating-point precision issues
result = 0.1 + 0.2
print(result)  # 0.30000000000000004 (not exactly 0.3!)

# Special float values
positive_infinity = float('inf')
negative_infinity = float('-inf')
not_a_number = float('nan')

# Checking for special values
import math
math.isinf(positive_infinity)  # True
math.isnan(not_a_number)       # True
```

**What this shows:** Floats have precision limitations due to binary representation. Special values (infinity, NaN) exist. Never test float equality with `==`; use tolerances instead.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Numeric Type)

**Similar terms in this pattern:**

1. `int` - Integer numbers (whole numbers, no decimals)
2. `complex` - Complex numbers (real + imaginary parts)
3. `bool` - Boolean values (True/False, subclass of int)

**Pattern rule:** Numeric type constructors should use noun forms representing the kind of number they store. These are type names, not verbs.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `int` | entero | عدد صحيح | 整数 | पूर्णांक |
| `bool` | booleano | منطقي | 布尔 | बूलियन |
| `float` | **flotante** | **عائم** | **浮点** | **फ्लोट** |

---

## Etymology (Brief)

**English Origin:** Computing/Mathematics (20th century)

**Root meaning:** Short for "floating-point." The term comes from how the decimal point "floats" to different positions depending on the number's magnitude. Unlike fixed-point representation (decimal always at same position), floating-point allows representing both very large (3.0e100) and very small (1.5e-50) numbers.

**Why Python uses this:** "Float" is the standard computing term for IEEE 754 floating-point numbers, used universally across programming languages (C, Java, JavaScript, etc.). The term has been standard since FORTRAN in the 1950s.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `float` type represents real numbers (numbers with fractional parts) using IEEE 754 double-precision format (64 bits). This provides approximately 15-17 decimal digits of precision and can represent numbers from about 10^-308 to 10^308. Floats can also represent special values: infinity (`inf`), negative infinity (`-inf`), and not-a-number (`nan`).

Floats are created by using decimal points in numeric literals (`3.14`), scientific notation (`1.5e10`), or the `float()` constructor. Unlike integers which are exact, floats are approximations—binary fractions can't exactly represent many decimal fractions (like 0.1), leading to precision issues.

Common uses include measurements (temperature, distance), financial calculations (with caution due to precision), scientific computing, and any domain requiring decimal fractions. For exact decimal arithmetic (like money), use the `decimal` module instead.

**Key behaviors:**

1. **Approximate representation:** Floats use binary fractions internally, so many decimal numbers can't be represented exactly. `0.1 + 0.2 == 0.3` is False due to rounding errors. Always use tolerance when comparing floats: `abs(a - b) < 1e-9`.

2. **IEEE 754 standard:** Python floats follow IEEE 754 double-precision, ensuring consistent behavior across platforms. This includes rules for special values, rounding modes, and exceptional conditions.

3. **Automatic type promotion:** Operations mixing int and float produce float. `3 + 4.5` returns `7.5` (float). Division always returns float: `10 / 5` is `2.0`, not `2`. Use `//` for integer division.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (represents a numeric data type)
- **Action vs State:** STATE - describes what kind of number it is
- **Temporal aspect:** N/A - this is a type classification

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun/Adjective | "flotante" (floating) - from computing |
| Germanic (de, nl, sv) | Noun | "Gleitkomma" (floating comma) |
| Slavic (ru, pl, uk) | Adjective as noun | "плавающая" (floating) |
| Arabic | Adjective as noun | "عائم" (floating) |
| Chinese | Noun compound | "浮点" (floating point) |
| Hindi | Transliterated | "फ्लोट" (borrowed term) |

**Primary recommendation:** Most languages either:
1. Use adjective "floating" as a noun (flotante, floating)
2. Use compound "floating-point" (Gleitkommazahl, 浮点)
3. Transliterate "float" as a technical term

**Forms to AVOID:**

- ❌ Using verb "to float" (this is a noun/type name, not an action)
- ❌ Using "decimal" (all floats have decimals, but not all decimals are floats)
- ❌ Using "real" (ambiguous—mathematically different from float representation)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `flotante`
- **Form:** Adjective used as noun (masculine)
- **Why it works:** Standard Spanish computing term. Short for "número flotante" (floating-point number). Used consistently in Spanish CS education and programming documentation. Clear technical term.

**Arabic:**

- **Translation:** `عائم` (ʿāʾim)
- **Form:** Active participle/adjective (masculine)
- **Why it works:** Arabic word for "floating." Used in Arabic technical literature for floating-point numbers. Concise and clear. Conveys the concept of a number whose decimal point position varies.

**Chinese:**

- **Translation:** `浮点` (fúdiǎn) or `浮点数` (fúdiǎnshù)
- **Form:** Noun compound
- **Why it works:** 浮 (float/drift) + 点 (point). Standard Chinese term for floating-point. Used universally in Chinese computing. Can add 数 (number) for clarity: "floating-point number."

**Hindi:**

- **Translation:** `फ्लोट` (floṭ)
- **Form:** Transliterated noun
- **Why it works:** Direct transliteration of "float." Used as a borrowed technical term in Hindi CS education. No established native Hindi equivalent exists, so borrowing is appropriate for this specialized computing concept.

### ❌ Common Translation Mistakes

**Mistake 1: Using "decimal"**

- **Wrong:** `decimal` (Spanish)
- **Why wrong:** While floats display with decimals, "decimal" refers to base-10 representation, not floating-point format. Python has a separate `decimal` type for exact decimal arithmetic. "Flotante" is the specific computing term.
- **Right:** `flotante` (floating-point)

**Mistake 2: Using verb form**

- **Wrong:** `flotar` (Spanish - "to float")
- **Why wrong:** This is a verb meaning "to float/drift." Python type names are nouns/adjectives, not verbs. "Flotante" (floating) is the adjective form used as a noun.
- **Right:** `flotante` (floating, adjective/noun)

**Mistake 3: Using "real"**

- **Wrong:** `real` (Spanish - "real")
- **Why wrong:** Mathematically, "real numbers" include both rationals and irrationals, while floats are a specific computational approximation. Some languages use "real" for floats, but "flotante" is more precise.
- **Right:** `flotante` (specifically floating-point)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "To float on water" (verb: stay on surface)
- ❌ Meaning 2: "A parade float" (noun: decorated vehicle)
- ❌ Meaning 3: "To float an idea" (verb: propose tentatively)
- ✅ Meaning 4: **FLOATING-POINT NUMBER** (computing: decimal number format)

**Example:**

English "float" can mean:

1. "The boat floats on the lake" (verb: stays on surface) ❌
2. "We saw colorful floats in the parade" (decorated vehicle) ❌
3. "Let me float this proposal" (propose tentatively) ❌
4. "`3.14` is a float in Python" ✅ **This is the Python meaning**

**Your translation should capture meaning #4: floating-point number—a computational representation of decimal/real numbers using IEEE 754 format.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `float`, check these translations:**

- [ ] `int` - Related numeric type; should use compatible noun form
- [ ] `complex` - Related numeric type; should use noun form
- [ ] `bool` - Related basic type; should use noun form
- [ ] `str` - Related basic type; should use noun form

**Consistency rule:**

All basic type constructors (`int`, `float`, `complex`, `bool`, `str`) must be nouns or adjectives used as nouns. They name types, not actions.

**Example:**

Spanish: `entero`, `flotante`, `complejo`, `booleano`, `cadena` - all nouns ✅
NOT: `flotante` (noun) + `crear_entero` (verb phrase) ❌

### Functional relationships

**This term works WITH:**

1. **Type conversion**: Converting between numeric types
```python
x = float(42)      # int to float: 42.0
y = int(3.7)       # float to int: 3 (truncates)
z = float("3.14")  # string to float
```

2. **Mathematical operations**: Automatic type promotion
```python
result = 5 + 2.5   # int + float = float (7.5)
ratio = 7 / 2      # Always returns float (3.5)
```

**Common pairing:**

```python
# Creating floats
price = 19.99
pi = 3.14159
temperature = -40.0

# Type conversion
age_float = float(25)        # 25.0
text = "3.14"
number = float(text)         # 3.14

# Scientific notation
big = 1.5e10     # 15000000000.0
small = 2.3e-5   # 0.000023

# Special values
infinity = float('inf')
not_a_num = float('nan')

# Precision issues (important!)
a = 0.1 + 0.2
b = 0.3
print(a == b)    # False!
print(abs(a - b) < 1e-9)  # True (correct comparison)

# Float operations
import math
math.floor(3.7)   # 3
math.ceil(3.2)    # 4
round(3.567, 2)   # 3.57

# Checking float properties
x = 3.14
x.is_integer()    # False
y = 5.0
y.is_integer()    # True
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Universal computing term
- Standardized across programming languages
- Most languages have adopted "float" or direct translation
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Float" (floating-point) is a standard computing term used globally across all programming languages and technical documentation. Most languages either transliterate "float," use "floating" in their language, or use "floating-point" compound. The concept is taught consistently in computer science education worldwide.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FLOATING-POINT NUMBER concept (not just decimal)?
- [ ] Would a native speaker recognize this as a computing data type?
- [ ] Distinguishes from integer and other numeric types?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/adjective for type name)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other numeric types (`int`, `complex`)?
- [ ] Uses noun form like other type constructors?
- [ ] Aligns with CS education terminology in target language?

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
term: float
language: es
translation: flotante
form: adjective/noun (masculine)
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "flotante" is the standard computing term for floating-point numbers, used consistently across Spanish programming documentation and CS education. It's an adjective ("floating") used as a noun, clearly conveying the concept of a number whose decimal point position varies. The term is immediately recognizable to Spanish-speaking programmers.

**Alternatives considered:**

1. `float` (English loan) - Some Spanish programmers use English, but "flotante" is standard
2. `decimal` (decimal) - Too generic; doesn't specify floating-point format
3. `real` (real) - Mathematical term but "flotante" is more precise for computing

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Flotante" is the established term in Spanish computing and consistently used across educational materials and technical documentation.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
