# Repository attribution

Repository attribution is opt-in usage attribution. When you switch it on, a
Legesher client attaches a label for the current repository to its calls to
Legesher's hosted service, so usage can be attributed to a repository. The
label is derived from the repository; the repository's name, path and remote
URL are not sent as such.

## What is sent

`X-Legesher-Repo: <32 hex characters>`

For a repository with an `origin` remote, the value is the first 32 hex
characters of a SHA-256 hash of the fixed prefix `legesher-repo/v1:` followed
by the canonical form of the remote URL (described below). The hash has no key
and no salt, so every clone of the same repository produces the same label,
however many people work in it.

### What the label reveals

The label is not secret. Anyone who knows or guesses a repository's remote URL
can compute its label with the same recipe, and so can tell whether that
repository is the one in use. For a public repository, assume the label
identifies it. The label does not reveal a remote URL that nobody can guess.

A repository with no `origin` remote (or whose remote is a local path, or is
treated as malformed as described below) gets a per-install label instead: the
same hash over a random salt minted once into `~/.legesher/install-salt` plus
the repository's top-level path. The salt never leaves your machine, so the path
cannot be checked against the label, and two installs give the same local-only
project different labels. Any directory inside the repository gives the
repository's label.

If `~/.legesher/install-salt` exists but is not exactly 32 lowercase hex
characters, or cannot be read or created, no label is sent. Delete a damaged
file to have a new salt minted on the next run.

### The canonical remote

The canonical form is computed the same way, character for character, by the
Python and TypeScript helpers. That holds for characters whose Unicode
normalization is the same in the Unicode versions of the runtimes in use:
Unicode 16 added compositions (U+105D2 followed by U+0307 composes to U+105C9)
that Python 3.13 does not apply but Python 3.14 and current Node do. The steps:

1. Trim ASCII whitespace and one leading byte order mark.
2. A single letter followed by `:/` or `:\` (a Windows drive, such as
   `C:/Users/alice/repo`) and a `file://` URL are local paths: the per-install
   label applies.
3. From `scheme://[user@]host[:port]/path[?query][#fragment]`, or from the
   scp-like `[user@]host:path` (a colon with no slash before it, as git reads
   it), keep only the host and the path. The scheme, the userinfo (everything up
   to the last `@` before the host), the port, the query and the fragment are
   dropped. An IPv6 host keeps its brackets, `[::1]`. If an `@` is still left in
   the host or the path, the remote is treated as malformed (git reads
   `user:password@host:path` as the host `user`), so it has no canonical form
   and the per-install label applies. A password in a malformed remote never
   reaches the hash.
4. Put the host and path in Unicode NFC, lowercase ASCII `A` to `Z` only, and
   apply NFC again.
5. Remove leading and trailing slashes from the path, then one trailing `.git`,
   then trailing slashes again.

Nothing is percent-decoded or percent-encoded, a Unicode host is not converted
to or from punycode, and `.` and `..` segments are kept. Two spellings that
differ in any of those ways count as different remotes.

Lowercasing ASCII letters makes `github.com/Legesher/legesher-next` and
`github.com/LEGESHER/Legesher-Next` one repository, which matches how GitHub and
most hosts treat owner and repository names. The trade-off: two repositories on
a case-sensitive self-hosted server whose paths differ only in ASCII letter case
share one label.

`libs/core/tests/fixtures/repo_attribution_vectors.json` holds the vectors both
helpers are tested against, in Devanagari, vocalised Arabic, Sinhala with ZWJ
and CJK as well as Latin script, with NFC and NFD spellings of each.

## Switching it on and off

Attribution is off by default and needs two settings in your user config
(`~/.legesher/config.yml`):

```bash
legesher config set --global telemetry.enabled true          # the default
legesher config set --global telemetry.repo_attribution true
```

Only the boolean `true` opts in; a string such as `"yes"` does not.
`telemetry.enabled` is off when it is `false`, `null`, `0`, an empty string or
one of the words `off`, `no`, `false` or `0`, in any case.

Telemetry settings are per user. They are read from the user config only, and a
project's `.legesher/config.yml` cannot change them, so a committed project
file can neither opt you in nor switch you back on. `legesher config set`
refuses a telemetry key without `--global`.

Either kill switch turns every kind of telemetry off, whatever the config
says, when it is set to anything but `0`, `false`, `no`, `off` or an empty
value (ASCII whitespace and ASCII letter case are ignored):

```bash
export LEGESHER_TELEMETRY_DISABLED=1
export DO_NOT_TRACK=1
```

In VS Code the settings are `legesher.telemetry.enabled` and
`legesher.telemetry.repoAttribution`, and VS Code's own telemetry setting must
also be on. The extension does not send this label yet: the
`legesher.telemetry.repoAttribution` setting records your choice only.

## For client authors

Python:

```python
from legesher_core.repo_attribution import repo_attribution_headers

headers = {**base_headers, **repo_attribution_headers(repo_root, config=config)}
```

TypeScript (the VS Code extension):

```ts
import { repoAttributionHeaders } from './repoAttribution';

const headers = {
    ...baseHeaders,
    ...repoAttributionHeaders({
        remoteUrl, repoRoot, installSalt,
        telemetryEnabled, repoAttribution,
        vscodeTelemetryEnabled: vscode.env.isTelemetryEnabled,
    }),
};
```

Both helpers return an empty mapping when attribution is not allowed or no
label can be produced safely, so a caller can always spread the result. Neither
raises.
