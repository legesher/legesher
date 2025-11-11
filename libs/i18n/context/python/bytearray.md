# Python Builtin Type: `bytearray` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (compound)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `bytearray` type represents mutable sequences of bytes (integers 0-255). Like `bytes` but modifiable - you can change individual bytes after creation. Used when you need to build or modify binary data incrementally, like buffers for file or network I/O.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create mutable bytearray
data = bytearray([72, 101, 108, 108, 111])
print(data)  # Output: bytearray(b'Hello')

# Modify individual bytes
data[0] = 104  # Change 'H' to 'h'
print(data)  # Output: bytearray(b'hello')
```

**What this does:** `bytearray()` creates a mutable sequence of bytes. Unlike `bytes` which is immutable, you can modify individual bytes by assignment.

### Example 2: Common Pattern

```python
# Build binary data incrementally
buffer = bytearray()
buffer.append(72)        # Add 'H'
buffer.extend([101, 108, 108, 111])  # Add 'ello'
print(buffer)  # Output: bytearray(b'Hello')

# Convert between bytes and bytearray
immutable = bytes([1, 2, 3])
mutable = bytearray(immutable)
mutable[0] = 99
print(mutable)  # bytearray(b'c\x02\x03')
```

**What this does:** Bytearrays support list-like operations (append, extend, insert, pop). You can build binary data incrementally. Convert between `bytes` (immutable) and `bytearray` (mutable) as needed.

### Example 3: Edge Case

```python
# Bytearray as buffer
data = bytearray(10)  # Pre-allocate 10 bytes (all zeros)
print(data)  # Output: bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

# Modify in-place
data[0:5] = b'Hello'
print(data)  # Output: bytearray(b'Hello\x00\x00\x00\x00\x00')
```

**What this shows:** You can pre-allocate bytearrays with specific size (filled with zeros). Useful for buffers. Slice assignment works, allowing in-place modifications.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Mutable Binary Sequence)

**Similar terms in this pattern:**

1. `bytes` - Immutable bytes (cannot modify)
2. `list` - Mutable sequence (any objects, not just bytes)
3. `memoryview` - View into byte buffers (related to bytes)

**Pattern rule:** Mutable type constructors should use noun forms. Compound terms should clearly show relationship to base type (byte + array).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `bytes` | bytes | بايتات | 字节串 | बाइट्स |
| `list` | lista | قائمة | 列表 | सूची |
| `bytearray` | **matriz_bytes** | **مصفوفة_بايت** | **字节数组** | **बाइट_सरणी** |

---

## Etymology (Brief)

**English Origin:** Compound (byte + array)

**Root meaning:** Combines "byte" (8-bit unit) with "array" (ordered collection). "Array" comes from Old French "arayer" meaning "to put in order." In programming, an array is a data structure holding multiple values.

**Why Python uses this:** The name clearly indicates this is an array (sequence) of bytes that can be modified. The compound name distinguishes it from immutable `bytes` while showing they're related types.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `bytearray` type is a mutable version of `bytes`. It stores a sequence of integers 0-255, but unlike `bytes`, you can modify individual elements after creation. This makes it suitable for building binary data incrementally or modifying existing binary data.

Bytearrays support all sequence operations plus list-like mutation methods: `append()`, `extend()`, `insert()`, `pop()`, `remove()`, etc. You can change individual bytes, slices, or grow/shrink the sequence. This mutability comes with a tradeoff: bytearrays aren't hashable and can't be used as dict keys or in sets.

Common use cases include network buffers, file I/O buffers, and any scenario where you're building or modifying binary data piece by piece. When done modifying, you can convert to immutable `bytes` using `bytes(bytearray)`.

**Key behaviors:**

1. **Mutable sequence:** Can modify individual bytes, slices, or size after creation. Supports in-place operations like `append`, `extend`, `insert`. Not hashable due to mutability.

2. **Same value range:** Like `bytes`, each element must be 0-255. Larger values raise `ValueError`. Indexing returns integers. Supports same indexing and slicing as `bytes`.

3. **Memory efficiency:** More efficient than creating new `bytes` objects repeatedly. Can pre-allocate with specific size. Good for buffers and incremental binary data construction.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (byte + array)
- **Action vs State:** STATE/THING - describes what the object is
- **Temporal aspect:** Static type definition

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound noun | "matriz_bytes", "tableau_octets" |
| Germanic (de, nl, sv) | Compound noun | "Byte-Array", "bytearray" |
| Slavic (ru, pl, uk) | Compound | "байтовый_массив" (byte array) |
| Arabic | Compound | "مصفوفة بايتات" (array bytes) |
| Chinese | Compound | "字节数组" (byte array) |
| Hindi | Compound | "बाइट सरणी" (byte array) |

**Primary recommendation:** Use compound form combining "byte" + "array" concept. Keep relationship to `bytes` clear while indicating mutability/array nature.

**Forms to AVOID:**

- ❌ Using singular "byte" - should indicate multiple bytes
- ❌ Breaking compound into two separate words (if language doesn't allow)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `matriz_bytes` or `arreglo_bytes`
- **Form:** Compound noun
- **Why it works:** "Matriz" (matrix/array) + "bytes" clearly indicates mutable byte sequence. Could also use "arreglo" (array). Maintains connection to `bytes` while showing array nature.

**Arabic:**

- **Translation:** `مصفوفة_بايت` (mṣfūfat bāyt) or `صف_بايتات` (ṣaf bāytāt)
- **Form:** Compound noun
- **Why it works:** "مصفوفة" (array/matrix) + "بايت" (byte). Standard Arabic computing terminology. Shows mutable collection structure.

**Chinese:**

- **Translation:** `字节数组` (zìjié shùzǔ)
- **Form:** Compound noun
- **Why it works:** 字节 (byte) + 数组 (array). Standard Chinese term for byte array. Clear structure indicating multiple bytes in array form.

**Hindi:**

- **Translation:** `बाइट_सरणी` (bāiṭ saraṇī) or `बाइट_अरे`
- **Form:** Compound noun
- **Why it works:** "बाइट" (byte) + "सरणी" (array). Could also transliterate "array" as "अरे." Shows mutable sequence of bytes.

### ❌ Common Translation Mistakes

**Mistake 1: Using only "array" without "byte"**

- **Wrong:** `matriz` (Spanish - "array" alone)
- **Why wrong:** Too generic. Could be array of anything. Need to specify it's bytes.
- **Right:** `matriz_bytes` (byte array - specific)

**Mistake 2: Using same translation as bytes**

- **Wrong:** `bytes` (same as immutable bytes type)
- **Why wrong:** `bytes` and `bytearray` are different types - one immutable, one mutable. Need distinct translations to show this difference.
- **Right:** `bytes` vs `matriz_bytes` (distinct types)

**Mistake 3: Using "list" terminology**

- **Wrong:** `lista_bytes` (Spanish - "byte list")
- **Why wrong:** While similar to lists, bytearrays are specifically for bytes (0-255) and have different characteristics. "Array" better captures the fixed-type nature.
- **Right:** `matriz_bytes` or `arreglo_bytes` (byte array)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specific compound term)

**"Bytearray" in Python context:**

✅ **Mutable sequence of bytes** (integers 0-255) - Python's modifiable binary sequence type

The term is unambiguous. It's a compound of "byte" + "array," clearly indicating an array of bytes that can be modified.

**Your translation should:** Combine concepts of "byte" and "array/matrix" to show this is a mutable collection of bytes. Keep relationship to `bytes` clear.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `bytearray`, check these translations:**

- [ ] `bytes` - Immutable version; should share "byte" root with clear differentiator
- [ ] `list` - Similar mutable sequence; but bytearray is specific to bytes
- [ ] `memoryview` - Related buffer type; all deal with binary data

**Consistency rule:**

Binary data types (`bytes`, `bytearray`, `memoryview`) should use related terminology. The "byte" part should be consistent, with differentiator showing mutability or view nature.

**Example:**

Spanish: `bytes`, `matriz_bytes` - consistent "bytes" root ✅
Chinese: `字节串`, `字节数组` - consistent "字节" (byte) root ✅
NOT: `bytes`, `array_binario` ❌ (inconsistent roots)

### Functional relationships

**This term works WITH:**

1. **`bytearray` modification**: In-place changes
```python
data = bytearray(b"Hello")
data[0] = ord('J')  # Modify first byte
print(data)  # bytearray(b'Jello')
```

2. **`bytearray` with bytes**: Conversion between mutable/immutable
```python
immutable = bytes([1, 2, 3])
mutable = bytearray(immutable)
mutable.append(4)
back_to_bytes = bytes(mutable)
```

**Common pairing:**

```python
# Create bytearray
data1 = bytearray([65, 66, 67])   # From integers
data2 = bytearray(b"ABC")          # From bytes
data3 = bytearray(10)              # Pre-allocate (zeros)

