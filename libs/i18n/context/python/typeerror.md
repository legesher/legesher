# Python Builtin: `TypeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`TypeError` is raised when an operation or function is applied to an object of inappropriate type. It signals that the data type itself is wrong for the operation, not just the specific value—you're trying to use data in a way that doesn't make sense for its type.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# TypeError: cannot add string and integer
try:
result = "hello" + 5
except TypeError:
print("Cannot add string and number")
```

**What this does:** The `+` operator works with two strings or two numbers, but not a mix. Since "hello" is a string and `5` is an integer, Python raises `TypeError` because the types are incompatible for addition.

### Example 2: Common Pattern

```python
# TypeError from wrong argument type
def calculate_area(radius):
if not isinstance(radius, (int, float)):
raise TypeError("Radius must be a number")
return 3.14 * radius ** 2

try:
area = calculate_area("10")
except TypeError as e:
print(f"Wrong type: {e}")
```

**What this does:** When validating parameter types, raise `TypeError` if the wrong type is passed. Here, the function expects a number but receives a string, so it explicitly raises `TypeError` to signal the type mismatch.

### Example 3: Edge Case

```python
# TypeError vs ValueError distinction
import math

try:
result = math.sqrt("16")  # TypeError: wrong type
except TypeError:
print("sqrt() needs number, not string")

try:
result = math.sqrt(-1)  # ValueError: wrong value
except ValueError:
print("sqrt() needs non-negative number")
```

**What this shows:** `TypeError` occurs when the type is completely wrong (string instead of number), while `ValueError` occurs when the type is correct but the specific value is inappropriate (negative number). Understanding this distinction is fundamental to Python error handling.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Specific Exception Class)

**Similar terms in this pattern:**

1. `ValueError` - Raised for wrong value (complementary error category)
2. `AttributeError` - Raised for wrong attribute access (type-related)
3. `KeyError` - Raised for wrong dictionary key (type/value-related)

**Pattern rule:** Error exceptions should use compound noun form combining the problematic element ("Type") with "Error", following Python's exception naming conventions.


---

## Etymology (Brief)

**English Origin:** English "type" (Greek "typos") + "error" (Latin "error")

**Root meaning:** "Type" comes from Greek "typos" meaning "a blow, impression, or mark." "Error" comes from Latin "errare" meaning "to wander" or "to go astray."

**Why Python uses this:** Python is dynamically typed, meaning types are checked at runtime. `TypeError` explicitly names what's wrong—the type of data being used. This exception is fundamental to Python's type system, occurring when you try to perform operations that don't make sense for the given type (like adding strings to numbers, or calling non-callable objects).

---

## Concept Explanation (Intermediate Level)

**What it does:**

`TypeError` is one of the most common exceptions in Python, raised whenever you try to use data in a way that's incompatible with its type. This happens in many situations: performing operations between incompatible types (`"text" + 5`), passing wrong types to functions (`len(5)`), trying to call non-callable objects (`x = 5; x()`), or attempting unsupported operations on a type (`"text"[1.5]`).

The fundamental distinction is between `TypeError` (wrong kind of thing entirely) and `ValueError` (right kind of thing, wrong specific instance). If a function expects a number and you pass a string, that's a `TypeError`—the type is wrong. If it expects a positive number and you pass `-5`, that's a `ValueError`—the type is right (number) but the value is inappropriate (negative).

Python raises `TypeError` automatically for built-in operations and functions when types don't match. When writing your own functions, you can raise `TypeError` explicitly to enforce type requirements, though Python's duck typing philosophy encourages accepting any type that supports the needed operations rather than checking types rigidly.

**Key behaviors:**

1. **Incompatible Operations:** Raised when performing operations between incompatible types (adding string to int, multiplying list by float, comparing uncomparable types in older Python versions).

2. **Function Argument Mismatches:** Raised when passing wrong types to functions (too many/few arguments counts as `TypeError`, wrong types for parameters, passing non-callable to higher-order functions).

3. **Type-Specific Behavior Failures:** Raised when attempting operations that specific types don't support (indexing with non-integers, calling non-callable objects, iterating over non-iterables).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun - concept noun ("type") + error noun
- **Action vs State:** State/Problem - describes what IS wrong (a type mismatch)
- **Temporal aspect:** Point-in-time - marks when type incompatibility is detected

### Recommended Form

**Primary recommendation:** Compound noun combining "type" concept with "error" concept, following Python's exception naming pattern and maintaining consistency with `ValueError`.

**Forms to AVOID:**

- ❌ Verb form - This names an exception class, not an action
- ❌ Adjective alone - Needs both "type" and "error" components

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Type" as in keyboard typing or typesetting
- ❌ Meaning 2: "Type" as in category or kind in general language
- ✅ Meaning 3: "Type" as data type in programming (int, string, list, etc.) (CORRECT)
- ❌ Meaning 4: "Type" as a personality type or archetype

**Example:**

English "type" can mean:

1. Keyboard typing ("type a letter") ❌
2. General category ("blood type") ❌
3. Programming data type (int, str, list) ✅ **This is the Python meaning**
4. Kind or sort ("not my type") ❌

English "error" means:

1. Mistake or exception condition ✅ **This is the Python meaning**
2. Statistical deviation ❌

**Your translation should capture "type" as programming data type (int, string, list, object types) and "error" as exception, NOT other meanings.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `TypeError`, check these translations:**

- [ ] `Exception` - Base class for all errors
- [ ] `ValueError` - Must follow same compound pattern (Value + Error)
- [ ] `AttributeError` - Should follow same pattern (Attribute + Error)
- [ ] `KeyError` - Should follow same pattern (Key + Error)
- [ ] `IndexError` - Should follow same pattern (Index + Error)
- [ ] `type()` - Built-in function for checking types (should relate linguistically)
- [ ] `class` - Since types are classes in Python

**Consistency rule:**

All `*Error` exceptions should follow identical compound structure. If `ValueError` is "Value + Error", then `TypeError` must be "Type + Error" in the same pattern with same connectors and word order.


### Functional relationships

**This term works WITH:**

1. **`raise TypeError`**: Raising type validation errors
2. **`except TypeError`**: Catching type errors specifically
3. **`isinstance()`, `type()`**: Type-checking functions that prevent TypeError
4. **Operators and functions**: Common sources of TypeError when types mismatch

**Common pairing:**

```python
# TypeError appears in type validation and operations
try:
result = "5" + 10
except TypeError:
print("Cannot add string and number")

