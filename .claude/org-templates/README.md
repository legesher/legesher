# Claude Code templates

This directory holds a starting point for Claude Code configuration in other
projects.

## Contents

- `settings.json.template`: hooks and permissions you can copy into another
  project as `.claude/settings.json`, then edit for that project.

The template is not kept in step with this repository's own
`.claude/settings.json`, which is the maintained reference. The template has
no push guard, and its YAML hook matches no language-pack path and breaks on a
file path that contains a quote. Compare it with `settings.json` before you
copy it.

## How to use

```bash
cp .claude/org-templates/settings.json.template your-project/.claude/settings.json
```

Then remove what the other project does not need. Personal settings go in
`.claude/settings.local.json`, which should be listed in that project's
`.gitignore`. Settings for all your projects go in `~/.claude/settings.json`.

To improve the template, open a pull request in this repository.
