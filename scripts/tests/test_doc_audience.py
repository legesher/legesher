"""Every Markdown document names who it is for.

``CONTRIBUTING.md``, under "Who each document is for", gives each audience
one fixed line. A document carries its main reader's line as the first thing
under its title, and a section written for a different reader carries that
reader's line as the first thing under its heading. This module reads the
lines from that table, lists every tracked Markdown file, and fails, naming
the file and the line, when a document in scope has no line under its title,
carries a line that is not in the table, or puts one anywhere but directly
under a heading.

The files that carry no line are matched by ``OUT_OF_SCOPE``, one pattern per
rule with its reason. A rule that no longer matches a tracked file fails as
well, so the exclusions cannot outlive the files they were written for.
"""

from __future__ import annotations

import functools
import re
import subprocess
from pathlib import Path

import pytest

LABEL_PREFIX = "> **Audience:** "
VOCABULARY_FILE = "CONTRIBUTING.md"
VOCABULARY_HEADING = "Who each document is for"
#: markdownlint's MD013 limit for prose lines in this repository.
MAX_LINE = 120

#: ``(pattern, reason)``. Each pattern must match the whole repository-relative
#: POSIX path of a tracked Markdown file.
OUT_OF_SCOPE: tuple[tuple[str, str], ...] = (
    (r"(?:.*/)?CHANGELOG\.md", "release history, stamped by the release trains"),
    (r"libs/i18n/language-packs/.*", "language pack files, written by the exporter and its scripts"),
    (r"docs/src/content/.*", "documentation site pages: user documentation, in three languages"),
    (r"libs/i18n/context/[^/]+/(?!README\.md$)[^/]+\.md", "translation briefs, read by the generation pipeline"),
    (r"(?:.*/)?CLAUDE\.md", "written for coding agents"),
    (r"\.claude/agents/[^/]+\.md", "agent definitions, written for coding agents"),
    (r"libs/mcp/skills/[^/]+/SKILL\.md", "a skill for coding agents in users' repositories"),
    (r"\.github/PULL_REQUEST_TEMPLATE\.md", "copied by GitHub into every new pull request"),
    (r"\.github/pull_request_template/[^/]+\.md", "pull request templates"),
    (r"libs/mcp/templates/AGENTS-template\.md", "copied into users' repositories as AGENTS.md"),
    (r"scripts/translate/test-results/RESPONSE_TEMPLATE\.md", "a form for recording a model's answer"),
    (r"libs/vs-code/images/walkthrough/[^/]+\.md", "pages of the walkthrough inside VS Code"),
    (r"libs/i18n/spec/targets/[^/]+/GUIDE\.md", "rendered verbatim into generation prompts"),
    (r"scripts/translate/prompts/[^/]+-translation-prompt\.md", "prompt text pasted into a model"),
    (r"scripts/translate/test-cases/[^/]+\.md", "pasted whole into a model"),
    (r"CONTRIBUTORS\.md", "written by the all-contributors bot"),
    (r"CODE_OF_CONDUCT\.md", "a community health file, for everyone who takes part"),
    (r"LICENSING\.md", "a community health file, for everyone who takes part"),
    (r"\.github/SECURITY\.md", "a community health file, for everyone who takes part"),
)

HEADING = re.compile(r"#{1,6}(?:[ \t]|$)")
FENCE = re.compile(r"\s*(`{3,}|~{3,})")
#: Wider than ``LABEL_PREFIX`` on purpose, so a misspelt label is reported as
#: one rather than read as an ordinary blockquote.
LABEL_LIKE = re.compile(r"\s*>\s*(?:\*\*|__)?\s*audience\b", re.IGNORECASE)


def _repo_root() -> Path:
    """The work tree containing this file; skips the module outside git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        proc = None
    if proc is None or proc.returncode != 0:
        pytest.skip(
            "the audience guard needs a git work tree: `git rev-parse --show-toplevel`"
            " failed from the test directory",
            allow_module_level=True,
        )
    return Path(proc.stdout.strip())


REPO: Path = _repo_root()


def _tracked_markdown() -> tuple[str, ...]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z", "--", "*.md", "*.mdx"],
        capture_output=True,
        check=True,
    ).stdout
    return tuple(sorted(p.decode("utf-8") for p in out.split(b"\0") if p))


TRACKED = _tracked_markdown()
RULES = tuple((re.compile(pattern), reason) for pattern, reason in OUT_OF_SCOPE)
IN_SCOPE = tuple(p for p in TRACKED if not any(rule.fullmatch(p) for rule, _ in RULES))


def outside_fences(text: str) -> list[tuple[int, str]]:
    """``(line number, line)`` for every line outside a fenced code block."""
    kept: list[tuple[int, str]] = []
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        marker = FENCE.match(line)
        if fence:
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
                and not line[marker.end() :].strip()
            ):
                fence = ""
            continue
        if marker:
            fence = marker.group(1)
            continue
        kept.append((number, line))
    return kept


def audience_problems(text: str, lines: frozenset[str]) -> list[str]:
    """What is wrong with ``text``'s audience lines, given the allowed ``lines``."""
    content = outside_fences(text)
    title = next((i for i, (_, line) in enumerate(content) if line.startswith("# ")), None)
    if title is None:
        return ["no level-one title (a '# ' line) to put the audience line under"]
    problems: list[str] = []
    under_title = next((line for _, line in content[title + 1 :] if line.strip()), "")
    if not LABEL_LIKE.match(under_title):
        problems.append("no audience line directly under the title")
    previous = ""
    for number, line in content:
        if LABEL_LIKE.match(line):
            if line.rstrip() not in lines:
                problems.append(f"line {number}: {line.strip()!r} is not one of the audience lines")
            if not HEADING.match(previous):
                problems.append(f"line {number}: an audience line belongs directly under a heading")
        if line.strip():
            previous = line
    return problems


