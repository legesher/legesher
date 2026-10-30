# CLAUDE.md

Guidance for AI coding sessions in this repository. This file holds what applies everywhere. Package detail
lives in each package's own `CLAUDE.md` (`libs/core`, `libs/i18n`, `libs/legesher`, `libs/language-server`,
`libs/vs-code`); `libs/mcp` and `libs/runtime` have a README instead. Human setup is in `DEVELOPMENT.md`, and
contribution rules (licensing, DCO, release trains) are in `CONTRIBUTING.md`.

## What this repository is

Legesher lets people write code with the keywords and builtins of their own natural language. This monorepo is
the Python toolchain plus the VS Code extension. It is a uv workspace with pdm-backend builds. Packages support
Python `>=3.10,<4.0`; development uses 3.13 (`.python-version`).

| Path                                     | Distribution                  | What it is                                                                     |
| ---------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------ |
| `libs/i18n/`                             | `legesher-i18n`               | Pack loading and validation, language registry, translations DB tooling        |
| `libs/i18n/language-packs/python/{lang}` | `legesher-i18n-python-{lang}` | One package per natural language, versioned and released on its own            |
| `libs/core/`                             | `legesher-core`               | Translation engine (token and tree-sitter backends), git filter, Unicode guard |
| `libs/legesher/`                         | `legesher`                    | The `legesher` CLI and runtime import hooks                                    |
| `libs/runtime/`                          | `legesher-runtime`            | Localized tracebacks, required by the CLI                                      |
| `libs/language-server/`                  | `legesher-language-server`    | LSP server, entry point `legesher-lsp`                                         |
| `libs/mcp/`                              | `legesher-mcp`                | MCP server                                                                     |
| `libs/vs-code/`                          | `legesher-vscode` (npm)       | VS Code extension (TypeScript); starts `legesher-lsp`                          |
| `docs/`                                  |                               | Astro Starlight site for docs.legesher.io (pnpm)                               |

Internal dependencies point one way: `legesher-i18n` depends on no other package here; core, runtime,
language-server and the packs build on it; the CLI and the MCP server build on core. Each package's
`pyproject.toml` (`package.json` for the extension) holds its version; do not copy version numbers into docs.

The pack count is the number of directories under `libs/i18n/language-packs/python/` (56 today;
`version-index.yml` there is not a pack). In code, get the set from `get_active_language_codes()`
(`legesher_i18n.language_registry`), never a hard-coded list.

## Validate

The Makefile is the entry point. Run it from the repository root.

```bash
make install              # uv sync --all-extras (CI runs plain `uv sync`)
make test                 # test-i18n, test-core, test-legesher, test-language-server, test-mcp, test-runtime in turn
make test-core            # one package; the other five targets follow the same naming
uv run pytest scripts/tests -q   # repo scripts, workflow auditor, repo-hygiene guard; ci.yml runs it on every PR
make lint                 # ruff check libs/
make format               # ruff check --fix, then ruff format
make check-generated      # drift gate for every generated artifact (see "Generated files")
```

Summary lines from `make test` and the scripts suite as of 2026-10-30. Counts grow; a drop means
tests stopped being collected, so find out why.

- i18n: `2930 passed, 58 skipped`
- core: `8301 passed, 4 skipped, 49 xfailed`
- legesher: `479 passed, 1 skipped, 1 xfailed`
- language-server: `644 passed, 5 deselected, 3 xfailed`
- mcp: `367 passed, 10 deselected, 1 xfailed`
- runtime: `57 passed`
- scripts/tests: `1924 passed, 118 skipped`

The deselected tests are the `scheduled` release-tier suites, which have their own targets:
`make test-mcp-scheduled` (every-pack round-trip sweep and a clean-environment wheel spawn) and
`make test-language-server-scheduled` (wheel install plus a live LSP session). Both build wheels. The release
workflows run them as gates, so run the matching one green before a release of either package.

**Run one package per pytest invocation.** Every package keeps its tests in a top-level `tests` package with its
own `conftest.py`, so `uv run pytest libs/core/tests libs/mcp/tests` fails at collection with
`ImportPathMismatchError`. One package at a time from the root works (`uv run pytest libs/core/tests -q`, which
is what `ci.yml` does). `make test-coverage` runs `pytest libs/` in one invocation and fails the same way; for
coverage, add `--cov` to a single-package run.

