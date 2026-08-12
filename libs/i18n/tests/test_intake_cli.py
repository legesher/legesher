"""CLI surface of the intake write path (CORE-1688 + CORE-1828).

``legesher-i18n import-review-bundle`` / ``import-issue`` are the ritual's
entry points; ``clear-option`` is the DISTINCT maintainer act that ends a
quarantine; ``quarantine-queue`` is the triage lens; ``--sync`` is the
durable-home write-through that ends every import run (CORE-1794 ritual).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from legesher_i18n.cli import cli
from legesher_i18n.db.schema_v2 import apply_schema_v2, option_uid
from legesher_i18n.intake.sync import sync_to_durable_home

SALT = "intake-test-salt"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LEGESHER_CONTRIBUTOR_SALT", SALT)
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.executescript(
        """
        INSERT INTO programming_languages(code, name, status)
            VALUES ('python','Python','shipping');
        INSERT INTO locales(tag, language_subtag, name, native_name, direction, in_registry)
            VALUES ('ur','ur','Urdu','اردو','rtl',1);
        INSERT INTO concepts(slug, definition_en, category)
            VALUES ('elif-compound','otherwise-if','control_flow');
        INSERT INTO terms(concept_id, programming_language, name, category)
            VALUES (1,'python','elif','keyword');
        """
    )
    conn.commit()
    conn.close()
    return path


def valid_bundle() -> dict:
    return {
        "bundle_version": "1.0",
        "kit_version": "v2@2026-08-11+abc123",
        "locale": "ur",
        "track": "reserved_words",
        "contributor": {
            "source_key": "cli-reviewer",
            "claimed_rung": "native_claimed",
            "consent": {"consent_version": "1.0", "credit_preference": "anonymous"},
        },
        "attestations": {
            "native_or_fluent": True,
            "original_work": True,
            "license_grant": "Apache-2.0",
            "coc_agreed": True,
            "dco": True,
        },
        "responses": [
            {
                "concept": "elif-compound",
                "blind": {"surface_form": "ورنہ_اگر"},
                "endorsements": [],
                "ranking": ["ورنہ_اگر"],
            }
        ],
        "session": {"started_at": "2026-08-11T09:00:00Z"},
    }


NEW_OPT = option_uid("elif-compound", "ur", "ورنہ_اگر")


def write_bundle(tmp_path: Path, bundle: dict) -> Path:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    return path


def test_import_review_bundle_accepts_and_prints_the_reply(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    bundle_file = write_bundle(tmp_path, valid_bundle())
    report_path = tmp_path / "ledger.json"
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(bundle_file),
            "--db",
            str(db_path),
            "--json-report",
            str(report_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "accepted" in result.output
    assert NEW_OPT in result.output  # reply names the option uids
    ledger = json.loads(report_path.read_text())
    assert ledger["status"] == "accepted"
    # Every created option is quarantined on arrival, so the ledger carries
    # one list, not two copies of it.
    assert ledger["created_options"] == [NEW_OPT]
    assert "quarantined_options" not in ledger


def test_import_review_bundle_returned_is_actionable_and_nonzero(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    bundle = valid_bundle()
    bundle["responses"][0]["ranking"] = ["توڑو"]  # never endorsed
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, bundle)),
            "--db",
            str(db_path),
        ],
    )
    assert result.exit_code == 1
    assert "returned" in result.output
    assert "توڑو" in result.output  # the report names the offending surface


def test_import_review_bundle_halts_on_postdated_withdrawal(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    from legesher_i18n.db.schema_v2 import contributor_id

    cid = contributor_id("cli-reviewer", salt=SALT)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (cid,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, withdrawn_at)"
        " VALUES (?, '2026-08-01')",
        (cid,),
    )
    conn.commit()
    conn.close()
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
        ],
    )
    assert result.exit_code == 3  # stop and surface to a human
    assert "human" in result.output.lower()


def test_import_issue_from_a_payload_file(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    payload = {
        "number": 7,
        "url": "https://github.com/legesher/legesher-next/issues/7",
        "author": {"login": "drive-by"},
        "title": "[Review]: Urdu (Python)",
        "createdAt": "2026-08-11T08:00:00Z",
        # A COMPLETE rendered form: the parser refuses a partial body, because
        # a missing section is how a forged heading swallows the real ones.
        "body": (
            "### Language being reviewed\n\nUrdu (ur)\n\n"
            "### Your relationship to this language\n\nI am a native speaker\n\n"
            "### Review notes\n\n- `elif` → `ورنہ_اگر` ✅ reads well\n\n"
            "### Additional context\n\n_No response_\n\n"
            "### How would you like to be credited?\n\nAnonymous (default)\n\n"
            "### Consent\n\n"
            "- [x] I have read [Your contributions and your data](x) (v1.0) and agree\n"
            "- [x] I agree to follow this project's [Code of Conduct](y)\n"
        ),
    }
    payload_file = tmp_path / "issue.json"
    payload_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    result = runner.invoke(
        cli, ["import-issue", str(payload_file), "--db", str(db_path)]
    )
    assert result.exit_code == 0, result.output
    assert "accepted" in result.output

    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT method FROM review_sessions").fetchone() == ("github",)
    conn.close()


def test_import_issue_parse_notes_reach_the_ledger(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    """CORE-1838: the issue lane is the ONLY one that produces parse notes.

    `ImportResult.parse_notes` exists so a note rides the ledger and the
    verification report rather than a terminal scrollback — which it cannot do
    if the lane that generates notes never hands them to the importer.
    """
    payload = {
        "number": 8,
        "url": "https://github.com/legesher/legesher-next/issues/8",
        "author": {"login": "drive-by"},
        "title": "[Review]: Urdu (Python)",
        "createdAt": "2026-08-11T08:00:00Z",
        "body": (
            "### Language being reviewed\n\nUrdu (ur)\n\n"
            "### Your relationship to this language\n\nI am a native speaker\n\n"
            "### Review notes\n\n- `elif` → `ورنہ_اگر` ✅ reads well\n"
            # No concept maps to `walrus`: a note, and the line is skipped.
            "- `walrus` → `والرس` ✅ fine\n\n"
            "### Additional context\n\n_No response_\n\n"
            "### How would you like to be credited?\n\nAnonymous (default)\n\n"
            "### Consent\n\n"
            "- [x] I have read [Your contributions and your data](x) (v1.0) and agree\n"
            "- [x] I agree to follow this project's [Code of Conduct](y)\n"
        ),
    }
    payload_file = tmp_path / "issue.json"
    payload_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    report = tmp_path / "ledger.json"

    result = runner.invoke(
        cli,
        [
            "import-issue",
            str(payload_file),
            "--db",
            str(db_path),
            "--json-report",
            str(report),
        ],
    )

    assert result.exit_code == 0, result.output
    ledger = json.loads(report.read_text(encoding="utf-8"))
    assert any("walrus" in note for note in ledger["parse_notes"])
    # And as a stage, so the ledger reads as a record of the run rather than a
    # loose list beside it.
    parse_stages = [s for s in ledger["report"]["stages"] if s["stage"] == "parse"]
    assert len(parse_stages) == 1
    assert parse_stages[0]["status"] == "warn"


def test_quarantine_queue_and_clear_option_roundtrip(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
        ],
    )
    queue = runner.invoke(cli, ["quarantine-queue", "--db", str(db_path)])
    assert queue.exit_code == 0
    assert NEW_OPT in queue.output

    missing_by = runner.invoke(
        cli, ["clear-option", NEW_OPT, "--verdict", "cleared", "--db", str(db_path)]
    )
    assert missing_by.exit_code != 0  # clearing must be attributable

    cleared = runner.invoke(
        cli,
        [
            "clear-option",
            NEW_OPT,
            "--verdict",
            "cleared",
            "--by",
            "madi",
            "--note",
            "import ritual 2026-08-11",
            "--db",
            str(db_path),
        ],
    )
    assert cleared.exit_code == 0, cleared.output

    conn = sqlite3.connect(db_path)
    assert conn.execute(
        "SELECT verdict, screened_by FROM option_screening_status WHERE option_uid=?",
        (NEW_OPT,),
    ).fetchone() == ("cleared", "madi")
    # Visible to rankings again.
    assert conn.execute(
        "SELECT COUNT(*) FROM option_standings WHERE option_uid=?", (NEW_OPT,)
    ).fetchone() == (1,)
    conn.close()

    empty = runner.invoke(cli, ["quarantine-queue", "--db", str(db_path)])
    assert NEW_OPT not in empty.output


def rewind_before_screening(path: Path) -> None:
    """Strip the CORE-1828 objects: what the ritual actually carries forward.

    The import lane installs them on arrival, so the two commands that read
    the screening verdict have to survive being the FIRST thing run against a
    carried-forward database — the triage lens is exactly what a maintainer
    reaches for before importing anything.
    """
    conn = sqlite3.connect(path)
    conn.execute("DROP TRIGGER trg_canon_no_quarantined_option")
    for view in (
        "option_standings",
        "terminology_export",
        "quarantine_queue",
        "option_withheld",
        "option_screening_status",
    ):
        conn.execute(f"DROP VIEW {view}")  # nosec B608 - fixed names
    conn.execute("DROP TABLE option_screenings")
    conn.commit()
    conn.close()


def test_quarantine_queue_survives_a_carried_forward_database(
    runner: CliRunner, db_path: Path
) -> None:
    """CORE-1838: the lens must not die with `no such table: quarantine_queue`."""
    rewind_before_screening(db_path)

    queue = runner.invoke(cli, ["quarantine-queue", "--db", str(db_path)])

    assert queue.exit_code == 0, queue.output
    assert "quarantine queue is empty" in queue.output


def test_clear_option_survives_a_carried_forward_database(
    runner: CliRunner, db_path: Path
) -> None:
    """A verdict is recordable on a database that predates the verdict table."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO options(uid, concept_id, locale, surface_form)"
        " VALUES (?, 1, 'ur', 'ورنہ_اگر')",
        (NEW_OPT,),
    )
    conn.commit()
    conn.close()
    rewind_before_screening(db_path)

    result = runner.invoke(
        cli,
        [
            "clear-option",
            NEW_OPT,
            "--verdict",
            "held",
            "--by",
            "madi",
            "--db",
            str(db_path),
        ],
    )

    assert result.exit_code == 0, result.output
    conn = sqlite3.connect(db_path)
    assert conn.execute(
        "SELECT verdict, screened_by FROM option_screening_status WHERE option_uid=?",
        (NEW_OPT,),
    ).fetchone() == ("held", "madi")
    conn.close()


