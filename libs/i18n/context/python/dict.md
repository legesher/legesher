# Python Builtin Type: `dict` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (type constructor)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `dict` type in Python represents a dictionary - an unordered collection of key-value pairs. It's short for "dictionary" and provides fast lookup: give it a key, get back the associated value. Dictionaries are mutable and one of Python's most powerful data structures.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create a dictionary
person = {"name": "Alice", "age": 30}
print(person["name"])  # Output: Alice
print(person["age"])   # Output: 30
```

**What this does:** Curly braces `{}` with `key: value` pairs create a dictionary. Access values by their keys using square brackets. Keys must be unique; if duplicated, last value wins.

### Example 2: Common Pattern

```python
# Mutable - can add/modify/delete
scores = {"Alice": 95, "Bob": 87}
scores["Charlie"] = 92   # Add new key-value pair
scores["Alice"] = 98     # Update existing value
del scores["Bob"]        # Remove key-value pair
print(scores)  # Output: {'Alice': 98, 'Charlie': 92}

# Check if key exists
if "Alice" in scores:
    print("Alice found")
```

**What this does:** Dictionaries are mutable - add new pairs, update values, delete pairs. Use `in` operator to check key existence. Attempting to access non-existent key raises `KeyError`.

### Example 3: Edge Case

```python
# Empty dictionary
empty = {}
also_empty = dict()

# Mixed value types (keys must be hashable)
data = {
    "name": "Alice",
    "age": 30,
    "scores": [95, 87, 92],
    ("x", "y"): "coordinate"  # tuple key OK
}

# Get with default (avoids KeyError)
value = data.get("missing", "default")  # Returns "default"
```

**What this shows:** Create empty dicts with `{}` or `dict()`. Values can be any type. Keys must be immutable/hashable (strings, numbers, tuples - not lists). `.get()` method provides safe access with default value.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR / MAPPING TYPE

**Similar terms in this pattern:**

1. `list` - Ordered collection (indexed by position)
2. `set` - Unordered collection of unique items
3. `tuple` - Immutable ordered collection

**Pattern rule:** Collection type constructors should use noun forms naming the container type. For `dict`, use the word for "dictionary" or "map" depending on language conventions.


---

## Etymology (Brief)

**English Origin:** Latin via Medieval Latin

**Root meaning:** Latin "dictio" meant "word, saying." Through Medieval Latin "dictionarium" (collection of words and phrases), it became English "dictionary" - a book of words with definitions. In programming, extended to data structures mapping keys to values (like words to definitions).

**Why Python uses this:** "Dictionary" is the perfect metaphor: just as a word dictionary maps words to definitions, a Python dict maps keys to values. Most languages call this "map," "hash," or "dictionary." Python abbreviated to "dict" for brevity while keeping the clear metaphor.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `dict` type represents a hash table - a mapping from keys to values. It provides O(1) average-case lookup time: given a key, retrieve its value instantly (regardless of dictionary size). Dictionaries maintain insertion order in Python 3.7+, though this is an implementation detail.

Keys must be hashable (immutable types: strings, numbers, tuples of immutables). Values can be any Python object. Each key appears once - adding a key that exists updates its value rather than creating a duplicate. Dictionaries are mutable: you can add, modify, and remove key-value pairs after creation.

Common operations include: access by key (`d[key]`), safe access (`.get(key, default)`), membership test (`key in d`), iteration (`.keys()`, `.values()`, `.items()`), and bulk operations (`.update()`, `.pop()`). Dictionaries excel at lookups, aggregation, and counting tasks.

**Key behaviors:**

1. **Key-value mapping:** Core concept is association. Each key maps to exactly one value. The key uniquely identifies the value. Like a phone book: name (key) → phone number (value).

2. **Fast lookup:** Hash table implementation provides O(1) average lookup time. Searching a million-item dict is as fast as searching a 10-item dict. This makes dicts ideal for caching, indexing, and counting.

3. **Mutable and dynamic:** Dictionaries grow as needed. Add unlimited key-value pairs. Modify values. Delete pairs. No pre-declaration of size required. Efficient for building up data incrementally.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (names a container type)
- **Action vs State:** STATE/CONTAINER - describes what holds data
- **Temporal aspect:** Timeless - a type is a permanent category

### Recommended Form

**Primary recommendation:** Use noun form meaning "dictionary" (the book of words and definitions). This maintains Python's metaphor. Alternative: use "map" or "mapping" if that's CS convention in your language, though "dictionary" is preferred.

**Forms to AVOID:**

- ❌ Using "hash" alone - too low-level, implementation detail
- ❌ Using "map" verb form - should be noun naming the container
- ❌ Using "association" - too abstract; "dictionary" is concrete

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (abbreviated form)

**"Dict" is unambiguous:**

"Dict" is clearly short for "dictionary." While "dictionary" can mean:

1. Book of words and definitions ✅ (metaphor source)
2. Data structure of key-value pairs ✅ (Python meaning)

Both meanings are related - the programming term borrows the metaphor from the book. Your translation should use the word for dictionary (book), which naturally extends to the data structure.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `dict`, check these translations:**

- [ ] `list`/`tuple`/`set` - Other collection types; should use similar noun forms
- [ ] `keys`/`values`/`items` - Dictionary methods; should feel related
- [ ] `hash` - Related concept; avoid confusion with dict itself

**Consistency rule:**

All collection type constructors (`dict`, `list`, `tuple`, `set`) should use noun forms. They name data structures, not actions.


### Functional relationships

**This term works WITH:**

1. **`dict` + key access**: Lookup values

```python
data = {"name": "Alice", "age": 30}
print(data["name"])
data["city"] = "NYC"
```

2. **`dict` + methods**: Manipulate mappings

```python
person = {"name": "Alice"}
person.update({"age": 30, "city": "NYC"})
keys = person.keys()
values = person.values()
```

**Common pairing:**

```python
# dict creation
config = {"debug": True, "port": 8080}
empty = {}
from_pairs = dict([("a", 1), ("b", 2)])

# dict access
value = config["debug"]
safe = config.get("missing", "default")

# dict methods
config["new_key"] = "value"
config.update({"key": "val"})
config.pop("debug")

# dict iteration
for key in config:
    print(key, config[key])

for key, value in config.items():
    print(f"{key}: {value}")

# dict comprehension
squares = {x: x**2 for x in range(5)}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `dict`

- Universal concept (dictionaries exist in all languages)
- "Dictionary" book metaphor is universal
- Well-established in programming globally
- Clear semantic mapping from book to data structure

**For this term:** EASY

**Rationale:** The concept of a dictionary (book mapping words to definitions) exists in all literate cultures. The programming metaphor (mapping keys to values) is intuitive and universally adopted. Translation is straightforward: use the word for dictionary (book).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: some languages' CS education might use "map" instead of "dictionary." Check conventions, but "dictionary" is generally preferred for maintaining Python's metaphor.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures KEY-VALUE MAPPING concept?
- [ ] Understood as dictionary metaphor (key → value like word → definition)?
- [ ] Distinct from list (indexed by position) and set (unique items)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other collection types (`list`, `tuple`, `set`)?
- [ ] All collection types use noun forms?
- [ ] Aligns with how dictionaries are discussed in target language CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word from dictionary book)?

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
term: dict
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
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
