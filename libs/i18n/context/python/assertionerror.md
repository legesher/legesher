# Python Builtin: `AssertionError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Subcategory:** assertion
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`AssertionError` is a built-in exception raised when an `assert` statement fails - that is, when the asserted condition evaluates to false. It signals that an assumption the programmer declared to be true turned out not to hold, which usually indicates a bug in the program rather than a user or environment problem.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A failing assert statement raises AssertionError
x = 2
assert x == 3, "x should be 3"
# Raises AssertionError: x should be 3
```

**What this does:** The `assert` statement checks whether `x == 3`. Because the condition is false, Python raises `AssertionError` with the optional message "x should be 3". If the condition had been true, execution would have continued silently.

### Example 2: Common Pattern

```python
# Asserting internal invariants inside a function
def average(values):
    assert len(values) > 0, "average() requires at least one value"
    return sum(values) / len(values)

print(average([2, 4, 6]))  # 4.0

try:
    average([])
except AssertionError as e:
    print(f"Invariant violated: {e}")
```

**What this does:** The `assert` guards an internal assumption: the function must never be called with an empty list. When the assumption is violated, `AssertionError` is raised and can be caught with `try-except`. In practice, assertion failures are usually left uncaught during development so the bug surfaces immediately.

### Example 3: Edge Case

```python
# Assertions can be disabled - and a classic tuple mistake
# Running: python -O script.py  strips all assert statements
# (the __debug__ constant becomes False and asserts are skipped)

assert True, "never raises"

# WRONG: wrapping the assert in parentheses creates a tuple
assert (1 == 2, "expected 1 to equal 2")
# Does NOT raise! A non-empty tuple is always truthy,
# so this assertion can never fail (Python emits a SyntaxWarning).

# Raising AssertionError manually (rare, but legal)
raise AssertionError("explicit assertion failure")
```

**What this shows:** `AssertionError` normally comes from the `assert` statement, and that statement is removed entirely when Python runs with the `-O` (optimize) flag - so assertions must never guard behavior the program depends on. The tuple form is a well-known trap: `assert (condition, message)` tests the truthiness of a two-element tuple, which is always true.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ValueError` - Raised when a value is of the right type but inappropriate
2. `TypeError` - Raised when an operation is applied to the wrong type
3. `RuntimeError` - Raised for errors that don't fit a more specific category
4. `AttributeError` - Raised when attribute access fails

**Pattern rule:** Exception classes are noun compounds, typically ending with "Error" in English. Translations should combine the problem domain ("assertion") with the "error" component, using the same "error" word as every other exception class in the language pack.


---

## Etymology (Brief)

**English Origin:** Latin compound

**Root meaning:** "Assertion" comes from Latin "asserere" meaning "to claim, to maintain, to declare firmly" (ad- "to" + serere "to join"). An assertion is a statement declared to be true. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The `assert` statement lets programmers declare conditions they believe must be true at a given point in the program. When such a declaration fails, `AssertionError` names exactly what went wrong: the assertion did not hold. The name follows Python's convention of combining the problem domain ("Assertion") with "Error" to form a self-describing exception name.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`AssertionError` is the exception raised when an `assert` statement's condition evaluates to false. Assertions are a debugging aid: they document assumptions the programmer believes are always true (invariants), and they turn silent logic errors into loud, immediate failures during development. When `assert condition, message` fails, Python constructs an `AssertionError` carrying the optional message and raises it at that exact line.

Unlike most exceptions, `AssertionError` almost always indicates a programming bug rather than bad user input or a failed external resource. For that reason, production code rarely catches it: an assertion failure means the program's internal logic is broken, and the safest response is usually to crash visibly. Validating user input should use explicit checks that raise `ValueError` or `TypeError` instead, because assertions can be compiled away.

That last point is the critical operational detail: running Python with the `-O` flag sets the built-in constant `__debug__` to `False` and strips every `assert` statement from the compiled bytecode. Any check that must run in production therefore cannot live in an `assert`. Testing frameworks such as `pytest` build directly on this exception - a failing test is, at bottom, a raised `AssertionError`.

**Key behaviors:**

1. **Raised by failing `assert` statements:** `assert condition, message` evaluates the condition; if false, Python raises `AssertionError(message)`. The message argument is optional - without it the exception carries no text.

