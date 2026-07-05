# Python Builtin: `ExceptionGroup` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.11+
**Difficulty:** HARD

---

## Quick Summary

`ExceptionGroup` (Python 3.11, PEP 654) is an exception that wraps multiple ordinary exceptions raised together, such as several concurrent tasks failing at once. It is the `Exception`-subclass variant of `BaseExceptionGroup`: it may only contain `Exception` instances, is catchable by `except Exception`, and is what `BaseExceptionGroup(...)` automatically returns when all contained exceptions are regular `Exception` subclasses.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Raising several ordinary errors as one group
raise ExceptionGroup(
    "validation failed",
    [ValueError("age must be positive"), TypeError("name must be a string")],
)
# ExceptionGroup: validation failed (2 sub-exceptions)
#   +-- ValueError: age must be positive
#   +-- TypeError: name must be a string
```

**What this does:** Creates and raises one exception containing two independent validation errors. The traceback renders the group as a tree, showing every contained exception instead of discarding all but one. The contained exceptions are available as the `.exceptions` tuple.

### Example 2: Common Pattern

```python
# Collect-then-raise validation, unpacked with except*
def validate(record):
    errors = []
    if record.get("age", -1) < 0:
        errors.append(ValueError("age must be non-negative"))
    if not isinstance(record.get("name"), str):
        errors.append(TypeError("name must be a string"))
    if errors:
        raise ExceptionGroup("invalid record", errors)

try:
    validate({"age": -5, "name": 42})
except* ValueError as eg:
    print(f"value errors: {[str(e) for e in eg.exceptions]}")
except* TypeError as eg:
    print(f"type errors: {[str(e) for e in eg.exceptions]}")
```

**What this does:** Instead of stopping at the first problem, the validator collects every error and raises them together. The `except*` clauses each receive a group containing just their matching exceptions - both clauses run for this one raise, which plain `except` can never do.

### Example 3: Edge Case

```python
# ExceptionGroup is strict about its contents, and groups can nest
try:
    ExceptionGroup("bad", [KeyboardInterrupt()])
except TypeError as e:
    print("rejected:", e)  # ExceptionGroup may only contain Exception instances

# BaseExceptionGroup auto-selects this class when contents are ordinary
eg = BaseExceptionGroup("all ordinary", [ValueError("v")])
print(type(eg).__name__)  # ExceptionGroup

# Nested groups form a tree; subgroup() prunes it
nested = ExceptionGroup(
    "outer",
    [ValueError("v1"), ExceptionGroup("inner", [ValueError("v2"), TypeError("t")])],
)
only_values = nested.subgroup(ValueError)
print(only_values.message)  # outer  (structure preserved, TypeError pruned)
```

**What this shows:** `ExceptionGroup(...)` raises `TypeError` if any member is not an `Exception` instance - system-level signals like `KeyboardInterrupt` require `BaseExceptionGroup`. Conversely, `BaseExceptionGroup(...)` returns an `ExceptionGroup` when everything inside is ordinary. Groups nest into trees, and `.subgroup()`/`.split()` preserve that nesting while filtering.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (Container)

**Similar terms in this pattern:**

1. `BaseExceptionGroup` - The parent variant that can also hold system-level exceptions
2. `Exception` - The base class this group inherits from, and the type its members must have
3. `BaseException` - Root of the hierarchy; anchors the parallel naming

**Pattern rule:** Exception container classes are noun compounds built from already-translated parts. `ExceptionGroup` = the translation of `Exception` + the noun for "group," using the same word for "group" as `BaseExceptionGroup`.


---

## Etymology (Brief)

**English Origin:** Latin + Germanic compound

**Root meaning:** "Exception" from Latin "excipere" meaning "to take out, exclude." "Group" from Italian "gruppo" via French "groupe," meaning a cluster or knot of things - originally Germanic. Together: a cluster of exceptions.

**Why Python uses this:** PEP 654 (2021) introduced exception groups so that concurrent code - `asyncio` task groups in particular - could report several simultaneous failures without losing any. `ExceptionGroup` is the everyday variant: because it subclasses `Exception`, existing `except Exception` handlers still catch it, keeping the new machinery compatible with two decades of Python error handling.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ExceptionGroup` bundles several ordinary exceptions into one raisable object. It stores a message (`.message`) and a tuple of contained exceptions (`.exceptions`), and its traceback renders as a tree showing every failure. The canonical producers are concurrency primitives: when an `asyncio.TaskGroup` has multiple tasks fail, it raises one `ExceptionGroup` carrying all of their exceptions. Application code can use the same pattern for anything that accumulates independent failures, such as validating many fields at once.

The class sits inside a deliberate two-level design. `BaseExceptionGroup` subclasses `BaseException` and may contain any exceptions; `ExceptionGroup` subclasses both `BaseExceptionGroup` and `Exception`, and may only contain `Exception` instances - the constructor raises `TypeError` otherwise. The runtime chooses for you: calling `BaseExceptionGroup(msg, excs)` returns an `ExceptionGroup` instance whenever all members are `Exception` subclasses. This preserves the hierarchy's core promise: `except Exception` catches an `ExceptionGroup` but never a bare `BaseExceptionGroup`, so system-level signals like `KeyboardInterrupt` cannot hide inside an innocent-looking group.

Handling is selective. The `except* SomeType` syntax extracts matching members from a raised group into a new group bound to the clause variable; multiple `except*` clauses can each run once for a single raise, and unmatched members re-propagate as a smaller group. For manual work, `.split(condition)` returns `(matched, unmatched)` groups and `.subgroup(condition)` returns just the matching part - both preserve the nested tree structure and copy the message, `__cause__`, and other metadata onto the derived groups.

