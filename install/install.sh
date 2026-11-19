#!/bin/sh
# Install Legesher on macOS or Linux in one line:
#
#     curl -LsSf https://raw.githubusercontent.com/legesher/legesher/main/install/install.sh | sh
#
# What it does, in order:
#   1. Finds uv (https://docs.astral.sh/uv/). When there is none, it downloads
#      the pinned uv release from GitHub, checks it against the SHA-256 below,
#      and puts uv and uvx in ~/.local/bin (or $UV_INSTALL_DIR).
#   2. Installs the legesher CLI and the legesher-lsp language server as uv
#      tools, on Python 3.12. Every package is pinned to an exact version by the
#      constraints below; uv checks each file it downloads against the SHA-256
#      the package index publishes for it, and builds nothing from source.
#   3. Puts uv's tool folder on PATH with `uv tool update-shell`, unless
#      LEGESHER_NO_MODIFY_PATH=1 is set, in which case it prints the folder.
#   4. Installs the VS Code extension when VS Code's `code` command is on PATH.
#
# It never asks a question and never needs a key press, so it also runs where
# there is no terminal to answer. Remove what it installed with:
#
#     uv tool uninstall legesher legesher-language-server
#
# After changing a pin, run: uv run python scripts/update_installer_constraints.py

set -eu

UV_VERSION="0.13.7"
# The oldest uv whose tool commands this relies on (tool install --constraints,
# tool dir --bin, tool update-shell).
UV_MINIMUM="0.5.0"
SERVER_PYTHON="3.12"
CLI_PIN="legesher==0.27.0"
SERVER_PIN="legesher-language-server==0.3.0"
EXTENSION_ID="legesher.legesher-vscode"
MANUAL_STEPS="https://github.com/legesher/legesher#installation"

say() {
    printf 'legesher: %s\n' "$*"
}

fail() {
    printf 'legesher: %s\n' "$*" >&2
    exit 1
}

# The SHA-256 of each uv release archive this installer may download. The same
# values pin the VS Code extension's own install (libs/vs-code/src/uvRelease.ts);
# scripts/tests/test_installers.py fails if the two ever differ.
# BEGIN UV CHECKSUMS
uv_sha256() {
    case "$1" in
        aarch64-apple-darwin) echo "81b811b57e4624df7ed3aac148e0359100d9962f3d9dce00aec533dc2e086731" ;;
        x86_64-apple-darwin) echo "20c47e4c1f630b8abaff8c291fa9b9aa300fef92c4fbff95adf198b55287cda7" ;;
        aarch64-unknown-linux-gnu) echo "71279f8d3c67241e807b9d8db872d1bf541579fb9f08b7d1eb1682196d1e57dc" ;;
        x86_64-unknown-linux-gnu) echo "c5221ff41b7892bfc223543883600125f6a47fe845093e0f5bdff4f359196d83" ;;
        x86_64-unknown-linux-musl) echo "287491da03f2a785c70fa75b13e1f849918c2f2b5415fe84876b8214eeb792f9" ;;
        *) echo "" ;;
    esac
}
# END UV CHECKSUMS

# Whether this Linux machine's C library is musl. ldd says which C library it
# belongs to; the musl loader alone is not enough, because a glibc system can
# have the musl package installed beside it.
is_musl() {
    if command -v ldd >/dev/null 2>&1; then
        case "$(ldd --version 2>&1 || true)" in
            *musl*) return 0 ;;
            *GLIBC* | *"GNU libc"* | *"GNU C Library"*) return 1 ;;
        esac
    fi
    [ -e /lib/ld-musl-x86_64.so.1 ] || [ -e /lib/ld-musl-aarch64.so.1 ]
}

