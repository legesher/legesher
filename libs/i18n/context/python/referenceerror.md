# Python Builtin: `ReferenceError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`ReferenceError` is a built-in exception raised when a weak reference proxy (created with `weakref.proxy`) is used after the object it refers to has been garbage-collected. It is one of Python's rarest built-in exceptions, appearing almost exclusively in code that uses the `weakref` module for caches, observers, and other non-owning references.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Using a weakref proxy after its referent is gone
import weakref

class Config:
    pass

config = Config()
proxy = weakref.proxy(config)

proxy.mode = "fast"     # Works: the referent is alive
print(proxy.mode)       # fast

del config              # Last strong reference removed; object collected
print(proxy.mode)
# Raises ReferenceError: weakly-referenced object no longer exists
```

**What this does:** `weakref.proxy(config)` creates a proxy that behaves like `config` without keeping it alive. While `config` exists, the proxy forwards every operation transparently. After `del config` removes the last strong reference, the object is collected, and ANY use of the proxy raises `ReferenceError`.

### Example 2: Common Pattern

```python
# Guarding proxy access - or preferring weakref.ref with a None check
import weakref

class Listener:
    def notify(self):
        print("notified")

listener = Listener()
proxy = weakref.proxy(listener)

def notify_safely(p):
    try:
        p.notify()
    except ReferenceError:
        print("listener already gone; dropping it")

notify_safely(proxy)   # notified
del listener
notify_safely(proxy)   # listener already gone; dropping it

# Alternative style: weakref.ref returns None instead of raising
ref = weakref.ref(Listener())
target = ref()             # the referent was already collected here
if target is None:
    print("no listener to notify")
```

**What this does:** Code holding proxies long-term wraps access in `try/except ReferenceError` because the referent can die at any time. The sibling API `weakref.ref` offers the non-raising style: call the reference to get the object or `None`. Choosing proxy-plus-exception vs. ref-plus-None-check is a design decision; only the proxy raises `ReferenceError`.

### Example 3: Edge Case

```python
# EVERY operation on a dead proxy raises - even printing it
import weakref

class Node:
    def __len__(self):
        return 3

node = Node()
proxy = weakref.proxy(node)
print(len(proxy))      # 3 - dunder calls are forwarded too

del node

try:
    len(proxy)         # forwarded __len__ hits the dead referent
except ReferenceError:
    print("len() failed")

try:
    str(proxy)         # even converting to a string fails
except ReferenceError:
    print("str() failed")

# The proxy object itself still exists - only its TARGET is gone
print(type(proxy))     # <class 'weakproxy'>
```

**What this shows:** The proxy is not a value that "becomes None" - it is a live forwarding object whose target has vanished. Attribute access, method calls, `len()`, `str()`, arithmetic: every forwarded operation raises `ReferenceError` once the referent is collected. Only operations on the proxy object itself (like `type()`) still succeed.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `NameError` - Also "the thing you referred to is not there," but for names in namespaces
2. `AttributeError` - Missing attribute on a live object (vs. a dead referent here)
3. `KeyError` - Missing key in a mapping; same family of failed lookups
4. `MemoryError` - Fellow memory-management exception (allocation vs. object lifetime)

**Pattern rule:** Exception classes are noun compounds, typically ending with "Error" in English. Translations should combine the problem domain ("reference") with the same "error" word used by every other exception in the pack.


---

## Etymology (Brief)

**English Origin:** Latin compounds

**Root meaning:** "Reference" from Latin "referre" meaning "to carry back, to relate to" (re- "back" + ferre "to carry") - a reference points back to something else. "Error" from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The exception guards weak references - pointers that deliberately do NOT keep their target alive. When such a reference is followed after its target has been collected, the reference itself is the broken thing, so Python names the exception after it. The name predates the `weakref` module's modern API (it was once `weakref.ReferenceError` before becoming a builtin), which is why it says "reference" rather than "weak reference."

---

## Concept Explanation (Intermediate Level)

**What it does:**

Python objects normally stay alive as long as something refers to them. The `weakref` module provides the exception to that rule: weak references point at an object without owning it, so the object can be collected the moment its last STRONG reference disappears. This is the standard tool for caches that should not pin their entries in memory, observer lists that should not keep listeners alive, and parent-child structures that must avoid reference cycles.

`weakref.proxy(obj)` is the convenient form: it returns an object that transparently forwards attribute access, method calls, and most operations to the referent, so code can use the proxy exactly as if it were the object. The price of that transparency is `ReferenceError`: when the referent has been collected, there is no object to forward to, and every forwarded operation raises. The exception is therefore not about wrong data or a coding typo - it is about object LIFETIME: the target no longer exists, and the proxy is a dangling (but memory-safe) pointer. Unlike a dangling pointer in C, following it is perfectly safe: you get a clean, catchable exception instead of undefined behavior.

Two clarifications keep the concept sharp. First, this is among the rarest built-in exceptions - most Python developers never see it, because most code never touches `weakref`; JavaScript developers should note it is unrelated to JavaScript's `ReferenceError` (which is closer to Python's `NameError`). Second, its non-raising sibling: `weakref.ref(obj)` must be CALLED to dereference, returning the object or `None` when dead - that style never raises `ReferenceError`. The proxy raises precisely because it hides the dereference step.

**Key behaviors:**

1. **Raised on any use of a dead proxy:** Once the referent is collected, attribute access, method calls, `len()`, `str()`, comparisons - every forwarded operation on the `weakref.proxy` object raises `ReferenceError`. The proxy never becomes `None`; it stays a proxy whose target is gone.

2. **Timing depends on garbage collection:** In CPython, removing the last strong reference collects the object immediately (reference counting), so the error is deterministic in simple cases. With reference cycles or alternative interpreters, collection - and therefore the first `ReferenceError` - can happen later.

3. **Only the proxy style raises it:** `weakref.ref` returns `None` from a dead reference instead of raising, and `WeakValueDictionary`/`WeakKeyDictionary` simply drop dead entries. `ReferenceError` is the proxy's contract: transparent access in exchange for an exception at death.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment a dead proxy is used

### Recommended Form

**Primary recommendation:** Use a compound noun combining the language's CS term for "reference" (the pointer/refer-to-object sense, as in "pass by reference") with the pack's standard "error" word.

**Forms to AVOID:**

- ❌ The bibliographic sense of reference (citation, footnote) - wrong domain
- ❌ The recommendation-letter sense of reference - wrong domain
- ❌ Verb forms - exception classes are noun compounds, never actions

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A bibliographic citation ("see reference [12]")
- ❌ Meaning 2: A character reference or recommendation ("glowing references")
- ❌ Meaning 3: The act of mentioning ("a reference to her earlier work")
- ❌ Meaning 4: JavaScript's ReferenceError (an undefined variable name - that is Python's `NameError`)
- ✅ Meaning 5: **A POINTER TO AN OBJECT IN MEMORY - here, a weak reference whose target has been collected**

**Example:**

English "reference" can mean:

1. "List your references at the end of the paper" (citations) ❌
2. "Her manager provided a reference" (recommendation) ❌
3. "He made reference to the budget" (mention) ❌
4. `x` is not defined → ReferenceError (JavaScript's meaning) ❌
5. `weakref.proxy(obj)` used after `obj` was collected (a dead object reference) ✅ **This is the Python meaning**

**Your translation should capture meaning #5: the memory-management sense of reference - the same word used in "reference counting" and "pass by reference" in your language's CS vocabulary.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ReferenceError`, check these translations:**

