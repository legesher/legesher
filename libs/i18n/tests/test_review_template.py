"""The review template's hidden metadata line and the review-pin check (CORE-1702).

One module serves three callers: the generator stamps the line, the future
markdown parser reads it back, and the pull-request check refuses a review
whose pin names a version that does not exist. The values on the line are the
only version strings a review carries, so the parse must be exact and every
refusal must name what it refused.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legesher_i18n.intake.review_template import (
    FORMAT_VERSION,
    ReviewTemplateError,
    TemplateMetadata,
    check_review_pin,
    known_pack_versions,
    known_pins_from_template,
    parse_metadata_line,
    render_metadata_line,
    review_file_name,
    review_folder,
)

ROOT = Path(__file__).resolve().parents[3]
PACKS_DIR = ROOT / "libs" / "i18n" / "language-packs" / "python"
REGISTRY = json.loads(
    (ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json").read_text(
        encoding="utf-8"
    )
)["languages"]

SI = TemplateMetadata(
    format=FORMAT_VERSION,
    pack="legesher-i18n-python-si",
    pack_version="0.0.3",
    python="3.14",
    code="si",
    bcp47="si",
    digest="0123456789ab",
)


def test_metadata_line_round_trips() -> None:
    line = render_metadata_line(SI)
    assert line.startswith("<!-- legesher-review-template format=1 ")
    assert line.endswith(" -->")
    assert parse_metadata_line(line + "\n# Sinhala\n") == SI


def test_kit_version_names_pack_version_python_and_digest() -> None:
    assert (
        SI.kit_version
        == "reference-md/legesher-i18n-python-si@0.0.3+py3.14#0123456789ab"
    )


def test_parse_refuses_a_file_without_the_line() -> None:
    with pytest.raises(ReviewTemplateError, match="first line"):
        parse_metadata_line("# Sinhala review\n")


def test_parse_names_a_missing_field() -> None:
    line = render_metadata_line(SI).replace(" bcp47=si", "")
    with pytest.raises(ReviewTemplateError, match="bcp47"):
        parse_metadata_line(line)


def test_parse_refuses_an_unknown_format_version() -> None:
    line = render_metadata_line(SI).replace("format=1", "format=99")
    with pytest.raises(ReviewTemplateError, match="format=99"):
        parse_metadata_line(line)


def test_pin_accepts_a_known_version() -> None:
    problems = check_review_pin(
        SI,
        known_versions={"0.0.2", "0.0.3"},
        python_versions={"3.10", "3.11", "3.12", "3.13", "3.14"},
        registry_entry=REGISTRY["si"],
    )
    assert problems == []


def test_pin_refuses_a_version_that_never_existed() -> None:
    meta = TemplateMetadata(**{**SI.__dict__, "pack_version": "0.0.9"})
    problems = check_review_pin(
        meta,
        known_versions={"0.0.2", "0.0.3"},
        python_versions={"3.10", "3.14"},
        registry_entry=REGISTRY["si"],
    )
    assert any("0.0.9" in p and "legesher-i18n-python-si" in p for p in problems), (
        problems
    )


def test_pin_refuses_a_python_version_the_pack_has_no_file_for() -> None:
    meta = TemplateMetadata(**{**SI.__dict__, "python": "3.9"})
    problems = check_review_pin(
        meta,
        known_versions={"0.0.3"},
        python_versions={"3.10", "3.14"},
        registry_entry=REGISTRY["si"],
    )
    assert any("3.9" in p for p in problems), problems


def test_pin_refuses_a_bcp47_that_disagrees_with_the_registry() -> None:
    meta = TemplateMetadata(**{**SI.__dict__, "bcp47": "si-LK"})
    problems = check_review_pin(
        meta,
        known_versions={"0.0.3"},
        python_versions={"3.14"},
        registry_entry=REGISTRY["si"],
    )
    assert any("si-LK" in p for p in problems), problems


def test_pin_refuses_a_code_the_registry_does_not_have() -> None:
    problems = check_review_pin(
        SI, known_versions={"0.0.3"}, python_versions={"3.14"}, registry_entry=None
    )
    assert any("si" in p and "registry" in p for p in problems), problems


def test_known_pack_versions_reads_pyproject_and_changelog() -> None:
    versions = known_pack_versions(PACKS_DIR / "si")
    # pyproject.toml is 0.0.3; the stamped CHANGELOG lists 0.0.2 and 0.0.1.
    assert {"0.0.3", "0.0.2", "0.0.1"} <= versions
    assert "0.0.9" not in versions


@pytest.mark.parametrize("code", sorted(REGISTRY))
def test_review_folder_is_the_bcp47_tag(code: str) -> None:
    assert review_folder(code, REGISTRY[code]["bcp47"]) == REGISTRY[code]["bcp47"]


def test_review_file_name_first_review_and_after_a_bump() -> None:
    assert review_file_name("si", "supunTE") == "si-supunTE.md"
    assert (
        review_file_name("si", "supunTE", pack_version="0.0.4") == "si-supunTE-0.0.4.md"
    )
    assert review_file_name("zh-Hans", "madiedgar") == "zh-Hans-madiedgar.md"


def test_parse_tolerates_a_byte_order_mark() -> None:
    assert parse_metadata_line("\ufeff" + render_metadata_line(SI)) == SI


def test_parse_refuses_a_duplicated_field() -> None:
    line = render_metadata_line(SI).replace(
        "pack_version=0.0.3", "pack_version=0.0.3 pack_version=9.9.9"
    )
    with pytest.raises(ReviewTemplateError, match="pack_version"):
        parse_metadata_line(line)


def test_known_pack_versions_reads_the_git_history_of_pyproject(tmp_path: Path) -> None:
    import subprocess

    pack = tmp_path / "xx"
    pack.mkdir()
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
    }
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "init", "-q"], check=True, env=env)
    for version in ("0.0.1", "0.0.2", "0.0.3"):
        (pack / "pyproject.toml").write_text(
            f'[project]\nname = "legesher-i18n-python-xx"\nversion = "{version}"\n',
            encoding="utf-8",
        )
        subprocess.run([*git, "add", "xx/pyproject.toml"], check=True, env=env)
        subprocess.run([*git, "commit", "-q", "-m", version], check=True, env=env)
    # No CHANGELOG.md at all: the earlier bumps exist only in git.
    assert known_pack_versions(pack) == {"0.0.1", "0.0.2", "0.0.3"}
    assert known_pack_versions(pack, use_git=False) == {"0.0.3"}


# --- the pin index where no pack tree exists (CORE-2508) ---------------------


def _git(cwd: Path, *args: str) -> None:
    import subprocess

    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def test_pins_from_a_template_outside_git_are_its_own_line(tmp_path: Path) -> None:
    template = tmp_path / "si.md"
    template.write_text(
        (PACKS_DIR / "si" / "REFERENCE.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    versions, pythons = known_pins_from_template(template)
    meta = parse_metadata_line(template.read_text(encoding="utf-8"))
    assert (versions, pythons) == ({meta.pack_version}, {meta.python})


def test_pins_from_a_template_include_every_pin_its_history_carried(
    tmp_path: Path,
) -> None:
    text = (PACKS_DIR / "si" / "REFERENCE.md").read_text(encoding="utf-8")
    meta = parse_metadata_line(text)
    old = text.replace(
        f"pack_version={meta.pack_version}", "pack_version=0.0.1", 1
    ).replace(f"python={meta.python}", "python=3.12", 1)
    _git(tmp_path, "init", "-q")
    template = tmp_path / "si.md"
    template.write_text(old, encoding="utf-8")
    _git(tmp_path, "add", "si.md")
    _git(tmp_path, "commit", "-q", "-m", "old pin")
    template.write_text(text, encoding="utf-8")
    _git(tmp_path, "commit", "-q", "-am", "new pin")
    versions, pythons = known_pins_from_template(template)
    assert versions == {"0.0.1", meta.pack_version}
    assert pythons == {"3.12", meta.python}
    assert known_pins_from_template(template, use_git=False) == (
        {meta.pack_version},
        {meta.python},
    )


def test_templates_at_takes_the_path_literally_never_as_a_glob(tmp_path: Path) -> None:
    from legesher_i18n.intake.review_template import ReviewTemplateError, templates_at

    _git(tmp_path, "init", "-q")
    (tmp_path / "reference").mkdir()
    (tmp_path / "reference" / "si.md").write_text("template\n", encoding="utf-8")
    _git(tmp_path, "add", "reference/si.md")
    _git(tmp_path, "commit", "-q", "-m", "template")
    assert templates_at(tmp_path, "HEAD", "reference/si.md") == ["template\n"]
    for pattern in ("reference/s?.md", "reference/*.md", "reference/[s]i.md"):
        with pytest.raises(ReviewTemplateError):
            templates_at(tmp_path, "HEAD", pattern)
