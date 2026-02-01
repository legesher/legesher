# Python Builtin Function: `setattr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** compound_verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `setattr()` function in Python sets an attribute on an object by name (as a string) to a specified value. It's equivalent to `object.attribute = value` but allows dynamic attribute assignment when the attribute name is stored in a variable. Essential for metaprogramming and dynamic object manipulation.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Set attribute by string name
class Person:
    pass

person = Person()
setattr(person, "name", "Alice")
print(person.name)  # Output: Alice
```

**What this does:** `setattr(object, "name", value)` sets the `name` attribute on `person` to "Alice". Equivalent to `person.name = "Alice"` but uses string for attribute name. Enables dynamic attribute creation.

### Example 2: Common Pattern

```python
# Dynamic attribute setting
class Config:
    pass

config = Config()

# Set multiple attributes from dictionary
settings = {"debug": True, "port": 8000, "host": "localhost"}
for key, value in settings.items():
    setattr(config, key, value)

print(config.debug)  # True
print(config.port)  # 8000
print(config.host)  # localhost
```

**What this does:** Dynamically sets attributes from a dictionary. Attribute names come from dictionary keys. Common pattern for configuration objects, deserialization, and building objects from data.

### Example 3: Edge Case

```python
# Modify existing attribute
class Counter:
    def __init__(self):
        self.count = 0

counter = Counter()
print(counter.count)  # 0
setattr(counter, "count", 10)
print(counter.count)  # 10

# Add new attribute dynamically
setattr(counter, "max_count", 100)
print(counter.max_count)  # 100 (new attribute created)

