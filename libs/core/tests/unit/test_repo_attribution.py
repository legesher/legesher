"""The repo attribution label: a hash when opted in, nothing otherwise.

No raw repository name, path or remote URL may leave the helper. The
tests pin the opt-in gates, the literal canonicalization shared with the
TypeScript twin (through one vector file both suites load), the salted
per-install fallback and its salt file, and the never-raise contract.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import unicodedata
from pathlib import Path

import pytest

from legesher_core import repo_attribution as ra

HEX32 = re.compile(r"^[0-9a-f]{32}$")
OPTED_IN = {"telemetry": {"enabled": True, "repo_attribution": True}}

VECTORS_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "repo_attribution_vectors.json"
)
VECTORS = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
BY_NAME = {vector["name"]: vector for vector in VECTORS["vectors"]}

ROOT_BYPASSES_CHMOD = pytest.mark.skipif(
    getattr(os, "geteuid", lambda: 1)() == 0,
    reason="root bypasses chmod; act and some self-hosted runners run as root",
)
POSIX_PERMISSIONS = pytest.mark.skipif(
    sys.platform == "win32", reason="chmod doesn't restrict access on Windows"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _sha_label(material: bytes) -> str:
    return hashlib.sha256(material).hexdigest()[:32]


def _unsalted(root: Path) -> str:
    """The label an empty salt would give: a plain hash of the path."""
    return _sha_label(b"legesher-repo/v1:local::" + os.fsencode(root.resolve()))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "my-private-project"
    path.mkdir()
    _git(path, "init", "-q", "-b", "trunk")
    return path


# -- shared vectors: the Python and TypeScript helpers agree ----------------


def test_the_vector_file_matches_this_module() -> None:
    assert VECTORS["label_prefix"] == ra.LABEL_PREFIX
    assert VECTORS["label_hex_length"] == ra.LABEL_HEX_LENGTH
    assert len(BY_NAME) == len(VECTORS["vectors"]), "vector names must be unique"


@pytest.mark.parametrize("vector", VECTORS["vectors"], ids=lambda v: v["name"])
def test_shared_vector(vector: dict) -> None:
    assert ra.canonical_remote(vector["input"]) == vector["canonical"]
    assert ra.label_for_remote(vector["input"]) == vector["label"]
    if vector["canonical"] is not None:
        canonical = vector["canonical"]
        assert unicodedata.is_normalized("NFC", canonical)
        assert vector["label"] == _sha_label(
            (ra.LABEL_PREFIX + canonical).encode("utf-8")
        )


@pytest.mark.parametrize("group", sorted(VECTORS["same_label"]))
def test_every_spelling_in_a_group_gets_one_label(group: str) -> None:
    members = [BY_NAME[name] for name in VECTORS["same_label"][group]]
    assert len({m["input"] for m in members}) == len(members)
    labels = {ra.label_for_remote(m["input"]) for m in members}
    assert len(labels) == 1
    (label,) = labels
    assert label is not None and HEX32.match(label)


@pytest.mark.parametrize(
    "pair", VECTORS["different_label"], ids=lambda pair: " vs ".join(pair)
)
def test_literal_differences_stay_different(pair: list[str]) -> None:
    first, second = (ra.label_for_remote(BY_NAME[name]["input"]) for name in pair)
    assert first is not None and second is not None and first != second


def test_the_nfc_and_nfd_vectors_really_differ() -> None:
    nfc = BY_NAME["vocalised Arabic, NFC"]["input"]
    nfd = BY_NAME["vocalised Arabic, NFD"]["input"]
    assert nfc != nfd
    assert unicodedata.is_normalized("NFC", nfc)
    assert not unicodedata.is_normalized("NFC", nfd)
    assert not unicodedata.is_normalized(
        "NFC", BY_NAME["Sinhala with ZWJ, NFD"]["input"]
    )
    assert "\u200d" in BY_NAME["Sinhala with ZWJ, NFC"]["canonical"]


# -- the label is a one-way digest of the canonical remote ------------------


def test_the_label_is_the_exact_digest_not_an_encoding(
    repo: Path, tmp_path: Path
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/my-private-project.git")
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "home")
    assert label is not None and HEX32.match(label)
    canonical = b"github.com/org/my-private-project"
    material = b"legesher-repo/v1:" + canonical
    assert label == hashlib.sha256(material).hexdigest()[:32]
    for encoded in (
        material.hex(),
        canonical.hex(),
        base64.b64encode(material).decode(),
        base64.urlsafe_b64encode(material).decode(),
        base64.b32encode(material).decode().lower(),
    ):
        assert label != encoded[:32]
    decoded = bytes.fromhex(label).decode("latin-1").lower()
    for secret in ("my-private-project", "private", "org", "github", str(repo)):
        assert secret.lower() not in label
        assert secret.lower() not in decoded


def test_every_clone_of_one_repository_agrees(repo: Path, tmp_path: Path) -> None:
    _git(repo, "remote", "add", "origin", "git@GitHub.com:Org/Repo.git")
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "home")
    assert label == _sha_label(b"legesher-repo/v1:github.com/org/repo")
    clone = tmp_path / "elsewhere" / "clone-of-the-same"
    clone.mkdir(parents=True)
    _git(clone, "init", "-q", "-b", "trunk")
    _git(clone, "remote", "add", "origin", "https://github.com/org/repo.git")
    assert ra.repo_label(clone, config=OPTED_IN, env={}, home=tmp_path / "h2") == label


# -- the opt-in gates -------------------------------------------------------


def test_attribution_is_off_by_default(repo: Path, tmp_path: Path) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/Repo.git")
    assert ra.repo_label(repo, config=None, env={}, home=tmp_path / "home") is None
    assert (
        ra.repo_label(
            repo, config={"telemetry": {"enabled": True}}, env={}, home=tmp_path
        )
        is None
    )
    assert ra.repo_attribution_headers(repo, config=None, env={}, home=tmp_path) == {}


@pytest.mark.parametrize(
    "value", ["true", "True", "yes", "on", "1", "off", "no", "false", 1, [True]]
)
def test_only_the_boolean_true_opts_in(
    repo: Path, tmp_path: Path, value: object
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/Repo.git")
    config = {"telemetry": {"enabled": True, "repo_attribution": value}}
    assert ra.repo_attribution_opted_in(config) is False
    assert ra.repo_label(repo, config=config, env={}, home=tmp_path) is None


@pytest.mark.parametrize(
    "value", [False, None, 0, "off", "no", "false", "0", "", " OFF ", "False", "No"]
)
def test_telemetry_enabled_false_words_switch_it_off(
    repo: Path, tmp_path: Path, value: object
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/Repo.git")
    config = {"telemetry": {"enabled": value, "repo_attribution": True}}
    assert ra.telemetry_enabled(config, env={}) is False
    assert ra.repo_label(repo, config=config, env={}, home=tmp_path) is None


@pytest.mark.parametrize("section", [False, "off", "no", 0])
def test_a_telemetry_section_written_as_off_is_off(section: object) -> None:
    assert ra.telemetry_enabled({"telemetry": section}, env={}) is False
    assert ra.repo_attribution_opted_in({"telemetry": section}) is False


def test_a_null_telemetry_section_reads_as_empty() -> None:
    assert ra.telemetry_enabled({"telemetry": None}, env={}) is True
    assert ra.repo_attribution_opted_in({"telemetry": None}) is False


@pytest.mark.parametrize("switch", ["LEGESHER_TELEMETRY_DISABLED", "DO_NOT_TRACK"])
@pytest.mark.parametrize("value", ["1", "true", "yes", "anything"])
def test_a_kill_switch_wins_over_an_opted_in_config(
    repo: Path, tmp_path: Path, switch: str, value: str
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/Repo.git")
    assert (
        ra.repo_label(repo, config=OPTED_IN, env={switch: value}, home=tmp_path) is None
    )
    assert ra.telemetry_enabled(OPTED_IN, env={switch: value}) is False


@pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
def test_a_false_word_does_not_trip_the_kill_switch(value: str) -> None:
    assert ra.telemetry_enabled(OPTED_IN, env={"DO_NOT_TRACK": value}) is True


@pytest.mark.parametrize("switch", ra.KILL_SWITCHES)
@pytest.mark.parametrize(
    "case", VECTORS["kill_switch"], ids=lambda case: repr(case["value"])
)
def test_shared_kill_switch_value(switch: str, case: dict) -> None:
    """The TypeScript suite reads the same values: one trim rule, ASCII only.

    Includes a leading BOM and the information separators, which Python's
    ``str.strip`` and JavaScript's ``trim`` used to treat differently.
    """
    assert ra.telemetry_enabled(OPTED_IN, env={switch: case["value"]}) is (
        not case["set"]
    )


@pytest.mark.parametrize("value", ["\ufeff0", "\x1c0", "0\x1f"])
def test_only_ascii_whitespace_is_trimmed_from_a_kill_switch(value: str) -> None:
    assert value in {case["value"] for case in VECTORS["kill_switch"]}
    assert ra.telemetry_enabled(OPTED_IN, env={"DO_NOT_TRACK": value}) is False


def test_headers_carry_the_label_under_the_documented_name(
    repo: Path, tmp_path: Path
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:Org/Repo.git")
    headers = ra.repo_attribution_headers(repo, config=OPTED_IN, env={}, home=tmp_path)
    assert list(headers) == ["X-Legesher-Repo"]
    assert HEX32.match(headers["X-Legesher-Repo"])


# -- no remote: a per-install label ----------------------------------------


def test_a_repo_without_a_remote_gets_a_stable_per_install_label(
    repo: Path, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    first = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    second = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    assert first is not None and HEX32.match(first) and first == second
    salt_file = home / ".legesher" / "install-salt"
    salt = salt_file.read_text()
    assert re.fullmatch(r"[0-9a-f]{32}\n", salt)
    assert first == _sha_label(
        b"legesher-repo/v1:local:"
        + salt.strip().encode()
        + b":"
        + os.fsencode(repo.resolve())
    )
    assert first != _unsalted(repo)
    assert str(repo) not in first and salt.strip() not in first
    # Only the salt is left behind: no temporary files.
    assert sorted(p.name for p in (home / ".legesher").iterdir()) == ["install-salt"]
    # Another install (another salt) labels the same path differently.
    other = ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "other-home")
    assert other is not None and other != first


@POSIX_PERMISSIONS
def test_the_salt_file_is_private(repo: Path, tmp_path: Path) -> None:
    home = tmp_path / "home"
    assert ra.repo_label(repo, config=OPTED_IN, env={}, home=home) is not None
    mode = stat.S_IMODE((home / ".legesher" / "install-salt").stat().st_mode)
    assert mode == 0o600


def test_a_repo_root_and_its_subdirectory_share_one_label(
    repo: Path, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    (repo / "src" / "deep").mkdir(parents=True)
    at_root = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    in_src = ra.repo_label(repo / "src", config=OPTED_IN, env={}, home=home)
    deeper = ra.repo_label(repo / "src" / "deep", config=OPTED_IN, env={}, home=home)
    assert at_root is not None and at_root == in_src == deeper


def test_the_working_directory_is_the_default_root(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    (repo / "src").mkdir()
    expected = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    monkeypatch.chdir(repo / "src")
    assert ra.repo_label(config=OPTED_IN, env={}, home=home) == expected


def test_outside_git_still_yields_a_per_install_label(tmp_path: Path) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    label = ra.repo_label(plain, config=OPTED_IN, env={}, home=tmp_path / "home")
    assert label is not None and HEX32.match(label)


def test_a_local_path_remote_takes_the_salted_fallback(
    repo: Path, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    no_remote = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    _git(repo, "remote", "add", "origin", "C:/Users/alice/repo")
    assert ra.repo_label(repo, config=OPTED_IN, env={}, home=home) == no_remote


@pytest.mark.parametrize(
    ("remote", "malformed_canonical"),
    [
        ("user:hunter2@github.com:acme/repo.git", "user/hunter2@github.com:acme/repo"),
        ("https://user:p/ss@github.com/acme/repo.git", "user/ss@github.com/acme/repo"),
    ],
)
def test_a_password_in_a_malformed_remote_never_reaches_the_hash(
    repo: Path, tmp_path: Path, remote: str, malformed_canonical: str
) -> None:
    home = tmp_path / "home"
    no_remote = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    _git(repo, "remote", "add", "origin", remote)
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    assert ra.canonical_remote(remote) is None
    assert label == no_remote, "the salted per-install fallback applies"
    assert label != _sha_label(
        b"legesher-repo/v1:" + malformed_canonical.encode("utf-8")
    )


# -- the salt file: atomic, validated, and never fatal ----------------------


def test_a_concurrent_first_run_mints_one_salt(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every thread passes the "no salt yet" check before any of them mints.

    The barrier sits in front of the first random draw each thread makes,
    which any minting implementation needs, so the race is forced rather
    than left to the scheduler.
    """
    threads = 12
    home = tmp_path / "home"
    barrier = threading.Barrier(threads, timeout=10)
    first_draw = threading.local()
    real_token_hex = ra.secrets.token_hex

    def token_hex(nbytes: int | None = None) -> str:
        if not getattr(first_draw, "done", False):
            first_draw.done = True
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass
        return real_token_hex(nbytes)

    monkeypatch.setattr(ra.secrets, "token_hex", token_hex)
    labels: list[str | None] = [None] * threads

    def run(index: int) -> None:
        labels[index] = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)

    workers = [threading.Thread(target=run, args=(i,)) for i in range(threads)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert len(set(labels)) == 1, labels
    salt = (home / ".legesher" / "install-salt").read_text().strip()
    assert re.fullmatch(r"[0-9a-f]{32}", salt)
    assert labels[0] == _sha_label(
        b"legesher-repo/v1:local:" + salt.encode() + b":" + os.fsencode(repo.resolve())
    )
    assert sorted(p.name for p in (home / ".legesher").iterdir()) == ["install-salt"]


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"  \n",
        b"x",
        b"\n\n",
        b"0" * 31,
        b"0" * 33,
        b"ABCDEF0123456789ABCDEF0123456789",
        b"g" * 32,
        b"0123456789abcdef0123456789abcdef extra",
        b"\xff" * 32,
        b"0123456789abcdef" * 8,
    ],
    ids=repr,
)
def test_a_damaged_salt_file_never_gives_an_unsalted_label(
    repo: Path, tmp_path: Path, content: bytes
) -> None:
    home = tmp_path / "home"
    (home / ".legesher").mkdir(parents=True)
    salt_file = home / ".legesher" / "install-salt"
    salt_file.write_bytes(content)
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    assert label is None
    assert label != _unsalted(repo)
    assert salt_file.read_bytes() == content, "a damaged salt is not silently replaced"


