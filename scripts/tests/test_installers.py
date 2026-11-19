"""The one-line installers in ``install/`` (``install.sh`` and ``install.ps1``).

Three things are pinned in three places, and these tests hold them together:

- the uv release and the SHA-256 of each uv archive, which the VS Code
  extension pins too (``libs/vs-code/src/uvRelease.ts``);
- the exact version of every Python package, inline in both installers and in
  ``install/constraints.txt``, generated from ``install/requirements.in`` by
  ``scripts/update_installer_constraints.py``;
- the two tools' own pins, at the top of each installer.

The rest runs ``install.sh`` for real against stand-ins for ``uv``, ``code``,
``curl`` and ``uname`` on PATH, so no test touches the network. It guards the
four ways a shell installer commonly leaves a half-finished install: a path
with spaces split into words, a key press the host cannot give, a Windows
execution policy nobody mentions, and a PATH fix that points at the wrong
folder.

Run with:  uv run pytest scripts/tests -q
"""

from __future__ import annotations

import json
import os
import re
import shutil
import hashlib
import io
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / "install"
SH = INSTALL / "install.sh"
PS1 = INSTALL / "install.ps1"
CONSTRAINTS = INSTALL / "constraints.txt"
REQUIREMENTS = INSTALL / "requirements.in"
README = INSTALL / "README.md"
UV_RELEASE = REPO / "libs" / "vs-code" / "src" / "uvRelease.ts"

#: A home folder name with a space, Devanagari, Sinhala with a ZWJ and
#: vocalised Arabic: what a real user's folder can be called.
HOME_NAME = "home देवनागरी ශ්‍රී عَرَبِيّ"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Pins
# ---------------------------------------------------------------------------


def _extension_uv() -> tuple[str, dict[str, str]]:
    """The extension's pinned uv version and its checksum for each target triple."""
    text = _text(UV_RELEASE)
    version = re.search(r"export const UV_VERSION = '([^']+)';", text)
    assert version, f"no UV_VERSION in {UV_RELEASE}"
    pairs = re.findall(
        r"triple: '([^']+)',\s*archive: '[^']+',\s*sha256: '([0-9a-f]{64})'", text
    )
    assert pairs, f"no targets in {UV_RELEASE}"
    return version.group(1), dict(pairs)


def _sh_uv() -> tuple[str, dict[str, str]]:
    text = _text(SH)
    version = re.search(r'^UV_VERSION="([^"]+)"$', text, re.M)
    block = text.split("# BEGIN UV CHECKSUMS")[1].split("# END UV CHECKSUMS")[0]
    return version.group(1) if version else "", dict(
        re.findall(r'(\S+)\) echo "([0-9a-f]{64})"', block)
    )


def _ps1_uv() -> tuple[str, dict[str, str]]:
    text = _text(PS1)
    version = re.search(r"^\s*\$UvVersion = '([^']+)'$", text, re.M)
    block = text.split("# BEGIN UV CHECKSUMS")[1].split("# END UV CHECKSUMS")[0]
    return version.group(1) if version else "", dict(
        re.findall(r"'(\S+)' = '([0-9a-f]{64})'", block)
    )


def test_installers_pin_the_uv_release_the_extension_pins() -> None:
    version, extension = _extension_uv()
    for name, (pinned, table) in {
        "install.sh": _sh_uv(),
        "install.ps1": _ps1_uv(),
    }.items():
        assert pinned == version, (
            f"{name} pins uv {pinned!r}, the extension pins {version!r}"
        )
        for triple, sha256 in table.items():
            assert triple in extension, (
                f"{name} pins uv for {triple}, which the extension does not know"
            )
            assert sha256 == extension[triple], (
                f"{name} and {UV_RELEASE.name} disagree on uv for {triple}"
            )


def test_install_sh_covers_every_unix_target_the_cli_has_wheels_for() -> None:
    _, extension = _extension_uv()
    unix = {triple for triple in extension if not triple.endswith("windows-msvc")}
    # The CLI needs tree-sitter, which has no wheel for ARM64 musl; the
    # installer refuses it by name instead.
    assert set(_sh_uv()[1]) == unix - {"aarch64-unknown-linux-musl"}
    assert set(_ps1_uv()[1]) == {"x86_64-pc-windows-msvc"}


