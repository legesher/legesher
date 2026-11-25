---
title: Privacy
description: Where Legesher's privacy and legal documents are, and the VS Code extension settings that control what it sends.
---

Legesher's privacy and legal documents are on legesher.io:

- [Privacy Policy](https://www.legesher.io/privacy)
- [Cookie Policy](https://www.legesher.io/cookies)
- [Terms of Service](https://www.legesher.io/terms)
- [Usage Policy](https://www.legesher.io/usage-policy)

## VS Code extension settings

The extension's three settings are off by default. Add one to your VS Code settings to keep it off, or to turn it off again.

### Usage telemetry

```json
{
  "legesher.telemetry.enabled": false
}
```

### ML training data (opt-in only)

```json
{
  "legesher.telemetry.contributeToMLTraining": false
}
```

### Repository attribution

```json
{
  "legesher.telemetry.repoAttribution": false
}
```

### VS Code's own telemetry

VS Code's own telemetry setting also turns the extension's telemetry off.

```json
{
  "telemetry.telemetryLevel": "off"
}
```
