# Python Keyword: `nonlocal` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** adjective
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

The `nonlocal` keyword in Python declares that a variable name refers to a variable in the nearest enclosing scope (excluding global), allowing nested functions to modify variables from their parent functions. It enables write access to variables in outer function scopes.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Modify variable from enclosing function
def outer():
    count = 0

    def inner():
        nonlocal count  # Refers to count in outer()
        count += 1
        return count

    return inner

counter = outer()
print(counter())  # 1
print(counter())  # 2
```

**What this does:** The `nonlocal count` declaration tells Python that `count` refers to the variable from the enclosing `outer()` function, not a new local variable. This allows `inner()` to modify the `count` variable that persists across calls through closure.

### Example 2: Common Pattern

```python
# Closure with state
def make_accumulator():
    total = 0

    def add(value):
        nonlocal total
        total += value
        return total

    def reset():
        nonlocal total
        total = 0

    return add, reset

add_func, reset_func = make_accumulator()
print(add_func(10))  # 10
print(add_func(5))   # 15
reset_func()
print(add_func(3))   # 3
```

**What this does:** Multiple nested functions can declare the same enclosing variable as `nonlocal`. Both `add()` and `reset()` modify the same `total` variable from `make_accumulator()`. This creates a closure with shared mutable state.

### Example 3: Edge Case

```python
# Multiple enclosing scopes
def outer():
    x = "outer"

    def middle():
        x = "middle"

        def inner():
            nonlocal x  # Refers to middle's x, not outer's x
            x = "modified"
            print(f"Inner x: {x}")

        inner()
        print(f"Middle x: {x}")

    middle()
    print(f"Outer x: {x}")

