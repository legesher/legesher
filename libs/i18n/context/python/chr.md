# Python Builtin Function: `chr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (conversion function)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `chr` function in Python converts a Unicode code point (integer) to its corresponding character (string). It's the inverse of `ord()`. Takes an integer in range 0-1,114,111 (valid Unicode range) and returns a single-character string.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Convert code point to character
char = chr(65)
print(char)  # Output: 'A' (Unicode U+0041)

# Lowercase letter
char = chr(97)
print(char)  # Output: 'a' (Unicode U+0061)
```

**What this does:** `chr()` takes an integer code point and returns the Unicode character. 65 is the code point for 'A', 97 is 'a'. Returns a single-character string.

### Example 2: Common Pattern

```python
# Special characters
print(chr(64))   # '@'
print(chr(36))   # '$'
print(chr(169))  # '©' (copyright symbol)

# Generate alphabet
alphabet = [chr(i) for i in range(65, 91)]
print(alphabet)  # ['A', 'B', 'C', ..., 'Z']

# Emoji and extended Unicode
print(chr(128512))  # '😀' (grinning face emoji)
print(chr(0x1F600)) # '😀' (same, using hex literal)
```

**What this does:** Works with any valid Unicode code point including symbols, accented letters, emoji. Can use decimal or hex notation for code points. Useful for generating character sequences.

### Example 3: Edge Case

```python
# First printable ASCII
print(chr(32))   # ' ' (space)

# Newline and special whitespace
print(repr(chr(10)))  # '\n' (newline)
print(repr(chr(9)))   # '\t' (tab)

# Unicode boundaries
print(chr(0))        # '\x00' (null character)
# chr(1114112)       # ValueError: exceeds valid Unicode range
# chr(-1)            # ValueError: negative not allowed

