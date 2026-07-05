# Python Builtin: `TabError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`TabError` is a subclass of `IndentationError` raised when a file's indentation mixes tab characters and spaces inconsistently - in a way whose meaning would depend on how wide a tab is displayed. Python 3 refuses to guess and rejects the code at parse time with `inconsistent use of tabs and spaces in indentation`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Syntax-family errors fire at parse time, so we compile a string.
# Line 2 is indented with a TAB, line 3 with 8 SPACES:
source = "if True:\n\tx = 1\n        y = 2"
compile(source, "<example>", "exec")
# Raises TabError: inconsistent use of tabs and spaces in indentation
```

**What this does:** Both indented lines look aligned in *some* editors - but only if a tab renders as 8 columns. Under a different tab width they would sit at different depths, changing which block each line belongs to. Because the structure depends on display settings, Python raises `TabError` instead of guessing.

### Example 2: Common Pattern

```python
# A pre-flight check for pasted or student-submitted code
def check_indentation_style(source):
    try:
        compile(source, "<check>", "exec")
    except TabError as e:
        return f"line {e.lineno}: mixed tabs and spaces - pick one"
    except SyntaxError:
        return "other syntax problem"
    return "ok"

pasted = "def f():\n\tx = 1\n        return x"
print(check_indentation_style(pasted))
# line 3: mixed tabs and spaces - pick one
```

**What this does:** Mixed indentation typically arrives via copy-paste between editors with different settings. Compiling the text and catching `TabError` (before its parents `IndentationError`/`SyntaxError`) lets a tool give the precise diagnosis - the fix is to re-indent the file uniformly, with spaces per PEP 8.

### Example 3: Edge Case

```python
# Consistent tabs are legal; consistent spaces are legal; mixing is not
tabs_only = "if True:\n\tx = 1\n\ty = 2"
compile(tabs_only, "<ok>", "exec")      # Compiles fine

spaces_only = "if True:\n    x = 1\n    y = 2"
compile(spaces_only, "<ok>", "exec")    # Compiles fine

# The full hierarchy: TabError -> IndentationError -> SyntaxError
print(issubclass(TabError, IndentationError))  # True
print(issubclass(TabError, SyntaxError))       # True

mixed = "if True:\n\tx = 1\n        y = 2"
try:
    compile(mixed, "<demo>", "exec")
except IndentationError as e:   # Parent class catches TabError
    print(type(e).__name__)      # TabError
