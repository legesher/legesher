"""Tests for BCP 47 locale-tag parsing, validation, canonicalization, fallback.

CORE-1500. Three layers are exercised separately, because the whole point of the
module is that they are *different* questions:

- well-formedness (:func:`~legesher_i18n.bcp47.parse`) — grammar only;
- validity (:func:`~legesher_i18n.bcp47.validate`) — subtags exist and are live;
- canonicality (:func:`~legesher_i18n.bcp47.check_canonical`) — Legesher's key form.

Plus a guard that every tag in the CORE-1500 backfill proposal is canonical, so
the proposal and the validator can never drift apart.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from legesher_i18n.bcp47 import (
    REGISTRY_PATH,
    InvalidLocaleTagError,
    LocaleTag,
    canonicalize,
    check_canonical,
    fallback_chain,
    is_canonical,
    is_macrolanguage,
    is_valid,
    parse,
    registry_file_date,
    suppressed_script,
    validate,
)
from legesher_i18n.scripts.propose_bcp47_backfill import (
    EDITORIAL_DECISIONS,
    NEEDS_REVIEW,
    NO_SCRIPT_DESPITE_NO_SUPPRESS,
    UnresolvedScriptError,
    build_rows,
    render_tsv,
    resolve_proposal,
)
from legesher_i18n.scripts.refresh_iana_subtags import (
    TruncatedRegistryError,
    check_not_truncated,
    snapshot_record_count,
)
from tests import language_packs_root

# The vendored snapshot this test suite was written against. If a refresh moves
# it, that is fine — but a human should look at the diff (a subtag going
# Deprecated is the case that matters), so the pin is deliberate.
# Refresh with: scripts/refresh_iana_subtags.py
EXPECTED_REGISTRY_DATE = "2026-06-14"

# The date alone is NOT a staleness guard: File-Date is the snapshot's first line,
# so a truncated fetch — or a hand-deleted row — keeps it intact while silently
# removing subtags (delete the one `script Hant` row and is_valid("zh-Hant")
# becomes False with every date/canonicality test still green). Pin the content.
EXPECTED_REGISTRY_RECORDS = 9296
EXPECTED_REGISTRY_DIGEST = (
    "f17c2af51eea37c7360dcf368f62e308e14616e564a86d6b9120b49e1b78bc6d"
)

# The six editorial calls, pinned BY VALUE against the committed TSV. Without this
# the tags are only checked for canonicality and uniqueness — so flipping
# EDITORIAL_DECISIONS["zh"] to "zh-Hant" and regenerating would keep CI green while
# silently reversing a one-way door. 'no' -> 'nb' and 'tl' -> 'fil' were decided
# by Madison (2026-07-15, as recommended): changing one is allowed, changing it
# *by accident* is not. Update this map deliberately, in the same commit.
PINNED_EDITORIAL_TAGS = {
    "zh": "zh-Hans",
    "sr": "sr-Cyrl",
    "uz": "uz-Latn",
    "mn": "mn-Cyrl",
    "no": "nb",
    "tl": "fil",
}

# Languages in the 103-language target (CORE-674) with NO Suppress-Script in the
# registry, several with a live script contrast: az = Latn/Arab/Cyrl, ku = Latn/Arab,
# sd = Arab/Deva. The default rule must never hand one of these a bare tag.
UNRESOLVED_SCRIPT_LANGUAGES = ["az", "ku", "sd", "ha", "ky", "tg", "ff"]

I18N_ROOT = Path(__file__).resolve().parents[1]
BACKFILL_TSV = I18N_ROOT / "legesher_i18n" / "db" / "migrations" / "bcp47_backfill.tsv"
PACK_ROOT = language_packs_root()


def _backfill_rows() -> list[dict[str, str]]:
    """The committed proposal TSV, as rows (comments stripped)."""
    lines = [
        line
        for line in BACKFILL_TSV.read_text(encoding="utf-8").splitlines()
        if not line.startswith("#")
    ]
    return list(csv.DictReader(lines, delimiter="\t"))


def _registry_data_rows() -> list[str]:
    """The snapshot's subtag records — no comments, no column header."""
    return [
        line
        for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and not line.startswith("type\t")
    ]