**Key behaviors:**

1. **Contains only `Exception` instances:** The constructor validates members and raises `TypeError` for anything not an `Exception`. This is what keeps `except Exception` a safe catch-all - groups it catches cannot smuggle `SystemExit` or `KeyboardInterrupt`.

2. **Auto-selected by the base constructor:** `BaseExceptionGroup(msg, excs)` returns an `ExceptionGroup` when every member is an `Exception`. Code rarely needs to pick between the two names at construction time; the distinction matters most when catching.

3. **Unpacked by `except*`, dissected by `.split()`/`.subgroup()`:** `except*` matches the contained exception types (naming an exception-group type in `except*` is not allowed), several clauses can run for one raise, and `except` and `except*` cannot be mixed in the same `try` statement.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun ("exception" + container "group")
- **Action vs State:** STATE - names a category of exception object, not an action
- **Temporal aspect:** Instantaneous as an event (raised once), but structural as a container

### Recommended Form

**Primary recommendation:** Build compositionally: the pack's existing `Exception` translation plus the ordinary noun for "group/collection." Use the SAME "group" word as `BaseExceptionGroup`, so the two class names differ only by the "base" component - exactly as they do in English.

**Forms to AVOID:**

- ❌ A different "exception" word than the `Exception` translation - the hierarchy must stay visible
- ❌ "List," "set," "array" vocabulary for "group" - collides with data-structure terms that have their own Python meanings
- ❌ Words implying the exceptions are related or identical ("series," "chain") - members are independent and unrelated; "chain" also collides with exception chaining (`raise ... from ...`)

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Group" as a social group of people (a team, a band)
- ❌ Meaning 2: "Group" as a mathematical group (algebraic structure)
- ❌ Meaning 3: "Group" as a verb ("to group items together")
- ✅ Meaning 4: **A CONTAINER EXCEPTION holding several unrelated `Exception` instances raised as one**

**Example:**

English "group" can mean:

1. "A group of tourists" (people) ❌
2. "The group axioms" (mathematics) ❌
3. "Group the files by date" (verb) ❌
4. `ExceptionGroup("msg", [e1, e2])` (a bundle of exceptions) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a noun naming a container of exception objects. It must remain a noun compound (never a verb) and must not suggest the members are ordered, chained, or causally related.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ExceptionGroup`, check these translations:**

- [ ] `Exception` - Must appear as the root of this compound; this class IS an `Exception`
- [ ] `BaseExceptionGroup` - Must share the identical "group" word; the pair must differ only by the "base" component
- [ ] `BaseException` - Anchors the "base" component used in the sibling name
- [ ] `except` - The `except*` syntax that unpacks groups; handler vocabulary must stay compatible
- [ ] `set` / `list` - Verify your "group" word does NOT collide with these data-structure translations

**Consistency rule:**

Translate compositionally and in lockstep with `BaseExceptionGroup`: `ExceptionGroup` = translation(`Exception`) + translation("group"); `BaseExceptionGroup` = translation(`BaseException`) + the SAME translation("group"). Whoever translates one group class must translate (or verify) the other in the same pass.


### Functional relationships

**This term works WITH:**

1. **`except*` + `ExceptionGroup`**: Selective handling of members

```python
try:
    validate_all(records)
except* ValueError as eg:
    report(eg.exceptions)
```

2. **`raise` + `ExceptionGroup`**: Raising accumulated failures

```python
if errors:
    raise ExceptionGroup("batch failed", errors)
```

**Common pairing:**

```python
# The collect-and-raise pattern
def process_batch(items):
    errors = []
    results = []
    for item in items:
        try:
            results.append(process(item))
        except Exception as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup(f"{len(errors)} items failed", errors)
    return results

# Callers unpack by type; unmatched members keep propagating
try:
    process_batch(data)
except* ValueError as eg:
    log_bad_values(eg.exceptions)
except* OSError as eg:
    retry_io(eg.exceptions)

# Manual dissection without except*
# match, rest = eg.split(ValueError)
# values_only = eg.subgroup(ValueError)
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `ExceptionGroup`

- Must be built from the existing `Exception` translation plus a "group" word, in the language's natural compound order
- Locked in a strict parallel with `BaseExceptionGroup` - the pair must be translated together
- "Group" candidates often collide with `set`/`list`/collection vocabulary that already has Python meanings
- Python 3.11 concept with little localized documentation to anchor community expectations

**For this term:** HARD

**Rationale:** Each component is common vocabulary, but the translation is constrained from three directions at once: compositional transparency with `Exception`, exact parallelism with `BaseExceptionGroup`, and non-collision with data-structure terms. Because exception groups are new, translators cannot lean on established local usage and may improvise structurally inconsistent names. Review both group classes side by side before accepting either.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures a CONTAINER of multiple independent exceptions (not one error, not a chain)?
- [ ] Consistent with this class being catchable by `except Exception`?
- [ ] Avoids implying order, causality, or relatedness among members?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun, not verb)?
- [ ] Compound word order natural in target language?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the existing `Exception` translation as its root?
- [ ] Uses the identical "group" word as `BaseExceptionGroup`?
- [ ] Does NOT collide with the `set`/`list` data-structure translations?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Instantly distinguishable from `BaseExceptionGroup`?

### 5. Cultural Appropriateness

- [ ] "Group" word free of unwanted social/political connotations?
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
term: ExceptionGroup
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
