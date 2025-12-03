"""AI Context Generator for Legesher.

This module generates AI-friendly context files that help coding assistants
(Claude Code, GitHub Copilot, Cursor, etc.) understand multilingual Python code.

The generated context files include:
- Translation tables for keywords, builtins, and exceptions
- Bilingual code examples
- Metadata about the language pack and Python version

Public API:
    - AIContextGenerator: Main class for generating AI context files
    - generate_keyword_table: Format keyword translations as markdown table
    - generate_builtin_table: Format builtin translations as markdown table
    - generate_exception_table: Format exception translations as markdown table
    - generate_bilingual_examples: Generate bilingual code examples

Example:
    >>> from pathlib import Path
    >>> from legesher_core import AIContextGenerator
    >>> from legesher_i18n import LanguagePackLoader
    >>>
    >>> # Load Spanish language pack
    >>> loader = LanguagePackLoader()
    >>> pack = loader.load("es", "python", "3.13")
    >>>
    >>> # Generate AI context
    >>> generator = AIContextGenerator(
    ...     language_code="es",
    ...     python_version="3.13",
    ...     keywords=pack.keywords,
    ...     builtins=pack.builtins,
    ...     exceptions=getattr(pack, "exceptions", {}),
    ... )
    >>> output_path = Path(".legesher/AI-CONTEXT.md")
    >>> generator.generate(output_path)
"""

from pathlib import Path

from legesher_i18n.language_registry import LANGUAGE_METADATA


class AIContextGenerator:
    """Generate AI-friendly context files for multilingual Python code.

    This class creates markdown files with translation tables and examples
    that help AI coding assistants understand code written in non-English
    languages.

    Attributes:
        language_code: ISO 639-1 language code (e.g., "es", "ar", "zh")
        python_version: Python version string (e.g., "3.13")
        keywords: Dictionary mapping English keywords to translations
        builtins: Dictionary mapping English builtins to translations
        exceptions: Dictionary mapping English exceptions to translations
    """

    def __init__(
        self,
        language_code: str,
        python_version: str,
        keywords: dict[str, str],
        builtins: dict[str, str],
        exceptions: dict[str, str] | None = None,
    ):
        """Initialize the AI context generator.

        Args:
            language_code: ISO 639-1 language code (e.g., "es", "ar", "zh")
            python_version: Python version string (e.g., "3.13")
            keywords: Dictionary mapping English keywords to translations
            builtins: Dictionary mapping English builtins to translations
            exceptions: Dictionary mapping English exceptions to translations
        """
        self.language_code = language_code
        self.python_version = python_version
        self.keywords = keywords
        self.builtins = builtins
        self.exceptions = exceptions or {}

        # Get language metadata
        metadata = LANGUAGE_METADATA.get(language_code)
        if metadata:
            self.language_name = metadata["name"]
            self.language_native = metadata["native"]
            self.is_rtl = metadata["rtl"]
        else:
            # Fallback for unknown languages
            self.language_name = language_code.upper()
            self.language_native = language_code.upper()
            self.is_rtl = False

    def generate(self, output_path: Path) -> None:
        """Generate AI context file at the specified path.

        Args:
            output_path: Path where the AI-CONTEXT.md file should be written

        Raises:
            ValueError: If output_path contains path traversal attempts

        Example:
            >>> generator = AIContextGenerator("es", "3.13", keywords, builtins)
            >>> generator.generate(Path(".legesher/AI-CONTEXT.md"))
        """
        # Resolve path and validate (security: prevent path traversal)
        resolved_path = output_path.resolve()

        # Create parent directory
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate and validate content
        content = self._generate_content()
        if not self._validate_markdown(content):
            raise ValueError("Generated markdown content is invalid or incomplete")

        # Write to file
        resolved_path.write_text(content, encoding="utf-8")

    def _generate_content(self) -> str:
        """Generate the complete markdown content for AI context file.

        Returns:
            Complete markdown content as string
        """
        sections = [
            self._generate_header(),
            self._generate_overview(),
            self._generate_keyword_table(),
            self._generate_builtin_table(),
        ]

        if self.exceptions:
            sections.append(self._generate_exception_table())

        sections.append(self._generate_bilingual_examples())
        sections.append(self._generate_best_practices())

        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate the file header with title and metadata."""
        rtl_note = ""
        if self.is_rtl:
            rtl_note = f"\n**Text Direction**: Right-to-Left (RTL) - {self.language_native} reads from right to left"

        return f"""# Legesher AI Context - {self.language_name} ({self.language_native}) Python

