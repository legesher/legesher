"""Every Markdown document names who it is for.

``CONTRIBUTING.md``, under "Who each document is for", gives each audience
one fixed line. A document carries its main reader's line as the first thing
under its title, and a section written for a different reader carries that
reader's line as the first thing under its heading. This module reads the
lines from that table, lists every tracked Markdown file, and fails, naming
the file and the line, when a document in scope:

- has no line directly under its title;
- carries an audience statement that is not exactly a line from the table,
  in any common shape (quoted or not, bold or italic, "Audience" or
  "Audiences" followed by a colon);
- puts a line anywhere but directly under a heading, a code block, an HTML
  comment or front matter in between counting as something else;
- runs the next paragraph into the line instead of leaving a blank line or a
  bare ``>`` line after it.

The files that carry no line are matched by ``OUT_OF_SCOPE``, one pattern per
rule with its reason, and the translation briefs are the files each
``libs/i18n/context/*/index.json`` lists. A rule that no longer matches a
tracked file fails as well, so the exclusions cannot outlive the files they
were written for.
"""

from __future__ import annotations

import functools
import json
import re
import subprocess
from pathlib import Path

import pytest

LABEL_PREFIX = "> **Audience:** "
VOCABULARY_FILE = "CONTRIBUTING.md"
VOCABULARY_HEADING = "Who each document is for"
#: markdownlint's MD013 limit for prose lines in this repository.
MAX_LINE = 120
CONTEXT_INDEXES = "libs/i18n/context/*/index.json"

#: ``(pattern, reason)``. Each pattern must match the whole repository-relative
#: POSIX path of a tracked Markdown file.
OUT_OF_SCOPE: tuple[tuple[str, str], ...] = (
    (r"(?:.*/)?CHANGELOG\.md", "release history, stamped by the release trains"),
    (r"libs/i18n/language-packs/[^/]+/[^/]+/.+", "files of a language pack, written by the exporter and its scripts"),
    (r"docs/src/content/.*", "documentation site pages: user documentation, in three languages"),
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
    (r"CONTRIBUTORS\.md", "the contributor credits list, whose table the all-contributors bot keeps"),
    (r"CODE_OF_CONDUCT\.md", "a community or policy page, for everyone"),
    (r"LICENSING\.md", "a community or policy page, for everyone"),
    (r"\.github/SECURITY\.md", "a community or policy page, for everyone"),
)

TITLE = re.compile(r" {0,3}#[ \t]+\S")
HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)")
FENCE = re.compile(r"([ \t]*)(`{3,}|~{3,})")
#: Any line that states an audience, quoted or not, bold or italic, singular or
#: plural, so that one which is not exactly a line from the table is reported
#: rather than read as prose. The colon keeps sentences that merely start with
#: the word out.
LABEL_LIKE = re.compile(r" {0,3}(?:>[ \t]*)*[*_]{0,3}[ \t]*audiences?[ \t]*[*_]{0,3}[ \t]*:", re.IGNORECASE)
#: Stands in for a fenced code block, an HTML comment or front matter, so that
#: nothing counts as directly under a heading across one.
BLOCK = "<block>"


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


def _indexed_briefs() -> frozenset[str]:
    """The translation briefs, as each context folder's ``index.json`` lists them."""
    briefs: set[str] = set()
    for index in sorted(REPO.glob(CONTEXT_INDEXES)):
        folder = index.parent.relative_to(REPO).as_posix()
        for document in json.loads(index.read_text(encoding="utf-8"))["documents"]:
            briefs.add(f"{folder}/{document['filename']}")
    return frozenset(briefs)


TRACKED = _tracked_markdown()
BRIEFS = _indexed_briefs()
RULES = tuple((re.compile(pattern), reason) for pattern, reason in OUT_OF_SCOPE)
IN_SCOPE = tuple(
    p for p in TRACKED if p not in BRIEFS and not any(rule.fullmatch(p) for rule, _ in RULES)
)


