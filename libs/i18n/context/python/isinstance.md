# Python Builtin: `isinstance` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`isinstance()` checks if an object is an instance of a class or tuple of classes, returning True or False, the preferred way to check object types in Python.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic type checking
x = 42
print(isinstance(x, int))  # Output: True
print(isinstance(x, str))  # Output: False

name = "Alice"
print(isinstance(name, str))  # Output: True
```

**What this does:** `isinstance(object, class)` checks if an object is an instance of a specific class, returning True if it is, False otherwise.

### Example 2: Common Pattern

```python
# Multiple type checking with tuple
def process_value(value):
if isinstance(value, (int, float)):
return value * 2
elif isinstance(value, str):
return value.upper()
elif isinstance(value, list):
return len(value)
else:
return None

print(process_value(10))  # Output: 20
print(process_value("hello"))  # Output: HELLO
print(process_value([1, 2, 3]))  # Output: 3
```

**What this does:** Pass a tuple of classes to check if an object is an instance of any of them, cleaner than multiple `or` conditions.

### Example 3: Edge Case

```python
# Works with inheritance
class Animal:
pass

class Dog(Animal):
pass

dog = Dog()
print(isinstance(dog, Dog))  # Output: True
print(isinstance(dog, Animal))  # Output: True (inheritance!)
print(isinstance(dog, object))  # Output: True (everything inherits from object)

# Difference from type()
print(type(dog) == Dog)  # Output: True
print(type(dog) == Animal)  # Output: False (type() doesn't consider inheritance)

# Use isinstance, not type checking
if isinstance(dog, Animal):  # ✅ Correct - considers inheritance
print("It's an animal")

