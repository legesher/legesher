# Release Process

This document describes how to release Legesher packages using our hybrid versioning strategy with python-semantic-release.

## Overview

Legesher uses a **hybrid versioning strategy**:

- **Foundation Suite** (core, i18n, legesher) - Synchronized versioning
- **Application Packages** (vs-code, pride) - Independent versioning
- **Language Packs** (i18n-python-es, i18n-python-ar, etc.) - Independent versioning

All releases are automated using [python-semantic-release](https://python-semantic-release.readthedocs.io/) and follow
[Semantic Versioning 2.0.0](https://semver.org/).

## Version Strategy

### Foundation Suite (Synchronized)

The foundation packages are released together with the same version number:

- `legesher-core` - Token-based translation engine
- `legesher-i18n` - Language pack system
- `legesher` - Main CLI package

**When to release:** Quarterly or when significant core changes are made.

**Example:** All three packages go from v0.1.0 → v0.2.0 together.

### Application Packages (Independent)

Application packages can be released independently on their own schedule:

- `legesher-vs-code` - VS Code extension backend
- `legesher-pride` - Community platform

**When to release:** As needed for bug fixes, features, or integrations.

**Example:** vs-code can go v0.1.0 → v0.2.0 while foundation stays at v0.1.0.

### Language Packs (Independent)

Language packs are released independently, allowing each language community to iterate at their own pace:

- `legesher-i18n-python-es` - Spanish translations for Python
- `legesher-i18n-python-ar` - Arabic translations for Python
- Future: `legesher-i18n-python-fr`, `legesher-i18n-python-zh`, etc.

**When to release:** As translations are updated, improved, or expanded.

**Example:** Spanish pack can reach v1.0.0 while Arabic is at v0.5.0, independent of each other and the foundation.

## Prerequisites

1. **Clean working directory:**

   ```bash
   git status  # Should show no uncommitted changes
   ```

2. **On main branch:**

   ```bash
   git checkout main
   git pull origin main
   ```

3. **All tests passing:**

   ```bash
   pytest
   ```

4. **Conventional commits:** All commits since last release must follow [Conventional Commits](https://www.conventionalcommits.org/)

## Release Commands

### Option 1: Release Foundation Suite

Release core, i18n, and legesher together:

```bash
./scripts/release-foundation.sh
```

This script will:

1. ✅ Verify you're on main branch
2. ✅ Check working directory is clean
3. 📦 Run semantic-release to determine next version
4. 🔒 Sync uv.lock if needed
5. 🏷️ Create git tag (e.g., `v0.2.0`)
6. 📝 Update all CHANGELOGs
7. ✅ Commit version bump
8. 🚀 Push to remote (if configured)

### Option 2: Release Individual App

Release vs-code or pride independently:

```bash
# Release VS Code extension
./scripts/release-app.sh vs-code

# Release Pride platform
./scripts/release-app.sh pride
```

This script will:

1. ✅ Verify you're on main branch
2. ✅ Check working directory is clean
3. 📦 Run semantic-release for that package only
4. 🏷️ Create git tag (e.g., `vs-code-v0.2.0`)
5. 📝 Update package CHANGELOG
6. ✅ Commit version bump
7. 🚀 Push to remote (if configured)

### Option 3: Release Language Pack

Release individual language packs independently:

```bash
# Release Spanish Python language pack
./scripts/release-language-pack.sh python es

# Release Arabic Python language pack
./scripts/release-language-pack.sh python ar
```

This script will:

1. ✅ Verify you're on main branch
2. ✅ Check working directory is clean
3. 📦 Run semantic-release for that language pack only
4. 🏷️ Create git tag (e.g., `i18n-python-es-v0.2.0`)
5. 📝 Update package CHANGELOG
6. ✅ Commit version bump
7. 🚀 Push to remote (if configured)

### Option 4: Manual Sync (Advanced)

If you need to manually sync foundation versions:

```bash
./scripts/sync-foundation-versions.py
```

This ensures core, i18n, and legesher all have the same version as the root pyproject.toml.

## Version Determination

Versions are determined automatically based on conventional commits since the last release:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor (0.1.0 → 0.2.0) | New feature |
| `fix:` | Patch (0.1.0 → 0.1.1) | Bug fix |
| `BREAKING CHANGE:` | Major (0.1.0 → 1.0.0) | Breaking change |
| `docs:`, `chore:`, etc. | None | No version bump |

**Note:** During 0.x.x development, breaking changes bump minor version (0.1.0 → 0.2.0) not major.

## Dependency Management

Application packages use semantic version constraints to depend on foundation:

```toml
# libs/vs-code/pyproject.toml
dependencies = [
    "legesher>=0.1.0,<0.2.0",      # Allows 0.1.x patches
    "legesher-core>=0.1.0,<0.2.0",
]
```

This means:

- ✅ Patch updates (0.1.1, 0.1.2) install automatically
- ⚠️ Minor updates (0.2.0) require explicit dependency update
- ❌ Major updates (1.0.0) require code changes

### Updating App Dependencies

When foundation is released, update app dependencies:

```bash
# Edit libs/vs-code/pyproject.toml
dependencies = [
    "legesher>=0.2.0,<0.3.0",      # Update range
    "legesher-core>=0.2.0,<0.3.0",
]

# Then release the app
./scripts/release-app.sh vs-code
```

## Release Workflow

### Scenario 1: Regular Release (Foundation)

**Goal:** Release new features in core, i18n, and main packages.

```bash
# 1. Ensure on latest main
git checkout main
git pull origin main

# 2. Verify commits since last release
git log v0.1.0..HEAD --oneline

# 3. Check what commits will trigger release
git log v0.1.0..HEAD --oneline | grep -E "^[a-f0-9]+ (feat|fix|BREAKING)"

# 4. Release foundation
./scripts/release-foundation.sh

# 5. Verify release
git log -1
git tag -l "v*" | tail -1
```

### Scenario 2: App-Only Release

**Goal:** Ship VS Code bug fix without releasing foundation.

```bash
# 1. Ensure on latest main
git checkout main
git pull origin main

# 2. Check VS Code changes
git log vs-code-v0.1.0..HEAD --oneline -- libs/vs-code/

# 3. Release VS Code
./scripts/release-app.sh vs-code

# 4. Verify release
git log -1
git tag -l "vs-code-v*" | tail -1
```

### Scenario 3: Coordinated Release

**Goal:** Release foundation, then update and release apps.

```bash
# 1. Release foundation
./scripts/release-foundation.sh

# Foundation now at v0.2.0

# 2. Update app dependencies
# Edit libs/vs-code/pyproject.toml
# Change: "legesher>=0.1.0,<0.2.0" → "legesher>=0.2.0,<0.3.0"

# 3. Commit dependency update
git add libs/vs-code/pyproject.toml
git commit -m "chore(vs-code): update foundation dependencies to v0.2.0"

# 4. Release VS Code
./scripts/release-app.sh vs-code

# 5. Repeat for pride
```

## Testing Releases (Dry Run)

To preview what would happen without making changes:

```bash
# Check what version would be released
uv run semantic-release --noop version --print

# Verbose output showing commit analysis
uv run semantic-release --noop version --verbose
```

**Note:** This only works on main branch with a clean working directory.

## Troubleshooting

### "No release needed"

**Cause:** No conventional commits since last release.

**Solution:** Ensure commits follow conventional format:

```bash
# Good commits that trigger releases
git commit -m "feat(core): add new translation engine"
git commit -m "fix(i18n): resolve pack loading bug"

# Commits that don't trigger releases
git commit -m "chore: update dependencies"
git commit -m "docs: improve README"
```

### "Must be on main branch"

**Cause:** You're on a feature branch.

**Solution:**

```bash
git checkout main
git pull origin main
./scripts/release-foundation.sh
```

### "Working directory must be clean"

**Cause:** Uncommitted changes.

**Solution:**

```bash
git status
git add .
git commit -m "type: description"
./scripts/release-foundation.sh
```

### Version Mismatch After Release

**Cause:** Foundation versions out of sync.

**Solution:**

```bash
./scripts/sync-foundation-versions.py
git add -A
git commit -m "chore: sync foundation versions"
```

## CHANGELOG Management

Each package has its own CHANGELOG.md:

- `libs/core/CHANGELOG.md`
- `libs/i18n/CHANGELOG.md`
- `libs/legesher/CHANGELOG.md`
- `libs/vs-code/CHANGELOG.md`
- `libs/pride/CHANGELOG.md`

Changelogs are updated automatically by semantic-release:

- ✅ Organized by version
- ✅ Grouped by type (Added, Fixed, Changed, etc.)
- ✅ Include commit messages
- ✅ Follow [Keep a Changelog](https://keepachangelog.com/) format

**Manual editing:** You can manually edit changelogs before tagging if needed.

## Git Tags

Tags follow these formats:

- Foundation: `v{version}` (e.g., `v0.2.0`)
- VS Code: `vs-code-v{version}` (e.g., `vs-code-v0.2.0`)
- Pride: `pride-v{version}` (e.g., `pride-v0.1.0`)

To view all tags:

```bash
git tag -l
```

To view tags for specific package:

```bash
git tag -l "v*"           # Foundation releases
git tag -l "vs-code-v*"   # VS Code releases
git tag -l "pride-v*"     # Pride releases
```

## Future: CI/CD Automation

**Phase 3 (Planned):** Releases will be automated in GitHub Actions:

- Automatic releases on merge to main
- PyPI publishing
- GitHub Release creation
- Notification to team

Until then, use the manual scripts documented above.

## FAQ

### When should we release?

**Foundation:** Quarterly or when significant features are ready.

**Apps:** As needed - weekly, monthly, or per feature.

### Can I release on a feature branch?

**No.** Releases must be on main branch to avoid conflicts.

### What if I need to fix a bug in an old version?

Create a maintenance branch from the tag:

```bash
git checkout -b maint/v0.1.x v0.1.0
# Make fixes
git commit -m "fix: critical bug"
# Release from maint branch (requires PSR config update)
```

### How do I revert a release?

```bash
# Delete tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Revert commits
git revert HEAD~2..HEAD
```

**Note:** Avoid reverting releases if possible. Better to release a fix.

## Related Documentation

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [python-semantic-release Docs](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Commit message guidelines
