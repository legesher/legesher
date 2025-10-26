# Claude Code Hooks Examples

<!--
SOURCES:
- Claude Code Hooks Guide: https://docs.claude.com/en/docs/claude-code/hooks-guide
- GitButler hooks integration
- Automation best practices
-->

This file contains example hooks configurations for automating common development workflows.

## What Are Hooks?

Hooks are shell commands that execute automatically at various points in Claude Code's lifecycle:

- **PreToolUse**: Run BEFORE a tool executes
- **PostToolUse**: Run AFTER a tool executes
- **Stop**: Run when conversation ends

## Configuration Location

Hooks are configured in JSON files:

- **User settings**: `~/.claude/settings.json` (applies to all projects)
- **Project settings**: `.claude/settings.json` (checked into git, shared with team)
- **Local overrides**: `.claude/settings.local.json` (not committed, personal preferences)

## Hook Configuration Format

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "What this hook does",
        "matcher": "ToolName|OtherTool",  // Which tools trigger this
        "hooks": [
          {
            "type": "command",
            "command": "shell command to run"
          }
        ]
      }
    ]
  }
}
```

## Example Hooks

### 1. Auto-Format Code (PostToolUse)

Automatically format files after Claude edits them.

**Python (Black + Ruff)**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Auto-format Python files with Black and Ruff",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.py$'; then uv run black \"$file_path\" && uv run ruff check --fix \"$file_path\"; fi; }"
          }
        ]
      }
    ]
  }
}
```

**JavaScript/TypeScript (Prettier + ESLint)**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Auto-format JS/TS files with Prettier and ESLint",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE '\\.(js|jsx|ts|tsx)$'; then npx prettier --write \"$file_path\" && npx eslint --fix \"$file_path\"; fi; }"
          }
        ]
      }
    ]
  }
}
```

**Markdown (Prettier)**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Auto-format Markdown files with Prettier",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.md$'; then npx prettier --write \"$file_path\"; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 2. Run Tests After Changes (PostToolUse)

Automatically run tests when test files or implementation files are modified.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Run tests when Python files change",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.py$'; then package=$(echo \"$file_path\" | grep -oP 'libs/\\K[^/]+'); if [ -n \"$package\" ]; then echo \"Running tests for $package...\"; cd \"libs/$package\" && uv run pytest -x 2>&1 | tail -20; fi; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 3. Log Commands for Debugging (PreToolUse)

Log all bash commands before they execute, useful for debugging and auditing.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "Log bash commands with timestamps",
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input | \"\\(.command) # \\(.description // \\\"No description\\\")\"' | { read cmd; echo \"[$(date '+%Y-%m-%d %H:%M:%S')] $cmd\" >> ~/.claude/bash_history.log; }"
          }
        ]
      }
    ]
  }
}
```

View the log:

```bash
tail -f ~/.claude/bash_history.log
```

### 4. Prevent Accidental Production Changes (PreToolUse)

Block edits to production configuration files.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "Block edits to production config files",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE '(production\\.yml|prod\\.env|\\.env\\.production)$'; then echo '{\"decision\": \"block\", \"reason\": \"Cannot modify production config files. Edit staging first.\"}'; exit 1; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 5. Require Explanation for Sensitive Files (PreToolUse)

Ask for justification before modifying critical files.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "Require explanation for security-sensitive files",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE '(auth|security|permission)'; then echo 'Modifying security-sensitive file. Ensure changes are reviewed.' >&2; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 6. Update Package Version on Changes (PostToolUse)

Automatically bump version when code changes (for libraries).

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Suggest version bump when code changes",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE 'libs/[^/]+/legesher_[^/]+/.*\\.py$'; then echo 'Reminder: Update version in pyproject.toml if this is a breaking change.' >&2; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 7. Backup Files Before Editing (PreToolUse)

Create backup copies before Claude modifies important files.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "Backup important files before editing",
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE '\\.(py|js|ts|yml)$'; then backup_dir=\"$HOME/.claude/backups/$(date +%Y%m%d)\"; mkdir -p \"$backup_dir\"; cp \"$file_path\" \"$backup_dir/$(basename \"$file_path\").$(date +%H%M%S).bak\" 2>/dev/null || true; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 8. Notify on File Changes (PostToolUse)

Send notifications when certain files are modified.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Notify when critical files change",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE '(CLAUDE\\.md|pyproject\\.toml)$'; then osascript -e 'display notification \"Claude modified critical file: '\"$file_path\"'\" with title \"Claude Code\"' 2>/dev/null || notify-send \"Claude Code\" \"Modified: $file_path\" 2>/dev/null || true; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 9. Check Code Coverage After Tests (PostToolUse)

Automatically check coverage when tests are run.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Check code coverage after test commands",
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.command' | { read cmd; if echo \"$cmd\" | grep -q 'pytest'; then echo 'Running coverage report...'; package=$(echo \"$cmd\" | grep -oP 'libs/\\K[^/]+'); if [ -n \"$package\" ]; then cd \"libs/$package\" && uv run pytest --cov --cov-report=term-missing | tail -30; fi; fi; }"
          }
        ]
      }
    ]
  }
}
```

### 10. GitButler Integration

Automatically organize changes into virtual branches (requires GitButler).

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "GitButler pre-tool hook",
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "which gitbutler >/dev/null 2>&1 && gitbutler claude pre-tool || true"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "description": "GitButler post-tool hook",
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "which gitbutler >/dev/null 2>&1 && gitbutler claude post-tool || true"
          }
        ]
      }
    ],
    "Stop": [
      {
        "description": "GitButler session end hook",
        "hooks": [
          {
            "type": "command",
            "command": "which gitbutler >/dev/null 2>&1 && gitbutler claude stop || true"
          }
        ]
      }
    ]
  }
}
```

