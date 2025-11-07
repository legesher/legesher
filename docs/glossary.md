# Technical Glossary

This glossary provides clear definitions of technical terms used throughout the Legesher
project. It's designed for beginners and non-native English speakers.

**Tip:** Use your browser's search (Ctrl+F or Cmd+F) to quickly find specific terms.

---

## A

### AST (Abstract Syntax Tree)

**Definition:** A tree structure that represents the grammatical structure of source code.
Each node in the tree represents a construct in the code (like a function, variable, or loop).

**In Legesher:** We use ASTs to understand code structure during translation. This allows us
to translate keywords and identifiers while preserving the logic and meaning of the code.

**Example:** The code `if x > 5:` becomes a tree with an "if statement" node that has
children for the condition (`x > 5`) and the body of the if block.

---

## B

### Bidirectional Translation

**Definition:** The ability to translate in both directions - from language A to language B
and from language B back to language A without losing information.

**In Legesher:** You can write code in Spanish, save it as English in Git, then open it
again in Spanish. Or a teammate can open the same file in Arabic. Everyone works in their
preferred language.

**Example:** Spanish `si edad >= 18:` translates to English `if age >= 18:` and can
translate back to Spanish exactly as it was originally written.

### Built-in Functions

**Definition:** Functions that come pre-packaged with a programming language and are
always available without importing additional code.

**In Legesher:** We translate built-in function names like `print()`, `len()`, and `range()`
so developers can use them in their native language. Spanish speakers write `imprimir()`
instead of `print()`.

**Example:** Python's `print("hello")` becomes `imprimir("hola")` in Spanish.

---

## C

### CHANGELOG

**Definition:** A file that contains a chronologically ordered list of notable changes for
each version of a project.

**In Legesher:** We maintain a CHANGELOG.md file following the Keep a Changelog format.
This helps users understand what's new, what's changed, and what's been fixed in each release.

### Clean Filter (Git)

**Definition:** A Git filter that runs when files are staged for commit. It transforms
file content before storing it in the Git repository.

**In Legesher:** The clean filter translates your native language code to English before
saving to Git. This ensures all code in the repository is stored in a standard format.

**Example:** When you commit Spanish code, the clean filter automatically converts
`si x > 5:` to `if x > 5:` before storing it in Git.

### CLI (Command Line Interface)

**Definition:** A text-based interface where users type commands to interact with software,
rather than using a graphical interface with buttons and menus.

**In Legesher:** Our CLI tool (`legesher`) allows developers to translate files, manage
language packs, and configure settings using terminal commands like `legesher translate`.

### Conventional Commits

**Definition:** A specification for writing clear, standardized commit messages that follow
a specific format: `type(scope): description`.

**In Legesher:** We use Conventional Commits to maintain a clean Git history and
automatically generate CHANGELOGs. Examples: `feat: add Arabic support`, `fix: resolve
translation bug`.

### Cultural Comments

**Definition:** Code comments that include cultural context, idioms, or explanations that
are specific to a particular language or culture.

**In Legesher:** We preserve comments in the developer's original language, allowing them
to use culturally-relevant explanations and metaphors that make sense in their language.

**Example:** A Spanish comment might reference "tortilla de patatas" when explaining a
layered data structure, which is more meaningful than a direct English translation.

---

## G

### Git Filter

**Definition:** A mechanism in Git that allows you to transform file content automatically
when files are checked in (clean filter) or checked out (smudge filter).

**In Legesher:** Git filters are the core technology that enables our bidirectional
translation. They translate between your native language and English automatically as you
work.

---

## I

### IDE (Integrated Development Environment)

**Definition:** Software that provides comprehensive tools for programming, including a
code editor, debugger, and build tools all in one application.

**In Legesher:** We integrate with IDEs like VS Code, Zed, and PyCharm to provide
real-time translation, autocomplete, and error messages in your native language.

**Example:** VS Code with the Legesher extension shows Spanish keywords while you type and
provides Spanish error messages.

### Incremental Parsing

**Definition:** A parsing technique that updates only the changed portions of a syntax tree
rather than re-parsing the entire file.

**In Legesher:** We use Tree-sitter's incremental parsing to provide fast, real-time
translation as you type. Only the lines you change are re-translated, keeping the editor
responsive.

### IntelliSense

**Definition:** A code-completion feature that provides intelligent suggestions while typing,
including function names, variable names, and documentation.

**In Legesher:** We extend IntelliSense to show suggestions in your native language. When
you type `impr` in Spanish, IntelliSense suggests `imprimir()` with Spanish documentation.

---

## K

### Keywords

**Definition:** Reserved words in a programming language that have special meaning and cannot
be used as variable names. Examples include `if`, `for`, `while`, and `return`.

**In Legesher:** We translate all Python keywords to their equivalents in supported
languages. Spanish uses `si` for `if`, `para` for `for`, and `mientras` for `while`.

---

## L

### Language Pack

**Definition:** A package that contains all the translation data, rules, and metadata needed
to support programming in a specific language.

**In Legesher:** Each language pack (like `legesher-i18n-python-es` for Spanish) contains
keyword translations, built-in function names, and documentation. Developers install the
language pack for their language.

**Example:** The Spanish language pack maps `if` to `si`, `print` to `imprimir`, and
includes Spanish error messages.

### Language Server Protocol (LSP)

**Definition:** A standardized protocol for providing programming language features
(autocomplete, go-to-definition, error checking) to any text editor or IDE.