class TestRegistrySnapshot:
    """The vendored IANA registry is present, parseable, and pinned."""

    def test_snapshot_is_committed(self) -> None:
        assert REGISTRY_PATH.exists(), (
            f"vendored registry missing at {REGISTRY_PATH}; regenerate with "
            f"scripts/refresh_iana_subtags.py"
        )

    def test_file_date_is_pinned(self) -> None:
        assert registry_file_date() == EXPECTED_REGISTRY_DATE, (
            "the vendored IANA snapshot changed. Review the diff (watch for newly "
            "deprecated subtags), then update EXPECTED_REGISTRY_DATE."
        )

    def test_record_count_is_pinned(self) -> None:
        """A count, unlike the File-Date, notices a truncated or thinned snapshot."""
        count = len(_registry_data_rows())
        assert count == EXPECTED_REGISTRY_RECORDS, (
            f"the vendored snapshot has {count} records, pinned at "
            f"{EXPECTED_REGISTRY_RECORDS}. A DROP means a truncated fetch or a "
            f"deleted row — subtags would silently stop validating. An increase is a "
            f"real IANA refresh: review the diff, then update the pin."
        )

    def test_content_digest_is_pinned(self) -> None:
        """Pin the data rows themselves, so no row can be edited or dropped unseen."""
        digest = hashlib.sha256(
            "\n".join(_registry_data_rows()).encode("utf-8")
        ).hexdigest()
        assert digest == EXPECTED_REGISTRY_DIGEST, (
            f"the vendored snapshot's contents changed (digest {digest}). If this is "
            f"a deliberate refresh, review the diff and update "
            f"EXPECTED_REGISTRY_DIGEST, EXPECTED_REGISTRY_RECORDS, and "
            f"EXPECTED_REGISTRY_DATE together."
        )

    def test_known_subtags_resolve(self) -> None:
        # A language, a script, a region, and a 3-letter (ISO 639-3-only) language.
        assert is_valid("en")
        assert is_valid("zh-Hans")
        assert is_valid("pt-BR")
        assert is_valid("din"), (
            "Dinka is ISO 639-3 only; the 103-language target needs it"
        )

    def test_reserved_future_tags_still_resolve(self) -> None:
        """The tags this proposal deliberately leaves free must stay valid.

        Each depends on one script row (Hant, Latn, Cyrl, Mong). Losing that row is
        exactly the silent failure the digest pin above exists to catch — these
        assert the consequence, so the reason for the pin is on the record.
        """
        for tag in ["zh-Hant", "sr-Latn", "uz-Cyrl", "mn-Mong", "nn"]:
            assert is_valid(tag), f"{tag} no longer resolves against the snapshot"


class TestTruncationGuard:
    """A refresh may not silently shrink the registry (see refresh_iana_subtags)."""

    def test_counts_only_data_rows(self) -> None:
        snapshot = (
            "# comment\n# File-Date: 2026-06-14\ntype\tsubtag\nlanguage\ten\n"
            "script\tHant\n"
        )
        assert snapshot_record_count(snapshot) == 2

    def test_vendored_snapshot_count_agrees_with_the_pin(self) -> None:
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        assert snapshot_record_count(text) == EXPECTED_REGISTRY_RECORDS

    def test_truncated_snapshot_is_rejected(self) -> None:
        """Half a registry, with an intact header, must fail loudly — not overwrite."""
        with pytest.raises(TruncatedRegistryError, match="truncated"):
            check_not_truncated(
                EXPECTED_REGISTRY_RECORDS // 2, EXPECTED_REGISTRY_RECORDS
            )

    def test_dropping_a_single_row_is_rejected_at_a_strict_ratio(self) -> None:
        """The `script Hant` deletion the reviewer used, at ratio 1.0."""
        with pytest.raises(TruncatedRegistryError):
            check_not_truncated(
                EXPECTED_REGISTRY_RECORDS - 1, EXPECTED_REGISTRY_RECORDS, ratio=1.0
            )

    def test_a_growing_registry_is_accepted(self) -> None:
        """IANA adds subtags; that is a normal refresh, not a truncation."""
        check_not_truncated(EXPECTED_REGISTRY_RECORDS + 40, EXPECTED_REGISTRY_RECORDS)

    def test_a_first_refresh_has_nothing_to_compare_against(self) -> None:
        check_not_truncated(EXPECTED_REGISTRY_RECORDS, 0)


