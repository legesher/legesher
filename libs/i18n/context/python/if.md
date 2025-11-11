# Python Keyword: `if` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `if` keyword in Python tests a condition and executes a block of code only when that condition evaluates to `True`. It is the fundamental building block for conditional logic, allowing programs to make decisions and branch execution paths based on runtime values.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Check if a number is positive
x = 5
if x > 0:
    print("Positive number")
```

**What this does:** Evaluates whether `x` is greater than 0. If true, prints "Positive number". If false, does nothing and continues to the next statement.

### Example 2: Common Pattern

```python
# Validate user age before granting access
age = 18
if age >= 18:
    print("Access granted")
    allow_entry = True
```

**What this does:** Tests if age meets the minimum requirement. If the condition is true, executes both statements in the indented block. This demonstrates how `if` can control multiple lines of code.

### Example 3: Edge Case

```python
# Empty collections evaluate to False in if conditions
data = []
if data:
    print("Has data")
# This won't print because empty list is "falsy"
```

**What this shows:** Python's `if` doesn't require explicit boolean comparisons. Empty lists, empty strings, zero, and `None` all evaluate to `False` in conditional contexts. This "truthiness" evaluation is a key Python idiom.

---

## Pattern Classification

**This term is:** STATE KEYWORD

**Similar terms in this pattern:**

1. `elif` - Sequential alternative condition (combines "else" + "if")
2. `while` - Conditional loop that repeats while condition is true
3. `is` - Identity test operator used in conditions

**Pattern rule:** All conditional test keywords should use conjunction or present tense form in target language, NOT imperative verb form. They describe state/condition, not commands.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `while` | mientras | بينما | 当 | जबकि |
| `elif` | sino_si | والا_إذا | 否则如果 | नहींतो_यदि |
| `if` | **si** | **إذا** | **如果** | **यदि** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "gif" meant "if, whether, though" - expressing condition or supposition. Related to German "ob" (whether) and Dutch "of" (if/whether).

**Why Python uses this:** "if" is the universal English conditional particle, immediately recognizable to English speakers. Guido van Rossum chose simple, readable English words to make Python accessible, avoiding cryptic symbols like `?` (ternary operator in C) for basic conditionals.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `if` keyword implements conditional branching in Python's control flow. It evaluates an expression (the "condition") and converts it to a boolean value. If the result is `True`, Python executes the indented code block following the `if` statement. If `False`, Python skips that block entirely and continues with the next unindented statement.

The condition can be any expression that produces a value. Python uses "truthiness" - values like `0`, `None`, `False`, `""` (empty string), `[]` (empty list), and `{}` (empty dict) are considered "falsy" and evaluate to `False` in conditions. All other values are "truthy" and evaluate to `True`.

An `if` statement can stand alone or be combined with `elif` (else-if) and `else` clauses to create multi-branch decision structures. Unlike languages that use braces or keywords to mark block boundaries, Python uses indentation to define which statements belong to the `if` block - this enforces readable code structure.

**Key behaviors:**

1. **Lazy evaluation:** The condition is evaluated exactly once when the `if` line executes. If false, the entire block is skipped without evaluating anything inside it.
2. **Truthiness conversion:** Any Python value can be used as a condition. Python automatically calls `bool()` on the expression to convert it to `True` or `False`.
3. **Indentation-based scope:** All lines indented after the `if` line belong to the conditional block. The first line with less indentation ends the `if` block.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Subordinating conjunction introducing a conditional clause
- **Action vs State:** STATE - tests and describes a condition, does not perform an action
- **Temporal aspect:** Immediate present - evaluates condition at the moment of execution

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Conditional conjunction | "si", "se" - natural conditional particle |
| Germanic (de, nl, sv) | Conditional conjunction | "wenn", "als" - standard conditional word |
| Slavic (ru, pl, uk) | Conditional conjunction | "если", "jeśli" - native conditional particle |
| Arabic | Conditional particle (حرف شرط) | "إذا" - standard conditional particle in MSA |
| Chinese | Conditional word | "如果" - standard two-character conditional |
| Hindi | Conditional conjunction | "यदि" or "अगर" - Sanskrit-derived conditional |

**Primary recommendation:** Use the target language's natural conditional word/particle - the equivalent of "if" in everyday speech. This is NOT a verb and should NOT use verb forms (infinitive or imperative).

**Forms to AVOID:**

- ❌ Imperative verb form - "if" is not a command
- ❌ Infinitive verb - "if" does not express an action "to do"
- ❌ Question form - "if" makes a statement about condition, not a query

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `si`
- **Form:** Conjunction
- **Why it works:** Standard Spanish conditional particle. Same word used in everyday speech ("si llueve, me quedo en casa"). Extremely natural and universally understood.

**Arabic:**

- **Translation:** `إذا` (idhā)
- **Form:** Conditional particle (حرف شرط)
- **Why it works:** Classical and Modern Standard Arabic conditional particle. Used in formal writing and Quranic Arabic. Clear, unambiguous conditional meaning.

**Chinese:**

- **Translation:** `如果` (rúguǒ)
- **Form:** Conditional compound word
- **Why it works:** Standard two-character conditional used in formal Chinese. Universally understood across all Chinese-speaking regions. Alternative `假如` (jiǎrú) also valid but `如果` more common in technical contexts.

**Hindi:**

- **Translation:** `यदि` (yadi)
- **Form:** Conditional conjunction
- **Why it works:** Sanskrit-derived formal conditional. Aligns with technical/educational register. Alternative `अगर` (agar) more colloquial but both acceptable.

### ❌ Common Translation Mistakes

**Mistake 1: Using verb form instead of conjunction**

- **Wrong:** `verificar` (Spanish - "to verify/check")
- **Why wrong:** "If" is not an action verb. It doesn't mean "check whether" - it's a conditional particle. This changes the meaning fundamentally.
- **Right:** `si`

**Mistake 2: Using question particle**

- **Wrong:** `¿` or question form (any language)
- **Why wrong:** "If" makes a conditional statement, not a question. Conditional and interrogative are different grammatical categories.
- **Right:** Use conditional particle, not interrogative

**Mistake 3: Overly formal or archaic term**

- **Wrong:** `假若` (jiǎruò) in Chinese - archaic/literary form
- **Why wrong:** While technically correct, this is rarely used in modern speech or technical writing. Programmers wouldn't recognize it as readily.
- **Right:** `如果` (standard modern conditional)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Provided that, on condition that" (formal conditional)
- ❌ Meaning 2: "Whether" (introducing indirect questions - "I don't know if...")
- ✅ Meaning 3: **HYPOTHETICAL CONDITIONAL** - "in the case that X is true, then Y happens"

**Example:**

English "if" can mean:

1. "Come to the party **if** you want" (permission/option) ❌
2. "Tell me **if** you see John" (whether - interrogative) ❌
3. "**If** temperature > 100, turn off heater" (conditional logic) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: hypothetical conditional testing, NOT permission or indirect questions.**

Many languages distinguish between:
- Conditional "if" (if X then Y)
- Interrogative "if/whether" (I wonder if X)

Use the CONDITIONAL form. For example, Spanish distinguishes `si` (conditional) from `si` (whether/interrogative context) - they're homonyms but grammatically different.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `if`, check these translations:**

- [ ] `elif` - Must use compatible linguistic form (usually compound: "else" + "if")
- [ ] `else` - Must use compatible form (alternative clause marker)
- [ ] `while` - Should use similar conditional particle/conjunction structure

**Consistency rule:**

All conditional/test keywords (`if`, `elif`, `while`) should use the same grammatical category in your target language. If you use a conjunction for `if`, use conjunction forms for the others. Do NOT mix verb forms with conjunction forms.

**Example:**

If you translate `if` as conjunction ("si"), then:

- `elif` should also be conjunction-based ("si no" or "sino si")
- `while` should use conjunction form ("mientras")
- NOT: `if` conjunction + `while` verb form (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`if` + `elif` + `else`**: The complete conditional chain structure
```python
x = 5
if x > 0:
    print("positive")
