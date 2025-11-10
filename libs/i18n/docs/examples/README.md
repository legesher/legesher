# Deep Context Examples - Reference Guide

**Purpose**: Validated reference examples for generating deep context documents across all 105
Python terms.

**Related Issues**:

- CORE-392: Template validation through 4 example contexts
- CORE-393: Mass generation of remaining 101 term contexts

## Overview

This directory contains **4 carefully validated deep context documents** that serve as gold-standard
references for generating linguistic context for all Python keywords and builtin functions.
Each example represents a distinct **translation pattern** encountered when translating programming
terms into world languages.

### Why Exactly 4 Examples?

These examples were strategically chosen to cover the four major translation challenges in Python:

1. **Action Keywords** - Terms with clear verb semantics (`def`)
2. **Modern Technical Keywords** - Terms requiring transliteration decisions (`async`)
3. **Simple Builtin Functions** - Beginner-friendly action verbs (`print`)
4. **Compound Terms** - Multi-word concepts needing decomposition (`isinstance`)

Together, these 4 examples demonstrate **all linguistic patterns** needed to translate the
remaining 101 Python terms consistently and accurately.

## Example Breakdown

### 1. `def.md` - Action Keyword Pattern

**Category**: Python Keyword
**Pattern Type**: Action keyword with infinitive verb semantics

**Key Characteristics**:

- Clear verb form (to define, to declare)
- Abstract action (not physical)
- Formal register required
- Direct infinitive translations in most languages

**Translation Challenges**:

- Distinguishing "define" (create) vs "define" (describe)
- Choosing correct formality level
- Handling verb aspect (perfective vs imperfective)

**When to Use This Example**:
Reference `def.md` when translating Python keywords that represent programming **actions** with
verb semantics:

- `return`, `break`, `continue`, `pass`, `raise`, `yield`
- `import`, `from`, `del`, `assert`
- `global`, `nonlocal` (less directly verbal but still action-oriented)

**Key Sections Demonstrated**:

- Verb infinitive forms across languages
- Formal vs informal register choices
- Grammatical aspect handling
- Cultural context for abstract actions

---

### 2. `async.md` - Complex Modern Keyword

**Category**: Python Keyword
**Pattern Type**: Modern technical term requiring transliteration strategy

**Key Characteristics**:

- Technical jargon (asynchronous)
- No traditional translation in many languages
- Transliteration vs semantic translation decision
- Compound word in origin (Greek: a + synchronous)

**Translation Challenges**:

- Deciding when to transliterate vs translate
- Handling prefix semantics ("a-" = without)
- Adapting to languages without Greek/Latin influence
- Balancing clarity vs technical accuracy

**When to Use This Example**:
Reference `async.md` when translating **modern technical keywords** or terms requiring
transliteration decisions:

- `await`, `match`, `case`, `with`
- `lambda` (Greek letter/mathematical term)
- `yield` (technical meaning diverges from common meaning)
- Any term where transliteration might be preferred over translation

**Key Sections Demonstrated**:

- Transliteration strategies by language family
- Etymology and morphological breakdown
- Technical jargon adaptation patterns
- Cross-linguistic consistency for modern terms

---

### 3. `print.md` - Simple Builtin Function

**Category**: Python Builtin Function
**Pattern Type**: Simple action verb, beginner-friendly

**Key Characteristics**:

- Common verb with everyday meaning
- Physical/concrete action (printing on paper)
- Semantic shift in programming context (display to screen)
- High-frequency term in beginner code

**Translation Challenges**:

- Choosing between "print" (physical) and "display" (screen)
- Regional variations (e.g., Spanish: imprimir vs mostrar)
- Beginner accessibility vs technical precision
- Cultural expectations for output actions

**When to Use This Example**:
Reference `print.md` when translating **simple builtin functions** with everyday verb
meanings:

- `input`, `len`, `str`, `int`, `float`, `bool`
- `list`, `dict`, `set`, `tuple`
- `open`, `close`, `read`, `write`
- `min`, `max`, `sum`, `abs`, `round`

**Key Sections Demonstrated**:

- Semantic shift from everyday to programming context
- Beginner-friendly terminology choices
- Regional variation handling
- Cross-language consistency for high-frequency terms

---

### 4. `isinstance.md` - Compound Term Challenge

**Category**: Python Builtin Function
**Pattern Type**: Compound English term requiring decomposition

**Key Characteristics**:

