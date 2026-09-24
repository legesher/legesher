-- ===========================================================================
-- Legesher translations schema v2 (CORE-1501): concept-centric, with an
-- endorsement corpus.
--
-- Structure only. What every table, column, trigger and view is for lives in
-- schema_v2.descriptions.yml beside this file; the two are rendered together
-- into libs/i18n/docs/schema-v2-reference.md by `make generate-schema-reference`,
-- which fails when they disagree or when a comment appears here outside this
-- header and the section banners.
--
-- Requires SQLite >= 3.31 (STORED generated columns). Verified on 3.51.
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- ===========================================================================
-- REFERENCE
-- ===========================================================================

CREATE TABLE programming_languages (
    code        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'planned'
                CHECK (status IN ('shipping', 'in_progress', 'planned')),
    spec_url    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE locales (
    tag                  TEXT PRIMARY KEY,
    parent_tag           TEXT REFERENCES locales(tag) ON DELETE RESTRICT,
    language_subtag      TEXT NOT NULL,
    script_subtag        TEXT,
    region_subtag        TEXT,
    name                 TEXT NOT NULL,
    native_name          TEXT NOT NULL,
    direction            TEXT NOT NULL DEFAULT 'ltr' CHECK (direction IN ('ltr', 'rtl')),
    numeral_system       TEXT,
    has_case_distinction INTEGER NOT NULL DEFAULT 1 CHECK (has_case_distinction IN (0, 1)),
    terminology_policy   TEXT,
    iso639_3             TEXT,
    status               TEXT NOT NULL DEFAULT 'experimental'
                         CHECK (status IN ('experimental', 'in_review', 'official')),
    in_registry          INTEGER NOT NULL DEFAULT 0 CHECK (in_registry IN (0, 1)),
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (
        tag GLOB '[a-z][a-z]'
     OR tag GLOB '[a-z][a-z][a-z]'
     OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]'
     OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]'
     OR tag GLOB '[a-z][a-z]-[A-Z][A-Z]'
     OR tag GLOB '[a-z][a-z][a-z]-[A-Z][A-Z]'
     OR tag GLOB '[a-z][a-z]-[0-9][0-9][0-9]'
     OR tag GLOB '[a-z][a-z][a-z]-[0-9][0-9][0-9]'
     OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]-[A-Z][A-Z]'
     OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]-[A-Z][A-Z]'
     OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]-[0-9][0-9][0-9]'
     OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]-[0-9][0-9][0-9]'
    ),
    CHECK (language_subtag GLOB '[a-z][a-z]' OR language_subtag GLOB '[a-z][a-z][a-z]'),
    CHECK (script_subtag IS NULL OR script_subtag GLOB '[A-Z][a-z][a-z][a-z]'),
    CHECK (region_subtag IS NULL
           OR region_subtag GLOB '[A-Z][A-Z]'
           OR region_subtag GLOB '[0-9][0-9][0-9]'),
    CHECK (
        tag = language_subtag
              || CASE WHEN script_subtag IS NULL THEN '' ELSE '-' || script_subtag END
              || CASE WHEN region_subtag IS NULL THEN '' ELSE '-' || region_subtag END
    ),
    CHECK (parent_tag IS NULL OR parent_tag <> tag)
);

CREATE INDEX idx_locales_parent ON locales(parent_tag);

CREATE TABLE concepts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    slug              TEXT NOT NULL UNIQUE,
    definition_en     TEXT NOT NULL,
    definition_source TEXT,
    category          TEXT NOT NULL,
    pattern_class     TEXT,
    notes             TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (slug = LOWER(slug) AND slug NOT LIKE '% %' AND instr(slug, char(31)) = 0)
);

CREATE TABLE concept_slug_aliases (
    alias       TEXT PRIMARY KEY,
    concept_id  INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    retired_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reason      TEXT
);

CREATE TABLE concept_briefs (
    concept_id  INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    tier        INTEGER NOT NULL DEFAULT 1 CHECK (tier IN (1, 2)),
    path        TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (concept_id, tier)
);

CREATE TABLE concept_relations (
    concept_id      INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    related_concept INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relation        TEXT NOT NULL
                    CHECK (relation IN ('consistency_group',
                                        'contrast',
                                        'supersedes')),
    note            TEXT,
    PRIMARY KEY (concept_id, related_concept, relation),
    CHECK (concept_id <> related_concept)
);

CREATE TABLE terms (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    programming_language TEXT NOT NULL REFERENCES programming_languages(code) ON DELETE RESTRICT,
    name                 TEXT NOT NULL,
    category             TEXT NOT NULL,
    subcategory          TEXT,
    version_added        TEXT,
    version_removed      TEXT,
    usage_note           TEXT,
    doc_url              TEXT,
    export_role          TEXT NOT NULL DEFAULT 'primary'
                         CHECK (export_role IN ('primary', 'secondary')),
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (programming_language, name, concept_id)
);

CREATE UNIQUE INDEX idx_terms_one_primary
    ON terms(programming_language, name) WHERE export_role = 'primary';
CREATE INDEX idx_terms_concept ON terms(concept_id);
CREATE INDEX idx_terms_pl      ON terms(programming_language, category);
CREATE INDEX idx_terms_name    ON terms(name);

-- ===========================================================================
-- CORPUS
-- ===========================================================================

CREATE TABLE review_rungs (
    rung             TEXT PRIMARY KEY,
    rank             INTEGER NOT NULL UNIQUE,
    weight           REAL NOT NULL CHECK (weight >= 0),
    counts_as_native INTEGER NOT NULL DEFAULT 0 CHECK (counts_as_native IN (0, 1)),
    policy_version   TEXT NOT NULL,
    description      TEXT
);

INSERT INTO review_rungs (rung, rank, weight, counts_as_native, policy_version, description) VALUES
    ('anonymous',      0, 0.0, 0, 'v0-draft', 'Unauthenticated signal. Recorded, weighted zero; brigading evidence.'),
    ('contributor',    1, 1.0, 0, 'v0-draft', 'Authenticated account, no verified native claim.'),
    ('native_claimed', 2, 2.0, 0, 'v0-draft', 'Self-declared native speaker of the locale.'),
    ('native_verified',3, 4.0, 1, 'v0-draft', 'Native status vouched by a maintainer or ambassador.'),
    ('certified',      4, 8.0, 1, 'v0-draft', 'Certified Contributor (CORE-1446); paid-reviewer eligible.'),
    ('maintainer',     5, 8.0, 1, 'v0-draft', 'Legesher maintainer. Same weight as certified by design.');

