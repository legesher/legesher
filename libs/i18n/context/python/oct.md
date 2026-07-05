# Python Builtin Function: `oct` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun/adjective
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `oct` function converts an integer to an octal string representation prefixed with "0o". Octal (base-8) uses digits 0-7, historically used in Unix file permissions and some low-level programming contexts.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Convert integer to octal
number = 64
octal_str = oct(number)
print(octal_str)  # Output: '0o100'
```

**What this does:** `oct()` converts integer 64 to octal string "0o100" (100 in octal = 64 in decimal). The "0o" prefix indicates octal notation.

### Example 2: Common Pattern

```python
# Various numbers to octal
print(oct(0))       # '0o0'
print(oct(8))       # '0o10'
print(oct(64))      # '0o100'
print(oct(511))     # '0o777'
print(oct(-10))     # '-0o12'

# Remove '0o' prefix if needed
number = 42
octal_digits = oct(number)[2:]  # Remove first 2 chars
print(octal_digits)  # Output: '52'
```

**What this does:** Shows `oct()` with various values. Digits are 0-7. Negative numbers have minus sign before "0o". String slicing removes prefix.

### Example 3: Edge Case

```python
# Common use case: Unix file permissions
permission = 0o755  # Octal literal: rwxr-xr-x
print(f"Permission bits: {oct(permission)}")  # '0o755'

# Each octal digit represents 3 bits
number = 0b111101101  # Binary
print(oct(number))     # '0o755' (group 3 bits: 111 101 101)

# Convert back from octal string
octal_str = "755"
number = int(octal_str, 8)  # 493
print(number)
```

**What this shows:** Octal commonly used for Unix/Linux file permissions (chmod 755). Each octal digit represents exactly 3 bits. Can convert back using `int(octal_str, 8)`.

---

## Pattern Classification

**This term is:** CONVERSION FUNCTION (Number Base Representation)

**Similar terms in this pattern:**

1. `bin` - Converts integer to binary string (base-2)
2. `hex` - Converts integer to hexadecimal string (base-16)
3. `int` - Converts to integer (base-10, or from other bases)

**Pattern rule:** Base conversion functions should use short, technical names (often abbreviations) representing the target number system.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** "Oct" is abbreviation of "octal," from Latin "octo" meaning "eight." Octal system uses 8 digits (0-7), convenient for representing 3-bit groups.

**Why Python uses this:** "oct" abbreviates "octal" for brevity, matching pattern of `bin` and `hex`. Octal was important in early computing (PDP-11, etc.) and remains relevant for Unix permissions.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `oct()` function returns a string representation of an integer in octal (base-8) notation. Octal uses only digits 0-7, where each digit represents exactly 3 bits. The returned string has "0o" prefix (zero followed by lowercase 'o') following Python 3's syntax for octal literals.

Octal was more common in early computing when word sizes were often multiples of 3 bits. Today, its primary use in Python is Unix/Linux file permissions (chmod), where each octal digit encodes read (4), write (2), and execute (1) permissions. For example, 0o755 means owner has rwx (7), group has r-x (5), others have r-x (5).

Each octal digit represents 3 bits, making conversion from binary straightforward: group binary digits by threes. While less common than hexadecimal in modern programming, octal remains important for system administration and legacy code.

**Key behaviors:**

1. **Returns string with "0o" prefix:** Output format is "0o" followed by octal digits (0-7). Example: 64 becomes "0o100". Python 3 uses "0o" prefix (Python 2 used just "0").

2. **Only accepts integers:** Like `bin()` and `hex()`, only works with integer types. Passing floats raises `TypeError`. Negative numbers show minus sign before "0o": oct(-8) returns "-0o10".

3. **Base-8 representation:** Each position is a power of 8 (1, 8, 64, 512...). Digits range 0-7 only. Each octal digit corresponds to exactly 3 binary bits.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun/adjective (representing number system)
- **Action vs State:** Can be seen as ACTION (convert) or TARGET (octal form)
- **Temporal aspect:** Instantaneous conversion

### Recommended Form

**Primary recommendation:** Use noun or adjective form meaning "octal." Can abbreviate to "oct" if target language uses abbreviations, or keep full word. Must align with `bin` and `hex` translation strategy.

**Forms to AVOID:**

- ❌ "Eight" alone - too generic, doesn't capture base-8 system
- ❌ Inconsistent abbreviation with `bin`/`hex`
- ❌ Verb forms - should name the target system

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (within computing context)

**If YES, identify the CORRECT meaning for Python:**

N/A - "oct" and "octal" are unambiguous in computing contexts. Always refers to base-8 number system.

**Note:** Outside computing, "oct" might be confused with "oct-" prefix meaning eight (octagon, octopus). But in programming, always means octal numeral system.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `oct`, check these translations:**

- [ ] `bin` - Sister function for binary; MUST use parallel structure
- [ ] `hex` - Sister function for hexadecimal; MUST use parallel structure
- [ ] `int` - Related conversion function; should feel part of same family

**Consistency rule:**

Base conversion functions (`bin`, `hex`, `oct`) MUST use parallel grammatical structure. This is critical. All abbreviated or all full words.


### Functional relationships

**This term works WITH:**

1. **`oct` + integer input**: Convert to octal string

```python
print(oct(64))     # '0o100'
print(oct(511))    # '0o777'
```

2. **`oct` + file permissions**: Unix chmod values

```python
perm = 0o755  # Owner: rwx, Group: r-x, Others: r-x
print(oct(perm))  # '0o755'
```

**Common pairing:**

```python
# Number base conversions (compare representations)
number = 64
print(bin(number))  # '0b1000000'
print(oct(number))  # '0o100'
print(hex(number))  # '0x40'

# File permissions (common octal use)
import os
mode = 0o755
print(f"Chmod {oct(mode)}")

# Each octal digit = 3 bits
binary = 0b111101101  # 9 bits
print(oct(binary))     # '0o755' (groups: 111 101 101)

# Convert back from octal string
octal_str = "755"
number = int(octal_str, 8)  # 493
print(f"Decimal: {number}")

# Remove prefix for display
perm_value = 0o644
clean = oct(perm_value)[2:]  # '644'
print(f"File permission: {clean}")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `oct`

- "Octal" is standard computing term
- But less common than hex/binary in modern code
- Abbreviation vs full word varies by language
- MUST align with `bin` and `hex` (critical)

**For this term:** MEDIUM

**Rationale:** Octal is well-established but less commonly used than binary or hexadecimal. Main challenge is ensuring consistency with `bin`/`hex` translation strategy in same language pack. This consistency requirement is critical.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures OCTAL (base-8) number system concept?
- [ ] Distinguished from decimal number 8?
- [ ] Related to computer number representation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/adjective for number system)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] **CRITICAL:** Matches pattern of `bin` and `hex` translations?
- [ ] Uses same structure (all abbreviated or all full words)?
- [ ] Aligns with computing terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words or abbreviation)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Recognizable to programmers?

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
term: oct
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
