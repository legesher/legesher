"""CLI commands for the intake write path (CORE-1688 + CORE-1828).

Registered on the main ``legesher-i18n`` group by ``legesher_i18n.cli``:

* ``import-review-bundle <file>`` — the Stage-1 lane (canonical bundle files).
* ``import-issue <url-or-json-file>`` — the Stage-0 lane (issue-form emoji
  notation); a URL is fetched with ``gh issue view``.
* ``quarantine-queue`` — the triage lens the import ritual walks.
* ``clear-option <uid>`` — the DISTINCT, attributed maintainer act that ends
  (or extends) a quarantine; writes the auditable per-option verdict.

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
    parse_notes: list[str] | None = None,
    reply_target: str | None = None,
) -> None:
    click.echo(f"session: {result.session_uid}")
    click.echo(f"status:  {result.status}")
    for stage in result.report.get("stages", []):
        click.echo(f"  [{stage['status']:4}] {stage['stage']}")
        for detail in stage["details"]:
            click.echo(f"         - {detail}")
    for note in parse_notes or []:
        click.echo(f"  [note] {note}")
    if result.withdrawn_replay:
        click.echo(
            "  [note] withdrawn-contributor replay: evidence written, no "
            "identity column populated (runbook importer rule)"
        )
    if result.quarantined_options:
        click.echo(
            f"  [note] {len(result.quarantined_options)} option(s) quarantined "
            "pending the import ritual (CORE-1828): clear with "
            "`legesher-i18n clear-option <uid> --verdict cleared --by <you>`"
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

    if sync and result.status == "accepted":
        payloads = [raw_payload] if raw_payload else []
        sha = sync_to_durable_home(
            db_path, payloads, ritual="review import [CORE-1688]"
        )
        click.echo(
            f"durable home synced ({sha[:12]})"
            if sha
            else "durable home already current"
        )
    elif sync:
        click.echo(f"sync skipped: session {result.status}, nothing accepted")

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
def import_review_bundle(
    bundle_file: Path,
    db_path: Path,
    wordlist: Path | None,
    json_report: Path | None,
    reply: bool,
    reply_to: str | None,
    sync: bool,
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
        importer = BundleImporter(db_path, conduct_wordlist=_load_wordlist(wordlist))
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
        result = importer.import_bundle(parsed.bundle)
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
        parse_notes=parsed.notes,
        reply_target=reply_target,
    )


@click.command("quarantine-queue")
@_DB_OPTION
def quarantine_queue(db_path: Path) -> None:
    """List options awaiting the maintainer screen (the ritual's triage lens)."""
    _require_db(db_path)
    conn = schema_v2.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT option_uid, concept_slug, locale, surface_form, verdict,"
            " screened_at, note FROM quarantine_queue ORDER BY screened_at"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        click.echo("quarantine queue is empty")
        return
    for uid, slug, locale, surface, verdict, at, note in rows:
        click.echo(f"{uid}  {locale}  {slug}  {surface!r}  [{verdict}] since {at}")
        if note:
            click.echo(f"    {note}")
    click.echo(f"\n{len(rows)} option(s) awaiting a verdict")


@click.command("clear-option")
@click.argument("option_uid")
@click.option(
    "--verdict",
    type=click.Choice(["cleared", "held"]),
    required=True,
    help="'cleared' releases the option to rankings/export; 'held' keeps it back.",
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
        if not conn.execute(
            "SELECT 1 FROM options WHERE uid = ?", (option_uid,)
        ).fetchone():
            raise click.ClickException(f"no option {option_uid} in {db_path}")
        conn.execute(
            "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
            " screen_version, note) VALUES (?, ?, ?, ?, ?)",
            (option_uid, verdict, screened_by, SCREEN_VERSION, note),
        )
        conn.commit()
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
