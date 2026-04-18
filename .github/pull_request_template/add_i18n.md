# New Language Pack

## Language Details

- **Language:** <!-- e.g., Swahili (Kiswahili) -->
- **ISO 639-1 Code:** <!-- e.g., sw -->
- **Text Direction:** <!-- LTR or RTL -->
- **Pack Location:** `libs/i18n/language-packs/python/XX/` <!-- replace XX with language code -->

## Related Issues

Closes #

## Translation Coverage

<!-- Check all that apply -->

- [ ] Keywords (37 terms)
- [ ] Builtins (72 terms)
- [ ] Exceptions (66 terms)
- [ ] Python version files created (3.10-3.14 with inheritance)

## Checklist

- [ ] All commits are signed off (`git commit -S -s`)
- [ ] Pack follows the [existing structure](../../libs/i18n/language-packs/python/es/) (use Spanish as reference)
- [ ] `pyproject.toml` created with correct metadata
- [ ] `CHANGELOG.md`, `README.md`, and `__init__.py` created
- [ ] Root `pyproject.toml` updated (`[tool.uv.sources]` and `[tool.uv.workspace]`)
- [ ] `uv sync` completes without errors
- [ ] Pack validation passes: `legesher-i18n validate path/to/3.10.yml`
- [ ] Tests pass: `uv run pytest libs/i18n/`

## Native Speaker Verification

- [ ] I am a native or fluent speaker of this language
- [ ] Translations reflect how programming concepts are taught in this language's educational context

## Cultural Context

<!-- Any dialect considerations, script notes, or cultural context for reviewers? -->
