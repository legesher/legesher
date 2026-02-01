# Python Builtin Function: `round` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb/noun (mathematical function)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `round` function in Python rounds a number to a specified number of decimal places. Without a second argument, rounds to the nearest integer. Uses "round half to even" (banker's rounding) to reduce cumulative rounding errors. Returns int when rounding to zero decimals, float otherwise.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Round to nearest integer
result = round(3.7)
print(result)  # Output: 4

# Round down when closer to lower integer
result = round(3.2)
print(result)  # Output: 3
```

**What this does:** `round()` with one argument rounds to the nearest whole number. 3.7 is closer to 4, so rounds up. 3.2 is closer to 3, so rounds down. Returns an integer.

### Example 2: Common Pattern

```python
# Round to specific decimal places
pi = 3.14159265
rounded = round(pi, 2)
print(rounded)  # Output: 3.14 (two decimal places)

# Round to tens place (negative decimals)
value = 1234.56
rounded = round(value, -1)
print(rounded)  # Output: 1230.0 (rounded to nearest 10)
```

**What this does:** Second parameter specifies decimal places. Positive values round after decimal point. Negative values round before decimal point (tens, hundreds, etc.). Returns float when decimals specified.

### Example 3: Edge Case

```python
# Banker's rounding (round half to even)
print(round(2.5))  # Output: 2 (even)
print(round(3.5))  # Output: 4 (even)
print(round(4.5))  # Output: 4 (even)

# Floating-point precision issues
print(round(2.675, 2))  # Output: 2.67 (not 2.68!)
# Due to binary representation: 2.675 is actually ~2.674999...

