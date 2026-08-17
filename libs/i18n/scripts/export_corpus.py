"""Export the CORPUS layer of a v2 translations database to Parquet (CORE-1505).

Read-only with respect to the source database. Writes, into ``<out>``: one
Parquet file per Hugging Face dataset config under ``data/``; the dataset card
as ``README.md``, with its banner under ``assets/``; the card's two companions,
``NOTICE`` (upstream licence text) and ``PRIVACY.md`` (the privacy posture),
both linked from the card and both on the push allowlist; and the
reconciliation ledger ``reconciliation.json``.

Nothing written here may cite an internal ticket. These files are read by
people outside the project, to whom a bare ``CORE-####`` is an unresolvable
reference; the test suite asserts it over every published text file.

The publish surface is the CORPUS layer and nothing else:

    concepts, terms, options (+ cached validations, + aggregated provenance
    sources), endorsements, contributors

Everything outside that surface is NEVER exported, and the script is built to
fail loudly rather than trust the reader (CORE-1502):

* ``contributor_identities`` -- the only way back from an opaque ``c_<hex>`` id
  to a person. :data:`NEVER_EXPORT` is asserted against every config's SQL
  before a single row is read.
* ``canon_selections`` -- the maintainer decision. The canon lives in the
  monorepo as PR-reviewable text; the community corpus must never imply that
  publishing it is on the table.
* the whole CORE-1538 review-intake layer, ``option_flags``, and ``build_meta``
  -- session evidence, contact/verification signals, moderation reports, and
  salt provenance. Excluded by declaration in :data:`NEVER_EXPORT`, never by
  omission.

Columns are audited too: after writing, every Parquet file is re-opened and the
export aborts if any column in :data:`FORBIDDEN_COLUMNS` survived. Belt (SQL
never selects them) and suspenders (the files prove it).

Counts are DERIVED, never stored: no config carries an endorsement-count
column. The reconciliation ledger recomputes the total from the exported
``endorsements`` rows and cross-checks it against the ``endorsement_counts``
view, so a consumer can always reproduce the headline number from the rows.

Usage:
    uv run python scripts/export_corpus.py --db build/translations_v2.db \\
                                           --out build/hf-corpus \\
                                           [--target-repo legesher/language-corpus] \\
                                           [--push --governance-signoff CORE-1502]

``--push`` runs FOUR gates before the export writes anything, in order:

1. approval -- ``--governance-signoff CORE-1502`` AND
   ``LEGESHER_HF_PUSH_APPROVED=1``; refused before any network library import;
2. target -- a non-default ``--target-repo`` must be repeated in
   ``LEGESHER_HF_TARGET_OVERRIDE`` (a typo must not mint keys against the
   wrong repo);
3. provenance -- the database must be a ``--publish`` build whose
   ``build_meta`` salt fingerprint matches ``$LEGESHER_CONTRIBUTOR_SALT``
   (which therefore must be set in the pushing shell);
4. Hub auth -- ``whoami`` preflight, so bad credentials fail before the
   export runs, not mid-upload (this gate is the first to touch the network).

The first push freezes every published key forever, so it is a governance
act, not a script flag.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import textwrap
from pathlib import Path
from typing import Any

#: Tables that must never appear in a published config, under any name, ever.
#:
#: ``contributor_identities`` is the pre-image of the opaque contributor ids --
#: the ONLY way back from ``c_<hex>`` to a person (CORE-1502). ``canon_selections``
#: is the maintainer decision, which lives in the monorepo as reviewable text
#: and is not community data. :func:`_assert_configs_avoid_private_tables` scans
#: every config's SQL against this set before a single row is read.
#:
#: The review-intake layer (CORE-1538) is excluded BY DECLARATION, not by
#: omission: ``review_sessions`` carries contact/verification signals, the
#: session evidence tables are raw per-reviewer data awaiting aggregation, and
#: expansions/commentary are contributor free text whose publishability is a
#: moderation decision. If any of it is ever published, that is a deliberate
#: CONFIG_SQL + governance change, not a default.
NEVER_EXPORT: frozenset[str] = frozenset(
    {
        "contributor_identities",
        "canon_selections",
        "review_sessions",
        "session_options",
        "session_endorsements",
        "session_rankings",
        "option_annotations",
        "option_expansions",
        "concept_commentary",
        "commentary_moderation",
        "style_ratifications",
        "message_endorsements",
        # Moderation / harm reports (contributor_id + free-text note); the
        # dataset card promises these stay private pending CORE-1502 policy.
        "option_flags",
        # Screening verdicts (CORE-1828): maintainer moderation decisions with
        # free-text notes. Whether verdicts ever publish is an open CORE-1797
        # sub-decision; until it is decided, they stay private. The EXCLUSION
        # they drive is public behaviour: quarantined options (and their
        # endorsements) are held out of the options/endorsements configs via
        # the option_screening_status view, counted in the reconciliation
        # ledger's quarantined_rows.
        "option_screenings",
        # Salt fingerprint + publish provenance -- same boundary as
        # contributor_identities per its own schema comment.
        "build_meta",
    }
)

#: Column names that must not survive into any written Parquet file.
#:
#: * ``source_detail`` -- v1 reviewer labels with real first names ride in this
#:   column (the ``<firstname>_review`` family); only ``source`` is safe.
#: * ``source_key`` / ``display_name`` -- contributor_identities columns; their
#:   presence anywhere means the private table leaked.
#: * ``comment`` -- endorsement free text; may carry PII (CORE-1502 decision).
#: * ``email`` / ``verification_report`` -- contributor_identities contact and
#:   review_sessions pipeline internals (CORE-1538); private-channel only.
#: * ``github_handle`` / ``contact`` -- the remaining contributor_identities
#:   re-identification columns; any of them anywhere means the private table
#:   leaked.
#: * ``rationale`` / ``model_rationale`` -- model reasoning text.
#:   ``CONTRIBUTOR_PRIVACY.md`` promises it is never published; listing it here
#:   turns that promise into a tested guard rather than an accident of which
#:   columns ``CONFIG_SQL`` happens to select.
FORBIDDEN_COLUMNS: frozenset[str] = frozenset(
    {
        "source_detail",
        # Model reasoning text. CONTRIBUTOR_PRIVACY.md promises it is never
        # published; until now that held only because no config happened to
        # select the column. Promises belong under the tested guard.
        "rationale",
        "model_rationale",
        "source_key",
        "display_name",
        "comment",
        "email",
        "verification_report",
        "github_handle",
        "contact",
    }
)

#: The governance ticket whose sign-off gates the first (and every) HF push.
GOVERNANCE_TICKET = "CORE-1502"

#: Environment variable that must be ``1`` for ``--push`` to proceed. A CLI
#: flag alone is one typo away from a publish; the env var makes the push a
#: deliberate two-key turn.
PUSH_ENV_VAR = "LEGESHER_HF_PUSH_APPROVED"

DEFAULT_TARGET_REPO = "legesher/language-corpus"

#: One SELECT per dataset config. Rules the SQL below obeys:
#:
#: * Internal AUTOINCREMENT ids (``concepts.id``, ``terms.id``) never leave the
#:   database -- the public keys are ``concepts.slug`` and the content-addressed
#:   ``opt_``/``end_``/``c_`` uids.
#: * ``option_provenance.source_detail`` is NOT selected: it carries v1 reviewer
#:   labels containing real first names (CORE-1505). Only the closed ``source``
#:   vocabulary is exported, aggregated per option into a ``sources`` list.
#: * ``endorsements.comment`` is NOT selected: free text offered next to a vote
#:   may carry PII (a name, an email, an @-handle), so publish-or-strip is a
#:   CORE-1502 governance decision and the default is strip.
#: * Every query carries a total ORDER BY so re-exporting the same database
#:   yields byte-identical Parquet files.
CONFIG_SQL: dict[str, str] = {
    "concepts": """
        SELECT slug, definition_en, definition_source, category, pattern_class,
               notes, created_at, updated_at
        FROM concepts
        ORDER BY slug
    """,
    "terms": """
        SELECT c.slug AS concept_slug, t.programming_language, t.name,
               t.category, t.subcategory, t.version_added, t.version_removed,
               t.usage_note, t.doc_url, t.export_role, t.created_at, t.updated_at
        FROM terms t
        JOIN concepts c ON c.id = t.concept_id
        ORDER BY t.programming_language, t.name, c.slug
    """,
    "options": """
        SELECT o.uid AS option_uid, c.slug AS concept_slug, o.locale,
               o.programming_language, o.pl_scope, o.surface_form,
               o.first_seen_at, o.withdrawn_at,
               v.identifier_valid, v.nfkc_stable, v.script_consistent,
               v.collides_en_keyword, v.min_interpreter_ok,
               v.validator_version, v.checked_at
        FROM options o
        JOIN concepts c ON c.id = o.concept_id
        LEFT JOIN option_validations v ON v.option_uid = o.uid
        -- Quarantined community submissions never export until a maintainer
        -- clears them (CORE-1828); counted in the ledger's quarantined_rows.
        WHERE NOT EXISTS (
            SELECT 1 FROM option_withheld q
            WHERE q.option_uid = o.uid
        )
        ORDER BY o.uid
    """,
    "endorsements": """
        SELECT e.uid, e.option_uid, e.contributor_id, e.method,
               e.rung_at_endorsement, e.created_at, e.retracted_at
        FROM endorsements e
        -- An endorsement of a quarantined option would dangle (its option row
        -- is held back above) and leak that the submission exists; held out
        -- with its option (CORE-1828).
        WHERE NOT EXISTS (
            SELECT 1 FROM option_withheld q
            WHERE q.option_uid = e.option_uid
        )
        ORDER BY e.uid
    """,
    "contributors": """
        SELECT id, current_rung, joined_at
        FROM contributors
        ORDER BY id
    """,
}

#: The provenance aggregation feeding the ``options.sources`` list column.
#: DISTINCT + sorted: the list answers "what kinds of source attested this
#: rendering", not "how many rows" -- row-level provenance stays private
#: because its ``source_detail`` cannot be published (see above).
PROVENANCE_SOURCES_SQL = """
    SELECT DISTINCT option_uid, source
    FROM option_provenance
    ORDER BY option_uid, source