- Compound word: "is" + "instance"
- Requires understanding of both components
- Object-oriented programming concept
- Four distinct compound translation strategies demonstrated

**Translation Challenges**:

- Decomposing compound into meaningful parts
- Choosing between 4 compound strategies:
  1. **Literal Translation** (translate each part)
  2. **Calque/Loan Translation** (structure preserved)
  3. **Semantic Equivalent** (different structure, same meaning)
  4. **Descriptive Paraphrase** (explain the concept)
- Maintaining consistency with related terms (e.g., `issubclass`)

**When to Use This Example**:
Reference `isinstance.md` when translating **compound builtin functions** or multi-word
concepts:

- `hasattr`, `getattr`, `setattr`, `delattr`
- `issubclass`, `isinstance`
- Any `is*` function (e.g., future `isdigit`, `isalpha`)
- Compound terms like `RuntimeError`, `ValueError`

**Key Sections Demonstrated**:

- All 4 compound translation strategies with examples
- Morphological decomposition
- Cross-linguistic consistency for OOP terms
- Strategy selection criteria

---

## Decision Tree: Which Example Matches My Term?

Use this decision tree to select the most relevant reference example:

```text
START: What type of term am I translating?

├─ Is it a KEYWORD?
│  ├─ Does it represent a programming ACTION (verb)?
│  │  └─ YES → Use def.md (Action Keyword Pattern)
│  │      Examples: return, break, continue, raise, import
│  │
│  └─ Is it a MODERN/TECHNICAL term or potential transliteration?
│     └─ YES → Use async.md (Complex Modern Keyword)
│         Examples: await, match, lambda, with, yield
│
└─ Is it a BUILTIN FUNCTION?
   ├─ Is it a SIMPLE everyday verb?
   │  └─ YES → Use print.md (Simple Builtin Pattern)
   │      Examples: input, len, open, read, write, min, max
   │
   └─ Is it a COMPOUND word (multiple English parts)?
      └─ YES → Use isinstance.md (Compound Term Pattern)
          Examples: isinstance, hasattr, getattr, issubclass
```

---

## Pattern Recognition Guide

### Quick Reference Table

| Pattern | Example File | Term Type | Similar Python Terms |
|---------|--------------|-----------|----------------------|
| **Action Keywords** | `def.md` | Keywords (verbs) | `return`, `break`, `continue`, `pass`, `raise`, `yield`, `import`, `from`, `del`, `assert`, `global`, `nonlocal` |
| **Modern Keywords** | `async.md` | Keywords (technical) | `await`, `match`, `case`, `with`, `lambda`, `except`, `finally`, `class` |
| **Simple Builtins** | `print.md` | Builtin functions (simple verbs) | `input`, `len`, `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`, `open`, `close`, `read`, `write`, `min`, `max`, `sum`, `abs`, `round`, `sorted`, `reversed`, `enumerate`, `zip`, `map`, `filter` |
| **Compound Builtins** | `isinstance.md` | Builtin functions (compounds) | `hasattr`, `getattr`, `setattr`, `delattr`, `issubclass`, `isinstance` |

### Extended Term Classification

**Action Keywords** (use `def.md`):

- Control flow: `if`, `elif`, `else`, `for`, `while`, `break`, `continue`, `pass`
- Function/class definition: `def`, `class`, `return`
- Exception handling: `raise`, `try`, `except`, `finally`
- Scope: `global`, `nonlocal`, `del`
- Importing: `import`, `from`, `as`
- Assertion: `assert`

**Modern Keywords** (use `async.md`):

- Async/await: `async`, `await`
- Pattern matching: `match`, `case`
- Context managers: `with`, `as`
- Generators: `yield`
- Lambda: `lambda`
- Boolean: `and`, `or`, `not`, `is`, `in`

**Simple Builtins** (use `print.md`):

- I/O: `print`, `input`, `open`
- Type conversion: `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`
- Basic operations: `len`, `min`, `max`, `sum`, `abs`, `round`, `pow`
- Iteration: `range`, `enumerate`, `zip`, `sorted`, `reversed`
- Functional: `map`, `filter`, `all`, `any`

**Compound Builtins** (use `isinstance.md`):

- Type checking: `isinstance`, `issubclass`
- Attribute operations: `hasattr`, `getattr`, `setattr`, `delattr`
- String methods: `startswith`, `endswith` (if added to builtin scope)
- Future compounds: any term with `is*`, `has*`, `get*`, `set*`, `del*`