# Works with any name (including keywords as strings)
setattr(counter, "class", "MyCounter")
print(getattr(counter, "class"))  # MyCounter
```

**What this shows:** `setattr()` modifies existing attributes or creates new ones. Can set attributes whose names are Python keywords (as strings). Bypasses normal syntax limitations, enabling complete dynamic control over object attributes.

---

## Pattern Classification

**This term is:** ATTRIBUTE MUTATOR FUNCTION (Reflection/Introspection)

**Similar terms in this pattern:**

1. `getattr` - Gets attribute by name (attribute access)
2. `hasattr` - Checks if attribute exists (attribute testing)
3. `delattr` - Deletes attribute by name (attribute removal)

**Pattern rule:** Attribute manipulation functions are compound terms: verb + "attr" (attribute). "setattr" = set + attribute. These form a family of related operations on object attributes. Must maintain consistency across this group.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `getattr` | obtener_atributo | جلب_صفة | 获取属性 | गुण_प्राप्त |
| `hasattr` | tiene_atributo | له_صفة | 有属性 | गुण_है |
| `setattr` | **establecer_atributo** | **تعيين_صفة** | **设置属性** | **गुण_निर्धारित** |

---

## Etymology (Brief)

**English Origin:** Compound abbreviation (English)

**Root meaning:** "set" (Old English "settan" - to put, place) + "attr" (abbreviation of "attribute" from Latin "attributus" - assigned). In programming, "set" means assign/modify a value, and "attribute" means property/characteristic of an object.

**Why Python uses this:** Compound function names clearly describe the operation. "setattr" = set attribute. Python's reflection API uses consistent naming: `getattr`, `setattr`, `hasattr`, `delattr` - all follow verb+attr pattern. Compact yet descriptive.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `setattr()` function provides dynamic attribute modification - setting an object's attribute when the attribute name is a string variable rather than a literal identifier. While `obj.name = value` requires knowing the attribute name at code-writing time, `setattr(obj, "name", value)` allows the attribute name to be determined at runtime.

Signature: `setattr(object, name, value)`. Sets the named attribute to the specified value. If attribute doesn't exist, creates it. If it exists, modifies it. No return value (returns `None`). This is the dynamic equivalent of assignment statements.

Common use cases include configuration systems (set config values from files), deserialization (reconstruct objects from JSON/data), object builders (construct objects step-by-step), and plugin systems (add attributes dynamically). Essential for metaprogramming, ORMs, and dynamic systems.

**Key behaviors:**

1. **Dynamic attribute modification:** Attribute name as string allows runtime determination. Can come from variables, user input, config files, data sources. More flexible than dot notation assignment.

2. **Creates or modifies:** If attribute exists, modifies it. If doesn't exist, creates it. No error either way. Enables building objects dynamically attribute-by-attribute.

3. **Returns None:** Unlike `getattr` which returns value, `setattr` returns `None` (it's a mutating operation, not a query). Used for side effects (modifying object state).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb (action performed)
- **Action vs State:** ACTION - assigns/modifies attribute
- **Temporal aspect:** Instantaneous - sets value at call time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb + noun compound | "establecer_atributo" - set attribute |
| Germanic (de, nl, sv) | Verb + noun compound | "setzeAttribut" - set attribute |
| Slavic (ru, pl, uk) | Verb + noun compound | "установить_атрибут" - set attribute |
| Arabic | Verb + noun phrase | "تعيين_صفة" - set/assign attribute |
| Chinese | Verb + noun compound | "设置属性" - set attribute |
| Hindi | Verb + noun compound | "गुण_निर्धारित" - set attribute |

**Primary recommendation:** Use compound following pattern: verb meaning "set/assign/establish" + noun meaning "attribute/property." Maintain consistency with `getattr` and `hasattr` - all should use same "attr/attribute" term.

**Forms to AVOID:**

- ❌ Using only "set" without "attribute" - ambiguous what is being set
- ❌ Using "write" instead of "set" - "set" is standard for mutators
- ❌ Different attribute word than getattr/hasattr - breaks family consistency

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `establecer_atributo` or `est_atr`
- **Form:** Verb + noun compound
- **Why it works:** "Establecer" (to set/establish) + "atributo" (attribute). Clear action-object structure. Could abbreviate if desired. Matches pattern with `obtener_atributo` (getattr), `tiene_atributo` (hasattr).

**Arabic:**

- **Translation:** `تعيين_صفة` (ta'yīn_ṣifa) or `ضبط_صفة` (ḍabṭ_ṣifa)
- **Form:** Verb + noun compound
- **Why it works:** "تعيين" (set/assign) + "صفة" (attribute). "ضبط" (set/adjust) also works. Both concise action + object. Matches with `جلب_صفة` (getattr), `له_صفة` (hasattr).

**Chinese:**

- **Translation:** `设置属性` (shèzhì shǔxìng)
- **Form:** Verb + noun compound
- **Why it works:** "设置" (set/configure) + "属性" (attribute). Standard Chinese programming terminology. Matches with `获取属性` (getattr), `有属性` (hasattr).

**Hindi:**

- **Translation:** `गुण_निर्धारित` (guṇ nirdhārit) or `गुण_सेट_करना` (guṇ set karnā)
- **Form:** Noun + verb compound
- **Why it works:** "गुण" (attribute) + "निर्धारित" (set/determined). Could add "करना" for full verb form. Matches pattern with getattr/hasattr using "गुण" for attribute.

### ❌ Common Translation Mistakes

**Mistake 1: Using only "set" without attribute noun**

- **Wrong:** `establecer` (Spanish - "to set/establish")
- **Why wrong:** Too generic. Set what? Must specify setting attribute. Compound term necessary for clarity and consistency with getattr/hasattr family.
- **Right:** `establecer_atributo` (set attribute - complete compound)

**Mistake 2: Using different word for "attribute" than getattr/hasattr**

- **Wrong:** `establecer_propiedad` (Spanish - "set property")
- **Why wrong:** Inconsistent. If getattr uses "atributo", setattr must too. These three functions form a family - must use same terminology for the "attr" component.
- **Right:** `establecer_atributo` (matches getattr/hasattr)

**Mistake 3: Using "write" or "assign" instead of "set"**

- **Wrong:** `escribir_atributo` (Spanish - "write attribute")
- **Why wrong:** "Write" implies file/output operations. "Set" is standard programming term for assignment/mutation. Doesn't match Python's get/set pattern.
- **Right:** `establecer_atributo` (set - standard mutator term)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specialized compound term)

**The term is unambiguous:**

"setattr" is a programming-specific compound of "set" + "attribute." While "set" and "attribute" individually have multiple meanings, the compound "setattr" unambiguously means "assign a value to an object attribute by name" in programming contexts.

**Translation consideration:**

Create compound matching Python's pattern: verb (set/assign/establish) + noun (attribute/property). Ensure the "attribute" component matches what you use in `getattr` and `hasattr` - these three must be linguistically consistent.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `setattr`, check these translations:**

- [ ] `getattr` - Must use SAME "attribute" word, compatible "get" verb
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

- `getattr` → `obtener_atributo` (uses "atributo")
- `setattr` → `establecer_propiedad` (uses "propiedad")
Different terms ❌ WRONG!

### Functional relationships

**This term works WITH:**

1. **`setattr` + dynamic modification**: Runtime attribute assignment

```python
attr_name = "status"
setattr(obj, attr_name, "active")
```

2. **`setattr` + object construction**: Build objects from data

```python
for key, value in data.items():
    setattr(obj, key, value)