CREATE TABLE contributors (
    id           TEXT PRIMARY KEY,
    current_rung TEXT NOT NULL DEFAULT 'contributor' REFERENCES review_rungs(rung),
    joined_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (id GLOB 'c_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
                || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

CREATE TABLE contributor_identities (
    contributor_id        TEXT PRIMARY KEY REFERENCES contributors(id) ON DELETE CASCADE,
    source_key            TEXT UNIQUE,
    display_name          TEXT,
    github_handle         TEXT,
    contact               TEXT,
    consent_public_credit INTEGER NOT NULL DEFAULT 0 CHECK (consent_public_credit IN (0, 1)),
    consent_version       TEXT,
    consent_at            TEXT,
    credit_preference     TEXT NOT NULL DEFAULT 'anonymous'
                          CHECK (credit_preference IN ('anonymous', 'handle', 'name')),
    email                 TEXT
                          CHECK (email IS NULL
                                 OR (email = TRIM(email)
                                     AND email NOT LIKE '% %'
                                     AND email NOT GLOB '*' || char(9)  || '*'
                                     AND email NOT GLOB '*' || char(10) || '*'
                                     AND email NOT GLOB '*' || char(13) || '*'
                                     AND email LIKE '%_@_%.%_'
                                     AND email NOT LIKE '%@%@%')),
    email_verified_at     TEXT,
    withdrawn_at          TEXT,
    CHECK (credit_preference <> 'name'   OR display_name  IS NOT NULL),
    CHECK (credit_preference <> 'handle' OR github_handle IS NOT NULL)
);

CREATE TABLE build_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE options (
    uid                  TEXT PRIMARY KEY,
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale               TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope             TEXT NOT NULL
                         GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    surface_form         TEXT NOT NULL,
    first_seen_at        TEXT NOT NULL DEFAULT (datetime('now')),
    withdrawn_at         TEXT,
    UNIQUE (concept_id, locale, pl_scope, surface_form),
    CHECK (uid GLOB 'opt_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    CHECK (surface_form <> ''
           AND surface_form = TRIM(surface_form, char(9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
                                                      133, 160, 5760, 8192, 8193, 8194, 8195,
                                                      8196, 8197, 8198, 8199, 8200, 8201, 8202,
                                                      8232, 8233, 8239, 8287, 12288))),
    CHECK (instr(surface_form, char(31)) = 0)
);

CREATE UNIQUE INDEX idx_options_identity ON options(uid, concept_id, locale);
CREATE INDEX idx_options_lookup ON options(locale, concept_id);

CREATE TABLE option_provenance (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    option_uid     TEXT NOT NULL REFERENCES options(uid) ON DELETE CASCADE,
    source         TEXT NOT NULL
                   CHECK (source IN
                     ('legesher',
                      'upstream',
                      'community',
                      'model')),
    source_detail  TEXT,
    model_version  TEXT,
    contributor_id TEXT REFERENCES contributors(id) ON DELETE SET NULL,
    word_type      TEXT,
    word_form      TEXT,
    confidence     TEXT,
    rationale      TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (source <> 'model' OR model_version IS NOT NULL OR source_detail IS NOT NULL)
);

CREATE INDEX idx_provenance_option ON option_provenance(option_uid);
CREATE INDEX idx_provenance_source ON option_provenance(source);

CREATE TABLE endorsements (
    uid                 TEXT PRIMARY KEY,
    option_uid          TEXT NOT NULL REFERENCES options(uid) ON DELETE CASCADE,
    contributor_id      TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    method              TEXT NOT NULL
                        CHECK (method IN ('portal',
                                          'survey',
                                          'workshop',
                                          'github',
                                          'interview',
                                          'import')),
    rung_at_endorsement TEXT NOT NULL REFERENCES review_rungs(rung),
    comment             TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at        TEXT,
    CHECK (uid GLOB 'end_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

CREATE UNIQUE INDEX idx_endorsement_one_per_person
    ON endorsements(option_uid, contributor_id) WHERE retracted_at IS NULL;
CREATE INDEX idx_endorsement_option ON endorsements(option_uid);
CREATE INDEX idx_endorsement_contributor ON endorsements(contributor_id);

CREATE TABLE option_flags (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    option_uid     TEXT NOT NULL REFERENCES options(uid) ON DELETE CASCADE,
    contributor_id TEXT REFERENCES contributors(id) ON DELETE SET NULL,
    reason         TEXT NOT NULL
                   CHECK (reason IN ('offensive', 'wrong_meaning', 'register_mismatch',
                                     'invalid_identifier', 'transliteration', 'spam')),
    note           TEXT,
    resolved_at    TEXT,
    resolution     TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_flags_option ON option_flags(option_uid);

CREATE TABLE option_validations (
    option_uid          TEXT PRIMARY KEY REFERENCES options(uid) ON DELETE CASCADE,
    validator_version   TEXT NOT NULL,
    identifier_valid    INTEGER NOT NULL CHECK (identifier_valid IN (0, 1)),
    nfkc_stable         INTEGER NOT NULL CHECK (nfkc_stable IN (0, 1)),
    nfkc_delta_class    TEXT CHECK (nfkc_delta_class IS NULL
                                    OR nfkc_delta_class IN ('sara-am-only', 'other')),
    script_consistent   INTEGER NOT NULL CHECK (script_consistent IN (0, 1)),
    collides_en_keyword INTEGER NOT NULL DEFAULT 0 CHECK (collides_en_keyword IN (0, 1)),
    min_interpreter_ok  INTEGER NOT NULL DEFAULT 1 CHECK (min_interpreter_ok IN (0, 1)),
    format_chars_clean  INTEGER CHECK (format_chars_clean IN (0, 1)),
    checked_at          TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (validator_version <> '' AND validator_version = TRIM(validator_version))
);

CREATE TABLE option_screenings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    option_uid     TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    verdict        TEXT NOT NULL
                   CHECK (verdict IN ('quarantined',
                                      'cleared',
                                      'held',
                                      'rejected')),
    screened_by    TEXT NOT NULL,
    screen_version TEXT NOT NULL,
    note           TEXT,
    screened_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (screened_by <> '' AND screen_version <> '')
);

CREATE INDEX idx_screenings_option ON option_screenings(option_uid, id);

CREATE TRIGGER trg_screenings_append_only
BEFORE UPDATE ON option_screenings
BEGIN SELECT RAISE(ABORT, 'option_screenings are append-only: write a new verdict'); END;
CREATE TRIGGER trg_screenings_no_delete
BEFORE DELETE ON option_screenings
BEGIN SELECT RAISE(ABORT, 'option_screenings are append-only: the audit trail stays'); END;

CREATE VIEW option_screening_status AS
SELECT s.option_uid, s.verdict, s.screened_by, s.screen_version, s.note, s.screened_at
FROM option_screenings s
WHERE s.id = (SELECT MAX(s2.id) FROM option_screenings s2
               WHERE s2.option_uid = s.option_uid);

CREATE VIEW option_withheld AS
SELECT option_uid, verdict FROM option_screening_status WHERE verdict <> 'cleared';

-- ===========================================================================
-- CANON
-- ===========================================================================

CREATE TABLE canon_selections (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale               TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope             TEXT NOT NULL
                         GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    option_uid           TEXT NOT NULL,
    surface_form         TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'machine'
                         CHECK (status IN ('machine',
                                           'experimental',
                                           'reviewed',
                                           'official')),
    identity_ok          INTEGER NOT NULL DEFAULT 0 CHECK (identity_ok IN (0, 1)),
    decided_by           TEXT,
    decided_at           TEXT NOT NULL DEFAULT (datetime('now')),
    decision_reason      TEXT,
    source_file          TEXT NOT NULL,
    source_revision      TEXT,
    UNIQUE (concept_id, locale, pl_scope),
    FOREIGN KEY (option_uid, concept_id, locale)
        REFERENCES options(uid, concept_id, locale) ON DELETE RESTRICT
);

CREATE INDEX idx_canon_locale ON canon_selections(locale, status);
CREATE INDEX idx_canon_concept ON canon_selections(concept_id);

-- ===========================================================================
-- TRIGGERS
-- ===========================================================================

CREATE TRIGGER trg_options_append_only
BEFORE UPDATE OF concept_id, locale, programming_language, surface_form, uid,
                 first_seen_at ON options
BEGIN
    SELECT RAISE(ABORT, 'options are append-only: withdraw the row, do not edit it');
END;

CREATE TRIGGER trg_options_withdrawal_is_final
BEFORE UPDATE OF withdrawn_at ON options
WHEN OLD.withdrawn_at IS NOT NULL AND NEW.withdrawn_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'options are append-only: a withdrawal cannot be reversed');
END;

CREATE TRIGGER trg_options_no_delete
BEFORE DELETE ON options
BEGIN
    SELECT RAISE(ABORT,
        'options are append-only: DELETE would cascade away the endorsements; withdraw instead');
END;

CREATE TRIGGER trg_provenance_append_only
BEFORE UPDATE OF id, option_uid, source, source_detail, model_version, created_at
ON option_provenance
BEGIN
    SELECT RAISE(ABORT, 'option_provenance is append-only');
END;

CREATE TRIGGER trg_provenance_no_delete
BEFORE DELETE ON option_provenance
BEGIN
    SELECT RAISE(ABORT, 'option_provenance is append-only');
END;

CREATE TRIGGER trg_endorsements_append_only
BEFORE UPDATE OF uid, option_uid, contributor_id, method, rung_at_endorsement, created_at
ON endorsements
BEGIN
    SELECT RAISE(ABORT,
        'endorsements are append-only: retract the row and add a new one, do not edit it');
END;

CREATE TRIGGER trg_endorsements_retraction_is_final
BEFORE UPDATE OF retracted_at ON endorsements
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'endorsements are append-only: a retraction cannot be reversed');
END;

CREATE TRIGGER trg_endorsements_no_delete
BEFORE DELETE ON endorsements
BEGIN
    SELECT RAISE(ABORT, 'endorsements are append-only: retract, do not delete');
END;

CREATE TRIGGER trg_contributor_id_is_immutable
BEFORE UPDATE OF id ON contributors
BEGIN
    SELECT RAISE(ABORT, 'contributors.id is the published key: it cannot be repointed');
END;

CREATE TRIGGER trg_validations_frozen_under_canon
BEFORE UPDATE ON option_validations
WHEN EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.option_uid)
BEGIN
    SELECT RAISE(ABORT,
        'option_validations: this option is canon-selected; drop the canon row before revalidating');
END;

CREATE TRIGGER trg_validations_no_delete_under_canon
BEFORE DELETE ON option_validations
WHEN EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.option_uid)
BEGIN
    SELECT RAISE(ABORT,
        'option_validations: this option is canon-selected; drop the canon row first');