**Benchmarks are opt-in.** Core and legesher put `--benchmark-disable` in their pytest `addopts`, so the default
run executes each benchmark once with no timing. `make bench` turns timing on, one invocation per package, and
autosaves under each package's `.benchmarks/` (gitignored). The language server's timing tests are plain tests
marked `timing`; they assert through `tests/timing.py`'s `assert_within`, which enforces the wall-clock bound
only under `--timing`. `make bench` runs them with `-m timing --timing`.

**`make typecheck` does not get past its first file.** mypy stops on
`libs/core/tests/fixtures/sample_spanish.py` (translated Python it cannot parse), reports
`Found 1 error in 1 file (errors prevented further checking)`, and checks nothing else. No workflow runs mypy.

**Python 3.10 locally.** uv follows `.python-version` over whatever interpreter is on `PATH`. Set
`UV_PYTHON=3.10` to test on 3.10, as the CI matrix does.

**The translations database is not in git.** `libs/i18n/legesher_i18n/db/translations.db` is untracked, so a
fresh clone has none: DB-dependent tests skip, and the language-registry half of `make check-generated` prints
`SKIP` and passes. Writing the DB has its own procedure; read `libs/i18n/CLAUDE.md` before touching it.

## Testing contract

Where this and generic testing advice disagree, this wins.

- **Known failures are strict xfail ledgers, never weakened assertions.** A pack, locale or case that fails a
  real assertion is recorded as `pytest.mark.xfail(strict=True, reason=...)` with a reason that names the
  tracking issue. Strict means an entry that starts passing fails the run (XPASS), which is the signal to remove
  it. Loosening an assertion, commenting out a case or adding a print-and-continue path is a defect in the test.
- **Ledgers in the tree:** `KNOWN_ROUND_TRIP_FAILURES` in `libs/core/tests/integration/test_every_pack.py` (same
  shape in `libs/mcp/tests/test_roundtrip_sweep.py`); the interpreter-gap ledger in
  `libs/core/tests/interpreter_gaps.py` (CPython 3.10/3.11 tokenizer and pre-Unicode-15.1 identifier rules); and
  `STALE_VERSION_MAX` in `libs/core/tests/integration/test_all_languages_parametrized.py`. Add to an existing
  ledger before inventing a new one.
- **Parametrize language coverage from `get_active_language_codes()`.** A frozen `["es", "ar"]` with the rest
  commented out passes while testing almost nothing.
- **One corpus.** Cross-pack constructs go in `libs/core/tests/fixtures/corpus/`, registered in
  `manifest.json` with the lowest grammar each file parses under. `test_every_pack.py` translates, reverses and
  compiles it through every pack in the default core run, and `libs/mcp/tests/corpus.py` reads the same
  directory. Do not add inline corpus strings to a new test module.
- **Latin proves nothing.** Identifier and round-trip assertions use combining-mark and multi-codepoint scripts:
  Devanagari, Sinhala with ZWJ, Tamil, Bengali, Thai, pointed Hebrew, vocalised Arabic, Ethiopic, Myanmar, CJK,
  Hangul. Assert byte-for-byte survival, NFC output, no bidi or format controls outside the per-script
  allowlist, and that the English side compiles. `libs/core/tests/unit/test_identifier_scripts.py` is the model.
- **Text identity is store-NFC, compare-NFKC plus casefold.** An NFD-spelled native keyword must still
  translate; test it that way.
- **Performance assertions are structural.** In the default run a cache test asserts `cache_info().hits`, and
  any speedup floor sits where scheduler noise cannot trip it, with the reason in a comment. Absolute bounds run
  only under `make bench`. `libs/language-server/tests/benchmarks/test_cache_performance.py` is the model.
- **Property suites run every time.** The Hypothesis suite in `libs/core/tests/property/` is part of the default
  core run.
- **Prove every new guard or ledger test can fail before raising the PR.** Inject the defect in a throwaway copy
  (never the branch), confirm the failure names the offending path, key or value, and put the probe in the PR
  body: what was injected, the failure line, and the counts before and after.

## One contract, one implementation

The CLI, the MCP server, the language server and the VS Code extension all read and write the same artifacts:
language packs, `.legesher/identifier_map.json`, the translations DB. Before adding validation or normalization
for one of them, find the surface that already writes that artifact. It owns the contract. Import its
implementation, promoting a helper to public API if needed, instead of re-deriving the rules.

Two implementations of one contract drift, and the weaker one starts accepting what the stricter one rejects.
Nothing crashes; the weak surface reports success and the bad value lands in an artifact. A validator weaker
than the one guarding the same file is worse than none, because it turns "unchecked" into "checked and fine".

