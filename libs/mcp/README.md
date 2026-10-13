# legesher-mcp

<!-- mcp-name: io.github.legesher/legesher-mcp -->

The Legesher [Model Context Protocol](https://modelcontextprotocol.io) server:
the engine's translation capability inside every MCP-capable client — Claude,
IDE assistants, agent frameworks — as six coarse, task-shaped tools.

**Using the MCP server is free forever (Apache-2.0).** The local server runs
entirely against the locally installed Legesher engine: it needs no account
and sends no telemetry. Some capabilities require a Legesher account on the
hosted instance. What the server does is defined by this open package and
nothing else.

## Tools

| Tool | What it does |
| --- | --- |
| `translate_to_native` | Translate Python source into your natural language. Accepts complete files and fragments alike — no separate snippet mode. |
| `translate_to_source` | Translate native-language code back to English-keyword Python — the form the interpreter, the toolchain, and upstream collaborators use. |
| `explain_in_language` | Return the *engine facts* an assistant needs to explain code in your language: construct-by-construct keyword mappings, a static validation result, and (optionally) the translated source. The model writes the prose; the tool never does. |
| `lookup_keyword_mapping` | Quick-reference lookup: how do specific terms (or the full mapping) render in a language. |
| `map_existing_codebase` | The legibility report: given a set of files, what would translating this codebase into a language look like — per-file coverage, unmapped constructs, and optionally the translated files. |
| `validate_identifier_translations` | Check proposed identifier translations before recording them: malformed identifiers, unsafe text, names the pack has reserved, drift (one concept, two terms) and collision (two concepts, one term) — against both your existing glossary and the rest of the batch. Comparison is NFKC+casefold, so case variants and decomposed forms count as the same term. Returns the conflict-free subset, NFC-normalized and ready to record. |

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
| `legesher://languages/{lang}/terms` | The full term dictionary (keywords, builtins, exceptions, reserved words) for one language, at the default Python version. |
| `legesher://languages/{lang}/terms/{python_version}` | The same dictionary pinned to a Python version, for callers on a grammar other than the default. |

## Prompts

- `explain-in` — scaffolds "explain the selected code in {language}",
  steering the model to `explain_in_language` first and keeping engine facts
  distinct from narration.
- `translate-review` — walks a source/translated pair: translate, validate,
  then summarize what changed and what did not map.
- `legibility-report` — drives `map_existing_codebase` over pasted files and
  renders the coverage report as a stakeholder-readable summary.

## Install

The server needs the Legesher engine. Every language pack ships inside
`legesher-i18n`, so nothing else is installed:

```bash
# The server (pulls legesher-core and legesher-i18n, packs included)
uvx legesher-mcp
```

Inside the monorepo workspace all 51 packs are already installed:

```bash
uv run legesher-mcp
```

The server is quiet by default (log level WARNING). For troubleshooting,
set `LEGESHER_MCP_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`,
`CRITICAL`); unrecognized values fall back to the quiet default. GUI
clients do not run your shell, so the variable has to go in the client's
own config — every block below shows where.

## Client configuration

### Claude Desktop

`claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "legesher": {
      "command": "uvx",
      "args": ["legesher-mcp"],
      "env": { "LEGESHER_MCP_LOG_LEVEL": "DEBUG" }
    }
  }
}
```

### Claude Code

