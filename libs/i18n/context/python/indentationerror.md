# Python Builtin: `IndentationError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`IndentationError` is a subclass of `SyntaxError` raised when the parser rejects code because its indentation - the leading whitespace at the start of each line - is incorrect. Indentation is structural in Python: it is how blocks are delimited, a design unique to Python among mainstream languages, which makes translating this term pedagogically load-bearing.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# The parser rejects the code before it runs, so we show the
# error honestly by compiling a string:
source = "def greet():\nprint('hi')"   # body line not indented
compile(source, "<example>", "exec")
# Raises IndentationError: expected an indented block
# (3.10+: expected an indented block after function definition on line 1)
```

**What this does:** After `def greet():` Python requires the function body to be indented - the indentation is what marks it as the body. The unindented `print` line breaks that rule, so parsing stops with `IndentationError`. Like all syntax-family errors, it fires at compile time; none of the code runs.

### Example 2: Common Pattern

```python
# A teaching tool checking student code for indentation problems
def check_indentation(source):
    try:
        compile(source, "<lesson>", "exec")
    except IndentationError as e:
        return f"line {e.lineno}: {e.msg}"
    except SyntaxError:
        return "other syntax problem"
    return "ok"

print(check_indentation("x = 1\n    y = 2"))
# line 2: unexpected indent
print(check_indentation("x = 1\ny = 2"))
# ok
```

**What this does:** The second line `    y = 2` is indented although no `:`-header introduced a block, so the parser reports `unexpected indent`. Handlers list `IndentationError` before `SyntaxError` (its parent class) so indentation problems get the specific message.

### Example 3: Edge Case

```python
# Dedenting to a level that never existed
source = (
    "if True:\n"
    "        a = 1\n"
    "    b = 2\n"      # 4 spaces: less than 8, but not back to 0
)
try:
    compile(source, "<example>", "exec")
except SyntaxError as e:   # IndentationError IS a SyntaxError
    print(type(e).__name__)  # IndentationError
    print(e.msg)             # unindent does not match any outer indentation level

print(issubclass(IndentationError, SyntaxError))  # True
```

**What this shows:** Every dedent must return to an indentation level already on the block stack; `b = 2` returns to a level (4 spaces) that was never opened, so the parser cannot tell which block it belongs to. The `except SyntaxError` handler catching it demonstrates the subclass relationship.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (specific subclass of `SyntaxError`)

**Similar terms in this pattern:**

1. `SyntaxError` - Parent class: any grammar violation; indentation is one kind
2. `TabError` - Child class: the still-more-specific tabs/spaces inconsistency
3. `ValueError` - Same "Error" compound naming shape
4. `ModuleNotFoundError` - Another specific subclass refining a general error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. The domain word here is "indentation" - the leading whitespace that shifts a line's start inward - and translations must name that typographic concept, coining a careful compound where the language has no established word for it.


---

## Etymology (Brief)

**English Origin:** Latin + Latin-derived

**Root meaning:** "Indent" comes from Latin "indentare" - "to notch, to make tooth-like cuts" (from "dens/dentis," tooth): an indented edge looks like a row of teeth. Typography adopted it for text set in from the margin, as at a paragraph's start. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Python made a radical design choice: the whitespace at the start of a line is not decoration but grammar - blocks are defined by indentation, not by braces `{}` or `begin/end` keywords. `IndentationError` names violations of that rule. No other mainstream language elevates indentation to syntax, which is why many human languages never needed a word for it - and why this translation carries real teaching weight.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`IndentationError` is raised by the parser when a line's leading whitespace breaks Python's block structure rules. In most languages indentation is a readability convention; in Python it is the syntax itself. A compound statement header ending in `:` (after `if`, `for`, `def`, `class`, `try`...) must be followed by a more-indented block; lines at the same indentation belong to the same block; and dedenting must return exactly to a previously established level. The parser tracks these levels on a stack, and the three classic messages correspond to the three ways to violate them: `expected an indented block` (a header with no indented body), `unexpected indent` (indentation with no header to justify it), and `unindent does not match any outer indentation level` (a dedent to a level that was never opened).

Because it subclasses `SyntaxError`, everything true of the parent holds: the error occurs at compile time, before any statement runs; a file cannot catch its own indentation errors; and the exception carries `filename`, `lineno`, `offset`, and `text`. Tools catch it via `compile()`/`exec()` of strings or when importing a broken module, and should list `except IndentationError:` before `except SyntaxError:` so the specific case is reported precisely.

For learners coming from brace-delimited languages, this exception *is* the lesson that Python's whitespace is meaningful. That is why the translated name matters more than usual: a learner who reads the translated `IndentationError` should come away knowing that the spacing at the start of the line - not a bracket, not a keyword - is what the parser rejected. A vague rendering ("format error," "spacing error") squanders the teaching moment.

**Key behaviors:**

1. **Raised at parse time for block-structure violations:** Missing indentation after a `:` header, indentation where none is expected, or a dedent to an unknown level. No code executes; the file (or string) fails to compile.

2. **Subclass of `SyntaxError`:** `except SyntaxError:` catches it; `except IndentationError:` targets just indentation problems. Its own subclass `TabError` covers the tabs-versus-spaces special case.

3. **About leading whitespace only:** Spaces elsewhere in a line (around operators, inside brackets) never raise it. Continuation lines inside unclosed brackets are exempt from indentation rules - a frequent source of confusion when learners see legal "hanging indents."

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain: leading-whitespace structure)
- **Action vs State:** STATE - describes rejected code, not an action
- **Temporal aspect:** Instantaneous - occurs during parsing

### Recommended Form

**Primary recommendation:** Use your language's established typography/computing word for indentation if one exists. Where none exists - true for many languages, because indentation was never a named everyday concept - choose deliberately between (a) a naturalized loanword compound and (b) a coined descriptive compound ("leading-space," "inward-shift"), and document the choice. Do not leave the concept vague: the name must point at the whitespace at the start of the line.

**Forms to AVOID:**

- ❌ Generic "spacing/format error" - loses the specific concept of *leading* whitespace that defines block structure
- ❌ "Margin error" - the margin is the page edge; indentation is the deliberate inward shift from it
- ❌ Verb forms or sentences ("BadlyIndented"-style participles) - exceptions are noun compounds ending with the family error word

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A physical dent or notch in a surface
- ❌ Meaning 2: Paragraph aesthetics - the decorative first-line indent of prose typography
- ❌ Meaning 3: General "formatting" or visual tidiness of code
- ✅ Meaning 4: **STRUCTURAL LEADING WHITESPACE** - the spaces/tabs at the start of a line that define which block the line belongs to

**Example:**

English "indentation" can mean:

1. "An indentation in the metal" (physical dent) ❌
2. "Indent the first line of each paragraph" (prose typography) ❌ Related origin, wrong function
3. "Please clean up the formatting" (cosmetics) ❌
4. The body of `def greet():` must be indented, or `IndentationError` ✅ **This is the Python meaning**

**Your translation should capture meaning #4 - and here is the honest difficulty: in Python the indentation is not decoration but *grammar*. Many languages never lexicalized this concept because handwriting and most printing traditions did not need it named. Choose a word (established, borrowed, or carefully coined) that identifies the inward shift at the line's start, and let the documentation teach that Python gives it structural force.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `IndentationError`, check these translations:**

- [ ] `SyntaxError` - Parent class; must share the family error word and read as its general case
- [ ] `TabError` - Child class; must read as a more specific kind of this error
- [ ] `if` / `for` / `def` / `class` - The block-opening keywords whose bodies indentation defines; documentation phrasing must connect
- [ ] `pass` - The placeholder statement that exists largely to satisfy indentation ("expected an indented block")
- [ ] Editor/tooling vocabulary ("indent", "dedent") in any localized UI strings

**Consistency rule:**

Preserve the three-level hierarchy in one vocabulary: `SyntaxError` (grammar) → `IndentationError` (grammar of leading whitespace) → `TabError` (tabs vs spaces within that). The indentation word chosen here must be reused verbatim in `TabError` documentation and in every tutorial sentence of the form "Python blocks are defined by indentation."


### Functional relationships

**This term works WITH:**

1. **Block headers (`:`) + `IndentationError`**: Every colon-terminated header demands an indented body

```python
compile("if x:\ndo()", "<s>", "exec")   # expected an indented block
```

2. **`except SyntaxError` + `IndentationError`**: Parent handlers catch it; order specific-first

```python
try:
    compile(source, "<s>", "exec")
