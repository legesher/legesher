# legesher

The `legesher` command (`legesher.cli.main:cli`) and the import machinery behind `legesher run`. It is mostly a
front end over `legesher-core`, `legesher-i18n` and `legesher-runtime`. The root `CLAUDE.md` holds the
repository commands and the testing contract.

## Tests

`make test-legesher` from the root; the expected summary line is in the root file. `--strict-markers` is on,
so register a new marker in `pyproject.toml`.

## Layout

- `legesher/cli/`: one module per command. `main.py` registers each with `cli.add_command()`. Commands:
  `init`, `translate`, `run`, `git` (`setup`, `status`), `guard`, `metadata` (`show`, `history`, `list`,
  `validate`, `raw`), `config` (`get`, `set`, `list`). `legesher <command> --help` is the reference for flags.
- `legesher/runtime/`: `import_hook.py` (translates a localized module at import time), `source_mapper.py`,
  `error_handler.py` (traceback frames point at the localized source). `legesher run` installs both through
  `install_import_hook()` and `install_error_handler()`.
- `legesher/config.py`: project `.legesher/config.yml` over user `~/.legesher/config.yml` over defaults. It
  owns the file's contract; add to it rather than re-deriving any part elsewhere:
  - where the file is: `find_project_config()` (the root file inside a repository, else the nearest at or
    above the working directory; never the user file) and `project_root()` (where `init` writes: the git
    root, else the working directory). A home directory kept in git is not a repository for either
    (`home_is_the_repository()`); `init` and `git setup` refuse to set the filter up there.
  - how one file is read: `parse_config_text()` (and `read_config_file()` for a file on disk), which returns
    the data through `normalize_config_data()` (including the shape an earlier `init` wrote) or the reason
    the file is left out whole. The loader, `load_project_config()`, `load_user_config()`, `legesher config
    get` and `list`, and `git setup` all use it. `guard --diff` reads a base commit's blob with
    `language_named_in()` instead: the same reading of `language`, without validating the rest, so a bad
    value elsewhere in a merged file cannot switch the pull-request check to English.
  - how the two files combine: `merge_config_data()`, per top-level key, used by `load()` and `config`.
  - how a file is written: `dump_config()`; `save_*_config()` merge into the file on disk.
- `git setup`, `git status` and `init`'s git step locate the repository with `LegesherConfig._find_repo_root()`,
  because git commands need the real repository; they check `home_is_the_repository()` before writing.
  `config set` reads and writes the raw YAML on purpose, so it can fix a value that fails validation.

## Gotchas

- **`legesher.runtime` is not `legesher_runtime`.** The first is this package's import hook and source mapper.
  The second is a separate distribution (`libs/runtime/`) that renders exception type names and messages from
  the pack. `legesher run` uses both.
- **Saving a config keeps the keys it does not own.** `save_project_config()` and `save_user_config()` merge
  into the file on disk. A command that changes one setting loads the file first and changes that setting
  (`git setup` does), so it cannot reset the others to their defaults.
- **`telemetry` is read from the user config only.** It is consent, so a committed project config must not be
  able to change it (`USER_ONLY_SECTIONS` in `config.py`). Keep any new consent setting user-only too.
- **`metadata` is per-file translation history** under `.legesher/metadata/`, not language-pack information.
- `translate` takes `--from` (default `en`) and requires `--to`. Without `--full` it moves only keywords and
  builtins. `--full` sends identifiers, comments and strings to a model backend (`anthropic`, `cohere-aya`,
  `openai-compat`). The provider classes live in `legesher_i18n.api.providers`, not here.
- `examples/` holds demo scripts named `test_*.py`, some in Spanish. Pytest pointed at `libs/legesher` collects
  them and stops with three collection errors. Point it at `libs/legesher/tests`.
