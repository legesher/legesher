# Python Builtin: `staticmethod` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** decorator
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`@staticmethod` decorator creates a method that doesn't receive an implicit first argument (neither `self` nor `cls`), functioning like a regular function but organized within a class namespace.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic staticmethod
class MathUtils:
@staticmethod
def add(x, y):
return x + y

@staticmethod
def multiply(x, y):
return x * y

# Called on class (no instance needed)
print(MathUtils.add(5, 3))  # Output: 8
print(MathUtils.multiply(4, 7))  # Output: 28

# Can also call on instance
utils = MathUtils()
print(utils.add(2, 2))  # Output: 4
```

**What this does:** `@staticmethod` creates a method that doesn't receive `self` or `cls`, working like a regular function but namespaced within the class for organization.

### Example 2: Common Pattern

```python
# Utility/helper methods
class Validator:
@staticmethod
def is_valid_email(email):
return '@' in email and '.' in email

@staticmethod
def is_valid_phone(phone):
return phone.isdigit() and len(phone) >= 10

# Usage - logical grouping of related functions
if Validator.is_valid_email("user@example.com"):
print("Valid email")

if Validator.is_valid_phone("1234567890"):
print("Valid phone")
```

**What this does:** Groups related utility functions under a class name for organization without needing instance or class state, cleaner than standalone functions when functions are thematically related.

### Example 3: Edge Case

```python
# Staticmethod doesn't access class or instance
class Example:
value = 10

@staticmethod
def static_func(x):
return x * 2
# Cannot access self.value or Example.value directly
# Acts like a regular function

@classmethod
def class_func(cls, x):
return x * cls.value  # Can access cls.value

def instance_func(self, x):
return x * self.value  # Can access self.value

# All callable, but different access
print(Example.static_func(5))  # Output: 10 (no access to class/instance)
print(Example.class_func(5))  # Output: 50 (accesses class)