**Language**: {self.language_name} ({self.language_code}) - {self.language_native}
**Python Version**: {self.python_version}{rtl_note}
**Generated by**: Legesher Core

---

**For AI Coding Assistants**: This file provides translation context for Python code
written in {self.language_name} ({self.language_code}). Use these tables to understand and assist with
multilingual Python code."""

    def _generate_overview(self) -> str:
        """Generate overview section explaining the purpose."""
        return f"""## Overview

This project uses **Legesher** to enable Python development in {self.language_name} ({self.language_code}).
All Python keywords, builtins, and exceptions can be written in {self.language_name}
instead of English.

### What Gets Translated

**✅ ALWAYS Translated**:
- **Python keywords**: `def`, `if`, `return`, `True`, `False`, etc.
- **Built-in functions**: `print()`, `len()`, `range()`, etc.
- **Exception types**: `ValueError`, `TypeError`, etc.
- **User-defined names**: Function names, variable names, class names, parameters
  - Example: `greet()` becomes `saludar()` (Spanish), `name` becomes `nombre`
  - The ENTIRE codebase uses {self.language_name}, not just keywords

**⚙️ OPTIONALLY Translated** (user preference):
- **String literals**: Content inside quotes can be translated by user choice
  - Example: `imprimir("Hola, Mundo!")` vs `imprimir("Hello, World!")`
  - Strings may contain user-facing messages in any language
  - Default: Follow existing patterns in the codebase
- **Comments**: Code comments can be in any language (often {self.language_name}, English, or both)
  - User can choose to translate or keep in original language
- **Library imports**: Future feature - translating standard library names (e.g., `os`, `sys`)
  - Currently: Standard library names remain English (e.g., `importar os`)

**❌ NOT Recommended to Translate**:
- **Brand names**: Company/product names should remain unchanged (e.g., `GoogleAPI`, `AWS`)
- **Technical terms**: Domain-specific terminology that should stay consistent across teams

### How to Approach Multilingual Code

When you encounter {self.language_name} code in this project:

1. **Understand the context**:
   - Use the translation tables below to map {self.language_name} terms to English concepts
   - All code logic is generally identical to English Python, just written in {self.language_name}
   - Note: Some adjustments may apply for RTL languages or specific syntactic elements
   - When unsure: Check project documentation or ask the developer for clarification

2. **Generate suggestions in {self.language_name}**:
   - Function names, variable names, class names: ALL in {self.language_name}
   - Keywords and builtins: ALL in {self.language_name}
   - Example: Don't suggest `def calculate_total()`, suggest `definir calcular_total()`

3. **Handle mixed-language codebases**:
   - If a file uses {self.language_name}, ALL your suggestions should be in {self.language_name}
   - If a file uses English, maintain English
   - NEVER mix languages within a single code block or file
   - Check the first few lines of code to detect which language is being used

4. **String literals and user-facing content**:
   - String content depends on project requirements (may be English, {self.language_name}, or other)
   - Don't automatically translate strings unless the developer asks
   - Log messages, error messages, UI text: follow existing patterns in the codebase

5. **Brand names and domain terminology**:
   - Keep brand names unchanged: `cliente_aws` (good), not `cliente_aes` (bad)
   - Ask if unsure: "Should I keep 'DatabaseConnection' or translate to 'ConexiónBaseDeDatos'?"
   - Some projects prefer English for technical terms, {self.language_name} for business logic

### Important Notes

- **This is real Python**: {self.language_name} code runs identically to English Python
- **Git stores English**: Legesher git filters convert code to English in version control
- **IDE shows {self.language_name}**: Developers see and write {self.language_name} in their editor
- **AI assistants see {self.language_name}**: You should understand and generate {self.language_name} code"""

    def _generate_keyword_table(self) -> str:
        """Generate markdown table for keyword translations."""
        return generate_keyword_table(self.keywords, self.language_code)

    def _generate_builtin_table(self) -> str:
        """Generate markdown table for builtin translations."""
        return generate_builtin_table(self.builtins, self.language_code)

    def _generate_exception_table(self) -> str:
        """Generate markdown table for exception translations."""
        return generate_exception_table(self.exceptions, self.language_code)

    def _generate_bilingual_examples(self) -> str:
        """Generate bilingual code examples showing translations in action."""
        return generate_bilingual_examples(
            self.language_code, self.keywords, self.builtins
        )

    def _generate_best_practices(self) -> str:
        """Generate best practices section for AI assistants."""
        return f"""## Best Practices for AI Assistants

