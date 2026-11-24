# Supporting a new Python version

Python ships a new minor version each October. This page lists what each one needs in this
repository, in order, with the files each step touches and the check that shows it is done.

It was written from the Python 3.15 work. Steps 1 to 5 were run for 3.15 and are described
from those runs. Steps 6 to 9 had not been run for 3.15 when this page was written; each says
so, and lists what is known to move. Rewrite a step from the real run when you do it.

`X.Y` below is the new version and `X.W` the one before it. Paths are from the repository
root, and so are the commands.

## The steps

| Step | What | Done for 3.15 |
| --- | --- | --- |
| 1 | Measure what the release added, on the real interpreter | Yes |
| 2 | Confirm nothing breaks on day one | Yes |
| 3 | Refresh the lock so the workspace installs | Yes |
| 4 | Register the release: term inventory, version list, classifiers | Yes, except the version index entry (step 6) |
| 5 | Measure the identifier characters the release added | Yes |
| 6 | Add the pack file for the release to every pack | Not yet |
| 7 | Add the reworded and new interpreter messages | Not yet |
| 8 | Add the release to CI | Not yet |
| 9 | Update the prose that states the supported versions | Not yet |

Steps 1 to 5 are small. Step 6 is the large one, and steps 7 and 9 wait for it.

Every claim about the new interpreter comes from running it. Print `sys.version` in each run
you record. CI does not run the new version until step 8, so until then a local run on
`X.Y` is the only evidence for steps 1, 4 and 5; quote it in the pull request.

## 1. Measure what the release added

Run this under both interpreters and compare. It needs no checkout and no dependencies.

```python
# names.py
import builtins
import keyword
import sys

print("#", sys.version)
for name in sorted(keyword.kwlist):
    print("keyword", name)
for name in sorted(keyword.softkwlist):
    print("soft keyword", name)
for name in sorted(dir(builtins)):
    value = getattr(builtins, name)
    if isinstance(value, type) and issubclass(value, BaseException):
        print("exception", name, "<", value.__mro__[1].__name__)
    elif isinstance(value, type):
        print("built-in type", name)
    else:
        print("built-in", name)
```

```bash
uv run --no-project --python X.W python names.py > names-X.W.txt
uv run --no-project --python X.Y python names.py > names-X.Y.txt
diff names-X.W.txt names-X.Y.txt
```

For 3.15 against 3.14 the difference is five names: the soft keyword `lazy`, the built-in
`__lazy_import__`, the built-in types `frozendict` and `sentinel`, and the exception
`ImportCycleError` (a subclass of `ImportError`).

What to watch for:

- **Names that start with two underscores count.** `__lazy_import__` is a built-in a
  programmer can call, as `__import__` is. The few the inventory leaves out on purpose
  (`__build_class__`, `__loader__`, and module attributes such as `__doc__`) are listed in
  `BUILTINS_STDLIB_ONLY` in `libs/i18n/tests/test_baseline_against_stdlib.py`.
- **A removed name is a finding too.** The version index has `removed_keywords`,
  `removed_builtins` and `removed_exceptions` for it.
- **Do not measure from another interpreter.**
  `libs/i18n/scripts/extract_python_content.py` reads the interpreter that runs it. Its
  `--version` option only labels the output.

Two scripts help, neither required:

- `libs/i18n/scripts/monitor_python.py` prints `X.Y` when CPython has tagged `vX.Y.0` and
  the version index does not list it yet, and nothing otherwise. It asks GitHub without a
  token. `--show-current` prints the newest indexed version and needs no network.
- `libs/i18n/scripts/extract_python_content.py --output content-X.Y.json --pretty`, run
  under the new interpreter, writes the same names with their docstrings and signatures.
  That is the context a translator needs for step 6.

**Check:** the diff above, with both `sys.version` lines in it.

## 2. Confirm nothing breaks on day one

There is nothing to change. The pack loader serves each pack's newest file to an interpreter
newer than every file the pack has, as long as the major version is the same. A project on
`X.Y` keeps working, and the words `X.Y` added stay in English until step 6. The rule is in
`libs/i18n/legesher_i18n/pack_loader.py` (`LanguagePackLoader.load`), and it is logged once
at INFO.

