# Python Keyword: `else` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `else` keyword in Python introduces an alternative code block that executes when a preceding `if` condition is false, when a loop (`for`/`while`) completes normally, or when a `try` block doesn't raise an exception. It represents the "otherwise" case in control flow.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic if-else
x = 10
if x > 20:
    print("Greater than 20")
else:
    print("20 or less")
# Output: 20 or less
```

**What this does:** When the `if` condition is false, the `else` block executes. Only one branch runs - either `if` or `else`, never both. This provides binary decision making: do X or do Y.

### Example 2: Common Pattern

```python
# for-else: executes if loop completes without break
numbers = [1, 3, 5, 7, 9]
for num in numbers:
    if num == 4:
        print("Found 4")
        break
else:
    print("4 not found in list")
# Output: 4 not found in list
```

**What this does:** The `else` block after a `for` loop runs only if the loop completes normally (doesn't exit via `break`). This is Python's elegant pattern for "search succeeded vs. failed" logic.

### Example 3: Edge Case

```python
# try-except-else: runs if no exception occurred
try:
    result = int("42")
except ValueError:
    print("Conversion failed")
else:
    print(f"Success: {result}")
# Output: Success: 42
```

**What this shows:** In try-except structures, `else` runs when the `try` block succeeds (no exception raised). This separates "successful operation code" from "error handling code" cleanly.

---

## Pattern Classification

**This term is:** ALTERNATIVE CLAUSE KEYWORD

**Similar terms in this pattern:**

1. `elif` - Alternative condition (combines "else" + "if")
2. `except` - Alternative for exception cases in try blocks
3. `finally` - Unconditional alternative (always runs after try)

**Pattern rule:** Alternative clause keywords should use conjunction or particle forms expressing contrast or alternative. "Else" means "otherwise" or "in the other case."

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `if` | si | إذا | 如果 | यदि |
| `elif` | sino_si | والا_إذا | 否则如果 | नहींतो_यदि |
| `else` | **sino** | **والا** | **否则** | **नहींतो** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "elles" meant "otherwise, in another way." It's the genitive form of "el-" (other/else), related to Latin "alius" (other). "Else" fundamentally expresses "the other case."

**Why Python uses this:** "Else" is the natural English word for presenting an alternative. In everyday speech: "If X, do Y, else do Z." Guido van Rossum extended this beyond `if-else` to loops (for-else, while-else) and exception handling (try-except-else) - a Python innovation not found in most languages.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `else` keyword introduces an alternative execution path in Python's control structures. Its behavior varies by context but always means "in the other case" or "otherwise":

**With if statements:** `else` executes when all preceding `if`/`elif` conditions are false. It's the catch-all: "if none of the above, then do this." Only one branch in an if-elif-else chain executes.

**With loops:** `else` after `for` or `while` executes when the loop completes normally (reaching the end of iteration or condition becoming false). Crucially, it does NOT run if the loop exits via `break`. This enables "search and report failure" patterns: try to find something in a loop, break if found, else report not found.

**With try blocks:** `else` after `try-except` executes when no exception occurs in the `try` block. It runs before `finally` (if present). This separates happy-path code (else) from error handling (except), improving code clarity.

**Key behaviors:**

1. **Mutually exclusive execution:** In if-else chains, exactly one block executes (the first true condition, or else if all false). The `else` is the default/fallback.

2. **Loop-else semantics:** This is Python-specific and often surprising to programmers from other languages. `else` after a loop means "if we didn't break out." It's not "if loop didn't run" - it's "if loop completed naturally."

3. **Optional everywhere:** `else` is always optional. You can have `if` without `else`, `for` without `else`, `try-except` without `else`. Adding `else` provides explicit handling for the alternative case.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adversative/alternative conjunction
- **Action vs State:** Neither - it's a structural marker indicating alternative branch
- **Temporal aspect:** Immediate - introduces alternative that executes if condition fails

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adversative conjunction | "sino", "sinon" - meaning "otherwise" |
| Germanic (de, nl, sv) | Adversative conjunction/adverb | "sonst", "anders" - otherwise |
| Slavic (ru, pl, uk) | Adversative conjunction | "иначе", "inaczej" - otherwise |
| Arabic | Adversative particle | "والا" or "غير ذلك" - otherwise |
| Chinese | Adversative conjunction | "否则" - otherwise/if not |
| Hindi | Adversative conjunction | "नहीं तो" or "वरना" - otherwise |

**Primary recommendation:** Use your language's word for "otherwise" or "if not." This should be a conjunction or particle that introduces an alternative scenario. The word should feel like the natural opposite of "if."

**Forms to AVOID:**

- ❌ Using negative "not" alone - `else` needs the alternative sense, not just negation
- ❌ Using "or" (disjunction) - `else` is conditional alternative, not logical OR
- ❌ Using "then" - that goes with "if," not with the alternative

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `sino`
- **Form:** Adversative conjunction
- **Why it works:** "Sino" means "but rather/otherwise" in Spanish. It's the natural alternative marker: "si no X, sino Y" (if not X, but rather Y). Standard in Spanish programming. Note: distinct from "pero" (but - contrast) and "o" (or - option).

**Arabic:**

- **Translation:** `والا` (wa illā) or `غيرذلك` (ghayr dhālik)
- **Form:** Adversative particle
- **Why it works:** "والا" (wa illā) means "otherwise/if not." Common in conditional expressions. Alternative: "غير ذلك" (ghayr dhālik = other than that). Both convey alternative case clearly.

**Chinese:**

- **Translation:** `否则` (fǒuzé)
- **Form:** Adversative conjunction
- **Why it works:** Standard Chinese for "otherwise/if not." Two characters: 否 (not/negative) + 则 (then/in that case). Widely used in programming and logical expressions. Clear alternative meaning.

**Hindi:**

- **Translation:** `नहींतो` (nahīṁ to) or `वरना` (varnā)
- **Form:** Adversative conjunction/particle
- **Why it works:** "नहीं तो" literally "if not then" - clear alternative. "वरना" means "otherwise." Both formal and natural in Hindi. Can be written together or as two words depending on convention.

### ❌ Common Translation Mistakes

**Mistake 1: Using generic "but" instead of "otherwise"**

- **Wrong:** `pero` (Spanish - "but")
- **Why wrong:** "But" expresses contrast between facts ("I'm tired but happy"). "Else" expresses conditional alternative ("if not X, do Y"). Different logical relationships.
- **Right:** `sino` (otherwise/but rather)

**Mistake 2: Using "or" (logical OR)**

- **Wrong:** `o` (Spanish - "or")
- **Why wrong:** "Or" offers simultaneous options ("tea or coffee"). "Else" provides conditional fallback ("if condition fails, then do this"). Confuses alternatives with options.
- **Right:** `sino`

**Mistake 3: Using only "not" without alternative sense**

- **Wrong:** `no` (Spanish - "not")
- **Why wrong:** "Not" is pure negation. "Else" requires both negation of condition AND introduction of alternative action. Need "otherwise" sense, not just "not."
- **Right:** `sino` (incorporates both negation and alternative)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Additional, more" (adjective - "what else do you want?")
- ❌ Meaning 2: "Different" (adjective - "someone else")
- ✅ Meaning 3: **CONDITIONAL ALTERNATIVE** - "otherwise, if not, in the other case"

**Example:**

English "else" can mean:

1. "What else happened?" (additional/more) ❌
2. "Someone else did it" (different/other) ❌
3. "If not X, else do Y" (conditional alternative) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: the alternative action when a condition is not met.**

Many languages have different words for:
- "Else" as "other/different" (adjective)
- "Else" as "otherwise" (conditional alternative)

Use the CONDITIONAL ALTERNATIVE form (otherwise/if not), not the adjective "other."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `else`, check these translations:**

- [ ] `if` - `else` is the natural opposite/alternative to `if`
- [ ] `elif` - Usually compound of `else` + `if` (must be consistent)
- [ ] `except` - Similar alternative clause role in try-except

**Consistency rule:**

`elif` is typically formed by combining your translations of `else` and `if`. Ensure they work together naturally. For example, Spanish: `elif` → `sino si` (else if) or contracted.

**Example:**

If `else` → `sino` and `if` → `si`, then `elif` should be `sino_si` or similar compound ✅

### Functional relationships

**This term works WITH:**

1. **`if` + `else`**: Basic conditional branching
```python
if condition:
    do_something()
