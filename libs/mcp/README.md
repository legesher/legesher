# legesher-mcp

The Legesher [Model Context Protocol](https://modelcontextprotocol.io) server:
the engine's translation capability inside every MCP-capable client — Claude,
IDE assistants, agent frameworks — as five coarse, task-shaped tools.

**Free forever. Apache-2.0. No telemetry.** This server runs entirely against
the locally installed Legesher engine: it makes no network calls, requires no
account, and emits nothing. What it does is defined by this open package and
nothing else.

## Tools

| Tool | What it does |
| --- | --- |
| `translate_to_native` | Translate Python source into your natural language. Accepts complete files and fragments alike — no separate snippet mode. |
| `translate_to_source` | Translate native-language code back to English-keyword Python — the form the interpreter, the toolchain, and upstream collaborators use. |
| `explain_in_language` | Return the *engine facts* an assistant needs to explain code in your language: construct-by-construct keyword mappings, a static validation result, and (optionally) the translated source. The model writes the prose; the tool never does. |
| `lookup_keyword_mapping` | Quick-reference lookup: how do specific terms (or the full mapping) render in a language. |
| `map_existing_codebase` | The legibility report: given a set of files, what would translating this codebase into a language look like — per-file coverage, unmapped constructs, and optionally the translated files. |

Notes on shape, straight from the design:

- Translation X→Y **pivots through English** (packs are authored against
  English). The engine has no direct X→Y path; when the pivot is taken the
  result says so via `pivoted: true` rather than failing.
- Validation is **static only** — `compile()`, never `exec()` — submitted
  code is parsed, never executed.
- Error results carry a machine code (`unsupported_language`,
  `language_pack_not_found`, `invalid_source`) and a generic message: no
  stack traces, no filesystem paths, no echoed source.

## Resources

| URI | Contents |
| --- | --- |
| `legesher://languages` | The language catalog with pack availability. |
| `legesher://languages/{lang}/terms` | The full term dictionary (keywords, builtins, exceptions, reserved words) for one language. |

## Prompts

- `explain-in` — scaffolds "explain the selected code in {language}",
  steering the model to `explain_in_language` first and keeping engine facts
  distinct from narration.
- `translate-review` — walks a source/translated pair: translate, validate,
  then summarize what changed and what did not map.
- `legibility-report` — drives `map_existing_codebase` over pasted files and
  renders the coverage report as a stakeholder-readable summary.

## Install

The server needs the Legesher engine and at least one language pack:

```bash
# The server (pulls legesher-core + legesher-i18n)
uvx legesher-mcp

# Language packs are separate packages — install the ones you use, e.g.:
pip install legesher-i18n-python-es legesher-i18n-python-ar
```

Inside the monorepo workspace all 51 packs are already installed:

```bash
uv run legesher-mcp
```

## Client configuration

### Claude Desktop

`claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "legesher": {
      "command": "uvx",
      "args": ["legesher-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add legesher -- uvx legesher-mcp
```

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "legesher": {
      "command": "uvx",
      "args": ["legesher-mcp"]
    }
  }
}
```

### Zed

`settings.json` → `context_servers`:

```json
{
  "context_servers": {
    "legesher": {
      "command": {
        "path": "uvx",
        "args": ["legesher-mcp"]
      }
    }
  }
}
```

## Privacy

- **No telemetry.** The stdio server emits no events, pings, or metrics of
  any kind.
- **No network.** Every tool call is served by the local engine.
- **No persistence.** Submitted source is processed in memory; file *paths*
  passed to `map_existing_codebase` are report labels — echoed back to you,
  never logged, never used to touch the filesystem.

## Development

```bash
cd libs/mcp
uv run pytest          # tests (exercise every tool through the MCP layer)
uv run ruff check .    # lint
uv run mypy legesher_mcp  # types
```

## License

Apache-2.0. See [LICENSE](LICENSE).
