"""``legesher guard``: refuse a commit that must not land (CORE-1841).

The git clean filter normalizes and never refuses, because git stores a file
unchanged when its filter fails. This command is where refusal lives. The
pre-commit hook that ``legesher git setup`` installs runs ``legesher guard
--staged``. The hook is a client-side check: ``git commit --no-verify``,
merges and rebases skip it. ``legesher guard --diff`` is what a pull-request
check runs (CORE-1323): it sees changes made anywhere, though it checks a
pull request's net change rather than each commit in it.

Exit status: 0 no findings, 1 findings, 2 the guard could not run.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click

from legesher_core.guard import (
    Finding,
    check_artifact,
    check_blob,
    is_known_artifact,
    is_legesher_path,
)
from legesher_core.stored_form import KeywordTable, keyword_table

#: The gitattributes filter value that marks a file as Legesher's.
FILTER_NAME = "legesher"

#: Index modes of regular files. A symlink's blob is its target path and a
#: gitlink has no blob, so neither is read as source.
REGULAR_FILE_MODES = frozenset({"100644", "100755"})

#: The index mode of a symlink, whose blob is its target path.
SYMLINK_MODE = "120000"

#: The index mode of a submodule (a gitlink), which has no blob.
GITLINK_MODE = "160000"

#: Seconds any one git command may take.
GIT_TIMEOUT = 60


class GuardError(Exception):
    """The guard cannot run (not a repository, unknown language, git failed)."""


def _git(
    repo: Path,
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            input=stdin,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT,
            env=env,
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


def _legesher_paths_at(repo: Path, commit: str, paths: list[str]) -> list[str]:
    """The paths a commit's own ``.gitattributes`` files mark as Legesher's.

    Read through a throwaway index holding that commit's tree, so it works on
    every git version (``check-attr --source`` is git 2.40 and later).
    """
    if not paths:
        return []
    with tempfile.TemporaryDirectory(prefix="legesher-guard-") as scratch:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(scratch) / "index"))
        loaded = _git(repo, "read-tree", commit, env=env)
        if loaded.returncode != 0:
            raise GuardError(loaded.stderr.decode().strip() or "git read-tree failed")
        return _legesher_paths(repo, paths, cached=True, env=env)


def _legesher_paths(
    repo: Path, paths: list[str], *, cached: bool, env: dict[str, str] | None = None
) -> list[str]:
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
        env=env,
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


def _changed(repo: Path, *revisions: str) -> list[tuple[str, str]]:
    """``(path, new mode)`` for every path the diff adds or changes.

    ``--raw`` gives each path's new mode, ``--no-renames`` reports a rename as
    the added path, and ``--diff-filter=d`` keeps every status but deletion,
    type changes included. ``revisions`` is ``("--cached",)`` for what is
    staged, or a base and ``HEAD`` for a pull request.
    """
    result = _git(
        repo, "diff", *revisions, "--raw", "-z", "--no-renames", "--diff-filter=d"
    )
    if result.returncode != 0:
        raise GuardError(result.stderr.decode().strip() or "git diff failed")
    fields = result.stdout.decode("utf-8", "surrogateescape").split("\0")
    changed = []
    # Each record is ":old_mode new_mode old_sha new_sha status" NUL path NUL.
    for header, path in zip(fields[0::2], fields[1::2], strict=False):
        parts = header.split()
        if len(parts) >= 2:
            changed.append((path, parts[1]))
    return changed


def _check_changed(
    repo: Path,
    changed: list[tuple[str, str]],
    local: KeywordTable,
    *,
    content_revision: str,
    stored_revision: str,
    attribute_commits: tuple[str, ...] = (),
) -> tuple[int, list[Finding]]:
    """Check source files and ``.legesher`` entries among ``changed``.

    Content is read at ``content_revision`` (``:0`` for the index, or
    ``HEAD``); each file's block language is judged against its version at
    ``stored_revision``. A path is a source file when ``.gitattributes``
    gives it the Legesher filter at any of ``attribute_commits`` (the base and
    the head of a pull request, so a pull request cannot unmark its own
    file), or, when none are given, in the index or the working tree.
    """
    candidates = [
        path
        for path, mode in changed
        if mode in REGULAR_FILE_MODES or mode == SYMLINK_MODE
    ]
    marked: set[str] = set()
    if attribute_commits:
        for commit in attribute_commits:
            marked |= set(_legesher_paths_at(repo, commit, candidates))
    else:
        # The commit carries the staged attributes, but right after setup the
        # .gitattributes file is not staged yet and the clean filter reads the
        # working tree's. Either one marking a path makes it Legesher's, so an
        # unstaged edit cannot exempt a file and an unstaged file still counts.
        marked |= set(_legesher_paths(repo, candidates, cached=True))
        marked |= set(_legesher_paths(repo, candidates, cached=False))
    sources = [
        (path, mode)
        for path, mode in changed
        if path in marked and not is_legesher_path(path)
    ]
    artifacts = [(path, mode) for path, mode in changed if is_legesher_path(path)]

    findings: list[Finding] = []
    for path, mode in sources:
        if mode == SYMLINK_MODE:
            # Following links cannot be made complete (chains, directory
            # links, a change to the target alone), so a Legesher-marked
            # symlink is refused; its blob, the target's name, is never read.
            findings.append(Finding(path, 1, 1, "artifact", _SYMLINK_SOURCE))
            continue
        data = _blob_bytes(repo, f"{content_revision}:{path}")
        if data is None:
            raise GuardError(f"cannot read {path} at {content_revision}")
        stored = _blob(repo, f"{stored_revision}:{path}")
        findings.extend(check_blob(data, path=path, local=local, stored=stored))
    for path, mode in artifacts:
        # Only the formats the open toolchain owns are loaded; anything else
        # (the map engine's files included) is judged by its mode alone.
        data = b""
        if mode in REGULAR_FILE_MODES and is_known_artifact(path):
            data = _blob_bytes(repo, f"{content_revision}:{path}") or b""
        findings.extend(check_artifact(path, data, mode=mode))
    return len(sources) + len(artifacts), findings


_SYMLINK_SOURCE = (
    "a symlink marked for Legesher: the guard cannot check what it points to, "
    "so replace it with the file"
)


def _tree_links(repo: Path, commit: str) -> list[tuple[str, str]]:
    """Every symlink and submodule in ``commit``'s tree, with its mode."""
    listing = _git(repo, "ls-tree", "-r", "-z", commit)
    if listing.returncode != 0:
        raise GuardError(listing.stderr.decode().strip() or "git ls-tree failed")
    links = []
    for record in listing.stdout.decode("utf-8", "surrogateescape").split("\0"):
        meta, _, path = record.partition("\t")
        mode = meta.split(" ", 1)[0]
        if mode in (SYMLINK_MODE, GITLINK_MODE):
            links.append((path, mode))
    return links


