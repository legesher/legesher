"""The markdown review template's hidden metadata line and the review-pin check.

A review template (the generated ``REFERENCE.md`` of one pack) opens with one
HTML comment that pins what the reviewer saw::

    <!-- legesher-review-template format=1 pack=legesher-i18n-python-si
         pack_version=0.0.3 python=3.14 code=si bcp47=si digest=0123456789ab -->

Three callers share this module so the line has one definition:

* ``scripts/generate_reference_docs.py`` stamps the line
  (:func:`render_metadata_line`);
* the future markdown parser reads it back (:func:`parse_metadata_line`) and
  turns it into the bundle's ``kit_version`` (:attr:`TemplateMetadata.kit_version`)
  and ``locale`` (the ``bcp47`` field);
* the pull-request check on a review file refuses a pin that names a pack
  version, Python version or locale that does not exist
  (:func:`check_review_pin`).

The check is pure: the caller supplies the sets of known versions. In the
monorepo :func:`known_pack_versions` derives them from a pack directory
(``pyproject.toml`` plus the stamped ``CHANGELOG.md`` headings); a check that
runs where no pack tree exists supplies them from whatever index it has.

File placement follows the registry's BCP 47 tag (:func:`review_folder`,
:func:`review_file_name`): ``reviews/<bcp47>/<bcp47>-<github-username>.md``
for the first review of a pack version and ``<bcp47>-<github-username>-<pack-version>.md``
for a review after a version bump.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

#: Bumped only on a deliberate change to the template's shape. Every template
#: regenerates on a bump; nothing else touches more than one pack's template.
FORMAT_VERSION = 1

METADATA_PREFIX = "legesher-review-template"

_FIELDS = ("format", "pack", "pack_version", "python", "code", "bcp47", "digest")
_LINE_RE = re.compile(
    rf"^<!--\s*{re.escape(METADATA_PREFIX)}\s+(?P<body>.*?)\s*-->\s*$"
)
_PAIR_RE = re.compile(r"(?P<key>[a-z_0-9]+)=(?P<value>\S+)")
_CHANGELOG_VERSION_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\]", re.MULTILINE)


def code_span(value: str) -> str:
    """*value* as one inert markdown code span, whatever it contains.

    Reviewer text reaches reports that may be posted on a pull request. Inside a
    code span GitHub renders no image, link or @-mention, so every value a
    reviewer controls goes through here: the fence is one backtick longer than
    the longest run inside, and line breaks become spaces.
    """
    flat = " ".join(value.splitlines())
    runs = [len(run) for run in re.findall(r"`+", flat)]
    fence = "`" * (max(runs, default=0) + 1)
    pad = " " if flat.startswith("`") or flat.endswith("`") or not flat else ""
    return f"{fence}{pad}{flat}{pad}{fence}"


class ReviewTemplateError(ValueError):
    """A template or review file whose metadata line cannot be trusted."""


@dataclass(frozen=True)
class TemplateMetadata:
    """The values stamped on a template's first line."""

    format: int
    pack: str
    pack_version: str
    python: str
    code: str
    bcp47: str
    digest: str

    @property
    def kit_version(self) -> str:
        """The bundle's ``kit_version`` for a review made from this template."""
        return f"reference-md/{self.pack}@{self.pack_version}+py{self.python}#{self.digest}"


def render_metadata_line(meta: TemplateMetadata) -> str:
    """The HTML comment that opens a template, without a trailing newline."""
    pairs = " ".join(f"{name}={getattr(meta, name)}" for name in _FIELDS)
    return f"<!-- {METADATA_PREFIX} {pairs} -->"