"""

#: Base table behind each config, for the row-count reconciliation.
CONFIG_BASE_TABLE: dict[str, str] = {
    "concepts": "concepts",
    "terms": "terms",
    "options": "options",
    "endorsements": "endorsements",
    "contributors": "contributors",
}

#: How many base-table rows each config held back under quarantine
#: (CORE-1828). The reconciliation requires db_rows == parquet_rows +
#: quarantined_rows -- an exclusion the ledger cannot see is a silent cap,
#: and a count that does not reconcile is a corrupted corpus.
QUARANTINED_COUNT_SQL: dict[str, str] = {
    "options": """
        SELECT COUNT(*) FROM options o
        WHERE EXISTS (
            SELECT 1 FROM option_withheld q
            WHERE q.option_uid = o.uid
        )
    """,
    "endorsements": """
        SELECT COUNT(*) FROM endorsements e
        WHERE EXISTS (
            SELECT 1 FROM option_withheld q
            WHERE q.option_uid = e.option_uid
        )
    """,
}

#: ``option_withheld`` as an empty relation, prepended to a query when the real
#: view is absent (CORE-1838). A CTE shadows a table of the same name, so this
#: needs no second copy of any query — the screening predicate stays written
#: once, in one place, and simply matches nothing.
#:
#: Absent screening objects mean a database carried forward from before
#: CORE-1828: no verdict was ever recorded on it, so nothing is withheld, and
#: exporting every row is the CORRECT reading rather than a lenient one. It is
#: the same rule the schema states for a missing screening ROW ("absence
#: changes nothing"), one level up. The export cannot install the objects
#: itself: it opens the database ``mode=ro`` on purpose, so that publishing can
#: never mutate the artifact it is publishing.
_NO_SCREENING_CTE = (
    "WITH option_withheld(option_uid, verdict) AS (SELECT NULL, NULL WHERE 0)\n"
)


def _screening_installed(conn: sqlite3.Connection) -> bool:
    """Whether this database has the CORE-1828 screening view at all."""
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'option_withheld'"
        ).fetchone()
        is not None
    )


def _screening_sql(sql: str, *, installed: bool) -> str:
    """*sql*, made runnable on a database that predates screening."""
    return sql if installed else _NO_SCREENING_CTE + sql


#: The PINNED Arrow schema of every config, as (column, kind) pairs.
#:
#: Inference (``pa.table(dict)``) types each column from the data it happens to
#: hold, so a column that is all-NULL in one export (``withdrawn_at`` before the
#: first withdrawal, the validation columns before the first validator run)
#: ships as Arrow type ``null`` and silently flips to a real type the moment
#: data arrives -- schema drift across HF revisions of the same dataset.
#: Declaring the schema also makes the export byte-identical across data
#: states, not just across re-runs of one state.
#:
#: Kinds: ``string`` (ids, text, and ISO-8601 timestamps -- SQLite stores them
#: as TEXT and the corpus publishes them verbatim), ``bool`` (the validation
#: flags; SQLite stores 0/1, the published type is a real boolean), and
#: ``list<string>`` (the aggregated provenance ``sources``). No config
#: currently carries a genuine integer column -- the endorsement count is
#: derived, never stored, by design.
#:
#: CONFIG_SQL and this map must change together; the export refuses on drift.
CONFIG_SCHEMA: dict[str, list[tuple[str, str]]] = {
    "concepts": [
        ("slug", "string"),
        ("definition_en", "string"),
        ("definition_source", "string"),
        ("category", "string"),
        ("pattern_class", "string"),
        ("notes", "string"),
        ("created_at", "string"),
        ("updated_at", "string"),
    ],
    "terms": [
        ("concept_slug", "string"),
        ("programming_language", "string"),
        ("name", "string"),
        ("category", "string"),
        ("subcategory", "string"),
        ("version_added", "string"),
        ("version_removed", "string"),
        ("usage_note", "string"),
        ("doc_url", "string"),
        ("export_role", "string"),
        ("created_at", "string"),
        ("updated_at", "string"),
    ],
    "options": [
        ("option_uid", "string"),
        ("concept_slug", "string"),
        ("locale", "string"),
        ("programming_language", "string"),
        ("pl_scope", "string"),
        ("surface_form", "string"),
        ("first_seen_at", "string"),
        ("withdrawn_at", "string"),
        ("identifier_valid", "bool"),
        ("nfkc_stable", "bool"),
        ("script_consistent", "bool"),
        ("collides_en_keyword", "bool"),
        ("min_interpreter_ok", "bool"),
        ("validator_version", "string"),
        ("checked_at", "string"),
        ("sources", "list<string>"),
    ],
    "endorsements": [
        ("uid", "string"),
        ("option_uid", "string"),
        ("contributor_id", "string"),
        ("method", "string"),
        ("rung_at_endorsement", "string"),
        ("created_at", "string"),
        ("retracted_at", "string"),
    ],
    "contributors": [
        ("id", "string"),
        ("current_rung", "string"),
        ("joined_at", "string"),
    ],
}

#: Well-formedness floor for ``options.locale``: language[-Script][-REGION] in
#: RFC 5646 canonical casing (lowercase language, Titlecase script, UPPERCASE
#: region or 3-digit UN M.49), mirroring the CHECK constraint on ``locales.tag``.
#: This is SYNTAX only -- registry-level validation (is ``qq`` a real language?)
#: arrives when CORE-1500's ``legesher_i18n/bcp47.py`` validator merges; until
#: then this regex is the export-side floor.
BCP47_WELL_FORMED = re.compile(r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|[0-9]{3}))?$")

#: The frontmatter line the rendered `language:` list is spliced in after. A
#: named constant because it is a LOAD-BEARING anchor, not decoration: change
#: the licence line without changing this and the card loses its language list.
#: :func:`_splice` refuses rather than letting that ship.
CARD_LICENSE_ANCHOR = "license: cc-by-4.0\n"

#: Stand-in for the dataset repo id inside :data:`DATASET_CARD`. The push
#: target is a runtime value (``--target-repo``), so a card that hardcodes
#: the canonical id would, on a rehearsal push to another namespace, tell
#: readers to load a different dataset and file issues somewhere they are
#: not wanted. Substituted in :func:`_render_dataset_card`, which REFUSES
#: if the placeholder has gone missing from the template.
CARD_REPO_PLACEHOLDER = "{{REPO}}"

#: Stand-in for the number of published configs. The card's own rule is to
#: never state a number it cannot prove, and a hardcoded "Five configs"
#: above six rows is exactly the drift that rule exists to prevent.
CARD_CONFIG_COUNT_PLACEHOLDER = "{{CONFIG_COUNT}}"

#: Wrap column for the ``## Languages`` list.
#:
#: The locale list is NOT a table (Madison, 2026-08-17). It went from two
#: columns to six to twelve chasing the full width, and every version had the
#: same flaw: a markdown table must have a header row, every column pair here
#: holds the same thing, so the header was either the same two words repeated
#: across the page or -- once emptied -- a blank band above the data. Neither
#: describes anything. A flowing list has no header to get wrong, fills the
#: width by construction, and reflows to the reader's viewport instead of
#: forcing a horizontal scrollbar on a phone.
LANGUAGE_LIST_WIDTH = 78

#: The privacy posture, kept OFF the dataset card (Madison, 2026-08-17). It
#: had grown into a bullet list that restated what the Community contributions
#: section already says, and it cited internal ticket numbers that mean nothing
#: to a reader of a public dataset. It ships beside the card as ``PRIVACY.md``,
#: which the card links. Nothing published here may cite an internal ticket:
#: the card and its companions are read by people outside the project, and a
#: bare ``CORE-####`` is an unresolvable reference to them.
PRIVACY_FILE = """\
# Privacy

