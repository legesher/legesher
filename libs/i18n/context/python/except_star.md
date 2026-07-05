# Python Keyword: `except*` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** exception_handling (exception group filtering)
**Python Version:** 3.11+ (PEP 654)
**Difficulty:** HARD

---

## Quick Summary

The `except*` syntax (Python 3.11+, PEP 654) handles exceptions raised inside an `ExceptionGroup`. It is NOT a new keyword - it is the existing `except` keyword combined with the `*` symbol. Where a plain `except` picks one handler (first match wins), `except*` clauses each extract the exceptions they match from the group, so MULTIPLE `except*` clauses can all run for a single raised group.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Handling an ExceptionGroup by type (requires Python 3.11+)
try:
    raise ExceptionGroup(
        "setup failed",
        [ValueError("bad value"), TypeError("bad type")],
    )
except* ValueError as eg:
    print(f"Value errors: {eg.exceptions}")
except* TypeError as eg:
    print(f"Type errors: {eg.exceptions}")

# Output:
# Value errors: (ValueError('bad value'),)
# Type errors: (TypeError('bad type'),)
```

**What this does:** One `raise` carries TWO exceptions bundled in an `ExceptionGroup`. Each `except*` clause pulls out the exceptions matching its type - and BOTH clauses run, one after the other. This is the fundamental difference from plain `except`, where exactly one handler executes. Note that `eg` is bound to an `ExceptionGroup` containing the matched exceptions (a tuple in `eg.exceptions`), not to a single exception.

### Example 2: Common Pattern

```python
# Collect errors from many operations, then handle them by type (Python 3.11+)
def validate_all(records):
    errors = []
    for record in records:
        try:
            validate(record)          # may raise ValueError or KeyError
        except (ValueError, KeyError) as exc:
            errors.append(exc)
    if errors:
        raise ExceptionGroup("validation failed", errors)

try:
    validate_all(records)
except* ValueError as eg:
    for err in eg.exceptions:
        print(f"Bad value: {err}")
except* KeyError as eg:
    for err in eg.exceptions:
        print(f"Missing key: {err}")
```

**What this does:** Instead of stopping at the first failure, `validate_all` gathers every error and raises them together as one `ExceptionGroup`. The caller then sorts the pile by type: all `ValueError`s go to the first clause, all `KeyError`s to the second, and both clauses run if both types are present. This "gather many failures, handle by category" pattern is why `except*` exists - concurrent code (`asyncio.TaskGroup`, also new in 3.11) raises exception groups the same way.

### Example 3: Edge Case

```python
# Partial matching: unmatched exceptions propagate onward (Python 3.11+)
try:
    try:
        raise ExceptionGroup(
            "mixed", [ValueError("v"), TypeError("t"), KeyError("k")]
        )
    except* ValueError as eg:
        print(f"Handled: {eg.exceptions}")
except ExceptionGroup as remainder:
    print(f"Still unhandled: {remainder.exceptions}")

# Output:
# Handled: (ValueError('v'),)
# Still unhandled: (TypeError('t'), KeyError('k'))

