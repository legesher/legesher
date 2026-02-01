# Python Builtin Function: `filter` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `filter()` function in Python creates an iterator that yields only the elements from an iterable that satisfy a given condition (predicate function). It's a functional programming tool for selecting items that pass a test, making code more declarative and readable than manual loops.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Filter even numbers
numbers = [1, 2, 3, 4, 5, 6]
evens = filter(lambda x: x % 2 == 0, numbers)
print(list(evens))  # Output: [2, 4, 6]
```

**What this does:** `filter()` applies the lambda function to each element. Only elements where the function returns `True` are included in the result. Returns an iterator that yields filtered values.

### Example 2: Common Pattern

```python
# Filter with built-in function
values = [0, 1, False, 2, "", 3, None, 4]
truthy = list(filter(None, values))
print(truthy)  # Output: [1, 2, 3, 4]

# Filter strings by length
words = ["a", "hello", "hi", "wonderful", "ok"]
long_words = list(filter(lambda w: len(w) > 2, words))
print(long_words)  # Output: ['hello', 'wonderful']
```

**What this does:** Using `None` as the filter function tests for truthiness (filters out falsy values). Lambda functions can use any condition - here checking string length to select longer words.

### Example 3: Edge Case

```python
# Filter returns empty when no matches
numbers = [1, 3, 5, 7]
evens = list(filter(lambda x: x % 2 == 0, numbers))
print(evens)  # Output: []