def _block(path: Path) -> str:
    match = re.search(
        r"^# BEGIN CONSTRAINTS\n(.*?)^# END CONSTRAINTS$", _text(path), re.S | re.M
    )
    assert match, f"no constraints block in {path.name}"
    return match.group(1)


def test_inline_constraints_match_the_generated_file() -> None:
    generated = _text(CONSTRAINTS)
    for script in (SH, PS1):
        assert _block(script) == generated, (
            f"{script.name}'s constraints differ from {CONSTRAINTS.name}; "
            "run: uv run python scripts/update_installer_constraints.py"
        )


def test_every_constraint_is_an_exact_pin() -> None:
    for line in _text(CONSTRAINTS).splitlines():
        spec = line.split(";")[0].strip()
        assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*==\S+", spec), (
            f"not an exact pin: {line!r}"
        )


def _requirement_pins() -> dict[str, str]:
    pins = {}
    for line in _text(REQUIREMENTS).splitlines():
        if line.strip() and not line.startswith("#"):
            name, version = line.strip().split("==")
            pins[name] = version
    return pins


# The versions the installers install, read from requirements.in so a bump
# needs no edit here.
CLI_VERSION = _requirement_pins()["legesher"]
SERVER_VERSION = _requirement_pins()["legesher-language-server"]
CLI_PIN = f"legesher=={CLI_VERSION}"
SERVER_PIN = f"legesher-language-server=={SERVER_VERSION}"


def test_tool_pins_agree_everywhere() -> None:
    pins = _requirement_pins()
    assert set(pins) == {"legesher", "legesher-language-server"}
    constraints = _text(CONSTRAINTS)
    sh = _text(SH)
    ps1 = _text(PS1)
    for name, version in pins.items():
        assert re.search(
            rf"^{re.escape(name)}=={re.escape(version)}$", constraints, re.M
        ), f"{CONSTRAINTS.name} does not pin {name}=={version}; regenerate it"
        assert f'"{name}=={version}"' in sh, (
            f"install.sh does not install {name}=={version}"
        )
        assert f"'{name}=={version}'" in ps1, (
            f"install.ps1 does not install {name}=={version}"
        )


# ---------------------------------------------------------------------------
# The scripts parse
# ---------------------------------------------------------------------------


def test_install_sh_parses() -> None:
    subprocess.run(["sh", "-n", str(SH)], check=True)


