# Python Keyword: `global` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** adjective
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `global` keyword in Python declares that a variable name refers to a variable in the global (module-level) scope, allowing functions to modify global variables rather than creating local ones. It enables write access to variables defined outside the function.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Modify global variable from function
counter = 0

def increment():
    global counter  # Declare counter refers to global variable
    counter += 1    # Modifies the global counter

increment()
print(counter)  # Prints: 1
```

**What this does:** Without `global counter`, Python would treat `counter += 1` as creating a new local variable, causing an error. The `global` declaration tells Python that `counter` refers to the module-level variable, allowing the function to modify it.

### Example 2: Common Pattern

```python
# Multiple global declarations
total = 0
count = 0

def add_value(value):
    global total, count  # Declare multiple globals
    total += value
    count += 1
    return total / count  # Calculate average

add_value(10)
add_value(20)
print(f"Total: {total}, Count: {count}")  # Total: 30, Count: 2
```

**What this does:** A function can declare multiple global variables in one statement. This allows the function to modify several module-level variables. The declarations must appear before the variables are used in the function.

### Example 3: Edge Case

```python
# Reading vs writing global variables
message = "Hello"

def read_global():
    # No global declaration needed for reading
    print(message)  # Can read global without declaration

def write_global():
    global message  # Declaration needed for writing
    message = "Goodbye"  # Modifies global variable

read_global()   # Prints: Hello
write_global()
read_global()   # Prints: Goodbye
```

**What this shows:** Python allows reading global variables without `global` declaration. You only need `global` when modifying (writing to) a global variable. If you assign to a name without `global`, Python creates a new local variable, shadowing the global one.

---

## Pattern Classification

**This term is:** SCOPE MODIFIER (Adjective/Declaration)

**Similar terms in this pattern:**

1. `nonlocal` - Declares variable from enclosing scope (similar scope modifier)
2. `local` - (not a Python keyword, but conceptual opposite of global)
3. No direct Python keyword pair, but related to scope concepts

**Pattern rule:** Scope modifiers should use adjective forms describing where the variable exists: global (worldwide), nonlocal (parent scope), local (current scope). They describe the scope property of variables.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `nonlocal` | no_local | غير محلي | 非局部 | गैर-स्थानीय |
| `global` | **global** | **عام** | **全局** | **वैश्विक** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "globus" (sphere, ball) became French "global" meaning "worldwide, universal, encompassing everything." In programming, "global" means "accessible from everywhere, across all functions within a module."

**Why Python uses this:** "Global" perfectly captures the scope concept: a global variable exists at the module level, accessible from all functions. The term comes from early programming languages where "global scope" contrasted with "local scope" (within a function). "Global" is nearly universal across programming languages (C, JavaScript, PHP, etc.), making it recognizable to programmers learning Python.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `global` keyword declares that assignments to specified variable names should modify the module-level (global) variable rather than creating a new local variable. Python's scope rules normally treat any name assigned within a function as local to that function. When you write `x = 5` inside a function, Python creates a local variable `x`, even if a global variable `x` already exists.

The `global` statement overrides this default behavior. By declaring `global x` at the beginning of a function, you tell Python that references to `x` within that function should use the module-level `x`. Assignments like `x = 5` will modify the global `x`, not create a local one.

You can read global variables without declaring them global—Python searches outer scopes automatically when a name isn't found locally. The `global` declaration is only necessary when you want to assign (modify) a global variable from within a function.

**Key behaviors:**

1. **Declaration before use:** `global` declarations must appear before you use the variable in the function. Typically placed at the function's beginning. Multiple variables can be declared in one statement: `global x, y, z`.

2. **Module-level scope only:** `global` refers to the module's top-level namespace, not truly "global" across all modules. Each module has its own global namespace. If you import a module, its globals are separate from your module's globals.

3. **Read vs. write distinction:** Reading a global variable doesn't require `global`. Only write operations (assignment, augmented assignment like `+=`, deletion) require the declaration. This asymmetry surprises beginners: `print(x)` works without `global x`, but `x += 1` doesn't.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective describing scope (global scope, worldwide scope)
- **Action vs State:** STATE descriptor - describes where the variable lives
- **Temporal aspect:** Static/permanent - the variable's scope doesn't change over time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adjective | "global", "mondial" - meaning worldwide/universal |
| Germanic (de, nl, sv) | Adjective | "global", "globaal" - meaning global/universal |
| Slavic (ru, pl, uk) | Adjective | "глобальный", "globalny" - meaning global |
| Arabic | Adjective | "عام" (ʿām) or "عالمي" (ʿālamī) - meaning general/global/universal |
| Chinese | Adjective | "全局" (quánjú) - meaning global/overall |
| Hindi | Adjective | "वैश्विक" (vaishvik) or "सार्वभौमिक" (sārvabhaumik) - meaning global/universal |

**Primary recommendation:** Use adjective form meaning "global," "worldwide," or "universal." The word should convey "accessible everywhere within the module" rather than "local to one function."

**Forms to AVOID:**

- ❌ Using "public" - wrong concept (visibility vs. scope)
- ❌ Using "universal" - may be too broad (implies across all modules)
- ❌ Using verb form "to globalize" - should be adjective

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `global`
- **Form:** Adjective (loanword)
- **Why it works:** "Global" is used in Spanish programming as a loanword. Widely understood and standard in Spanish CS education. Alternative "mundial" exists but "global" is more common in technical contexts. Recognized internationally.

**Arabic:**

- **Translation:** `عام` (ʿām) or `عالمي` (ʿālamī)
- **Form:** Adjective
- **Why it works:** `عام` means "general/public/global." Shorter and more common. `عالمي` means "global/worldwide" (from عالم = world). Both acceptable; `عام` is more concise.

**Chinese:**

- **Translation:** `全局` (quánjú)
- **Form:** Adjective compound
- **Why it works:** 全 (complete/whole) + 局 (scope/situation) = "global scope/overall situation." Standard Chinese programming term for global scope. Used universally in Chinese CS education.

**Hindi:**

- **Translation:** `वैश्विक` (vaishvik)
- **Form:** Adjective
- **Why it works:** Sanskrit-derived adjective meaning "global, worldwide, universal." Formal and professional. Used in Hindi technical writing. Alternative: सार्वभौमिक (more philosophical) or ग्लोबल (transliteration, less preferred).

### ❌ Common Translation Mistakes

**Mistake 1: Using "public" instead of "global"**

- **Wrong:** `público` (Spanish - "public")
- **Why wrong:** "Public" refers to visibility/access control (public vs. private), not scope (global vs. local). These are different concepts. Global variables exist at module level; public variables are accessible from outside a class. Confusing these concepts misleads learners.
- **Right:** `global` (scope modifier, not access modifier)

**Mistake 2: Using "universal" with too-broad meaning**

- **Wrong:** `universal` (Spanish - might imply across all programs/modules)
- **Why wrong:** While semantically close, "global" in Python means module-level scope, not truly universal across all modules. "Universal" might suggest broader reach than Python's globals have. "Global" is more precise.
- **Right:** `global` (module-level scope)

**Mistake 3: Using verb or noun form**

- **Wrong:** `globalizar` (Spanish - "to globalize" - verb)
- **Why wrong:** `global` is an adjective describing the variable's scope, not a verb performing an action. The keyword declares scope property, not an action to perform.
- **Right:** `global` (adjective)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Worldwide, affecting the whole world" (geopolitical context)
- ❌ Meaning 2: "Comprehensive, considering everything" (holistic approach)
- ✅ Meaning 3: **"MODULE-LEVEL SCOPE, accessible from all functions"** (programming scope)

**Example:**

English "global" can mean:

1. "Global warming affects everyone" (worldwide - geopolitical) ❌
2. "Take a global view of the problem" (comprehensive/holistic) ❌
3. "Global variables exist at module level" (programming scope) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: variable scope at the module level, accessible from all functions within that module, contrasting with local (function-level) scope.**

The key semantic components are:
- **Scope level:** Module-level, not function-level
- **Accessibility:** Available to all functions in the module
- **Contrast:** Opposite of "local" (function-specific)

Important nuance: Python's "global" is actually "module-global," not "program-global." Each module has its own global namespace. True cross-module globals require imports.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `global`, check these translations:**

- [ ] `nonlocal` - Similar scope modifier for enclosing scope; both should use adjective forms
- [ ] `def` - Defines functions which have local scope; global contrasts with this local scope
- [ ] `class` - Defines classes which also have scope; related scope concept

**Consistency rule:**

Scope-related keywords and concepts should use consistent forms. If `global` is an adjective, `nonlocal` should also be an adjective (or adjective phrase). Don't mix adjectives with verbs for scope modifiers.

**Example:**

Spanish:
- `global` (adjective) + `no_local` (adjective phrase) ✅ Consistent
- NOT: `global` (adjective) + `localizar` (verb - to localize) ❌ Inconsistent

### Functional relationships

**This term works WITH:**

1. **Functions and assignment:** `global` enables functions to modify module-level variables
```python
x = 0
def increment():
    global x
    x += 1