```bash
claude mcp add legesher -- uvx legesher-mcp

# with troubleshooting logs
claude mcp add legesher --env LEGESHER_MCP_LOG_LEVEL=DEBUG -- uvx legesher-mcp
```

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "legesher": {
      "command": "uvx",
      "args": ["legesher-mcp"],
      "env": { "LEGESHER_MCP_LOG_LEVEL": "DEBUG" }
    }
  }
}
```

### VS Code

`.vscode/mcp.json` (workspace) or the user-level `mcp.json` (Command
Palette: *MCP: Open User Configuration*):

```json
{
  "servers": {
    "legesher": {
      "type": "stdio",
      "command": "uvx",
      "args": ["legesher-mcp"],
      "env": { "LEGESHER_MCP_LOG_LEVEL": "DEBUG" }
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
        "args": ["legesher-mcp"],
        "env": { "LEGESHER_MCP_LOG_LEVEL": "DEBUG" }
      }
    }
  }
}
```

The `env` block is optional in every case — drop it to keep the quiet
default.

## Serving over HTTP (self-host / single-user)

stdio is the default and what every client config above spawns. The same
server also speaks the MCP streamable HTTP transport, for running it as a
long-lived local service or on a machine you control:

```bash
legesher-mcp --transport streamable-http                # 127.0.0.1:8000/mcp
legesher-mcp --transport streamable-http --port 9000
legesher-mcp --transport streamable-http --host 192.0.2.7
```

The posture, deliberately:

- **Loopback by default, never a wildcard.** `--host` defaults to
  `127.0.0.1`, and wildcard binds (`0.0.0.0`, `::`) are refused: this
  entry ships **no authentication**, so it binds exactly one interface
  you name. To serve beyond a machine you trust end to end, put your own
  auth in front (below).
- **Stateless, plain JSON.** Every request is self-contained — no
  server-held session — and responses are `application/json`, not SSE.
- **`Origin` validated when present.** A browser page from another
  origin (the DNS-rebinding vector) is rejected with 403; the allowlist
  derives from the bound interface. MCP clients that send no `Origin`
  header are unaffected.

Embedding instead of running: `legesher_mcp.server.create_server()` builds
the complete server from a `Backend` and an entitlement gate, and
`create_http_app()` returns it as an ASGI app to mount behind your own
middleware (TLS, auth, request context for the gate — see
`legesher_mcp.gate.request_context`). The gate is **default-open**: no
deployment code here installs one, gated tools always stay listed, and an
unentitled call answers with an actionable message rather than an opaque
failure. `validate_identifier_translations` is permanently free by
construction.

## Making agent sessions stay localized

The server is the deterministic half; two shipped artifacts carry the
policy and playbook half for agent sessions:

- **`templates/AGENTS-template.md`** — the language-policy declaration.
  Copy it into a repository root as `AGENTS.md`, fill in the declared
  language, and every `AGENTS.md`-reading agent (Codex, Cursor, Claude
  Code, Antigravity, Windsurf) picks up the same eight rules: write
  natively, never hand-translate keywords, one-concept-one-term naming
  via the project glossary, and the byte-identical round-trip guarantee.
  The file is the *declaration*; long sessions evict rules files from
  context, which is exactly why the deterministic tools — not the file —
  are the *guarantee*.
- **`skills/legesher-localized-code/`** — the stable-knowledge skill
  ([Agent Skills](https://agentskills.io) format: portable across Claude
  Code, Claude apps, and the API). It teaches the mental model
  (run form ↔ native, deterministic vs fuzzy layers), which tool to call
  when, the write → round-trip → validate workflow, and the naming
  discipline. Claude Code: copy the directory into your project's
  `.claude/skills/`. Skills carry the *stable* playbook; the MCP server
  stays the live surface — that split is deliberate.

## Privacy

- **No telemetry.** The stdio server emits no events, pings, or metrics of
  any kind.
- **No network.** Every tool call is served by the local engine.
- **No persistence.** Submitted source is processed in memory; file *paths*
  passed to `map_existing_codebase` are report labels — echoed back to you,
  never logged, never used to touch the filesystem. This is why
  `validate_identifier_translations` takes your glossary as *content* and
  hands back the accepted entries rather than saving them: recording is
  yours to do, whether that is `.legesher/identifier_map.json` in your repo
  or the `legesher` CLI, which already maintains that file. A durable
  glossary that outlives the session and is shared across repos and
  teammates is a system of record, and belongs behind the hosted API — not
  in a local subprocess.
- **Declared, not just claimed.** All six tools carry MCP annotations
  saying so — `readOnlyHint: true`, `idempotentHint: true`,
  `destructiveHint: false`, `openWorldHint: false`. Clients that read the
  hints (Claude Code among them) can reduce or skip approval prompts,
  because nothing here writes a file, executes submitted code (validation
  is `compile()` only), or opens a socket. A surface-lock test asserts the
  annotations, so a future tool that *does* any of those has to change them
  deliberately.

## Development

```bash
cd libs/mcp
uv run pytest             # the per-commit suite (every tool, through MCP)
uv run pytest -m scheduled  # release-tier: all-packs sweep + wheel spawn
uv run ruff check .       # lint
uv run mypy legesher_mcp  # types
```

Two test tiers. The default run exercises every tool through a real MCP
client session and stays fast. The `scheduled` tier is excluded from it and
run before a release:

- **All-packs round-trip sweep** — the byte-identical guarantee across every
  installed pack and the whole construct corpus (the per-commit run samples
  three packs). Known engine/pack failures are listed as strict xfails in
  `tests/test_roundtrip_sweep.py`, so a fix announces itself.
- **Clean-environment spawn** — builds the wheels, installs them into a
  fresh virtualenv in an empty directory, and drives a stdio session with a
  stripped environment. It is the only test that exercises the artifact the
  way a host actually starts it: outside the workspace, with no
  `PYTHONPATH` and no repo checkout.

  **It gates the release.** `release-mcp.yml` runs `make test-mcp-scheduled`
  before the version step, so a failure means no version bump, no tag, and
  no GitHub release — nothing to un-publish. Run it locally with
  `make test-mcp-scheduled` before you expect a release to go out.

  Scope, so the guarantee isn't overread: it gates *cutting a version*. The
  push to a package index is the `mcp` target of `publish-pypi.yml`, which is
  dispatch-only and runs after `foundation` has reached the same index
  (CORE-626).

## Versioning

`legesher-mcp` releases on its own train, independent of the foundation
suite: tags are `mcp-v{version}`, cut by `release-mcp.yml` when something
under `libs/mcp/` lands on `main`. The version in `pyproject.toml` is the
single source — `__version__` reads it back through `importlib.metadata`, so
the `initialize` handshake cannot report a number the wheel does not have.

Pre-1.0, a breaking change bumps the minor (`0.1.0` → `0.2.0`);
`major_on_zero` is off, so reaching 1.0.0 is a deliberate decision rather
than a side effect of one commit.

## Listings

`server.json` is the manifest the official MCP registry reads, and the
`mcp-name` comment at the top of this README is how that registry confirms
the PyPI package belongs to the listing. `docs/registry-listings.md` holds
the canonical listing copy and what each directory reads, so every listing
says the same thing. `tests/test_registry_manifest.py` pins the manifest to
this package's name, version and environment variables.

## License

Apache-2.0. See [LICENSE](LICENSE).
