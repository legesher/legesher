# Python Builtin: `SyntaxError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`SyntaxError` is raised when Python's parser rejects code because it does not follow the grammar of the language - the code cannot even begin to run. The exception carries `filename`, `lineno`, `offset`, and `text` locating the problem, and since Python 3.10 its messages have become far more precise (naming unclosed brackets, suggesting missing colons or commas).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# The parser rejects invalid code at compile time.
# Syntax errors can't be triggered by running bad code inline -
# the file wouldn't compile - so we hand the parser a string:
compile("if True\n    print('hi')", "<example>", "exec")
# Raises SyntaxError: expected ':'   (Python 3.10+ wording)
```

**What this does:** `compile()` asks the parser to turn source text into runnable code. The string is missing the colon after `if True`, so parsing fails with `SyntaxError` before any execution happens. In Python 3.10+ the message states exactly what the parser expected (`expected ':'`, at the line and offset of the missing token); older versions say the generic `invalid syntax`.

### Example 2: Common Pattern

```python
# Validating user-supplied code (a teaching tool, REPL, or plugin loader)
def check_snippet(source):
    try:
        compile(source, "<user-code>", "exec")
    except SyntaxError as e:
        return f"line {e.lineno}, column {e.offset}: {e.msg}"
    return "ok"

print(check_snippet("total = 1 +"))
# line 1, column ...: invalid syntax
print(check_snippet("x = 1"))
# ok
```

**What this does:** Tools that accept code as data - editors, graders, notebook kernels - compile it first and catch `SyntaxError` to report problems. The exception's attributes (`lineno`, `offset`, `msg`) let the tool point at the exact place the parser gave up, instead of just saying "bad code."

### Example 3: Edge Case

```python
# A file cannot catch its OWN syntax errors: parsing happens before running.
# try/except only works when the bad code arrives as a string or module.
bad = "results = [1, 2\nprint(results)"

try:
    compile(bad, "demo.py", "exec")
except SyntaxError as e:
    print(e.filename)  # demo.py
    print(e.lineno)    # 1  - the line where the problem starts
    print(e.offset)    # column position (1-based)
    print(e.text)      # the offending source line
