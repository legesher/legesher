# Language Packs - Python Keyword Translations

**Status:** Development / Community Translations Migrated
**Purpose:** Testing infrastructure with real community data

---

## ⚠️ Important Notice

**These language pack files contain COMMUNITY TRANSLATIONS** migrated from the legesher-translations repository (2019-2021). These are **real translations** created by community contributors, NOT mock data.

**Current Status:** `migrated` - awaiting review and refinement with new linguistic standards

**DO NOT USE IN PRODUCTION** until translations have been:

1. Reviewed against new linguistic standards (2025)
2. Verified by native speakers
3. Community re-approved
4. Marked as `status: reviewed`

---

## Current Status

### Available Language Packs

| Language | Code | Status | Keywords | Builtins | Community Reviews | Notes |
|----------|------|--------|----------|----------|-------------------|-------|
| Spanish | es | Migrated | 35/35 ✅ | 69/69 ✅ | 0 | Base language (all dialects) |
| Arabic | ar | Migrated | 35/35 ✅ | 69/69 ✅ | 101 | Base language (all dialects) |
| Hindi | hi | Migrated | 35/35 ✅ | 69/69 ✅ | 0 | Base language (all dialects) |
| Chinese | zh | Planned | 0/35 | 0/69 | - | No existing translations found |

**Note:** Using 2-letter base codes (es, ar, hi) rather than dialect-specific codes (es-ES, ar-SA, hi-IN). Dialect distinctions will be added later with native speaker input.

### Translation Coverage

**Total migrated:** 312 translations (105 keywords + 207 builtins across 3 languages)
**Community reviews:** 101 review comments (Arabic translations have extensive feedback)

### Source

