"""The automated submission moderation gate (CORE-1797).

No community rendering goes live unscreened. This module is the automated
half of the screening regime CORE-1828 shipped manually: the importer already
quarantines every community-minted option and records verdicts in
``option_screenings``; this gate adds the checks that run *before* that
verdict is written, and decides — per option — which verdict it is.

The gate writes the SAME verdict vocabulary the interim ritual writes
(``quarantined`` / ``cleared`` / ``held`` / ``rejected``, latest row wins,
``option_withheld`` is the one predicate), so every consumer CORE-1828
repaired — ``option_standings``, ``terminology_export``, the canon guard, the
corpus export — needs no change at all. What changes is who writes the first
verdict and what it is allowed to be:

* **findings → held.** Any safety finding (bidi/invisible-character
  injection, a confusable-skeleton match, a wordlist hit, a spam heuristic,
  a rate-limit breach, a linguist-review concern) escalates to a human. The
  gate never writes ``rejected``: rejection is a decision a person owns,
  exactly as the conduct stage has always insisted.
* **clean + trusted rung → cleared.** A contributor whose STORED rung (the
  maintainer-curated ``contributors.current_rung``, never the bundle's
  self-claim) meets :attr:`ModerationConfig.fast_path_min_rank` fast-paths a
  clean, mechanically-valid option straight to ``cleared``. Fast-path is a
  shortcut through the queue, never around the screen — every check above
  ran first.
* **clean + everyone else → quarantined.** Exactly the CORE-1828 default;
  the import ritual remains the clearing path.

Three sub-decisions are open on the ticket (Madison confirms separately).
Each is a :class:`ModerationConfig` flag with the conservative default, so
flipping one is configuration, not a rebuild:

* ``quarantine_visibility`` — ``hidden`` (quarantined options are visible to
  no one but maintainers) vs ``submitter_only`` (greyed, to their submitter).
  :func:`quarantined_uids_visible_to` is the query the reviewer surface
  (CORE-1616) must use.
* ``export_verdicts`` — ``False`` (verdicts stay private; the filter is not
  advertised to adversaries) vs ``True`` (a sanitized verdict trail exports
  for transparency). Consumed by ``scripts/export_corpus.py``.
* ``escalation_policy`` — ``maintainer_and_certified`` (flagged cases go to
  Madison plus trusted rung-4s) vs ``maintainer_only``.
  :func:`escalation_recipients` resolves it against the ladder.

Wordlists are per-locale files in a PRIVATE directory
(``$LEGESHER_WORDLIST_DIR``, decision 2026-08-12: never in the monorepo), and
matching is word-boundary aware — the corpus is full of English keywords, and
a substring match on a mild term flags ``class``, ``pass`` and ``assert``.
A wordlist hit is a question for a human, never a verdict: it escalates.

The model screen is framed as linguist review (:class:`LinguistReview`): a
hook with a typed opinion, not a judge. The default implementation is
offline (:class:`OfflineLinguistReview`) and returns ``unavailable``, which
blocks nothing — quarantine-by-default is already the safety net, and a
missing model must not silently become a wall.
"""

from __future__ import annotations

import keyword
import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from legesher_i18n.script_policy import (
    BIDI_CONTROLS,
    FORBIDDEN_FORMAT_CHARS,
    has_policy,
    is_default_ignorable,
    policy_for,
)

__all__ = [
    "AUTO_SCREEN_VERSION",
    "AUTO_SCREENED_BY",
    "GateOutcome",
    "LinguistOpinion",
    "LinguistReview",
    "ModerationConfig",
    "ModerationGate",
    "OfflineLinguistReview",
    "OptionScreenPlan",
    "escalation_recipients",
    "quarantined_uids_visible_to",
    "skeleton",
]

#: ``option_screenings.screen_version`` for verdicts this gate writes. The
#: interim ritual keeps writing ``manual-interim-v1`` for the HUMAN act of
#: clearing; the two regimes stay distinguishable in the audit trail forever.
AUTO_SCREEN_VERSION = "auto-gate-v1"

#: ``option_screenings.screened_by`` for verdicts this gate writes. A fixed
#: name, not a person: attributing an automated verdict to whoever ran the
#: import would claim a judgment they never made.
AUTO_SCREENED_BY = "auto-gate"


# ---------------------------------------------------------------------------
# Configuration — the three open sub-decisions, as flags
# ---------------------------------------------------------------------------


