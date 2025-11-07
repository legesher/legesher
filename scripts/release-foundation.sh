#!/bin/bash
set -e

echo "🚀 Releasing Foundation Suite (core, i18n, legesher)..."

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

# Run semantic-release for foundation (workspace root config)
echo "📦 Running python-semantic-release..."
if ! uv run semantic-release version; then
    echo "ℹ️  No release needed (no releasable commits)"
    exit 0
fi

echo "✅ Version bumped successfully"

# Sync uv.lock
echo "🔒 Syncing uv.lock..."
if ! uv sync; then
    echo "❌ Error: Failed to sync uv.lock"
    exit 1
fi

# Commit lock file changes if needed
if [ -n "$(git status --porcelain uv.lock)" ]; then
    git add uv.lock
    git commit -m "chore: update uv.lock after version bump"
fi

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

echo "🎉 Foundation release complete!"
