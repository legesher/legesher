# Python Builtin: `BaseExceptionGroup` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.11+
**Difficulty:** HARD

---

## Quick Summary

`BaseExceptionGroup` (Python 3.11, PEP 654) is an exception that wraps multiple unrelated exceptions raised together - for example, several concurrent tasks failing at once. It subclasses `BaseException`, may contain any `BaseException` instances (including `KeyboardInterrupt`), and is handled selectively with the `except*` syntax or split apart with `.split()` and `.subgroup()`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Grouping unrelated exceptions into one raisable object
eg = BaseExceptionGroup(
    "several things failed",
    [KeyboardInterrupt(), ValueError("bad input")],
)
print(type(eg).__name__)  # BaseExceptionGroup
print(eg.exceptions)      # (KeyboardInterrupt(), ValueError('bad input'))
raise eg
```

**What this does:** Creates one exception object holding two unrelated exceptions. Because one of them (`KeyboardInterrupt`) is not an `Exception` subclass, the group must be a `BaseExceptionGroup`. The contained exceptions are available as the read-only `.exceptions` tuple, and raising the group raises all of them as a unit.

### Example 2: Common Pattern

```python
# Handling parts of a group selectively with except*
try:
    raise BaseExceptionGroup(
        "shutdown problems",
        [KeyboardInterrupt(), ValueError("bad value"), TypeError("bad type")],
    )
except* ValueError as eg:
    print(f"value problems: {eg.exceptions}")
except* KeyboardInterrupt as eg:
    print(f"interrupts: {eg.exceptions}")
except* TypeError as eg:
    print(f"type problems: {eg.exceptions}")
```

**What this does:** `except*` (new in 3.11) matches exceptions INSIDE the group. Each `except*` clause receives a new group containing only the matching exceptions, and - unlike plain `except` - multiple `except*` clauses can all run for one raised group. Anything left unmatched propagates onward as a smaller group.

### Example 3: Edge Case

```python
# The constructor auto-selects the subclass, and .split() partitions a group
only_regular = BaseExceptionGroup("all ordinary", [ValueError("v"), TypeError("t")])
print(type(only_regular).__name__)  # ExceptionGroup (auto-downgraded!)

mixed = BaseExceptionGroup("mixed", [KeyboardInterrupt(), ValueError("v")])
print(type(mixed).__name__)         # BaseExceptionGroup