def _env_int(environ: dict[str, str], key: str, default: int) -> int:
    raw = environ.get(key)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{key} must be an integer, got {raw!r}")


@dataclass(frozen=True)
class ModerationConfig:
    """The gate's policy knobs. Defaults are the conservative reading.

    The first three fields are the CORE-1797 open sub-decisions; the rest are
    operational thresholds. Every field is overridable via environment
    (:meth:`from_env`) so a policy change is a config change, not a rebuild.
    """

    #: ``hidden`` — a quarantined option is visible to no one but the
    #: maintainer lens. ``submitter_only`` — additionally visible (greyed) to
    #: the contributor who submitted it. Conservative default: fully hidden.
    quarantine_visibility: str = "hidden"

    #: Whether a sanitized screening-verdict trail exports with the corpus.
    #: Conservative default: private — a published filter is one an adversary
    #: reads around.
    export_verdicts: bool = False

    #: Who clears escalated (``held``) cases: ``maintainer_and_certified``
    #: (Madison + trusted rung-4s) or ``maintainer_only``.
    escalation_policy: str = "maintainer_and_certified"

    #: Minimum ``review_rungs.rank`` of the STORED rung for the cleared
    #: fast path. Default 4 (``certified``): the same trust bar as the
    #: escalation crew. The self-claimed bundle rung never counts — the wire
    #: schema caps claims at ``native_claimed`` and the gate reads only what
    #: a maintainer stored.
    fast_path_min_rank: int = 4

    #: Per-contributor rate limit: more than this many review sessions inside
    #: :attr:`rate_window_hours` escalates everything the next session mints.
    max_sessions_per_window: int = 5
    rate_window_hours: int = 24

    #: Spam heuristics: a plausible identifier is short, and no natural word
    #: repeats one character five times.
    max_surface_length: int = 40
    max_char_run: int = 4

    #: Directory of per-locale wordlists (``<language-subtag>.txt``, one term
    #: per line, ``#`` comments). PRIVATE data home material — never the
    #: monorepo. ``None`` disables the wordlist screen (the model screen and
    #: quarantine-by-default remain).
    wordlist_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.quarantine_visibility not in ("hidden", "submitter_only"):
            raise ValueError(
                "quarantine_visibility must be 'hidden' or 'submitter_only', "
                f"got {self.quarantine_visibility!r}"
            )
        if self.escalation_policy not in (
            "maintainer_and_certified",
            "maintainer_only",
        ):
            raise ValueError(
                "escalation_policy must be 'maintainer_and_certified' or "
                f"'maintainer_only', got {self.escalation_policy!r}"
            )

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> ModerationConfig:
        """Build the effective config from ``LEGESHER_MODERATION_*`` variables.

        Args:
            environ: Override for testing; defaults to ``os.environ``.

        Returns:
            The config, with every unset variable at its conservative default.

        Raises:
            ValueError: if a variable holds a value outside its vocabulary.
        """
        env = dict(os.environ if environ is None else environ)
        wordlist_dir = env.get("LEGESHER_WORDLIST_DIR")
        return cls(
            quarantine_visibility=env.get(
                "LEGESHER_MODERATION_QUARANTINE_VISIBILITY", "hidden"
            ),
            export_verdicts=env.get("LEGESHER_MODERATION_EXPORT_VERDICTS", "")
            .strip()
            .lower()
            in ("1", "true", "yes"),
            escalation_policy=env.get(
                "LEGESHER_MODERATION_ESCALATION", "maintainer_and_certified"
            ),
            fast_path_min_rank=_env_int(
                env, "LEGESHER_MODERATION_FAST_PATH_MIN_RANK", 4
            ),
            max_sessions_per_window=_env_int(
                env, "LEGESHER_MODERATION_MAX_SESSIONS_PER_WINDOW", 5
            ),
            rate_window_hours=_env_int(
                env, "LEGESHER_MODERATION_RATE_WINDOW_HOURS", 24
            ),
            max_surface_length=_env_int(
                env, "LEGESHER_MODERATION_MAX_SURFACE_LENGTH", 40
            ),
            max_char_run=_env_int(env, "LEGESHER_MODERATION_MAX_CHAR_RUN", 4),
            wordlist_dir=Path(wordlist_dir) if wordlist_dir else None,
        )