obj = Example()
obj.value = 20
print(obj.instance_func(5))  # Output: 100 (accesses instance)
```

**What this shows:** Staticmethods cannot access instance (`self`) or class (`cls`) attributes - they're truly standalone functions just organized within a class namespace for logical grouping.

---

## Pattern Classification

**This term is:** METHOD DECORATOR

**Similar terms in this pattern:**

1. `classmethod` - Related decorator for class-level methods
2. `property` - Descriptor decorator for managed attributes
3. `def` - Regular method definition

**Pattern rule:** Method decorators should indicate the type of method they create, using compound terms or clear technical vocabulary.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `class` | clase | صنف | 类 | वर्ग |
| `classmethod` | método_clase | دالة_صنف | 类方法 | वर्ग_विधि |
| `staticmethod` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** "static" + "method" (compound)

**Root meaning:** "Static" from Latin "staticus" (causing to stand, fixed). In programming, "static" means belonging to the class itself rather than instances, or unchanging/fixed.

**Why Python uses this:** "Static method" is standard OOP terminology from languages like Java and C++. In those languages, static methods belong to the class and don't require instances. Python's `@staticmethod` creates similar behavior - a method that doesn't depend on instance or class state.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`@staticmethod` is a decorator that creates a method that doesn't receive an implicit first argument. Unlike instance methods (which get `self`) or classmethods (which get `cls`), staticmethods receive no automatic arguments - they're just regular functions organized within a class namespace.

The main use case is organizing related utility functions under a class name for logical grouping, without needing any instance or class state. For example, validation functions, mathematical operations, or data conversion functions that are thematically related to a class but don't need access to its data.

Staticmethods are less common than instance methods or classmethods because if a function doesn't need access to class or instance data, it could just be a module-level function. However, they're useful when you want to keep related functions together in a class namespace for organizational clarity.

**Key behaviors:**

1. **No implicit first argument:** Unlike instance methods (`self`) or classmethods (`cls`), staticmethods receive no automatic arguments.
2. **Callable on class or instance:** Can be called as `Class.method()` or `instance.method()`, both work identically.
3. **No access to class/instance:** Cannot access `self` or `cls` - if you need access, use instance method or classmethod instead.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (type of method)
- **Action vs State:** DESCRIPTOR - describes what kind of method this is
- **Temporal aspect:** N/A (it's a type descriptor)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound: static + method | Método estático, méthode statique |
| Germanic (de, nl, sv) | Compound noun | Statische Methode (natural compounds) |
| Slavic (ru, pl, uk) | Compound with static + method | Technical compound |
| Arabic | Compound: static + method | Descriptive compound |
| Chinese | Compound noun | 静态方法 (static method) |
| Hindi | Compound | स्थिर विधि (static method) |

**Primary recommendation:** Create a compound combining translations of "static" (fixed/unchanging) and "method". Should parallel the structure of `classmethod` translation.

**Forms to AVOID:**

- ❌ Just "method" - needs "static" qualifier
- ❌ Just "static" - needs "method" specification
- ❌ Different pattern from `classmethod` - should be parallel

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `método_estático`
- **Form:** Compound noun
- **Why it works:** Clear compound of "método" (method) + "estático" (static), parallels `método_clase`, standard term

**Arabic:**

- **Translation:** `دالة_ثابتة` (dāllat thābita - static function/method)
- **Form:** Compound noun
- **Why it works:** Technical compound, "ثابتة" means static/fixed, clear in CS context

**Chinese:**

- **Translation:** `静态方法` (jìngtài fāngfǎ - static method)
- **Form:** Compound noun
- **Why it works:** Standard CS term for staticmethod, widely used in Chinese OOP documentation

**Hindi:**

- **Translation:** `स्थिर_विधि` (sthir vidhi - static method)
- **Form:** Compound noun
- **Why it works:** Clear Sanskrit-derived compound, "स्थिर" means static/fixed, professional

### ❌ Common Translation Mistakes

**Mistake 1: Inconsistent with classmethod**

- **Wrong:** `métodoestático` (no underscore) while `método_clase` (has underscore)
- **Why wrong:** Should use same compound pattern as `classmethod`
- **Right:** `método_estático` (consistent with `método_clase`)

**Mistake 2: Using "constant" instead of "static"**

- **Wrong:** `método_constante` (Spanish - "constant method")
- **Why wrong:** "Static" and "constant" are different concepts; static methods aren't necessarily constant
- **Right:** `método_estático` (static, not constant)

**Mistake 3: Too verbose**

- **Wrong:** `método_sin_estado` (Spanish - "stateless method")
- **Why wrong:** While accurate, too long and non-standard terminology
- **Right:** `método_estático` (standard term)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "staticmethod" is unambiguous in Python

**Single technical meaning:**

✅ **Python meaning:** A method decorator that creates a method with no implicit first argument (no `self` or `cls`).

The term is a Python-specific compound with one clear meaning. Your translation should be a clear compound of "static" + "method" in the target language, parallel to `classmethod` structure.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `staticmethod`, check these translations:**

- [ ] `classmethod` - MUST use parallel compound structure
- [ ] `def` / method - Should use consistent term for "method"
- [ ] `property` - Related decorator, compatible style
- [ ] `class` - For contextual understanding

**Consistency rule:**

The method decorators (`@classmethod`, `@staticmethod`, `@property`) MUST follow consistent naming patterns. The structure of `staticmethod` should mirror `classmethod`:
- If `classmethod` = `método_clase`, then `staticmethod` = `método_estático`
- If `classmethod` = `métodoclase`, then `staticmethod` = `métodoestático`
- Same separator, same word order, same formality

**Example:**

✅ **Consistent:**

- `classmethod` → `método_clase` (underscore compound)
- `staticmethod` → `método_estático` (underscore compound)
- Parallel structure ✅

❌ **Inconsistent:**

- `classmethod` → `método_clase` (underscore)
- `staticmethod` → `métodoestático` (no underscore)
- Different patterns ❌

### Functional relationships

**This term works WITH:**

1. **`@staticmethod` + no special first param**: Unlike `self` or `cls`
2. **`class` definition**: Staticmethods defined within classes

**Common pairing:**

```python
# No self or cls parameter
class Example:
@staticmethod
def func(x, y):  # No self, no cls
return x + y
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Advanced OOP concept
- Must be perfectly parallel to `classmethod`
- Compound term requiring consistent parts
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** Must maintain perfect consistency with `classmethod` translation pattern while correctly translating "static". Requires understanding of both terms to ensure parallel structure and consistent naming conventions.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clearly a compound of "static" + "method"?
- [ ] Distinguishable from instance/class methods?
- [ ] Recognized in OOP contexts?

### 2. Linguistic Correctness

- [ ] Proper compound structure for target language?
- [ ] Uses appropriate "static" translation?
- [ ] Uses same "method" term as `classmethod`?

### 3. Consistency

- [ ] PERFECTLY parallel to `classmethod` structure?
- [ ] Same separator pattern (underscore, concatenation, etc.)?
- [ ] Same formality level as `classmethod`?

### 4. Usability

- [ ] Reasonably concise (2-3 words max)?
- [ ] Easy to understand?
- [ ] Clear that it's a type of method?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] Works with @ decorator syntax?

---

## Translation Output Format

**Your translation:**

```yaml
term: staticmethod
language: {es|ar|zh|hi}
translation: {your_translation}
form: {compound_noun}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you created a compound from "static" + "method" translations, maintaining perfect parallel structure to `classmethod`. Emphasize consistency.}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Need to verify parallel structure with `classmethod`, check OOP terminology}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
