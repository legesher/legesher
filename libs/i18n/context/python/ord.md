# Python Builtin Function: `ord` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (conversion function)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `ord` function in Python converts a single character (string of length 1) to its Unicode code point (integer). It's the inverse of `chr()`. Takes a single-character string and returns an integer representing that character's position in Unicode.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get code point of a character
code = ord('A')
print(code)  # Output: 65 (Unicode U+0041)

# Lowercase letter
code = ord('a')
print(code)  # Output: 97 (Unicode U+0061)
```

**What this does:** `ord()` takes a single character and returns its Unicode code point as an integer. 'A' is at position 65, 'a' is at 97 in Unicode.

### Example 2: Common Pattern

```python
# Special characters
print(ord('@'))  # 64
print(ord('$'))  # 36
print(ord('©'))  # 169 (copyright symbol)

# Check if uppercase
char = 'Z'
if 65 <= ord(char) <= 90:
    print(f"{char} is uppercase")

# Character arithmetic
char = 'C'
next_char = chr(ord(char) + 1)
print(next_char)  # 'D'
```

**What this does:** Works with any Unicode character. Useful for comparisons, sorting, and character arithmetic. Can manipulate characters by working with their numeric values.

### Example 3: Edge Case

```python
# Emoji and extended Unicode
print(ord('😀'))  # 128512 (U+1F600)

# Chinese character
print(ord('中'))  # 20013

# Must be single character
# ord('AB')  # TypeError: expected a character, but string of length 2 found
# ord('')    # TypeError: expected a character, but string of length 0 found