# ---------------------------------------------------------------------------
# The linguist-review hook (the model screen, framed honestly)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LinguistOpinion:
    """One reviewer-shaped opinion about one surface form.

    ``opinion`` vocabulary:

    * ``no_concern`` — nothing to raise; contributes no finding.
    * ``concern`` — the reviewer would not teach this word without a human
      looking first; escalates (``held``), never rejects.
    * ``unavailable`` — the screen did not run (offline, no model, no
      coverage for this locale). Recorded as a note; blocks nothing.
    """

    opinion: str
    note: str | None = None

    def __post_init__(self) -> None:
        if self.opinion not in ("no_concern", "concern", "unavailable"):
            raise ValueError(f"unknown linguist opinion {self.opinion!r}")


class LinguistReview(Protocol):
    """The model screen, framed as what it is: one linguist's read, escalating
    to humans — zero weight toward any native gate (CORE-1802 posture)."""

    def review(self, surface: str, locale: str, concept_slug: str) -> LinguistOpinion:
        """Return an opinion on one candidate rendering."""
        ...


class OfflineLinguistReview:
    """The default hook: no model configured, and honest about it.

    Returns ``unavailable`` for everything. Deliberately NOT a finding:
    quarantine-by-default already guarantees a human screen for untrusted
    submitters, and a missing model must not turn the whole intake path into
    a wall. When a real model screen lands it implements the same protocol
    and is passed to :class:`ModerationGate` — no pipeline change.
    """

    def review(self, surface: str, locale: str, concept_slug: str) -> LinguistOpinion:
        return LinguistOpinion(
            "unavailable",
            "linguist model screen not configured; wordlist + quarantine "
            "remain the screen",
        )


# ---------------------------------------------------------------------------
# Confusable skeleton (homoglyph detection, stdlib-only)
# ---------------------------------------------------------------------------

#: Single-character homoglyphs of Latin letters, from scripts whose lowercase
#: glyphs are visually identical (or near-identical) in code-editor fonts.
#: A deliberately SMALL, reviewable table of the classic attack alphabet —
#: not a vendored UTS #39 confusables.txt. Over-matching is safe here: a
#: skeleton match is a finding, a finding escalates to a human, and the
#: fail-safe direction for a moderation gate is a question, not a pass.
_CONFUSABLE_TO_LATIN: dict[str, str] = {
    # Cyrillic
    "а": "a",  # а
    "е": "e",  # е
    "к": "k",  # к (U+043A — PR #161 review finding: UTS-39 confusable)
    "о": "o",  # о
    "р": "p",  # р
    "с": "c",  # с
    "у": "y",  # у
    "х": "x",  # х
    "ѕ": "s",  # ѕ
    "і": "i",  # і
    "ј": "j",  # ј
    "һ": "h",  # һ
    "ӏ": "l",  # ӏ palochka (U+04CF; U+04C0 casefolds here — PR #161 review finding)
    "ԁ": "d",  # ԁ
    "ԛ": "q",  # ԛ
    "ԝ": "w",  # ԝ
    "ѵ": "v",  # ѵ
    # Greek
    "ο": "o",  # ο
    "ρ": "p",  # ρ
    "ν": "v",  # ν
    "ι": "i",  # ι
    "υ": "u",  # υ
    "κ": "k",  # κ
    # Latin lookalikes NFKC does not fold
    "ɑ": "a",  # ɑ
    "ı": "i",  # ı (dotless i)
    "ℓ": "l",  # ℓ
}

#: English keywords a skeleton may spoof: hard keywords plus soft keywords
#: (``match``, ``case``, ``type``, ``_``) — the same surface a shadowed
#: keyword would confuse.
_EN_KEYWORDS: frozenset[str] = frozenset(keyword.kwlist) | frozenset(
    getattr(keyword, "softkwlist", ())
)


def skeleton(text: str) -> str:
    """The confusable skeleton of *text*: what it LOOKS like, canonicalized.

    NFKC folds compatibility clones (fullwidth forms, ligatures), casefold
    removes case, invisible characters are dropped (they render as nothing,
    which is the point of using them), and single-character homoglyphs map to
    their Latin twin. Two strings with one skeleton are indistinguishable to
    a reader even though Python treats them as different identifiers.

    Args:
        text: Any surface form.

    Returns:
        The skeleton string.
    """
    folded = unicodedata.normalize("NFKC", text).casefold()
    visible = "".join(
        ch
        for ch in folded
        if not is_default_ignorable(ch) and ch not in FORBIDDEN_FORMAT_CHARS
    )
    return "".join(_CONFUSABLE_TO_LATIN.get(ch, ch) for ch in visible)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OptionScreenPlan:
    """One NEW option as the pipeline hands it to the gate."""

    uid: str
    surface: str
    concept_slug: str
    #: Every mechanical gate passed (identifier, NFKC, script, EN-keyword,
    #: interpreter floor). Required for the cleared fast path; a mechanical
    #: failure still ingests as evidence (CORE-1400) but never fast-paths.
    mechanical_clean: bool


