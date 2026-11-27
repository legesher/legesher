---
title: Versioning
description: How the Legesher Bridge API is versioned, and how a version or a route is deprecated and retired.
---

## Versions

- **Every route lives under a version prefix, today `/v1`.** The version is part of the path, never a header
  or a query parameter, so a URL always says which contract it targets.
- **A new version (`/v2`) comes only with a breaking change:** a removed or renamed field, a changed type, a
  changed status code, or a removed route.
- **Additions ship into the current version.** A new optional field, a new route or a new enum value is not
  breaking. Write clients that ignore fields they do not know.
- **Old and new versions run side by side** for the whole deprecation window, so no client has to move on a
  deploy day.

Nothing is deprecated today.

## Deprecation window

A deprecated version or route keeps working for a designated period between the announcement and its sunset,
the date it stops responding. The sunset date is given when the deprecation is announced, so you know from the
start how long you have. You hear about it three ways:

1. **Response headers** on every call to the deprecated path (below), so a client can alert without anyone
   reading the docs.
2. **The [OpenAPI document](/api/openapi.json):** the route is marked `deprecated: true`, and the
   [endpoint reference](/api/reference/) shows it.
3. **A migration guide** under `docs.legesher.io/api/migrations/`, linked from the `Link` header, and a note
   in the changelog.

## Deprecation headers

A response from a deprecated route carries these headers on success and error answers alike
([RFC 9745](https://www.rfc-editor.org/rfc/rfc9745), [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594)):

| Header        | Meaning                                                                                           | Example                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `Deprecation` | When the route was deprecated: a date (`@` and Unix seconds), or `true` when no date is set.      | `Deprecation: @1798761600`                                                    |
| `Sunset`      | When the route stops responding, as an HTTP date.                                                 | `Sunset: Thu, 01 Apr 2027 00:00:00 GMT`                                       |
| `Link`        | The migration guide (`rel="deprecation"`) and the version to move to (`rel="successor-version"`). | `Link: <https://docs.legesher.io/api/migrations/v1-to-v2>; rel="deprecation"` |

## What a client should do

- **Log or alert** when a response carries `Deprecation`, so whoever owns the integration hears about it.
- **Treat `Sunset` as a deadline.** After it, the route may fail or stop responding. Plan the move well
  inside the window.
- **Follow the `Link` header** to the migration guide and the new version's base URL.
- Until `Sunset`, a deprecated route behaves exactly as before.
