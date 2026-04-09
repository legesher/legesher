#!/usr/bin/env bash
# block-push-to-main.sh
#
# Claude Code PreToolUse hook that blocks direct pushes to main/master.
# Invoked by .claude/settings.json on every Bash tool call.
#
# Enforces the workflow rule: every change must go through a branch + PR,
# even trivial ones. See MEMORY.md for rationale.
#
# Input:  JSON payload on stdin with .tool_input.command
# Output: exit 0 to allow, exit 2 (with stderr message) to block
#
# Tested edge cases (28 tests, all passing as of 2026-04-09):
#
# Explicit main/master (ALWAYS BLOCK, regardless of current branch):
#   git push origin main                  -> BLOCK (explicit)
#   git push origin master                -> BLOCK (explicit)
#   git push -f origin main               -> BLOCK (explicit)
#   git push origin HEAD:main             -> BLOCK (refspec-head)
#   git push origin HEAD:refs/heads/main  -> BLOCK (refspec)
#
# Bare push (BLOCK only if current branch IS main/master):
#   git push                              -> BLOCK on main, ALLOW on feature
#   git push -v                           -> BLOCK on main, ALLOW on feature
#   git push --force                      -> BLOCK on main, ALLOW on feature
#   git push --force-with-lease           -> BLOCK on main, ALLOW on feature
#   git push -v origin                    -> BLOCK on main, ALLOW on feature
#   git push -u origin                    -> BLOCK on main, ALLOW on feature
#
# Pushing a feature branch (ALLOW, even from main):
#   git push -u origin my-branch          -> ALLOW
#   git push -v -u origin feature/foo     -> ALLOW
#   git push origin my-main-branch        -> ALLOW (no false positive on "main" substring)
#   git push origin feature/mainly-done   -> ALLOW (no false positive)
#
# Bypass and non-push commands:
#   git push --dry-run origin main        -> ALLOW (dry-run exception)
#   git commit -m "foo"                   -> ALLOW (not a push)

set -e

cmd="$(jq -r '.tool_input.command // ""')"

# Not a git push → allow
case "$cmd" in
  "git push" | "git push "*) : ;;
  *) exit 0 ;;
esac

# Dry run → allow
case "$cmd" in
  *--dry-run*) exit 0 ;;
esac

target=""

# Case 1: explicit "main" or "master" as a token in the command
# Matches: "git push origin main", "git push -f origin master"
if echo "$cmd" | grep -qE '(^|[[:space:]])(main|master)([[:space:]]|$)'; then
  target="explicit"
fi

# Case 2: refspec syntax "HEAD:main" or ":main" or ":refs/heads/main"
if [ -z "$target" ] && echo "$cmd" | grep -qE 'HEAD:(main|master)([[:space:]]|$)'; then
  target="refspec-head"
fi
if [ -z "$target" ] && echo "$cmd" | grep -qE ':(refs/heads/)?(main|master)([[:space:]]|$)'; then
  target="refspec"
fi

# Case 3: bare "git push" (no remote+refspec args) from main/master branch
# Detected by:
#   1. Stripping all short/long flags (-v, -f, --force, -u, --set-upstream, etc.)
#      so they don't get mistaken for a remote or refspec
#   2. Stripping the "git push" prefix so "push" isn't mistaken for a token
#   3. Checking whether the remaining tokens form a remote+refspec PAIR
#      (at least two whitespace-separated alphanumeric tokens)
#   4. If there's no explicit pair, check the current branch via git symbolic-ref
#
# Classification after stripping flags and the "git push" prefix:
#   "git push"              -> remainder=""                  -> no pair, check branch
#   "git push -v origin"    -> remainder="origin"            -> no pair, check branch
#   "git push --force"      -> remainder=""                  -> no pair, check branch
#   "git push -u origin my" -> remainder="origin my"         -> has pair, skip check
#   "git push -v -u origin feature/foo" -> remainder="origin feature/foo" -> has pair
if [ -z "$target" ]; then
  # Strip long flags (--foo, --foo=bar) then short flags (-x, -xyz)
  stripped="$(echo "$cmd" | sed -E 's/([[:space:]]|^)--[a-zA-Z0-9_-]+(=[^[:space:]]*)?//g; s/([[:space:]]|^)-[a-zA-Z]+//g')"
  # Strip the "git push" prefix to get just the remote/refspec tokens
  remainder="$(echo "$stripped" | sed -E 's/^[[:space:]]*git[[:space:]]+push[[:space:]]*//')"
  # Check for remote+refspec pair (two whitespace-separated tokens) in the remainder
  if ! echo "$remainder" | grep -qE '^[a-zA-Z0-9._/-]+[[:space:]]+[a-zA-Z0-9._/-]+'; then
    current="$(git symbolic-ref --short HEAD 2>/dev/null || echo "")"
    if [ "$current" = "main" ] || [ "$current" = "master" ]; then
      target="current-branch"
    fi
  fi
fi

if [ -n "$target" ]; then
  cat >&2 <<EOF
BLOCKED: Direct push to main/master is forbidden.
Reason: $target
Create a branch and open a PR instead.
See MEMORY.md workflow rules.
EOF
  exit 2
fi

exit 0
