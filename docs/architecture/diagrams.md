# Architecture Diagrams

**Last Updated:** 2025-11-07
**Purpose:** Visual architecture documentation for Legesher
**Audience:** Developers, contributors, and architects

---

## Overview

This document provides visual representations of Legesher's architecture using Mermaid diagrams. Each diagram
illustrates a critical aspect of the system, from package dependencies to runtime translation flows.

**Related Documentation:**

- Complete Architecture Guide (private-working-memory repository)
- Implementation Roadmap (private-working-memory repository)
- API Documentation (`/docs/api/`)
- Developer Guide (`/CONTRIBUTING.md`)

---

## 1. Package Architecture

This diagram shows the complete package structure of the Legesher monorepo, organized into four tiers based on
dependencies and functionality.

```mermaid
flowchart TB
    subgraph Tier1["Tier 1: Foundation"]
        style Tier1 fill:#e1f5ff,stroke:#01579b
        core["@legesher/core<br/>Token transformer<br/>AST utilities<br/>Git filters"]
        style core fill:#b3e5fc,stroke:#0277bd
    end

    subgraph Tier2["Tier 2: Language Support"]
        style Tier2 fill:#f3e5f5,stroke:#4a148c
        i18n["@legesher/i18n<br/>Language pack API<br/>Version management<br/>Translation registry"]
        style i18n fill:#e1bee7,stroke:#6a1b9a

        i18n-python-es["@legesher/i18n-python-es<br/>Spanish Python keywords"]
        i18n-python-ar["@legesher/i18n-python-ar<br/>Arabic Python keywords"]

        style i18n-python-es fill:#e1bee7,stroke:#6a1b9a
        style i18n-python-ar fill:#e1bee7,stroke:#6a1b9a
    end

    subgraph Tier3["Tier 3: User Tools"]
        style Tier3 fill:#e8f5e9,stroke:#1b5e20
        legesher["@legesher/legesher<br/>Main package<br/>CLI tools<br/>User workflows"]
        language-server["@legesher/language-server<br/>LSP implementation<br/>IDE integration"]
        vscode["@legesher/vscode<br/>VS Code extension<br/>UI components"]

        style legesher fill:#c8e6c9,stroke:#2e7d32
        style language-server fill:#c8e6c9,stroke:#2e7d32
        style vscode fill:#c8e6c9,stroke:#2e7d32
    end

    subgraph Tier4["Tier 4: Community"]
        style Tier4 fill:#fff3e0,stroke:#e65100
        pride["@legesher/pride<br/>Community platform<br/>Language pack registry"]
        style pride fill:#ffe0b2,stroke:#ef6c00
    end

    %% Dependencies
    i18n --> core
    i18n-python-es --> i18n
    i18n-python-ar --> i18n

    legesher --> core
    legesher --> i18n
    language-server --> core
    language-server --> i18n
    vscode --> language-server

    pride --> core
    pride --> i18n
```

### Package Tiers Explained

**Tier 1 - Foundation:**

- `@legesher/core`: The foundation package containing the token transformer, AST utilities, and git filter
  implementations. Has zero external Legesher dependencies.

**Tier 2 - Language Support:**

- `@legesher/i18n`: Core language pack system with version management and translation registry
- `@legesher/i18n-python-es`: Spanish keyword translations for Python
- `@legesher/i18n-python-ar`: Arabic keyword translations for Python
- Additional language packs follow the same pattern

**Tier 3 - User Tools:**

- `@legesher/legesher`: Main user-facing package with CLI tools
- `@legesher/language-server`: LSP server for IDE integration
- `@legesher/vscode`: VS Code extension providing the user interface

**Tier 4 - Community:**

- `@legesher/pride`: Community platform and public language pack registry

### Key Takeaways

1. Clear separation of concerns across tiers
2. Foundation packages have no Legesher dependencies
3. Language packs are modular and can be added independently
4. User tools build on stable foundation and language support layers
5. Community layer depends on all lower tiers but is optional

---

## 2. Translation Flow

This diagram illustrates how Legesher translates code from one language to another using the token-based
approach (MVP implementation).