## Contributors are opaque tokens, never people

A contributor appears in this dataset as an id like `c_1a2b3c4d5e6f7890` --
a salted digest, and nothing else. It is never a name, an email, or a handle.
The mapping from that token back to a person is held privately by Legesher and
has never been part of any published revision of this dataset.

The `contributors` config carries exactly three columns: the token, the
reviewer's current standing, and the date they joined.

## What we deliberately leave out

| Held back | Why |
| --- | --- |
| The fine-grained provenance label on each rendering | Older labels embed a reviewer's first name. Only the four-value `sources` vocabulary is published. |
| The free-text comment attached to an endorsement | A note written next to a vote can name people or say something about them. We strip it rather than screen it. |
| Moderation and harm reports on renderings | These are signals about words *and* about the people who reported them. They stay private. |

## Withdrawal

A contributor may ask to be forgotten at any time.

Every field that could identify them is erased, and the record is marked
withdrawn. Their contributor token and their endorsements remain, because
other people's choices depend on those counts, and an endorsement with no
person attached says nothing about anyone. **Counts survive; identifying
information does not.**

No published revision of this dataset is affected by a withdrawal, because no
published revision has ever carried an identity. Withdrawal is an erasure on
our side, not a retraction of data you may already have downloaded.

## Questions

Write to <privacy@legesher.com>. We will send the full contributor privacy
commitment and the withdrawal procedure on request.
"""

#: Third-party notices, kept OFF the dataset card (Madison, 2026-08-17): the
#: card describes this dataset's licence, and three walls of someone else's
#: licence text buried what it actually says. The retention obligation is real
#: though -- MIT asks for the copyright and permission notice in all copies,
#: Apache-2.0 §4 for the notice plus a statement of changes -- so the text
#: ships beside the card as ``NOTICE`` and the card links it. Off the front
#: page, still travelling with the data.
NOTICE_FILE = """\
Legesher language corpus -- third-party notices
===============================================

The corpus as a compilation is licensed CC BY 4.0. Parts of it were taken
from the open-source projects below, which carry their own terms. Those
terms are reproduced here in full and are not superseded by CC BY 4.0.

Which rows are affected is machine-visible: every row in the `options`
config whose `sources` list contains `upstream` came from one of these
projects. See the dataset card's "Upstream projects" section.


-------------------------------------------------------------------------
legesher-translations -- https://github.com/legesher/legesher-translations
Reserved-word renderings contributed to that project.

The 149 contributors to that project are credited in its own
`.all-contributorsrc`, which stays the canonical roster and is deliberately
not duplicated here: one place to be added to, one place to be removed
from, and no stale copy. This is a Legesher repository, so retaining the
notice is a commitment we are keeping to those people rather than an
obligation someone else is holding us to. We would owe them the credit
either way.
-------------------------------------------------------------------------

MIT License

Copyright (c) 2019 Legesher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


-------------------------------------------------------------------------
UniversalPython -- https://github.com/UniversalPython/UniversalPython
Urdu (ur) renderings.

CHANGES WERE MADE. As Section 4(b) of the Apache License requires us to
state: these renderings were adapted, not reproduced verbatim. They were
normalised to our identifier conventions and re-keyed onto our concept
slugs, and some were subsequently superseded by other options in this
corpus. Do not read a rendering here as UniversalPython's own current
form -- consult the upstream project for that.
-------------------------------------------------------------------------

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

Section 4(a) asks us to give recipients a copy of the License, so here it is
in full rather than by reference alone:


                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.



-------------------------------------------------------------------------
Latino -- https://github.com/lenguaje-latino/latino
Spanish (es) renderings.

Its LICENSE.txt is standard MIT despite GitHub's licence API reporting
NOASSERTION -- the API could not classify the file's formatting; the text
itself is unambiguous.
-------------------------------------------------------------------------

The MIT License (MIT)

Copyright (c) 2015 - Latino

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

#: The card's banner image: source path in this repo, and the path it is
#: published at inside the dataset repo (the ``![](...)`` target in
#: :data:`DATASET_CARD`). The card references it relatively, so the file has to
#: ride along in the export directory AND in :data:`PUSH_ALLOW_PATTERNS`.
CARD_IMAGE_SOURCE = (
    Path(__file__).resolve().parents[1] / "assets" / "language-corpus-card.png"
)
CARD_IMAGE_TARGET = Path("assets") / "language-corpus-card.png"

