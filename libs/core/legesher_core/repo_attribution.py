"""The opt-in repository label a client sends to the hosted service.

This is opt-in usage attribution: when the user switches it on, a client
attaches an ``X-Legesher-Repo`` header to its calls to Legesher's hosted
service, so usage can be attributed to a repository. The header's value is
a label derived from the repository, never the repository's name, path or
remote URL themselves.

Two switches gate it:

- Telemetry as a whole. ``LEGESHER_TELEMETRY_DISABLED`` or ``DO_NOT_TRACK``
  set in the environment (to anything but a false word), or
  ``telemetry.enabled`` set to ``false``, ``null`` or a false word such as
  ``"off"`` in the user's config, means no label at all.
- Repo attribution itself. Only ``telemetry.repo_attribution: true`` (the
  boolean, not a string) opts in; the default is off.

What the label is, and what it reveals:

- With an ``origin`` remote, the label is the first 32 hex characters of an
  unkeyed SHA-256 over ``LABEL_PREFIX`` plus the canonical remote (see
  :func:`canonical_remote`). Every clone of one repository produces the same
  label. The label is not secret: anyone who knows or guesses a remote URL
  can compute its label, so the label reveals whether a known remote is in
  use. It does not reveal a remote nobody can guess.
- Without a remote, the label is the same digest over a random salt minted
  once per install into ``~/.legesher/install-salt`` plus the repository's
  top-level path. Without the salt the path cannot be checked against the
  label. If the salt file is missing and cannot be created, or exists but
  is not exactly 32 lowercase hex characters, no label is produced.

:func:`repo_label` never raises: attribution is optional, and an exception
message could carry a remote URL with credentials in it.

The TypeScript twin is ``libs/vs-code/src/repoAttribution.ts``. Both are
pinned to ``libs/core/tests/fixtures/repo_attribution_vectors.json``.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import string
import subprocess
import unicodedata
from collections.abc import Mapping
from pathlib import Path

__all__ = [
    "HEADER",
    "LABEL_PREFIX",
    "canonical_remote",
    "label_for_remote",
    "repo_attribution_headers",
    "repo_attribution_opted_in",
    "repo_label",
    "telemetry_enabled",
]

#: The request header the hosted service reads (its value is this label).
HEADER = "X-Legesher-Repo"

#: Domain separation for the digest: a label can never collide with a digest
#: of the same string made for another purpose.
LABEL_PREFIX = "legesher-repo/v1:"

#: Length of the hex label (128 bits of the digest).
LABEL_HEX_LENGTH = 32

#: Environment variables that switch every kind of telemetry off.
KILL_SWITCHES = ("LEGESHER_TELEMETRY_DISABLED", "DO_NOT_TRACK")

#: Name of the per-install salt file under ``~/.legesher``.
SALT_FILENAME = "install-salt"

_FALSE_WORDS = frozenset({"0", "false", "no", "off", ""})

# Canonicalization is literal and must match the TypeScript twin character
# for character, so every rule below is spelled out rather than borrowed
# from a URL library (whose percent-encoding, IDNA and NFKC checks differ
# between languages).
_ASCII_WHITESPACE = " \t\n\r\x0b\x0c"
_ASCII_LOWER = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")
_WINDOWS_DRIVE = re.compile(r"[A-Za-z]:[/\\]")
_SALT = re.compile(r"[0-9a-f]{32}")
_SALT_READ_LIMIT = 64
_GIT_TIMEOUT_SECONDS = 10


def _word(value: str) -> str:
    """``value`` with ASCII whitespace trimmed and ASCII letters lowercased.

    ASCII only, so the TypeScript twin agrees: ``str.strip`` and JavaScript's
    ``trim`` disagree on a byte order mark and the information separators.
    """
    return value.strip(_ASCII_WHITESPACE).translate(_ASCII_LOWER)


def _is_set(value: str | None) -> bool:
    """Whether an environment value means "on" (anything but a false word)."""
    return value is not None and _word(value) not in _FALSE_WORDS


def _is_off(value: object) -> bool:
    """Whether a config value means "off": false, null, zero or a false word."""
    if value is None or value is False:
        return True
    if isinstance(value, str):
        return _word(value) in _FALSE_WORDS
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value == 0
    return False


def _telemetry_section(config: Mapping[str, object] | None) -> object:
    if not isinstance(config, Mapping):
        return None
    return config.get("telemetry")


def telemetry_enabled(
    config: Mapping[str, object] | None, *, env: Mapping[str, str] = os.environ
) -> bool:
    """Whether telemetry is on: no kill switch set, and the config allows it.

    ``config`` is the merged Legesher configuration mapping (the shape
    ``legesher.config.DEFAULT_CONFIG`` has); ``None`` means defaults. The
    kill switches win over any config. ``telemetry.enabled`` is off when it
    is ``False``, ``None``, zero or a false word (``"off"``, ``"no"``,
    ``"false"``, ``"0"``, empty), compared with ASCII whitespace trimmed and
    ASCII letters lowercased. A whole ``telemetry`` section written as
    ``false`` or a false word is off too; a ``null`` section reads as empty.
    """
    if any(_is_set(env.get(name)) for name in KILL_SWITCHES):
        return False
    telemetry = _telemetry_section(config)
    if isinstance(telemetry, Mapping):
        return not _is_off(telemetry.get("enabled", True))
    if telemetry is None:
        return True
    return not _is_off(telemetry)


def repo_attribution_opted_in(config: Mapping[str, object] | None) -> bool:
    """Whether the user opted into repo attribution (off by default).

    Only the boolean ``True`` opts in. A string such as ``"true"`` or
    ``"off"`` does not: consent is never inferred from a truthy value.
    """
    telemetry = _telemetry_section(config)
    if not isinstance(telemetry, Mapping):
        return False
    return telemetry.get("repo_attribution") is True


def _first_of(text: str, characters: str) -> int:
    """Index of the first of ``characters`` in ``text``, or ``len(text)``."""
    found = [index for index in map(text.find, characters) if index != -1]
    return min(found, default=len(text))


def _fold(text: str) -> str:
    """NFC, then ASCII A-Z lowercased, then NFC again.

    NFC comes first so a character that normalizes to an ASCII capital
    (KELVIN SIGN to ``K``) is lowercased too, and again last because
    lowercasing can make a composition possible (``W`` plus a combining ring
    has no precomposed form, ``w`` plus the ring does).
    """
    lowered = unicodedata.normalize("NFC", text).translate(_ASCII_LOWER)
    return unicodedata.normalize("NFC", lowered)


def _authority_host(authority: str) -> str | None:
    """The host of ``[userinfo@]host[:port]``; an IPv6 host keeps brackets."""
    host_port = authority[authority.rfind("@") + 1 :]
    if host_port.startswith("["):
        close = host_port.find("]")
        return host_port[: close + 1] if close != -1 else None
    colon = host_port.find(":")
    return host_port if colon == -1 else host_port[:colon]


def _split_remote(text: str) -> tuple[str, str] | None:
    """``(host, path)`` of a remote, or ``None`` for a local path."""
    if _WINDOWS_DRIVE.match(text):
        return None
    scheme = _SCHEME.match(text)
    if scheme:
        if scheme.group(0)[:-3].translate(_ASCII_LOWER) == "file":
            return None
        rest = text[scheme.end() :]
        authority_end = _first_of(rest, "/?#")
        tail = rest[authority_end:]
        host = _authority_host(rest[:authority_end])
        if host is None:
            return None
        return host, tail[: _first_of(tail, "?#")]
    # scp-like [user@]host:path, recognised as git does: a colon with no
    # slash before it. Anything else is a local path.
    colon = text.find(":")
    slash = text.find("/")
    if colon == -1 or (slash != -1 and slash < colon):
        return None
    start = text.rfind("@", 0, colon) + 1
    if text.startswith("[", start):
        close = text.find("]", start)
        if close == -1 or text[close + 1 : close + 2] != ":":
            return None
        return text[start : close + 1], text[close + 2 :]
    return text[start:colon], text[colon + 1 :]


def canonical_remote(url: str) -> str | None:
    """The canonical form of a remote URL, or ``None`` for a local path.

    The algorithm is literal, so the TypeScript twin produces the same
    string for the same input:

    1. Trim ASCII whitespace, drop one leading byte order mark, trim again.
    2. A single letter followed by ``:/`` or ``:\\`` is a Windows drive path,
       and a ``file://`` URL is local too: both return ``None``.
    3. ``scheme://[userinfo@]host[:port]/path[?query][#fragment]`` keeps the
       host and path. ``[user@]host:path`` (a colon with no slash before it)
       keeps the host and path. Anything else is a local path.
    4. The scheme, userinfo, port, query and fragment are dropped. An IPv6
       host keeps its brackets, ``[::1]``. An ``@`` still left in the host
       or path marks a malformed remote (``user:password@host:path``, which
       git reads as host ``user``) and returns ``None``, so a password can
       never reach the hashed string.
    5. Host and path are put in NFC, ASCII ``A``-``Z`` lowercased, and put
       in NFC again. No other character changes case.
    6. Leading and trailing slashes come off the path, then one trailing
       ``.git``, then trailing slashes again.

    Nothing is percent-decoded, percent-encoded or converted to or from
    punycode, and ``.`` and ``..`` segments stay. A string with a lone
    surrogate, or with no host or no path left, returns ``None``.
    """
    text = url.strip(_ASCII_WHITESPACE)
    if text.startswith("﻿"):
        text = text[1:].strip(_ASCII_WHITESPACE)
    if not text or any("\ud800" <= char <= "\udfff" for char in text):
        return None
    parts = _split_remote(text)
    if parts is None:
        return None
    host = _fold(parts[0])
    path = _fold(parts[1]).strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")].rstrip("/")
    if not host or not path or "@" in host or "@" in path:
        return None
    return f"{host}/{path}"


def _digest(material: bytes) -> str:
    return hashlib.sha256(LABEL_PREFIX.encode("ascii") + material).hexdigest()[
        :LABEL_HEX_LENGTH
    ]


def label_for_remote(url: str) -> str | None:
    """The label for a remote URL, or ``None`` when it has no canonical form.

    This is the remote half of :func:`repo_label` with no gates applied;
    the shared test vectors pin it.
    """
    canonical = canonical_remote(url)
    return _digest(canonical.encode("utf-8")) if canonical is not None else None


def _git_stdout(cwd: Path, *args: str) -> bytes | None:
    """``git -C cwd ARGS`` standard output, or ``None`` on any failure."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _work_tree_root(path: Path) -> Path | None:
    """The top level of the git work tree containing ``path``, if any."""
    out = _git_stdout(path, "rev-parse", "--show-toplevel")
    text = os.fsdecode(out).rstrip("\r\n") if out else ""
    return Path(text).resolve() if text else None


