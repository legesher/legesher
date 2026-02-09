#!/bin/bash

#######################################################################
# Build Preview Release - Compile wheels and copy to preview repo
#
# This script builds Python wheels from the monorepo packages and
# copies them to the preview-repo repository for distribution.
#
# Usage:
#   ./scripts/build-preview-release.sh [version] [preview-repo-path]
#
# Example:
#   ./scripts/build-preview-release.sh 0.1.0-beta.2 ../Legesher/preview-repo
#
# Requirements:
# - uv installed
# - preview-repo repository cloned locally
#######################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION="${1:-0.1.0-beta.1}"
PREVIEW_REPO="${2:-../Legesher/preview-repo}"

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Build Preview Release - v${VERSION}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header

# Validate preview repo exists
if [ ! -d "${PREVIEW_REPO}" ]; then
    print_error "Preview repository not found at: ${PREVIEW_REPO}"
    echo "   Please provide the correct path as second argument"
    echo "   Example: ./scripts/build-preview-release.sh 0.1.0-beta.2 /path/to/preview-repo"
    exit 1
fi

print_success "Found preview repository at: ${PREVIEW_REPO}"

# Resolve to absolute path so cd's don't break relative references
RELEASE_DIR="$(cd "${PREVIEW_REPO}" && pwd)/releases/v${VERSION}"

# Create release directory
print_info "Creating release directory: ${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"
print_success "Release directory created"

echo ""
echo "🔨 Building Python wheels..."
echo ""

# Build core package
print_info "Building legesher-core..."
cd libs/core
rm -rf dist/
uv build -o dist
cp dist/*.whl "${RELEASE_DIR}/"
print_success "legesher-core built and copied"

# Build i18n infrastructure package
print_info "Building legesher-i18n..."
cd ../i18n
rm -rf dist/
uv build -o dist
cp dist/*.whl "${RELEASE_DIR}/"
print_success "legesher-i18n built and copied"

# Build main legesher package
print_info "Building legesher..."
cd ../legesher
rm -rf dist/
uv build -o dist
cp dist/*.whl "${RELEASE_DIR}/"
print_success "legesher built and copied"

# Build language server
print_info "Building legesher-language-server..."
cd ../language-server
rm -rf dist/
uv build -o dist
cp dist/*.whl "${RELEASE_DIR}/"
print_success "legesher-language-server built and copied"

# Build individual language packs
print_info "Building language packs..."
cd ../i18n/language-packs/python
PACK_COUNT=0
for lang_dir in */; do
    lang="${lang_dir%/}"
    if [ -f "${lang_dir}pyproject.toml" ]; then
        print_info "Building language pack: ${lang}..."
        cd "${lang_dir}"
        rm -rf dist/
        uv build -o dist
        cp dist/*.whl "${RELEASE_DIR}/"
        cd ..
        PACK_COUNT=$((PACK_COUNT + 1))
    fi
done
print_success "Built ${PACK_COUNT} language packs"

# Build VS Code extension
print_info "Building VS Code extension..."
cd ../../../vs-code
npm run package  # Creates .vsix file

# Validate telemetry connection string was embedded in production build
if grep -qi "InstrumentationKey" out/extension.js 2>/dev/null || grep -qi "ingestionendpoint" out/extension.js 2>/dev/null; then
    print_success "Telemetry connection string embedded in build"
else
    echo -e "${YELLOW}⚠${NC}  WARNING: Telemetry connection string NOT found in build output"
    echo "   Set LEGESHER_TELEMETRY_CONNECTION_STRING in .env or environment"
    echo "   Telemetry will be disabled in this build"
fi

# Validate telemetry module is bundled (not externalized)
if grep -q 'require.*@vscode/extension-telemetry' out/extension.js 2>/dev/null; then
    print_error "ERROR: @vscode/extension-telemetry is externalized - it must be bundled!"
    echo "   Check esbuild.js external array - remove @vscode/extension-telemetry"
    exit 1
fi

cp *.vsix "${RELEASE_DIR}/"
print_success "VS Code extension built and copied"

# Return to root
cd ../..

echo ""
echo "📦 Built packages:"
echo ""
ls -lh "${RELEASE_DIR}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📂 Release artifacts saved to:"
echo "   ${RELEASE_DIR}"
echo ""
echo "📋 Next steps:"
echo "   1. cd ${PREVIEW_REPO}"
echo "   2. Update install-preview.sh to reference v${VERSION}"
echo "   3. Test installation with: ./install-preview.sh"
echo "   4. Commit and push to preview repo"
echo ""
