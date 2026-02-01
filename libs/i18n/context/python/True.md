# Python Keyword: `True` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** constant (boolean literal)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

`True` is a boolean literal in Python representing the logical value "true." It's one of two possible `bool` values (the other being `False`) and is fundamental to conditional logic, comparisons, and control flow. Note the capital 'T' - it's a keyword, not a variable.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Boolean literal
is_valid = True
if is_valid:
    print("Valid!")  # This executes
```

**What this does:** `True` is a built-in constant. Assigning it to a variable creates a boolean value. In conditionals, `True` causes the if-block to execute.

### Example 2: Common Pattern

```python
# Comparison returns True
age = 25
is_adult = (age >= 18)  # Evaluates to True
print(is_adult)  # Output: True

# Function returns True
def is_positive(n):
    return n > 0

result = is_positive(5)  # Returns True
```

**What this does:** Comparison operators (`>`, `>=`, `==`, etc.) return `True` or `False`. Functions commonly return boolean values to indicate success, validity, or conditions.

### Example 3: Edge Case

```python
# True is singleton - only one True object
a = True
b = True
print(a is b)  # Output: True (same object)

# True in arithmetic (True == 1)
print(True + True)  # Output: 2
print(int(True))    # Output: 1
```

**What this shows:** `True` is a singleton - there's only one `True` object in Python. All references point to the same object. Historically, `bool` is subclass of `int`, so `True` equals 1 in numeric contexts (though using booleans in arithmetic is uncommon).

---

## Pattern Classification

**This term is:** BOOLEAN LITERAL / CONSTANT

**Similar terms in this pattern:**

1. `False` - The other boolean value (logical false)
2. `None` - Null/absence value (neither true nor false)
3. Boolean constants in other languages (often lowercase: true, false)

**Pattern rule:** Boolean literals should use noun or adjective forms representing truth/correctness. Many languages capitalize boolean literals (True/False) or use lowercase (true/false). Follow target language conventions.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `False` | Falso | خطأ | 假 | असत्य |
| `None` | Ninguno | لاشيء | 无 | कोई_नहीं |
| `True` | **Verdadero** | **صحيح** | **真** | **सत्य** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "trēowe" meant "faithful, trustworthy, honest." It became "true" meaning "in accordance with fact, genuine, accurate." In logic, "true" represents statements that correspond to reality or satisfy conditions.

**Why Python uses this:** "True" is the standard English word for logical truth. Most programming languages use "true" or "True" for the boolean positive value. Python capitalizes it (`True` not `true`) to distinguish it as a keyword/constant, not a regular word.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`True` is one of Python's built-in constants, representing the boolean value for logical truth. It's a keyword - you cannot assign to it or use it as a variable name. `True` is an instance of the `bool` type (and due to inheritance, also an instance of `int` with value 1).

In boolean logic, `True` represents affirmation: a condition is met, a comparison holds, a state is active. Comparison operators like `==`, `>`, `<` return `True` when their condition is satisfied. Logical operators (`and`, `or`, `not`) work with `True` and `False` to combine or negate conditions.

Python has truthiness: many values evaluate to `True` in boolean contexts. Non-zero numbers, non-empty strings, non-empty collections all are "truthy" (behave like `True` in `if` statements). However, the literal `True` is the explicit, canonical true value.

**Key behaviors:**

1. **Singleton object:** Python maintains exactly one `True` object. All occurrences of `True` refer to the same object in memory. This makes identity comparison (`True is True`) always succeed.

2. **Keyword status:** `True` is a reserved keyword. You cannot do `True = 5` or define a variable named `True`. This prevents accidental redefinition (older Python 2 allowed this, causing bugs).

3. **Integer heritage:** `bool` is subclass of `int`, making `True == 1` evaluate to true. You can use `True` in arithmetic (`True + 5 == 6`) though this is rarely done in practice. This design decision maintains backward compatibility with older code.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective-as-noun or constant
- **Action vs State:** STATE - represents a truth value, not an action
- **Temporal aspect:** Timeless - truth is absolute, not time-dependent

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adjective (masculine) | "Verdadero", "Vrai" - true/truthful |
| Germanic (de, nl, sv) | Adjective | "Wahr", "waar" - true |
| Slavic (ru, pl, uk) | Adjective/noun | "Истина", "prawda" - truth/true |
| Arabic | Adjective | "صحيح" - correct/true |
| Chinese | Adjective | "真" - true/real |
| Hindi | Adjective/noun | "सत्य" - truth/true |

**Primary recommendation:** Use adjective form meaning "true" or "truthful." Follow Python's capitalization (first letter capital) unless target language has different conventions for boolean constants.

**Forms to AVOID:**

- ❌ Using verb "to be true" - should be adjective/state
- ❌ Using "yes" - while related, "true" is more formal/logical
- ❌ Using "1" or "one" - booleans are logical, not numeric

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `Verdadero`
- **Form:** Adjective (masculine), capitalized
- **Why it works:** Standard Spanish for "true/truthful." Capitalized like Python. Pairs naturally with `Falso` (False). Used in Spanish CS education for boolean true value.

**Arabic:**

- **Translation:** `صحيح` (ṣaḥīḥ)
- **Form:** Adjective
- **Why it works:** Means "correct/true/valid." Standard in Arabic for truth value. Pairs with `خطأ` (false/error). Natural in logical contexts.

**Chinese:**

- **Translation:** `真` (zhēn)
- **Form:** Adjective
- **Why it works:** Single character meaning "true/real/genuine." Standard Chinese for boolean true. Concise. Pairs with `假` (false). Used in Chinese programming.

**Hindi:**

- **Translation:** `सत्य` (satya)
- **Form:** Noun/adjective
- **Why it works:** Sanskrit-derived word for truth/true. Philosophical and formal. Used in Hindi for logical truth. Pairs with `असत्य` (false). Appropriate register for programming.

### ❌ Common Translation Mistakes

**Mistake 1: Using lowercase when Python uses uppercase**

- **Wrong:** `verdadero` (Spanish - lowercase)
- **Why wrong:** Python capitalizes boolean literals: `True`, `False`. Translation should match this capitalization to maintain visual consistency.
- **Right:** `Verdadero` (capitalized)

**Mistake 2: Using "yes" or affirmative particle**

- **Wrong:** `sí` (Spanish - "yes")
- **Why wrong:** "Yes" is conversational affirmation. "True" is logical/philosophical truth. Different concepts. Programming uses logical truth, not conversational yes/no.
- **Right:** `Verdadero` (logical truth)

**Mistake 3: Using numeric "1" or "one"**

- **Wrong:** `uno` (Spanish - "one")
- **Why wrong:** While `True == 1` in Python, conceptually they're different. `True` is logical truth; 1 is a number. Don't conflate them in naming.
- **Right:** `Verdadero` (logical concept)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Genuine, authentic" (this is true gold)
- ❌ Meaning 2: "Loyal, faithful" (a true friend)
- ✅ Meaning 3: **LOGICAL/FACTUAL TRUTH** (statement corresponds to reality)

**Example:**

English "true" can mean:

1. "This is true leather" (genuine/authentic) ❌
2. "He's a true friend" (loyal/faithful) ❌
3. "`5 > 3` evaluates to `True`" (logical truth) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: logical or factual truth, statements that correspond to reality or satisfy conditions.**

Most languages distinguish these meanings. Use the word for logical/factual truth, not loyalty or authenticity.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `True`, check these translations:**

- [ ] `False` - Opposite value; should use opposite word in target language
- [ ] `bool` - Type that `True` belongs to; should feel related
- [ ] `None` - Another constant; should use similar capitalization/form

**Consistency rule:**

`True` and `False` are opposites and should use antonym words in target language. Both should have same capitalization pattern. If `True` is adjective, `False` should be too.

**Example:**

Spanish: `Verdadero` (True), `Falso` (False) - both capitalized adjectives ✅
NOT: `Verdadero` (adj) + `No` (particle for False) - inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **Comparisons return `True`**:

```python
result = (5 > 3)  # True
is_equal = (x == y)
```

2. **Boolean operators use `True`**:

```python
result = True and False  # False
result = True or False   # True
result = not True        # False
```

**Common pairing:**

```python
# True in conditionals
if True:
    print("Always executes")

