# Python Builtin Function: `ascii` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `ascii` function returns a string representation of an object similar to `repr()`, but escapes non-ASCII characters using `\x`, `\u`, or `\U` escape sequences. It ensures the output contains only ASCII characters, making it safe for environments that don't support Unicode.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# ASCII representation of a string
text = "Café"
print(ascii(text))  # Output: 'Caf\xe9'
```

**What this does:** `ascii()` converts the string to a representation where non-ASCII characters (like é) are shown as escape sequences (`\xe9`). The output contains only ASCII characters.

### Example 2: Common Pattern

```python
# Various Unicode characters
emoji = "Hello 👋"
print(ascii(emoji))  # Output: 'Hello \U0001f44b'

greeting = "你好"
print(ascii(greeting))  # Output: '\u4f60\u597d'
```

**What this does:** All non-ASCII characters are escaped. Emojis use `\U` (32-bit), most Unicode uses `\u` (16-bit), Latin-1 extended uses `\x` (8-bit). The resulting string is pure ASCII.

### Example 3: Edge Case

```python
# ASCII characters unchanged
regular = "Hello123"
print(ascii(regular))  # Output: 'Hello123'

# Comparison with repr
text = "Café"
print(repr(text))   # Output: 'Café' (Unicode intact)
print(ascii(text))  # Output: 'Caf\xe9' (escaped)
```

**What this shows:** ASCII characters (0-127) pass through unchanged. Only non-ASCII gets escaped. `ascii()` is like `repr()` but with forced ASCII-only output.

---

## Pattern Classification

**This term is:** REPRESENTATION FUNCTION (ASCII-only)

**Similar terms in this pattern:**

1. `repr` - General string representation (may include Unicode)
2. `str` - Human-readable string (supports Unicode)
3. `ord` - Character to number (related to character codes)

**Pattern rule:** Representation functions should use noun forms describing the type of representation. "ASCII" refers to the character encoding standard.


---

## Etymology (Brief)

**English Origin:** Acronym (American)

**Root meaning:** ASCII stands for "American Standard Code for Information Interchange" (1963). It's a character encoding standard that uses 7 bits to represent 128 characters (letters, digits, punctuation, control characters).

**Why Python uses this:** The function is named after the ASCII standard because it ensures output contains only characters from the ASCII range (0-127). This was crucial for compatibility with older systems and protocols that only support ASCII.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `ascii()` function works like `repr()` but ensures the result contains only ASCII characters by escaping anything outside the ASCII range (characters with code points above 127). It calls the object's `__repr__()` method, then escapes non-ASCII characters using Python's escape sequences.

Characters are escaped based on their code point: `\xhh` for 8-bit values, `\uxxxx` for 16-bit values, and `\Uxxxxxxxx` for 32-bit values. This makes the output safe for ASCII-only systems, logs, or protocols, while still showing the original character information.

The function is useful for debugging when you need pure ASCII output, writing to ASCII-only files, or ensuring compatibility with systems that don't handle Unicode well. However, modern Python 3 code usually handles Unicode fine, so `ascii()` is less commonly needed than in Python 2.

**Key behaviors:**

1. **ASCII-only output:** Guarantees result contains only characters 0-127. Non-ASCII characters become escape sequences. This makes output safe for any system that supports ASCII.

2. **Uses repr internally:** Calls `__repr__()` then escapes non-ASCII. Behavior mirrors `repr()` except for character escaping. Object representation structure is identical.

3. **Escape sequences:** Uses `\x` for Latin-1 extended (128-255), `\u` for BMP characters (256-65535), `\U` for higher Unicode planes (65536+). Output is still valid Python string literal.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Proper noun (name of encoding standard)
- **Action vs State:** STATE/PROPERTY - describes encoding type
- **Temporal aspect:** Instantaneous - converts at moment of call

### Recommended Form

**Primary recommendation:** Keep "ascii" as-is (lowercase). It's an internationally recognized technical acronym. No translation needed.

**Forms to AVOID:**

- ❌ Translating meaning ("American Standard...") - too verbose
- ❌ Using local encoding names - ASCII is the specific standard

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (it's a specific acronym)

**ASCII has one technical meaning:**

✅ **American Standard Code for Information Interchange** - 7-bit character encoding (0-127)

The term is unambiguous in computing contexts. It specifically refers to the ASCII standard, not general "text" or "character."

**Your translation should:** Keep "ASCII" or transliterate it. No semantic translation needed.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ascii`, check these translations:**

- [ ] `repr` - Similar representation function; ascii is specialized version
- [ ] `str` - String conversion; ascii ensures ASCII-only
- [ ] `ord`/`chr` - Character code conversion; related to ASCII codes

**Consistency rule:**

Character/string representation functions (`ascii`, `repr`, `str`) should use compatible forms. ASCII is special because it's a proper noun (standard name), while others are common nouns/verbs.


### Functional relationships

**This term works WITH:**

1. **`ascii` for safe representation**: Ensure ASCII-only output

```python
text = "Café ☕"
print(ascii(text))  # 'Caf\xe9 \u2615'
```

2. **`ascii` vs `repr`**: ASCII-safe vs Unicode-aware

```python
s = "Hello 世界"
print(repr(s))   # 'Hello 世界' (Unicode intact)
print(ascii(s))  # 'Hello \u4e16\u754c' (escaped)
```

**Common pairing:**

```python
# ascii with Unicode strings
text = "Café"
print(ascii(text))  # 'Caf\xe9'

# Emoji handling
emoji = "🎉"
print(ascii(emoji))  # '\U0001f389'

# Logging with ASCII
import logging
name = "José"
logging.info(f"User: {ascii(name)}")  # Ensures ASCII-safe logs

# ASCII vs repr vs str
s = "Pythön"
print(str(s))    # Pythön
print(repr(s))   # 'Pythön'
print(ascii(s))  # 'Pyth\xf6n'

# Custom objects
class User:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"User('{self.name}')"

user = User("François")
print(ascii(user))  # User('Fran\xe7ois')
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ascii`

- Decision point: keep acronym vs transliterate vs translate
- "ASCII" is internationally recognized but some languages prefer transliteration
- Balance between universal recognition and linguistic consistency
- Need to decide on case (ASCII vs ascii)

**For this term:** MEDIUM

**Rationale:** While ASCII is universally known, the question is whether to keep it unchanged, transliterate it, or translate it. Best practice is keeping it unchanged (lowercase "ascii" for Python) as it's an international standard. Medium difficulty because of these translation strategy choices.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: ASCII is a technical acronym, not a common word. Acronyms are usually kept or transliterated, rarely translated.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Preserves ASCII encoding concept?
- [ ] Recognizable as the ASCII standard?
- [ ] Not confused with generic "character" or "text"?

### 2. Linguistic Correctness

- [ ] Appropriate handling of acronym (keep or transliterate)?
- [ ] Capitalization correct (lowercase "ascii" for function name)?
- [ ] Follows target language conventions for loanwords/acronyms?

### 3. Consistency

- [ ] Compatible with `repr` and `str` translations?
- [ ] Matches how ASCII is referenced in target language CS education?
- [ ] Consistent with other technical acronyms?

### 4. Usability

- [ ] Short (preferably 5 characters like "ascii")?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Immediately recognizable to developers?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Professional technical term?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: ascii
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
