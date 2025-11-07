#!/bin/bash
set -e

TARGET=$1
LANGUAGE=$2
VALID_TARGETS=("python")
VALID_LANGUAGES=("es" "ar")

if [ -z "$TARGET" ] || [ -z "$LANGUAGE" ]; then
    echo "Usage: ./release-language-pack.sh <target> <language>"
    echo ""
    echo "Examples:"
    echo "  ./release-language-pack.sh python es    # Release Spanish Python pack"
    echo "  ./release-language-pack.sh python ar    # Release Arabic Python pack"
    echo ""
    echo "Valid targets: ${VALID_TARGETS[*]}"
    echo "Valid languages: ${VALID_LANGUAGES[*]}"
    exit 1
fi

# Validate target argument
if [[ ! " ${VALID_TARGETS[@]} " =~ " ${TARGET} " ]]; then
    echo "❌ Error: Invalid target '$TARGET'"
    echo "Valid targets: ${VALID_TARGETS[*]}"
    exit 1
fi

# Validate language argument
if [[ ! " ${VALID_LANGUAGES[@]} " =~ " ${LANGUAGE} " ]]; then
    echo "❌ Error: Invalid language '$LANGUAGE'"
    echo "Valid languages: ${VALID_LANGUAGES[*]}"
    exit 1
fi

PACKAGE="i18n-${TARGET}-${LANGUAGE}"
echo "🚀 Releasing legesher-$PACKAGE..."

# Ensure on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch to release"
    exit 1
fi

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory must be clean"
    exit 1
fi

# Navigate to package directory
cd "libs/$PACKAGE"

# Run semantic-release for this package
echo "📦 Running python-semantic-release..."
if ! uv run semantic-release version; then
    echo "ℹ️  No release needed (no releasable commits for $PACKAGE)"
    exit 0
fi

echo "✅ Version bumped successfully"

# Return to repo root
cd ../..

# Push to remote if configured
if git remote get-url origin &>/dev/null; then
    echo "🚀 Pushing to remote..."
    if ! git push --follow-tags; then
        echo "⚠️  Warning: Push failed. You may need to push manually:"
        echo "    git push --follow-tags"
    else
        echo "✅ Pushed to remote successfully"
    fi
else
    echo "ℹ️  No remote configured, skipping push"
    echo "    To push later: git push --follow-tags"
fi

echo "🎉 legesher-$PACKAGE release complete!"