@dataclass(frozen=True)
class GateOutcome:
    """What the safety stage decided, ledger-ready."""

    #: Per option: the verdict (``cleared`` / ``quarantined`` / ``held``) and
    #: the audit note that lands on the ``option_screenings`` row.
    verdicts: dict[str, tuple[str, str]] = field(default_factory=dict)
    #: Stage-report lines (the ``safety`` stage's details).
    details: list[str] = field(default_factory=list)
    #: Whether anything escalated (drives ``needs_human_eyes``).
    escalated: bool = False


class ModerationGate:
    """Screens a session's newly-minted options and decides their first verdict.

    Args:
        config: Policy knobs; defaults to :meth:`ModerationConfig.from_env`.
        linguist: The model-screen hook; defaults to the offline no-op.
    """

    def __init__(
        self,
        config: ModerationConfig | None = None,
        linguist: LinguistReview | None = None,
    ) -> None:
        self.config = config or ModerationConfig.from_env()
        self.linguist = linguist or OfflineLinguistReview()
        self._wordlists: dict[str, frozenset[str]] = {}

    # -- wordlists ----------------------------------------------------------

    def wordlist_for(self, language_subtag: str) -> frozenset[str]:
        """The locale's offensive-term list, casefolded; empty when absent."""
        cached = self._wordlists.get(language_subtag)
        if cached is not None:
            return cached
        terms: frozenset[str] = frozenset()
        if self.config.wordlist_dir is not None:
            path = self.config.wordlist_dir / f"{language_subtag}.txt"
            if path.is_file():
                terms = frozenset(
                    line.strip().casefold()
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")
                )
        self._wordlists[language_subtag] = terms
        return terms

    # -- per-surface screens ------------------------------------------------

    @staticmethod
    def _injection_findings(surface: str, language_subtag: str) -> list[str]:
        """Bidi controls and non-allow-listed invisible characters.

        Defense in depth over the mechanical identifier check: a bidi control
        makes ``str.isidentifier()`` fail, but a mechanical failure only makes
        the row canon-INELIGIBLE — it still ingests, and without this screen a
        Trojan-source payload would sit un-escalated in the quarantine queue
        looking like an ordinary invalid identifier.
        """
        findings: list[str] = []
        allowed_format = (
            policy_for(language_subtag).allowed_format_chars
            if has_policy(language_subtag)
            else frozenset()
        )
        for ch in sorted(set(surface)):
            if ch in BIDI_CONTROLS:
                findings.append(
                    f"bidi control U+{ord(ch):04X} in surface form — "
                    "Trojan-source injection vector (CVE-2021-42574)"
                )
            elif ch in allowed_format:
                continue
            elif ch in FORBIDDEN_FORMAT_CHARS or is_default_ignorable(ch):
                findings.append(
                    f"invisible/format character U+{ord(ch):04X} in surface "
                    "form — renders as nothing, not allow-listed for this locale"
                )
        return findings

    def _confusable_findings(
        self,
        conn: sqlite3.Connection,
        surface: str,
        locale: str,
    ) -> list[str]:
        """Homoglyph-skeleton matches against English keywords and the corpus.

        Catches what the script gate cannot: a surface entirely in a script
        the locale legitimately allows, spelling — to the eye — an English
        keyword or an established word of the same locale.
        """
        findings: list[str] = []
        skel = skeleton(surface)
        fold = unicodedata.normalize("NFKC", surface).casefold()
        if skel in _EN_KEYWORDS and fold != skel:
            findings.append(
                f"confusable-skeleton match: renders like English keyword "
                f"{skel!r} without being it — homoglyph spoof"
            )
        for other_surface, other_uid in conn.execute(
            "SELECT surface_form, uid FROM options"
            " WHERE locale = ? AND withdrawn_at IS NULL",
            (locale,),
        ):
            other_fold = unicodedata.normalize("NFKC", other_surface).casefold()
            if other_fold == fold:
                continue  # same word by the comparison contract; not a spoof
            if skeleton(other_surface) == skel:
                findings.append(
                    f"confusable-skeleton match with existing option "
                    f"{other_uid} ({other_surface!r}) in this locale — "
                    "homoglyph twin of an established word"
                )
        return findings

    def _wordlist_findings(self, surface: str, language_subtag: str) -> list[str]:
        """Word-boundary-aware wordlist screen on the surface form.

        The whole folded surface and each identifier segment (split on
        underscores and non-word characters) are matched EXACTLY against the
        list — never substrings, which in this corpus flags three Python
        keywords on one mild English term (``class``/``pass``/``assert``).
        """
        wordlist = self.wordlist_for(language_subtag)
        if not wordlist:
            return []
        fold = unicodedata.normalize("NFKC", surface).casefold()
        segments = {s for s in re.split(r"[\W_]+", fold) if s}
        segments.add(fold)
        hits = sorted(segments & wordlist)
        if hits:
            return [
                f"wordlist hit ({hit!r}) — a wordlist hit is a question for a "
                "human, never a verdict"
                for hit in hits
            ]
        return []

    def _spam_findings(self, surface: str) -> list[str]:
        findings: list[str] = []
        if len(surface) > self.config.max_surface_length:
            findings.append(
                f"surface form is {len(surface)} characters "
                f"(limit {self.config.max_surface_length}) — spam heuristic"
            )
        run = re.search(r"(.)\1{" + str(self.config.max_char_run) + ",}", surface)
        if run:
            findings.append(
                f"character {run.group(1)!r} repeats "
                f"{len(run.group(0))} times consecutively — spam heuristic"
            )
        return findings

    def _linguist_result(
        self, surface: str, locale: str, concept_slug: str
    ) -> tuple[list[str], list[str]]:
        """(findings, notes) from the model-screen hook."""
        opinion = self.linguist.review(surface, locale, concept_slug)
        if opinion.opinion == "concern":
            detail = f": {opinion.note}" if opinion.note else ""
            return [f"linguist review raised a concern{detail}"], []
        if opinion.opinion == "unavailable":
            return [], [opinion.note or "linguist review unavailable"]
        return [], []

    # -- session-level screens ----------------------------------------------

    def rate_limit_findings(
        self, conn: sqlite3.Connection, contributor_id: str
    ) -> list[str]:
        """Per-contributor session rate limit inside the rolling window.

        Counts PRIOR ``review_sessions`` rows (this session's row is written
        at ingest, after this check), every status included: a spammer's
        returned sessions are exactly the signal.
        """
        window = f"-{self.config.rate_window_hours} hours"
        count = conn.execute(
            "SELECT COUNT(*) FROM review_sessions"
            " WHERE contributor_id = ? AND submitted_at >= datetime('now', ?)",
            (contributor_id, window),
        ).fetchone()[0]
        if count >= self.config.max_sessions_per_window:
            return [
                f"rate limit: {count} sessions in the last "
                f"{self.config.rate_window_hours}h (limit "
                f"{self.config.max_sessions_per_window}) — everything this "
                "session mints escalates"
            ]
        return []

    # -- the decision --------------------------------------------------------

    def _escalation_target(self) -> str:
        if self.config.escalation_policy == "maintainer_only":
            return "maintainers"
        return "maintainers + certified (rung-4) reviewers"

    def screen_session(
        self,
        conn: sqlite3.Connection,
        *,
        contributor_id: str,
        stored_rung_rank: int,
        locale: str,
        language_subtag: str,
        new_options: list[OptionScreenPlan],
    ) -> GateOutcome:
        """Screen every NEW option a session mints; decide each first verdict.

        Args:
            conn: Open connection (read: options, review_sessions).
            contributor_id: The minted ``c_…`` id.
            stored_rung_rank: ``review_rungs.rank`` of the contributor's rung
                as STORED before this session touched the database — 0 for a
                contributor this session would create. Never the bundle claim.
            locale: The session's locale tag.
            language_subtag: The locale's language subtag (wordlist + format
                -char policy key).
            new_options: The options the session would mint.

        Returns:
            The outcome: per-option verdicts with audit notes, stage-report
            details, and whether anything escalated.
        """
        session_findings = self.rate_limit_findings(conn, contributor_id)
        verdicts: dict[str, tuple[str, str]] = {}
        details: list[str] = list(session_findings)
        escalated = bool(session_findings)

        for option in new_options:
            findings = list(session_findings)
            notes: list[str] = []
            findings += self._injection_findings(option.surface, language_subtag)
            findings += self._confusable_findings(conn, option.surface, locale)
            findings += self._wordlist_findings(option.surface, language_subtag)
            findings += self._spam_findings(option.surface)
            linguist_findings, linguist_notes = self._linguist_result(
                option.surface, locale, option.concept_slug
            )
            findings += linguist_findings
            notes += linguist_notes

            if findings:
                escalated = True
                verdict = "held"
                note = (
                    "auto-gate: "
                    + "; ".join(findings)
                    + f" — escalated to {self._escalation_target()}"
                )
                details.append(
                    f"{option.surface!r} ({option.uid}): HELD — " + "; ".join(findings)
                )
            elif (
                option.mechanical_clean
                and stored_rung_rank >= self.config.fast_path_min_rank
            ):
                verdict = "cleared"
                note = (
                    f"auto-gate fast path: all screens passed; stored rung "
                    f"rank {stored_rung_rank} >= {self.config.fast_path_min_rank}"
                )
                details.append(
                    f"{option.surface!r} ({option.uid}): cleared — screened, "
                    f"fast-pathed on stored rung (rank {stored_rung_rank})"
                )
            else:
                verdict = "quarantined"
                note = (
                    "auto-gate: screens passed; quarantined pending the "
                    "import ritual (CORE-1828)"
                    if option.mechanical_clean
                    else "auto-gate: screens passed; mechanical gate failures "
                    "keep this out of the fast path"
                )
                details.append(
                    f"{option.surface!r} ({option.uid}): quarantined — "
                    "awaiting maintainer clearing"
                )
            if notes:
                note += " [" + "; ".join(notes) + "]"
            verdicts[option.uid] = (verdict, note)

        if not new_options:
            details.append("no new options minted; nothing to screen")
        return GateOutcome(verdicts=verdicts, details=details, escalated=escalated)