class TestParse:
    """Well-formedness: grammar only, no registry lookup."""

    @pytest.mark.parametrize(
        ("tag", "expected"),
        [
            ("en", LocaleTag("en")),
            ("din", LocaleTag("din")),
            ("zh-Hans", LocaleTag("zh", script="Hans")),
            ("pt-BR", LocaleTag("pt", region="BR")),
            ("zh-Hant-TW", LocaleTag("zh", script="Hant", region="TW")),
            ("es-419", LocaleTag("es", region="419")),
            ("de-DE-1996", LocaleTag("de", region="DE", variants=("1996",))),
        ],
    )
    def test_parses_positionally(self, tag: str, expected: LocaleTag) -> None:
        assert parse(tag) == expected

    @pytest.mark.parametrize(
        ("messy", "canonical"),
        [
            ("ZH-HANS", "zh-Hans"),
            ("zh-hans", "zh-Hans"),
            ("PT-br", "pt-BR"),
            ("SR-cyrl", "sr-Cyrl"),
        ],
    )
    def test_normalizes_casing(self, messy: str, canonical: str) -> None:
        assert str(parse(messy)) == canonical

    def test_wellformed_but_unregistered_still_parses(self) -> None:
        """Well-formedness is structural — 'qq-Zzzz' has the right shape."""
        assert parse("qq-Zzzz") == LocaleTag("qq", script="Zzzz")
        assert not is_valid("qq-Zzzz")

    @pytest.mark.parametrize(
        "tag",
        ["", "   ", "e", "-en", "en-", "en--US", " en", "en ", "toolongsubtag"],
    )
    def test_rejects_malformed(self, tag: str) -> None:
        with pytest.raises(InvalidLocaleTagError):
            parse(tag)

    @pytest.mark.parametrize(
        ("tag", "reason"),
        [
            ("en-US-x-private", "private-use"),
            ("de-DE-u-co-phonebk", "extension"),
            ("zh-cmn", "extlang"),
        ],
    )
    def test_rejects_constructs_excluded_from_key_domain(
        self, tag: str, reason: str
    ) -> None:
        """Extensions, private use, and extlangs are a second spelling of one locale."""
        with pytest.raises(InvalidLocaleTagError, match=reason):
            parse(tag)


class TestValidate:
    """Validity: every subtag is registered and none is deprecated."""

    @pytest.mark.parametrize("tag", ["en", "ar", "zh-Hans", "sr-Cyrl", "pt-BR", "fil"])
    def test_valid_tags_have_no_issues(self, tag: str) -> None:
        assert validate(tag) == []

    def test_unknown_language_subtag(self) -> None:
        issues = validate("qq")
        assert [issue.code for issue in issues] == ["unknown-subtag"]

    def test_unknown_script_subtag(self) -> None:
        issues = validate("en-Zqqq")
        assert [issue.code for issue in issues] == ["unknown-subtag"]

    @pytest.mark.parametrize(
        ("tag", "replacement"),
        [("iw", "he"), ("in", "id"), ("ji", "yi"), ("mo", "ro")],
    )
    def test_flags_deprecated_legacy_codes(self, tag: str, replacement: str) -> None:
        """The 1989 ISO 639 legacy codes must never become Legesher keys."""
        issues = validate(tag)
        assert [issue.code for issue in issues] == ["deprecated"]
        assert replacement in issues[0].message

    def test_valid_is_not_the_same_as_canonical(self) -> None:
        """'ar-Arab': every subtag is real, but the script is suppressed."""
        assert validate("ar-Arab") == []
        assert not is_canonical("ar-Arab")


class TestSuppressScript:
    """Suppress-Script drives the 'do I write the script subtag?' decision."""

    @pytest.mark.parametrize(
        ("language", "script"),
        [
            ("ar", "Arab"),
            ("he", "Hebr"),
            ("en", "Latn"),
            ("ur", "Arab"),
            ("ti", "Ethi"),
        ],
    )
    def test_languages_with_a_suppressed_script(
        self, language: str, script: str
    ) -> None:
        assert suppressed_script(language) == script

    @pytest.mark.parametrize("language", ["zh", "sr", "uz", "mn", "gd", "su"])
    def test_languages_with_no_suppressed_script(self, language: str) -> None:
        """These are exactly the languages where a script subtag is *possible*.

        Possible is not the same as required — gd and su take no script subtag
        (no live contrast). That call is editorial and lives in the backfill.
        """
        assert suppressed_script(language) is None

    @pytest.mark.parametrize("language", ["qq", "zz", "xxx", ""])
    def test_unknown_language_returns_none(self, language: str) -> None:
        """A language absent from the registry answers None, never raises.

        Pins the docstring's 'or is not in the registry' clause — the ternary
        in the implementation binds looser than ``or``, so ``record`` is only
        dereferenced when it exists. This test keeps a refactor honest.
        """
        assert suppressed_script(language) is None

    def test_suppressed_script_is_flagged_as_non_canonical(self) -> None:
        issues = check_canonical("ar-Arab")
        assert [issue.code for issue in issues] == ["suppress-script"]
        assert "Suppress-Script: Arab" in issues[0].message

    def test_unsuppressed_script_is_canonical(self) -> None:
        assert check_canonical("zh-Hans") == []
        assert check_canonical("sr-Cyrl") == []