---

## Quality Standards

### What Makes a Good Deep Context Document?

A high-quality deep context document must:

1. **Linguistic Accuracy**
   - Correct translations in all target languages
   - Proper grammatical forms (infinitives for verbs, nouns for objects)
   - Accurate etymological information
   - Valid morphological breakdowns

2. **Cultural Appropriateness**
   - Formal register for technical terms
   - Cultural context explanations where relevant
   - Regional variations documented
   - Sensitivity to language-specific norms

3. **Consistency**
   - Terminology aligned with other Python terms
   - Translation strategies consistent within language families
   - Cross-references to related terms included
   - Compound strategies applied uniformly

4. **Completeness**
   - All template sections filled out
   - Examples provided for each language
   - Edge cases and challenges documented
   - Usage notes for translators included

5. **Pedagogical Value**
   - Beginner-friendly explanations
   - Clear distinction between everyday and technical meanings
   - Examples that illuminate translation choices
   - Guidance for future translators

### Validation Checklist

Before considering a deep context document complete, verify:

- [ ] **Etymology**: Accurate origin and historical development
- [ ] **Morphology**: Correct word structure breakdown
- [ ] **Semantics**: Core meaning and programming-specific meaning distinguished
- [ ] **Pragmatics**: Appropriate formality and register
- [ ] **Cross-linguistic consistency**: Terminology aligns with examples
- [ ] **Regional variations**: Documented where applicable
- [ ] **Compound strategies**: All 4 strategies considered for compound terms
- [ ] **Related terms**: Cross-references to similar Python terms
- [ ] **Translator notes**: Clear guidance for language pack creators
- [ ] **Examples**: Code snippets and usage contexts provided

### Consistency Requirements

To maintain consistency across all 105 contexts:

1. **Terminology Alignment**
   - Use same metalanguage (e.g., "infinitive form", "formal register")
   - Apply same translation strategies within language families
   - Cross-reference related terms (e.g., `async` ↔ `await`, `isinstance` ↔ `issubclass`)

2. **Structure Consistency**
   - Follow template structure exactly
   - Use same heading levels and formatting
   - Maintain consistent section ordering
   - Apply same markdown conventions

3. **Language Coverage**
   - Include same target languages across all contexts
   - Provide same level of detail for each language
   - Document regional variations consistently

4. **Example Quality**
   - Code examples should be runnable
   - Use consistent code formatting
   - Provide context for each example
   - Show both correct usage and common mistakes

---

## For CORE-393 Contributors

### How These Examples Will Be Used

During the mass generation phase (CORE-393), these 4 validated examples will serve as:

1. **AI Training References**
   - Few-shot learning examples for LLM-assisted generation
   - Quality benchmarks for automated validation
   - Pattern templates for consistency checking

2. **Human Review Baselines**
   - Gold standards for evaluating generated contexts
   - Reference points for linguistic accuracy
   - Quality thresholds for approval

3. **Consistency Anchors**
   - Ensure all 105 contexts maintain same structure
   - Verify terminology alignment across terms
   - Check translation strategy consistency

### AI Translation Pipeline

The planned workflow for CORE-393:

1. **Input**: Python term + category (keyword/builtin)
2. **Reference Selection**: AI selects most relevant example(s) from these 4
3. **Context Generation**: AI generates deep context using examples as templates
4. **Automated Validation**: Check structure, completeness, basic consistency
5. **Human Review**: Multilingual reviewers validate linguistic accuracy
6. **Iteration**: Refine based on feedback, using examples as quality baseline
7. **Approval**: Accept when quality matches example standards

### What to Check When Reviewing Generated Contexts

When reviewing AI-generated contexts against these examples:

**Structure Check**:

- [ ] All sections from template present
- [ ] Headings match example formatting
- [ ] Markdown conventions followed
- [ ] Length comparable to similar examples

**Content Check**:

- [ ] Etymology accurate and sourced
- [ ] Morphology correctly analyzed
- [ ] Translations grammatically correct
- [ ] Regional variations noted where applicable
- [ ] Compound strategies applied (if applicable)

**Consistency Check**:

- [ ] Terminology aligns with examples
- [ ] Translation strategies match similar terms
- [ ] Cross-references to related terms included
- [ ] Formality level appropriate

**Quality Check**:

- [ ] Linguistic accuracy verified by native speakers
- [ ] Code examples runnable and relevant
- [ ] Translator notes clear and actionable
- [ ] Cultural context appropriate