```

2. **Multiple declarations:** Can declare several globals at once
```python
def reset():
    global count, total, average
    count = total = average = 0
```

**Common pairing:**

```python
# State management with global variables
state = "inactive"

def activate():
    global state
    state = "active"

def deactivate():
    global state
    state = "inactive"

# Counter pattern
counter = 0

def increment():
    global counter
    counter += 1
    return counter

# Configuration globals
DEBUG = False

def enable_debug():
    global DEBUG
    DEBUG = True

# Multiple related globals
total_score = 0
player_count = 0

def add_player_score(score):
    global total_score, player_count
    total_score += score
    player_count += 1
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `global`:

- Universal programming concept (scope exists in all languages)
- Many languages use "global" as loanword in technical contexts
- Moderate ambiguity: "global," "worldwide," "universal," "general" are all possible
- Risk of confusion with "public" (access control vs. scope)
- Translation choice depends on whether target language adopts English technical terms

**For this term:** MEDIUM

**Rationale:** "Global" is widely used internationally in programming, often as a loanword. However, some languages may prefer native terms. The concept is clear but choosing between loanword vs. native translation requires cultural/linguistic knowledge. Additionally, must distinguish from "public" (wrong concept). Check local CS education for preference.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures MODULE-LEVEL SCOPE concept?
- [ ] Distinguishes from "public" (access control)?
- [ ] Contrasts with "local" (function-level)?
- [ ] Understood as scope modifier, not access modifier?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective)?
- [ ] Describes scope location (where variable lives)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other scope keywords (`nonlocal`)?
- [ ] Uses adjective form like other scope descriptors?
- [ ] Aligns with how scope is taught in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common adjective)?

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
term: global
language: es
translation: global
form: adjective
confidence: high
```

**Rationale (2-3 sentences):**

Spanish programming uses "global" as a loanword from English. It's universally understood in Spanish CS education and technical documentation. While native alternatives like "mundial" exist, "global" is the standard technical term.

**Alternatives considered:**

1. `mundial` (worldwide) - Native Spanish, but less common in technical contexts
2. `general` (general) - Could work but less specific than "global"
3. `universal` (universal) - Too broad, implies more than module-level scope

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for Spanish. "Global" is the standard loanword. For languages that resist loanwords (like French with "mondial" or Arabic with "عام"), verify which form is preferred in CS education for that language. Some languages strongly prefer native terms over English loanwords.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