```mermaid
flowchart LR
    subgraph Input
        spanish["Spanish Source Code<br/>def saludar(nombre):<br/>    devolver f'Hola {nombre}'"]
        style spanish fill:#fff9c4,stroke:#f57f17
    end

    subgraph Translation["Translation Process"]
        tokenizer["Tokenizer<br/>Split into tokens:<br/>[def, saludar, (, nombre, ), :, ...]"]
        lookup["Language Pack Lookup<br/>def → def<br/>devolver → return"]
        transformer["Token Transformer<br/>Replace keywords<br/>Preserve identifiers"]

        tokenizer --> lookup
        lookup --> transformer

        style tokenizer fill:#e1f5ff,stroke:#01579b
        style lookup fill:#f3e5f5,stroke:#4a148c
        style transformer fill:#e1f5ff,stroke:#01579b
    end

    subgraph Output
        english["English Source Code<br/>def saludar(nombre):<br/>    return f'Hola {nombre}'"]
        style english fill:#e8f5e9,stroke:#2e7d32
    end

    subgraph RoundTrip["Round-Trip Capability"]
        reverse["Reverse Translation<br/>English → Spanish<br/>Same process, reversed"]
        style reverse fill:#fff3e0,stroke:#e65100
    end

    spanish --> tokenizer
    transformer --> english
    english -.-> reverse
    reverse -.-> spanish
```

### Translation Steps Explained

**Step 1 - Tokenization:**

The source code is split into individual tokens (keywords, identifiers, operators, literals). The tokenizer
preserves whitespace and structure.

**Step 2 - Language Pack Lookup:**

Each token is checked against the language pack:

- Keywords (def, devolver) are mapped to English equivalents
- Identifiers (saludar, nombre) are preserved unchanged
- Operators and literals pass through unchanged

**Step 3 - Token Transformation:**

The TokenTransformer reconstructs the code with translated keywords while maintaining:

- Original formatting and indentation
- User-defined identifiers (variable/function names)
- Comments and docstrings
- String literals

**Round-Trip Translation:**

The same process works in reverse, allowing seamless translation between any supported language pair. This
enables teams to work in different languages on the same codebase.

### Package Architecture Key Takeaways

1. Token-based approach is simple and fast (MVP)
2. Preserves everything except keywords
3. Bidirectional translation support
4. No AST parsing required (future enhancement)
5. Works with existing Python tooling

---

## 3. Git Workflow

This diagram shows how Legesher integrates with Git using clean and smudge filters to maintain a canonical
English representation in the repository while allowing developers to work in their native languages.

```mermaid
flowchart TB
    subgraph Developer1["Developer A (Spanish)"]
        write1["Write Spanish Code<br/>clase Calculadora:<br/>    def sumar(a, b):"]
        read1["See Spanish Code<br/>clase Calculadora:<br/>    def sumar(a, b):"]
        style write1 fill:#fff9c4,stroke:#f57f17
        style read1 fill:#fff9c4,stroke:#f57f17
    end

    subgraph GitOps["Git Operations"]
        clean["Clean Filter<br/>(git add)<br/>Spanish → English<br/>Translation"]
        commit["Git Commit<br/>Stores English:<br/>class Calculadora:<br/>    def sumar(a, b):"]
        checkout["Git Checkout<br/>Retrieves English:<br/>class Calculadora:<br/>    def sumar(a, b):"]
        smudge["Smudge Filter<br/>(git checkout)<br/>English → Arabic<br/>Translation"]

        style clean fill:#e1f5ff,stroke:#01579b
        style commit fill:#e8f5e9,stroke:#2e7d32
        style checkout fill:#e8f5e9,stroke:#2e7d32
        style smudge fill:#e1f5ff,stroke:#01579b
    end

    subgraph Developer2["Developer B (Arabic)"]
        read2["See Arabic Code<br/>صنف Calculadora:<br/>    تعريف sumar(a, b):"]
        write2["Write Arabic Code<br/>صنف Calculadora:<br/>    تعريف sumar(a, b):"]
        style read2 fill:#f3e5f5,stroke:#4a148c
        style write2 fill:#f3e5f5,stroke:#4a148c
    end

    subgraph Remote["Remote Repository"]
        remote["GitHub/GitLab<br/>English code only<br/>Universal collaboration"]
        style remote fill:#fff3e0,stroke:#e65100
    end

    write1 --> clean
    clean --> commit
    commit --> remote
    remote --> checkout
    checkout --> smudge
    smudge --> read2

    write2 --> |"Clean filter"| commit
    checkout --> |"Smudge filter"| read1
```

### Git Integration Explained

**Clean Filter (Pre-Commit):**

When a developer commits code, the clean filter automatically translates their native language code to English
before it reaches the Git repository. This happens transparently during `git add` or `git commit`.

