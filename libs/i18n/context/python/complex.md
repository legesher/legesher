# Python Builtin Type: `complex` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun/adjective
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `complex` type in Python represents complex numbers with real and imaginary parts. Complex numbers are essential in mathematics, engineering, and scientific computing, representing numbers as `a + bj` where `j` is the imaginary unit (√-1). Python provides first-class support for complex arithmetic.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create complex number
z = complex(3, 4)  # 3 + 4j
print(z)  # Output: (3+4j)

# Using j notation directly
z2 = 3 + 4j
print(z2)  # Output: (3+4j)
```

**What this does:** `complex(real, imag)` creates a complex number with real part 3 and imaginary part 4. Python uses `j` (not `i`) for the imaginary unit, following engineering convention. Literal notation `3 + 4j` also works.

### Example 2: Common Pattern

```python
# Access real and imaginary parts
z = 3 + 4j
print(z.real)  # Output: 3.0
print(z.imag)  # Output: 4.0

# Complex arithmetic
z1 = 2 + 3j
z2 = 1 + 2j
print(z1 + z2)  # Output: (3+5j)
print(z1 * z2)  # Output: (-4+7j)

# Conjugate and absolute value
print(z1.conjugate())  # Output: (2-3j)
print(abs(z1))  # Output: 3.605551275463989 (magnitude)
```

**What this does:** Access components with `.real` and `.imag` attributes. Complex numbers support standard arithmetic operators. `.conjugate()` flips imaginary sign. `abs()` returns magnitude (distance from origin).

### Example 3: Edge Case

```python
# Convert from string
z = complex("2+3j")
print(z)  # Output: (2+3j)

# Complex with zero imaginary part
z = complex(5, 0)
print(z)  # Output: (5+0j)

# Pure imaginary number
z = complex(0, 1)
print(z)  # Output: 1j

# Division by zero
try:
    result = (3 + 4j) / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
```

**What this shows:** `complex()` can parse strings. Complex numbers always have both parts (even if zero). `0 + 1j` is the imaginary unit. Complex division by zero raises same error as real division.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Numeric Type)

**Similar terms in this pattern:**

1. `int` - Integer number type (numeric type)
2. `float` - Floating-point number type (numeric type)
3. `bool` - Boolean type (logical type)

**Pattern rule:** Type constructors should use noun forms naming the type of data. "Complex" refers to complex numbers - a fundamental mathematical concept. Can be adjective ("complex number") or noun ("a complex").


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "complexus" (past participle of "complecti"), meaning "encompassed, composed of parts." In mathematics, "complex number" means a number composed of two parts: real and imaginary components.

**Why Python uses this:** "Complex" is the universal mathematical term for numbers with real and imaginary parts. Introduced by mathematicians in the 16th-17th centuries, now standard in mathematics, engineering, and physics. Python follows mathematical convention by naming this type `complex`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `complex` type represents complex numbers as pairs of floating-point values: a real part and an imaginary part. Complex numbers extend the real number system to include solutions to equations like x² = -1. In Python, complex numbers use the form `a + bj` where `a` is the real part, `b` is the imaginary part, and `j` represents √-1.

Complex arithmetic is built into Python's operator system. Addition/subtraction combine components separately: `(a+bj) + (c+dj) = (a+c) + (b+d)j`. Multiplication follows mathematical rules: `(a+bj) * (c+dj) = (ac-bd) + (ad+bc)j`. Python handles this automatically through operator overloading.

The type is essential for scientific computing, signal processing, electrical engineering, quantum mechanics, and any domain working with oscillations, waves, or rotations. Python's `complex` type provides efficient, accurate complex arithmetic with full integration into the numeric tower (complex, float, int).

**Key behaviors:**

1. **Immutable numeric type:** Complex numbers are immutable like int and float. Operations create new complex objects. Automatic type conversion happens: `int + complex` yields complex. Part of Python's numeric tower.

2. **Uses j notation:** Python uses `j` for imaginary unit (not `i`), following electrical engineering convention. Literal notation like `3+4j` creates complex directly. Must write `4j` not `j4` (j is suffix on number).

3. **Floating-point components:** Both `.real` and `.imag` are floats, even if created from integers. This ensures precision in complex arithmetic. Cannot create integer-only complex (always promoted to float).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (name of number type)
- **Action vs State:** STATE - describes type of mathematical object
- **Temporal aspect:** Permanent - type classification

### Recommended Form

**Primary recommendation:** Use adjective or noun form meaning "complex" in mathematical sense (composed of parts), not "complicated." This is a standard mathematical term that exists in most languages' technical vocabulary.

**Forms to AVOID:**

- ❌ Using "complicated" - wrong meaning ("complex" = composed of parts, not difficult)
- ❌ Using "imaginary" alone - misses the real component
- ❌ Using "compound" - ambiguous, not standard mathematical terminology

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Complicated/difficult" (complex problem)
- ✅ Meaning 2: **COMPOSED OF REAL AND IMAGINARY PARTS** (mathematical complex number)
- ❌ Meaning 3: "Building complex" (group of buildings)

**Example:**

English "complex" can mean:

1. "This is a complex issue" (complicated) ❌
2. "`complex(3, 4)` creates 3+4j" (mathematical complex number) ✅ **This is the Python meaning**
3. "Apartment complex" (group of structures) ❌

**Your translation should capture meaning #2: numbers with real and imaginary components.**

In mathematics, "complex" specifically means "composed of multiple parts" - the real and imaginary components. Not "difficult" or "complicated."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `complex`, check these translations:**

- [ ] `int` - Basic numeric type; should have consistent pattern
- [ ] `float` - Floating-point type; should match grammatical form
- [ ] `bool` - Boolean type; should align with type naming pattern

**Consistency rule:**

Type constructors (`int`, `float`, `complex`, `bool`, `str`) should use consistent grammatical forms - all nouns or all adjectives. They're all names of data types, so linguistic parallelism helps learners understand the pattern.

**Example:**

If you translate types as nouns:

- `int` → `entero` (integer - noun)
- `float` → `flotante` (floating - noun/adjective)
- `complex` → `complejo` (complex - noun/adjective) ✅

NOT: `int` noun + `complex` verb (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`complex` + arithmetic**: Standard operations

```python
z1 = 3 + 4j
z2 = 1 + 2j
z1 + z2  # Addition
z1 * z2  # Multiplication
```

2. **`complex` + methods**: Complex number operations

```python
z = 3 + 4j
z.conjugate()  # Complex conjugate
abs(z)  # Magnitude
z.real, z.imag  # Components
```

**Common pairing:**

```python
# Creating complex numbers
z1 = complex(3, 4)  # Constructor
z2 = 3 + 4j  # Literal notation