def _check_tree_links(
    repo: Path, commit: str, attribute_commits: tuple[str, ...], reported: set[str]
) -> list[Finding]:
    """Refuse the links in ``commit``'s tree that a change elsewhere can use.

    A link the change did not touch still resolves to whatever its target now
    holds: under ``.legesher/`` it can carry a recorded path outside the
    repository, and marked for Legesher it runs code the guard never read.
    Paths in ``reported`` already have an artifact finding and are skipped.
    """
    links = _tree_links(repo, commit)
    findings = []
    for path, mode in links:
        if is_legesher_path(path) and path not in reported:
            findings.extend(check_artifact(path, b"", mode=mode))
    symlinks = [
        path
        for path, mode in links
        if mode == SYMLINK_MODE and not is_legesher_path(path)
    ]
    marked: set[str] = set()
    for attributes in attribute_commits:
        marked |= set(_legesher_paths_at(repo, attributes, symlinks))
    for path in sorted(marked - reported):
        findings.append(Finding(path, 1, 1, "artifact", _SYMLINK_SOURCE))
    return findings


def _language_at(repo: Path, commit: str) -> str | None:
    """The ``language`` a commit's own ``.legesher/config.yml`` names."""
    import yaml

    data = _blob(repo, f"{commit}:.legesher/config.yml")
    if data is None:
        return None
    try:
        config = yaml.safe_load(data)
    except (yaml.YAMLError, RecursionError):
        return None
    language = config.get("language") if isinstance(config, dict) else None
    return language if isinstance(language, str) else None


def _language(
    repo: Path | None, language: str | None, base: str | None = None
) -> KeywordTable:
    if language is None and repo is not None and base is not None:
        # A pull request is judged by the language its base declares, English
        # when it declares none (the configuration's default), and never by
        # its own configuration, so it cannot choose a laxer one for itself.
        language = _language_at(repo, base) or "en"
    if language is None:
        from legesher.config import LegesherConfig

        language = LegesherConfig.load(repo).language
    try:
        return keyword_table(language)
    except Exception as exc:
        raise GuardError(f"cannot load the '{language}' language pack: {exc}") from exc


