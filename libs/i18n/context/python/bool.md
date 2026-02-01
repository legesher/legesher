# Python Builtin Type: `bool` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (type constructor)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `bool` type in Python represents boolean values - `True` or `False`. It's short for "boolean" (named after mathematician George Boole) and is fundamental to logic, conditionals, and control flow in programming.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Boolean values
is_valid = True
is_empty = False

if is_valid:
    print("Valid!")  # This executes
```

**What this does:** Boolean variables store `True` or `False`. Used in conditionals to control program flow. `True` and `False` are the only two `bool` values.

### Example 2: Common Pattern

```python
# Boolean from comparisons
age = 25
is_adult = age >= 18  # True

# Boolean conversion
value = bool(10)      # True (non-zero)
empty = bool(0)       # False (zero)
has_items = bool([])  # False (empty list)
```

**What this does:** Comparison operators return booleans. `bool()` constructor converts values to `True` or `False` using truthiness rules: 0, `None`, empty collections → `False`; everything else → `True`.

### Example 3: Edge Case

```python
# bool is subclass of int
print(True + True)    # Output: 2 (True == 1)
print(False * 5)      # Output: 0 (False == 0)
print(int(True))      # Output: 1

# Boolean operators
result = True and False  # False
result = True or False   # True
result = not True        # False
```

**What this shows:** Historically, `bool` is a subclass of `int` in Python. `True` equals 1 and `False` equals 0 in numeric contexts. You can use booleans in arithmetic, though it's uncommon. Boolean operators (`and`, `or`, `not`) work with bool values.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR / PRIMITIVE TYPE

**Similar terms in this pattern:**

1. `int` - Integer number type
2. `float` - Floating-point number type
3. `str` - String (text) type

**Pattern rule:** Type constructors should use noun forms naming the category. For `bool`, use the noun form of "boolean" (logical true/false type).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `int` | entero | عدد_صحيح | 整数 | पूर्णांक |
| `str` | cadena | سلسلة | 字符串 | स्ट्रिंग |
| `bool` | **booleano** | **منطقي** | **布尔** | **बूलियन** |

---

## Etymology (Brief)

**English Origin:** Named after George Boole

**Root meaning:** George Boole (1815-1864) was an English mathematician who invented Boolean algebra - a system of logic using only two values (true/false). "Boolean" derives from his name + "-ean" suffix (meaning "relating to").

**Why Python uses this:** "Boolean" is the universal term in computer science for true/false logic, adopted from Boolean algebra. Python abbreviates to "bool" like "def" (define) and "str" (string) - keeping function/type names concise while remaining recognizable.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `bool` type represents one of two values: `True` or `False`. These are singleton objects - there's only one `True` object and one `False` object in Python. All boolean variables point to these two objects.

`bool()` constructor converts values to boolean using Python's truthiness rules. "Falsy" values (evaluate to `False`): `False`, `None`, `0`, `0.0`, `""` (empty string), `[]` (empty list), `{}` (empty dict), `set()` (empty set). Everything else is "truthy" (evaluates to `True`).

Technically, `bool` is a subclass of `int` where `True` has value 1 and `False` has value 0. This allows booleans in arithmetic (`True + True == 2`) but is rarely used in practice. The `isinstance(True, int)` check returns `True` due to this inheritance.

**Key behaviors:**

1. **Only two values:** Unlike other types with infinite possibilities, `bool` has exactly two values: `True` and `False`. These are keywords, not strings or variables - capitalization matters.

2. **Truthiness conversion:** Every Python value can be evaluated in boolean context. `if mylist:` is equivalent to `if bool(mylist):`. Python automatically calls `bool()` on values used in conditionals.

3. **Comparison results:** All comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `is`) return `bool`. Logical operators (`and`, `or`, `not`) work with and return boolean values (or use short-circuit evaluation).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (adjective-derived) - names a type
- **Action vs State:** STATE/CATEGORY - describes what something is
- **Temporal aspect:** Timeless - a type is a permanent classification

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adjective-as-noun | "booleano" - boolean/relating to Boole |
| Germanic (de, nl, sv) | Adjective-as-noun | "boolesch" - boolean |
| Slavic (ru, pl, uk) | Adjective or noun | "булев" (Boole's), "логический" (logical) |
| Arabic | Adjective | "منطقي" (logical) or transliteration |
| Chinese | Transliteration | "布尔" (bù'ěr) - Boole's name |
| Hindi | Transliteration | "बूलियन" (būliyan) - boolean |

**Primary recommendation:** Use adjective form meaning "boolean" or "logical." Many languages transliterate "Boolean" from the English (Boole's name). Alternatively, use word for "logical" if that's established in CS education.

**Forms to AVOID:**

- ❌ Using only "true/false" - that's the values, not the type
- ❌ Using "binary" - while related, boolean is specific to logic
- ❌ Using "bit" - that's storage representation, not logical type

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `booleano`
- **Form:** Adjective-as-noun (masculine)
- **Why it works:** Standard Spanish form of "Boolean" (Boole's name + Spanish "-eano" suffix). Used in Spanish CS education for logical true/false type. Natural in "valor booleano" (boolean value).

**Arabic:**

- **Translation:** `منطقي` (manṭiqī) or `بولياني` (būliyānī)
- **Form:** Adjective or transliteration
- **Why it works:** "منطقي" means "logical" - clear and natural. Alternative: "بولياني" (transliteration of Boolean). "منطقي" may be more accessible; both are used in Arabic CS contexts.

**Chinese:**

- **Translation:** `布尔` (bù'ěr) or `布尔型` (bù'ěrxíng)
- **Form:** Transliteration of "Boole"
- **Why it works:** Standard Chinese transliteration of Boolean/Boole's name. Sometimes extended to "布尔型" (Boolean type). Universally recognized in Chinese programming.

**Hindi:**

- **Translation:** `बूलियन` (būliyan)
- **Form:** Transliteration
- **Why it works:** Direct transliteration of "Boolean" widely adopted in Indian CS education. Alternative: "तार्किक" (tārkik - logical) but transliteration more recognizable.

### ❌ Common Translation Mistakes

**Mistake 1: Using "true/false" instead of "boolean"**

- **Wrong:** `verdadero_falso` (Spanish - "true_false")
- **Why wrong:** "True" and "False" are the VALUES of type `bool`. The type itself is "boolean" - the category containing those two values. Like confusing 5 (value) with `int` (type).
- **Right:** `booleano` (the type name)

**Mistake 2: Using "binary" instead of "boolean"**

- **Wrong:** `binario` (Spanish - "binary")
- **Why wrong:** "Binary" refers to base-2 number system (0 and 1 as digits). "Boolean" is logical true/false. Related but distinct concepts. Bool values can be represented in binary, but they're not the same thing.
- **Right:** `booleano` (logical type, not numeric base)

**Mistake 3: Using "logical" when "boolean" is established**

- **Wrong:** Using only `lógico` when `booleano` is standard
- **Why wrong:** While "logical" captures the concept, "Boolean" is the technical term honoring George Boole. If your language's CS education uses "Boolean" (transliterated), use that. "Logical" is acceptable if standard, but check conventions.
- **Right:** `booleano` if that's the CS education standard

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO

**"Boolean" is unambiguous:**

"Boolean" specifically refers to George Boole's logical system and the true/false data type in computing. There are no other common meanings.

**Your translation should:**

- Honor George Boole's name (transliteration common)
- OR use word for "logical" if that's CS education standard
- Capture the two-valued logic concept

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `bool`, check these translations:**

- [ ] `True`/`False` - The values of `bool` type; should feel related
- [ ] `int`/`str`/`float` - Other primitive types; should use similar noun forms
- [ ] `and`/`or`/`not` - Boolean operators; work with bool values

**Consistency rule:**

All type constructors (`bool`, `int`, `float`, `str`, `list`, `dict`) should use noun forms. They name categories, not actions. `bool` specifically should relate to the concept of logical true/false.

**Example:**

Spanish: `booleano`, `entero`, `flotante`, `cadena` - all nouns/adjectives-as-nouns ✅

### Functional relationships

**This term works WITH:**

1. **`bool` + comparisons**: Boolean results

```python
result = (5 > 3)  # True
is_equal = (x == y)  # bool value
```

2. **`bool()` conversion**: Truthiness evaluation

```python
bool(10)    # True
bool(0)     # False
bool([])    # False
bool([1])   # True
```

**Common pairing:**

```python
# bool in conditionals
is_valid = True
if is_valid:
    process()

