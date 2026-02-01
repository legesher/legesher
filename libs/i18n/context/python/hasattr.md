# Python Builtin Function: `hasattr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** compound_verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `hasattr()` function in Python checks whether an object has a specified attribute (by name as a string). Returns `True` if the attribute exists, `False` otherwise. Essential for defensive programming, duck typing, and avoiding `AttributeError` exceptions when accessing object attributes.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Check if attribute exists
class Person:
    def __init__(self, name):
        self.name = name

person = Person("Alice")
print(hasattr(person, "name"))  # Output: True
print(hasattr(person, "age"))  # Output: False
```

**What this does:** `hasattr(object, "name")` returns `True` if object has the `name` attribute, `False` otherwise. Safe way to test for attribute existence before accessing it.

### Example 2: Common Pattern

```python
# Defensive attribute access
class Config:
    debug = True

config = Config()

# Check before accessing
if hasattr(config, "debug"):
    print(f"Debug mode: {config.debug}")

# Avoid AttributeError
if hasattr(config, "production"):
    print(config.production)
else:
    print("Production mode not configured")

# Alternative to try/except
# Instead of:
try:
    value = config.timeout
except AttributeError:
    value = 30

# Can use:
if hasattr(config, "timeout"):
    value = config.timeout
else:
    value = 30
```

**What this does:** Use `hasattr()` before accessing attributes to prevent `AttributeError`. Cleaner than try/except for simple existence checks. Common in defensive programming and configuration handling.

### Example 3: Edge Case

```python
# Works with methods
class Calculator:
    def add(self, x, y):
        return x + y

calc = Calculator()
print(hasattr(calc, "add"))  # True - method exists
print(hasattr(calc, "subtract"))  # False - method doesn't exist

# Dynamic duck typing
def process(obj):
    if hasattr(obj, "process"):
        obj.process()
    elif hasattr(obj, "run"):
        obj.run()
    else:
        print("Object has no process method")

# Check attribute on class vs instance
class MyClass:
    class_attr = "I'm a class attribute"

