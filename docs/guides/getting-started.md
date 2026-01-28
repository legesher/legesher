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
legesher translate hola_mundo.py --from es --to en --output hello_world.py
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
legesher translate hello_world.py --from en --to es --output hola_mundo_nuevo.py
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

Legesher currently supports 26 languages (all experimental, awaiting community validation):

| Code | Language   | Native Name      | RTL |
|------|------------|------------------|-----|
| ar   | Arabic     | العربية          | Yes |
| da   | Danish     | Dansk            | No  |
| de   | German     | Deutsch          | No  |
| el   | Greek      | Ελληνικά         | No  |
| en   | English    | English          | No  |
| es   | Spanish    | Español          | No  |
| fi   | Finnish    | Suomi            | No  |
| fr   | French     | Français         | No  |
| he   | Hebrew     | עברית            | Yes |
| hi   | Hindi      | हिन्दी           | No  |
| hu   | Hungarian  | Magyar           | No  |
| id   | Indonesian | Bahasa Indonesia | No  |
| it   | Italian    | Italiano         | No  |
| ja   | Japanese   | 日本語           | No  |
| ko   | Korean     | 한국어           | No  |
| ms   | Malay      | Bahasa Melayu    | No  |
| nl   | Dutch      | Nederlands       | No  |
| no   | Norwegian  | Norsk            | No  |
| pl   | Polish     | Polski           | No  |
| pt   | Portuguese | Português        | No  |
| ru   | Russian    | Русский          | No  |
| sv   | Swedish    | Svenska          | No  |
| th   | Thai       | ไทย              | No  |
| tr   | Turkish    | Türkçe           | No  |
| vi   | Vietnamese | Tiếng Việt       | No  |
| zh   | Chinese    | 中文             | No  |

Want to create your own? See the [Translation Guide](translation-guide.md).

### Version-Aware Language Packs

Language packs are **version-aware** - they know which Python version you're using:

Language packs support Python 3.10 through 3.14 with version inheritance. The translate command
automatically uses the appropriate translations for your installed Python version.

If you need a specific Python version's keywords, configure it during project setup:

```bash
legesher init --python-version 3.10
```

## CLI Commands Overview

Here are the main Legesher commands. For full details, run `legesher --help`.

### translate: Convert Between Languages

The primary command you'll use:

```bash
# Basic translation
legesher translate input.py --from es --to en --output output.py

# Translate to stdout (no file created)
legesher translate input.py --from es --to en

# Batch translate a directory
legesher translate src/ --from es --to en --output dist/
```

Options:

- `--from`: Source language code (default: en)
- `--to`: Target language code (required)
- `--output`: Output file or directory (stdout if omitted)

### run: Execute Native Language Code Directly

Skip the translation step and run your code in one command:

```bash
# Run a Spanish Python file directly
legesher run hola_mundo.py --lang es

# Run with arguments passed to the script
legesher run hola_mundo.py --lang es --args "--verbose"
```

### init: Set Up a Legesher Project

Initialize Legesher configuration for your project:

```bash
# Interactive setup (recommended)
legesher init

# Pre-select languages and skip prompts
legesher init -l es -l ar --git --ai-context
```

This creates a `.legesher/config.yml` file with your project settings.

### git: Transparent Translation in Git

Store code in English in git while working in your native language:

```bash
# Set up git filters for Spanish
legesher git setup --language es

# Check current git filter status
legesher git status
```

See [Git Workflow Guide](git-workflow.md) for details.

### metadata: Track Translation History

View and manage translation metadata for your project:

```bash
# List tracked files
legesher metadata list

# Show metadata for a specific file
legesher metadata show hola_mundo.py
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
legesher translate calculadora.py --from es --to en --output calculator.py
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

Your source code has a syntax error. Check that your code uses valid keywords
from the language pack. You can verify installed packs with:

```bash
pip show legesher-i18n-python-es
```

### "Unsupported Python version"

The language pack doesn't support your Python version. Check available versions:

```bash
pip show legesher-i18n-python-es
```

Re-initialize your project with a supported version:

```bash
legesher init --python-version 3.11
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