#: The dataset card: what the corpus is, which languages it covers, what the
#: configs hold, and where every rendering came from. It is the public promise,
#: so it must read as a document for someone outside the project -- **no
#: internal ticket numbers**, and the two long-form commitments it makes live
#: in companions it links, :data:`PRIVACY_FILE` and :data:`NOTICE_FILE`, rather
#: than as walls of text between the reader and the data.
DATASET_CARD = """\
---
# Both the MIT- and Apache-2.0-derived subsets are permissive and allow
# inclusion in a differently-licensed compilation, provided their notices are
# retained -- that retention is the NOTICE file shipped beside this card. CC BY
# 4.0 governs the COMPILATION; it does not relicense the contributed parts.
license: cc-by-4.0
configs:
  - config_name: concepts
    data_files:
      - split: train
        path: data/concepts.parquet
  - config_name: terms
    data_files:
      - split: train
        path: data/terms.parquet
  - config_name: options
    data_files:
      - split: train
        path: data/options.parquet
  - config_name: endorsements
    data_files:
      - split: train
        path: data/endorsements.parquet
  - config_name: contributors
    data_files:
      - split: train
        path: data/contributors.parquet
---

# Legesher language corpus

![Legesher language corpus](assets/language-corpus-card.png)

## What this corpus is

A concept-centric corpus of reserved-word translations for programming
languages: every candidate rendering ("option") of a programming-language
concept in a human locale that anyone -- Legesher, another open-source project,
a community reviewer, or a model -- ever offered, together with every
endorsement a person attached to it.

This is a **growing dataset**, and append-only by design. New locales, new
concepts, new renderings, and new endorsements arrive with each release, and
nothing already published is rewritten in place: a rendering that is superseded
stays, with its replacement recorded alongside it. Treat a revision as a
snapshot of the evidence to date, not as a finished vocabulary.

Options are keyed by content-addressed, stable uids (`opt_` + 24 hex), so the
corpus survives database rebuilds and re-exports byte-identically -- an
`option_uid` you pin today means the same rendering in every later revision.

Locales ride on `options.locale` as canonical-case BCP 47 tags; there is no
separate locales config.

## Configs

{{CONFIG_COUNT}} configs. Load one with
`load_dataset("{{REPO}}", "options")`.

| Config | One row is | Columns |
| --- | --- | --- |
| `concepts` | A programming-language concept, independent of any human language | `slug` (the public, frozen key), `definition_en`, `definition_source`, `category`, `pattern_class`, `notes`, `created_at`, `updated_at` |
| `terms` | That concept's surface form in one programming language | `concept_slug`, `programming_language`, `name`, `category`, `subcategory`, `version_added`, `version_removed`, `usage_note`, `doc_url`, `export_role`, `created_at`, `updated_at` |
| `options` | One candidate rendering of one concept in one locale — the heart of the corpus | `option_uid`, `concept_slug`, `locale`, `programming_language`, `pl_scope`, `surface_form`, `first_seen_at`, `withdrawn_at`, `sources`; plus the cached validation verdict `identifier_valid`, `nfkc_stable`, `script_consistent`, `collides_en_keyword`, `min_interpreter_ok`, `validator_version`, `checked_at` (all null when a rendering has not been validated) |
| `endorsements` | One endorsement event: a person standing behind a rendering | `uid`, `option_uid`, `contributor_id`, `method`, `rung_at_endorsement`, `created_at`, `retracted_at` |
| `contributors` | A reviewer, as an opaque token | `id` (`c_` + 16 hex), `current_rung`, `joined_at` |

An option's endorsement count is `COUNT(*)` over its `endorsements` rows with
`retracted_at IS NULL`; no config ships a precomputed count column.

## Where each rendering came from

The single most important column here is `options.sources`, a list saying what
kinds of source attested that rendering. The vocabulary is cut on one question
-- *what do we owe for this?* -- so four values, four obligations:

| `sources` value | What it means | What we owe |
| --- | --- | --- |
| `legesher` | Produced by the Legesher project: our own packs, curated corrections, values we composed from existing pack material | nothing beyond this licence |
| `upstream` | Lifted from another open-source project | that project's notice and credit -- see [Upstream projects](#upstream-projects) |
| `community` | Offered or attested by an individual through our native-review process | credit on request, withdrawal on request -- see [Community contributions](#community-contributions) |
| `model` | Generated by a language model | disclosure of which model -- see [Machine-generated renderings](#machine-generated-renderings) |

An option can carry more than one value: the same rendering is often proposed
by a model and then independently attested by a reviewer. `sources` says who
offered a rendering, never how good it is -- standing comes only from the
`endorsements` rows recorded against it.

Row-level detail beyond these four values is deliberately not published: the
finer-grained provenance field carries reviewer labels that identify people,
and no part of this dataset is a route from an opaque contributor id back to a
person. That is also why the upstream project names live in this card rather
than in a column -- the obligation is machine-visible (`upstream`), the
identity of the upstream project is human-readable here.

## Upstream projects

This section and the three that follow walk the `sources` vocabulary in the
order the work actually happened. Other people rendered these concepts before
we did, and `upstream` is where their work enters the corpus — under their own
licence, with their notice retained.

| Project | Licence | What we pulled | Details |
| --- | --- | --- | --- |
| [legesher-translations](https://github.com/legesher/legesher-translations) | [MIT](https://github.com/legesher/legesher-translations/blob/main/LICENSE.md) | Reserved-word renderings — the original community translation set | A Legesher repository (`Copyright (c) 2019 Legesher`). Its 149 contributors are credited in [`.all-contributorsrc`](https://github.com/legesher/legesher-translations/blob/main/.all-contributorsrc), which stays the canonical roster |
| [UniversalPython](https://github.com/UniversalPython/UniversalPython) | [Apache-2.0](https://github.com/UniversalPython/UniversalPython/blob/main/LICENSE) | Urdu (`ur`) renderings | **Adapted, not reproduced verbatim** — normalised to our identifier conventions and re-keyed onto our concept slugs |
| [Latino](https://github.com/lenguaje-latino/latino) | [MIT](https://github.com/lenguaje-latino/latino/blob/master/LICENSE.txt) | Spanish (`es`) renderings | GitHub's licence API reports `NOASSERTION`; it could not classify the file's formatting, but the text itself is standard MIT |

Is there a dataset we should add? Open a discussion on
[this dataset](https://huggingface.co/datasets/{{REPO}}/discussions) -- if a
project has rendered these concepts in a language, we would rather credit it
than duplicate it.

## Legesher-produced renderings

Renderings marked `legesher` are the project's own work product, and they are
the bulk of the corpus. They arrive by three routes:

* **Language packs.** Terms authored for Legesher's per-locale language packs,
  written against the concept inventory (the `concepts` config) and its
  English definitions, then run through the pack pipeline's mechanical gates.
  Those per-row verdicts are not summarised away: they ship in this corpus as
  the validation columns on the `options` config, listed in
  [Configs](#configs), so a consumer can apply exactly the filters we do.
* **Curated corrections.** Fixes a maintainer made to an existing rendering
  -- a wrong form, a corrupted import, a style-guide violation. The corpus is
  append-only evidence, so the superseded rendering stays, and the correction
  enters as a new option alongside it.
* **Composed values.** Renderings a human assembled from existing pack
  material, for example compounding two already-attested words to cover a new
  concept. No model was asked; calling these `model` would overstate the
  machine's involvement, so they are `legesher`.

`legesher` describes who produced a rendering, not how good it is. That is the
division the whole corpus runs on: Legesher, the upstream projects, and the
models all **propose** — only the people in the next section **attest**. So a
Legesher-produced rendering carries exactly the native-speaker standing its
`endorsements` rows give it, and no more. Much of our own work sits here
waiting for that review rather than shipping as settled, and the corpus is
built to show you which is which.

## Community contributions

This is the other half of the section above. Renderings marked `community`
come from native speakers who reviewed our vocabulary — most often vocabulary
Legesher or an upstream project proposed — and their endorsements are what
turn a proposal into an attested rendering. A speaker can also offer a
rendering of their own, which is what makes `community` a source kind and not
only a review signal; either way the same rows carry it.

Each review is a recorded session in which a reviewer endorses, passes on, or
flags a rendering. Only endorsements appear here (the `endorsements` config),
and a reviewer's standing at the time rides on `rung_at_endorsement`.

Reviewers appear as opaque tokens, and a contributor may ask to be credited by
name or to be removed. Either request is honoured without losing the
endorsement itself, so the record of *what* was agreed survives a person's
decision about *whether to be named* — see [Privacy](#privacy).

The practical consequence for a consumer: join `options` to `endorsements` on
`option_uid` and you can separate what was proposed from what a native speaker
stood behind. That join, not the `sources` column, is the quality signal.

## Machine-generated renderings

Renderings marked `model` were produced by a language model:

| Model | Licence |
| --- | --- |
| [Aya 101](https://huggingface.co/CohereLabs/aya-101) (Cohere For AI) | Apache-2.0 |
| Claude (Anthropic) | outputs owned by the API customer |

Where the generating run recorded a specific model version it is retained in
the source database; the earliest machine-generated rows predate version
recording, so this card discloses the model family rather than promising a
per-row version.

They are a starting point, not an endorsement. A machine-generated rendering
carries no native-speaker attestation until one is recorded against it -- which
is what the `endorsements` config is for, and why packs built from this corpus
ship labelled experimental. Values a human composed from existing pack
material are `legesher`, not `model` -- see "Legesher-produced renderings"
above.

## Licence and attribution

This dataset is released under **CC BY 4.0**. You may share and adapt it,
including commercially, with attribution.

Part of it comes from other open-source projects that carry their own terms.
CC BY 4.0 governs the **compilation** and does not relicense the contributed
parts; each project's own licence is linked under
[Upstream projects](#upstream-projects), and the notices they ask us to retain
travel with the data in [`NOTICE`](NOTICE). Which obligation attaches to which
row is [`options.sources`](#where-each-rendering-came-from).

## Privacy

Contributors appear here only as opaque salted tokens -- never a name, email,
or handle -- and the mapping back to a person has never been part of any
published revision. Reviewer labels, the free text attached to an endorsement,
and moderation reports are all held back.

The full posture, including how withdrawal works, is [`PRIVACY.md`](PRIVACY.md)
beside this card.

"""


def _require_pyarrow() -> tuple[Any, Any]:
    """Import pyarrow, or explain how to get it.

    pyarrow is a dev-group dependency (``uv sync`` brings it in), but the
    exporter should say so rather than stack-trace when run from a bare
    environment.

    Returns:
        The ``(pyarrow, pyarrow.parquet)`` modules.

    Raises:
        SystemExit: when pyarrow is not importable.
    """
    try:
        import pyarrow as pa  # type: ignore[import-untyped]
        import pyarrow.parquet as pq  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit(
            "export_corpus requires pyarrow to write Parquet files.\n"
            "Install it with:  uv sync  (it is in the dev dependency group)\n"
            "or:               uv add --package legesher-i18n --dev pyarrow"
        ) from exc
    return pa, pq


