---
title: Privacy
description: Where Legesher's privacy and legal documents are, and the VS Code extension's privacy settings.
---

Legesher's privacy and legal documents are on legesher.io:

- [Privacy Policy](https://www.legesher.io/privacy)
- [Cookie Policy](https://www.legesher.io/cookies)
- [Terms of Service](https://www.legesher.io/terms)
- [Usage Policy](https://www.legesher.io/usage-policy)

## VS Code extension settings

The extension's three telemetry settings are off by default. Add one to your VS Code settings to keep it off, or to turn it off again.

### Usage telemetry

Usage statistics, with no code content. Error messages are scrubbed of file paths, email addresses and URLs before they are sent. The bundled VS Code telemetry library adds a pseudonymous machine id.

```json
{
  "legesher.telemetry.enabled": false
}
```

### ML training data (opt-in only)

Records your consent to share translation feedback. The extension sends no translation corrections today.

```json
{
  "legesher.telemetry.contributeToMLTraining": false
}
```

### Repository attribution

Records your choice about attaching a repository label to requests to Legesher's hosted service. The extension sends no repository label today. It also needs usage telemetry and VS Code's telemetry to be on.

```json
{
  "legesher.telemetry.repoAttribution": false
}
```

### VS Code's own telemetry

Setting VS Code's telemetry to off also turns off the extension's telemetry, and VS Code's own.

```json
{
  "telemetry.telemetryLevel": "off"
}
```