# Syntax restrictions (all are errors):
#   except* :                         SyntaxError - a type is mandatory
#   mixing except and except*         SyntaxError - one try may use only one style
#   break/continue/return in except*  SyntaxError - not allowed inside the clause
#   except* ExceptionGroup            TypeError at runtime - filter by leaf types instead
```

**What this shows:** `except*` consumes only what it matches. The `ValueError` is handled; the `TypeError` and `KeyError` are re-raised automatically as a smaller `ExceptionGroup` that the outer `try` catches. Also note the hard restrictions: `except*` always requires an exception type, cannot be mixed with plain `except` in the same `try` statement, and cannot contain `break`, `continue`, or `return`.

---

## Pattern Classification

**This term is:** EXCEPTION HANDLING KEYWORD (Group Filtering) - the `except` keyword plus the `*` syntax marker

**Similar terms in this pattern:**

1. `except` - The SAME keyword; `except*` is `except` with a star appended, not a new word
2. `try` - Begins the protected block that `except*` clauses attach to
3. `raise` - Raises the `ExceptionGroup` instances that `except*` filters

**Pattern rule:** The word part of `except*` MUST be translated identically to `except` - same word, same form, byte-for-byte. The `*` is Python syntax (like the `*` in `*args`), is appended unchanged, and is NEVER translated, transliterated, or replaced with a native symbol.


---

## Etymology (Brief)

**English Origin:** Latin (keyword) + Greek (symbol name)

**Root meaning:** The word is `except` (Latin "exceptus," to take out/exclude - see `except.md`). The `*` is an asterisk, from Greek "asteriskos" (little star). In computing, `*` conventionally means "many/any": wildcard globs (`*.txt`), and in Python itself `*args` (many positional arguments) and iterable unpacking (`*items`).

**Why Python uses this:** PEP 654 (Python 3.11) needed syntax for handling `ExceptionGroup` without inventing a new keyword, which would have broken existing code using that word as a variable name. Reusing `except` signals "this is still exception handling," and the `*` evokes "match MANY exceptions" - the same plurality the star already carries in `*args`. Read `except* ValueError` as "except, possibly several, ValueErrors."

---

## Concept Explanation (Intermediate Level)

**What it does:**

Python 3.11 introduced `ExceptionGroup`: a single exception object that carries several unrelated exceptions at once. Groups arise naturally from concurrent code - if three parallel tasks fail, there is no single "the" exception - and from batch operations that collect every failure before reporting. Plain `except` handles one exception with one handler; it has no way to say "give me only the ValueErrors out of this bundle." That is the job of `except*`.

When an `ExceptionGroup` is raised in a `try` block with `except*` clauses, Python visits each clause in order. Each clause extracts (splits off) the subgroup of exceptions matching its type and runs its body once with that subgroup bound via `as`. Because each clause takes only its own matches, several clauses can all run for one raised group - a fundamental departure from plain `except`'s first-match-wins rule. Each individual exception is consumed by at most one clause: the first clause whose type it matches.

Whatever no clause matches is not lost: Python automatically re-raises the leftovers as a smaller `ExceptionGroup` after all clauses have run. Symmetrically, if the `try` block raises a plain, non-grouped exception (say a bare `ValueError`), `except* ValueError` still catches it - Python wraps it into a group first, so the `as` target is always an `ExceptionGroup`.

**Key behaviors:**

1. **All matching clauses run:** Plain `except` picks exactly one handler. With `except*`, every clause that matches part of the group executes (each at most once, in source order). Handling a group of `[ValueError, TypeError]` with `except* ValueError` and `except* TypeError` clauses runs BOTH bodies.

2. **Binds a group, not a single exception:** `except* ValueError as eg` binds `eg` to an `ExceptionGroup` whose `.exceptions` tuple holds the matched `ValueError`(s). Handler bodies typically loop over `eg.exceptions`. A naked (non-group) exception raised in the `try` block is wrapped into a group before binding.

3. **Unmatched remainder propagates:** Exceptions no clause matched are re-raised automatically as a trimmed `ExceptionGroup`. Restrictions enforce clarity: a `try` cannot mix `except` and `except*`; `except*` requires a type (no bare form); `break`/`continue`/`return` are forbidden inside `except*` bodies; and `except* ExceptionGroup` itself raises `TypeError` (filter by the leaf exception types instead).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Identical to `except` - preposition/exceptive particle - followed by the `*` syntax marker
- **Action vs State:** CONDITIONAL HANDLING - catches matching cases out of a group
- **Temporal aspect:** Reactive - responds to raised exception groups; clauses may each fire once

### Recommended Form

**Primary recommendation:** There is no independent translation decision here. Take the language's finalized `except` translation and append the ASCII asterisk. The translator's real task is the DOCUMENTATION around the term: explaining "match many out of a group" in natural prose, while the token itself is mechanically derived.

**Forms to AVOID:**

- ❌ Translating or replacing the `*` (e.g., a word for "star," "many," or a native typographic star symbol) - the `*` is parser syntax and must remain the ASCII asterisk
- ❌ Choosing a different word than the `except` translation (a synonym instead of the exact keyword rendering) - breaks the visible identity between the two forms
- ❌ Inflecting the keyword for plurality (e.g., a plural or modified form of the `except` word) - the grouping meaning lives in the `*`, not in the word

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (the ambiguity is in the `*`, not the word)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Multiplication operator (`3 * 4`)
- ❌ Meaning 2: Footnote or emphasis marker (prose asterisk)
- ❌ Meaning 3: Pointer/dereference (C/C++ `*ptr`)
- ✅ Meaning 4: **"MATCH MANY" SYNTAX MARKER** - as in `*args` and wildcard `*`, here meaning "extract the matching exceptions out of a group"

**Example:**

The `*` in Python can mean:

1. `3 * 4` (multiplication) ❌
2. `def f(*args)` (collect many arguments) ✅ Closest relative
3. `except* ValueError` (match many exceptions from a group) ✅ **This is the meaning here**

**Your translation should treat the `*` as untranslatable syntax carrying meaning #4.**

The load-bearing rule, stated plainly: **the target rendering of `except*` is the target rendering of `except`, plus the ASCII asterisk. The word part must be identical to the pack's `except` translation; the `*` is never translated, never replaced with a native symbol, and never dropped.** There is no scenario in which `except*` gets an independent word.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `except*`, check these translations:**

- [ ] `except` - MANDATORY IDENTITY: the word part of `except*` must be byte-for-byte the same as the `except` translation (see `except.md`)
- [ ] `try` - `except*` clauses attach to `try` blocks; the pair must read naturally together
- [ ] `raise` - Raises the `ExceptionGroup` instances that `except*` filters
- [ ] `as` - Binds the matched subgroup (`except* ValueError as eg`)

**Consistency rule:**

Consistency with `except.md` is not a preference - it is a hard requirement. Derive the `except*` rendering mechanically: take the finalized `except` translation, append `*`, done. If the `except` translation is ever revised, `except*` must be regenerated in the same change. `ExceptionGroup` is a builtin class name and follows the pack's builtin-translation policy, not this brief.


### Functional relationships

**This term works WITH:**

1. **`try` + `except*`:** Group-aware error handling (all clauses may run)

```python
try:
    run_batch()
