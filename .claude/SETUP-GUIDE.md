# Claude Code setup

This guide is for contributors who want to use Claude Code in this
repository. Claude Code is optional. For what each file in `.claude/` does,
see [README.md](README.md).

## 1. Install the tools

1. Install Claude Code. Follow the
   [official setup guide](https://docs.claude.com/en/docs/claude-code/setup).
2. Install the tools that the hooks call:
   - [uv](https://docs.astral.sh/uv/). The Python hook runs ruff through
     `uv run`.
   - [Node.js](https://nodejs.org/), which includes `npx`. The Markdown hook
     runs `npx prettier`. If prettier is not installed, `npx` downloads it.
   - [jq](https://jqlang.org/). Every hook uses `jq` to read its input.
3. From the repository root, install the workspace (`uv sync --all-extras`).
   This also installs ruff:

   ```bash
   make install
   ```

## 2. Open the repository

Start Claude Code from the repository root:

```bash
claude
```

Claude Code then loads these files automatically:

- `CLAUDE.md` at the repository root: project rules and commands.
- `.claude/settings.json`: the hooks and permissions.
- `.claude/agents/`: the five agents.

The first time you open the folder, Claude Code asks whether you trust it.
Accept to load the project settings.

## 3. Personal settings (optional)

Put personal settings in `.claude/settings.local.json`. The repository
`.gitignore` lists this file, so Git does not commit it. Claude Code reads it
in addition to `settings.json`. It does not replace the project hooks. The
README explains how to
[turn hooks off](README.md#personal-overrides).

## Troubleshooting

If a hook does not run, check these points:

- **jq is missing.** Run `jq --version`. Without jq, no hook can read its
  input. The push guard then fails and does not block anything.
- **You started Claude Code in a subdirectory.** The push guard is called
  with the relative path `bash .claude/hooks/block-push-to-main.sh`. Start
  Claude Code from the repository root.
- **ruff does not format.** Run `uv run ruff --version` from the repository
  root. If it fails, run `make install` again. The hook hides ruff
  errors, so a failure is silent.
- **prettier does not format.** Run `npx prettier --version`. The hook hides
  prettier errors.
- **Hooks are turned off.** Check `.claude/settings.local.json` and
  `~/.claude/settings.json` for `"disableAllHooks": true`.
- **The settings file is not valid JSON.** Run
  `jq . .claude/settings.json` and `jq . .claude/settings.local.json`.
- **You want to see hook output.** Run `claude --debug`. It prints each hook
  that runs and its result. Inside a session, the `/hooks` command lists the
  hooks that Claude Code has loaded.