```

**What this shows:** `TabError` is not about tabs being wrong - a file indented entirely with tabs is legal Python. The offense is *inconsistency*: mixing the two whitespace kinds so block depth becomes ambiguous. The `issubclass` checks make the three-level hierarchy concrete.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (most specific member of the syntax family)

**Similar terms in this pattern:**

1. `IndentationError` - Parent class: any incorrect indentation
2. `SyntaxError` - Grandparent class: any grammar violation
3. `UnicodeError` - Another exception named after a character-level concern
4. `ValueError` - Same "Error" compound naming shape

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. The domain word here is "tab" - the tabulator character/key - for which most languages use either a loanword or a "tabulation" derivative; translations must name that character, not furniture or browser tabs.


---

## Etymology (Brief)

**English Origin:** Abbreviation of Latin-derived word + Latin-derived

**Root meaning:** "Tab" abbreviates "tabulator," from Latin "tabula" (board, writing tablet, table). Typewriters had a tabulator key that jumped the carriage to preset column stops for typing tables; computing inherited both the key and the invisible character (U+0009) it produces. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name points at the culprit character. A tab has no fixed width - it displays as 2, 4, or 8 columns depending on settings - so indentation mixing tabs with spaces can mean different block structures on different screens. Python 2 guessed (treating a tab as 8 spaces); Python 3 made the ambiguity a hard error and named it after the character that causes it.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`TabError` is the most specific member of the syntax-error family: it fires when the parser finds indentation that mixes tab characters and spaces *inconsistently* - meaning the code's block structure would differ depending on how many columns a tab is assumed to span. In Python, indentation is grammar, so ambiguous indentation is ambiguous grammar. Rather than silently pick a tab width (and possibly run code the author never wrote), Python 3 rejects the file at compile time with `inconsistent use of tabs and spaces in indentation`.

The error is emphatically not "you used a tab." A file indented entirely with tabs compiles happily; so does a file indented entirely with spaces (PEP 8 recommends 4 spaces). Trouble starts when the two mix such that comparing two lines' indentation requires knowing a tab's width - most commonly after copy-pasting code between editors configured differently, or editing someone else's file with your own editor defaults. Because the offending characters are invisible, the bug is bewildering to beginners: two lines that look identical are not. Editors' "show whitespace" and "convert tabs to spaces" features exist for exactly this.

In the hierarchy, `TabError` subclasses `IndentationError`, which subclasses `SyntaxError` - each level a more specific diagnosis. Handlers should be ordered most-specific first. Like all parse-time errors, it cannot be caught by the file that contains it; it surfaces through `compile()`, `exec()`, or importing the broken module, carrying the standard location attributes (`filename`, `lineno`, `offset`, `text`).

**Key behaviors:**

1. **Raised only for inconsistent mixing:** All-tabs and all-spaces files are both legal. The parser errors when indentation comparisons would depend on tab width - the structure is display-dependent, hence ambiguous.

2. **Most specific class in its chain:** `TabError` → `IndentationError` → `SyntaxError` → `Exception`. Any parent's `except` clause catches it; write `except TabError:` first when the distinction matters for the message you show.

3. **Compile-time, invisible-character error:** It fires during parsing (nothing runs), and the cause is characters the reader cannot see. Diagnosis needs a whitespace-revealing editor or a re-indent; the fix is uniform indentation, conventionally 4 spaces.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain: the tab character)
- **Action vs State:** STATE - describes rejected code, not an action
- **Temporal aspect:** Instantaneous - occurs during parsing

### Recommended Form

**Primary recommendation:** Use your language's established word for the tab key/character - usually a "tabulation" derivative or the naturalized loanword "tab" - plus the family error word. Prefer the character-level term ("tab character" rather than a label/UI-tab word) so the name cannot be misread as browser tabs or UI tabs.

**Forms to AVOID:**

- ❌ The browser/UI "tab" word - a completely different object that happens to share the English name
- ❌ Naming tabs as inherently wrong ("ErrorPorUsarTabulador" - "error for using tab") - tabs alone are legal; the offense is inconsistent mixing
- ❌ Sentences describing the mix ("ErrorDeMezclaDeTabuladoresYEspacios") - accurate but far too long for an identifier; the docs explain, the name labels

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES - "tab" is heavily overloaded

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A browser or dialog tab (UI element)
- ❌ Meaning 2: A restaurant tab (running bill: "put it on my tab")
- ❌ Meaning 3: The physical tab of a file folder or a can ("pull tab")
- ✅ Meaning 4: **THE TAB CHARACTER U+0009** - the tabulator character produced by the Tab key, used (dangerously) in indentation

**Example:**

English "tab" can mean:

1. "Open a new tab in your browser" (UI) ❌
2. "The bar kept a tab for us" (bill) ❌
3. "Lift the tab to open" (physical flap) ❌
4. A `\t` character in a line's indentation triggering `TabError` ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the invisible tabulator character. Choose the word your language uses for the *keyboard key/character* (a "tabulation" derivative in most languages), never the browser-tab word - in several languages those are entirely different terms, and picking the wrong one makes the exception unintelligible.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `TabError`, check these translations:**

- [ ] `IndentationError` - Parent class; this must read as its more specific case (same error word, compatible domain vocabulary)
- [ ] `SyntaxError` - Grandparent class; family error word must match
- [ ] Escape sequence `\t` and the word for "space character" in documentation - the tab/space contrast must use stable vocabulary
- [ ] Editor/tooling UI strings ("convert tabs to spaces") in any localized materials
- [ ] `UnicodeError` family - other character-level exception names should treat "character" vocabulary consistently

**Consistency rule:**

The three-level chain must be visible in translation: the syntax-error name ⊃ the indentation-error name ⊃ the tab-error name - same error word throughout, each name narrowing the domain. The tab word chosen here must be the same one documentation uses when it says "indent with spaces, not tabs."


### Functional relationships

**This term works WITH:**

1. **Indentation + the `\t` character**: The error's raw material

```python
compile("if x:\n\ta = 1\n        b = 2", "<s>", "exec")  # TabError
```

2. **`except` ordering + the class chain**: Most specific first

```python
try:
    compile(source, "<s>", "exec")
except TabError:
    print("mixed tabs and spaces")
except IndentationError:
    print("other indentation problem")
except SyntaxError:
    print("other grammar problem")
```

**Common pairing:**

```python
# Diagnosing invisible characters in a suspect line
line = "\tx = 1"
print([c for c in line if c in ("\t", " ")])   # ['\t'] - there's the tab

# A repair utility: normalize indentation to spaces
def detab(source, width=4):
    return "\n".join(
        ln.replace("\t", " " * width) for ln in source.splitlines()
    )

mixed = "if True:\n\ta = 1\n        b = 2"
try:
    compile(mixed, "<before>", "exec")
except TabError:
    fixed = detab(mixed, 8)
    compile(fixed, "<after>", "exec")   # Now compiles
    print("re-indented with spaces")

# Both pure styles compile; only the mix fails
compile("while x:\n\tstep()", "<tabs>", "exec")        # ok
compile("while x:\n    step()", "<spaces>", "exec")    # ok
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `TabError`

- Inherits `IndentationError`'s difficulty: the underlying concept (structural indentation) is not universally lexicalized
- "Tab" itself is a loanword or "tabulation" derivative nearly everywhere - the native-word option rarely exists
- Severe false-friend risk: many languages have a *different* established word for browser tabs
- The name must not imply tabs are forbidden - a subtle connotation to control in a two-word compound

**For this term:** HARD

**Rationale:** The pieces look easy - most languages do have a settled tab-key word - but the term sits at the bottom of the hierarchy whose upper levels (`IndentationError`) are the genuinely hard translation, and it must stay vocabulary-compatible with them. Add the browser-tab false friend and the "tabs are illegal" connotation trap, and native review is warranted even when the compound seems obvious.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the TAB CHARACTER (tabulator, U+0009) - not browser tabs, bills, or flaps?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Avoids implying tab characters are inherently forbidden?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word as `IndentationError` and `SyntaxError` translations?
- [ ] Reads as the most specific member of that chain?
- [ ] Tab word matches the one used for the Tab key/`\t` in local documentation?

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
term: TabError
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