def content_lines(text: str) -> list[tuple[int, str]]:
    """``(line number, line)`` for each line, as a reader of the rendered page meets it.

    Each fenced code block, HTML comment and leading front-matter block becomes one
    ``BLOCK`` placeholder at its first line. A fence opened inside a list item also
    ends where the item does, at the first non-blank line indented less than the
    fence. Lines are split on newlines only, so a Unicode line separator stays inside
    its line, as it does on the page; a byte-order mark and carriage returns go.
    """
    kept: list[tuple[int, str]] = []
    fence, fence_indent, comment, front = "", 0, False, False
    for number, raw in enumerate(text.removeprefix("﻿").split("\n"), start=1):
        line = raw.removesuffix("\r")
        if number == 1 and line.strip() == "---":
            front = True
            kept.append((number, BLOCK))
            continue
        if front:
            front = line.strip() not in ("---", "...")
            continue
        if comment:
            comment = "-->" not in line
            continue
        marker = FENCE.match(line)
        if fence:
            if (
                marker
                and marker.group(2)[0] == fence[0]
                and len(marker.group(2)) >= len(fence)
                and not line[marker.end() :].strip()
            ):
                fence = ""
                continue
            if not line.strip() or len(line) - len(line.lstrip()) >= fence_indent:
                continue
            fence = ""
        if marker:
            fence, fence_indent = marker.group(2), len(marker.group(1))
            kept.append((number, BLOCK))
            continue
        if line.lstrip().startswith("<!--"):
            comment = "-->" not in line
            kept.append((number, BLOCK))
            continue
        kept.append((number, line))
    return kept


def _level(heading: str) -> int:
    stripped = heading.lstrip(" ")
    return len(stripped) - len(stripped.lstrip("#"))


def audience_problems(text: str, lines: frozenset[str]) -> list[str]:
    """What is wrong with ``text``'s audience lines, given the allowed ``lines``."""
    content = content_lines(text)
    title = next((i for i, (_, line) in enumerate(content) if TITLE.match(line)), None)
    if title is None:
        return ["no level-one title (a '# Title' line) to put the audience line under"]
    problems: list[str] = []
    under_title = next((line for _, line in content[title + 1 :] if line.strip()), "")
    if not LABEL_LIKE.match(under_title):
        problems.append(f"line {content[title][0]}: no audience line directly under the title")
    previous = ""
    for index, (number, line) in enumerate(content):
        if LABEL_LIKE.match(line):
            if line.rstrip() not in lines:
                problems.append(f"line {number}: {line.strip()!r} is not one of the audience lines")
            if not HEADING.match(previous):
                problems.append(f"line {number}: an audience line belongs directly under a heading")
            following = content[index + 1][1].strip() if index + 1 < len(content) else ""
            if following not in ("", ">"):
                problems.append(
                    f"line {number}: the next line runs into the audience line;"
                    " leave a blank line or a bare '>' line after it"
                )
        if line.strip():
            previous = line
    return problems


def parse_vocabulary(text: str) -> dict[str, str]:
    """``{audience: line}`` from the table under the vocabulary heading in ``text``."""
    content = content_lines(text)
    start = next(
        (
            i
            for i, (_, line) in enumerate(content)
            if HEADING.match(line) and line.strip().lstrip("#").strip() == VOCABULARY_HEADING
        ),
        None,
    )
    assert start is not None, f"{VOCABULARY_FILE} has no '{VOCABULARY_HEADING}' heading"
    level = _level(content[start][1])
    found: dict[str, str] = {}
    for _, line in content[start + 1 :]:
        if HEADING.match(line) and _level(line) <= level:
            break
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].startswith("`" + LABEL_PREFIX) and cells[1].endswith("`"):
            assert cells[0] not in found, f"{VOCABULARY_FILE}: the audience {cells[0]!r} has two rows"
            found[cells[0]] = cells[1][1:-1]
    assert found, (
        f"{VOCABULARY_FILE}, '{VOCABULARY_HEADING}': no table row gives an audience and its"
        f" line as a code span starting with {LABEL_PREFIX!r}"
    )
    return found


@functools.cache
def vocabulary() -> dict[str, str]:
    """The repository's audience lines, from ``CONTRIBUTING.md``."""
    return parse_vocabulary((REPO / VOCABULARY_FILE).read_text(encoding="utf-8"))


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


