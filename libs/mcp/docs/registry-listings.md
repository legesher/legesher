# Registry listings

The same server, listed everywhere people who build with agents look for
tools. This page holds the canonical listing copy and what each directory
reads, so every listing says the same thing and none of it is written on
submission day.

## Canonical copy

| Field | Value |
| --- | --- |
| Registry name | `io.github.legesher/legesher-mcp` |
| Display name | Legesher |
| Package | `legesher-mcp` on PyPI, run with `uvx legesher-mcp` |
| Tagline (100 characters or fewer) | Translate Python between English keywords and your language, with round-trip verification. |
| Categories | developer tools, code translation, localization, education |
| Keywords | legesher, mcp, model-context-protocol, python, translation, i18n, localization, multilingual, language-packs, round-trip (the `keywords` list in `pyproject.toml`) |
| License | Apache-2.0 |
| Homepage | <https://legesher.io> |
| Source | <https://github.com/legesher/legesher>, folder `libs/mcp` |
| Transport | stdio (local) |

**Short description.** Legesher lets people write and read Python in their
own language. This server puts the translation engine inside any MCP
client: translate a file into a language and back to the English-keyword
form the interpreter runs, prove the round trip is byte-for-byte, look up
how terms render, get the engine facts behind an explanation, check
identifier names before you record them, and report how legible an
existing codebase would be in a language. Six tools, three resources, three
prompts. Free forever, Apache-2.0. Every tool call runs locally against the
installed engine and your language packs.

**What makes it different.** Translation is pack-based and reviewed, not
model-guessed: a language pack is a reviewed dictionary, so the same code
translates the same way every time, and the engine can prove a translation
round-trips. The model does the fuzzy work (prose, identifiers,
explanations); the server supplies the deterministic layer underneath it.
Validation is static: submitted code is parsed, never executed.

**Install line.** `uvx legesher-mcp`. Every language pack ships inside
`legesher-i18n`; nothing else is installed. Client configuration blocks for
Claude Desktop, Claude Code, Cursor, VS Code and Zed are in the README.

Keep every listing to what this open package does.

## Metadata in the repository and the package

`README.md` and `pyproject.toml` ship in the package (the README is the
PyPI description). `server.json` and this page stay in the repository: the
registry reads `server.json` from the working directory at publish time.

The manifest names the repository by URL only. The registry's optional
`repository.id` (the forge's numeric id, `gh api repos/legesher/legesher
--jq .id`) is added at submission time, once the public repository exists,
because the id changes if the public repository is a fresh one.

| Artifact | Read by | Kept true by |
| --- | --- | --- |
| `server.json` | the official MCP registry | `tests/test_registry_manifest.py` |
| `mcp-name` comment at the top of `README.md` | the official registry's PyPI ownership check | the same test |
| `[project.urls]` in `pyproject.toml` | the PyPI project page | review |
| `keywords` and `classifiers` in `pyproject.toml` | PyPI search | review |
| Client configuration blocks in `README.md` | every directory that renders the README | review |

The manifest's `version` and the package entry's `version` must equal the
version in `pyproject.toml` at submission time. The test enforces it, so a
release that bumps `pyproject.toml` also bumps `server.json`.

## Directories

Preconditions for all of them: the repository is public and the package is
on PyPI at the version the manifest names.

| Directory | What it reads | How a listing happens |
| --- | --- | --- |
| Official MCP Registry (`registry.modelcontextprotocol.io`) | `server.json`; the `mcp-name` marker in the README published on PyPI | `mcp-publisher login github` as an Owner of the `legesher` GitHub organisation (membership alone is refused for the `io.github.legesher/*` namespace; a DNS-verified name under the project domain is the alternative), then `mcp-publisher publish` from `libs/mcp`. Re-publish on every version bump. |
| PyPI | `README.md`, `[project.urls]`, keywords, classifiers | Nothing beyond the package publish. |
| Glama (`glama.ai/mcp/servers`) | the public GitHub repository | Indexed automatically. To claim and edit the listing, add `glama.json` at the repository root (`$schema` `https://glama.ai/mcp/schemas/server.json`, `maintainers` as GitHub usernames; organisation repositories must use the file), then run the claim flow. Check on the day. |
| Smithery (`smithery.ai`) | the public GitHub repository | Submit with a GitHub sign-in. Check their current requirements for a stdio server on the day; they change. |
| PulseMCP (`pulsemcp.com`) | the official registry | Submissions paused as of October 2026; the site says it will pick up the official registry when it reopens. Check on the day. |
| mcp.so | a submission | Submit the repository URL and the canonical copy. |
| Cursor | the README's Cursor block | No documented submission path for a local server; check on the day. |
| VS Code | GitHub's MCP registry, which picks up the official registry | No separate submission for a stdio server; the README's VS Code block is the install path. |

The `modelcontextprotocol/servers` repository no longer lists third-party
servers; the official registry is the route. Directories for remote servers
(Anthropic's connectors directory, OpenAI's apps directory, cloud
marketplaces) list a remote endpoint, not a local package, and are outside
this page.

## Submission day

1. Confirm the published PyPI version equals `server.json`'s `version`.
2. Confirm the published README carries the `mcp-name` marker (it ships in
   the package description).
3. Run `uv run --package legesher-mcp pytest libs/mcp/tests/test_registry_manifest.py -q`.
4. Publish to the official registry, then work down the table.
5. Record each listing URL in the package README under Listings.
