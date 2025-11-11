# Python Builtin Function: `min` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (comparison/aggregation)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `min` function in Python returns the smallest item from an iterable or the smallest of two or more arguments. Works with numbers, strings, or any objects that support comparison operators. Can accept a key function for custom comparison logic.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Find minimum of multiple arguments
smallest = min(5, 2, 9, 1, 7)
print(smallest)  # Output: 1

# Find minimum in a list
numbers = [10, 3, 7, 1, 9]
result = min(numbers)
print(result)  # Output: 1
```

**What this does:** `min()` can take multiple arguments or a single iterable. Returns the smallest value using natural ordering (numeric comparison for numbers).

### Example 2: Common Pattern

```python
# String comparison (lexicographic order)
words = ["zebra", "apple", "mango", "banana"]
first_word = min(words)
print(first_word)  # Output: "apple" (alphabetically first)

# With key function (custom comparison)
names = ["Alice", "Bob", "Charlotte", "Dan"]
shortest_name = min(names, key=len)
print(shortest_name)  # Output: "Bob" (shortest length)
```

**What this does:** Works with any comparable types. Strings compare lexicographically (dictionary order). Key parameter transforms elements before comparison - compares `len(name)` values but returns original name.

### Example 3: Edge Case

```python
# Empty iterable with default
# min([])  # ValueError: min() arg is an empty sequence
result = min([], default="N/A")
print(result)  # Output: "N/A"

# Mixed types cause TypeError
# min(5, "hello")  # TypeError: '<' not supported

# Tuples compare element-by-element
pairs = [(2, 'b'), (1, 'c'), (2, 'a')]
smallest = min(pairs)
print(smallest)  # Output: (1, 'c') - compares first element, then second
```

**What this shows:** Empty iterables raise ValueError unless `default` provided. Can't compare incompatible types. Tuples/lists compare lexicographically (first element, then second if tied, etc.).

---

## Pattern Classification

**This term is:** COMPARISON FUNCTION (Selection/Aggregation)

**Similar terms in this pattern:**

1. `max` - Returns largest item (opposite of min)
2. `sorted` - Orders all items (uses same comparison logic)
3. `sum` - Aggregation function (different operation)

**Pattern rule:** Comparison/selection functions should use adjective forms describing the superlative property. "Minimum" = smallest/lowest.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `max` | máximo | أقصى | 最大 | अधिकतम |
| `sum` | suma | مجموع | 总和 | योग |
| `min` | **mínimo** | **أدنى** | **最小** | **न्यूनतम** |

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "minimus" (smallest, least), superlative of "minor" (smaller). Related to "minus" (less) and "minimum" (the least possible). In mathematics, "minimum" means the smallest value in a set.

**Why Python uses this:** "Min" abbreviates "minimum," the universal mathematical term for smallest value. Like "max" (maximum) and "def" (define), Python favors concise abbreviations of clear technical terms. "Minimum" is recognized globally in math and CS.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `min()` function finds and returns the smallest element from a collection using Python's comparison operators. It can work two ways: (1) multiple arguments `min(a, b, c)` returns smallest argument, or (2) single iterable `min([a, b, c])` returns smallest element.

Internally, `min()` iterates through all elements once (O(n) time complexity), maintaining the current minimum. It uses the `<` operator (or `__lt__()` method) to compare elements. Any objects implementing comparison methods can work with `min()`.

The optional `key` parameter accepts a function that transforms each element before comparison. For example, `min(words, key=len)` compares lengths but returns the original word. The `default` parameter (Python 3.4+) provides a fallback value for empty iterables, preventing ValueError.

**Key behaviors:**

1. **Comparison-based:** Uses `<` operator. Objects must be orderable (comparable). Mixing incompatible types (like int and str) raises TypeError. Custom objects need `__lt__()` method implementation.

2. **Returns original element:** Even with `key` function, returns the actual element (not the key value). `min([3, 1, 4], key=lambda x: -x)` returns 4 (largest number, smallest -x value).

3. **Multiple arguments or iterable:** `min(1, 2, 3)` and `min([1, 2, 3])` both work. For iterables, unpacking with `*` works: `min(*my_list)`. Can't mix: `min(1, [2, 3])` compares int to list (usually TypeError).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective (superlative) used as noun
- **Action vs State:** STATE/PROPERTY - describes the smallest
- **Temporal aspect:** Result of comparison

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Superlative adjective/noun | "mínimo", "minimum" - smallest |
| Germanic (de, nl, sv) | Superlative noun | "Minimum", "minimum" - smallest |
| Slavic (ru, pl, uk) | Superlative adjective | "минимум", "minimum" - smallest |
| Arabic | Superlative adjective | "أدنى" - lowest/smallest |
| Chinese | Superlative compound | "最小" - most small |
| Hindi | Superlative adjective | "न्यूनतम", "लघुतम" - smallest |

**Primary recommendation:** Use superlative form meaning "smallest" or "minimum." This is a mathematical superlative - the least value in a set.

**Forms to AVOID:**

- ❌ Using comparative "smaller" - want superlative "smallest"
- ❌ Using verb "minimize" - function returns value, doesn't optimize
- ❌ Using "less" - that's comparative, not superlative

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `mínimo`
- **Form:** Superlative adjective/noun (masculine)
- **Why it works:** Standard Spanish mathematical term for minimum/smallest. Natural in "el mínimo valor" (the minimum value). Universally used in Spanish mathematics and statistics.

**Arabic:**

- **Translation:** `أدنى` (adnā)
- **Form:** Elative/superlative adjective
- **Why it works:** Standard Arabic word for lowest/smallest/minimum. Used in Arabic mathematics and statistics. Clear superlative meaning. Pairs naturally with `أقصى` (maximum).

**Chinese:**

- **Translation:** `最小` (zuìxiǎo)
- **Form:** Superlative compound
- **Why it works:** Two characters: 最 (most/superlative marker) + 小 (small). Standard Chinese mathematical term for minimum. Clear, concise, universally recognized. Pairs with 最大 (maximum).

**Hindi:**

- **Translation:** `न्यूनतम` (nyūnatam) or `लघुतम` (laghutam)
- **Form:** Superlative adjective
- **Why it works:** `न्यूनतम` from Sanskrit "न्यून" (less) + "तम" (superlative suffix). Standard in Hindi mathematics. `लघुतम` (smallest) also valid. `न्यूनतम` more common in technical contexts.

### ❌ Common Translation Mistakes

**Mistake 1: Using comparative "menor" instead of superlative "mínimo"**

- **Wrong:** `menor` (Spanish - "smaller/less" - comparative)
- **Why wrong:** "Menor" compares two things (A is smaller than B). "Mínimo" is superlative (the smallest of all). `min()` finds the absolute smallest, not just smaller.
- **Right:** `mínimo` (smallest/minimum - superlative)

**Mistake 2: Using verb "minimizar" (minimize)**

- **Wrong:** `minimizar` (Spanish - "to minimize" - verb)
- **Why wrong:** "Minimizar" means to make smaller/reduce. `min()` doesn't modify anything - it selects/returns the already-smallest value. Different concept.
- **Right:** `mínimo` (the minimum - noun/adjective)

**Mistake 3: Using "pequeño" (small) without superlative**

- **Wrong:** `pequeño` (Spanish - "small" - positive adjective)
- **Why wrong:** "Pequeño" means small, but not smallest. Need superlative "el más pequeño" or better, mathematical term "mínimo."
- **Right:** `mínimo` (minimum/smallest - superlative)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Minimum" as required amount ("minimum wage")
- ✅ Meaning 2: **SMALLEST VALUE** in a set (mathematical minimum)
- ❌ Meaning 3: "Minimal" meaning barely adequate

**Example:**

English "minimum" can mean:

1. "You need minimum 8 hours sleep" (required amount) ❌
2. "`min([3, 1, 4])` returns 1" (smallest value) ✅ **This is the Python meaning**
3. "Minimum effort" (barely adequate) ❌

**Your translation should capture meaning #2: the smallest/lowest value in a collection.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `min`, check these translations:**

- [ ] `max` - Logical opposite; MUST use parallel superlative forms
- [ ] `sum` - Aggregation function; should use compatible pattern
- [ ] `sorted` - Uses same comparison logic
- [ ] `<`, `>` operators - Comparison operators used by min/max

**Consistency rule:**

`min` and `max` MUST be translated as grammatical opposites using the same superlative pattern. They're complementary functions.

**Example:**

Spanish: `mínimo` (minimum), `máximo` (maximum) - both superlatives ✅
NOT: `mínimo` (superlative) + `más_grande` (comparative phrase) ❌

### Functional relationships

**This term works WITH:**

1. **`min` with comparables**: Find smallest
```python
min(5, 2, 8)  # 2
min("zebra", "apple", "mango")  # "apple"
```

2. **`min` with key function**: Custom comparison
```python
min(names, key=len)  # shortest name
min(points, key=lambda p: p.distance())
```

**Common pairing:**

```python
# Basic usage
numbers = [10, 3, 7, 1, 9]
smallest = min(numbers)  # 1