The tests for it derive "a newer Python" from the packs themselves, so they run on any
interpreter: `libs/i18n/tests/test_newest_tier_fallback.py` for the loader, and
`libs/legesher/tests/unit/test_cli_run_newer_python.py` for `legesher run`.

**Check:** after step 3, run the suites on the new interpreter from the repository root.

```bash
UV_PYTHON=X.Y make test
```

Expect the cases that need a later step to fail and name it. Before step 4,
`libs/i18n/tests/test_baseline_against_stdlib.py` reports the names from step 1 as
`unexpected missing keywords`, `unexpected missing builtins` or
`Real CPython exception(s) absent`. Anything else that fails is a real finding.

## 3. Refresh the lock so the workspace installs

The acceptance command is the whole test:

```bash
UV_PYTHON=X.Y UV_FROZEN=1 uv sync --all-extras
```

If it succeeds, skip this step. It fails when a locked package has no wheel for `X.Y` at its
locked release and cannot be built. Move only those packages:

1. For each package that failed, find whether a newer release ships an `X.Y` wheel. A package
   with no such release yet stays where it is, and builds from source if it can.
2. Move the named packages, and nothing else, to their newest release that is at least seven
   days old. Seven days is the cooldown Dependabot uses here (`.github/dependabot.yml`).

   ```bash
   uv lock --exclude-newer <timestamp seven days ago> \
       --upgrade-package <name> --upgrade-package <name>
   ```

3. Run `uv lock` again with no options. It keeps every version from the first run and drops
   the recorded cutoff, so the lock carries no `[options]` table.

Rules that held for 3.15:

- **No exact pins.** `uv.lock` resolves each supported Python separately. A release that
  needs a newer Python than the floor breaks the older ones if it is pinned with `==`;
  `--upgrade-package` lets each take its own newest release.
- **Use a `uv` that keeps the lock's format.** Compare the `revision` line at the top of
  `uv.lock` before and after. An older `uv` rewrites the file at a lower revision.
- **Leave the floor alone.** `requires-python` and the root `filelock` constraint for Python
  3.10 do not change in this step.
- **Say what moved and why** in the pull request: package, old release, new release, upload
  date. A lock change is otherwise unreadable.

**Check:** the acceptance command succeeds on `X.Y`, `uv lock --check` is clean, and the
suites give the same counts as before on 3.13 and 3.10.

## 4. Register the release

Four places name the Python versions the engine knows. They move together, in one pull
request, and none of them changes a pack file.

| File | What to add | Test that notices when it is missing |
| --- | --- | --- |
| `libs/i18n/legesher_i18n/term_definitions.py` | A list per kind of name the release added (`KEYWORDS_X_Y`, `BUILTIN_FUNCTIONS_X_Y`, `BUILTIN_TYPES_X_Y`, `EXCEPTIONS_X_Y`) and a row in `VERSION_ADDITIONS`. A release that added nothing still gets a row, an empty one | `libs/i18n/tests/test_term_definitions_versions.py`; `libs/i18n/tests/test_baseline_against_stdlib.py` on the new interpreter |
| `libs/mcp/legesher_mcp/versions.py` | `X.Y` in `_FALLBACK_VERSIONS` | `libs/mcp/tests/test_version_support.py` |
| The six engine `pyproject.toml` files (`libs/core`, `i18n`, `language-server`, `legesher`, `mcp`, `runtime`) | The `Programming Language :: Python :: X.Y` classifier | `scripts/tests/test_engine_python_classifiers.py` |
| `libs/i18n/tests/test_baseline_against_stdlib.py` | `X.Y` in `INDEX_ENTRY_PENDING`, with the reason | The same module, on every interpreter |

**The version index entry does not go here.**
`libs/i18n/language-packs/python/version-index.yml` records what each release added, but
the pack tests and the review-template contract also read it as the list of files every
pack ships. An entry with no pack files behind it fails
several hundred cases. So the entry lands in step 6 with the files, and until then
`INDEX_ENTRY_PENDING` records that the release is registered and not yet indexed. The ledger
is a strict expected failure: the day the entry lands, the test tells you to remove the
ledger line.

