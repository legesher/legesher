"""CLI commands for the intake write path (CORE-1688 + CORE-1828).

Registered on the main ``legesher-i18n`` group by ``legesher_i18n.cli``:

* ``import-review-bundle <file>`` — the Stage-1 lane (canonical bundle files).
* ``import-issue <url-or-json-file>`` — the Stage-0 lane (issue-form emoji
  notation); a URL is fetched with ``gh issue view``.
* ``quarantine-queue`` — the triage lens the import ritual walks
  (escalations first, then higher submitter rungs — CORE-1797 queue order).
* ``clear-option <uid>`` — the DISTINCT, attributed maintainer act that ends
  (or extends) a quarantine; writes the auditable per-option verdict.
* ``rescreen-flagged`` — feeds ``option_flags`` reports back into screening
  (CORE-1797): visible community options with open flags are held for a
  human moderator.

Exit codes: 0 accepted/duplicate · 1 returned (actionable report printed) ·
3 halted (withdrawal rule: a human must decide — never code).

The reply text is always printed, ready to post; ``--reply`` posts it with
``gh`` and closes the issue with the ``contrib:imported`` label. ``--sync``
runs the durable-home write-through (CORE-1794): DB + accepted raw payload
pushed to ``$LEGESHER_DATA_REPO``.
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import click

from legesher_i18n.db import schema_v2
from legesher_i18n.intake.issue_parser import parse_issue
from legesher_i18n.intake.moderation import AUTO_SCREEN_VERSION, AUTO_SCREENED_BY
from legesher_i18n.intake.pipeline import SCREEN_VERSION, BundleImporter, ImportResult
from legesher_i18n.intake.sync import sync_to_durable_home

_EXIT_CODES = {"accepted": 0, "duplicate": 0, "returned": 1, "halted": 3}

_DB_OPTION = click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default=Path("build/translations_v2.db"),
    show_default=True,
    help="The operational v2 database (the one review store).",
)


def _require_db(db_path: Path) -> None:
    if not db_path.is_file():
        raise click.ClickException(
            f"no database at {db_path}. Point --db at the operational v2 "
            "database (copy it in from the durable data home, or build one "
            "with scripts/migrate_to_v2.py)."
        )


def _load_wordlist(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _finish(
    result: ImportResult,
    *,
    db_path: Path,
    raw_payload: tuple[str, bytes] | None,
    json_report: Path | None,
    reply: bool,
    sync: bool,
    reply_target: str | None = None,
) -> None:
    click.echo(f"session: {result.session_uid}")
    click.echo(f"status:  {result.status}")
    # Parse notes are one of these stages now, not a list printed beside them.
    for stage in result.report.get("stages", []):
        click.echo(f"  [{stage['status']:4}] {stage['stage']}")
        for detail in stage["details"]:
            click.echo(f"         - {detail}")
    if result.withdrawn_replay:
        click.echo(
            "  [note] withdrawn-contributor replay: evidence written, no "
            "identity column populated (runbook importer rule)"
        )
    if result.created_options:
        pending = [
            uid
            for uid in result.created_options
            if result.option_verdicts.get(uid) != "cleared"
        ]
        held = sum(1 for uid in pending if result.option_verdicts.get(uid) == "held")
        cleared = len(result.created_options) - len(pending)
        if cleared:
            click.echo(
                f"  [note] {cleared} option(s) cleared by the automated gate "
                "(fast path, CORE-1797) — live in rankings"
            )
        if pending:
            click.echo(
                f"  [note] {len(pending)} option(s) withheld pending the "
                f"import ritual ({held} escalated by the safety screen): "
                "clear with `legesher-i18n clear-option <uid> --verdict "
                "cleared --by <you>`"
            )

    if json_report:
        json_report.write_text(result.to_json(), encoding="utf-8")
        click.echo(f"ledger written to {json_report}")

    click.echo("\n--- reply (ready to post) ---")
    click.echo(result.reply_text())
    click.echo("--- end reply ---\n")

    if reply and result.status == "halted":
        click.echo(
            "--reply suppressed: this import halted on the withdrawal rule. "
            "Reply by hand, and do not quote the reason above — it names a "
            "withdrawal the contributor asked us to erase."
        )
    elif reply and reply_target:
        _post_reply(result, reply_target)
    elif reply:
        click.echo(
            "--reply requested but no reply target was given. Pass --reply-to "
            "<github issue url>; the target is never taken from the submission, "
            "because a submitter could otherwise aim `gh` at any repository "
            "your token can write to."
        )

    sync_failed = False
    if sync and result.status == "accepted":
        payloads = [raw_payload] if raw_payload else []
        try:
            sha = sync_to_durable_home(
                db_path, payloads, ritual="review import [CORE-1688]"
            )
        except (RuntimeError, subprocess.CalledProcessError) as error:
            sync_failed = True
            # The import already committed; only the write-through failed. Say
            # both, so nobody re-runs an idempotent-but-confusing import to
            # "fix" a git problem.
            detail = getattr(error, "stderr", None) or error
            click.echo(
                f"SYNC FAILED: {detail}\n"
                "The import itself is committed to the local database — do not "
                "re-run it. Fix the data home (set $LEGESHER_DATA_REPO, or "
                "resolve the git state) and push it by hand; the run is not "
                "complete until the database and payload reach the data home."
            )
        else:
            click.echo(
                f"durable home synced ({sha[:12]})"
                if sha
                else "durable home already current"
            )
    elif sync:
        click.echo(f"sync skipped: session {result.status}, nothing accepted")

    if sync_failed:
        # Exit non-zero even though the import itself succeeded: the ritual is
        # "import AND push", and a scripted caller that reads 0 here would
        # record a run whose database never left the workstation.
        sys.exit(4)
    sys.exit(_EXIT_CODES.get(result.status, 1))


#: A GitHub issue URL and nothing else. The reply target becomes an argument to
#: `gh` under the maintainer's credentials, so it is matched against a closed
#: shape rather than merely sanitized: host pinned to github.com, path exactly
#: /<owner>/<repo>/issues/<number>. This also rejects a value beginning with
#: "-", which `gh` would otherwise parse as a flag.
_ISSUE_URL_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9][A-Za-z0-9._-]*/"
    r"[A-Za-z0-9][A-Za-z0-9._-]*/issues/[1-9][0-9]*$"
)


def validated_issue_url(url: str) -> str:
    """Return *url* if it is a GitHub issue URL, else raise.

    Raises:
        ValueError: if the value is not a well-formed GitHub issue URL.
    """
    if not isinstance(url, str) or not _ISSUE_URL_RE.match(url):
        raise ValueError(
            f"{url!r} is not a GitHub issue URL. The reply target runs as an "
            "argument to `gh` under your credentials, so it must be an "
            "explicit https://github.com/<owner>/<repo>/issues/<number>."
        )
    return url


def _reply_steps(
    result: ImportResult, target: str | None = None
) -> list[tuple[list[str], str]]:
    """The gh steps for this outcome, in order.

    Only an ACCEPTED submission is labelled `contrib:imported` and closed:
    a returned issue has not been imported, so both would be false — and
    closing it would end the conversation the report just opened.

    A HALTED import posts NOTHING. It means the withdrawal-tombstone rule
    fired, and the runbook's instruction there is to stop and surface it to a
    human; an automated comment on a withdrawn contributor's own issue is
    precisely the disclosure the tombstone exists to prevent.
    """
    if result.status == "halted":
        return []
    url = target or ""
    steps = [
        (["gh", "issue", "comment", url, "--body", result.reply_text()], "comment")
    ]
    if result.status in ("accepted", "duplicate"):
        steps.append(
            (["gh", "issue", "edit", url, "--add-label", "contrib:imported"], "label")
        )
        steps.append((["gh", "issue", "close", url], "close"))
    return steps


def _post_reply(result: ImportResult, target: str) -> None:
    # Sequential and fail-closed: each step is a precondition of the next.
    # Closing an issue whose reply never posted leaves the contributor with
    # silence and a closed issue — the exact opposite of the feedback loop.
    for argv, what in _reply_steps(result, target):
        try:
            subprocess.run(  # nosec B603 B607 - fixed gh argv, no shell
                argv, check=True, capture_output=True, text=True
            )
            click.echo(f"gh {what}: done")
        except FileNotFoundError:
            click.echo(f"gh {what}: gh CLI not found — post the reply above by hand")
            return
        except subprocess.CalledProcessError as error:
            click.echo(
                f"gh {what} failed: {error.stderr.strip()} — stopping here; "
                "post the reply above by hand"
            )
            return


@click.command("import-review-bundle")
@click.argument("bundle_file", type=click.Path(exists=True, path_type=Path))
@_DB_OPTION
@click.option(
    "--wordlist",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Conduct-screen wordlist (one term per line; hits escalate, never reject).",
)
@click.option("--json-report", type=click.Path(path_type=Path), default=None)
@click.option(
    "--reply", is_flag=True, help="Post the reply via gh and close the issue."
)
@click.option(
    "--reply-to",
    "reply_to",
    default=None,
    help="GitHub issue URL to reply on. Required with --reply: the target is "
    "never read from the bundle, which a stranger controls.",
)
@click.option(
    "--sync", is_flag=True, help="Push DB + payload to the durable data home."
)
@click.option(
    "--recovered-history",
    is_flag=True,
    help="Import a bundle reconstructed from recovered public review history "
    "(the pre-intake GitHub era): only the original_work attestation is "
    "required, because CoC agreement and DCO sign-off were never collected "
    "then. The flag relaxes which attestations are REQUIRED — it never "
    "changes what the bundle asserts, and a bundle claiming coc_agreed or "
    "dco it does not have is still a lie the maintainer owns.",
)
def import_review_bundle(
    bundle_file: Path,
    db_path: Path,
    wordlist: Path | None,
    json_report: Path | None,
    reply: bool,
    reply_to: str | None,
    sync: bool,
    recovered_history: bool,
) -> None:
    """Import a canonical review-bundle file (the Stage-1 lane)."""
    _require_db(db_path)
    if reply_to is not None:
        try:
            reply_to = validated_issue_url(reply_to)
        except ValueError as error:
            raise click.ClickException(str(error))
    raw = bundle_file.read_bytes()
    try:
        lane = (
            # Recovered bundles are reconstructed GitHub-era review signal, so
            # the endorsement channel is github, never the portal default.
            {"required_attestations": ("original_work",), "method": "github"}
            if recovered_history
            else {}
        )
        importer = BundleImporter(
            db_path, conduct_wordlist=_load_wordlist(wordlist), **lane
        )
        result = importer.import_bundle(raw)
    except json.JSONDecodeError as error:
        raise click.ClickException(f"bundle is not valid JSON: {error}")
    except ValueError as error:
        raise click.ClickException(str(error))
    except sqlite3.IntegrityError as error:
        raise click.ClickException(
            f"the database refused a row this bundle produced: {error}. "
            "Nothing was written (the ingest is one transaction). Please file "
            "this with the bundle attached — a constraint reached at ingest is "
            "a gap in the verification pipeline, not your mistake."
        )
    name = f"{result.session_uid}.json" if result.session_uid else bundle_file.name
    _finish(
        result,
        db_path=db_path,
        raw_payload=(name, raw),
        json_report=json_report,
        reply=reply,
        sync=sync,
        reply_target=reply_to,
    )


@click.command("import-issue")
@click.argument("issue")
@_DB_OPTION
@click.option("--wordlist", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--json-report", type=click.Path(path_type=Path), default=None)
@click.option(
    "--reply", is_flag=True, help="Post the reply via gh and close the issue."
)
@click.option(
    "--sync", is_flag=True, help="Push DB + payload to the durable data home."
)
def import_issue(
    issue: str,
    db_path: Path,
    wordlist: Path | None,
    json_report: Path | None,
    reply: bool,
    sync: bool,
) -> None:
    """Import a language_pack_review issue (Stage 0): URL or a gh-JSON file."""
    _require_db(db_path)
    # The reply target is the URL the MAINTAINER typed, never the one the
    # submission carries. Passing a gh-JSON file gives no trusted target.
    reply_target: str | None = None
    if issue.startswith(("http://", "https://")):
        try:
            reply_target = validated_issue_url(issue)
        except ValueError as error:
            raise click.ClickException(str(error))
        try:
            fetched = subprocess.run(  # nosec B603 B607 - fixed gh argv, no shell
                [
                    "gh",
                    "issue",
                    "view",
                    issue,
                    "--json",
                    "number,url,author,title,body,createdAt",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except FileNotFoundError:
            raise click.ClickException(
                "gh CLI not found; fetch the issue JSON yourself and pass the file"
            )
        except subprocess.CalledProcessError as error:
            raise click.ClickException(f"gh issue view failed: {error.stderr.strip()}")
        payload = json.loads(fetched)
        raw = fetched.encode("utf-8")
    else:
        raw = Path(issue).read_bytes()
        payload = json.loads(raw.decode("utf-8"))

    conn = schema_v2.connect(db_path)
    try:
        parsed = parse_issue(payload, conn)
    except ValueError as error:
        raise click.ClickException(str(error))
    finally:
        conn.close()

    try:
        importer = BundleImporter(
            db_path,
            method="github",
            elicited_default="quick",
            # The old form collects no DCO sign-off; see issue_parser docstring.
            required_attestations=("original_work", "coc_agreed"),
            conduct_wordlist=_load_wordlist(wordlist),
        )
        # The notes belong to the IMPORT, not to this terminal: `import_bundle`
        # records them as a `parse` warn stage and on `ImportResult.parse_notes`,
        # so they reach the ledger and the verification report (CORE-1838).
        result = importer.import_bundle(parsed.bundle, parse_notes=parsed.notes)
    except ValueError as error:
        raise click.ClickException(str(error))
    except sqlite3.IntegrityError as error:
        raise click.ClickException(
            f"the database refused a row this issue produced: {error}. Nothing "
            "was written (the ingest is one transaction)."
        )
    name = f"{result.session_uid}.issue.json" if result.session_uid else "issue.json"
    _finish(
        result,
        db_path=db_path,
        raw_payload=(name, raw),
        json_report=json_report,
        reply=reply,
        sync=sync,
        reply_target=reply_target,
    )


@click.command("quarantine-queue")
@_DB_OPTION
def quarantine_queue(db_path: Path) -> None:
    """List options awaiting the maintainer screen (the ritual's triage lens)."""
    _require_db(db_path)
    conn = schema_v2.connect(db_path)
    try:
        # The lens is what a maintainer reaches for BEFORE importing anything,
        # so it cannot assume the import lane has already upgraded the
        # carried-forward database (CORE-1838).
        schema_v2.ensure_intake_screening(conn)
        rows = conn.execute(
            "SELECT q.option_uid, q.concept_slug, q.locale, q.surface_form,"
            " q.verdict, q.screened_at, q.note FROM quarantine_queue q"
            # 'rejected' is a decision already taken. It stays withheld
            # forever (append-only, and the view is `<> cleared`), but it is
            # not awaiting anything, and leaving it here would grow the queue
            # monotonically until the real work was invisible in it.
            " WHERE q.verdict <> 'rejected'"
            # Triage order (CORE-1797): escalations first — a `held` verdict
            # is the safety screen saying "a human must look" — then higher
            # submitter rungs fast-path the queue (never the screen), oldest
            # first within a band. Rung read from the submitter's STORED rung
            # via community provenance; options without one sort last.
            " ORDER BY (q.verdict = 'held') DESC,"
            " COALESCE((SELECT MAX(r.rank) FROM option_provenance p"
            "   JOIN contributors c ON c.id = p.contributor_id"
            "   JOIN review_rungs r ON r.rung = c.current_rung"
            "   WHERE p.option_uid = q.option_uid AND p.source = 'community'),"
            " -1) DESC,"
            " q.screened_at"
        ).fetchall()
        conn_rejected_count = conn.execute(
            "SELECT COUNT(*) FROM option_withheld WHERE verdict = 'rejected'"
        ).fetchone()[0]
    finally:
        conn.close()
    rejected = conn_rejected_count
    if not rows:
        click.echo("quarantine queue is empty")
        if rejected:
            click.echo(f"({rejected} rejected option(s) withheld, decision taken)")
        return
    for uid, slug, locale, surface, verdict, at, note in rows:
        click.echo(f"{uid}  {locale}  {slug}  {surface!r}  [{verdict}] since {at}")
        if note:
            click.echo(f"    {note}")
    click.echo(f"\n{len(rows)} option(s) awaiting a verdict")
    if rejected:
        click.echo(f"({rejected} rejected option(s) withheld, decision taken)")


@click.command("clear-option")
@click.argument("option_uid")
@click.option(
    "--verdict",
    type=click.Choice(["cleared", "held", "rejected"]),
    required=True,
    help="'cleared' releases the option to rankings and export; 'held' keeps it "
    "back for eyes you do not have; 'rejected' is the moderation verdict for "
    "harmful, spam or injection content. Only 'cleared' is visible anywhere.",
)
@click.option(
    "--by",
    "screened_by",
    required=True,
    help="Who decided. Clearing must be attributable (CORE-1828 audit record).",
)
@click.option("--note", default=None, help="Why — lands on the audit record.")
@_DB_OPTION
def clear_option(
    option_uid: str, verdict: str, screened_by: str, note: str | None, db_path: Path
) -> None:
    """Record a maintainer screening verdict for one option (CORE-1828)."""
    _require_db(db_path)
    conn = schema_v2.connect(db_path)
    try:
        # Recording the FIRST verdict on a carried-forward database is a normal
        # thing to do; the table it lands in may not exist yet (CORE-1838).
        schema_v2.ensure_intake_screening(conn)
        if not conn.execute(
            "SELECT 1 FROM options WHERE uid = ?", (option_uid,)
        ).fetchone():
            raise click.ClickException(f"no option {option_uid} in {db_path}")
        try:
            conn.execute(
                "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
                " screen_version, note) VALUES (?, ?, ?, ?, ?)",
                (option_uid, verdict, screened_by, SCREEN_VERSION, note),
            )
            conn.commit()
        except sqlite3.IntegrityError as error:
            conn.rollback()
            hint = (
                "An option that is currently canon-selected cannot be withheld "
                "in place — remove it from libs/i18n/canon/<locale>.toml and "
                "reload, so the demotion is a reviewed text change rather than "
                "a side effect."
                if "canon-selected" in str(error)
                else "The database refused the verdict itself. If this is a "
                "carried-forward database built before the 'rejected' verdict "
                "existed, its CHECK constraint predates the vocabulary; rebuild "
                "it or apply the current schema."
            )
            raise click.ClickException(
                f"the database refused this verdict: {error}. {hint}"
            )
        visible = conn.execute(
            "SELECT COUNT(*) FROM option_standings WHERE option_uid = ?",
            (option_uid,),
        ).fetchone()[0]
    finally:
        conn.close()
    click.echo(
        f"{option_uid}: verdict '{verdict}' recorded by {screened_by} — "
        + ("now visible to rankings and export" if visible else "held back")
    )
    click.echo(
        "remember: the ritual ends with a push to the durable data home "
        "(run the sync or re-run the import with --sync)"
    )


@click.command("rescreen-flagged")
@click.option(
    "--dry-run", is_flag=True, help="Report what would be re-screened; write nothing."
)
@_DB_OPTION
def rescreen_flagged(dry_run: bool, db_path: Path) -> None:
    """Pull flagged community options back behind the screen (CORE-1797).

    ``option_flags`` is the post-hoc report channel, and this is where it
    feeds re-screening: every community-sourced option carrying an UNRESOLVED
    flag while currently visible (verdict ``cleared``, or no verdict at all)
    gets a new ``held`` verdict — withdrawn from rankings, views and export
    until a human moderator decides. A flag is a person saying "look at
    this"; the automated gate never converts it into a rejection.
    """
    _require_db(db_path)
    conn = schema_v2.connect(db_path)
    wrote = 0
    blocked: list[tuple[str, str]] = []
    try:
        schema_v2.ensure_intake_screening(conn)
        rows = conn.execute(
            "SELECT o.uid, o.surface_form,"
            " (SELECT GROUP_CONCAT(DISTINCT f.reason) FROM option_flags f"
            "   WHERE f.option_uid = o.uid AND f.resolved_at IS NULL) AS reasons"
            " FROM options o"
            " WHERE EXISTS (SELECT 1 FROM option_flags f WHERE f.option_uid = o.uid"
            "               AND f.resolved_at IS NULL)"
            "   AND EXISTS (SELECT 1 FROM option_provenance p"
            "               WHERE p.option_uid = o.uid AND p.source = 'community')"
            "   AND NOT EXISTS (SELECT 1 FROM option_withheld q"
            "                   WHERE q.option_uid = o.uid)"
            " ORDER BY o.uid"
        ).fetchall()
        for uid, surface, reasons in rows:
            click.echo(f"{uid}  {surface!r}  open flag(s): {reasons}")
            if dry_run:
                continue
            try:
                conn.execute(
                    "INSERT INTO option_screenings(option_uid, verdict,"
                    " screened_by, screen_version, note) VALUES"
                    " (?, 'held', ?, ?, ?)",
                    (
                        uid,
                        AUTO_SCREENED_BY,
                        AUTO_SCREEN_VERSION,
                        f"re-screen on open flag(s): {reasons} — a report is a "
                        "question for a human, never a verdict",
                    ),
                )
                conn.commit()
                wrote += 1
            except sqlite3.IntegrityError as error:
                conn.rollback()
                blocked.append((uid, str(error)))
    finally:
        conn.close()
    if dry_run:
        click.echo(f"{len(rows)} flagged option(s) would be re-screened (dry run)")
        return
    click.echo(f"{wrote} option(s) held for re-screening")
    for uid, error in blocked:
        click.echo(
            f"  BLOCKED {uid}: {error} — a canon-selected option cannot be "
            "withheld in place; remove it from libs/i18n/canon/<locale>.toml "
            "and reload first"
        )
    if wrote:
        click.echo(
            "remember: the ritual ends with a push to the durable data home "
            "(run the sync or re-run the import with --sync)"
        )
