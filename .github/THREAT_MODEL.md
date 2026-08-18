# Script-inclusion threat model

**Scope:** every surface where "additional scripts" — code, or data that shapes how code renders or executes — can
enter a Legesher product. One section per surface: attack classes, existing mitigations (with file citations), gaps,
and a verdict.

**Out of scope:** the Hosted-API service chapter (STRIDE/OWASP analysis of the FastAPI service — auth, rate limiting,
billing) is a separate document tracked as CORE-1090 and deferred until a Hosted-API launch is scheduled.

**Status:** governing | superseded-by: none | defers-to: [SECURITY.md](SECURITY.md) (reporting, disclosure, response
process)

**Ticket:** CORE-1452. File paths are relative to the repository root unless prefixed with a repository name.

---

## The trust model in one paragraph

Legesher's load-bearing security claim is **"packs are data, not code."** The engine translates Python between natural
languages through reviewed YAML term maps; nothing a pack or map contains may ever be executed, and nothing a pack or
map contains may make code *render* differently than it *executes* (the Trojan-Source family, generalized). Every
surface below is a path by which attacker-controlled bytes could break one of those two invariants — by smuggling
execution into a data channel, or by splitting the rendered surface from the executed canonical form.

Two prior workstreams anchor the mitigations cited throughout:

- **CORE-1315** — Unicode/script safety validation gate: per-language `ScriptPolicy` (default-deny), `SchemaValidator`
  strict checks, path-traversal guards in the pack loader, and the `validate-packs` CI gate (blocking since
  CORE-1318).
- **CORE-1453** — the "data, not code" contract made mechanical: `legesher_i18n/data_contract.py` (safe-load-only YAML
  with no tags/anchors, file-size cap, URL-scheme allowlist, top-level-key allowlist, pack-level render-vs-execute
  round-trip).

---

## Surface 1 — Language packs

Packs are YAML term maps under `libs/i18n/language-packs/`, loaded by the engine, the MCP server, and the VS Code
extension. They are the primary community-contribution surface once packs open for external review.

### Attack classes

- **Code smuggled into the data channel:** YAML tags that construct objects on load; anchor/alias expansion
  (billion-laughs DoS); executable-shaped extra keys; `javascript:`/`file:`/`data:` URLs in metadata.
- **Map-as-attack-vector (render vs execute):** a pack or map entry that makes source render one way and execute
  another — bidi controls, invisible/format characters, default-ignorable code points, NFKC-unstable sequences,
  cross-section collisions, or a map whose rendered surface does not round-trip to the canonical form it claims to
  represent.
- **Path traversal:** pack `version` or `extends` values escaping the pack directory.
- **Trust-tier confusion:** a machine-drafted pack presenting as reviewed/official.

### Existing mitigations

- Safe-load only, everywhere on the Python side: `libs/i18n/legesher_i18n/pack_loader.py` uses `yaml.safe_load`;
  `libs/i18n/legesher_i18n/data_contract.py::check_yaml_data_only` additionally rejects any YAML tag or anchor/alias
  at the event-stream level, so the contract holds however the file is later loaded.
- File-size cap (`data_contract.MAX_PACK_FILE_BYTES`, 1 MiB), top-level-key allowlist, and http(s)-only metadata URLs
  (`data_contract.py`, CORE-1453).
- Strict schema + Unicode gate: `libs/i18n/legesher_i18n/schema_validator.py` (`validate_pack_strict`: NFKC stability,
  script consistency, format-char policy, live-keyword collisions including fullwidth confusables, min-interpreter XID
  checks) over `libs/i18n/legesher_i18n/script_policy.py` (per-language allowed scripts and format chars,
  **default-deny** for unpolicied languages).
- Path-traversal guards: `pack_loader.py` validates `version` before joining it into a filename and component-checks
  `extends` chains (Windows and POSIX separators both).
- Pack-level render-vs-execute round-trip: `data_contract.py::check_map_roundtrip` verifies the localized surface a
  merged pack renders maps back byte-identically to its canonical form; its source-level counterpart is
  `libs/core/legesher_core/round_trip.py` (byte-identical by design — normalization would mask exactly the defect the
  check exists to catch).
- Engine-side guard, independent of pack validation: `libs/core/legesher_core/unicode_guard.py` detects bidi controls
  (CVE-2021-42574 set), invisibles, default-ignorables, tatweel padding, and interior BOMs in source text.
- Blocking CI: `.github/workflows/validate-packs.yml` fails on any audit error across all shipped packs (CORE-1318).
- Review ladder as trust tier: `libs/i18n/docs/pack-maturity-ladder.md` (`experimental → reviewed → official`),
  stamped in `metadata.review_status` and warned on by `LanguagePackLoader.load(strict=True)` for anything not
  `official`.