```

**Common pairing:**

```python
# Basic usage
class Person:
    pass

person = Person()
setattr(person, "name", "Alice")
setattr(person, "age", 30)
print(person.name, person.age)  # Alice 30

# Build object from dictionary
class Config:
    pass

config = Config()
settings = {
    "debug": True,
    "port": 8000,
    "host": "localhost"
}

for key, value in settings.items():
    setattr(config, key, value)

# Deserialization pattern
def from_dict(cls, data):
    obj = cls()
    for key, value in data.items():
        setattr(obj, key, value)
    return obj

# Dynamic attribute names
class DynamicObject:
    pass

obj = DynamicObject()
attributes = ["x", "y", "z"]
for i, attr in enumerate(attributes):
    setattr(obj, attr, i * 10)

print(obj.x, obj.y, obj.z)  # 0 10 20

# Set attribute with keyword name (normally invalid)
setattr(obj, "class", "MyClass")  # "class" is keyword
print(getattr(obj, "class"))  # MyClass

# Combined with getattr for attribute copying
def copy_attributes(source, target, attrs):
    for attr in attrs:
        value = getattr(source, attr)
        setattr(target, attr, value)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY-MEDIUM)

- Clear compound term pattern
- "Set" and "attribute" have straightforward translations
- Must coordinate with getattr/hasattr family
- **AI confidence should be HIGH**

### Why LOW for `setattr`

- Simple verb + noun compound
- "Set" is universal programming term for assignment
- "Attribute" is standard OOP terminology
- Pattern is consistent across languages

**For this term:** LOW

**Rationale:** "setattr" is a straightforward compound of two common programming terms. The key challenge is ensuring consistency with the attr-family (getattr, hasattr, delattr) by using the same word for "attribute" across all four functions.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Critical requirement: MUST use the same "attribute" translation as getattr and hasattr. Check those terms first to ensure consistency.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ASSIGN ATTRIBUTE concept?
- [ ] Understood as dynamic attribute modification by name?
- [ ] Conveys creating or modifying behavior?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb + noun compound)?
- [ ] Uses "set/assign" verb appropriately?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Uses SAME "attribute" word as getattr/hasattr?
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
term: setattr
language: es
translation: establecer_atributo
form: compound_verb_noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "establecer_atributo" clearly compounds "establecer" (to set/establish) with "atributo" (attribute), matching the English pattern. Uses same "atributo" as getattr/hasattr for family consistency. Natural Spanish programming terminology for assignment operations.

**Alternatives considered:**

1. `est_atr` (abbreviated) - Could work but full form clearer
2. `asignar_atributo` (assign attribute) - "establecer" more standard for setters
3. `establecer_propiedad` (set property) - Must use "atributo" for consistency with getattr

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. setattr is a clear compound term with straightforward translation, provided it matches getattr/hasattr.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