## Advanced Hook Patterns

### Conditional Execution Based on File Path

```bash
jq -r '.tool_input.file_path' | {
  read file_path

  # Only run for specific directories
  if echo "$file_path" | grep -q '^libs/core/'; then
    # Core package logic
    echo "Modifying core package"
  elif echo "$file_path" | grep -q '^libs/i18n/'; then
    # i18n package logic
    echo "Modifying i18n package"
  fi
}
```

### Extract Tool Input Fields

Available fields vary by tool:

**Edit/Write tools**:

```bash
# Get file path
jq -r '.tool_input.file_path'

# Get old content (Edit only)
jq -r '.tool_input.old_string'

# Get new content
jq -r '.tool_input.new_string'
```

**Bash tool**:

```bash
# Get command
jq -r '.tool_input.command'

# Get description
jq -r '.tool_input.description // "No description"'
```

### Return Structured Responses

Hooks can return JSON to control Claude Code behavior:

```json
{
  "decision": "approve" | "block",
  "reason": "Explanation shown to user",
  "continue": true | false,
  "suppressOutput": true | false
}
```

Example:

```bash
if [ some_condition ]; then
  echo '{"decision": "block", "reason": "Tests must pass before committing"}'
  exit 1
fi
```

## Best Practices

### 1. Make Hooks Fast

Hooks run synchronously, so keep them fast:

- ❌ `npm install` (slow)
- ✅ `npx prettier --write file` (fast)

### 2. Handle Failures Gracefully

Use `|| true` to prevent hooks from blocking Claude:

```bash
npx prettier --write "$file_path" || true
```

### 3. Silent Unless Important

Redirect output to /dev/null for routine operations:

```bash
ruff check --fix "$file_path" 2>/dev/null || true
```

Show output only for important events:

```bash
echo "Warning: Modifying security-sensitive file" >&2
```

### 4. Test Hooks Manually

Test hook commands before adding to settings:

```bash
# Simulate hook input
echo '{"tool_input": {"file_path": "test.py"}}' | jq -r '.tool_input.file_path'
```

### 5. Use Descriptive Names

```json
{
  "description": "Auto-format Python with Black (max line 88)"
  // Not just: "Format code"
}
```

### 6. Document Hook Purpose

Add comments explaining why the hook exists:

```json
{
  "// Purpose": "Automatically format code to maintain consistent style across team",
  "description": "Auto-format Python files with Black",
  ...
}
```

## Debugging Hooks

### Enable Hook Logging

Check Claude Code logs to see hook execution:

```bash
# macOS
tail -f ~/Library/Logs/Claude/main.log

# Linux
tail -f ~/.config/Claude/logs/main.log
```

### Test Hook Commands

Run hook commands manually with sample input:

```bash
# Test a PostToolUse hook for Edit
echo '{"tool_input": {"file_path": "/path/to/test.py", "old_string": "old", "new_string": "new"}}' | jq -r '.tool_input.file_path' | {
  read file_path
  echo "Would format: $file_path"
}
```

### Common Issues

**Hook doesn't run**:

- Check matcher (tool name must match exactly)
- Verify JSON syntax (use JSONLint)
- Check file paths in script

**Hook blocks Claude**:

- Command is taking too long
- Command is failing without `|| true`
- Output is too verbose (redirect to /dev/null)

**Hook runs for wrong tools**:

- Matcher too broad (`matcher: ".*"`)
- Need more specific tool names

## Legesher-Specific Hooks

### Auto-run tests when i18n changes

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Run i18n tests when language packs change",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q 'libs/i18n/languages/'; then cd libs/i18n && uv run pytest tests/ -x; fi; }"
          }
        ]
      }
    ]
  }
}
```

### Validate language pack YAML

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Validate language pack YAML after editing",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE 'languages/.*\\.yml$'; then python -c \"import yaml; yaml.safe_load(open('$file_path'))\" && echo 'YAML valid' || echo 'YAML invalid!'; fi; }"
          }
        ]
      }
    ]
  }
}
```

### Update CHANGELOG reminder

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Remind to update CHANGELOG for user-facing changes",
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -qE 'libs/[^/]+/legesher_[^/]+/'; then echo 'Reminder: Update CHANGELOG.md if this is a user-facing change' >&2; fi; }"
          }
        ]
      }
    ]
  }
}
```

## Resources

- [Claude Code Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [GitButler Hooks Integration](https://docs.gitbutler.com/features/ai-integration/claude-code-hooks)
- [jq Manual](https://jqlang.github.io/jq/manual/)

## Tips

- Start with simple hooks and iterate
- Test hooks manually before adding to settings
- Use project settings for team workflows
- Use local settings for personal preferences
- Keep hooks fast and failure-tolerant
- Document why hooks exist, not just what they do

Remember: Hooks should enhance your workflow, not slow it down. If a hook is annoying, remove or modify it!
