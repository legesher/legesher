# Python Builtin: `NotImplementedError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`NotImplementedError` is a built-in exception raised to mark a method or function that exists but has deliberately not been implemented - typically an abstract method that subclasses must override, or a stub awaiting future work. It is critically distinct from `NotImplemented`, which is a special VALUE returned (never raised) by binary dunder methods like `__eq__` and `__add__`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A base-class method that subclasses must override
class Storage:
    def save(self, data):
        raise NotImplementedError("Subclasses must implement save()")

Storage().save(b"payload")
# Raises NotImplementedError: Subclasses must implement save()
```

**What this does:** The base class defines the interface (`save` exists and documents its contract) but provides no behavior. Calling it raises `NotImplementedError` with a message telling the developer exactly what is missing: an override in a subclass.

### Example 2: Common Pattern

```python
# Abstract interface with concrete subclasses
class Exporter:
    def export(self, records):
        raise NotImplementedError

class CsvExporter(Exporter):
    def export(self, records):
        return "\n".join(",".join(map(str, r)) for r in records)

class JsonExporter(Exporter):
    pass  # forgot to override!

print(CsvExporter().export([(1, 2)]))  # "1,2"

try:
    JsonExporter().export([(1, 2)])
except NotImplementedError:
    print("JsonExporter does not implement export() yet")
```

**What this does:** `Exporter.export` is a placeholder that every real exporter must replace. The forgotten override in `JsonExporter` fails loudly at call time instead of silently doing nothing - the exception converts an incomplete class into an explicit, debuggable error.

### Example 3: Edge Case

```python
# NotImplementedError (exception) vs NotImplemented (value) - do not mix them
class Meters:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, Meters):
            return NotImplemented   # VALUE: returned, lets Python try other.__eq__
        return self.value == other.value

print(Meters(3) == Meters(3))  # True
print(Meters(3) == "3m")       # False (both sides declined; Python falls back)

# Raising the VALUE is a TypeError - it is not an exception:
# raise NotImplemented
# TypeError: exceptions must derive from BaseException

# Raising the EXCEPTION from __eq__ would be wrong too:
# it would abort every mismatched comparison instead of delegating.
```

**What this shows:** The two names divide cleanly by verb: you `raise NotImplementedError` from unfinished methods, and you `return NotImplemented` from binary dunder methods to trigger Python's reflected-operation protocol. Swapping them breaks programs in both directions.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `NotImplemented` - The sentinel VALUE with the near-identical name; the pair must translate as visibly related but distinct
2. `RuntimeError` - The direct parent class of `NotImplementedError`
3. `TypeError` - Raised when operations are unsupported for a type (what unhandled `NotImplemented` becomes)
4. `AttributeError` - Another `...Error` noun compound in the same family

**Pattern rule:** Exception classes are noun compounds ending with the pack's "error" word. `NotImplementedError` = the existing `NotImplemented` translation (negated past participle) + "error," so the exception visibly extends the value's name exactly as it does in English.


---

## Etymology (Brief)

**English Origin:** Germanic negation + Latin participle + Latin noun

**Root meaning:** "Not" (Germanic negation) + "implemented" from Latin "implere" meaning "to fill up, fulfill, carry out" - an implementation is a carried-out plan. "Error" from Latin "error" meaning "wandering, mistake." Together: the error of something not having been carried out.

**Why Python uses this:** Python needed a standard way for a method to say "I exist as an interface, but nobody has written my body." Deriving the name from the state description "not implemented" plus the conventional "Error" suffix makes stubs self-documenting. The unfortunate side effect is a near-collision with the older sentinel value `NotImplemented`; Python keeps both because they serve unrelated protocols.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`NotImplementedError` marks intentional gaps. When a base class defines an interface, it can give each required method a body of `raise NotImplementedError`, so any subclass that forgets an override fails immediately and explicitly at call time rather than misbehaving quietly. The same pattern marks work-in-progress: a function whose signature is settled but whose body is pending can raise it as a to-do marker. Operating-system-dependent features also use it - a method may raise `NotImplementedError` on platforms where the operation is unavailable.

The class inherits from `RuntimeError`. In modern Python, the `abc` module (`ABC`, `@abstractmethod`) is the stronger tool for enforcing interfaces - it prevents instantiation of incomplete classes rather than failing at call time - but `raise NotImplementedError` remains ubiquitous for lightweight interfaces, mixins, and stubs, and the two techniques are often combined (an abstract method whose body raises it for anyone calling via `super()`).

The essential confusion to prevent - and the reason this brief exists - is with `NotImplemented`, the singleton VALUE. Binary dunder methods (`__eq__`, `__lt__`, `__add__`, ...) RETURN `NotImplemented` to tell the interpreter "I don't handle this operand type; try the other operand's reflected method." That is a normal, silent part of the operator protocol, not an error. Raising `NotImplementedError` from `__eq__` would abort comparisons that should have been delegated; returning `NotImplemented` from an unfinished ordinary method would just hand callers a strange value. One is a raised exception; the other is a returned sentinel. The names differ only by "Error" - and in translation they must keep exactly that relationship.

**Key behaviors:**

1. **Raised, never returned:** `raise NotImplementedError("message")` is the correct use. It signals "this callable is not implemented here"; callers may catch it to detect optional/unfinished features.

2. **Subclasses `RuntimeError`:** `except RuntimeError:` also catches it. It is a genuine error class on the `Exception` side of the hierarchy, unlike control-flow signals.

3. **Not the operator-protocol tool:** Binary dunder methods must `return NotImplemented` (the value) instead. If both operands' methods return the value, Python raises `TypeError` - not `NotImplementedError` - for the unsupported operation.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (negated past participle + error noun)
- **Action vs State:** STATE - names the error condition of an unimplemented callable
- **Temporal aspect:** Instantaneous when raised; describes a persistent gap in the code

### Recommended Form

**Primary recommendation:** Take the pack's existing `NotImplemented` translation (negation + past participle) and attach the standard "error" word, in whatever order the language's other exception names use. The value and the exception must differ by exactly the "error" component - that one-word difference IS the lesson.

**Forms to AVOID:**

- ❌ A rendering unrelated to the `NotImplemented` translation - severs the value/exception pair users must learn to distinguish
- ❌ Verb or imperative forms ("DoNotImplement") - this names a state, not a command
- ❌ "Abstract method error" style paraphrases - abstract methods are one use case, not the definition

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES - and the decisive ambiguity is not inside the English word, but between two Python names.

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: `NotImplemented` - the singleton VALUE returned by binary dunder methods (`__eq__`, `__add__`, ...) to request delegation to the other operand. Returned, never raised. Not an error.
- ❌ Meaning 2: "Not implemented" as a command ("do not implement this")
- ✅ Meaning 3: **`NotImplementedError` - the EXCEPTION raised by a method/function whose body is intentionally missing (abstract method, stub, unsupported platform)**

**Example:**

The two Python names in action:

1. `def __eq__(self, other): return NotImplemented` (value - operator protocol delegation) ❌ not this term
2. "Don't implement this method" (imperative reading) ❌
3. `def save(self): raise NotImplementedError` (exception - unimplemented callable) ✅ **This is this term**

**Your translation must capture meaning #3 AND preserve the pairing: the exception's name must be the `NotImplemented` value's translation plus the pack's "error" word - nothing more, nothing less. A reader of translated code must be able to see at a glance that `raise <NotImplementedError>` and `return <NotImplemented>` involve two related but different names, exactly one of which is an error.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `NotImplementedError`, check these translations:**

- [ ] `NotImplemented` - THE critical pair: this exception must be that value's translation + "error"
- [ ] `RuntimeError` - The parent class; must share the same "error" word
- [ ] `TypeError` - What the interpreter raises when both operands return `NotImplemented`; same error family
- [ ] `raise` - This term is raised; the verb must read naturally with the noun
- [ ] `return` - The value twin is returned; the two verb pairings anchor the distinction
- [ ] `class` / `def` - The definition keywords in whose bodies this exception appears

**Consistency rule:**

Translate the pair as a unit: first fix `NotImplemented` (negation + past participle), then form `NotImplementedError` by adding the standard "error" word in the position your other exceptions use. Never let the two drift to different stems, and never let them become identical.


### Functional relationships

**This term works WITH:**

1. **`raise` + `NotImplementedError`**: The only correct verb for this name

```python
def parse(self, text):
    raise NotImplementedError("parser backend pending")
