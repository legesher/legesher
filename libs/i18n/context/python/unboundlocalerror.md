# Python Builtin: `UnboundLocalError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`UnboundLocalError` is a subclass of `NameError` raised when a function references a local variable before any value has been bound to it. It typically strikes when a name is assigned *somewhere* in a function - which makes it local throughout the whole function - but is read before that assignment runs. Since Python 3.11 the message spells the situation out: `cannot access local variable 'x' where it is not associated with a value`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Augmented assignment makes 'count' local - then reads it before it exists
count = 0

def increment():
    count += 1   # count = count + 1: the read happens before any local value

increment()
# Raises UnboundLocalError: cannot access local variable 'count'
# where it is not associated with a value      (3.11+ wording)
# Older versions: local variable 'count' referenced before assignment
```

**What this does:** Because `count += 1` assigns to `count`, the compiler classifies `count` as local *for the entire function* - the global `count = 0` is no longer visible inside. The `+=` must first read the local `count`, which has no value yet, so Python raises `UnboundLocalError`.

### Example 2: Common Pattern

```python
# A variable assigned only on one branch
def describe(temperature):
    if temperature > 30:
        label = "hot"
    return label   # UnboundLocalError whenever temperature <= 30

describe(35)  # "hot"
describe(20)  # Raises UnboundLocalError: cannot access local variable 'label'...

# The fix: guarantee a binding on every path
def describe_fixed(temperature):
    label = "moderate"          # bound before any branch
    if temperature > 30:
        label = "hot"
    return label
```

**What this does:** `label` is assigned inside the `if`, so it is local - but when the branch is skipped, the `return` reads a local that was never bound. The reliable fix is initializing the variable before the conditional (or covering every branch with an `else`), so a value exists on every execution path.

### Example 3: Edge Case

```python
# Declaring intent with global/nonlocal avoids the local classification
count = 0

def increment_global():
    global count
    count += 1        # OK: 'count' now refers to the module-level name

def make_counter():
    n = 0
    def bump():
        nonlocal n
        n += 1        # OK: 'n' refers to the enclosing function's variable
        return n
    return bump

# del unbinds a local: reading it afterwards raises the same error
def demo_del():
    x = 1
    del x
    print(x)          # Raises UnboundLocalError

# The subclass relationship
print(issubclass(UnboundLocalError, NameError))  # True
try:
    demo_del()
except NameError:     # Catches UnboundLocalError too
    print("caught via NameError")
