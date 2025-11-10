# Translation Database Schema

## Overview

The Legesher translation database is a SQLite database that stores translations from 4 primary sources:

1. **Community Translations** - Crowdsourced translations from the Legesher community
2. **Aya 23** - Linguistic expert translations and cultural insights
3. **Claude** - AI-generated translations using Claude language models
4. **GPT-4o** - AI-generated translations using GPT-4o language models

The database maintains full review history and metadata for each translation, enabling
quality assessment, community feedback integration, and continuous improvement of language packs.

## Architecture

### Storage Location

The translation database is stored in a SQLite file with a configurable location:

```text
Default path: .legesher/translations.db
```

The storage path can be configured at initialization:

```python
from legesher_i18n.db import TranslationDatabase

# Use default path
db = TranslationDatabase()

# Use custom path
db = TranslationDatabase(db_path="/custom/path/translations.db")
```

### Database Tables

#### translations

Stores all translation candidates from the 4 sources with comprehensive metadata.

**Columns:**

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `id` | INTEGER | Primary key | PRIMARY KEY |
| `language_code` | TEXT | ISO 639-1 language code (e.g., "es", "ar", "zh", "hi") | NOT NULL |
| `term` | TEXT | English Python keyword or term to translate | NOT NULL |
| `term_type` | TEXT | Type of term: "keyword", "builtin", "constant" | NOT NULL |
| `translation` | TEXT | Translated version of the term | NOT NULL |
| `source` | TEXT | Source of translation: "community", "aya23", "claude", "gpt4o" | NOT NULL |
| `word_type` | TEXT | Linguistic classification: "verb", "noun", "modifier", "action_state", "literal", "cultural_adapt" | NOT NULL |
| `word_form` | TEXT | Grammatical form or variant (e.g., "imperative", "infinitive") | |
| `model_rationale` | TEXT | For AI sources: explanation of why this translation was chosen | |
| `alternatives_considered` | JSON | Array of alternative translations not selected, with reasons | |
| `confidence` | REAL | Confidence score 0.0-1.0 (1.0 = highest confidence) | |
| `created_at` | TIMESTAMP | When the translation was created | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | When the translation was last updated | DEFAULT CURRENT_TIMESTAMP |
| `created_by` | TEXT | Creator identifier (GitHub username for community) | |

**Constraints:**

```sql
UNIQUE(language_code, term, term_type, source)
```

This ensures each source provides at most one translation per term in a given language.

**Purpose:**

The `translations` table is the core data store for all translation candidates. It tracks:

- What was translated from which source
- Quality metadata (confidence, rationale)
- Alternative options considered
- Who contributed (for attribution and accountability)
- When changes occurred (for audit trail)

**Example Data:**

```yaml
language_code: "es"
term: "if"
term_type: "keyword"
translation: "si"
source: "aya23"
word_type: "action_state"
model_rationale: "In Spanish, 'si' (without accent) means 'if' and is the standard conditional keyword"
confidence: 0.95
created_by: "aya23_team"
```

---

#### reviews

Stores community feedback, expert reviews, and voting data for translations.

**Columns:**

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `id` | INTEGER | Primary key | PRIMARY KEY |
| `translation_id` | INTEGER | Foreign key to translations table | FOREIGN KEY, NOT NULL |
| `reviewer_github` | TEXT | GitHub username of reviewer | NOT NULL |
| `reviewer_proficiency` | TEXT | Self-reported proficiency level: "native", "fluent", "intermediate", "beginner", "learning" | |
| `regional_variant` | TEXT | Regional variant of language (e.g., "es_MX" for Mexican Spanish) | |
| `vote` | TEXT | Review outcome: "approved", "rejected", "suggest_revision" | NOT NULL |
| `emoji` | TEXT | Sentiment indicator for quick scanning | |
| `comment` | TEXT | Detailed feedback or explanation | |
| `suggested_translation` | TEXT | If suggesting revision, the proposed translation | |
| `alternatives_suggested` | JSON | Array of alternative translations suggested by reviewer | |
| `review_source` | TEXT | Where review came from: "github_issue", "web_dashboard", "vs_code_extension" | |
| `github_issue_url` | TEXT | Link to GitHub issue if review came from GitHub | |
| `created_at` | TIMESTAMP | When the review was created | DEFAULT CURRENT_TIMESTAMP |

**Foreign Key:**

```sql
FOREIGN KEY(translation_id) REFERENCES translations(id) ON DELETE CASCADE
```

Deleting a translation cascades to delete all its reviews.

**Purpose:**

The `reviews` table captures the community validation process:

- Who reviewed each translation and their expertise level
- Whether the translation was approved or needs revision
- Cultural/regional feedback
- Suggested alternatives
- Audit trail of all feedback

**Example Data:**

