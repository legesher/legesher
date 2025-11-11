# Python Keyword: `is` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** operator (identity test)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `is` keyword is an identity test operator in Python that checks whether two variables refer to the same object in memory (same identity), not whether they have equal values. It returns `True` if both operands are the same object, `False` otherwise. This is different from `==` which checks value equality.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Identity test with None
x = None
print(x is None)      # True (x refers to None singleton)

# Identity vs equality
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)         # True (equal values)
print(a is b)         # False (different objects)
```

**What this does:** `is` checks if two variables point to the exact same object in memory. Different from `==` which checks if values are equal. Objects can be equal (`==`) without being identical (`is`).

### Example 2: Common Pattern

```python
# Check for None (idiomatic)
if value is None:
    print("No value provided")

# Check for True/False singletons
if flag is True:
    print("Explicitly True")

# Negation with is not
if result is not None:
    process(result)

# Identity with small integers (cached)
x = 5
y = 5
print(x is y)         # True (small ints cached)
```

**What this does:** `is None` is the idiomatic way to check for None in Python (preferred over `== None`). Works with singleton objects like `None`, `True`, `False`. Can negate with `is not`. Small integers may be cached by Python.

### Example 3: Edge Case

```python
# String interning (unexpected identity)
s1 = "hello"
s2 = "hello"
print(s1 is s2)       # True (strings may be interned)

# Large integers not cached
x = 1000
y = 1000
print(x is y)         # False (large ints not cached)
print(x == y)         # True (values equal)

# List identity
list1 = [1, 2, 3]
list2 = list1         # Same reference
list3 = [1, 2, 3]     # Different object
print(list1 is list2) # True (same object)
print(list1 is list3) # False (different objects)
print(list1 == list3) # True (equal values)
```

**What this shows:** Python caches small integers (-5 to 256) and may intern strings, making `is` return `True` unexpectedly. For large numbers or mutable objects, different variables are different objects even with equal values. `is` checks memory identity, `==` checks value equality.

---

## Pattern Classification

**This term is:** IDENTITY OPERATOR / COMPARISON KEYWORD

**Similar terms in this pattern:**

1. `is not` - Negative identity test
2. `==` - Equality operator (value comparison, different from identity)
3. `!=` - Inequality operator (value comparison)

**Pattern rule:** Identity operators should use copula or verb forms that express "being" or "sameness." "Is" expresses identity - being the exact same thing.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `==` | == | == | == | == |
| `!=` | != | != | != | != |
| `is` | **es** | **هو** | **是** | **है** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "is" from Proto-Germanic "isti" (is), from Proto-Indo-European "esti." Third-person singular present form of "to be." Expresses existence, identity, or equivalence. Most fundamental verb across Indo-European languages.

**Why Python uses this:** "Is" is the natural English verb for identity. Reading "x is y" aligns with English grammar. Python distinguishes identity (`is`) from equality (`==`) - "x is y" asks "are they the same thing?" while "x == y" asks "do they have the same value?" Borrowed from natural language where "is" expresses identity.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `is` operator performs identity testing - it checks whether two variables refer to the same object in memory. Python assigns every object a unique `id()` value (memory address). `x is y` returns `True` if `id(x) == id(y)`, meaning both variables point to the exact same object.

This is fundamentally different from `==` (equality operator). Two objects can have equal values (`==` returns `True`) without being the same object (`is` returns `False`). For example, two separate lists `[1,2,3]` are equal but not identical - they're distinct objects in memory.

Identity matters for: checking singletons (None, True, False), understanding mutability (modifying one variable affects the other if `is` returns `True`), and optimization (Python caches small integers and interns some strings, making `is` return `True` for efficiency).

**Key behaviors:**

1. **Checks object identity, not value:** `is` compares memory addresses via `id()` function. Two objects are identical only if they're the same object. Mutable objects (lists, dicts) are almost never identical unless one is assigned from the other.

2. **Singletons always identical:** `None`, `True`, and `False` are singletons - only one instance exists. `x is None` always works correctly. This is why `is None` is preferred over `== None`.

3. **Caching and interning:** Python caches small integers (-5 to 256) and may intern short strings for efficiency. This means `x = 5; y = 5; x is y` returns `True` because they share the same cached integer object. Don't rely on this for larger values.

4. **Use `==` for value comparison:** Unless checking for singletons (None, True, False), usually want `==` not `is`. `is` is for identity, `==` is for equality. Using `is` to compare numbers/strings (beyond singletons) is usually wrong.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Copula verb (linking verb expressing identity)
- **Action vs State:** STATE - expresses being/identity
- **Temporal aspect:** Present tense - immediate identity check

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Copula verb (3rd person) | "es", "est", "é" - is |
| Germanic (de, nl, sv) | Copula verb | "ist", "is" - is |
| Slavic (ru, pl, uk) | Copula verb (present) | Often omitted in present; use "есть", "jest" if needed |
| Arabic | Copula pronoun/verb | "هو" - huwa (he/it is) |
| Chinese | Copula verb | "是" - shì (is/to be) |
| Hindi | Copula verb | "है" - hai (is) |

**Primary recommendation:** Use the target language's copula verb for "is" - the verb expressing identity or equivalence (3rd person singular present tense of "to be").

**Forms to AVOID:**

- ❌ Using "equals" (comparison) when "is" (identity) is different
- ❌ Using "same" (adjective) when need verb
- ❌ Using "identical" - too verbose for frequent operator

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `es`
- **Form:** Copula verb (3rd person singular, present)
- **Why it works:** "Es" is "is" in Spanish. "x es y" means "x is y." Natural for identity check. Standard copula verb. Reads like natural Spanish.

**Arabic:**

- **Translation:** `هو` (huwa)
- **Form:** Copula pronoun (3rd person masculine)
- **Why it works:** Arabic often omits copula in present tense, but `هو` (he/it is) makes identity explicit. Can also use `هي` (hiya - she/it is) or simply `ـ` (omitted). `هو` clear for programming.

**Chinese:**

- **Translation:** `是` (shì)
- **Form:** Copula verb
- **Why it works:** `是` is the standard Chinese copula "to be." "x 是 y" means "x is y." Universal Chinese verb for identity/equivalence. Natural for identity test.

**Hindi:**

- **Translation:** `है` (hai)
- **Form:** Copula verb (present, 3rd person)
- **Why it works:** "Hai" is "is" in Hindi. "x hai y" expresses identity. Standard present tense copula. Natural for identity check in Hindi.

### ❌ Common Translation Mistakes

**Mistake 1: Using "equals" or "igual" (equality not identity)**

- **Wrong:** `igual` (Spanish - "equal")
- **Why wrong:** "Equal" is value comparison (`==`), "is" is identity check. Different concepts. Need word for "being the same object," not "having equal value."
- **Right:** `es` (copula for identity)

**Mistake 2: Using "same" adjective instead of "is" verb**

- **Wrong:** `mismo` (Spanish - "same")
- **Why wrong:** "Same" is adjective; need verb for operator. "Is" is verb expressing identity. Word order would be wrong with adjective.
- **Right:** `es` (verb)

**Mistake 3: Using "identical" (too verbose)**

- **Wrong:** `idéntico` (Spanish - "identical")
- **Why wrong:** While conceptually correct, too long for frequent operator. Python's `is` is two letters. Use simple copula verb.
- **Right:** `es` (simple, short)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Exists" (there is a problem)
- ✅ Meaning 2: **IDENTITY** (X is Y - they are the same object)
- ❌ Meaning 3: "Equals" (value comparison - often conflated)
- ❌ Meaning 4: "Present tense of be" (general state - he is happy)

**Example:**

English "is" can mean:
1. "There is a book" (existence) ❌
2. "x is y" (identity - same object) ✅ **This is the Python meaning**
3. "5 is 5" (equality) - NO, use `==` for this ❌
4. "She is tall" (state/property) ❌

**Your translation should capture meaning #2: identity - being the exact same object in memory.**

Use the copula verb for identity/equivalence, not existence or general state.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `is`, check these translations:**

- [ ] `is not` - Negative identity; should be natural combination
- [ ] `==` - Equality operator; should be distinguished from `is`
- [ ] `None` - Singleton checked with `is`
- [ ] `True`/`False` - Singletons checked with `is`

**Consistency rule:**

`is` and `is not` should work together naturally. If `is` is a verb, `is not` should be verb + negation. The phrase should read naturally in the target language.

**Example:**

Spanish: `es` (is), `no es` or `is not` combined naturally ✅

**Important distinction:**
`is` (identity) and `==` (equality) MUST be different. Don't translate both the same way.

### Functional relationships

**This term works WITH:**

1. **`is` with None**:
```python
if value is None:
    handle_none()