def _assert_configs_avoid_private_tables() -> None:
    """Structural gate: no published config may mention a NEVER_EXPORT table.

    A word-boundary scan of the ENTIRE SQL text, deliberately NOT a FROM/JOIN
    parse. A parser is a bypass surface -- comma-joins
    (``FROM endorsements e, contributor_identities ci``), quoted names
    (``FROM "contributor_identities"``), and schema-qualified references
    (``main.canon_selections``) all slip past a FROM/JOIN regex -- while a
    refusal gate is allowed false positives: if a config ever legitimately
    needs the *word* ``canon_selections`` (even in a SQL comment), that is
    exactly the moment a human should re-read this gate.

    Runs before a single row is read.

    Raises:
        SystemExit: if any config's SQL mentions a private table.
    """
    queries = dict(CONFIG_SQL)
    queries["options.sources"] = PROVENANCE_SOURCES_SQL
    # The locale list is published text, so it is publish-surface SQL and gets
    # the same gate. It reads `locales`, which is not a private table today --
    # but "today" is the whole reason this gate is structural rather than a
    # code review: every query whose result reaches a reader belongs here.
    queries["card.languages"] = CARD_LOCALE_SQL
    for name, sql in queries.items():
        mentioned = {
            table
            for table in NEVER_EXPORT
            if re.search(rf"\b{re.escape(table)}\b", sql, re.IGNORECASE)
        }
        if mentioned:
            raise SystemExit(
                f"EXPORT REFUSED: config {name!r} mentions private table(s) "
                f"{sorted(mentioned)}. contributor_identities and "
                "canon_selections are never published (CORE-1502)."
            )


def _assert_no_forbidden_columns(pq: Any, data_dir: Path) -> None:
    """Post-write audit: re-open every Parquet file and check its schema.

    The SQL never selects these columns, but the files are the artifact that
    actually leaves the machine, so the files are what get audited.

    Args:
        pq: The ``pyarrow.parquet`` module.
        data_dir: Directory holding the written ``*.parquet`` files.

    Raises:
        SystemExit: if any written file carries a forbidden column.
    """
    for parquet_path in sorted(data_dir.glob("*.parquet")):
        names = set(pq.ParquetFile(parquet_path).schema_arrow.names)
        leaked = names & FORBIDDEN_COLUMNS
        if leaked:
            # Fail loudly AND leave nothing: a poisoned artifact must not
            # survive its own refusal, or the next `upload_folder` run would
            # push the very file this gate exists to stop.
            parquet_path.unlink()
            raise SystemExit(
                f"EXPORT REFUSED: {parquet_path.name} carried forbidden "
                f"column(s) {sorted(leaked)} and has been deleted. "
                "source_detail/source_key/display_name/comment must never be "
                "published (CORE-1502 / CORE-1505)."
            )


def _splice(card: str, anchor: str, text: str, *, before: bool) -> str:
    """Insert ``text`` at ``anchor`` in the card, or REFUSE.

    ``str.replace(..., 1)`` returns the string unchanged when the anchor is
    missing, so an edit to :data:`DATASET_CARD` that moves an anchor silently
    drops whatever it was splicing in -- and the export still succeeds, still
    passes every gate, and ships a card missing its language list. That is a
    published artifact quietly losing a section, which is worse than a build
    that stops. So the anchor is required, and required to be unique.

    Args:
        card: The card template.
        anchor: Text that must appear EXACTLY ONCE in ``card``.
        text: What to insert.
        before: Insert before the anchor rather than after it.

    Returns:
        The card with ``text`` spliced in.

    Raises:
        SystemExit: when the anchor is missing or ambiguous.
    """
    found = card.count(anchor)
    if found != 1:
        raise SystemExit(
            f"DATASET_CARD anchor {anchor!r} appears {found} times, expected "
            "exactly 1.\nThe card template and _render_dataset_card have drifted "
            "-- fix the anchor rather\nthan letting the export ship a card with a "
            "section silently missing."
        )
    return card.replace(anchor, (text + anchor) if before else (anchor + text), 1)


def _splice_after(card: str, anchor: str, text: str) -> str:
    """Insert ``text`` directly after ``anchor``. See :func:`_splice`."""
    return _splice(card, anchor, text, before=False)


def _splice_before(card: str, anchor: str, text: str) -> str:
    """Insert ``text`` directly before ``anchor``. See :func:`_splice`."""
    return _splice(card, anchor, text, before=True)


#: The locales the card may name: exactly those carrying an option the
#: ``options`` config actually publishes. The ``option_withheld`` filter is the
#: same one that config applies (CORE-1828) -- without it, a locale whose every
#: option is quarantined is announced in the Hub-indexed ``language:`` header
#: while shipping no rows, which is the card claiming coverage the data does
#: not have.
CARD_LOCALE_SQL = """
    SELECT DISTINCT o.locale AS locale, l.name AS name
    FROM options o
    LEFT JOIN locales l ON l.tag = o.locale
    WHERE NOT EXISTS (
        SELECT 1 FROM option_withheld q
        WHERE q.option_uid = o.uid
    )
    ORDER BY o.locale
"""


def _render_dataset_card(
    conn: sqlite3.Connection, *, screening: bool, target_repo: str
) -> str:
    """The dataset card with the EXACT language list rendered from the DB.

    The card never claims a count it cannot prove: the locale list is queried
    from the very rows being exported (``options.locale``, minus quarantine),
    so the card and the data cannot drift (Madison, 2026-07-14). Two
    renderings:

    * YAML ``language:`` header -- deduplicated primary language subtags, the
      shape the HF Hub indexes for search/filtering.
    * A ``## Languages`` section -- every BCP 47 locale tag with its language
      name, as one flowing list wrapped at :data:`LANGUAGE_LIST_WIDTH`.

    The name comes from ``locales.name``; a locale carrying options with no
    ``locales`` row falls back to its own tag rather than rendering nothing,
    because the locale list must stay exhaustive even when the metadata table
    lags the data.

    Args:
        conn: Read-only connection to the source database.
        screening: Whether the CORE-1828 screening tables are installed.

    Returns:
        The rendered card.
    """
    rows = conn.execute(_screening_sql(CARD_LOCALE_SQL, installed=screening)).fetchall()
    primaries = sorted({str(row["locale"]).split("-")[0] for row in rows})
    language_yaml = "language:\n" + "".join(f"  - {code}\n" for code in primaries)

    entries = [f"`{row['locale']}` {row['name'] or row['locale']}" for row in rows]
    lines = [
        "## Languages",
        "",
        *textwrap.wrap(
            f"All {len(entries)} locales carried by `options.locale` in this "
            "export, as BCP 47 tag followed by language name. The primary-subtag "
            "rollup in the frontmatter above is what the Hub indexes for search; "
            "this is the full list, script subtags and all.",
            width=LANGUAGE_LIST_WIDTH,
        ),
        "",
    ]

    # Wrap at the separators, never inside an entry, and leave the separator
    # at the END of the wrapped line. Markdown joins these lines back into one
    # paragraph with a single space, so a line that ends without its separator
    # renders as "Catalan `cs` Czech" -- two languages run together with
    # nothing between them. Keeping the tag beside its name is for whoever
    # reads the raw file; keeping the trailing separator is correctness.
    separator = " ·"
    line = ""
    for entry in entries:
        piece = entry if not line else f"{separator} {entry}"
        if line and len(line) + len(piece) + len(separator) > LANGUAGE_LIST_WIDTH:
            lines.append(line + separator)
            line = entry
        else:
            line += piece
    lines.append(line)
    section = "\n".join(lines) + "\n\n"

    card = _splice_after(DATASET_CARD, CARD_LICENSE_ANCHOR, language_yaml)
    card = _splice_before(card, "## Configs", section)

    # The card must not name a repo it is not being published to: on a
    # rehearsal push it would send readers to load a different dataset and to
    # open discussions on someone else's. Refuse rather than ship a card whose
    # self-references are wrong -- same reasoning as _splice's anchor check.
    if CARD_REPO_PLACEHOLDER not in card:
        raise SystemExit(
            f"EXPORT REFUSED: {CARD_REPO_PLACEHOLDER} has vanished from "
            "DATASET_CARD, so the card can no longer name its own dataset "
            "repo. Restore the placeholder rather than hardcoding an id."
        )
    count = len(CONFIG_SQL)
    words = {5: "Five", 6: "Six", 7: "Seven"}
    card = card.replace(CARD_CONFIG_COUNT_PLACEHOLDER, words.get(count, str(count)))
    return card.replace(CARD_REPO_PLACEHOLDER, target_repo)


