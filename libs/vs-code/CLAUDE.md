# legesher-vscode

The VS Code extension, in TypeScript: an LSP client for `legesher-language-server`, the translation panel,
language selection and detection, onboarding, telemetry and feedback. Commands, settings and the supported
VS Code and Node versions are declared in `package.json` (`contributes`, `engines`). The root `CLAUDE.md` holds
the repository commands and conventions.

## Build and test

Run from `libs/vs-code/` after `npm ci`.

```bash
npm run compile      # esbuild bundle to out/ (make vscode-compile from the root)
npm run typecheck    # tsc, no emit
npm run lint         # eslint src/
npm run test:unit    # mocha + ts-node over test/unit/**/*.test.ts; no editor needed
npm test             # pretest (typecheck, compile, compile:integration, lint, test:unit), then
                     # vscode-test: test/integration in a downloaded VS Code; Linux needs xvfb-run -a
npm run package      # .vsix via vsce (make vscode-package)
```

- **No workflow runs these on a pull request.** `release-apps.yml` runs `npm test` on three operating systems
  only after a push to `main` that touches `libs/vs-code/`, and then releases. Run `npm test` locally before
  raising a PR that changes this package, and quote its result.
- **Unit-tested modules must not import `vscode`.** `test:unit` runs outside an editor, where the module does
  not exist. Put logic you want unit-tested in a `vscode`-free module (as `languageProfile.ts`,
  `languageDetection.ts`, `serverInstall.ts` and the other modules under test are) and keep the editor wiring
  in `extension.ts`, `client.ts` or `config.ts`. `test/unit/support/languageClient.ts` stands in for
  `vscode` when a test must load `vscode-languageclient`.
- `.vscode-test.mjs` puts the test editor's user-data directory under the system temp directory. macOS caps
  socket paths at 103 characters, and the default path inside a git worktree passes that limit.

## Generated and guarded files

- `src/generated/languages.ts` is generated (see the root file); do not edit it.
- The language settings in `package.json` (`legesher.workingLanguage`, `legesher.targetLanguage`) carry
  hand-kept `enum` and `enumDescriptions` arrays. `scripts/tests/test_vscode_language_enums.py` requires them
  to list exactly the registry's published codes, each labelled as itself. A new language means editing both
  arrays in step.
- `package.json` is the extension's only version source; `release-apps.yml` tags `vscode-v<version>` from it.
  `pyproject.toml` (the `legesher-vs-code` Python dependency bundle) must carry the same version.
  `scripts/tests/test_vs_code_version_source.py` fails when they differ, so bump both together.

## Language roles

`src/languageProfile.ts` holds the rules. Keep the roles separate:

| Role    | Setting                    | Meaning                               |
| ------- | -------------------------- | ------------------------------------- |
| Pivot   | `legesher.sourceLanguage`  | Python's own vocabulary; the run form |
| File    | detected per file          | What a given file is written in       |
| Working | `legesher.workingLanguage` | What the user reads and writes in     |
| Known   | `legesher.knownLanguages`  | What the user reads comfortably       |

- The client sends the file and working languages as separate `initializationOptions` slots (`fileLanguage`,
  `workingLanguage`), plus a deprecated `targetLanguage` slot that mirrors `fileLanguage` for older servers.
  Never collapse them client-side; the server cannot separate one value again. Each document's language goes to
  the server in a `legesher/documentLanguage` notification. Detection happens here, never in the server.
- `legesher.targetLanguage` is deprecated but still honoured where `legesher.workingLanguage` is not set, at
  its own scope. VS Code's scope precedence (folder over workspace over user) decides first; only within one
  scope does the new name outrank the old.

## Other gotchas

- The extension does not bundle the server. `legesher.serverCommand` defaults to `legesher-lsp` from the
  `legesher-language-server` Python package; `serverInstall.ts` words the message shown when it is missing.
- Telemetry is opt-in: `legesher.telemetry.enabled`, `legesher.telemetry.repoAttribution` and
  `legesher.telemetry.contributeToMLTraining` all default to `false`, and VS Code's global telemetry setting
  also gates sending.
- Debugging: set `legesher.trace.server` to `verbose` and read the "Legesher Language Server" output channel.
