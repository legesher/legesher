# Python Builtin Function: `getattr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** compound_verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `getattr()` function in Python retrieves an attribute from an object by name (as a string). It's equivalent to `object.attribute` but allows dynamic attribute access when the attribute name is stored in a variable. Supports optional default value if attribute doesn't exist.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get attribute by string name
class Person:
    def __init__(self, name):
        self.name = name

person = Person("Alice")
name = getattr(person, "name")
print(name)  # Output: Alice
```

**What this does:** `getattr(object, "name")` retrieves the `name` attribute from `person` object. Equivalent to `person.name` but uses string for attribute name. Enables dynamic attribute access.

### Example 2: Common Pattern

```python
# With default value
class Config:
    debug = True

config = Config()
value = getattr(config, "debug", False)
print(value)  # Output: True

missing = getattr(config, "production", False)
print(missing)  # Output: False (default, attribute doesn't exist)

# Dynamic attribute access
attr_name = "debug"
value = getattr(config, attr_name)
print(value)  # Output: True
```

**What this does:** Three-argument form `getattr(obj, name, default)` returns default if attribute doesn't exist, avoiding `AttributeError`. Useful when attribute name comes from user input, config, or computation.

### Example 3: Edge Case

```python
# Works with methods
class Calculator:
    def add(self, x, y):
        return x + y

calc = Calculator()
method = getattr(calc, "add")
result = method(3, 5)  # Call the method
print(result)  # Output: 8

# Raises AttributeError without default
try:
    getattr(calc, "nonexistent")
except AttributeError as e:
    print(f"Error: {e}")