The scripts that classify a term before writing its database row
(`import_yaml_to_db.py` and `pipeline.py` in `libs/i18n/scripts/translate/`) read the newest
registered release, so they need no edit. `DEFAULT_RUN_PYTHON_VERSION` in
`pipeline.py`, the version a default pipeline run translates, stays where it is until
step 6.

**Check:** on the new interpreter, and again on 3.13 and 3.10:

```bash
UV_PYTHON=X.Y uv run pytest libs/i18n/tests/test_baseline_against_stdlib.py \
    libs/i18n/tests/test_term_definitions_versions.py \
    libs/i18n/tests/test_extract_python_content.py -q
uv run pytest scripts/tests/test_engine_python_classifiers.py \
    libs/mcp/tests/test_version_support.py -q
```

## 5. Measure the identifier characters the release added

Each CPython release reads identifiers with its own Unicode version, and a newer Unicode
version makes more characters legal in a name. A word that uses one of them does not parse
on an older Python. `libs/i18n/legesher_i18n/schema_validator.py` holds one measured table
per release, so that every check gives the same answer whichever interpreter runs it.

Measure the table. Do not derive it from the Unicode release notes.

```python
# xid.py
import sys

print("#", sys.version, file=sys.stderr)
for cp in range(sys.maxunicode + 1):
    if ("a" + chr(cp)).isidentifier():
        print(f"{cp:06X}")
```

```bash
uv run --no-project --python X.W python xid.py > xid-X.W.txt
uv run --no-project --python X.Y python xid.py > xid-X.Y.txt
comm -13 xid-X.W.txt xid-X.Y.txt | wc -l    # added by X.Y
comm -23 xid-X.W.txt xid-X.Y.txt | wc -l    # removed by X.Y: expect 0
```

For 3.15 against 3.14 that is 4,699 characters added and none removed. If nothing was
added, the release needs no table and this step is done.

Otherwise, in `schema_validator.py`:

- Add the ranges as `_XID_RANGES_ADDED_BY_CPYTHON_XY`, with the two `sys.version` strings and
  the counts in the comment above it.
- Add the release to `_XID_ADDED_BY_CPYTHON` and to `_UNICODE_OF_CPYTHON`.

And beside it:

- `libs/i18n/tests/test_min_interpreter_identifier.py`: the release in `RELEASES`, and the table's
  size and digest in `RANGE_DIGESTS`.
- `libs/i18n/tests/interpreter_gaps.py`: one sample character in `NEWER_IDENTIFIER_SAMPLES`.
- `libs/i18n/scripts/translate/prompts/vocabulary_prompt.md`: the release, in both places the rule is
  stated. The prompt that is sent reads the tables and needs no edit.
- `libs/i18n/legesher_i18n/surface_validation.py`: move `VALIDATOR_VERSION`. A new table changes what
  the stored `min_interpreter_ok` verdict means, so an existing corpus database needs the
  recompute step in [corpus-publish-runbook.md](./corpus-publish-runbook.md).

Nothing else needs to change. The schema gate, the publish gate for recommended names, the
intake path, the review check, the pack exporter and the corpus repair script all read these
tables, most of them through `interpreter_needed_for_identifier`.

One thing a new table does not do: let a pack use the new characters. The exporter keeps two
spellings of a word across the 3.13 boundary only
(`schema_validator.TIERED_IDENTIFIER_RELEASE`). It refuses a word that needs a later release
and names the character.

**Check:** on both interpreters, because each half of the comparison runs on one side only:

```bash
UV_PYTHON=X.W uv run pytest libs/i18n/tests/test_min_interpreter_identifier.py -q
UV_PYTHON=X.Y uv run pytest libs/i18n/tests/test_min_interpreter_identifier.py -q
```

## 6. Add the pack file for the release

**Not yet run for 3.15.** What follows is what is known to move, not a procedure that has
been followed.

Every pack gains `X.Y.yml`, which extends `X.W.yml` and holds only the words from step 1.
The words come from the translations database and the pack files are written by the
exporter, never by hand: read "Changing pack values" in `libs/i18n/CLAUDE.md` first. It is
its own pull request, started only when no other pack regeneration is in flight.

Places that hold the list of pack files and move together:

- `libs/i18n/scripts/translate/yaml_exporter.py`: `_PACK_VERSIONS`, the sections built in
  `_build_version_sections`, the plan of files in `export_language`, and the default
  `python_version_max`.