except* ValueError as eg:
    handle_values(eg.exceptions)
except* OSError as eg:
    handle_io(eg.exceptions)
```

2. **`raise ExceptionGroup` + `except*`:** Producing and consuming grouped failures

```python
raise ExceptionGroup("batch failed", [ValueError("a"), OSError("b")])
```

**Common pairing:**

```python
# asyncio.TaskGroup (Python 3.11+) raises ExceptionGroups naturally
import asyncio

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch("a"))
            tg.create_task(fetch("b"))
    except* TimeoutError as eg:
        print(f"{len(eg.exceptions)} task(s) timed out")
    except* ConnectionError as eg:
        print(f"{len(eg.exceptions)} task(s) failed to connect")

# Nested groups: except* matches leaf exceptions at any depth
try:
    raise ExceptionGroup(
        "outer",
        [ValueError("v"), ExceptionGroup("inner", [TypeError("t")])],
    )
except* TypeError as eg:
    print("caught nested TypeError")   # runs: matching descends into subgroups

# A naked exception is wrapped into a group for except*
try:
    raise ValueError("plain")           # not raised inside a group
except* ValueError as eg:
    print(eg.exceptions)                # (ValueError('plain'),)
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `except*`

- The difficulty is CONCEPT NOVELTY, not vocabulary: `ExceptionGroup` semantics (multiple clauses all running, subgroup binding, remainder re-raise) are new in 3.11 and have essentially no established terminology in any language's CS education yet
- The token itself is mechanically derived (`except` translation + `*`), so the word choice is deterministic once `except` is fixed
- The risk is translators "helpfully" translating the star, choosing a fresh word, or inflecting the keyword - all of which break the system
- Explanatory prose around the term (docs, error messages, tutorials) needs careful native phrasing for "match many out of a group"

**For this term:** HARD

**Rationale:** Vocabulary confidence is HIGH once the pack's `except` translation exists, because the rendering is derived, not chosen. Conceptual confidence is MEDIUM: the brief's documentation prose must explain semantics that most target-language CS communities have never named. Human review should focus on the explanation text and on how the word+star token renders across scripts, not on the word itself.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Word part identical to the pack's `except` translation?
- [ ] `*` preserved as the ASCII asterisk, untranslated?
- [ ] Documentation prose conveys "multiple clauses can ALL run"?
- [ ] Documentation prose conveys "binds a group, not a single exception"?

### 2. Linguistic Correctness

- [ ] Same part of speech and form as the `except` translation?
- [ ] No added plural/inflection morphology on the keyword?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Byte-for-byte match with `except.md`'s chosen rendering (word part)?
- [ ] Reads naturally after the `try` translation?
- [ ] Works with the `as` translation for subgroup binding?

### 4. Usability

- [ ] Token is the `except` rendering + one character - no longer?
- [ ] Easy to type (star is on standard keyboards)?
- [ ] Visually recognizable as "except plus star" at a glance?

### 5. Cultural Appropriateness

- [ ] No offensive meanings introduced by the combination?
- [ ] `*` not confused with a culturally loaded symbol in target locale?

### 6. Technical Compatibility

- [ ] ASCII `*` used (never a full-width or decorative Unicode star lookalike)?
- [ ] RTL rendering verified: source order is keyword-then-star?
- [ ] Renders correctly in IDEs and syntax highlighters next to the keyword?

---

## Translation Output Format

**Your translation:**

```yaml
term: except*
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
