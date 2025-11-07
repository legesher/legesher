# Getting Started with Legesher

Welcome to Legesher! This guide will walk you through your first experience coding in your native language and translating
between languages. By the end, you'll understand how Legesher works and be ready to integrate it into your workflow.

## What You'll Learn

- How to write Python code in Spanish
- How to translate code between languages
- What gets translated (and what doesn't)
- How to use the Legesher CLI
- What language packs are and how they work

This tutorial takes about 15 minutes and assumes you've already installed Legesher. If you haven't, see the
[Installation Guide](installation.md).

## Your First Translation

Let's start with a classic: Hello World in Spanish.

### Step 1: Create a Python File in Spanish

Create a new file called `hola_mundo.py`:

```python
# Mi primer programa en Legesher
definir hola():
    imprimir("Hola, mundo!")
    devolver Verdadero

si __nombre__ == "__principal__":
    resultado = hola()
    si resultado:
        imprimir("Programa completado con exito")
```

Notice how natural this looks! You're using Spanish keywords like `definir` (define/def), `imprimir` (print),
`devolver` (return), and `si` (if).

### Step 2: Translate to English

Now let's translate this code to English so Python can run it:

```bash
legesher translate hola_mundo.py --source es --target en --output hello_world.py
```

Legesher will create `hello_world.py` with the translated code:

```python
# Mi primer programa en Legesher
def hola():
    print("Hola, mundo!")
    return True

if __nombre__ == "__principal__":
    resultado = hola()
    if resultado:
        print("Programa completado con exito")
```

### Step 3: Run the Translated Code

Now you can run the English version with Python:

```bash
python hello_world.py
```

Expected output:

```text
Hola, mundo!
Programa completado con exito
```

Success! Your Spanish code ran through Python.

### Step 4: Translate Back to Spanish

Want to convert English code back to Spanish? Easy:

```bash
legesher translate hello_world.py --source en --target es --output hola_mundo_nuevo.py
```

This creates a Spanish version from the English code. You can go back and forth as much as you need.

## Understanding the Translation

Let's break down what happened in our example.

### What Gets Translated

Legesher translates **Python keywords and built-in functions**:

| Spanish        | English  | Type          |
|----------------|----------|---------------|
| definir        | def      | Keyword       |
| imprimir       | print    | Built-in      |
| devolver       | return   | Keyword       |
| si             | if       | Keyword       |
| Verdadero      | True     | Built-in      |

These are defined in the **language pack** for Spanish (es).

### What Stays the Same

Legesher preserves your **code's meaning**:

- **Variable names:** `hola`, `resultado`, `__nombre__` stay exactly as written
- **String literals:** `"Hola, mundo!"` remains unchanged
- **Comments:** `# Mi primer programa en Legesher` stays in Spanish
- **Logic:** The program structure and flow stay identical

This is important: Legesher translates the **programming language**, not your code's content or intent.

### Why This Matters

You can:

- Write code in your native language
- Collaborate with developers who use different languages
- Store code in git in any language (see [Git Workflow](git-workflow.md))
- Switch between languages without losing meaning

## Language Pack Basics

Language packs are what make translation possible. Let's understand how they work.

### What Are Language Packs

A language pack maps Python keywords and built-ins to another language:

```python
# Spanish language pack (simplified)
{
    "def": "definir",
    "if": "si",
    "else": "sino",
    "return": "devolver",
    "print": "imprimir",
    "True": "Verdadero",
    "False": "Falso"
}
```

Language packs are installed as Python packages:

- `legesher-i18n-python-es` - Spanish
- `legesher-i18n-python-ar` - Arabic

### Available Languages

Currently, Legesher supports:

| Code | Language | Status     |
|------|----------|------------|
| en   | English  | Built-in   |
| es   | Spanish  | Available  |
| ar   | Arabic   | Available  |

More languages coming soon! You can also create your own (see [Translation Guide](translation-guide.md)).

### Version-Aware Language Packs

Language packs are **version-aware** - they know which Python version you're using:

```bash
# Python 3.8 - no walrus operator
legesher translate code.py --source es --target en --python-version 3.8

# Python 3.10 - includes match/case statements
legesher translate code.py --source es --target en --python-version 3.10
```

If you don't specify a version, Legesher uses your current Python version:

```bash
python --version  # Python 3.11.5
legesher translate code.py --source es --target en  # Uses 3.11 keywords
```

This ensures your translations are accurate for your Python environment.

## CLI Commands Overview

Let's explore the main Legesher commands.

### translate: Convert Between Languages

The main command you'll use:

```bash
# Basic translation
legesher translate input.py --source es --target en --output output.py

# Shorter version (auto-detect language)
legesher translate input.py --target en -o output.py

# Translate to stdout (no file created)
legesher translate input.py --source es --target en

# Batch translate a directory
legesher translate src/ --source es --target en --output dist/
```

Options:

- `--source`, `-s`: Source language code (auto-detected if omitted)
- `--target`, `-t`: Target language code (required)
- `--output`, `-o`: Output file or directory (stdout if omitted)
- `--python-version`: Python version for translation (default: current)
- `--in-place`: Overwrite the input file

### config: Manage Settings

Configure Legesher for your project:

```bash
# Set default language for your project
legesher config set language es

# Set Python version
legesher config set python-version 3.11

# View current configuration
legesher config list

# View all available settings
legesher config --help
```

Configuration is stored in `.legesher.json` in your project root:

```json
{
  "language": "es",
  "python_version": "3.11",
  "git_integration": true
}
```

### info: Check Language Packs

See what language packs are installed:

```bash
# List all installed language packs
legesher info

# Show details for a specific language
legesher info es
```

Example output:

```text
Installed Language Packs:
  es (Spanish) - v1.0.0
    Python versions: 3.8, 3.9, 3.10, 3.11, 3.12
    Keywords: 35
    Built-ins: 68

  ar (Arabic) - v1.0.0
    Python versions: 3.8, 3.9, 3.10, 3.11, 3.12
    Keywords: 35
    Built-ins: 68
```

## Try a More Complex Example

Let's write something more interesting in Spanish:

```python
# Calculadora simple
definir sumar(a, b):
    """Suma dos numeros"""
    devolver a + b

definir restar(a, b):
    """Resta dos numeros"""
    devolver a - b

definir dividir(a, b):
    """Divide dos numeros"""
    si b == 0:
        lanzar ValorError("No se puede dividir por cero")
    devolver a / b

# Pruebas
si __nombre__ == "__principal__":
    imprimir("5 + 3 =", sumar(5, 3))
    imprimir("5 - 3 =", restar(5, 3))

    intentar:
        resultado = dividir(10, 0)
    excepto ValorError como e:
        imprimir("Error:", e)
```

Save this as `calculadora.py`, then translate and run:

```bash
legesher translate calculadora.py --source es --target en --output calculator.py
python calculator.py
```

Output:

```text
5 + 3 = 8
5 - 3 = 2
Error: No se puede dividir por cero
```

Notice how Legesher handles:

- Function definitions with docstrings
- Exception handling (`intentar`/try, `excepto`/except, `lanzar`/raise)
- Built-in exceptions (`ValorError`/ValueError)
- Variable names in any language

## Next Steps

Congratulations! You've learned the basics of Legesher. Here's where to go next:

### Integrate with Git

Learn how to store code in one language (like English) while working in another:

- [Git Workflow Guide](git-workflow.md) - Automatic translation on commit/checkout
- Set up git filters for seamless integration

### Use the Language Server

Get real-time translation in your IDE:

- [Language Server Documentation](../language-server/README.md)
- VS Code extension setup
- IntelliSense in your native language

### Create Your Own Language Pack

Want to code in a language we don't support yet?

- [Translation Guide](translation-guide.md) - Create a language pack
- [Language Pack Specification](../architecture/language-pack-spec.md)
- Contribute to the Legesher ecosystem

### Advanced Features

Explore more Legesher capabilities:

- **Version-aware translations:** Handle different Python versions
- **Batch processing:** Translate entire projects at once
- **Custom mappings:** Override default translations
- **CI/CD integration:** Automate translation in your pipeline

### Join the Community

- [GitHub Discussions](https://github.com/legesher/legesher/discussions) - Ask questions
- [Contributing Guide](../../CONTRIBUTING.md) - Help build Legesher
- [Code of Conduct](../../CODE_OF_CONDUCT.md) - Our community values

## Troubleshooting

### "Language pack not found"

Install the language pack:

```bash
pip install legesher-i18n-python-es  # Spanish
pip install legesher-i18n-python-ar  # Arabic
```

### "Translation failed: Syntax error"

Your source code has a syntax error. Check that it's valid in the source language:

```bash
# For Spanish code
legesher validate hola_mundo.py --language es
```

### "Unsupported Python version"

The language pack doesn't support your Python version. Check available versions:

```bash
legesher info es
```

Then specify a supported version:

```bash
legesher translate code.py --source es --target en --python-version 3.11
```

## Summary

You now know how to:

- Write code in Spanish (or Arabic)
- Translate between languages
- Run translated code
- Use the Legesher CLI
- Understand what gets translated

Legesher gives you the power to code in your native language while maintaining compatibility with the Python ecosystem.
The next step is integrating it into your daily workflow with git and your IDE.

Happy coding in your language!