# Accessing components
print(z1.real)  # 3.0
print(z1.imag)  # 4.0

# Arithmetic
z3 = z1 + z2  # (6+8j)
z4 = z1 * z2  # (-7+24j)

# Mathematical operations
conjugate = z1.conjugate()  # (3-4j)
magnitude = abs(z1)  # 5.0
phase = cmath.phase(z1)  # Requires cmath module

# Type conversion
z = complex(5)  # (5+0j) from int
z = complex(3.5)  # (3.5+0j) from float

# Useful in scientific computing
import cmath
# Exponential form: e^(iθ) = cos(θ) + i*sin(θ)
z = cmath.exp(1j * cmath.pi)  # ≈ -1 (Euler's identity)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY)

- Standard mathematical term with established translations
- "Complex" exists in most languages' mathematical vocabulary
- Clear distinction from "complicated"
- **AI confidence should be HIGH**

### Why LOW for `complex`

- Universal mathematical concept taught globally
- "Complex number" is standard terminology in all languages
- Cognates exist in many language families
- Well-established in educational contexts

**For this term:** LOW

**Rationale:** Complex numbers are fundamental in mathematics and engineering worldwide. Every language with mathematical education has a term for "complex number." The key is distinguishing mathematical "complex" (composed of parts) from colloquial "complex" (complicated).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Ensure translation captures mathematical meaning (real + imaginary) not colloquial meaning (complicated/difficult).

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MATHEMATICAL COMPLEX NUMBER concept?
- [ ] Understood as having real and imaginary parts?
- [ ] Distinguishes from "complicated" meaning?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun or adjective for type)?
- [ ] Matches mathematical terminology in target language?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python types)?

### 3. Consistency

- [ ] Matches pattern of `int`, `float`, other numeric types?
- [ ] Uses similar form as other type constructors?
- [ ] Aligns with mathematical education in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Recognizable as mathematical term?

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
term: complex
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
