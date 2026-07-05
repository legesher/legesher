# Python Builtin: `DeprecationWarning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category)
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`DeprecationWarning` is the warning category for features that are deprecated: they still work today, but they are officially discouraged and scheduled for removal, so *developers* should migrate away from them. It subclasses `Warning`, is emitted via `warnings.warn()`, and since Python 3.7 (PEP 565) is shown by default only when triggered by code running in `__main__`; deprecations triggered inside imported libraries are hidden by default.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Marking an old function as deprecated
import warnings

def old_api():
    warnings.warn(
        "old_api() is deprecated; use new_api() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_api()

def new_api():
    return "result"

old_api()   # warning shown (this call is in __main__), then returns "result"
```

**What this does:** The deprecated function still works - it delegates to its replacement and returns normally. The warning is advice to the developer: "this will be removed; migrate." `stacklevel=2` points the message at the caller's line, showing developers *their* code that needs updating.

### Example 2: Common Pattern

```python
# Default visibility depends on WHERE the deprecated call happens (PEP 565)
import warnings

# Calls made directly in __main__ (scripts, REPL): shown by default.
# The same deprecated call inside an imported library: hidden by default.

# Test runners re-enable them so library authors still see deprecations:
warnings.simplefilter("default", DeprecationWarning)   # show all, once per location

# Or from the command line:
#   python -W default::DeprecationWarning script.py
#   python -W error::DeprecationWarning script.py      (fail fast on any deprecation)
```

**What this does:** Since Python 3.7 the default filter list contains `default::DeprecationWarning:__main__` followed by `ignore::DeprecationWarning`, so deprecations are visible when your own top-level code triggers them but silent when a library you imported triggers them. Developers who want to prepare for upgrades re-enable them globally with a filter or the `-W` flag; `unittest` and `pytest` also re-enable them during test runs.

### Example 3: Edge Case

```python
# Deprecating a class attribute / module-level name with __getattr__
import warnings

class Config:
    def __getattr__(self, name):
        if name == "timeout_ms":
            warnings.warn(
                "timeout_ms is deprecated; use timeout (seconds)",
                DeprecationWarning,
                stacklevel=2,
            )
            return self.timeout * 1000
        raise AttributeError(name)

    timeout = 30

cfg = Config()
print(cfg.timeout_ms)   # warns, then prints 30000 - the old name still works
```

**What this shows:** Deprecation is a *transition* mechanism: the old spelling keeps functioning while warning developers to move. This is the semantic core translators must keep - not "broken," not "removed," but "still works, officially discouraged, will be removed."

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY)

**Similar terms in this pattern:**

1. `Warning` - The base class supplying the shared root
2. `PendingDeprecationWarning` - Sibling: the feature is NOT deprecated yet, but will be (hidden by default)
3. `FutureWarning` - Sibling: deprecation-related warnings aimed at END USERS (shown by default everywhere)
4. `UserWarning` - Sibling: generic default category

**Pattern rule:** Qualifier + shared "warning" root. The qualifier here must express "officially discouraged / being phased out," and it must stay distinguishable from the qualifiers of `PendingDeprecationWarning` (future deprecation) and `FutureWarning` (end-user audience).


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "deprecari" - "to pray against, to ward off by prayer" (de- "away" + precari "to pray"). English "deprecate" drifted from "express disapproval of" to the software sense: "officially disapprove of a feature while it still exists, pending removal." This software meaning is younger than the dictionary meaning and is jargon even in English.

**Why Python uses this:** "Deprecated" was already the established industry word (documentation, Java's `@Deprecated`, RFCs) for "still supported but scheduled for removal." Python adopted it for the warning category that manages exactly that lifecycle stage.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`DeprecationWarning` marks the middle stage of a feature's life cycle: introduced → deprecated → removed. When maintainers decide a function, argument, or behavior should go away, they cannot simply delete it - that would break working programs. Instead they keep it functioning and make it emit `DeprecationWarning`, giving developers one or more release cycles to migrate before the removal actually happens.

The intended *audience* is developers, not end users. This is encoded in the default visibility rule (PEP 565, Python 3.7): the warning is shown when the deprecated call is triggered by code in `__main__` (a script or REPL session - code the person seeing the message can fix) and hidden when triggered from inside imported libraries (an application's end user can't fix a library's internals, so showing them the message is noise). Library developers see them anyway because test runners like `unittest` and `pytest` re-enable them.

Two siblings divide the remaining semantic space, and translators must keep all three distinct: `PendingDeprecationWarning` means "not deprecated *yet*, but it will be" (hidden by default), and `FutureWarning` is for deprecation messages that *end users* of an application are meant to see (shown by default everywhere). Several languages are tempted to translate all three with one word for "old/obsolete" - that collapses a three-way distinction Python's documentation depends on.

**Key behaviors:**

1. **The feature still works:** Emitting `DeprecationWarning` changes nothing about execution; the deprecated code path runs to completion. Deprecation is a scheduled future removal, not a present failure.

2. **Shown by default only in `__main__` (since 3.7):** The default filters are `default::DeprecationWarning:__main__` then `ignore::DeprecationWarning` - visible for your own top-level code, silent from imported libraries. `-W`, `PYTHONWARNINGS`, `filterwarnings()`, and test runners override this.

3. **Promotable for migration audits:** `python -W error::DeprecationWarning` turns every deprecated usage into a raised exception, a standard technique for finding all migration work before upgrading a dependency or Python itself.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (qualifier "deprecation" + root "warning")
- **Action vs State:** STATE - names the phased-out status of a feature
- **Temporal aspect:** Present status with future consequence - discouraged NOW, removed LATER

### Recommended Form

**Primary recommendation:** Qualifier meaning "being phased out of use / officially discouraged" + the family's "warning" root. Prefer the term your language's existing developer documentation uses for "deprecated" (check local Java/.NET/Python docs) - this word is jargon everywhere, and matching established jargon beats inventing a purer word nobody recognizes.

**Forms to AVOID:**

- ❌ "Old" / "outdated" alone - a feature can be old without being deprecated; deprecation is an official status, not an age
- ❌ "Removed" / "abandoned" / "dead" - the feature still works; translating it as already-gone is factually wrong
- ❌ "Forbidden" / "prohibited" - using it is discouraged, not disallowed
- ❌ Any error/failure word for the root - execution continues

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Dictionary "deprecate" = to express strong disapproval of, to belittle ("self-deprecating humor")
- ❌ Meaning 2: "Depreciate" = to lose monetary value (a common English confusion; some languages only have this word)
- ❌ Meaning 3: Already removed / no longer functional
- ✅ Meaning 4: **OFFICIALLY DISCOURAGED PENDING REMOVAL** - the feature works today, developers should migrate before it is removed

**Example:**

English "deprecation" can mean:

1. "He spoke with gentle self-deprecation" (belittling) ❌
2. "The car's depreciation was steep" (loss of value - different word, often conflated) ❌
3. "That module was deleted in 3.12" (removal - the stage AFTER deprecation) ❌
4. `warnings.warn("use new_api()", DeprecationWarning)` while `old_api()` still works ✅ **This is the Python meaning**

**Your translation should capture meaning #4. Two non-negotiables: the root must be a "warning" word, never an "error" word (the deprecated feature still runs - nothing has failed); and the qualifier must read as a status ("being phased out"), not an event ("was removed"). Where no native word exists, a "disuse/obsolescence" noun plus the family root is the honest compromise.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `DeprecationWarning`, check these translations:**

- [ ] `Warning` - root must match exactly
- [ ] `PendingDeprecationWarning` - must read as "upcoming/pending" + THIS term's qualifier + root; the pair must be visibly related and visibly different
- [ ] `FutureWarning` - must NOT share this term's qualifier; its distinction is audience (end users), expressed as "future"
- [ ] `UserWarning` - sibling; same structural pattern

**Consistency rule:**

The deprecation trio encodes two axes - timing (now vs later) and audience (developers vs end users). `DeprecationWarning` = deprecated NOW, message for DEVELOPERS. `PendingDeprecationWarning` = deprecated LATER, for developers. `FutureWarning` = deprecation messaging for END USERS. Translate the three so that a reader can recover both axes; never let two of them share an identical name.


### Functional relationships

**This term works WITH:**

1. **`warnings.warn()` + `DeprecationWarning`**: the standard deprecation idiom

```python
warnings.warn("use new_api()", DeprecationWarning, stacklevel=2)
```

2. **`-W` / filters + `DeprecationWarning`**: migration auditing

```python
# python -W error::DeprecationWarning  → any deprecated usage raises
```

**Common pairing:**

```python
import warnings

def fetch(url, timeout_ms=None, timeout=None):
    if timeout_ms is not None:
        warnings.warn(
            "timeout_ms is deprecated; pass timeout in seconds",
            DeprecationWarning,
            stacklevel=2,
        )
        timeout = timeout_ms / 1000
    return _do_fetch(url, timeout)

# Library test suite: fail on any deprecated usage
with warnings.catch_warnings():
    warnings.simplefilter("error", DeprecationWarning)
    try:
        fetch("https://example.org", timeout_ms=5000)
    except DeprecationWarning:
        print("migration needed before next release")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `DeprecationWarning`

- "Deprecation" is software jargon even in English; many languages have no lexicalized equivalent at all
- Candidate words ("obsolete," "outdated," "discouraged," "disused," "abandoned") each miss part of the meaning: official status + still functional + future removal
- Must remain distinguishable from `PendingDeprecationWarning` and `FutureWarning` after translation
- Established local jargon (from Java/.NET/docs translations) may conflict with the "purest" dictionary choice, and following established jargon is usually right

**For this term:** HARD

**Rationale:** This is the hardest word in the warning family. The best-established qualifier in a language's technical register is rarely a perfect semantic match - candidates tend to lean toward natural aging, neglect, or falling out of currency rather than "officially discouraged pending removal." Where officially localized Python documentation already uses a term, that term is the strongest candidate. A native-speaker linguist should confirm each choice against local developer-documentation conventions.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "officially discouraged, still works, will be removed" - not "removed," "broken," or merely "old"?
- [ ] Root word means "warning" (advisory, non-fatal), never "error"?
- [ ] Does NOT accidentally mean monetary depreciation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Qualifier attaches per target-language compounding rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Uses the exact root chosen for `Warning`?
- [ ] Distinct from BOTH `PendingDeprecationWarning` and `FutureWarning` translations?
- [ ] Matches how local developer documentation already translates "deprecated"?

### 4. Usability

- [ ] Short enough (ideally ≤3 words)?
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
term: DeprecationWarning
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