# Negative numbers
print(round(-3.7))  # Output: -4
print(round(-3.2))  # Output: -3
```

**What this shows:** Python uses "round half to even" (banker's rounding) - when exactly halfway, rounds to nearest even number. This reduces statistical bias. Floating-point representation can cause surprising results. Negative numbers round away from zero when > .5.

---

## Pattern Classification

**This term is:** MATHEMATICAL TRANSFORMATION FUNCTION

**Similar terms in this pattern:**

1. `abs` - Transforms to absolute value
2. `int` - Transforms to integer (truncation)
3. `float` - Transforms to floating-point
4. `ceil`/`floor` (in math module) - Round up/down

**Pattern rule:** Mathematical transformation functions use verb or noun forms naming the operation. "Round" describes the rounding transformation.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `abs` | absoluto | مطلق | 绝对值 | निरपेक्ष |
| `int` | entero | عدد_صحيح | 整数 | पूर्णांक |
| `round` | **redondear** | **تقريب** | **四舍五入** | **पूर्णांकित** |

---

## Etymology (Brief)

**English Origin:** Old French/Latin

**Root meaning:** Old French "rond" (circular), from Latin "rotundus" (round, circular). In mathematics, "to round" means to reduce precision by approximating to a simpler value - conceptually like smoothing sharp corners into a round shape.

**Why Python uses this:** "Round" is the universal mathematical term for approximating numbers to fewer decimal places. Clear, concise verb that describes the transformation. Used consistently across programming languages and calculators.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `round()` function approximates a number to a specified precision by reducing decimal places. It takes two parameters: the number to round (required) and the number of decimal places (optional, defaults to 0). For `round(x, n)`, it returns x rounded to n digits after the decimal point.

Python uses "round half to even" (also called banker's rounding or unbiased rounding). When a number is exactly halfway between two possibilities (like 2.5), it rounds to the nearest even number. This prevents systematic upward bias in repeated rounding operations - half the halfway cases round up, half round down (to even).

The return type depends on parameters: `round(x)` (no second arg) returns int. `round(x, n)` where n > 0 returns float. Negative n rounds to positions left of decimal: `round(1234, -2)` rounds to nearest hundred (1200.0).

**Key behaviors:**

1. **Banker's rounding:** Halfway cases round to even. `round(0.5)` → 0 (even), `round(1.5)` → 2 (even), `round(2.5)` → 2 (even). Reduces cumulative error in statistical calculations. Different from "round half up" used in elementary school.

2. **Type changes:** `round(x)` returns int (if x is finite). `round(x, n)` where n is specified returns float, even if result has no fractional part. `round(3.9)` → 4 (int), `round(3.9, 0)` → 4.0 (float).

3. **Floating-point surprises:** Binary floating-point representation causes unexpected results. `round(2.675, 2)` → 2.67 (not 2.68) because 2.675 in binary is actually ~2.6749999... Use `decimal` module for exact decimal arithmetic when precision critical.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (transformation action)
- **Action vs State:** ACTION - performs rounding
- **Temporal aspect:** Instantaneous transformation

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "redondear", "arrondir" - to round |
| Germanic (de, nl, sv) | Infinitive verb | "runden", "afronden" - to round |
| Slavic (ru, pl, uk) | Infinitive verb | "округлить", "zaokrąglić" - to round |
| Arabic | Verbal noun (masdar) | "تقريب" - rounding/approximation |
| Chinese | Verb phrase | "四舍五入", "取整" - round off |
| Hindi | Verbal noun/infinitive | "पूर्णांकित करना", "गोल करना" - to round |

**Primary recommendation:** Use infinitive verb form meaning "to round" or "to approximate." This is an action that transforms a number.

**Forms to AVOID:**

- ❌ Using adjective "circular" - geometric meaning, not mathematical
- ❌ Using noun "circle" - wrong concept
- ❌ Using "approximate" when "round" is more specific

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `redondear`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish mathematical term for rounding. From "redondo" (round/circular). Natural in "redondear un número" (round a number). Universally used in Spanish mathematics and calculators.

**Arabic:**

- **Translation:** `تقريب` (taqrīb)
- **Form:** Verbal noun (masdar)
- **Why it works:** Standard Arabic word for rounding/approximation. From root ق-ر-ب (to be near/approach). Used in Arabic mathematics for rounding operations. Clear mathematical meaning.

**Chinese:**

- **Translation:** `四舍五入` (sìshěwǔrù) or `取整` (qǔzhěng)
- **Form:** Idiomatic phrase or verb
- **Why it works:** `四舍五入` = "four discard five enter" - describes "round down if <5, up if ≥5" rule. Traditional Chinese rounding term. `取整` = "take integer" - shorter, more modern. Both widely recognized.

**Hindi:**

- **Translation:** `पूर्णांकित करना` (pūrṇāṅkit karnā) or `गोल करना` (gol karnā)
- **Form:** Verbal phrase
- **Why it works:** `पूर्णांकित करना` = "to make whole/integer" (technical term). `गोल करना` = "to round/make round" (more colloquial). `पूर्णांकित` more formal/mathematical. Both valid.

### ❌ Common Translation Mistakes

**Mistake 1: Using adjective "redondo" instead of verb "redondear"**

- **Wrong:** `redondo` (Spanish - "round" - adjective)
- **Why wrong:** "Redondo" describes something circular/round (adjective). Need verb form for the action of rounding. "Redondear" is the infinitive verb.
- **Right:** `redondear` (to round - verb)

**Mistake 2: Using "aproximar" when "redondear" is more specific**

- **Wrong:** `aproximar` (Spanish - "to approximate")
- **Why wrong:** "Aproximar" is too general - means any approximation. "Redondear" specifically means rounding (approximating to specified decimal places). More precise term is better.
- **Right:** `redondear` (to round - specific type of approximation)

**Mistake 3: Using "circular" or geometric rounding**

- **Wrong:** `hacer_circular` (Spanish - "make circular")
- **Why wrong:** Confuses geometric concept (making something round/circular) with mathematical rounding. Different meanings. Use mathematical term.
- **Right:** `redondear` (mathematical rounding)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Round" as shape/adjective (circular)
- ✅ Meaning 2: **MATHEMATICAL ROUNDING** - approximate to fewer decimal places
- ❌ Meaning 3: "Round" as in sports/games (one complete sequence)
- ❌ Meaning 4: "Round" as journey ("round trip")

**Example:**

English "round" can mean:

1. "A round table" (circular shape) ❌
2. "`round(3.7)` returns 4" (mathematical rounding) ✅ **This is the Python meaning**
3. "First round of tournament" (sequence/iteration) ❌
4. "Round trip ticket" (there and back) ❌

**Your translation should capture meaning #2: the mathematical operation of approximating a number to a specified precision.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `round`, check these translations:**

- [ ] `int` - Related type conversion (truncation vs rounding)
- [ ] `abs` - Mathematical transformation function
- [ ] `float` - Numeric type; `round` often returns float
- [ ] `ceil`/`floor` (math module) - Related rounding concepts

**Consistency rule:**

Mathematical transformation functions should use verb forms (infinitive) for action-oriented operations. `round`, like other transformations, performs an action on the number.

**Example:**

Spanish: `redondear`, `convertir_a_entero`, `calcular_absoluto` - verb forms ✅
(Note: `int`, `abs` may be nouns, but `round` as verb is standard)

### Functional relationships

**This term works WITH:**

1. **`round` to integer**: Remove decimals

```python
round(3.7)  # 4
round(3.2)  # 3
```

2. **`round` to precision**: Specify decimal places

```python
round(3.14159, 2)  # 3.14
round(1234.56, -2)  # 1200.0
```

**Common pairing:**

```python
# Basic rounding to integer
print(round(3.7))  # 4
print(round(3.2))  # 3
print(round(3.5))  # 4 (banker's rounding)

