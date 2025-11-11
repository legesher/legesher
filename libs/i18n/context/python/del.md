# Python Keyword: `del` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `del` keyword in Python removes references to objects, deleting variable names, list items, dictionary keys, or object attributes from their namespaces. It unbinds names rather than directly destroying objects, which are garbage collected when no references remain.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Delete a variable
x = 42
del x
# x no longer exists in this scope
# print(x)  # Would raise NameError
```

**What this does:** The `del` statement removes the name `x` from the current namespace. After deletion, attempting to access `x` raises a NameError because the name no longer exists. The object (42) is garbage collected if no other references exist.

### Example 2: Common Pattern

```python
# Delete dictionary key
user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
del user["email"]
# user is now {"name": "Alice", "age": 30}

# Delete list element by index
numbers = [10, 20, 30, 40]
del numbers[1]  # Remove element at index 1
# numbers is now [10, 30, 40]
```

**What this does:** `del` can remove items from collections using subscript notation. For dictionaries, it removes the key-value pair. For lists, it removes the element at the specified index, and subsequent elements shift down. Unlike list.remove(), `del` works by position, not value.

### Example 3: Edge Case

```python
# Delete slice from list
letters = ['a', 'b', 'c', 'd', 'e']
del letters[1:3]  # Delete elements at indices 1-2
# letters is now ['a', 'd', 'e']

# Delete object attribute
class Person:
    def __init__(self):
        self.name = "Bob"