# Chinese character
print(chr(20013))    # '中' (Chinese character for "middle")
```

**What this shows:** Handles control characters (newline, tab, null). Valid range is 0 to 0x10FFFF (1,114,111). Values outside this range raise ValueError. Works with all Unicode planes including CJK, emoji, symbols.

---

## Pattern Classification

**This term is:** CONVERSION FUNCTION (Code Point to Character)

**Similar terms in this pattern:**

1. `ord` - Inverse operation (character to code point)
2. `int` - Conversion to integer
3. `str` - Conversion to string
4. `bin`, `hex`, `oct` - Number format conversions

**Pattern rule:** Conversion functions should use abbreviated or noun forms naming the target type or operation. "Chr" abbreviates "character."

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `ord` | ordinal | ترتيبي | 序数 | क्रमिक |
| `str` | cadena | سلسلة | 字符串 | स्ट्रिंग |
| `chr` | **carácter** | **حرف** | **字符** | **वर्ण** |

---

## Etymology (Brief)

**English Origin:** Greek via Latin

**Root meaning:** "Chr" abbreviates "character," from Greek "kharaktēr" (engraved mark, distinctive mark). From "kharassein" (to engrave, scratch). In computing, "character" means a single letter, digit, or symbol encoded as a number (code point).

**Why Python uses this:** "Chr" is a concise abbreviation for "character," following Python's pattern of short builtin names (len, int, str). The function converts code point numbers to characters, making the name descriptive. Pairs logically with `ord` (ordinal) which does the reverse.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `chr()` function converts a Unicode code point (integer) to its corresponding character (string). It's the inverse of `ord()`: if `ord(char)` returns code point n, then `chr(n)` returns that character. Takes one argument: an integer in the valid Unicode range (0 to 0x10FFFF or 1,114,111).

Unicode assigns a unique number (code point) to every character across all writing systems, symbols, and emoji. For example, 'A' is U+0041 (65 in decimal), 'é' is U+00E9 (233), and '😀' is U+1F600 (128512). The `chr()` function provides the mapping from these numbers to actual character strings.

Python 3 uses Unicode strings natively, so `chr()` works with the full Unicode range. The function returns a string of length 1 containing the character. For code points outside the valid range, raises ValueError. This is essential for text processing, generating characters programmatically, and encoding/decoding operations.

**Key behaviors:**

1. **Unicode range:** Accepts integers from 0 to 1,114,111 (0x10FFFF). This covers all defined and undefined Unicode code points across 17 planes (Basic Multilingual Plane + supplementary planes). Values outside this range raise ValueError.

2. **Returns string:** Always returns a string (str) of length 1, never a character type (Python has no char type). For surrogate pairs or multi-byte characters, still returns string of length 1 (one Unicode code point).

3. **Inverse of ord:** `chr(ord(c)) == c` for any single character c. `ord(chr(n)) == n` for any valid code point n. These functions are perfect inverses within the valid Unicode range.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (abbreviated from "character")
- **Action vs State:** CONVERSION - transforms number to character
- **Temporal aspect:** Instantaneous conversion

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "carácter", "caractère" - character |
| Germanic (de, nl, sv) | Noun | "Zeichen", "karakter" - character |
| Slavic (ru, pl, uk) | Noun | "символ", "znak" - character/symbol |
| Arabic | Noun | "حرف" - letter/character |
| Chinese | Noun | "字符" - character |
| Hindi | Noun | "वर्ण", "अक्षर" - character/letter |

**Primary recommendation:** Use noun form meaning "character." Could abbreviate if target language has common abbreviation for character.

**Forms to AVOID:**

- ❌ Using "letter" - too narrow; characters include symbols, digits, emoji
- ❌ Using verb "to characterize" - wrong concept
- ❌ Using "symbol" when "character" is more standard in computing

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `carácter` or `car`
- **Form:** Noun
- **Why it works:** "Carácter" means character in computing context. Could abbreviate to "car" following Python's "chr" abbreviation pattern. Natural in "convertir a carácter" (convert to character). Standard in Spanish CS terminology.

**Arabic:**

- **Translation:** `حرف` (ḥarf)
- **Form:** Noun
- **Why it works:** Standard Arabic word for letter/character. Used in computing and typography. Short, clear. While it can mean "letter," context makes computing sense clear. Standard in Arabic CS education.

**Chinese:**

- **Translation:** `字符` (zìfú)
- **Form:** Noun compound
- **Why it works:** Two characters: 字 (character/word) + 符 (mark/symbol). Standard Chinese computing term for character. Universally recognized in Chinese programming contexts.

**Hindi:**

- **Translation:** `वर्ण` (varṇ) or `अक्षर` (akṣar)
- **Form:** Noun
- **Why it works:** `वर्ण` means letter/character (Sanskrit term). `अक्षर` also means letter/character. Both used in Hindi computing. `वर्ण` more technical/formal, commonly used in CS education.

### ❌ Common Translation Mistakes

**Mistake 1: Using "letra" (letter) when "carácter" is more accurate**

- **Wrong:** `letra` (Spanish - "letter")
- **Why wrong:** "Letra" specifically means alphabetic letter. `chr()` converts to any character including digits ('0'-'9'), symbols ('@', '$'), punctuation, emoji, etc. "Carácter" is broader and correct.
- **Right:** `carácter` (character - includes all types)

**Mistake 2: Using verb "caracterizar" (to characterize)**

- **Wrong:** `caracterizar` (Spanish - "to characterize/describe")
- **Why wrong:** "Caracterizar" means to describe or give characteristics to something. Different concept from computing "character." Need noun for the data type.
- **Right:** `carácter` (character - the data type)

**Mistake 3: Using "símbolo" (symbol) when "carácter" is standard**

- **Wrong:** `símbolo` (Spanish - "symbol")
- **Why wrong:** While characters can be symbols, "carácter" is the technical term in computing for any encoded unit. "Símbolo" is too narrow (suggests only punctuation/special chars). "Carácter" is standard CS term.
- **Right:** `carácter` (character - standard computing term)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Character" as personality trait
- ❌ Meaning 2: "Character" as person in a story
- ✅ Meaning 3: **COMPUTING CHARACTER** - encoded letter/symbol/digit
- ❌ Meaning 4: "Character" as reputation

**Example:**

English "character" can mean:

1. "She has strong character" (personality) ❌
2. "Main character in the novel" (fictional person) ❌
3. "`chr(65)` returns 'A'" (encoded symbol in computing) ✅ **This is the Python meaning**
4. "Attack on his character" (reputation) ❌

**Your translation should capture meaning #3: a single encoded unit in text - letter, digit, symbol, emoji, etc.**

In computing: the smallest unit of text, represented by a Unicode code point.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `chr`, check these translations:**

- [ ] `ord` - Inverse function; should have compatible naming
- [ ] `str` - String type (collection of characters)
- [ ] `int` - Integer type (what chr accepts)
- [ ] Unicode terminology - character, code point concepts

**Consistency rule:**

`chr` and `ord` are inverse operations and should have linguistically related translations. If `ord` means "ordinal/order," `chr` should clearly relate to "character."

**Example:**

Spanish: `carácter` (character), `ordinal` (ordinal) - clear inverse relationship ✅
NOT: `carácter` + `número_código` (breaks the inverse pattern) ❌

### Functional relationships

**This term works WITH:**

1. **`chr` and `ord` are inverses**: Convert between representations

```python
chr(65)      # 'A'
ord('A')     # 65
chr(ord('A')) == 'A'  # True
```

2. **`chr` for character generation**: Create specific characters

```python
alphabet = [chr(i) for i in range(65, 91)]
```

**Common pairing:**

```python
# Basic conversion
print(chr(65))   # 'A'
print(chr(97))   # 'a'
print(chr(48))   # '0'