@functools.lru_cache(maxsize=None)
def vocabulary() -> dict[str, str]:
    """``{audience: line}`` from the table under the vocabulary heading."""
    content = outside_fences((REPO / VOCABULARY_FILE).read_text(encoding="utf-8"))
    start = next(
        (
            i
            for i, (_, line) in enumerate(content)
            if HEADING.match(line) and line.lstrip("#").strip() == VOCABULARY_HEADING
        ),
        None,
    )
    assert start is not None, f"{VOCABULARY_FILE} has no '{VOCABULARY_HEADING}' heading"
    level = len(content[start][1]) - len(content[start][1].lstrip("#"))
    found: dict[str, str] = {}
    for _, line in content[start + 1 :]:
        if HEADING.match(line) and len(line) - len(line.lstrip("#")) <= level:
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and len(cells) >= 2:
            code = cells[1]
            if code.startswith("`" + LABEL_PREFIX) and code.endswith("`"):
                found[cells[0]] = code[1:-1]
    assert found, (
        f"{VOCABULARY_FILE}, '{VOCABULARY_HEADING}': no table row gives an audience and its"
        f" line as a code span starting with {LABEL_PREFIX!r}"
    )
    return found


# The guard's own rules, on documents written here.

LINES = frozenset(
    {
        "> **Audience:** Readers, who read.",
        "> **Audience:** Writers, who write.",
    }
)


def test_a_document_with_its_line_under_the_title_passes() -> None:
    doc = "# Title\n\n> **Audience:** Readers, who read.\n\nBody.\n"
    assert audience_problems(doc, LINES) == []


def test_a_document_without_a_line_fails() -> None:
    doc = "# Title\n\nBody.\n"
    assert len(audience_problems(doc, LINES)) == 1


def test_a_line_naming_an_audience_outside_the_table_fails_on_its_line() -> None:
    doc = "# Title\n\n> **Audience:** Everyone, who reads.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 3:")


def test_a_misspelt_line_is_reported_once_not_read_as_a_quote() -> None:
    doc = "# Title\n\n> **Audience**: Readers, who read.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 3:")


def test_a_section_line_directly_under_its_heading_passes() -> None:
    doc = (
        "# Title\n\n> **Audience:** Readers, who read.\n\n"
        "## Writing\n\n> **Audience:** Writers, who write.\n\nHow to write.\n"
    )
    assert audience_problems(doc, LINES) == []


def test_a_line_in_the_middle_of_a_section_fails_on_its_line() -> None:
    doc = "# Title\n\n> **Audience:** Readers, who read.\n\nA paragraph.\n\n> **Audience:** Writers, who write.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 7:")


def test_the_line_may_open_a_longer_blockquote() -> None:
    doc = "# Title\n\n> **Audience:** Readers, who read.\n>\n> A second paragraph of the same quote.\n"
    assert audience_problems(doc, LINES) == []


def test_headings_and_lines_inside_code_fences_are_not_read() -> None:
    doc = (
        "```markdown\n# Not the title\n\n> **Audience:** Nobody, ignored.\n```\n\n"
        "# Title\n\n> **Audience:** Readers, who read.\n\n"
        "~~~~\n> **Audience:** Nobody, ignored.\n~~~\n~~~~\n"
    )
    assert audience_problems(doc, LINES) == []


def test_a_document_with_no_level_one_title_fails() -> None:
    doc = "## Only a section\n\n> **Audience:** Readers, who read.\n"
    assert len(audience_problems(doc, LINES)) == 1


def test_a_title_in_a_combining_mark_script_is_found() -> None:
    doc = "# מַדְרִיךְ · मार्गदर्शिका\n\n> **Audience:** Readers, who read.\n"
    assert audience_problems(doc, LINES) == []


# The repository.


def test_contributing_gives_one_line_per_audience() -> None:
    table = vocabulary()
    assert len(set(table.values())) == len(table), f"two audiences share a line: {table}"
    for name, line in table.items():
        assert line.startswith(f"{LABEL_PREFIX}{name}"), f"{name!r}: its line does not name it: {line!r}"
        assert len(line) <= MAX_LINE, f"{name!r}: its line is {len(line)} characters; the limit is {MAX_LINE}"


@pytest.mark.parametrize(("pattern", "reason"), OUT_OF_SCOPE, ids=[p for p, _ in OUT_OF_SCOPE])
def test_each_exclusion_still_matches_a_tracked_file(pattern: str, reason: str) -> None:
    rule = re.compile(pattern)
    assert any(rule.fullmatch(p) for p in TRACKED), (
        f"OUT_OF_SCOPE rule {pattern!r} ({reason}) matches no tracked Markdown file; remove it"
    )


@pytest.mark.parametrize("doc", IN_SCOPE)
def test_document_names_its_audience(doc: str) -> None:
    path = REPO / doc
    if not path.is_file():
        pytest.skip(f"{doc} is deleted in the work tree")
    problems = audience_problems(path.read_text(encoding="utf-8"), frozenset(vocabulary().values()))
    assert not problems, (
        f"{doc}:\n  "
        + "\n  ".join(problems)
        + f"\n  The lines are in {VOCABULARY_FILE}, '{VOCABULARY_HEADING}'."
    )
