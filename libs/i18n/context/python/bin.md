# Python Builtin: `bin` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `bin()` function converts an integer to a binary string prefixed with "0b". It returns the binary (base-2) representation of the number.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Convert integer to binary
print(bin(5))   # Output: '0b101'
print(bin(10))  # Output: '0b1010'
```

**What this does:** Converts the integer to its binary representation as a string. The "0b" prefix indicates it's a binary number.

### Example 2: Common Pattern

```python
# Binary representations of different numbers
numbers = [0, 1, 2, 8, 15, 255]
for num in numbers:
    print(f"{num} in binary is {bin(num)}")

# Output:
# 0 in binary is 0b0
# 1 in binary is 0b1
# 2 in binary is 0b10
# 8 in binary is 0b1000
# 15 in binary is 0b1111
# 255 in binary is 0b11111111
```

**What this does:** Shows how different decimal numbers convert to binary representation, useful for understanding bitwise operations.

### Example 3: Edge Case

```python
# Negative numbers use two's complement representation
print(bin(-5))   # Output: '-0b101'

# Remove '0b' prefix if needed
num = 42
binary = bin(num)[2:]  # Slice off '0b'
print(binary)  # Output: '101010'
```

**What this shows:** Negative numbers show minus sign before '0b', and you can remove the prefix by slicing the string.

---

## Pattern Classification

**This term is:** NUMBER BASE CONVERSION BUILTIN (function that converts numbers between bases)

**Similar terms in this pattern:**

1. `hex` - Converts integer to hexadecimal (base-16) string
2. `oct` - Converts integer to octal (base-8) string
3. `int` - Can convert from different bases back to integer

**Pattern rule:** Base conversion builtins should use short noun forms representing the target number system.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `int` | entero | عدد صحيح | 整数 | पूर्णांक |
| `hex` | hex | سداسي عشري | 十六进制 | हेक्स |
| `bin` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Latin via modern computing

**Root meaning:** "bin" is short for "binary" from Latin "binarius" meaning "consisting of two" (bi- = two)

**Why Python uses this:** Binary (base-2) is fundamental to computing since computers store everything as 1s and 0s. Python uses "bin" as a concise abbreviation of "binary", following the pattern of other short function names like "int" (integer), "hex" (hexadecimal), and "oct" (octal).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `bin()` function converts an integer to its binary (base-2) string representation. Binary is the number system using only digits 0 and 1, which corresponds to how computers store and process data at the hardware level. Each position in a binary number represents a power of 2, just as decimal positions represent powers of 10.

When you call `bin()` on an integer, Python calculates the binary digits and returns them as a string prefixed with "0b" to indicate binary format. This prefix follows Python's convention: "0b" for binary, "0x" for hexadecimal, "0o" for octal. The prefix makes it clear what base the number uses.

Binary representations are essential for understanding bitwise operations, working with binary data, networking protocols, and low-level programming. While computers work exclusively in binary, Python lets you work primarily in decimal and convert when needed using functions like `bin()`.

**Key behaviors:**

1. **Returns string, not number:** Output is a string like '0b101', not a numeric type; this allows displaying the representation with its "0b" prefix.
2. **Prefix '0b' included:** The binary string always starts with '0b' to indicate base-2; you can slice it off with `[2:]` if needed.
3. **Works with negative numbers:** Negative integers show a minus sign before the prefix, like '-0b101' for -5.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun/abbreviation - refers to binary number system
- **Action vs State:** State/property - describes the binary form of a number
- **Temporal aspect:** Instantaneous conversion - generates representation at call time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Abbreviation or noun | "bin" or "binario" - binary number system |
| Germanic (de, nl, sv) | Abbreviation or noun | "bin" or "binär" - binary concept |
| Slavic (ru, pl, uk) | Abbreviation or noun | "bin" or "двоичный" - binary system |
| Arabic | Noun/adjective | "ثنائي" - binary/dual system |
| Chinese | Noun phrase | "二进制" - binary (base-2) system |
| Hindi | Noun/adjective | "द्विआधारी" or "बाइनरी" - binary system |

**Primary recommendation:** Use abbreviation "bin" if universally understood, or short noun meaning "binary"

**Forms to AVOID:**

- ❌ Verb forms ("convert to binary") - Returns a representation, not an action
- ❌ "Two" alone - Too vague, doesn't indicate number system
- ❌ Long phrases like "binary representation" - Too wordy for function name

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `bin` or `binario`
- **Form:** abbreviation or adjective/noun
- **Why it works:** "bin" is universally understood in Spanish tech; "binario" clearly means binary. Abbreviation preferred for consistency with "hex" and "oct".

**Arabic:**

- **Translation:** `ثنائي`
- **Form:** adjective/noun (thunā'ī - binary)
- **Why it works:** Standard Arabic term for binary system, clear and concise, matches technical vocabulary

**Chinese:**

- **Translation:** `二进制`
- **Form:** noun phrase
- **Why it works:** 二进制 (èrjìnzhì) literally means "base-2 system", standard term for binary in Chinese computing

**Hindi:**

- **Translation:** `बाइनरी` or `द्विआधारी`
- **Form:** noun (transliteration or Sanskrit-derived)
- **Why it works:** बाइनरी (bāinarī) is widely understood transliteration; द्विआधारी (dviyādhārī) is formal Sanskrit term for binary

### ❌ Common Translation Mistakes

**Mistake 1: Using verb form**

- **Wrong:** `convertir_binario` (Spanish - "convert to binary")
- **Why wrong:** Function name should be noun/abbreviation, not action phrase; too wordy
- **Right:** `bin` or `binario`

**Mistake 2: Using "two" alone**

- **Wrong:** `dos` (Spanish - "two")
- **Why wrong:** Doesn't indicate this is about number system/base-2 representation
- **Right:** `binario` (binary system)

**Mistake 3: Too technical/verbose**

- **Wrong:** `representación_binaria` (Spanish - "binary representation")
- **Why wrong:** Too long for builtin function name; loses the conciseness of "bin"
- **Right:** `bin` or `binario`

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Container/receptacle for storage ("trash bin", "storage bin")
- ✅ Meaning 2: Short for "binary" - base-2 number system **This is the Python meaning**
- ❌ Meaning 3: Osama bin Laden (part of Arabic name structure)

**Example:**

English "bin" can mean:

1. Container for storage ❌
2. Abbreviation for "binary" (base-2) ✅ **This is the Python meaning**
3. Part of name structure ❌

**Your translation should capture meaning #2 (binary number system), NOT the other meanings.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `bin`, check these translations:**

- [ ] `hex` - Parallel function for hexadecimal, should use same pattern
- [ ] `oct` - Parallel function for octal, should use same pattern
- [ ] `int` - Related base type, should use compatible noun form
- [ ] `format` - Can format numbers in different bases, related concept

**Consistency rule:**

All base conversion functions (bin, hex, oct) should use the same linguistic pattern - either all abbreviations or all short nouns. They form a family of related functions that convert integers to different base representations.

**Example:**

If you translate `bin` as abbreviation (keep "bin"), then:

- `hex` should also be abbreviation (keep "hex")
- `oct` should also be abbreviation (keep "oct")
- NOT: `bin` abbreviation + `hex` full word "hexadecimal" (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`bin` + `int`**: Convert to binary and back
2. **`bin` + `hex` + `oct`**: Family of base conversion functions

**Common pairing:**

```python
# Converting between bases
num = 42
print(bin(num))  # 0b101010 (binary)
print(hex(num))  # 0x2a (hexadecimal)
print(oct(num))  # 0o52 (octal)