```

**What this shows:** `getattr()` works with methods too - returns bound method object. Without default value, raises `AttributeError` if attribute missing. With default, never raises error. Powerful for dynamic method dispatch.

---

## Pattern Classification

**This term is:** ATTRIBUTE ACCESSOR FUNCTION (Reflection/Introspection)

**Similar terms in this pattern:**

1. `setattr` - Sets attribute by name (attribute modification)
2. `hasattr` - Checks if attribute exists (attribute testing)
3. `delattr` - Deletes attribute by name (attribute removal)

**Pattern rule:** Attribute manipulation functions are compound terms: verb + "attr" (attribute). "getattr" = get + attribute. These form a family of related operations on object attributes. Must maintain consistency across this group.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `setattr` | establecer_atributo | تعيين_صفة | 设置属性 | गुण_निर्धारित |
| `hasattr` | tiene_atributo | له_صفة | 有属性 | गुण_है |
| `getattr` | **obtener_atributo** | **جلب_صفة** | **获取属性** | **गुण_प्राप्त** |

---

## Etymology (Brief)

**English Origin:** Compound abbreviation (English)

**Root meaning:** "get" (Old Norse "geta" - to obtain) + "attr" (abbreviation of "attribute" from Latin "attributus" - assigned). In programming, "get" means retrieve/access, and "attribute" means property/characteristic of an object.

**Why Python uses this:** Compound function names clearly describe the operation. "getattr" = get attribute. Python's reflection API uses consistent naming: `getattr`, `setattr`, `hasattr`, `delattr` - all follow verb+attr pattern. Compact yet descriptive.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `getattr()` function provides dynamic attribute access - retrieving an object's attribute when the attribute name is a string variable rather than a literal identifier. While `obj.name` requires knowing the attribute name at code-writing time, `getattr(obj, "name")` allows the attribute name to be determined at runtime.

Signature: `getattr(object, name[, default])`. Returns the value of the named attribute. If attribute doesn't exist and default is provided, returns default. If attribute doesn't exist and no default, raises `AttributeError`. This makes it safe for cases where attribute might not exist.

Common use cases include configuration systems (access config.setting_name dynamically), plugin architectures (call methods by name from user input), serialization (iterate over object attributes), and API dispatch (route to methods based on strings). Essential for metaprogramming and dynamic systems.

**Key behaviors:**

1. **Dynamic attribute access:** Attribute name as string allows runtime determination. Can come from variables, user input, config files, computation. More flexible than dot notation but same result.

2. **Optional default value:** Three-argument form `getattr(obj, name, default)` never raises AttributeError. Returns default if attribute missing. Two-argument form raises AttributeError like dot notation would.

3. **Works with all attribute types:** Retrieves data attributes, methods, properties, class attributes. Methods returned as bound methods (ready to call). Follows same attribute resolution as dot notation (instance → class → parent classes).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb (action performed)
- **Action vs State:** ACTION - retrieves/accesses attribute
- **Temporal aspect:** Instantaneous - gets value at call time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb + noun compound | "obtener_atributo" - get attribute |
| Germanic (de, nl, sv) | Verb + noun compound | "holeAttribut" - get/fetch attribute |
| Slavic (ru, pl, uk) | Verb + noun compound | "получить_атрибут" - get attribute |
| Arabic | Verb + noun phrase | "جلب_صفة" - fetch attribute |
| Chinese | Verb + noun compound | "获取属性" - get/obtain attribute |
| Hindi | Verb + noun compound | "गुण_प्राप्त" - obtain attribute |

**Primary recommendation:** Use compound following pattern: verb meaning "get/obtain/retrieve" + noun meaning "attribute/property." Maintain consistency with `setattr` and `hasattr` - all should use same "attr/attribute" term.

**Forms to AVOID:**

- ❌ Using only "get" without "attribute" - ambiguous what is being gotten
- ❌ Using "read" instead of "get" - "get" is standard for accessors
- ❌ Different attribute word than setattr/hasattr - breaks family consistency

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `obtener_atributo` or `obt_atr`
- **Form:** Verb + noun compound
- **Why it works:** "Obtener" (to obtain/get) + "atributo" (attribute). Clear action-object structure. Could abbreviate like English if desired. Matches pattern with `establecer_atributo` (setattr), `tiene_atributo` (hasattr).

**Arabic:**

- **Translation:** `جلب_صفة` (jalab_ṣifa) or `الحصول_على_صفة` (al-ḥuṣūl 'alā ṣifa)
- **Form:** Verb + noun compound
- **Why it works:** "جلب" (fetch/get) + "صفة" (attribute). Concise action + object. Alternative "الحصول على" (obtain) more verbose. First option more compact, matching getattr brevity.

**Chinese:**

- **Translation:** `获取属性` (huòqǔ shǔxìng) or `取属性` (qǔ shǔxìng)
- **Form:** Verb + noun compound
- **Why it works:** "获取" (obtain/get) + "属性" (attribute). Standard Chinese programming terminology. Shorter "取属性" also works. Matches with `设置属性` (setattr), `有属性` (hasattr).

**Hindi:**

- **Translation:** `गुण_प्राप्त` (guṇ prāpt) or `गुण_प्राप्त_करना` (guṇ prāpt karnā)
- **Form:** Noun + verb compound
- **Why it works:** "गुण" (attribute/property) + "प्राप्त" (obtained/received). Could add "करना" for full verb form. Matches pattern with setattr/hasattr using "गुण" for attribute.

### ❌ Common Translation Mistakes

**Mistake 1: Using only "get" without attribute noun**

- **Wrong:** `obtener` (Spanish - "to get/obtain")
- **Why wrong:** Too generic. Get what? Must specify getting attribute. Compound term necessary for clarity and consistency with setattr/hasattr family.
- **Right:** `obtener_atributo` (get attribute - complete compound)

**Mistake 2: Using different word for "attribute" than setattr/hasattr**

- **Wrong:** `obtener_propiedad` (Spanish - "get property")
- **Why wrong:** Inconsistent. If setattr uses "atributo", getattr must too. These three functions form a family - must use same terminology for the "attr" component.
- **Right:** `obtener_atributo` (matches setattr/hasattr)

**Mistake 3: Using "read" instead of "get"**

- **Wrong:** `leer_atributo` (Spanish - "read attribute")
- **Why wrong:** "Read" implies file/text reading. "Get" is standard programming term for accessors. Doesn't match Python's get/set pattern.
- **Right:** `obtener_atributo` (get - standard accessor term)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specialized compound term)

**The term is unambiguous:**

"getattr" is a programming-specific compound of "get" + "attribute." While "get" and "attribute" individually have multiple meanings, the compound "getattr" unambiguously means "retrieve an object attribute by name" in programming contexts.

**Translation consideration:**

Create compound matching Python's pattern: verb (get/obtain/retrieve) + noun (attribute/property). Ensure the "attribute" component matches what you use in `setattr` and `hasattr` - these three must be linguistically consistent.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `getattr`, check these translations:**

- [ ] `setattr` - Must use SAME "attribute" word, compatible "set" verb
- [ ] `hasattr` - Must use SAME "attribute" word, compatible "has" verb
- [ ] `delattr` - Must use SAME "attribute" word, compatible "delete" verb

**Consistency rule:**

The attr-family (`getattr`, `setattr`, `hasattr`, `delattr`) MUST use the same word for "attribute" across all four. Only the verb changes. This linguistic parallelism is essential for learners to recognize the pattern.

**Example:**

✅ **Consistent (Spanish):**

- `getattr` → `obtener_atributo`
- `setattr` → `establecer_atributo`
- `hasattr` → `tiene_atributo`
- `delattr` → `eliminar_atributo`
All use "atributo" ✅

❌ **Inconsistent:**

- `getattr` → `obtener_propiedad` (uses "propiedad")
- `setattr` → `establecer_atributo` (uses "atributo")
Different terms ❌ WRONG!

### Functional relationships

**This term works WITH:**

1. **`getattr` + dynamic access**: Runtime attribute names

```python
attr_name = "username"
value = getattr(user, attr_name)
```

2. **`getattr` + safe access**: With default value

```python
value = getattr(config, "setting", default_value)
```

**Common pairing:**

```python
# Basic usage
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

