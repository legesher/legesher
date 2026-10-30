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

**Applications** (vs-code):

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

## PyPI Publishing (manual dispatch)

Publishing is a manual run of **Publish to PyPI** (`publish-pypi.yml`). A PyPI upload is
public and permanent: a version number can never be re-uploaded, and deleting a release
does not free the file name (CORE-626).

### Credentials: Trusted Publishers, not API tokens

The workflow authenticates with OpenID Connect (`id-token: write`) through a
[Trusted Publisher](https://docs.pypi.org/trusted-publishers/) registration. There is no
`PYPI_API_TOKEN` or `TEST_PYPI_API_TOKEN` secret, and the workflow reads none. A package's
first upload to an index needs a pending publisher. On PyPI, register it from the
`Legesher` organization's Publishing page, so the project is created organization-owned.
PyPI and TestPyPI are separate instances, with separate accounts and separate
registrations.

An index holds only one pending publisher per repository, workflow and environment, and
all six packages share those, so register them one at a time: register a package's
pending publisher, dispatch that package alone (see "First publish to an index"), and
register the next once its project exists. From then on the registration is an ordinary
publisher, and every later run of the same workflow and environment uses it.

| Field | Value |
| --- | --- |
| Project name | one registration each for `legesher-i18n`, `legesher-core`, `legesher-runtime`, `legesher`, `legesher-mcp`, `legesher-language-server` |
| Owner | `legesher` |
| Repository | the repository name in use at publish time (a registration does not follow a rename) |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` on PyPI, `testpypi` on TestPyPI |

The job runs in the GitHub environment named by the `environment` input. Neither exists
yet. Create and protect `pypi` and `testpypi` before the first dispatch, limiting `pypi`
to the `main` branch and `testpypi` to `main` and `rehearsal/*` (see "TestPyPI first"): a
dispatch into a missing environment creates it with no protection rules.

### Order of dispatch

PyPI checks requirements at install time, not at upload. An upload out of order succeeds,
then fails to install, and the version number is consumed. Dispatch in this order and
confirm each upload before the next:

1. `runtime`, only when `legesher-runtime` has a new version (see "Versioning" in
   `libs/runtime/README.md`). It goes before `foundation` so that a failed runtime upload
   leaves no published CLI requiring a runtime the index lacks.
2. `foundation`: `legesher-core`, `legesher-i18n` and `legesher` in one run.
3. `mcp`: `legesher-mcp`.
4. `language-server`: `legesher-language-server`.

On the first publish, check installs once the whole set is up: `legesher-runtime` requires
`legesher-i18n>=0.23.0`, which is on the index only after `foundation` has uploaded. On
later publishes, a package can be checked as soon as its own requirements are on the index.

### First publish to an index

A pending publisher creates exactly one project, so a run that uploads several new
packages creates one of them and has the rest refused. On an index where the packages
do not exist yet, `foundation` is replaced by its three packages one at a time, and every
dispatch carries one package:

1. `runtime`
2. `i18n`
3. `core`
4. `cli` (the `legesher` distribution)
5. `mcp`
6. `language-server`

Before each dispatch, register that package's pending publisher; after it, confirm the
project exists before registering the next. Once all six exist, later releases follow
"Order of dispatch", with `foundation`, and never the `i18n`, `core` or `cli` targets:
the three share one version, and a file uploaded by one of them makes the next
`foundation` run fail to re-upload it.

If a run in this sequence is refused at the token exchange after the first project
exists, nothing was uploaded: stop and record it on the release ticket before going on.
The TestPyPI rehearsal runs the same sequence first, so it would surface there.

Do not dispatch the `all-language-packs`, `i18n-python-*` or `vs-code` targets, although
the dropdown still offers them. The language packs are not published from this
repository: they will be published later, from the
`legesher/language-packs` repository. `legesher-vs-code` is not published to PyPI.

### TestPyPI first

1. Dispatch each target with environment `testpypi` from a commit that sets each
   package's version to a development release of its NEXT version, so the real version
   numbers stay free on both indexes. For example, `0.23.1.dev1` while `0.23.0` is
   current: `0.23.0.dev1` sorts before `0.23.0`, so it does not satisfy an internal floor
   such as `legesher-i18n>=0.23.0`. The workflow has no version override.

   Make that commit on a short-lived branch named `rehearsal/<name>`, which `testpypi`
   allows and `pypi` refuses, and never merge it. A branch is simpler than a commit on
   `main` that is later reverted: on `main`, the rehearsal's version changes would start
   the foundation, mcp and language-server release workflows, and so would the revert.
2. Install from a clean virtual environment outside the workspace:

   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ legesher
   ```

   TestPyPI does not mirror PyPI, so the extra index supplies the third-party
   dependencies.
3. Repeat with environment `pypi` from `main`, in the same order, and verify each package
   from a clean virtual environment again.

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

- [Package versioning](../README.md#versioning-strategy) in the root README
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Workflows](../. github/workflows/)

---

**Last Updated:** 2026-10-13
**Part of:** CORE-439 - CI/CD Release Workflow
