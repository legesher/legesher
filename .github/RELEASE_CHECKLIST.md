# Release Checklist

Quick reference checklist for releasing Legesher packages.

## Pre-Release Checklist

Before triggering a release:

- [ ] All tests passing in CI
- [ ] All PRs for the milestone merged
- [ ] On latest `main` branch (`git pull origin main`)
- [ ] Working directory is clean (`git status`)
- [ ] CHANGELOG reviewed (semantic-release will generate)
- [ ] No known critical bugs

## Release Methods

### 1. Automatic Release (Recommended)

Releases happen automatically when you merge to `main`:

**Foundation Suite** (core, i18n, legesher):

```bash
# Merge PR that touches foundation packages
# GitHub Actions automatically:
# - Runs semantic-release
# - Creates git tag (v0.X.Y)
# - Updates CHANGELOGs
# - Creates GitHub Release
# - Builds packages
```

**Language Packs** (i18n-python-es, i18n-python-ar):

```bash
# Merge PR that touches language pack
# GitHub Actions automatically releases changed packs
```

**Applications** (vs-code, home):

```bash
# Merge PR that touches app
# GitHub Actions automatically releases changed apps
```

### 2. Manual Release

Trigger release manually via GitHub Actions:

1. Go to **Actions** tab
2. Select workflow:
   - **Release Foundation Suite**
   - **Release Language Packs**
   - **Release Applications**
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow** button

**For language packs/apps:**

- Select target/language or app name
- Click **Run workflow**

## Post-Release Verification

After release completes:

- [ ] Check **Actions** tab - workflow completed successfully
- [ ] Verify git tag created: `git fetch --tags && git tag -l | tail -5`
- [ ] Check **Releases** page - GitHub Release created
- [ ] Verify CHANGELOG.md updated in package directory
- [ ] Check build artifacts uploaded (Actions → Workflow → Artifacts)
- [ ] Version numbers match across packages (for foundation)

## Version Verification

```bash
# Check what version was released
git tag -l | tail -5

# View release commit
git log -1

# Check package versions (foundation)
cat pyproject.toml | grep version
cat libs/core/pyproject.toml | grep version
cat libs/i18n/pyproject.toml | grep version
cat libs/legesher/pyproject.toml | grep version
```

## PyPI Publishing (Optional)

**Currently disabled by default.** To publish to PyPI:

1. Go to **Actions** → **Publish to PyPI**
2. Click **Run workflow**
3. Select package: `foundation`, `i18n-python-es`, etc.
4. Select environment:
   - `testpypi` - Test environment (recommended first)
   - `pypi` - Production
5. Click **Run workflow**

**First time setup:**

- Create PyPI and TestPyPI accounts
- Generate API tokens
- Add to GitHub Secrets:
  - `PYPI_API_TOKEN`
  - `TEST_PYPI_API_TOKEN`

## Troubleshooting

### "No release needed"

**Cause:** No conventional commits since last release.

**Fix:** Ensure commits follow format:

- `feat:` - New feature (minor bump)
- `fix:` - Bug fix (patch bump)
- `BREAKING CHANGE:` - Breaking change (major bump)

### Workflow didn't trigger

**Cause:** Changes didn't touch watched paths.

**Fix:** Use manual trigger:

1. Actions → Select workflow
2. Run workflow → main branch

### Version mismatch in foundation

**Cause:** Foundation versions out of sync.

**Fix:** Run sync script:

```bash
./scripts/sync-foundation-versions.py
git add -A
git commit -m "chore: sync foundation versions"
git push origin main
```

### Release commit triggered another release

**Cause:** Release commit has `chore(release):` prefix.

**Fix:** Workflow already skips these via:

```yaml
if: "!contains(github.event.head_commit.message, 'chore(release)')"
```

If loop occurs, check workflow configuration.

## Emergency Rollback

If a release has critical issues:

### Option 1: Release a Fix (Recommended)

```bash
# Fix the issue
git commit -m "fix: critical bug in X"
git push origin main

# Automatic release will create v0.X.Y+1
```

### Option 2: Delete Release and Tag

⚠️ **Use with caution** - Only if release hasn't been distributed.

```bash
# Delete tag locally and remotely
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Delete GitHub Release (via web UI or gh cli)
gh release delete v0.2.0 --yes

# Revert release commit
git revert HEAD
git push origin main
```

## Release Cadence

**Foundation Suite:**

- Quarterly releases
- Or when significant features are ready
- Coordinate with team

**Language Packs:**

- As needed for translations
- When new Python versions released
- Community contributions

**Applications:**

- Weekly, monthly, or per feature
- Independent of foundation
- Bug fixes can go out immediately

## Related Documentation

- [Full Release Process](../docs/RELEASE_PROCESS.md)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Workflows](../. github/workflows/)

---

**Last Updated:** 2025-11-07
**Part of:** CORE-439 - CI/CD Release Workflow