**In Legesher:** We implement LSP to provide Legesher features across multiple editors.
One LSP implementation works with VS Code, Zed, and any other LSP-compatible editor.

### Lossless Translation

**Definition:** Translation that preserves all information from the original, allowing
perfect reconstruction of the source material.

**In Legesher:** Our translation is lossless - no code, comments, or formatting is lost
when translating between languages. Your code translates perfectly in both directions.

---

## M

### Metadata

**Definition:** Data that provides information about other data. Examples include file
creation dates, author names, or file sizes.

**In Legesher:** Language packs include metadata like supported Python versions, author
information, and translation completeness. This helps users choose the right language pack.

### MLCP (Multilingual Code Protocol)

**Definition:** Legesher's open specification for representing and exchanging multilingual
source code. It defines how code in different languages is structured and shared.

**In Legesher:** MLCP is our standard format for language packs, translation rules, and
multilingual code files. It ensures compatibility across tools and allows community
contributions.

**Example:** A language pack's JSON file follows MLCP specifications, ensuring any
MLCP-compatible tool can use it.

### Monorepo

**Definition:** A software development approach where code for multiple projects or packages
is stored in a single Git repository.

**In Legesher:** Our monorepo contains all Legesher packages (core, i18n, CLI, VS Code
extension) in one repository. This simplifies development and ensures version compatibility.

---

## P

### Package Manager

**Definition:** A tool that automates installing, updating, and managing software packages
and their dependencies.

**In Legesher:** We distribute Legesher through PyPI (Python's package manager). Users
install with `pip install legesher` and the package manager handles all dependencies.

### Pylance

**Definition:** Microsoft's Python language server that provides rich IntelliSense, type
checking, and code analysis for Python in VS Code.

**In Legesher:** Our VS Code extension integrates with Pylance to provide language-aware
features. We translate Pylance's suggestions and error messages to your native language.

### PyPI

**Definition:** The Python Package Index - the official repository for distributing Python
packages. Developers upload packages to PyPI and users install them with pip.

**In Legesher:** We publish all Legesher packages to PyPI, making installation simple:
`pip install legesher` or `pip install legesher-i18n-python-es`.

---

## R

### RTL (Right-to-Left)

**Definition:** Writing systems that are written from right to left instead of left to right.
Arabic, Hebrew, and Persian are RTL languages.

**In Legesher:** We support RTL languages in the code editor, ensuring proper text direction,
cursor movement, and selection behavior for Arabic and Hebrew developers.

**Example:** Arabic code displays with Arabic text flowing right-to-left while maintaining
proper code indentation and structure.

### Round-Trip Fidelity

**Definition:** The property where data can be converted to another format and back without
any loss or corruption.

**In Legesher:** Code maintains perfect round-trip fidelity when translating between
languages. Code in Spanish translates to English and back to Spanish with no changes.

**Example:** Spanish code with specific variable names, comments, and formatting translates
to English and back to the exact original Spanish.

---

## S

### Semantic Versioning

**Definition:** A versioning system using three numbers (MAJOR.MINOR.PATCH) where each
number increments based on the type of changes: breaking changes, new features, or bug fixes.

**In Legesher:** We follow semantic versioning (e.g., v1.2.3). MAJOR changes break
compatibility, MINOR adds features, PATCH fixes bugs. This helps users understand update impact.

**Example:** Version 1.0.0 to 1.1.0 adds new features but doesn't break existing code.
Version 1.1.0 to 2.0.0 may require code changes.

### Smudge Filter (Git)

**Definition:** A Git filter that runs when files are checked out from the repository. It
transforms file content after retrieving it from Git but before writing it to your working
directory.

**In Legesher:** The smudge filter translates English code from Git to your preferred
language when you open files. This allows you to work in your native language.

**Example:** When you open a file, the smudge filter converts stored English `if x > 5:`
to Spanish `si x > 5:` in your editor.

---

## T

### Token-Based Transformation

**Definition:** A translation technique that works by replacing individual words or symbols
(tokens) in source code without understanding the code's grammatical structure.

**In Legesher:** Our MVP uses token-based transformation for speed and simplicity. We
replace English keywords with their translations (e.g., `if` becomes `si`) using a lookup
table.

**Example:** Token-based translation replaces `if age >= 18:` with `si edad >= 18:` by
substituting tokens: `if`→`si`, `age`→`edad`.

### Tree-sitter

**Definition:** A parser generator tool and parsing library that creates fast, incremental
parsers for programming languages.

**In Legesher:** We plan to use Tree-sitter for production-quality translation. It provides
better accuracy than token-based translation by understanding code structure and handling
edge cases.

**Example:** Tree-sitter can distinguish between the keyword `in` and a variable named `in`,
translating only the keyword.

---

## V

### Version-Aware Packs

**Definition:** Language packs that support multiple versions of a programming language and
adjust translations based on the version being used.

**In Legesher:** Our language packs know which keywords and features are available in each
Python version. Python 3.10+ users get translations for `match` and `case` keywords.

**Example:** A Python 3.12 language pack includes translations for the newest keywords,
while a Python 3.8 pack only includes keywords available in that version.

---

## Need More Help?

If you encounter an unfamiliar term not listed here:

- Check the main [documentation](README.md)
- Search in the [architecture guide](architecture/complete-architecture-guide.md)
- Ask in the community discussions

**Contributing:** If you find a term that should be added to this glossary, please open
an issue or submit a pull request.
