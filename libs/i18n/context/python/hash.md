# Python Builtin Function: `hash` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (computational function)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `hash` function in Python returns the hash value of an object (if it has one). Hash values are integers used for fast dictionary lookups and set membership testing. Immutable objects can be hashed; mutable objects like lists and dicts cannot. Two equal objects must have the same hash value.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Hash of integer (returns itself for small ints)
h = hash(42)
print(h)  # Output: 42

# Hash of string
h = hash("hello")
print(h)  # Output: some integer (varies by Python session)
```

**What this does:** `hash()` computes a hash value (integer) for an object. For small integers, returns the number itself. For strings and other objects, returns a computed hash. Hash values may differ between Python sessions.

### Example 2: Common Pattern

```python
# Hash of tuple (immutable, hashable)
t = (1, 2, 3)
h = hash(t)
print(h)  # Some integer

# Cannot hash mutable objects
try:
    hash([1, 2, 3])  # Lists are mutable
except TypeError as e:
    print(e)  # "unhashable type: 'list'"

# Equal objects have equal hashes
a = "test"
b = "test"
print(hash(a) == hash(b))  # True
```

**What this does:** Immutable objects (int, str, tuple) are hashable. Mutable objects (list, dict, set) are not hashable and raise TypeError. Equal objects must have equal hashes (but different objects may have same hash - collision).

### Example 3: Edge Case

```python
# Hash randomization (varies per session)
# Run multiple times - hash("hello") gives different values
print(hash("hello"))  # e.g., 5043678898234015791
# Next session might show different number

# None has a hash
print(hash(None))  # Usually 0 or small value

