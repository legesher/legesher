# Python Builtin: `PendingDeprecationWarning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category)
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`PendingDeprecationWarning` is the warning category for features that are NOT deprecated yet but are expected to be deprecated in the future. It is one stage earlier than `DeprecationWarning` in a feature's phase-out timeline. It subclasses `Warning`, is emitted via `warnings.warn()`, and is ignored (hidden) by default - maintainers use it as an early, quiet signal that only developers who opt in will see.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Early signal: this API WILL be deprecated, but is not yet
import warnings

def legacy_mode():
    warnings.warn(
        "legacy_mode() will be deprecated in a future release",
        PendingDeprecationWarning,
        stacklevel=2,
    )
    return "still fully supported"

legacy_mode()   # runs normally; the warning is HIDDEN by default
```

**What this does:** The function emits a `PendingDeprecationWarning` and returns normally - and under default filters nothing is even printed, because this category is ignored by default. It is a whisper to attentive maintainers, not an announcement.

### Example 2: Common Pattern

```python
# Opting in to see pending deprecations
import warnings

warnings.simplefilter("default", PendingDeprecationWarning)  # un-hide them
legacy_mode()   # now the warning prints, execution still continues

# Or from the command line, without touching code:
#   python -W default::PendingDeprecationWarning script.py
# Or fail fast to build a migration list:
#   python -W error::PendingDeprecationWarning script.py
```

**What this does:** Because the category is hidden by default, forward-looking developers enable it explicitly with a filter or the `-W` flag. `"default"` shows each warning once per source location; `"error"` promotes it to an exception, useful for auditing where a codebase touches soon-to-be-deprecated APIs.

### Example 3: Edge Case

```python
# The phase-out ladder: pending → deprecated → removed
import warnings

def api_v1():
    # Release N: quiet heads-up (hidden by default)
    warnings.warn("api_v1 will be deprecated", PendingDeprecationWarning, stacklevel=2)
    ...

def api_v1_later():
    # Release N+1: real deprecation (shown by default in __main__)
    warnings.warn("api_v1 is deprecated; use api_v2", DeprecationWarning, stacklevel=2)
    ...

