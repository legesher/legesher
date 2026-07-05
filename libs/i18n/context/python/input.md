# Python Builtin Function: `input` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb/noun
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `input` function in Python reads a line of text from the user (standard input), waits for the user to press Enter, and returns the text as a string. It's the primary way to get interactive input from users in console programs.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get user input
name = input()
print(f"Hello, {name}")
# User types: Alice
# Output: Hello, Alice
```

**What this does:** `input()` pauses program execution and waits for user to type text and press Enter. Returns whatever the user typed as a string.

### Example 2: Common Pattern

```python
# Input with prompt
age = input("Enter your age: ")
print(f"You are {age} years old")
# Display: Enter your age:
# User types: 25
# Output: You are 25 years old
```

**What this does:** The optional prompt parameter displays a message to guide the user. This is the standard pattern - always provide a helpful prompt so users know what to enter.

### Example 3: Edge Case

```python
# Converting input to numbers
age_str = input("Enter age: ")
age_num = int(age_str)  # Convert string to integer

# Or combined:
age = int(input("Enter age: "))
# If user enters non-number, raises ValueError
```

**What this shows:** `input()` ALWAYS returns a string, even if user types numbers. You must explicitly convert to `int()`, `float()`, etc. Invalid conversion raises exception.

---

## Pattern Classification

**This term is:** I/O FUNCTION (Input)

**Similar terms in this pattern:**

1. `print` - Output function (I/O pair with `input`)
2. `open` - File I/O function
3. `read` - Method for reading from files

**Pattern rule:** I/O functions should use verb forms (infinitive) or noun forms depending on language. They perform actions that interact with external sources (users, files, network).


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "in-" (in) + "putare" (to reckon/think). Through medieval Latin "inputare" (to input/enter), it became English "input" - putting information into a system.

**Why Python uses this:** "Input" is the standard term for data entering a program, contrasting with "output" (data leaving). Most programming languages use "input" or equivalent. Python 3 simplified to `input()` (Python 2 had both `input()` and `raw_input()`).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `input()` function reads from standard input (stdin), which typically comes from keyboard in interactive programs. It displays an optional prompt, waits for the user to type text and press Enter, then returns that text as a string (excluding the newline).

Program execution blocks (pauses) at `input()` until the user provides input. This makes programs interactive - they can ask questions and respond to user answers. The returned value is ALWAYS a string in Python 3, regardless of what the user types.

For non-string data, you must convert explicitly: `int(input("Number: "))` converts to integer, `float(input("Price: "))` to decimal number. If conversion fails (user enters invalid data), Python raises `ValueError` which you can catch with try-except.

**Key behaviors:**

1. **Blocking operation:** Program stops and waits at `input()`. In GUI applications or web servers, this behavior is problematic - blocking the main thread freezes the interface. `input()` is for console/terminal programs.

2. **Always returns string:** Even `input("Age: ")` with user typing "25" returns string `"25"`, not integer 25. Must convert: `int(input(...))`. This prevents type errors and makes conversion explicit.

3. **Prompt is optional:** `input()` without arguments works but provides no guidance. Always use prompt: `input("Enter name: ")` is better UX than bare `input()`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (the input data) or verb (action of inputting)
- **Action vs State:** Can be either - "input" can mean the data (noun) or the act of entering data (verb)
- **Temporal aspect:** Instantaneous action or state of data

### Recommended Form

**Primary recommendation:** Use noun form meaning "input" or "entry." In most languages, "input" can be both noun and verb; the noun form (the data entering) is typically more natural for a function name.

**Forms to AVOID:**

- ❌ Using "read" exclusively - while related, "input" is more specific for user input
- ❌ Using "ask" - that's prompting, not receiving the input
- ❌ Using "receive" - too general; "input" is standard technical term

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ✅ Meaning 1: **DATA ENTERING A SYSTEM** (computing)
- ❌ Meaning 2: "Contribution to a discussion" (opinion/feedback)
- ❌ Meaning 3: "Power/energy input" (electrical)

**Example:**

English "input" can mean:

1. "`input()` gets data from user" (computing - data entry) ✅ **This is the Python meaning**
2. "I need your input on this decision" (opinion/contribution) ❌
3. "The device requires 120V input" (electrical power) ❌

**Your translation should capture meaning #1: data or information entering a program from an external source (user, file, etc.).**

In technical contexts, "input" vs. "output" are standard terms. Use the computing sense, not general "contribution."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `input`, check these translations:**

- [ ] `print` - I/O pair; should feel related but opposite
- [ ] `open` - File I/O; should use compatible verb/noun form
- [ ] `read` - Related but distinct; avoid confusion

**Consistency rule:**

I/O functions (`input`, `print`, `open`, `read`) should use compatible grammatical forms. They're all interactions with external sources. If using verbs, use infinitive consistently.


### Functional relationships

**This term works WITH:**

1. **`input` + `print`**: Interactive I/O loop

```python
name = input("Enter name: ")
print(f"Hello, {name}")
```

2. **`input` + type conversion**: Getting typed data

```python
age = int(input("Enter age: "))
price = float(input("Enter price: "))
```

**Common pairing:**

```python
# basic input
name = input("Name: ")

# input with conversion
age = int(input("Age: "))

# input in loop (interactive menu)
while True:
    choice = input("Command (q to quit): ")
    if choice == 'q':
        break

# input with validation
while True:
    try:
        num = int(input("Enter number: "))
        break
    except ValueError:
        print("Invalid number!")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `input`

- Universal I/O concept (all languages handle user input)
- "Input" is standard technical term globally
- Clear opposite of "output"
- Well-established in CS education

**For this term:** EASY

**Rationale:** Input/output are fundamental computing concepts. Every programming language handles user input. The term "input" (or its equivalent) is standard technical vocabulary across languages. Translation is straightforward: use the computing term for "input."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: whether to use native term or English loanword "input" (common in some languages' technical vocabulary).

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures USER INPUT concept (data entering program)?
- [ ] Understood as receiving data, not asking for it?
- [ ] Distinct from "read" (file operation) and "print" (output)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun or infinitive verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Pairs naturally with `print` (input/output pair)?
- [ ] Compatible form with other I/O functions?
- [ ] Aligns with computing terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard technical term)?

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
term: input
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