```

2. **`is` with singletons**:
```python
if flag is True:
    process()
```

**Common pairing:**

```python
# is with None (idiomatic)
if result is None:
    print("No result")

# is not with None
if data is not None:
    process(data)

# is with True/False
if success is True:
    celebrate()

# is for checking same object
list1 = [1, 2, 3]
list2 = list1
if list1 is list2:
    print("Same list object")

# is with variable aliasing
x = [1, 2, 3]
y = x         # y is alias for x
z = [1, 2, 3] # z is different object
print(x is y) # True
print(x is z) # False

# is vs == comparison
a = [1, 2]
b = [1, 2]
print(a == b) # True (equal values)
print(a is b) # False (different objects)

# is for sentinel values
SENTINEL = object()
if value is SENTINEL:
    print("Sentinel found")

# Common pattern: None check
def process(data=None):
    if data is None:
        data = []
    return data
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have copula verb "is"
- Universal grammatical concept
- **AI confidence should be HIGH**

### Why EASY for `is`:

- Universal concept (identity/being in all languages)
- Copula verb exists in every language
- Natural semantic mapping
- Well-established grammatical concept

**For this term:** EASY

**Rationale:** Every language has a copula verb for "is" (third person singular present of "to be"). The concept of identity - checking if two things are the same object - translates naturally to the copula expressing identity/equivalence.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Some languages (like Russian) may omit copula in present tense. Translator should decide whether to use explicit copula or contextually appropriate form.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures IDENTITY concept (same object, not equal value)?
- [ ] Distinguished from `==` (equality operator)?
- [ ] Natural for checking "are these the same object?"

### 2. Linguistic Correctness

- [ ] Correct part of speech (copula verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Compatible with `is not` (negation)?
- [ ] Distinguished from `==` translation?
- [ ] Works naturally with `None`, `True`, `False`?

### 4. Usability

- [ ] Short enough (2-3 characters ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (most common copula)?

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
term: is
language: es
translation: es
form: copula_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "es" is the third-person singular present tense of "ser/estar" (to be), expressing identity. Natural for asking "x es y?" (is x y?). Works for identity checks. Standard Spanish copula.

**Alternatives considered:**

1. `igual` (equal) - Wrong concept; that's `==` not identity
2. `mismo` (same - adjective) - Wrong part of speech; need verb
3. `idéntico` (identical) - Too verbose; "es" is standard and short

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Copula verbs expressing "is/to be" are universal with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
