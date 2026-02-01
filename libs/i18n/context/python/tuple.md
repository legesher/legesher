# Python Builtin Type: `tuple` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (immutable sequence)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

A `tuple` in Python is an immutable, ordered sequence of items. Like a list but cannot be modified after creation. Tuples are created with parentheses `()` or just commas, and are commonly used for fixed collections of related values.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create a tuple
coordinates = (10, 20)
x = coordinates[0]  # 10
y = coordinates[1]  # 20
print(f"Position: ({x}, {y})")
```

**What this does:** Creates a tuple with two values. Access items by index like lists. Parentheses are optional but recommended for clarity.

### Example 2: Common Pattern

```python
# Multiple return values
def get_user():
    return "Alice", 25, "alice@example.com"

name, age, email = get_user()  # Tuple unpacking
print(name)  # Alice

# Tuple as dictionary key (lists can't do this)
locations = {
    (0, 0): "origin",
    (1, 2): "point A"
}
```

**What this does:** Functions often return tuples for multiple values. Tuples can be dictionary keys because they're immutable (hashable). Tuple unpacking extracts values directly into variables.

### Example 3: Edge Case

```python
# Single-item tuple requires trailing comma
not_a_tuple = (5)      # Just an int: 5
is_a_tuple = (5,)      # Tuple with one item: (5,)

# Empty tuple
empty = ()
print(len(empty))      # 0

# Tuples are immutable
point = (1, 2)
# point[0] = 5  # TypeError: 'tuple' object does not support item assignment
```

**What this shows:** Single-item tuples need a trailing comma to distinguish from parentheses used for grouping. Tuples cannot be modified—attempting to change an item raises TypeError.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Immutable Sequence)

**Similar terms in this pattern:**

1. `list` - Mutable ordered sequence (can be changed)
2. `set` - Mutable unordered collection (no duplicates)
3. `frozenset` - Immutable version of set

**Pattern rule:** Collection type constructors should use noun forms representing the data structure. These are type names that describe what kind of container they create.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `list` | lista | قائمة | 列表 | सूची |
| `set` | conjunto | مجموعة | 集合 | सेट |
| `tuple` | **tupla** | **صف** | **元组** | **टपल** |

---

## Etymology (Brief)

**English Origin:** Mathematics/Computer Science (modern invention)

**Root meaning:** From mathematics: "tuple" is a generalization of "double," "triple," "quadruple," etc. An n-tuple is an ordered collection of n elements. The word combines the ending of "quintuple, sextuple..." into a general term.

**Why Python uses this:** Mathematics and computer science needed a term for fixed-size ordered collections. "Tuple" (from "n-tuple") became standard. Python adopted this established mathematical/CS terminology for immutable sequences.

---

## Concept Explanation (Intermediate Level)

**What it does:**

A tuple is an immutable sequence type in Python that stores an ordered collection of items. Once created, a tuple's contents cannot be changed—you cannot add, remove, or modify elements. This immutability makes tuples hashable (usable as dictionary keys or set elements) and slightly more memory-efficient than lists.

Tuples are created with comma-separated values, optionally enclosed in parentheses: `(1, 2, 3)` or just `1, 2, 3`. In practice, parentheses are usually included for clarity except in contexts like function returns or multiple assignment where commas create implicit tuples.

Tuples support all sequence operations except those that modify the sequence: indexing, slicing, iteration, membership testing (`in`), and concatenation. They're commonly used for fixed collections (RGB colors, coordinates), multiple function returns, and as immutable alternatives to lists when you want to prevent modification.

**Key behaviors:**

1. **Immutability:** Once created, tuples cannot be modified. This makes them safe to use as dictionary keys and in sets. Immutability also provides a guarantee: if you pass a tuple to a function, it cannot change your data.

2. **Ordered sequence:** Like lists, tuples maintain insertion order and support integer indexing. `tuple[0]` gets first item, `tuple[-1]` gets last. Slicing works identically to lists: `tuple[1:3]`.

3. **Heterogeneous:** Tuples can contain items of different types: `("Alice", 25, True)`. Often used to group related but different types of data (like a database row or function return values).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (represents a data structure type)
- **Action vs State:** STATE - describes what kind of object it is
- **Temporal aspect:** Instantaneous - creates the tuple object immediately

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun (technical term) | "tupla" - mathematical term |
| Germanic (de, nl, sv) | Noun | "Tupel" - borrowed from mathematics |
| Slavic (ru, pl, uk) | Noun | "кортеж" - established CS term |
| Arabic | Noun | "صف" (row/tuple) or transliterate |
| Chinese | Noun compound | "元组" - element-group |
| Hindi | Transliterated noun | "टपल" - borrowed term |

**Primary recommendation:** This is a specialized mathematical/CS term. Many languages either:

1. Use a cognate/loan word from mathematics ("tupla", "Tupel", "tuple")
2. Create a compound describing "ordered group" or "fixed sequence"
3. Transliterate if no native equivalent exists

**Forms to AVOID:**

- ❌ Using "pair" or "double" (tuple can have any number of items)
- ❌ Using generic "group" without indicating ordered/fixed nature
- ❌ Translating as "immutable list" (too verbose for a type name)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `tupla`
- **Form:** Noun (feminine)
- **Why it works:** Established Spanish mathematical term. Used in Spanish computer science education and Python documentation. Clear, concise, recognized by Spanish-speaking programmers.

**Arabic:**

- **Translation:** `صف` (ṣaff - row/rank/tuple)
- **Form:** Noun (masculine)
- **Why it works:** Arabic word for ordered row or rank. Used in mathematics and can represent ordered sequences. Concise alternative to longer descriptive phrases. Alternative: `مجموعة مرتبة` (ordered group) but too long.

**Chinese:**

- **Translation:** `元组` (yuánzǔ)
- **Form:** Noun compound
- **Why it works:** Two characters: 元 (element/primary) + 组 (group). Standard Chinese CS term for tuple. Used consistently in Chinese Python documentation and education. Clear and concise.

**Hindi:**

- **Translation:** `टपल` (ṭapal)
- **Form:** Transliterated noun
- **Why it works:** Direct transliteration of "tuple." Used in Hindi CS education as a borrowed technical term. No native Hindi equivalent exists for this specific CS concept, so borrowing is appropriate.

### ❌ Common Translation Mistakes

**Mistake 1: Using "pair" or "double"**

- **Wrong:** `pareja` (Spanish - "pair")
- **Why wrong:** Tuples can have any number of elements (1, 2, 3, or more), not just two. "Pair" incorrectly suggests always having exactly two items.
- **Right:** `tupla` (n-tuple, any number of items)

**Mistake 2: Overly descriptive phrase**

- **Wrong:** `lista inmutable` (Spanish - "immutable list")
- **Why wrong:** Too verbose for a type name. While technically descriptive, Python uses concise type names. "Tuple" is a specific type, not just "immutable list."
- **Right:** `tupla` (concise technical term)

**Mistake 3: Generic "group" without specificity**

- **Wrong:** `grupo` (Spanish - "group")
- **Why wrong:** Too generic—doesn't convey ordered or immutable nature. Sets and lists are also "groups" but behave differently. Need specific technical term.
- **Right:** `tupla` (specific ordered immutable sequence)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (in modern usage)

"Tuple" is a technical term invented for mathematics and computer science. It doesn't have colloquial meanings outside of technical contexts.

**Note:** The term comes from mathematical notation (2-tuple, 3-tuple, n-tuple) representing ordered collections of n elements. This meaning is consistent across all technical uses.

**Your translation should represent: an ordered, immutable sequence of elements—the mathematical and CS concept of an n-tuple.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `tuple`, check these translations:**

- [ ] `list` - Related sequence type (mutable version); should use compatible noun
- [ ] `set` - Related collection type; should use noun form
- [ ] `dict` - Related collection type; should use noun form
- [ ] `frozenset` - Related immutable type; should align in immutability concept

**Consistency rule:**

All collection/sequence types (`list`, `tuple`, `set`, `dict`, `frozenset`) must be nouns representing data structures. If you translate one as a noun, translate all as nouns.

**Example:**

Spanish: `lista`, `tupla`, `conjunto`, `diccionario` - all nouns ✅
NOT: `lista` (noun) + `crear_tupla` (verb phrase) ❌

### Functional relationships

**This term works WITH:**

1. **Tuple unpacking**: Extracting values into variables

```python
x, y, z = (1, 2, 3)
name, age = ("Alice", 30)
```

2. **Function returns**: Returning multiple values

```python
def get_stats():
    return min_val, max_val, avg