class TestCanonicalize:
    """Canonicalization is mechanical: casing, deprecation, suppressed script."""

    @pytest.mark.parametrize(
        ("tag", "expected"),
        [
            ("ZH-hans", "zh-Hans"),
            ("ar-Arab", "ar"),  # suppressed script dropped
            ("he-Hebr", "he"),
            ("iw", "he"),  # deprecated -> Preferred-Value
            ("iw-Hebr", "he"),  # both at once
            ("pt-br", "pt-BR"),
            ("sr-cyrl", "sr-Cyrl"),
            ("zh-Hans", "zh-Hans"),  # idempotent
        ],
    )
    def test_canonicalizes(self, tag: str, expected: str) -> None:
        assert canonicalize(tag) == expected

    def test_is_idempotent(self) -> None:
        for tag in ["en", "zh-Hans", "pt-BR", "ar", "sr-Cyrl", "fil"]:
            assert canonicalize(canonicalize(tag)) == canonicalize(tag)

    def test_does_not_narrow_macrolanguages(self) -> None:
        """zh -> cmn is an editorial call about pack content, not a rewrite rule."""
        assert is_macrolanguage("zh")
        assert canonicalize("zh") == "zh"
        assert canonicalize("ar") == "ar"

    def test_does_not_invent_a_script(self) -> None:
        """A missing Suppress-Script is not permission to add a script subtag."""
        assert canonicalize("sr") == "sr"
        assert canonicalize("gd") == "gd"

    def test_rejects_unregistered_subtag(self) -> None:
        with pytest.raises(ValueError, match="not a registered language subtag"):
            canonicalize("qq")

    def test_substitutes_deprecated_variant(self) -> None:
        """heploc is the registry's only variant with a Preferred-Value."""
        assert canonicalize("ja-Latn-hepburn-heploc") == "ja-Latn-hepburn-alalc97"

    def test_substitutes_deprecated_region(self) -> None:
        assert canonicalize("my-BU") == "my-MM"

    def test_rejects_unregistered_variant(self) -> None:
        """The docstring's contract: *any* unregistered subtag raises.

        ``foobar`` and ``zzzzz`` are well-formed variant shapes, so they reach
        the registry lookup rather than the parser.
        """
        for tag in ("en-foobar", "de-DE-zzzzz"):
            with pytest.raises(ValueError, match="not a registered variant subtag"):
                canonicalize(tag)

    def test_rejects_deprecated_variant_with_no_replacement(self) -> None:
        """arevela's replacement lives in registry Comments, not Preferred-Value."""
        with pytest.raises(ValueError, match="deprecated .* no registered replacement"):
            canonicalize("hy-arevela")

    def test_variant_substitution_collapses_a_collision(self) -> None:
        """Substituting heploc next to an explicit alalc97 must not duplicate it."""
        assert canonicalize("ja-Latn-alalc97-heploc") == "ja-Latn-alalc97"

    @pytest.mark.parametrize(
        "tag", ["ja-Latn-hepburn-heploc", "my-BU", "iw-Hebr", "ar-Arab", "ZH-hans"]
    )
    def test_canonicalize_output_is_canonical(self, tag: str) -> None:
        """The invariant the variant gap broke: canonicalize's output validates."""
        assert is_canonical(canonicalize(tag))