END;

CREATE TRIGGER trg_canon_scope_compatible
BEFORE INSERT ON canon_selections
WHEN (SELECT o.pl_scope FROM options o WHERE o.uid = NEW.option_uid)
     NOT IN ('*', COALESCE(NEW.programming_language, '*'))
BEGIN
    SELECT RAISE(ABORT, 'canon: option pl_scope does not cover this selection');
END;

CREATE TRIGGER trg_canon_requires_valid_identifier
BEFORE INSERT ON canon_selections
WHEN NOT EXISTS (
    SELECT 1 FROM option_validations v
    WHERE v.option_uid = NEW.option_uid
      AND v.identifier_valid = 1
      AND v.script_consistent = 1
      AND (v.nfkc_stable = 1 OR v.nfkc_delta_class = 'sara-am-only')
      AND v.format_chars_clean = 1
      AND v.validator_version <> 'migration-seed'
)
BEGIN
    SELECT RAISE(ABORT, 'canon: option is unvalidated or fails identifier/NFKC/script/format-char validation');
END;

CREATE TRIGGER trg_canon_surface_matches_option
BEFORE INSERT ON canon_selections
WHEN NEW.surface_form <> (SELECT o.surface_form FROM options o WHERE o.uid = NEW.option_uid)
BEGIN
    SELECT RAISE(ABORT, 'canon: surface_form does not match the selected option');
END;

CREATE TRIGGER trg_canon_no_withdrawn_option
BEFORE INSERT ON canon_selections
WHEN (SELECT o.withdrawn_at FROM options o WHERE o.uid = NEW.option_uid) IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'canon: option has been withdrawn');
END;