### Ensuring Quality at Scale

To maintain example-level quality across all 105 contexts:

1. **Batch Review by Pattern**
   - Review all "action keywords" together (using `def.md` as baseline)
   - Review all "modern keywords" together (using `async.md` as baseline)
   - Review all "simple builtins" together (using `print.md` as baseline)
   - Review all "compound builtins" together (using `isinstance.md` as baseline)

2. **Cross-Language Consistency**
   - Assign language-specific reviewers to verify all contexts for their language
   - Check that translation strategies align within language families
   - Ensure regional variations documented consistently

3. **Automated Validation**
   - Use scripts to check structure completeness
   - Validate markdown formatting
   - Check for required sections and cross-references
   - Verify code example syntax

4. **Iterative Refinement**
   - Generate in small batches (10-20 contexts)
   - Review and refine before next batch
   - Update generation prompts based on common issues
   - Maintain quality standards throughout

---

## Validation Status

### Example Validation History

| Example | Initial Creation | Linguistic Review | Final Validation | Status |
|---------|------------------|-------------------|------------------|--------|
| `def.md` | 2025-10-25 | Pending | Pending | ✅ Template Validated |
| `async.md` | 2025-10-25 | Pending | Pending | ✅ Template Validated |
| `print.md` | 2025-10-25 | Pending | Pending | ✅ Template Validated |
| `isinstance.md` | 2025-10-25 | Pending | Pending | ✅ Template Validated |

**Note**: These examples have been validated for **template structure and coverage** (CORE-392).
Linguistic review by native speakers in target languages is planned as part of CORE-393 to ensure
translation accuracy.

### Template Coverage

Each example demonstrates different sections of the deep context template:

| Template Section | def.md | async.md | print.md | isinstance.md |
|------------------|--------|----------|----------|---------------|
| Etymology | ✅ | ✅ | ✅ | ✅ |
| Morphology | ✅ | ✅ | ✅ | ✅ |
| Semantics | ✅ | ✅ | ✅ | ✅ |
| Pragmatics | ✅ | ✅ | ✅ | ✅ |
| Cross-linguistic patterns | ✅ | ✅ | ✅ | ✅ |
| Translation challenges | ✅ | ✅ | ✅ | ✅ |
| Compound strategies | ❌ | ❌ | ❌ | ✅ (all 4) |
| Transliteration strategies | ❌ | ✅ | ❌ | ❌ |
| Regional variations | ✅ | ✅ | ✅ | ✅ |
| Related terms | ✅ | ✅ | ✅ | ✅ |
| Code examples | ✅ | ✅ | ✅ | ✅ |
| Translator notes | ✅ | ✅ | ✅ | ✅ |

**Coverage**: All template sections demonstrated across the 4 examples.

---

## Quick Start for Contributors

### I'm translating a term - which example should I use?

1. **Identify your term type**: Keyword or builtin function?
2. **Check the decision tree** (above) to find the matching pattern
3. **Open the relevant example** (`def.md`, `async.md`, `print.md`, or `isinstance.md`)
4. **Follow the structure** and apply the same translation strategies
5. **Cross-reference** with other examples if your term shares characteristics

### I'm reviewing a generated context - what should I check?

1. **Structure**: Does it match the example formatting?
2. **Completeness**: Are all sections filled out like the examples?
3. **Consistency**: Does terminology align with these examples?
4. **Quality**: Is linguistic accuracy at the same level as examples?
5. **Cross-references**: Are related terms mentioned like in examples?

### I found an issue with an example - what should I do?

1. **Document the issue**: Note the specific problem (linguistic, structural, etc.)
2. **Check if it's systematic**: Does the issue affect other examples?
3. **Propose a fix**: Suggest how to improve the example
4. **Update related contexts**: If fixing an example, update any dependent contexts
5. **Document the change**: Note in validation history

---

## Summary

These 4 examples represent **validated patterns** for translating all Python terms into world
languages. By following these examples, contributors to CORE-393 can ensure:

- **Consistency** across all 105 deep context documents
- **Quality** at the level of human-expert translation
- **Completeness** covering all linguistic aspects
- **Usability** for translators creating language packs

When in doubt, refer to the most similar example and follow its pattern. Quality at scale comes
from consistent application of validated patterns.

---

**Last Updated**: 2025-10-25
**Related Issues**: CORE-392 (validation), CORE-393 (mass generation)
**Maintained by**: Legesher i18n team