# Python 3.10+ message: '[' was never closed
# - it points at the OPENING bracket, not the confusing later line
```

**What this shows:** Why wrapping your own top-level code in `try/except SyntaxError` is futile: the whole file is parsed before any statement runs, so the error fires before the `try` exists. The attributes pinpoint the failure, and 3.10+ messages locate the true cause (the unclosed `[`) rather than the line where the parser finally got confused.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (compile-time, raised by the parser)

**Similar terms in this pattern:**

1. `IndentationError` - Subclass: the specific syntax failure of incorrect indentation
2. `TabError` - Sub-subclass: inconsistent tabs/spaces in indentation
3. `NameError` - Contrast: a runtime failure; the code parsed fine but a name is missing
4. `ValueError` - Contrast: runtime failure of content, not form

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. For `SyntaxError`, the domain word should be your language's *linguistics* term for syntax - the grammar-of-sentences concept taught in school - not an improvised "code form" phrase.


---

## Etymology (Brief)

**English Origin:** Greek via Latin + Latin-derived

**Root meaning:** "Syntax" comes from Greek "syntaxis" - "arranging together" ("syn-" together + "taxis" arrangement). Since antiquity it has named the branch of grammar governing how words combine into valid sentences. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Programming languages borrowed "syntax" from linguistics deliberately: a language - human or programming - has a grammar, and the parser is its grammarian. `SyntaxError` says your program is not a well-formed "sentence" of Python. This borrowed-from-linguistics lineage is a gift to translators: most languages already have a school-grammar word for syntax.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`SyntaxError` is raised when the parser cannot make grammatical sense of source code. It is fundamentally different from runtime exceptions like `TypeError` or `KeyError`: those occur while a program runs; `SyntaxError` occurs *before* the program exists as runnable code. Python reads the entire file (or string), builds a parse tree according to the language grammar, and only then executes. A missing colon, an unclosed bracket, a stray keyword - any of these stops compilation, so not a single statement of that file runs.

This timing has a practical consequence learners trip over: you cannot catch a `SyntaxError` raised by the file that contains the `try` statement, because the error happens while parsing, before the `try` is ever executed. The exception *is* catchable when the bad code arrives at runtime as data - through `compile()`, `exec()`, `eval()`, or importing a broken module - which is exactly how editors, graders, and REPLs report syntax problems to their users.

The exception object is unusually informative: `msg` (the parser's explanation), `filename`, `lineno` and `offset` (1-based line and column), and `text` (the offending source line); Python 3.10 added `end_lineno` and `end_offset` marking the span's end. Python 3.10 also overhauled the messages themselves: instead of a bare `invalid syntax`, the parser now reports `'[' was never closed`, `expected ':'`, or `Perhaps you forgot a comma?` - and points at the true origin of the problem (for example the opening bracket) rather than the later line where parsing collapsed. When translating teaching material, note that learners on different Python versions see different messages for the same mistake.

**Key behaviors:**

1. **Raised at compile time, not runtime:** Parsing precedes execution, so a syntax error in a file prevents the whole file from running - including any `try/except` inside it. Only code compiled from strings or imported modules can have its syntax errors caught.

2. **Carries precise location data:** `filename`, `lineno`, `offset`, `text` (plus `end_lineno`/`end_offset` since 3.10) let tools point at the exact span the parser rejected. The standard traceback prints the line with a `^` marker (a `^~~~` range since 3.10).

3. **Messages improved sharply in 3.10:** Modern Python names the missing token or unclosed bracket and often suggests the fix. `IndentationError` and `TabError` are subclasses, so `except SyntaxError:` catches indentation problems too.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain: the language's grammar rules)
- **Action vs State:** STATE - describes a condition (ungrammatical code), not an action
- **Temporal aspect:** Instantaneous - occurs during parsing, before any execution

### Recommended Form

**Primary recommendation:** Use your language's native *linguistics* word for syntax - the one taught in school grammar classes - plus the family's error word. Most languages have this term, it is instantly meaningful to every educated speaker, and it preserves the human-language/programming-language parallel that the English name relies on.

**Forms to AVOID:**

- ❌ Transliterating English "syntax" when a native grammar term exists - wastes the one word the reader already knows from school
- ❌ Vague "writing error" or "format error" phrases - syntax is specifically the grammar of valid combinations, not spelling or style
- ❌ Verb forms or sentences ("invalid writing" phrasings) - exceptions are noun compounds

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (though narrower than most)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Prose style or diction ("her elegant syntax" in literary criticism)
- ❌ Meaning 2: Spelling and punctuation mechanics
- ❌ Meaning 3: Semantics - what code means or whether it behaves correctly
- ✅ Meaning 4: **THE GRAMMAR OF THE PROGRAMMING LANGUAGE** - the formal rules for how tokens may combine into valid programs

**Example:**

English "syntax" in context:

1. "The poet's unusual syntax" (literary style) ❌
2. "Check your spelling and punctuation" (mechanics) ❌
3. "The code runs but gives wrong answers" (semantics - not a SyntaxError) ❌
4. `if True print('hi')` rejected by the parser ✅ **This is the Python meaning**

**Your translation should capture meaning #4: code that violates the language's grammar and therefore cannot be parsed at all. The deep parallel - programming languages have grammar exactly as human languages do - is the pedagogical heart of this term; a native school-grammar word makes that parallel land for free.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `SyntaxError`, check these translations:**

- [ ] `IndentationError` - Subclass; must read as a specific kind of this error (same error word)
- [ ] `TabError` - Sub-subclass; same requirement one level down
- [ ] `compile` - The builtin that surfaces syntax errors from strings; documentation vocabulary must match
- [ ] `eval` / `exec` - The other compile-and-run builtins that raise it
- [ ] `NameError` - The contrast case (runtime, not parse-time); documentation must keep the boundary crisp

**Consistency rule:**

`SyntaxError` heads a three-level hierarchy: `SyntaxError` → `IndentationError` → `TabError`. All three must share the family error word, and the subclass names must read as increasingly specific kinds of syntax problems. The word chosen here for "syntax" becomes the anchor the other two are explained against ("an indentation error is a syntax error about...").


### Functional relationships

**This term works WITH:**

1. **`compile()` + `SyntaxError`**: The honest way to demonstrate and catch parse failures

```python
try:
    code = compile(source_text, filename, "exec")
except SyntaxError as e:
    report(e.lineno, e.offset, e.msg)
```

2. **`import` + `SyntaxError`**: Importing a module with broken syntax raises it at import time

```python
import broken_module  # SyntaxError from the module's own source
```

**Common pairing:**

```python
# A minimal linter: compile, catch, report
def lint(source, filename="<input>"):
    try:
        compile(source, filename, "exec")
    except SyntaxError as e:
        pointer = " " * ((e.offset or 1) - 1) + "^"
        return f"{e.filename}:{e.lineno}: {e.msg}\n  {e.text or ''}\n  {pointer}"
    return None

print(lint("def f(:\n    pass"))

# eval/exec raise SyntaxError for malformed strings too
try:
    eval("2 +")
except SyntaxError:
    print("incomplete expression")

# The hierarchy: indentation problems are syntax problems
try:
    compile("if True:\nprint('x')", "<s>", "exec")
except SyntaxError as e:            # Catches IndentationError as well
    print(type(e).__name__)          # IndentationError

# Version note: the same mistake, different messages
# 3.9:   SyntaxError: invalid syntax
# 3.10+: SyntaxError: expected ':'
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `SyntaxError`

- Most languages already possess a native linguistics term for syntax - the main task is finding and using it
- The trap is dilution: settling for "writing error" or "format error" when a precise grammar word exists
- Must anchor a three-level hierarchy (`SyntaxError` → `IndentationError` → `TabError`)
- The compile-time vs runtime distinction must survive in surrounding documentation

**For this term:** MEDIUM

**Rationale:** This is the rare exception name where school education has done the translator's work: syntax is taught as a grammar concept in most literate traditions. Confidence should be high wherever such a term exists and is used in local CS education; the difficulty rises only for languages whose grammar tradition lacks a distinct syntax word, where a careful choice between "grammar" and a coined compound is needed.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures GRAMMAR-OF-THE-LANGUAGE violation (not spelling, style, or meaning)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a reader connect it to their school grammar classes?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word as `TypeError`, `ValueError` translations?
- [ ] Anchors `IndentationError` and `TabError` as its visible subclasses?
- [ ] Vocabulary matches `compile`/`eval`/`exec` documentation?

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
term: SyntaxError
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
