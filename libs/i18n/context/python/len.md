# Python Builtin Function: `len` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun/verb
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `len` function in Python returns the number of items in a container (list, string, dict, etc.). It's short for "length" and provides a consistent interface for measuring the size of sequences and collections.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get length of a list
numbers = [1, 2, 3, 4, 5]
count = len(numbers)
print(count)  # Output: 5
```

**What this does:** `len()` counts the elements in the list and returns that count as an integer. Works with any object that has a defined length.

### Example 2: Common Pattern

```python
# String length
message = "Hello, World!"
char_count = len(message)  # 13 characters (includes space and punctuation)

# Empty collection
empty_list = []
print(len(empty_list))  # Output: 0
```

**What this does:** Demonstrates `len()` works on strings (counts characters) and returns 0 for empty collections. Length is always a non-negative integer.

### Example 3: Edge Case

```python
# Dictionary length (counts key-value pairs)
person = {"name": "Alice", "age": 30, "city": "NYC"}
print(len(person))  # Output: 3 (three keys)

# Nested structures - only counts top level
nested = [[1, 2], [3, 4, 5], [6]]
print(len(nested))  # Output: 3 (three sublists, not total elements)
```

**What this shows:** For dictionaries, `len()` counts key-value pairs. For nested structures, it only counts top-level items. To count all nested elements, you'd need to iterate.

---

## Pattern Classification

**This term is:** QUERY FUNCTION (Measurement)

**Similar terms in this pattern:**

1. `min` - Returns smallest item (query/measurement)
2. `max` - Returns largest item (query/measurement)
3. `sum` - Returns total of items (query/aggregation)

**Pattern rule:** Query/measurement functions should use noun or verb forms that suggest obtaining information, not modifying data. "Length" is a property you measure/query.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `min` | mínimo | أدنى | 最小 | न्यूनतम |
| `max` | máximo | أقصى | 最大 | अधिकतम |
| `len` | **longitud** | **طول** | **长度** | **लंबाई** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "lengthu" meant "linear extent, distance." Related to "long." In computing, "length" extended to mean "number of items" in a collection, not just physical measurement.

**Why Python uses this:** "len" abbreviates "length," a natural word for measuring size. Most languages use "length," "size," or "count" for this concept. Python chose the abbreviation "len" for brevity (like "def" for "define") while remaining clear.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `len()` function returns the number of items in an object by calling the object's `__len__()` method. Any object that implements `__len__()` works with `len()`. This provides a uniform interface: whether it's a list, string, dict, or custom object, you use `len()` the same way.

For sequences (lists, strings, tuples), length is the number of elements. For mappings (dicts), it's the number of key-value pairs. For sets, it's the number of unique elements. The return value is always a non-negative integer.

Internally, `len()` doesn't iterate to count - most built-in types cache their length for O(1) constant-time access. This makes `len()` very fast even for large collections. Custom objects can implement `__len__()` to define their own length semantics.

**Key behaviors:**

1. **Calls __len__ method:** `len(obj)` is equivalent to `obj.__len__()`. Objects without `__len__()` raise `TypeError`. This makes `len()` part of Python's protocol-based design.

2. **Returns integer:** Always returns `int` type, never `float` or `None`. Empty collections return 0. There's no maximum limit (Python ints are unbounded).

3. **Top-level only:** For nested structures, `len()` counts only the immediate children, not recursive total. `len([[1,2],[3]])` is 2, not 3.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (property being measured)
- **Action vs State:** STATE/PROPERTY - describes an attribute of the object
- **Temporal aspect:** Instantaneous - measures current state

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "longitud", "longueur" - length as property |
| Germanic (de, nl, sv) | Noun | "Länge", "lengte" - length/size |
| Slavic (ru, pl, uk) | Noun | "длина", "długość" - length |
| Arabic | Noun | "طول" - length/longness |
| Chinese | Noun compound | "长度" - length/extent |
| Hindi | Noun | "लंबाई" - length |

**Primary recommendation:** Use noun form meaning "length" or "size." This is a measurement property, not an action. Abbreviate if your language commonly abbreviates technical terms, otherwise use full word.

**Forms to AVOID:**

- ❌ Using verb "to measure" - `len` names the property, not the action
- ❌ Using "count" for sequences - while related, "length" is more precise
- ❌ Using "size" when "length" is more specific - depends on language

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `longitud` or `lon`
- **Form:** Noun
- **Why it works:** "Longitud" means length/extent in Spanish. Could abbreviate to "lon" following Python's abbreviation pattern. Natural in "obtener la longitud" (get the length). Standard in Spanish math/CS.

**Arabic:**

- **Translation:** `طول` (ṭūl)
- **Form:** Noun
- **Why it works:** Standard Arabic word for length/height. Concise (one word). Clear meaning in measurement contexts. Used in Arabic mathematics and technical writing.

**Chinese:**

- **Translation:** `长度` (chángdù)
- **Form:** Noun compound
- **Why it works:** Two characters: 长 (long/length) + 度 (degree/measure). Standard Chinese term for length in physics, mathematics, and programming. Universally recognized.

**Hindi:**

- **Translation:** `लंबाई` (lambaī)
- **Form:** Noun
- **Why it works:** Standard Hindi word for length. Derived from "लंबा" (long). Natural in measurement contexts. Used in Hindi mathematics education.

### ❌ Common Translation Mistakes

**Mistake 1: Using verb "to measure" or "to count"**

- **Wrong:** `medir` (Spanish - "to measure")
- **Why wrong:** Function names should be nouns (properties/objects) or infinitive verbs. `len` refers to the length property itself, not the action of measuring.
- **Right:** `longitud` (the length property)

**Mistake 2: Using "size" when "length" is more specific**

- **Wrong:** `tamaño` (Spanish - "size")
- **Why wrong:** "Size" is more general (could mean area, volume). "Length" specifically means linear extent or count of items. More precise term is better.
- **Right:** `longitud` (specifically length)

**Mistake 3: Using only abbreviation without context**

- **Wrong:** `l` (Spanish - single letter)
- **Why wrong:** Too ambiguous. While Python uses "len" (recognizable English abbreviation), single letter in target language may not be clear. Use meaningful abbreviation or full word.
- **Right:** `lon` or `longitud` (clear abbreviation or full word)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (parent word "length")

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Physical distance/extent" (spatial measurement)
- ✅ Meaning 2: **NUMBER OF ITEMS** in a collection (count/cardinality)
- ⚠️ Meaning 3: "Duration" (time length)

**Example:**

English "length" can mean:

1. "The length of the table is 2 meters" (physical dimension) ❌
2. "`len([1,2,3])` returns 3" (count of items) ✅ **This is the Python meaning**
3. "The length of the movie is 2 hours" (duration) ❌

**Your translation should capture meaning #2: the count or number of items in a collection.**

In most languages, the same word covers both physical length and count-of-items (which is acceptable). Context makes the meaning clear.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `len`, check these translations:**

- [ ] `min`/`max` - Similar query functions; should use compatible forms
- [ ] `sum` - Aggregation function; should feel related
- [ ] `list`/`str` - Objects that have length; relationship should be clear

**Consistency rule:**

Query/measurement functions (`len`, `min`, `max`, `sum`) should use similar grammatical forms - either all nouns or all infinitive verbs. They're all read-only operations that return information.

**Example:**

Spanish: `longitud`, `mínimo`, `máximo`, `suma` - all nouns ✅
NOT: `longitud` (noun) + `obtener_mínimo` (verb phrase) ❌

### Functional relationships

**This term works WITH:**

1. **`len` + sequences**: Measure collection sizes
```python
print(len([1, 2, 3]))      # lists
print(len("hello"))        # strings
print(len((1, 2)))         # tuples
```

2. **`len` in conditionals**: Check if collection is empty
```python
if len(data) == 0:
    print("No data")
