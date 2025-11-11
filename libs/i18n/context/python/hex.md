# Python Builtin: `hex` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `hex()` function converts an integer to a hexadecimal string prefixed with "0x". It returns the hexadecimal (base-16) representation of the number.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Convert integer to hexadecimal
print(hex(15))   # Output: '0xf'
print(hex(255))  # Output: '0xff'
```

**What this does:** Converts the integer to its hexadecimal representation as a string. The "0x" prefix indicates it's a hexadecimal number.

### Example 2: Common Pattern

```python
# Hexadecimal representations of different numbers
numbers = [0, 10, 16, 255, 4096]
for num in numbers:
    print(f"{num} in hex is {hex(num)}")

# Output:
# 0 in hex is 0x0
# 10 in hex is 0xa
# 16 in hex is 0x10
# 255 in hex is 0xff
# 4096 in hex is 0x1000
```

**What this does:** Shows how decimal numbers convert to hexadecimal, useful for working with colors, memory addresses, and low-level data.

### Example 3: Edge Case

```python
# Negative numbers and uppercase conversion
print(hex(-255))  # Output: '-0xff'

# Remove '0x' prefix if needed
num = 42
hex_str = hex(num)[2:]  # Slice off '0x'
print(hex_str)  # Output: '2a'

# Uppercase hex digits
print(hex(255).upper())  # Output: '0XFF'
```

**What this shows:** Negative numbers show minus sign before '0x', you can remove prefix by slicing, and use `.upper()` for uppercase hex digits.

---

## Pattern Classification

**This term is:** NUMBER BASE CONVERSION BUILTIN (function that converts numbers between bases)

**Similar terms in this pattern:**

1. `bin` - Converts integer to binary (base-2) string
2. `oct` - Converts integer to octal (base-8) string
3. `int` - Can convert from different bases back to integer

**Pattern rule:** Base conversion builtins should use short noun forms representing the target number system.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `int` | entero | عدد صحيح | 整数 | पूर्णांक |
| `bin` | bin | ثنائي | 二进制 | बाइनरी |
| `hex` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Greek via modern computing

**Root meaning:** "hex" is short for "hexadecimal" from Greek "hexa-" (six) + Latin "decem" (ten) = sixteen

**Why Python uses this:** Hexadecimal (base-16) is crucial in computing for representing bytes, memory addresses, and colors. Python uses "hex" as a concise abbreviation of "hexadecimal", following the pattern of other short function names like "bin" (binary), "oct" (octal), and "int" (integer). Hex uses digits 0-9 and letters A-F to represent values 0-15.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `hex()` function converts an integer to its hexadecimal (base-16) string representation. Hexadecimal is a number system using sixteen symbols: digits 0-9 for values 0-9, and letters A-F (or a-f) for values 10-15. Each hexadecimal digit represents exactly four binary bits, making hex a natural way to represent binary data compactly.

When you call `hex()` on an integer, Python calculates the hexadecimal digits and returns them as a string prefixed with "0x" to indicate hexadecimal format. This prefix follows Python's convention for number literals: "0x" for hex, "0b" for binary, "0o" for octal. Python uses lowercase letters (a-f) by default, but you can convert to uppercase with `.upper()`.

Hexadecimal is ubiquitous in computing: RGB colors (#FF5733), memory addresses (0x7fff5fbff710), byte values (0xFF), and Unicode code points (U+1F600). While not as intuitive as decimal for humans, hex provides a compact, standardized way to represent binary data.

**Key behaviors:**

1. **Returns string, not number:** Output is a string like '0xff', not a numeric type; this allows displaying the representation with its "0x" prefix.
2. **Prefix '0x' included:** The hex string always starts with '0x' to indicate base-16; you can slice it off with `[2:]` if needed.
3. **Lowercase by default:** Python uses lowercase a-f for hex digits; use `.upper()` method for uppercase A-F.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun/abbreviation - refers to hexadecimal number system
- **Action vs State:** State/property - describes the hexadecimal form of a number
- **Temporal aspect:** Instantaneous conversion - generates representation at call time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Abbreviation or noun | "hex" or "hexadecimal" - hex number system |
| Germanic (de, nl, sv) | Abbreviation or noun | "hex" or "hexadezimal" - hexadecimal concept |
| Slavic (ru, pl, uk) | Abbreviation or noun | "hex" or "шестнадцатеричный" - base-16 system |
| Arabic | Noun/adjective | "سداسي عشري" - hexadecimal (six-ten) system |
| Chinese | Noun phrase | "十六进制" - hexadecimal (base-16) system |
| Hindi | Noun/adjective | "हेक्साडेसिमल" or "षोडश" - hexadecimal/sixteen-based |

**Primary recommendation:** Use abbreviation "hex" if universally understood, or short noun meaning "hexadecimal"

**Forms to AVOID:**

- ❌ Verb forms ("convert to hexadecimal") - Returns a representation, not an action
- ❌ "Sixteen" alone - Too vague, doesn't indicate number system
- ❌ Long phrases like "hexadecimal representation" - Too wordy for function name

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `hex` or `hexadecimal`
- **Form:** abbreviation or noun
- **Why it works:** "hex" is universally understood in Spanish tech; "hexadecimal" clearly means base-16. Abbreviation preferred for consistency with "bin" and "oct".

**Arabic:**

- **Translation:** `سداسي_عشري` or `hex`
- **Form:** adjective/noun (sudāsī 'asharī - six-ten/hexadecimal)
- **Why it works:** سداسي عشري is standard Arabic for hexadecimal; "hex" also recognized in tech contexts

**Chinese:**

- **Translation:** `十六进制`
- **Form:** noun phrase
- **Why it works:** 十六进制 (shíliùjìnzhì) literally means "base-16 system", standard term for hexadecimal in Chinese computing

**Hindi:**

- **Translation:** `हेक्स` or `षोडश`
- **Form:** noun (transliteration or Sanskrit)
- **Why it works:** हेक्स (heks) is widely understood transliteration; षोडश (ṣoḍaśa) means sixteen in Sanskrit, formal term

### ❌ Common Translation Mistakes

**Mistake 1: Using verb form**

- **Wrong:** `convertir_hexadecimal` (Spanish - "convert to hexadecimal")
- **Why wrong:** Function name should be noun/abbreviation, not action phrase; too wordy
- **Right:** `hex` or `hexadecimal`

**Mistake 2: Using "sixteen" alone**

- **Wrong:** `dieciséis` (Spanish - "sixteen")
- **Why wrong:** Doesn't indicate this is about number system/base-16 representation
- **Right:** `hexadecimal` (hexadecimal system)

**Mistake 3: Mixing with "six" terminology**

- **Wrong:** `seis` (Spanish - "six")
- **Why wrong:** While "hexa" means six, hexadecimal is sixteen (6+10), not just six
- **Right:** `hexadecimal` (base-16 system)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A curse or spell ("put a hex on someone")
- ✅ Meaning 2: Short for "hexadecimal" - base-16 number system **This is the Python meaning**
- ❌ Meaning 3: Six-sided (hexagonal shape)

**Example:**

English "hex" can mean:

1. Curse or evil spell ❌
2. Abbreviation for "hexadecimal" (base-16) ✅ **This is the Python meaning**
3. Related to six or hexagon ❌

**Your translation should capture meaning #2 (hexadecimal number system), NOT the other meanings.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `hex`, check these translations:**

- [ ] `bin` - Parallel function for binary, should use same pattern
- [ ] `oct` - Parallel function for octal, should use same pattern
- [ ] `int` - Related base type, should use compatible noun form
- [ ] `format` - Can format numbers in different bases, related concept

**Consistency rule:**

All base conversion functions (bin, hex, oct) should use the same linguistic pattern - either all abbreviations or all short nouns. They form a family of related functions that convert integers to different base representations.

**Example:**

If you translate `hex` as abbreviation (keep "hex"), then:

- `bin` should also be abbreviation (keep "bin")
- `oct` should also be abbreviation (keep "oct")
- NOT: `hex` abbreviation + `bin` full word "binario" (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`hex` + `int`**: Convert to hexadecimal and back
2. **`bin` + `hex` + `oct`**: Family of base conversion functions

**Common pairing:**

```python
# Converting between bases
num = 42
print(bin(num))  # 0b101010 (binary)
print(hex(num))  # 0x2a (hexadecimal)
print(oct(num))  # 0o52 (octal)

