# Python Builtin: `exec` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`exec()` executes Python statements from a string or code object, unlike `eval()` which only handles expressions, powerful but dangerous with untrusted input.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic statement execution
exec("x = 5")
print(x)  # Output: 5

exec("print('Hello from exec')")  # Output: Hello from exec

# Multiple statements
code = """
y = 10
z = 20
result = y + z
"""
exec(code)
print(result)  # Output: 30
```

**What this does:** `exec()` executes Python statements from a string, creating variables, running functions, and performing any valid Python operations.

### Example 2: Common Pattern

```python
# Execute with custom namespace
code = """
def greet(name):
return f"Hello, {name}!"

message = greet("Alice")
"""

namespace = {}
exec(code, namespace)
print(namespace['message'])  # Output: Hello, Alice!
print(namespace['greet']('Bob'))  # Output: Hello, Bob!

# Isolated execution
safe_globals = {"__builtins__": {}}
safe_locals = {"x": 10}
exec("result = x * 2", safe_globals, safe_locals)
print(safe_locals['result'])  # Output: 20
```

**What this does:** Execute code in controlled namespaces to isolate variables and restrict access to builtins, providing some security sandboxing.

### Example 3: Edge Case

```python
# SECURITY WARNING: exec is dangerous
dangerous_code = "__import__('os').system('ls')"
# exec(dangerous_code)  # DON'T RUN - executes system commands!

# exec vs eval
exec("x = 5")  # Works - statements allowed
print(x)  # Output: 5

# eval("x = 5")  # SyntaxError - statements not allowed

# eval returns value, exec doesn't
result_eval = eval("2 + 2")
print(result_eval)  # Output: 4

result_exec = exec("print(2 + 2)")
# Output: 4 (printed)
# BUT: result_exec is None

print(result_exec)  # Output: None (exec returns nothing)

