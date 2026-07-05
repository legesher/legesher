# Python Builtin: `IOError` - Translation Brief (Tier 1)

**Category:** exception
**Subcategory:** os_io
**Type:** exception class (legacy alias of `OSError`)
**Python Version:** 3.x+ (alias of `OSError` since 3.3, PEP 3151)
**Difficulty:** EASY

---

## Quick Summary

`IOError` is a **legacy alias of `OSError`** — since Python 3.3 (PEP 3151) the two names are bound to the exact same class (`IOError is OSError` is `True`). It is kept only for backward compatibility with pre-3.3 code; new code should write `OSError`. There is no separate "I/O error" class to translate: this entry inherits its meaning, and its translation, entirely from `OSError`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# IOError IS OSError — the same class under an old name
print(IOError is OSError)  # True
print(IOError)             # <class 'OSError'>
```

**What this does:** The identity check proves `IOError` is not a subclass or a similar class — it is literally the same object as `OSError`. Printing the alias even displays `OSError`, because that is the class's real name.

### Example 2: Common Pattern

```python
# Legacy code catching IOError still catches modern OS errors
try:
    with open("missing.txt") as f:
        data = f.read()
except IOError as e:          # written pre-3.3, still works
    print(e.errno, e.strerror)  # 2 'No such file or directory'
```

**What this does:** Old code written for Python 2 (where `IOError` was a distinct class) keeps working unchanged: because `IOError` now names `OSError`, this handler catches `FileNotFoundError`, `PermissionError`, and every other member of the OS exception family. New code should spell the handler `except OSError:` instead.

### Example 3: Edge Case

```python
# Raising IOError constructs an OSError (or its mapped subclass)
import errno

e = IOError(errno.ENOENT, "No such file or directory")
print(type(e))  # <class 'FileNotFoundError'>

try:
    raise IOError("device not ready")
except OSError as caught:      # OSError handler catches "IOError"
    print(type(caught).__name__)  # OSError
