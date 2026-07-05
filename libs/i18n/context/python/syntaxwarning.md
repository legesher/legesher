# Python Builtin: `SyntaxWarning` - Translation Brief (Tier 1)

**Category:** exception
**Type:** exception class (warning category)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`SyntaxWarning` is the warning category for dubious syntax - source code that parses and runs, but is written in a way that usually indicates a mistake, such as testing `is` against a literal. It subclasses `Warning`, is shown by default, and is emitted at compile time (when the code is parsed), unlike its sibling `RuntimeWarning`. Its hard-failure counterpart is `SyntaxError`, where the code cannot be parsed at all.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# The classic: `is` with a literal
answer = "yes"

if answer is "yes":        # SyntaxWarning: "is" with a literal.
    print("confirmed")     #   Did you mean "=="?
```

**What this does:** `is` tests object *identity*, not equality; whether two equal strings are the same object is an interpreter implementation detail. The code compiles and runs - it may even print "confirmed" - but the result is unreliable, so CPython (3.8+) emits `SyntaxWarning` at compile time suggesting `==`. Advisory, not fatal: the program executes.

### Example 2: Common Pattern

```python
# Another compile-time catch: an assert that can never fail
def check(items):
    assert (len(items) > 0, "items must not be empty")
    # SyntaxWarning: assertion is always true; perhaps
    #   remove parentheses?

# The tuple (condition, message) is always truthy, so the assert
# never fires. Correct spelling:
def check_fixed(items):
    assert len(items) > 0, "items must not be empty"
```

**What this does:** Wrapping an assert's condition and message in parentheses creates a two-element tuple, which is always truthy - the assertion silently stops asserting anything. The parser recognizes this almost-certainly-wrong shape and warns while still compiling the code. Recent CPython versions also flag invalid string escape sequences like `"\d"` with `SyntaxWarning` (they were a `DeprecationWarning` before Python 3.12).

### Example 3: Edge Case

```python
# Compile time, not run time: the warning fires on import/definition
import warnings

code = 'flag = (value is 10)'          # dubious identity test on an int

warnings.simplefilter("error", SyntaxWarning)
try:
    compile(code, "<generated>", "exec")   # warning raised HERE, at compile
except SyntaxError:
    print("unreachable in this example")
except SyntaxWarning as exc:
    print(f"caught at compile time: {exc}")