@pytest.mark.skipif(
    shutil.which("shellcheck") is None, reason="shellcheck is not installed"
)
def test_install_sh_passes_shellcheck() -> None:
    result = subprocess.run(
        ["shellcheck", "-s", "sh", str(SH)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout


@pytest.mark.skipif(
    shutil.which("pwsh") is None, reason="PowerShell (pwsh) is not installed"
)
def test_install_ps1_parses() -> None:
    script = (
        "$errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile($args[0], [ref]$null, [ref]$errors) | Out-Null; "
        "if ($errors) { $errors | ForEach-Object { $_.Message }; exit 1 }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", script, str(PS1)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# install.sh, run against stand-ins
# ---------------------------------------------------------------------------


def _executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _recorder() -> str:
    """A stand-in program that records how it was called, one JSON line per call."""
    return (
        f"#!{sys.executable}\n"
        "import json, os, shutil, sys\n"
        "name = os.path.basename(sys.argv[0])\n"
        "args = sys.argv[1:]\n"
        "with open(os.environ['STUB_LOG'], 'a', encoding='utf-8') as log:\n"
        "    log.write(json.dumps([name, *args], ensure_ascii=False) + '\\n')\n"
    )


def _uv_stub() -> str:
    """A stand-in for uv: records each call and answers the commands install.sh uses."""
    return _recorder() + (
        "if args[:2] == ['tool', 'install']:\n"
        "    shutil.copy(args[args.index('--constraints') + 1], os.environ['STUB_SEEN_CONSTRAINTS'])\n"
        "elif args[:3] == ['tool', 'dir', '--bin']:\n"
        "    print(os.environ['STUB_TOOL_BIN'])\n"
        "elif args[:2] == ['tool', 'update-shell']:\n"
        "    sys.exit(int(os.environ.get('STUB_UPDATE_SHELL_EXIT', '0')))\n"
        "elif args == ['--version']:\n"
        "    print('uv 0.13.7 (stand-in)')\n"
    )


class Sandbox:
    """A home folder, a temp folder and a PATH of stand-ins for one run of install.sh."""

    def __init__(self, root: Path, *, uv: bool = True, code: bool = True) -> None:
        self.home = root / HOME_NAME
        self.tmp = root / "tmp ශ්‍රී"
        self.stubs = root / "stubs"
        self.tool_bin = root / "tool bin देव"
        self.log = root / "calls.jsonl"
        self.seen_constraints = root / "seen-constraints.txt"
        for folder in (self.home, self.tmp, self.stubs, self.tool_bin):
            folder.mkdir(parents=True)
        self.env = {
            "HOME": str(self.home),
            "TMPDIR": str(self.tmp),
            "PATH": f"{self.stubs}:/usr/bin:/bin",
            "STUB_LOG": str(self.log),
            "STUB_TOOL_BIN": str(self.tool_bin),
            "STUB_SEEN_CONSTRAINTS": str(self.seen_constraints),
        }
        if uv:
            _executable(self.stubs / "uv", _uv_stub())
        if code:
            _executable(self.stubs / "code", _recorder())
        # No test reaches the network: downloads fail unless a test serves one.
        for downloader in ("curl", "wget"):
            _executable(
                self.stubs / downloader,
                "#!/bin/sh\necho 'network blocked in tests' >&2\nexit 97\n",
            )
        _executable(
            self.tool_bin / "legesher",
            f"#!/bin/sh\necho 'legesher, version {CLI_VERSION}'\n",
        )
        _executable(
            self.tool_bin / "legesher-lsp",
            f"#!/bin/sh\necho 'legesher-lsp {SERVER_VERSION}'\n",
        )

    def stub(self, name: str, body: str) -> None:
        _executable(self.stubs / name, body)

    def uv_release(self, triple: str) -> str:
        """Serve a uv release archive through a curl stand-in.

        Returns install.sh with that archive's checksum pinned in place of the
        real one, so the run installs uv from the archive (whose uv is the
        recording stand-in) and then drives it.
        """
        body = io.BytesIO()
        with tarfile.open(fileobj=body, mode="w:gz") as archive:
            data = _uv_stub().encode("utf-8")
            for program in ("uv", "uvx"):
                info = tarfile.TarInfo(f"uv-{triple}/{program}")
                info.size = len(data)
                # Not executable in the archive, so the test shows the script
                # makes uv runnable itself rather than relying on the archive.
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))
        served = self.home.parent / "served.tar.gz"
        served.write_bytes(body.getvalue())
        self.stub(
            "curl",
            f'#!/bin/sh\nwhile [ "$#" -gt 1 ]; do [ "$1" = -o ] && cp "{served}" "$2"; shift; done\n',
        )
        return _text(SH).replace(
            _sh_uv()[1][triple], hashlib.sha256(body.getvalue()).hexdigest()
        )

    def run(
        self, script: str | None = None, **extra: str
    ) -> subprocess.CompletedProcess[str]:
        # Piped into sh, as the one-liner does, with no terminal to answer.
        return subprocess.run(
            ["sh"],
            input=script if script is not None else _text(SH),
            env={**self.env, **extra},
            capture_output=True,
            text=True,
            timeout=120,
        )

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
        ]


def test_installs_both_tools_and_the_extension(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)
    result = sandbox.run()
    assert result.returncode == 0, result.stderr
    calls = sandbox.calls()
    installs = [call for call in calls if call[:3] == ["uv", "tool", "install"]]
    assert [call[-1] for call in installs] == [
        CLI_PIN,
        SERVER_PIN,
    ]
    for call in installs:
        assert call[3:7] == ["--python", "3.12", "--no-build", "--constraints"], call
    assert ["code", "--install-extension", "legesher.legesher-vscode"] in calls
    assert f"legesher, version {CLI_VERSION}" in result.stdout
    assert f"legesher-lsp {SERVER_VERSION}" in result.stdout


def test_a_path_with_spaces_and_any_script_reaches_uv_as_one_argument(
    tmp_path: Path,
) -> None:
    """Paths with spaces were split into words by unquoted expansions.

    The temp folder and the home folder here both have spaces and non-Latin
    names. The constraints file uv is given has to be one argument, an
    existing file, holding exactly the generated pins.
    """
    sandbox = Sandbox(tmp_path)
    result = sandbox.run()
    assert result.returncode == 0, result.stderr
    install = next(
        call for call in sandbox.calls() if call[:3] == ["uv", "tool", "install"]
    )
    constraints = install[install.index("--constraints") + 1]
    assert constraints.startswith(str(sandbox.tmp)), constraints
    assert sandbox.seen_constraints.read_text(encoding="utf-8") == (
        "# BEGIN CONSTRAINTS\n" + _text(CONSTRAINTS) + "# END CONSTRAINTS\n"
    )
    # The temp folder is cleaned up afterwards.
    assert list(sandbox.tmp.iterdir()) == []