CREATE TRIGGER trg_canon_no_quarantined_option
BEFORE INSERT ON canon_selections
WHEN EXISTS (
    SELECT 1 FROM option_withheld q WHERE q.option_uid = NEW.option_uid
)
BEGIN
    SELECT RAISE(ABORT,
        'canon: option is quarantined pending moderation (CORE-1828); clear it first');
END;

CREATE TRIGGER trg_screenings_no_quarantine_while_canon
BEFORE INSERT ON option_screenings
WHEN NEW.verdict <> 'cleared'
 AND EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = NEW.option_uid)
BEGIN
    SELECT RAISE(ABORT,
        'option_screenings: option is canon-selected; remove it from the canon file first');
END;

CREATE TRIGGER trg_canon_no_update
BEFORE UPDATE ON canon_selections
BEGIN
    SELECT RAISE(ABORT,
        'canon_selections is a loaded projection: edit libs/i18n/canon/<locale>.toml and reload');
END;

CREATE TRIGGER trg_options_no_withdraw_while_canon
BEFORE UPDATE OF withdrawn_at ON options
WHEN NEW.withdrawn_at IS NOT NULL
 AND OLD.withdrawn_at IS NULL
 AND EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.uid)
BEGIN
    SELECT RAISE(ABORT,
        'options: this option is canon-selected; remove it from the canon file before withdrawing');
END;

-- ===========================================================================
-- VIEWS
-- ===========================================================================

CREATE VIEW locale_fallback AS
WITH RECURSIVE chain(request_tag, resolved_tag, depth) AS (
    SELECT tag, tag, 0 FROM locales
    UNION ALL
    SELECT c.request_tag, l.parent_tag, c.depth + 1
    FROM chain c
    JOIN locales l ON l.tag = c.resolved_tag
    WHERE l.parent_tag IS NOT NULL
)
SELECT request_tag, resolved_tag, depth FROM chain;

CREATE VIEW endorsement_counts AS
SELECT
    o.uid                                        AS option_uid,
    COUNT(e.uid)                                 AS endorsements,
    COUNT(DISTINCT e.contributor_id)             AS endorsers,
    COALESCE(SUM(r.weight), 0.0)                 AS weighted_endorsement,
    COUNT(CASE WHEN r.counts_as_native = 1 THEN 1 END) AS native_verified_or_above,
    MIN(e.created_at)                            AS first_endorsed_at,
    MAX(e.created_at)                            AS last_endorsed_at
FROM options o
LEFT JOIN endorsements e
       ON e.option_uid = o.uid AND e.retracted_at IS NULL
LEFT JOIN review_rungs r
       ON r.rung = e.rung_at_endorsement
GROUP BY o.uid;

CREATE VIEW option_standings AS
SELECT
    c.slug                       AS concept_slug,
    o.locale,
    o.pl_scope,
    o.uid                        AS option_uid,
    o.surface_form,
    ec.endorsements,
    ec.weighted_endorsement,
    ec.native_verified_or_above,
    o.withdrawn_at,
    (SELECT GROUP_CONCAT(DISTINCT p.source)
       FROM option_provenance p WHERE p.option_uid = o.uid) AS sources,
    (SELECT COUNT(*) FROM option_flags f
      WHERE f.option_uid = o.uid AND f.resolved_at IS NULL)  AS open_flags,
    COALESCE(v.identifier_valid, 0)  AS identifier_valid,
    COALESCE(v.nfkc_stable, 0)       AS nfkc_stable,
    COALESCE(v.script_consistent, 0) AS script_consistent,
    COALESCE(v.format_chars_clean, 0) AS format_chars_clean,
    v.nfkc_delta_class,
    RANK() OVER (
        PARTITION BY o.concept_id, o.locale, o.pl_scope
        ORDER BY ec.weighted_endorsement DESC, ec.endorsements DESC, o.surface_form ASC
    )                            AS standing
FROM options o
JOIN concepts c            ON c.id = o.concept_id
JOIN endorsement_counts ec ON ec.option_uid = o.uid
LEFT JOIN option_validations v ON v.option_uid = o.uid
WHERE NOT EXISTS (
    SELECT 1 FROM option_withheld q WHERE q.option_uid = o.uid
);

CREATE VIEW canon_resolution AS
SELECT
    f.request_tag   AS locale,
    f.resolved_tag  AS resolved_locale,
    f.depth         AS locale_distance,
    cs.concept_id,
    cs.pl_scope,
    cs.surface_form,
    cs.status,
    cs.option_uid,
    cs.identity_ok
FROM locale_fallback f
JOIN canon_selections cs ON cs.locale = f.resolved_tag;

CREATE VIEW term_resolution AS
WITH ranked AS (
    SELECT
        t.id              AS term_id,
        t.export_role,
        t.programming_language,
        r.locale,
        t.name            AS english_term,
        t.category,
        t.subcategory,
        t.version_added,
        t.version_removed,
        c.slug            AS concept_slug,
        r.surface_form    AS translation,
        r.status,
        r.identity_ok,
        r.option_uid,
        r.resolved_locale,
        r.locale_distance,
        CASE WHEN r.pl_scope = t.programming_language
             THEN 'pl_override' ELSE 'concept_wide' END AS scope,
        ROW_NUMBER() OVER (
            PARTITION BY t.programming_language, r.locale, t.id
            ORDER BY r.locale_distance ASC,
                     CASE WHEN r.pl_scope = t.programming_language THEN 0 ELSE 1 END ASC
        ) AS rk
    FROM terms t
    JOIN concepts c ON c.id = t.concept_id
    JOIN canon_resolution r
      ON r.concept_id = t.concept_id
     AND r.pl_scope IN ('*', t.programming_language)
)
SELECT term_id, export_role, programming_language, locale, english_term, category,
       subcategory, concept_slug, translation, status, identity_ok, option_uid,
       resolved_locale, locale_distance, scope, version_added, version_removed
FROM ranked
WHERE rk = 1;

CREATE VIEW pack_export AS
SELECT programming_language, locale, english_term, category, subcategory,
       concept_slug, translation, status, identity_ok, option_uid,
       resolved_locale, locale_distance, scope, version_added, version_removed
FROM term_resolution
WHERE export_role = 'primary';

CREATE VIEW canon_coverage AS
SELECT
    locale,
    pl_scope,
    COUNT(*)                    AS canon_terms,
    SUM(identity_ok)            AS identity_cognates,
    COUNT(*) - SUM(identity_ok) AS translated_terms