# Converting back to integer
binary_str = '0b101010'
num = int(binary_str, 2)  # Convert binary string to int

# Bitwise operations with binary
a = 0b1010  # 10 in decimal
b = 0b1100  # 12 in decimal
print(bin(a & b))  # 0b1000 (bitwise AND)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- "Binary" is universal in computing
- Minimal ambiguity
- **AI confidence should be HIGH**

**For this term:** EASY

**Rationale:** Binary (base-2) is a fundamental computing concept that exists in all programming languages and computer science education worldwide. Most languages either keep "binary" as a loanword or have a clear native equivalent. The abbreviation "bin" is widely recognized.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the "binary/base-2" concept?
- [ ] Would a programmer understand this converts to binary representation?
- [ ] Avoids confusion with "bin" as container?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/abbreviation, not verb)?
- [ ] Natural abbreviation or short form?
- [ ] Follows target language grammar rules?
- [ ] Uses lowercase (Python convention for builtins)?

### 3. Consistency

- [ ] Matches pattern of `hex` and `oct` (parallel base conversion functions)?
- [ ] Uses same form (abbreviation/noun) as related functions?
- [ ] Aligns with `int` as the base type?

### 4. Usability

- [ ] Short (1-2 words, ideally 3-4 characters)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

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
term: bin
language: {es|ar|zh|hi}
translation: {your_translation}
form: {abbreviation|noun}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Why you chose this translation. Address: concept accuracy (binary base-2 system), linguistic form (abbreviation/noun), consistency with hex/oct pattern, whether "bin" is universally understood or needs translation}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{What concerns you have, what needs human verification}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
