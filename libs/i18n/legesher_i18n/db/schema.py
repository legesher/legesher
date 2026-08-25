"""Database schema definitions for translation storage.

This module contains SQL schema definitions for the four core tables:
- terms: Canonical list of reserved words, extensible across programming languages
- languages: Language registry with ISO standards and script metadata
- translations: One row per translation suggestion (per term, per language, per source)
- selected_translations: Tracks which translation is currently active for YAML packs

plus the vocabulary partition (CORE-1396), which mirrors that trio for
knowledge that is vocabulary rather than term translation:
- vocabulary_entries: Canonical inventory of symbols and variable-name roles
- vocabulary_translations: One row per suggestion (per entry, language, source)
- selected_vocabulary: The active value per entry+language

Future tables (deferred to CORE-595):
- reviews: Community reviews and feedback on translations
- deep_contexts: Etymology and detailed explanations of programming terms
- linguistic_standards: Language-specific formatting guidelines
"""

# Terms table - canonical list of reserved words
#
# CORE-1400: uniqueness includes ``category`` because the same surface
# token can hold two distinct pack slots (``type`` is both the 3.10
# builtin and the 3.12 soft keyword, and the two may carry different
# translations in a language). ``get_term_by_name`` disambiguates via its
# ``category`` parameter.
TERMS_TABLE = """
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    programming_language TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    version_added TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, programming_language, category)
);
"""

# Languages table - language registry
#
# CORE-611: translations.db is the single source of truth for the published
# language registry.
#   - ``in_registry`` marks which languages are published to the generated
#     artifacts (languages.json + the VS Code languages.ts). The registry is
#     generated from the rows where ``in_registry = 1``.
#   - ``has_case_distinction`` is per-language script metadata consumed by the
#     prompt builder; it previously lived only in languages.json.
LANGUAGES_TABLE = """
CREATE TABLE IF NOT EXISTS languages (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    native_name TEXT NOT NULL,
    iso639_2 TEXT,
    bcp47 TEXT,
    family TEXT,
    direction TEXT DEFAULT 'ltr',
    script TEXT,
    numeral_system TEXT,
    has_case_distinction BOOLEAN DEFAULT 1,
    status TEXT DEFAULT 'experimental',
    has_yaml_pack BOOLEAN DEFAULT 0,
    in_registry BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Translations table - one row per translation suggestion
TRANSLATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    language_code TEXT NOT NULL,
    translation TEXT NOT NULL,
    source TEXT NOT NULL,
    model_version TEXT,
    word_type TEXT,
    word_form TEXT,
    confidence TEXT,
    model_rationale TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT,
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code) ON DELETE CASCADE,
    UNIQUE(term_id, language_code, source, translation)
);
"""

# Selected translations table - one row per term+language = the active translation
SELECTED_TRANSLATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS selected_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    language_code TEXT NOT NULL,
    translation TEXT NOT NULL,
    selected_at TEXT NOT NULL DEFAULT (datetime('now')),
    selected_by TEXT,
    selection_reason TEXT,
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code) ON DELETE CASCADE,
    UNIQUE(term_id, language_code)
);
"""

# ---------------------------------------------------------------------------
# Vocabulary partition (CORE-1396)
# ---------------------------------------------------------------------------
# Symbol names and idiomatic variable names are NOT term translations, and
# putting them through ``terms``/``selected_translations`` would be wrong in
# both directions:
#
# * ``set_selected`` enforces the CORE-1400 publish gate — every selected
#   value must be a valid Python identifier. A symbol NAME is prose
#   ("opening parenthesis", "guion bajo"); it has spaces, and it is never
#   meant to be executed. It would be rejected, correctly.
# * ``find_collisions`` treats one value serving two term names as a
#   round-trip break. Vocabulary is not a token map — nothing reverses a
#   symbol name back into source code — so that guard would fire on
#   perfectly good data.
#
# Hence a partition of its own, shaped exactly like the term trio so the
# same invariant holds and reads the same way: ``vocabulary_translations``
# is a dirty-tolerant candidate pool, ``selected_vocabulary`` is the
# publish-gated layer the exporter reads, and nothing else writes packs.
#
# The canonical inventory (which slugs exist, their glyphs, their English
# names) lives in ``legesher_i18n/vocabulary_definitions.py``, not here:
# it is identical in all 51 languages, so it is code, and
# ``scripts/seed_vocabulary.py`` projects it into ``vocabulary_entries``.
# That is why this table carries no glyph column — a glyph is canonical.
VOCABULARY_ENTRIES_TABLE = """
CREATE TABLE IF NOT EXISTS vocabulary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL CHECK (section IN ('symbols', 'variable_conventions')),
    slug TEXT NOT NULL,
    programming_language TEXT NOT NULL DEFAULT 'python',
    english_value TEXT NOT NULL,
    role TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(section, slug, programming_language)
);
"""

# Candidate pool. Mirrors ``translations``: many rows per (entry, language),
# one per source/value, so a re-generation adds rather than overwrites and
# cross-model convergence stays visible.
VOCABULARY_TRANSLATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS vocabulary_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    language_code TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT NOT NULL,
    model_version TEXT,
    confidence TEXT,
    model_rationale TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT,
    FOREIGN KEY (entry_id) REFERENCES vocabulary_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code) ON DELETE CASCADE,
    UNIQUE(entry_id, language_code, source, value)
);
"""

# The publish-gated layer: exactly one active value per entry+language, and
# the only thing ``yaml_exporter`` reads for these sections.
SELECTED_VOCABULARY_TABLE = """
CREATE TABLE IF NOT EXISTS selected_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    language_code TEXT NOT NULL,
    value TEXT NOT NULL,
    selected_at TEXT NOT NULL DEFAULT (datetime('now')),
    selected_by TEXT,
    selection_reason TEXT,
    FOREIGN KEY (entry_id) REFERENCES vocabulary_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code) ON DELETE CASCADE,
    UNIQUE(entry_id, language_code)
);
"""

# Indexes for optimized lookups
INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_terms_category
    ON terms(category);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_terms_lang
    ON terms(programming_language);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_translations_lookup
    ON translations(language_code, term_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_translations_source
    ON translations(source);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_translations_term_lang
    ON translations(term_id, language_code);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_selected_lookup
    ON selected_translations(language_code);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_vocabulary_entries_section
    ON vocabulary_entries(section);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_vocabulary_translations_lookup
    ON vocabulary_translations(language_code, entry_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_selected_vocabulary_lookup
    ON selected_vocabulary(language_code);
    """,
]


def get_schema() -> list[str]:
    """
    Get all schema statements for database initialization.

    Returns:
        List of SQL statements to create tables and indexes
    """
    return [
        TERMS_TABLE,
        LANGUAGES_TABLE,
        TRANSLATIONS_TABLE,
        SELECTED_TRANSLATIONS_TABLE,
        # CORE-1396. Every statement above and below is IF NOT EXISTS and
        # ``_init_db`` replays the whole list on every open, so an existing
        # ``translations.db`` grows the vocabulary partition the first time
        # any code opens it. No separate migration script is needed here —
        # unlike the messages partition, whose DDL lives in the v2 schema
        # file and therefore needed ``activate_messages_partition.py``.
        VOCABULARY_ENTRIES_TABLE,
        VOCABULARY_TRANSLATIONS_TABLE,
        SELECTED_VOCABULARY_TABLE,
    ] + INDEXES