# Rounding to decimal places
pi = 3.14159265359
print(round(pi, 2))   # 3.14
print(round(pi, 4))   # 3.1416
print(round(pi, 0))   # 3.0 (float, not int)

# Rounding to tens, hundreds
value = 1234.56
print(round(value, -1))  # 1230.0 (nearest 10)
print(round(value, -2))  # 1200.0 (nearest 100)
print(round(value, -3))  # 1000.0 (nearest 1000)

# Banker's rounding examples
print(round(0.5))  # 0 (to even)
print(round(1.5))  # 2 (to even)
print(round(2.5))  # 2 (to even)
print(round(3.5))  # 4 (to even)

# Negative numbers
print(round(-3.7))  # -4
print(round(-3.2))  # -3
print(round(-3.5))  # -4 (to even)

# Money calculations
price = 19.99
tax_rate = 0.08
total = price * (1 + tax_rate)
rounded_total = round(total, 2)  # 21.59

# Percentage formatting
ratio = 0.66666
percentage = round(ratio * 100, 1)  # 66.7%

# List of rounded values
values = [3.14159, 2.71828, 1.41421]
rounded = [round(v, 2) for v in values]  # [3.14, 2.72, 1.41]
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `round`

- Universal mathematical concept (taught globally)
- "Rounding" is standard term in mathematics
- All calculators and programming languages have rounding
- Well-established terminology

**For this term:** EASY

**Rationale:** Rounding is a fundamental mathematical operation taught in elementary school worldwide. Every language has a standard verb for this operation. Translation is straightforward: use the mathematical term for rounding numbers.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: Distinguish mathematical rounding from geometric "round" (circular shape). Context makes the mathematical meaning clear.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MATHEMATICAL ROUNDING concept?
- [ ] Understood as approximation to fewer decimals?
- [ ] Distinguished from geometric "round" (circular)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (infinitive verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of transformation functions?
- [ ] Uses mathematical terminology?
- [ ] Aligns with calculator/math education terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard math term)?

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
term: round
language: es
translation: redondear
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "redondear" is the universal mathematical term for rounding numbers. It's an infinitive verb form matching Python's action-oriented builtin functions. Standard term used on calculators, in mathematics education, and programming contexts.

**Alternatives considered:**

1. `aproximar` (approximate) - Too general; "redondear" more specific
2. `redondo` (round - adjective) - Wrong part of speech
3. `hacer_redondo` (make round) - Verbose; infinitive verb better

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Rounding is a universal mathematical concept with clear, standard translations in all languages.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