```

**What this shows:** `global` and `nonlocal` tell the compiler the name is *not* local, restoring access to the outer binding - the idiomatic cure for Example 1. `del` removes a local binding, so a later read fails the same way. And because `UnboundLocalError` subclasses `NameError`, an `except NameError:` handler catches both.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (specific subclass of `NameError`)

**Similar terms in this pattern:**

1. `NameError` - Parent class: a name could not be found in any accessible scope
2. `AttributeError` - Related lookup failure, for attributes on objects
3. `KeyError` - Related lookup failure, for dictionary keys
4. `ModuleNotFoundError` - Another "specific diagnosis" subclass refining a general error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Subclass names must visibly extend their parent: this is a `NameError` narrowed to *local variables without a value*, so the translation should narrow the `NameError` vocabulary rather than invent an unrelated name.


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin + Latin-derived)

**Root meaning:** "Bound" is the past participle of "bind" (Old English "bindan," to tie); in programming, *binding* is the tie between a name and a value, so "unbound" means "not yet tied to any value." "Local" comes from Latin "locus" (place) - belonging to the local scope, the function's own place. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name states the precise diagnosis in Python's own semantics: a *local* name exists (the compiler created the slot because an assignment appears somewhere in the function) but is *unbound* - no value has been tied to it yet at the moment it is read. It is deliberately more specific than `NameError`: the name is known; its value is missing.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`UnboundLocalError` is raised when a function reads a local variable that has no value bound to it yet. Its root cause is a compile-time rule that surprises almost every Python learner: if a name is assigned *anywhere* in a function body, the compiler classifies that name as local *throughout the entire function*. There is no line-by-line fallback to the global scope. So a function containing `count += 1` treats `count` as local from its first line - and executing the `+=` requires reading the local `count` before anything was ever assigned to it, which raises `UnboundLocalError` even when a global `count` sits in plain sight.

The same mechanism produces the conditional-assignment trap (a variable assigned only inside an `if` branch, then read after it), the `del`-then-read case (deleting a local unbinds it), and confusing shadows (a function that reads a global at the top and assigns to the same name at the bottom fails at the *top*). The remedies map to intent: use `global` or `nonlocal` when you genuinely mean the outer variable; initialize the local before branching when you mean a fresh local; restructure when the function is doing both jobs at once. Python 3.11 rewrote the message from `local variable 'x' referenced before assignment` to `cannot access local variable 'x' where it is not associated with a value`, pointing more clearly at the missing binding rather than implying a mere ordering problem.

As a subclass of `NameError`, it inherits the family meaning - a name lookup failed - while sharpening the diagnosis: the name *is* known to be local; what is missing is its value. Handlers for `NameError` catch it, and its `.name` attribute (like the parent's, since 3.10) carries the variable's name for tooling.

**Key behaviors:**

1. **Locality is decided at compile time, for the whole function:** Any assignment (including `+=`, `for` targets, `with ... as`, unpacking) anywhere in the body makes the name local everywhere in the body. A read that executes before any binding raises `UnboundLocalError` - the global with the same name is not consulted.

2. **Escape hatches are declarations, not assignments:** `global name` and `nonlocal name` reclassify the name so reads and writes go to the module scope or the enclosing function's scope. Initializing the local before use is the alternative when a genuinely local variable is intended.

3. **Subclass of `NameError`:** `except NameError:` catches it; `except UnboundLocalError:` targets only the missing-local-value case. `del x` unbinds a local, so a subsequent read in the same function raises `UnboundLocalError` (whereas reading a never-defined name at module level raises plain `NameError`).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (negated participle + scope adjective + error type)
- **Action vs State:** STATE - describes a variable's condition (no value bound), not an action
- **Temporal aspect:** Instantaneous - occurs at the moment of the premature read

### Recommended Form

**Primary recommendation:** Narrow the `NameError` family with the "local variable" domain: [local variable words] + [family error word]. Unlike `NameError` - which covers all identifiers, so its brief rejects "variable" - this exception genuinely *is* about local variables only, so the variable word is correct here and the contrast is meaningful. Include an "unbound / without value" element only if your language can keep the compound reasonably short (many languages cannot without becoming a sentence).

**Forms to AVOID:**

- ❌ Translating "unbound" as "limitless/unbounded" - a serious false friend; "unbound" here means *not tied to a value*, not "without bounds"
- ❌ Dropping "local" - the local scope is the diagnosis; without it the name collapses into plain `NameError`
- ❌ Full sentences ("variable used before assigning" phrasings) - accurate but far too long; the message explains, the name labels

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Unbound" as limitless, without bounds ("unbounded enthusiasm")
- ❌ Meaning 2: "Unbound" as physically untied or a book without binding
- ❌ Meaning 3: "Local" as geographic ("local news," "local shop")
- ✅ Meaning 4: **A FUNCTION-SCOPE VARIABLE WITH NO VALUE BOUND TO IT** - the name is local to the function, and no assignment has given it a value yet

**Example:**

English components in context:

1. "Her joy knew no bounds - unbounded joy" (limitless) ❌ False friend for "unbound"
2. "An unbound manuscript" (no book binding) ❌
3. "Support your local library" (geographic) ❌
4. `count += 1` reading local `count` before any value is bound ✅ **This is the Python meaning**

**Your translation should capture meaning #4: "binding" is the tie between a name and a value; "unbound" means that tie does not exist yet; "local" means the function's own scope. Prioritize the local-variable diagnosis; encode the missing-binding nuance only if your language can do it compactly.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `UnboundLocalError`, check these translations:**

- [ ] `NameError` - Parent class; this name must read as its narrowed local-variable case (same error word)
- [ ] `global` - The keyword that reclassifies a name to module scope, curing the common case
- [ ] `nonlocal` - The keyword for enclosing-function scope; "local" vocabulary must match
- [ ] `locals()` - The builtin returning local names; same "local" word
- [ ] `del` - Unbinding a local makes later reads raise this exception; "binding" vocabulary should be coherent

**Consistency rule:**

Three vocabularies must lock together: the *error family* word (shared with `NameError`), the *local/scope* word (shared with `nonlocal`, `locals()`, and scope documentation), and - if included - the *binding* word (shared with how documentation describes name↔value binding). This class must compose the `NameError` error word with the exact "local variable" vocabulary the `locals()` documentation uses, not an unrelated coinage.


### Functional relationships

**This term works WITH:**

1. **Assignment anywhere in a function + an earlier read**: The defining trigger

```python
def f():
    print(x)   # UnboundLocalError: the line below makes x local
    x = 1
```

2. **`global`/`nonlocal` + the cure**: Declarations that reclassify the name

```python
total = 0
def add(n):
    global total
    total += n   # OK now
```

**Common pairing:**

```python
# The classic counter, broken and repaired
counter = 0

def broken():
    counter += 1          # UnboundLocalError

def repaired():
    global counter
    counter += 1          # OK: writes the module-level name

# Closure state with nonlocal
def make_accumulator():
    total = 0
    def add(n):
        nonlocal total
        total += n
        return total
    return add

acc = make_accumulator()
acc(5); acc(3)            # 8

# Branch-only assignment, guarded read
def first_word(text):
    for word in text.split():
        found = word
        break
    try:
        return found       # UnboundLocalError if text was empty
    except UnboundLocalError:
        return None

# Catching at the family level
try:
    broken()
except NameError as e:     # UnboundLocalError is a NameError
    print(type(e).__name__, "-", e)
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `UnboundLocalError`

- "Unbound" (in the binding sense) has no everyday equivalent in most languages and a dangerous "limitless" false friend
- Three semantic components (unbound + local + error) strain compound length in most languages; something usually must be dropped, and the choice matters
- Must narrow `NameError` visibly while coordinating with `global`/`nonlocal`/`locals()` scope vocabulary
- The underlying compile-time locality rule is itself unintuitive; the name is many learners' first contact with it

**For this term:** HARD

**Rationale:** The pedagogical stakes are high - this exception is where learners meet Python's whole-function locality rule - and the English name compresses a three-part diagnosis that few languages can compound compactly. The recommended compromise (keep "local variable" + family error word; let docs carry "unbound") should be validated per language by a native reviewer, and any rendering of "unbound" must be checked against the limitless false friend.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOCAL VARIABLE WITHOUT A VALUE (not "limitless," not geographic "local")?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Reads as a more specific `NameError`, not an unrelated exception?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun, not a sentence)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word as the `NameError` translation?
- [ ] "Local" word matches `nonlocal`, `locals()`, and scope documentation?
- [ ] If a "bind" word is used, it matches how docs describe name↔value binding?

### 4. Usability

- [ ] As short as the meaning allows (prefer 2-3 content words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: UnboundLocalError
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries this concept's semantic components in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.


---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-04
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
