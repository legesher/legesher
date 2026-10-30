# legesher-core

The translation engine. It rewrites Python keywords, builtins and the implicit parameters (`self`, `cls`)
through a language pack, and owns the git clean filter, the guard, round-trip verification and the
text-identity and Unicode contracts that other packages import. The root `CLAUDE.md` holds the repository
commands and the testing contract; this file covers what is specific to this package.

## Tests

`make test-core` from the root; the expected summary line is in the root file.

- `--strict-markers` is on. A new marker must be registered under `[tool.pytest.ini_options]` in
  `pyproject.toml` or collection fails.
- `tests/conftest.py` imports `TreeSitterTranslator`, so the suite needs the `treesitter` extra. The workspace
  installs it (the `legesher` package depends on `legesher-core[treesitter]`).
- The `translator_class` fixture runs a test against both backends. Use it for any behaviour both share.

## Layout

- `transformer.py`: `TokenTranslator`, pure stdlib. `tree_sitter/translator.py`: `TreeSitterTranslator`.
  `language_interface.py`: the `Translator` protocol and the `create_translator*` factories
  (`LEGESHER_USE_TREE_SITTER=true` switches the default backend).
- `tree_sitter/llm_translator.py`, `extractor.py`, `identifier_map.py`, `identifier_validator.py`: the full
  (model-backed) translation of identifiers, comments and strings behind `legesher translate --full`.
- `git_filter.py`, `filter_process.py`, `stored_form.py`, `guard.py`: the clean filter, git's long-running
  filter protocol, keyword normalization to each block's stored form, and the checks behind `legesher guard`.
  `__main__.py` is the `legesher-filter` console script git calls.
- `text_identity.py` (`compare_key`), `unicode_guard.py` (`scan_text`), `script_lookup.py`: the text and
  script contracts other packages import.
- `round_trip.py`: the owning round-trip implementation (`verify_round_trip`).
- `artifact_io.py`: shared read, write and versioning for the files under `.legesher/`.
- `metadata.py`, `translation_tracker.py`: per-file history under `.legesher/metadata/`.
- `translation_memory/`, `cultural_comments.py`, `ai_context.py`, `repo_attribution.py`: see the module
  docstrings and `libs/core/docs/`.

## Rules

- **Tree-sitter stays optional.** The tree-sitter exports in `legesher_core/__init__.py` load lazily (PEP 562),
  so `import legesher_core` and `TokenTranslator` work without the C extensions.
  `tests/test_import_without_tree_sitter.py` enforces this. Never add a top-level `tree_sitter` import on the
  token path.
- **Translation behaviour changes in both backends.** `TokenTranslator` and `TreeSitterTranslator` share
  `TokenMapper`; a change to one that the other lacks is a divergence the both-backend tests should catch.
- **Implicit parameters come from the pack's `implicit_params` section.** The canonical list is
  `legesher_i18n.term_definitions.IMPLICIT_PARAMS`. The extractor skips them, so they never reach the model.
  `create_translator_from_language_pack()` loads the section itself; `create_translator()` takes
  `implicit_param_map` explicitly.
- **The language server keeps its own copy of the renaming rule** (it does not depend on this package).
  Changing how names are renamed here fails `libs/language-server/tests/test_proxy_engine_parity.py` until the
  proxy follows.
- Design notes: `libs/core/docs/` (round-trip verification, translation memory, repository attribution,
  adding languages, the tree-sitter ADR).
