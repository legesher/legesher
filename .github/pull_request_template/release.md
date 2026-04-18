# Release

## Release Details

- **Package:** <!-- e.g., legesher-core -->
- **Version:** <!-- e.g., 0.5.2 -->
- **Release Type:** <!-- patch / minor / major -->

## Checklist

- [ ] Version bumped in `pyproject.toml`
- [ ] Package `CHANGELOG.md` updated (moved Unreleased items to new version heading)
- [ ] Root `CHANGELOG.md` updated with Package Versions table
- [ ] All tests pass: `uv run pytest libs/<package>/`
- [ ] Pre-commit hooks pass: `uv run pre-commit run --all-files`
- [ ] No new security warnings from Bandit: `uv run bandit -c pyproject.toml -r libs/<package>/`
- [ ] Integration tests pass with dependent packages

## Changes in This Release

<!-- Summarize what's included. Reference Linear issues where applicable -->

### Added

### Changed

### Fixed

### Removed

## Post-Release

- [ ] GitHub release created (automated via semantic-release)
- [ ] PyPI package published (automated via publish-pypi workflow)
- [ ] Documentation updated if needed