FROM canon_selections
GROUP BY locale, pl_scope;

CREATE VIEW pack_export_conflicts AS
SELECT
    programming_language,
    locale,
    english_term,
    COUNT(DISTINCT translation) AS distinct_renderings,
    GROUP_CONCAT(DISTINCT translation) AS renderings
FROM term_resolution
GROUP BY programming_language, locale, english_term
HAVING COUNT(DISTINCT translation) > 1;

CREATE VIEW canon_collisions AS
SELECT
    p1.programming_language,
    p1.locale,
    p1.translation,
    GROUP_CONCAT(DISTINCT p1.english_term) AS english_terms,
    COUNT(DISTINCT p1.concept_slug)        AS concepts
FROM pack_export p1
GROUP BY p1.programming_language, p1.locale, p1.translation
HAVING COUNT(DISTINCT p1.concept_slug) > 1;

CREATE VIEW review_queue AS
SELECT
    l.tag                 AS locale,
    c.slug                AS concept_slug,
    c.definition_en,
    c.category            AS concept_category,
    cs.surface_form       AS current_selection,
    COALESCE(cs.status, 'none') AS status,
    (SELECT COUNT(*) FROM options o
      WHERE o.concept_id = c.id AND o.locale = l.tag AND o.withdrawn_at IS NULL)
                          AS candidate_options,
    (SELECT COALESCE(SUM(ec.endorsements), 0)
       FROM options o JOIN endorsement_counts ec ON ec.option_uid = o.uid
      WHERE o.concept_id = c.id AND o.locale = l.tag AND o.withdrawn_at IS NULL)
                          AS total_endorsements,
    (SELECT GROUP_CONCAT(DISTINCT t.programming_language)
       FROM terms t WHERE t.concept_id = c.id) AS used_by,
    (SELECT GROUP_CONCAT(DISTINCT t.name)
       FROM terms t WHERE t.concept_id = c.id) AS surface_forms
FROM concepts c
CROSS JOIN locales l
LEFT JOIN canon_selections cs
       ON cs.concept_id = c.id AND cs.locale = l.tag AND cs.pl_scope = '*'
WHERE l.in_registry = 1
  AND (cs.status IS NULL OR cs.status IN ('machine', 'experimental'));

CREATE VIEW locale_progress AS
SELECT
    t.programming_language,
    l.tag                                          AS locale,
    l.name                                         AS locale_name,
    COUNT(DISTINCT t.concept_id)                   AS concepts_needed,
    COUNT(DISTINCT cs.concept_id)                  AS concepts_selected,
    COUNT(DISTINCT CASE WHEN cs.status IN ('reviewed', 'official')
                        THEN cs.concept_id END)    AS concepts_reviewed,
    COUNT(DISTINCT CASE WHEN cs.status = 'official'
                        THEN cs.concept_id END)    AS concepts_official
FROM terms t
CROSS JOIN locales l
LEFT JOIN canon_selections cs
       ON cs.concept_id = t.concept_id
      AND cs.locale = l.tag
      AND cs.pl_scope IN ('*', t.programming_language)
WHERE t.export_role = 'primary'
GROUP BY t.programming_language, l.tag;

CREATE VIEW new_pl_reuse AS
SELECT
    t.programming_language,
    cs.locale,
    COUNT(DISTINCT t.concept_id)   AS concepts_total,
    COUNT(DISTINCT cs.concept_id)  AS concepts_already_selected,
    COUNT(DISTINCT CASE WHEN cs.status IN ('reviewed', 'official')
                        THEN cs.concept_id END) AS concepts_already_reviewed
FROM terms t
LEFT JOIN canon_selections cs
       ON cs.concept_id = t.concept_id AND cs.pl_scope = '*'
WHERE t.export_role = 'primary'
GROUP BY t.programming_language, cs.locale;

-- ===========================================================================
-- DEFERRED
-- ===========================================================================

CREATE TABLE message_templates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    implementation TEXT NOT NULL,
    key            TEXT NOT NULL,
    template_en    TEXT NOT NULL,
    placeholders   TEXT,
    matcher        TEXT,
    concept_id     INTEGER REFERENCES concepts(id) ON DELETE SET NULL,
    version_added  TEXT,
    version_removed TEXT,
    UNIQUE (implementation, key, version_added)
);

CREATE TABLE message_translations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES message_templates(id) ON DELETE CASCADE,
    locale      TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    template    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'machine'
                CHECK (status IN ('machine', 'experimental', 'reviewed', 'official')),
    source      TEXT,
    model_version TEXT,
    created_by  TEXT,
    UNIQUE (template_id, locale)
);

-- ===========================================================================
-- REVIEW INTAKE
-- ===========================================================================

CREATE TABLE import_sources (
    id              TEXT PRIMARY KEY,
    kind            TEXT NOT NULL CHECK (kind IN ('model', 'initiative', 'dataset')),
    name            TEXT NOT NULL,
    url             TEXT,
    license_spdx    TEXT,
    redistributable INTEGER NOT NULL DEFAULT 0 CHECK (redistributable IN (0, 1)),
    attribution     TEXT,
    fetched_ref     TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (id = LOWER(id) AND id NOT LIKE '% %' AND instr(id, char(31)) = 0),
    CHECK (redistributable = 0 OR license_spdx IS NOT NULL)
);