```

2. **Base classes + overrides**:

```python
class Handler:
    def handle(self, event):
        raise NotImplementedError
```

**Common pairing:**

```python
# The interface-stub pattern, and its abc-based upgrade
class Codec:
    def encode(self, data):
        raise NotImplementedError("encode() must be overridden")

    def decode(self, data):
        raise NotImplementedError("decode() must be overridden")

# Callers can probe for unfinished features
def try_decode(codec, data):
    try:
        return codec.decode(data)
    except NotImplementedError:
        return None  # feature not available in this codec

# Contrast: the VALUE in the operator protocol
class Point:
    def __init__(self, x):
        self.x = x
    def __add__(self, other):
        if not isinstance(other, Point):
            return NotImplemented        # value: delegate, don't fail
        return Point(self.x + other.x)

# Point(1) + "a"  ->  TypeError (both sides declined), NOT NotImplementedError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `NotImplementedError`

- The compound itself is mechanical once `NotImplemented` is fixed: stem + error word
- The hard constraint is relational: must differ from the value's translation by exactly the "error" component
- "Implemented" has several candidate participles per language (executed, realized, applied, carried out); the choice was already made for `NotImplemented` and must simply be reused
- Translators unaware of the value/exception split may "helpfully" merge or rename the pair

**For this term:** MEDIUM

**Rationale:** Linguistically this is one of the most constrained - and therefore easiest - exception names: the stem is inherited from `NotImplemented` and only the error suffix is added. All genuine difficulty is conceptual discipline: keeping the pair parallel and resisting paraphrases like "abstract method error." A translator who reads the Ambiguity Resolution section should land this with high confidence; one who skips it is likely to break the pair.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "callable exists but has no implementation" (not a command, not the operator sentinel)?
- [ ] Clearly indicates an ERROR (unlike the `NotImplemented` value)?
- [ ] Would a developer reading `raise <your term>` understand a stub/abstract method was called?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Negation + past participle preserved from the value translation?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Equals the `NotImplemented` translation + the pack's standard "error" word?
- [ ] Same "error" word as `RuntimeError`, `TypeError`, `ValueError`?
- [ ] NOT identical to the `NotImplemented` translation?

### 4. Usability

- [ ] Distinguishable from `NotImplemented` at a glance, yet visibly related?
- [ ] Reasonable length (the compound is inherently longer; 2-4 words acceptable)?
- [ ] Easy to type on standard keyboard?

### 5. Cultural Appropriateness

- [ ] Professional/technical register?
- [ ] No unintended blame or moral connotation in the negated participle?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: NotImplementedError
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
