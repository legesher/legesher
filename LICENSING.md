# Legesher Licensing

Legesher is a multi-license monorepo. The root [LICENSE](LICENSE) file contains the full text
of the Apache License 2.0, which applies to most of the repository. However, **individual
packages may be licensed differently** — the per-package LICENSE file always takes precedence
for that directory.

This document enumerates the license for each package and directory.

## Open Source — Apache License 2.0

These packages are licensed under the [Apache License 2.0](LICENSE). You may use, modify, and
distribute them freely, subject to the terms of the license.

| Package                    | Path                                                                 | License    |
| -------------------------- | -------------------------------------------------------------------- | ---------- |
| `legesher`                 | [libs/legesher/](libs/legesher/)                                     | Apache-2.0 |
| `legesher-core`            | [libs/core/](libs/core/)                                             | Apache-2.0 |
| `legesher-i18n`            | [libs/i18n/](libs/i18n/)                                             | Apache-2.0 |
| `legesher-language-server` | [libs/language-server/](libs/language-server/)                       | Apache-2.0 |
| `legesher-mcp`             | [libs/mcp/](libs/mcp/)                                               | Apache-2.0 |
| `legesher-vs-code`         | [libs/vs-code/](libs/vs-code/)                                       | Apache-2.0 |
| Python language packs (51) | [libs/i18n/language-packs/python/](libs/i18n/language-packs/python/) | Apache-2.0 |

The 51 Python language packs inherit their license from [libs/i18n/LICENSE](libs/i18n/LICENSE).

Everything published from this repository is Apache-2.0. You may use, modify, and redistribute
it — including commercially — subject to the license terms.

## Paid Capabilities Live in the Hosted Service

Legesher is open-core. The open half is this repository: the engine, the language data, the CLI,
and the editor integrations, all Apache-2.0 and locally executable with no account and no network
call. That matters beyond price — Legesher rewrites your source and installs a git filter, so you
should be able to read exactly what it does to your code before you run it.

The commercial half is the hosted service (cloud translation API, and the collaboration and
analytics capabilities built on it). It is a separate, closed-source codebase, and access is
gated by account, API key, and subscription — not by the license on anything in this repository.
Its customer terms live with that service.

Pricing and availability: [legesher.io/pricing](https://legesher.io/pricing).

## Third-Party Dependencies

Third-party dependency licenses are listed in each package's `pyproject.toml` (Python) or
`package-lock.json` (Node.js). These files record the SPDX license identifier declared by
each upstream dependency.

## Questions

For licensing questions, contact [legal@legesher.com](mailto:legal@legesher.com) or open a
[license question issue](.github/issue_template/license_question.yml).

## Trademarks

"Legesher" and associated logos are trademarks and may not be used without permission.