- `libs/i18n/scripts/verify_pack_regen.py`: `EXPECTED_VERSIONS`.
- `libs/i18n/scripts/export_packs.py`: `VERSIONS`.
- `libs/i18n/language-packs/python/version-index.yml`: the entry for `X.Y`, with the same change that
  removes the release from `INDEX_ENTRY_PENDING` (step 4).
- `libs/i18n/scripts/translate/pipeline.py`: `DEFAULT_RUN_PYTHON_VERSION`.
- Each pack's `pyproject.toml` classifiers and the `python_version_max` in its newest file.
- Counts written into prose: "five version files" in `libs/i18n/CLAUDE.md`, and the number
  of shipped pack files in [packs-publish-runbook.md](./packs-publish-runbook.md).

The gates a regeneration has to pass are listed in [quality-gates.md](./quality-gates.md).
The three that matter most here:

```bash
uv run python libs/i18n/scripts/verify_pack_regen.py          # regeneration reproduces the shipped files
uv run python libs/i18n/scripts/audit_collisions.py           # no two terms share a word
uv run python libs/i18n/scripts/translate/screen_terms.py --gate   # every new word has been screened
```

Run them on Python 3.13, the interpreter the pack tooling is written for.

## 7. Add the interpreter messages

**Not yet run for 3.15.**

A new Python rewords some error messages and adds others. Packs that carry a `messages`
section translate them ([pack-messages.md](./pack-messages.md)). What is known:

- The English templates live in `libs/i18n/legesher_i18n/db/seeds/cpython_messages.json` and are
  transcribed by hand. No tool extracts them from an interpreter.
- A reworded message is a new row under the new `version_added`, never an edit of the old
  one. Older Pythons still print the old wording.
- `libs/i18n/scripts/seed_message_templates.py` adds the rows to a database.
  `libs/i18n/scripts/add_message_locale.py` is how a locale that already has messages catches up;
  `libs/i18n/scripts/translate/generate_messages.py` only fills a locale that has none.
- The exporter writes each translation into the pack file of its `version_added`, and
  refuses a wording whose version has no pack file. So this step comes after step 6.

**Check:** `libs/runtime/tests/test_golden_tracebacks.py` on the new interpreter. It raises
real exceptions and compares what is rendered, so it is the suite that notices a wording the
catalog does not know.

## 8. Add the release to CI

**Not yet run for 3.15.**

`.github/workflows/ci.yml` runs the test job on Python 3.10 and 3.13
(`matrix.python-version`). Until `X.Y` is in that list, the inventory row from step 4 and
the new half of the table from step 5 are checked only when someone runs them locally.

The matrix is described in prose in the root `CLAUDE.md`, `CONTRIBUTING.md` and
`DEVELOPMENT.md`; update those with it.

## 9. Update the prose that states the supported versions

**Not yet run for 3.15.** Do this last, after step 6: until the packs carry the release, the
new words are not translated, and the pages should not say more than that.

These find the statements:

```bash
git grep -n -E '3\.10 ?(-|to|through|a|إلى) ?\*{0,2}3\.1[0-9]|3\.10, 3\.11|3\.10 or higher|Python 3\.10\+' \
    -- ':!*CHANGELOG.md' ':!libs/i18n/language-packs/python/*/REFERENCE.md' \
       ':!libs/i18n/context/*' ':!uv.lock' ':!*.py'
git grep -n -E '^- Python 3\.1[0-9]$|Python 3\.1[0-9] in development' \
    -- 'libs/i18n/language-packs/python/*/README.md'
git grep -n -E "'3\.1[0-9]'|3\.1[0-9]\)" -- .github/ISSUE_TEMPLATE .github/pull_request_template
```

They cover the root `README.md` and `ROADMAP.md`, the package READMEs, the documentation
site's supported-languages page in each site language, the issue and pull-request templates,
and every pack's own README. A pack's README sits in the pack's directory, so it changes with
the pack, in the pull request for step 6. The first search also returns lines that state
only the floor (`Python 3.10+`) and a few pack file headers; those need no change.

## When the list is finished

Update the table at the top of this page, and rewrite any step that was marked as not yet
run from what you did.
