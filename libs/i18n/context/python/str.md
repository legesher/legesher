# Python Builtin Type: `str` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (type constructor)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `str` type in Python represents text (strings of characters). It's an immutable sequence type supporting Unicode characters, and serves both as the type name and a constructor function to convert other values to their string representations.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Creating a string
text = str("Hello")
# or simply:
message = "Hello"  # Python infers this is a str
```

**What this does:** The `str()` function creates a string object. When you write text in quotes (`"..."` or `'...'`), Python automatically treats it as a `str`. Calling `str()` explicitly is usually for type conversion.

### Example 2: Common Pattern

```python
# Converting numbers to strings
age = 25
text = "Age: " + str(age)  # Result: "Age: 25"

# String concatenation requires str type
# This would error: "Age: " + 25
# Must use: "Age: " + str(25)
```

**What this does:** The most common use of `str()` is converting numbers or other objects to strings for display or concatenation. Python requires explicit conversion - you can't directly concatenate strings and numbers.

### Example 3: Edge Case

```python
# Custom object string conversion
class Person:
    def __str__(self):
        return "Person object"

p = Person()
print(str(p))  # Output: "Person object"
```

**What this shows:** `str()` calls an object's `__str__()` method to get a human-readable string representation. Custom classes can define how they appear as strings. Without `__str__()`, Python falls back to a default representation like `<Person object at 0x...>`.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR / SEQUENCE TYPE

**Similar terms in this pattern:**

1. `int` - Integer number type
2. `float` - Floating-point number type
3. `list` - Mutable sequence type (list of items)

**Pattern rule:** Type constructors should use noun forms in target language. They name a category/class of values. For `str`, use the noun for "string/text/character sequence."


---

## Etymology (Brief)

**English Origin:** Abbreviated from "string"

**Root meaning:** The word "string" in computing comes from the metaphor of characters strung together like beads on a string. In early computing, text was treated as a sequence (string) of individual characters, much like beads on a thread.

**Why Python uses this:** Abbreviated to `str` from "string" for brevity and consistency with other type names (`int`, `bool`). Most programming languages use "string" or abbreviations thereof. The term is universally understood in CS to mean "text data."

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `str` type represents text in Python - sequences of Unicode characters. Strings are immutable, meaning once created, their contents cannot be changed. Operations that appear to modify strings actually create new string objects. Python 3 uses Unicode by default, supporting text in any language (Latin, Arabic, Chinese, emoji, etc.).

Python's `str()` serves dual purposes: it's the type name and a constructor function. As a constructor, it converts objects to string representations by calling their `__str__()` method. For basic types: `str(42)` → `"42"`, `str(3.14)` → `"3.14"`, `str(True)` → `"True"`. Called with no arguments, `str()` returns an empty string `""`.

Strings support extensive operations: indexing (`s[0]`), slicing (`s[1:5]`), concatenation (`s1 + s2`), repetition (`s * 3`), searching (`"x" in s`), and numerous methods (`.upper()`, `.split()`, `.replace()`, etc.). They're iterable - you can loop through characters with `for char in text:`.

**Key behaviors:**

1. **Immutable:** You cannot change characters in an existing string. `s[0] = 'A'` raises an error. Methods like `.upper()` return new strings rather than modifying the original. This enables safe string reuse and optimization.

2. **Unicode support:** Python 3 strings are Unicode by default. A single character can be ASCII (`"A"`), accented (`"é"`), Arabic (`"ع"`), Chinese (`"中"`), or emoji (`"😀"`). No separate "Unicode string" type needed.

3. **Multiple representations:** Strings can be defined with single quotes (`'text'`), double quotes (`"text"`), or triple quotes (`'''multiline'''` or `"""multiline"""`). They're all the same `str` type. Triple quotes allow multi-line strings and embedded quotes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun - names a type/category of values
- **Action vs State:** STATE/CATEGORY - describes what something IS (a text sequence)
- **Temporal aspect:** Timeless - a type is a permanent classification

### Recommended Form

**Primary recommendation:** Use your target language's established CS education term for "string" (text data type). This is usually "string," "character chain/sequence," or "text." Avoid overly literal translations that aren't used in education.

**Forms to AVOID:**

- ❌ Verb form - "to string" or "to text" (wrong part of speech)
- ❌ Just "text" without technical context - may be too vague
- ❌ Overly complex compound words if simpler term exists

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (the full word "string" does)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Physical string (rope, cord, thread)
- ❌ Meaning 2: Series of events ("string of victories")
- ✅ Meaning 3: **SEQUENCE OF CHARACTERS** (text data type in computing)

**Example:**

English "string" can mean:

1. "Tie it with string" (physical cord) ❌
2. "A string of pearls" (sequence/series of objects) ⚠️ (closer, but not computing context)
3. "Store name as string variable" (character sequence data type) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: a data type representing text/character sequences in computing.**

Many languages distinguish between:

- Physical string/rope
- Text string data type

Use the COMPUTING/PROGRAMMING term, not the physical object term.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `str`, check these translations:**

- [ ] `int` - Must use similar noun structure (both are types)
- [ ] `float` - Must use noun form (type name)
- [ ] `bool` - Must use noun form (type name)
- [ ] `list` - Must use noun form (sequence type)

**Consistency rule:**

All type constructors (`str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`) must use the same grammatical category - all nouns. Don't mix noun types with verb types or adjectives.


### Functional relationships

**This term works WITH:**

1. **Type conversion:** `str(42)`, `str(3.14)`, `str(True)` - converting to string
2. **String methods:** `.upper()`, `.lower()`, `.split()`, `.join()`, `.replace()`
3. **String formatting:** f-strings, `.format()`, `%` operator

**Common pairing:**

```python
# str used for type conversion
age_str = str(25)

# str in concatenation
message = "Age: " + str(age)

# str in type hints
def greet(name: str) -> str:
    return f"Hello, {name}"

# str with isinstance
if isinstance(value, str):
    process_text(value)

# str for user input (input always returns str)
name = input("Enter name: ")  # name is str type
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `str`

- "String" is a universal CS concept
- Every programming language has strings
- Standard translations exist in all CS education systems
- Well-documented globally

**For this term:** EASY

**Rationale:** The concept of text/string data types is fundamental to all programming languages. Every language with CS education has established terminology. The term "string" or its equivalent ("character chain/sequence") appears in the first lessons of any programming course.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Some languages debate between native term vs. English loanword "string" (especially languages written in non-Latin scripts). Follow your target language's CS education conventions - if "string" is widely adopted as a loanword, that's acceptable.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures STRING/TEXT/CHARACTER SEQUENCE concept?
- [ ] Understood as programming data type (not physical string)?
- [ ] Distinguishes from other text-related concepts (line, word, paragraph)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (singular noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other type names (`int`, `float`, `list`)?
- [ ] All type names use same grammatical form (nouns)?
- [ ] Aligns with CS terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard CS term)?

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
term: str
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
