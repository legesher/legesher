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
| `legesher-core`            | [libs/core/](libs/core/)                                             | Apache-2.0 |
| `legesher-i18n`            | [libs/i18n/](libs/i18n/)                                             | Apache-2.0 |
| `legesher-language-server` | [libs/language-server/](libs/language-server/)                       | Apache-2.0 |
| `legesher-vscode`          | [libs/vs-code/](libs/vs-code/)                                       | Apache-2.0 |
| Python language packs (51) | [libs/i18n/language-packs/python/](libs/i18n/language-packs/python/) | Apache-2.0 |

The 51 Python language packs inherit their license from [libs/i18n/LICENSE](libs/i18n/LICENSE).

## Dual Licensed — Apache 2.0 OR Commercial

The main `legesher` CLI package is available under either the Apache License 2.0 (free tier)
or a commercial license from Legesher (premium tier). You may choose whichever option fits
your use case.

| Package    | Path                             | License                               |
| ---------- | -------------------------------- | ------------------------------------- |
| `legesher` | [libs/legesher/](libs/legesher/) | `Apache-2.0 OR LicenseRef-Commercial` |

See [libs/legesher/LICENSE](libs/legesher/LICENSE) for the full dual-license text.

**Free tier** (Apache 2.0): Local translation, CLI tools, editor integrations, language packs.

**Premium tier** (Commercial): Cloud sync, team collaboration, advanced analytics, priority
support, SLA guarantees. Contact [sales@legesher.com](mailto:sales@legesher.com) or visit
[legesher.io/pricing](https://legesher.io/pricing).

## Third-Party Dependencies

Third-party dependency licenses are listed in each package's `pyproject.toml` (Python) or
`package-lock.json` (Node.js). These files record the SPDX license identifier declared by
each upstream dependency.

## Questions

For licensing questions, contact [legal@legesher.com](mailto:legal@legesher.com) or open a
[license question issue](.github/issue_template/license_question.yml).

## Trademarks

"Legesher" and associated logos are trademarks and may not be used without permission.