# Inverse of chr
char = '€'
code = ord(char)      # 8364
back = chr(code)      # '€'
assert char == back   # True
```

**What this shows:** Works with any single Unicode character including emoji, CJK characters, symbols. Requires exactly one character - empty strings or multi-character strings raise TypeError. Perfect inverse of `chr()`.

---

## Pattern Classification

**This term is:** CONVERSION FUNCTION (Character to Code Point)

**Similar terms in this pattern:**

1. `chr` - Inverse operation (code point to character)
2. `int` - Conversion to integer
3. `str` - Conversion to string
4. `bin`, `hex`, `oct` - Number format conversions

**Pattern rule:** Conversion functions should use abbreviated or noun forms naming the source or operation. "Ord" abbreviates "ordinal" (position in sequence).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `chr` | carácter | حرف | 字符 | वर्ण |
| `int` | entero | عدد_صحيح | 整数 | पूर्णांक |
| `ord` | **ordinal** | **ترتيبي** | **序数** | **क्रमिक** |

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** "Ord" abbreviates "ordinal," from Latin "ordinalis" (relating to order in a series). From "ordo" (row, series, order). In computing, "ordinal value" means the position/number assigned to a character in the encoding sequence.

**Why Python uses this:** "Ord" is a concise abbreviation for "ordinal," referring to the ordinal number (position) of a character in Unicode. Pairs logically with `chr` (character) - they're inverse operations. Short, memorable, follows Python's naming pattern.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `ord()` function converts a single character to its Unicode code point (integer). It's the inverse of `chr()`: if `chr(n)` returns character c, then `ord(c)` returns n. Takes one argument: a string of exactly length 1 (single character).

Every character in Unicode has a unique code point - an integer from 0 to 1,114,111 (0x10FFFF). For example, 'A' is U+0041 (65), 'é' is U+00E9 (233), '中' is U+4E2D (20013). The `ord()` function provides the mapping from characters to these numeric values.

This is essential for text processing, character comparisons, sorting, and understanding string internals. In Python 3, all strings are Unicode, so `ord()` works with any character from any language, script, or symbol set.

**Key behaviors:**

1. **Single character only:** Requires string of exactly length 1. Empty string or multi-character string raises TypeError: "ord() expected a character, but string of length X found." Use `ord(s[0])` to get code point of first character in string.

2. **Returns integer:** Always returns int in range 0 to 1,114,111 (valid Unicode range). This is the code point, not the byte representation. For 'A', returns 65 (not the byte encoding which varies by encoding scheme).

3. **Inverse of chr:** `ord(chr(n)) == n` for any valid code point n. `chr(ord(c)) == c` for any single character c. These functions form perfect inverse pair for character/code point conversion.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective/noun (abbreviated from "ordinal")
- **Action vs State:** CONVERSION - transforms character to number
- **Temporal aspect:** Instantaneous conversion

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adjective/noun | "ordinal" - relating to order |
| Germanic (de, nl, sv) | Adjective/noun | "ordinal", "Ordnungszahl" |
| Slavic (ru, pl, uk) | Adjective | "порядковый", "liczba porządkowa" |
| Arabic | Adjective | "ترتيبي" - ordinal/sequential |
| Chinese | Compound noun | "序数", "顺序" - ordinal number |
| Hindi | Adjective | "क्रमिक", "क्रमांक" - ordinal |

**Primary recommendation:** Use adjective/noun form meaning "ordinal" (relating to position/order in sequence). This captures the concept of getting the character's position number.

**Forms to AVOID:**

- ❌ Using "order" as command - confuses with sorting
- ❌ Using "number" alone - too generic
- ❌ Using "code" alone - less precise than "code point" or "ordinal"

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `ordinal` or `ord`
- **Form:** Adjective/noun
- **Why it works:** "Ordinal" means relating to order/position in sequence. Natural in "valor ordinal" (ordinal value) or "número ordinal" (ordinal number). Standard mathematical/CS term in Spanish.

**Arabic:**

- **Translation:** `ترتيبي` (tartībī)
- **Form:** Adjective (nisba form)
- **Why it works:** From root ت-ر-ت-ب (order/arrangement). Means "ordinal/sequential/positional." Used in Arabic mathematics for ordinal numbers. Clear technical meaning.

**Chinese:**

- **Translation:** `序数` (xùshù) or `序号` (xùhào)
- **Form:** Compound noun
- **Why it works:** `序数` = "ordinal number" (sequence + number). `序号` = "sequence number/serial number." Both capture position-in-sequence concept. `序数` more mathematical/formal.

**Hindi:**

- **Translation:** `क्रमिक` (kramik) or `क्रमांक` (kramāṅk)
- **Form:** Adjective/noun
- **Why it works:** `क्रमिक` means "sequential/ordinal" (from Sanskrit "krama" = sequence). `क्रमांक` means "serial number." Both capture ordinal concept. Standard in Hindi mathematics.

### ❌ Common Translation Mistakes

**Mistake 1: Using "orden" (order as command) instead of "ordinal"**

- **Wrong:** `orden` (Spanish - "order" as command/arrangement)
- **Why wrong:** "Orden" can mean command, sequence, or tidiness. "Ordinal" specifically means the position number in a sequence. More precise term needed. Computing uses "ordinal."
- **Right:** `ordinal` (ordinal number/value - technical term)

**Mistake 2: Using "número" (number) alone**

- **Wrong:** `número` (Spanish - "number")
- **Why wrong:** Too generic. `ord()` doesn't return just any number - it returns the ordinal value (position in Unicode). "Número ordinal" or just "ordinal" is more precise.
- **Right:** `ordinal` (specifically the ordinal/position number)

**Mistake 3: Using "código" (code) without "ordinal" context**

- **Wrong:** `código` (Spanish - "code")
- **Why wrong:** "Código" just means code. Could be error code, source code, etc. Need "código de punto" (code point) or better, "ordinal" which is the standard term for character position values.
- **Right:** `ordinal` (ordinal value - standard CS term)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (the full word "ordinal")

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Ordinal" as relating to clergy orders
- ✅ Meaning 2: **MATHEMATICAL ORDINAL** - position number in sequence
- ❌ Meaning 3: "Ordinal" in set theory (transfinite ordinals)

**Example:**

English "ordinal" can mean:

1. Religious context (ordinal rites) ❌
2. "`ord('A')` returns 65" (position in sequence, ordinal number) ✅ **This is the Python meaning**
3. Set theory transfinite ordinals (ω, ω+1, etc.) ❌

**Your translation should capture meaning #2: the ordinal number - the position of a character in the Unicode sequence.**

In mathematics: "ordinal number" contrasts with "cardinal number" (counting vs. ordering).

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ord`, check these translations:**