```yaml
translation_id: 42
reviewer_github: "linguist_maria"
reviewer_proficiency: "native"
regional_variant: "es_ES"
vote: "approved"
comment: "Excellent choice. 'si' is natural and matches Python conventions in Spanish."
created_at: "2025-11-10T14:32:00Z"
```

---

#### deep_contexts

Stores deep contextual information for each Python term to guide translation decisions.

**Columns:**

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `id` | INTEGER | Primary key | PRIMARY KEY |
| `term` | TEXT | English Python keyword or term | NOT NULL, UNIQUE |
| `term_type` | TEXT | Type of term: "keyword", "builtin", "constant" | NOT NULL |
| `etymology` | TEXT | Linguistic origin and history of the English term | |
| `explanation_simple` | TEXT | Simple explanation (for learners) | |
| `explanation_beginner` | TEXT | Beginner programmer explanation | |
| `explanation_intermediate` | TEXT | Intermediate programmer explanation with examples | |
| `explanation_expert` | TEXT | Advanced explanation with technical details | |
| `concept_agnostic` | TEXT | Language-agnostic concept description | |
| `translation_guidance` | TEXT | Specific guidance for translators on this term | |
| `created_at` | TIMESTAMP | When context was created | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | When context was last updated | DEFAULT CURRENT_TIMESTAMP |

**Constraints:**

```sql
UNIQUE(term, term_type)
```

**Purpose:**

The `deep_contexts` table provides translator guidance with multiple explanations for different skill levels and use cases:

- Etymology helps translators understand the concept
- Multi-level explanations aid in choosing appropriate translations
- Guidance specific to translation challenges
- Supports both community translators and AI translation models

**Example Data:**

```yaml
term: "class"
term_type: "keyword"
etymology: "From Latin 'classis' (military unit/category)"
explanation_simple: "A blueprint for creating objects with shared properties and behaviors"
explanation_expert: "A template for OOP that defines attributes and methods"
translation_guidance: "Look for words meaning 'template' or 'type definition'"
```

---

#### linguistic_standards

Stores linguistic standards and conventions per language to ensure consistency.

**Columns:**

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `id` | INTEGER | Primary key | PRIMARY KEY |
| `language_code` | TEXT | ISO 639-1 language code | NOT NULL, UNIQUE |
| `language_family` | TEXT | Language family for context | |
| `action_keyword_form` | TEXT | Grammatical form for action keywords (e.g., verb conjugation style) | |
| `state_keyword_form` | TEXT | Grammatical form for state keywords | |
| `constant_form` | TEXT | Convention for constant names (e.g., ALL_CAPS) | |
| `guidelines` | TEXT | JSON object with language-specific translation guidelines | |
| `created_at` | TIMESTAMP | When standards were established | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | When standards were last updated | DEFAULT CURRENT_TIMESTAMP |

**Constraints:**

```sql
UNIQUE(language_code)
```

**Purpose:**

The `linguistic_standards` table stores language-wide conventions:

- Grammatical preferences for different keyword types
- Naming conventions (constants, variables, etc.)
- Translation guidelines specific to the language
- Related issues: CORE-392

**Example Data:**

```yaml
language_code: "es"
language_family: "Romance"
action_keyword_form: "infinitive"
state_keyword_form: "present_tense"
constant_form: "SNAKE_CASE_UPPERCASE"
guidelines: {
  "capitalization": "Use lowercase for keywords unless it's a constant",
  "accent_marks": "Preserve accent marks for native pronunciation",
  "word_order": "Follow Spanish SVO word order for multi-word terms"
}
```

### Entity Relationship Diagram

```text
+------------------+         +------------------+
|  translations    |         |    reviews       |
+------------------+         +------------------+
| id (PK)          |<--(FK)--| id (PK)          |
| language_code    |         | translation_id   |
| term             |         | reviewer_github  |
| term_type        |         | reviewer_prof... |
| translation      |         | vote             |
| source           |         | comment          |
| word_type        |         | created_at       |
| confidence       |         +------------------+
| created_at       |
| updated_at       |
+------------------+

+------------------+         +------------------+
| deep_contexts    |         | linguistic_...   |
+------------------+         | standards        |
| id (PK)          |         +------------------+
| term (UNIQUE)    |         | id (PK)          |
| term_type        |         | language_code... |
| etymology        |         | (UNIQUE)         |
| explanation_*    |         | action_form      |
| translation_...  |         | state_form       |
| created_at       |         | constant_form    |
| updated_at       |         | guidelines       |
+------------------+         | created_at       |
                              | updated_at       |
                              +------------------+

Legend:
(PK) = Primary Key
(FK) = Foreign Key
(UNIQUE) = Unique Constraint
```

## Database Design Decisions

### Why SQLite?

SQLite was chosen for the translation database because:

1. **Offline-First**: Developers can work without internet connection
2. **No Server Setup**: Single-file database, trivial deployment
3. **Version Control Friendly**: Can be checked into git (when appropriate)
4. **Query Performance**: Sufficient for translation lookup operations
5. **Cross-Platform**: Runs identically on Windows, macOS, Linux
6. **Python Integration**: Built-in support via `sqlite3` module

### Why 4 Tables?

The database structure uses 4 main tables to separate concerns:

1. **translations**: Core translation data with source tracking
2. **reviews**: Community feedback decoupled from translations
3. **deep_contexts**: Reusable documentation for translators (many-to-many relationship with translations)
4. **linguistic_standards**: Language-wide standards (one per language)

This design allows:

- Multiple reviews per translation (one-to-many)
- Tracking which reviews approved/rejected which translations
- Reusing context documents across languages
- Enforcing language standards consistently

### Why JSON for Arrays?

Arrays of alternatives are stored as JSON strings in the database because:

1. **Flexibility**: Variable number of alternatives per translation
2. **Structured Data**: JSON preserves structure and can be queried
3. **Language Support**: SQLite lacks native array types; JSON functions provide query capability
4. **Simplicity**: JSON is human-readable in database inspection

Example JSON structure:

```json
{
  "alternatives": [
    {
      "translation": "whether",
      "reason": "More formal English meaning"
    },
    {
      "translation": "in_case",
      "reason": "Alternative verb form"
    }
  ]
}
```

## Integration with Other Issues

### CORE-392: Linguistic Standards

The `linguistic_standards` table (CORE-392) stores language-specific rules:

- Grammatical conventions per language
- Translation guidelines
- Naming conventions

These standards guide the AI translation process (CORE-394) and help validate community suggestions.

### CORE-393: Deep Contexts

The `deep_contexts` table (CORE-393) stores contextual information:

- Etymology and explanations at multiple levels
- Translation guidance for tricky terms
- Concept descriptions for both humans and AI models

This enables better translation quality by providing rich context.

### CORE-394: AI Translations

AI translation workflows use the database to:

- Load deep contexts and linguistic standards for the target language
- Store generated translations with `model_rationale` field
- Track confidence scores
- Compare with existing community translations

### CORE-395: Community Data

Community translation data import/export uses:

- `reviews` table for tracking community feedback
- `created_by` field in translations for attribution
- Bulk import of translations with sources

## Usage Examples

### Basic Operations

#### Initialize Database

```python
from legesher_i18n.db import TranslationDatabase

# Use default path (.legesher/translations.db)
db = TranslationDatabase()

# Use custom path
db = TranslationDatabase(db_path="/custom/path/translations.db")

# Database is automatically initialized with tables
db.close()
```

#### Add Translation

```python
# Add a community translation
translation_id = db.add_translation(
    language_code="es",
    term="def",
    term_type="keyword",
    translation="definir",
    source="community",
    word_type="verb",
    word_form="infinitive",
    created_by="github_username"
)

# Add an AI-generated translation
ai_translation_id = db.add_translation(
    language_code="es",
    term="def",
    term_type="keyword",
    translation="definir",
    source="claude",
    word_type="verb",
    word_form="infinitive",
    confidence="high",
    model_rationale="Infinitive form matches linguistic standards for action keywords",
    alternatives_considered='["función", "definicion"]',
    created_by="ai-claude"
)
```

#### Query Translations

```python
# Get specific translation
translation = db.get_translation(
    language_code="es",
    term="def",
    term_type="keyword",
    source="community"
)

# Get all translations for a term (from all sources)
all_def_translations = db.get_all_translations(
    term="def",
    term_type="keyword"
)

# Get all Spanish translations
spanish_translations = db.get_all_translations(language_code="es")

# Get all community translations
community_translations = db.get_all_translations(source="community")

# Get all high-confidence AI translations
high_confidence = db.get_all_translations(confidence="high")
```

#### Update Translation

```python
# Update confidence after review
success = db.update_translation(
    translation_id=translation_id,
    confidence="high",
    word_type="verb"
)
```

#### Add Reviews

```python
# Add a community review
review_id = db.add_review(
    translation_id=translation_id,
    reviewer_github="native_speaker_username",
    reviewer_proficiency="native",
    regional_variant="Mexican Spanish",
    vote="approve",
    emoji="✅",
    comment="Perfect translation! This is how we say it in Mexico.",
    review_source="github-issue",
    github_issue_url="https://github.com/madiedgar/legesher/issues/123"
)

# Add a review with suggestions
alternative_review_id = db.add_review(
    translation_id=translation_id,
    reviewer_github="spanish_dev",
    reviewer_proficiency="proficient",
    vote="discuss",
    emoji="🤔",
    comment="Good, but in Spain we might use a different form",
    suggested_translation="declarar",
    alternatives_suggested='["declarar", "especificar"]',
    review_source="google-form"
)

# Get all reviews for a translation
reviews = db.get_reviews(translation_id)
for review in reviews:
    print(f"{review['emoji']} {review['reviewer_github']}: {review['comment']}")
```