class TestFallbackChain:
    """RFC 4647 Lookup: truncate from the right until something matches."""

    @pytest.mark.parametrize(
        ("tag", "chain"),
        [
            ("en", ["en"]),
            ("ar-EG", ["ar-EG", "ar"]),
            ("pt-BR", ["pt-BR", "pt"]),
            ("zh-Hans", ["zh-Hans", "zh"]),
            ("zh-Hant-TW", ["zh-Hant-TW", "zh-Hant", "zh"]),
            ("de-DE-1996", ["de-DE-1996", "de-DE", "de"]),
        ],
    )
    def test_chain(self, tag: str, chain: list[str]) -> None:
        assert fallback_chain(tag) == chain

    def test_chain_is_canonically_cased(self) -> None:
        assert fallback_chain("ZH-hant-tw") == ["zh-Hant-TW", "zh-Hant", "zh"]

    def test_chain_always_ends_at_the_bare_language(self) -> None:
        for tag in ["ar-EG", "zh-Hant-TW", "de-DE-1996", "es-419"]:
            assert fallback_chain(tag)[-1] == parse(tag).language

    def test_chain_always_starts_with_the_request(self) -> None:
        for tag in ["ar-EG", "zh-Hant-TW", "pt-BR"]:
            assert fallback_chain(tag)[0] == tag


class TestBackfillProposal:
    """The CORE-1500 proposal must agree with the validator, row for row.

    This is the drift guard: if someone edits a proposed tag by hand into
    something non-canonical, or a registry refresh deprecates a subtag the
    proposal uses, CI fails here.
    """

    @staticmethod
    def _rows() -> list[dict[str, str]]:
        return _backfill_rows()

    def test_proposal_is_committed(self) -> None:
        assert BACKFILL_TSV.exists(), (
            f"backfill proposal missing at {BACKFILL_TSV}; regenerate with "
            f"scripts/propose_bcp47_backfill.py"
        )

    def test_covers_every_language_in_the_db(self) -> None:
        from legesher_i18n.db import TranslationDatabase

        db = TranslationDatabase()
        try:
            codes = {row["code"] for row in db.get_languages()}
        finally:
            db.close()
        assert {row["code"] for row in self._rows()} == codes

    def test_every_proposed_tag_is_canonical(self) -> None:
        offenders = {
            row["code"]: [str(issue) for issue in check_canonical(row["proposed_tag"])]
            for row in self._rows()
            if check_canonical(row["proposed_tag"])
        }
        assert not offenders, f"non-canonical proposed tags: {offenders}"

    def test_proposed_tags_are_unique(self) -> None:
        """The tag is destined to be a primary key — no two languages may collide."""
        tags = [row["proposed_tag"] for row in self._rows()]
        assert len(tags) == len(set(tags))

    def test_default_slugs_are_valid_python_identifiers(self) -> None:
        """A pack dir becomes a module name: legesher_i18n_{target}_{slug}."""
        for row in self._rows():
            slug = row["default_slug_if_new"]
            assert f"legesher_i18n_python_{slug}".isidentifier(), (
                f"default_slug_if_new {slug!r} for {row['code']!r} would not form a "
                f"valid Python module name"
            )

    def test_default_slugs_are_unique(self) -> None:
        """Two locales must never resolve to one pack directory."""
        slugs = [row["default_slug_if_new"] for row in self._rows()]
        assert len(slugs) == len(set(slugs))

    def test_current_pack_dir_exists_on_disk(self) -> None:
        """The dir a shipped pack lives in TODAY — not the slug a new pack would get.

        This is the column a loader must key on for an existing pack. `no` keeps
        `no/` and `zh` keeps `zh/` even though their keys become `nb` and `zh-Hans`
        (renaming `no/` renames the published PyPI dist), so joining
        `default_slug_if_new` would send a loader to directories that do not exist.
        """
        for row in self._rows():
            if row["has_pack"] != "1":
                assert row["current_pack_dir"] == "-"
                continue
            directory = PACK_ROOT / row["current_pack_dir"]
            assert directory.is_dir(), (
                f"{row['code']}: current_pack_dir {row['current_pack_dir']!r} does "
                f"not exist at {directory}"
            )

    def test_the_two_packs_that_must_not_move_keep_their_directory(self) -> None:
        """The rows the design doc explicitly pins: keep `no/`, keep `zh/`."""
        rows = {row["code"]: row for row in self._rows()}
        for code, tag, new_slug in [("no", "nb", "nb"), ("zh", "zh-Hans", "zh_hans")]:
            row = rows[code]
            assert row["proposed_tag"] == tag
            assert row["current_pack_dir"] == code
            assert row["default_slug_if_new"] == new_slug
            assert (PACK_ROOT / code).is_dir()
            assert not (PACK_ROOT / new_slug).exists(), (
                f"{new_slug}/ must not exist: {code}/ stays put (doc section 6)"
            )

    def test_script_subtag_only_where_not_suppressed(self) -> None:
        """The central rule: never write a script the registry suppresses."""
        for row in self._rows():
            if row["script_subtag_used"] == "yes":
                language = parse(row["proposed_tag"]).language
                assert suppressed_script(language) is None, (
                    f"{row['code']}: proposed {row['proposed_tag']} carries a script "
                    f"subtag, but the registry suppresses one for {language!r}"
                )

    def test_every_bare_tag_states_why_it_carries_no_script(self) -> None:
        """No row may take a bare tag while leaving the script question unanswered.

        A bare tag is only justified two ways: the registry suppresses the script,
        or an editorial entry says there is no live contrast. `tl` -> `fil` is the
        subtle one — `tl` has Suppress-Script: Latn, but the tag actually adopted is
        `fil`, which does not, so the reason has to be stated for `fil`.
        """
        for row in self._rows():
            if row["script_subtag_used"] == "yes":
                continue
            if row["suppress_script"] != "-":
                assert "Suppress-Script" in row["rationale"]
                continue
            language = parse(row["proposed_tag"]).language
            note = NO_SCRIPT_DESPITE_NO_SUPPRESS.get(language)
            assert note is not None and note in row["rationale"], (
                f"{row['code']}: proposed bare tag {row['proposed_tag']!r}, whose "
                f"language {language!r} has no Suppress-Script, but the rationale "
                f"never says why no script subtag belongs"
            )


