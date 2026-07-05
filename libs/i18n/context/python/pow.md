# Python Builtin Function: `pow` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (mathematical function)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `pow` function in Python raises a number to a power (exponentiation). `pow(x, y)` returns x raised to the power y (x**y). Optionally accepts a third argument for modular exponentiation: `pow(x, y, z)` returns (x**y) % z efficiently.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic exponentiation
result = pow(2, 3)
print(result)  # Output: 8 (2³ = 2 × 2 × 2)

# Square a number
squared = pow(5, 2)
print(squared)  # Output: 25 (5²)
```

**What this does:** `pow(x, y)` computes x raised to the power y. Equivalent to `x ** y` operator but as a function. Returns the result of exponentiation.

### Example 2: Common Pattern

```python
# Negative exponents (reciprocal)
result = pow(2, -3)
print(result)  # Output: 0.125 (2⁻³ = 1/8)

# Fractional exponents (roots)
result = pow(9, 0.5)
print(result)  # Output: 3.0 (√9)

# Larger calculations
result = pow(10, 6)
print(result)  # Output: 1000000 (10⁶)
```

**What this does:** Negative exponents compute reciprocals. Fractional exponents compute roots (0.5 = square root, 1/3 = cube root). Works with int and float.

### Example 3: Edge Case

```python
# Modular exponentiation (three arguments)
result = pow(2, 10, 1000)
print(result)  # Output: 24 (2¹⁰ mod 1000 = 1024 mod 1000)

# Special cases
print(pow(0, 0))    # Output: 1 (by convention)
print(pow(5, 0))    # Output: 1 (anything⁰ = 1)
print(pow(2, 100))  # Large number (Python handles big ints)

# Float vs int return type
print(pow(2, 3))    # Output: 8 (int)
print(pow(2.0, 3))  # Output: 8.0 (float)
print(pow(2, -1))   # Output: 0.5 (float for negative exponent)
```

**What this shows:** Three-argument form `pow(x, y, z)` computes `(x**y) % z` efficiently (important in cryptography). Type of result depends on inputs and exponent sign. Python handles arbitrarily large integer powers.

---

## Pattern Classification

**This term is:** MATHEMATICAL OPERATION FUNCTION

**Similar terms in this pattern:**

1. `abs` - Mathematical transformation (absolute value)
2. `round` - Mathematical transformation (rounding)
3. `divmod` - Mathematical operation (division with remainder)
4. `**` operator - Exponentiation operator (same operation)

**Pattern rule:** Mathematical operation functions should use noun forms naming the operation or result. "Power" is the mathematical term for exponentiation.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "potentia" meaning "power, ability, strength." From "potens" (powerful). In mathematics, "power" refers to repeated multiplication - raising a number to a power. The exponent shows how many times to multiply the base by itself.

**Why Python uses this:** "Pow" abbreviates "power," the universal mathematical term for exponentiation (x^y or xʸ). Like "abs" and "max," Python uses concise abbreviations of standard mathematical operations. The function provides exponentiation with optional modulo.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `pow()` function performs exponentiation - raising a base to an exponent. For `pow(x, y)`, it computes x multiplied by itself y times. The result is x^y (x to the power y). This is equivalent to the `**` operator: `pow(2, 3)` equals `2 ** 3`.

The three-argument form `pow(x, y, z)` computes `(x**y) % z` but more efficiently than computing x**y first then taking modulo. This is crucial for cryptographic algorithms where you need (base^exponent) mod modulus with very large numbers. Python implements this using fast modular exponentiation (binary exponentiation).

Type handling: If both x and y are integers and y is non-negative, returns int. If either is float or y is negative, returns float. For negative exponents, computes the reciprocal: `pow(x, -y)` = 1 / pow(x, y).

**Key behaviors:**

1. **Exponent determines type:** Positive integer exponent with integer base → int result. Negative exponent or float inputs → float result. `pow(2, 3)` = 8 (int), `pow(2, -3)` = 0.125 (float).

2. **Modular exponentiation:** Three-argument form `pow(x, y, z)` efficiently computes `(x**y) % z`. Uses fast algorithm avoiding intermediate huge numbers. All three arguments must be integers; y must be non-negative when z is provided.

3. **Special cases:** `pow(0, 0)` returns 1 (mathematical convention, though sometimes defined as undefined). `pow(x, 0)` = 1 for any x. `pow(0, negative)` raises ZeroDivisionError (division by zero). Supports arbitrarily large integer exponents in Python.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (mathematical operation/result)
- **Action vs State:** RESULT - the power/exponentiation result
- **Temporal aspect:** Computed result

### Recommended Form

**Primary recommendation:** Use noun form meaning "power" or "exponent." This names the mathematical operation of exponentiation.

**Forms to AVOID:**

- ❌ Using verb "to raise" - function names result, not action
- ❌ Using only "exponent" - that's the y in x^y, not the operation
- ❌ Using "multiplication" - power is repeated multiplication, distinct operation

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Power" meaning authority/control
- ❌ Meaning 2: "Power" meaning energy/electricity
- ✅ Meaning 3: **MATHEMATICAL POWER** - exponentiation (x^y)
- ❌ Meaning 4: "Power" meaning capability/strength

**Example:**

English "power" can mean:

1. "Political power" (authority) ❌
2. "Electrical power" (energy/watts) ❌
3. "`pow(2, 3)` returns 8" (mathematical exponentiation, 2³) ✅ **This is the Python meaning**
4. "Physical power" (strength) ❌

**Your translation should capture meaning #3: the mathematical operation of exponentiation - raising a base to an exponent.**

Mathematically written as x^y, xʸ, or x**y.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `pow`, check these translations:**

- [ ] `**` operator - Exponentiation operator (same operation)
- [ ] `abs` - Mathematical transformation function
- [ ] `round` - Mathematical transformation function
- [ ] `sqrt` (in math module) - Related (square root is inverse)

**Consistency rule:**

Mathematical operation functions should use noun forms naming the operation or result. `pow`, `abs`, etc. should all use compatible naming patterns.


### Functional relationships

**This term works WITH:**

1. **`pow` for basic exponentiation**: Raise to power

```python
pow(2, 8)  # 256 (2⁸)
pow(5, 3)  # 125 (5³)
```

2. **`pow` with modulo**: Cryptographic operations

```python
pow(base, exp, mod)  # (base^exp) % mod
```

**Common pairing:**

```python
# Basic exponentiation
print(pow(2, 3))   # 8 (2³)
print(pow(10, 4))  # 10000 (10⁴)
print(pow(5, 0))   # 1 (anything⁰ = 1)

