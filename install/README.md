# One-line installers

> **Audience:** Users, who install and use Legesher.

Install the Legesher CLI (`legesher`), the language server (`legesher-lsp`) and,
when VS Code's `code` command is on your PATH, the VS Code extension.

macOS and Linux:

```bash
curl -LsSf https://raw.githubusercontent.com/legesher/legesher/main/install/install.sh | sh
```

Windows, from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/legesher/legesher/main/install/install.ps1 | iex"
```

`-ExecutionPolicy Bypass` applies to that one command only. Windows' default
policy refuses to run script files, and this runs the installer without
changing the policy for anything else.

## What they do

1. Find [uv](https://docs.astral.sh/uv/). When there is none, download the
   pinned uv release from GitHub, check it against a SHA-256 written in the
   script, and put it in `~/.local/bin` (`%USERPROFILE%\.local\bin` on
   Windows), or in `UV_INSTALL_DIR` when you set it.
2. Install `legesher` and `legesher-language-server` as uv tools on Python
   3.12. uv downloads Python when the machine has no 3.12 and checks it against
   the checksums built into uv. Every Python package is pinned to an exact
   version (`constraints.txt`, which each script carries inline). uv checks
   each file against the SHA-256 the package index publishes for it, and builds
   nothing from source.
3. Put uv's tool folder on your PATH with `uv tool update-shell`. Set
   `LEGESHER_NO_MODIFY_PATH=1` to skip that; the script then prints the folder.
4. Install the VS Code extension from the Marketplace with
   `code --install-extension legesher.legesher-vscode`. VS Code keeps it
   updated, and the extension uses the `legesher-lsp` this installed. If VS
   Code was already open, restart it so it sees the new PATH.

An existing uv is used when it is 0.5.0 or newer. An older one is left as it is,
and the pinned uv runs from a temporary folder for this install. The scripts
honour `UV_INSTALL_DIR`, and `install.sh` also `XDG_BIN_HOME`, for where uv
goes.

They ask no questions and never wait for a key press. Run either again to
update to the versions it pins.

To remove what they installed:

```bash
uv tool uninstall legesher legesher-language-server
```

## Where they do not install

- **ARM64 Linux with musl (Alpine).** `tree-sitter`, which the CLI needs, has no
  ready-made build for it.
- **Windows on ARM.** `lru-dict`, which the language server needs, has no
  ready-made build for it.

Both installers stop there with a message, before changing anything. Install by
hand on those: see [Installation](../README.md#installation).

## Changing a pinned version

> **Audience:** Maintainers, who run releases, regenerate packs and write to the translations database.

Edit `requirements.in`, then regenerate the pins in `constraints.txt` and in
both scripts:

```bash
uv run python scripts/update_installer_constraints.py
```

The pinned uv and its checksums are the ones the VS Code extension pins
(`libs/vs-code/src/uvRelease.ts`). `scripts/tests/test_installers.py` fails when
any of these copies disagree.