```

**What this shows:** Everything raised through the `IOError` name is an `OSError` instance (or a mapped subclass, via `OSError`'s errno constructor magic), and `except OSError` catches it. The alias has no behavior of its own — no separate hierarchy, no separate attributes.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS ALIAS (legacy name for `OSError`)

**Similar terms in this pattern:**

1. `OSError` - The real class this name points to; the canonical modern spelling
2. `EnvironmentError` - The other legacy alias of `OSError`, with identical treatment
3. `WindowsError` - Windows-only legacy alias of `OSError` (not present on other platforms)

**Pattern rule:** Aliases do not get independent translations. The translation of `IOError` must be IDENTICAL to the translation of `OSError` in every language — or, if the pack policy exposes aliases as distinct entries, explicitly marked as the legacy spelling of that same translation.


---

## Etymology (Brief)

**English Origin:** Initialism + Latin-derived noun

**Root meaning:** "I/O" abbreviates "input/output" — data flowing into and out of a program. "Error" derives from Latin "errare" (to wander, to go astray).

**Why Python uses this:** In Python 2, `IOError` was a distinct exception for failed input/output operations (mostly file reads/writes), while `OSError` covered other system calls. The split was arbitrary in practice — both wrapped the same OS error codes — so PEP 3151 (Python 3.3) merged them, keeping `IOError` as an alias so existing code would not break.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`IOError` does nothing of its own: it is a second name bound to the `OSError` class. Any `raise IOError(...)` creates an `OSError` instance, any `except IOError:` catches exactly what `except OSError:` catches, and `IOError.__name__` is the string `"OSError"`. The name survives purely so that the large body of pre-3.3 code (and Python 2 code ported mechanically) continues to run.

Historically the distinction mattered: Python 2 raised `IOError` from file operations (`open`, `read`, `write`) and `OSError` from `os`-module calls, with `EnvironmentError` as their shared base. PEP 3151 found this three-way split unhelpful — programmers could never remember which operation raised which — and collapsed all of them into `OSError`, adding the precise subclasses (`FileNotFoundError`, `PermissionError`, ...) that modern code catches instead.

For translation purposes the only fact that matters: **this is the same class as `OSError`.** Inventing a distinct "input/output error" translation would fabricate a semantic difference that no longer exists in the language, and would mislead learners into thinking two exception types exist.

**Key behaviors:**

1. **Identity, not inheritance:** `IOError is OSError` is `True`. It is not a subclass; there is exactly one class with two (three, on Windows) names.

2. **Kept for backward compatibility only:** The Python documentation lists `IOError` under "deprecated aliases"; new code should write `OSError`. Linters and reviewers flag `IOError` in modern codebases.

3. **Fully interchangeable in raise/except:** Raising through either name and catching through either name behave identically, including the errno-to-subclass constructor mapping.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (alias of the `OSError` compound noun)
- **Action vs State:** STATE - names the same error condition `OSError` names
- **Temporal aspect:** Instantaneous - identical to `OSError`

### Recommended Form

**Primary recommendation:** Reuse the finalized `OSError` translation verbatim. Do not translate "I/O" or "input/output" at all — the English name is a historical leftover, not a description of a distinct concept. If the pack's policy is to expose aliases as separate surface entries, the entry must be visibly marked as the legacy form (e.g. in metadata: `alias_of: OSError, status: legacy`), still carrying the same translated string.

**Forms to AVOID:**

- ❌ A distinct "input/output error" translation ("ErrorDeEntradaSalida") - fabricates a class distinction that stopped existing in Python 3.3
- ❌ Verb forms - exception classes are noun compounds
- ❌ Translating the alias but not marking it legacy - learners will assume two different exceptions exist

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO — not in Python 3. The only trap is historical, not semantic:

- ❌ Meaning 1: A distinct exception class for input/output failures (TRUE ONLY IN PYTHON 2)
- ✅ Meaning 2: **A legacy alias of `OSError`** — the same class, kept for backward compatibility

**The binding rule for this entry:** the translation must be **IDENTICAL to the pack's `OSError` translation**. If the pack policy is to expose aliases as separate entries, the entry must be clearly marked as the legacy spelling (alias metadata), never given invented distinct semantics. Do not translate "input/output."

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `IOError`, check these translations:**

- [ ] `OSError` - THE constraint: this entry's translation must equal it exactly
- [ ] `EnvironmentError` - The other alias; all three surface forms must resolve to the same translated name
- [ ] `FileNotFoundError` / `PermissionError` - Subclasses learners meet through `except IOError:` in old code

**Consistency rule:**

Translate `OSError` first; copy the result here. Any later revision to the `OSError` translation must be propagated to this entry and to `EnvironmentError` in the same change.


### Functional relationships

**This term works WITH:**

1. **`except IOError:` in legacy code**: Catches the full modern `OSError` family

2. **`OSError` in new code**: The name that should replace it

**Common pairing:**

```python
# Legacy and modern spellings are interchangeable
try:
    open("data.bin")
except IOError:        # legacy spelling
    pass

try:
    open("data.bin")
except OSError:        # modern spelling — same class, preferred
    pass

assert IOError is OSError is EnvironmentError
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

**For this term:** EASY

**Rationale:** There is no translation decision to make: the answer is defined as "whatever `OSError` received." The only failure mode is not knowing the alias fact — which this brief states explicitly. Difficulty is EASY conditional on `OSError` being finalized first.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Translation is character-for-character IDENTICAL to the pack's `OSError` translation?
- [ ] No "input/output" vocabulary introduced?

### 2. Linguistic Correctness

- [ ] Inherits whatever correctness review `OSError` passed?

### 3. Consistency

- [ ] `IOError` = `EnvironmentError` = `OSError` in the translated surface?
- [ ] Entry metadata marks this as a legacy alias of `OSError`?

### 4. Usability

- [ ] Same compact form as `OSError` (1-3 words)?

### 5. Cultural Appropriateness

- [ ] Inherited from the `OSError` review — nothing new introduced?

### 6. Technical Compatibility

- [ ] Single script, renders in IDEs, RTL-safe — as verified for `OSError`?

---

## Translation Output Format

**Your translation:**

```yaml
term: IOError
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
