# Language Pack Release

## Release Details

- **Language(s):** <!-- e.g., Spanish (es), Arabic (ar) -->
- **Version:** <!-- e.g., 0.0.3 -->
- **Tag Format:** `i18n-python-{lang}-v{version}`

## Checklist

- [ ] Pack `CHANGELOG.md` updated
- [ ] Version bumped in pack's `pyproject.toml`
- [ ] Pack validation passes: `legesher-i18n validate path/to/3.10.yml`
- [ ] All YAML files valid: `uv run pre-commit run validate-language-pack-yaml --all-files`
- [ ] Tests pass: `uv run pytest libs/i18n/`
- [ ] Version inheritance chain intact (3.10 to 3.11 to 3.12 to 3.13 to 3.14)

## Translation Changes (if any)

<!-- List translation updates included in this release -->

| Term | Old Translation | New Translation | Reason |
| ---- | --------------- | --------------- | ------ |
|      |                 |                 |        |

## Review Status

<!-- For packs moving from experimental to accepted, list reviewer sign-offs -->

- [ ] Reviewer 1: <!-- @username -->
- [ ] Reviewer 2: <!-- @username -->
- [ ] Reviewer 3: <!-- @username -->
- [ ] Reviewer 4: <!-- @username -->
- [ ] Reviewer 5: <!-- @username -->

## Post-Release

- [ ] GitHub release created with tag `i18n-python-{lang}-v{version}`
- [ ] PyPI package published
