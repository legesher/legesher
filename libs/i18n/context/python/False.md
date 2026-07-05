# Python Keyword: `False` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** constant (boolean literal)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

`False` is a boolean literal in Python representing the logical value "false." It's one of two possible `bool` values (the other being `True`) and is fundamental to conditional logic, comparisons, and control flow. Note the capital 'F' - it's a keyword, not a variable.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Boolean literal
is_valid = False
if is_valid:
    print("Valid!")  # This does NOT execute
else:
    print("Invalid!")  # This executes
```

**What this does:** `False` is a built-in constant. In conditionals, `False` causes the if-block to skip and else-block to execute (if present).

### Example 2: Common Pattern

```python
# Comparison returns False
age = 15
is_adult = (age >= 18)  # Evaluates to False
print(is_adult)  # Output: False

# Function returns False to indicate failure
def is_positive(n):
    return n > 0

result = is_positive(-5)  # Returns False
```

**What this does:** Comparison operators return `False` when conditions aren't met. Functions commonly return `False` to indicate failure, invalidity, or negative conditions.

### Example 3: Edge Case

```python
# False is singleton
a = False
b = False
print(a is b)  # Output: True (same object)

# False in arithmetic (False == 0)
print(False + 10)  # Output: 10
print(int(False))  # Output: 0

# Falsy values (behave like False)
if not False:
    print("Executes")
if not 0:  # 0 is falsy
    print("Also executes")
```

**What this shows:** `False` is a singleton. Historically, `False` equals 0 in numeric contexts. Many values are "falsy" (behave like `False`): 0, empty string `""`, empty list `[]`, `None` - but `False` is the explicit false literal.

---

## Pattern Classification

**This term is:** BOOLEAN LITERAL / CONSTANT

**Similar terms in this pattern:**

1. `True` - The other boolean value (logical true)
2. `None` - Null/absence value (neither true nor false)
3. Falsy values (0, "", [], etc.) - values that evaluate to False

**Pattern rule:** Boolean literals should use noun or adjective forms representing falsehood/incorrectness. Should be natural opposite of `True` translation.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "falsus" meant "deceived, erroneous." Through Old French "fals," it became English "false" meaning "not true, incorrect, deceptive." In logic, "false" represents statements that don't correspond to reality or fail conditions.

**Why Python uses this:** "False" is the standard English word for logical falsehood, the opposite of "true." Most programming languages use "false" or "False." Python capitalizes it to match `True` and distinguish it as a keyword.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`False` is Python's built-in constant representing logical falsehood. It's a keyword - immutable and cannot be used as a variable name. `False` is an instance of `bool` type (and due to inheritance, also of `int` with value 0).

In boolean logic, `False` represents negation: a condition isn't met, a comparison fails, a state is inactive. Comparison operators return `False` when their condition doesn't hold. Logical operators work with `False` and `True` to combine or negate conditions.

Python's truthiness system means many values evaluate to `False` in boolean contexts: zero (0, 0.0), empty containers ([], {}, ""), and `None`. These are "falsy" values. However, the literal `False` is the explicit, canonical false value - the opposite of `True`.

**Key behaviors:**

1. **Singleton object:** Only one `False` object exists in Python. All occurrences of `False` refer to the same object. This makes `False is False` always true.

2. **Keyword status:** `False` is reserved. You cannot reassign it (`False = 5` raises error) or use it as a variable name. This prevents bugs from accidental redefinition.

3. **Zero equivalence:** `bool` inherits from `int`, making `False == 0` evaluate to true. You can use `False` in arithmetic (`False + 5 == 5`), though this is uncommon. This design maintains backward compatibility.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective-as-noun or constant
- **Action vs State:** STATE - represents a truth value
- **Temporal aspect:** Timeless - falsehood is absolute

### Recommended Form

**Primary recommendation:** Use adjective form meaning "false" or "untrue." Must be natural opposite/antonym of `True` translation. Follow Python's capitalization.

**Forms to AVOID:**

- ❌ Using "no" particle - too conversational
- ❌ Using "wrong" when "false" is more logical
- ❌ Using "0" or "zero" - booleans are logical, not numeric

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Fake, counterfeit" (false diamonds)
- ❌ Meaning 2: "Disloyal, unfaithful" (false friend)
- ✅ Meaning 3: **LOGICAL FALSEHOOD** (statement doesn't correspond to reality)

**Example:**

English "false" can mean:

1. "False teeth" (fake/artificial) ❌
2. "False accusations" (untrue/incorrect) ✅ (closer)
3. "`5 > 10` evaluates to `False`" (logical falsehood) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: logical or factual falsehood, statements that don't correspond to reality or fail conditions.**

Use the word for logical/factual falsehood, not fakery or disloyalty.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `False`, check these translations:**

- [ ] `True` - Opposite value; must use antonym
- [ ] `bool` - Type that `False` belongs to
- [ ] `not` - Operator that negates True/False

**Consistency rule:**

`False` and `True` MUST be opposites in target language. They should use the same grammatical form (both adjectives, both nouns, etc.) and same capitalization pattern.


### Functional relationships

**This term works WITH:**

1. **Comparisons return `False`**:

```python
result = (5 > 10)  # False
is_equal = (x != x)  # False
```

2. **Boolean operators use `False`**:

```python
result = True and False  # False
result = False or False  # False
result = not False       # True
```

**Common pairing:**

```python
# False in conditionals
if False:
    print("Never executes")

# False from comparisons
is_valid = (age < 0)  # Likely False

# False as return value
def has_errors(data):
    if not data:
        return True
    return False  # No errors

# False in boolean logic
can_proceed = has_permission and not is_blocked  # False if blocked
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity in logical context
- **AI confidence should be HIGH**

### Why EASY for `False`

- Universal concept (falsehood exists in all cultures)
- Natural opposite of "true"
- Well-established in programming
- Standard logical term globally

**For this term:** EASY

**Rationale:** Falsehood is the universal opposite of truth. Every language has words for true/false. In logical/programming contexts, these translations are standard and well-documented. The main requirement is ensuring `False` is the natural opposite of your `True` translation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOGICAL FALSEHOOD concept (not fakery)?
- [ ] Understood as boolean value (not numeric 0)?
- [ ] Natural opposite/antonym of `True`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective or noun for falsehood)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization matches Python convention (First letter capital)?

### 3. Consistency

- [ ] Opposite/antonym of `True` translation?
- [ ] Same grammatical form as `True`?
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
term: False
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
