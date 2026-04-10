# Pre-Open-Source Audit — Follow-Up Punch List

**Date**: 2026-04-10
**Parent audit report**: [pre-open-source-2026-04-10.md](./pre-open-source-2026-04-10.md)
**Parent tickets**: CORE-721 (security audit), CORE-781 (quality review)
**Merging PR**: [#206](https://github.com/madiedgar/legesher/pull/206) — security audit remediations

This document lists every open item surfaced by the pre-open-source audit that is
**NOT** covered by PR #206. Use it as the reference punch list for the work that
must happen between the #206 merge and the public org transfer (CORE-758).

---

## What PR #206 Covered (DONE)

Landing in #206 — no further action needed:

- `.gitignore` hardened with crypto/credential patterns (`*.key`, `*.pem`, `*.p12`, `*.pfx`, `credentials.json`, `secrets/`)
- CodeQL workflow re-enabled with push/PR/weekly triggers (was `workflow_dispatch` only)
- Private `linear.app/legesher` URLs removed from:
  - `libs/core/legesher_core/language_interface.py` (2 NotImplementedError messages)
  - `libs/core/docs/adding-languages.md`
  - `libs/i18n/docs/README.md`
  - `libs/i18n/docs/VALIDATION.md`
  - `libs/i18n/scripts/translate/README.md`
  - `libs/language-server/CHANGELOG.md`
  - `scripts/migrate_translations/README.md`
  - `scripts/translate/prompts/README.md`
- Replaced private URLs with `https://docs.legesher.io` or plain `CORE-XXX` refs
- Root `CHANGELOG.md` updated with Security section entry

---

## Launch Blockers — MUST fix before public org transfer

These items must be addressed before the repo flips public. Each should get its
own Linear ticket (or be bundled into a small follow-up PR per category).

### 1. Dependency vulnerability bumps

**Source**: `pip-audit` and `npm audit` run during the audit.

- **Python (pip-audit)**: 18 vulnerabilities across 6 packages. All have fixes available.
- **VS Code extension (npm audit)**: 12 vulnerabilities (8 high), primarily in `undici` and `serialize-javascript`.
- **Docs site (pnpm audit)**: Clean.

**Why blocker**: Dependabot will start auto-flagging these the moment the repo goes
public. Better to land clean.

**Next step**: One ticket per ecosystem (Python + npm) or a single bundled
Dependabot-style PR. Verify no breaking changes in the bumps, re-run tests.

### 2. `docs.legesher.io` TypeScript roadmap page

**Source**: PR #206 replaced `linear.app/legesher/project/typescript-support` with
`https://docs.legesher.io` in NotImplementedError messages and docs. The docs site
does not currently have a dedicated TypeScript roadmap page.

**Why blocker**: The error message users will see if they call
`create_translator("typescript", ...)` now points them to a URL that doesn't have
the content the message implies.

**Options**:

- **A**: Add a TypeScript roadmap page to the docs site (`docs/src/content/docs/roadmap/typescript.md`) and update the error URL to point at it directly.
- **B**: Change the error URL to a stable landing page that already exists (e.g., the main docs index or a general roadmap section) and skip the dedicated page until Phase 2C work starts.

**Recommendation**: Option A — small doc page linking to the CORE-421 through CORE-427 ticket summaries. Future-proofs the error messages.

### 3. `ruff format` fix for `test_cli_translate.py`

**Source**: `ruff format --check libs/` during the audit.

- One file fails formatting: `libs/legesher/tests/test_cli_translate.py`
- Likely whitespace or quote-style drift.

**Why blocker**: CI formatting check will fail on first PR after public transfer if
left unfixed.

**Next step**: `uv run ruff format libs/legesher/tests/test_cli_translate.py` and commit.

### 4. Public API docstrings — critical subset

**Source**: Quality review under CORE-781.

- Missing or incomplete docstrings on public-facing functions/classes across
  `legesher-core`, `legesher-i18n`, and `legesher` CLI entrypoints.
- Not all docstrings — only the ones a PyPI consumer would see.

**Why blocker**: First impression for users who find us on PyPI is `help(function)`.
Empty or terse docstrings on `create_translator`, `TranslatorConfig`, and the main
CLI commands will hurt adoption.

**Next step**: Triage a list of "touched by external users" functions, fill in
docstrings with examples. Internal helpers and private methods can defer.

### 5. `libs/i18n` `pack_loader.py` coverage bump

**Source**: Quality review under CORE-781.

- `libs/i18n` overall coverage: 69% (1% below the 70% threshold).
- Biggest gap is in `pack_loader.py`, which contains the path-traversal protection
  code (`_is_safe_parent_path`).

**Why blocker**: This is the security-critical code path. We flagged it as PASS in
the OWASP review, but the tests don't exercise every branch. For a security-audited
launch, the file guarding path traversal should be near 100%.

**Next step**: Add edge-case tests for `_is_safe_parent_path` covering symlinks,
relative `..` sequences, absolute paths outside the pack root, and Unicode
normalization.

---

## Should Fix Before Launch — high-value, low-risk

Not strict blockers, but strong ROI for a public launch.

### 6. `vulture` dead-code scan

**Source**: Quality review (CORE-781) — scan not yet run.

**What**: Run `uv run vulture libs/` to identify unused imports, unreachable code,
and unused functions. Surfaces cleanup targets ahead of the public release.

**Next step**: Run scan, triage findings, delete anything clearly unused, whitelist
anything that looks dead but is actually used by reflection / entry points.

### 7. Type hints — public API subset

**Source**: Quality review (CORE-781).

**What**: Ensure every public function / method has return type annotations and
parameter type hints. Internal helpers can stay as-is.

**Next step**: Run `mypy --strict` on public modules, fix annotations on the surface
area users will type-check against.

### 8. CodeQL JS/TS monorepo tuning (from PR #206 Copilot review)

**Source**: Copilot review comment on `.github/workflows/codeql.yml:9`.

**What**: With CodeQL re-enabled, the `autobuild` step now runs for the
`javascript-typescript` matrix entry. Because this monorepo has no Node project at
the root and only in subdirectories (`docs/`, `libs/vs-code/`), autobuild from root
will likely fail or skip dependency resolution, reducing signal.

**Why not a PR #206 fix**: Decided during PR review to merge #206 as-is and tune
CodeQL after we see one real run's logs rather than guessing at the right build
config blind.

**Options**:

- **A**: Add explicit `npm ci` steps for each Node subdir (full signal, more YAML).
- **B**: Set `build-mode: none` on the JS/TS matrix entry (CodeQL still scans source, loses dep-aware analysis).
- **C**: Let autobuild fail gracefully — source extraction still happens.

**Next step**: Wait for the first real CodeQL run on `main` post-merge. If the
JS/TS run warns or skips, file a ticket and pick A or B based on what the logs show.

---

## Post-Launch — can defer

Documented here for completeness. Not blocking the public transfer.

### 9. Internal docstrings

Private methods and helper functions across all packages. Nice to have, not required
for external users.

### 10. Internal type hints

Same scope — private helpers. Internal-only code can defer without impacting the
public API experience.

### 11. Non-critical test coverage

Coverage currently sits at: core 87%, i18n 69%, legesher 70%, language-server 71%.
Item #5 above handles the i18n gap. Bumping the others from ~70% to ~85% is worth
doing, but not launch-blocking — these are functional tests, not security tests.

---

## Informational (no action required)

### Gitleaks false positive

**Source**: Full git history scan via gitleaks during the audit.

One finding: an example API key in `.claude/agents/security-reviewer.md` used as a
documentation example of what a secret looks like. Confirmed false positive — not a
real secret, documented as such. No remediation needed.

### GitHub Actions secrets inventory (CORE-758 scope)

Listed here so the org transfer ticket has the checklist. These secrets must exist
in the new `Legesher` org after transfer:

| Secret                                 | Used In                          | Notes                                         |
| -------------------------------------- | -------------------------------- | --------------------------------------------- |
| `LEGESHER_TELEMETRY_CONNECTION_STRING` | release-apps.yml                 | Azure AppInsights connection string           |
| `PREVIEW_REPO_PAT`                     | sync-reference-docs.yml          | PAT for preview-repo repo access          |
| `VSCE_PAT`                             | release-apps.yml (commented out) | VS Code Marketplace publishing token (future) |
| `GITHUB_TOKEN`                         | Multiple workflows               | Auto-provided by GitHub, no action needed     |

Actual secret migration belongs to CORE-758, not this audit.

---

## Suggested Follow-Up Ticket Structure

Rather than filing 8 separate tickets, group by theme:

1. **`[chore:deps] Pre-launch dependency vulnerability bumps`** — covers items 1 (Python + npm).
2. **`[chore:ci] Pre-launch code hygiene (ruff format + vulture)`** — covers items 3, 6.
3. **`[docs:public-api] Public API docstrings for PyPI release`** — covers item 4.
4. **`[docs:roadmap] Add TypeScript roadmap page to docs.legesher.io`** — covers item 2.
5. **`[i18n:test] Path traversal edge case coverage for pack_loader`** — covers item 5.
6. **`[core:types] Public API type hint pass for mypy --strict`** — covers item 7.
7. **`[ci:codeql] Tune CodeQL monorepo build after first main run`** — covers item 8, only file after seeing real run logs.

Items 9–11 (internal docstrings/types/coverage) can roll into a single
post-launch `CORE-TBD Q2 tech-debt batch`.

---

## Sign-off Reference

Full audit report with scan results, OWASP review, coverage tables, and sign-off
recommendation: [pre-open-source-2026-04-10.md](./pre-open-source-2026-04-10.md)

**Audit gate status**: PASS (both CORE-721 and CORE-781)
**Launch recommendation**: Merge #206, then work through the Launch Blockers list
above before flipping the repo public.
