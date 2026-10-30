"""The mechanical gate on a review pull request (CORE-2508).

The gate runs where no database and no salt exist (a pull-request check in
language-packs, or a maintainer's laptop before an import). It reads the file
with the same reader the importer uses, checks the pin, and runs the
mechanical checks over the ``Suggested`` column. Its one job is a report that
names every failing row by its key, so a reviewer can fix a file without a
maintainer translating a stack trace.
"""

from __future__ import annotations

import re

import pytest

from legesher_i18n.intake.review_gate import gate_review_file
from legesher_i18n.intake.review_template import known_pack_versions
from tests.interpreter_gaps import IDENTIFIER_RULES_ARE_UNICODE_15_1
from tests.review_fixtures import (
    CODES,
    PACKS_DIR,
    PR_AUTHOR,
    REGISTRY,
    current_word,
    fill,
    review_path,
    row_cells,
    template_text,
)

SI = template_text("si")

#: A Sinhala suggestion with U+200D on a row pinned at Python 3.14 that also
#: ships for 3.10 to 3.12. Only Unicode 15.1 tables (CPython 3.13+) can judge
#: the joiner; older tables make the gate report instead of guess, so the
#: joiner-word tests below assert one branch each.
JOINER_SUGGESTION = {"keywords.is": ("`අනන්\u200dයවේ`", "වේ alone means becomes")}


def python_versions(code: str) -> set[str]:
    (packs,) = (PACKS_DIR / code).glob("legesher_i18n_python_*/packs")
    return {path.stem for path in packs.glob("3.*.yml")}


def gate(text: str, code: str = "si", **overrides):
    arguments = {
        "template_text": template_text(code),
        "path": review_path(code),
        "author": PR_AUTHOR,
        "known_versions": known_pack_versions(PACKS_DIR / code, use_git=False),
        "python_versions": python_versions(code),
        "registry_entry": REGISTRY[code],
    }
    arguments.update(overrides)
    return gate_review_file(text, **arguments)


def failing(report, check: str) -> dict[str, str]:
    return {
        finding.key: finding.detail
        for finding in report.findings
        if finding.check == check and finding.severity == "fail"
    }


@pytest.mark.parametrize("code", CODES)
def test_every_template_endorsed_throughout_passes(code: str) -> None:
    template = template_text(code)
    text = fill(template, {key: ("", "✓") for key in row_cells(template)})
    report = gate(text, code)
    assert report.passed, report.to_markdown()


def test_an_invalid_identifier_fails_by_key() -> None:
    report = gate(fill(SI, {"keywords.if": ("`හොත් නම්`", "two words read better")}))
    assert "keywords.if" in failing(report, "identifier")
    assert not report.passed


def test_an_nfkc_unstable_suggestion_fails_by_key() -> None:
    report = gate(fill(SI, {"keywords.if": ("`ﬁහොත්`", "ligature typed by accident")}))
    assert "keywords.if" in failing(report, "nfkc")


def test_a_suggestion_equal_to_another_rows_current_word_collides() -> None:
    taken = current_word(SI, "keywords.else")
    report = gate(fill(SI, {"keywords.elif": (f"`{taken}`", "shorter")}))
    detail = failing(report, "collision")["keywords.elif"]
    assert "keywords.else" in detail


def test_two_suggestions_that_are_the_same_word_collide() -> None:
    report = gate(
        fill(SI, {"keywords.if": ("`හොත්`", "one"), "keywords.elif": ("`හොත්`", "two")})
    )
    collisions = failing(report, "collision")
    assert {"keywords.if", "keywords.elif"} <= set(collisions)


def test_the_same_word_for_the_keyword_and_the_builtin_type_is_allowed() -> None:
    word = current_word(SI, "builtins.type")
    report = gate(fill(SI, {"keywords.type": (f"`{word}`", "keep the pair")}))
    assert "keywords.type" not in failing(report, "collision")


def test_a_suggestion_that_is_a_live_python_name_collides() -> None:
    report = gate(fill(SI, {"builtins.print": ("`list`", "short")}))
    assert "builtins.print" in failing(report, "collision")


def test_a_suggestion_equal_to_its_own_english_term_is_not_a_collision() -> None:
    report = gate(fill(SI, {"builtins.print": ("`print`", "loanword in daily use")}))
    assert "builtins.print" not in failing(report, "collision")


@pytest.mark.skipif(
    not IDENTIFIER_RULES_ARE_UNICODE_15_1,
    reason="judging U+200D needs Unicode 15.1 tables (CPython 3.13 or newer)",
)
def test_a_joiner_word_on_a_row_that_covers_python_3_10_warns_by_key() -> None:
    report = gate(fill(SI, JOINER_SUGGESTION))
    tier = {f.key: f for f in report.findings if f.check == "version-tier"}
    assert tier["keywords.is"].severity == "warn"
    assert "3.10 to 3.12" in tier["keywords.is"].detail
    assert report.passed