# Mutable operations
data = bytearray(b"Hello")
data[0] = 104                      # Modify: h'ello'
data.append(33)                    # Add '!'
data.extend(b" World")             # Extend
print(data)  # bytearray(b'hello! World')

# In-place methods
data = bytearray(b"Hello World")
data.remove(ord('o'))              # Remove first 'o'
data.insert(0, ord('!'))           # Insert at start
last = data.pop()                  # Remove and return last

# Convert to/from bytes
mutable = bytearray(b"Test")
immutable = bytes(mutable)         # Convert to bytes
mutable2 = bytearray(immutable)    # Back to bytearray

# Buffer usage
buffer = bytearray(1024)           # 1KB buffer
buffer[0:5] = b"Start"
# Use buffer for I/O operations
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `bytearray`:

- Compound term requires translating two concepts
- Decision: keep English vs translate both parts vs hybrid
- Need to show relationship to `bytes` while indicating mutability
- "Array" has multiple possible translations (array, matrix, list)

**For this term:** MEDIUM

**Rationale:** The compound nature makes this moderately complex. Need to maintain connection to `bytes` while adding array/mutability concept. Different languages have different preferences for compound terms (underscore, camelCase, single word, two words).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Relationship to `bytes` must be clear. The mutable/array aspect must be evident.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MUTABLE BYTE SEQUENCE concept?
- [ ] Clearly related to but distinct from `bytes`?
- [ ] Shows array/collection nature?

### 2. Linguistic Correctness

- [ ] Correct compound form for target language?
- [ ] Follows target language rules for technical compounds?
- [ ] Capitalization correct (lowercase for Python types)?

### 3. Consistency

- [ ] Shares root with `bytes` translation?
- [ ] Uses standard "array" term from target language?
- [ ] Aligns with how compound types are named?

### 4. Usability

- [ ] Short enough (2-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Immediately shows relationship to bytes?

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
term: bytearray
language: es
translation: matriz_bytes
form: compound_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "matriz_bytes" combines "matriz" (matrix/array) with "bytes," clearly indicating a mutable byte collection. The underscore follows Python convention for compound names. Maintains clear relationship to `bytes` while showing the array/mutable nature.

**Alternatives considered:**

1. `arreglo_bytes` (byte array) - Also valid, "arreglo" is common for arrays
2. `bytearray` (keep English) - Works but loses clarity about byte relationship
3. `bytes_mutable` (mutable bytes) - Focuses on mutability but "array" better indicates structure

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Compound "byte + array" terms are straightforward in most languages. The structure clearly shows relationship to `bytes` with added mutability.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
