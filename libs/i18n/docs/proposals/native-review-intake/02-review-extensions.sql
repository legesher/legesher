-- ===========================================================================
-- Review-intake extensions to schema v2 — PROPOSAL (rev 2, 2026-07-21)
--
-- HISTORICAL RATIONALE, NOT AUTHORITATIVE DDL. This DDL is folded into the
-- committed libs/i18n/legesher_i18n/db/schema_v2.sql, which is the single
-- source of truth from that point on; this file remains as the annotated
-- design record and is NOT kept byte-synchronized with later schema fixes.
-- Behavioral coverage lives in tests/test_review_extensions.py.
-- Extends the committed libs/i18n/legesher_i18n/db/schema_v2.sql (CORE-1501)
-- with the intake layer: sessions, rankings, annotations, expansions,
-- commentary, style ratifications, the import-source registry, and the
-- identity deltas decided 2026-07-21 (opaque-id publishing + three-way credit
-- preference + email at submission).
--
-- rev 2 = the pre-migration hard review: every table re-aligned to the
-- committed schema's actual conventions (pl_scope '*' STORED generated
-- column; hex-precise uid CHECKs; vocabulary-in-CHECK house style), full
-- append-only trigger discipline ("an INSERT-only trigger is not an
-- invariant"), the rank-requires-endorsement invariant, moderation split out
-- of the append-only commentary row, and canon-eligibility logic that
-- matches trg_canon_requires_valid_identifier exactly (script_consistent +
-- the sara-am-only allowance the rev-1 draft missed).
--
-- HARDENING ADDENDUM (second review, 2026-07-21): the folded schema also
-- carries six invariants this file's rev-2 text predates — ranking locale
-- must match the session locale; a session may only claim its own
-- contributor's endorsements; session-linked annotations/expansions/
-- commentary/style rows must match the session contributor; the
-- verification report freezes once a session is terminal; and
-- latest_rankings excludes rankings whose endorsement was later retracted.
-- The folded schema_v2.sql is authoritative for the exact trigger text.
--
-- STATUS: FOLDED IN on this branch (2026-07-21). schema_v2.sql now carries
-- every statement below (identity deltas as real columns + table-level
-- CHECKs instead of the ALTERs), schema_v2.py carries the uid helpers
-- (session_uid, annotation_uid, expansion_uid, commentary_uid, style_uid,
-- bundle_digest) with golden vectors, and tests/test_review_extensions.py
-- is the validation suite (73/73 with the committed suite). This file
-- remains the annotated rationale; the folded schema is the source of
-- truth. Landing must precede the first HF publish (CORE-1312): session
-- linkage cannot be retrofitted onto published endorsement rows.
--
-- Layer boundaries (same vocabulary as schema_v2.sql):
--   CORPUS-ADJACENT (community-writable, append-only, publish-eligible):
--     review_sessions, session_options, session_endorsements,
--     session_rankings, option_annotations, option_expansions,
--     concept_commentary
--   PRIVATE (never exported, same boundary as contributor_identities):
--     the contributor_identities deltas (email, credit_preference). The
--     email NEVER appears in any corpus-adjacent table; review_sessions
--     carries only contact_captured, a yes/no assertion.
--   DERIVED (regenerable, mutable): commentary_moderation
--   REFERENCE (maintainer-curated): import_sources
--   DEFERRED (created inert, NOT part of the one-way door):
--     message_endorsements
--
-- uid minting (formulae live in schema_v2.py next to option_uid):
--   session uid  = 'ses_' + sha256(canonical-bundle-json)[:24]
--   child uids   = '<pfx>_' + sha256(pfx ‖ 0x1F-joined natural key)[:24]
--     ann: (session_uid, option_uid, contributor_id, kind)
--     exp: (session_uid, option_uid, contributor_id, NFC(expansion))
--     com: (session_uid, contributor_id, concept_slug-or-'', locale, topic,
--           sha256(body))
--     sty: (session_uid, contributor_id, locale, field)
--   Deterministic on purpose: re-importing the same bundle re-mints the same
--   uids, so ingest is INSERT-idempotent and never duplicates. Interior
--   U+001F is rejected by the same _digest guard as option_uid.
-- ===========================================================================

PRAGMA foreign_keys = ON;   -- per-connection, as in schema_v2.sql; consumers
                            -- must connect through schema_v2.connect()

-- ===========================================================================
-- IDENTITY DELTAS (decided 2026-07-21) — private side only
-- ===========================================================================
-- The published corpus carries opaque contributor ids ONLY (CORE-1501 Q1,
-- option (a) — decided). What a contributor is CALLED on public credit
-- surfaces (CONTRIBUTORS.md, locale dashboards, founding-reviewer marks) is
-- their explicit choice:
--   'anonymous' — opaque id only (the default; credit is opt-IN)
--   'handle'    — their GitHub handle
--   'name'      — their chosen display_name
-- consent_public_credit (committed column) is kept and derived
-- (credit_preference <> 'anonymous'); the importer writes both. Collapsing
-- the boolean into the enum is a cleanup CORE-1502 may take when these fold
-- into the CREATE TABLE — additive ALTERs are used here so the committed
-- test suite keeps passing unchanged.
--
-- EMAIL (decided 2026-07-21: collected at every submission, validated):
--   * lives HERE and only here. It never enters a bundle file — Stage-1
--     bundles are submitted by public PR, so an email inside the bundle
--     would be published to the repo forever. Transport options for getting
--     it to this private column are in doc 01 §4a.
--   * validation tiers: syntax + normalization at intake (the CHECK below is
--     the DB floor only — one @, a dotted domain, no whitespace; the
--     importer stores it trimmed with the domain lowercased and runs the
--     real syntax check); deliverability verification is a magic-link flow
--     when the portal ships, recorded in email_verified_at. An unverified
--     email never blocks a submission.
ALTER TABLE contributor_identities ADD COLUMN email TEXT
    CHECK (email IS NULL
           OR (email = TRIM(email)
               AND email NOT LIKE '% %'
               -- Fixed post-fold: LIKE '% %' covers only U+0020; tab/CR/LF
               -- need their own guards (LIKE wildcards match controls).
               AND email NOT GLOB '*' || char(9)  || '*'
               AND email NOT GLOB '*' || char(10) || '*'
               AND email NOT GLOB '*' || char(13) || '*'
               AND email LIKE '%_@_%.%_'
               AND email NOT LIKE '%@%@%'));
ALTER TABLE contributor_identities ADD COLUMN email_verified_at TEXT;
ALTER TABLE contributor_identities ADD COLUMN credit_preference TEXT NOT NULL
    DEFAULT 'anonymous'
    CHECK (credit_preference IN ('anonymous', 'handle', 'name'));
-- Cross-column rule (importer-enforced, drift-tested; SQLite cannot ADD a
-- table-level CHECK): credit_preference='name' requires display_name;
-- 'handle' requires github_handle. Folding into CREATE TABLE makes it a real
-- CHECK at migration time.

-- ===========================================================================
-- REFERENCE: import sources — the registry behind provenance + the license line
-- ===========================================================================
-- Every non-human candidate stream is registered here so license posture and
-- attribution are data, not lore. `redistributable` gates whether terms from
-- this source may be STORED as options / exported in the Apache-2.0 corpus,
-- or only DISPLAYED as attributed references in the review kit (doc 05).
-- option_provenance.source_detail carries this id for source='model'/'import'.

CREATE TABLE import_sources (
    id              TEXT PRIMARY KEY,          -- 'model:aya-expanse-32b', 'initiative:hedy'
    kind            TEXT NOT NULL CHECK (kind IN ('model', 'initiative', 'dataset')),
    name            TEXT NOT NULL,             -- display name: 'Hedy', 'Aya Expanse 32B'
    url             TEXT,
    license_spdx    TEXT,                      -- 'Apache-2.0', 'EUPL-1.2'; NULL = none found
    redistributable INTEGER NOT NULL DEFAULT 0 CHECK (redistributable IN (0, 1)),
    attribution     TEXT,                      -- credit line required when displayed/exported
    fetched_ref     TEXT,                      -- commit sha / dataset revision imported from
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (id = LOWER(id) AND id NOT LIKE '% %' AND instr(id, char(31)) = 0),
    -- Redistribution is a verified license posture, never a default: flipping
    -- it on requires a recorded license id.
    CHECK (redistributable = 0 OR license_spdx IS NOT NULL)
);

-- ===========================================================================
-- CORPUS-ADJACENT: review sessions — one completed sitting of the review app
-- ===========================================================================
-- The provenance + verification anchor for everything a reviewer produced in
-- one sitting. uid is content-addressed from the canonical bundle bytes, so
-- re-importing the same bundle is idempotent, not a duplicate.
--
-- MUTABILITY: the session row is the ONE intake table with a workflow, so it
-- is append-only EXCEPT status / verification_report / notes (the pipeline's
-- own columns). Everything evidential — who, where, which kit, what rung,
-- when — is frozen by trigger below.

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
    bundle_digest       TEXT NOT NULL,         -- full sha256 of the canonical bundle (64 hex);
                                               -- uid is its 24-hex truncation
    contact_captured    INTEGER NOT NULL DEFAULT 0 CHECK (contact_captured IN (0, 1)),
                                               -- email reached the PRIVATE channel; the email
                                               -- itself is in contributor_identities only
    started_at          TEXT,                  -- client-reported; advisory evidence
    submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
    status              TEXT NOT NULL DEFAULT 'submitted'
                        CHECK (status IN ('submitted',   -- bundle received
                                          'verifying',   -- pipeline running
                                          'accepted',    -- rows ingested into corpus
                                          'returned',    -- fixable problem; may resubmit
                                          'rejected')),  -- guideline violation; not ingested
    verification_report TEXT,                  -- JSON, one entry per pipeline stage (doc 01 §5)
    notes               TEXT,
    CHECK (uid GLOB 'ses_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
               || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    -- Fixed post-fold: '[0-9a-f]*' anchors only the first character; the
    -- committed schema uses the negated class over the whole string and also
    -- binds the uid to the digest's truncation.
    CHECK (bundle_digest NOT GLOB '*[^0-9a-f]*' AND length(bundle_digest) = 64),
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

-- Terminal states stay terminal: an accepted session has already been
-- ingested (un-accepting would orphan corpus rows), and a rejection is a
-- moderation decision with its own record. A returned session is resubmitted
-- as a NEW bundle (new content -> new uid), never mutated back.
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

-- -- Session junctions ---------------------------------------------------------
-- Which corpus rows a session produced. options/endorsements stay exactly as
-- committed (no new columns on frozen shapes); linkage lives here. `elicited`
-- preserves the blind-first ordering — the research signal Stage 1 exists to
-- collect. Fully frozen: junction rows are facts about an accepted ingest.

CREATE TABLE session_options (
    session_uid  TEXT NOT NULL REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    option_uid   TEXT NOT NULL REFERENCES options(uid) ON DELETE RESTRICT,
    elicited     TEXT NOT NULL CHECK (elicited IN ('blind',         -- offered before candidates shown
                                                   'after_reveal',  -- offered after seeing candidates
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

-- ===========================================================================
-- CORPUS-ADJACENT: rankings — session-scoped preference order
-- ===========================================================================
-- Separate from endorsements on purpose:
--   endorsement = "I would teach this word"   (positive, at-most-one per person)
--   ranking     = "among those, this order"   (re-elicitable, session-scoped)
-- Append-only across sessions; aggregation reads each contributor's LATEST
-- accepted session per (concept, locale, pl_scope) via latest_rankings.
-- No downvotes anywhere: an unranked, unendorsed option is simply "passed".

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
    -- KEY (SQLite rule; canon_selections uses the same UNIQUE-with-pl_scope
    -- pattern for the same reason).
    UNIQUE (session_uid, concept_id, locale, pl_scope, option_uid)
);

-- One option per rank slot within a session's view of a concept. pl_scope is
-- never NULL (the '*' sentinel), so the index needs no IFNULL gymnastics.
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

CREATE TRIGGER trg_rankings_append_only
BEFORE UPDATE ON session_rankings
BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only: a new session supersedes them'); END;
CREATE TRIGGER trg_rankings_no_delete
BEFORE DELETE ON session_rankings
BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only'); END;

-- ===========================================================================
-- CORPUS-ADJACENT: annotations — neutral, crowd-attestable descriptors
-- ===========================================================================
-- Distinct from option_flags (moderation/harm): an annotation carries no
-- resolution workflow and no negative charge. This is the transliteration
-- checkbox, alongside the descriptors that make the corpus useful
-- terminology data for `legesher translate`:
--   * transliteration popularity per locale = revealed preference feeding
--     locales.terminology_policy (Bengali-style communities are legitimate);
--   * option_flags(reason='transliteration') stays reserved for the policy
--     violation (a MODEL candidate that dodged into transliteration).
-- Vocabulary is a CHECK, matching the house style for flags/methods; adding
-- a kind rides a migration like any vocabulary change.

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

-- ===========================================================================
-- CORPUS-ADJACENT: expansions — the phrase layer (elif-class concepts)
-- ===========================================================================
-- The reviewed agreement for phrase-derived tokens has TWO layers:
--   1. the expanded phrase in the target language (prose; spaces welcome)
--   2. the contracted surface form that becomes the identifier (the option)
-- Options carry layer 2. Expansions carry layer 1, attached to the option
-- whose contraction they justify. The canon TOML gains an optional
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

-- ===========================================================================
-- CORPUS-ADJACENT: commentary — free-text community knowledge per concept
-- ===========================================================================
-- The word-formation / pedagogy / register discussion that belongs to a
-- CONCEPT (or the locale as a whole), not to one option — the terminology
-- feedstock for `legesher translate` beyond the packed word.
--
-- The community row is APPEND-ONLY and carries no workflow. Whether a piece
-- of commentary is publishable is a MODERATION verdict — derived, mutable,
-- re-runnable — so it lives in commentary_moderation (the option_validations
-- pattern), not on the evidence row. Export includes a commentary row only
-- when its moderation row says 'published'.

CREATE TABLE concept_commentary (
    uid               TEXT PRIMARY KEY,
    contributor_id    TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid       TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    concept_id        INTEGER REFERENCES concepts(id) ON DELETE RESTRICT,
                      -- NULL = locale-level commentary. Export keys by slug;
                      -- the INTEGER id never leaves this database.
    locale            TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    topic             TEXT NOT NULL
                      CHECK (topic IN ('word_formation',  -- how to build/concatenate terms
                                       'expansion',       -- how a phrase concept reads in full
                                       'register',        -- formal/informal/diglossia notes
                                       'pedagogy',        -- how this is taught natively
                                       'style',           -- feeds style-guides/<locale>.yml
                                       'general')),
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
    moderated_by    TEXT,                      -- maintainer / pipeline identifier
    moderated_at    TEXT,
    note            TEXT
);

-- ===========================================================================
-- CORPUS-ADJACENT: style ratifications — track 3
-- ===========================================================================
-- One reviewer's answer to one named style-profile question for a locale
-- (doc 08 §7 field list). The style-guides/<locale>.yml generator aggregates
-- these exactly as canon aggregates endorsements: evidence rows here, the
-- shipped guide is a generated artifact, promotion is a query. Style guides
-- remain SUGGESTIONS — ratification records community preference, not law.

CREATE TABLE style_ratifications (
    uid             TEXT PRIMARY KEY,
    contributor_id  TEXT NOT NULL REFERENCES contributors(id) ON DELETE RESTRICT,
    session_uid     TEXT REFERENCES review_sessions(uid) ON DELETE RESTRICT,
    locale          TEXT NOT NULL REFERENCES locales(tag) ON DELETE RESTRICT,
    field           TEXT NOT NULL
                    CHECK (field IN ('word_boundaries',         -- '_' | concatenate | camel
                                     'constants_strategy',      -- marker_affix | double_separator | positional
                                     'class_marker',            -- morphology statement
                                     'modifier_order',          -- adjective/noun order in compounds
                                     'abbreviation_granularity',-- letter | word | character
                                     'identifier_length_max',
                                     'numerals_policy',         -- ascii_only | native_in_identifiers
                                     'docstring_mood',
                                     'terminology_policy',      -- loanword-vs-purism stance
                                     'zen_preamble')),
    value           TEXT NOT NULL,             -- per-field value grammar in doc 01 §7
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

-- ===========================================================================
-- DEFERRED: message-track endorsements (track 2)
-- Created inert alongside message_templates / message_translations, and like
-- them NOT part of the HF one-way door. Activated with the messages track.
-- NOTE for that activation: message_translations has an AUTOINCREMENT id; if
-- message endorsements are ever published, the same content-addressed-key
-- rework options got must happen FIRST (same reasoning as options.uid).
-- ===========================================================================

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

-- ===========================================================================
-- VIEWS
-- ===========================================================================

-- Each contributor's LATEST accepted session per (concept, locale, pl_scope):
-- the ranking set that counts. Deterministic on ties (submitted_at, then uid).
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
)
SELECT session_uid, contributor_id, concept_id, locale, pl_scope,
       option_uid, rank, revised_after_reveal, comment, submitted_at
FROM scoped
WHERE session_recency = 1;

-- Promotion check per option — a THIN layer over the committed
-- option_standings, adding exactly two things: the native-endorser threshold
-- and canon-eligibility mirrored from trg_canon_requires_valid_identifier
-- (identifier_valid AND script_consistent AND (nfkc_stable OR
-- sara-am-only)). Thresholds live here, in one place (CORE-1501 Q5
-- recommendation: >=2 native, zero open flags), easy to re-cut.
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

-- The one-endorsement-away queue: what the app shows a locale's NEXT reviewer
-- first (doc 03 §2). Live, canon-eligible options one native endorsement
-- short of the reviewed bar.
CREATE VIEW second_endorsement_queue AS
SELECT concept_slug, locale, pl_scope, option_uid, surface_form,
       native_verified_or_above, endorsements
FROM option_promotion_status
WHERE reviewed_eligible = 0
  AND canon_eligible = 1
  AND open_flags = 0
  AND native_verified_or_above = 1;

-- Pack promotion dashboard: the experimental -> official gate per
-- (PL x locale) as a query. Numbers are proposals (doc 04 §7) pending
-- Madison's cut; the gate reads THIS view so re-cutting is one place.
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
-- canon word plus ranked alternates, descriptors, and the most-attested
-- expansion — the "how else is this concept expressed" layer prompt assembly
-- injects. Published commentary joins by concept slug in the exporter.
-- License note: rows whose ONLY provenance is a non-redistributable
-- import_source are excluded by the EXPORTER (a provenance condition the
-- export code applies; this view is also the maintainers' internal lens, so
-- it stays unfiltered).
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
-- checkbox exists to measure, and the input to a terminology_policy
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