**Repository Storage:**

All code is stored in English in the Git repository. This provides:

- Universal collaboration across language barriers
- Compatibility with existing tools (GitHub, code review, CI/CD)
- Single source of truth for code review
- Language-agnostic diffs and merges

**Smudge Filter (Post-Checkout):**

When a developer checks out code, the smudge filter translates from English to their configured language. Each
developer can use their own language preference.

**Configuration:**

Developers configure their language preference via:

- `.gitattributes`: Specifies which files to filter
- Legesher config: Sets target language (es, ar, etc.)
- Git config: Registers clean/smudge filters

### Translation Flow Key Takeaways

1. Git stores canonical English representation
2. Developers work in their native language
3. Automatic translation on commit/checkout
4. No conflicts from language differences
5. Full Git workflow compatibility (branch, merge, rebase)
6. Language preference is per-developer, not per-repository

---

## 4. LSP Communication

This sequence diagram shows how the Legesher Language Server integrates with VS Code and Pylance to provide
IDE features with real-time translation.

```mermaid
sequenceDiagram
    participant VSCode as VS Code
    participant LSP as Legesher LSP
    participant Pylance as Pylance
    participant LangPack as Language Pack

    Note over VSCode,LangPack: Hover Request Flow

    VSCode->>LSP: textDocument/hover<br/>(Spanish code position)
    activate LSP

    LSP->>LangPack: Translate Spanish → English
    activate LangPack
    LangPack-->>LSP: English code
    deactivate LangPack

    LSP->>Pylance: textDocument/hover<br/>(English code position)
    activate Pylance
    Pylance-->>LSP: Hover info (English)
    deactivate Pylance

    LSP->>LangPack: Translate hover info → Spanish
    activate LangPack
    LangPack-->>LSP: Spanish hover info
    deactivate LangPack

    LSP-->>VSCode: Display Spanish hover
    deactivate LSP

    Note over VSCode,LangPack: Completion Request Flow

    VSCode->>LSP: textDocument/completion<br/>(cursor after "de")
    activate LSP

    LSP->>LangPack: Check if "de" is partial keyword
    activate LangPack
    LangPack-->>LSP: Matches "def" (Spanish)
    deactivate LangPack

    LSP->>Pylance: textDocument/completion<br/>(English context)
    activate Pylance
    Pylance-->>LSP: Completion list
    deactivate Pylance

    LSP->>LangPack: Translate completions → Spanish
    activate LangPack
    LangPack-->>LSP: Spanish completions
    deactivate LangPack

    LSP-->>VSCode: Display Spanish completions<br/>(def, del, devolver, ...)
    deactivate LSP
```

### LSP Integration Explained

**Language Server Protocol (LSP):**

The Legesher Language Server acts as a middleware between VS Code and Pylance, providing translation services
while maintaining full IDE feature support.

**Hover Request Flow:**

1. Developer hovers over Spanish code in VS Code
2. VS Code sends hover request to Legesher LSP
3. LSP translates position context from Spanish to English
4. LSP forwards request to Pylance with English code
5. Pylance returns hover information (types, docs)
6. LSP translates hover content back to Spanish
7. VS Code displays Spanish hover information

**Completion Request Flow:**

1. Developer types "de" in Spanish Python code
2. VS Code sends completion request to Legesher LSP
3. LSP checks if "de" matches Spanish keywords (def, del, devolver)
4. LSP queries Pylance with English context
5. Pylance returns completion suggestions
6. LSP translates completions to Spanish
7. VS Code displays Spanish completion list

**Other LSP Features:**

The same translation pattern applies to:

- Go to definition
- Find references
- Diagnostics (errors/warnings)
- Code actions (refactoring)
- Signature help
- Document formatting

### Git Workflow Key Takeaways

1. Legesher LSP acts as transparent translation layer
2. Pylance provides Python intelligence unchanged
3. Real-time bidirectional translation
4. Full IDE feature parity with English Python
5. No modification to existing language servers
6. Extensible to other IDEs via LSP standard

---

## 5. Language Pack Inheritance

This diagram shows how version-aware language packs inherit keywords across Python versions, minimizing
duplication while maintaining version-specific accuracy.