obj = MyClass()
print(hasattr(MyClass, "class_attr"))  # True
print(hasattr(obj, "class_attr"))  # True (inherited)
```

**What this shows:** `hasattr()` works with methods, properties, and any attribute type. Useful for duck typing - checking if object has expected interface. Works on both classes and instances, following Python's attribute resolution.

---

## Pattern Classification

**This term is:** ATTRIBUTE PREDICATE FUNCTION (Reflection/Introspection)

**Similar terms in this pattern:**

1. `getattr` - Gets attribute by name (attribute access)
2. `setattr` - Sets attribute by name (attribute modification)
3. `delattr` - Deletes attribute by name (attribute removal)

**Pattern rule:** Attribute manipulation functions are compound terms: verb + "attr" (attribute). "hasattr" = has + attribute. These form a family of related operations on object attributes. Must maintain consistency across this group.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `getattr` | obtener_atributo | جلب_صفة | 获取属性 | गुण_प्राप्त |
| `setattr` | establecer_atributo | تعيين_صفة | 设置属性 | गुण_निर्धारित |
| `hasattr` | **tiene_atributo** | **له_صفة** | **有属性** | **गुण_है** |

---

## Etymology (Brief)

**English Origin:** Compound abbreviation (English)

**Root meaning:** "has" (Old English "habban" - to possess, hold) + "attr" (abbreviation of "attribute" from Latin "attributus" - assigned). In programming, "has" indicates possession/existence test, and "attribute" means property/characteristic of an object.

**Why Python uses this:** Compound function names clearly describe the operation. "hasattr" = has attribute (tests for existence). Python's reflection API uses consistent naming: `getattr`, `setattr`, `hasattr`, `delattr` - all follow verb+attr pattern. Compact yet descriptive.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `hasattr()` function tests whether an object has a specified attribute, returning a boolean result. It's the safe way to check attribute existence before accessing it, preventing `AttributeError` exceptions. Signature: `hasattr(object, name)` where name is a string.

Internally, `hasattr()` actually tries to call `getattr()` and catches any `AttributeError`. If `getattr()` succeeds, `hasattr()` returns `True`. If `AttributeError` is raised, returns `False`. This means it checks not just if the name exists, but if it's accessible.

Common use cases include defensive programming (check before access), duck typing (test for expected interface), API flexibility (handle objects with different capabilities), and conditional logic based on object features. Essential for robust code that works with diverse object types.

**Key behaviors:**

1. **Returns boolean:** Always returns `True` or `False`. Never raises exceptions. Safe to call on any object with any attribute name. `True` means attribute exists and is accessible.

2. **Tests accessibility, not just existence:** Calls `getattr()` internally. If property getter raises exception, `hasattr()` returns `False`. Catches `AttributeError` only - other exceptions propagate.

3. **Follows attribute resolution:** Checks instance attributes, class attributes, and inherited attributes (full MRO). Same lookup order as dot notation. Returns `True` if attribute found anywhere in chain.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb/predicate (tests condition)
- **Action vs State:** STATE TEST - checks if attribute exists
- **Temporal aspect:** Instantaneous - tests current state

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb + noun compound | "tiene_atributo" - has attribute |
| Germanic (de, nl, sv) | Verb + noun compound | "hatAttribut" - has attribute |
| Slavic (ru, pl, uk) | Verb + noun compound | "имеет_атрибут" - has attribute |
| Arabic | Verb + noun phrase | "له_صفة" - has attribute (for it attribute) |
| Chinese | Verb + noun compound | "有属性" - has/possess attribute |
| Hindi | Verb + noun compound | "गुण_है" - attribute exists/is |

**Primary recommendation:** Use compound following pattern: verb meaning "has/possess" + noun meaning "attribute/property." Maintain consistency with `getattr` and `setattr` - all should use same "attr/attribute" term.

**Forms to AVOID:**

- ❌ Using only "has" without "attribute" - ambiguous what is possessed
- ❌ Using "exists" alone - less clear than "has attribute"
- ❌ Different attribute word than getattr/setattr - breaks family consistency

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `tiene_atributo` or `tne_atr`
- **Form:** Verb + noun compound
- **Why it works:** "Tiene" (has/possesses) + "atributo" (attribute). Clear possession test structure. Could abbreviate if desired. Matches pattern with `obtener_atributo` (getattr), `establecer_atributo` (setattr).

**Arabic:**

- **Translation:** `له_صفة` (lahu_ṣifa) or `يملك_صفة` (yamlik_ṣifa)
- **Form:** Verb + noun compound/phrase
- **Why it works:** "له" (has/for it) + "صفة" (attribute). "يملك" (possesses) also works. Both express possession/existence. Matches with `جلب_صفة` (getattr), `تعيين_صفة` (setattr).

**Chinese:**

- **Translation:** `有属性` (yǒu shǔxìng)
- **Form:** Verb + noun compound
- **Why it works:** "有" (has/exists) + "属性" (attribute). Standard Chinese for existence/possession. Concise and clear. Matches with `获取属性` (getattr), `设置属性` (setattr).

**Hindi:**

- **Translation:** `गुण_है` (guṇ hai) or `गुण_रखता_है` (guṇ rakhtā hai)
- **Form:** Noun + verb compound
- **Why it works:** "गुण" (attribute) + "है" (is/exists). "रखता है" (possesses) more explicit. First more concise. Matches pattern with getattr/setattr using "गुण" for attribute.

### ❌ Common Translation Mistakes

**Mistake 1: Using only "has" or "exists" without attribute noun**

- **Wrong:** `tiene` (Spanish - "has")
- **Why wrong:** Too generic. Has what? Must specify checking attribute. Compound term necessary for clarity and consistency with getattr/setattr family.
- **Right:** `tiene_atributo` (has attribute - complete compound)

**Mistake 2: Using different word for "attribute" than getattr/setattr**

- **Wrong:** `tiene_propiedad` (Spanish - "has property")
- **Why wrong:** Inconsistent. If getattr uses "atributo", hasattr must too. These three functions form a family - must use same terminology for the "attr" component.
- **Right:** `tiene_atributo` (matches getattr/setattr)

**Mistake 3: Using "check" or "verify" instead of "has"**

- **Wrong:** `verificar_atributo` (Spanish - "verify attribute")
- **Why wrong:** "Verify" is action of checking. "Has" expresses the test more directly. Doesn't match Python's has/get/set pattern.
- **Right:** `tiene_atributo` (has - expresses possession test)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specialized compound term)

**The term is unambiguous:**

"hasattr" is a programming-specific compound of "has" + "attribute." While "has" and "attribute" individually have multiple meanings, the compound "hasattr" unambiguously means "test whether an object possesses a named attribute" in programming contexts.

**Translation consideration:**

Create compound matching Python's pattern: verb (has/possess) + noun (attribute/property). Ensure the "attribute" component matches what you use in `getattr` and `setattr` - these three must be linguistically consistent.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `hasattr`, check these translations:**

- [ ] `getattr` - Must use SAME "attribute" word, compatible "get" verb
- [ ] `setattr` - Must use SAME "attribute" word, compatible "set" verb
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

- `getattr` → `obtener_atributo` (uses "atributo")
- `hasattr` → `tiene_propiedad` (uses "propiedad")
Different terms ❌ WRONG!

### Functional relationships

**This term works WITH:**

1. **`hasattr` + defensive access**: Check before accessing

```python
if hasattr(obj, "method"):
    obj.method()