#### Deep Context Operations

```python
# Add deep context for a term
context_id = db.add_deep_context(
    term="def",
    term_type="keyword",
    etymology="Short for 'define'. From Latin 'definire' meaning 'to bound, limit'",
    explanation_simple="Like naming a recipe - you give it a name and write down what it does",
    explanation_beginner="def creates a function - a reusable block of code with a name",
    explanation_intermediate="Defines a function object with scope, parameters, and return values",
    explanation_expert="Creates a function object in the current namespace with bytecode compilation",
    concept_agnostic="A way to encapsulate and name a sequence of operations",
    translation_guidance="Use imperative or infinitive verb forms. Focus on the action of defining/declaring."
)

# Retrieve context
context = db.get_deep_context("def")
print(context['etymology'])
print(context['explanation_simple'])
```

#### Linguistic Standards

```python
# Add linguistic standards for Spanish
standard_id = db.add_linguistic_standard(
    language_code="es",
    language_family="romance",
    action_keyword_form="infinitive",
    state_keyword_form="present_tense",
    constant_form="UPPERCASE_SNAKE",
    guidelines="Use infinitive for verbs (definir, retornar). Use lowercase for keywords."
)

# Retrieve standards
standards = db.get_linguistic_standard("es")
print(f"Action keywords should use: {standards['action_keyword_form']}")
```

### CLI Commands

#### Database Initialization

```bash
# Initialize with default path
legesher-i18n db init

# Initialize with custom path
legesher-i18n db init --path /custom/path/translations.db
```

**Output:**

```text
✓ Database initialized at .legesher/translations.db
✓ Tables: translations, reviews, deep_contexts, linguistic_standards
```

#### Show Statistics

```bash
# Show stats for default database
legesher-i18n db stats

# Show stats for custom path
legesher-i18n db stats --path /custom/path/translations.db
```

**Example Output:**

```text
📊 Database Statistics

Database: .legesher/translations.db

Tables:
  Translations: 156
  Reviews: 43
  Deep Contexts: 35
  Linguistic Standards: 24

Languages:
  es: 52 translations
  ar: 38 translations
  fr: 30 translations
  zh: 36 translations

Sources:
  community: 78 translations
  claude: 26 translations
  gpt4o: 26 translations
  aya23: 26 translations
```

#### Optimize Database

```bash
# Run VACUUM to reclaim space and optimize
legesher-i18n db vacuum

# With custom path
legesher-i18n db vacuum --path /custom/path/translations.db
```

**Output:**

```text
Optimizing database: .legesher/translations.db...
✓ Database optimized: .legesher/translations.db
```

### Integration Workflow Example

Complete workflow from adding translations to generating final language pack:

```python
from legesher_i18n.db import TranslationDatabase

# Initialize
db = TranslationDatabase()

# 1. Add deep context (from CORE-393)
db.add_deep_context(
    term="def",
    term_type="keyword",
    etymology="From Latin 'definire'",
    explanation_simple="Creates a named set of instructions",
    # ... more fields
)

# 2. Add linguistic standards (from CORE-392)
db.add_linguistic_standard(
    language_code="es",
    language_family="romance",
    action_keyword_form="infinitive"
)

# 3. Add translations from different sources (CORE-394, CORE-395)
community_id = db.add_translation("es", "def", "keyword", "definir", "community")
ai_id = db.add_translation("es", "def", "keyword", "definir", "claude", confidence="high")

# 4. Add community reviews (CORE-397, CORE-398)
db.add_review(community_id, reviewer_github="user1", vote="approve", emoji="✅")
db.add_review(community_id, reviewer_github="user2", vote="approve", emoji="✅")

# 5. Query for comparison (CORE-396)
all_translations = db.get_all_translations(language_code="es", term="def")
print(f"Found {len(all_translations)} translations for 'def' in Spanish")

# 6. Export approved translations (CORE-404)
approved = [t for t in all_translations if t['confidence'] == 'high']

db.close()
```

## Future Enhancements

Potential future additions to the database:

1. **Search indexing**: Full-text search on translations and comments
2. **Usage statistics**: Track which terms are used most frequently
3. **Quality metrics**: Aggregate scores across reviews
4. **Collaboration**: Track translation workflows and approvals
5. **Versioning**: Support multiple translation versions per term
6. **Exports**: Generate language packs from the database

## References

- CORE-392: Linguistic Standards Schema
- CORE-393: Deep Contexts Documentation
- CORE-394: AI Translation Workflows
- CORE-395: Community Data Import/Export
- Phase 3: Full API implementation and usage examples