person = Person("Alice", 30)

# Same as person.name
name = getattr(person, "name")
print(name)  # Alice

# Dynamic attribute access
for attr in ["name", "age"]:
    value = getattr(person, attr)
    print(f"{attr}: {value}")

# With default value
email = getattr(person, "email", "no-email@example.com")
print(email)  # no-email@example.com (default)

# Method access
class Calculator:
    def add(self, x, y):
        return x + y
    def multiply(self, x, y):
        return x * y

calc = Calculator()
operation = "add"
method = getattr(calc, operation)
result = method(5, 3)  # 8

# Configuration system
class Config:
    DEBUG = True
    PORT = 8000

config = Config()
# Get setting by name from environment variable
import os
setting = os.environ.get("SETTING_NAME", "DEBUG")
value = getattr(config, setting, None)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY-MEDIUM)

- Clear compound term pattern
- "Get" and "attribute" have straightforward translations
- Must coordinate with setattr/hasattr family
- **AI confidence should be HIGH**

### Why LOW for `getattr`

- Simple verb + noun compound
- "Get" is universal programming term
- "Attribute" is standard OOP terminology
- Pattern is consistent across languages

**For this term:** LOW

**Rationale:** "getattr" is a straightforward compound of two common programming terms. The key challenge is ensuring consistency with the attr-family (setattr, hasattr, delattr) by using the same word for "attribute" across all four functions.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Critical requirement: MUST use the same "attribute" translation as setattr and hasattr. Check those terms first to ensure consistency.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures RETRIEVE ATTRIBUTE concept?
- [ ] Understood as dynamic attribute access by name?
- [ ] Conveys optional default value capability?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb + noun compound)?
- [ ] Uses "get/obtain" verb appropriately?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Uses SAME "attribute" word as setattr/hasattr?
- [ ] Matches grammatical pattern with attr-family?
- [ ] Aligns with target language OOP terminology?

### 4. Usability

- [ ] Short enough (2-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear action-object structure?

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
term: getattr
language: es
translation: obtener_atributo
form: compound_verb_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "obtener_atributo" clearly compounds "obtener" (to get/obtain) with "atributo" (attribute), matching the English pattern. Uses same "atributo" as setattr/hasattr for family consistency. Natural Spanish programming terminology.

**Alternatives considered:**

1. `obt_atr` (abbreviated) - Could work but full form clearer
2. `conseguir_atributo` (get/obtain) - "obtener" more standard for getters
3. `obtener_propiedad` (get property) - Must use "atributo" for consistency with setattr

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. getattr is a clear compound term with straightforward translation, provided it matches setattr/hasattr.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