elif x < 0:
    print("negative")
else:
    print("zero")
```

2. **`if` + boolean operators** (`and`, `or`, `not`): Compound conditions
```python
age = 20
has_license = True
if age >= 18 and has_license:
    print("Can drive")
```

**Common pairing:**

```python
# if frequently appears with comparison operators
x = 5
my_list = [1, 2, 3, 4, 5]

if x == 5:        # equality
    pass
if x != 0:        # inequality
    pass
if x > 10:        # greater than
    pass
if x in my_list:  # membership test
    pass
if not x:         # negation
    pass
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `if`:

- Universal programming concept
- Every natural language has a conditional particle or conjunction
- Well-established translations in CS education globally
- Minimal cultural or linguistic complexity

**For this term:** EASY

**Rationale:** The conditional "if" concept exists in every human language. No language lacks a way to express "if X is true, then do Y." Translation is straightforward: find the target language's standard conditional word. Low risk of error.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

If you're uncertain about the translation, it likely means you're overthinking it or considering the wrong word type (e.g., verb instead of conjunction). Check that you're using the natural conditional particle, not a verb or other form.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the PYTHON CONCEPT (conditional test, not question or action)
- [ ] Would a native speaker understand this introduces a conditional block?
- [ ] Avoids misleading connotations (not interrogative, not optative)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (conjunction/particle, NOT verb)?
- [ ] Correct form (conditional, not interrogative or imperative)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches the pattern of similar keywords (`elif`, `while`)?
- [ ] Same grammatical category as other conditional keywords?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1 word for `if` - should be very brief)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common everyday word)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL for Arabic/Hebrew)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: if
language: es
translation: si
form: conjunction
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "si" is the standard conditional conjunction used in all contexts to express hypothetical conditions. It directly maps to the programming concept of conditional testing. This is the universally recognized term in Spanish CS education and technical documentation.

**Alternatives considered:**

1. `si_entonces` (if_then) - Too verbose; Python doesn't require explicit "then"
2. `cuando` (when) - Wrong meaning; expresses temporal "when" not conditional "if"

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term due to clear one-to-one mapping across all target languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