# Type checking to prevent TypeError
if not isinstance(x, (int, float)):
raise TypeError("Expected number")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:**

Translating `TypeError` involves moderate complexity:

**Moderate aspects:**

- Compound term with two clear components
- "Error" typically has established translation
- "Type" is fundamental programming concept
- Pattern must match other `*Error` exceptions

**Challenges:**

- "Type" has multiple meanings in English (must choose data type sense)
- Compound structure varies by language (word order, connectors)
- Must maintain perfect consistency with entire `*Error` family
- "Type" translation must align with `type()` function and type system vocabulary

The difficulty is MEDIUM because while the components are well-known in programming, creating a compound that's concise, natural, technically precise, and consistent with the entire exception hierarchy requires careful attention to naming patterns and technical vocabulary. The translation must clearly indicate data types, not typography or general categories.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "type" as programming data type (not typing/typesetting)?
- [ ] Indicates this is an error exception?
- [ ] Clearly distinguishes from `ValueError`?

### 2. Linguistic Correctness

- [ ] Compound noun structure appropriate?
- [ ] "Type" component uses programming/CS term?
- [ ] "Error" component uses established exception term?
- [ ] Capitalization follows class naming conventions?

### 3. Consistency

- [ ] Matches pattern of `ValueError`, `AttributeError`, etc.?
- [ ] Uses same "error" component across all `*Error` exceptions?
- [ ] Follows Python's concise naming style?
- [ ] Aligns with `type()` function translation if applicable?

### 4. Usability

- [ ] Concise compound (not verbose phrase)?
- [ ] Easy to recognize as type-related error?
- [ ] Distinguishable from other error types?

### 5. Cultural Appropriateness

- [ ] Uses technical/professional vocabulary?
- [ ] No confusing connotations (especially avoiding "typing" confusion)?
- [ ] Respects CS education terminology?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] Works in error messages and stack traces?
- [ ] No special characters that break code?

---

## Translation Output Format

**Your translation:**

```yaml
term: TypeError
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