# Custom objects with __hash__
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p = Point(1, 2)
print(hash(p))  # Hash based on tuple (1, 2)
```

**What this shows:** String/bytes hashes are randomized per Python session (security feature). `None`, booleans, and numbers have predictable hashes. Custom classes can implement `__hash__()` to be hashable (must also implement `__eq__()`).

---

## Pattern Classification

**This term is:** COMPUTATIONAL FUNCTION (Fingerprinting)

**Similar terms in this pattern:**

1. `id` - Returns object identity (memory address)
2. `len` - Returns object property (length)
3. `type` - Returns object property (type)

**Pattern rule:** Computational/introspection functions should use noun forms naming what they compute or return. "Hash" is both the operation and the result.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `id` | identificador | معرّف | 标识符 | पहचानकर्ता |
| `len` | longitud | طول | 长度 | लंबाई |
| `hash` | **dispersión** | **تجزئة** | **哈希** | **हैश** |

---

## Etymology (Brief)

**English Origin:** French via cooking term

**Root meaning:** From French "hacher" meaning "to chop/mince." In computing (1950s), "hash" referred to chopping up data into a mixed-up form. A "hash function" chops/transforms data into a fixed-size fingerprint. The term evokes scrambling or mixing.

**Why Python uses this:** "Hash" is the universal CS term for computing fingerprints of data. Hash functions map objects to integers for fast lookup in dictionaries and sets. Python uses the short, standard term "hash" recognized worldwide in programming.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `hash()` function returns the hash value of an object by calling its `__hash__()` method. Hash values are integers used internally by dictionaries (dict) and sets to enable O(1) average-case lookup. When you use an object as a dict key or add it to a set, Python computes its hash value.

Only immutable objects can be hashed (int, float, str, tuple, frozenset, None, True, False). Mutable objects (list, dict, set) are unhashable because their content can change, which would change their hash, breaking dict/set internals. If an object is mutable, `hash()` raises TypeError: "unhashable type."

Hash contract: if `a == b`, then `hash(a) == hash(b)` must be true. The reverse isn't required - different objects can have the same hash (collision). Python's dict/set handle collisions gracefully. Hash values are consistent within a Python session but may differ across sessions (string hash randomization for security).

**Key behaviors:**

1. **Hashable types:** Immutable built-ins are hashable: int, float, str, bytes, tuple (if elements hashable), frozenset, None, True, False. Mutable types are not: list, dict, set, bytearray. Custom objects are hashable if they implement `__hash__()` and `__eq__()`.

2. **Equality contract:** Equal objects must have equal hashes. `hash(3) == hash(3.0)` because `3 == 3.0`. Custom classes must maintain this: if you override `__eq__()`, you must override `__hash__()` consistently or set `__hash__ = None`.

3. **Hash randomization:** String and bytes hashes include a random seed (different per Python process) to prevent hash collision DoS attacks. `hash("test")` gives different values in different Python sessions. Numbers and None have deterministic hashes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (computational result/operation)
- **Action vs State:** COMPUTATION - generates fingerprint
- **Temporal aspect:** Computed value

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun/technical term | "dispersión", "hachage" - hash |
| Germanic (de, nl, sv) | Noun/loanword | "Hash", "Hashwert" |
| Slavic (ru, pl, uk) | Noun/loanword | "хеш", "hasz" |
| Arabic | Verbal noun or loanword | "تجزئة" (fragmentation) or "هاش" |
| Chinese | Transliteration | "哈希", "散列" |
| Hindi | Transliteration or compound | "हैश", "सारांश" |

**Primary recommendation:** Use transliteration "hash" or native technical term meaning "dispersion/fragmentation/chopping." Hash is a specialized CS term that many languages transliterate.

**Forms to AVOID:**

- ❌ Using "# symbol" - that's hashtag/number sign, different concept
- ❌ Using generic "code" - hash is specific fingerprinting algorithm
- ❌ Using "scramble" - too informal, not standard CS term

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `dispersión` or `hash`
- **Form:** Noun or transliteration
- **Why it works:** "Dispersión" means dispersion/scattering - captures hash function concept. Alternatively, transliterate "hash" (pronounced "hash" or "jash"). Both used in Spanish CS contexts. "Dispersión" more descriptive, "hash" more universal.

**Arabic:**

- **Translation:** `تجزئة` (tajzi'a) or `هاش` (hāsh)
- **Form:** Verbal noun or transliteration
- **Why it works:** `تجزئة` means "fragmentation/partitioning" - captures hash concept. `هاش` is direct transliteration. Technical CS contexts use both. `تجزئة` more Arabic, `هاش` more internationally recognizable.

**Chinese:**

- **Translation:** `哈希` (hāxī) or `散列` (sànliè)
- **Form:** Transliteration or native term
- **Why it works:** `哈希` is phonetic transliteration of "hash" - widely recognized in Chinese CS. `散列` means "scatter/disperse" - descriptive native term. Both standard in Chinese programming contexts. `哈希` more common.

**Hindi:**

- **Translation:** `हैश` (haish) or `सारांश` (sārāṃsh)
- **Form:** Transliteration or native term
- **Why it works:** `हैश` is direct transliteration - used in Indian CS education. `सारांश` means "summary/digest" - captures fingerprint concept. Transliteration more standard in technical contexts.

### ❌ Common Translation Mistakes

**Mistake 1: Using "almohadilla" (#symbol) instead of hash function**

- **Wrong:** `almohadilla` (Spanish - "hash symbol" #, hashtag)
- **Why wrong:** "Almohadilla" refers to the # symbol (number sign/hashtag), not the hash function in computing. Different concepts. Need computational hash term.
- **Right:** `dispersión` or `hash` (hash function, computational concept)

**Mistake 2: Using generic "código" (code)**

- **Wrong:** `código` (Spanish - "code")
- **Why wrong:** "Código" is too generic - could mean source code, error code, etc. Hash is a specific cryptographic/computational fingerprint. Need precise term.
- **Right:** `dispersión` or `hash` (specific hash function/value)

**Mistake 3: Using "mezcla" (mixture) informally**

- **Wrong:** `mezcla` (Spanish - "mixture/blend")
- **Why wrong:** While hash functions do "mix" data, "mezcla" is too informal/colloquial. Need technical term. Not standard in CS education.
- **Right:** `dispersión` (technical term) or `hash` (transliteration)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Hash" as # symbol (hashtag, number sign)
- ❌ Meaning 2: "Hash" as food (corned beef hash)
- ✅ Meaning 3: **COMPUTATIONAL HASH** - fingerprint/digest of data
- ❌ Meaning 4: "Hash" slang for hashish

**Example:**

English "hash" can mean:

1. "Use a hash symbol (#)" - number sign ❌
2. "Corned beef hash" - food ❌
3. "`hash('hello')` returns integer fingerprint" ✅ **This is the Python meaning**
4. Slang for cannabis ❌

**Your translation should capture meaning #3: the computational hash function - an algorithm that maps data to fixed-size integer fingerprint.**

Used in dictionaries, sets, cryptography, data integrity checking.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `hash`, check these translations:**

- [ ] `dict` - Uses hashing internally for keys
- [ ] `set` - Uses hashing for membership
- [ ] `id` - Related identity function
- [ ] `__hash__` method - Dunder method name

**Consistency rule:**

Hash-related terminology should use the same root translation. If you translate `hash` as "dispersión," then `__hash__` should be `__dispersión__` and hash-related discussions use "dispersión."

**Example:**

Spanish: If using `dispersión` for `hash`, then:

- "función de dispersión" (hash function)
- "valor de dispersión" (hash value)
- "tabla de dispersión" (hash table)
Consistency across all hash-related terms ✅

### Functional relationships

**This term works WITH:**

1. **`hash` for hashable objects**: Get fingerprint

```python
hash(42)      # Integer
hash("text")  # String
hash((1, 2))  # Tuple
```

2. **`hash` in dict/set operations**: Enable fast lookup

```python
# Dict uses hash for keys
d = {key: value}  # Internally: hash(key)