The owners to reuse:

- Text comparison: `legesher_core.text_identity.compare_key` (NFKC plus casefold; storage is NFC). Raw `==` on
  user-visible text is the bug.
- Identifier validity: `IdentifierValidator` (`legesher_core.tree_sitter.identifier_validator`).
- Invisible and bidi characters: `legesher_core.unicode_guard.scan_text`.

The MCP tool `validate_identifier_translations` once re-derived these checks and accepted malformed identifiers,
invisible codepoints, case variants of pack terms and decomposed spellings. The fix was to delete its rules and
call the three owners above. When reuse is impossible (another runtime or a network boundary), pin both
implementations to shared test vectors so divergence fails a test.

A docstring that promises a guarantee must match what the code delivers, no more.

## Design constraints

- **Git stores each file in its author's language.** The clean filter only normalizes stray keywords to the
  file's stored language. The English run form is produced at run time and never replaces the stored file.
- **Local first.** Translation works offline; any cloud provider is optional.
- **More than one programming language and editor.** Python is first, but keep language-specific logic behind
  the translator interface in `libs/core` and editor logic behind the language server, so other languages and
  editors (Zed, JetBrains, Neovim, Helix) can follow.

## Generated files

Regenerate these; never edit them by hand. `make check-generated` diffs each against a fresh regeneration.

| Artifact                                              | Source                                                 | Regenerate with                                         |
| ----------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------- |
| `libs/i18n/legesher_i18n/languages.json`              | `languages` rows with `in_registry = 1` in the DB      | `make generate-languages` (needs the DB)                |
| `libs/vs-code/src/generated/languages.ts`             | the same rows, written by the same generator           | `make generate-languages` (needs the DB)                |
| `docs/generated/`                                     | `docs/snippets/*.py`, shipped packs, `languages.json`  | `make generate-docs`                                    |
| `libs/i18n/docs/schema-v2-reference.md`               | `schema_v2.sql` and `schema_v2.descriptions.yml`       | `make generate-schema-reference`                        |
| `libs/i18n/language-packs/python/*/REFERENCE.md`      | pack YAML, `languages.json`, the generator itself      | `uv run python scripts/generate_reference_docs.py`      |
| Pack README term counts                               | pack YAML                                              | `uv run python scripts/update_pack_readme_counts.py`    |

The pre-commit hooks regenerate some of these when their usual inputs change, but only `make check-generated`
covers every input. Run it after changing a generator or anything a generator reads.

## Pre-commit

`pre-commit install` once. Beyond whitespace, YAML/TOML/JSON checks, ruff, markdownlint (120-column lines) and
zizmor on workflows, the local hooks that catch real mistakes are:

- `validate-language-pack-yaml`, `enforce-pack-data-contract`: pack YAML shape.
- `validate-showcase-examples`: reverse-translates the `hello_world.py` showcase examples through the packs.
  It reads them from the preview repository checkout (`LEGESHER_PREVIEW_ROOT`) and skips without failing
  when that is not set, so a pack change that breaks an example can pass locally.
- `require-pack-version-bump`: a pack content change must move the pack's version, and the version in its
  `pyproject.toml` and `__init__.py` must agree. A bump can leave `uv.lock` modified; stage it.
- `check-changelog-on-version-bump`: a version change in core, i18n, legesher, language-server or the
  extension needs that package's `CHANGELOG.md` and the root `CHANGELOG.md` staged with it.
- `check-internal-dep-constraints`: version bounds between workspace packages.
- `regenerate-reference-docs`, `regenerate-schema-reference`, `update-pack-readme-counts`: rewrite generated
  files in place; stage what they change.
- `commitizen` and `commitizen-branch`: conventional commit messages.

## Commits, pull requests and merge evidence