def _require_card_template() -> None:
    """The card template must still be renderable. PRE-FLIGHT.

    :func:`_render_dataset_card` refuses on a missing splice anchor or a lost
    ``{{REPO}}`` placeholder, but it runs after the Parquet files are written
    -- so a template edit would leave fresh data beside the previous run's card
    and a ledger describing neither. These are static properties of the
    template, so they can be, and are, checked before anything is written.

    Raises:
        SystemExit: if an anchor is missing, duplicated, or the placeholder is
            gone.
    """
    for anchor in (CARD_LICENSE_ANCHOR, "## Configs"):
        found = DATASET_CARD.count(anchor)
        if found != 1:
            raise SystemExit(
                f"EXPORT REFUSED: DATASET_CARD anchor {anchor!r} appears "
                f"{found} times, expected exactly 1. The template and "
                "_render_dataset_card have drifted."
            )
    for placeholder in (CARD_REPO_PLACEHOLDER, CARD_CONFIG_COUNT_PLACEHOLDER):
        if placeholder not in DATASET_CARD:
            raise SystemExit(
                f"EXPORT REFUSED: {placeholder} has vanished from DATASET_CARD. "
                "Restore the placeholder rather than hardcoding a value the "
                "card cannot prove."
            )


def _require_card_image() -> None:
    """The card's banner image must exist before the export writes anything.

    The card links the image relatively, so a missing file is not a cosmetic
    problem -- it is a broken image at the top of a public dataset page.

    Raises:
        SystemExit: if the source image is not in the repository.
    """
    if not CARD_IMAGE_SOURCE.is_file():
        raise SystemExit(
            f"EXPORT REFUSED: the dataset card's banner image is missing from "
            f"{CARD_IMAGE_SOURCE}. The card links it relatively, so exporting "
            "without it ships a broken image on the dataset page. Restore the "
            "file or drop the ![](...) line from DATASET_CARD."
        )


def _require_publishable_out_dir(out_dir: Path) -> None:
    """``--out`` must name a directory this export may own. PRE-FLIGHT.

    ``--out`` is an arbitrary path and everything under it is published, so the
    two ways a wrong one does damage are checked here, before a byte is
    written -- alongside the other refusals, not halfway through the export:

    * a ``README.md`` that is not a dataset card. ``--out libs/i18n`` overwrites
      the package's own README, which is the mistake this function exists for;
      it is not hypothetical, it happened while testing this code.
    * a stray image beside the banner. It would ship on the dataset page, and
      no sweep can tell a renamed banner from a file that simply lives there,
      so this refuses rather than deleting -- the rule
      :func:`_require_clean_data_dir` already applies to Parquet.

    Re-exporting into a previous export directory stays fine: that README *is*
    a generated card, and the banner is the file we are about to rewrite.

    Args:
        out_dir: The export directory.

    Raises:
        SystemExit: if ``<out>`` holds a foreign README or a stray image.
    """
    # Every text file this export overwrites gets the same check, keyed on a
    # sentinel only our own version carries. NOTICE is the one that matters
    # most: silently destroying somebody's licence notice because --out was
    # wrong is the worst outcome on this path.
    sentinels = {
        "README.md": (CARD_LICENSE_ANCHOR, "a dataset card"),
        "NOTICE": ("third-party notices", "this export's NOTICE"),
        "PRIVACY.md": ("# Privacy", "this export's privacy posture"),
    }
    for name, (sentinel, described) in sentinels.items():
        existing = out_dir / name
        if existing.is_file() and sentinel not in existing.read_text(
            encoding="utf-8", errors="replace"
        ):
            raise SystemExit(
                f"EXPORT REFUSED: {existing} is not {described}, and this "
                "export would overwrite it. --out names a directory the export "
                "takes over entirely; point it somewhere of its own."
            )

    assets_dir = out_dir / CARD_IMAGE_TARGET.parent
    if not assets_dir.is_dir():
        return
    source = CARD_IMAGE_SOURCE.resolve()
    # rglob for the same reason as _require_clean_data_dir: the allowlist is
    # fnmatch, so assets/drafts/x.png ships too.
    bystanders = sorted(
        path.relative_to(assets_dir).as_posix()
        for path in assets_dir.rglob(f"*{CARD_IMAGE_TARGET.suffix}")
        if path.resolve() != source and path.name != CARD_IMAGE_TARGET.name
    )
    if bystanders:
        raise SystemExit(
            f"EXPORT REFUSED: {assets_dir} holds image(s) this export did not "
            f"write: {bystanders}. Everything under assets/ is published, so a "
            "bystander would ship on the dataset page. Move them aside, or "
            "point --out at a directory of this export's own."
        )


def _copy_card_image(out_dir: Path) -> None:
    """Place the card's banner image where the card's relative link points.

    The directory was vetted by :func:`_require_publishable_out_dir` before the
    export wrote anything, so this only has to put the file there.

    Args:
        out_dir: The export directory.
    """
    target = out_dir / CARD_IMAGE_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve() != CARD_IMAGE_SOURCE.resolve():
        shutil.copyfile(CARD_IMAGE_SOURCE, target)


def _require_clean_data_dir(data_dir: Path) -> None:
    """``<out>/data`` may hold no Parquet files but this run's own.

    Non-Parquet bystanders (a ``.gitkeep``, an editor swap file) are
    tolerated -- only ``*.parquet`` can ride into the dataset as data.

    ``--push`` uploads by allowlist, and ``data/*.parquet`` is ON it -- so a
    stale Parquet file from an older run (a renamed config, an abandoned
    experiment) would still ride along into the published dataset unnoticed.
    Unknown files refuse the export (a human decides what they were); the
    known config files are deleted up front, so every byte present after a
    successful run was written by that run.

    Args:
        data_dir: The ``<out>/data`` directory (already created).

    Raises:
        SystemExit: if the directory holds a Parquet file this exporter does
            not produce.
    """
    # rglob, not glob: the push matches this allowlist with fnmatch, whose
    # "*" crosses "/", so `data/nested/stale.parquet` uploads too. A guard
    # that only looks one level deep does not cover what the push publishes.
    known = {f"{name}.parquet" for name in CONFIG_SQL}
    strays = sorted(
        path.relative_to(data_dir).as_posix()
        for path in data_dir.rglob("*.parquet")
        if path.relative_to(data_dir).as_posix() not in known
    )
    if strays:
        raise SystemExit(
            f"EXPORT REFUSED: {data_dir} contains parquet file(s) not produced "
            f"by this exporter: {strays}. A stale artifact would ride along in "
            "the HF push; remove it or use a fresh --out directory."
        )
    for name in known:
        (data_dir / name).unlink(missing_ok=True)


def _arrow_schema(pa: Any, config: str) -> Any:
    """Build the pinned :data:`CONFIG_SCHEMA` for one config as a pa.schema."""
    kinds = {
        "string": pa.string(),
        "bool": pa.bool_(),
        "list<string>": pa.list_(pa.string()),
    }
    return pa.schema([(column, kinds[kind]) for column, kind in CONFIG_SCHEMA[config]])


def _require_well_formed_locales(conn: sqlite3.Connection) -> None:
    """Every published ``options.locale`` must be well-formed BCP 47.

    The locale tag is inside the frozen option uid, so a malformed or
    wrongly-cased tag published once is a permanent fork of that locale's
    corpus. The DB CHECK on ``locales.tag`` should make this unreachable; the
    export re-checks because the Parquet files are the one-way door.

    Args:
        conn: Read-only connection to the v2 database.

    Raises:
        SystemExit: listing every malformed tag found.
    """
    bad = [
        row["locale"]
        for row in conn.execute("SELECT DISTINCT locale FROM options ORDER BY locale")
        if not BCP47_WELL_FORMED.match(row["locale"])
    ]
    if bad:
        raise SystemExit(
            f"EXPORT REFUSED: malformed BCP 47 locale tag(s) in options: {bad}. "
            "Tags must be language[-Script][-REGION] in canonical casing "
            "('ar', 'zh-Hans', 'ar-EG', 'es-419'). Registry-level validation "
            "lands with CORE-1500's bcp47.py."
        )


