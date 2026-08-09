-- ===========================================================================
-- Legesher translations schema v2 — concept-centric, with an endorsement corpus
-- CORE-1501. Supersedes the four-table v1 schema in schema.py.
--
-- The full design / migration / HF-dataset rationale lives in the CORE-1501
-- design docs, which are not part of this repository.
--
-- Three layers, and the boundary between them is load-bearing:
--
--   REFERENCE  programming_languages, locales, concepts, terms, briefs
--              Maintainer-curated. Small. Ships in the monorepo.
--
--   CORPUS     options, option_provenance, endorsements, option_flags,
--              option_validations, contributors
--              Community-writable, APPEND-ONLY, published to Hugging Face.
--              Every rendering anyone ever offered, and every person who
--              endorsed it. Counts are DERIVED (COUNT(*)), never stored.
--
--   CANON      canon_selections
--              The maintainer decision. Lives in the monorepo as PR-reviewable
--              text (libs/i18n/canon/<locale>.toml); this table is a LOADED
--              PROJECTION of those files, never a write target. Enforced by
--              source_file NOT NULL + a CI drift test. Never published as a
--              writable dataset.
--
-- Requires SQLite >= 3.31 (STORED generated columns). Verified on 3.51.
-- ===========================================================================

-- NOT PERSISTED. `foreign_keys` is a PER-CONNECTION setting that SQLite
-- defaults to OFF; this line only covers the connection that runs the DDL. A
-- fresh sqlite3.connect() to the resulting FILE reports foreign_keys = 0 and
-- every FK below is silently inert. Consumers must open the database through
-- schema_v2.connect() (or issue the pragma themselves) — asserted by
-- tests/test_schema_v2.py::test_foreign_keys_must_be_enabled_per_connection.
PRAGMA foreign_keys = ON;

-- ===========================================================================
-- REFERENCE
-- ===========================================================================

CREATE TABLE programming_languages (
    code        TEXT PRIMARY KEY,              -- 'python', 'javascript', 'rust'
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'planned'
                CHECK (status IN ('shipping', 'in_progress', 'planned')),
    spec_url    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One table, keyed by BCP 47 (RFC 5646). There is no separate `languages`
-- table: a language tag IS a well-formed locale tag ('ar' and 'ar-EG' occupy
-- the same column), so a two-table language/locale split would only reintroduce
-- the redundant key v1 already suffers from. See CORE-1500.
--
-- `parent_tag` is the RFC 4647 "Lookup" fallback edge: ar-EG -> ar -> (root).
-- Self-referential, so sr-Latn-RS -> sr-Latn -> sr works without a schema
-- change. Root locales have parent_tag NULL.
--
-- THE TAG IS INSIDE THE FROZEN OPTION HASH, SO ITS CASING IS LOAD-BEARING.
-- BCP 47 is case-INSENSITIVE ('ar-EG' and 'ar-eg' are the same locale) but
-- SQLite TEXT keys and SHA-256 are case-SENSITIVE:
--
--     option_uid(..., 'ar-EG', ...)  ->  opt_9bb3fb19da327424bf3b91f3
--     option_uid(..., 'ar-eg', ...)  ->  opt_31e241ca1f4f029c8e52e4b8
--
-- One wrongly-cased row, inserted once by one script, permanently FORKS every
-- option in that locale into two disjoint corpora. Before this CHECK existed,
-- 'ar-eg', 'AR', 'en_US', 'not a tag!', 'zzzzz-Qaaa-QQ' and a 40-character
-- string were all accepted.
--
-- The CHECK below pins RFC 5646 canonical form (RFC 5646 §2.1.1: lowercase
-- language, Titlecase script, UPPERCASE region) for the subtag shapes we
-- actually use. It is deliberately a WHITELIST: extensions, private-use
-- (x-...), grandfathered tags, and variant subtags (rozaj, 1996) are rejected
-- until someone extends this list on purpose, because every tag admitted here
-- becomes a permanent key.
--
--   TODO(CORE-1500): PR #18 lands `legesher_i18n/bcp47.py` with is_canonical()
--   / validate() — a full RFC 5646 parser with IANA subtag-registry lookup.
--   Once it merges, the WRITE PATH must call it (a GLOB cannot know that
--   'qq-Zzzz-ZZ' is well-formed but unregistered), and this CHECK stays as the
--   last-resort DB-level floor.
CREATE TABLE locales (
    tag                  TEXT PRIMARY KEY,     -- 'ar', 'ar-EG', 'zh-Hans', 'din'
    parent_tag           TEXT REFERENCES locales(tag) ON DELETE RESTRICT,
    language_subtag      TEXT NOT NULL,        -- ISO 639-1 where it exists, else 639-3 ('din')
    script_subtag        TEXT,                 -- ISO 15924, only when not suppress-script
    region_subtag        TEXT,                 -- ISO 3166-1 alpha-2
    name                 TEXT NOT NULL,
    native_name          TEXT NOT NULL,
    direction            TEXT NOT NULL DEFAULT 'ltr' CHECK (direction IN ('ltr', 'rtl')),
    numeral_system       TEXT,
    has_case_distinction INTEGER NOT NULL DEFAULT 1 CHECK (has_case_distinction IN (0, 1)),
    -- Per-locale terminology policy the prompt builder injects (purist vs
    -- loanword-tolerant, register/diglossia). Doc 06 asked for this; v1 had
    -- nowhere to put it.
    terminology_policy   TEXT,
    iso639_3             TEXT,                 -- metadata only, never a key
    status               TEXT NOT NULL DEFAULT 'experimental'
                         CHECK (status IN ('experimental', 'in_review', 'official')),
    in_registry          INTEGER NOT NULL DEFAULT 0 CHECK (in_registry IN (0, 1)),
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),
    -- Canonical BCP 47 (RFC 5646) syntax AND casing. GLOB is case-sensitive;
    -- LIKE is not, so GLOB is the only usable operator here.
    --   lang        2-3 lowercase alpha        ar, din
    --   -Script     4 alpha, Titlecase         zh-Hans
    --   -REGION     2 UPPERCASE alpha          ar-EG
    --               or 3 digits (UN M.49)      es-419
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
    -- The component columns must agree with the tag's canonical casing too;
    -- they are what a rebuild would re-join the tag from.
    CHECK (language_subtag GLOB '[a-z][a-z]' OR language_subtag GLOB '[a-z][a-z][a-z]'),
    CHECK (script_subtag IS NULL OR script_subtag GLOB '[A-Z][a-z][a-z][a-z]'),
    CHECK (region_subtag IS NULL
           OR region_subtag GLOB '[A-Z][A-Z]'
           OR region_subtag GLOB '[0-9][0-9][0-9]'),
    -- Exact recomposition, not just a prefix match: the component columns are
    -- a DECOMPOSITION of the tag, and a prefix check still admitted
    -- ('ar-EG', ..., region_subtag='SA') — a row whose components lie to every
    -- join that uses them. If the columns cannot re-join into the tag, the row
    -- is wrong.
    CHECK (
        tag = language_subtag
              || CASE WHEN script_subtag IS NULL THEN '' ELSE '-' || script_subtag END
              || CASE WHEN region_subtag IS NULL THEN '' ELSE '-' || region_subtag END
    ),
    CHECK (parent_tag IS NULL OR parent_tag <> tag)
);

CREATE INDEX idx_locales_parent ON locales(parent_tag);