person = Person()
del person.name
# person.name no longer exists
# print(person.name)  # Would raise AttributeError
```

**What this shows:** `del` can remove slices from sequences and attributes from objects. Slicing allows bulk removal. Attribute deletion removes the attribute entirely from the object's namespace, different from setting it to None (which keeps the attribute with a None value).

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Namespace Manipulation)

**Similar terms in this pattern:**

1. `def` - Defines/creates names (opposite of del)
2. `import` - Adds names to namespace
3. `pass` - Does nothing (del removes something, pass does nothing)

**Pattern rule:** Namespace manipulation keywords should use verb forms (infinitive). They perform actions that modify what names exist in the current scope: creating, deleting, importing.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `def` | definir | تعريف | 定义 | परिभाषित |
| `import` | importar | استيراد | 导入 | आयात |
| `del` | **eliminar** | **حذف** | **删除** | **हटाना** |

---

## Etymology (Brief)

**English Origin:** Abbreviation

**Root meaning:** `del` is short for "delete," which comes from Latin "deletus" (past participle of "delere" = to destroy, erase, annihilate). In computing, "delete" has meant "remove" or "erase" since early programming languages.

**Why Python uses this:** Python abbreviates "delete" to `del` for brevity. Unlike functions like `remove()` or `pop()`, `del` is a statement that works at the syntax level, capable of deleting variables, attributes, subscripts, and slices. The three-letter keyword is concise while remaining recognizable. Most programming languages use "delete," "del," or "remove" for this operation.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `del` statement removes bindings between names and objects. In Python, variables are names that reference objects. When you execute `del x`, Python removes the name `x` from the namespace, severing the reference to whatever object `x` pointed to. The object itself remains in memory until Python's garbage collector determines no references remain, at which point the object is destroyed.

This distinction is crucial: `del` removes references (names), not objects directly. If multiple names reference the same object, deleting one name doesn't affect the object or other names. `del` can target simple variables, list/dict items by subscript, object attributes, or slices.

The syntax varies by target: `del variable`, `del list[index]`, `del dict[key]`, `del object.attribute`, `del sequence[start:stop]`. Python interprets each form appropriately: namespace lookup for variables, `__delitem__` method for subscript deletion, `__delattr__` for attribute deletion.

**Key behaviors:**

1. **Name removal, not object destruction:** `del x` unbinds the name `x`, but the object survives if other references exist. Python's reference counting garbage collector handles actual memory deallocation.

2. **Works on various targets:** Unlike a function that returns values, `del` is a statement that modifies namespaces or containers in place. It can delete variables, subscripted items, attributes, or slices—contexts where you could perform assignment.

3. **Immediate effect:** After `del x`, accessing `x` immediately raises NameError (for variables) or AttributeError (for attributes) or KeyError (for dict keys). The name is gone from that namespace, though the object may persist elsewhere.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Transitive verb (takes object - what to delete)
- **Action vs State:** Pure ACTION - performs removal/deletion
- **Temporal aspect:** Instantaneous/perfective - happens immediately and completes

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "eliminar", "supprimer" - to delete/remove |
| Germanic (de, nl, sv) | Infinitive verb | "löschen", "verwijderen" - to delete/remove |
| Slavic (ru, pl, uk) | Infinitive verb | "удалить", "usunąć" - to delete/remove |
| Arabic | Masdar (verbal noun) | "حذف" (ḥadhf) - deletion/removing |
| Chinese | Verb | "删除" (shānchú) - to delete/remove |
| Hindi | Infinitive verb | "हटाना" (haṭānā) - to remove/delete |

**Primary recommendation:** Use infinitive verb meaning "to delete" or "to remove." Focus on removal/elimination action. The term should be general enough to apply to variables, list items, dict keys, and attributes.

**Forms to AVOID:**

- ❌ Using "destroy" - too strong, implies object destruction rather than name removal
- ❌ Using "erase" - may imply data wiping rather than reference removal
- ❌ Using noun "deletion" - should be verb "to delete"

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `eliminar`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish verb meaning "to eliminate, to remove, to delete." Used in Spanish programming contexts for deletion operations. Broad enough to cover variables, list items, dict keys, and attributes. Natural and professional.

**Arabic:**

- **Translation:** `حذف` (ḥadhf)
- **Form:** Masdar (verbal noun)
- **Why it works:** Standard Arabic term for deletion/removal. Root ح-ذ-ف (ḥ-dh-f) means delete/remove. Commonly used in Arabic computing contexts. Masdar form suitable for keyword representing deletion action.

**Chinese:**

- **Translation:** `删除` (shānchú)
- **Form:** Verb compound
- **Why it works:** Standard Chinese computing term. 删 (delete) + 除 (remove) = comprehensive deletion concept. Universally used in Chinese programming documentation and education for delete operations.

**Hindi:**

- **Translation:** `हटाना` (haṭānā)
- **Form:** Infinitive verb
- **Why it works:** Common Hindi verb meaning "to remove." Natural and clear. Used in Hindi computing contexts. Less formal than Sanskrit alternatives, making it accessible while remaining professional.

### ❌ Common Translation Mistakes

**Mistake 1: Using "destroy" instead of "delete/remove"**

- **Wrong:** `destruir` (Spanish - "to destroy")
- **Why wrong:** "Destroy" implies violent obliteration of the object itself. Python's `del` removes references/names, not necessarily objects. "Destruir" is too strong and technically inaccurate. "Eliminar" or "borrar" better capture reference removal.
- **Right:** `eliminar` (to eliminate/remove/delete)

**Mistake 2: Using noun form**

- **Wrong:** `eliminación` (Spanish - "the deletion" - noun)
- **Why wrong:** Keywords are actions (verbs), not things (nouns). "Del" performs deletion action, so translation should be verb "to delete," not noun "deletion."
- **Right:** `eliminar` (verb infinitive)

**Mistake 3: Using "erase" with data wiping connotation**

- **Wrong:** `borrar` (Spanish - "to erase") - borderline acceptable
- **Why wrong:** "Borrar" often implies wiping/erasing data (like erasing a whiteboard). While acceptable in some contexts, "eliminar" is more precise for namespace operations. "Borrar" isn't wrong but "eliminar" is more technical and accurate.
- **Right:** `eliminar` (more precise for reference removal)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (del is abbreviation of "delete," which has multiple meanings)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Physically destroy object" (permanent obliteration)
- ❌ Meaning 2: "Erase data/wipe clean" (like formatting a disk)
- ✅ Meaning 3: **"REMOVE NAME/REFERENCE FROM NAMESPACE"** (unbind, dereference)

**Example:**

English "delete" can mean:

1. "Delete the file" (destroy/remove from disk) ⚠️ (similar but more permanent)
2. "Delete your browser history" (erase data) ❌
3. "`del x` removes the name x from namespace" (unbind reference) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: removing names/references from namespaces, which may eventually lead to garbage collection but isn't direct object destruction.**

Key semantic nuance: Python's `del` operates at the namespace/reference level, not the object level. The object persists if other references exist. Translation should emphasize "remove/eliminate" rather than "destroy/annihilate."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `del`, check these translations:**

- [ ] `def` - Defines/creates names; `del` removes names; conceptual opposites, should use consistent verb forms
- [ ] `import` - Adds names to namespace; `del` removes names; both namespace operations
- [ ] `return` - Returns values; `del` removes names; both action keywords with verb forms

**Consistency rule:**

Namespace and control flow keywords (`def`, `del`, `import`, `return`, `break`) should all use verb forms (infinitive). They perform actions that affect program state. Don't mix verb and noun forms across these keywords.

**Example:**

Spanish: `definir` (def), `eliminar` (del), `importar` (import) - all infinitive verbs ✅
NOT: `definir` (verb) + `eliminación` (noun) ❌

### Functional relationships

**This term works WITH:**

1. **Variables:** `del variable_name`
```python
x = 10
del x  # Remove x from namespace
```

2. **Collection items:** `del collection[key/index]`
```python
del my_list[0]  # Remove first element
del my_dict["key"]  # Remove dictionary key
```

**Common pairing:**

```python
# Variable deletion
temp = calculate_value()
use_value(temp)
del temp  # Clean up temporary variable