# Filter is lazy (returns iterator)
huge_range = range(1000000)
filtered = filter(lambda x: x % 1000 == 0, huge_range)
# No computation yet - happens only when iterating
first_ten = list(itertools.islice(filtered, 10))
```

**What this shows:** `filter()` returns empty iterator when no elements satisfy the condition. Like `map()`, it returns an iterator for lazy evaluation, enabling memory-efficient filtering of large or infinite sequences.

---

## Pattern Classification

**This term is:** HIGHER-ORDER FUNCTION (Functional Programming - Selection)

**Similar terms in this pattern:**

1. `map` - Transforms all elements (functional transformation)
2. `reduce` - Combines elements into one value (functional aggregation)
3. `sorted` - Reorders elements (functional sorting)

**Pattern rule:** Functional programming operations should use verb forms describing their operation pattern. "Filter" means selecting elements that pass a test, removing those that don't.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `map` | mapear | تعيين | 映射 | मैप |
| `reduce` | reducir | اختزال | 归约 | न्यूनीकरण |
| `filter` | **filtrar** | **تصفية** | **过滤** | **फ़िल्टर** |

---

## Etymology (Brief)

**English Origin:** Latin via Medieval French

**Root meaning:** From Medieval Latin "filtrum" (felt used for straining), from Germanic "filtiz" (felt). Extended to mean separating wanted from unwanted elements by passing through a selective barrier.

**Why Python uses this:** "Filter" is the standard term in functional programming for selecting elements matching a predicate. Borrowed from languages like Lisp and Haskell. The metaphor of filtering (letting some things through, blocking others) perfectly captures the operation of conditional selection.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `filter()` function implements the filter operation from functional programming. It takes a predicate function (returns boolean) and an iterable, applies the predicate to each element, and returns an iterator yielding only elements where the predicate returned `True`. This provides a declarative way to select subset of elements without explicit loops.

`filter(function, iterable)` calls `function(item)` for each item. If the result is truthy, the item is included; otherwise, it's excluded. Special case: `filter(None, iterable)` uses identity test, filtering out falsy values (0, False, None, "", [], etc.).

The return value is a filter iterator object (lazy evaluation). Computation happens on-demand as you iterate, making `filter()` memory-efficient for large sequences. Convert to list with `list(filter(...))` when you need all results. In modern Python, list comprehensions with conditions often provide more readable alternatives, but `filter()` remains useful when you have an existing predicate function.

**Key behaviors:**

1. **Returns iterator:** `filter()` returns an iterator, not a list. Filtering happens lazily as you consume the iterator. Memory-efficient for large datasets. Convert with `list()`, `tuple()`, etc. when needed.

2. **Predicate testing:** Function should return boolean (or truthy/falsy value). `True` means include, `False` means exclude. Special case: `filter(None, ...)` filters out falsy values.

3. **Preserves order:** Filtered elements appear in same order as original iterable. `filter()` doesn't reorder, only selects. Output is subsequence of input maintaining relative positions.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (action of selecting/filtering)
- **Action vs State:** ACTION - performs selection based on condition
- **Temporal aspect:** Continuous/iterative - tests each element

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "filtrar", "filtrer" - to filter/select |
| Germanic (de, nl, sv) | Infinitive verb | "filtern" - to filter |
| Slavic (ru, pl, uk) | Infinitive verb | "фильтровать" - to filter |
| Arabic | Verbal noun (masdar) | "تصفية" - filtering/purification |
| Chinese | Verb compound | "过滤" - to filter/strain |
| Hindi | Transliterated/verb | "फ़िल्टर करना" - to filter |

**Primary recommendation:** Use verb form meaning "to filter" or "to select by condition." This is an action that separates wanted from unwanted elements. "Filter" is widely recognized as a technical term, so transliteration might be appropriate in some languages.

**Forms to AVOID:**

- ❌ Using "select" alone - less specific than "filter" (filter implies conditional selection)
- ❌ Using "separate" - too general, doesn't convey conditional testing
- ❌ Using noun "filtro" - function names should be verbs

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `filtrar`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish verb for filtering operations. Natural cognate from Latin "filtrum". Widely used in Spanish programming and technical contexts. Natural in "filtrar elementos" (filter elements).

**Arabic:**

- **Translation:** `تصفية` (taṣfiya)
- **Form:** Verbal noun (masdar)
- **Why it works:** Means "filtering/purification/refining" in Arabic. Standard term for filtering in computing. Captures both selection and removal aspects. Used in Arabic technical documentation.

**Chinese:**

- **Translation:** `过滤` (guòlǜ)
- **Form:** Verb compound
- **Why it works:** Two characters: 过 (pass through) + 滤 (filter/strain). Standard Chinese term for filtering in all contexts. Used in Chinese programming and engineering. Clear physical filtering metaphor.

**Hindi:**

- **Translation:** `फ़िल्टर` (filṭar) or `फ़िल्टर करना` (filṭar karnā)
- **Form:** Transliterated/verb
- **Why it works:** Transliteration of "filter" widely used in Indian tech and everyday language (air filter, water filter). Adding "करना" makes full verb form. Alternative: "छानना" (strain) but transliteration more standard in programming.

### ❌ Common Translation Mistakes

**Mistake 1: Using "select" without filtering concept**

- **Wrong:** `seleccionar` (Spanish - "to select")
- **Why wrong:** Too general. "Select" doesn't convey the conditional testing aspect. "Filter" specifically means selecting based on passing a test/condition.
- **Right:** `filtrar` (to filter - conditional selection)

**Mistake 2: Using "remove" instead of "filter"**

- **Wrong:** `remover` (Spanish - "to remove")
- **Why wrong:** Focuses on what's excluded rather than what's included. Filter emphasizes keeping matching elements, not removing non-matching ones. Conceptual opposite.
- **Right:** `filtrar` (to filter - keep matching elements)

**Mistake 3: Using noun instead of verb**

- **Wrong:** `filtro` (Spanish noun - "filter")
- **Why wrong:** Function names should be verbs (actions). "filtro" is the device/concept (noun), "filtrar" is the action of filtering.
- **Right:** `filtrar` (verb form)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Coffee filter" (physical strainer device)
- ✅ Meaning 2: **SELECT ELEMENTS MATCHING CONDITION** (conditional selection)
- ❌ Meaning 3: "Instagram filter" (visual effect/transformation)

**Example:**

English "filter" can mean:

1. "Buy coffee filters at the store" (physical device) ❌
2. "`filter(lambda x: x > 0, numbers)` keeps positive numbers" (conditional selection) ✅ **This is the Python meaning**
3. "Apply a sepia filter to the photo" (visual transformation) ❌

**Your translation should capture meaning #2: selecting only elements that satisfy a boolean condition.**

In programming, "filter" specifically means conditional selection based on a predicate function, not physical filtering or visual effects.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `filter`, check these translations:**

- [ ] `map` - Similar functional programming operation; should use compatible verb form
- [ ] `reduce` - Functional aggregation; should match grammatical pattern
- [ ] `sorted` - Sequence operation; should have similar style

**Consistency rule:**

Functional programming operations (`filter`, `map`, `reduce`) should use consistent verb forms. They're all higher-order functions operating on sequences, so grammatical parallelism is essential for learner comprehension.

**Example:**

If you translate `filter` as infinitive ("filtrar"), then:

- `map` should also be infinitive ("mapear")
- `reduce` should also be infinitive ("reducir")
- NOT: `filter` infinitive + `map` noun (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`filter` + lambda**: Conditional selection with anonymous function

```python
filter(lambda x: x > 0, numbers)
```

2. **`filter` + None**: Filter falsy values

```python
filter(None, values)  # Removes 0, False, None, "", [], etc.
```

**Common pairing:**

```python
# Basic filtering
numbers = [1, -2, 3, -4, 5, -6]
positives = list(filter(lambda x: x > 0, numbers))
# Output: [1, 3, 5]