def test_a_code_block_between_the_title_and_the_line_fails() -> None:
    doc = "# Title\n\n```bash\npip install legesher\n```\n\n> **Audience:** Readers, who read.\n"
    problems = audience_problems(doc, LINES)
    assert [p.split(":")[0] for p in problems] == ["line 1", "line 7"]


def test_a_section_line_below_a_code_block_fails_on_its_line() -> None:
    doc = (
        "# Title\n\n> **Audience:** Readers, who read.\n\n## Writing\n\n"
        "```text\nan example\n```\n\n> **Audience:** Writers, who write.\n"
    )
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 11:")


def test_a_title_inside_an_html_comment_is_not_the_title() -> None:
    doc = "<!--\n# Old title\n\n> **Audience:** Readers, who read.\n-->\n\n# Title\n\nBody.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 7:")


def test_a_fence_left_open_in_a_list_item_ends_with_the_item() -> None:
    doc = (
        "# Title\n\n> **Audience:** Readers, who read.\n\n1. Run it:\n\n   ```bash\n   make test\n\n"
        "## Next\n\n> **Audience:** Everyone, who reads.\n"
    )
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 12:")


@pytest.mark.parametrize(
    "statement",
    [
        "> *Audience:* Readers, who read.",
        "> **Audiences:** Readers, who read.",
        "**Audience:** Readers, who read.",
        "**Audience**: Readers and writers",
    ],
)
def test_an_audience_statement_in_another_shape_is_reported(statement: str) -> None:
    doc = f"# Title\n\n> **Audience:** Readers, who read.\n\n## Section\n\n{statement}\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 7:")


def test_a_line_run_into_the_next_paragraph_fails() -> None:
    doc = "# Title\n\n> **Audience:** Readers, who read.\nThe first paragraph joins the quote.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 3:")


def test_a_byte_order_mark_does_not_hide_the_title() -> None:
    doc = "﻿# Title\n\n> **Audience:** Readers, who read.\n"
    assert audience_problems(doc, LINES) == []


def test_a_line_separator_inside_the_title_does_not_split_it() -> None:
    doc = "# Title > **Audience:** Readers, who read.\n\nBody.\n"
    problems = audience_problems(doc, LINES)
    assert len(problems) == 1
    assert problems[0].startswith("line 1:")


def test_front_matter_before_the_title_is_skipped() -> None:
    doc = "---\ntitle: Title\n# a comment in the front matter\n---\n\n# Title\n\n> **Audience:** Readers, who read.\n"
    assert audience_problems(doc, LINES) == []


@pytest.mark.parametrize("title", ["#\tTitle", "   # Title"])
def test_a_title_after_a_tab_or_an_indent_is_found(title: str) -> None:
    doc = f"{title}\n\n> **Audience:** Readers, who read.\n"
    assert audience_problems(doc, LINES) == []


TABLE = "| Audience | The line |\n| --- | --- |\n"


def test_the_vocabulary_is_read_from_its_own_section() -> None:
    text = (
        f"## {VOCABULARY_HEADING}\n\n{TABLE}| Readers | `> **Audience:** Readers, who read.` |\n\n"
        f"## Next\n\n{TABLE}| Writers | `> **Audience:** Writers, who write.` |\n"
    )
    assert parse_vocabulary(text) == {"Readers": "> **Audience:** Readers, who read."}


def test_a_vocabulary_with_two_rows_for_one_audience_is_refused() -> None:
    text = (
        f"## {VOCABULARY_HEADING}\n\n{TABLE}| Readers | `> **Audience:** Readers, who read.` |\n"
        "| Readers | `> **Audience:** Readers, who skim.` |\n"
    )
    with pytest.raises(AssertionError, match="two rows"):
        parse_vocabulary(text)


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


def test_each_brief_an_index_lists_is_tracked() -> None:
    assert BRIEFS, f"no {CONTEXT_INDEXES} lists a brief; remove the brief exclusion"
    missing = sorted(BRIEFS - set(TRACKED))
    assert not missing, f"{CONTEXT_INDEXES} lists briefs git does not track: {missing}"


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