def parse_metadata_line(text: str) -> TemplateMetadata:
    """Read the metadata line from the first line of *text*.

    Raises:
        ReviewTemplateError: when the first line is not a metadata line, a
            field is missing, or the format version is one this code does not
            read. The message names the offender.
    """
    first_line = text.lstrip("\ufeff").split("\n", 1)[0]
    match = _LINE_RE.match(first_line)
    if match is None:
        raise ReviewTemplateError(
            f"the first line is not a {METADATA_PREFIX} metadata line: {code_span(first_line)}"
        )
    pairs = [
        (m.group("key"), m.group("value"))
        for m in _PAIR_RE.finditer(match.group("body"))
    ]
    keys = [key for key, _ in pairs]
    duplicated = sorted({key for key in keys if keys.count(key) > 1})
    if duplicated:
        raise ReviewTemplateError(
            f"metadata line repeats {', '.join(duplicated)}: {code_span(first_line)}"
        )
    values = dict(pairs)
    missing = [name for name in _FIELDS if name not in values]
    if missing:
        raise ReviewTemplateError(
            f"metadata line is missing {', '.join(missing)}: {code_span(first_line)}"
        )
    if values["format"] != str(FORMAT_VERSION):
        raise ReviewTemplateError(
            f"metadata line says format={values['format']}; this code reads format={FORMAT_VERSION}"
        )
    return TemplateMetadata(
        format=FORMAT_VERSION,
        pack=values["pack"],
        pack_version=values["pack_version"],
        python=values["python"],
        code=values["code"],
        bcp47=values["bcp47"],
        digest=values["digest"],
    )


_PYPROJECT_VERSION_RE = re.compile(
    r'^\+version = "(?P<version>\d+\.\d+\.\d+)"', re.MULTILINE
)


def known_pack_versions(pack_root: Path, *, use_git: bool = True) -> set[str]:
    """Every version a pack has carried.

    Three sources, unioned: the current ``pyproject.toml``; the stamped
    ``CHANGELOG.md`` headings (``## [0.0.2] - 2026-04-29``); and, when
    *use_git* is true and the pack sits in a git checkout, every ``version =``
    line ever added to its ``pyproject.toml``. The git source matters because
    the changelog stamp is not tied to the bump: a pack can sit at 0.0.3 with
    only 0.0.2 and 0.0.1 stamped. No release tag exists yet for any pack.
    """
    versions: set[str] = set()
    pyproject = pack_root / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
        version = data.get("project", {}).get("version")
        if isinstance(version, str):
            versions.add(version)
    changelog = pack_root / "CHANGELOG.md"
    if changelog.is_file():
        versions.update(
            m.group("version")
            for m in _CHANGELOG_VERSION_RE.finditer(
                changelog.read_text(encoding="utf-8")
            )
        )
    if use_git and pyproject.is_file():
        versions.update(_versions_from_git(pyproject))
    return versions