# Better: if not data:
```

**Common pairing:**

```python
# len with different types
items = [1, 2, 3]
print(len(items))          # 3

text = "Hello"
print(len(text))           # 5

mapping = {"a": 1, "b": 2}
print(len(mapping))        # 2

# len in loops
for i in range(len(items)):
    print(items[i])

# len for validation
if len(password) < 8:
    print("Password too short")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `len`:

- Universal concept (all languages measure length/count)
- "Length" is basic mathematical/physical term
- Well-established in programming globally
- Clear semantic mapping

**For this term:** EASY

**Rationale:** The concept of length or count is universal. Every language has words for measuring extent or counting items. Translation is straightforward: use the standard word for "length" in measurement contexts.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: whether to abbreviate like English "len" or use full word "length." Follow target language conventions for technical abbreviations.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LENGTH/COUNT concept (number of items)?
- [ ] Understood as measurement/query (not modification)?
- [ ] Applicable to collections (lists, strings, dicts)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun preferred for property)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other query functions (`min`, `max`)?
- [ ] Uses similar form as other measurement functions?
- [ ] Aligns with how length is discussed in target language math/CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common measurement term)?

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
term: len
language: es
translation: longitud
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "longitud" is the standard noun for length in mathematics, physics, and programming. It clearly captures the measurement concept. Could be abbreviated to "lon" following Python's pattern, but full word is more immediately recognizable.

**Alternatives considered:**

1. `tamaño` (size) - Too general; "longitud" more specific for count/length
2. `lon` (abbreviation) - Valid but less clear than full word
3. `largo` (long - adjective) - Wrong part of speech

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Length/count is a universal measurement concept with clear translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