# Release N+2: the function is removed; calling it raises AttributeError/ImportError
```

**What this shows:** The two categories are consecutive rungs on one ladder, differing in timing and default visibility. A translation must keep them clearly related (same deprecation qualifier, same warning root) and clearly ordered ("pending/upcoming" marks the earlier rung).

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY)

**Similar terms in this pattern:**

1. `DeprecationWarning` - The next stage: the feature IS deprecated now (shown by default in `__main__`)
2. `FutureWarning` - Deprecation-related warnings aimed at END USERS (shown by default everywhere)
3. `Warning` - The base class supplying the shared root
4. `UserWarning` - Sibling generic category

**Pattern rule:** Qualifier + shared "warning" root. This term's qualifier = "pending/upcoming" + the exact deprecation word chosen for `DeprecationWarning`. The pair must differ ONLY by the pending/upcoming marker.


---

## Etymology (Brief)

**English Origin:** Latin (both components)

**Root meaning:** "Pending" comes from Latin "pendere," "to hang" - something hanging, not yet settled, awaiting resolution. "Deprecation" from "deprecari," "to pray away" (see the `DeprecationWarning` brief). Together: a deprecation that hangs in the future, announced but not yet in force.

**Why Python uses this:** Python's warning system (PEP 230) wanted a two-step phase-out: first a quiet advance notice, then the real deprecation. "Pending" is standard English for "scheduled but not yet effective" (pending legislation, patent pending), making the timeline explicit in the class name.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`PendingDeprecationWarning` exists for maintainers who want to phase a feature out gently. Before committing to a deprecation - with its documentation changes, migration guides, and removal schedule - they can emit this category to say: "we intend to deprecate this; if you're building something new, don't use it." The feature remains fully supported; nothing about its behavior or its support status has changed yet.

Its defining operational property is silence: the default warning filters include `ignore::PendingDeprecationWarning`, so nobody sees it unless they opt in with `warnings.simplefilter()`, `filterwarnings()`, the `-W` flag, or `PYTHONWARNINGS`. That is deliberate audience selection - only maintainers and forward-planning developers who actively ask for early signals receive them. Compare `DeprecationWarning` (shown by default in `__main__`) and `FutureWarning` (shown by default everywhere, aimed at end users): the three categories form a visibility gradient that mirrors their urgency and audience.

In practice this category is used sparingly - many projects skip straight to `DeprecationWarning` - but it remains part of the standard hierarchy, and standard-library modules have historically used it for long phase-outs. For translation, what matters is the relationship: this term is `DeprecationWarning` plus a "not yet / upcoming" marker, and readers must be able to see both the kinship and the ordering at a glance.

**Key behaviors:**

1. **Earlier stage than deprecation:** The feature is NOT deprecated yet. The warning announces intent: deprecation will come in a future release. Nothing about current support changes.

2. **Ignored by default:** The default filter list contains `ignore::PendingDeprecationWarning`, so it prints nothing unless a developer opts in via filters or `-W`. This is the quietest rung of the deprecation ladder.

3. **Advisory and promotable like all warnings:** Emitted with `warnings.warn()`, execution continues; `-W error::PendingDeprecationWarning` can promote it to an exception for early migration audits.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (modifier "pending" + qualifier "deprecation" + root "warning")
- **Action vs State:** STATE - names a scheduled-but-not-yet-effective status
- **Temporal aspect:** Explicitly future - the deprecation has not happened yet

### Recommended Form

**Primary recommendation:** Take the FINAL translation of `DeprecationWarning` verbatim and add your language's standard marker for "upcoming / scheduled / not yet in effect." Do not re-translate the deprecation part - the visual kinship between the two class names is load-bearing.

**Forms to AVOID:**

- ❌ A different deprecation word than `DeprecationWarning` uses - breaks the ladder relationship
- ❌ Markers meaning "suspended/paused" (a common mistranslation of "pending") - the deprecation is coming, not paused
- ❌ Collapsing into the same name as `DeprecationWarning` - erases the timing distinction
- ❌ Any error/failure word for the root - nothing has failed; this is the mildest warning in the family

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Pending" as suspended, on hold, in limbo
- ❌ Meaning 2: "Pending" as unresolved/undecided (the deprecation IS decided - it just hasn't taken effect)
- ✅ Meaning 3: **SCHEDULED AND FORTHCOMING** - the deprecation is planned and will arrive in a future release; the feature is fully supported today

**Example:**

English "pending" can mean:

1. "The project is pending funding" (blocked, on hold) ❌
2. "The verdict is pending" (undecided) ❌
3. "Patent pending" (filed, in the pipeline, arriving) ✅ **This is the Python meaning**

**Your translation should capture meaning #3, NOT the others. And as with every member of this family: the root must be a "warning" word, never an "error" word. This is arguably the least error-like class in Python - the feature is not even deprecated yet, let alone broken; execution continues and, by default, nothing is even printed.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `PendingDeprecationWarning`, check these translations:**

- [ ] `DeprecationWarning` - THIS term must equal that translation + a "pending/upcoming" marker; translate that one first
- [ ] `Warning` - root must match exactly
- [ ] `FutureWarning` - must remain distinct; its qualifier is "future" (end-user audience), not "pending deprecation"
- [ ] `UserWarning` - sibling; same structural pattern

**Consistency rule:**

Derive, don't invent: `PendingDeprecationWarning` = [pending marker] + [exact `DeprecationWarning` translation], composed per your language's grammar. The deprecation trio must keep both axes readable - timing (pending → deprecated) and audience (`FutureWarning` = end users). No two of the three may share an identical name.


### Functional relationships

**This term works WITH:**

1. **`warnings.warn()` + `PendingDeprecationWarning`**: the early-notice idiom

```python
warnings.warn("will be deprecated", PendingDeprecationWarning, stacklevel=2)
```

2. **Filters + `PendingDeprecationWarning`**: opt-in visibility (hidden by default)

```python
warnings.simplefilter("default", PendingDeprecationWarning)
```

**Common pairing:**

```python
import warnings

def old_helper():
    warnings.warn(
        "old_helper() will be deprecated; prefer new_helper()",
        PendingDeprecationWarning,
        stacklevel=2,
    )
    return 42

old_helper()          # silent: ignored by default

# A maintainer auditing for upcoming breakage:
with warnings.catch_warnings():
    warnings.simplefilter("error", PendingDeprecationWarning)
    try:
        old_helper()
    except PendingDeprecationWarning as exc:
        print(f"plan migration: {exc}")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `PendingDeprecationWarning`

- Inherits every difficulty of "deprecation" (see the `DeprecationWarning` brief) and adds a second untranslatable-ish word
- "Pending" is polysemous: suspended vs undecided vs scheduled-and-coming - only the third is correct
- The result is a three-part compound; some languages produce something unwieldy and are tempted to shorten it into collision with `DeprecationWarning`
- Correctness is relational: this translation is only right if it visibly extends the final `DeprecationWarning` translation

**For this term:** HARD

**Rationale:** The deprecation qualifier is already the hardest word in the family, and the pending marker adds a second precision requirement (forthcoming, not suspended). The main failure modes are collapsing into `DeprecationWarning`'s name or picking a "paused" word. Because the term is rarely encountered, there is little established local jargon to lean on - derive it mechanically from the sibling translation and have a native speaker sanity-check the "pending" word's connotation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "deprecation scheduled for the future, feature fully supported today"?
- [ ] "Pending" word means forthcoming/scheduled, NOT suspended or undecided?
- [ ] Root word means "warning" (advisory, non-fatal), never "error"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Modifier order natural in the target language?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the exact `DeprecationWarning` translation as its core?
- [ ] Uses the exact root chosen for `Warning`?
- [ ] Distinct from both `DeprecationWarning` and `FutureWarning`?

### 4. Usability

- [ ] As short as the three-part meaning allows?
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
term: PendingDeprecationWarning
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
