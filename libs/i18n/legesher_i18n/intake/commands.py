"""CLI commands for the intake write path (CORE-1688 + CORE-1828).

Registered on the main ``legesher-i18n`` group by ``legesher_i18n.cli``:

* ``import-review-bundle <file>`` — the Stage-1 lane (canonical bundle files).
* ``import-issue <url-or-json-file>`` — the Stage-0 lane (issue-form emoji
  notation); a URL is fetched with ``gh issue view``.
* ``import-review-file <path> --pull-request <url-or-json-file>``: the
  markdown review lane: one review file from a merged language-packs pull
  request (CORE-2508).
* ``check-review-files <path>...``: the mechanical gate on a review pull
  request, no database and no salt: one report naming every failing row.
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
from legesher_i18n.intake.review_gate import Finding, GateReport, gate_review_file
from legesher_i18n.intake.review_parser import (
    REVIEW_LANE,
    PullRequest,
    ReviewFileRefused,
    parse_review_file,
    read_review,
)
from legesher_i18n.intake.review_template import (
    ReviewTemplateError,
    TemplateMetadata,
    code_span,
    check_review_pin,
    known_pack_versions,
    known_pins_from_template,
    parse_metadata_line,
    templates_at,
)
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


#: A GitHub pull-request URL and nothing else, for the same reason as above.
_PR_URL_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9][A-Za-z0-9._-]*/"
    r"[A-Za-z0-9][A-Za-z0-9._-]*/pull/[1-9][0-9]*$"
)


def validated_pull_request_url(url: str) -> str:
    """Return *url* if it is a GitHub pull-request URL, else raise.

    Raises:
        ValueError: if the value is not a well-formed GitHub pull-request URL.
    """
    if not isinstance(url, str) or not _PR_URL_RE.fullmatch(url):
        raise ValueError(
            f"{url!r} is not a GitHub pull-request URL. It runs as an argument "
            "to `gh` under your credentials, so it must be an explicit "
            "https://github.com/<owner>/<repo>/pull/<number>."
        )
    return url


def validated_issue_url(url: str) -> str:
    """Return *url* if it is a GitHub issue URL, else raise.

    Raises:
        ValueError: if the value is not a well-formed GitHub issue URL.
    """
    if not isinstance(url, str) or not _ISSUE_URL_RE.fullmatch(url):
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
    if _PR_URL_RE.fullmatch(url):
        # A review file arrives on a MERGED pull request: there is nothing to
        # close, and merging was the acceptance. The reply and the label are
        # the whole of it.
        steps = [
            (["gh", "pr", "comment", url, "--body", result.reply_text()], "comment")
        ]
        if result.status in ("accepted", "duplicate"):
            steps.append(
                (["gh", "pr", "edit", url, "--add-label", "contrib:imported"], "label")
            )
        return steps
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


# --- the markdown review lane (CORE-2508) ---------------------------------------


def _git(repo: Path, *args: str) -> bytes:
    """Raw git output: a review is archived as the bytes the merge committed."""
    try:
        result = subprocess.run(  # nosec B603 B607 - fixed git argv, no shell
            ["git", "--literal-pathspecs", "-C", str(repo), *args],
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise click.ClickException(f"git could not run: {error}")
    if result.returncode != 0:
        raise click.ClickException(
            f"git {' '.join(args[:2])} failed in {repo}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def _checkout(path: Path) -> tuple[Path, str]:
    """The checkout holding *path*, and *path* relative to it (``reviews/<tag>/<file>``).

    Refuses a symlink: the file a pull request carried is the one at its path,
    not wherever a link points.
    """
    if path.is_symlink():
        raise click.ClickException(
            f"{code_span(str(path))} is a symlink; check the file itself"
        )
    root = Path(
        _git(path.resolve().parent, "rev-parse", "--show-toplevel").decode().strip()
    )
    return root, path.resolve().relative_to(root).as_posix()


def _reads_cleanly(review_text: str, template_text: str) -> bool:
    """Whether *review_text* reads against *template_text* with no problems.

    An older template that shares the metadata line can have another shape (a
    box added since); the reader raises on such a template, and here that only
    means it is not the one the review was copied from.
    """
    try:
        return not read_review(review_text, template_text)[1]
    except ValueError:
        return False


def _base_template(
    root: Path, ref: str, review_text: str, tag: str
) -> tuple[str, set[str], set[str]]:
    """The template a review was copied from, read at *ref*, and every pin *ref* knows.

    The template comes from the base ref, never from the pull request's own
    files, and the version is matched by the review's metadata line, so a
    review started before a pack version bump is read against its own template.
    """
    try:
        history = templates_at(root, ref, f"reference/{tag}.md")
    except ReviewTemplateError as error:
        raise click.ClickException(str(error))
    first = review_text.lstrip("\ufeff").replace("\r\n", "\n").split("\n", 1)[0]
    # The digest covers the pack's words, not the template's prose, so several
    # versions can share a metadata line: take the first the review reads cleanly.
    candidates = [t for t in history if t.split("\n", 1)[0] == first] or history[:1]
    template = next(
        (t for t in candidates if _reads_cleanly(review_text, t)), candidates[0]
    )
    versions: set[str] = set()
    pythons: set[str] = set()
    for text in history:
        try:
            meta = parse_metadata_line(text)
        except ReviewTemplateError:
            continue
        versions.add(meta.pack_version)
        pythons.add(meta.python)
    return template, versions, pythons


def _registry_entry(code: str) -> dict | None:
    registry = json.loads(
        (Path(__file__).resolve().parents[1] / "languages.json").read_text(
            encoding="utf-8"
        )
    )["languages"]
    return registry.get(code)


def _registry_problems(meta: TemplateMetadata) -> list[str]:
    """The pin's code and tag against the registry, checked before either reaches git.

    ``bcp47`` names the template path; a value the registry does not hold
    (``../README``, ``s?``) is refused here and never handed to git.
    """
    return check_review_pin(
        meta,
        known_versions=[meta.pack_version],
        python_versions=[meta.python],
        registry_entry=_registry_entry(meta.code),
    )


def _pack_pins(packs_root: Path | None, code: str) -> tuple[set[str], set[str]] | None:
    """Known versions and Python versions from a pack tree, when one is given."""
    if packs_root is None or not (packs_root / code).is_dir():
        return None
    pack = packs_root / code
    pythons = {p.stem for p in pack.glob("legesher_i18n_python_*/packs/3.*.yml")}
    return known_pack_versions(pack), pythons


def _check_review_markdown(
    path: Path,
    *,
    author: str,
    template: Path | None,
    base_ref: str,
    packs_root: Path | None,
) -> GateReport:
    root, relative = _checkout(path)
    text = path.read_text(encoding="utf-8")
    try:
        meta = parse_metadata_line(text)
    except ReviewTemplateError as error:
        return GateReport(
            relative, None, [Finding(None, "structure", "fail", f"line 1: {error}")]
        )
    registry = _registry_problems(meta)
    if registry:
        return GateReport(
            relative,
            None,
            [Finding(None, "pin", "fail", problem) for problem in registry],
        )
    if template is not None:
        template_text = template.read_text(encoding="utf-8")
        versions, pythons = known_pins_from_template(template)
    else:
        template_text, versions, pythons = _base_template(
            root, base_ref, text, meta.bcp47
        )
    pins = _pack_pins(packs_root, meta.code)
    if pins is not None:
        versions, pythons = pins
    return gate_review_file(
        text,
        template_text=template_text,
        path=relative,
        author=author,
        known_versions=versions,
        python_versions=pythons,
        registry_entry=_registry_entry(meta.code),
    )


#: The shared contribution-check runner: one checker per file kind. The
#: bundle-PR lane registers ``.json`` here rather than building a second runner.
_CHECKERS = {".md": _check_review_markdown}


@click.command("check-review-files")
@click.argument(
    "paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "--author", required=True, help="GitHub login of the pull request author."
)
@click.option(
    "--base-ref",
    default="origin/main",
    show_default=True,
    help="The ref the templates and the known pins are read from: the pull "
    "request's base, never its own branch, so a pull request cannot vouch for "
    "itself by editing reference/<tag>.md.",
)
@click.option(
    "--template",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Check against this template file instead of the base ref's.",
)
@click.option(
    "--packs-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="A pack tree (the monorepo's libs/i18n/language-packs/python) to read "
    "known versions from, instead of the template's history.",
)
@click.option(
    "--report",
    "report_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the markdown report here (the local-runner artifact).",
)
@click.option("--json-report", type=click.Path(path_type=Path), default=None)
def check_review_files(
    paths: tuple[Path, ...],
    author: str,
    base_ref: str,
    template: Path | None,
    packs_root: Path | None,
    report_path: Path | None,
    json_report: Path | None,
) -> None:
    """Run the mechanical gate over review files; exit 1 if any row fails.

    No database, no salt, no identity: safe in a pull-request check.
    """
    reports: list[GateReport] = []
    for path in paths:
        checker = _CHECKERS.get(path.suffix)
        if checker is None:
            reports.append(
                GateReport(
                    path.as_posix(),
                    None,
                    [
                        Finding(
                            None,
                            "unchecked",
                            "fail",
                            f"no checker for {path.suffix or 'this kind of'} file in this runner",
                        )
                    ],
                )
            )
            continue
        try:
            reports.append(
                checker(
                    path,
                    author=author,
                    template=template,
                    base_ref=base_ref,
                    packs_root=packs_root,
                )
            )
        except (click.ClickException, ValueError) as error:
            # One file that cannot be read is a failing report for that file,
            # never an aborted run that leaves the other files unreported.
            # ValueError covers ReviewTemplateError and UnicodeDecodeError. The
            # detail can carry a path the pull request chose, so it stays inert.
            detail = code_span(
                error.message if isinstance(error, click.ClickException) else str(error)
            )
            reports.append(
                GateReport(
                    path.as_posix(), None, [Finding(None, "structure", "fail", detail)]
                )
            )
    markdown = "\n".join(report.to_markdown() for report in reports)
    click.echo(markdown)
    if report_path:
        report_path.write_text(markdown, encoding="utf-8")
    if json_report:
        json_report.write_text(
            json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    sys.exit(0 if all(report.passed for report in reports) else 1)


_PR_FIELDS = (
    "number,url,author,createdAt,state,mergedAt,mergeCommit,baseRefOid,headRefOid,files"
)


def _pull_request_payload(value: str) -> tuple[dict, str | None]:
    """The ``gh pr view --json`` payload, and the reply target when a URL was typed."""
    if value.startswith(("http://", "https://")):
        try:
            target = validated_pull_request_url(value)
        except ValueError as error:
            raise click.ClickException(str(error))
        try:
            fetched = subprocess.run(  # nosec B603 B607 - fixed gh argv, no shell
                ["gh", "pr", "view", target, "--json", _PR_FIELDS],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except FileNotFoundError:
            raise click.ClickException(
                "gh CLI not found; fetch the pull request JSON yourself and pass the file"
            )
        except subprocess.CalledProcessError as error:
            raise click.ClickException(f"gh pr view failed: {error.stderr.strip()}")
        return json.loads(fetched), target
    return json.loads(Path(value).read_text(encoding="utf-8")), None


@click.command("import-review-file")
@click.argument(
    "review_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--pull-request",
    "pull_request",
    required=True,
    help="The merged pull request: its URL (fetched with gh) or a `gh pr view "
    f"--json {_PR_FIELDS}` file. Identity comes from here, never from the review file.",
)
@click.option(
    "--template",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Read against this template file instead of the one at the merge's base.",
)
@click.option(
    "--packs-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("libs/i18n/language-packs/python"),
    show_default=True,
    help="The pack tree the pin is checked against.",
)
@_DB_OPTION
@click.option("--wordlist", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--json-report", type=click.Path(path_type=Path), default=None)
@click.option(
    "--reply", is_flag=True, help="Post the reply on the pull request and label it."
)
@click.option(
    "--sync", is_flag=True, help="Push DB + payload to the durable data home."
)
@click.option(
    "--before-merge",
    is_flag=True,
    help="Read a pull request that has not merged yet, at its head commit. A dry "
    "run: refused with --reply or --sync, and refused against a database that "
    "carries a salt fingerprint (a publish build or its durable copy).",
)
def import_review_file(
    review_file: Path,
    pull_request: str,
    template: Path | None,
    packs_root: Path | None,
    db_path: Path,
    wordlist: Path | None,
    json_report: Path | None,
    reply: bool,
    sync: bool,
    before_merge: bool,
) -> None:
    """Import one markdown review file from a merged language-packs pull request.

    The file is read from git at the commit the pull request merged (its head,
    with --before-merge), never from the working tree: a later pull request to
    the same file, or a maintainer edit, must not be recorded under this one.
    REVIEW_FILE names the path; its checkout must hold that commit.
    """
    _require_db(db_path)
    if before_merge and (reply or sync):
        raise click.ClickException(
            "--before-merge is a dry run: it cannot reply on the pull request or "
            "write to the durable home. Import for real after the merge."
        )
    if before_merge:
        conn = schema_v2.connect(db_path)
        try:
            fingerprinted = conn.execute(
                "SELECT 1 FROM build_meta WHERE key = 'salt_fingerprint'"
            ).fetchone()
        finally:
            conn.close()
        if fingerprinted:
            raise click.ClickException(
                f"{db_path} carries a salt fingerprint (a publish build, or a copy of "
                "one), and --before-merge writes a real session. Dry-run on a copy with "
                "the fingerprint removed: copy the database, then run sqlite3 <copy> "
                "\"DELETE FROM build_meta WHERE key = 'salt_fingerprint'\" and export "
                "a throwaway LEGESHER_CONTRIBUTOR_SALT."
            )
    payload, reply_target = _pull_request_payload(pull_request)
    if payload.get("state") != "MERGED" and not before_merge:
        raise click.ClickException(
            f"pull request {payload.get('url')} is {payload.get('state', 'not merged')}. "
            "Merging is the acceptance of a review; import it after it merges."
        )
    root, relative = _checkout(review_file)
    listed = [entry.get("path") for entry in payload.get("files") or []]
    if relative not in listed:
        raise click.ClickException(
            f"{relative} is not one of the files pull request {payload.get('url')} "
            f"changed ({len(listed)} listed)"
        )
    # The template history is read at the pull request's base commit in both
    # modes: under a rebase merge the merge commit's parent is the pull
    # request's own commit, which may carry its own edit to reference/.
    base = payload.get("baseRefOid")
    if before_merge:
        commit = payload.get("headRefOid")
    else:
        commit = (payload.get("mergeCommit") or {}).get("oid")
    if not commit or not base:
        raise click.ClickException(
            f"pull request {payload.get('url')} names no "
            f"{'head' if before_merge else 'merge'} commit or base commit; "
            f"fetch it with `gh pr view --json {_PR_FIELDS}`"
        )
    raw = _git(root, "show", f"{commit}:{relative}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise click.ClickException(f"{relative} at {commit} is not UTF-8: {error}")
    try:
        meta = parse_metadata_line(text)
    except ReviewTemplateError as error:
        raise click.ClickException(f"{relative} line 1: {error}")
    registry = _registry_problems(meta)
    if registry:
        raise click.ClickException(f"{relative}: " + "; ".join(registry))
    if template is not None:
        template_text = template.read_text(encoding="utf-8")
        versions, pythons = known_pins_from_template(template)
    else:
        template_text, versions, pythons = _base_template(root, base, text, meta.bcp47)
    pins = _pack_pins(packs_root, meta.code)
    if pins is not None:
        versions, pythons = pins
    pin_problems = check_review_pin(
        meta,
        known_versions=versions,
        python_versions=pythons,
        registry_entry=_registry_entry(meta.code),
    )
    if pin_problems:
        raise click.ClickException(
            f"{relative}: the pin is not one this importer knows:\n- "
            + "\n- ".join(pin_problems)
        )
    pr = PullRequest(
        url=payload["url"],
        number=int(payload["number"]),
        author=payload["author"]["login"],
        created_at=payload.get("createdAt"),
    )
    conn = schema_v2.connect(db_path)
    try:
        parsed = parse_review_file(
            text,
            template_text=template_text,
            path=relative,
            pull_request=pr,
            conn=conn,
        )
    except ReviewFileRefused as error:
        raise click.ClickException(
            f"{relative} refused, nothing imported:\n- " + "\n- ".join(error.problems)
        )
    finally:
        conn.close()
    try:
        importer = BundleImporter(
            db_path,
            conduct_wordlist=_load_wordlist(wordlist),
            **REVIEW_LANE,  # type: ignore[arg-type]
        )
        result = importer.import_bundle(parsed.bundle, parse_notes=parsed.notes)
    except ValueError as error:
        raise click.ClickException(str(error))
    except sqlite3.IntegrityError as error:
        raise click.ClickException(
            f"the database refused a row this review produced: {error}. Nothing "
            "was written (the ingest is one transaction)."
        )
    name = f"{result.session_uid}.review.md" if result.session_uid else review_file.name
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
    """Record a maintainer screening verdict for one option."""
    # CORE-1828: the maintainer screening lane of the intake queue.
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