```

**What this shows:** `SyntaxWarning` is attached to *compilation*: it fires when a module is imported, a function is defined, or `compile()` runs - even if the dubious line never executes. Under an `"error"` filter, compilation of that code raises. Contrast `SyntaxError`: there the text is not valid Python at all and cannot compile; here it is valid but suspicious.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (WARNING CATEGORY)

**Similar terms in this pattern:**

1. `Warning` - The base class supplying the shared root
2. `SyntaxError` - The ERROR counterpart: the source cannot be parsed (same qualifier, error root)
3. `RuntimeWarning` - Sibling: dubiousness detected during execution instead of at compile time
4. `UserWarning` - Sibling: generic default category

**Pattern rule:** Qualifier + shared "warning" root. The qualifier "syntax" must use the same word your pack uses (or will use) for `SyntaxError` - the grammar-of-code sense - so the compile-time pair shares a visible domain.


---

## Etymology (Brief)

**English Origin:** Greek via Latin

**Root meaning:** "Syntax" from Greek "syntaxis" - "arrangement, putting together in order" (syn- "together" + tassein "to arrange"). In linguistics and programming alike: the rules for how symbols may be arranged into valid expressions.

**Why Python uses this:** The parser is the component that knows arrangement rules, and it reports at two severities: `SyntaxError` when the arrangement is invalid (cannot compile), `SyntaxWarning` when it is valid but suspicious (compiles, probably a mistake). The shared qualifier tells developers which stage of the pipeline is speaking.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`SyntaxWarning` is emitted by Python's compiler for constructs that are grammatically legal but idiomatically wrong - shapes of code that experience says are nearly always mistakes. The flagship case is `is`/`is not` with a literal (`x is "yes"`, `n is 10`): identity comparison against a literal depends on interpreter internals like small-integer caching and string interning, so it can "work" in testing and fail in production. CPython warns and suggests `==`. Other cases include the parenthesized assert-tuple (an assertion that is always true) and, in recent versions, invalid escape sequences in string literals such as `"\d"` (promoted from `DeprecationWarning` to `SyntaxWarning` in Python 3.12 on the road to becoming errors).

The distinctive property for this category is *when* it fires: at compile time. Python compiles source to bytecode when a module is imported, a function is defined, or `compile()`/`exec()` is called - and that is when `SyntaxWarning` appears, even for lines that never execute. This makes it the compile-time mirror of `RuntimeWarning`, and the advisory mirror of `SyntaxError`. Keep the three-way geometry in mind: same qualifier as `SyntaxError` (both are the parser speaking), same root as `RuntimeWarning` (both are advisories), all four names built from just two qualifiers and two roots.

`SyntaxWarning` is shown by default (no default filter ignores it) and, like the whole family, can be promoted: linters aside, `python -W error::SyntaxWarning` makes suspicious syntax fail fast, which some teams use in CI. The code still exists on a legal path - nothing has failed when the warning prints; the parser is predicting a bug, not reporting one.

**Key behaviors:**

1. **Compile-time emission:** Fires when source is compiled (import, definition, `compile()`), not when the line runs - a dubious line inside a never-called function still warns at definition/import time.

2. **Legal but probably wrong:** The canonical triggers - `is` with a literal, always-true assert tuples, invalid escape sequences - all compile and execute; the warning flags shapes that rarely mean what was written.

3. **Shown by default, promotable:** Not in the default ignore list; prints once per location and compilation proceeds. Under an `"error"` filter the warning is raised at compile time instead.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (qualifier "syntax" + root "warning")
- **Action vs State:** STATE - names a category of advisory diagnostic
- **Temporal aspect:** Compile time - before execution begins

### Recommended Form

**Primary recommendation:** Your language's established word for programming-language syntax - the one used in "syntax error," which every developer has seen - plus the family's warning root. When `SyntaxError` enters the pack, the two must share the qualifier exactly.

**Forms to AVOID:**

- ❌ A different "syntax" word than `SyntaxError` will use - the parser's two severities must visibly pair
- ❌ General "grammar of natural language" words if your language separates linguistic grammar from code syntax
- ❌ "Style/formatting warning" phrasings - style is a linter's domain; this comes from the compiler and concerns meaning, not aesthetics
- ❌ Any error/failure word for the root - the code compiled and runs; failure to parse is `SyntaxError`

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A syntax ERROR - source that cannot be parsed (that is `SyntaxError`)
- ❌ Meaning 2: Style or formatting complaints (linter territory)
- ❌ Meaning 3: Natural-language grammar issues
- ✅ Meaning 4: **AN ADVISORY FROM THE COMPILER ABOUT LEGAL-BUT-DUBIOUS SYNTAX** - the code parses and runs, but its shape almost certainly isn't what the author meant

**Example:**

English "syntax warning" could be parsed as:

1. `def f(:` failing to parse (that raises `SyntaxError` - compilation fails) ❌
2. "Line longer than 79 characters" (style tool output) ❌
3. A grammar checker flagging an essay ❌
4. `if answer is "yes":` compiling fine while printing `SyntaxWarning: "is" with a literal. Did you mean "=="?` ✅ **This is the Python meaning**

**Your translation should capture meaning #4. This term carries the family's highest risk of error-word contamination, because "syntax error" is the best-known diagnostic phrase in programming. Hold the line: the root must be your family's "warning" word - the parser is predicting a bug in code that runs, not rejecting code that doesn't.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `SyntaxWarning`, check these translations:**

- [ ] `SyntaxError` (when added to the pack) - MUST share this term's qualifier; the pair differs only in root
- [ ] `Warning` - root must match exactly
- [ ] `RuntimeWarning` - the execution-time counterpart; the two qualifiers must contrast cleanly (compile time vs run time)
- [ ] `is` / `assert` - the keywords in this class's flagship diagnostics; message translations should echo the class name's vocabulary

**Consistency rule:**

Two-by-two grid discipline: {syntax, runtime} × {warning, error} yields four class names from exactly two qualifiers and two roots. Translate the grid, not the individual cells - pick one syntax word, one runtime word, one warning root, one error root, and compose all four names from them.


### Functional relationships

**This term works WITH:**

1. **`is` (keyword) + `SyntaxWarning`**: the identity-vs-equality diagnostic

```python
x is "literal"   # SyntaxWarning: did you mean "=="?
```

2. **`compile()` / import + `SyntaxWarning`**: emission happens at compilation

```python
compile('n is 5', '<s>', 'eval')   # warning attached to this step
```

**Common pairing:**

```python
import warnings

# CI recipe: dubious syntax fails the build
warnings.simplefilter("error", SyntaxWarning)

source = '''
def confirm(answer):
    return answer is "yes"     # should be ==
'''

try:
    compile(source, "review.py", "exec")
except SyntaxWarning as exc:
    print(f"fix before merge: {exc}")

# Normal runs leave it advisory:
#   the module imports, the function works often enough to hide the bug -
#   which is exactly why the compiler speaks up.
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `SyntaxWarning`

- "Syntax" has a settled technical translation in most languages thanks to "syntax error"'s ubiquity
- Some languages have competing renderings of "syntax" needing one standardization decision
- The error-word contamination risk is unusually high because of the fame of "syntax error"
- Grid consistency with `SyntaxError`/`RuntimeWarning`/`RuntimeError` constrains the choice helpfully

**For this term:** MEDIUM

**Rationale:** The qualifier is well-trodden vocabulary in every language with programming education; the real work is grid discipline (one syntax word shared with `SyntaxError`) and keeping the root firmly on the warning side despite the gravitational pull of the phrase "syntax error." A language with competing syntax renderings needs one deliberate standardization between them.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "compiler advisory about dubious-but-legal syntax," not "code failed to parse"?
- [ ] Root word means "warning" (advisory, non-fatal), never "error"?
- [ ] "Syntax" is the code-structure sense, not style or natural-language grammar?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Qualifier attaches per target-language compounding rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Uses the exact root chosen for `Warning`?
- [ ] Qualifier reserved to match `SyntaxError` when it enters the pack?
- [ ] Contrasts cleanly with `RuntimeWarning`'s qualifier (the 2×2 grid holds)?

### 4. Usability

- [ ] Short enough (1-3 words)?
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
term: SyntaxWarning
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