# Set uses hash for membership
s = {1, 2, 3}    # Internally: hash(1), hash(2), hash(3)
```

**Common pairing:**

```python
# Basic hashing
print(hash(42))        # 42 (small ints hash to themselves)
print(hash(3.14))      # Some integer
print(hash("hello"))   # Some integer (varies per session)
print(hash(True))      # 1
print(hash(False))     # 0
print(hash(None))      # Usually 0 or small value

# Immutable objects (hashable)
hash((1, 2, 3))        # Tuple: OK
hash(frozenset([1, 2])) # Frozenset: OK
hash(42)               # Int: OK
hash("text")           # Str: OK

# Mutable objects (unhashable)
try:
    hash([1, 2, 3])    # List: TypeError
except TypeError:
    print("Lists are unhashable")

try:
    hash({1: 'a'})     # Dict: TypeError
except TypeError:
    print("Dicts are unhashable")

# Equal objects have equal hashes
assert hash(3) == hash(3.0)  # 3 == 3.0
assert hash("abc") == hash("abc")

# Use in sets (requires hashability)
s = {1, 2, 3}          # OK - ints hashable
# s = {[1], [2]}       # Error - lists unhashable

# Use as dict keys
d = {(1, 2): "point"}  # OK - tuple hashable
# d = {[1, 2]: "list"} # Error - list unhashable

# Custom hashable class
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(1, 2)
p2 = Point(1, 2)
print(hash(p1) == hash(p2))  # True (equal objects)

# Use custom object as dict key
points_dict = {p1: "origin"}  # Works!

# Hash in sets
points_set = {Point(0, 0), Point(1, 1)}  # Works!

# Check if object is hashable
from collections.abc import Hashable
print(isinstance(42, Hashable))      # True
print(isinstance("text", Hashable))  # True
print(isinstance([1, 2], Hashable))  # False
print(isinstance({1: 2}, Hashable))  # False
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear technical concept
- Standard CS terminology exists
- Widely transliterated internationally
- **AI confidence should be HIGH**

### Why EASY for `hash`

- Universal computing concept (hash functions)
- Standard term in CS globally
- Often transliterated rather than translated
- Well-established in programming

**For this term:** EASY

**Rationale:** Hash functions are fundamental in computer science and cryptography. The term "hash" is so universal that many languages simply transliterate it. Alternative translations use terms meaning "dispersion," "fragmentation," or "digest" which are also well-established in CS literature.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Distinguish computational hash from other meanings (# symbol, food). Programming context makes the computational meaning clear. Choice between transliteration vs. native term depends on target language's CS education conventions.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures COMPUTATIONAL HASH concept?
- [ ] Understood as fingerprint/digest generation?
- [ ] Distinguished from # symbol (hashtag)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches CS terminology in target language?
- [ ] Compatible with dict/set concepts (which use hashing)?
- [ ] Aligns with how hashing is taught in CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard CS term or transliteration)?

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
term: hash
language: es
translation: dispersión
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "dispersión" (dispersion/scattering) is a technical term used for hash functions in Spanish CS contexts. It captures the concept of distributing/scattering data into fingerprints. Alternative: direct transliteration "hash" is also widely used and recognized.

**Alternatives considered:**

1. `hash` (transliteration) - Widely recognized, international term
2. `picadillo` (hash as chopped mixture) - Too colloquial/food-related
3. `almohadilla` (# symbol) - Wrong concept (hashtag, not hash function)

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Hash is a universal CS concept with established translations or transliterations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