else:
    do_alternative()
```

2. **`if` + `elif` + `else`**: Multi-way branching
```python
if x > 0:
    print("positive")
elif x < 0:
    print("negative")
else:
    print("zero")
```

**Common pairing:**

```python
# if-else for binary decisions
if is_valid:
    process()
else:
    reject()

# for-else for search patterns
for item in collection:
    if matches(item):
        found = item
        break
else:
    print("Not found")

# try-except-else for success handling
try:
    data = load_file()
except FileNotFoundError:
    handle_error()
else:
    process(data)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `else`:

- Universal conditional logic concept
- Every language expresses "otherwise/if not"
- Well-documented in programming globally
- Clear role as alternative clause

**For this term:** EASY

**Rationale:** The concept of "otherwise" or "in the other case" exists in all human languages. It's fundamental to conditional reasoning. Translation is straightforward: find the word meaning "otherwise" in conditional contexts.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The only consideration: distinguishing "else" (conditional alternative) from "or" (logical disjunction) and "but" (contrast). Use "otherwise" concept, not "or" or "but."

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ALTERNATIVE/OTHERWISE concept?
- [ ] Works in conditional context (if not X, do Y)?
- [ ] Distinct from "or" (options) and "but" (contrast)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adversative conjunction/particle)?
- [ ] Expresses conditional alternative (not just difference)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Natural opposite/complement to `if` translation?
- [ ] Forms logical compound with `if` for `elif`?
- [ ] Compatible with other alternative keywords (`except`, `finally`)?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common conditional word)?

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
term: else
language: es
translation: sino
form: adversative_conjunction
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "sino" is the standard adversative conjunction meaning "but rather/otherwise" - perfect for conditional alternatives. It forms natural compound with `si` (if) for `elif` → `sino si`. Universally used in Spanish programming and logical expressions.

**Alternatives considered:**

1. `pero` (but - contrast) - Wrong type of opposition (factual contrast vs. conditional alternative)
2. `o` (or - disjunction) - Offers options, doesn't express conditional fallback
3. `de_otro_modo` (otherwise - phrase) - Too verbose; `sino` is standard

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Conditional alternatives ("otherwise") are universal in human languages and programming.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