```

**Common pairing:**

```python
# Creating tuples
point = (10, 20)
rgb = (255, 128, 0)
person = ("Alice", 25, "Engineer")

# Tuple unpacking
x, y = point
first, *rest = (1, 2, 3, 4)  # first=1, rest=[2,3,4]

# As dictionary keys
positions = {
    (0, 0): "origin",
    (1, 1): "diagonal"
}

# Multiple return values
def divide_with_remainder(a, b):
    return a // b, a % b

quotient, remainder = divide_with_remainder(17, 5)

# Tuple methods (only 2)
numbers = (1, 2, 2, 3, 2)
numbers.count(2)  # 3
numbers.index(3)  # 3

# Converting between types
my_list = [1, 2, 3]
my_tuple = tuple(my_list)  # (1, 2, 3)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Established mathematical/CS term
- Most languages have adopted the term or created standard equivalent
- Clear technical concept
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Tuple" is a well-established term in mathematics and computer science education globally. Most languages either use a cognate (tupla, Tupel), transliterate it, or have developed a standard technical term. The concept is taught consistently across educational systems.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Some languages may need to decide between loan word/transliteration vs. native descriptive term. Follow established usage in target language's CS education.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ORDERED IMMUTABLE SEQUENCE concept?
- [ ] Would a native speaker recognize this as a data structure type?
- [ ] Distinguishes from mutable sequences (lists)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun for type name)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other collection types (`list`, `set`, `dict`)?
- [ ] Uses noun form like other type constructors?
- [ ] Aligns with CS education terminology in target language?

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
term: tuple
language: es
translation: tupla
form: noun (feminine)
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "tupla" is the established mathematical and computer science term for tuples. It's used consistently in Spanish Python documentation, CS education, and programming discussions. The term is a cognate that Spanish speakers in technical fields immediately recognize.

**Alternatives considered:**

1. `tuple` (English loan) - Some Spanish programmers use English term, but "tupla" is standard
2. `pareja` (pair) - Wrong: implies exactly 2 items, tuples can have any number
3. `secuencia inmutable` (immutable sequence) - Too verbose for a type name

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Tupla" is the standard term across Spanish-speaking technical communities and educational materials.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