def _origin_url(work_tree: Path) -> str | None:
    """The ``origin`` remote URL, or ``None`` without one.

    A value that is not UTF-8 is treated as no remote (the salted fallback
    then applies) rather than decoded loosely.
    """
    out = _git_stdout(work_tree, "config", "--get", "remote.origin.url")
    if out is None:
        return None
    try:
        value = out.decode("utf-8").rstrip("\r\n")
    except UnicodeDecodeError:
        return None
    return value or None


def _read_salt(path: Path) -> str | None:
    """The salt in ``path`` if it is exactly 32 lowercase hex characters.

    Raises ``FileNotFoundError`` when there is no file and ``OSError`` when
    it cannot be read; returns ``None`` for a file that is not a salt.
    """
    with open(path, "rb") as handle:
        data = handle.read(_SALT_READ_LIMIT + 1)
    if len(data) > _SALT_READ_LIMIT:
        return None
    try:
        text = data.decode("ascii").strip(_ASCII_WHITESPACE)
    except UnicodeDecodeError:
        return None
    return text if _SALT.fullmatch(text) else None


def _mint_salt(directory: Path, path: Path) -> str | None:
    """Publish a new salt at ``path`` atomically, or ``None`` if one exists.

    The salt is written in full to a private temporary file first and then
    hard-linked into place. ``os.link`` fails when ``path`` exists, so a
    concurrent first run cannot overwrite another process's salt, and a
    reader never sees a half-written file.
    """
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    salt = secrets.token_hex(16)
    temporary = directory / f".{SALT_FILENAME}.{os.getpid()}.{secrets.token_hex(8)}"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            handle.write(salt + "\n")
        try:
            os.link(temporary, path)
        except FileExistsError:
            return None
        return salt
    finally:
        try:
            os.unlink(temporary)
        except OSError:
            pass