def test_sync_to_durable_home_pushes_db_and_payload(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    home = tmp_path / "data-home"
    subprocess.run(["git", "clone", "-q", str(remote), str(home)], check=True)
    for key, value in (
        ("user.email", "test@example.invalid"),
        ("user.name", "Test"),
    ):
        subprocess.run(["git", "-C", str(home), "config", key, value], check=True)
    monkeypatch.setenv("LEGESHER_DATA_REPO", str(home))

    sha = sync_to_durable_home(
        db_path,
        [("ses_test.json", b'{"hello": 1}')],
        ritual="review import [CORE-1688]",
    )
    assert sha
    assert (home / "db" / db_path.name).exists()
    archived = list((home / "intake").rglob("ses_test.json"))
    assert len(archived) == 1
    # The push is real: the remote has the commit.
    remote_sha = subprocess.run(
        ["git", "-C", str(remote), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_sha == sha


def test_sync_refuses_without_a_data_home(
    db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LEGESHER_DATA_REPO", raising=False)
    with pytest.raises(RuntimeError, match="LEGESHER_DATA_REPO"):
        sync_to_durable_home(db_path, [], ritual="x")


# ---------------------------------------------------------------------------
# review findings (2026-08-11): gh step gating and sync commit scope
# ---------------------------------------------------------------------------


def test_reply_steps_gate_on_acceptance_and_stop_on_failure() -> None:
    from legesher_i18n.intake.commands import _reply_steps
    from legesher_i18n.intake.pipeline import ImportResult

    url = "https://github.com/legesher/legesher-next/issues/9"

    accepted = ImportResult(
        session_uid="ses_" + "a" * 24, status="accepted", report={}, source_ref=url
    )
    kinds = [what for _, what in _reply_steps(accepted, url)]
    assert kinds == ["comment", "label", "close"]

    # A returned submission is NOT imported: labelling it `contrib:imported`
    # and closing it would both be lies, but the report is worth sending.
    returned = ImportResult(
        session_uid=None, status="returned", report={"stages": []}, source_ref=url
    )
    assert [what for _, what in _reply_steps(returned, url)] == ["comment"]

    # A HALTED import posts NOTHING. It fired the withdrawal rule, and every
    # automated sentence available to say there discloses the withdrawal.
    # (This assertion previously read `== ["comment"]` — it encoded the leak.)
    halted = ImportResult(
        session_uid=None, status="halted", report={"stages": []}, source_ref=url
    )
    assert _reply_steps(halted, url) == []

    # And the target is an argument, never bundle content: with none supplied
    # the steps carry an empty URL rather than silently using source_ref.
    assert _reply_steps(accepted)[0][0][3] == ""


def test_a_failed_comment_aborts_the_remaining_gh_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from legesher_i18n.intake import commands
    from legesher_i18n.intake.pipeline import ImportResult

    attempted: list[str] = []

    def fake_run(argv, **kwargs):
        attempted.append(argv[2])  # comment | edit | close
        raise subprocess.CalledProcessError(1, argv, stderr="rate limited")

    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    result = ImportResult(
        session_uid="ses_" + "b" * 24,
        status="accepted",
        report={},
        source_ref="https://github.com/legesher/legesher-next/issues/9",
    )
    commands._post_reply(result, "https://github.com/legesher/legesher-next/issues/9")
    # Closing an issue whose "your contribution landed" reply never posted
    # leaves the contributor with silence and a closed issue.
    assert attempted == ["comment"]


def test_sync_commits_only_its_own_paths(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    remote = tmp_path / "remote2.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    home = tmp_path / "home2"
    subprocess.run(["git", "clone", "-q", str(remote), str(home)], check=True)
    for key, value in (("user.email", "t@example.invalid"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(home), "config", key, value], check=True)
    monkeypatch.setenv("LEGESHER_DATA_REPO", str(home))

    # Someone left unrelated work staged in the data repo — a half-finished
    # identity-map edit is exactly the file that must not ride an import.
    (home / "identity").mkdir()
    (home / "identity" / "contributor_identity_map.json").write_text(
        '{"work": "in progress"}', encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", str(home), "add", "identity/contributor_identity_map.json"],
        check=True,
    )

    sync_to_durable_home(db_path, [], ritual="review import [CORE-1688]")

    committed = subprocess.run(
        ["git", "-C", str(home), "show", "--name-only", "--format=", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert committed == [f"db/{db_path.name}"]
    # The unrelated file is still staged, uncommitted, unpushed.
    staged = subprocess.run(
        ["git", "-C", str(home), "diff", "--cached", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert staged == ["identity/contributor_identity_map.json"]


def test_a_missing_salt_is_a_clean_refusal_not_a_traceback(
    runner: CliRunner, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LEGESHER_CONTRIBUTOR_SALT", raising=False)
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "LEGESHER_CONTRIBUTOR_SALT" in result.output


# ---------------------------------------------------------------------------
# second review (2026-08-12): the reply must not disclose a withdrawal, and
# the gh target must never come from bundle content
# ---------------------------------------------------------------------------


def test_a_halted_import_posts_nothing_and_leaks_no_withdrawal(
    db_path: Path, tmp_path: Path
) -> None:
    from legesher_i18n.db.schema_v2 import contributor_id
    from legesher_i18n.intake.commands import _reply_steps
    from legesher_i18n.intake.pipeline import BundleImporter

    cid = contributor_id("cli-reviewer", salt=SALT)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (cid,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, withdrawn_at)"
        " VALUES (?, '2026-08-01')",
        (cid,),
    )
    conn.commit()
    conn.close()

    result = BundleImporter(db_path, salt=SALT).import_bundle(valid_bundle())
    assert result.status == "halted"

    # The withdrawal date is diagnostic for the MAINTAINER only. Posting it
    # would re-associate the person's public account with the withdrawal the
    # CORE-1780 tombstone exists to erase.
    reply = result.reply_text()
    assert "2026-08-01" not in reply
    assert "withdrew" not in reply.lower()
    assert "withdrawn" not in reply.lower()
    # And nothing is posted at all: a human decides what to say here.
    assert _reply_steps(result) == []
    # The maintainer still sees the full reason locally.
    assert any(
        "2026-08-01" in str(d)
        for stage in result.report["stages"]
        for d in stage["details"]
    )


def test_the_reply_target_never_comes_from_bundle_content(
    runner: CliRunner, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A submitter who sets source.url would otherwise get an arbitrary issue
    # commented, labelled and CLOSED under the maintainer's gh credentials.
    from legesher_i18n.intake import commands

    called: list[list[str]] = []
    monkeypatch.setattr(
        commands.subprocess,
        "run",
        lambda argv, **kw: (
            called.append(argv) or subprocess.CompletedProcess(argv, 0, "", "")
        ),
    )

    bundle = valid_bundle()
    bundle["source"] = {
        "kind": "github_issue",
        "url": "https://github.com/attacker/victim-repo/issues/1",
        "id": 1,
    }
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, bundle)),
            "--db",
            str(db_path),
            "--reply",
        ],
    )
    assert result.exit_code == 0, result.output
    assert called == []  # no gh invocation without a maintainer-supplied target
    assert "--reply-to" in result.output


@pytest.mark.parametrize(
    "bad",
    [
        "https://evil.example.com/legesher/legesher-next/issues/1",
        "https://github.com/legesher/legesher-next/pull/1",
        "--add-label=owned",
        "https://github.com/legesher/legesher-next/issues/notanumber",
        "not a url at all",
    ],
)
def test_reply_to_rejects_anything_that_is_not_a_github_issue_url(bad: str) -> None:
    from legesher_i18n.intake.commands import validated_issue_url

    with pytest.raises(ValueError):
        validated_issue_url(bad)


def test_reply_to_accepts_a_real_github_issue_url() -> None:
    from legesher_i18n.intake.commands import validated_issue_url

    url = "https://github.com/legesher/legesher-next/issues/42"
    assert validated_issue_url(url) == url


def test_clear_option_covers_held_rejected_and_the_error_paths(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
        ],
    )
    for verdict in ("held", "rejected", "cleared"):
        out = runner.invoke(
            cli,
            [
                "clear-option",
                NEW_OPT,
                "--verdict",
                verdict,
                "--by",
                "madi",
                "--db",
                str(db_path),
            ],
        )
        assert out.exit_code == 0, out.output
    # The vocabulary is closed, and an unknown option is a clean refusal.
    assert (
        runner.invoke(
            cli,
            [
                "clear-option",
                NEW_OPT,
                "--verdict",
                "approved",
                "--by",
                "madi",
                "--db",
                str(db_path),
            ],
        ).exit_code
        != 0
    )
    missing = runner.invoke(
        cli,
        [
            "clear-option",
            "opt_" + "0" * 24,
            "--verdict",
            "cleared",
            "--by",
            "madi",
            "--db",
            str(db_path),
        ],
    )
    assert missing.exit_code != 0
    assert "no option" in missing.output


def test_clear_option_refuses_to_withhold_a_canon_selected_word(
    runner: CliRunner, db_path: Path, tmp_path: Path
) -> None:
    runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
        ],
    )
    runner.invoke(
        cli,
        [
            "clear-option",
            NEW_OPT,
            "--verdict",
            "cleared",
            "--by",
            "madi",
            "--db",
            str(db_path),
        ],
    )
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
        " screen_version) VALUES (?, 'cleared', 'madi', 'manual-interim-v1')",
        (NEW_OPT,),
    )
    conn.execute(
        "INSERT INTO canon_selections(concept_id, locale, option_uid,"
        " surface_form, source_file) VALUES (1,'ur',?,'ورنہ_اگر',"
        " 'libs/i18n/canon/ur.toml')",
        (NEW_OPT,),
    )
    conn.commit()
    conn.close()
    held = runner.invoke(
        cli,
        [
            "clear-option",
            NEW_OPT,
            "--verdict",
            "held",
            "--by",
            "madi",
            "--db",
            str(db_path),
        ],
    )
    assert held.exit_code != 0
    assert "canon" in held.output  # a ClickException, not a traceback
    assert held.exception is None or isinstance(held.exception, SystemExit)


def test_sync_reports_a_failure_without_implying_the_import_was_lost(
    runner: CliRunner, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LEGESHER_DATA_REPO", raising=False)
    result = runner.invoke(
        cli,
        [
            "import-review-bundle",
            str(write_bundle(tmp_path, valid_bundle())),
            "--db",
            str(db_path),
            "--sync",
        ],
    )
    assert "SYNC FAILED" in result.output
    assert "do not" in result.output.lower()
    # The import itself stands.
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT status FROM review_sessions").fetchone() == (
        "accepted",
    )
    conn.close()


def test_sync_is_a_noop_when_nothing_changed(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    remote = tmp_path / "remote3.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    home = tmp_path / "home3"
    subprocess.run(["git", "clone", "-q", str(remote), str(home)], check=True)
    for k, v in (("user.email", "t@example.invalid"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(home), "config", k, v], check=True)
    monkeypatch.setenv("LEGESHER_DATA_REPO", str(home))

    assert sync_to_durable_home(db_path, [], ritual="first") is not None
    assert sync_to_durable_home(db_path, [], ritual="again") is None


def test_sync_refuses_a_directory_that_is_not_a_checkout(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    monkeypatch.setenv("LEGESHER_DATA_REPO", str(plain))
    with pytest.raises(RuntimeError, match="not a git checkout"):
        sync_to_durable_home(db_path, [], ritual="x")