# Multiple arguments
minimum = min(5, 2, 8, 3)  # 2

# With strings
first_word = min(["zebra", "apple", "mango"])  # "apple"

# With key function
words = ["python", "is", "awesome"]
shortest = min(words, key=len)  # "is"

# With default (empty iterable)
result = min([], default=0)  # 0 (no ValueError)

# Tuples (lexicographic comparison)
min([(2, 'a'), (1, 'b'), (2, 'c')])  # (1, 'b')

# Find minimum by property
students = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 20}]
youngest = min(students, key=lambda s: s["age"])  # Bob

# Compare with max
numbers = [1, 5, 3, 9, 2]
range_span = max(numbers) - min(numbers)  # 9 - 1 = 8
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `min`:

- Universal mathematical concept (smallest/minimum)
- Standard term in mathematics globally
- Clear superlative form in most languages
- Well-established in programming

**For this term:** EASY

**Rationale:** The concept of minimum (smallest value) is universal across all mathematical traditions. Every language has superlative forms for "smallest" or mathematical term "minimum." Translation is straightforward: use the superlative or mathematical minimum term.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Ensure you use superlative (smallest) not comparative (smaller), and pair with `max` using parallel grammatical forms.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MINIMUM/SMALLEST concept?
- [ ] Understood as selection (not modification)?
- [ ] Distinguished from comparative "smaller"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (superlative adjective/noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Parallel form with `max` translation?
- [ ] Matches pattern of comparison functions?
- [ ] Aligns with mathematical terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard math term)?

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
term: min
language: es
translation: mínimo
form: superlative_adjective_as_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "mínimo" is the standard mathematical term for minimum/smallest value. It's a superlative adjective used as a noun in technical contexts. Pairs naturally with "máximo" and is universally taught in Spanish mathematics.

**Alternatives considered:**

1. `menor` (smaller) - Comparative, not superlative; wrong degree
2. `pequeño` (small) - Positive adjective, not superlative
3. `minimizar` (minimize - verb) - Wrong concept; that means to reduce

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Minimum is a universal mathematical concept with clear, standard translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
