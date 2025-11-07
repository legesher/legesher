#!/bin/bash
set -e

PACKAGE=$1
VALID_APPS=("vs-code" "pride")

if [ -z "$PACKAGE" ]; then
    echo "Usage: ./release-app.sh <vs-code|pride>"
    exit 1
fi

# Validate package argument
if [[ ! " ${VALID_APPS[@]} " =~ " ${PACKAGE} " ]]; then
    echo "❌ Error: Invalid package '$PACKAGE'"
    echo "Valid packages: ${VALID_APPS[*]}"
    exit 1
fi

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