All translations migrated from [legesher-translations](https://github.com/legesher/legesher-translations) repository branches:

- Spanish: `spanish-translation` branch
- Arabic: `arabic-translation` branch (101 community reviews!)
- Hindi: `hindi-translation` branch

---

## How to Use (Development)

### Import a Language Pack

```python
from legesher.i18n import load_language_pack

# Load Spanish keyword translations
spanish = load_language_pack("es")

# Get translation for keyword
spanish.keywords["def"]  # → "definir"
spanish.keywords["return"]  # → "retornar"
spanish.keywords["True"]  # → "Verdadero"
```

### Test Translation

```python
from legesher.core import transform

spanish_code = """
definir saludar(nombre):
    retornar f"Hola, {nombre}!"

print(saludar("Mundo"))
"""

# Transform to English Python
english_code = transform(spanish_code, from_lang="es", to_lang="en")
# Result:
# def saludar(nombre):
#     return f"Hola, {nombre}!"
```

---

## File Structure

```text
language-packs/
├── README.md                  # This file
├── es/                        # Spanish (base language)
│   └── keywords.yml           # 35 keywords + 69 builtins ✅ (migrated)
├── ar/                        # Arabic (base language)
│   └── keywords.yml           # 35 keywords + 69 builtins ✅ (migrated, 101 reviews)
├── hi/                        # Hindi (base language)
│   └── keywords.yml           # 35 keywords + 69 builtins ✅ (migrated)
└── zh/                        # Chinese (planned)
    └── keywords.yml           # Coming later
```

---

## Language Pack Format

```yaml
language:
  code: es
  name: Spanish
  native_name: Español
  family: Romance
  direction: ltr

metadata:
  status: migrated
  version: 0.1.0-community
  source: legesher-translations repository
  branch: spanish-translation
  review_count: 0
  notes: Migrated from legesher-translations community contributions

keywords:
  def:
    translation: definir
    form: infinitive
    pattern: ACTION_KEYWORD
    confidence: COMMUNITY
    notes: Migrated from legesher-translations repository

  # ... more keywords

builtins:
  abs:
    translation: absoluto
    confidence: COMMUNITY
    notes: Migrated from legesher-translations repository

  # ... more builtins
```

---

## When to Populate with Real Translations

**Timeline:** Coming in 1-2 weeks

**Process:**

### Step 1: Generate AI Translations (Day 1)

- Run translation scripts from `scripts/translate/`
- Submit to Claude, GPT-4, and Aya APIs
- Get 3 model suggestions per term
- Cost: ~$21 for all 3 models, or $7.56 for Claude only

### Step 2: Community Review (1-2 weeks)

- Post translations to GitHub Discussions
- Native speakers review and approve
- Reach consensus on each translation

### Step 3: Update Language Packs (Day 1)

- Replace mock translations with approved ones
- Update `status: reviewed`
- Add reviewer names
- Bump version to `1.0.0`

### Step 4: Release (Day 1)

- Run integration tests
- Update documentation
- Publish to npm
- Announce to community

---

## Translation Guidelines

### Pattern Consistency

**ACTION_KEYWORD** (verbs - actions you perform):

- Form: Infinitive verb
- Examples: `def` → `definir`, `return` → `retornar`, `break` → `romper`

**STATE_KEYWORD** (conjunctions/prepositions - conditions/states):

- Form: Conjunction or preposition
- Examples: `if` → `si`, `while` → `mientras`, `with` → `con`

**VALUE_CONSTANT** (fixed values):

- Form: Adjective or noun, first letter capitalized
- Examples: `True` → `Verdadero`, `False` → `Falso`, `None` → `Ninguno`

**OPERATOR_KEYWORD** (logical operators):

- Form: Conjunction or adverb
- Examples: `and` → `y`, `or` → `o`, `not` → `no`

### Language-Specific Rules

**Spanish (es-ES):**

- ACTION keywords: infinitive verbs (-ar, -er, -ir endings)
- Constants: masculine form for consistency
- Register: technical/formal (CS education vocabulary)
- Avoid: regional slang, overly academic terms

**Arabic (ar-SA):**

- No diacritics in keywords (easier to type)
- RTL language: max 10 characters per keyword
- Verb forms: use present tense 3rd person
- Test: verify rendering in IDEs

**Chinese (zh-CN):**

- Prefer single characters for simple concepts
- Use Simplified Chinese only
- Follow CS education terminology
- Prioritize: brevity and clarity

**Hindi (hi-IN):**

- ACTION keywords: infinitive form (करना ending)
- Use Devanagari script only (not romanization)
- Avoid: overly formal Sanskrit if simpler Hindi exists
- Balance: technical accuracy with naturalness

---

## Quality Standards

### For Production Release

All translations must meet these criteria:

✅ **Technical Accuracy**

- Captures the correct Python concept (not just English word)
- Verified against Python documentation

✅ **CS Education Alignment**

- Matches terminology used in target language CS textbooks
- Confirmed by educators or students

✅ **Naturalness**

- Comfortable for native speakers to type hundreds of times per day
- Easy to pronounce in code reviews
- Memorable and intuitive

✅ **Consistency**

- Follows pattern classification (ACTION/STATE/VALUE)
- Matches grammatical form of related terms
- Predictable for learners

✅ **Usability**

- Short enough (1-2 words for keywords, max 3 for builtins)
- No offensive or misleading meanings
- Renders correctly in common IDEs

✅ **Community Approval**

- Reviewed by 3+ native speakers
- Regional diversity verified (if applicable)
- Consensus or majority vote reached

---

## Testing Language Packs

### Unit Tests

```bash
# Test language pack loading
pytest tests/i18n/test_language_packs.py

# Test specific language
pytest tests/i18n/test_es_ES.py
```

### Integration Tests

```bash
# Test transformation (Spanish → English)
pytest tests/integration/test_es_transform.py

# Test execution of translated code
pytest tests/integration/test_es_execute.py
```

### Manual Testing

```python
# Test in Python REPL
from legesher.i18n import load_language_pack
from legesher.core import transform

spanish = load_language_pack("es")

code = """
definir suma(a, b):
    retornar a + b

print(suma(5, 3))
"""

# Should transform to valid Python
english = transform(code, from_lang="es", to_lang="en")
print(english)
```

---

## Contributing

### Adding a New Language

1. Create directory: `language-packs/{code}/`
2. Copy template: `cp templates/keywords.template.yml {code}/keywords.yml`
3. Fill in language metadata
4. Add translations (start with mock/examples)
5. Update this README
6. Create PR for review

### Updating Existing Translations

1. Check current `status` in language pack file
2. If `status: example`, propose better translation
3. If `status: reviewed`, provide evidence for change (CS education sources, native speaker input)
4. Create GitHub Discussion for community input
5. Once approved, update file and bump version

---

## Resources

### Translation Infrastructure

- **Context templates:** `docs/context-template-tier1.md`, `docs/context-template-tier2.md`
- **Linguistic standards:** `docs/linguistic-standards.md`
- **Model prompts:** `scripts/translate/prompts/`
- **Test cases:** `scripts/translate/test-cases/`

### Workflow Documentation

- **Example outputs:** `scripts/translate/EXAMPLE_OUTPUTS.md` - See what AI models produce
- **Complete workflow:** `scripts/translate/WORKFLOW.md` - Step-by-step process
- **Manual testing:** `scripts/translate/QUICK_START.md` - Test in Claude Desktop

### Community

- **Discussions:** [GitHub Discussions](https://github.com/legesher/legesher/discussions)
- **Issues:** [Translation Issues](https://github.com/legesher/legesher/issues?q=label:translation)
- **Discord:** Coming soon

---

## FAQ

### Q: Can I use these translations in production?

**A: No, not yet.** Current translations are community-contributed (2019-2021) and need review against new linguistic standards (2025). Wait for re-reviewed translations marked as `status: reviewed`.

### Q: How do I know when translations are production-ready?

**A: Check the `status` field:**

- `status: migrated` - Community translations from 2019-2021, needs review
- `status: draft` - AI-generated, needs review
- `status: review` - Under community review
- `status: reviewed` - Approved by community, safe for production

### Q: Can I suggest better translations?

**A: Yes!** Open a GitHub Discussion with:

- Current translation
- Your proposed translation
- Rationale (CS education sources, native speaker perspective)
- Regional considerations

### Q: When will real translations be ready?

**A: Estimated 3-4 weeks:**

- Week 1: AI generation + processing
- Weeks 2-3: Community review
- Week 4: Finalize & release

### Q: Why these 3 languages first?

**A: We have existing community translations!** Spanish, Arabic, and Hindi translations were contributed by the community in 2019-2021 in the legesher-translations repository. We've migrated them as a starting point for testing infrastructure while building out the new system.

---

**Last Updated:** 2025-10-28
**Maintained by:** Legesher Team
**Questions?** Open a [GitHub Discussion](https://github.com/legesher/legesher/discussions)