# Negative exponents
print(pow(2, -3))  # 0.125 (2⁻³ = 1/8)
print(pow(10, -2)) # 0.01 (10⁻² = 1/100)

# Fractional exponents (roots)
print(pow(9, 0.5))    # 3.0 (√9)
print(pow(27, 1/3))   # 3.0 (∛27)
print(pow(16, 0.25))  # 2.0 (⁴√16)

# Modular exponentiation (3 arguments)
print(pow(2, 10, 1000))    # 24 ((2¹⁰) mod 1000)
print(pow(3, 100, 7))      # 4 ((3¹⁰⁰) mod 7)

# Large numbers (Python handles big ints)
print(pow(2, 100))  # 1267650600228229401496703205376

# Equivalent to ** operator
print(pow(2, 5))   # 32
print(2 ** 5)      # 32 (same result)

# Scientific calculations
distance = pow(10, 9)  # 1 billion (10⁹)

# Compound interest
principal = 1000
rate = 1.05
years = 10
amount = principal * pow(rate, years)  # 1628.89

# Square numbers
squares = [pow(x, 2) for x in range(1, 6)]  # [1, 4, 9, 16, 25]

# Cryptography (modular exponentiation)
# RSA example: c = m^e mod n
message = 42
public_exponent = 65537
modulus = 3233
ciphertext = pow(message, public_exponent, modulus)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `pow`

- Universal mathematical concept (exponentiation)
- "Power" is standard term in mathematics globally
- Taught in elementary/middle school mathematics
- Well-established terminology

**For this term:** EASY

**Rationale:** Exponentiation (raising to a power) is a fundamental mathematical operation taught globally. Every language has a standard term for "power" or "exponentiation." Translation is straightforward: use the mathematical term for power/exponent.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Distinguish mathematical "power" from other meanings (electricity, authority, strength). Mathematical context makes the meaning clear.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MATHEMATICAL POWER/EXPONENTIATION concept?
- [ ] Understood as x^y operation?
- [ ] Distinguished from other meanings of "power"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of mathematical functions?
- [ ] Uses mathematical terminology?
- [ ] Compatible with `**` operator meaning?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard math term)?

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
term: pow
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