# True from comparisons
is_valid = (age >= 18)  # May be True

# True as return value
def is_positive(n):
    return n > 0  # Returns True or False

# True in boolean logic
can_proceed = has_permission and is_verified  # True if both true
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity in logical context
- **AI confidence should be HIGH**

### Why EASY for `True`

- Universal concept (truth exists in all cultures)
- "True" is standard logical term
- Well-established in programming
- Clear opposition to "False"

**For this term:** EASY

**Rationale:** The concept of truth (as opposed to falsehood) is universal across human languages and cultures. Every language has words for true/false. In logical/programming contexts, these translations are well-established and documented.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: capitalization conventions may vary. Follow Python's capitalization unless target language has strong counter-conventions.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOGICAL TRUTH concept (not loyalty or authenticity)?
- [ ] Understood as boolean value (not numeric 1)?
- [ ] Pairs naturally with `False` (opposite)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective or noun for truth)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization matches Python convention (First letter capital)?

### 3. Consistency

- [ ] Opposite/antonym of `False` translation?
- [ ] Same grammatical form as `False` (both adjectives, etc.)?
- [ ] Related to `bool` type name?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word)?

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
term: True
language: es
translation: Verdadero
form: adjective
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "Verdadero" is the standard adjective for true/truthful, representing logical truth. Capitalized to match Python's convention. Natural opposite of "Falso" (False). Used universally in Spanish CS education.

**Alternatives considered:**

1. `Cierto` (true/certain) - Valid but "Verdadero" more common in CS
2. `Sí` (yes) - Wrong concept; conversational vs. logical
3. `verdadero` (lowercase) - Should capitalize to match Python

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Logical truth/falsehood are universal concepts with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