# Dictionary key removal
cache = {"user1": data1, "user2": data2}
del cache["user1"]  # Remove specific entry

# List element removal
items = [1, 2, 3, 4, 5]
del items[2]  # Remove element at index 2

# Slice deletion
sequence = [0, 1, 2, 3, 4, 5, 6]
del sequence[2:5]  # Remove elements 2, 3, 4

# Attribute deletion
class Config:
    debug = True

del Config.debug  # Remove class attribute

# Multiple deletions
x, y, z = 1, 2, 3
del x, y, z  # Delete multiple names
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `del`:

- Universal concept (deletion/removal exists in all languages)
- Most languages have "delete" or "remove" verbs
- Moderate ambiguity: multiple deletion-related verbs available
- Need to choose between "delete," "remove," "eliminate," "erase"
- Context clarifies: namespace/reference removal, not data wiping

**For this term:** MEDIUM

**Rationale:** Every language has deletion verbs, and computing contexts are clear. However, translators must choose the right deletion verb: one that emphasizes namespace/reference removal rather than data destruction. Options like "delete," "remove," "eliminate" may all be valid, requiring knowledge of local CS education terminology. "Destroy" and "erase" are typically too strong.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures REMOVAL/DELETION concept (unbinding names)?
- [ ] Emphasizes name/reference removal, not object destruction?
- [ ] Understood as namespace manipulation operation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive, not past tense)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other action keywords (`def`, `import`, `return`)?
- [ ] Uses verb form like other namespace keywords?
- [ ] Aligns with how deletion is discussed in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common deletion verb)?

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
term: del
language: es
translation: eliminar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "eliminar" is the standard verb for deletion/removal operations in programming. It's broad enough to cover removing variables, list items, dictionary keys, and attributes. Widely used in Spanish technical documentation and CS education.

**Alternatives considered:**

1. `borrar` (to erase) - Also acceptable, common in Spain, but slightly less technical
2. `suprimir` (to suppress/delete) - More formal, less common in programming contexts
3. `destruir` (to destroy) - Too strong, implies object destruction rather than reference removal

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for Spanish. "Eliminar" is standard in Spanish CS education. Regional variation exists (Spain may prefer "borrar"), but "eliminar" is universally understood. For other languages, verify that chosen verb emphasizes removal/deletion without excessive violence connotation.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
