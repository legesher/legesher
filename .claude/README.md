# Claude Code configuration

This directory holds the project configuration for
[Claude Code](https://docs.claude.com/en/docs/claude-code/overview). Claude
Code loads it when you open the repository. You do not need Claude Code to
contribute. If you use it, these files give you formatting hooks, a guard
against pushing to `main`, and a few specialized agents.

For first-time setup, read [SETUP-GUIDE.md](SETUP-GUIDE.md). For project
rules that apply to all work in this repository, read
[CLAUDE.md](../CLAUDE.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

## Directory layout

```text
.claude/
├── README.md                     # This file
├── SETUP-GUIDE.md                # Setup steps and troubleshooting
├── settings.json                 # Project hooks and permissions (committed)
├── hooks/
│   └── block-push-to-main.sh     # Blocks git push to main or master
├── hooks-examples.md             # Optional hook examples, not active
├── agents/                       # Subagent definitions
│   ├── code-quality-reviewer.md
│   ├── codebase-explorer.md
│   ├── doc-writer.md
│   ├── security-reviewer.md
│   └── test-engineer.md
└── org-templates/                # Starting point for other projects
    ├── README.md
    └── settings.json.template
```

You can also create `settings.local.json` here for personal settings. Git
ignores it. See [Personal overrides](#personal-overrides).

Team workflow skills are maintained outside this repository. You do not need
them to contribute.

## Agents

An agent is a subagent with its own context window and its own tool list.
Claude Code can choose an agent by its description, or you can ask for one by
name, for example: "use the security-reviewer agent on this diff".

| Agent                   | Tools                               | Use it to                                                                                                                              |
| ----------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `codebase-explorer`     | Read, Glob, Grep, Bash              | Map an unfamiliar area: architecture, patterns, dependencies, prior art. It is read-only and does not edit files.                      |
| `code-quality-reviewer` | Read, Grep, Glob, Bash              | Review changed code for reuse, quality, performance and fit with project patterns. It suggests changes and does not apply them.        |
| `security-reviewer`     | Read, Grep, Glob, Bash              | Check code for input validation gaps, injection (SQL, command, path traversal), data exposure and risky dependencies.                  |
| `test-engineer`         | Read, Edit, Write, Bash, Grep, Glob | Write tests with a test-first approach (pytest, and Vitest for TypeScript). It follows the testing contract written in the agent file. |
| `doc-writer`            | Read, Write, Edit, Glob, Grep       | Write READMEs, docstrings, tutorials, how-to guides and architecture decision records.                                                 |

The files in `agents/` are the canonical copies. Maintainers who want the
agents in every repository on their machine keep symlinks in
`~/.claude/agents/` that point to these files. Do not keep edited copies
there, because they drift from the tracked files.

To change an agent, edit its file here and open a pull request. Each file
starts with YAML frontmatter (`name`, `description`, `tools`).

## Hooks

`settings.json` defines four hooks. A hook is a shell command that Claude
Code runs before or after it uses a tool.

| When                            | What it does                                                                          |
| ------------------------------- | ------------------------------------------------------------------------------------- |
| After Claude edits a `.py` file | Runs `uv run ruff format` and then `uv run ruff check --fix` on that file.            |
| After Claude edits a `.md` file | Runs `npx prettier --write` on that file.                                             |
| Before each Bash command        | Appends the command with a timestamp to `~/.claude/bash_history.log` on your machine. |
| Before each Bash command        | Runs `hooks/block-push-to-main.sh`.                                                   |

The formatting hooks only act on files that Claude edits. They do not touch
files you edit yourself.

### The push guard

`hooks/block-push-to-main.sh` reads the command from the hook input with
`jq`. It looks only at commands that start with `git push`. It blocks the
command (exit code 2, with a message) when:

- the command names `main` or `master` as a branch, for example
  `git push origin main`;
- the command uses a refspec to `main` or `master`, for example
  `git push origin HEAD:main`;
- the command has no remote and branch pair, for example `git push` or
  `git push --force`, and the current branch is `main` or `master`.

It allows `--dry-run` pushes and pushes of other branches, including branch
names that only contain the word "main". It only checks commands that Claude
runs. It does not affect pushes from your own terminal.

The guard is a convenience, not a protection. It matches the command text, so
some pushes to `main` get through: `git push origin HEAD` while on `main`,
`git push origin refs/heads/main`, and any push behind a prefix such as
`cd dir &&`. It also blocks nothing when `jq` is missing or the hook path does
not resolve (see the setup guide's troubleshooting). Only branch protection on
GitHub can stop a push to `main`.

### Permissions

`permissions.allow` pre-approves three tools from a Linear MCP server. They
have no effect unless you have connected that server yourself.

### Personal overrides

Claude Code reads `.claude/settings.local.json` after `settings.json`. Use it
for personal settings. Git ignores this file.

Claude Code runs the hooks from every settings file it loads. An empty
`hooks` list in `settings.local.json` does not remove the project hooks. To
turn off all hooks for yourself, add this to `settings.local.json`:

```json
{
  "disableAllHooks": true
}
```

This also turns off the push guard. There is no setting that turns off one
project hook and keeps the others. If one hook causes trouble, see the
troubleshooting section in [SETUP-GUIDE.md](SETUP-GUIDE.md#troubleshooting)
first.

## More

- [hooks-examples.md](hooks-examples.md): optional hook examples (run tests,
  back up files, validate YAML). None of them are active. Copy one into your
  `settings.local.json` if you want it.
- [org-templates/](org-templates/README.md): a `settings.json` template you
  can copy into another project as a starting point.
- [Claude Code hooks documentation](https://docs.claude.com/en/docs/claude-code/hooks)
- [Claude Code subagents documentation](https://docs.claude.com/en/docs/claude-code/sub-agents)
