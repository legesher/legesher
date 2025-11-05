# Legesher Metadata User Guide

Complete guide to understanding and using Legesher's metadata tracking system.

## Table of Contents

- [Overview](#overview)
- [What is Metadata?](#what-is-metadata)
- [Metadata Schema](#metadata-schema)
- [CLI Commands](#cli-commands)
- [Configuration](#configuration)
- [Privacy & Security](#privacy--security)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

Legesher's metadata tracking system provides a comprehensive audit trail for all translation operations and git filter activities. Every file you translate gets a corresponding metadata file that records:

- What language it was originally written in
- All translation operations performed
- Git filter operations (clean/smudge)
- Python version and translator version used
- Timestamps and git commit information

This metadata enables debugging, auditing, and understanding how your multilingual codebase has evolved over time.

## What is Metadata?

### What Does Metadata Track?

The metadata system records:

1. **File Information**
   - File path relative to repository root
   - Original language the file was written in
   - Canonical language stored in git (usually English)
   - Python version for the file

2. **Translation Records**
   - Target language of each translation
   - Translation method used (token_transformer, tree_sitter, manual)
   - Timestamp of translation
   - Git commit SHA (if available)
   - Translator version (legesher-core version)
   - Python version used for translation

3. **History Entries**
   - Git filter actions (clean or smudge)
   - Source and target languages
   - Timestamp of operation
   - Git commit SHA (if available)

### What Does Metadata NOT Track?

Importantly, metadata does **not** include:

- Source code content
- Variable names or function names
- Comments or docstrings
- Any personally identifiable information
- File contents of any kind

Metadata only contains file paths, language codes, timestamps, and version information.

### Where is Metadata Stored?

Metadata is stored in the `.legesher/metadata/` directory at your repository root. The directory structure mirrors your source tree:

```
.legesher/
└── metadata/
    ├── src/
    │   ├── calculator.py.yml
    │   ├── utils.py.yml
    │   └── models/
    │       └── user.py.yml
    └── tests/
        └── test_calculator.py.yml
```

Each source file gets a corresponding `.yml` metadata file that tracks its translation history.

## Metadata Schema

### Complete Example

Here's a complete metadata file (`.legesher/metadata/src/calculator.py.yml`):

```yaml
file: src/calculator.py
original_language: es
canonical_language: en
python_version: "3.13"
created_at: "2025-11-06T10:30:00Z"
updated_at: "2025-11-06T14:35:00Z"
translations:
  - language: en
    method: token_transformer
    timestamp: "2025-11-06T10:30:00Z"
    commit_sha: a91228a
    translator_version: "0.1.0"
    python_version: "3.13"
  - language: es
    method: token_transformer
    timestamp: "2025-11-06T10:31:00Z"
    commit_sha: a91228a
    translator_version: "0.1.0"
    python_version: "3.13"
history:
  - action: clean
    from_language: es
    to_language: en
    timestamp: "2025-11-06T10:35:00Z"
    commit_sha: def456
  - action: smudge
    from_language: en
    to_language: es
    timestamp: "2025-11-06T10:36:00Z"
    commit_sha: def456
```

### Field Descriptions

**Top-level fields:**

- `file`: Relative path from repository root (e.g., "src/calculator.py")
- `original_language`: ISO 639-1 language code for the language the file was originally authored in
- `canonical_language`: Language stored in git (always "en" for English by default)
- `python_version`: Python version string (e.g., "3.13", "3.12")
- `created_at`: ISO 8601 timestamp when metadata was first created
- `updated_at`: ISO 8601 timestamp of last metadata update

**Translation record fields:**

- `language`: Target language code (e.g., "en", "es", "ar")
- `method`: Translation method - one of:
  - `token_transformer`: Token-based translation (current MVP)
  - `tree_sitter`: AST-based translation (future)
  - `manual`: Manual translation by developer
- `timestamp`: ISO 8601 timestamp of translation operation
- `commit_sha`: Short git commit SHA (7 characters), or null if not in git
- `translator_version`: Version of legesher-core that performed translation
- `python_version`: Python version used for translation

**History entry fields:**

- `action`: Git filter action - either "clean" (working → git) or "smudge" (git → working)
- `from_language`: Source language before translation
- `to_language`: Target language after translation
- `timestamp`: ISO 8601 timestamp of git operation
- `commit_sha`: Short git commit SHA, or null if not available

## CLI Commands

Legesher provides comprehensive CLI commands for viewing and managing metadata.

### View Metadata for a File

Display comprehensive metadata including translations and recent history:

```bash
legesher metadata show src/calculator.py
```

**Example output:**

```
File: src/calculator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Original Language:    es
Canonical Language:   en
Python Version:       3.13
Created:              2025-11-06 10:30:00 UTC
Last Updated:         2025-11-06 14:35:00 UTC

Translations
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Language ┃ Method            ┃ Timestamp            ┃ Version ┃ Commit ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ en       │ token_transformer │ 2025-11-06 10:30:00  │ 0.1.0   │ a91228a│
│ es       │ token_transformer │ 2025-11-06 10:31:00  │ 0.1.0   │ a91228a│
└──────────┴───────────────────┴──────────────────────┴─────────┴────────┘

Recent History (last 5 entries)
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━┳━━━━┳━━━━━━━━┓
┃ Timestamp            ┃ Action ┃ From ┃ To ┃ Commit ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━╇━━━━╇━━━━━━━━┩
│ 2025-11-06 10:36:00  │ smudge │ en   │ es │ def456 │
│ 2025-11-06 10:35:00  │ clean  │ es   │ en │ def456 │
└──────────────────────┴────────┴──────┴────┴────────┘
```

**Options:**

- `--repo PATH`: Specify repository root (default: current directory)

### View Translation History

Show complete translation history for a file in chronological order:

```bash
legesher metadata history src/calculator.py
```

**Example output:**

```
Translation History: src/calculator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Timestamp            ┃ Action ┃ Translation  ┃ Commit ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 2025-11-06 10:36:00  │ smudge │ en → es      │ def456 │
│ 2025-11-06 10:35:00  │ clean  │ es → en      │ def456 │
│ 2025-11-06 10:31:00  │ smudge │ en → es      │ a91228a│
│ 2025-11-06 10:30:00  │ clean  │ es → en      │ a91228a│
└──────────────────────┴────────┴──────────────┴────────┘

Total entries: 4
```

**Options:**

- `--limit N`: Limit number of history entries shown (default: 10)
- `--repo PATH`: Specify repository root (default: current directory)

**Examples:**

```bash
# Show last 20 history entries
legesher metadata history src/calculator.py --limit 20

# Show history for specific repo
legesher metadata history src/main.py --repo /path/to/repo
```

### List All Tracked Files

Display all files with metadata:

```bash
legesher metadata list
```

**Example output:**

```
Tracked Files: 15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ File                  ┃ Original Lang┃ Python Ver ┃ Translations ┃ History ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ src/calculator.py     │ es           │ 3.13       │ 2            │ 4       │
│ src/utils.py          │ es           │ 3.13       │ 2            │ 2       │
│ src/models/user.py    │ ar           │ 3.12       │ 1            │ 1       │
│ tests/test_calc.py    │ en           │ 3.13       │ 0            │ 0       │
└───────────────────────┴──────────────┴────────────┴──────────────┴─────────┘
```

**Options:**

- `--repo PATH`: Specify repository root (default: current directory)

### Validate Metadata

Check that metadata file exists and is valid:

```bash
legesher metadata validate src/calculator.py
```

**Example output (valid):**

```
Validating metadata: src/calculator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Metadata is valid

Metadata Summary:
  File: src/calculator.py
  Original Language: es
  Python Version: 3.13
  Translations: 2
  History Entries: 4
```

**Example output (invalid):**

```
Validating metadata: src/unknown.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ Metadata is invalid or missing

Hint: Run 'legesher git-setup' to initialize metadata
```

**Options:**

- `--repo PATH`: Specify repository root (default: current directory)

### View Raw YAML

Display the raw YAML metadata file with syntax highlighting:

```bash
legesher metadata raw src/calculator.py
```

**Example output:**

```
Raw Metadata: src/calculator.py
Location: /path/to/repo/.legesher/metadata/src/calculator.py.yml
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1  file: src/calculator.py
  2  original_language: es
  3  canonical_language: en
  4  python_version: '3.13'
  5  created_at: '2025-11-06T10:30:00Z'
  6  updated_at: '2025-11-06T14:35:00Z'
  7  translations:
  8  - language: en
  9    method: token_transformer
 10    timestamp: '2025-11-06T10:30:00Z'
...
```

**Options:**

- `--repo PATH`: Specify repository root (default: current directory)

**Use cases:**

- Debugging metadata issues
- Understanding metadata structure
- Copying metadata for documentation
- Verifying metadata format

## Configuration

Metadata tracking can be configured in `.legesher/config.yml`:

```yaml
metadata:
  # Enable or disable metadata tracking
  enabled: true

  # Directory for storing metadata files (relative to repo root)
  directory: .legesher/metadata

  # Track metadata files in git
  track_in_git: true

  # Include verbose history information
  verbose_history: false

  # Maximum number of history entries per file
  max_history_entries: 100
```

### Configuration Options

**`enabled`** (boolean, default: `true`)

Enable or disable metadata tracking entirely. When disabled:

- No metadata files are created
- Existing metadata is not updated
- Translation still works normally
- CLI commands will show "metadata not found" messages

**Example - Disable metadata:**

```yaml
metadata:
  enabled: false
```

**`directory`** (string, default: `.legesher/metadata`)

Directory for storing metadata files, relative to repository root. Must be a relative path, not absolute.

**Example - Custom directory:**

```yaml
metadata:
  directory: .legesher/tracking
```

**`track_in_git`** (boolean, default: `true`)

Whether to track metadata files in git. When `true`, metadata is committed alongside source code. When `false`, add `.legesher/metadata/` to `.gitignore`.

**Example - Don't track in git:**

```yaml
metadata:
  track_in_git: false
```

Then add to `.gitignore`:

```gitignore
.legesher/metadata/
```

**`verbose_history`** (boolean, default: `false`)

Include detailed information in history entries. When enabled, history entries may include additional context like file size, line count, etc. (future feature).

**`max_history_entries`** (integer, default: `100`)

Maximum number of history entries to keep per file. Older entries are automatically removed when this limit is exceeded. Set to `0` for unlimited entries (not recommended).

**Example - Limit history:**

```yaml
metadata:
  max_history_entries: 50
```

### Configuration Precedence

Configuration is loaded with the following precedence (highest to lowest):

1. **Project config**: `.legesher/config.yml` (in repository root)
2. **User config**: `~/.legesher/config.yml` (in home directory)
3. **Default values**: Built-in defaults

This means project settings override user settings, which override defaults.

## Privacy & Security

### What Information is Stored?

Metadata files contain ONLY:

- File paths (relative to repository root)
- Language codes (ISO 639-1, e.g., "es", "en", "ar")
- Timestamps (ISO 8601 format)
- Git commit SHAs (short form, 7 characters)
- Version strings (legesher-core version, Python version)
- Translation methods (e.g., "token_transformer")

### What is NOT Stored?

Metadata does NOT contain:

- Source code
- Variable names, function names, class names
- Comments or docstrings
- String literals or data
- File contents of any kind
- Personally identifiable information (PII)
- Secrets, credentials, or API keys

### Local-First Design

- All metadata is stored locally in `.legesher/metadata/`
- No cloud services required
- No external network calls
- No data transmission to external servers
- You have complete control over your metadata

### Git Considerations

By default, metadata is tracked in git. This means:

- Metadata is part of your git history
- Collaborators see metadata in their clones
- Metadata shows in git diffs and logs

If you don't want metadata in git:

1. Set `track_in_git: false` in config
2. Add `.legesher/metadata/` to `.gitignore`

### File Security

- All YAML writes use atomic write-then-rename to prevent corruption
- Temporary files are cleaned up even on crashes
- No partial writes can occur during git operations
- File permissions match repository defaults

## Use Cases

### 1. Debugging Translation Issues

When a translation doesn't work as expected, check the metadata:

```bash
# View complete history
legesher metadata history src/problematic_file.py

# Check which translator version was used
legesher metadata show src/problematic_file.py
```

This helps identify:

- Which translation method was used
- What Python version was active
- When the issue was introduced (commit SHA)
- Whether file has been translated before

### 2. Auditing Team Translations

For team projects, use metadata to understand translation patterns:

```bash
# List all tracked files
legesher metadata list

# View specific file history
legesher metadata history src/core/engine.py --limit 50
```

This helps answer:

- Which files have been translated?
- What languages are being used?
- When did translations happen?
- Who made the changes? (via git commit SHA)

### 3. Migration Assistance

When migrating between Legesher versions:

```bash
# Validate all metadata
for file in $(find . -name "*.py"); do
  legesher metadata validate "$file"
done
```

This helps:

- Identify outdated metadata
- Find corrupted metadata files
- Verify migration success

### 4. Understanding File Evolution

Track how files have evolved across languages:

```bash
# View complete translation history
legesher metadata history src/calculator.py --limit 100
```

This shows:

- How many times file has been translated
- Language transitions over time
- Translation method changes
- Git operations (clean/smudge) timeline

### 5. Quality Assurance

Verify translation quality and consistency:

```bash
# Check all files use same Python version
legesher metadata list | grep -v "3.13"

# Verify all files have metadata
legesher metadata list
```

This helps ensure:

- Consistent Python versions
- All files are tracked
- No missing metadata

## Troubleshooting

### Metadata File Not Found

**Problem:** CLI commands show "No metadata found for file"

**Solution:**

1. Check if metadata is enabled:

   ```bash
   cat .legesher/config.yml | grep enabled
   ```

2. Initialize metadata:

   ```bash
   legesher git-setup
   ```

3. Verify file path is correct (relative to repo root)

### Corrupted Metadata File

**Problem:** Metadata file exists but is invalid

**Solution:**

1. Validate the metadata:

   ```bash
   legesher metadata validate src/file.py
   ```

2. View raw YAML to see corruption:

   ```bash
   legesher metadata raw src/file.py
   ```

3. Fix manually or regenerate:

   ```bash
   # Backup corrupted file
   cp .legesher/metadata/src/file.py.yml /tmp/backup.yml

   # Remove corrupted file
   rm .legesher/metadata/src/file.py.yml

   # Re-run git setup to regenerate
   legesher git-setup
   ```

### Metadata Directory Doesn't Exist

**Problem:** `.legesher/metadata/` directory is missing

**Solution:**

1. Run git setup to create directory:

   ```bash
   legesher git-setup
   ```

2. Or create manually:

   ```bash
   mkdir -p .legesher/metadata
   ```

### Too Many History Entries

**Problem:** Metadata files are too large due to extensive history

**Solution:**

1. Reduce max history entries in config:

   ```yaml
   metadata:
     max_history_entries: 50
   ```

2. Clean up existing metadata (manual):

   ```python
   from pathlib import Path
   import yaml

   # Read metadata
   with open('.legesher/metadata/src/file.py.yml') as f:
       data = yaml.safe_load(f)

   # Keep only last 50 entries
   data['history'] = data['history'][-50:]

   # Write back
   with open('.legesher/metadata/src/file.py.yml', 'w') as f:
       yaml.safe_dump(data, f)
   ```

### Metadata Out of Sync

**Problem:** Metadata doesn't match actual file state

**Solution:**

1. Validate metadata:

   ```bash
   legesher metadata validate src/file.py
   ```

2. Check git status:

   ```bash
   git status src/file.py
   ```

3. Regenerate metadata by re-running git filters:

   ```bash
   # Checkout file again to trigger smudge
   git checkout -- src/file.py
   ```

### Cannot Disable Metadata

**Problem:** Metadata still being created even when disabled

**Solution:**

1. Check configuration is properly loaded:

   ```bash
   cat .legesher/config.yml
   ```

2. Ensure config file is in repository root

3. Verify config syntax is valid YAML

4. Check for typos in field names

### Permission Errors

**Problem:** Cannot write metadata files

**Solution:**

1. Check directory permissions:

   ```bash
   ls -la .legesher/
   ```

2. Ensure you have write access:

   ```bash
   chmod -R u+w .legesher/metadata/
   ```

3. Check disk space:

   ```bash
   df -h .
   ```

## Advanced Usage

### Programmatic Access

Access metadata from Python code:

```python
from pathlib import Path
from legesher_core.metadata import MetadataManager

# Initialize manager
repo_root = Path.cwd()
manager = MetadataManager(repo_root)

# Read metadata
metadata = manager.get_metadata(Path("src/calculator.py"))
if metadata:
    print(f"Original language: {metadata['original_language']}")
    print(f"Created: {metadata['created_at']}")
    print(f"Translations: {len(metadata['translations'])}")

    # Access translation records
    for trans in metadata['translations']:
        print(f"  - {trans['language']} via {trans['method']}")

    # Access history
    for entry in metadata['history']:
        print(f"  - {entry['action']}: {entry['from_language']} → {entry['to_language']}")

# List all tracked files
all_files = manager.list_metadata_files()
print(f"Tracking {len(all_files)} files")

# Validate metadata
is_valid = manager.validate_metadata(Path("src/calculator.py"))
print(f"Valid: {is_valid}")
```

### Bulk Operations

Process multiple files:

```python
from pathlib import Path
from legesher_core.metadata import MetadataManager

manager = MetadataManager(Path.cwd())

# Get all metadata files
metadata_files = manager.list_metadata_files()

# Process each file
for metadata_file in metadata_files:
    # Get source file path from metadata file
    relative_path = metadata_file.relative_to(manager.metadata_dir)
    source_file = str(relative_path)[:-4]  # Remove .yml

    # Load metadata
    metadata = manager.get_metadata(Path(source_file))
    if metadata:
        print(f"{source_file}: {metadata['original_language']}")
```

### Custom Metadata Analysis

Analyze translation patterns:

```python
from collections import Counter
from pathlib import Path
from legesher_core.metadata import MetadataManager

manager = MetadataManager(Path.cwd())

# Count languages
language_counter = Counter()
for metadata_file in manager.list_metadata_files():
    relative_path = metadata_file.relative_to(manager.metadata_dir)
    source_file = str(relative_path)[:-4]

    metadata = manager.get_metadata(Path(source_file))
    if metadata:
        language_counter[metadata['original_language']] += 1

print("Files by original language:")
for lang, count in language_counter.most_common():
    print(f"  {lang}: {count} files")
```

### Integration with CI/CD

Validate metadata in CI pipeline:

```bash
#!/bin/bash
# validate-metadata.sh

echo "Validating metadata for all tracked files..."

# Get all Python files
for file in $(find . -name "*.py" -not -path "./.venv/*"); do
  if ! legesher metadata validate "$file" &>/dev/null; then
    echo "❌ Invalid metadata: $file"
    exit 1
  fi
done

echo "✅ All metadata valid"
```

Add to GitHub Actions:

```yaml
name: Validate Metadata

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Legesher
        run: pip install legesher
      - name: Validate metadata
        run: ./validate-metadata.sh
```

### Exporting Metadata

Export metadata to JSON for analysis:

```python
import json
from pathlib import Path
from legesher_core.metadata import MetadataManager

manager = MetadataManager(Path.cwd())

# Collect all metadata
all_metadata = []
for metadata_file in manager.list_metadata_files():
    relative_path = metadata_file.relative_to(manager.metadata_dir)
    source_file = str(relative_path)[:-4]

    metadata = manager.get_metadata(Path(source_file))
    if metadata:
        all_metadata.append(metadata)

# Export to JSON
with open('metadata_export.json', 'w') as f:
    json.dump(all_metadata, f, indent=2)

print(f"Exported {len(all_metadata)} metadata files")
```

### Migration Between Repositories

Copy metadata to a new repository:

```bash
#!/bin/bash
# migrate-metadata.sh

SOURCE_REPO="/path/to/source"
TARGET_REPO="/path/to/target"

# Copy metadata directory
cp -r "$SOURCE_REPO/.legesher/metadata" "$TARGET_REPO/.legesher/"

# Copy config
cp "$SOURCE_REPO/.legesher/config.yml" "$TARGET_REPO/.legesher/"

echo "✅ Metadata migrated"
```

---

## Summary

Legesher's metadata tracking system provides comprehensive audit trails for translation operations while maintaining privacy and security. It enables debugging, auditing, and understanding how multilingual codebases evolve over time.

**Key Points:**

- Metadata tracks translations and git operations, not source code
- Stored locally in `.legesher/metadata/` as YAML files
- Comprehensive CLI commands for viewing and validating metadata
- Configurable via `.legesher/config.yml`
- Local-first, no cloud services required
- Can be tracked in git or excluded via `.gitignore`

**Next Steps:**

- Read the [API documentation](../libs/core/legesher_core/metadata.py) for programmatic access
- See [git workflow documentation](git-workflow.md) for how metadata integrates with git
- Check [configuration guide](configuration.md) for all configuration options

For issues or questions, see the [troubleshooting section](#troubleshooting) above.