match, rest = mixed.split(ValueError)
print(match.exceptions)  # (ValueError('v'),)
print(rest.exceptions)   # (KeyboardInterrupt(),)
```

**What this shows:** Calling `BaseExceptionGroup(...)` when every contained exception is an `Exception` subclass returns an `ExceptionGroup` instance instead - the base name is only kept when a non-`Exception` (like `KeyboardInterrupt`) is inside. `.split(condition)` divides a group into the matching part and the non-matching part, preserving the group structure.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (Container/Base Class)

**Similar terms in this pattern:**

1. `BaseException` - The root of the exception hierarchy; this group class inherits from it
2. `ExceptionGroup` - The `Exception`-subclass variant of this class for ordinary errors
3. `Exception` - Base for regular errors; determines which group variant is used

**Pattern rule:** Exception container classes are noun compounds built from already-translated parts. `BaseExceptionGroup` = the translation of `BaseException` + the noun for "group," assembled with the same word order the language uses for other compound class names.


---

## Etymology (Brief)

**English Origin:** Greek + Latin + Germanic compound

**Root meaning:** "Base" from Greek "basis" (foundation), "exception" from Latin "excipere" (to take out), "group" from Italian "gruppo" via French "groupe" (cluster, knot), originally Germanic. A "group of base exceptions": several exceptions gathered into one.

**Why Python uses this:** PEP 654 (2021) needed a way for concurrent code - notably `asyncio` task groups - to report several simultaneous, unrelated failures without discarding any of them. The name stacks Python's existing conventions: it is a "Group" of exceptions, and the "BaseException" prefix signals it sits on the `BaseException` side of the hierarchy, able to carry non-`Exception` signals like `KeyboardInterrupt`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

Before Python 3.11, an exception handler could deal with exactly one exception at a time. Concurrent code broke that model: if three parallel tasks fail with three different, unrelated exceptions, which one should propagate? PEP 654's answer is the exception group - a single exception object that contains a tuple of other exceptions (accessible via `.exceptions`) plus a message describing the group. `BaseExceptionGroup` is the root of this mechanism and inherits from `BaseException`.

The class has one important construction rule: `BaseExceptionGroup(message, exceptions)` inspects its contents. If every contained exception is an instance of `Exception`, the constructor returns an `ExceptionGroup` instead (the friendlier subclass that plain `except Exception` can catch). Only when at least one member is a bare `BaseException` descendant - `KeyboardInterrupt`, `SystemExit`, and similar system-level signals - does the object remain a `BaseExceptionGroup`. This mirrors the existing split between `BaseException` and `Exception`.

Handling uses the `except*` syntax: each `except* SomeType` clause extracts the matching members from the raised group and receives them wrapped in a new group; non-matching members continue propagating. Groups can also be dissected manually: `.split(condition)` returns a `(matched, unmatched)` pair of groups, and `.subgroup(condition)` returns only the matching part. Both preserve nesting structure, because groups can contain other groups, forming a tree.

**Key behaviors:**

1. **Wraps a tuple of unrelated exceptions:** `.exceptions` holds the contained exceptions; `.message` holds the description. Groups may nest, so a group can contain other groups, forming a tree of failures.

2. **Constructor auto-selects the subclass:** `BaseExceptionGroup(msg, excs)` returns an `ExceptionGroup` when all members are `Exception` instances, and a true `BaseExceptionGroup` only when a system-level exception is present. Subclassing note: `ExceptionGroup(msg, excs)` raises `TypeError` if any member is not an `Exception`.

3. **Handled with `except*`, split with `.split()`/`.subgroup()`:** `except*` clauses match members inside the group (several clauses can run for one raise), and it is a syntax error to mix `except` and `except*` in one `try`. `except*` also may not name an exception-group type directly - it matches the contained (leaf) exception types.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (hierarchy marker "base" + "exception" + container "group")
- **Action vs State:** STATE - names a category of exception object, not an action
- **Temporal aspect:** Instantaneous as an event (raised once), but structural as a container

### Recommended Form

**Primary recommendation:** Build the translation mechanically from parts the pack already has: take the existing `BaseException` translation and attach the language's ordinary noun for "group/collection." Do not re-translate "base" or "exception" from scratch - the reader must be able to see `BaseException` inside `BaseExceptionGroup`.

**Forms to AVOID:**

- ❌ A fresh word for "exception" different from the `Exception`/`BaseException` translations - destroys the visible hierarchy
- ❌ Words meaning "list," "set," or "array" for "group" - these carry data-structure meanings that conflict with `list`/`set` translations
- ❌ Dropping the "base" component - then it collides with `ExceptionGroup`, which is a different class

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Group" as a social group of people
- ❌ Meaning 2: "Group" as a mathematical group (algebraic structure)
- ❌ Meaning 3: "Base" as a military installation or chemical base
- ✅ Meaning 4: **A CONTAINER EXCEPTION holding several exceptions, rooted at the BASE of the exception hierarchy**

**Example:**

English "group" can mean:

1. "A group of friends" (social gathering) ❌
2. "The symmetry group of a cube" (mathematics) ❌
3. `BaseExceptionGroup("msg", [exc1, exc2])` (a bundle of exceptions raised as one) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a collection/bundle of exception objects. "Base" must carry the same "foundational parent class" sense used in `BaseException`, NOT military, chemical, or geometric senses.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `BaseExceptionGroup`, check these translations:**

- [ ] `BaseException` - Must appear verbatim (or in its grammatically adjusted form) inside this translation
- [ ] `ExceptionGroup` - Must be this translation minus the "base" component, and share the same "group" word
- [ ] `Exception` - The shared "exception" root across the whole hierarchy
- [ ] `except` - The `except*` syntax handles groups; the handler keyword vocabulary should remain compatible
- [ ] `KeyboardInterrupt` / `SystemExit` - The system-level exceptions whose presence keeps a group "base"

**Consistency rule:**

Translate compositionally: `BaseExceptionGroup` = translation(`BaseException`) + translation("group"), and `ExceptionGroup` = translation(`Exception`) + the SAME translation of "group." The two group classes must differ by exactly the same component that distinguishes `BaseException` from `Exception` in your language.


### Functional relationships

**This term works WITH:**

1. **`except*` + `BaseExceptionGroup`**: Selective handling of group members

```python
try:
    risky_concurrent_work()
except* OSError as eg:
    handle_io_failures(eg.exceptions)
```

2. **`.split()` / `.subgroup()` + `BaseExceptionGroup`**: Manual partitioning

```python
match, rest = eg.split(TimeoutError)
timeouts_only = eg.subgroup(TimeoutError)
```

**Common pairing:**

```python
# Collecting failures from several independent operations
errors = []
for task in tasks:
    try:
        task.run()
    except BaseException as e:
        errors.append(e)

if errors:
    raise BaseExceptionGroup("some tasks failed", errors)

# Downstream, callers unpack it selectively
try:
    run_all(tasks)
except* ValueError as eg:
    print(f"{len(eg.exceptions)} value problems")
except* KeyboardInterrupt:
    print("user interrupted at least one task")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `BaseExceptionGroup`

- Three-component compound; word order for "base + exception + group" varies sharply across languages
- Must embed the existing `BaseException` translation verbatim, constraining the solution space
- Must stay perfectly parallel with `ExceptionGroup` (differing only in the "base" component)
- The concept itself (Python 3.11 exception groups) is new; target-language CS communities may have no established term yet

**For this term:** HARD

**Rationale:** The individual words are easy, but the translation is over-constrained: it must contain the `BaseException` translation, share its "group" word with `ExceptionGroup`, avoid data-structure vocabulary, and still parse naturally as one class name. Because PEP 654 is recent, there is little existing localized documentation to lean on, so a plausible-sounding but structurally inconsistent rendering is the main risk. Human review of the compound's word order is recommended.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures a CONTAINER of multiple exceptions (not a single error)?
- [ ] "Base" carries the parent-class sense from `BaseException`?
- [ ] Would a developer understand this can hold `KeyboardInterrupt`-level signals?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Compound word order natural in target language?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the existing `BaseException` translation?
- [ ] Shares its "group" word with the `ExceptionGroup` translation?
- [ ] Differs from `ExceptionGroup` by exactly the "base" component?

### 4. Usability

- [ ] As short as the three-part concept allows?
- [ ] Easy to type on standard keyboard?
- [ ] Visually distinguishable from `ExceptionGroup` at a glance?

### 5. Cultural Appropriateness

- [ ] "Group" word has no unwanted social/political connotations?
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
term: BaseExceptionGroup
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