CREATE TABLE review_sessions (
    uid                 TEXT PRIMARY KEY,
    contributor_id      TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    locale              TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    track               TEXT NOT NULL
                        CHECK (track IN ('reserved_words', 'messages', 'style_profile')),
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope            TEXT NOT NULL
                        GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    method              TEXT NOT NULL
                        CHECK (method IN ('portal', 'survey', 'workshop', 'github',
                                          'interview', 'import')),
    kit_version         TEXT NOT NULL,
    app_version         TEXT,
    rung_at_session     TEXT NOT NULL REFERENCES review_rungs(rung),
    bundle_digest       TEXT NOT NULL,
    contact_captured    INTEGER NOT NULL DEFAULT 0 CHECK (contact_captured IN (0, 1)),
    started_at          TEXT,
    submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
    status              TEXT NOT NULL DEFAULT 'submitted'
                        CHECK (status IN ('submitted', 'verifying', 'accepted',
                                          'returned', 'rejected')),
    verification_report TEXT,
    notes               TEXT,
    CHECK (uid GLOB 'ses_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    CHECK (bundle_digest NOT GLOB '*[^0-9a-f]*' AND length(bundle_digest) = 64),
    CHECK (uid = 'ses_' || substr(bundle_digest, 1, 24)),
    CHECK (track <> 'style_profile' OR programming_language IS NULL)
);

CREATE INDEX idx_sessions_locale ON review_sessions(locale, track, status);
CREATE INDEX idx_sessions_contributor ON review_sessions(contributor_id);

CREATE TRIGGER trg_sessions_evidence_frozen
BEFORE UPDATE OF uid, contributor_id, locale, track, programming_language, method,
                 kit_version, app_version, rung_at_session, bundle_digest,
                 contact_captured, started_at, submitted_at ON review_sessions
BEGIN
    SELECT RAISE(ABORT,
        'review_sessions: evidence is append-only; only status/verification_report/notes may change');
END;

CREATE TRIGGER trg_sessions_terminal_states
BEFORE UPDATE OF status ON review_sessions
WHEN OLD.status IN ('accepted', 'rejected') AND NEW.status <> OLD.status
BEGIN
    SELECT RAISE(ABORT, 'review_sessions: accepted/rejected are terminal; resubmit as a new bundle');
END;

CREATE TRIGGER trg_sessions_no_delete
BEFORE DELETE ON review_sessions
BEGIN
    SELECT RAISE(ABORT, 'review_sessions are append-only');
END;

CREATE TRIGGER trg_sessions_report_frozen_when_terminal
BEFORE UPDATE OF verification_report, notes ON review_sessions
WHEN OLD.status IN ('accepted', 'rejected') AND NEW.status = OLD.status
BEGIN
    SELECT RAISE(ABORT,
        'review_sessions: the verification report is frozen once the session is terminal');
END;

CREATE TABLE session_options (
    session_uid  TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    option_uid   TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    elicited     TEXT NOT NULL CHECK (elicited IN ('blind',
                                                   'after_reveal',
                                                   'quick')),
    PRIMARY KEY (session_uid, option_uid)
) WITHOUT ROWID;

CREATE TRIGGER trg_session_options_frozen
BEFORE UPDATE ON session_options
BEGIN SELECT RAISE(ABORT, 'session_options is append-only'); END;
CREATE TRIGGER trg_session_options_no_delete
BEFORE DELETE ON session_options
BEGIN SELECT RAISE(ABORT, 'session_options is append-only'); END;

CREATE TABLE session_endorsements (
    session_uid     TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    endorsement_uid TEXT NOT NULL REFERENCES endorsements(uid) ON DELETE RESTRICT,
    PRIMARY KEY (session_uid, endorsement_uid)
) WITHOUT ROWID;

CREATE TRIGGER trg_session_endorsements_frozen
BEFORE UPDATE ON session_endorsements
BEGIN SELECT RAISE(ABORT, 'session_endorsements is append-only'); END;
CREATE TRIGGER trg_session_endorsements_no_delete
BEFORE DELETE ON session_endorsements
BEGIN SELECT RAISE(ABORT, 'session_endorsements is append-only'); END;

CREATE TRIGGER trg_session_endorsements_same_contributor
BEFORE INSERT ON session_endorsements
WHEN (SELECT e.contributor_id FROM endorsements e WHERE e.uid = NEW.endorsement_uid)
  <> (SELECT s.contributor_id FROM review_sessions s WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT,
        'session_endorsements: endorsement belongs to a different contributor than the session');
END;

CREATE TABLE session_rankings (
    session_uid  TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    concept_id   INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale       TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope     TEXT NOT NULL
                 GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    option_uid   TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    rank         INTEGER NOT NULL CHECK (rank >= 1),
    revised_after_reveal INTEGER NOT NULL DEFAULT 0
                 CHECK (revised_after_reveal IN (0, 1)),
    comment      TEXT,
    UNIQUE (session_uid, concept_id, locale, pl_scope, option_uid)
);

CREATE UNIQUE INDEX uq_ranking_slot
    ON session_rankings(session_uid, concept_id, locale, pl_scope, rank);
CREATE INDEX idx_rankings_option ON session_rankings(option_uid);

CREATE TRIGGER trg_ranking_requires_endorsement
BEFORE INSERT ON session_rankings
WHEN NOT EXISTS (
    SELECT 1
    FROM endorsements e
    JOIN review_sessions s ON s.uid = NEW.session_uid
    WHERE e.option_uid = NEW.option_uid
      AND e.contributor_id = s.contributor_id
      AND e.retracted_at IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'session_rankings: rank only options this contributor has endorsed');
END;

CREATE TRIGGER trg_ranking_option_matches_concept
BEFORE INSERT ON session_rankings
WHEN NOT EXISTS (
    SELECT 1 FROM options o
    WHERE o.uid = NEW.option_uid
      AND o.concept_id = NEW.concept_id
      AND o.locale = NEW.locale
      AND o.pl_scope IN ('*', NEW.pl_scope)
)
BEGIN
    SELECT RAISE(ABORT, 'session_rankings: option does not render this concept/locale/scope');
END;

CREATE TRIGGER trg_ranking_locale_matches_session
BEFORE INSERT ON session_rankings
WHEN NEW.locale <> (SELECT s.locale FROM review_sessions s WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT, 'session_rankings: locale does not match the session locale');
END;

CREATE TRIGGER trg_rankings_append_only
BEFORE UPDATE ON session_rankings
BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only: a new session supersedes them'); END;
CREATE TRIGGER trg_rankings_no_delete
BEFORE DELETE ON session_rankings
BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only'); END;

CREATE TABLE option_annotations (
    uid             TEXT PRIMARY KEY,
    option_uid      TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    kind            TEXT NOT NULL
                    CHECK (kind IN ('transliteration',
                                    'cognate_loanword',
                                    'established_term',
                                    'coined_neologism',
                                    'register_formal',
                                    'register_informal',
                                    'regional')),
    comment         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at    TEXT,
    CHECK (uid GLOB 'ann_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

CREATE UNIQUE INDEX uq_annotation_once
    ON option_annotations(option_uid, contributor_id, kind)
    WHERE retracted_at IS NULL;
CREATE INDEX idx_annotations_option ON option_annotations(option_uid);

CREATE TRIGGER trg_annotations_contributor_matches_session
BEFORE INSERT ON option_annotations
WHEN NEW.session_uid IS NOT NULL
 AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                             WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT, 'option_annotations: contributor does not match the session contributor');
END;

CREATE TRIGGER trg_annotations_append_only
BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, kind, created_at
ON option_annotations
BEGIN SELECT RAISE(ABORT, 'option_annotations are append-only: retract, do not edit'); END;
CREATE TRIGGER trg_annotations_retraction_is_final
BEFORE UPDATE OF retracted_at ON option_annotations
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN SELECT RAISE(ABORT, 'option_annotations: a retraction cannot be reversed'); END;
CREATE TRIGGER trg_annotations_no_delete
BEFORE DELETE ON option_annotations
BEGIN SELECT RAISE(ABORT, 'option_annotations are append-only: retract, do not delete'); END;

CREATE TABLE option_expansions (
    uid             TEXT PRIMARY KEY,
    option_uid      TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    expansion       TEXT NOT NULL,
    formation_note  TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at    TEXT,
    CHECK (uid GLOB 'exp_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    CHECK (expansion <> '' AND instr(expansion, char(31)) = 0)
);

CREATE INDEX idx_expansions_option ON option_expansions(option_uid);

CREATE TRIGGER trg_expansions_contributor_matches_session
BEFORE INSERT ON option_expansions
WHEN NEW.session_uid IS NOT NULL
 AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                             WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT, 'option_expansions: contributor does not match the session contributor');
END;

CREATE TRIGGER trg_expansions_append_only
BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, expansion,
                 formation_note, created_at ON option_expansions
BEGIN SELECT RAISE(ABORT, 'option_expansions are append-only: retract, do not edit'); END;
CREATE TRIGGER trg_expansions_retraction_is_final
BEFORE UPDATE OF retracted_at ON option_expansions
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN SELECT RAISE(ABORT, 'option_expansions: a retraction cannot be reversed'); END;
CREATE TRIGGER trg_expansions_no_delete
BEFORE DELETE ON option_expansions
BEGIN SELECT RAISE(ABORT, 'option_expansions are append-only: retract, do not delete'); END;

CREATE TABLE concept_commentary (
    uid               TEXT PRIMARY KEY,
    contributor_id    TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid       TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    concept_id        INTEGER REFERENCES concepts(id) ON DELETE RESTRICT,
    locale            TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    topic             TEXT NOT NULL
                      CHECK (topic IN ('word_formation', 'expansion', 'register',
                                       'pedagogy', 'style', 'general')),
    body              TEXT NOT NULL,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at      TEXT,
    CHECK (uid GLOB 'com_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    CHECK (body <> '')
);

CREATE INDEX idx_commentary_concept ON concept_commentary(concept_id, locale);
CREATE INDEX idx_commentary_locale ON concept_commentary(locale, topic);

CREATE TRIGGER trg_commentary_contributor_matches_session
BEFORE INSERT ON concept_commentary
WHEN NEW.session_uid IS NOT NULL
 AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                             WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT, 'concept_commentary: contributor does not match the session contributor');
END;

CREATE TRIGGER trg_commentary_append_only
BEFORE UPDATE OF uid, contributor_id, session_uid, concept_id, locale, topic,
                 body, created_at ON concept_commentary
BEGIN SELECT RAISE(ABORT, 'concept_commentary is append-only: retract, do not edit'); END;
CREATE TRIGGER trg_commentary_retraction_is_final
BEFORE UPDATE OF retracted_at ON concept_commentary
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN SELECT RAISE(ABORT, 'concept_commentary: a retraction cannot be reversed'); END;
CREATE TRIGGER trg_commentary_no_delete
BEFORE DELETE ON concept_commentary
BEGIN SELECT RAISE(ABORT, 'concept_commentary is append-only: retract, do not delete'); END;

CREATE TABLE commentary_moderation (
    commentary_uid  TEXT PRIMARY KEY REFERENCES concept_commentary(uid) ON DELETE RESTRICT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'published', 'withheld')),
    moderated_by    TEXT,
    moderated_at    TEXT,
    note            TEXT
);

