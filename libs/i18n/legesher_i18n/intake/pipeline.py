"""The six-stage review-bundle verification pipeline (CORE-1688).

One pipeline for every intake lane: Stage-0 issue imports and Stage-1 bundle
files call the same :class:`BundleImporter`; the Stage-2 portal will too. The
stages, in order, each recorded in ``review_sessions.verification_report``:

1. **schema** — canonical-JSON + JSON Schema validation, kit compatibility,
   and the bundle-level semantic floor (ranking ⊆ endorsements, no
   flag∩ranking, concepts exist). Failure → ``returned``.
2. **conduct** — free text scanned for PII and wordlist hits. Findings
   ESCALATE to the import ritual's human; they never auto-reject. This is the
   only stage that reads content as content.
3. **identity** — attestations checked; the contributor minted via the salted
   path (CORE-1502); consent recorded at identity minting — no consent
   asserted, no identity row; the withdrawal-tombstone rule applied exactly as
   ``docs/contributor-withdrawal-runbook.md`` specifies.
4. **gates** — the committed mechanical validator suite on every NEW surface.
   ERRORS block the ROW's canon eligibility, never the session: invalid rows
   ingest as evidence with their failed validation cached (CORE-1400 reframe).
5. **quality** — WARN-only signals. Policy, stated here because it is
   load-bearing: no stage compares a human submission against model output,
   and disagreement with a model panel is not a signal at all.
6. **ingest** — append-only rows in one transaction; content-addressed uids
   make re-import a no-op; community-sourced NEW options land quarantined
   (CORE-1828) until the maintainer clears them during the ritual.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from legesher_i18n.db import schema_v2
from legesher_i18n.db.schema_v2 import (
    annotation_uid,
    bundle_digest,
    commentary_uid,
    contributor_id,
    endorsement_uid,
    expansion_uid,
    is_identity_translation,
    normalize_surface_form,
    option_uid,
    session_uid,
    style_uid,
)
from legesher_i18n.intake.canonical import canonicalize
from legesher_i18n.schema_validator import SchemaValidator
from legesher_i18n.script_policy import BIDI_EMBEDDINGS
from legesher_i18n.surface_validation import (
    VALIDATOR_VERSION,
    allowed_scripts_for,
    validate_surface,
)

__all__ = ["BundleImporter", "ImportResult", "SCREEN_VERSION"]

#: The interim screening regime (CORE-1828): the maintainer is the screen.
#: CORE-1797's automated gate will introduce its own versions.
SCREEN_VERSION = "manual-interim-v1"

_SCHEMA_PATH = Path(__file__).with_name("bundle_schema.json")


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


@lru_cache(maxsize=1)
def _validator() -> Any:
    import jsonschema

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class _Stage:
    stage: str
    status: str  # pass | warn | fail
    details: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "status": self.status, "details": self.details}


@dataclass
class ImportResult:
    """What one import attempt did, in ledger-ready form."""

    session_uid: str | None
    status: str  # accepted | returned | halted | duplicate
    report: dict[str, Any]
    locale: str | None = None
    #: Options this submission MINTED. Every one is quarantined on arrival
    #: (CORE-1828), so there is no separate quarantined list to carry.
    created_options: list[str] = field(default_factory=list)
    endorsements_linked: int = 0
    withdrawn_replay: bool = False
    needs_human_eyes: bool = False
    source_ref: str | None = None
    #: Parse-time notes from the lane that produced the bundle (unknown terms,
    #: a credit choice the form cannot satisfy). They ride the ledger and the
    #: verification report, not just stdout: a note that exists only in a
    #: terminal scrollback is a note nobody acts on.
    parse_notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "session_uid": self.session_uid,
                "status": self.status,
                "locale": self.locale,
                "created_options": self.created_options,
                "endorsements_linked": self.endorsements_linked,
                "withdrawn_replay": self.withdrawn_replay,
                "needs_human_eyes": self.needs_human_eyes,
                "source_ref": self.source_ref,
                "parse_notes": self.parse_notes,
                "report": self.report,
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _fence(text: str) -> str:
        """Neutralize submitter-controlled text for a GitHub comment.

        Report details quote surface forms, locales and slugs straight from the
        submission, and `--reply` posts them under the maintainer's account.
        Backticks, tags and leading list/heading markers would let a submitter
        shape a comment we are signing, so the whole detail is rendered as one
        inline code span with its own backticks stripped.
        """
        flattened = " ".join(text.split()).replace("`", "'")
        return f"`{flattened}`"

    def reply_text(self) -> str:
        """The "your contribution landed" reply the ritual posts on the issue."""
        if self.status == "duplicate":
            return (
                f"This submission was already imported as session "
                f"`{self.session_uid}` — nothing new to record. Thank you!"
            )
        if self.status == "halted":
            # A halt means the withdrawal-tombstone rule fired. The stage detail
            # naming the withdrawal date is for the MAINTAINER'S report only:
            # posting it would re-associate a public account with the withdrawal
            # the CORE-1780 tombstone exists to erase. The runbook says stop and
            # surface it to a human — so the human writes whatever gets said.
            return (
                "This submission needs a maintainer to look at it before it can "
                "be recorded. Nothing is wrong with your work — we will follow "
                "up directly."
            )
        if self.status != "accepted":
            lines = [
                "Thanks for the submission — it needs one more pass before it can land:",
                "",
            ]
            for stage in self.report.get("stages", []):
                for detail in stage.get("details", []):
                    if stage.get("status") == "fail":
                        lines.append(f"- {self._fence(str(detail))}")
            lines.append("")
            lines.append("Fix the items above and resubmit; nothing you wrote is lost.")
            return "\n".join(lines)
        lines = [
            "Your contribution landed. Thank you!",
            "",
            f"- Review session: `{self.session_uid}`",
        ]
        for uid in self.created_options:
            lines.append(f"- New option recorded: `{uid}`")
        if self.endorsements_linked:
            lines.append(f"- Endorsements recorded: {self.endorsements_linked}")
        lines += [
            "",
            "**What happens next:** every community submission is screened by",
            "a human maintainer before it becomes visible in rankings or the",
            "published corpus (see CONTRIBUTOR_PRIVACY.md and REVIEWING.md).",
            "The queue is walked at least weekly; once your options clear the",
            "screen they compete for the pack like every other candidate.",
        ]
        return "\n".join(lines)


class BundleImporter:
    """Imports canonical review bundles into a v2 translations database.

    Args:
        db_path: The operational v2 database (the one review store, durably
            homed in the private data repo — CORE-1794).
        salt: Contributor salt override; defaults to
            ``$LEGESHER_CONTRIBUTOR_SALT`` exactly like
            :func:`legesher_i18n.db.schema_v2.contributor_id`.
        method: ``endorsements.method`` vocabulary for this lane
            (``portal`` for bundle files, ``github`` for issue imports).
        elicited_default: ``session_options.elicited`` for non-blind rows
            (``after_reveal`` for the review app, ``quick`` for issues).
        conduct_wordlist: Locale wordlist terms whose presence in free text
            escalates to the human screen. Never auto-rejects.
        screened_by: Recorded on the quarantine verdicts this importer writes.
        required_attestations: Which boolean attestations must be affirmed for
            this lane. The bundle lane requires the full set; the Stage-0
            issue lane cannot collect a DCO sign-off (the form has no such
            checkbox — see ``issue_parser``), so it drops ``dco`` and keeps
            ``original_work`` + ``coc_agreed``.
        allow_dev_salt: Permit minting with the PUBLIC
            :data:`~legesher_i18n.db.schema_v2.DEFAULT_CONTRIBUTOR_SALT`.
            For fixtures and dry runs only — never for a database anyone will
            keep.

    Raises:
        ValueError: if the effective salt is the public dev salt and
            ``allow_dev_salt`` is not set.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        salt: str | None = None,
        method: str = "portal",
        elicited_default: str = "after_reveal",
        conduct_wordlist: list[str] | None = None,
        screened_by: str = "importer",
        required_attestations: tuple[str, ...] = ("original_work", "coc_agreed", "dco"),
        allow_dev_salt: bool = False,
    ) -> None:
        self.db_path = Path(db_path)
        self.salt = salt
        self.method = method
        self.elicited_default = elicited_default
        self.conduct_wordlist = [w.casefold() for w in (conduct_wordlist or [])]
        self.screened_by = screened_by
        self.required_attestations = required_attestations
        self.allow_dev_salt = allow_dev_salt
        self._effective_salt = (
            salt
            if salt is not None
            else os.environ.get(
                "LEGESHER_CONTRIBUTOR_SALT", schema_v2.DEFAULT_CONTRIBUTOR_SALT
            )
        )
        if (
            self._effective_salt == schema_v2.DEFAULT_CONTRIBUTOR_SALT
            and not allow_dev_salt
        ):
            raise ValueError(
                "refusing to import with the PUBLIC default contributor salt. "
                "contributor_id is an ingredient of a PRIMARY KEY: minting live "
                "rows with a public salt makes every id reversible by dictionary "
                "attack over a known username list, and forks the ids of any "
                "database built with the real salt — unrecoverably, one publish "
                "later. Set $LEGESHER_CONTRIBUTOR_SALT to the escrowed salt "
                "(or pass allow_dev_salt=True for a throwaway run)."
            )

    def _require_matching_salt(self, conn: sqlite3.Connection) -> None:
        """Refuse a salt that did not mint this database's contributor ids.

        ``build_meta.salt_fingerprint`` is the only record of WHICH salt a
        built database was minted with (schema_v2.salt_fingerprint). Importing
        under a different one silently forks every contributor id it writes —
        the same unrecoverable mistake ``migrate_to_v2.py --publish`` guards
        against, one import at a time.
        """
        row = conn.execute(
            "SELECT value FROM build_meta WHERE key = 'salt_fingerprint'"
        ).fetchone()
        if row is None:
            return  # not a --publish build; nothing to check against
        expected = schema_v2.salt_fingerprint(self._effective_salt)
        if row[0] != expected:
            raise ValueError(
                f"salt_fingerprint mismatch: this database was built with a "
                f"different contributor salt ({row[0]} on the build, "
                f"{expected} in this shell). Importing would fork every "
                "contributor id it writes. Export the escrowed "
                "$LEGESHER_CONTRIBUTOR_SALT for THIS database and re-run."
            )

    # -- public entry -------------------------------------------------------

    def import_bundle(
        self,
        bundle: dict | bytes | str | Path,
        source_ref: str | None = None,
        parse_notes: list[str] | None = None,
    ) -> ImportResult:
        obj = self._parse(bundle)
        canonical = canonicalize(obj)
        ses_uid = session_uid(canonical)
        digest = bundle_digest(canonical)
        if source_ref is None:
            src = obj.get("source") or {}
            source_ref = src.get("url")

        conn = schema_v2.connect(self.db_path)
        try:
            # A carried-forward database predates the screening objects.
            schema_v2.ensure_intake_screening(conn)
            self._require_matching_salt(conn)
            stages: list[_Stage] = []
            if parse_notes:
                # From the lane that built this bundle (an unknown term, a
                # credit choice the form cannot express). Persisted with the
                # session so the decision is auditable later, not just visible
                # in whoever ran the import's terminal.
                #
                # Built BEFORE the duplicate check: re-running an import is
                # what a maintainer does to re-read a submission, and a note
                # that disappears on the second run is a note they cannot go
                # back and find.
                stages.append(_Stage("parse", "warn", list(parse_notes)))

            existing = conn.execute(
                "SELECT status FROM review_sessions WHERE uid = ?", (ses_uid,)
            ).fetchone()
            # Only a TERMINAL session is a duplicate. A `returned` row is the
            # record of a rejection the maintainer may have since fixed (a
            # missing concept registered, a locale added) — re-submitting the
            # identical bundle must be able to complete, and the schema agrees:
            # accepted/rejected are terminal, `returned` is not.
            if existing and existing[0] in ("accepted", "rejected"):
                return ImportResult(
                    session_uid=ses_uid,
                    status="duplicate",
                    report={"stages": [s.as_dict() for s in stages]},
                    locale=obj.get("locale"),
                    source_ref=source_ref,
                    parse_notes=list(parse_notes or []),
                )
            resuming = existing is not None

            # ---- stage 1: schema + semantic floor -------------------------
            errors, locale_writable = self._stage_schema(conn, obj)
            stages.append(
                _Stage(
                    "schema",
                    "fail" if errors else "pass",
                    errors
                    or [
                        f"kit_version {obj.get('kit_version')!r} recorded; "
                        "kit compatibility not yet enforced (no kit builder — "
                        "stale kits will degrade gracefully when it lands)"
                    ],
                )
            )
            if errors:
                return self._returned(
                    conn,
                    obj,
                    ses_uid,
                    digest,
                    stages,
                    locale_writable,
                    source_ref,
                    resuming,
                )

            # ---- stage 2: conduct screen (escalate, never auto-reject) ----
            findings = self._stage_conduct(obj)
            stages.append(
                _Stage(
                    "conduct",
                    "warn" if findings else "pass",
                    findings or ["no PII or wordlist findings in free text"],
                )
            )

            # ---- stage 3: identity + attestations + withdrawal rule -------
            att_errors = self._attestation_errors(obj)
            if att_errors:
                stages.append(_Stage("identity", "fail", att_errors))
                return self._returned(
                    conn, obj, ses_uid, digest, stages, True, source_ref, resuming
                )

            cid = contributor_id(
                obj["contributor"]["source_key"], salt=self._effective_salt
            )
            withdrawn_at = self._withdrawn_at(conn, cid)
            replay = False
            identity_notes: list[str] = []
            if withdrawn_at:
                started = self._bundle_timestamp(obj)
                if started and started[:10] < withdrawn_at[:10]:
                    replay = True
                    identity_notes.append(
                        f"contributor withdrew on {withdrawn_at}; this bundle "
                        f"predates it ({started}) — a replay of old history. "
                        "Evidence written, no identity column populated "
                        "(withdrawal-runbook importer rule)."
                    )
                else:
                    stages.append(
                        _Stage(
                            "identity",
                            "fail",
                            [
                                f"contributor withdrew on {withdrawn_at} and this "
                                f"bundle postdates it (started_at="
                                f"{started or 'missing'}). Import HALTED: this may "
                                "be re-consent or a mistake — a human must decide; "
                                "re-consent is never decided in code."
                            ],
                        )
                    )
                    return ImportResult(
                        session_uid=ses_uid,
                        status="halted",
                        report=self._report(stages),
                        locale=obj["locale"],
                        source_ref=source_ref,
                    )

            consent = (
                (obj["contributor"].get("consent") or None) if not replay else None
            )
            if not replay and consent is None:
                identity_notes.append(
                    "no consent asserted with this submission: evidence ingests, "
                    "but NO identity is minted (decision 2026-08-11). Invite the "
                    "contributor to agree to CONTRIBUTOR_PRIVACY.md to be "
                    "creditable and reachable."
                )
            if consent is not None and self._consent_on_file(conn, cid):
                # Consent is written FORWARD only. A bundle can name any
                # source_key, so honouring a fresh consent block over a stored
                # one would let a stranger flip someone's credit_preference to
                # 'name' and set consent_public_credit = 1 - manufacturing the
                # record that later authorizes publishing that person's name.
                # It would also overwrite an `oss-pre-notice` row, which the
                # schema says grants nothing. Changing a credit preference is a
                # maintainer action (see the withdrawal runbook), never an
                # import side effect.
                consent = None
                identity_notes.append(
                    "consent already on file for this contributor: the stored "
                    "version and credit preference are left untouched. A change "
                    "of credit preference is a maintainer action, not something "
                    "a submission can assert."
                )
            stages.append(
                _Stage(
                    "identity",
                    "warn" if identity_notes else "pass",
                    identity_notes or ["contributor resolved; consent recorded"],
                )
            )

            # ---- stage 4: mechanical term gates ---------------------------
            plan = self._plan_rows(conn, obj)
            gate_details, gate_status = self._stage_gates(conn, obj, plan)
            stages.append(_Stage("gates", gate_status, gate_details))

            # ---- stage 5: quality signals (WARN only) ---------------------
            quality = self._stage_quality(conn, obj, plan)
            stages.append(
                _Stage(
                    "quality",
                    "warn" if quality else "pass",
                    quality
                    or [
                        "no warnings. Policy note: no stage compares this "
                        "submission against model output."
                    ],
                )
            )

            # ---- stage 6: idempotent append-only ingest -------------------
            result = self._stage_ingest(
                conn,
                obj,
                ses_uid,
                digest,
                cid,
                consent,
                replay,
                plan,
                stages,
                source_ref,
                resuming,
            )
            result.needs_human_eyes = bool(findings)
            result.withdrawn_replay = replay
            result.parse_notes = list(parse_notes or [])
            return result
        finally:
            conn.close()

    # -- parsing ------------------------------------------------------------

    @staticmethod
    def _parse(bundle: dict | bytes | str | Path) -> dict:
        if isinstance(bundle, dict):
            return bundle
        if isinstance(bundle, Path):
            parsed = json.loads(bundle.read_text(encoding="utf-8"))
        elif isinstance(bundle, bytes):
            parsed = json.loads(bundle.decode("utf-8"))
        else:
            parsed = json.loads(bundle)
        if not isinstance(parsed, dict):
            # A batch file (top-level array) or a bare scalar would otherwise
            # surface as an AttributeError traceback three frames deep.
            raise ValueError(
                f"a review bundle must be a JSON object, got "
                f"{type(parsed).__name__}. One bundle is one session; import "
                "a batch file one submission at a time."
            )
        return parsed

    # -- stage 1 ------------------------------------------------------------

    @staticmethod
    def _endorsed_surfaces(response: dict) -> list[str]:
        """Endorsed surface forms, blind suggestion included (it is visibly
        the reviewer's own, pre-endorsed), NFC-deduplicated, order kept."""
        surfaces: list[str] = []
        blind = response.get("blind")
        if blind:
            surfaces.append(blind["surface_form"])
        for endorsement in response.get("endorsements", []):
            surfaces.append(endorsement["surface_form"])
        seen: set[str] = set()
        out: list[str] = []
        for surface in surfaces:
            key = normalize_surface_form(surface)
            if key not in seen:
                seen.add(key)
                out.append(surface)
        return out

    def _stage_schema(
        self, conn: sqlite3.Connection, obj: dict
    ) -> tuple[list[str], bool]:
        """Validate the bundle; return (errors, may_write_a_session_row).

        The second value separates a MALFORMED bundle from a well-formed one
        that breaks a semantic rule. Only the latter earns a `review_sessions`
        row, because writing one also mints a `contributors` row — a
        permanently, publicly exported key — and nothing binds the bundle's
        `source_key` to whoever submitted it. A malformed bundle naming a
        fabricated username must leave no trace in the corpus.
        """
        structural_errors = [
            f"at $.{'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in _validator().iter_errors(obj)
        ]
        errors = list(structural_errors)
        locale = obj.get("locale")
        locale_known = bool(
            isinstance(locale, str)
            and conn.execute(
                "SELECT 1 FROM locales WHERE tag = ?", (locale,)
            ).fetchone()
        )
        if isinstance(locale, str) and not locale_known:
            errors.append(f"locale {locale!r} is not registered in this database")
        if errors:
            return errors, locale_known and not structural_errors

        pl = obj.get("programming_language")
        if (
            pl is not None
            and not conn.execute(
                "SELECT 1 FROM programming_languages WHERE code = ?", (pl,)
            ).fetchone()
        ):
            errors.append(f"programming_language {pl!r} is not registered")
        if obj["track"] == "style_profile" and pl is not None:
            errors.append(
                "a style_profile session is locale-wide: programming_language must be null"
            )

        locale_for_uid = obj.get("locale")
        seen_concepts: set[str] = set()
        for index, response in enumerate(obj.get("responses", [])):
            slug = response["concept"]
            if not conn.execute(
                "SELECT 1 FROM concepts WHERE slug = ?", (slug,)
            ).fetchone():
                errors.append(f"responses[{index}]: unknown concept {slug!r}")
                continue
            # One response per concept: two would collide on the ranking-slot
            # unique index mid-ingest, which is a bundle defect, not a crash.
            if slug in seen_concepts:
                errors.append(
                    f"responses[{index}]: concept {slug!r} is answered twice — "
                    "one response per concept per session"
                )
                continue
            seen_concepts.add(slug)
            endorsed = {
                normalize_surface_form(s) for s in self._endorsed_surfaces(response)
            }
            ranking = response.get("ranking", [])
            for surface in ranking:
                if normalize_surface_form(surface) not in endorsed:
                    errors.append(
                        f"responses[{index}] ({slug}): ranking contains "
                        f"{surface!r}, which was not endorsed — rank only words "
                        "you would teach (ranking ⊆ endorsements)"
                    )
            # A word may hold only one rank slot: a repeat is a client bug that
            # would otherwise surface as an IntegrityError traceback.
            normalized_ranking = [normalize_surface_form(s) for s in ranking]
            for surface in sorted(
                {s for s in normalized_ranking if normalized_ranking.count(s) > 1}
            ):
                errors.append(
                    f"responses[{index}] ({slug}): {surface!r} appears in the "
                    "ranking more than once — one rank slot per word"
                )
            ranked = set(normalized_ranking)
            for flag in response.get("flags", []):
                normalized_flag = normalize_surface_form(flag["surface_form"])
                if normalized_flag in ranked:
                    errors.append(
                        f"responses[{index}] ({slug}): {flag['surface_form']!r} is "
                        "both flagged and ranked — a flag and a rank contradict "
                        "each other"
                    )
                # A flag REPORTS a candidate the reviewer was shown. Minting the
                # word from a flag would create an option whose community
                # provenance names the REPORTER as its author -- recording the
                # person who reported a slur as the person who proposed it.
                if normalized_flag in endorsed:
                    continue
                flagged_uid = option_uid(
                    slug,
                    locale_for_uid,
                    normalized_flag,
                    obj.get("programming_language"),
                )
                if not conn.execute(
                    "SELECT 1 FROM options WHERE uid = ?", (flagged_uid,)
                ).fetchone():
                    errors.append(
                        f"responses[{index}] ({slug}): flagged word "
                        f"{flag['surface_form']!r} is not an option in this "
                        "corpus. A flag reports a candidate you were shown — "
                        "recording it from a flag would credit you as the "
                        "author of the word you are reporting. If the word "
                        "genuinely needs to exist before it can be flagged, "
                        "raise it with a maintainer."
                    )
            expansion = response.get("expansion")
            if expansion and normalize_surface_form(expansion["for"]) not in endorsed:
                errors.append(
                    f"responses[{index}] ({slug}): expansion attaches to "
                    f"{expansion['for']!r}, which was not endorsed"
                )
        return errors, locale_known

    # -- stage 2 ------------------------------------------------------------

    def _free_texts(self, obj: dict) -> list[tuple[str, str]]:
        texts: list[tuple[str, str]] = []
        consent = obj.get("contributor", {}).get("consent") or {}
        if consent.get("credit_text"):
            texts.append(("contributor.consent.credit_text", consent["credit_text"]))
        for index, response in enumerate(obj.get("responses", [])):
            base = f"responses[{index}]"
            blind = response.get("blind")
            if blind and blind.get("rationale"):
                texts.append((f"{base}.blind.rationale", blind["rationale"]))
            for j, endorsement in enumerate(response.get("endorsements", [])):
                if endorsement.get("comment"):
                    texts.append(
                        (f"{base}.endorsements[{j}].comment", endorsement["comment"])
                    )
            for j, flag in enumerate(response.get("flags", [])):
                if flag.get("comment"):
                    texts.append((f"{base}.flags[{j}].comment", flag["comment"]))
            expansion = response.get("expansion")
            if expansion and expansion.get("formation_note"):
                texts.append(
                    (f"{base}.expansion.formation_note", expansion["formation_note"])
                )
            for j, commentary in enumerate(response.get("commentary", [])):
                texts.append((f"{base}.commentary[{j}].body", commentary["body"]))
        for index, answer in enumerate(obj.get("style_answers", [])):
            if answer.get("rationale"):
                texts.append((f"style_answers[{index}].rationale", answer["rationale"]))
        return texts

    def _stage_conduct(self, obj: dict) -> list[str]:
        findings: list[str] = []
        for path, text in self._free_texts(obj):
            for match in _EMAIL_RE.findall(text):
                findings.append(
                    f"{path}: looks like an email address ({match}) — PII does "
                    "not belong in a public bundle; escalated for human review"
                )
            if any(ch in BIDI_EMBEDDINGS for ch in text):
                findings.append(
                    f"{path}: contains explicit bidi control characters — "
                    "escalated for human review (injection smell)"
                )
            folded = text.casefold()
            for word in self.conduct_wordlist:
                if word in folded:
                    findings.append(
                        f"{path}: wordlist hit ({word!r}) — escalated for human "
                        "review; a wordlist hit is a question, never a verdict"
                    )
        return findings

    # -- stage 3 ------------------------------------------------------------

    def _attestation_errors(self, obj: dict) -> list[str]:
        att = obj.get("attestations", {})
        errors = [
            f"attestation {name!r} must be affirmed"
            for name in self.required_attestations
            if att.get(name) is not True
        ]
        consent = obj.get("contributor", {}).get("consent")
        if (
            consent
            and consent.get("credit_preference") == "name"
            and not consent.get("credit_text")
        ):
            errors.append("credit_preference 'name' requires credit_text")
        return errors

    @staticmethod
    def _consent_on_file(conn: sqlite3.Connection, cid: str) -> bool:
        """Whether this contributor already has consent recorded."""
        row = conn.execute(
            "SELECT consent_at, consent_version FROM contributor_identities"
            " WHERE contributor_id = ?",
            (cid,),
        ).fetchone()
        return bool(row and (row[0] is not None or row[1] is not None))

    @staticmethod
    def _withdrawn_at(conn: sqlite3.Connection, cid: str) -> str | None:
        row = conn.execute(
            "SELECT withdrawn_at FROM contributor_identities WHERE contributor_id = ?",
            (cid,),
        ).fetchone()
        return row[0] if row else None

    @staticmethod
    def _bundle_timestamp(obj: dict) -> str | None:
        started = (obj.get("session") or {}).get("started_at")
        if started:
            return started
        return (obj.get("source") or {}).get("created_at")

    # -- stage 4 ------------------------------------------------------------

    def _plan_rows(self, conn: sqlite3.Connection, obj: dict) -> dict[str, Any]:
        """Resolve every surface the bundle touches into planned option rows."""
        locale = obj["locale"]
        pl = obj.get("programming_language")
        plan: dict[str, Any] = {"options": {}, "responses": []}
        for response in obj.get("responses", []):
            slug = response["concept"]
            concept_id = conn.execute(
                "SELECT id FROM concepts WHERE slug = ?", (slug,)
            ).fetchone()[0]
            term_row = conn.execute(
                "SELECT name FROM terms WHERE concept_id = ? ORDER BY "
                "CASE WHEN programming_language = ? THEN 0 "
                "WHEN programming_language = 'python' THEN 1 ELSE 2 END, id LIMIT 1",
                (concept_id, pl or ""),
            ).fetchone()
            term_name = term_row[0] if term_row else ""

            surfaces: dict[str, dict[str, Any]] = {}

            def add(surface: str, elicited: str, sdict: dict = surfaces) -> str:
                normalized = normalize_surface_form(surface)
                uid = option_uid(slug, locale, normalized, pl)
                if uid not in sdict:
                    existing = conn.execute(
                        "SELECT 1 FROM options WHERE uid = ?", (uid,)
                    ).fetchone()
                    sdict[uid] = {
                        "surface": normalized,
                        "elicited": elicited,
                        "new": existing is None,
                    }
                return uid

            blind = response.get("blind")
            blind_uid = add(blind["surface_form"], "blind") if blind else None
            endorsed_uids: list[str] = []
            if blind_uid:
                endorsed_uids.append(blind_uid)
            annotations: list[tuple[str, str]] = []
            if blind:
                for kind in blind.get("self_annotations", []):
                    annotations.append((blind_uid, kind))
            comments: dict[str, str] = {}
            for endorsement in response.get("endorsements", []):
                uid = add(endorsement["surface_form"], self.elicited_default)
                if uid not in endorsed_uids:
                    endorsed_uids.append(uid)
                for kind in endorsement.get("annotations", []):
                    annotations.append((uid, kind))
                if endorsement.get("comment"):
                    comments[uid] = endorsement["comment"]
            flag_rows = [
                (
                    add(flag["surface_form"], self.elicited_default),
                    flag["reason"],
                    flag.get("comment"),
                )
                for flag in response.get("flags", [])
            ]
            ranking_uids = [
                option_uid(slug, locale, normalize_surface_form(s), pl)
                for s in response.get("ranking", [])
            ]
            expansion = response.get("expansion")
            plan["responses"].append(
                {
                    "slug": slug,
                    "concept_id": concept_id,
                    "term_name": term_name,
                    "surfaces": surfaces,
                    "blind": blind,
                    "blind_uid": blind_uid,
                    "endorsed_uids": endorsed_uids,
                    "annotations": annotations,
                    "comments": comments,
                    "flags": flag_rows,
                    "ranking_uids": ranking_uids,
                    "expansion": (
                        {
                            "option_uid": option_uid(
                                slug,
                                locale,
                                normalize_surface_form(expansion["for"]),
                                pl,
                            ),
                            "text": expansion["text"],
                            "formation_note": expansion.get("formation_note"),
                        }
                        if expansion
                        else None
                    ),
                    "commentary": response.get("commentary", []),
                }
            )
            plan["options"].update(
                {
                    uid: {**info, "concept_id": concept_id, "term_name": term_name}
                    for uid, info in surfaces.items()
                }
            )
        return plan

    def _stage_gates(
        self, conn: sqlite3.Connection, obj: dict, plan: dict[str, Any]
    ) -> tuple[list[str], str]:
        locale = obj["locale"]
        subtag = conn.execute(
            "SELECT language_subtag FROM locales WHERE tag = ?", (locale,)
        ).fetchone()[0]
        allowed = allowed_scripts_for(subtag)
        details: list[str] = []
        status = "pass"
        # One scan of the locale, folded, instead of one per new surface: the
        # query is O(options in locale) and the loop ran it per candidate.
        existing_by_fold: dict[str, list[tuple[str, int]]] = {}
        for other_slug, other_surface, other_concept in conn.execute(
            "SELECT c.slug, o.surface_form, o.concept_id FROM options o"
            " JOIN concepts c ON c.id = o.concept_id"
            " WHERE o.locale = ? AND o.withdrawn_at IS NULL",
            (locale,),
        ):
            key = unicodedata.normalize("NFKC", other_surface).casefold()
            existing_by_fold.setdefault(key, []).append((other_slug, other_concept))
        for uid, info in plan["options"].items():
            if not info["new"]:
                continue
            verdict = validate_surface(info["surface"], info["term_name"], allowed)
            min_ok = not any(
                ch in SchemaValidator._XID_ONLY_FROM_CPYTHON_313
                for ch in info["surface"]
            )
            info["validation"] = verdict
            info["min_interpreter_ok"] = min_ok
            problems = []
            if not verdict.identifier_valid:
                problems.append("not a valid identifier")
            if not verdict.nfkc_stable and verdict.nfkc_delta_class == "other":
                problems.append("NFKC-unstable")
            if not verdict.script_consistent:
                problems.append("script-inconsistent for this locale")
            if verdict.collides_en_keyword:
                problems.append("collides with an English keyword")
            if not min_ok:
                details.append(
                    f"{info['surface']!r}: uses ZWJ/ZWNJ — identifier-valid only "
                    "on CPython 3.13+ (version-tiered, not invalid)"
                )
            if problems:
                status = "warn"
                details.append(
                    f"{info['surface']!r} ({uid}): {', '.join(problems)} — the row "
                    "still ingests as evidence, canon-INELIGIBLE (CORE-1400 "
                    "reframe); the session is never dropped"
                )
            fold = unicodedata.normalize("NFKC", info["surface"]).casefold()
            for other_slug, other_concept in existing_by_fold.get(fold, ()):
                if other_concept == info["concept_id"]:
                    continue
                status = "warn"
                details.append(
                    f"{info['surface']!r}: same word already renders concept "
                    f"{other_slug!r} in this locale — both recorded; the "
                    "collision surfaces at selection time"
                )
        return details or ["all new surfaces pass the mechanical gates"], status

    # -- stage 5 ------------------------------------------------------------

    def _stage_quality(
        self, conn: sqlite3.Connection, obj: dict, plan: dict[str, Any]
    ) -> list[str]:
        warnings: list[str] = []
        locale = obj["locale"]
        for response in plan["responses"]:
            blind = response["blind"]
            if blind and blind.get("established_term") == "coined":
                siblings = conn.execute(
                    "SELECT COUNT(*) FROM options WHERE concept_id = ? AND locale = ?",
                    (response["concept_id"], locale),
                ).fetchone()[0]
                if siblings == 0:
                    warnings.append(
                        f"{response['slug']}: novel coinage with no established-"
                        "term sibling — routed to the second-reviewer queue with "
                        "priority (more human eyes, not machine judgment)"
                    )
            for uid, info in response["surfaces"].items():
                annotated = {kind for u, kind in response["annotations"] if u == uid}
                if is_identity_translation(
                    response["term_name"], info["surface"]
                ) and not annotated & {"transliteration", "cognate_loanword"}:
                    warnings.append(
                        f"{info['surface']!r} equals the English term — if this is "
                        "a deliberate cognate/loanword, the cognate_loanword "
                        "annotation would record that (suggestion, not a mandate)"
                    )
        return warnings

    # -- returned + report helpers ------------------------------------------

    @staticmethod
    def _report(stages: list[_Stage]) -> dict[str, Any]:
        return {
            "pipeline_version": "intake-v1",
            "stages": [s.as_dict() for s in stages],
        }

    def _returned(
        self,
        conn: sqlite3.Connection,
        obj: dict,
        ses_uid: str,
        digest: str,
        stages: list[_Stage],
        writable: bool,
        source_ref: str | None,
        resuming: bool = False,
    ) -> ImportResult:
        report = self._report(stages)
        track = obj.get("track")
        if writable and track in ("reserved_words", "messages", "style_profile"):
            try:
                if resuming:
                    # The row already exists from an earlier return. Its evidence
                    # columns are frozen (and identical — same bytes), so only the
                    # report moves. `returned` is not terminal, so this is allowed.
                    conn.execute(
                        "UPDATE review_sessions SET status = 'returned',"
                        " verification_report = ? WHERE uid = ?",
                        (json.dumps(report, ensure_ascii=False), ses_uid),
                    )
                    conn.commit()
                    return ImportResult(
                        session_uid=ses_uid,
                        status="returned",
                        report=report,
                        locale=obj.get("locale"),
                        source_ref=source_ref,
                    )
                cid = contributor_id(
                    obj["contributor"]["source_key"], salt=self._effective_salt
                )
                rung = self._upsert_contributor(conn, cid, obj)
                conn.execute(
                    "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
                    " programming_language, method, kit_version, app_version,"
                    " rung_at_session, bundle_digest, contact_captured, started_at,"
                    " status, verification_report, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'returned', ?, ?)",
                    (
                        ses_uid,
                        cid,
                        obj["locale"],
                        track,
                        obj.get("programming_language")
                        if track != "style_profile"
                        else None,
                        self.method,
                        str(obj.get("kit_version") or "unknown"),
                        (obj.get("session") or {}).get("app_version"),
                        rung,
                        digest,
                        1 if obj.get("contributor", {}).get("contact_captured") else 0,
                        self._bundle_timestamp(obj),
                        json.dumps(report, ensure_ascii=False),
                        source_ref,
                    ),
                )
                conn.commit()
            except (sqlite3.Error, KeyError, ValueError):
                conn.rollback()  # report-only: an unwritable return is still actionable
        return ImportResult(
            session_uid=ses_uid,
            status="returned",
            report=report,
            locale=obj.get("locale"),
            source_ref=source_ref,
        )

    # -- stage 6 ------------------------------------------------------------

    def _upsert_contributor(self, conn: sqlite3.Connection, cid: str, obj: dict) -> str:
        claimed = obj.get("contributor", {}).get("claimed_rung") or "contributor"
        # The rung is set ONCE, when the contributor first appears. It is never
        # moved by a later bundle: nothing binds `source_key` to whoever
        # submitted the file, so a bundle naming an existing person could
        # otherwise promote them to `native_claimed` — doubling the weight of
        # every endorsement they have (review_rungs: 2.0 vs 1.0) and changing a
        # column the public corpus exports. Rung changes are a maintainer act;
        # the claim itself survives as session evidence in `rung_at_session`.
        conn.execute(
            "INSERT OR IGNORE INTO contributors(id, current_rung) VALUES (?, ?)",
            (cid, claimed),
        )
        return conn.execute(
            "SELECT current_rung FROM contributors WHERE id = ?", (cid,)
        ).fetchone()[0]

    def _record_consent(
        self, conn: sqlite3.Connection, cid: str, obj: dict, consent: dict, now: str
    ) -> None:
        source_key = obj["contributor"]["source_key"]
        preference = consent["credit_preference"]
        display_name = consent.get("credit_text") if preference == "name" else None
        github_handle = source_key if preference == "handle" else None
        conn.execute(
            """
            INSERT INTO contributor_identities(
                contributor_id, source_key, display_name, github_handle,
                consent_public_credit, consent_version, consent_at,
                credit_preference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(contributor_id) DO UPDATE SET
                source_key = excluded.source_key,
                -- A downgrade to 'anonymous' must also drop what it stopped
                -- authorizing: keeping display_name/github_handle would leave
                -- publishable credit attached to a preference that forbids it.
                display_name = CASE WHEN excluded.credit_preference = 'anonymous'
                                    THEN NULL
                                    ELSE COALESCE(excluded.display_name, display_name) END,
                github_handle = CASE WHEN excluded.credit_preference = 'anonymous'
                                     THEN NULL
                                     ELSE COALESCE(excluded.github_handle, github_handle) END,
                consent_public_credit = excluded.consent_public_credit,
                consent_version = excluded.consent_version,
                consent_at = excluded.consent_at,
                credit_preference = excluded.credit_preference
            """,
            (
                cid,
                source_key,
                display_name,
                github_handle,
                0 if preference == "anonymous" else 1,
                consent["consent_version"],
                now,
                preference,
            ),
        )

    def _stage_ingest(
        self,
        conn: sqlite3.Connection,
        obj: dict,
        ses_uid: str,
        digest: str,
        cid: str,
        consent: dict | None,
        replay: bool,
        plan: dict[str, Any],
        stages: list[_Stage],
        source_ref: str | None,
        resuming: bool = False,
    ) -> ImportResult:
        now = _now_iso()
        locale = obj["locale"]
        pl = obj.get("programming_language")
        created: list[str] = []
        endorsements_linked = 0
        try:
            rung = self._upsert_contributor(conn, cid, obj)
            if consent is not None:
                self._record_consent(conn, cid, obj, consent, now)

            if resuming:
                # A previously RETURNED session whose cause the maintainer has
                # since fixed. Evidence columns are frozen by trigger and are
                # identical anyway (same bytes, same uid); only the workflow
                # column moves, which `returned` (non-terminal) permits.
                conn.execute(
                    "UPDATE review_sessions SET status = 'verifying' WHERE uid = ?",
                    (ses_uid,),
                )
            else:
                conn.execute(
                    "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
                    " programming_language, method, kit_version, app_version,"
                    " rung_at_session, bundle_digest, contact_captured, started_at,"
                    " status, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'verifying', ?)",
                    (
                        ses_uid,
                        cid,
                        locale,
                        obj["track"],
                        pl,
                        self.method,
                        obj["kit_version"],
                        (obj.get("session") or {}).get("app_version"),
                        rung,
                        digest,
                        1 if obj.get("contributor", {}).get("contact_captured") else 0,
                        self._bundle_timestamp(obj),
                        source_ref,
                    ),
                )

            # Options first (everything else references them).
            for uid, info in plan["options"].items():
                if not info["new"]:
                    continue
                conn.execute(
                    "INSERT INTO options(uid, concept_id, locale,"
                    " programming_language, surface_form) VALUES (?, ?, ?, ?, ?)",
                    (uid, info["concept_id"], locale, pl, info["surface"]),
                )
                created.append(uid)
                verdict = info["validation"]
                conn.execute(
                    "INSERT INTO option_validations(option_uid, validator_version,"
                    " identifier_valid, nfkc_stable, nfkc_delta_class,"
                    " script_consistent, collides_en_keyword, min_interpreter_ok)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        uid,
                        VALIDATOR_VERSION,
                        int(verdict.identifier_valid),
                        int(verdict.nfkc_stable),
                        verdict.nfkc_delta_class,
                        int(verdict.script_consistent),
                        int(verdict.collides_en_keyword),
                        int(info["min_interpreter_ok"]),
                    ),
                )
                conn.execute(
                    "INSERT INTO option_provenance(option_uid, source,"
                    " contributor_id, word_form, rationale) VALUES"
                    " (?, 'community', ?, ?, ?)",
                    (
                        uid,
                        cid,
                        self._blind_field(plan, uid, "word_form"),
                        self._blind_field(plan, uid, "rationale"),
                    ),
                )
                # Quarantine-by-default (CORE-1828): every community-created
                # option is invisible to rankings and export until cleared.
                conn.execute(
                    "INSERT INTO option_screenings(option_uid, verdict,"
                    " screened_by, screen_version, note) VALUES"
                    " (?, 'quarantined', ?, ?, ?)",
                    (
                        uid,
                        self.screened_by,
                        SCREEN_VERSION,
                        f"community submission via session {ses_uid}",
                    ),
                )

            # Every option the reviewer TOUCHED gets its session junction —
            # including words the corpus already held. session_options.elicited
            # is the sole record of blind-vs-after_reveal ordering, and endorsing
            # an established word is the common case, so restricting this to
            # newly-minted options destroyed the signal exactly where it mattered
            # most. Runs after the options above exist (FK), and the
            # (session_uid, option_uid) PK keeps it idempotent.
            for uid, info in plan["options"].items():
                conn.execute(
                    "INSERT OR IGNORE INTO session_options(session_uid, option_uid,"
                    " elicited) VALUES (?, ?, ?)",
                    (ses_uid, uid, info["elicited"]),
                )

            for response in plan["responses"]:
                # Endorsements (blind suggestion is pre-endorsed).
                for uid in response["endorsed_uids"]:
                    live = conn.execute(
                        "SELECT uid FROM endorsements WHERE option_uid = ? AND"
                        " contributor_id = ? AND retracted_at IS NULL",
                        (uid, cid),
                    ).fetchone()
                    if live:
                        end_uid = live[0]
                    else:
                        end_uid = endorsement_uid(uid, cid, self.method, now)
                        conn.execute(
                            "INSERT INTO endorsements(uid, option_uid,"
                            " contributor_id, method, rung_at_endorsement,"
                            " comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                end_uid,
                                uid,
                                cid,
                                self.method,
                                rung,
                                response["comments"].get(uid),
                                now,
                            ),
                        )
                    conn.execute(
                        "INSERT OR IGNORE INTO session_endorsements(session_uid,"
                        " endorsement_uid) VALUES (?, ?)",
                        (ses_uid, end_uid),
                    )
                    endorsements_linked += 1

                for rank, uid in enumerate(response["ranking_uids"], start=1):
                    conn.execute(
                        "INSERT INTO session_rankings(session_uid, concept_id,"
                        " locale, programming_language, option_uid, rank)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (ses_uid, response["concept_id"], locale, pl, uid, rank),
                    )

                for uid, kind in response["annotations"]:
                    live = conn.execute(
                        "SELECT 1 FROM option_annotations WHERE option_uid = ? AND"
                        " contributor_id = ? AND kind = ? AND retracted_at IS NULL",
                        (uid, cid, kind),
                    ).fetchone()
                    if not live:
                        conn.execute(
                            "INSERT INTO option_annotations(uid, option_uid,"
                            " contributor_id, session_uid, kind)"
                            " VALUES (?, ?, ?, ?, ?)",
                            (
                                annotation_uid(ses_uid, uid, cid, kind),
                                uid,
                                cid,
                                ses_uid,
                                kind,
                            ),
                        )

                expansion = response["expansion"]
                if expansion:
                    conn.execute(
                        "INSERT INTO option_expansions(uid, option_uid,"
                        " contributor_id, session_uid, expansion, formation_note)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            expansion_uid(
                                ses_uid, expansion["option_uid"], cid, expansion["text"]
                            ),
                            expansion["option_uid"],
                            cid,
                            ses_uid,
                            normalize_surface_form(expansion["text"]),
                            expansion["formation_note"],
                        ),
                    )

                for commentary in response["commentary"]:
                    com_uid = commentary_uid(
                        ses_uid,
                        cid,
                        response["slug"],
                        locale,
                        commentary["topic"],
                        commentary["body"],
                    )
                    conn.execute(
                        "INSERT INTO concept_commentary(uid, contributor_id,"
                        " session_uid, concept_id, locale, topic, body)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            com_uid,
                            cid,
                            ses_uid,
                            response["concept_id"],
                            locale,
                            commentary["topic"],
                            commentary["body"],
                        ),
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO commentary_moderation(commentary_uid)"
                        " VALUES (?)",
                        (com_uid,),
                    )

                for uid, reason, comment in response["flags"]:
                    conn.execute(
                        "INSERT INTO option_flags(option_uid, contributor_id,"
                        " reason, note) VALUES (?, ?, ?, ?)",
                        (uid, cid, reason, comment),
                    )

            for answer in obj.get("style_answers", []):
                live = conn.execute(
                    "SELECT uid, value FROM style_ratifications WHERE locale = ?"
                    " AND field = ? AND contributor_id = ? AND retracted_at IS NULL",
                    (locale, answer["field"], cid),
                ).fetchone()
                if live and live[1] == answer["value"]:
                    continue  # same live answer: nothing to change
                if live:
                    conn.execute(
                        "UPDATE style_ratifications SET retracted_at = ? WHERE uid = ?",
                        (now, live[0]),
                    )
                conn.execute(
                    "INSERT INTO style_ratifications(uid, contributor_id,"
                    " session_uid, locale, field, value, rationale)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        style_uid(ses_uid, cid, locale, answer["field"]),
                        cid,
                        ses_uid,
                        locale,
                        answer["field"],
                        answer["value"],
                        answer.get("rationale"),
                    ),
                )

            stages.append(
                _Stage(
                    "ingest",
                    "pass",
                    [
                        f"options created: {len(created)} (all quarantined pending "
                        f"the import ritual)"
                        if created
                        else "options created: 0",
                        f"endorsements linked to session: {endorsements_linked}",
                    ],
                )
            )
            report = self._report(stages)
            conn.execute(
                "UPDATE review_sessions SET status = 'accepted',"
                " verification_report = ? WHERE uid = ?",
                (json.dumps(report, ensure_ascii=False), ses_uid),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return ImportResult(
            session_uid=ses_uid,
            status="accepted",
            report=report,
            locale=locale,
            created_options=created,
            endorsements_linked=endorsements_linked,
            source_ref=source_ref,
        )

    @staticmethod
    def _blind_field(plan: dict[str, Any], uid: str, key: str) -> str | None:
        for response in plan["responses"]:
            if response["blind_uid"] == uid and response["blind"]:
                return response["blind"].get(key)
        return None