def test_never_waits_for_a_key_or_an_answer() -> None:
    """Waiting on a key press crashed hosts without a console, after part of the install."""
    for script in (SH, PS1):
        text = _text(script)
        for waits in ("ReadKey", "Read-Host", "pause", "read -", 'read "'):
            assert waits not in text, f"{script.name} waits for input with {waits!r}"
    assert not re.search(r"^\s*read\s", _text(SH), re.M), (
        "install.sh reads from the terminal"
    )


def test_install_ps1_never_exits_the_window_it_runs_in() -> None:
    """Piped into iex, `exit` closes the user's PowerShell window and hides the error."""
    code = "\n".join(line.split("#")[0] for line in _text(PS1).splitlines())
    assert not re.search(r"(?i)\bexit\b", code), "install.ps1 calls exit; throw instead"


def test_the_windows_one_liner_says_how_to_get_past_the_execution_policy() -> None:
    """Windows' default execution policy refuses script files, and nothing said so."""
    one_liner = 'powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/legesher/legesher/main/install/install.ps1 | iex"'
    assert one_liner in _text(PS1)
    assert one_liner in _text(README)


def test_the_path_fix_names_the_folder_uv_reports(tmp_path: Path) -> None:
    """A PATH fix that names a folder the install did not use leaves the user stuck.

    The folder comes from `uv tool dir --bin`, and here that folder is unlike
    any the script could guess.
    """
    sandbox = Sandbox(tmp_path)
    result = sandbox.run(LEGESHER_NO_MODIFY_PATH="1")
    assert result.returncode == 0, result.stderr
    assert (
        f"add this folder to your PATH to run legesher and legesher-lsp: {sandbox.tool_bin}"
        in result.stdout
    )
    assert not any(
        call[:3] == ["uv", "tool", "update-shell"] for call in sandbox.calls()
    )


def test_updates_the_shell_through_uv_and_treats_already_done_as_done(
    tmp_path: Path,
) -> None:
    sandbox = Sandbox(tmp_path)
    # uv exits 1 when the shell files already add the folder, as on a re-run.
    result = sandbox.run(STUB_UPDATE_SHELL_EXIT="1")
    assert result.returncode == 0, result.stderr
    assert ["uv", "tool", "update-shell"] in sandbox.calls()
    assert "could not" not in result.stdout + result.stderr
    assert str(sandbox.tool_bin) in result.stdout


def test_refuses_a_uv_download_that_does_not_match_its_checksum(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path, uv=False)
    sandbox.stub(
        "uname", '#!/bin/sh\ncase "$1" in -s) echo Linux ;; -m) echo x86_64 ;; esac\n'
    )
    # A download that arrives, but with the wrong bytes.
    sandbox.stub(
        "curl",
        '#!/bin/sh\nwhile [ "$#" -gt 1 ]; do [ "$1" = -o ] && echo tampered > "$2"; shift; done\n',
    )
    result = sandbox.run()
    assert result.returncode != 0
    assert "did not match its pinned checksum" in result.stderr
    assert "nothing was installed" in result.stderr
    assert not (sandbox.home / ".local" / "bin" / "uv").exists()


@pytest.mark.parametrize(
    ("system", "machine", "message"),
    [
        ("FreeBSD", "x86_64", "this installer is for macOS and Linux"),
        ("Linux", "riscv64", "does not support the riscv64 processor"),
        ("MINGW64_NT-10.0", "x86_64", "on Windows use install.ps1"),
    ],
)
def test_says_plainly_where_it_does_not_install(
    tmp_path: Path, system: str, machine: str, message: str
) -> None:
    sandbox = Sandbox(tmp_path)
    sandbox.stub(
        "uname",
        f'#!/bin/sh\ncase "$1" in -s) echo {system} ;; -m) echo {machine} ;; esac\n',
    )
    result = sandbox.run()
    assert result.returncode != 0
    assert message in result.stderr
    assert "https://github.com/legesher/legesher#installation" in result.stderr
    assert sandbox.calls() == []


