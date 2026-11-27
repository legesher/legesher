---
title: Errors and limits
description: The error envelope, every error code, and how to read your request rate and monthly usage.
---

## The error envelope

Every error answer from the API has the same body:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [{ "field": "body.source_lang", "message": "Field required", "type": "missing" }]
  }
}
```

- `code` is stable and machine-readable. Branch on it, not on `message`.
- `message` is for people and may change.
- `details` appears only on `validation_error`, with one entry per field.

An error body never contains file paths, stack traces or the source you sent. A `401` never says whether a
key exists, was revoked or was mistyped.

The device sign-in endpoints answer the OAuth way instead (`{"error": "authorization_pending"}`); see
[Keys and sign-in](/api/keys/#sign-in-from-a-command-line-or-an-editor).

## Error codes

| Status | `error.code`              | When                                                                                       |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------ |
| 400    | `bad_request`             | The request is malformed at the HTTP level.                                                |
| 401    | `unauthorized`            | The key sent is malformed, unknown or revoked; or `/v1/me` was called with no key.         |
| 402    | `tier_required`           | The request uses something your plan does not include, such as `"enhanced": true`.         |
| 402    | `entitlement_required`    | `POST /v1/map` was called without a key, or with a key whose plan does not include it.     |
| 404    | `not_found`               | The route does not exist.                                                                  |
| 404    | `language_pack_not_found` | The language is supported but has no pack for the requested `python_version`.              |
| 405    | `method_not_allowed`      | The route exists but not with this HTTP method.                                            |
| 413    | `payload_too_large`       | The request body or the source is over the size limit. Send less per request.              |
| 422    | `validation_error`        | A field is missing or malformed. `details` names each one.                                 |
| 422    | `unsupported_language`    | A language code is not one the API supports. See [Languages](/api/languages/).             |
| 422    | `invalid_source_code`     | The source could not be read as Python.                                                    |
| 429    | `rate_limited`            | Too many requests in a short time. Wait for `Retry-After` seconds when sent, then retry.   |
| 429    | `quota_exceeded`          | This month's character allowance is used up. It resets at the start of the next UTC month. |
| 500    | `internal_error`          | Something failed on our side. Retrying later is safe.                                      |
| 503    | `foundation_unavailable`  | The translation engine is unavailable. Retry later.                                        |
| 504    | `request_timeout`         | The request took too long to process. Send less source per request.                        |

## Limits

A plan can set a request rate and a monthly character allowance. Requests without a key share a smaller
trial allowance. The figures that apply to you are always in the response, so a client never needs to hard-code
them.

| Header                         | Meaning                                                              |
| ------------------------------ | -------------------------------------------------------------------- |
| `X-RateLimit-Limit`            | Requests allowed per minute on your plan.                            |
| `X-RateLimit-Remaining`        | Requests left in the current window.                                 |
| `X-RateLimit-Reset`            | Seconds until the window fully resets.                               |
| `X-Usage-Characters-Used`      | Characters used this UTC month.                                      |
| `X-Usage-Characters-Remaining` | Characters left this UTC month.                                      |

These headers come on success and error answers alike from the translate, validate, explain, map and
`/v1/me` routes, except on a request refused before the caller is identified, such as a `401`. A plan with no rate limit
leaves out the `X-RateLimit-*` set, and a plan with no character limit leaves out the `X-Usage-Characters-*`
pair. `GET /v1/me` reports the same numbers, along with when the month's window ends.

Every response, on every route, also carries `X-Request-ID`: an id for that request. Send your own and it is
echoed back.

A few rules about usage:

- Only a request that succeeds counts against your allowance. An error is not billed.
- For an account, every key draws on one shared monthly allowance.
- A request over a limit gets `429`. There is no overage charge.

## Retrying

Retry `rate_limited` after `Retry-After`, and `500`, `503` and `504` after a short pause. Do not retry other
`4xx` answers unchanged: fix the request first.

```python
import time

import httpx


def translate(client: httpx.Client, payload: dict) -> dict:
    for attempt in range(3):
        response = client.post("https://api.legesher.io/v1/translate", json=payload)
        if response.status_code == 429 and response.json()["error"]["code"] == "rate_limited":
            time.sleep(int(response.headers.get("Retry-After", "1")))
            continue
        if response.status_code in (500, 503, 504):
            time.sleep(2**attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("the API is still busy; try again later")
```

When you report a problem, include the `X-Request-ID` of the request.
