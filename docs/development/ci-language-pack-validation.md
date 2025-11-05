# CI Integration for Language Pack Validation

Automatically validate language packs in your CI/CD pipeline using GitHub Actions.

## GitHub Actions Workflow

### Basic Validation Workflow

Create `.github/workflows/validate-language-packs.yml`:

```yaml
name: Validate Language Packs

on:
  pull_request:
    paths:
      - 'libs/i18n/languages/**/*.yml'
  push:
    branches:
      - main
    paths:
      - 'libs/i18n/languages/**/*.yml'

jobs:
  validate:
    name: Validate Language Pack Files
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd libs/i18n
          uv sync

      - name: Validate all language packs
        run: |
          cd libs/i18n
          for file in languages/**/*.yml; do
            echo "Validating $file..."
            uv run legesher-i18n validate "$file" --strict
          done
```

### Validate Only Changed Files

More efficient workflow that only validates changed language packs:

```yaml
name: Validate Changed Language Packs

on:
  pull_request:
    paths:
      - 'libs/i18n/languages/**/*.yml'

jobs:
  validate:
    name: Validate Changed Packs
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch all history for changed file detection

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd libs/i18n
          uv sync

      - name: Get changed language pack files
        id: changed-files
        uses: tj-actions/changed-files@v45
        with:
          files: |
            libs/i18n/languages/**/*.yml

      - name: Validate changed language packs
        if: steps.changed-files.outputs.any_changed == 'true'
        run: |
          cd libs/i18n
          for file in ${{ steps.changed-files.outputs.all_changed_files }}; do
            # Remove libs/i18n/ prefix if present
            file_path="${file#libs/i18n/}"
            echo "Validating $file_path..."
            uv run legesher-i18n validate "$file_path" --strict
          done

      - name: No changes detected
        if: steps.changed-files.outputs.any_changed != 'true'
        run: echo "No language pack files changed, skipping validation"
```

### Matrix Strategy for Multiple Languages

Validate different languages in parallel:

```yaml
name: Validate Language Packs (Matrix)

on:
  pull_request:
    paths:
      - 'libs/i18n/languages/**/*.yml'

jobs:
  detect-languages:
    name: Detect Changed Languages
    runs-on: ubuntu-latest
    outputs:
      languages: ${{ steps.set-languages.outputs.languages }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect changed languages
        id: set-languages
        run: |
          # Get unique language codes from changed files
          languages=$(git diff --name-only origin/main...HEAD | \
            grep 'libs/i18n/languages' | \
            grep -oP '(?<=/)[a-z]{2}\.yml$' | \
            sed 's/\.yml$//' | \
            sort -u | \
            jq -R -s -c 'split("\n")[:-1]')
          echo "languages=$languages" >> $GITHUB_OUTPUT

  validate:
    name: Validate ${{ matrix.language }}
    needs: detect-languages
    if: needs.detect-languages.outputs.languages != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: ${{ fromJson(needs.detect-languages.outputs.languages) }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd libs/i18n
          uv sync

      - name: Validate ${{ matrix.language }} packs
        run: |
          cd libs/i18n
          for file in languages/**/${{ matrix.language }}.yml; do
            echo "Validating $file..."
            uv run legesher-i18n validate "$file" --strict
          done
```

### With Coverage and Reporting

Add validation reports as PR comments:

```yaml
name: Validate with Reporting

on:
  pull_request:
    paths:
      - 'libs/i18n/languages/**/*.yml'

jobs:
  validate:
    name: Validate and Report
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd libs/i18n
          uv sync

      - name: Validate and generate report
        id: validate
        run: |
          cd libs/i18n

          echo "## Language Pack Validation Results" > report.md
          echo "" >> report.md

          failed=0
          passed=0

          for file in languages/**/*.yml; do
            echo "Validating $file..."
            if uv run legesher-i18n validate "$file" --strict > output.txt 2>&1; then
              echo "✅ \`$file\` - Passed" >> report.md
              ((passed++))
            else
              echo "❌ \`$file\` - **Failed**" >> report.md
              echo "\`\`\`" >> report.md
              cat output.txt >> report.md
              echo "\`\`\`" >> report.md
              ((failed++))
            fi
          done

          echo "" >> report.md
          echo "**Summary:** $passed passed, $failed failed" >> report.md

          echo "failed=$failed" >> $GITHUB_OUTPUT

      - name: Comment PR
        uses: actions/github-script@v7
        if: always()
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('libs/i18n/report.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

      - name: Fail if any validations failed
        if: steps.validate.outputs.failed != '0'
        run: exit 1
```

## Additional CI Checks

### Generate Compatibility Matrix

Automatically generate and commit updated compatibility matrices:

```yaml
      - name: Generate compatibility matrix
        run: |
          cd libs/i18n
          for lang in es ar; do
            uv run python scripts/generate_compatibility_matrix.py $lang \
              --output ../../docs/compatibility/${lang}-keywords.md
          done

      - name: Check for changes
        id: git-check
        run: |
          git diff --exit-code docs/compatibility/ || echo "changed=true" >> $GITHUB_OUTPUT

      - name: Commit updated matrices
        if: steps.git-check.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/compatibility/
          git commit -m "docs: Update compatibility matrices"
          git push
```

## Best Practices

1. **Run on PR and main** - Validate both during PR review and after merge
2. **Use --strict mode** - Fail on warnings in CI to maintain quality
3. **Cache dependencies** - Use GitHub Actions caching for faster builds
4. **Only validate changed files** - More efficient for large repos
5. **Add status checks** - Require validation to pass before merging

## Troubleshooting

### Workflow doesn't trigger

Check the `paths` filter matches your language pack location:

```yaml
paths:
  - 'libs/i18n/languages/**/*.yml'
```

### Permission denied errors

Ensure workflow has necessary permissions in `.github/workflows/`:

```yaml
permissions:
  contents: write  # For committing generated files
  pull-requests: write  # For commenting on PRs
```

### Validation passes locally but fails in CI

- Check Python version matches (use `python-version: '3.13'`)
- Verify uv is properly installed
- Ensure dependencies are synced with `uv sync`

## Related

- [Pre-commit Hooks](./pre-commit-language-packs.md) - Local validation
- [Manual Validation](../libs/i18n/README.md#validation) - Using CLI directly