if type(dog) == Animal:  # ❌ Wrong - doesn't consider inheritance
print("This won't print")
```

**What this shows:** `isinstance()` respects inheritance - subclass instances are considered instances of parent classes. This is why `isinstance()` is preferred over `type()` comparisons.

---

## Pattern Classification

**This term is:** TYPE CHECKING FUNCTION (Compound term)

**Similar terms in this pattern:**

1. `issubclass` - Checks if a class is a subclass of another
2. `type` - Returns the type of an object
3. `hasattr` - Checks if object has an attribute

**Pattern rule:** Introspection functions using "is" + noun pattern should indicate what they check. The "is" suggests a boolean return.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `is` | es | هو | 是 | है |
| `type` | tipo | نوع | 类型 | प्रकार |
| `isinstance` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** "is" + "instance" (compound)

**Root meaning:** "Instance" from Latin "instantia" (presence, example). In OOP, an "instance" is a concrete occurrence of a class.

**Why Python uses this:** The name is self-explanatory - checks if something "is" an "instance" of a class. The compound verb-noun structure makes the function's purpose immediately clear. Replaces older type-checking patterns with a more object-oriented approach.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`isinstance()` checks whether an object is an instance of a specified class or any class in a tuple of classes. It returns a boolean (True/False) and is the recommended way to perform type checking in Python because it respects inheritance.

Unlike `type()` which returns the exact type, `isinstance()` considers the entire inheritance hierarchy. If you check `isinstance(dog, Animal)` where Dog inherits from Animal, it returns True. This is crucial for polymorphism - code should work with any subclass, not just the exact type.

The function accepts either a single class or a tuple of classes. When given a tuple, it returns True if the object is an instance of any of the classes, equivalent to `isinstance(obj, Class1) or isinstance(obj, Class2)` but more efficient and readable.

**Key behaviors:**

1. **Respects inheritance:** Returns True for parent classes, making it work correctly with polymorphism and subclassing.
2. **Tuple support:** Can check multiple classes at once with `isinstance(obj, (Class1, Class2, Class3))`, cleaner than multiple `or` conditions.
3. **Preferred over type():** `isinstance()` is the Pythonic way to check types because it works with inheritance, while `type(obj) == Class` fails for subclasses.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound verb+noun functioning as function name
- **Action vs State:** QUERY - asks a question and returns boolean
- **Temporal aspect:** Instantaneous check

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb "is" + noun "instance" | es_instancia, est_instance |
| Germanic (de, nl, sv) | Verb + noun or compound | ist_Instanz, isInstance |
| Slavic (ru, pl, uk) | Verb "is" + noun "instance" | является_экземпляром |
| Arabic | Verb "is" + noun "instance" | هو_نموذج (huwa namūdhaj) |
| Chinese | Verb + noun | 是实例 (shì shílì) |
| Hindi | Verb + noun | है_उदाहरण (hai udāharaṇ) |

**Primary recommendation:** Create compound from "is" (verb) + "instance" (noun), maintaining the verb-noun structure. Should read naturally as "is [an] instance [of]".

**Forms to AVOID:**

- ❌ Reversing to "instance is" - wrong word order
- ❌ Using only "is" or only "instance" - both parts needed
- ❌ Not matching the `is` keyword translation - should be consistent

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `es_instancia` or `esinstancia`
- **Form:** Compound verb+noun
- **Why it works:** Clear compound of "es" (is) + "instancia" (instance), immediately understood, parallel to English structure

**Arabic:**

- **Translation:** `هو_نموذج` (huwa namūdhaj - is instance/example)
- **Form:** Compound verb+noun
- **Why it works:** "هو" (is) + "نموذج" (instance/model), clear and follows compound pattern

**Chinese:**

- **Translation:** `是实例` (shì shílì - is instance)
- **Form:** Compound verb+noun
- **Why it works:** Standard CS term, "是" (is) + "实例" (instance), widely used

**Hindi:**

- **Translation:** `है_उदाहरण` (hai udāharaṇ - is instance)
- **Form:** Compound verb+noun
- **Why it works:** Clear compound, "है" (is) + "उदाहरण" (instance/example), follows pattern

### ❌ Common Translation Mistakes

**Mistake 1: Wrong word order**

- **Wrong:** `instancia_es` (Spanish - "instance is")
- **Why wrong:** Reverses the natural verb-noun order of the English term
- **Right:** `es_instancia` (is instance)

**Mistake 2: Using different verb than `is`**

- **Wrong:** `verifica_instancia` (Spanish - "verify instance")
- **Why wrong:** Should use same verb as `is` keyword for consistency
- **Right:** `es_instancia` (uses "es" from `is`)

**Mistake 3: Too verbose**

- **Wrong:** `comprobar_si_es_instancia` (Spanish - "check if is instance")
- **Why wrong:** Adds unnecessary words; function name should be concise
- **Right:** `es_instancia` (concise compound)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "isinstance" is unambiguous in Python

**Single technical meaning:**

✅ **Python meaning:** A function that checks if an object is an instance of a specified class or classes, returning a boolean.

The compound term is Python-specific with one clear meaning. Your translation should clearly compound "is" + "instance" in natural word order for the target language.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `isinstance`, check these translations:**

- [ ] `is` - MUST use same verb in compound
- [ ] `issubclass` - Parallel function, should use same "is" + different noun pattern
- [ ] `class` - For understanding what "instance" relates to
- [ ] `type` - Related type-checking function

**Consistency rule:**

The "is*" functions (`isinstance`, `issubclass`) MUST use the same verb translation as the `is` keyword:

- If `is` = "es" (Spanish), then `isinstance` = "es_instancia" (not "está_instancia")
- If `is` = "هو" (Arabic), then `isinstance` = "هو_نموذج" (same verb)

**Example:**

✅ **Consistent:**

- `is` → `es`
- `isinstance` → `es_instancia`
- `issubclass` → `es_subclase`
- All use "es" ✅

❌ **Inconsistent:**

- `is` → `es`
- `isinstance` → `verifica_instancia` (different verb!)
- Inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **`isinstance` + class names**: Checks against specific classes
2. **`isinstance` + tuple of classes**: Checks multiple types
3. **`isinstance` vs `type`**: isinstance preferred for inheritance

**Common pairing:**

```python
# Type checking pattern
if isinstance(obj, (int, float)):
# Handle numeric types

# Inheritance-aware checking
if isinstance(obj, BaseClass):
# Works for BaseClass and all subclasses
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Compound term requiring two parts
- Must align with `is` keyword translation
- Must parallel `issubclass` pattern
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While conceptually straightforward, creating a natural compound that maintains consistency with both the `is` keyword and the parallel `issubclass` function requires careful attention to linguistic patterns and OOP terminology.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clear compound of "is" + "instance"?
- [ ] Conveys type-checking concept?
- [ ] Would OOP developers understand this checks instance membership?

### 2. Linguistic Correctness

- [ ] Uses same verb as `is` keyword?
- [ ] Natural compound structure for target language?
- [ ] Proper word order (typically verb-noun)?

### 3. Consistency

- [ ] Matches `is` keyword translation?
- [ ] Parallel structure to `issubclass`?
- [ ] Compatible with OOP terminology?

### 4. Usability

- [ ] Concise (1-2 words, compound acceptable)?
- [ ] Easy to remember?
- [ ] Clear what it checks?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues with compound structure?

---

## Translation Output Format

**Your translation:**

```yaml
term: isinstance
language: {es|ar|zh|hi}
translation: {your_translation}
form: {compound_verb_noun}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you compounded the `is` verb translation with "instance" noun, maintaining natural word order. Emphasize consistency with `is` keyword and parallel structure to `issubclass`.}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Need to verify `is` translation, check consistency with `issubclass` pattern}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
