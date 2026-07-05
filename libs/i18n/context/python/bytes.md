# Python Builtin Type: `bytes` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `bytes` type represents immutable sequences of bytes (integers 0-255). It's used for binary data like file contents, network packets, and encoded text. Unlike strings which are text, bytes are raw binary data with no inherent encoding.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create bytes object
data = bytes([72, 101, 108, 108, 111])
print(data)  # Output: b'Hello'
```

**What this does:** `bytes()` creates an immutable sequence of byte values. When displayed, ASCII-printable bytes show as characters (prefixed with `b`), others show as `\x` escape sequences.

### Example 2: Common Pattern

```python
# Encode string to bytes
text = "Hello"
binary = text.encode('utf-8')
print(binary)         # Output: b'Hello'
print(type(binary))   # Output: <class 'bytes'>

# Bytes are immutable
# binary[0] = 72  # TypeError: 'bytes' object does not support item assignment
```

**What this does:** Strings encode to bytes using an encoding like UTF-8. Once created, bytes objects are immutable - you cannot modify individual bytes. To modify, convert to `bytearray`.

### Example 3: Edge Case

```python
# Non-ASCII bytes
data = bytes([0x48, 0x65, 0x6C, 0xFF, 0x00])
print(data)  # Output: b'Hel\xff\x00'

# Bytes vs string
text = "Hello"
binary = b"Hello"
print(text == binary)    # Output: False (different types)
print(text == binary.decode())  # Output: True (after decoding)
```

**What this shows:** Bytes can contain any values 0-255. Non-printable bytes display as `\x` escapes. Bytes and strings are different types even if they look similar - must decode bytes to get strings.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Immutable Binary Sequence)

**Similar terms in this pattern:**

1. `bytearray` - Mutable bytes (can modify individual bytes)
2. `str` - Text strings (characters, not raw bytes)
3. `list` - General sequence (any objects, not just bytes)

**Pattern rule:** Type constructors should use noun forms describing what they create. "Bytes" is plural noun referring to binary data units.


---

## Etymology (Brief)

**English Origin:** Computing term

**Root meaning:** "Byte" was coined in 1956 by Werner Buchholz at IBM. It's a play on "bit" (binary digit), with the 'y' to avoid confusion with "bit." A byte is typically 8 bits and is the basic addressable unit of computer memory.

**Why Python uses this:** "bytes" is the plural of "byte," indicating a sequence of bytes. Python 3 made the string/bytes distinction explicit: `str` for text, `bytes` for binary data. This prevents encoding errors common in Python 2.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `bytes` type represents immutable sequences of integers in range 0-255 (one byte each). It's Python's type for binary data - raw bytes with no text encoding. Unlike strings which are sequences of Unicode characters, bytes are sequences of 8-bit values.

You create bytes from iterables of integers, string literals with `b` prefix, or by encoding strings. Once created, bytes are immutable like strings. To create mutable byte sequences, use `bytearray`. Bytes support sequence operations (indexing, slicing, iteration) and have methods for searching, splitting, etc.

In Python 3, the string/bytes distinction is strict. You cannot mix them without explicit conversion. Strings must be encoded to bytes (`.encode()`) and bytes must be decoded to strings (`.decode()`). This prevents the encoding bugs that plagued Python 2 where strings and bytes mixed implicitly.

**Key behaviors:**

1. **Immutable sequence:** Once created, cannot modify individual bytes. Slicing creates new bytes objects. This makes bytes hashable and safe to use as dict keys or in sets.

2. **Values 0-255:** Each element must be an integer 0-255 (one byte). Trying to use larger values raises `ValueError`. Indexing returns integers, not single-byte bytes objects.

3. **Binary data:** Used for non-text data (images, audio, network packets) or encoded text. Has no inherent encoding - interpretation depends on context. Must explicitly decode to get strings.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (the data type)
- **Action vs State:** STATE/THING - describes what the object is
- **Temporal aspect:** Static type definition

### Recommended Form

**Primary recommendation:** Keep "bytes" unchanged or transliterate. It's an international computing term. If translating, use plural form of "byte" in target language.

**Forms to AVOID:**

- ❌ Using singular "byte" - should be plural
- ❌ Using "binary" alone - too general

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specific technical term)

**"Bytes" in computing context:**

✅ **Sequence of 8-bit values** (range 0-255) - Python's immutable binary sequence type

The term is unambiguous in programming contexts. It specifically refers to binary data in byte-sized chunks, not text or other data types.

**Your translation should:** Capture that this is binary data in byte units. Keep as "bytes" (international term) or transliterate/translate plural form of "byte."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `bytes`, check these translations:**

- [ ] `bytearray` - Mutable version; should feel related (same root + differentiator)
- [ ] `str` - Text type; should be clearly distinct from bytes
- [ ] `int` - Integer type; bytes contain integers but are sequences

**Consistency rule:**

Binary data types (`bytes`, `bytearray`) should use related translations showing they're both byte-based. Clear distinction from text (`str`) is critical in Python 3.


### Functional relationships

**This term works WITH:**

1. **`bytes` from encoding**: String to binary

```python
text = "Hello"
binary = text.encode('utf-8')  # str -> bytes
```

2. **`bytes` with decoding**: Binary to string

```python
binary = b"Hello"
text = binary.decode('utf-8')  # bytes -> str
```

**Common pairing:**

```python
# Create bytes
data1 = bytes([65, 66, 67])      # From integers
data2 = b"ABC"                    # Literal
data3 = "ABC".encode('utf-8')    # From string

# Immutable
data = b"Hello"
# data[0] = 72  # TypeError!

# Indexing returns int
print(b"A"[0])  # Output: 65 (not b'A')

# Common operations
data = b"Hello, World"
print(data[0:5])          # b'Hello' (slicing)
print(b"Hello" + b"!")    # b'Hello!' (concatenation)
print(len(data))          # 12 (length)

# bytes vs bytearray
immutable = bytes([1, 2, 3])     # Cannot modify
mutable = bytearray([1, 2, 3])   # Can modify
mutable[0] = 99                   # OK
# immutable[0] = 99               # TypeError

# Encoding/decoding
text = "Café"
utf8_bytes = text.encode('utf-8')
back_to_text = utf8_bytes.decode('utf-8')
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `bytes`

- Decision: keep English term vs translate vs transliterate
- "Byte" is international but some languages have native terms
- Need to ensure plural form (not singular "byte")
- Distinction from "string" must be clear

**For this term:** MEDIUM

**Rationale:** "Byte" is internationally recognized in computing, but the question is whether to keep it as "bytes," transliterate it to local script, or translate to native equivalent (like "octets"). The plural form is important. Medium because of these strategy choices.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: In Python 3, bytes/string distinction is critical. Translation must not blur this line.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures BINARY DATA concept (not text)?
- [ ] Clearly distinct from string type?
- [ ] Understood as sequence of byte values?

### 2. Linguistic Correctness

- [ ] Correct part of speech (plural noun)?
- [ ] Follows target language grammar for plurals?
- [ ] Capitalization correct (lowercase for Python types)?

### 3. Consistency

- [ ] Related to `bytearray` translation (similar root)?
- [ ] Clearly distinct from `str` translation?
- [ ] Aligns with how "byte" is used in target language CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Immediately recognizable?

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
term: bytes
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