# Use compile for better control
code_obj = compile("print('Compiled')", '<string>', 'exec')
exec(code_obj)  # Output: Compiled
```

**What this shows:** `exec()` is even more dangerous than `eval()` because it can execute any Python statement including assignments, imports, loops, and function definitions. Always returns None. Use `compile()` for pre-compilation. Never use with untrusted input.

---

## Pattern Classification

**This term is:** CODE EXECUTION FUNCTION (Dynamic execution)

**Similar terms in this pattern:**

1. `eval` - Evaluates Python expressions (not statements)
2. `compile` - Compiles code to bytecode
3. `__import__` - Dynamic module importing

**Pattern rule:** Dynamic code execution functions should clearly indicate they execute code. Must distinguish `exec` (statements) from `eval` (expressions).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `eval` | evaluar | تقييم | 求值 | मूल्यांकन |
| `compile` | compilar | تجميع | 编译 | संकलन |
| `exec` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Short for "execute"

**Root meaning:** From Latin "exsequi" (to follow out, carry out, accomplish). "Execute" means to carry out or perform an action.

**Why Python uses this:** In programming, "execute" means to run code. Python's `exec()` executes statements dynamically from strings or code objects. The name parallels Unix's `exec()` system call and is universal in computing for "run this code."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`exec()` takes a string or code object containing Python statements, parses it, compiles it to bytecode, and executes it. Unlike `eval()` which only handles expressions, `exec()` can execute any Python statement: assignments, loops, function definitions, class definitions, imports, etc.

The function always returns None - it's about side effects (creating variables, calling functions) not return values. By default it executes in the current scope, but you can provide custom global and local namespaces to isolate execution and restrict access to dangerous builtins.

`exec()` is extremely dangerous with untrusted input - even more so than `eval()`. It can create arbitrary code, import modules, access the filesystem, execute system commands, etc. Modern Python applications avoid `exec()` entirely or use heavily restricted sandboxed namespaces. There's rarely a legitimate use case that can't be solved more safely with proper code design.

**Key behaviors:**

1. **Statements, not just expressions:** Can execute assignments, loops, function definitions - any valid Python statement, unlike `eval()`.
2. **Always returns None:** Designed for side effects, not return values. If you need a return value, use `eval()` with expressions.
3. **Extreme security risk:** Can execute any Python code including system calls, file operations, and imports. Never use with untrusted input.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Function name (action verb)
- **Action vs State:** ACTION - performs execution
- **Temporal aspect:** Instantaneous action (executes code)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | ejecutar, exécuter (to execute) |
| Germanic (de, nl, sv) | Infinitive verb | ausführen, uitvoeren |
| Slavic (ru, pl, uk) | Infinitive verb | выполнить, wykonać |
| Arabic | Verbal noun (masdar) | تنفيذ (tanfīdh - execution) |
| Chinese | Verb | 执行 (zhíxíng - execute) |
| Hindi | Infinitive verb | निष्पादन (niṣpādan - execute) |

**Primary recommendation:** Use a verb meaning "to execute," "to run," or "to perform." Should clearly convey running/executing code, and should be distinguishable from `eval`.

**Forms to AVOID:**

- ❌ Same term as `eval` - must be distinguishable
- ❌ Noun forms - this is an action (function), not a thing
- ❌ Vague terms that don't convey code execution

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `ejecutar` or `exec` (borrowed)
- **Form:** Infinitive verb
- **Why it works:** "Ejecutar" means "to execute/run" in Spanish, clearly different from "evaluar" (eval), distinguishing statements from expressions

**Arabic:**

- **Translation:** `تنفيذ` (tanfīdh - execute/implement)
- **Form:** Verbal noun (masdar)
- **Why it works:** Technical term for execution, clearly distinct from "تقييم" (evaluate), appropriate for running code

**Chinese:**

- **Translation:** `执行` (zhíxíng - execute)
- **Form:** Verb
- **Why it works:** Standard CS term for execution, clearly distinct from "求值" (evaluate), widely used

**Hindi:**

- **Translation:** `निष्पादन` (niṣpādan - execute) or `चलाना` (chalānā - run)
- **Form:** Verbal noun/infinitive
- **Why it works:** Formal term for execution, distinct from evaluation, professional

### ❌ Common Translation Mistakes

**Mistake 1: Same as eval**

- **Wrong:** Using same translation as `eval`
- **Why wrong:** Must distinguish exec (statements) from eval (expressions)
- **Right:** Different verbs - execute vs evaluate

**Mistake 2: Too vague**

- **Wrong:** `hacer` (Spanish - "to do")
- **Why wrong:** Too generic, doesn't convey specific concept of code execution
- **Right:** `ejecutar` (execute specifically)

**Mistake 3: Noun instead of verb**

- **Wrong:** `ejecución` (Spanish - "execution" noun)
- **Why wrong:** Function names should be verbs (infinitive), not nouns
- **Right:** `ejecutar` (infinitive verb)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (in broader context), but Python meaning is specific

**Python-specific meaning:**

✅ **Python meaning:** Execute Python statements from a string or code object.

In general English, "execute" can mean carry out a plan, put to death, or perform an action. In Python/programming, it specifically means "run code/statements." Your translation should use the technical computing sense (run/execute code).

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `exec`, check these translations:**

- [ ] `eval` - MUST be distinguishable (exec=statements, eval=expressions)
- [ ] `compile` - Related to code compilation/execution
- [ ] `run` - May share similar meaning in some contexts

**Consistency rule:**

`exec` and `eval` MUST be clearly distinguishable because they serve different purposes:
- `exec` = execute statements (no return value)
- `eval` = evaluate expressions (returns value)

Recommended pattern:
- `exec` → "execute/run" (action-oriented)
- `eval` → "evaluate/compute" (value-oriented)

**Example:**

✅ **Consistent and distinguishable:**

- `eval` → `evaluar` (evaluate)
- `exec` → `ejecutar` (execute)
- Clear distinction ✅

❌ **Not distinguishable:**

- `eval` → `ejecutar`
- `exec` → `ejecutar`
- Same translation ❌

### Functional relationships

**This term works WITH:**

1. **`exec` + string statements**: Executes string as code
2. **`exec` vs `eval`**: exec for statements, eval for expressions
3. **`compile` + `exec`**: Can exec compiled code objects

**Common pairing:**

```python
# exec for statements (no return)
exec("x = 5")

# eval for expressions (returns value)
result = eval("2 + 2")

# compile + exec
code_obj = compile("print('hi')", '<string>', 'exec')
exec(code_obj)
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Security-critical function
- Must distinguish from `eval`
- Technical concept (statement execution)
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While "execute" is common, using it correctly in technical sense and distinguishing from `eval` requires understanding Python's execution model. The security implications make this high-stakes. Must verify distinction from `eval` is clear.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Conveys "execute statements/code"?
- [ ] Clearly different from `eval` (expressions)?
- [ ] Would programmers understand this runs code?

### 2. Linguistic Correctness

- [ ] Verb form (infinitive)?
- [ ] Appropriate for "running/executing code"?
- [ ] Technical register?

### 3. Consistency

- [ ] CLEARLY distinguishable from `eval` translation?
- [ ] Compatible with execution/code-running terminology?
- [ ] Matches CS terminology in target language?

### 4. Usability

- [ ] Concise (1 word preferred)?
- [ ] Clear meaning?
- [ ] Recognizable to programmers?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues?

---

## Translation Output Format

**Your translation:**

```yaml
term: exec
language: {es|ar|zh|hi}
translation: {your_translation}
form: {infinitive_verb}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you chose a verb meaning "execute" or "run code," emphasizing statement execution (not expression evaluation). MUST mention distinction from `eval`.}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Need to verify distinction from `eval`, check CS terminology for "execute statements"}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