```mermaid
flowchart TB
    subgraph Python310["Python 3.10 Base"]
        base310["Python 3.10 Spanish<br/><br/>35 Keywords:<br/>def → def<br/>class → clase<br/>
return → devolver<br/>import → importar<br/>...<br/><br/>No parent version"]
        style base310 fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    end

    subgraph Python311["Python 3.11 Extension"]
        base311["Python 3.11 Spanish<br/><br/>Parent: 3.10<br/>Inherits: 35 keywords<br/><br/>
New keyword:<br/>except* → excepto*<br/><br/>Total: 36 keywords"]
        style base311 fill:#f3e5f5,stroke:#4a148c,stroke-width:3px
    end

    subgraph Python312["Python 3.12 Extension"]
        base312["Python 3.12 Spanish<br/><br/>Parent: 3.11<br/>Inherits: 36 keywords<br/><br/>
New keyword:<br/>type → tipo<br/><br/>Total: 37 keywords"]
        style base312 fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    end

    subgraph Python313["Python 3.13 Extension"]
        base313["Python 3.13 Spanish<br/><br/>Parent: 3.12<br/>Inherits: 37 keywords<br/><br/>
No new keywords<br/><br/>Total: 37 keywords"]
        style base313 fill:#fff3e0,stroke:#e65100,stroke-width:3px
    end

    Python310 ==>|"Extends (adds except*)"| Python311
    Python311 ==>|"Extends (adds type)"| Python312
    Python312 ==>|"Extends (no changes)"| Python313

    classDef inheritArrow stroke:#ff6f00,stroke-width:2px
```

### Version Inheritance Explained

**Base Version (Python 3.10):**

The base language pack contains all 35 standard Python keywords. This is the foundation that newer versions
build upon. Each keyword has translations in the target language:

- Spanish: def → def, class → clase, return → devolver
- Arabic: def → تعريف, class → صنف, return → عودة

**Python 3.11 Extensions:**

Python 3.11 introduced the `except*` keyword for exception groups. The 3.11 language pack:

- Specifies parent version: 3.10
- Inherits all 35 keywords automatically
- Adds only the new translation: except*→ excepto* (Spanish)
- Total vocabulary: 36 keywords

**Python 3.12 Extensions:**

Python 3.12 introduced the `type` keyword for type aliases. The 3.12 language pack:

- Specifies parent version: 3.11
- Inherits all 36 keywords (35 base + except*)
- Adds only the new translation: type → tipo (Spanish)
- Total vocabulary: 37 keywords

**Python 3.13 Extensions:**

Python 3.13 introduced no new keywords. The 3.13 language pack:

- Specifies parent version: 3.12
- Inherits all 37 keywords unchanged
- Adds no new translations
- Total vocabulary: 37 keywords (same as 3.12)

**Benefits of Inheritance:**

1. Minimal duplication (only store deltas)
2. Consistency across versions
3. Easy updates (fix in base propagates)
4. Clear version compatibility
5. Reduced maintenance burden

### LSP Communication Key Takeaways

1. Language packs inherit from previous Python versions
2. Only store differences, not full keyword sets
3. Base version (3.10) contains all core keywords
4. Each version adds only new keywords
5. Version chain: 3.10 → 3.11 → 3.12 → 3.13
6. Automatic fallback to parent versions
7. Future versions extend the chain

---

## Diagram Conventions

**Color Scheme:**

- Blue: Core/Foundation components
- Purple: Language support and translation
- Green: User-facing tools and outputs
- Orange: Community and external systems
- Yellow: Input/Source code

**Arrow Types:**

- Solid arrows: Direct dependencies or data flow
- Dashed arrows: Optional or reverse flow
- Thick arrows: Inheritance or extension

**Box Styles:**

- Rounded boxes: Processes or transformations
- Square boxes: Data or code representations
- Subgraphs: Logical groupings or tiers

---

## Additional Resources

**Architecture Documentation:**

- Complete Architecture Guide (private-working-memory)
- Implementation Roadmap (private-working-memory)
- MLCP Protocol Specification (private-working-memory)

**Package Documentation:**

- Core API (`/libs/core/README.md`)
- I18n API (`/libs/i18n/README.md`)
- LSP Implementation (`/libs/language-server/README.md`)

**Contributing:**

- Developer Guide (`/CONTRIBUTING.md`)
- Code Style Guide (`/docs/code-style.md`)
- Testing Guide (`/docs/testing.md`)

---

**Last Updated:** 2025-11-07
**Maintained by:** Madison Edgar
**Diagram Format:** Mermaid.js
**License:** See repository LICENSE files
