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

The manifest names the repository by URL and by `repository.id`, the
forge's numeric id (`gh api repos/legesher/legesher --jq .id`), written as a
string. The registry schema describes the id as stable across renames and
different for a repository that was deleted and recreated, so if the
repository is ever recreated, read the new id and change it in `server.json`
and in the test together.

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
| Official MCP Registry (`registry.modelcontextprotocol.io`) | `server.json`; the `mcp-name` marker in the README published on PyPI | `mcp-publisher login github --token <token>` as an Owner of the `legesher` GitHub organisation, with a token that can read the organisation's membership (a classic personal access token with `read:org`, or the `MCP_GITHUB_TOKEN` environment variable holding one); the browser sign-in without a token cannot grant an organisation namespace ([registry#1468](https://github.com/modelcontextprotocol/registry/issues/1468)). Membership alone is refused for the `io.github.legesher/*` namespace; a DNS-verified name under the project domain is the alternative. Then `mcp-publisher publish` from `libs/mcp` on a checkout of `main` whose `server.json` carries the released version. Re-publish on every version bump. |
| PyPI | `README.md`, `[project.urls]`, keywords, classifiers | Nothing beyond the package publish. |
| Glama (`glama.ai/mcp/servers`) | the public GitHub repository, `glama.json`, and the build settings saved on the listing | Listed at <https://glama.ai/mcp/servers/legesher/legesher>. `glama.json` at the repository root names the maintainers who can edit it (organisation repositories must use the file). Glama builds a container from the listing's build settings before it lists a server; see [Glama](#glama) below. |
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

## Glama

What follows is how the listing worked in November 2026; check it on the day.

Glama builds each server into a container, starts it and runs the protocol's
introspection exchange (`tools/list`, `resources/list`, `prompts/list`)
before it lists it. The build comes from settings saved on the listing (its
Admin tab, under Dockerfile), not from a file in this repository: Glama turns
the settings into its own Dockerfile.

The settings for this server install the published package, so the listing
runs what `uvx legesher-mcp` runs:

| Setting | Value |
| --- | --- |
| Python version | 3.13 |
| Build steps | `["uv venv /opt/legesher-mcp", "uv pip install --python /opt/legesher-mcp/bin/python legesher-mcp==<version>"]` |
| Command | `["mcp-proxy", "--", "/opt/legesher-mcp/bin/legesher-mcp"]` |

`<version>` is the `legesher-mcp` version on PyPI that the Glama release is
for. Naming it makes a Glama release mean one server version; left out, each
rebuild installs whatever is newest that day. The build step names no date,
so on Glama the server's dependencies resolve on the day of each build. The
settings page kept an edit only when a build was started from it.

`libs/mcp/Dockerfile` runs the same build steps on a pinned base, so they can
be tried on a laptop first. It fixes everything the build downloads: the base
image and the uv image by digest; Python, mcp-proxy and `legesher-mcp` by
version; and the packages those two depend on by date (`RESOLVED_BEFORE`).
The base image, the user and the mcp-proxy version are this file's own
choices; Glama's generated file makes its own. The file needs no build
context, so it builds from standard input:

```bash
docker build -t legesher-mcp - < libs/mcp/Dockerfile
make test-mcp-docker
```

The make target builds the image and drives a session against it twice: over stdio, the
image's default, and through mcp-proxy over HTTP, the listing's command. Each
runs the introspection exchange, and a translation into Arabic and Hindi and
back, byte for byte. It needs a running Docker daemon and fails without one.
`tests/test_container_image.py` holds the file to its pins in the default
test run, and keeps the Python version, the command and the start of each
build step above in step with the file.

The image starts the stdio server by default. mcp-proxy, the listing's
command, listens on every interface, asks for no credentials and answers any
origin; that suits a directory's sandbox. To try it by hand, publish the port
on loopback only:

```bash
docker run --rm --publish 127.0.0.1:8080:8080 legesher-mcp mcp-proxy -- /opt/legesher-mcp/bin/legesher-mcp
```

For each `legesher-mcp` release, after the package is on PyPI:

1. In `libs/mcp/Dockerfile`, raise `LEGESHER_MCP_VERSION` to the published
   version, and `RESOLVED_BEFORE` to a day after it and the `legesher-core`
   and `legesher-i18n` releases it requires were published. The date may not
   be in the future, so a release published today waits until tomorrow. Then
   run `make test-mcp-docker`. Commit it as `build(mcp)`; a `fix` or `feat`
   subject would start another release.
2. On the listing, set the same version in the build step, start a build, and
   wait for its test to pass.
3. Create the Glama release from that build, with the server's own version
   number.

Refresh the other pins (the two image digests, Python and mcp-proxy) in the
same change when a newer release of one has been out for a week, or at once
when it is a security fix.

Keep Glama's automatic releases off for this repository. That setting cut a
Glama release for every GitHub release, and this repository publishes one for
each package it holds, so the listing would take its version numbers from
other packages. Glama accepted only a version higher than its latest, and its
admin page had no way to remove a release.

## Submission day

1. Confirm the published PyPI version equals `server.json`'s `version`.
2. Confirm the published README carries the `mcp-name` marker (it ships in
   the package description).
3. Run `uv run --package legesher-mcp pytest libs/mcp/tests/test_registry_manifest.py -q`.
4. Publish to the official registry, then work down the table.
5. Record each listing URL in the package README under Listings.
