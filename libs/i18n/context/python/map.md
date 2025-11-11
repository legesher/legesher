# Python Builtin Function: `map` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `map()` function in Python applies a given function to each item in an iterable (list, tuple, etc.) and returns an iterator of the results. It's a functional programming tool for transforming sequences without explicit loops, making code more concise and expressive.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Apply function to each element
numbers = [1, 2, 3, 4]
squared = map(lambda x: x ** 2, numbers)
print(list(squared))  # Output: [1, 4, 9, 16]
```

**What this does:** `map()` takes a function (here `lambda x: x ** 2`) and applies it to each element in `numbers`. Returns an iterator that yields squared values. Converting to list shows all results.

### Example 2: Common Pattern

```python
# Using built-in function with map
strings = ["1", "2", "3", "4"]
integers = list(map(int, strings))
print(integers)  # Output: [1, 2, 3, 4]

# Map with multiple iterables
nums1 = [1, 2, 3]
nums2 = [10, 20, 30]
sums = list(map(lambda x, y: x + y, nums1, nums2))
print(sums)  # Output: [11, 22, 33]
```

**What this does:** First example uses built-in `int()` function to convert strings to integers. Second example shows `map()` with multiple iterables - function receives one argument from each iterable per call.

### Example 3: Edge Case

```python
# Map stops at shortest iterable
list1 = [1, 2, 3, 4, 5]
list2 = [10, 20]
result = list(map(lambda x, y: x + y, list1, list2))
print(result)  # Output: [11, 22] (stops after list2 exhausted)

# Map returns iterator (lazy evaluation)
big_range = range(1000000)
mapped = map(lambda x: x * 2, big_range)  # No computation yet
# Computation happens only when you iterate
```

**What this shows:** With multiple iterables, `map()` stops when the shortest one is exhausted. `map()` returns an iterator, not a list, enabling lazy evaluation for memory efficiency with large datasets.

---

## Pattern Classification

**This term is:** HIGHER-ORDER FUNCTION (Functional Programming)

**Similar terms in this pattern:**

1. `filter` - Selects elements matching condition (functional filtering)
2. `reduce` - Combines elements into single value (functional aggregation)
3. `sorted` - Transforms sequence order (functional transformation)

**Pattern rule:** Functional programming operations should use verb forms that describe the transformation pattern. "Map" means applying a transformation across all elements, creating a one-to-one mapping.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `filter` | filtrar | تصفية | 过滤 | फ़िल्टर |
| `reduce` | reducir | اختزال | 归约 | न्यूनीकरण |
| `map` | **mapear** | **تعيين** | **映射** | **मैप** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** From Medieval Latin "mappa" (cloth, map), extended to mean "mapping" in mathematics - establishing correspondence between sets. In functional programming, "map" means applying a function to establish correspondence between input and output sequences.

**Why Python uses this:** In mathematics and functional programming, "map" is the standard term for applying a function to each element of a collection. Borrowed from functional languages like Lisp and Haskell. The term captures the mathematical concept of mapping elements from one domain to another.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `map()` function implements the map operation from functional programming. It takes a function and one or more iterables, applies the function to corresponding elements, and returns an iterator yielding the results. This provides a declarative way to transform sequences without writing explicit loops.

`map(function, iterable1, iterable2, ...)` calls `function(item1, item2, ...)` for each group of items from the iterables. With one iterable, it's a simple element-wise transformation. With multiple iterables, the function receives one element from each, and mapping stops when the shortest iterable is exhausted.

The return value is a map iterator object (lazy evaluation), not a list. Computation happens only when you iterate, making `map()` memory-efficient for large or infinite sequences. Convert to list with `list(map(...))` when you need all results at once. In modern Python, list comprehensions often provide more readable alternatives, but `map()` remains useful for applying existing functions.

**Key behaviors:**

1. **Returns iterator:** `map()` returns an iterator, not a list. This enables lazy evaluation - transformations happen on-demand as you iterate. Memory-efficient for large datasets. Convert with `list()`, `tuple()`, etc. when needed.

2. **One-to-one mapping:** Each input element produces exactly one output element. Function is called once per element group. Output length equals input length (or shortest input if multiple iterables).

3. **Accepts multiple iterables:** `map(func, iter1, iter2)` passes one element from each iterable to function. Stops when any iterable is exhausted. Useful for element-wise operations on parallel sequences.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (action of applying function)
- **Action vs State:** ACTION - performs transformation across sequence
- **Temporal aspect:** Continuous/iterative - applies to each element

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "mapear" - to map/establish correspondence |
| Germanic (de, nl, sv) | Infinitive verb | "abbilden" - to map/transform |
| Slavic (ru, pl, uk) | Infinitive verb | "отображать" - to map |
| Arabic | Verbal noun (masdar) | "تعيين" - mapping/assignment |
| Chinese | Verb compound | "映射" - mapping/projection |
| Hindi | Transliterated/verb | "मैप करना" - to map |

**Primary recommendation:** Use verb form meaning "to map" or "to apply transformation." This is an action that creates correspondence between input and output. In languages without established programming term for "map," consider transliteration (keeping "map") as it's a standard functional programming term.

**Forms to AVOID:**

- ❌ Using "transform" alone - too general, doesn't capture one-to-one correspondence
- ❌ Using "apply" alone - less specific than "map"
- ❌ Using noun "mapping" - function names should be verbs

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `mapear`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish verb for mapping operations. Borrowed from English "map" with Spanish infinitive ending. Widely used in Spanish programming and mathematics. Natural in "mapear una función" (map a function).

**Arabic:**

- **Translation:** `تعيين` (ta'yīn) or `خريطة` (kharīṭa)
- **Form:** Verbal noun
- **Why it works:** "تعيين" means assignment/mapping in mathematics and computing. Standard term in Arabic functional programming. "خريطة" literally means map but "تعيين" more technical for function mapping.

**Chinese:**

- **Translation:** `映射` (yìngshè)
- **Form:** Verb compound
- **Why it works:** Two characters: 映 (reflect/project) + 射 (shoot/emit). Standard Chinese mathematical term for mapping/function mapping. Used in Chinese CS education for map operations.

**Hindi:**

- **Translation:** `मैप` (maip) or `मैप करना` (maip karnā)
- **Form:** Transliterated/verb
- **Why it works:** "मैप" is transliteration of "map" (widely recognized in Indian tech). Adding "करना" makes it verb form. Alternative: "आच्छादन" (covering/mapping) but transliteration more common in programming.

### ❌ Common Translation Mistakes

**Mistake 1: Using "apply" or "apply function" instead of "map"**

- **Wrong:** `aplicar` (Spanish - "to apply")
- **Why wrong:** Too general. "Apply" doesn't capture the one-to-one correspondence concept. "Map" is specific functional programming term establishing mathematical mapping between sets.
- **Right:** `mapear` (to map - specific term)

**Mistake 2: Using "transform" without mapping concept**

- **Wrong:** `transformar` (Spanish - "to transform")
- **Why wrong:** "Transform" is generic change. "Map" specifically means applying function to each element, creating correspondence. Technical precision matters.
- **Right:** `mapear` (to map - functional programming term)

**Mistake 3: Using noun instead of verb**

- **Wrong:** `mapeo` (Spanish noun - "mapping")
- **Why wrong:** Function names should be verbs (actions). "mapeo" is the noun (the result/concept), not the action of mapping.
- **Right:** `mapear` (verb form)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Geographic map" (physical representation)
- ✅ Meaning 2: **APPLY FUNCTION TO EACH ELEMENT** (mathematical mapping)
- ❌ Meaning 3: "Map out a plan" (plan/organize)

**Example:**

English "map" can mean:

1. "Road map of California" (geographic chart) ❌
2. "`map(func, list)` applies func to each element" (functional mapping) ✅ **This is the Python meaning**
3. "Map out the project" (plan strategy) ❌

**Your translation should capture meaning #2: applying a function across a sequence to establish element-wise correspondence.**

In mathematics and programming, "map" means establishing a correspondence between sets through a function. This is the technical meaning to capture.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `map`, check these translations:**

- [ ] `filter` - Similar functional programming operation; should use compatible verb form
- [ ] `sorted` - Sequence transformation function; should have similar pattern
- [ ] `list`/`tuple` - Type converters; `map` often used with these

**Consistency rule:**

Functional programming operations (`map`, `filter`, `reduce`) should use consistent verb forms. They're all higher-order functions that transform sequences, so grammatical parallelism is important.

**Example:**

If you translate `map` as infinitive ("mapear"), then:
- `filter` should also be infinitive ("filtrar")
- `reduce` should also be infinitive ("reducir")
- NOT: `map` infinitive + `filter` noun (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`map` + lambda**: Anonymous function transformation
```python
map(lambda x: x * 2, numbers)
```

2. **`map` + built-in functions**: Type conversion, operations
```python
map(int, strings)
map(str.upper, words)
```

**Common pairing:**

```python
# Basic transformation
numbers = [1, 2, 3, 4]
doubled = list(map(lambda x: x * 2, numbers))

