# Python Builtin Function: `compile` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `compile()` function converts Python source code (string) into code object that can be executed by `exec()` or evaluated by `eval()`. Takes three required arguments: source code, filename (for error messages), and mode ('exec', 'eval', or 'single'). Used for dynamic code execution, template systems, and interactive environments like REPL.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Compile and execute code from string
code_string = "print('Hello from compiled code')"
code_object = compile(code_string, '<string>', 'exec')
exec(code_object)  # Output: Hello from compiled code

# Compile expression for evaluation
expr = "2 + 3 * 4"
code_obj = compile(expr, '<string>', 'eval')
result = eval(code_obj)
print(result)  # Output: 14
```

**What this does:** `compile(source, filename, mode)` converts Python source code string into executable code object. The filename argument is used in error messages (use '<string>' for dynamic code). Mode determines how code is treated: 'exec' for statements, 'eval' for expressions.

### Example 2: Common Pattern

```python
# Template system - compile once, execute many times
template = """
name = '{name}'
age = {age}
print(f'{{name}} is {{age}} years old')
"""

# Compile once
code_template = compile(template, '<template>', 'exec')

# Execute multiple times with different data
for person in [('Alice', 30), ('Bob', 25), ('Charlie', 35)]:
code = template.format(name=person[0], age=person[1])
compiled = compile(code, '<template>', 'exec')
exec(compiled)

# Configuration file execution
config_code = """
debug = True
max_connections = 100
timeout = 30
allowed_hosts = ['localhost', '127.0.0.1']
"""

# Compile and execute to populate namespace
config_namespace = {}
compiled_config = compile(config_code, 'config.py', 'exec')
exec(compiled_config, config_namespace)

print(config_namespace['debug'])  # True
print(config_namespace['max_connections'])  # 100

# Interactive single-statement mode
def run_interactive(statement):
try:
code = compile(statement, '<stdin>', 'single')
exec(code)
except SyntaxError as e:
print(f"Syntax error: {e}")

run_interactive("x = 10")
run_interactive("print(x)")  # Output: 10
run_interactive("x + 5")  # Output: 15 (single mode prints expression results)
```

**What this does:** Compile code once, execute multiple times for efficiency. Used in template systems, configuration loaders, and interactive shells. 'single' mode auto-prints expression results like Python REPL. Can execute in specific namespace by passing globals/locals to `exec()`.

### Example 3: Edge Case

```python
# Different modes: exec, eval, single
code_stmt = "x = 10; print(x)"
code_expr = "2 + 3"
code_single = "5 * 6"

# 'exec' mode - for statements
compiled_stmt = compile(code_stmt, '<string>', 'exec')
exec(compiled_stmt)  # Output: 10

# 'eval' mode - for expressions only
compiled_expr = compile(code_expr, '<string>', 'eval')
result = eval(compiled_expr)
print(result)  # Output: 5

# 'single' mode - interactive (prints expression results)
compiled_single = compile(code_single, '<string>', 'single')
exec(compiled_single)  # Output: 30 (auto-printed)

# Error handling - invalid code
try:
compile("x = ", '<string>', 'exec')
except SyntaxError as e:
print(f"Compilation error: {e}")

# Error messages use filename
try:
compile("invalid syntax $$", 'my_script.py', 'exec')
except SyntaxError as e:
print(e)  # Shows: File "my_script.py", line 1

# Compile flags - control compilation features
import __future__
code_with_annotations = "x: int = 5"
compiled = compile(
code_with_annotations,
'<string>',
'exec',
flags=__future__.annotations.compiler_flag
)

# AST mode - get AST instead of code object
import ast
source = "x = 1 + 2"
tree = compile(source, '<string>', 'exec', ast.PyCF_ONLY_AST)
print(type(tree))  # <class '_ast.Module'>

# Bytecode inspection
code_obj = compile("x = 10", '<string>', 'exec')
print(code_obj.co_code)  # Bytecode bytes
print(code_obj.co_names)  # Names used: ('x',)
print(code_obj.co_filename)  # '<string>'

# Multi-line code
multiline = """
def greet(name):
return f"Hello, {name}"

result = greet("World")
print(result)
"""