def _versions_from_git(pyproject: Path) -> set[str]:
    """``version =`` values ever added to *pyproject* per git; empty outside a checkout."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(pyproject.parent),
                "log",
                "--format=",
                "-p",
                "--",
                pyproject.name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if result.returncode != 0:
        return set()
    return {m.group("version") for m in _PYPROJECT_VERSION_RE.finditer(result.stdout)}


def known_pins_from_template(
    template: Path, *, use_git: bool = True
) -> tuple[set[str], set[str]]:
    """``(pack versions, Python versions)`` a published template has ever pinned.

    The index a check uses where no pack tree exists (language-packs, which
    holds only ``reference/<tag>.md``): the template's own metadata line, plus,
    when *use_git* is true, every metadata line git history ever added to it.
    A review pinning a version that no published template carried is refused.
    """
    versions: set[str] = set()
    pythons: set[str] = set()
    lines = [template.read_text(encoding="utf-8").split("\n", 1)[0]]
    if use_git:
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(template.parent),
                    "log",
                    "--format=",
                    "-p",
                    "--",
                    template.name,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            result = None
        if result is not None and result.returncode == 0:
            lines += [
                line[1:]
                for line in result.stdout.splitlines()
                if line.startswith("+<!--")
            ]
    for line in lines:
        try:
            meta = parse_metadata_line(line)
        except ReviewTemplateError:
            continue
        versions.add(meta.pack_version)
        pythons.add(meta.python)
    return versions, pythons


def templates_at(repo: Path, ref: str, path: str) -> list[str]:
    """Every version of the template at *path* reachable from *ref*, newest first.

    The trusted source for a pull-request check: read from the BASE ref, never
    from the pull request's own checkout, so a pull request that also edits
    ``reference/<tag>.md`` cannot vouch for its own review. The full list lets a
    review pinned before a version bump be read against the template it was
    copied from (match it by the metadata line).

    *path* is taken literally (``--literal-pathspecs``): it is built from a
    review's own metadata, so a ``?`` or ``*`` in it must never glob.

    Raises:
        ReviewTemplateError: when git cannot read *path* at *ref*, *ref* is not a
            ref, or a version is not UTF-8.
    """
    if not ref or ref.startswith("-"):
        raise ReviewTemplateError(f"{code_span(ref)} is not a git ref")

    def git(*args: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", "--literal-pathspecs", "-C", str(repo), *args],
                capture_output=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ReviewTemplateError(
                f"git could not run in {repo}: {error}"
            ) from error
        if result.returncode != 0:
            raise ReviewTemplateError(
                f"git {' '.join(args[:2])} failed in {repo}: "
                f"{result.stderr.decode('utf-8', 'replace').strip()}"
            )
        return result.stdout

    commits = git("log", "--format=%H", ref, "--", path).decode("ascii").split()
    if not commits:
        raise ReviewTemplateError(
            f"{code_span(path)} has no history at {code_span(ref)}"
        )
    texts: list[str] = []
    for commit in commits:
        try:
            texts.append(git("show", f"{commit}:{path}").decode("utf-8"))
        except UnicodeDecodeError as error:
            raise ReviewTemplateError(
                f"{path} at {commit} is not UTF-8: {error}"
            ) from error
    return texts


def check_review_pin(
    meta: TemplateMetadata,
    *,
    known_versions: Collection[str],
    python_versions: Collection[str],
    registry_entry: Mapping[str, object] | None,
) -> list[str]:
    """Problems with a review's pin, empty when the pin names things that exist.

    Args:
        meta: the parsed metadata line of the review file.
        known_versions: every pack version that has existed for ``meta.pack``.
        python_versions: the Python versions the pack has a version file for.
        registry_entry: the registry entry for ``meta.code``, or ``None`` when
            the registry has no such language.
    """
    problems: list[str] = []
    if meta.pack_version not in known_versions:
        problems.append(
            f"{code_span(meta.pack)} has no version {code_span(meta.pack_version)} "
            f"(known: {', '.join(sorted(known_versions)) or 'none'})"
        )
    if meta.python not in python_versions:
        problems.append(
            f"{code_span(meta.pack)} has no Python {code_span(meta.python)} version file "
            f"(has: {', '.join(sorted(python_versions)) or 'none'})"
        )
    if registry_entry is None:
        problems.append(f"code {code_span(meta.code)} is not in the language registry")
    elif registry_entry.get("bcp47") != meta.bcp47:
        problems.append(
            f"bcp47 {code_span(meta.bcp47)} disagrees with the registry's "
            f"{registry_entry.get('bcp47')} for code {code_span(meta.code)}"
        )
    return problems


def review_folder(code: str, bcp47: str) -> str:
    """The ``reviews/<folder>`` name for a language: its BCP 47 tag.

    The bundle's ``locale`` is BCP 47 and a dialect pack's tag (``es-MX``) is
    already a folder name, so the folder is the tag, never the pack ``code``.
    ``code`` is accepted so a caller holding both never has to pick.
    """
    del code
    return bcp47


def review_file_name(
    folder: str, github_username: str, pack_version: str | None = None
) -> str:
    """``<folder>-<username>.md``, or ``<folder>-<username>-<pack_version>.md`` after a bump."""
    if pack_version is None:
        return f"{folder}-{github_username}.md"
    return f"{folder}-{github_username}-{pack_version}.md"