# Special characters
print(chr(32))   # ' ' (space)
print(chr(10))   # '\n' (newline)
print(chr(9))    # '\t' (tab)

# Symbols
print(chr(64))   # '@'
print(chr(36))   # '$'
print(chr(169))  # '©'
print(chr(8364)) # '€'

# Generate alphabet
uppercase = [chr(i) for i in range(65, 91)]  # A-Z
lowercase = [chr(i) for i in range(97, 123)] # a-z
digits = [chr(i) for i in range(48, 58)]     # 0-9

# Unicode characters
print(chr(945))    # 'α' (Greek alpha)
print(chr(1575))   # 'ا' (Arabic alif)
print(chr(20013))  # '中' (Chinese)
print(chr(128512)) # '😀' (emoji)

# Inverse of ord
char = 'Z'
code = ord(char)      # 90
back = chr(code)      # 'Z'
assert char == back   # True

# Caesar cipher example
def shift_char(c, shift):
    if c.isalpha():
        base = ord('A') if c.isupper() else ord('a')
        return chr((ord(c) - base + shift) % 26 + base)
    return c

message = "HELLO"
encrypted = ''.join(shift_char(c, 3) for c in message)  # "KHOOR"

# Create string from code points
code_points = [72, 101, 108, 108, 111]
text = ''.join(chr(c) for c in code_points)  # "Hello"

# Escape sequences
print(chr(92))  # '\' (backslash)
print(chr(34))  # '"' (double quote)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity in computing context
- **AI confidence should be HIGH**

### Why EASY for `chr`

- Universal computing concept (character encoding)
- "Character" is standard term in CS globally
- All programming languages have this concept
- Clear technical meaning

**For this term:** EASY

**Rationale:** The concept of a character (encoded symbol) is universal in computer science. Every language has a word for "character" in computing contexts. Translation is straightforward: use the standard computing term for character.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Ensure you use computing sense of "character" (encoded symbol) not literary sense (story person) or psychological sense (personality trait). Computing context makes this clear.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures COMPUTING CHARACTER concept?
- [ ] Understood as code point to character conversion?
- [ ] Broad enough to include letters, digits, symbols, emoji?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Related to `ord` translation (inverse operations)?
- [ ] Compatible with `str` (string = collection of characters)?
- [ ] Uses standard computing terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard CS term)?

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
term: chr
language: es
translation: carácter
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "carácter" is the standard computing term for character (encoded symbol). Could abbreviate to "car" following Python's "chr" pattern. Universally used in Spanish CS education and programming contexts.

**Alternatives considered:**

1. `car` (abbreviation) - Valid but full word more recognizable initially
2. `letra` (letter) - Too narrow; excludes digits, symbols, emoji
3. `símbolo` (symbol) - Less standard than "carácter" in computing

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Character is a universal computing concept with clear, standard translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