# Filter with None (truthiness test)
mixed = [0, 1, False, 2, "", "hi", None, 3]
truthy = list(filter(None, mixed))
# Output: [1, 2, 'hi', 3]

# Filter strings
words = ["apple", "a", "banana", "hi", "wonderful"]
long_words = list(filter(lambda w: len(w) > 2, words))
# Output: ['apple', 'banana', 'wonderful']

# Combine filter and map
numbers = [1, 2, 3, 4, 5, 6]
# Square even numbers only
result = list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers)))
# Output: [4, 16, 36]

# Modern alternative (list comprehension)
# Instead of: list(filter(lambda x: x > 0, numbers))
# Can use: [x for x in numbers if x > 0]
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY)

- Clear concept with direct translations
- "Filter" is universal computing term
- Cognates exist in many languages
- **AI confidence should be HIGH**

### Why LOW for `filter`

- Filtering is universal concept (physical and computational)
- "Filter" widely adopted in technical vocabulary globally
- Clear metaphor from physical filtering
- Well-established in programming education

**For this term:** LOW

**Rationale:** Filtering is both a physical and computational concept understood worldwide. The term "filter" or its cognates appear in most languages' technical vocabulary. The key is using verb form (action of filtering) rather than noun form (the filter device).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Ensure translation conveys conditional selection (keeping matches) rather than removal (discarding non-matches), as filter emphasizes positive selection.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures CONDITIONAL SELECTION concept (keep matching elements)?
- [ ] Understood as predicate-based filtering (not physical filtering)?
- [ ] Conveys testing each element against condition?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb for function action)?
- [ ] Correct form (infinitive for functional operation)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of `map` and other functional operations?
- [ ] Uses infinitive verb like other transformations?
- [ ] Aligns with how filtering is discussed in target language CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common technical term)?

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
term: filter
language: es
translation: filtrar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "filtrar" is the standard verb for filtering operations in computing and engineering. It's a natural cognate from Latin that clearly captures conditional selection. Consistent with other functional operations like "mapear" (map) and "reducir" (reduce), maintaining grammatical parallelism.

**Alternatives considered:**

1. `seleccionar` (to select) - Too general; doesn't convey conditional/predicate aspect
2. `cribar` (to sift/screen) - Valid but "filtrar" more standard in computing
3. `filtro` (noun) - Wrong part of speech; should be verb

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Filtering is a universal concept with clear, established translations in technical contexts.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
