"""Database schema definitions for translation storage.

This module contains SQL schema definitions for the four main tables:
- translations: Core translation data with metadata
- reviews: Community reviews and feedback on translations
- deep_contexts: Etymology and detailed explanations of programming terms
- linguistic_standards: Language-specific formatting guidelines
"""

# Translations table - core translation data
TRANSLATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code TEXT NOT NULL,
    term TEXT NOT NULL,
    term_type TEXT NOT NULL,
    translation TEXT NOT NULL,
    source TEXT NOT NULL,
    word_type TEXT,
    word_form TEXT,
    model_rationale TEXT,
    alternatives_considered TEXT,
    confidence TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT,
    UNIQUE(language_code, term, term_type, source)
);
"""

# Reviews table - community feedback on translations
REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translation_id INTEGER NOT NULL,
    reviewer_github TEXT,
    reviewer_proficiency TEXT,
    regional_variant TEXT,
    vote TEXT,
    emoji TEXT,
    comment TEXT,
    suggested_translation TEXT,
    alternatives_suggested TEXT,
    review_source TEXT,
    github_issue_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (translation_id) REFERENCES translations(id) ON DELETE CASCADE
);
"""

# Deep contexts table - detailed explanations of programming terms
DEEP_CONTEXTS_TABLE = """
CREATE TABLE IF NOT EXISTS deep_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE,
    term_type TEXT NOT NULL,
    etymology TEXT,
    explanation_simple TEXT,
    explanation_beginner TEXT,
    explanation_intermediate TEXT,
    explanation_expert TEXT,
    concept_agnostic TEXT,
    translation_guidance TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Linguistic standards table - language-specific guidelines
LINGUISTIC_STANDARDS_TABLE = """
CREATE TABLE IF NOT EXISTS linguistic_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code TEXT NOT NULL UNIQUE,
    language_family TEXT,
    action_keyword_form TEXT,
    state_keyword_form TEXT,
    constant_form TEXT,
    guidelines TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Indexes for optimized lookups
INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_translations_lookup
    ON translations(language_code, term, term_type);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_translations_source
    ON translations(source);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_translation
    ON reviews(translation_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_github
    ON reviews(reviewer_github);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_contexts_term
    ON deep_contexts(term);
    """,
]


def get_schema() -> list[str]:
    """
    Get all schema statements for database initialization.

    Returns:
        List of SQL statements to create tables and indexes
    """
    return [
        TRANSLATIONS_TABLE,
        REVIEWS_TABLE,
        DEEP_CONTEXTS_TABLE,
        LINGUISTIC_STANDARDS_TABLE,
    ] + INDEXES