except IndentationError:
    print("indentation problem")
except SyntaxError:
    print("other grammar problem")
```

**Common pairing:**

```python
# The three classic violations, via compile() of strings
cases = {
    "missing body":   "def f():\nreturn 1",
    "unexpected":     "x = 1\n    y = 2",
    "bad dedent":     "if True:\n        a = 1\n    b = 2",
}
for label, src in cases.items():
    try:
        compile(src, "<demo>", "exec")
    except IndentationError as e:
        print(f"{label}: {e.msg}")
# missing body: expected an indented block ...
# unexpected: unexpected indent
# bad dedent: unindent does not match any outer indentation level

# pass exists to satisfy the indentation requirement
def not_implemented_yet():
    pass    # Without a body line, the def would be an IndentationError

# Continuation lines inside brackets are exempt
totals = [
    1,
        2,      # legal: bracket continuation, not block indentation
    3,
]
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `IndentationError`

- "Indentation" is unevenly lexicalized: established in some languages' technical vocabularies - absent or unsettled in many others
- Where no word exists, the translator must choose between loanword and coinage, and either needs native validation
- The concept is unique to Python among mainstream languages, so the translation *teaches* the concept rather than labeling a familiar one
- Wrong-but-nearby words (margin, spacing, formatting) actively mislead

**For this term:** HARD

**Rationale:** This is one of the highest-stakes translations in the exception set. In brace languages a bad indent is cosmetic; in Python it is a parse failure, and this exception is where learners discover that. Languages with an established indentation term can translate with confidence; for the rest, the compound must be built honestly (loanword + error word, or a coined "inward-shift" compound) and reviewed by a native programmer-linguist. Do not let the name drift toward cosmetics.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LEADING WHITESPACE AS BLOCK STRUCTURE (not margins, not general formatting)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a learner grasp that the spacing at the line's start was rejected?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word as `SyntaxError` translation (it is a subclass)?
- [ ] Indentation word reused in the `TabError` translation and tutorial prose?
- [ ] Coherent with block-keyword (`if`/`def`/`for`) documentation?

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
term: IndentationError
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
