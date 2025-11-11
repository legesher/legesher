# Python Keyword: `return` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `return` keyword in Python exits a function and optionally sends a value back to the caller. It marks the end of function execution and specifies what result (if any) the function produces. Functions without explicit `return` statements implicitly return `None`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Return a calculated value
def add(a, b):
    return a + b

result = add(5, 3)  # result = 8
```

**What this does:** The `return` statement sends the value `a + b` back to the caller. Function execution stops immediately at `return`. The returned value becomes the result of the function call expression.

### Example 2: Common Pattern

```python
# Early return for validation
def divide(a, b):
    if b == 0:
        return None  # Early exit on error
    return a / b

answer = divide(10, 0)  # answer = None
```

**What this does:** Demonstrates multiple return points. If `b` is zero, the function returns `None` immediately (early return pattern). Otherwise, it continues to the division return. Only one return executes per function call.

### Example 3: Edge Case

```python
# Return without value (implicitly returns None)
def greet(name):
    print(f"Hello, {name}")
    return  # Explicit return without value

# Function with no return statement
def display_message():
    print("Message")
# Implicitly returns None when function ends
```

**What this shows:** `return` without a value returns `None`. Functions without any `return` statement also implicitly return `None` when they complete. You can use bare `return` to exit early from void-like functions.

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Function Control)

**Similar terms in this pattern:**

1. `break` - Exits loop early (loop equivalent of return)
2. `yield` - Returns value but pauses function (generator)
3. `raise` - Exits function by raising exception

**Pattern rule:** Function/loop exit keywords should use verb forms (infinitive). They perform actions that alter control flow by terminating or suspending execution.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `break` | romper | كسر | 中断 | तोड़ना |
| `yield` | ceder | ينتج | 产生 | उत्पन्न |
| `return` | **retornar** | **إرجاع** | **返回** | **वापसी** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "re-" (back) + "tornare" (to turn). Through Old French "retourner," it became English "return" meaning "to turn back, go back, give back." In programming, "return" metaphorically gives back a value to the caller.

**Why Python uses this:** "Return" clearly expresses both actions: (1) going back to the caller, (2) giving back a value. Most programming languages use "return" for this dual concept. It's more precise than alternatives like "yield" (temporary), "send" (one-way), or "result" (noun).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `return` statement performs two related actions: it terminates function execution immediately and optionally sends a value back to the calling code. When Python encounters `return`, it stops executing the current function, discards the local scope, and transfers control back to where the function was called.

The syntax `return expression` evaluates the expression and sends its value to the caller. If no expression is provided (bare `return`), the function returns `None`. If a function reaches its end without hitting a `return` statement, Python implicitly adds `return None`.

Functions can have multiple `return` statements in different branches (if-else, try-except), but only one executes per function call. This enables early-return patterns: validate inputs and return error values early, avoiding deeply nested conditionals. The returned value can be any Python object: numbers, strings, lists, even other functions.

**Key behaviors:**

1. **Immediate termination:** Code after `return` in the same block never executes. This makes `return` useful for early exits: check error conditions, return failure value, avoid executing remaining code.

2. **Single value (or tuple):** `return x, y` looks like returning multiple values, but it actually returns a single tuple `(x, y)`. Python doesn't truly return multiple values - it packs them into one tuple. Callers can unpack: `a, b = func()`.

3. **None as default:** Functions without explicit return or with bare `return` yield `None`. This makes procedural functions (called for side effects like `print()`) consistent - they all return something, even if meaningless.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Transitive verb (takes object - what to return)
- **Action vs State:** Pure ACTION - performs termination and value sending
- **Temporal aspect:** Instantaneous/completive - happens immediately and ends function

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "retornar", "retourner" - to return/give back |
| Germanic (de, nl, sv) | Infinitive verb | "zurückgeben", "terugkeren" - to give back/return |
| Slavic (ru, pl, uk) | Infinitive verb | "вернуть", "zwrócić" - to return/give back |
| Arabic | Masdar (verbal noun) | "إرجاع" (returning/return) or verb form "يرجع" |
| Chinese | Verb compound | "返回" - return/go back |
| Hindi | Verbal noun or infinitive | "वापसी" (return - noun) or "लौटाना" (to return) |

**Primary recommendation:** Use infinitive verb form meaning "to return" or "to give back." Focus on the "giving back a value" meaning, not just "going back to a place."

**Forms to AVOID:**

- ❌ Using noun "the return" - should be verb "to return"
- ❌ Using "come back" (movement) vs. "give back" (value transfer)
- ❌ Past tense "returned" - should be present/infinitive

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `retornar`
- **Form:** Infinitive verb
- **Why it works:** Standard verb meaning "to return/give back." Used in Spanish programming for function returns. Distinct from `volver` (come back to place). `Retornar un valor` is natural technical Spanish. Also used in mathematics and formal contexts.

**Arabic:**

- **Translation:** `إرجاع` (irjāʿ)
- **Form:** Masdar (verbal noun)
- **Why it works:** Means "returning/giving back." Standard in Arabic CS terminology. Root ر-ج-ع (r-j-ʿ) means return/go back. Masdar form commonly used for function names in Arabic programming contexts.

**Chinese:**

- **Translation:** `返回` (fǎnhuí)
- **Form:** Verb compound
- **Why it works:** Two characters: 返 (return/go back) + 回 (return/back). Standard Chinese programming term for function return. Used universally in Chinese CS education. Clear "give back value" meaning.

**Hindi:**

- **Translation:** `वापसी` (vāpsī) or `लौटाना` (lauṭānā)
- **Form:** Verbal noun or infinitive verb
- **Why it works:** `वापसी` means "return/coming back" (noun form common in Hindi). `लौटाना` is infinitive "to return." Both acceptable; verbal noun may be more natural for function names in Hindi technical writing.

### ❌ Common Translation Mistakes

**Mistake 1: Using "come back" (movement) vs. "give back" (value)**

- **Wrong:** `volver` (Spanish - "to come back/return to place")
- **Why wrong:** "Volver" emphasizes physical return to location ("volver a casa" = return home). Programming `return` emphasizes giving back a value. "Retornar" better captures value transfer.
- **Right:** `retornar` (give back/return value)

**Mistake 2: Using noun form instead of verb**

- **Wrong:** `retorno` (Spanish - "the return" - noun)
- **Why wrong:** Keywords are actions (verbs), not things (nouns). Function name should be "to return" (action), not "the return" (result).
- **Right:** `retornar` (verb infinitive)

**Mistake 3: Using "send" or "output"**

- **Wrong:** `enviar` (Spanish - "to send")
- **Why wrong:** "Send" implies one-way transfer. "Return" implies completing a transaction - going back AND giving back. "Return" has specific meaning in function context that "send" lacks.
- **Right:** `retornar` (captures both return-to-caller and give-value)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Come back to a place" (physical movement - "return home")
- ❌ Meaning 2: "Give back a borrowed item" (restore possession - "return the book")
- ✅ Meaning 3: **GIVE BACK A VALUE TO CALLER** (function result transfer)

**Example:**

English "return" can mean:

1. "I'll return to Paris next year" (go back to place) ❌
2. "Please return my pen" (give back borrowed item) ⚠️ (closer - involves giving back)
3. "`return result` sends value to caller" (function value transfer) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: terminating function and sending a value back to the calling code.**

Many languages distinguish:
- Return to place (physical movement): volver, regreso
- Return a value (function context): retornar, devolver

Use the FUNCTION VALUE RETURN meaning. In some languages, the same word covers both (which is acceptable), but if your language distinguishes, use the "give back value" word, not the "go back to place" word.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `return`, check these translations:**

- [ ] `yield` - Similar concept (gives value) but pauses vs. exits; should use related verb form
- [ ] `break` - Exits loop; `return` exits function; both should use verb forms
- [ ] `def` - Defines functions that contain return statements; should feel cohesive

**Consistency rule:**

All action keywords (`return`, `break`, `continue`, `yield`, `raise`) should use verb forms (infinitive). They perform control flow actions. Don't mix verb and noun forms across these keywords.

**Example:**

Spanish: `retornar`, `romper`, `continuar`, `ceder`, `lanzar` - all infinitive verbs ✅
NOT: `retornar` (verb) + `pausa` (noun for break) ❌

### Functional relationships

**This term works WITH:**

1. **`def` + `return`**: Functions are defined to return values
```python
def calculate(x):
    return x * 2