def check_staged(repo: Path, local: KeywordTable) -> tuple[int, list[Finding]]:
    """``(files checked, findings)`` for what is staged: the pre-commit hook."""
    return _check_changed(
        repo,
        _changed(repo, "--cached"),
        local,
        content_revision=":0",
        stored_revision="HEAD",
    )


def check_diff(repo: Path, local: KeywordTable, base: str) -> tuple[int, list[Finding]]:
    """``(files checked, findings)`` for what changed from ``base`` to ``HEAD``.

    The pull-request check (CORE-1323). Only the changed files are read, at
    ``HEAD``, and each is judged against its version at ``base``. The diff is
    between the two trees, so with the pull request's merge commit checked
    out it is exactly the pull request, and ``base`` needs no history beyond
    its own commit. Links are the exception to reading only what changed: every
    symlink and submodule in ``HEAD``'s tree is listed (never read), and a
    marked symlink or any link under ``.legesher/`` is refused, changed or not.
    """
    resolved = _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    if resolved.returncode != 0:
        raise GuardError(f"{base!r} is not a commit in this repository")
    base_commit = resolved.stdout.decode().strip()
    changed = _changed(repo, base_commit, "HEAD")
    checked, findings = _check_changed(
        repo,
        changed,
        local,
        content_revision="HEAD",
        stored_revision=base_commit,
        attribute_commits=(base_commit, "HEAD"),
    )
    reported = {finding.path for finding in findings if finding.check == "artifact"}
    findings.extend(_check_tree_links(repo, "HEAD", (base_commit, "HEAD"), reported))
    return checked, findings


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


def _escape_data(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")


def github_annotation(finding: Finding) -> str:
    """A finding as a GitHub Actions ``::error`` workflow command."""
    properties = ",".join(
        [
            f"file={_escape_property(finding.path)}",
            f"line={finding.line}",
            f"col={finding.column}",
            f"title={_escape_property(f'legesher guard ({finding.check})')}",
        ]
    )
    return f"::error {properties}::{_escape_data(finding.message)}"


@click.command(name="guard")
@click.option(
    "--staged",
    is_flag=True,
    help="Check the Legesher files staged for commit (the default without PATHS).",
)
@click.option(
    "--diff",
    "base",
    default=None,
    metavar="BASE",
    help="Check only what changed from BASE to HEAD (the pull-request check).",
)
@click.option(
    "--language",
    "-l",
    default=None,
    help=(
        "Language this repository is written in (default: from config; with "
        "--diff, the base's config, or English when it names none)."
    ),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "github"]),
    default="text",
    show_default=True,
    help="github prints each finding as a workflow annotation.",
)
@click.argument("paths", nargs=-1, type=click.Path(exists=True, dir_okay=False))
def guard(
    staged: bool,
    base: str | None,
    language: str | None,
    output_format: str,
    paths: tuple[str, ...],
) -> None:
    """Refuse Trojan Source characters and keywords out of their stored form.

    \b
    Checks:
      encoding  content that is not UTF-8, or a coding declaration other
                than UTF-8
      unicode   bidi controls, invisible characters in code, tatweel, and
                identifier characters outside every supported script
      keyword   a keyword not in its block's stored form (the clean filter
                normalizes these; a finding means the file skipped it)
      artifact  a symlink marked for Legesher, or a file under .legesher/
                that is not a regular file, does not match its format, or
                records a path outside the repository

    \b
    Examples:
        $ legesher guard --staged        # what the pre-commit hook runs
        $ legesher guard --diff origin/main   # what the pull-request check runs
        $ legesher guard src/module.py
    """
    try:
        repo = _repo_root()
        if base is not None:
            if staged or paths:
                raise GuardError("--diff checks a range; it takes no --staged or PATHS")
            if repo is None:
                raise GuardError("not in a git repository")
            checked, findings = check_diff(repo, _language(repo, language, base), base)
        elif staged or not paths:
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
        if output_format == "github":
            click.echo(github_annotation(finding))
        else:
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
            "Keyword findings mean the file skipped the Legesher filter (staged or "
            "committed where it is not set up). Run `legesher git setup`, then "
            "`git add --renormalize <path>`."
        )
    if any(finding.check == "artifact" for finding in findings):
        click.echo(
            "Artifact findings: files marked for Legesher, and files under "
            ".legesher/, must be regular files; those under .legesher/ must be in "
            "their own format and never point outside the repository."
        )
    if any(finding.check == "unicode" for finding in findings):
        click.echo(
            "Unicode findings are characters that can make code read differently "
            "than it runs. Remove them; there is no override."
        )
    sys.exit(1)


__all__ = ["guard", "check_diff", "check_staged", "check_files", "github_annotation"]