-- The semantic core. `slug` is the PUBLIC, FROZEN key: it is what the Hugging
-- Face corpus exports and what community endorsements are attached to. The
-- INTEGER id is internal and must never leave this database.
CREATE TABLE concepts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    slug              TEXT NOT NULL UNIQUE,   -- 'function-definition', 'yield-generator'
    definition_en     TEXT NOT NULL,          -- the identity: what the official docs say it does
    definition_source TEXT,                   -- citation / URL for definition_en
    -- MIGRATION CAVEAT: migrate_to_v2.py seeds this from v1 `terms.category`,
    -- which is PL-LOCAL vocabulary (keyword, builtin_func, ...). Recategorizing
    -- to the PL-neutral vocabulary below is a follow-up curation pass; until it
    -- runs, treat migrated values as provisional.
    category          TEXT NOT NULL,          -- PL-NEUTRAL: control_flow, declaration,
                                              -- error_handling, value_literal, type_system,
                                              -- concurrency, module_system, builtin_operation,
                                              -- exception_type, accessor, memory
    pattern_class     TEXT,                   -- action_keyword, state_keyword, noun_type, ...
    notes             TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    -- The slug is a hashed field of options.uid, so a U+001F in it would let two
    -- distinct tuples forge one uid (see options.surface_form).
    CHECK (slug = LOWER(slug) AND slug NOT LIKE '% %' AND instr(slug, char(31)) = 0)
);

-- A published slug can never be deleted or silently repointed; renames go
-- through here so already-published option/endorsement rows stay resolvable.
CREATE TABLE concept_slug_aliases (
    alias       TEXT PRIMARY KEY,
    concept_id  INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    retired_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reason      TEXT
);

CREATE TABLE concept_briefs (
    concept_id  INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    tier        INTEGER NOT NULL DEFAULT 1 CHECK (tier IN (1, 2)),
    path        TEXT NOT NULL,                -- repo-relative markdown path
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (concept_id, tier)
);

-- Makes the briefs' cross-reference rules queryable ("return/yield/await must
-- share verb form").
CREATE TABLE concept_relations (
    concept_id      INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    related_concept INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relation        TEXT NOT NULL
                    CHECK (relation IN ('consistency_group',  -- render with the same word form
                                        'contrast',           -- must stay distinguishable
                                        'supersedes')),       -- e.g. except* vs except
    note            TEXT,
    PRIMARY KEY (concept_id, related_concept, relation),
    CHECK (concept_id <> related_concept)
);

