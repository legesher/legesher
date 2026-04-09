#!/usr/bin/env bash
# setup-dev.sh — One-time development environment setup for Legesher contributors
#
# Run this after cloning the repo:
#   bash scripts/setup-dev.sh
#
# What it does:
#   1. Configures repo-local git to auto-sign commits and add DCO sign-off
#   2. Installs pre-commit hooks
#   3. Syncs dependencies with uv
#   4. Verifies signing key is configured
#
# This is idempotent — safe to run multiple times.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || { echo "Error: not inside a git repository"; exit 1; })"
cd "$REPO_ROOT"

echo "==> Setting up development environment for Legesher"
echo "    Repository: $REPO_ROOT"
echo ""

# --- 1. Git config: auto-sign commits + DCO sign-off --------------------------
echo "==> Configuring git to auto-sign commits and add DCO sign-off (repo-local)"

git config --local commit.gpgsign true
git config --local format.signoff true

echo "    commit.gpgsign = true       (every 'git commit' is signed)"
echo "    format.signoff = true       (every 'git commit' adds DCO trailer)"

# --- 2. Verify signing key is configured --------------------------------------
signing_key="$(git config --get user.signingkey || echo '')"
gpg_format="$(git config --get gpg.format || echo 'openpgp')"

if [ -z "$signing_key" ]; then
  echo ""
  echo "    WARNING: no signing key configured in git."
  echo "    Configure one of:"
  echo "      git config --global user.signingkey ~/.ssh/your_key.pub"
  echo "      git config --global gpg.format ssh"
  echo "    OR for GPG:"
  echo "      git config --global user.signingkey <your-gpg-key-id>"
  echo ""
  echo "    See https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits"
else
  echo "    Using signing key: $signing_key (format: $gpg_format)"
fi

# --- 3. Verify author email is a GitHub noreply address -----------------------
author_email="$(git config --get user.email || echo '')"
case "$author_email" in
  *@users.noreply.github.com)
    echo "    Author email: $author_email (noreply — good)"
    ;;
  "")
    echo ""
    echo "    WARNING: no user.email configured."
    echo "    Set one with: git config --global user.email 'YOUR_ID+YOUR_USERNAME@users.noreply.github.com'"
    ;;
  *)
    echo ""
    echo "    WARNING: user.email is '$author_email' — consider using a GitHub noreply address"
    echo "    to keep your private email out of public commit history."
    echo "    See https://github.com/settings/emails"
    ;;
esac

# --- 4. Sync dependencies -----------------------------------------------------
# Sync first so `uv run pre-commit` is available in step 5.
if command -v uv >/dev/null 2>&1; then
  echo ""
  echo "==> Syncing dependencies with uv"
  uv sync
else
  echo ""
  echo "    WARNING: uv not found. Install from https://docs.astral.sh/uv/"
fi

# --- 5. Install pre-commit hooks ----------------------------------------------
# Prefer `uv run pre-commit` (installed via uv sync); fall back to global pre-commit.
pre_commit_cmd=""
if command -v uv >/dev/null 2>&1 && uv run pre-commit --version >/dev/null 2>&1; then
  pre_commit_cmd="uv run pre-commit"
elif command -v pre-commit >/dev/null 2>&1; then
  pre_commit_cmd="pre-commit"
fi

if [ -n "$pre_commit_cmd" ]; then
  echo ""
  echo "==> Installing pre-commit hooks ($pre_commit_cmd)"
  if ! $pre_commit_cmd install --install-hooks 2>&1; then
    echo "    WARNING: pre-commit install failed. If the error mentions 'core.hooksPath',"
    echo "    run: git config --unset-all core.hooksPath"
    echo "    Then re-run this script."
  fi
else
  echo ""
  echo "    WARNING: pre-commit not found. Install with 'uv sync' (if pre-commit is a dev dep)"
  echo "    or 'pip install pre-commit' and re-run this script."
fi

# --- 6. Verify git commit command is functional -------------------------------
# Note: --dry-run does NOT exercise signing, so this only validates that `git commit`
# runs at all. Actual signature verification requires a real commit + `git log --show-signature`.
echo ""
echo "==> Verifying git commit command is functional"
if git commit --allow-empty --dry-run -m "test" >/dev/null 2>&1; then
  echo "    OK: git commit dry-run succeeded"
else
  echo "    WARNING: git commit dry-run failed. Check your git config."
fi

echo ""
echo "==> Done. You're ready to contribute to Legesher."
echo ""
echo "    Every 'git commit' in this repo will now:"
echo "      - Be cryptographically signed (commit.gpgsign)"
echo "      - Include a DCO 'Signed-off-by' trailer (format.signoff)"
echo ""
echo "    No need to pass -S or -s manually."