def _install_salt(home: Path) -> str | None:
    """The per-install salt from ``home/.legesher``, minted on first use.

    ``None`` when the salt cannot be read or created, or when the existing
    file is not a valid salt: an empty or guessable salt would turn the
    label into a plain hash of the repository's path, so the label is
    withheld instead. Deleting a damaged file lets the next run mint a new
    one.
    """
    directory = home / ".legesher"
    path = directory / SALT_FILENAME
    try:
        try:
            return _read_salt(path)
        except FileNotFoundError:
            pass
        minted = _mint_salt(directory, path)
        if minted is not None:
            return minted
        # Another process published a salt first: use the winner's.
        return _read_salt(path)
    except OSError:
        return None


def repo_label(
    repo_root: Path | None = None,
    *,
    config: Mapping[str, object] | None = None,
    env: Mapping[str, str] = os.environ,
    home: Path | None = None,
) -> str | None:
    """The attribution label for the repository at ``repo_root``, or ``None``.

    ``None`` whenever telemetry is off, repo attribution is not opted in,
    or no label can be produced safely, so a caller attaches the result
    only when it exists. ``repo_root`` may be any directory inside the
    work tree; the label is the same for all of them. Never raises.
    """
    try:
        if not telemetry_enabled(config, env=env):
            return None
        if not repo_attribution_opted_in(config):
            return None
        start = (Path(repo_root) if repo_root is not None else Path.cwd()).resolve()
        work_tree = _work_tree_root(start)
        remote = _origin_url(work_tree) if work_tree is not None else None
        label = label_for_remote(remote) if remote else None
        if label is not None:
            return label
        salt = _install_salt(home if home is not None else Path.home())
        if salt is None:
            return None
        root = work_tree if work_tree is not None else start
        return _digest(b"local:" + salt.encode("ascii") + b":" + os.fsencode(root))
    except Exception:  # the never-raise contract in the docstring above
        return None


def repo_attribution_headers(
    repo_root: Path | None = None,
    *,
    config: Mapping[str, object] | None = None,
    env: Mapping[str, str] = os.environ,
    home: Path | None = None,
) -> dict[str, str]:
    """``{"X-Legesher-Repo": label}`` when opted in, else an empty dict.

    Spread this into the headers of any call to the hosted service.
    """
    label = repo_label(repo_root, config=config, env=env, home=home)
    return {HEADER: label} if label else {}