- [ ] `chr` - Inverse function; should have compatible naming
- [ ] `str` - String type (what ord accepts)
- [ ] `int` - Integer type (what ord returns)
- [ ] Unicode terminology - code point, character concepts

**Consistency rule:**

`ord` and `chr` are inverse operations and should have linguistically related translations. They form a pair for character encoding conversions.

**Example:**

Spanish: `ordinal` (ordinal value), `carácter` (character) - clear inverse ✅
Both are computing terms that work together logically.

### Functional relationships

**This term works WITH:**

1. **`ord` and `chr` are inverses**: Convert between representations

```python
ord('A')      # 65
chr(65)       # 'A'
ord(chr(65)) == 65  # True
```

2. **`ord` for comparisons**: Character ordering

```python
is_uppercase = 65 <= ord(char) <= 90
```

**Common pairing:**

```python
# Basic conversion
print(ord('A'))  # 65
print(ord('a'))  # 97
print(ord('0'))  # 48

# Special characters
print(ord(' '))  # 32 (space)
print(ord('\n')) # 10 (newline)
print(ord('\t')) # 9 (tab)

# Symbols
print(ord('@'))  # 64
print(ord('$'))  # 36
print(ord('©'))  # 169
print(ord('€'))  # 8364

# Unicode characters
print(ord('α'))  # 945 (Greek alpha)
print(ord('ا'))  # 1575 (Arabic alif)
print(ord('中')) # 20013 (Chinese)
print(ord('😀')) # 128512 (emoji)

# Character comparisons
char = 'M'
if ord('A') <= ord(char) <= ord('Z'):
    print(f"{char} is uppercase")

# Character arithmetic
letter = 'B'
next_letter = chr(ord(letter) + 1)  # 'C'
prev_letter = chr(ord(letter) - 1)  # 'A'

# Distance between characters
distance = ord('z') - ord('a')  # 25 (alphabet length - 1)

# Check character ranges
def is_digit(c):
    return ord('0') <= ord(c) <= ord('9')

def is_lowercase(c):
    return ord('a') <= ord(c) <= ord('z')

# Convert to uppercase (ASCII)
char = 'd'
uppercase = chr(ord(char) - 32)  # 'D'
# Better: use char.upper()

# Inverse of chr
codes = [72, 101, 108, 108, 111]
chars = [chr(c) for c in codes]       # ['H', 'e', 'l', 'l', 'o']
back_to_codes = [ord(c) for c in chars]  # [72, 101, 108, 108, 111]

# Caesar cipher
def caesar_shift(text, shift):
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
        else:
            result.append(char)
    return ''.join(result)

message = "HELLO"
encrypted = caesar_shift(message, 3)  # "KHOOR"

# Sort by Unicode code point
chars = ['a', 'Z', '1', '@', 'α']
sorted_chars = sorted(chars, key=ord)
# ['1', '@', 'Z', 'a', 'α']
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity in computing context
- **AI confidence should be HIGH**

### Why EASY for `ord`

- Universal computing concept (character code points)
- "Ordinal" is standard mathematical/CS term
- Clear technical meaning in programming
- Well-established across languages

**For this term:** EASY

**Rationale:** The concept of ordinal value (position number in sequence) is universal in mathematics and computer science. Every language has terminology for ordinal numbers. Translation is straightforward: use the term for "ordinal" or "ordinal number."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Ensure you use mathematical/CS sense of "ordinal" (position in sequence) not religious or set-theory senses. Programming context makes this clear.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ORDINAL VALUE concept?
- [ ] Understood as character to code point conversion?
- [ ] Related to position/sequence concepts?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective/noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Related to `chr` translation (inverse operations)?
- [ ] Compatible with `int` (returns integer)?
- [ ] Uses standard computing/mathematical terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard term)?

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
term: ord
language: es
translation: ordinal
form: adjective_as_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "ordinal" is the standard mathematical/CS term for ordinal number (position in sequence). Clearly captures the concept of getting a character's position value in Unicode. Natural pairing with "carácter" (chr function).

**Alternatives considered:**

1. `orden` (order) - Ambiguous; could mean command or tidiness
2. `número` (number) - Too generic; "ordinal" more specific
3. `código` (code) - Less standard than "ordinal" for this concept

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Ordinal is a universal mathematical concept with clear, standard translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