outer()
# Prints:
# Inner x: modified
# Middle x: modified  (middle's x was modified)
# Outer x: outer      (outer's x unchanged)
```

**What this shows:** `nonlocal` binds to the nearest enclosing scope with that variable name, not the global scope or all enclosing scopes. With multiple nested functions, `nonlocal x` refers to the closest outer function that defines `x`, skipping farther scopes.

---

## Pattern Classification

**This term is:** SCOPE MODIFIER (Adjective/Declaration)

**Similar terms in this pattern:**

1. `global` - Declares variable from module scope (similar scope modifier)
2. `local` - (not a keyword, but conceptual scope level)
3. No other direct Python keywords, but related to scope hierarchy

**Pattern rule:** Scope modifiers should use adjective forms describing where the variable exists: `global` (module-level), `nonlocal` (enclosing function), `local` (current function). They describe scope properties of variables.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `global` | global | عام | 全局 | वैश्विक |
| `local` | local | محلي | 局部 | स्थानीय |
| `nonlocal` | **no_local** | **غير محلي** | **非局部** | **गैर-स्थानीय** |

---

## Etymology (Brief)

**English Origin:** English prefix + Latin root

**Root meaning:** "Non-" (Latin prefix = not) + "local" (Latin "localis" = relating to a place). Together: "not local." In programming, "nonlocal" means "not in the current local scope, but in an enclosing scope."

**Why Python uses this:** Python 3.0 introduced `nonlocal` to solve a scope problem: how can nested functions modify variables from parent functions? Before `nonlocal`, you could read enclosing variables but not modify them (without tricks like mutable containers). "Nonlocal" precisely describes the target: not the current local scope, not the global scope, but an intermediate enclosing scope. The term distinguishes it from both `local` and `global`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `nonlocal` keyword declares that assignments to specified variable names should modify the variable in the nearest enclosing function scope, rather than creating a new local variable. Python has three main scope levels: local (current function), enclosing (parent functions), and global (module-level). Without `nonlocal`, assigning to a variable in a nested function creates a new local variable, shadowing any variable with the same name in enclosing scopes.

By declaring `nonlocal x`, you tell Python to search enclosing function scopes for `x` and bind assignments to that variable. This enables nested functions to maintain and modify state in their parent function's scope through closures. The variable must exist in an enclosing scope—`nonlocal` cannot create new variables, only bind to existing ones.

`Nonlocal` searches through enclosing function scopes (excluding global) and binds to the nearest one containing that variable name. If no enclosing scope has the variable, Python raises a SyntaxError. This differs from `global`, which always refers to module-level scope.

**Key behaviors:**

1. **Nearest enclosing scope:** With multiple nested functions, `nonlocal` binds to the closest enclosing function that has that variable. It doesn't search global scope. If the variable exists in multiple enclosing scopes, it uses the nearest one.

2. **Must already exist:** Unlike assignment which creates variables, `nonlocal` requires the variable to already exist in an enclosing scope. You can't use `nonlocal x` if no enclosing function has defined `x`. This prevents typos from creating unintended variables.

3. **Closures and state:** The primary use case is creating closures with mutable state. Nested functions can remember and modify variables from their parent function even after the parent function returns. This enables factory functions that produce customized functions with private state.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective (negative form) describing scope (not local, from enclosing)
- **Action vs State:** STATE descriptor - describes where the variable lives
- **Temporal aspect:** Static - the variable's scope relationship doesn't change

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Negative adjective | "no local", "non local" - meaning not-local |
| Germanic (de, nl, sv) | Negative adjective | "nichtlokal", "niet-lokaal" - meaning not-local |
| Slavic (ru, pl, uk) | Negative adjective | "нелокальный", "nielokalny" - meaning not-local |
| Arabic | Negative adjective | "غير محلي" (ghayr maḥallī) - meaning not local |
| Chinese | Negative adjective | "非局部" (fēi júbù) - meaning non-local |
| Hindi | Negative adjective | "गैर-स्थानीय" (gair-sthānīya) - meaning non-local |

**Primary recommendation:** Use negative adjective form meaning "non-local" or "not local." The word should convey "in an enclosing scope, not the current local scope, and not global."

**Forms to AVOID:**

- ❌ Using "outer" - too vague (could mean global)
- ❌ Using "parent" - too metaphorical (scope isn't exactly parental)
- ❌ Using "enclosing" alone - less precise than "nonlocal"

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `no_local` or `nolocal`
- **Form:** Negative adjective (compound)
- **Why it works:** Direct translation: "no" (not) + "local" (local) = "not local." Clear and logical. Mirrors the English structure. Distinguishes from both `local` and `global`. Spanish often uses "no" prefix for negation.

**Arabic:**

- **Translation:** `غير محلي` (ghayr maḥallī)
- **Form:** Negative adjective phrase
- **Why it works:** غير (ghayr = not/non) + محلي (maḥallī = local) = "not local." Standard Arabic construction for negative adjectives. Clear scope distinction. Used in Arabic technical writing.

**Chinese:**

- **Translation:** `非局部` (fēi júbù)
- **Form:** Negative adjective compound
- **Why it works:** 非 (fēi = non/not) + 局部 (júbù = local) = "non-local." Standard Chinese construction for negation. Parallels the structure of the English term. Clear scope semantics.

**Hindi:**

- **Translation:** `गैर-स्थानीय` (gair-sthānīya)
- **Form:** Negative adjective compound
- **Why it works:** गैर (gair = non/un) + स्थानीय (sthānīya = local) = "non-local." Standard Hindi construction. Clear scope distinction. Used in Hindi technical contexts for "non-local" concepts.

### ❌ Common Translation Mistakes

**Mistake 1: Using "outer" or "external"**

- **Wrong:** `externo` (Spanish - "external")
- **Why wrong:** "External" suggests outside the program or module (like external files/libraries), not enclosing function scope. "Nonlocal" specifically means "in an enclosing function scope," not just "outside" vaguely. "No local" is more precise.
- **Right:** `no_local` (not in current local scope, but in enclosing)

**Mistake 2: Using "parent" or "parental"**

- **Wrong:** `padre` (Spanish - "parent")
- **Why wrong:** While enclosing functions are conceptually "parent" functions, "parent" is too metaphorical for a scope keyword. Python uses "enclosing scope," not "parent scope" in documentation. "Nonlocal" is more technical and precise.
- **Right:** `no_local` (technical scope term)

**Mistake 3: Using positive term instead of negative**

- **Wrong:** `envolvente` (Spanish - "enclosing")
- **Why wrong:** The English keyword is "nonlocal" (negative construction), not "enclosing" (positive construction). Translations should mirror the linguistic structure: negative adjective modifying "local." This helps learners map between English and native language.
- **Right:** `no_local` (mirrors the negative structure)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (it's a technical term specific to programming)

**If YES, identify the CORRECT meaning for Python:**

N/A - "Nonlocal" is unambiguous in English. It's a technical term coined for programming. The only meaning is: "referring to a variable in an enclosing function scope (not local, not global)."

**Key semantic components:**

- **Negative:** NOT in the current local scope
- **Scope level:** In an enclosing function scope
- **Exclusions:** NOT global, NOT local to current function
- **Binding:** Refers to nearest enclosing function with that variable

**Translation clarity:**

Since this is an unambiguous technical term, translations should maintain the negative structure ("non-" or "not") to distinguish clearly from both "local" and "global." The three-way distinction is crucial:

- **local:** current function scope
- **nonlocal:** enclosing function scope
- **global:** module scope

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `nonlocal`, check these translations:**

- [ ] `global` - Similar scope modifier; both should use adjective forms
- [ ] `local` (concept) - Conceptual opposite; nonlocal contrasts with local
- [ ] `def` - Defines functions that create nested scopes; nonlocal navigates these scopes

**Consistency rule:**

Scope modifiers (`global`, `nonlocal`) should use consistent linguistic forms: adjectives describing scope location. The three-level scope system (local, nonlocal/enclosing, global) should have parallel structures.

**Example:**

Spanish scope hierarchy:

- `local` (local - current function) - adjective
- `no_local` (nonlocal - enclosing function) - negative adjective
- `global` (global - module) - adjective

All three are adjectives describing scope. ✅ Consistent

NOT: `local` (adjective) + `envolver` (verb - to enclose) + `global` (adjective) ❌ Inconsistent

### Functional relationships

**This term works WITH:**

1. **Nested functions and closures:**

```python
def outer():
    x = 0
    def inner():
        nonlocal x
        x += 1
    return inner