# Type conversion
strings = ["1", "2", "3"]
integers = list(map(int, strings))

# Multiple iterables
a = [1, 2, 3]
b = [10, 20, 30]
combined = list(map(lambda x, y: x + y, a, b))

# With built-in functions
words = ["hello", "world"]
upper_words = list(map(str.upper, words))

# Modern alternative (list comprehension)
# Instead of: list(map(lambda x: x * 2, numbers))
# Can use: [x * 2 for x in numbers]
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to MEDIUM)

- Standard functional programming term with translations
- "Map" well-established in mathematics and CS
- Some languages may need transliteration
- **AI confidence should be HIGH to MEDIUM**

### Why LOW for `map`:

- "Map" is universal in functional programming
- Standard mathematical concept (function mapping)
- Well-known in programming education globally
- Some languages transliterate, others translate

**For this term:** LOW

**Rationale:** Mapping is a fundamental mathematical and programming concept. While "map" as a programming term might be transliterated in some languages (especially where English tech terms are common), most languages have established translations for this functional programming operation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Some languages may prefer transliteration of "map" (keeping the English term) if it's standard in that language's programming community. Check local CS education materials.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FUNCTION MAPPING concept (apply to each element)?
- [ ] Understood as functional transformation (not filtering)?
- [ ] Conveys one-to-one correspondence idea?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb for function action)?
- [ ] Correct form (infinitive for functional operation)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of `filter` and other functional operations?
- [ ] Uses infinitive verb like other transformations?
- [ ] Aligns with how mapping is discussed in target language math/CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard FP term)?

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
term: map
language: es
translation: mapear
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "mapear" is the standard verb for mapping operations in functional programming and mathematics. It's derived from English "map" with Spanish infinitive ending, widely recognized in Spanish programming communities. Consistent with other functional operations like "filtrar" (filter) and "reducir" (reduce).

**Alternatives considered:**

1. `aplicar` (to apply) - Too general; doesn't capture mapping correspondence concept
2. `transformar` (to transform) - Generic change; "mapear" more specific for FP
3. `map` (keep English) - Could work but "mapear" is established Spanish term

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Map is a well-established functional programming concept with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