CREATE TABLE style_ratifications (
    uid             TEXT PRIMARY KEY,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    locale          TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    field           TEXT NOT NULL
                    CHECK (field IN ('word_boundaries', 'constants_strategy', 'class_marker',
                                     'modifier_order', 'abbreviation_granularity',
                                     'identifier_length_max', 'numerals_policy',
                                     'docstring_mood', 'terminology_policy', 'zen_preamble')),
    value           TEXT NOT NULL,
    rationale       TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at    TEXT,
    CHECK (uid GLOB 'sty_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    CHECK (value <> '')
);

CREATE UNIQUE INDEX uq_style_vote
    ON style_ratifications(locale, field, contributor_id)
    WHERE retracted_at IS NULL;

CREATE TRIGGER trg_style_contributor_matches_session
BEFORE INSERT ON style_ratifications
WHEN NEW.session_uid IS NOT NULL
 AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                             WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT, 'style_ratifications: contributor does not match the session contributor');
END;

CREATE TRIGGER trg_style_append_only
BEFORE UPDATE OF uid, contributor_id, session_uid, locale, field, value,
                 rationale, created_at ON style_ratifications
BEGIN SELECT RAISE(ABORT, 'style_ratifications are append-only: retract, do not edit'); END;
CREATE TRIGGER trg_style_retraction_is_final
BEFORE UPDATE OF retracted_at ON style_ratifications
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN SELECT RAISE(ABORT, 'style_ratifications: a retraction cannot be reversed'); END;
CREATE TRIGGER trg_style_no_delete
BEFORE DELETE ON style_ratifications
BEGIN SELECT RAISE(ABORT, 'style_ratifications are append-only: retract, do not delete'); END;

