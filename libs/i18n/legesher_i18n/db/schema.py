"""Database schema definitions for translation storage.

This module contains SQL schema definitions for the four core tables:
- terms: Canonical list of reserved words, extensible across programming languages
- languages: Language registry with ISO standards and script metadata
- translations: One row per translation suggestion (per term, per language, per source)
- selected_translations: Tracks which translation is currently active for YAML packs

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
    ] + INDEXES