-- A concept's surface form in ONE programming language.
--
-- UNIQUE includes concept_id so one spelling may map to two concepts in the
-- same PL (Python `type`: builtin AND 3.12 soft keyword). That is the whole
-- point — but it creates an export hazard: a pack is a map keyed by the English
-- token, so two concepts sharing (pl, name) cannot emit two different words.
-- `export_role` resolves it: exactly one primary per (pl, name); secondaries
-- are curation/documentation rows and are excluded from pack_export. Divergent
-- renderings across the two are surfaced by pack_export_conflicts.
CREATE TABLE terms (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    programming_language TEXT NOT NULL REFERENCES programming_languages(code) ON DELETE RESTRICT,
    name                 TEXT NOT NULL,       -- the spelling: 'def', 'fn', 'func'
    category             TEXT NOT NULL,       -- PL-LOCAL: keyword, soft_keyword, builtin_func,
                                              -- builtin_type, exception, contextual_keyword, ...
    subcategory          TEXT,
    version_added        TEXT,                -- in this PL's own version scheme
    version_removed      TEXT,
    usage_note           TEXT,                -- how THIS PL's usage varies from definition_en
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
-- CORPUS — community-writable, append-only, published to Hugging Face
-- ===========================================================================

-- The reviewer ladder (CORE-1466). Weight is POLICY, versioned and editable;
-- it is deliberately NOT stored on the endorsement row, so re-weighting the
-- ladder never rewrites community data.
-- `counts_as_native` is what `endorsement_counts.native_verified_or_above`
-- means. It lives here, on the policy table, rather than as a hardcoded
-- `rank >= 3` in the view: the ladder is explicitly designed to be re-tuned
-- (CORE-1466), and a magic number in a view would silently re-define the
-- headline number the moment a rung is inserted in the middle.
CREATE TABLE review_rungs (
    rung             TEXT PRIMARY KEY,
    rank             INTEGER NOT NULL UNIQUE,
    weight           REAL NOT NULL CHECK (weight >= 0),
    counts_as_native INTEGER NOT NULL DEFAULT 0 CHECK (counts_as_native IN (0, 1)),
    policy_version   TEXT NOT NULL,
    description      TEXT
);

-- PROPOSED ladder + weights — pending Madison's sign-off (see design.md Q4).
INSERT INTO review_rungs (rung, rank, weight, counts_as_native, policy_version, description) VALUES
    ('anonymous',      0, 0.0, 0, 'v0-draft', 'Unauthenticated signal. Recorded, weighted zero; brigading evidence.'),
    ('contributor',    1, 1.0, 0, 'v0-draft', 'Authenticated account, no verified native claim.'),
    ('native_claimed', 2, 2.0, 0, 'v0-draft', 'Self-declared native speaker of the locale.'),
    ('native_verified',3, 4.0, 1, 'v0-draft', 'Native status vouched by a maintainer or ambassador.'),
    ('certified',      4, 8.0, 1, 'v0-draft', 'Certified Contributor (CORE-1446); paid-reviewer eligible.'),
    ('maintainer',     5, 8.0, 1, 'v0-draft', 'Legesher maintainer. Same weight as certified by design.');

-- An opaque, stable, pseudonymous handle. This is the ONLY identity column the
-- corpus exports. Real-world identity lives in contributor_identities, which is
-- never published. Withdrawal (CORE-1502) deletes the identity row and keeps
-- the contributor + their endorsements: counts survive, PII does not.
--
-- THE CHECK IS A SHAPE, NOT A PREFIX. `LIKE 'c\_%'` was not a constraint at all:
-- `c_alt_ur_modern` satisfies it, and that is precisely what a migration
-- doing `'c_' || created_by` produces. The id must be `c_` + exactly 16
-- lowercase hex characters — a token that cannot carry a name (see
-- schema_v2.contributor_id, which mints it from a SALTED digest of the private
-- natural key).
--
-- >>> THE SALT IS IMMUTABLE FOREVER, AND MUST BE ESCROWED. <<<
--
-- It must be SECRET (the private source keys are GitHub usernames — public and
-- enumerable — so a public salt is reversible by dictionary attack). But secrecy
-- is the lesser half: the salt is an ingredient of THIS PRIMARY KEY. Lose it,
-- rotate it, or regenerate it after the first HF publish and every id below
-- changes, every endorsement re-keys, the corpus FORKS, and every contributor's
-- history is orphaned — with no way back, because a returning contributor's
-- matching id can never be minted again.
--
-- Generate once (secrets.token_hex(32)), store in a secret manager, back it up,
-- NEVER rotate. `migrate_to_v2.py --publish` refuses a public or short salt.
CREATE TABLE contributors (
    id           TEXT PRIMARY KEY,            -- 'c_' + 16 hex — never a name, email, or handle
    current_rung TEXT NOT NULL DEFAULT 'contributor' REFERENCES review_rungs(rung),
    joined_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (id GLOB 'c_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
                || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

-- PRIVATE. Never exported, never pushed to Hugging Face. The export script
-- must fail loudly if this table appears in a dataset config (CORE-1502).
--
-- `source_key` is the pre-image of contributors.id: the token is minted from it,
-- so it is the ONLY way back from an opaque id to a person — which is why this
-- table is the hard boundary of the publish surface.
--
-- IT IS A GITHUB USERNAME, not the raw v1 `created_by` label. A first name is a
-- bad key: it is ambiguous, it collides, and it changes — and v1's labels show
-- how misleading they can be: `zh_reviewer_review_old` LOOKS like the same person one
-- pack generation earlier, but holds the words her review REJECTED (see
-- SUPERSEDED_BY_REVIEW in migrate_to_v2.py; those rows mint no contributor and
-- no endorsement at all). Usernames are stable, unique and verifiable. (The
-- PUBLISHED id is unaffected — it stays the opaque digest; only the private key
-- improves.)
-- The v1 label -> username map is CONTRIBUTOR_IDENTITY_MAP in migrate_to_v2.py,
-- explicit by design: a heuristic that strips `_old`/`_review` would silently
-- mis-merge a future contributor — and would have merged a reviewer with the
-- words she threw out.
--
-- A source_key prefixed `unresolved:` means a label that names a person but not
-- WHICH person, or not ONE person. It mints no endorsements, and
-- `migrate_to_v2.py --publish` refuses to build a corpus while one exists.
-- (v1's `alt_ur_modern` sat in this state until Madison resolved it to
-- @sarr266 — one person — on 2026-07-14.)
CREATE TABLE contributor_identities (
    contributor_id        TEXT PRIMARY KEY REFERENCES contributors(id) ON DELETE CASCADE,
    source_key            TEXT UNIQUE,        -- GitHub username — NEVER published
    display_name          TEXT,
    github_handle         TEXT,
    contact               TEXT,
    consent_public_credit INTEGER NOT NULL DEFAULT 0 CHECK (consent_public_credit IN (0, 1)),
    consent_version       TEXT,
    consent_at            TEXT,
    -- Decided 2026-07-21 (CORE-1538; closes the CORE-1501 Q1 thread): how
    -- public credit reads is the contributor's explicit three-way choice.
    -- consent_public_credit stays as the derived boolean
    -- (credit_preference <> 'anonymous'); the importer writes both.
    credit_preference     TEXT NOT NULL DEFAULT 'anonymous'
                          CHECK (credit_preference IN ('anonymous', 'handle', 'name')),
    -- Contact email, captured at every submission (decided 2026-07-21).
    -- PRIVATE like everything in this table; NEVER in a bundle — bundles are
    -- public PR artifacts, so the address travels a private channel and lands
    -- only here. The importer stores it trimmed with the domain lowercased and
    -- runs the real syntax check; this CHECK is the DB floor (one @, dotted
    -- domain, no ASCII whitespace — space, tab, CR, LF; LIKE wildcards match
    -- control characters, so the tab/newline family needs its own guards).
    -- Deliverability verification is a magic-link flow recorded in
    -- email_verified_at; an unverified email never blocks.
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
    -- A credit choice must have something to credit.
    CHECK (credit_preference <> 'name'   OR display_name  IS NOT NULL),
    CHECK (credit_preference <> 'handle' OR github_handle IS NOT NULL)
);

-- PRIVATE. Never exported (same boundary as contributor_identities).
--
-- Facts about the BUILD, not the corpus: which schema built this file, when,
-- and — load-bearing — `salt_fingerprint`, sha256 of the contributor salt,
-- truncated. Nothing else in a built database records WHICH salt minted its
-- contributor ids, so without this row the push script cannot tell an artifact
-- minted with the escrowed salt from one minted with a dev or fat-fingered
-- salt — a mistake that is unrecoverable one publish later. The fingerprint
-- verifies the salt without revealing it (the publish gate already requires
-- the salt itself to be long and high-entropy).
CREATE TABLE build_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- An OPTION is a candidate rendering of ONE concept in ONE locale.
--
-- Identity is the rendering itself — (concept, locale, pl_scope, surface_form)
-- — NOT the source that proposed it. Aya proposing «ثابت» and a human offering
-- «ثابت» are the SAME option with two provenance rows, not two options. v1 keys
-- candidates by source, which is why 16,710 translation rows collapse to 11,335
-- distinct renderings: 5,375 rows are the same word re-attested. (v1 holds
-- 11,336 distinct (term, language, translation) triples; the 11,336th is a
-- Bengali word stored under two byte sequences that NFC collapses into one —
-- see migration.md.)
--
-- `uid` is content-addressed (see schema_v2.option_uid): deterministic,
-- reproducible from an export, and stable across a DB rebuild. Publishing an
-- AUTOINCREMENT rowid would be a bug — rebuilding the DB from files would
-- renumber it and dangle every published endorsement.
--
-- `programming_language` NULL = the option applies to the concept in ANY PL
-- (the default and the overwhelming majority). Non-NULL = offered specifically
-- for that PL's use of the concept. `pl_scope` exists because SQLite treats
-- NULLs as distinct in a UNIQUE index; it is the key, NULL is the meaning.
--
-- APPEND-ONLY: a bad option is evidence, not garbage (this is the CORE-1400
-- reframe — the 183 dirty exception translations are simply low-quality
-- options). Only `withdrawn_at` may be updated; triggers enforce the rest on
-- UPDATE *and* on DELETE — a DELETE here cascades away every endorsement a
-- native speaker ever attached to the row.
CREATE TABLE options (
    uid                  TEXT PRIMARY KEY,    -- 'opt_' + 24 hex — content-addressed
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale               TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope             TEXT NOT NULL
                         GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    surface_form         TEXT NOT NULL,       -- stored NFC; compared NFKC + casefold
    first_seen_at        TEXT NOT NULL DEFAULT (datetime('now')),
    withdrawn_at         TEXT,                -- contributor withdrawal / moderation; row stays
    UNIQUE (concept_id, locale, pl_scope, surface_form),
    CHECK (uid GLOB 'opt_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    -- SQLite's one-argument TRIM() strips SPACES ONLY, so `x = TRIM(x)` is
    -- strictly weaker than schema_v2.normalize_surface_form's str.strip(),
    -- which strips every Python whitespace character. The explicit set below
    -- closes the gap. NFC itself is not expressible in SQLite; the uid-drift
    -- test (recompute the uid from the stored columns) is what pins it.
    CHECK (surface_form <> ''
           AND surface_form = TRIM(surface_form, char(9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
                                                      133, 160, 5760, 8192, 8193, 8194, 8195,
                                                      8196, 8197, 8198, 8199, 8200, 8201, 8202,
                                                      8232, 8233, 8239, 8287, 12288))),
    -- U+001F is the field delimiter of the hashed uid tuple. An INTERIOR one
    -- survives str.strip()'s edge-only trim and lets two distinct tuples forge
    -- one uid. schema_v2._digest raises on it; this is the DB-level floor.
    CHECK (instr(surface_form, char(31)) = 0)
);

-- Parent key for the canon composite FK below.
CREATE UNIQUE INDEX idx_options_identity ON options(uid, concept_id, locale);
CREATE INDEX idx_options_lookup ON options(locale, concept_id);

-- WHO/WHAT proposed this rendering, and why. Append-only, many per option.
-- A model is a provenance, never a contributor: models propose, people endorse.
--
-- `source` IS PUBLIC: it is the only provenance column the corpus exports,
-- aggregated per option into `options.sources`. `source_detail` is PRIVATE (it
-- carries v1 reviewer labels containing real first names), so `source` alone
-- has to be a useful public vocabulary, and it is cut on ONE question:
--
--     *** WHAT DO WE OWE FOR THIS ROW? ***
--
-- Obligation, not pipeline origin. That is what makes the vocabulary stable:
-- a future row's bucket is decided by asking what it obliges us to do, not by
-- which script happened to insert it. The predecessor vocabulary
-- ('import' / 'community' / 'model' / 'maintainer' / 'literature') was cut on
-- pipeline origin, and it hid two other projects' work inside a 13,650-row
-- `import` grab-bag for months -- nothing in the published vocabulary said
-- "someone else's licence applies here" (CORE-1720).
--
-- The two retired values fold in by obligation, not by deletion:
--   * 'maintainer'  -> 'legesher' — a maintainer coinage is our own work; the
--                      person is already recorded on the endorsement, and the
--                      REVIEW RUNG 'maintainer' (review_rungs) is untouched.
--   * 'literature'  -> 'upstream' — an established rendering taken from CS
--                      pedagogy or a standards body owes that body a citation,
--                      which is the `upstream` obligation. Name it in
--                      `source_detail` / `import_sources`.
CREATE TABLE option_provenance (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    option_uid     TEXT NOT NULL REFERENCES options(uid) ON DELETE CASCADE,
    source         TEXT NOT NULL
                   -- value      -- what it means                      -- what we owe
                   CHECK (source IN
                     ('legesher',   -- our own packs, curated             nothing beyond
                                    -- corrections, compositions          the dataset licence
                      'upstream',   -- lifted from another open-source    retain their notice,
                                    -- project                           credit them
                      'community',  -- offered by an individual through   credit on request,
                                    -- our native-review process          withdrawal on request
                      'model')),    -- machine-generated                  disclose which model
    source_detail  TEXT,                     -- 'aya', 'claude', 'yaml_pack', 'universal_python'
    model_version  TEXT,
    contributor_id TEXT REFERENCES contributors(id) ON DELETE SET NULL,
    word_type      TEXT,
    word_form      TEXT,                     -- infinitive_verb, noun, masdar, ...
    confidence     TEXT,
    rationale      TEXT,                     -- CORE-1502: publish-or-strip is a decision
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    -- A machine proposal must say which machine: an unattributed 'model' row is
    -- unauditable provenance. Other sources may leave the detail null.
    CHECK (source <> 'model' OR model_version IS NOT NULL OR source_detail IS NOT NULL)
);

CREATE INDEX idx_provenance_option ON option_provenance(option_uid);
CREATE INDEX idx_provenance_source ON option_provenance(source);

-- ONE ROW PER ENDORSEMENT. The count is COUNT(*) — never a stored integer.
--
-- This is what makes the corpus auditable:
--   * dedupe      — the partial UNIQUE below makes double-voting impossible
--   * weighting   — rung_at_endorsement + review_rungs.weight, joined at query
--                   time, so the ladder can be re-weighted without touching
--                   community data
--   * brigading   — created_at + method + rung distribution are all on the row
--
-- Endorsements are POSITIVE only. Disagreement is expressed by endorsing a
-- different option (CORE-1466: "propose an option, don't edit the winner").
-- Harm ("this word is offensive/wrong") goes to option_flags, so it never
-- pollutes the count of people who said the word.
CREATE TABLE endorsements (
    uid                 TEXT PRIMARY KEY,    -- 'end_' + 24 hex
    option_uid          TEXT NOT NULL REFERENCES options(uid) ON DELETE CASCADE,
    contributor_id      TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    method              TEXT NOT NULL
                        CHECK (method IN ('portal',     -- review portal vote
                                          'survey',
                                          'workshop',
                                          'github',     -- PR / issue
                                          'interview',
                                          'import')),   -- reconstructed from v1 community rows
    -- Snapshot of the endorser's rung AT THE TIME. Immutable evidence. The
    -- weight is NOT stored here (see review_rungs).
    rung_at_endorsement TEXT NOT NULL REFERENCES review_rungs(rung),
    comment             TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    retracted_at        TEXT,
    CHECK (uid GLOB 'end_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
);

-- One person, one live endorsement per option. Retraction frees the slot, so
-- the table stays append-only AND double-voting stays impossible.
CREATE UNIQUE INDEX idx_endorsement_one_per_person
    ON endorsements(option_uid, contributor_id) WHERE retracted_at IS NULL;
CREATE INDEX idx_endorsement_option ON endorsements(option_uid);
CREATE INDEX idx_endorsement_contributor ON endorsements(contributor_id);

-- Moderation / harm signal — deliberately NOT a downvote. A downvote on a
-- minority-language term invites exactly the brigading the endorsement model
-- exists to detect.
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

-- Mechanical validation, cached. DERIVED — regenerate with the audit script,
-- never hand-edit. Kept out of `options` so the corpus stays append-only while
-- validators are re-run and re-versioned (PR #256 / CORE-1318 findings become
-- per-row review data, per CORE-1505).
--
-- `validator_version` names the code that produced the verdict, and the canon
-- trigger REJECTS the reserved value 'migration-seed'. Without that, the
-- CORE-1400 gate is circular: an earlier draft of migrate_to_v2.py stamped all
-- 5,136 canon-bound rows `identifier_valid = 1, nfkc_stable = 1` WITHOUT
-- RUNNING A VALIDATOR, and the trigger then dutifully passed them — including
-- 1 surface that is not a valid Python identifier (Amharic `ከቀረ*`, a literal
-- asterisk, from `except*`) and 25 that are NFKC-unstable (all Thai, the
-- U+0E33 class). "pack_export reproduces all 5,136" was true only because the
-- gate had been bypassed. A seeded row must never be mistaken for a validated
-- one; the migration now runs the real check and reports what fails.
CREATE TABLE option_validations (
    option_uid          TEXT PRIMARY KEY REFERENCES options(uid) ON DELETE CASCADE,
    validator_version   TEXT NOT NULL,
    identifier_valid    INTEGER NOT NULL CHECK (identifier_valid IN (0, 1)),
    nfkc_stable         INTEGER NOT NULL CHECK (nfkc_stable IN (0, 1)),
    -- WHY the value is NFKC-unstable, recorded as a FACT (CORE-1514). NULL when
    -- stable. 'sara-am-only' = the delta is exclusively U+0E33 (Thai SARA AM),
    -- which CPython itself NFKC-normalizes in identifiers (PEP 3131), so both
    -- spellings are one identifier at runtime and there is no spoofing surface.
    -- 'other' is any other instability and stays a hard block. The fact stays a
    -- fact: the ALLOWANCE for 'sara-am-only' is explicit policy in
    -- trg_canon_requires_valid_identifier, not a weakening of nfkc_stable.
    nfkc_delta_class    TEXT CHECK (nfkc_delta_class IS NULL
                                    OR nfkc_delta_class IN ('sara-am-only', 'other')),
    script_consistent   INTEGER NOT NULL CHECK (script_consistent IN (0, 1)),
    collides_en_keyword INTEGER NOT NULL DEFAULT 0 CHECK (collides_en_keyword IN (0, 1)),
    min_interpreter_ok  INTEGER NOT NULL DEFAULT 1 CHECK (min_interpreter_ok IN (0, 1)),
    checked_at          TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (validator_version <> '' AND validator_version = TRIM(validator_version))
);

-- ===========================================================================
-- CANON — the maintainer decision. Source of truth is TEXT IN THE MONOREPO.
-- ===========================================================================
--
-- This table is a projection of libs/i18n/canon/<locale>.toml, loaded by
-- `make canon-load`. It is structurally impossible to have a canon row that is
-- not backed by a reviewed file: source_file is NOT NULL, and a CI drift test
-- re-loads the files and asserts this table reproduces exactly (the CORE-611
-- languages.json precedent).
--
-- Two invariants enforced by triggers below:
--   1. You may only select a rendering that EXISTS IN THE CORPUS (option_uid is
--      NOT NULL, composite-FK'd to the option's concept + locale). Every shipped
--      word is traceable to an offered option, its provenance, and its
--      endorsements. A maintainer who wants a word nobody offered must first
--      add it as an option with source='legesher'.
--   2. You may not ship an invalid identifier. The trigger rejects any option
--      that fails identifier_valid / nfkc_stable. This is CORE-1400's real
--      requirement: gate the SELECTION, not the corpus.
--
-- programming_language NULL = concept-wide (the default, and the payoff:
-- one decision serves every PL that uses the concept). Non-NULL = a deliberate
-- per-PL override, taken only when a locale genuinely needs a different word
-- for that PL's use of the concept.
CREATE TABLE canon_selections (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id           INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale               TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope             TEXT NOT NULL
                         GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    option_uid           TEXT NOT NULL,
    surface_form         TEXT NOT NULL,      -- denormalized from the option for a readable diff
    -- The CORE-1466 ladder. 'community' from the v2 draft is gone: a community
    -- submission is an OPTION, never a canon status.
    status               TEXT NOT NULL DEFAULT 'machine'
                         CHECK (status IN ('machine',       -- auto-picked, unreviewed
                                           'experimental',  -- maintainer/ambassador pick
                                           'reviewed',      -- native sign-off
                                           'official')),    -- certified review + term screening
    identity_ok          INTEGER NOT NULL DEFAULT 0 CHECK (identity_ok IN (0, 1)),
                                             -- deliberate cognate/loanword equal to the English
                                             -- term (policy 2026-07-05); NOT "never translated"
    decided_by           TEXT,
    decided_at           TEXT NOT NULL DEFAULT (datetime('now')),
    decision_reason      TEXT,
    -- Proof this row came from reviewed text, not from someone poking the DB.
    source_file          TEXT NOT NULL,      -- 'libs/i18n/canon/ar.toml'
    source_revision      TEXT,               -- git sha of the file at load time
    UNIQUE (concept_id, locale, pl_scope),
    FOREIGN KEY (option_uid, concept_id, locale)
        REFERENCES options(uid, concept_id, locale) ON DELETE RESTRICT
);

CREATE INDEX idx_canon_locale ON canon_selections(locale, status);
CREATE INDEX idx_canon_concept ON canon_selections(concept_id);

-- ===========================================================================
-- TRIGGERS — the invariants that a FK cannot express
--
-- EVERY invariant here is enforced on INSERT *and* on UPDATE *and* on DELETE.
-- An INSERT-only trigger is not an invariant, it is a speed bump: each of the
-- rules below was previously defeated by a one-line UPDATE or DELETE that
-- re-entered the state the INSERT trigger exists to forbid —
--
--   UPDATE canon_selections SET surface_form = …   -> ship a word no option offered
--   UPDATE option_validations SET identifier_valid = 1
--                                                 -> ship 'de f!'
--   UPDATE options SET withdrawn_at = …           -> withdrawn option still exports
--   DELETE FROM options                           -> cascade away every endorsement
--   UPDATE endorsements SET rung_at_endorsement = 'maintainer'
--                                                 -> move a vote's weight 0.0 -> 8.0
--   UPDATE endorsements SET option_uid = …        -> move a vote to another word
-- ===========================================================================

-- -- CORPUS: append-only ------------------------------------------------------

-- The rendering, its concept, and its locale are immutable. Only `withdrawn_at`
-- may change.
-- first_seen_at is in the frozen list too: it is brigading-detection evidence
-- (a burst of first_seen_at timestamps is the signal), so back-dating it is an
-- attack, not a correction.
CREATE TRIGGER trg_options_append_only
BEFORE UPDATE OF concept_id, locale, programming_language, surface_form, uid,
                 first_seen_at ON options
BEGIN
    SELECT RAISE(ABORT, 'options are append-only: withdraw the row, do not edit it');
END;

-- Withdrawal is a one-way door. Un-withdrawing after a canon row was refused is
-- the same attack as never withdrawing.
CREATE TRIGGER trg_options_withdrawal_is_final
BEFORE UPDATE OF withdrawn_at ON options
WHEN OLD.withdrawn_at IS NOT NULL AND NEW.withdrawn_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'options are append-only: a withdrawal cannot be reversed');
END;

-- A DELETE cascades to option_provenance, endorsements, option_flags and
-- option_validations: it silently destroys every endorsement a native speaker
-- ever attached to the word. There is no legitimate caller.
CREATE TRIGGER trg_options_no_delete
BEFORE DELETE ON options
BEGIN
    SELECT RAISE(ABORT,
        'options are append-only: DELETE would cascade away the endorsements; withdraw instead');
END;

-- Provenance is evidence of who/what proposed a word. (contributor_id is
-- excluded from the UPDATE list: CORE-1502 withdrawal nulls it via ON DELETE
-- SET NULL, which is the one legitimate write.)
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

-- An endorsement is immutable evidence: WHO said WHICH word, at WHAT rung, WHEN.
-- Retraction (and moderating the free-text comment) are the only writes. This is
-- what makes `rung_at_endorsement` a snapshot rather than a mutable weight —
-- the property the PR body claims and, until now, did not have.
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

-- The opaque handle is stamped into every published endorsement uid; repointing
-- it re-keys the corpus. (current_rung — the promotion path — stays mutable.)
CREATE TRIGGER trg_contributor_id_is_immutable
BEFORE UPDATE OF id ON contributors
BEGIN
    SELECT RAISE(ABORT, 'contributors.id is the published key: it cannot be repointed');
END;

-- -- VALIDATION CACHE ---------------------------------------------------------

-- option_validations is a derived cache and is meant to be regenerated — but
-- NOT under a live canon row. Flipping `identifier_valid` to 1, or deleting the
-- row, while a canon selection depends on it re-opens exactly the hole the
-- canon trigger closes (it only fires on the canon INSERT). Re-validating a
-- shipped word is legitimate; the order of operations is: drop the canon rows,
-- re-run the validator, re-load the canon (which re-checks on INSERT).
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

-- -- CANON: only ever a loaded projection --------------------------------------

-- A PL-scoped option cannot be selected for a different PL. A concept-wide
-- option ('*') may be selected either concept-wide or as a PL override.
CREATE TRIGGER trg_canon_scope_compatible
BEFORE INSERT ON canon_selections
WHEN (SELECT o.pl_scope FROM options o WHERE o.uid = NEW.option_uid)
     NOT IN ('*', COALESCE(NEW.programming_language, '*'))
BEGIN
    SELECT RAISE(ABORT, 'canon: option pl_scope does not cover this selection');
END;

-- The selection rule (CORE-1400), corrected in both directions by the Q7 triage
-- (CORE-1514): never ship an option that fails mechanical validation, but do not
-- refuse a legitimate one either. Unvalidated is a reject — silence is not a
-- pass — and a 'migration-seed' row is unvalidated: a stamp, not a verdict.
-- Three real checks gate the SELECTION:
--   * identifier_valid  — term-aware (except* keeps its mirrored '*'), so a
--                         faithful rendering is no longer refused for structure.
--   * script_consistent — real per-character, locale-aware script classification,
--                         so a Cyrillic-in-Thai confusable (NFKC-stable, a valid
--                         identifier) no longer ships.
--   * NFKC              — stable, OR unstable for exactly one reason: SARA-AM.
--                         U+0E33 is legitimate Thai orthography that CPython
--                         normalizes in identifiers (PEP 3131); accepting the
--                         'sara-am-only' class is explicit policy, and it rides on
--                         identifier_valid + script_consistent, so the accepted
--                         NFKC form is itself an identifier-valid single script.
CREATE TRIGGER trg_canon_requires_valid_identifier
BEFORE INSERT ON canon_selections
WHEN NOT EXISTS (
    SELECT 1 FROM option_validations v
    WHERE v.option_uid = NEW.option_uid
      AND v.identifier_valid = 1
      AND v.script_consistent = 1
      AND (v.nfkc_stable = 1 OR v.nfkc_delta_class = 'sara-am-only')
      AND v.validator_version <> 'migration-seed'
)
BEGIN
    SELECT RAISE(ABORT, 'canon: option is unvalidated or fails identifier/NFKC/script validation');
END;

-- The denormalized surface_form must match the option it claims to ratify.
CREATE TRIGGER trg_canon_surface_matches_option
BEFORE INSERT ON canon_selections
WHEN NEW.surface_form <> (SELECT o.surface_form FROM options o WHERE o.uid = NEW.option_uid)
BEGIN
    SELECT RAISE(ABORT, 'canon: surface_form does not match the selected option');
END;

-- A withdrawn option may not be shipped.
CREATE TRIGGER trg_canon_no_withdrawn_option
BEFORE INSERT ON canon_selections
WHEN (SELECT o.withdrawn_at FROM options o WHERE o.uid = NEW.option_uid) IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'canon: option has been withdrawn');
END;

-- No UPDATE, ever. The canon is a LOADED PROJECTION of
-- libs/i18n/canon/<locale>.toml, replaced wholesale on each load — so there is
-- no legitimate in-place edit, and mirroring each INSERT trigger with a weaker
-- UPDATE equivalent would only invite one. Editing the canon means editing the
-- text file and reloading; the INSERT triggers then re-check every invariant.
-- (DELETE stays open: it is half of "replace wholesale".)
CREATE TRIGGER trg_canon_no_update
BEFORE UPDATE ON canon_selections
BEGIN
    SELECT RAISE(ABORT,
        'canon_selections is a loaded projection: edit libs/i18n/canon/<locale>.toml and reload');
END;

-- The canon may not outlive the option it ratifies. Withdrawing a shipped word
-- must fail loudly rather than leave a canon row pointing at a withdrawn option
-- (the FK is ON DELETE RESTRICT, but withdrawal is an UPDATE, not a DELETE).
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

-- RFC 4647 Lookup. For every locale, the chain of tags to try, nearest first.
-- depth 0 = the locale itself.
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

-- THE derived count. This is the table Madison asked for, as a GROUP BY.
-- `endorsements` and `endorsers` are equal by construction (the partial unique
-- index); if they ever diverge, the dedupe invariant has been violated.
CREATE VIEW endorsement_counts AS
SELECT
    o.uid                                        AS option_uid,
    COUNT(e.uid)                                 AS endorsements,
    COUNT(DISTINCT e.contributor_id)             AS endorsers,
    COALESCE(SUM(r.weight), 0.0)                 AS weighted_endorsement,
    -- Policy lives in review_rungs.counts_as_native, not in a `rank >= 3` magic
    -- number here: inserting a rung in the middle of the ladder would otherwise
    -- silently re-define this number across the whole published corpus.
    COUNT(CASE WHEN r.counts_as_native = 1 THEN 1 END) AS native_verified_or_above,
    MIN(e.created_at)                            AS first_endorsed_at,
    MAX(e.created_at)                            AS last_endorsed_at
FROM options o
LEFT JOIN endorsements e
       ON e.option_uid = o.uid AND e.retracted_at IS NULL
LEFT JOIN review_rungs r
       ON r.rung = e.rung_at_endorsement
GROUP BY o.uid;

-- "`true` may have four candidate words with a count each." One row per
-- candidate rendering, ranked within its (concept x locale x pl_scope).
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
    -- The other two predicates the canon gate (trg_canon_requires_valid_
    -- identifier) actually tests, so this view mirrors canon-eligibility rather
    -- than a stale subset: an identifier-valid, NFKC-stable option can still be
    -- refused for a foreign script (CORE-1514).
    COALESCE(v.script_consistent, 0) AS script_consistent,
    v.nfkc_delta_class,
    RANK() OVER (
        PARTITION BY o.concept_id, o.locale, o.pl_scope
        ORDER BY ec.weighted_endorsement DESC, ec.endorsements DESC, o.surface_form ASC
    )                            AS standing
FROM options o
JOIN concepts c            ON c.id = o.concept_id
JOIN endorsement_counts ec ON ec.option_uid = o.uid
LEFT JOIN option_validations v ON v.option_uid = o.uid;

-- Canon resolved through the locale fallback chain.
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

-- THE precedence rule, in exactly one place. Every term (primary AND secondary)
-- resolved to the ONE word it renders as, in one locale:
--
--   1. locale specificity   — nearest locale in the fallback chain wins
--   2. PL specificity       — within that locale, a PL override beats concept-wide
--
-- (documented in design.md, open question Q2)
--
-- pack_export and pack_export_conflicts BOTH read from here, which is the point:
-- a conflict view that re-derives the join without the precedence rule reports a
-- conflict for every legitimate PL override — see below.
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

-- Direction 1 — a developer pulls a pack: every term of one PL in one locale.
-- Exactly one row per (pl, locale, english_term): one `primary` term row per
-- (pl, name), resolved to one word by term_resolution.
CREATE VIEW pack_export AS
SELECT programming_language, locale, english_term, category, subcategory,
       concept_slug, translation, status, identity_ok, option_uid,
       resolved_locale, locale_distance, scope, version_added, version_removed
FROM term_resolution
WHERE export_role = 'primary';

-- The export hazard made visible: one (pl, spelling) mapping to two CONCEPTS
-- whose canon renderings differ (Python `type`: builtin AND 3.12 soft keyword).
-- The pack is keyed by the English token, so the two concepts cannot both be
-- rendered; `export_role` picks the primary and this view surfaces the
-- divergence for a maintainer to adjudicate instead of dropping it silently.
--
-- IT MUST READ POST-PRECEDENCE. The previous version joined canon_selections
-- directly with `cs.pl_scope IN ('*', t.programming_language)` and no ranking,
-- so a concept that has BOTH a concept-wide word and a legitimate PL override
-- produced two rows and was reported as a conflict. That is a false positive on
-- every use of the PL-override feature — and since this view's contract is
-- "must be empty, or the pack is ambiguous", a CI gate on it would have made the
-- feature unusable. Grouping term_resolution (one row per term) reports only a
-- real cross-concept divergence.
-- Coverage split (CORE-1355): deliberate cognates/loanwords (identity_ok = 1,
-- policy 2026-07-05) are their own class, never "untranslated gaps". Anything
-- reporting coverage numbers (README counts, corpus cards) reads the split
-- from here instead of re-deriving key == value at the pack layer.
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

-- v1's find_collisions(), re-keyed by concept: within one locale and one PL,
-- two DISTINCT concepts shipping the SAME word. Cross-PL reuse of a word is now
-- a feature (same concept, same word), so it is correctly not flagged here.
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

-- Direction 2 — the native-speaker review queue: concepts in one locale with no
-- reviewed canon, the definition attached as the review anchor, and every
-- candidate with its endorsement count.
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
    -- Same denominator as candidate_options: live (non-withdrawn) options
    -- only, so the two numbers in this row describe the same population.
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

-- The experimental -> official dashboard, per (PL x locale).
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

-- Onboarding a new PL: how much arrives already-translated. The number to put
-- in front of reviewers ("your Turkish review of `break` just shipped in 10
-- programming languages").
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
-- DEFERRED (created, inert, NOT part of the HF corpus one-way door)
-- Error message STRINGS are sentences with grammar, not vocabulary. Keyed by
-- (implementation, version, key) — CPython 3.12's rewordings must not
-- invalidate 3.11's translations. See proposal doc 06 / 09.
-- ===========================================================================

CREATE TABLE message_templates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    implementation TEXT NOT NULL,            -- 'cpython', 'v8', 'rustc'
    key            TEXT NOT NULL,            -- 'ZeroDivisionError.division_by_zero'
    template_en    TEXT NOT NULL,            -- 'division by zero'
    placeholders   TEXT,                     -- JSON: [{"name":"obj_type","example":"str"}]
    matcher        TEXT,                     -- regex/fingerprint for runtime interception
    concept_id     INTEGER REFERENCES concepts(id) ON DELETE SET NULL,
    version_added  TEXT,
    version_removed TEXT,
    UNIQUE (implementation, key, version_added)
);

CREATE TABLE message_translations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES message_templates(id) ON DELETE CASCADE,
    locale      TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    template    TEXT NOT NULL,               -- localized, placeholders preserved
    status      TEXT NOT NULL DEFAULT 'machine'
                CHECK (status IN ('machine', 'experimental', 'reviewed', 'official')),
    UNIQUE (template_id, locale)
);

-- ===========================================================================
-- REVIEW INTAKE (CORE-1538) — sessions, rankings, annotations, expansions,
-- commentary, style ratifications, import-source registry.
--
-- The intake layer over the corpus: how structured native review arrives
-- (review bundles — doc: libs/i18n/docs/proposals/native-review-intake/),
-- with the same discipline as the corpus itself: append-only community
-- tables (full UPDATE/DELETE trigger mirrors), content-addressed uids
-- (formulae in schema_v2.py: session_uid, annotation_uid, expansion_uid,
-- commentary_uid, style_uid — deterministic so re-importing a bundle is
-- INSERT-idempotent), pl_scope as the '*' STORED generated column, and
-- policy expressed in views so thresholds re-cut in one place.
--
-- Layers: review_sessions + junctions + session_rankings +
-- option_annotations + option_expansions + concept_commentary are
-- CORPUS-ADJACENT (community-writable, append-only, publish-eligible);
-- commentary_moderation is DERIVED (mutable, regenerable);
-- import_sources is REFERENCE; message_endorsements is DEFERRED/inert
-- like the message tables above.
-- ===========================================================================

-- REFERENCE: every non-human candidate stream, so license posture and
-- attribution are data, not lore. `redistributable` gates whether terms from
-- this source may be STORED as options / exported in the CC BY 4.0 corpus,
-- or only DISPLAYED as attributed references in the review kit.
-- option_provenance.source_detail carries this id for
-- source='model' / source='upstream' (CORE-1720).
CREATE TABLE import_sources (
    id              TEXT PRIMARY KEY,          -- 'model:aya-expanse-32b', 'initiative:hedy'
    kind            TEXT NOT NULL CHECK (kind IN ('model', 'initiative', 'dataset')),
    name            TEXT NOT NULL,
    url             TEXT,
    license_spdx    TEXT,                      -- 'Apache-2.0', 'EUPL-1.2'; NULL = none found
    redistributable INTEGER NOT NULL DEFAULT 0 CHECK (redistributable IN (0, 1)),
    attribution     TEXT,                      -- credit line required when displayed/exported
    fetched_ref     TEXT,                      -- commit sha / dataset revision imported from
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (id = LOWER(id) AND id NOT LIKE '% %' AND instr(id, char(31)) = 0),
    -- Redistribution is a verified license posture, never a default.
    CHECK (redistributable = 0 OR license_spdx IS NOT NULL)
);

-- One completed sitting of the review app (or an imported issue-form
-- response): the provenance + verification anchor for everything a reviewer
-- produced in it. uid = 'ses_' + sha256(canonical bundle)[:24], so re-import
-- is idempotent. The ONE intake table with a workflow: append-only EXCEPT
-- status / verification_report / notes.
CREATE TABLE review_sessions (
    uid                 TEXT PRIMARY KEY,
    contributor_id      TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    locale              TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    track               TEXT NOT NULL
                        CHECK (track IN ('reserved_words', 'messages', 'style_profile')),
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope            TEXT NOT NULL
                        GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    method              TEXT NOT NULL          -- same vocabulary as endorsements.method
                        CHECK (method IN ('portal', 'survey', 'workshop', 'github',
                                          'interview', 'import')),
    kit_version         TEXT NOT NULL,         -- review-kit build the reviewer saw
    app_version         TEXT,
    rung_at_session     TEXT NOT NULL REFERENCES review_rungs(rung),  -- snapshot, immutable
    bundle_digest       TEXT NOT NULL,         -- full sha256 (64 hex); uid is its truncation
    contact_captured    INTEGER NOT NULL DEFAULT 0 CHECK (contact_captured IN (0, 1)),
                                               -- email reached the PRIVATE channel; the address
                                               -- itself lives in contributor_identities only
    started_at          TEXT,                  -- client-reported; advisory evidence
    submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
    status              TEXT NOT NULL DEFAULT 'submitted'
                        CHECK (status IN ('submitted', 'verifying', 'accepted',
                                          'returned', 'rejected')),
    verification_report TEXT,                  -- JSON, one entry per pipeline stage
    notes               TEXT,
    CHECK (uid GLOB 'ses_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    -- Every character hex, not just the first: GLOB '[0-9a-f]*' anchors only
    -- position 1, so the negated class over the whole string is the real check.
    CHECK (bundle_digest NOT GLOB '*[^0-9a-f]*' AND length(bundle_digest) = 64),
    -- The uid IS the digest's truncation (schema_v2.session_uid); a hand-written
    -- INSERT must not be able to pair a well-formed uid with an unrelated digest,
    -- or re-import idempotency and bundle re-verification silently break.
    CHECK (uid = 'ses_' || substr(bundle_digest, 1, 24)),
    -- A style-profile session is locale-wide by definition.
    CHECK (track <> 'style_profile' OR programming_language IS NULL)
);

CREATE INDEX idx_sessions_locale ON review_sessions(locale, track, status);
CREATE INDEX idx_sessions_contributor ON review_sessions(contributor_id);

-- Evidence columns are frozen; only the workflow columns may move.
CREATE TRIGGER trg_sessions_evidence_frozen
BEFORE UPDATE OF uid, contributor_id, locale, track, programming_language, method,
                 kit_version, app_version, rung_at_session, bundle_digest,
                 contact_captured, started_at, submitted_at ON review_sessions
BEGIN
    SELECT RAISE(ABORT,
        'review_sessions: evidence is append-only; only status/verification_report/notes may change');
END;

-- Terminal states stay terminal: an accepted session has been ingested
-- (un-accepting would orphan corpus rows); a rejection is a moderation
-- decision with its own record. A returned session resubmits as a NEW
-- bundle (new content -> new uid), never mutates back.
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

-- Once a session is terminal, its verification report and notes are part of
-- the record: rewriting the audit trail after acceptance/rejection is the
-- same attack as editing evidence. (The transition INTO the terminal state
-- writes the report in the same UPDATE, which passes — OLD.status is not yet
-- terminal.)
CREATE TRIGGER trg_sessions_report_frozen_when_terminal
BEFORE UPDATE OF verification_report, notes ON review_sessions
WHEN OLD.status IN ('accepted', 'rejected') AND NEW.status = OLD.status
BEGIN
    SELECT RAISE(ABORT,
        'review_sessions: the verification report is frozen once the session is terminal');
END;

-- Junctions: which corpus rows a session produced. options/endorsements stay
-- exactly as above (no new columns on frozen shapes); linkage lives here.
-- `elicited` preserves the blind-first ordering — the research signal the
-- structured flow exists to collect. Fully frozen.
CREATE TABLE session_options (
    session_uid  TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    option_uid   TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    elicited     TEXT NOT NULL CHECK (elicited IN ('blind',         -- before candidates shown
                                                   'after_reveal',  -- after seeing candidates
                                                   'quick')),       -- non-session path (issue form)
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

-- A session may only claim endorsements its OWN contributor made — linking
-- someone else's endorsement to a session would misattribute evidence.
CREATE TRIGGER trg_session_endorsements_same_contributor
BEFORE INSERT ON session_endorsements
WHEN (SELECT e.contributor_id FROM endorsements e WHERE e.uid = NEW.endorsement_uid)
  <> (SELECT s.contributor_id FROM review_sessions s WHERE s.uid = NEW.session_uid)
BEGIN
    SELECT RAISE(ABORT,
        'session_endorsements: endorsement belongs to a different contributor than the session');
END;

-- Session-scoped preference order. Separate from endorsements on purpose:
--   endorsement = "I would teach this word"   (positive, at-most-one per person)
--   ranking     = "among those, this order"   (re-elicitable, session-scoped)
-- Append-only across sessions; aggregation reads each contributor's LATEST
-- accepted session via latest_rankings. No downvotes anywhere: an unranked,
-- unendorsed option is simply "passed".
CREATE TABLE session_rankings (
    session_uid  TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    concept_id   INTEGER NOT NULL REFERENCES concepts(id) ON DELETE RESTRICT,
    locale       TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    programming_language TEXT REFERENCES programming_languages(code) ON DELETE RESTRICT,
    pl_scope     TEXT NOT NULL
                 GENERATED ALWAYS AS (COALESCE(programming_language, '*')) STORED,
    option_uid   TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    rank         INTEGER NOT NULL CHECK (rank >= 1),   -- 1 = "ship this"
    revised_after_reveal INTEGER NOT NULL DEFAULT 0
                 CHECK (revised_after_reveal IN (0, 1)),
    comment      TEXT,
    -- A generated column may sit in a UNIQUE constraint but not in a PRIMARY
    -- KEY (SQLite rule; canon_selections uses the same pattern).
    UNIQUE (session_uid, concept_id, locale, pl_scope, option_uid)
);

CREATE UNIQUE INDEX uq_ranking_slot
    ON session_rankings(session_uid, concept_id, locale, pl_scope, rank);
CREATE INDEX idx_rankings_option ON session_rankings(option_uid);

-- You may only rank a word you endorsed (live, yours). The importer enforces
-- this at the bundle level; this trigger is the DB floor. A LATER retraction
-- legitimately strands the ranking row — it stays as evidence; aggregation
-- joins live endorsements and ignores it.
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

-- The ranked option must render the concept/locale the row claims — a
-- mis-keyed ranking would silently poison aggregation.
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

-- And the ranking's locale must be the session's locale — an Urdu ranking
-- filed under a Spanish session is mis-keyed evidence.
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

-- Neutral, crowd-attestable DESCRIPTORS of an option — distinct from
-- option_flags (moderation/harm): no resolution workflow, no negative
-- charge. This is the transliteration checkbox: transliteration popularity
-- per locale is revealed preference feeding locales.terminology_policy,
-- while option_flags(reason='transliteration') stays reserved for the
-- model-policy violation (2026-07-05 rule). Vocabulary is a CHECK, matching
-- the house style for flags/methods.
CREATE TABLE option_annotations (
    uid             TEXT PRIMARY KEY,
    option_uid      TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    kind            TEXT NOT NULL
                    CHECK (kind IN ('transliteration',   -- phonetic copy of the English term
                                    'cognate_loanword',  -- genuine cognate / established loan
                                    'established_term',  -- existing classroom/textbook usage
                                    'coined_neologism',  -- new coinage for this concept
                                    'register_formal',
                                    'register_informal',
                                    'regional')),        -- locale-specific; locale-split signal
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

-- A session-linked row must belong to the session's contributor: the uid
-- formula binds them, but the formula lives in application code and this
-- floor must hold against a hand-written INSERT. Same rule on expansions,
-- commentary, and style ratifications below.
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

-- The phrase layer (elif-class concepts). The reviewed agreement has TWO
-- layers: (1) the expanded phrase in the target language (prose; spaces
-- welcome) — this table; (2) the contracted surface form that becomes the
-- identifier — the option it attaches to. The canon TOML gains an optional
-- `expansion` per entry, copied from the winning option's most-attested
-- expansion at selection time.
CREATE TABLE option_expansions (
    uid             TEXT PRIMARY KEY,
    option_uid      TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    expansion       TEXT NOT NULL,             -- stored NFC, like surface_form
    formation_note  TEXT,                      -- how the expansion contracts to the token
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

-- Free-text community knowledge that belongs to a CONCEPT (or the locale as
-- a whole), not to one option — the terminology feedstock for
-- `legesher translate` beyond the packed word. The community row is
-- append-only and carries NO workflow; publishability is a MODERATION
-- verdict in commentary_moderation (the option_validations pattern).
-- Export includes a row only when its moderation row says 'published'.
CREATE TABLE concept_commentary (
    uid               TEXT PRIMARY KEY,
    contributor_id    TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid       TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    concept_id        INTEGER REFERENCES concepts(id) ON DELETE RESTRICT,
                      -- NULL = locale-level commentary. Export keys by slug;
                      -- the INTEGER id never leaves this database.
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

-- DERIVED moderation verdict, 1:1, regenerable — the mutable table.
CREATE TABLE commentary_moderation (
    commentary_uid  TEXT PRIMARY KEY REFERENCES concept_commentary(uid) ON DELETE RESTRICT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'published', 'withheld')),
    moderated_by    TEXT,
    moderated_at    TEXT,
    note            TEXT
);

-- Track 3: one reviewer's answer to one named style-profile question for a
-- locale. The style-guides/<locale>.yml generator aggregates these exactly
-- as canon aggregates endorsements: evidence rows here, the shipped guide is
-- a generated artifact, promotion is a query. Style guides remain
-- SUGGESTIONS — ratification records community preference, not law.
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

-- One LIVE answer per person per (locale, field); retraction frees the slot
-- for a changed mind, exactly like endorsements.
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

-- DEFERRED (like the message tables above): endorsements for message
-- translations, activated with the messages track. Before these are ever
-- PUBLISHED, message_translations must first gain content-addressed keys —
-- its AUTOINCREMENT id has exactly the rebuild-renumbering hazard options.uid
-- exists to prevent.
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

-- -- REVIEW-INTAKE VIEWS --------------------------------------------------------

-- Each contributor's LATEST accepted session per (concept, locale, pl_scope):
-- the ranking set that counts. Deterministic on ties (submitted_at, then
-- uid). Enforces its own contract: a ranking whose endorsement was later
-- retracted is stranded evidence and is excluded here, not left for every
-- consumer to remember to filter.
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

-- Promotion check per option — a THIN layer over option_standings, adding
-- exactly two things: the native-endorser threshold and canon-eligibility
-- mirrored from trg_canon_requires_valid_identifier (identifier_valid AND
-- script_consistent AND (nfkc_stable OR sara-am-only)). Thresholds live
-- here, in one place (Q5 recommendation: >=2 native, zero open flags).
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
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS canon_eligible,
    (s.withdrawn_at IS NULL
     AND s.native_verified_or_above >= 2
     AND s.open_flags = 0
     AND s.identifier_valid = 1
     AND s.script_consistent = 1
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS reviewed_eligible
FROM option_standings s;

-- The one-endorsement-away queue: what the app shows a locale's NEXT
-- reviewer first. Live, canon-eligible options one native endorsement short
-- of the reviewed bar.
CREATE VIEW second_endorsement_queue AS
SELECT concept_slug, locale, pl_scope, option_uid, surface_form,
       native_verified_or_above, endorsements
FROM option_promotion_status
WHERE reviewed_eligible = 0
  AND canon_eligible = 1
  AND open_flags = 0
  AND native_verified_or_above = 1;

-- The experimental -> official gate per (PL x locale) as a query. Threshold
-- numbers pending ratification; the gate reads THIS view so re-cutting is
-- one place.
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

-- Terminology export for `legesher translate`: per (concept x locale), the
-- canon word plus alternates, descriptors, and the most-attested expansion —
-- the "how else is this concept expressed" layer prompt assembly injects.
-- Published commentary joins by concept slug in the exporter. Rows whose
-- ONLY provenance is a non-redistributable import_source are excluded by the
-- EXPORTER (this view is also the maintainers' internal lens, so it stays
-- unfiltered).
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
WHERE o.withdrawn_at IS NULL;

-- Transliteration revealed-preference per locale — the aggregate the
-- annotation exists to measure, and the input to a terminology_policy
-- conversation with that locale's community.
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