CREATE TABLE message_endorsements (
    uid                    TEXT PRIMARY KEY,
    message_translation_id INTEGER NOT NULL REFERENCES message_translations(id) ON DELETE RESTRICT,
    contributor_id         TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid            TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    method                 TEXT NOT NULL
                           CHECK (method IN ('portal', 'survey', 'workshop', 'github',
                                             'interview', 'import')),
    rung_at_endorsement    TEXT NOT NULL REFERENCES review_rungs(rung),
    comment                TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at           TEXT,
    CHECK (uid GLOB 'men_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

CREATE UNIQUE INDEX uq_message_endorsement_once
    ON message_endorsements(message_translation_id, contributor_id)
    WHERE retracted_at IS NULL;

CREATE TRIGGER trg_message_endorsements_append_only
BEFORE UPDATE OF uid, message_translation_id, contributor_id, session_uid,
                 method, rung_at_endorsement, created_at ON message_endorsements
BEGIN SELECT RAISE(ABORT, 'message_endorsements are append-only: retract, do not edit'); END;
CREATE TRIGGER trg_message_endorsements_retraction_is_final
BEFORE UPDATE OF retracted_at ON message_endorsements
WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
BEGIN SELECT RAISE(ABORT, 'message_endorsements: a retraction cannot be reversed'); END;
CREATE TRIGGER trg_message_endorsements_no_delete
BEFORE DELETE ON message_endorsements
BEGIN SELECT RAISE(ABORT, 'message_endorsements are append-only: retract, do not delete'); END;

CREATE VIEW latest_rankings AS
WITH scoped AS (
    SELECT
        r.session_uid, r.concept_id, r.locale, r.pl_scope, r.option_uid,
        r.rank, r.revised_after_reveal, r.comment,
        s.contributor_id, s.submitted_at,
        DENSE_RANK() OVER (
            PARTITION BY s.contributor_id, r.concept_id, r.locale, r.pl_scope
            ORDER BY s.submitted_at DESC, s.uid DESC
        ) AS session_recency
    FROM session_rankings r
    JOIN review_sessions s ON s.uid = r.session_uid
    WHERE s.status = 'accepted'
      AND EXISTS (
          SELECT 1 FROM endorsements e
          WHERE e.option_uid = r.option_uid
            AND e.contributor_id = s.contributor_id
            AND e.retracted_at IS NULL
      )
)
SELECT session_uid, contributor_id, concept_id, locale, pl_scope,
       option_uid, rank, revised_after_reveal, comment, submitted_at
FROM scoped
WHERE session_recency = 1;

CREATE VIEW option_promotion_status AS
SELECT
    s.concept_slug,
    s.locale,
    s.pl_scope,
    s.option_uid,
    s.surface_form,
    s.endorsements,
    s.weighted_endorsement,
    s.native_verified_or_above,
    s.open_flags,
    s.standing,
    (s.identifier_valid = 1
     AND s.script_consistent = 1
     AND s.format_chars_clean = 1
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS canon_eligible,
    (s.withdrawn_at IS NULL
     AND s.native_verified_or_above >= 2
     AND s.open_flags = 0
     AND s.identifier_valid = 1
     AND s.script_consistent = 1
     AND s.format_chars_clean = 1
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS reviewed_eligible
FROM option_standings s;

CREATE VIEW second_endorsement_queue AS
SELECT concept_slug, locale, pl_scope, option_uid, surface_form,
       native_verified_or_above, endorsements
FROM option_promotion_status
WHERE reviewed_eligible = 0
  AND canon_eligible = 1
  AND open_flags = 0
  AND native_verified_or_above = 1;

CREATE VIEW quarantine_queue AS
SELECT
    q.option_uid,
    c.slug          AS concept_slug,
    o.locale,
    o.pl_scope,
    o.surface_form,
    q.verdict,
    q.screened_by,
    q.screen_version,
    q.note,
    q.screened_at
FROM option_screening_status q
JOIN options o  ON o.uid = q.option_uid
JOIN concepts c ON c.id = o.concept_id
WHERE q.verdict <> 'cleared';

CREATE VIEW pack_promotion_status AS
SELECT
    lp.programming_language,
    lp.locale,
    lp.concepts_needed,
    lp.concepts_selected,
    lp.concepts_reviewed,
    lp.concepts_official,
    (SELECT COUNT(DISTINCT s.contributor_id)
       FROM review_sessions s
       JOIN review_rungs rr ON rr.rung = s.rung_at_session
      WHERE s.locale = lp.locale
        AND s.track = 'reserved_words'
        AND s.status = 'accepted'
        AND rr.counts_as_native = 1)                          AS native_reviewers,
    (SELECT COUNT(DISTINCT s.contributor_id)
       FROM review_sessions s
      WHERE s.locale = lp.locale
        AND s.track = 'reserved_words'
        AND s.status = 'accepted')                            AS total_reviewers,
    (SELECT COUNT(DISTINCT sr.field)
       FROM style_ratifications sr
      WHERE sr.locale = lp.locale AND sr.retracted_at IS NULL) AS style_fields_answered,
    (lp.concepts_selected = lp.concepts_needed)               AS fully_selected,
    CAST(lp.concepts_reviewed AS REAL) / NULLIF(lp.concepts_needed, 0) AS reviewed_ratio
FROM locale_progress lp;

CREATE VIEW terminology_export AS
SELECT
    c.slug                        AS concept_slug,
    o.locale,
    o.pl_scope,
    o.surface_form,
    (cs.option_uid = o.uid)       AS is_canon,
    cs.status                     AS canon_status,
    ec.endorsements,
    ec.native_verified_or_above,
    (SELECT GROUP_CONCAT(a.kind)
       FROM option_annotations a
      WHERE a.option_uid = o.uid AND a.retracted_at IS NULL)  AS descriptors,
    (SELECT x.expansion
       FROM option_expansions x
      WHERE x.option_uid = o.uid AND x.retracted_at IS NULL
      GROUP BY x.expansion
      ORDER BY COUNT(*) DESC, MIN(x.created_at) ASC
      LIMIT 1)                                                AS expansion
FROM options o
JOIN concepts c             ON c.id = o.concept_id
LEFT JOIN endorsement_counts ec ON ec.option_uid = o.uid
LEFT JOIN canon_selections cs
       ON cs.concept_id = o.concept_id
      AND cs.locale = o.locale
      AND cs.pl_scope = o.pl_scope
WHERE o.withdrawn_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM option_withheld q WHERE q.option_uid = o.uid
  );

CREATE VIEW transliteration_preference AS
SELECT
    o.locale,
    COUNT(DISTINCT o.uid)                                     AS live_options,
    COUNT(DISTINCT a.option_uid)                              AS options_tagged_translit,
    COUNT(DISTINCT CASE WHEN e.retracted_at IS NULL
                        THEN e.uid END)                       AS endorsements_on_translit
FROM options o
LEFT JOIN option_annotations a
       ON a.option_uid = o.uid AND a.retracted_at IS NULL AND a.kind = 'transliteration'
LEFT JOIN endorsements e
       ON e.option_uid = a.option_uid
WHERE o.withdrawn_at IS NULL
GROUP BY o.locale;