# ---------------------------------------------------------------------------
# The sub-decision query surfaces (consumed by CORE-1616 and the export)
# ---------------------------------------------------------------------------


def quarantined_uids_visible_to(
    conn: sqlite3.Connection,
    viewer_contributor_id: str | None,
    config: ModerationConfig,
) -> list[str]:
    """The withheld options a given viewer may see, per the visibility flag.

    THE query the reviewer surface (CORE-1616) must use for any non-maintainer
    view. Under the conservative default (``hidden``) it returns nothing for
    everyone; under ``submitter_only`` it returns only the viewer's own
    community submissions, for a greyed "pending screening" rendering.
    Other reviewers' views never include withheld options under either value.

    Args:
        conn: Open connection.
        viewer_contributor_id: The viewer's ``c_…`` id, or ``None`` for an
            anonymous viewer (always sees nothing).
        config: The effective moderation config.

    Returns:
        Option uids, sorted.
    """
    if config.quarantine_visibility == "hidden" or viewer_contributor_id is None:
        return []
    rows = conn.execute(
        "SELECT DISTINCT q.option_uid FROM option_withheld q"
        " JOIN option_provenance p ON p.option_uid = q.option_uid"
        " WHERE p.source = 'community' AND p.contributor_id = ?"
        " ORDER BY q.option_uid",
        (viewer_contributor_id,),
    ).fetchall()
    return [row[0] for row in rows]


def escalation_recipients(
    conn: sqlite3.Connection, config: ModerationConfig
) -> list[str]:
    """Contributor ids authorized to clear escalated (``held``) cases.

    Resolved against the ladder, not hardcoded: ``maintainer_only`` is rank 5;
    ``maintainer_and_certified`` (the conservative default) adds rank 4 — at
    today's team size, Madison plus trusted rung-4s.

    Args:
        conn: Open connection.
        config: The effective moderation config.

    Returns:
        Contributor ids, sorted.
    """
    min_rank = 5 if config.escalation_policy == "maintainer_only" else 4
    rows = conn.execute(
        "SELECT c.id FROM contributors c"
        " JOIN review_rungs r ON r.rung = c.current_rung"
        " WHERE r.rank >= ? ORDER BY c.id",
        (min_rank,),
    ).fetchall()
    return [row[0] for row in rows]