def test_a_salt_written_before_this_change_is_still_accepted(
    repo: Path, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    (home / ".legesher").mkdir(parents=True)
    salt = "0123456789abcdef0123456789abcdef"
    (home / ".legesher" / "install-salt").write_text(salt + "\n")
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    assert label == _sha_label(
        b"legesher-repo/v1:local:" + salt.encode() + b":" + os.fsencode(repo.resolve())
    )


@POSIX_PERMISSIONS
@ROOT_BYPASSES_CHMOD
def test_an_unreadable_salt_file_gives_no_label(repo: Path, tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".legesher").mkdir(parents=True)
    salt_file = home / ".legesher" / "install-salt"
    salt_file.write_text("0123456789abcdef0123456789abcdef\n")
    salt_file.chmod(0)
    try:
        assert ra.repo_label(repo, config=OPTED_IN, env={}, home=home) is None
    finally:
        salt_file.chmod(0o600)


def test_a_legesher_file_where_the_directory_should_be_gives_no_label(
    repo: Path, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / ".legesher").write_text("not a directory")
    assert ra.repo_label(repo, config=OPTED_IN, env={}, home=home) is None


@POSIX_PERMISSIONS
@ROOT_BYPASSES_CHMOD
def test_a_read_only_home_gives_no_label(repo: Path, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    home.chmod(0o500)
    try:
        assert ra.repo_label(repo, config=OPTED_IN, env={}, home=home) is None
        assert not (home / ".legesher").exists()
    finally:
        home.chmod(0o700)


# -- never raises, never echoes ---------------------------------------------


@pytest.mark.parametrize(
    "remote",
    [
        "https://alice:s3cr3t\ufe6b@github.com/acme/repo.git",
        "https://[github.com/owner/repo",
        "https://alice:s3cr3t@[github.com/owner/repo",
    ],
)
def test_a_hostile_remote_never_raises_or_leaks(
    repo: Path, tmp_path: Path, remote: str
) -> None:
    _git(repo, "remote", "add", "origin", remote)
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "home")
    assert label is None or HEX32.match(label)
    assert "s3cr3t" not in (label or "")
    assert "s3cr3t" not in str(
        ra.repo_attribution_headers(
            repo, config=OPTED_IN, env={}, home=tmp_path / "home"
        )
    )


def test_a_remote_that_is_not_utf8_never_raises(repo: Path, tmp_path: Path) -> None:
    config_file = repo / ".git" / "config"
    config_file.write_bytes(
        config_file.read_bytes()
        + b'[remote "origin"]\n\turl = https://alice:p\xe4ss@git.example.com/acme/secret.git\n'
    )
    home = tmp_path / "home"
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=home)
    assert label is not None and HEX32.match(label)
    # Undecodable means no usable remote: the salted fallback applies.
    salt = (home / ".legesher" / "install-salt").read_text().strip()
    assert label == _sha_label(
        b"legesher-repo/v1:local:" + salt.encode() + b":" + os.fsencode(repo.resolve())
    )


def test_an_exception_inside_the_helper_never_escapes(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(repo, "remote", "add", "origin", "https://alice:s3cr3t@github.com/acme/r.git")

    def explode(url: str) -> str:
        raise ValueError(f"cannot parse {url}")

    monkeypatch.setattr(ra, "canonical_remote", explode)
    assert ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "h") is None
    assert (
        ra.repo_attribution_headers(repo, config=OPTED_IN, env={}, home=tmp_path / "h")
        == {}
    )


def test_git_missing_or_failing_falls_back_without_raising(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_git(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git")

    monkeypatch.setattr(ra.subprocess, "run", no_git)
    label = ra.repo_label(repo, config=OPTED_IN, env={}, home=tmp_path / "home")
    assert label is not None and HEX32.match(label)
