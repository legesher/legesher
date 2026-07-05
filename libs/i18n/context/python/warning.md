# Python Builtin: `Warning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category, base class)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`Warning` is the base class for all warning categories in Python. It subclasses `Exception`, but unlike ordinary exceptions, warnings are advisory: they are typically emitted with `warnings.warn()` rather than raised, execution continues after they are shown, and they can be filtered, silenced, or promoted to errors via the `warnings` module and the `-W` command-line flag.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Emitting a warning: the program keeps running
import warnings

warnings.warn("This feature is experimental")
print("This line still runs")
# stderr shows: UserWarning: This feature is experimental
```

**What this does:** `warnings.warn()` emits a warning message to `stderr` and then execution continues. Nothing is raised and nothing stops. When no category is given, the warning uses `UserWarning`, which is a subclass of `Warning`. This is the core difference from an error: a warning informs, an error fails.

### Example 2: Common Pattern

```python
# Defining a custom warning category by subclassing Warning
import warnings

class ConfigWarning(Warning):
    """Project-specific warning category."""

def load_config(path):
    if not path.endswith(".toml"):
        warnings.warn(f"unexpected config extension: {path}", ConfigWarning)
    return {}

warnings.simplefilter("ignore", ConfigWarning)   # silence this category
load_config("settings.ini")                       # nothing printed

warnings.simplefilter("default", ConfigWarning)  # show it again
load_config("settings.ini")                       # ConfigWarning printed
```

**What this does:** Libraries create their own warning categories by subclassing `Warning` (or one of its built-in subclasses). Because every warning carries a category class, users can filter by category: `simplefilter("ignore", ConfigWarning)` silences exactly this kind of warning without touching any other. The category passed to `warnings.warn()` must be a `Warning` subclass.

### Example 3: Edge Case

```python
# Warnings can be promoted to real exceptions
import warnings

warnings.simplefilter("error")   # promote ALL warnings to exceptions

try:
    warnings.warn("about to become an exception")
except UserWarning as exc:       # Warning subclasses Exception, so except works
    print(f"Caught: {exc}")

# Same idea from the command line:
#   python -W error script.py
```

**What this shows:** `Warning` inherits from `Exception`, so under an `"error"` filter the same call that normally just prints a message instead raises the warning as an exception that `try`/`except` can catch. This dual nature (advisory by default, raisable on demand) is why `Warning` lives in the exception hierarchy at all, and it is exactly the nuance a translation must not blur: the *default* behavior is non-fatal.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY - base of the warning family)

**Similar terms in this pattern:**

1. `UserWarning` - Default category used by `warnings.warn()`; subclasses `Warning`
2. `DeprecationWarning` - Warns developers about deprecated features; subclasses `Warning`
3. `RuntimeWarning` - Warns about dubious runtime behavior; subclasses `Warning`
4. `Exception` - The parent class of `Warning` in the exception hierarchy

**Pattern rule:** All warning categories are nouns. `Warning` supplies the shared root word; every subclass translation must reuse that exact root plus a qualifier (`UserWarning` = "user" + "warning", etc.), just as `...Error` exceptions share an "error" root.


---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** From Old English "warnian," meaning "to give notice of danger, to caution." The core sense has always been advisory: alerting someone so they can act, not punishing them for a fault already committed.

**Why Python uses this:** Python borrowed the compiler tradition of separating *errors* (the program cannot or should not continue) from *warnings* (the program continues, but the developer should know something). `Warning` names the root of that second channel, and the `warnings` module (PEP 230) built the filtering machinery around it.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Warning` is the base category for Python's warning system. A warning is a message about a condition that deserves attention but does not prevent the program from working: a feature scheduled for removal, a suspicious comparison, an unclosed file. Code emits warnings with `warnings.warn(message, category)`, where `category` is `Warning` or one of its subclasses. By default the warning is printed to `stderr` once per source location, and execution continues on the very next line.

Because `Warning` subclasses `Exception`, warning objects fit into the exception machinery: they can be raised deliberately, caught with `except`, and, most importantly, *promoted* to errors by filters (`warnings.simplefilter("error")` or `python -W error`). Filters are the second half of the design: each filter matches an action (`"ignore"`, `"default"`, `"always"`, `"error"`, `"once"`, `"module"`) to a category, so consumers of a library decide which warnings they see, silence, or treat as fatal.

Direct use of the bare `Warning` class is rare; it exists mostly as the ancestor that makes `except Warning:` and `simplefilter(action, Warning)` match every warning category at once. Application code normally emits `UserWarning` (the default), and libraries pick the built-in subclass whose meaning fits, or define their own.

**Key behaviors:**

1. **Advisory, not fatal:** Under default filters, emitting a warning prints a message and execution continues. This is the defining contrast with errors, and the property every translation must preserve.

2. **Category-based filtering:** Every warning has a category class. Filters (`warnings.filterwarnings`, `warnings.simplefilter`, the `-W` flag, `PYTHONWARNINGS`) match by category and decide whether it is shown once, always, ignored, or raised as an exception.