2. **Disappears under optimization:** With `python -O`, all `assert` statements are removed and `AssertionError` is never raised from them. This makes assertions unsuitable for input validation or security checks.

3. **Signals programmer error, not user error:** By convention, `AssertionError` means an internal invariant was violated. Test frameworks rely on it: `pytest` reports any test that raises `AssertionError` as a failure.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment the asserted condition evaluates to false

### Recommended Form

**Primary recommendation:** Use a compound noun combining the noun form of "assertion" with "error." The "assertion" component must be the noun that corresponds to the verb chosen for the `assert` keyword in the same language pack, so `assert` and `AssertionError` read as one family.

**Forms to AVOID:**

- ❌ Verb forms ("AssertionFailed" as a verb phrase) - exception classes are nouns, not actions
- ❌ Generic "error" without the "assertion" component - loses the connection to `assert`
- ❌ A noun unrelated to the `assert` keyword translation - breaks the keyword/exception pairing

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Assertion as forceful self-confidence ("she spoke with assertion")
- ❌ Meaning 2: Assertion as a legal claim or formal allegation
- ✅ Meaning 3: **A DECLARED CONDITION that must be true at a point in a program** (a checked invariant)

**Example:**

English "assertion" can mean:

1. "He made his point with assertion" (confident manner) ❌
2. "An assertion of ownership" (legal claim) ❌
3. `assert len(items) > 0` (a checked statement of program truth) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: a condition the programmer declares must be true, whose failure is an error. It should NOT suggest personality traits or legal claims.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `AssertionError`, check these translations:**

- [ ] `assert` - The keyword that raises this exception; the "assertion" noun must derive from the same root as the `assert` verb
- [ ] `ValueError` - Same `...Error` compound pattern must be followed
- [ ] `TypeError` - Same `...Error` compound pattern must be followed
- [ ] `Exception` - `AssertionError` is an `Exception` subclass; the general error/exception vocabulary must stay distinct and consistent
- [ ] `raise` - The verb used to raise exceptions should read naturally with this noun

**Consistency rule:**

The "assertion" component of `AssertionError` must be the noun form of whatever verb was chosen for the `assert` keyword. The exception must not switch to an unrelated noun (e.g., a generic "check/verification" word) that abandons the keyword's root. The "error" component must be identical to the one used in `ValueError`, `TypeError`, etc.


### Functional relationships

**This term works WITH:**

1. **`assert` + `AssertionError`**: The statement that raises it

```python
assert user.is_active, "inactive user reached checkout"
```

2. **Exception handling**:

```python
try:
    assert total >= 0
except AssertionError:
    print("invariant violated")
```

**Common pairing:**

```python
# AssertionError as the backbone of tests
def test_addition():
    assert 1 + 1 == 2

# Guarding function invariants during development
def withdraw(balance, amount):
    assert amount > 0, "amount must be positive"
    assert amount <= balance, "cannot overdraw"
    return balance - amount

# Explicit raise (rare)
def unreachable():
    raise AssertionError("this branch should never execute")

# Remember: python -O strips assert statements entirely,
# so never use assert to validate user input:
def set_age(age):
    if age < 0:  # correct: explicit check survives -O
        raise ValueError("age must be non-negative")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `AssertionError`

- "Assertion" is polysemous (confidence, legal claim, declared condition)
- The noun must derive from the same root as the `assert` keyword translation
- Must maintain the `...Error` compound pattern used by sibling exceptions
- Most languages have an established CS term for assertions through testing culture

**For this term:** MEDIUM

**Rationale:** The compound structure is straightforward and most languages already have a testing-culture word for "assertion." The real work is consistency: the exception must visibly share a root with the `assert` keyword translation and reuse the pack's standard "error" word. Where the keyword translation used a loose synonym, the translator must decide whether to keep that root or switch both terms together - never just one.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures DECLARED-CONDITION assertion (not confidence or legal claim)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer connect this name to the `assert` statement?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] "Assertion" component shares a root with the `assert` keyword translation?
- [ ] Same "error" word as `ValueError`, `TypeError`, `AttributeError`?
- [ ] Matches the pattern of other exception translations?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: AssertionError
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
**Last Updated:** 2026-07-04
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
