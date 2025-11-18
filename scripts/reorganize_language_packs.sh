#!/bin/bash

# Language Pack Reorganization Script
# ⚠️  HISTORICAL REFERENCE ONLY - DO NOT RUN ⚠️
#
# This script was used for the one-time migration from flat structure
# (libs/i18n-python-{lang}/) to hierarchical structure
# (libs/i18n/language-packs/python/{lang}/) completed on 2025-11-17.
#
# Kept for historical reference and documentation purposes.
# See PR #54 and Linear issue CORE-462 for details.
#
# Original purpose: Reorganize language packs into new hierarchical structure
# Status: COMPLETED - Migration finished successfully

set -e  # Exit on any error

echo "========================================="
echo "Language Pack Reorganization"
echo "Linear Issue: CORE-462"
echo "========================================="
echo ""

# Ensure we're on the feature branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "feature/language-pack-reorganization" ]; then
    echo "❌ Not on feature/language-pack-reorganization branch (currently on: $CURRENT_BRANCH)"
    echo "Please checkout the feature branch first:"
    echo "  git checkout feature/language-pack-reorganization"
    exit 1
fi

echo "✓ On correct branch: $CURRENT_BRANCH"
echo ""

# Step 1: Create directory structure
echo "[1/9] Creating new directory structure..."
mkdir -p libs/i18n/language-packs/python/{ar,es,en,fr,zh}
echo "✓ Created libs/i18n/language-packs/python/{ar,es,en,fr,zh}"
echo ""

# Step 2: Move existing packages
echo "[2/9] Moving existing packages..."
git mv libs/i18n-python-ar libs/i18n/language-packs/python/ar
echo "✓ Moved libs/i18n-python-ar → libs/i18n/language-packs/python/ar"

git mv libs/i18n-python-es libs/i18n/language-packs/python/es
echo "✓ Moved libs/i18n-python-es → libs/i18n/language-packs/python/es"
echo ""