```

2. **`return` + expression**: Returns computed values
```python
def get_status():
    return "ready" if initialized else "waiting"
```

**Common pairing:**

```python
# return with values
def square(n):
    return n ** 2

# early return pattern
def validate(data):
    if not data:
        return False
    return check(data)

# return None (implicit or explicit)
def log_message(msg):
    print(msg)
    # implicitly returns None

# return multiple values (tuple unpacking)
def get_coordinates():
    return x, y  # returns tuple (x, y)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `return`:

- Universal programming concept (all languages have function returns)
- Clear semantic mapping in most languages
- Well-documented globally
- Distinction from "go back to place" usually clear in technical contexts

**For this term:** EASY

**Rationale:** Function return is fundamental to programming. Every language with functions has a return mechanism. While some languages distinguish "return to place" from "return a value," the programming context makes the intended meaning clear. Standard translations exist across all languages.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Some languages might debate between "return/give back" (retornar/devolver in Spanish). Check which is more common in that language's CS education.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FUNCTION RETURN concept (giving back value to caller)?
- [ ] Emphasizes value transfer, not just physical return to place?
- [ ] Understood as terminating function execution?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive, not past tense)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other action keywords (`break`, `yield`)?
- [ ] Uses verb form like other function control keywords?
- [ ] Aligns with how functions are discussed in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common verb)?

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
term: return
language: es
translation: retornar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "retornar" is the standard verb for returning values in programming contexts. It emphasizes "giving back" a value rather than physical return to a location, which distinguishes it from "volver." Widely used in Spanish CS education and technical documentation.

**Alternatives considered:**

1. `devolver` (to return/give back) - Also acceptable, means "give back," common in some regions
2. `volver` (to return to place) - Wrong emphasis (physical location vs. value transfer)
3. `regresar` (to go back) - Similar to volver; emphasizes movement, not value transfer

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Function return is universal in programming. Minor variation: some Spanish-speaking regions prefer "devolver" over "retornar," but both are widely understood and acceptable. Check local CS education materials for preference.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
