# Pre-commit Hook for Language Pack Validation

Automatically validate language pack files before committing to ensure quality and consistency.

## Setup

### 1. Install pre-commit

```bash
pip install pre-commit
# or with uv
uv pip install pre-commit
```

### 2. Add to `.pre-commit-config.yaml`

Add the following configuration to your `.pre-commit-config.yaml` file:

```yaml
repos:
  # ... your existing hooks ...

  # Language pack validation
  - repo: local
    hooks:
      - id: validate-language-packs
        name: Validate language packs
        entry: uv run legesher-i18n validate
        language: system
        files: 'libs/i18n/languages/.*\.yml$'
        pass_filenames: true
        description: Validate language pack YAML files
```

### 3. Install the hook

```bash
pre-commit install
```

## Usage

### Automatic Validation

Now, every time you commit changes to language pack files (`.yml` files in `libs/i18n/languages/`), the validation hook will run automatically:

```bash
git add libs/i18n/languages/python/3.13/es.yml
git commit -m "Update Spanish keywords"
```

Output:

```
Validate language packs.........................................Passed
```

### Manual Validation

You can also run the hook manually on all files:

```bash
pre-commit run validate-language-packs --all-files
```

Or on specific files:

```bash
pre-commit run validate-language-packs --files libs/i18n/languages/python/3.13/es.yml
```

## Strict Mode

For stricter validation that fails on warnings, modify the hook:

```yaml
      - id: validate-language-packs
        name: Validate language packs (strict)
        entry: uv run legesher-i18n validate --strict
        language: system
        files: 'libs/i18n/languages/.*\.yml$'
        pass_filenames: true
```

## Validation Checks

The hook performs:

1. **Schema validation** - Ensures YAML structure matches required schema
2. **Completeness checks** - Warns about missing keywords or metadata
3. **Inheritance validation** - Verifies extends paths are valid
4. **Format validation** - Checks language codes, version format, etc.

## Example Output

### Success

```
Validating: libs/i18n/languages/python/3.13/es.yml
✅ Schema validation passed

Loading pack with inheritance...
✅ Pack loaded successfully

Pack Information:
   Language: es
   Target: python
   Version: 3.13
   Keywords: 37
   Builtins: 34
   Inheritance: 3.10 → 3.11 → 3.12 → 3.13

✅ Validation complete! (0 warnings)
```

### With Warnings (non-strict mode passes)

```
Validating: libs/i18n/languages/python/3.13/es.yml
✅ Schema validation passed
⚠️  Warning: No keywords defined in pack
⚠️  Warning: Metadata missing last_updated field

✅ Validation complete! (2 warnings)
```

### With Errors (fails)

```
Validating: libs/i18n/languages/python/3.13/es.yml
❌ Validation failed: libs/i18n/languages/python/3.13/es.yml
   • Field required: language
   • Field required: version
```

## Troubleshooting

### Hook doesn't run

Check that the file pattern matches:

```bash
pre-commit run validate-language-packs --files libs/i18n/languages/python/3.10/es.yml --verbose
```

### Command not found

Ensure `legesher-i18n` is installed in your environment:

```bash
uv pip install -e libs/i18n
```

### Skipping hooks temporarily

To commit without running hooks (not recommended):

```bash
git commit --no-verify
```

## Related

- [CI Integration](./ci-language-pack-validation.md) - Validate in GitHub Actions
- [Manual Validation](../libs/i18n/README.md#validation) - Using CLI directly