# Converting back to integer
hex_str = '0x2a'
num = int(hex_str, 16)  # Convert hex string to int

# RGB colors in hex
red = 255
green = 87
blue = 51
color = f"#{hex(red)[2:]:0>2}{hex(green)[2:]:0>2}{hex(blue)[2:]:0>2}"
print(color)  # #ff5733

# Memory addresses often shown in hex
obj = [1, 2, 3]
print(f"Object at {hex(id(obj))}")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- "Hexadecimal" is universal in computing
- Minimal ambiguity
- **AI confidence should be HIGH**

**For this term:** EASY

**Rationale:** Hexadecimal (base-16) is a fundamental computing concept that exists in all programming languages and computer science education worldwide. Most languages either keep "hexadecimal" as a loanword or have a clear native equivalent. The abbreviation "hex" is widely recognized in tech contexts.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the "hexadecimal/base-16" concept?
- [ ] Would a programmer understand this converts to hex representation?
- [ ] Avoids confusion with "hex" as curse or hexagon?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/abbreviation, not verb)?
- [ ] Natural abbreviation or short form?
- [ ] Follows target language grammar rules?
- [ ] Uses lowercase (Python convention for builtins)?

### 3. Consistency

- [ ] Matches pattern of `bin` and `oct` (parallel base conversion functions)?
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
term: hex
language: {es|ar|zh|hi}
translation: {your_translation}
form: {abbreviation|noun}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Why you chose this translation. Address: concept accuracy (hexadecimal base-16 system), linguistic form (abbreviation/noun), consistency with bin/oct pattern, whether "hex" is universally understood or needs translation}

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