# bool from comparisons
age = 20
can_vote = age >= 18  # bool value

# bool conversion
has_data = bool(data_list)

# bool with operators
result = True and False  # False
result = not False       # True
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `bool`

- Universal concept (true/false logic exists in all languages)
- "Boolean" is standard CS term globally (after George Boole)
- Well-established translations/transliterations
- Fundamental to all programming

**For this term:** EASY

**Rationale:** Boolean logic is universal in computer science. The term "Boolean" (from George Boole's name) is recognized worldwide. Most languages either transliterate "Boolean" or use their word for "logical." Both approaches are well-documented in CS education globally.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Only consideration: whether to transliterate "Boolean" or use native word for "logical." Check target language's CS education conventions.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures BOOLEAN/LOGICAL concept (true/false type)?
- [ ] Understood as type (category), not values (True/False)?
- [ ] Relates to logical/truth values, not just binary numbers?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun or adjective-as-noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other type names (`int`, `float`, `str`)?
- [ ] All type names use noun forms?
- [ ] Aligns with how boolean logic is discussed in target language CS?

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
term: bool
language: es
translation: booleano
form: adjective_as_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "booleano" is the standard form honoring George Boole's name, following Spanish adjective formation (-eano suffix). Used universally in Spanish CS education for logical true/false type. Natural in technical contexts alongside `entero`, `flotante`, `cadena`.

**Alternatives considered:**

1. `lógico` (logical) - Less specific; "booleano" is the precise CS term
2. `bool` (keep English) - Transliteration preferred when possible
3. `binario` (binary) - Wrong concept; confuses logical with numeric base-2

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Boolean logic is universal, and "Boolean" (Boole's name) is recognized globally in CS education.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