class TestEditorialDecisions:
    """The six editorial calls, pinned by value.

    Canonicality and uniqueness do not pin a *choice*: `zh-Hant` is every bit as
    canonical and unique as `zh-Hans`. These tests are what make a flip of any
    editorial tag — by hand in the TSV, or in the generator — fail CI.
    """

    @staticmethod
    def _by_code() -> dict[str, dict[str, str]]:
        return {row["code"]: row for row in _backfill_rows()}

    @pytest.mark.parametrize(("code", "tag"), sorted(PINNED_EDITORIAL_TAGS.items()))
    def test_committed_tsv_pins_the_decision(self, code: str, tag: str) -> None:
        assert self._by_code()[code]["proposed_tag"] == tag, (
            f"the committed proposal for {code!r} changed. This is a one-way door "
            f"(it becomes the DB key, the PyPI dist, the pack's `language:` field). "
            f"If the change is deliberate, update PINNED_EDITORIAL_TAGS in the same "
            f"commit — that is the review gate, not a formality."
        )

    @pytest.mark.parametrize(("code", "tag"), sorted(PINNED_EDITORIAL_TAGS.items()))
    def test_generator_pins_the_decision(self, code: str, tag: str) -> None:
        assert EDITORIAL_DECISIONS[code][0] == tag
        assert resolve_proposal(code)[0] == tag

    def test_there_are_exactly_six(self) -> None:
        assert set(EDITORIAL_DECISIONS) == set(PINNED_EDITORIAL_TAGS)

    def test_open_calls_are_flagged_for_review(self) -> None:
        """All three of Madison's calls (`no`→nb, `tl`→fil, `su` bare) were
        decided as recommended on 2026-07-15, so nothing is flagged — but the
        flag column must still track the set exactly."""
        assert NEEDS_REVIEW == frozenset()
        flagged = {
            row["code"] for row in _backfill_rows() if row["needs_review"] == "yes"
        }
        assert flagged == NEEDS_REVIEW

    def test_the_decided_calls_record_their_decision(self) -> None:
        """The rationale is the audit trail: each formerly-open row says DECIDED."""
        rows = {row["code"]: row for row in _backfill_rows()}
        for code in ("no", "tl", "su"):
            assert "DECIDED" in rows[code]["rationale"], code
            assert rows[code]["needs_review"] == "no", code

    def test_committed_tsv_matches_the_generator(self) -> None:
        """Drift guard: the TSV is generated output, not an editable file.

        Without this, a hand-edit that happens to stay canonical and unique — a
        swapped tag, a softened rationale, a retyped slug — survives CI.
        """
        assert render_tsv(build_rows()) == BACKFILL_TSV.read_text(encoding="utf-8"), (
            "bcp47_backfill.tsv is out of sync with its generator. Regenerate with: "
            "uv run python libs/i18n/legesher_i18n/scripts/propose_bcp47_backfill.py"
        )