# Which uv build this machine needs, or a reason it is not supported.
detect_target() {
    os=$(uname -s)
    arch=$(uname -m)
    case "$arch" in
        arm64 | aarch64) arch="aarch64" ;;
        x86_64 | amd64) arch="x86_64" ;;
        *) fail "this installer does not support the $arch processor. Install by hand: $MANUAL_STEPS" ;;
    esac
    case "$os" in
        Darwin) target="$arch-apple-darwin" ;;
        Linux)
            if is_musl; then
                target="$arch-unknown-linux-musl"
            else
                target="$arch-unknown-linux-gnu"
            fi
            ;;
        *) fail "this installer is for macOS and Linux; on Windows use install.ps1. Install by hand: $MANUAL_STEPS" ;;
    esac
    if [ "$target" = "aarch64-unknown-linux-musl" ]; then
        # The CLI needs tree-sitter, which publishes no build for this
        # platform, and this installer never compiles anything.
        fail "the legesher CLI has no ready-made build for ARM64 Linux with musl (Alpine). Install by hand: $MANUAL_STEPS"
    fi
}

# Whether the uv at $1 is at least UV_MINIMUM.
uv_is_recent() {
    version=$("$1" --version 2>/dev/null | cut -d ' ' -f 2) || return 1
    major=${version%%.*}
    rest=${version#*.}
    minor=${rest%%.*}
    case "$major$minor" in
        '' | *[!0-9]*) return 1 ;;
    esac
    want_rest=${UV_MINIMUM#*.}
    [ "$major" -gt "${UV_MINIMUM%%.*}" ] || { [ "$major" -eq "${UV_MINIMUM%%.*}" ] && [ "$minor" -ge "${want_rest%%.*}" ]; }
}

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum <"$1" | cut -d ' ' -f 1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 <"$1" | cut -d ' ' -f 1
    else
        fail "found neither sha256sum nor shasum, so uv's download cannot be checked; nothing was installed"
    fi
}

download() {
    if command -v curl >/dev/null 2>&1; then
        curl --proto '=https' --tlsv1.2 -fsSL -o "$2" "$1"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$2" "$1"
    else
        fail "found neither curl nor wget to download uv with"
    fi
}

# Download the pinned uv, check it, and put uv and uvx in $1.
install_uv() {
    bin_dir="$1"
    expected=$(uv_sha256 "$target")
    [ -n "$expected" ] || fail "no pinned uv build for $target. Install by hand: $MANUAL_STEPS"
    archive="$work/uv-$target.tar.gz"
    url="https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-$target.tar.gz"
    say "downloading uv $UV_VERSION from $url"
    download "$url" "$archive" || fail "could not download $url"
    actual=$(sha256_of "$archive")
    if [ "$actual" != "$expected" ]; then
        fail "uv's download did not match its pinned checksum (expected sha256 $expected, got $actual); nothing was installed"
    fi
    tar -xzf "$archive" -C "$work" || fail "could not unpack $archive"
    mkdir -p "$bin_dir"
    for program in uv uvx; do
        cp "$work/uv-$target/$program" "$bin_dir/$program.partial"
        chmod 755 "$bin_dir/$program.partial"
        mv -f "$bin_dir/$program.partial" "$bin_dir/$program"
    done
    say "installed uv $UV_VERSION in $bin_dir"
}