```

2. **Multiple enclosing variables:**

```python
def factory():
    count = 0
    total = 0

    def update(value):
        nonlocal count, total
        count += 1
        total += value

    return update
```

**Common pairing:**

```python
# Counter closure
def make_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    return increment

# State machine
def make_toggle():
    state = False

    def toggle():
        nonlocal state
        state = not state
        return state

    return toggle

# Accumulator with reset
def make_accumulator():
    total = 0

    def add(n):
        nonlocal total
        total += n
        return total

    def get():
        return total

    def reset():
        nonlocal total
        total = 0

    return add, get, reset

# Nested scope chain
def level1():
    x = "level1"

    def level2():
        nonlocal x
        x = "modified"

        def level3():
            nonlocal x
            print(x)  # Accesses level1's x via level2

        return level3

    return level2
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `nonlocal`

- Relatively new concept (Python 3.0+, 2008)
- Not all languages have nested function scope modification
- "Nonlocal" is English-specific technical coinage
- Translation requires maintaining negative structure
- Some languages might not have established term yet
- Risk of confusion with "global" or "external"

**For this term:** HARD

**Rationale:** "Nonlocal" is a specialized technical term for a somewhat advanced Python feature (closures with mutable state). Many learners encounter it later in their Python journey. Not all programming languages have an equivalent concept, so CS education in some languages may not have established translations. The negative structure ("non-X") must be preserved for clarity. Human review recommended to ensure translations maintain the precise scope semantics.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ENCLOSING SCOPE concept (not local, not global)?
- [ ] Maintains negative structure (non-/not-)?
- [ ] Distinguishes clearly from both "local" and "global"?
- [ ] Understood as referring to parent function's scope?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective)?
- [ ] Uses negative construction (non-/not- prefix)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other scope keywords (`global`)?
- [ ] Uses adjective form like other scope descriptors?
- [ ] Creates logical three-way scope distinction (local/nonlocal/global)?

### 4. Usability

- [ ] Short enough (1-2 words, compound acceptable)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (logical negative form)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?
- [ ] Underscore or hyphen acceptable if needed for compound?

---

## Translation Output Format

**Your translation:**

```yaml
term: nonlocal
language: es
translation: no_local
form: negative_adjective_compound
confidence: medium
```

**Rationale (2-3 sentences):**

Spanish "no_local" directly mirrors the English structure: "no" (not) + "local" (local). This maintains the negative construction and clearly distinguishes the scope from both "local" and "global." The underscore connects the compound for keyword clarity.

**Alternatives considered:**

1. `nolocal` (single word) - Could work but less clear that "no" is negating "local"
2. `envolvente` (enclosing) - Doesn't capture the negative structure; wrong linguistic form
3. `externo` (external) - Too vague, suggests outside the module rather than enclosing function
4. `no-local` (hyphen) - Alternative punctuation, but underscore more common in Python keywords

**If confidence is not HIGH, explain:**

Confidence is MEDIUM because "nonlocal" is a newer technical term (Python 3.0+) and Spanish CS education may not have a universally established translation yet. "No_local" is logical and clear, but native speaker review is recommended to confirm it sounds natural to Spanish Python programmers. Alternative structures (hyphen vs underscore) may also need community input.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
