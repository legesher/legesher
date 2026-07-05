# Python Builtin Method: `format` - Translation Brief (Tier 1)

**Category:** builtin_method
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `format()` method in Python creates formatted strings by inserting values into placeholders. It provides a powerful way to construct strings with dynamic content, replacing placeholders with actual values and controlling how those values are displayed.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic string formatting with one placeholder
template = "Hello, {}!"
result = template.format("Alice")
print(result)  # Output: Hello, Alice!
```

**What this does:** The curly braces `{}` act as a placeholder. The `format()` method replaces it with the argument "Alice". Simple insertion of values into strings.

### Example 2: Common Pattern

```python
# Multiple placeholders with positional arguments
message = "{} has {} apples".format("Bob", 5)
print(message)  # Output: Bob has 5 apples

# Named placeholders for clarity
info = "{name} is {age} years old".format(name="Carol", age=30)
print(info)  # Output: Carol is 30 years old
```

**What this does:** Multiple `{}` placeholders are filled in order by positional arguments. Named placeholders `{name}` use keyword arguments, making code more readable and maintainable.

### Example 3: Edge Case

```python
# Formatting numbers with precision control
price = "The price is ${:.2f}".format(19.99567)
print(price)  # Output: The price is $19.99

# Accessing attributes and indices
data = "Item {0[0]} costs ${0[1]:.2f}".format(["Apple", 2.5])
print(data)  # Output: Item Apple costs $2.50
```

**What this shows:** Format specifications like `:.2f` control number display (2 decimal places). You can access list indices `{0[0]}` and dictionary keys within format strings for complex formatting scenarios.

---

## Pattern Classification

**This term is:** ACTION METHOD (String Transformation)

**Similar terms in this pattern:**

1. `replace` - Substitutes substrings (string transformation)
2. `join` - Combines strings (string construction)
3. `split` - Divides strings (string decomposition)

**Pattern rule:** String manipulation methods should use verb forms that clearly indicate the transformation being performed. "Format" means to arrange or structure data into a specific form.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "formatus" (past participle of "formare"), meaning "to form, shape, fashion." In computing, "format" extended to mean arranging data according to a specified structure or appearance.

**Why Python uses this:** "Format" is the standard programming term for converting data into a human-readable string representation with specific styling. The word naturally conveys the idea of shaping raw data into a presentable form, making it intuitive for programmers.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `format()` method creates a new string by substituting placeholders with values and applying optional formatting rules. It's called on a string template that contains replacement fields marked by curly braces `{}`. When `format()` executes, it processes each replacement field, converts the provided values to strings, and inserts them at the placeholder positions.

Format strings support positional arguments `{0}`, `{1}`, keyword arguments `{name}`, and format specifications `{:.2f}` that control precision, width, alignment, and type conversion. This makes `format()` more powerful than simple string concatenation, allowing precise control over numeric display, padding, alignment, and more.

The method returns a new formatted string without modifying the original template. It handles type conversion automatically, calling `__format__()` on objects. This makes it work seamlessly with built-in types and custom classes that implement the format protocol.

**Key behaviors:**

1. **Placeholder replacement:** Curly braces `{}` mark insertion points. Empty braces use arguments in order, numbered braces `{0}` allow reordering, and named braces `{key}` use keyword arguments for clarity.

2. **Format specifications:** After a colon in placeholders `{:spec}`, you can control output: `.2f` for 2 decimal places, `>10` for right-alignment in 10 characters, `,` for thousands separators. These specs follow Python's format specification mini-language.

3. **Type conversion:** Values are automatically converted to strings. Format specs can enforce types: `:d` for integers, `:f` for floats, `:s` for strings. Objects with `__format__()` methods support custom formatting rules.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (action being performed)
- **Action vs State:** ACTION - transforms data into formatted output
- **Temporal aspect:** One-time action that produces a result

### Recommended Form

**Primary recommendation:** Use verb form meaning "to format" or "to arrange." This is an action that transforms data into a structured presentation. The term should convey shaping or arranging information.

**Forms to AVOID:**

- ❌ Using "shape" or "form" alone - too vague, "format" is specific technical term
- ❌ Using "print" - formatting and printing are separate operations
- ❌ Using "convert" - too general, doesn't capture the structured arrangement aspect

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Physical format" (book format, paper size)
- ✅ Meaning 2: **ARRANGE DATA INTO STRUCTURED STRING** (text formatting)
- ❌ Meaning 3: "Format disk" (initialize storage)

**Example:**

English "format" can mean:

1. "This book is in hardcover format" (physical form) ❌
2. "Format this string with values" (structure text output) ✅ **This is the Python meaning**
3. "Format the hard drive" (erase and initialize) ❌

**Your translation should capture meaning #2: arranging data into a structured string representation.**

Some languages may use different words for disk formatting vs string formatting - choose the one appropriate for text/data formatting, not storage formatting.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `format`, check these translations:**

- [ ] `replace` - Similar string method; should use same verb form
- [ ] `join` - String construction method; should use compatible pattern
- [ ] `split` - String manipulation method; should match grammatical pattern

**Consistency rule:**

String methods (`format`, `replace`, `join`, `split`) should all use infinitive verb forms in the same style. They're all actions performed on strings, so grammatical parallelism is essential.

**Example:**

If you translate `format` as infinitive ("formatear"), then:

- `replace` should also be infinitive ("reemplazar")
- `join` should also be infinitive ("unir")
- NOT: `format` infinitive + `replace` noun (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`format` + string templates**: Create formatted output

```python
"{} + {} = {}".format(2, 3, 5)
"Name: {name}".format(name="Alice")
```

2. **`format` + f-strings (modern alternative)**: Python 3.6+ provides f-strings as syntactic sugar

```python
# format method (traditional)
"Hello, {}".format(name)

# f-string (modern)
f"Hello, {name}"
```

**Common pairing:**

```python
# Formatting numbers
price = 19.99
"${:.2f}".format(price)  # $19.99

# Multiple values
name, age = "Bob", 25
"{} is {} years old".format(name, age)

# Named placeholders
"{name} scored {score} points".format(name="Alice", score=100)

# Format specifications
"{:>10}".format("right")   # Right-align in 10 chars
"{:^10}".format("center")  # Center in 10 chars
"{:,}".format(1000000)     # 1,000,000 (thousands separator)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY-MEDIUM)

- Clear technical concept with established translations
- Most languages have computing term for "format"
- Minor variation in whether to use verb or noun form
- **AI confidence should be HIGH with proper form selection**

### Why LOW for `format`

- "Format" is standard computing terminology worldwide
- Most languages borrowed or adapted this term
- Clear meaning in programming context (string formatting)
- Well-established in CS education globally

**For this term:** LOW

**Rationale:** Formatting is a universal computing concept. The term "format" or its cognates are widely used in technical contexts across languages. The main consideration is choosing the correct grammatical form (verb for the method action).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Distinguish between string formatting and disk formatting if language has different terms - use the term appropriate for text/data formatting.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures STRING FORMATTING concept (arranging data into text)?
- [ ] Understood as text manipulation (not disk formatting)?
- [ ] Conveys structured arrangement of values?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb for method action)?
- [ ] Correct form (infinitive for action)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python methods)?

### 3. Consistency

- [ ] Matches pattern of other string methods (`replace`, `join`)?
- [ ] Uses infinitive verb like other action methods?
- [ ] Aligns with how formatting is discussed in target language CS?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common computing term)?

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
term: format
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