- [ ] `NameError` - Must be clearly distinct; JavaScript users will expect them conflated, and they must not be
- [ ] `AttributeError` - What failed attribute access on a LIVE object raises; the dead-referent case must contrast with it
- [ ] `MemoryError` - Fellow memory-management exception; family prose should distinguish lifetime vs. allocation
- [ ] `del` - The statement that typically removes the last strong reference in examples
- [ ] `None` - What `weakref.ref` returns for dead referents; the non-raising alternative in prose

**Consistency rule:**

Use the same "reference" word your language's documentation uses for reference counting and pass-by-reference, and the pack's standard "error" word. Verify the triangle `NameError` / `AttributeError` / `ReferenceError` translates to three clearly distinct domains: names, attributes, references.


### Functional relationships

**This term works WITH:**

1. **`weakref.proxy` + `ReferenceError`**: The object whose dead-target use raises it

```python
proxy = weakref.proxy(target)
# ... target collected ...
proxy.attr  # ReferenceError
```

2. **Exception handling**:

```python
try:
    proxy.refresh()
except ReferenceError:
    unregister(proxy)
```

**Common pairing:**

```python
import weakref

# An observer registry that does not keep observers alive
class EventBus:
    def __init__(self):
        self._observers = []

    def register(self, observer):
        self._observers.append(weakref.proxy(observer))

    def fire(self, event):
        alive = []
        for obs in self._observers:
            try:
                obs.on_event(event)
                alive.append(obs)
            except ReferenceError:
                pass  # observer was collected; silently drop it
        self._observers = alive

# The non-raising alternative for comparison
class Cache:
    def __init__(self):
        self._entry = None

    def put(self, obj):
        self._entry = weakref.ref(obj)

    def get(self):
        if self._entry is None:
            return None
        return self._entry()   # object, or None if collected - no exception
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ReferenceError`

- "Reference" is heavily polysemous (citation, recommendation, mention) - the CS pointer sense must be selected
- Most languages have a settled CS term via "pass by reference"/"reference counting" vocabulary
- The JavaScript false friend (`ReferenceError` = undefined name) is a real cross-language trap for translators who know web development
- The underlying `weakref` concept is rare and advanced, so translators are unlikely to know it firsthand

**For this term:** MEDIUM

**Rationale:** The compound is mechanical and the CS sense of "reference" is well-established in most languages, which caps the difficulty at MEDIUM. The risks are selectional: choosing a non-CS sense of "reference," or - more insidiously - letting JavaScript's unrelated `ReferenceError` semantics steer the translation toward name-lookup vocabulary. The brief's examples exist precisely to anchor the weak-reference meaning.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the OBJECT-POINTER sense of reference (not citation/recommendation)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Consistent with "the referred-to object no longer exists" (not "name undefined")?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same "reference" word as pass-by-reference/reference-counting vocabulary in this language?
- [ ] Same "error" word as `NameError`, `AttributeError`, `MemoryError`?
- [ ] Clearly distinct from the `NameError` translation?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
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
term: ReferenceError
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
