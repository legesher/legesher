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
  owns the file's contract, and nothing else may re-derive any of it:
  - where the file is: `project_root()` (the git root inside a repository, else the working directory; `init`
    and `git setup` write there) and `find_project_config()` (the root file inside a repository, else the
    nearest at or above the working directory; never the user file);
  - how a file is read: `normalize_config_data()`, including the shape an earlier `init` wrote;
  - how the two files combine: `merge_config_data()`, per top-level key. `LegesherConfig.load()` and
    `legesher config` both use it;
  - how it is written: `dump_config()`.
- `guard` and `git setup` name the repository root themselves and read `<root>/.legesher/config.yml`
  through the same reader: a pull request's base has no working directory to search from.

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