def test_without_vs_code_it_points_at_the_marketplace(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path, code=False)
    result = sandbox.run()
    assert result.returncode == 0, result.stderr
    assert (
        "marketplace.visualstudio.com/items?itemName=legesher.legesher-vscode"
        in result.stdout
    )


@pytest.mark.skipif(os.name == "nt", reason="install.sh is for macOS and Linux")
def test_a_failed_tool_install_stops_the_run(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)
    sandbox.stub(
        "uv",
        f"#!{sys.executable}\nimport sys\n"
        "if sys.argv[1:] == ['--version']:\n    print('uv 0.13.7')\n"
        "sys.exit(2 if sys.argv[1:3] == ['tool', 'install'] else 0)\n",
    )
    result = sandbox.run()
    assert result.returncode != 0
    assert f"uv could not install {CLI_PIN}" in result.stderr
    assert "done." not in result.stdout
    assert "network blocked" not in result.stderr


def test_installs_uv_itself_into_a_home_with_spaces_and_any_script(
    tmp_path: Path,
) -> None:
    """The download path: unpack, copy and use uv inside a spaced, non-Latin home."""
    sandbox = Sandbox(tmp_path, uv=False)
    sandbox.stub(
        "uname", '#!/bin/sh\ncase "$1" in -s) echo Linux ;; -m) echo x86_64 ;; esac\n'
    )
    sandbox.stub("ldd", "#!/bin/sh\necho 'ldd (GNU libc) 2.39'\n")
    result = sandbox.run(sandbox.uv_release("x86_64-unknown-linux-gnu"))
    assert result.returncode == 0, result.stderr
    installed = sandbox.home / ".local" / "bin"
    assert os.access(installed / "uv", os.X_OK) and os.access(
        installed / "uvx", os.X_OK
    )
    assert f"installed uv 0.13.7 in {installed}" in result.stdout
    installs = [
        call for call in sandbox.calls() if call[:3] == ["uv", "tool", "install"]
    ]
    assert [call[-1] for call in installs] == [
        CLI_PIN,
        SERVER_PIN,
    ]


def test_leaves_an_old_uv_alone_and_uses_the_pinned_one(tmp_path: Path) -> None:
    """An old uv lacks the tool commands; it is neither replaced nor used."""
    sandbox = Sandbox(tmp_path, uv=False)
    sandbox.stub(
        "uname", '#!/bin/sh\ncase "$1" in -s) echo Linux ;; -m) echo x86_64 ;; esac\n'
    )
    sandbox.stub("ldd", "#!/bin/sh\necho 'ldd (GNU libc) 2.39'\n")
    script = sandbox.uv_release("x86_64-unknown-linux-gnu")
    old = tmp_path / "old uv"
    old.mkdir()
    old_body = '#!/bin/sh\n[ "$1" = --version ] && echo "uv 0.4.30" && exit 0\necho "old uv ran: $*" >&2\nexit 9\n'
    _executable(old / "uv", old_body)
    result = sandbox.run(script, PATH=f"{sandbox.stubs}:{old}:/usr/bin:/bin")
    assert result.returncode == 0, result.stderr
    assert "is older than 0.5.0; using uv 0.13.7 for this install" in result.stdout
    assert "old uv ran" not in result.stderr
    assert (old / "uv").read_text(encoding="utf-8") == old_body
    assert not (sandbox.home / ".local" / "bin" / "uv").exists()
    assert (
        len([call for call in sandbox.calls() if call[:3] == ["uv", "tool", "install"]])
        == 2
    )


@pytest.mark.parametrize(
    ("ldd", "refused"),
    [("musl libc (aarch64)", True), ("ldd (Ubuntu GLIBC 2.39-0ubuntu8) 2.39", False)],
)
def test_asks_ldd_which_c_library_it_has(
    tmp_path: Path, ldd: str, refused: bool
) -> None:
    """A glibc system can have musl's loader installed beside it; ldd decides."""
    sandbox = Sandbox(tmp_path)
    sandbox.stub(
        "uname", '#!/bin/sh\ncase "$1" in -s) echo Linux ;; -m) echo aarch64 ;; esac\n'
    )
    sandbox.stub("ldd", f"#!/bin/sh\necho '{ldd}' >&2\nexit 1\n")
    result = sandbox.run()
    assert (
        "no ready-made build for ARM64 Linux with musl" in result.stderr
    ) is refused, result.stderr
    assert (result.returncode != 0) is refused, result.stderr
