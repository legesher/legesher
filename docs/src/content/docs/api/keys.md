---
title: Keys and sign-in
description: Create an API key, sign in from a command line or an editor, check a key, and revoke it.
---

A request sends its key as a bearer token:

```http
Authorization: Bearer lgsh_live_...
```

Keys start with `lgsh_live_`. Treat a key like a password: keep it out of source control, browser code and
shared logs. Legesher stores only a hash of each key, so a key cannot be shown again after it is created.
If you lose one, create a new key and revoke the old one.

## Create a key on the keys page

1. Create an account at [app.legesher.io](https://app.legesher.io) and verify your email address.
2. Open **Your keys** and create a key.
3. Copy the key and store it. It is shown once.

How many keys you can hold at once depends on your plan. The keys page also revokes a key.

## Sign in from a command line or an editor

A tool can get a key for its user without asking them to copy one, through the OAuth 2.0 device
authorization grant ([RFC 8628](https://www.rfc-editor.org/rfc/rfc8628)). Starting it needs no key. The
endpoints accept JSON or form-encoded bodies.

1. **Ask for a code pair.**

   ```bash
   curl -X POST https://api.legesher.io/v1/oauth/device \
     -H "Content-Type: application/json" -d '{}'
   ```

   ```json
   {
     "device_code": "...",
     "user_code": "WDJB-MJHT",
     "verification_uri": "https://app.legesher.io/device",
     "verification_uri_complete": "https://app.legesher.io/device?user_code=WDJB-MJHT",
     "expires_in": 600,
     "interval": 5
   }
   ```

2. **Send the user to approve it.** Show `user_code` and open `verification_uri`, or open
   `verification_uri_complete`, which fills the code in. The user signs in at app.legesher.io and approves
   the sign-in.

3. **Poll for the key.** Every `interval` seconds, until the user decides or the code expires:

   ```bash
   curl -X POST https://api.legesher.io/v1/oauth/token \
     -H "Content-Type: application/json" \
     -d '{"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "device_code": "<device_code>"}'
   ```

   While the user has not decided, the answer is HTTP 400 with an OAuth error:

   | `error`                  | What to do                                                       |
   | ------------------------ | ---------------------------------------------------------------- |
   | `authorization_pending`  | Keep polling at the same interval.                               |
   | `slow_down`              | Add 5 seconds to the interval, then keep polling.                |
   | `access_denied`          | The user declined. Stop.                                         |
   | `expired_token`          | The code pair expired. Start again from step 1.                  |
   | `invalid_grant`          | The `device_code` is unknown or was already used. Start again.   |
   | `invalid_request`, `unsupported_grant_type` | The request is malformed: check `grant_type` and `device_code`. |

   Once the user approves, the answer is the key:

   ```json
   { "access_token": "lgsh_live_...", "token_type": "bearer" }
   ```

   The `access_token` is an ordinary API key. It does not expire and there is no refresh token. Store it the
   way you would store any key.

## Check a key

`GET /v1/me` describes the key that calls it: the plan, this month's usage, and the keys in its scope. Key
entries show a short hash prefix, never the key itself.

```bash
curl https://api.legesher.io/v1/me -H "Authorization: Bearer $LEGESHER_API_KEY"
```

## Revoke a key

Revoke a key on the keys page, or from a tool with `POST /v1/oauth/revoke`. This is how a command line
signs out:

```bash
curl -X POST https://api.legesher.io/v1/oauth/revoke \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$LEGESHER_API_KEY\"}"
```

A well-formed request gets `200` with the same body, whether the key was active, already revoked or never
existed (unless it is rate-limited, which answers `429`). A revoked key gets `401` from then on.