def _sources_by_option(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Aggregate provenance to a per-option list of distinct source kinds.

    Only ``option_provenance.source`` is read -- never ``source_detail``, which
    carries v1 reviewer labels with real first names (CORE-1505).

    Args:
        conn: Read-only connection to the v2 database.

    Returns:
        ``option_uid -> sorted distinct source values``.
    """
    sources: dict[str, list[str]] = {}
    for row in conn.execute(PROVENANCE_SOURCES_SQL):
        sources.setdefault(row["option_uid"], []).append(row["source"])
    return sources


def require_push_approval(governance_signoff: str | None) -> None:
    """Refuse to push without the CORE-1502 sign-off AND the env approval.

    Runs BEFORE the export writes anything and BEFORE any network library is
    imported: the first push freezes every published key (option uids,
    endorsement uids, contributor ids) forever, so it must be impossible to
    trip over.

    Args:
        governance_signoff: Value of ``--governance-signoff``.

    Raises:
        SystemExit: unless both keys are turned.
    """
    if governance_signoff != GOVERNANCE_TICKET:
        raise SystemExit(
            f"--push requires --governance-signoff {GOVERNANCE_TICKET}. The first "
            "HF push freezes the published keys and the license posture forever; "
            f"it is gated on the {GOVERNANCE_TICKET} governance decision, not on "
            "this script."
        )
    if os.environ.get(PUSH_ENV_VAR) != "1":
        raise SystemExit(
            f"--push requires {PUSH_ENV_VAR}=1 in the environment. The flag and "
            "the variable are deliberately two separate keys: a command-line "
            "typo must not be able to publish the corpus."
        )


def require_publish_grade_db(db_path: Path) -> None:
    """Refuse to push an artifact that was not minted as a publish build.

    ``migrate_to_v2.py`` records ``publish_build`` and ``salt_fingerprint`` in
    the private ``build_meta`` table; until now verifying them before a push
    was a manual checklist item, which means a dev-salt database would push
    without complaint. This turns the checklist item into code:

    * the database must carry ``publish_build = 1`` (built under ``--publish``,
      so the salt-quality and identity-resolution gates already ran);
    * the recorded fingerprint must not be the public dev salt's;
    * ``$LEGESHER_CONTRIBUTOR_SALT`` must be set for the push and its
      fingerprint must MATCH the recorded one -- proving the artifact was
      minted with the escrowed salt the operator is holding, not some other
      salt that would fork every contributor id on the next build.

    Args:
        db_path: The database being exported.

    Raises:
        SystemExit: unless the artifact is publish-grade and salt-verified.
    """
    # Deferred on purpose: export_corpus.py carries no sys.path shim and no
    # other legesher_i18n import, so every non-push code path keeps working
    # with only stdlib + pyarrow. Hoisting this to module level would break
    # standalone non-push runs in environments without the package installed.
    from legesher_i18n.db.schema_v2 import DEFAULT_CONTRIBUTOR_SALT, salt_fingerprint

    if not db_path.is_file():
        raise SystemExit(
            f"PUSH REFUSED: no database at {db_path}. Build a publish-grade one "
            "with scripts/migrate_to_v2.py --publish first."
        )
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            meta = dict(conn.execute("SELECT key, value FROM build_meta"))
        # DatabaseError is the parent that also covers "file is not a
        # database" -- the wrong-artifact case this gate exists for must get
        # the refusal message, not a raw sqlite3 traceback.
        except sqlite3.DatabaseError:
            raise SystemExit(
                f"PUSH REFUSED: {db_path} has no readable build_meta table -- "
                "it is not a database built by scripts/migrate_to_v2.py, so "
                "its salt provenance is unknowable."
            ) from None
    finally:
        conn.close()

    if meta.get("publish_build") != "1":
        raise SystemExit(
            "PUSH REFUSED: this database was NOT built with --publish "
            f"(build_meta.publish_build = {meta.get('publish_build')!r}), so the "
            "salt-quality and identity-resolution gates never ran on it. Rebuild "
            "with scripts/migrate_to_v2.py --publish."
        )
    recorded = meta.get("salt_fingerprint")
    if not recorded or recorded == salt_fingerprint(DEFAULT_CONTRIBUTOR_SALT):
        raise SystemExit(
            "PUSH REFUSED: the artifact's contributor ids were minted with the "
            "PUBLIC dev salt (or no salt was recorded). Publishing it would make "
            "every contributor id reversible. Rebuild with --publish and the "
            "escrowed salt."
        )
    env_salt = os.environ.get("LEGESHER_CONTRIBUTOR_SALT")
    if not env_salt:
        raise SystemExit(
            "PUSH REFUSED: $LEGESHER_CONTRIBUTOR_SALT is not set. The push "
            "verifies the artifact against the escrowed salt's fingerprint; "
            "without the salt in hand there is no proof this database was "
            "minted with it."
        )
    if salt_fingerprint(env_salt) != recorded:
        raise SystemExit(
            "PUSH REFUSED: $LEGESHER_CONTRIBUTOR_SALT does not match the salt "
            f"this database was minted with (recorded fingerprint {recorded}, "
            f"supplied {salt_fingerprint(env_salt)}). Pushing it would publish "
            "contributor ids that can never be re-minted for returning "
            "contributors. Find the escrowed salt, or rebuild from v1 with the "
            "salt you hold."
        )


#: Env var that must REPEAT a non-default ``--target-repo`` for a push. The
#: first push freezes every published key against its repo, so the destination
#: gets the same two-key discipline as the push itself: a typo'd repo id must
#: not be able to mint keys against the wrong namespace.
TARGET_OVERRIDE_ENV_VAR = "LEGESHER_HF_TARGET_OVERRIDE"


def require_intended_target(target_repo: str) -> None:
    """Refuse to push anywhere but the canonical repo without a second key.

    Args:
        target_repo: Value of ``--target-repo``.

    Raises:
        SystemExit: if the target is non-default and not repeated in
            :data:`TARGET_OVERRIDE_ENV_VAR`.
    """
    if target_repo == DEFAULT_TARGET_REPO:
        return
    if os.environ.get(TARGET_OVERRIDE_ENV_VAR) != target_repo:
        raise SystemExit(
            f"PUSH REFUSED: --target-repo {target_repo!r} is not the canonical "
            f"{DEFAULT_TARGET_REPO!r}. The first push freezes every published "
            "key against its repo, so a non-default destination must be "
            f"repeated verbatim in {TARGET_OVERRIDE_ENV_VAR} -- a typo must "
            "not be able to publish to the wrong namespace."
        )


def _require_hf_api() -> Any:
    """Import huggingface_hub lazily and return the ``HfApi`` class.

    One home for the lazy import + its refusal message: every non-push code
    path works without the library installed and provably never touches the
    network stack; the two push-path callers share this guard so the install
    instructions cannot drift apart.

    Raises:
        SystemExit: if huggingface_hub is not installed.
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit(
            "PUSH REFUSED: huggingface_hub is not installed. The push path "
            "needs it: `uv add --package legesher-i18n --dev huggingface_hub` "
            "(every non-push code path works without it)."
        ) from None
    return HfApi


def preflight_hub_auth() -> None:
    """Fail a push on missing Hub auth BEFORE the export runs.

    ``push_to_hub`` runs after the export; without a preflight an
    unauthenticated run does all the export work and then dies mid-upload,
    leaving a fully-built artifact behind as if it were push-ready.

    Raises:
        SystemExit: if huggingface_hub is missing or the token is absent/bad.
    """
    hf_api = _require_hf_api()
    try:
        who = hf_api().whoami()
    except Exception as error:  # hub raises several exception types here
        raise SystemExit(
            f"PUSH REFUSED: not authenticated to the Hugging Face Hub ({error}). "
            "Run `hf auth login` or set HF_TOKEN, then re-run."
        ) from None
    print(f"Hub auth ok: {who.get('name', '?')}")


#: The only files a push may upload -- exactly what the exporter writes. A
#: stray bystander in the output directory (scratch notes, a copied
#: translations_v2.db carrying contributor_identities, an editor swap file)
#: must never ride into the dataset repo, where it would survive the later
#: public flip.
PUSH_ALLOW_PATTERNS: tuple[str, ...] = (
    "README.md",
    "NOTICE",
    "PRIVACY.md",
    "reconciliation.json",
    "data/*.parquet",
    "assets/*.png",
)


def push_to_hub(out_dir: Path, target_repo: str) -> None:
    """Upload the exported corpus files to the Hugging Face Hub.

    Args:
        out_dir: The export directory (``data/*.parquet`` + ``README.md``).
        target_repo: Dataset repo id, e.g. ``legesher/language-corpus``.
    """
    api = _require_hf_api()()
    # Private-first (CORE-1502 decision, 2026-07-14): the repo is created
    # PRIVATE and this tool never changes visibility. Going public is a
    # separate, deliberate maintainer action on the Hub -- not a flag here,
    # so no invocation of this script can accidentally publish the corpus.
    api.create_repo(
        repo_id=target_repo,
        repo_type="dataset",
        private=True,
        exist_ok=True,
    )
    api.upload_folder(
        folder_path=str(out_dir),
        repo_id=target_repo,
        repo_type="dataset",
        allow_patterns=list(PUSH_ALLOW_PATTERNS),
        # A dataset repo's commit history is as public as its files, so the
        # message obeys the same rule they do: no internal ticket, which is
        # unresolvable to everyone who can read it.
        commit_message="corpus export",
        # upload_folder only ADDS. Without this, a banner pushed under an old
        # name stays in the repo beside its replacement forever -- the export
        # directory being clean says nothing about the remote. Scoped to the
        # banner: the data files are content-addressed by config name, and a
        # blanket delete here would be one typo away from unpublishing them.
        delete_patterns=[f"{CARD_IMAGE_TARGET.parent}/*{CARD_IMAGE_TARGET.suffix}"],
    )
    print(f"Pushed {out_dir} -> {target_repo}")


def export_corpus(
    db_path: Path, out_dir: Path, target_repo: str = DEFAULT_TARGET_REPO
) -> dict[str, Any]:
    """Export the five corpus configs, the dataset card, and the ledger.

    Args:
        db_path: Path to a v2 database. Opened read-only.
        out_dir: Output directory; ``data/`` is created inside it.
        target_repo: Dataset repo id the card should name as itself. Only
            differs from the default on a rehearsal push.

    Returns:
        The reconciliation ledger (also written to
        ``<out>/reconciliation.json``).

    Raises:
        SystemExit: if the database does not exist, a config would read a
            private table, a stale artifact sits in the output directory, a
            forbidden column survives into a written file, a locale tag is
            malformed, or the row counts do not reconcile.
    """
    # Path check first: a missing --db should never surface as a pyarrow
    # installation complaint (review finding on PR #20).
    if not db_path.is_file():
        raise SystemExit(
            f"EXPORT REFUSED: no database at {db_path}. --db must point at an "
            "existing v2 translations database (build one with "
            "scripts/migrate_to_v2.py)."
        )

    pa, pq = _require_pyarrow()
    _assert_configs_avoid_private_tables()
    # Before any Parquet is written: every other refusal in this function
    # aborts with the output directory untouched, and a missing banner should
    # not be the one gate that leaves a half-built export behind.
    _require_card_template()
    _require_card_image()
    _require_publishable_out_dir(out_dir)

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    screening = _screening_installed(conn)

    _require_well_formed_locales(conn)

    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _require_clean_data_dir(data_dir)

    sources = _sources_by_option(conn)
    configs: dict[str, dict[str, int]] = {}
    active_endorsements = 0

    for name, sql in CONFIG_SQL.items():
        cursor = conn.execute(_screening_sql(sql, installed=screening))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        table_data: dict[str, Any] = {
            column: [row[index] for row in rows] for index, column in enumerate(columns)
        }
        if name == "options":
            table_data["sources"] = [
                sources.get(uid, []) for uid in table_data["option_uid"]
            ]
            columns.append("sources")
        if name == "endorsements":
            active_endorsements = sum(
                1 for value in table_data["retracted_at"] if value is None
            )

        # The pinned schema is the corpus contract: SQL and CONFIG_SCHEMA must
        # change together, and silently shipping whatever the SELECT happened
        # to produce is exactly the drift the pin exists to prevent.
        schema_columns = [column for column, _ in CONFIG_SCHEMA[name]]
        if columns != schema_columns:
            raise SystemExit(
                f"EXPORT REFUSED: config {name!r} selects {columns} but its "
                f"pinned schema declares {schema_columns}. Update CONFIG_SQL "
                "and CONFIG_SCHEMA together."
            )
        # SQLite stores booleans as 0/1 INTEGERs; the published type is bool.
        for column, kind in CONFIG_SCHEMA[name]:
            if kind == "bool":
                table_data[column] = [
                    None if value is None else bool(value)
                    for value in table_data[column]
                ]

        table = pa.table(table_data, schema=_arrow_schema(pa, name))
        pq.write_table(table, data_dir / f"{name}.parquet")

        db_rows = conn.execute(
            f"SELECT COUNT(*) FROM {CONFIG_BASE_TABLE[name]}"  # noqa: S608 -- fixed map
        ).fetchone()[0]
        quarantined = (
            conn.execute(
                _screening_sql(QUARANTINED_COUNT_SQL[name], installed=screening)
            ).fetchone()[0]
            if name in QUARANTINED_COUNT_SQL
            else 0
        )
        configs[name] = {
            "db_rows": db_rows,
            "parquet_rows": table.num_rows,
            "quarantined_rows": quarantined,
        }

    _assert_no_forbidden_columns(pq, data_dir)

    # The view sum mirrors the publish surface: endorsements on quarantined
    # options are held back above, so they are held out of the target too.
    view_sum = conn.execute(
        _screening_sql(
            """
        SELECT COALESCE(SUM(ec.endorsements), 0) FROM endorsement_counts ec
        WHERE NOT EXISTS (
            SELECT 1 FROM option_withheld q
            WHERE q.option_uid = ec.option_uid
        )
        """,
            installed=screening,
        )
    ).fetchone()[0]
    dataset_card = _render_dataset_card(
        conn, screening=screening, target_repo=target_repo
    )
    conn.close()

    ok = all(
        c["db_rows"] == c["parquet_rows"] + c["quarantined_rows"]
        for c in configs.values()
    ) and (active_endorsements == view_sum)
    reconciliation: dict[str, Any] = {
        "configs": configs,
        "derived_endorsements": {
            "parquet_active_endorsements": active_endorsements,
            "endorsement_counts_view_sum": view_sum,
        },
        "ok": ok,
    }

    _copy_card_image(out_dir)
    (out_dir / "README.md").write_text(dataset_card, encoding="utf-8")
    (out_dir / "NOTICE").write_text(NOTICE_FILE, encoding="utf-8")
    (out_dir / "PRIVACY.md").write_text(PRIVACY_FILE, encoding="utf-8")
    (out_dir / "reconciliation.json").write_text(
        json.dumps(reconciliation, indent=2) + "\n", encoding="utf-8"
    )

    width = max(len(name) for name in configs)
    print("Export reconciliation:")
    for name, count in configs.items():
        reconciled = (
            count["db_rows"] == count["parquet_rows"] + count["quarantined_rows"]
        )
        verdict = "ok" if reconciled else "MISMATCH"
        held = (
            f"  quarantined={count['quarantined_rows']:,}"
            if count["quarantined_rows"]
            else ""
        )
        print(
            f"  {name.ljust(width)}  db={count['db_rows']:>7,}  "
            f"parquet={count['parquet_rows']:>7,}  {verdict}{held}"
        )
    print(
        f"  derived endorsements: parquet(active)={active_endorsements:,}  "
        f"endorsement_counts view={view_sum:,}  "
        f"{'ok' if active_endorsements == view_sum else 'MISMATCH'}"
    )

    if not ok:
        raise SystemExit(
            "EXPORT FAILED: reconciliation mismatch (see reconciliation.json). "
            "A published file that disagrees with its source database is a "
            "corrupted corpus, not a warning."
        )
    return reconciliation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, required=True, help="v2 translations database (read-only)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="output directory (data/*.parquet, README.md, reconciliation.json)",
    )
    parser.add_argument(
        "--target-repo",
        default=DEFAULT_TARGET_REPO,
        help=f"Hugging Face dataset repo id (default: {DEFAULT_TARGET_REPO})",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help=(
            "upload the export to the Hub. Requires --governance-signoff "
            f"{GOVERNANCE_TICKET} AND {PUSH_ENV_VAR}=1; refuses BEFORE writing "
            "anything, because the first push freezes every published key."
        ),
    )
    parser.add_argument(
        "--governance-signoff",
        default=None,
        help=f"the governance ticket authorizing the push ({GOVERNANCE_TICKET})",
    )
    args = parser.parse_args(argv)

    # The push gates run FIRST: a refused push must leave no artifact behind.
    # Approval (no network library imported) -> intended target -> publish-
    # grade DB + salt fingerprint -> Hub auth. Only then is the export worth
    # building.
    if args.push:
        require_push_approval(args.governance_signoff)
        require_intended_target(args.target_repo)
        require_publish_grade_db(args.db)
        preflight_hub_auth()

    export_corpus(args.db, args.out, args.target_repo)

    if args.push:
        push_to_hub(args.out, args.target_repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