### Gaps

The pack layer is gated; the **map layer is not**. Maps are the second data channel with render authority:
`.legesher/register_map.json` (`libs/core/legesher_core/register_map/model.py`, node-keyed, schema 1.2.0) and the
embedded identifier map (`libs/core/legesher_core/tree_sitter/identifier_map.py`). Unlike packs, map artifacts are
authored per-repo and — under the shared-map design — **received from other people**. Today:

- `RegisterMapDocument.load` parses JSON and checks `schema_version` only. No Unicode scan of stored `original_text`
  or rendered surfaces.
- `libs/core/legesher_core/register_map/correction.py` runs `unicode_guard.scan_text` on **newly authored**
  corrections (and `compare_key` for collision checks), but nothing re-validates entries already present in a loaded
  artifact. An artifact edited out-of-band, or synced from a teammate, bypasses the guard entirely.
- No render-vs-execute round-trip exists at the map layer: nothing proves that rendering a file through a received map
  and mapping it back yields the identical canonical program.

### Specification: map-layer render-vs-execute consistency check (extends CORE-1315 to maps)

A loaded or merged map artifact passes three checks before any rendering uses it, mirroring what CORE-1315/CORE-1453
already enforce for packs:

1. **Surface scan.** Every stored text with render authority (`original_text`, identifier translations, correction
   targets) passes `unicode_guard.scan_text` with the owning language's `script_policy` format-char allowlist. Fail
   closed; never sanitize (stripping a bidi control hides the attack the scan exists to surface — same posture as the
   JS guard).
2. **Identity discipline.** Stored text is NFC (the store-NFC contract already documented in `register_map/model.py`);
   collision detection over the map uses `compare_key` (NFKC + casefold) so no two entries can render visually
   identical while executing as different identifiers. Reject any pair of entries whose rendered surfaces are
   `compare_key`-equal but whose canonical targets differ.
3. **Round-trip.** Render the canonical source through the map, map the rendering back, and require byte-identical
   canonical output — `round_trip.verify_round_trip` extended over the map's identifier layer, the same "raw `==` is
   correct here" rule as pack round-trip.

Enforcement points: `RegisterMapDocument.load`, map merge (shared-map ingestion), and the CI gate for any map artifact
committed to a repo. A locally minted, never-shared map may run the scan lazily; a **received** map artifact must pass
all three before first use.

### Verdict

**Child-ticket proposal — "Shared/register map: render-vs-execute gate at load"**: apply the three-check specification
above to `RegisterMapDocument.load`/merge and identifier-map ingestion, so a received map artifact clears the same bar
as a shipped pack. (Pack-side enforcement is done — CORE-1453; this closes the map side before the shared-map OSS
flip.)

---

## Surface 2 — Import hook / runtime

`libs/legesher/legesher/runtime/import_hook.py` (CORE-464 lineage) implements PEP 302: native-language source is
translated to canonical Python and compiled to bytecode at import time. `libs/runtime/legesher_runtime/hooks.py`
localizes tracebacks on the way out.

### Attack classes

- **Semantic drift in translation:** if translation is non-deterministic or context-sensitive, the code a developer
  read is not the code that ran. The project rule "non-determinism here is a bug" is therefore a security property,
  not only a correctness one.
- **Trojan-Source on the execution path:** source containing bidi controls or invisibles that renders innocuously but
  tokenizes differently.
