# Python Builtin: `ValueError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`ValueError` is raised when a function receives an argument of the correct type but with an inappropriate value. It signals that while the data type is right, the specific value doesn't make sense for the operation being performed.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# ValueError raised by int() with invalid string
try:
number = int("abc")
except ValueError:
print("Cannot convert 'abc' to integer")
```

**What this does:** `int()` expects a string containing digits, not letters. The type (string) is correct, but the value ("abc") cannot be converted to an integer, so Python raises `ValueError`.

### Example 2: Common Pattern

```python
# Raising ValueError in custom function
def set_age(age):
if age < 0 or age > 150:
raise ValueError("Age must be between 0 and 150")
return age

try:
set_age(-5)
except ValueError as e:
print(f"Invalid value: {e}")
```

**What this does:** When validating user input, raise `ValueError` for logically invalid values. Here, `-5` is a valid integer (correct type), but it's an inappropriate value for representing age.

### Example 3: Edge Case

```python
# ValueError vs TypeError distinction
import math

try:
result = math.sqrt(-1)  # ValueError: negative number
except ValueError:
print("Cannot take square root of negative number")

try:
result = math.sqrt("16")  # TypeError: wrong type
except TypeError:
print("sqrt() requires number, not string")
```

**What this shows:** `ValueError` is for wrong values of correct types (negative number for `sqrt`), while `TypeError` is for wrong types entirely (string instead of number). Understanding this distinction is crucial for proper error handling.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Specific Exception Class)

**Similar terms in this pattern:**

1. `TypeError` - Raised for wrong type (related error category)
2. `KeyError` - Raised for invalid dictionary key (value-related)
3. `IndexError` - Raised for invalid sequence index (value-related)

**Pattern rule:** Error exceptions should use compound noun form combining the problematic element ("Value") with "Error", following Python's exception naming conventions.


---

## Etymology (Brief)

**English Origin:** English "value" (Latin "valere") + "error" (Latin "error")

**Root meaning:** "Value" comes from Latin "valere" meaning "to be worth" or "to be strong." "Error" comes from Latin "errare" meaning "to wander" or "to go astray."

**Why Python uses this:** Python distinguishes between type errors (wrong kind of data) and value errors (wrong specific value). `ValueError` explicitly names what's wrong—the value itself, not the type. This naming pattern (`TypeName` + `Error`) is consistent across Python's exception hierarchy and makes errors self-documenting.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ValueError` represents one of the most common error categories in Python: you passed data of the right type, but the specific value doesn't work for the operation. For example, `int("123")` succeeds because "123" can be converted to an integer, but `int("hello")` raises `ValueError` because "hello" cannot be meaningfully converted, even though both are strings.

The key distinction is between `ValueError` and `TypeError`. If you pass a completely wrong type—like passing a list where a string is expected—that's a `TypeError`. But if you pass the right type with an inappropriate value—like negative radius to a circle-drawing function—that's a `ValueError`.

Many built-in functions raise `ValueError` for invalid inputs: `int()` for unconvertible strings, `math.sqrt()` for negative numbers (in real math), unpacking with wrong number of values, and searching for items not in a sequence. When writing your own functions, raising `ValueError` for invalid argument values is the Pythonic way to signal input validation failures.

**Key behaviors:**

1. **Right Type, Wrong Value:** Raised when argument type is correct but value doesn't meet requirements (negative number where positive needed, empty string where non-empty expected, out-of-range number, etc.).

2. **Built-in Validation:** Many standard library functions raise `ValueError` automatically for invalid inputs, providing consistent error handling across Python's ecosystem.

3. **Custom Validation Standard:** When writing functions, `ValueError` is the conventional exception for input validation failures, signaling to callers that they provided inappropriate values.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun - concept noun ("value") + error noun
- **Action vs State:** State/Problem - describes what IS wrong (a value problem)
- **Temporal aspect:** Point-in-time - marks when invalid value is detected

### Recommended Form

**Primary recommendation:** Compound noun combining "value" concept with "error" concept, following Python's exception naming pattern.

**Forms to AVOID:**

- ❌ Verb form - This names an exception class, not an action
- ❌ Adjective alone - Needs both "value" and "error" components

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Value" as in personal values or beliefs
- ❌ Meaning 2: "Value" as monetary worth or price
- ✅ Meaning 3: "Value" as the specific data/content assigned to a variable (CORRECT)
- ❌ Meaning 4: "Error" as general mistake in judgment

**Example:**

English "value" can mean:

1. Personal principles ("family values") ❌
2. Monetary worth ("property value") ❌
3. Data content in programming ("variable value") ✅ **This is the Python meaning**
4. Importance ("value of education") ❌

English "error" means:

1. Mistake or incorrect action ✅ **This is the Python meaning**
2. Difference from true value (statistical error) ❌

**Your translation should capture "value" as programming data content and "error" as exception/problem, NOT other meanings.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ValueError`, check these translations:**

- [ ] `Exception` - Base class for all errors
- [ ] `TypeError` - Must follow same compound pattern (Type + Error)
- [ ] `KeyError` - Should follow same pattern (Key + Error)
- [ ] `IndexError` - Should follow same pattern (Index + Error)
- [ ] `AttributeError` - Should follow same pattern (Attribute + Error)
- [ ] `value` - The concept being validated (if translating variable-related terms)
- [ ] `UnicodeError` - Subclass; its family of four Unicode briefs anchors on this file's error suffix convention

**Consistency rule:**

All `*Error` exceptions should follow identical compound structure. If `TypeError` is "Type + Error", then `ValueError` must be "Value + Error" in the same pattern.


### Functional relationships

**This term works WITH:**

1. **`raise ValueError`**: Raising value validation errors
2. **`except ValueError`**: Catching value errors specifically
3. **`int()`, `float()`, conversion functions**: Common sources of ValueError

**Common pairing:**

```python
# ValueError appears in validation and conversion contexts
try:
age = int(user_input)
if age < 0:
raise ValueError("Age cannot be negative")
except ValueError:
print("Please enter a valid age")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:**

Translating `ValueError` involves moderate complexity:

**Moderate aspects:**

- Compound term with two clear components
- "Error" typically has established translation
- "Value" is common programming term
- Pattern must match other `*Error` exceptions

**Challenges:**

- "Value" can mean different things (must choose programming sense)
- Compound structure varies by language (word order, connectors)
- Must maintain consistency with entire `*Error` family
- Some languages distinguish between different types of values

The difficulty is MEDIUM because while the components are straightforward, creating a compound that's concise, natural, and consistent with the entire exception hierarchy requires careful attention to naming patterns and technical vocabulary.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "value" as programming data (not worth or principles)?
- [ ] Indicates this is an error exception?
- [ ] Clearly distinguishes from `TypeError`?

### 2. Linguistic Correctness

- [ ] Compound noun structure appropriate?
- [ ] "Value" component uses programming term?
- [ ] "Error" component uses established exception term?
- [ ] Capitalization follows class naming conventions?

### 3. Consistency

- [ ] Matches pattern of `TypeError`, `KeyError`, etc.?
- [ ] Uses same "error" component across all `*Error` exceptions?
- [ ] Follows Python's concise naming style?

### 4. Usability

- [ ] Concise compound (not verbose phrase)?
- [ ] Easy to recognize as value-related error?
- [ ] Distinguishable from other error types?

### 5. Cultural Appropriateness

- [ ] Uses technical/professional vocabulary?
- [ ] No confusing connotations?
- [ ] Respects CS education terminology?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] Works in error messages and stack traces?
- [ ] No special characters that break code?

---

## Translation Output Format

**Your translation:**

```yaml
term: ValueError
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
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