3. **Root of the hierarchy:** All built-in warning categories (`UserWarning`, `DeprecationWarning`, `FutureWarning`, `ResourceWarning`, ...) subclass `Warning`, and `Warning` itself subclasses `Exception`. Custom categories must subclass `Warning` or `warnings.warn()` rejects them with a `TypeError`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun - names a class of advisory messages, and serves as the root word for eleven sibling category names
- **Action vs State:** STATE - describes the nature of a message, not an action
- **Temporal aspect:** Instantaneous emission, but advisory about ongoing or future conditions

### Recommended Form

**Primary recommendation:** Use the single most standard noun for "warning" in the target language's existing developer tooling (compiler output, IDE messages, linters). This word becomes the shared root for the entire warning family, so choose one that compounds well with qualifiers.

**Forms to AVOID:**

- ❌ Any word meaning "error," "failure," or "fault" - erases the load-bearing warning/error distinction
- ❌ Weak words meaning "notice" / "hint" / "tip" - undersell that the condition deserves action
- ❌ Strong words meaning "alarm" / "danger" / "threat" - oversell severity; a warning is calm and advisory
- ❌ Verb forms ("to warn") - this is a category name, a noun

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A threat or ultimatum ("final warning before dismissal")
- ❌ Meaning 2: An alarm about immediate physical danger ("storm warning")
- ❌ Meaning 3: An error or failure (this is NOT what a warning is)
- ✅ Meaning 4: **AN ADVISORY MESSAGE** - a caution that something deserves attention while execution continues normally

**Example:**

English "warning" can mean:

1. "This is your last warning" (threat/ultimatum) ❌
2. "Tornado warning" (imminent-danger alarm) ❌
3. `person.age` failing (that is an *error*, not a warning) ❌
4. "DeprecationWarning: use X instead" printed while the program keeps running ✅ **This is the Python meaning**

**Your translation should capture meaning #4, NOT the others. The single most important test: the chosen word must NOT be a word for "error" or "failure." A warning means execution CONTINUES; an error means something failed. If the target-language word blurs that line, pick another word.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Warning`, check these translations:**

- [ ] `UserWarning` - must be "user" + the exact root chosen here
- [ ] `DeprecationWarning` - must be "deprecation" + the same root
- [ ] `FutureWarning` / `PendingDeprecationWarning` - same root; qualifiers carry the audience/timing distinctions
- [ ] `RuntimeWarning`, `SyntaxWarning`, `ImportWarning`, `UnicodeWarning`, `BytesWarning`, `EncodingWarning`, `ResourceWarning` - same root, qualifier per compounding rules
- [ ] `Exception` - parent class; the warning root must be clearly distinct from the exception/error root

**Consistency rule:**

`Warning` is the root of a 12-term family. Whatever word you choose here is REQUIRED, unchanged, in all eleven subclass translations - only the qualifier varies, attached according to the target language's noun-compounding rules. If `Warning` is "Advertencia," then `UserWarning` must be "AdvertenciaDeUsuario," never "AvisoDeUsuario."


### Functional relationships

**This term works WITH:**

1. **`warnings.warn()` + `Warning`**: the emitting function takes a `Warning` subclass as its category argument

```python
warnings.warn("message", Warning)  # explicit base category
```

2. **Filters + `Warning`**: filtering on the base class matches every warning category at once

```python
warnings.simplefilter("ignore", Warning)  # silence all warnings
```

**Common pairing:**

```python
import warnings

# Emit with the default category (UserWarning, a Warning subclass)
warnings.warn("caches disabled; performance will suffer")

# Temporarily control warnings inside a block
with warnings.catch_warnings():
    warnings.simplefilter("error")          # promote to exceptions here
    try:
        warnings.warn("strict mode")
    except Warning as exc:                  # base class catches ALL categories
        print(f"caught: {exc}")

# Command-line equivalents:
#   python -W ignore script.py     (silence all warnings)
#   python -W error script.py      (promote all warnings to errors)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `Warning`

- Every language has a word for "warning," but most have several (notice, caution, alert, alarm) at different severities
- The chosen word must sit exactly between "hint" and "error" - advisory, non-fatal, action-worthy
- The choice locks in the root for eleven other terms, raising the cost of a poor pick
- Must compound cleanly with qualifiers in the target language

**For this term:** MEDIUM

**Rationale:** The concept is universal and most languages have an established compiler-message word for it, so a well-contextualized model should land on the right term. The difficulty is synonym selection (severity register) plus the family-root responsibility: this single decision propagates to all twelve warning categories, so it deserves a deliberate check against existing developer-tool localization in the target language.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ADVISORY MESSAGE (execution continues), not error/failure?
- [ ] Clearly distinct from the word used for `Exception` / "...Error" classes?
- [ ] Neither too weak (hint) nor too strong (alarm/threat)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Usable unchanged as the root of all 11 subclass names?
- [ ] Compounds naturally with qualifiers (user, deprecation, syntax, ...)?
- [ ] Matches the word local compilers/IDEs already print for warnings?

### 4. Usability

- [ ] Short enough (1-2 words)?
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
term: Warning
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