- **Cache poisoning:** a stale or substituted translation served for a modified file.
- **Injection through the translation layer:** a pack/map entry that expands into more tokens than it claims (covered
  at the data layer by Surfaces 1's gates).

### Existing mitigations

- Translation is deterministic token mapping: the hook calls `TokenTranslator.translate_code`
  (`libs/core/legesher_core/`), a pure pack-driven token substitution. No LLM, no network, no environment-dependent
  behavior on the execution path.
- Round-trip verification is owned and byte-exact: `libs/core/legesher_core/round_trip.py`.
- The translation cache (`import_hook.py::_TranslationCache`) is in-process, thread-safe, and invalidated on file
  modification — there is no on-disk cache an attacker could pre-seed.
- Traceback hooks never raise and fall back to CPython's own hooks (`libs/runtime/legesher_runtime/hooks.py`), so the
  error path cannot be used to suppress or forge diagnostics.
- The git clean filter scans source with `unicode_guard.scan_text` before translating
  (`libs/core/legesher_core/git_filter.py`).

A framing note: the import hook grants no *new* execution authority. `import mi_modulo` executes code with the user's
privileges with or without Legesher — Python's baseline. The obligation specific to this layer is narrower:
translation must not silently *alter* what executes.

### Gaps

- **Guard asymmetry:** `unicode_guard` runs on the git-filter path but not on the import-hook path. Source imported
  directly (never having passed through the clean filter — e.g. a file received from a collaborator, or a repo where
  the filter is not installed) is translated and compiled without a bidi/invisible scan. The engine-side guard exists;
  it is simply not wired into `import_hook.get_data` or the `legesher run` path (`libs/legesher/legesher/cli/run.py`).
- The hook's language-detection heuristic (`import_hook.py`, keyword-substring check) decides whether translation
  applies; it is a UX heuristic, not a security control, and should never be one — the guard above must run regardless
  of detection outcome.

### Verdict

**Child-ticket proposal — "Runtime: unicode_guard on the import-hook and run paths"**: invoke
`unicode_guard.scan_text` (with the active language's format-char allowlist) on source before translation/compilation
in `import_hook` and `legesher run`, achieving parity with the git clean filter. Fail closed with a clear diagnostic.

---

## Surface 3 — Contributor CI bots

The planned contributor-experience bots (auto-format, changelog entry, DCO check) will run against untrusted PR code —
the classic GitHub Actions pwn-request vector.

### Attack classes

- **Pwn request:** untrusted PR code executing in a privileged workflow (`pull_request_target` + secrets + checkout of
  PR head).
- **Action supply chain:** unpinned third-party actions replaced upstream.
- **Token over-scope:** default write-scoped `GITHUB_TOKEN` in jobs that only need read.

### Existing mitigations

- The one bot-like workflow already in the repo models the correct pattern and says so:
  `.github/workflows/dependabot-auto-merge.yml` uses `pull_request` (explicitly *not* `pull_request_target`, per its
  own header comment) to avoid granting write context to PR-triggered runs.
- Least-privilege permissions blocks: `.github/workflows/security.yml` declares `permissions: contents: read`.
- Third-party actions are pinned by full commit SHA across workflows (e.g. `actions/checkout@d23441a4…` in
  `security.yml`).
- `workflow-lint.yml` lints the workflow files themselves.
- Bandit runs on every PR with High-severity findings blocking (`security.yml`); CodeQL is configured (`codeql.yml`).

### Gaps

None structural today — the bots do not exist yet, and the hardening design for them is already tracked: CORE-1454
specifies the unprivileged-run + artifact-handoff pattern (untrusted code only in `pull_request` jobs with no secrets;
privileged labeling/committing in a separate `workflow_run` job that never checks out PR code; SHA-pinned actions;
per-job least privilege; format-only bot diffs). The requirement is that the first bot ships against that design
rather than retrofitting it.

### Verdict

**Boundary adequate today**, with the hardening design already carried by the existing child ticket CORE-1454 (no new
ticket proposed; CORE-1454 becomes a child of this model when scheduled).

---

## Surface 4 — MCP server tools

`libs/mcp/legesher_mcp/` ships a local stdio server today; a multi-tenant hosted MCP server is planned. This section
models both; the hosted build work is CORE-1423 — **that ticket implements, this document models**, and the checklist
below is written to become CORE-1423's implementation checklist so requirements are tracked once.

### Attack classes

- **Path traversal / filesystem reach** via language codes or file paths supplied as tool arguments.
- **Resource exhaustion:** unbounded source payloads.
- **Information leak in errors:** stack traces, filesystem paths, echoed customer source.
- **Secrets-in-code reaching a fuzzy layer:** `map_existing_codebase` ingests customer repos; anything forwarded to an
  LLM-backed layer risks exfiltrating embedded secrets, and the never-train commitment must be enforced, not asserted.
- **Hosted-specific (2026 MCP CVE class):** token passthrough, cross-tenant leakage, tool poisoning (malicious
  instructions in tool descriptions), SSRF from server-side fetches.

### Existing mitigations (local server)

- Local-only by construction: stdio transport, no network calls, no accounts, no telemetry
  (`libs/mcp/legesher_mcp/server.py` module header and `_INSTRUCTIONS`).
- Path traversal cut off before any resolution: `LANG_CODE_PATTERN` is validated prior to pack/path lookup
  (`libs/mcp/legesher_mcp/engine.py`).
- Input caps: `SOURCE_MAX_CHARS`, `SNIPPET_MAX_CHARS`, `LANG_CODE_MAX_LENGTH` enforced through Pydantic field
  constraints (`libs/mcp/legesher_mcp/schemas.py`, applied in `server.py`).
- Content-free errors: `EngineError` carries a machine code plus generic message — no stack traces, no paths, no
  echoed source (`engine.py`, `server.py::_tool_error`).
- File paths in `map_existing_codebase` are report labels only — never logged, never used to touch the filesystem
  (`server.py`, parameter description and implementation).
- The engine is deterministic pack lookup; no LLM sits behind any tool, so there is currently no fuzzy layer for
  secrets to reach.
- Tool descriptions are static strings in reviewed source — tool-poisoning requires a code change that passes review,
  not a runtime injection.

### Gaps → the CORE-1423 implementation checklist

Everything below applies the moment the server is exposed beyond a local stdio pipe. Written as the checklist for
CORE-1423:

- [ ] OAuth 2.1 + PKCE; **audience validation** on every token; never forward client tokens upstream (no token
  passthrough)
- [ ] Tenant isolation: per-tenant data partitioning, tests that prove cross-tenant reads fail
- [ ] Schema-validated tool *outputs* (not only inputs), so a compromised engine cannot smuggle content into responses
- [ ] SSRF/egress controls: block server-side requests to private IP ranges and metadata endpoints; explicit egress
  allowlist
- [ ] Tool-poisoning defenses: tool descriptions pinned and hash-verified at deploy; no runtime-mutable tool metadata
- [ ] Secrets redaction before any fuzzy/LLM layer is added: scan ingested source for credential patterns and redact
  prior to any non-deterministic processing; document and enforce the never-train commitment at the same boundary
- [ ] Ingestion limits per tenant and per request (files, bytes, rate) — the local `SOURCE_MAX_CHARS` cap generalized
- [ ] Human-approval gates for any destructive or repo-mutating action
- [ ] Content-free error contract carried over unchanged from the local server
- [ ] `mcp-scan` (or equivalent) in CI — distribution platforms scan MCP traffic and block failing servers, so this
  gates reach as well as hygiene

### Verdict

**Local boundary adequate today.** The hosted boundary is owned by the existing child ticket CORE-1423 (no new ticket
proposed); the checklist above supersedes ad-hoc requirement tracking there.

---

## Surface 5 — Courseware integrations (courseware / JEJ)

Localized code written by students is translated by Legesher's JS layer (`js-engine-repo` repository) and graded on the
customer's Jobe sandbox. Legesher code never runs inside the customer's platform; the integration boundary is: we
supply translation, they own execution.

### Attack classes

- **Guard smuggling:** the translation layer converting a localized construct into canonical output that slips past
  the grader's syntax allowlist — i.e. Legesher becoming an encoder for constructs the sandbox would have rejected if
  typed directly.
- **Unicode attacks in student submissions:** bidi/invisible characters that make graded code differ from displayed
  code.
- **Responsibility ambiguity:** neither party validating something because each assumes the other does.

### Existing mitigations

- Fail-closed source guard on the JS side: `js-engine-repo/packages/core/src/assert-source-safe.ts` rejects bidi
  controls, invisibles, and the full `\p{Default_Ignorable_Code_Point}` derived property on first hit — hostile text
  is rejected, never sanitized (CORE-1384 lineage; known residual: script-aware allowlist for invisible marks in
  unsupported scripts is CORE-1558).
- Constrained execution surface in the JEJ package: `js-engine-repo/packages/jej/src/is-allowed-global.ts` (global
  allowlist), `deep-freeze.ts` (immutable surface), `surface.ts`, with `conformance-fixtures.ts` pinning expected
  behavior.
- Translation is deterministic token mapping over reviewed packs — it cannot *invent* constructs; it can only rename
  terms the pack maps, so canonical output contains exactly the construct set of the input.
- The grading sandbox itself is the customer's (Jobe), keeping arbitrary-code execution off Legesher infrastructure
  entirely.

### Gaps

- The **responsibility boundary is not documented in an integration-facing guide**. The division (Legesher: Unicode
  guard + deterministic translation; customer: syntax allowlisting + sandboxed execution + resource limits) exists in
  practice and in private working notes, but no artifact a courseware integrator receives states who guards what.
  Ambiguity here is itself the vulnerability.
- No conformance fixtures currently prove the negative claim end-to-end: that for every guard rule on the customer
  side, localized input cannot reach a canonical form that bypasses it.

### Verdict

**Child-ticket proposal — "Courseware integration guide: responsibility boundary + guard-parity fixtures"**: add a
security section to the integration guide stating the Legesher/customer responsibility split, and land conformance
fixtures demonstrating that localized submissions cannot smuggle constructs past target-side syntax guards.

---

## Surface 6 — Auto-PR package-map engine (future)

A planned engine that raises pull requests onto third-party repositories carrying package-map updates. Nothing is
built; today only a local `legesher map` CLI exists (`libs/legesher/legesher/cli/map_cmd.py`).

### Attack classes

- **Supply-chain injection:** a compromised or spoofed engine pushing malicious map/pack changes into downstream repos
  under Legesher's name.
- **Provenance gap:** maintainers unable to verify that a PR genuinely originated from the engine and corresponds to a
  published, reviewed map version.
- **Consent bypass:** PRs raised onto repos that never opted in — reputational and legal exposure even when content is
  benign.
- **Privilege concentration:** a bot identity with write access across many third-party repos becomes a single
  high-value target.

### Existing mitigations

None — the surface does not exist. That is the correct state to attach requirements to: security properties here are
design inputs, not retrofits.

### Verdict

**Child-ticket proposal — "Auto-PR engine design gate: provenance, signing, opt-in governance"**: a requirements
ticket that must close before any build starts — signed commits/artifacts traceable to a published map release,
explicit per-repo opt-in registry, least-privilege bot identity (short-lived tokens, per-repo scope), and
rate/blast-radius limits. The ticket exists to make "do not build without this" a tracked gate rather than a memory.

---

## Surface 7 — VS Code extension

`libs/vs-code/` renders pack data inside the privileged extension host. The same "data, not code" contract applies:
pack bytes may drive rendering, never execution.

### Attack classes

- **Pack-driven code execution in the extension host:** unsafe YAML deserialization, or pack content reaching
  `eval`-equivalent sinks.
- **Webview injection:** pack strings rendered into webview HTML executing script.
- **Resource exhaustion:** oversized pack files parsed in the host.

### Existing mitigations

- Safe YAML on the JS side: `libs/vs-code/src/languagePackLoader.ts` parses with js-yaml v4 `load` (`package.json`
  pins `js-yaml ^4.2.0`), which is safe-by-default — no object construction from tags.
- The CORE-1453 size cap is mirrored extension-side: `MAX_PACK_FILE_BYTES` in `languagePackLoader.ts` refuses
  oversized files before parsing, by design mirroring `legesher_i18n.data_contract`.
- Packs are loaded from the extension's own bundle or the monorepo checkout
  (`languagePackLoader.ts::getLanguagePacksPath`) — the same files that passed the blocking `validate-packs.yml` gate
  — not from arbitrary user-supplied paths.
- The webview ships a restrictive CSP with per-load nonce (`libs/vs-code/src/webview/panel.ts`:
  `Content-Security-Policy` limiting `style-src`/`font-src` to `cspSource` and `script-src` to `cspSource` plus a
  nonce).
- Extension posture documented in [SECURITY.md](SECURITY.md): minimal VS Code API permissions scoped to Python files,
  telemetry off by default, language server as a local process with no network calls.

### Gaps

- Extension-side schema validation is shallow (a size cap and a string-map shape check, but no strict schema, Unicode,
  or trust-tier validation). Acceptable while packs
  are exclusively bundled from a gated build; it becomes a real gap only if the extension ever loads user-supplied or
  marketplace-distributed packs — at which point the full Surface-1 contract (strict schema, Unicode gate, trust-tier
  warning) must be replicated or delegated to the language server. That trigger condition, not today's state, is the
  thing to watch.

### Verdict

**Boundary adequate today.** Revisit before any feature that loads packs from outside the gated bundle; that feature's
ticket must carry the Surface-1 contract as an acceptance criterion.

---

## Summary of verdicts

| # | Surface | Verdict |
| --- | --- | --- |
| 1 | Language packs | Pack layer gated (CORE-1315/1453/1318); **proposal:** map-layer render-vs-execute gate at load |
| 2 | Import hook / runtime | **Proposal:** unicode_guard on the import-hook and run paths (parity with the git filter) |
| 3 | Contributor CI bots | Boundary adequate today; design carried by existing CORE-1454 |
| 4 | MCP server tools | Local boundary adequate today; hosted checklist owned by existing CORE-1423 |
| 5 | Courseware integrations | **Proposal:** integration-guide responsibility boundary + guard-parity fixtures |
| 6 | Auto-PR engine | **Proposal:** design-gate ticket (provenance, signing, opt-in governance) before build |
| 7 | VS Code extension | Boundary adequate today; re-open if packs ever load from outside the gated bundle |

Child tickets are proposals only; which are filed now versus deferred is recorded on CORE-1452.