@pytest.mark.skipif(
    IDENTIFIER_RULES_ARE_UNICODE_15_1,
    reason="the older-tables branch: CPython 3.10 to 3.12 cannot judge U+200D",
)
def test_a_joiner_word_on_older_tables_is_reported_not_judged() -> None:
    report = gate(fill(SI, JOINER_SUGGESTION))
    tier = {f.key: f for f in report.findings if f.check == "version-tier"}
    assert tier["keywords.is"].severity == "warn"
    assert "3.10 to 3.12" in tier["keywords.is"].detail
    identifier = failing(report, "identifier")
    assert set(identifier) == {"keywords.is"}
    assert "cannot judge" in identifier["keywords.is"]
    assert "3.13 or newer" in identifier["keywords.is"]
    assert {f.check for f in report.findings if f.severity == "fail"} == {"identifier"}
    assert not report.passed


def test_a_joiner_word_is_an_invalid_identifier_at_a_python_3_12_pin() -> None:
    template = SI.replace("python=3.14", "python=3.12", 1)
    text = fill(template, {"keywords.is": ("`අනන්\u200dයවේ`", "")})
    report = gate(text, template_text=template)
    assert "keywords.is" in failing(report, "identifier")


def test_an_unknown_pin_fails_and_names_the_version() -> None:
    text = fill(SI).replace("pack_version=0.0.3", "pack_version=9.9.9", 1)
    report = gate(text)
    assert not report.passed
    assert "9.9.9" in report.to_markdown()


def test_a_template_and_review_that_agree_on_an_unknown_pin_still_fail() -> None:
    template = SI.replace("pack_version=0.0.3", "pack_version=9.9.9", 1)
    report = gate(fill(template), template_text=template)
    pins = [f.detail for f in report.findings if f.check == "pin"]
    assert pins and "9.9.9" in pins[0]
    assert not report.passed


def test_a_refused_file_is_a_report_not_an_exception() -> None:
    report = gate(fill(SI, ticked=range(4)))
    assert not report.passed
    assert "CONTRIBUTOR_PRIVACY.md" in report.to_markdown()


def test_the_report_names_every_failing_row() -> None:
    text = fill(
        SI,
        {
            "keywords.if": ("`හොත් නම්`", ""),
            "keywords.else": ("`ﬁ`", ""),
            "builtins.print": ("`list`", ""),
        },
    )
    markdown = gate(text).to_markdown()
    for key in ("keywords.if", "keywords.else", "builtins.print"):
        assert f"`{key}`" in markdown


def test_a_clean_report_says_so_and_counts_what_it_read() -> None:
    text = fill(SI, {"keywords.and": ("", "✓"), "keywords.if": ("`හොත්`", "names")})
    report = gate(text)
    assert report.passed
    markdown = report.to_markdown()
    assert "No failing rows" in markdown
    assert "1 suggestion" in markdown and "1 endorsement" in markdown


# --- review findings (fix pass) ------------------------------------------------------


def test_reviewer_text_cannot_break_out_of_the_report() -> None:
    hostile = "a` ![t](https://example.invalid/beacon.png) @legesher/maintainers `b"
    text = fill(
        SI, {"keywords.if": (f"``{hostile}``", "")}, username="@legesher/maintainers"
    )
    markdown = gate(text).to_markdown()
    for line in markdown.splitlines():
        if "beacon" in line or "@legesher" in line:
            # Every occurrence sits inside a code span: strip the spans, nothing remains.
            stripped = re.sub(r"(`+).*?\1", "", line)
            assert "beacon" not in stripped and "@legesher" not in stripped, line


def test_an_interpreter_without_the_3_13_tables_does_not_guess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import legesher_i18n.intake.review_gate as review_gate

    monkeypatch.setattr(review_gate, "_UNICODE_15_1", False)
    report = gate(fill(SI, {"keywords.is": ("`\u200dනන්\u200dයවේ`", "")}))
    detail = failing(report, "identifier")["keywords.is"]
    assert "cannot judge" in detail


def test_a_suggestion_equal_to_an_earlier_tier_word_collides() -> None:
    cells = row_cells(SI)["builtins.print"]
    earlier = re.search(r"`([^`]+)`", cells[3]).group(1)  # type: ignore[union-attr]
    report = gate(fill(SI, {"builtins.input": (f"`{earlier}`", "")}))
    assert "builtins.print" in failing(report, "collision")["builtins.input"]


def test_an_email_in_the_credit_name_is_flagged() -> None:
    report = gate(fill(SI, credit="this name: `someone@example.com`"))
    assert any(f.check == "privacy" for f in report.findings)


@pytest.mark.parametrize(
    "where",
    ["path", "digest", "pack_version"],
)
def test_metadata_and_path_cannot_break_out_of_the_report(where: str) -> None:
    payload = "x`![b](https://example.invalid/beacon.png)`@legesher/maintainers`y"
    text = fill(SI)
    path = review_path("si")
    if where == "path":
        path = f"reviews/si/si-{payload}.md"
    else:
        field = {"digest": "digest=", "pack_version": "pack_version="}[where]
        start = text.index(field) + len(field)
        end = text.index(" ", start)
        text = text[:start] + payload + text[end:]
    markdown = gate(text, path=path).to_markdown()
    assert "beacon" in markdown
    for line in markdown.splitlines():
        stripped = re.sub(r"(`+).*?\1", "", line)
        assert "beacon" not in stripped and "@legesher" not in stripped, line


def test_parse_notes_appear_in_the_report_without_failing_it() -> None:
    report = gate(fill(SI, {"keywords.async": ("", "Keep")}))
    assert report.passed
    notes = [f for f in report.findings if f.severity == "note"]
    assert any("Keep without a note" in f.detail for f in notes)