class TestUnresolvedScript:
    """The default rule may not assert a fact about script that nobody checked.

    A language with no Suppress-Script and no editorial entry used to fall through
    to "Shortest ISO 639 code; no script or regional contrast." — a confident,
    machine-generated rationale that is *false* for the languages the 103-language
    target actually adds. The failure has to be loud, and it has to be loud at the
    moment of expansion, which is exactly when nobody is looking for it.
    """

    @pytest.mark.parametrize("code", UNRESOLVED_SCRIPT_LANGUAGES)
    def test_an_unseen_no_suppress_language_cannot_get_a_bare_tag(
        self, code: str
    ) -> None:
        assert suppressed_script(code) is None, (
            f"{code} was expected to have no Suppress-Script; the registry changed"
        )
        with pytest.raises(UnresolvedScriptError, match="no Suppress-Script"):
            resolve_proposal(code)

    def test_the_error_names_both_ways_out(self) -> None:
        with pytest.raises(UnresolvedScriptError) as caught:
            resolve_proposal("az")
        message = str(caught.value)
        assert "EDITORIAL_DECISIONS" in message
        assert "NO_SCRIPT_DESPITE_NO_SUPPRESS" in message

    def test_a_suppress_script_language_still_takes_the_default(self) -> None:
        tag, rationale = resolve_proposal("ti")  # Tigrinya, Suppress-Script: Ethi
        assert tag == "ti"
        assert "Suppress-Script: Ethi" in rationale

    @pytest.mark.parametrize("code", ["gd", "su"])
    def test_an_answered_no_suppress_language_takes_the_bare_tag(
        self, code: str
    ) -> None:
        tag, rationale = resolve_proposal(code)
        assert tag == code
        assert rationale

    def test_the_editorial_script_languages_resolve(self) -> None:
        for code, tag in [("zh", "zh-Hans"), ("sr", "sr-Cyrl"), ("mn", "mn-Cyrl")]:
            assert resolve_proposal(code)[0] == tag


class TestBackfillApplied:
    """CORE-1512 slice 1: the DB column carries the reviewed proposal.

    The TSV was the *proposal*; `apply_bcp47_backfill.py` wrote it into
    `languages.bcp47` on 2026-07-15. From that moment the DB and the TSV must
    agree exactly — a divergence means either an unreviewed hand-edit to the DB
    or a regenerated proposal that was never applied, and both should fail CI.
    """

    @staticmethod
    def _db_column() -> dict[str, str | None]:
        import sqlite3

        db_path = I18N_ROOT / "legesher_i18n" / "db" / "translations.db"
        assert db_path.exists(), f"{db_path} missing"
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            return dict(conn.execute("SELECT code, bcp47 FROM languages"))
        finally:
            conn.close()

    def test_db_matches_the_committed_proposal_exactly(self) -> None:
        proposed = {row["code"]: row["proposed_tag"] for row in _backfill_rows()}
        assert self._db_column() == proposed

    def test_no_nulls_remain(self) -> None:
        nulls = [code for code, tag in self._db_column().items() if not tag]
        assert nulls == []

    def test_every_db_tag_is_canonical(self) -> None:
        for code, tag in self._db_column().items():
            assert tag is not None and is_canonical(tag), (code, tag)

    def test_pack_reference_docs_state_the_db_tag(self) -> None:
        """Every pack REFERENCE.md 'BCP 47 Tag' row matches the DB column.

        REFERENCE.md is hand-maintained (packs do not regenerate — CORE-1400),
        so nothing mechanical kept its language table honest: mn/sr/uz shipped
        stale bare tags for a day after the 2026-07-15 backfill. This pins the
        docs to the database.
        """
        import re as _re

        db = self._db_column()
        checked = 0
        for ref in sorted(PACK_ROOT.glob("*/REFERENCE.md")):
            code = ref.parent.name
            match = _re.search(
                r"\|\s*\*\*BCP 47 Tag\*\*\s*\|\s*`([^`]+)`\s*\|", ref.read_text()
            )
            assert match, f"{ref} has no BCP 47 Tag row"
            assert match.group(1) == db[code], (
                f"{ref}: says {match.group(1)!r}, DB says {db[code]!r}"
            )
            checked += 1
        # 50, not 51: en is the canonical source language and ships no
        # REFERENCE.md (there is nothing to translate back to).
        assert checked == 50