# Step 3: Create new packages from ar template
echo "[3/9] Creating new language pack packages (en, fr, zh)..."
for lang in en fr zh; do
    echo "  Creating $lang package..."

    # Copy structure from ar
    cp -r libs/i18n/language-packs/python/ar/* libs/i18n/language-packs/python/$lang/

    # Rename module directory
    mv libs/i18n/language-packs/python/$lang/legesher_i18n_python_ar \
       libs/i18n/language-packs/python/$lang/legesher_i18n_python_$lang

    # Update pyproject.toml
    sed -i '' "s/legesher-i18n-python-ar/legesher-i18n-python-$lang/g" \
        libs/i18n/language-packs/python/$lang/pyproject.toml
    sed -i '' "s/legesher_i18n_python_ar/legesher_i18n_python_$lang/g" \
        libs/i18n/language-packs/python/$lang/pyproject.toml
    sed -i '' "s/i18n-python-ar-v/i18n-python-$lang-v/g" \
        libs/i18n/language-packs/python/$lang/pyproject.toml

    # Update __init__.py
    sed -i '' "s/legesher_i18n_python_ar/legesher_i18n_python_$lang/g" \
        libs/i18n/language-packs/python/$lang/legesher_i18n_python_$lang/__init__.py

    # Clear out old packs (will be replaced with correct language)
    rm -f libs/i18n/language-packs/python/$lang/legesher_i18n_python_$lang/packs/*.yml

    echo "  ✓ Created $lang package"
done
echo ""

# Step 4: Copy YAML files from programming_languages/
echo "[4/9] Copying YAML files from source of truth..."
for lang in ar es en fr zh; do
    echo "  Copying $lang YAML files..."
    for version in 3.10 3.11 3.12 3.13 3.14; do
        src="libs/i18n/programming_languages/python/$version/$lang.yml"
        dest="libs/i18n/language-packs/python/$lang/legesher_i18n_python_$lang/packs/$version.yml"

        if [ -f "$src" ]; then
            cp "$src" "$dest"

            # Update extends path if it exists
            if grep -q "^extends:" "$dest" 2>/dev/null; then
                # Change "../3.XX/lang.yml" to "./3.XX.yml"
                sed -i '' -E "s|extends: \.\./([0-9]+\.[0-9]+)/$lang\.yml|extends: ./\1.yml|g" "$dest"
            fi
        else
            echo "    ⚠ Warning: $src not found"
        fi
    done

    file_count=$(ls -1 libs/i18n/language-packs/python/$lang/legesher_i18n_python_$lang/packs/*.yml 2>/dev/null | wc -l)
    echo "  ✓ Copied $file_count files for $lang"
done
echo ""

# Step 5: Add new files to git
echo "[5/9] Adding new packages to git..."
git add libs/i18n/language-packs/python/en/
git add libs/i18n/language-packs/python/fr/
git add libs/i18n/language-packs/python/zh/
echo "✓ Added new packages to git"
echo ""

# Step 6: Update CHANGELOGs
echo "[6/9] Updating CHANGELOG files..."
for lang in ar es en fr zh; do
    changelog_file="libs/i18n/language-packs/python/$lang/CHANGELOG.md"

    if [ "$lang" = "ar" ] || [ "$lang" = "es" ]; then
        # Existing packages - add v0.0.2 entry
        cat > "$changelog_file" << EOF
# Changelog

All notable changes to legesher-i18n-python-$lang will be documented in this file.

## [Unreleased]

## [0.0.2] - 2025-11-17

### Added
- Added Python 3.14 support
- Added 47 additional builtin terminology translations (88 total builtins, up from 41)

### Changed
- Improved translation quality from AI pipeline using Aya AI Model
- Migrated to new monorepo structure under \`libs/i18n/language-packs/\`

### Fixed
- Updated translation accuracy for core keywords and builtins

## [0.0.1] - 2025-11-07

### Added
- Initial release with Python 3.10, 3.11, 3.12, 3.13 support
- 38 keyword translations
- 41 builtin function translations

[Unreleased]: https://github.com/legesher/legesher/compare/i18n-python-$lang-v0.0.2...HEAD
[0.0.2]: https://github.com/legesher/legesher/compare/i18n-python-$lang-v0.0.1...i18n-python-$lang-v0.0.2
[0.0.1]: https://github.com/legesher/legesher/releases/tag/i18n-python-$lang-v0.0.1
EOF
    else
        # New packages - v0.0.2 as initial release
        cat > "$changelog_file" << EOF
# Changelog

All notable changes to legesher-i18n-python-$lang will be documented in this file.

## [Unreleased]

## [0.0.2] - 2025-11-17

### Added
- Initial release with Python 3.10, 3.11, 3.12, 3.13, 3.14 support
- 38 keyword translations
- 88 builtin function translations
- Translation quality from AI pipeline using Aya AI Model

[Unreleased]: https://github.com/legesher/legesher/compare/i18n-python-$lang-v0.0.2...HEAD
[0.0.2]: https://github.com/legesher/legesher/releases/tag/i18n-python-$lang-v0.0.2
EOF
    fi
    echo "  ✓ Updated CHANGELOG for $lang"
done
echo ""

# Step 7: Update package versions to 0.0.2
echo "[7/9] Bumping package versions to 0.0.2..."
for lang in ar es en fr zh; do
    sed -i '' 's/version = "0.0.1"/version = "0.0.2"/g' \
        libs/i18n/language-packs/python/$lang/pyproject.toml
done
echo "✓ Bumped all packages to v0.0.2"
echo ""

# Step 8: Verify structure
echo "[8/9] Verifying new structure..."
echo ""
echo "Language pack packages:"
for lang in ar es en fr zh; do
    pack_dir="libs/i18n/language-packs/python/$lang"
    yaml_count=$(ls -1 $pack_dir/legesher_i18n_python_$lang/packs/*.yml 2>/dev/null | wc -l | tr -d ' ')
    echo "  ✓ $lang: $yaml_count YAML files"
done
echo ""

# Step 9: Summary
echo "[9/9] Summary"
echo "========================================="
echo ""
echo "✓ Created new hierarchical structure:"
echo "  libs/i18n/language-packs/python/{ar,es,en,fr,zh}/"
echo ""
echo "✓ Moved existing packages:"
echo "  - libs/i18n-python-ar → .../python/ar"
echo "  - libs/i18n-python-es → .../python/es"
echo ""
echo "✓ Created new packages:"
echo "  - en (English)"
echo "  - fr (French)"
echo "  - zh (Chinese)"
echo ""
echo "✓ Copied 25 YAML files (5 languages × 5 versions)"
echo "✓ Updated all CHANGELOGs with v0.0.2 entry"
echo "✓ Bumped all package versions to 0.0.2"
echo ""
echo "========================================="
echo "Next steps:"
echo "1. Update root pyproject.toml with new package paths"
echo "2. Refactor LanguagePackLoader with importlib discovery"
echo "3. Update language-server integration paths"
echo "4. Delete old locations (programming_languages/, etc.)"
echo "5. Update documentation"
echo "6. Run tests and validation"
echo ""
echo "Review changes with:"
echo "  git status"
echo "  git diff --staged"
echo "========================================="