compiled = compile(multiline, 'script.py', 'exec')
exec(compiled)  # Output: Hello, World
```

**What this shows:** Three modes have different purposes - 'exec' for statements, 'eval' for expressions, 'single' for interactive REPL-like behavior. Filename parameter appears in error messages for debugging. Can compile with flags for future features. Can get AST instead of code object with `ast.PyCF_ONLY_AST` flag. Code objects contain metadata (names, filename, bytecode).

---

## Pattern Classification

**This term is:** CODE TRANSFORMATION FUNCTION (Meta-programming)

**Similar terms in this pattern:**

1. `exec` - Executes compiled code or code strings
2. `eval` - Evaluates compiled expressions or expression strings
3. `ast` - Module for parsing code into Abstract Syntax Trees
4. `__import__` - Dynamic module importing

**Pattern rule:** Meta-programming functions that work with code as data. "compile" is verb indicating transformation process (source → executable). Translations should convey compilation/transformation concept.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "compilare" meaning "to plunder, collect together." In computing, "compile" means to transform source code into executable form - collecting and transforming the pieces into a runnable program.

**Why Python uses this:** "Compile" is standard computer science term for translating source code to executable form. Python compiles source to bytecode. The `compile()` function exposes this compilation step, allowing dynamic compilation of code strings at runtime.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `compile()` function takes Python source code as a string and converts it into a code object that Python's virtual machine can execute. This is the same process Python does automatically when you run a .py file, but `compile()` lets you do it manually with dynamic code strings.

Signature: `compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1)`. Source is code string, filename appears in tracebacks (use descriptive name or '<string>'), mode determines interpretation: 'exec' compiles statements, 'eval' compiles single expression, 'single' compiles single interactive statement.

Common use cases: template systems (compile template once, execute many times), configuration files (compile and execute config code), dynamic code generation, implementing custom interpreters, REPL implementations, optimization (pre-compile frequently executed code), testing (compile code to check syntax without executing).

**Key behaviors:**

1. **Three modes with different purposes:** 'exec' mode for statements/multiple lines (returns None when executed). 'eval' mode for single expression (returns expression value). 'single' mode for interactive statements (auto-prints expression results like Python REPL).

2. **Returns code object, not result:** `compile()` returns code object, doesn't execute it. Use `exec(code_obj)` to execute statements or `eval(code_obj)` to evaluate expressions. Separating compilation from execution enables caching compiled code.

3. **Filename in error messages:** The filename parameter appears in exceptions and tracebacks. Use descriptive names ('<template>', 'config.py') for better debugging. Standard convention: angle brackets for dynamic code ('<string>'), file path for actual files.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (action - transforming source to executable)
- **Action vs State:** ACTION - performs compilation transformation
- **Temporal aspect:** One-time action producing result

### Recommended Form

**Primary recommendation:** Use verb form meaning "to compile" or "to transform/translate" code. Standard CS term across languages. Should convey transformation from source to executable.

**Forms to AVOID:**

- ❌ Noun form - compile is action (verb), not thing (noun)
- ❌ Using "collect" without "compile" context - computer science meaning specific
- ❌ Using "build" or "construct" - different concept than compile

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (but CS meaning is standard)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Compile a list/collection (gather together) - general meaning
- ❌ Meaning 2: Compile a report (assemble information) - document creation
- ✅ Meaning 3: Compile source code (transform to executable) - **This is the Python meaning**

**Example:**

English "compile" can mean:

1. Compile a list ("compile a list of names") ❌
2. Compile a book ("compile essays into anthology") ❌
3. Compile source code (transform to executable) ✅ **This is the Python meaning**

**Your translation should capture meaning #3 (CS compilation), NOT the others.**

Use standard CS term for compilation in target language.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `compile`, check these translations:**

- [ ] `exec` - Executes compiled code, related action
- [ ] `eval` - Evaluates compiled expressions, related action
- [ ] Similar verb forms if pattern exists

**Consistency rule:**

Meta-programming functions that work with code (`compile`, `exec`, `eval`) should use compatible verb forms. If using infinitives, use infinitives consistently. All should feel like code manipulation actions.


---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Standard CS term with established translations
- "Compile" universal in programming
- Clear verb form in most languages
- Well-documented concept
- **AI confidence should be HIGH with context**

**For this term:** MEDIUM

**Rationale:** "Compile" is standard CS terminology with direct translations in most languages. Challenge is ensuring verb form (not noun) and using established CS term (not general "collect/gather"). Once verified, translation is straightforward.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Use standard CS term for compilation, not general dictionary definition of "compile." Check CS education materials in target language.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures CODE COMPILATION concept?
- [ ] Understood as source-to-executable transformation?
- [ ] CS meaning, not general "collect" meaning?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Infinitive or appropriate verb form?
- [ ] Standard CS term for compilation?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Compatible verb form with exec/eval?
- [ ] Matches CS terminology in target language?
- [ ] Aligns with programming vocabulary?

### 4. Usability

- [ ] Short (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear meaning in CS context?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: compile
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
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
