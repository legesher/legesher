"""``legesher guard``: refuse a commit that must not land (CORE-1841).

The git clean filter normalizes and never refuses, because git stores a file
unchanged when its filter fails. This command is where refusal lives. The
pre-commit hook that ``legesher git setup`` installs runs ``legesher guard
--staged``. The hook is a client-side check: ``git commit --no-verify``,
merges and rebases skip it. The pull-request check (CORE-1323) is the layer
meant to see every commit.

Exit status: 0 no findings, 1 findings, 2 the guard could not run.
"""

import subprocess
import sys
from pathlib import Path

import click

from legesher_core.guard import Finding, check_blob
from legesher_core.stored_form import KeywordTable, keyword_table

#: The gitattributes filter value that marks a file as Legesher's.
FILTER_NAME = "legesher"

#: Index modes of regular files. A symlink's blob is its target path and a
#: gitlink has no blob, so neither is read as source.
REGULAR_FILE_MODES = frozenset({"100644", "100755"})

#: Seconds any one git command may take.
GIT_TIMEOUT = 60


class GuardError(Exception):
    """The guard cannot run (not a repository, unknown language, git failed)."""


def _git(
    repo: Path, *args: str, stdin: bytes | None = None
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            input=stdin,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GuardError(f"git {args[0]} failed: {exc}") from exc


def _repo_root() -> Path | None:
    result = _git(Path.cwd(), "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    return Path(result.stdout.decode().strip())


def _blob_bytes(repo: Path, revision: str) -> bytes | None:
    result = _git(repo, "cat-file", "blob", revision)
    return result.stdout if result.returncode == 0 else None


def _blob(repo: Path, revision: str) -> str | None:
    data = _blob_bytes(repo, revision)
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _legesher_paths(repo: Path, paths: list[str], *, cached: bool) -> list[str]:
    """The paths whose ``filter`` attribute is Legesher's, in order.

    ``cached`` reads ``.gitattributes`` from the index, which is what the
    commit carries; otherwise from the working tree, which is what the clean
    filter reads.
    """
    if not paths:
        return []
    result = _git(
        repo,
        "check-attr",
        "-z",
        "--stdin",
        *(["--cached"] if cached else []),
        "filter",
        stdin=b"".join(
            path.encode("utf-8", "surrogateescape") + b"\0" for path in paths
        ),
    )
    if result.returncode != 0:
        raise GuardError(result.stderr.decode().strip() or "git check-attr failed")
    fields = result.stdout.decode("utf-8", "surrogateescape").split("\0")
    # Output is path NUL attribute NUL value NUL, repeated.
    return [
        fields[index]
        for index in range(0, len(fields) - 2, 3)
        if fields[index + 2] == FILTER_NAME
    ]


def _staged_paths(repo: Path) -> list[str]:
    """Every staged path that is a regular file, whatever its change.

    ``--raw`` gives each path's new mode, ``--no-renames`` reports a rename as
    the added path, and ``--diff-filter=d`` keeps every status but deletion,
    type changes included.
    """
    result = _git(
        repo, "diff", "--cached", "--raw", "-z", "--no-renames", "--diff-filter=d"
    )
    if result.returncode != 0:
        raise GuardError(result.stderr.decode().strip() or "git diff --cached failed")
    fields = result.stdout.decode("utf-8", "surrogateescape").split("\0")
    paths = []
    # Each record is ":old_mode new_mode old_sha new_sha status" NUL path NUL.
    for header, path in zip(fields[0::2], fields[1::2], strict=False):
        parts = header.split()
        if len(parts) >= 2 and parts[1] in REGULAR_FILE_MODES:
            paths.append(path)
    return paths


def _language(repo: Path | None, language: str | None) -> KeywordTable:
    if language is None:
        from legesher.config import LegesherConfig

        language = LegesherConfig.load(repo).language
    try:
        return keyword_table(language)
    except Exception as exc:
        raise GuardError(f"cannot load the '{language}' language pack: {exc}") from exc


def check_staged(repo: Path, local: KeywordTable) -> tuple[int, list[Finding]]:
    """``(files checked, findings)`` for the staged Legesher files."""
    findings: list[Finding] = []
    staged = _staged_paths(repo)
    # The commit carries the staged attributes, but right after setup the
    # .gitattributes file is not staged yet and the clean filter reads the
    # working tree's. Either one marking a path makes it Legesher's, so an
    # unstaged edit cannot exempt a file and an unstaged file still counts.
    marked = set(_legesher_paths(repo, staged, cached=True))
    marked |= set(_legesher_paths(repo, staged, cached=False))
    paths = [path for path in staged if path in marked]
    for path in paths:
        data = _blob_bytes(repo, f":0:{path}")
        if data is None:
            raise GuardError(f"cannot read the staged version of {path}")
        stored = _blob(repo, f"HEAD:{path}")
        findings.extend(check_blob(data, path=path, local=local, stored=stored))
    return len(paths), findings


def check_files(
    repo: Path | None, names: list[str], local: KeywordTable
) -> list[Finding]:
    """Findings for files on disk, each judged against its committed version."""
    findings: list[Finding] = []
    for name in names:
        path = Path(name)
        data = path.read_bytes()
        stored = None
        shown = name
        if repo is not None:
            try:
                relative = path.resolve().relative_to(repo.resolve()).as_posix()
            except ValueError:
                relative = None
            if relative is not None:
                stored = _blob(repo, f"HEAD:{relative}")
                shown = relative
        findings.extend(check_blob(data, path=shown, local=local, stored=stored))
    return findings


@click.command(name="guard")
@click.option(
    "--staged",
    is_flag=True,
    help="Check the Legesher files staged for commit (the default without PATHS).",
)
@click.option(
    "--language",
    "-l",
    default=None,
    help="Language this repository is written in (default: from config).",
)
@click.argument("paths", nargs=-1, type=click.Path(exists=True, dir_okay=False))
def guard(staged: bool, language: str | None, paths: tuple[str, ...]) -> None:
    """Refuse Trojan Source characters and keywords out of their stored form.

    \b
    Checks:
      encoding  content that is not UTF-8, or a coding declaration other
                than UTF-8
      unicode   bidi controls, invisible characters in code, tatweel, and
                identifier characters outside every supported script
      keyword   a keyword not in its block's stored form (the clean filter
                normalizes these; a finding means the file skipped it)

    \b
    Examples:
        $ legesher guard --staged        # what the pre-commit hook runs
        $ legesher guard src/module.py
    """
    try:
        repo = _repo_root()
        if staged or not paths:
            if repo is None:
                raise GuardError("not in a git repository")
            checked, findings = check_staged(repo, _language(repo, language))
        else:
            local = _language(repo, language)
            checked, findings = len(paths), check_files(repo, list(paths), local)
    except GuardError as exc:
        click.echo(f"legesher guard: {exc}", err=True)
        sys.exit(2)

    for finding in findings:
        click.echo(finding.format())
    if not findings:
        click.echo(f"legesher guard: {checked} file(s) checked, no findings", err=True)
        return

    files = len({finding.path for finding in findings})
    click.echo(f"\nlegesher guard: {len(findings)} finding(s) in {files} file(s).")
    if any(finding.check == "encoding" for finding in findings):
        click.echo(
            "Encoding findings: Legesher files are UTF-8 with no other coding "
            "declaration, so the guard reads them the way Python does."
        )
    if any(finding.check == "keyword" for finding in findings):
        click.echo(
            "Keyword findings mean the file was staged without the Legesher "
            "filter. Run `legesher git setup`, then `git add --renormalize <path>`."
        )
    if any(finding.check == "unicode" for finding in findings):
        click.echo(
            "Unicode findings are characters that can make code read differently "
            "than it runs. Remove them; there is no override."
        )
    sys.exit(1)


__all__ = ["guard", "check_staged", "check_files"]