write_constraints() {
    # The exact version of every package the two tools need, for every
    # platform. Generated by scripts/update_installer_constraints.py from
    # install/requirements.in; do not edit by hand.
    cat >"$1" <<'CONSTRAINTS'
# BEGIN CONSTRAINTS
annotated-types==0.8.0
anthropic==2.10.0
anyio==4.16.0
attrs==26.1.0
cattrs==26.2.1
certifi==2026.10.23
click==8.5.1
docstring-parser==0.18.0
h11==0.16.0
httpcore==1.0.9
httpcore2==2.16.2 ; sys_platform != 'emscripten'
httpx==0.28.1
httpx2==2.16.2
httpx2-jsfetch==1.0 ; sys_platform == 'emscripten'
idna==3.20
jinja2==3.1.6
jiter==0.19.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
legesher==0.27.0
legesher-core==0.27.0
legesher-i18n==0.27.0
legesher-language-server==0.3.0
legesher-runtime==0.1.0
lru-dict==1.4.1
lsprotocol==2025.0.0
markdown-it-py==4.3.0
markupsafe==3.0.4
mdurl==0.1.2
ollama==0.6.3
opentelemetry-api==1.45.2
packaging==26.3
prompt-toolkit==3.0.53
pydantic==2.14.3
pydantic-core==2.50.4
pygls==2.1.1
pygments==2.21.0
pyyaml==6.0.3
questionary==2.1.1
referencing==0.37.0
rich==15.0.0
rpds-py==2026.9.1
sniffio==1.3.1
tree-sitter==0.26.1
tree-sitter-python==0.25.0
truststore==0.10.5 ; sys_platform != 'emscripten'
typing-extensions==4.16.0
typing-inspection==0.4.5
wcwidth==0.9.4
# END CONSTRAINTS
CONSTRAINTS
}

main() {
    detect_target

    # Named explicitly, because macOS mktemp ignores TMPDIR without a template.
    work=$(mktemp -d "${TMPDIR:-/tmp}/legesher.XXXXXXXX") || fail "could not make a temporary folder"
    trap 'rm -rf "$work"' EXIT

    uv_home="${UV_INSTALL_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
    uv=""
    if command -v uv >/dev/null 2>&1; then
        uv=$(command -v uv)
    elif [ -x "$uv_home/uv" ]; then
        uv="$uv_home/uv"
    fi
    if [ -n "$uv" ]; then
        if uv_is_recent "$uv"; then
            say "using the uv already installed at $uv"
        else
            # An older uv lacks the tool commands this needs. Leave it as it
            # is, and use the pinned uv from the temporary folder for this run.
            say "the uv at $uv is older than $UV_MINIMUM; using uv $UV_VERSION for this install. Update yours with: uv self update"
            install_uv "$work/uv"
            uv="$work/uv/uv"
        fi
    else
        install_uv "$uv_home"
        uv="$uv_home/uv"
    fi

    constraints="$work/constraints.txt"
    write_constraints "$constraints"
    for pin in "$CLI_PIN" "$SERVER_PIN"; do
        say "installing $pin"
        "$uv" tool install --python "$SERVER_PYTHON" --no-build --constraints "$constraints" "$pin" \
            || fail "uv could not install $pin"
    done

    # The folder uv puts tool commands in, as uv itself reports it.
    tool_bin=$(UV_NO_PROGRESS=1 "$uv" tool dir --bin) || fail "uv could not report its tool folder"
    say "checking the installed commands"
    "$tool_bin/legesher" --version || fail "the installed legesher command did not run"
    "$tool_bin/legesher-lsp" --version || fail "the installed legesher-lsp command did not run"

    case ":${PATH}:" in
        *":$tool_bin:"*) ;;
        *)
            if [ "${LEGESHER_NO_MODIFY_PATH:-0}" = "1" ]; then
                say "add this folder to your PATH to run legesher and legesher-lsp: $tool_bin"
            else
                # uv exits non-zero when the shell files already add the
                # folder, which is a success here, so its answer is not
                # treated as a failure. What to do next is the same either way.
                "$uv" tool update-shell >/dev/null 2>&1 || true
                say "open a new terminal to run legesher and legesher-lsp; if they are still not found, add this folder to your PATH: $tool_bin"
            fi
            ;;
    esac

    if command -v code >/dev/null 2>&1; then
        say "installing the VS Code extension"
        code --install-extension "$EXTENSION_ID" \
            || say "VS Code did not install the extension; install $EXTENSION_ID from the Extensions view"
    else
        say "VS Code's code command was not found; install the extension from https://marketplace.visualstudio.com/items?itemName=$EXTENSION_ID"
    fi

    say "done. If VS Code was open, restart it so it finds legesher-lsp."
    say "remove it all with: \"$uv\" tool uninstall legesher legesher-language-server"
}

main "$@"