```

2. **`hasattr` + duck typing**: Test for interface

```python
if hasattr(obj, "read") and hasattr(obj, "write"):
    # Treat as file-like object
```

**Common pairing:**

```python
# Basic usage
class Person:
    def __init__(self, name):
        self.name = name

person = Person("Alice")
print(hasattr(person, "name"))  # True
print(hasattr(person, "age"))  # False

# Defensive programming
class Config:
    debug = True

config = Config()
if hasattr(config, "debug"):
    print(f"Debug: {config.debug}")

# Duck typing - check for interface
def save_data(obj, filename):
    if hasattr(obj, "to_dict"):
        data = obj.to_dict()
    elif hasattr(obj, "serialize"):
        data = obj.serialize()
    else:
        raise TypeError("Object must implement to_dict or serialize")
    # Save data...

# Combined with getattr
def get_value(obj, attr, default=None):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    return default

# Check multiple attributes
class FileHandler:
    def read(self): pass
    def write(self, data): pass

handler = FileHandler()
is_file_like = hasattr(handler, "read") and hasattr(handler, "write")

# Method existence check
class Calculator:
    def add(self, x, y):
        return x + y

calc = Calculator()
operations = ["add", "subtract", "multiply"]
available = [op for op in operations if hasattr(calc, op)]
print(available)  # ['add']

# Graceful degradation
def process(obj):
    if hasattr(obj, "process_v2"):
        obj.process_v2()  # New method
    elif hasattr(obj, "process"):
        obj.process()  # Old method
    else:
        # Fallback behavior
        pass
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY-MEDIUM)

- Clear compound term pattern
- "Has" and "attribute" have straightforward translations
- Must coordinate with getattr/setattr family
- **AI confidence should be HIGH**

### Why LOW for `hasattr`

- Simple verb + noun compound
- "Has" is universal verb for possession
- "Attribute" is standard OOP terminology
- Pattern is consistent across languages

**For this term:** LOW

**Rationale:** "hasattr" is a straightforward compound of two common terms. The key challenge is ensuring consistency with the attr-family (getattr, setattr, delattr) by using the same word for "attribute" across all four functions.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Critical requirement: MUST use the same "attribute" translation as getattr and setattr. Check those terms first to ensure consistency.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ATTRIBUTE EXISTENCE TEST concept?
- [ ] Understood as boolean check for attribute?
- [ ] Conveys safe checking (no exceptions)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb + noun compound)?
- [ ] Uses "has/possess" verb appropriately?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Uses SAME "attribute" word as getattr/setattr?
- [ ] Matches grammatical pattern with attr-family?
- [ ] Aligns with target language OOP terminology?

### 4. Usability

- [ ] Short enough (2-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear possession/existence test structure?

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
term: hasattr
language: es
translation: tiene_atributo
form: compound_verb_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "tiene_atributo" clearly compounds "tiene" (has/possesses) with "atributo" (attribute), matching the English pattern. Uses same "atributo" as getattr/setattr for family consistency. Natural Spanish for expressing possession/existence tests.

**Alternatives considered:**

1. `tne_atr` (abbreviated) - Could work but full form clearer
2. `posee_atributo` (possesses attribute) - "tiene" more natural for existence
3. `tiene_propiedad` (has property) - Must use "atributo" for consistency with getattr/setattr

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. hasattr is a clear compound term with straightforward translation, provided it matches getattr/setattr.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
