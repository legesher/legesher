# Legesher Licensing

The root [LICENSE](LICENSE) file contains the full text of the Apache License 2.0. Every
package in this repository is licensed under it; the per-package LICENSE file is authoritative
for its directory.

This document enumerates the license for each package and directory, and states where the
open/paid boundary runs.

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

## The Open / Paid Boundary

Legesher is open-core. The open half is this repository — all of it Apache-2.0, locally
executable with no account and no network call. That matters beyond price — Legesher rewrites
your source and installs a git filter, so you should be able to read exactly what it does to
your code before you run it.

The commercial half lives in separate, closed-source codebases. Access is gated by account,
API key, and subscription — not by the license on anything in this repository — and customer
terms live with those services.

Pricing and availability: [legesher.io/pricing](https://legesher.io/pricing).

## Third-Party Dependencies

Third-party dependency licenses are listed in each package's `pyproject.toml` (Python) or
`package-lock.json` (Node.js). These files record the SPDX license identifier declared by
each upstream dependency.

## Questions

For licensing questions, contact [legal@legesher.com](mailto:legal@legesher.com) or open a
[license question issue](.github/ISSUE_TEMPLATE/license_question.yml).

## Trademarks

"Legesher" and associated logos are trademarks and may not be used without permission.
