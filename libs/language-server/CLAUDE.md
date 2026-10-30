# legesher-language-server

The LSP server (pygls 2) behind the VS Code extension and any other editor. Console script `legesher-lsp`
(`legesher_language_server.__main__:main`; `legesher-lsp --help` lists the flags). The root `CLAUDE.md` holds the
repository commands and the testing contract.

## Tests

`make test-language-server` from the root; the expected summary line, the `scheduled` tier and the `timing`
mode are in the root file.

- `addopts` adds coverage and `-m 'not scheduled'`. The deselected tests are `tests/test_clean_environment.py`.
- The report header says whether `assert_within` bounds were enforced. `tests/benchmarks/README.md` explains
  the cache tests and how to add a performance test.
- **Drift check.** The proxy transport is tested against `tests/fixtures/stub_langserver.py`. Tests marked
  `langserver_drift` compare the stub with a real `pyright-langserver` and skip without it; the run then prints
  `STUB DRIFT CHECK DID NOT RUN`. Install it with `npm install -g pyright`, or rely on the weekly
  `langserver-drift.yml` workflow.

## Layout

- `server.py`: the pygls server, provider registration, and the custom methods `legesher/status` (request) and
  `legesher/documentLanguage` (notification, client to server).
- `providers/`: hover, completion, diagnostic, semantic tokens. `utils/`: keyword docs, error templates,
  Python name tables.
- `enhanced_intelligence.py`, `incremental_translator.py`, `source_map.py`, `type_alias_generator.py`: the
  proxy to an external type-aware server. Localized code goes out as English; answers come back mapped to the
  reader's positions.
- `config.py`: `LanguageServerConfig`, from `LEGESHER_*` environment variables, then CLI flags, then the
  client's `initializationOptions`.

## Gotchas

- **No dependency on `legesher-core`.** The proxy keeps its own copy of the engine's renaming rule.
  `tests/test_proxy_engine_parity.py` pins the two together and skips when core is absent (a standalone
  install). Known differences there are strict xfails; change the proxy when the engine changes.
- **The proxy backend is `pyright-langserver`.** `pyright` from the same npm package is a CLI checker that
  closes the stream, so pointing at it leaves the feature silently dead. Pylance is not an option: its licence
  allows use only with Microsoft products and forbids standalone redistribution.
- **Three language roles, never collapsed.** `file_language` (what a document is written in; per document via
  `legesher/documentLanguage`, the server does no detection), `working_language` (what the reader reads), and
  the deprecated `target_language`, kept equal to `file_language`. `LEGESHER_TARGET_LANG` and `--target-lang`
  seed all three through `apply_legacy_target_language()`. The default for all of them is `en`.
- `LEGESHER_PYLANCE_ENABLED` and `LEGESHER_PYLANCE_PATH` are retired and deliberately not honoured; their
  replacements are in `RETIRED_ENV_VARS` in `config.py`.
- Providers load the Python 3.10 pack tier (`_PROVIDER_PACK_VERSION` in `server.py`), whatever interpreter runs
  the server.
- The version lives only in `pyproject.toml`; `__version__` reads the installed metadata, so there is no
  second literal to bump.
- `ARCHITECTURE.md` predates pygls 2 and the proxy. Trust the code over it.