- **Conventional commits**, enforced by commitizen: `type(scope): summary`. Types are `feat`, `fix`, `docs`,
  `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Scopes are package names (`core`,
  `i18n`, `legesher`, `language-server`, `mcp`, `runtime`, `vs-code`, `i18n-python-{lang}`) or an area such as
  `docs` or `ci`. Maintainer subjects also carry the tracker key in brackets: `fix(core): summary [CORE-####]`.
- **Sign off every commit** (`git commit -s`). The DCO check fails a PR with an unsigned commit.
- **Branch from `main`; never push to it.** The project hook in `.claude/` blocks `git push` to `main`.
- **Squash merge.** GitHub appends `(#N)` to the subject.
- **CI does not run on draft PRs.** Marking the PR ready runs it; the `ci:run` label runs it on a draft.
- **Merge evidence is the local run.** Quote the summary line of each suite you ran, verbatim, in the PR body.
- **Changelogs are hand-written in the PR.** Add entries under `## [Unreleased]` in the package `CHANGELOG.md`
  (and the root `CHANGELOG.md` for user-visible changes), Keep a Changelog headings. The release train stamps
  the version and date and updates the root Package Versions table; do not do that by hand.
- **Say whether AI helped** in the PR template's AI Assistance section (policy in `AI_CONTRIBUTIONS.md`).

## Releases

The Python trains run python-semantic-release from the repository root. The VS Code train is different: it
releases whatever version `libs/vs-code/package.json` holds when that tag does not exist yet, so the extension's
version is bumped by hand. Only the foundation trio shares a version. `CONTRIBUTING.md` ("Release trains")
explains the model.

| Train           | Packages                                            | Tag                             | Workflow                      |
| --------------- | --------------------------------------------------- | ------------------------------- | ----------------------------- |
| Foundation      | `legesher-core`, `legesher-i18n`, `legesher`        | `v{version}`                    | `release-foundation.yml`      |
| MCP server      | `legesher-mcp`                                      | `mcp-v{version}`                | `release-mcp.yml`             |
| Language server | `legesher-language-server`                          | `language-server-v{version}`    | `release-language-server.yml` |
| Language packs  | `legesher-i18n-python-{lang}`                       | `i18n-python-{lang}-v{version}` | `release-language-packs.yml`  |
| VS Code         | `legesher-vscode`                                   | `vscode-v{version}`             | `release-apps.yml`            |

Facts that change what you write:

- The foundation config is `[tool.semantic_release]` in the root `pyproject.toml`: the `conventional` parser,
  release commit `chore(release): {version}`, and `major_on_zero = false`, so a breaking change (`feat!:`)
  bumps the minor version while the foundation is below 1.0. Every pack pins `legesher-i18n<1.0.0`, so 1.0 is a
  coordinated decision, never a side effect.
- Bumps count every `feat`/`fix` commit since the package's last tag, whatever paths it touched. A workflow's
  `paths:` filter decides when a train runs, not what it counts.
- The MCP, language-server and pack trains refuse to run unless the last reachable tag equals
  `project.version`; a package with no baseline tag cannot release until one is pushed. Do not hand-edit the
  version of the foundation, `legesher-mcp` or `legesher-language-server`; their trains write it. Language packs
  differ today: `require-pack-version-bump` requires a hand bump with every content change.
- Per-package configs give paths relative to the git root (`libs/<pkg>/pyproject.toml:...`) and run as
  `semantic-release -c libs/<pkg>/pyproject.toml`. A cwd-relative path silently rewrites the root files.
  `scripts/tests/test_semantic_release_configs.py` checks this.
- The release commit prefixes `chore(release)`, `chore: update uv.lock` and `docs(changelog): stamp` skip CI and
  the trains. Do not start a normal commit subject with them.
- No train uploads to PyPI. `publish-pypi.yml` is a manual dispatch per target (`foundation`, `language-server`,
  `mcp`, `runtime`, packs). `legesher-runtime` has no train: its version moves by hand, and a new runtime version
  is published before `foundation`.

## CI

- `ci.yml`: pre-commit on all files, `scripts/tests`, then each package suite with coverage. PRs run Ubuntu on
  Python 3.10 and 3.13; pushes to `main` add macOS and Windows on 3.13.
- `security.yml` (bandit and more) and `codeql.yml` run on every PR. `validate-packs.yml`, `docs.yml`,
  `mcp-surface-scan.yml` and `workflow-lint.yml` run on PRs that touch their area.
- Actions are pinned by commit SHA and checked by zizmor. Keep new actions pinned the same way.

## Documentation site

```bash
cd docs && pnpm install && pnpm dev   # http://localhost:4321; `pnpm build` for production
```

Content is in `docs/src/content/docs/`. Prefer package READMEs, `pyproject.toml` files and the code over older
prose anywhere in `docs/` when they disagree.

## Claude Code configuration

`.claude/` holds the project hooks (ruff on edited `.py` files, prettier on edited `.md` files, the push guard)
and five agents: `codebase-explorer`, `code-quality-reviewer`, `security-reviewer`, `test-engineer`,
`doc-writer`. `.claude/README.md` describes them.
