# Git Workflow Guide for Legesher

**Last Updated:** 2025-11-07
**Target Audience:** Developers familiar with git basics
**Purpose:** Learn how to collaborate on multilingual codebases using Legesher's git integration

---

## Table of Contents

- [Introduction](#introduction)
- [How It Works](#how-it-works)
- [Setting Up Git Integration](#setting-up-git-integration)
- [Daily Workflow](#daily-workflow)
- [Team Collaboration](#team-collaboration)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Introduction

### Why Language-Agnostic Git?

Traditional version control systems assume all developers write code in English. This creates barriers for developers who:

- Think and code more effectively in their native language
- Are learning programming alongside learning English
- Want to maintain codebases in their local language

**The Challenge:** If one developer commits code in Spanish and another in Arabic, git sees them as different keywords,
creating merge conflicts even when there's no logical conflict.

**Legesher's Solution:** Store a single canonical English version in the repository while letting each developer work in
their preferred language. Git filters automatically translate between languages, eliminating keyword-based conflicts.

### Benefits

- **Zero merge conflicts** from keyword differences
- **Seamless collaboration** across language barriers
- **Consistent repository** with English as canonical storage
- **Developer freedom** to code in their native language
- **Standard git workflow** - all your favorite tools work normally

---

## How It Works

Legesher uses git's clean and smudge filters to automatically translate code between your language and English during
git operations.

### The Translation Pipeline

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Your Workflow                            │
└─────────────────────────────────────────────────────────────────┘

Working Directory (Spanish)          Git Repository (English)
┌──────────────────────┐             ┌──────────────────────┐
│                      │             │                      │
│  clase Persona:      │             │  class Person:       │
│    def __init__():   │   ──────>   │    def __init__():   │
│      pasar           │   CLEAN     │      pass            │
│                      │   FILTER    │                      │
└──────────────────────┘             └──────────────────────┘
         ^                                      │
         │                                      │
         │           SMUDGE FILTER              │
         │              (pull)                  │
         └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Teammate's Workflow                         │
└─────────────────────────────────────────────────────────────────┘

Working Directory (Arabic)           Git Repository (English)
┌──────────────────────┐             ┌──────────────────────┐
│                      │             │                      │
│  صنف شخص:            │             │  class Person:       │
│    تعريف __init__(): │   <──────   │    def __init__():   │
│      تمرير           │   SMUDGE    │      pass            │
│                      │   FILTER    │                      │
└──────────────────────┘             └──────────────────────┘
```

### Clean Filter (Commit)

When you run `git add` or `git commit`, the **clean filter** translates your code:

1. Reads your code in your language (e.g., Spanish)
2. Translates Python keywords to English
3. Stores English version in git repository

```bash
# You commit Spanish code
git add main.py
git commit -m "Added Person class"
# → Repository stores English version
```

### Smudge Filter (Checkout/Pull)

When you run `git checkout` or `git pull`, the **smudge filter** translates back:

1. Reads English code from repository
2. Translates Python keywords to your language
3. Writes translated version to working directory

```bash
# You pull from repository
git pull origin main
# → Your files appear in Spanish
```

### Key Insight

**You never see English code.** The translation happens transparently. From your perspective, you're just using git
normally, but in your language.

---

## Setting Up Git Integration

### Prerequisites

- Git 2.x or later
- Legesher installed (`pip install legesher`)
- A git repository (existing or new)

### Initial Setup

Navigate to your repository and run:

```bash
cd /path/to/your/project
legesher git setup --language es
```

This command:

1. Creates `.legesher/config.yml` with your language settings
2. Configures git filters in `.git/config`
3. Sets up `.gitattributes` to apply filters to Python files
4. Initializes metadata tracking

### Configuration File

The setup creates `.legesher/config.yml`:

```yaml
# Legesher Configuration
version: 1.0.0

# Primary language for your working directory
language: es

# Git integration settings
git:
  enabled: true
  canonical_language: en
  filter_extensions:
    - .py
    - .pyw

# Translation settings
translation:
  preserve_comments: true
  preserve_strings: true
  preserve_identifiers: true
  metadata_tracking: true
```

### Verifying Setup

Check that filters are configured:

```bash
# Check git configuration
git config --local filter.legesher-clean.clean
# Should show: legesher git clean %f

git config --local filter.legesher-smudge.smudge
# Should show: legesher git smudge %f

# Verify .gitattributes
cat .gitattributes
# Should show: *.py filter=legesher-clean filter=legesher-smudge
```

Test the integration:

```bash
# Create a test file in your language
echo "clase Prueba:\n    pasar" > test.py

# Add and check staged content
git add test.py
git show :test.py
# Should display English: class Test:\n    pass
```

> **Important:** The `.legesher/` directory should be committed to your repository so team members can see
> recommended settings, but each developer configures their own language preference.

---

## Daily Workflow

### Writing Code in Your Language

Write code naturally in your configured language:

```python
# Spanish developer writes (main.py)
clase Usuario:
    """Un usuario del sistema."""

    def __init__(mismo, nombre, edad):
        mismo.nombre = nombre
        mismo.edad = edad

    def saludar(mismo):
        retornar f"Hola, soy {mismo.nombre}"

# Standard usage
usuario = Usuario("María", 25)
imprimir(usuario.saludar())
```

### Committing Changes

Commit normally - translation happens automatically:

```bash
# Stage your changes
git add main.py

# Commit with your message
git commit -m "Agregué la clase Usuario con método saludar"

# Push to remote
git push origin main
```

**What happens:**

1. `git add` triggers clean filter
2. Your Spanish code is translated to English
3. English version is staged
4. Commit stores English in repository
5. Your working directory stays in Spanish

### Pulling Updates

Pull normally - translation happens automatically:

```bash
# Pull latest changes
git pull origin main

# Your working directory updates with Spanish code
```

**What happens:**

1. Git fetches English code from repository
2. Smudge filter translates to Spanish
3. Your working directory receives Spanish version
4. You see code in your language

### Reviewing Diffs

View diffs in your language:

```bash
# See unstaged changes (in your language)
git diff

# See staged changes (in your language)
git diff --cached

# Compare branches (in your language)
git diff main feature-branch
```

**Important:** By default, diffs show your working directory language. To see repository (English) versions:

```bash
# View repository version (English)
legesher git show-canonical main.py

# Compare repository versions (English)
legesher git diff-canonical HEAD~1 HEAD main.py
```

### Branching and Merging

Work with branches normally:

```bash
# Create feature branch
git checkout -b nueva-funcionalidad

# Make changes in Spanish
echo "def nueva_funcion():\n    pasar" >> main.py

# Commit changes
git commit -am "Agregué nueva función"

# Switch back to main
git checkout main

# Merge feature
git merge nueva-funcionalidad
```

Branches work seamlessly because the repository stores English, preventing keyword-based conflicts.

---

## Team Collaboration

### Multilingual Team Scenario

**Team Setup:**

- Ana (Spanish developer) - Madrid
- John (English developer) - San Francisco
- Ahmed (Arabic developer) - Cairo

All three collaborate on the same codebase with zero language conflicts.

### Ana's Workflow (Spanish)

Ana writes a new feature in Spanish:

```python
# Ana writes (usuario.py)
clase GestorUsuarios:
    """Gestiona usuarios del sistema."""

    def __init__(mismo):
        mismo.usuarios = []

    def agregar_usuario(mismo, usuario):
        si usuario no en mismo.usuarios:
            mismo.usuarios.append(usuario)
            retornar Verdadero
        retornar Falso
```

Ana commits and pushes:

```bash
# Ana's terminal (Spanish)
git add usuario.py
git commit -m "Agregué GestorUsuarios para manejar colección"
git push origin main
```

**Repository stores:**

```python
# Repository (English)
class UserManager:
    """Manages system users."""

    def __init__(self):
        self.users = []

    def add_user(self, user):
        if user not in self.users:
            self.users.append(user)
            return True
        return False
```

### John's Workflow (English)

John pulls Ana's changes and sees English:

```bash
# John's terminal (English)
git pull origin main
# Updates usuario.py
```

John sees and works with:

```python
# John sees (usuario.py)
class UserManager:
    """Manages system users."""

    def __init__(self):
        self.users = []

    def add_user(self, user):
        if user not in self.users:
            self.users.append(user)
            return True
        return False
```

John adds a method:

```python
# John adds (usuario.py)
    def remove_user(self, user):
        if user in self.users:
            self.users.remove(user)
            return True
        return False
```

John commits:

```bash
# John's terminal (English)
git commit -am "Added remove_user method"
git push origin main
```

### Ahmed's Workflow (Arabic)

Ahmed pulls both Ana's and John's changes:

```bash
# Ahmed's terminal (Arabic)
git pull origin main
# Updates usuario.py
```

Ahmed sees:

```python
# Ahmed sees (usuario.py)
صنف مديرالمستخدمين:
    """يدير مستخدمي النظام."""

    تعريف __init__(ذاتي):
        ذاتي.المستخدمين = []

    تعريف إضافةمستخدم(ذاتي، مستخدم):
        إذا مستخدم ليس في ذاتي.المستخدمين:
            ذاتي.المستخدمين.append(مستخدم)
            إرجاع صحيح
        إرجاع خطأ

    تعريف إزالةمستخدم(ذاتي، مستخدم):
        إذا مستخدم في ذاتي.المستخدمين:
            ذاتي.المستخدمين.remove(مستخدم)
            إرجاع صحيح
        إرجاع خطأ
```

Ahmed adds a method:

```python
# Ahmed adds (usuario.py)
    تعريف عدالمستخدمين(ذاتي):
        إرجاع len(ذاتي.المستخدمين)
```

Ahmed commits:

```bash
# Ahmed's terminal (Arabic)
git commit -am "أضفت طريقة عد_المستخدمين"
git push origin main
```

### Pull Request Review

When reviewing PRs, team members see code in their language:

**Ana reviews Ahmed's PR (Spanish):**

```python
# Ana sees in GitHub (via Legesher integration)
def contar_usuarios(mismo):
    retornar len(mismo.usuarios)
```

**John reviews Ahmed's PR (English):**

```python
# John sees in GitHub (via Legesher integration)
def count_users(self):
    return len(self.users)
```

**Key Point:** Reviews happen in each person's language, but discussions reference the canonical English names for
clarity.

### Best Practices for Multilingual Teams

1. **Use English for identifiers:** Variable/function names in English ensure clarity across team

   ```python
   # Good (Spanish keywords, English identifiers)
   clase UserManager:
       def agregar_usuario(mismo, user_name):
           pasar

   # Avoid (Spanish keywords AND identifiers)
   clase GestorUsuarios:
       def agregar_usuario(mismo, nombre_usuario):
           pasar
   ```

2. **Reference canonical names in PR discussions:** Use English names when discussing code

   ```text
   "In the UserManager.add_user method, we should validate the user parameter..."
   ```

3. **Document in team's shared language:** README, docs in one shared language (often English)

4. **Respect `.legesher/config.yml`:** Check recommended settings when joining project

---

## Troubleshooting

### Translation Issues

**Problem:** Code doesn't translate correctly after commit

**Symptoms:**

```bash
git show :main.py
# Shows Spanish instead of English
```

**Solution:**

```bash
# 1. Check filter configuration
git config --local filter.legesher-clean.clean
# Should output: legesher git clean %f

# 2. Re-run setup
legesher git setup --language es --force

# 3. Re-stage file
git reset HEAD main.py
git add main.py
```

### Filter Not Working

**Problem:** Clean/smudge filters not being applied

**Symptoms:**

- Commits show your language instead of English
- Pulls don't translate to your language

**Solution:**

```bash
# 1. Check .gitattributes exists and is correct
cat .gitattributes
# Should contain: *.py filter=legesher-clean filter=legesher-smudge

# 2. Ensure .gitattributes is committed
git add .gitattributes
git commit -m "Added Legesher git filters"

# 3. Refresh working directory
git checkout HEAD -- .
```

**Alternative:** Check if filters are blocked:

```bash
# Temporarily disable filter requirement
git config --local filter.legesher-clean.required false
git config --local filter.legesher-smudge.required false

# Try operation again
git add main.py
```

### Merge Conflicts

**Problem:** Merge conflict appears (rare but possible)

**When it happens:**

- Two developers modify same line with different logic (not just keywords)
- Structural changes conflict

**Example conflict:**

```python
<<<<<<< HEAD
def calcular_total(mismo, impuestos=Verdadero):
    si impuestos:
        retornar mismo.subtotal * 1.15
=======
def calcular_total(mismo, descuento=0):
    retornar mismo.subtotal * (1 - descuento)
>>>>>>> feature-branch
```

**Resolution:**

```bash
# 1. Resolve in your language as normal
# Edit the file to resolve conflict

def calcular_total(mismo, impuestos=Verdadero, descuento=0):
    total = mismo.subtotal * (1 - descuento)
    si impuestos:
        total *= 1.15
    retornar total

# 2. Mark resolved and commit
git add main.py
git commit -m "Resuelto conflicto de merge en calcular_total"
```

The resolution will be translated to English in the repository automatically.

### Repository Shows Mixed Languages

**Problem:** Some files in repository are in multiple languages

**Cause:** Filters weren't set up before initial commits

**Solution:**

```bash
# 1. Set up filters
legesher git setup --language es

# 2. Re-normalize repository
legesher git normalize

# This reads all files, translates to English, and re-commits
# Creates a normalization commit
```

> **Warning:** `git normalize` rewrites history. Coordinate with team before running.

### Performance Issues

**Problem:** Git operations are slow

**Common causes:**

- Large files being filtered
- Complex translation in many files

**Solution:**

```bash
# 1. Exclude large or generated files
echo "*.min.py -filter" >> .gitattributes
echo "build/** -filter" >> .gitattributes

# 2. Disable metadata tracking for performance
# Edit .legesher/config.yml
translation:
  metadata_tracking: false

# 3. Use shallow clones for CI/CD
git clone --depth 1 --filter=blob:none <repo-url>
```

---

## Advanced Topics

### Metadata Tracking

Legesher tracks translation metadata to preserve developer intent and enable advanced features.

**What's tracked:**

```yaml
# .legesher/metadata/main.py.yml
file: main.py
translations:
  - line: 5
    original_language: es
    original_text: "def calcular_total(mismo, impuestos):"
    canonical_text: "def calculate_total(self, taxes):"
    timestamp: 2025-11-07T10:30:00Z
    author: ana@example.com
```

**Use cases:**

- See who wrote code in which language
- Track translation history
- Debug translation issues
- Analytics on language usage

**Accessing metadata:**

```bash
# View metadata for file
legesher git metadata show main.py

# View translation history
legesher git metadata history main.py --line 5

# Export metadata
legesher git metadata export --format json > metadata.json
```

### Translation History

Track how code evolved across languages:

```bash
# See who translated a line
legesher git blame main.py

# Output shows:
# Author | Date | Language | Line
# Ana    | Nov 7 | es      | clase Usuario:
# John   | Nov 8 | en      |   def __init__(self):
# Ahmed  | Nov 9 | ar      |     self.users = []

# View file in different language at specific commit
legesher git show --language ar HEAD~5:main.py
# Shows historical version in Arabic, regardless of author's language
```

### Custom Configurations

#### Per-Directory Settings

Configure different languages for subdirectories:

```yaml
# .legesher/config.yml
language: es

overrides:
  - path: src/core/**
    language: en
  - path: src/plugins/arabic/**
    language: ar
```

#### Custom Keyword Mappings

Override default translations:

```yaml
# .legesher/config.yml
translation:
  custom_mappings:
    es:
      class: "tipo"      # Use "tipo" instead of "clase"
      return: "devolver" # Use "devolver" instead of "retornar"
```

#### Hook into Translation Pipeline

Add custom processing:

```yaml
# .legesher/config.yml
git:
  pre_clean_hook: scripts/pre_clean.py
  post_smudge_hook: scripts/post_smudge.py
```

```python
# scripts/pre_clean.py
def pre_clean_hook(content, language, file_path):
    """Called before clean filter translates to English."""
    # Custom processing
    return modified_content
```

### Working with Submodules

Each submodule maintains its own Legesher configuration:

```bash
# Initialize submodule with Legesher
cd submodules/shared-lib
legesher git setup --language es

# Parent repo and submodule can use different languages
cd ../..
legesher git setup --language ar
```

### Integration with Git Hooks

Enhance workflow with git hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Validate translations before commit
legesher git validate-translations
if [ $? -ne 0 ]; then
  echo "Translation validation failed"
  exit 1
fi
```

```bash
# .git/hooks/post-merge
#!/bin/bash
# Refresh translations after merge
legesher git refresh-metadata
```

### CI/CD Integration

Configure CI/CD to work with Legesher:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Don't translate in CI - work with canonical English
      - name: Disable Legesher filters
        run: |
          git config filter.legesher-clean.clean "cat"
          git config filter.legesher-smudge.smudge "cat"

      # Or enable specific language for testing
      - name: Setup Legesher for Spanish tests
        run: |
          pip install legesher
          legesher git setup --language es --ci-mode

      - name: Run tests
        run: pytest
```

### Migrating Existing Repository

Convert existing repository to use Legesher:

```bash
# 1. Backup your repository
git clone --mirror <repo-url> backup-repo

# 2. Set up Legesher
cd original-repo
legesher git setup --language es

# 3. Normalize existing code
legesher git normalize --dry-run
# Review changes

legesher git normalize --commit
# Creates normalization commit

# 4. Force push (coordinate with team!)
git push --force-with-lease origin main
```

---

## Summary

Legesher's git integration enables seamless multilingual collaboration:

- **Write** in your language
- **Store** in canonical English
- **Collaborate** with teammates in any language
- **Zero conflicts** from keyword differences

The git workflow remains familiar - filters handle translation transparently. Your team can focus on building
great software, not navigating language barriers.

### Next Steps

1. **Set up your repository:** `legesher git setup --language <code>`
2. **Configure team settings:** Share `.legesher/config.yml`
3. **Start coding:** Write naturally in your language
4. **Collaborate:** Push, pull, merge - it all just works

### Additional Resources

- [Legesher Core Documentation](../core/README.md)
- [Language Pack Guide](./language-packs.md)
- [CLI Reference](./cli-reference.md)
- [Translation Architecture](../../planning/architecture/complete-architecture-guide.md)

---

**Questions?** Open an issue or join our community discussions.

**Found a bug?** Report translation issues with `legesher git debug` output.