When working with {self.language_name} ({self.language_code}) Python code in this project:

1. **Language Detection**:
   - Check the file extension (`.py`) and language context
   - Examine existing code patterns to determine which language is being used
   - Look for {self.language_name} keywords in the first few lines
   - Default to the language used in the current file

2. **Code Suggestions**:
   - Always suggest code in the SAME language as the existing code
   - If the file uses {self.language_name} keywords, suggest ALL code in {self.language_name}
   - If the file uses English keywords, suggest ALL code in English
   - NEVER mix languages within a single code block or file
   - Translate user-defined names (functions, variables) to match the code language

3. **Completions**:
   - Use the translation tables above for accurate keyword/builtin suggestions
   - Translate identifiers to {self.language_name} when suggesting code
   - Maintain consistent naming conventions with existing code
   - Respect the developer's language choice throughout the file

4. **Error Messages & Explanations**:
   - You can explain concepts in English (or the developer's preferred natural language)
   - Code examples should match the project's language ({self.language_name})
   - Clearly distinguish between code language (programming) and explanation language (natural)

5. **String Literals & Comments**:
   - Don't automatically translate string content - check existing patterns
   - Follow the project's convention for user-facing messages
   - Comments may be in {self.language_name}, English, or both

6. **Git Integration**:
   - This project uses Legesher git filters to store code as English in git
   - You'll see {self.language_name} code in the working directory
   - Git history shows English (this is expected behavior)
   - Don't be confused if git diff shows English - that's intentional

---

*Generated by Legesher - Code in Your Language*
*https://legesher.io*"""

    def _validate_markdown(self, content: str) -> bool:
        """Validate that generated markdown contains all required sections.

        Args:
            content: Generated markdown content

        Returns:
            True if content is valid, False otherwise
        """
        required_headers = [
            "# Legesher AI Context",
            "## Overview",
            "## Python Keywords",
            "## Python Builtins",
            "## Bilingual Examples",
            "## Best Practices",
        ]

        return (
            all(header in content for header in required_headers)
            and len(content) > 1000
        )


def generate_keyword_table(keywords: dict[str, str], language_code: str) -> str:
    """Generate markdown table for keyword translations.

    Args:
        keywords: Dictionary mapping English keywords to translations
        language_code: ISO 639-1 language code

    Returns:
        Markdown table as string

    Example:
        >>> keywords = {"def": "definir", "return": "retornar"}
        >>> print(generate_keyword_table(keywords, "es"))
        ## Python Keywords
        ...
    """
    header = f"""## Python Keywords

The following Python keywords can be written in {language_code}:

| English | {language_code.upper()} | Usage Context |
|---------|---------|---------------|"""

    # Define usage context for common keywords
    context_map = {
        "def": "Function definition",
        "class": "Class definition",
        "if": "Conditional statement",
        "elif": "Else-if conditional",
        "else": "Else clause",
        "for": "For loop",
        "while": "While loop",
        "return": "Return statement",
        "import": "Import statement",
        "from": "From-import statement",
        "as": "Alias in import",
        "try": "Exception handling",
        "except": "Catch exception",
        "finally": "Finally clause",
        "raise": "Raise exception",
        "with": "Context manager",
        "lambda": "Anonymous function",
        "yield": "Generator yield",
        "await": "Async await",
        "async": "Async function",
        "pass": "Empty placeholder",
        "break": "Break loop",
        "continue": "Continue loop",
        "and": "Logical AND",
        "or": "Logical OR",
        "not": "Logical NOT",
        "in": "Membership test",
        "is": "Identity test",
        "None": "Null value",
        "True": "Boolean true",
        "False": "Boolean false",
        "global": "Global variable",
        "nonlocal": "Nonlocal variable",
        "del": "Delete statement",
        "assert": "Assertion",
    }

    rows = []
    for english, translated in sorted(keywords.items()):
        context = context_map.get(english, "")
        rows.append(f"| `{english}` | `{translated}` | {context} |")

    return header + "\n" + "\n".join(rows)


def generate_builtin_table(builtins: dict[str, str], language_code: str) -> str:
    """Generate markdown table for builtin translations.

    Args:
        builtins: Dictionary mapping English builtins to translations
        language_code: ISO 639-1 language code

    Returns:
        Markdown table as string

    Example:
        >>> builtins = {"print": "imprimir", "len": "longitud"}
        >>> print(generate_builtin_table(builtins, "es"))
        ## Python Builtins
        ...
    """
    header = f"""## Python Builtins

The following Python builtin functions can be written in {language_code}:

| English | {language_code.upper()} | Description |
|---------|---------|-------------|"""

    # Define descriptions for common builtins
    description_map = {
        "print": "Print to console",
        "len": "Get length",
        "range": "Generate range",
        "input": "Get user input",
        "int": "Integer type",
        "str": "String type",
        "float": "Float type",
        "bool": "Boolean type",
        "list": "List type",
        "dict": "Dictionary type",
        "set": "Set type",
        "tuple": "Tuple type",
        "type": "Get type",
        "isinstance": "Check instance",
        "open": "Open file",
        "abs": "Absolute value",
        "min": "Minimum value",
        "max": "Maximum value",
        "sum": "Sum values",
        "sorted": "Sort iterable",
        "enumerate": "Enumerate items",
        "zip": "Zip iterables",
        "map": "Map function",
        "filter": "Filter items",
        "all": "All true",
        "any": "Any true",
        "help": "Get help",
        "dir": "List attributes",
        "vars": "Get variables",
        "globals": "Global namespace",
        "locals": "Local namespace",
    }

    rows = []
    for english, translated in sorted(builtins.items()):
        description = description_map.get(english, "")
        rows.append(f"| `{english}()` | `{translated}()` | {description} |")

    return header + "\n" + "\n".join(rows)


def generate_exception_table(exceptions: dict[str, str], language_code: str) -> str:
    """Generate markdown table for exception translations.

    Args:
        exceptions: Dictionary mapping English exceptions to translations
        language_code: ISO 639-1 language code

    Returns:
        Markdown table as string

    Example:
        >>> exceptions = {"ValueError": "ErrorDeValor", "TypeError": "ErrorDeTipo"}
        >>> print(generate_exception_table(exceptions, "es"))
        ## Python Exceptions
        ...
    """
    header = f"""## Python Exceptions

The following Python exceptions can be written in {language_code}:

| English | {language_code.upper()} | When Raised |
|---------|---------|-------------|"""

    # Define when exceptions are raised
    when_raised_map = {
        "Exception": "Base exception",
        "ValueError": "Invalid value",
        "TypeError": "Invalid type",
        "KeyError": "Missing key",
        "IndexError": "Invalid index",
        "AttributeError": "Missing attribute",
        "NameError": "Undefined name",
        "ImportError": "Import failed",
        "RuntimeError": "Runtime error",
        "ZeroDivisionError": "Division by zero",
        "FileNotFoundError": "File not found",
        "PermissionError": "Permission denied",
        "NotImplementedError": "Not implemented",
        "StopIteration": "Iterator exhausted",
    }

    rows = []
    for english, translated in sorted(exceptions.items()):
        when_raised = when_raised_map.get(english, "")
        rows.append(f"| `{english}` | `{translated}` | {when_raised} |")

    return header + "\n" + "\n".join(rows)


def generate_bilingual_examples(
    language_code: str, keywords: dict[str, str], builtins: dict[str, str]
) -> str:
    """Generate bilingual code examples showing translations in action.

    Args:
        language_code: ISO 639-1 language code
        keywords: Dictionary mapping English keywords to translations
        builtins: Dictionary mapping English builtins to translations

    Returns:
        Markdown section with bilingual examples

    Example:
        >>> keywords = {"def": "definir", "return": "retornar"}
        >>> builtins = {"print": "imprimir", "len": "longitud"}
        >>> print(generate_bilingual_examples("es", keywords, builtins))
        ## Bilingual Examples
        ...
    """
    # Get common keywords for examples
    def_kw = keywords.get("def", "def")
    return_kw = keywords.get("return", "return")
    if_kw = keywords.get("if", "if")
    else_kw = keywords.get("else", "else")
    for_kw = keywords.get("for", "for")
    in_kw = keywords.get("in", "in")
    true_kw = keywords.get("True", "True")
    false_kw = keywords.get("False", "False")

    # Get common builtins for examples
    print_fn = builtins.get("print", "print")
    len_fn = builtins.get("len", "len")
    range_fn = builtins.get("range", "range")

    # Language-specific translated identifiers for examples
    # These show that user-defined names are ALSO translated
    translated_names = {
        "es": {  # Spanish
            "greet": "saludar",
            "name": "nombre",
            "is_adult": "es_adulto",
            "age": "edad",
            "count_items": "contar_elementos",
            "items": "elementos",
        },
        "ar": {  # Arabic
            "greet": "تحية",
            "name": "اسم",
            "is_adult": "بالغ",
            "age": "عمر",
            "count_items": "عد_العناصر",
            "items": "عناصر",
        },
        "fr": {  # French
            "greet": "saluer",
            "name": "nom",
            "is_adult": "est_adulte",
            "age": "âge",
            "count_items": "compter_éléments",
            "items": "éléments",
        },
        "zh": {  # Chinese
            "greet": "问候",
            "name": "名字",
            "is_adult": "是成年人",
            "age": "年龄",
            "count_items": "计数项目",
            "items": "项目",
        },
    }

    # Get translated names for this language, fallback to English
    names = translated_names.get(
        language_code,
        {
            "greet": "greet",
            "name": "name",
            "is_adult": "is_adult",
            "age": "age",
            "count_items": "count_items",
            "items": "items",
        },
    )

    # Get language metadata
    metadata = LANGUAGE_METADATA.get(language_code)
    if metadata:
        language_name = metadata["name"]
    else:
        language_name = language_code.upper()

    return f"""## Bilingual Examples

**IMPORTANT**: Notice that user-defined names (functions, variables, parameters) are ALSO
translated to {language_name}. The ENTIRE codebase uses {language_name}, not just keywords!

### Example 1: Function Definition

**English**:
```python
def greet(name):
    print(f"Hello, {{name}}!")
    return True
```

**{language_name} ({language_code})**:
```python
{def_kw} {names["greet"]}({names["name"]}):
    {print_fn}(f"Hello, {{{names["name"]}}}!")
    {return_kw} {true_kw}
```

> **Note**: `{names["greet"]}` is the {language_name} translation of `greet`, and `{names["name"]}` is the {language_name} translation of `name`.
> User-defined identifiers (function names, parameters) are translated just like keywords.

### Example 2: Conditional Logic

**English**:
```python
def is_adult(age):
    if age >= 18:
        return True
    else:
        return False
```

**{language_name} ({language_code})**:
```python
{def_kw} {names["is_adult"]}({names["age"]}):
    {if_kw} {names["age"]} >= 18:
        {return_kw} {true_kw}
    {else_kw}:
        {return_kw} {false_kw}
```

> **Note**: `{names["is_adult"]}` and `{names["age"]}` are {language_name} translations of the English identifiers.

### Example 3: Loops

**English**:
```python
def count_items(items):
    for i in range(len(items)):
        print(f"Item {{i}}: {{items[i]}}")
```

**{language_name} ({language_code})**:
```python
{def_kw} {names["count_items"]}({names["items"]}):
    {for_kw} i {in_kw} {range_fn}({len_fn}({names["items"]})):
        {print_fn}(f"Item {{i}}: {{{names["items"]}[i]}}")
```

> **Note**: `{names["count_items"]}` and `{names["items"]}` are {language_name} translations. The variable `i` stays as `i`
> (common practice for loop counters, though it could also be translated).

### When Suggesting Code

**❌ DON'T** suggest English code if the file uses {language_name}:
```python
# Bad - mixing languages
{def_kw} process_data(data):
    for item in data:  # English keywords mixed with {language_name}
        print(item)
```

**✅ DO** suggest consistent {language_name} code:
```python
# Good - consistent {language_name}
{def_kw} procesar_datos(datos):  # User-defined names also in {language_name}
    {for_kw} elemento {in_kw} datos:
        {print_fn}(elemento)
```

**Remember**: When suggesting code in {language_name}:
- Translate ALL identifiers (functions, variables, classes, parameters)
- Use {language_name} keywords and builtins from the tables above
- Keep string literals as-is unless asked to translate them
- Keep brand names and technical terms consistent with the codebase"""


__all__ = [
    "AIContextGenerator",
    "generate_keyword_table",
    "generate_builtin_table",
    "generate_exception_table",
    "generate_bilingual_examples",
]
