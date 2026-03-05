---
title: Privacy Policy
description: Legesher privacy policy and data collection practices
---

# Privacy Policy

## Overview

Legesher is committed to protecting your privacy. This policy explains what data we collect and how we use it.

## Documentation Website (docs.legesher.io)

### Hosting

This documentation site is hosted on [Vercel](https://vercel.com).
Vercel processes standard server access logs (IP addresses, request
timestamps, URLs) as part of normal hosting operations. See
[Vercel's Privacy Policy](https://vercel.com/legal/privacy-policy)
for details.

### Analytics

This site uses
[Vercel Web Analytics](https://vercel.com/docs/analytics/privacy-policy),
which is designed to be privacy-compliant:

- **No cookies**: Vercel Web Analytics does not use cookies or any
  client-side storage
- **No personal identifiers**: Visitors are identified by an anonymous
  hash that cannot be used to track individuals across sites
- **No cross-site tracking**: Data cannot reconstruct browsing sessions
  or identify individual users
- **Aggregated data only**: We see page view counts, referrers,
  geolocation (country/region level), device type, and browser,
  all in aggregate

Data collected per page view: URL, referrer, geolocation
(country/region), device OS, browser, device type, and timestamp.
No IP addresses, user agents, or personal information are stored.

Because Vercel Web Analytics collects no personal data and uses no
cookies, no consent banner is required under GDPR or ePrivacy
regulations.

### Fonts

All fonts (Noto Sans) are self-hosted and served directly from
docs.legesher.io. No third-party font services are used, so no data
is shared with external providers when loading pages.

## VS Code Extension

### Basic Telemetry (Optional)

When enabled, we collect anonymous usage statistics:

- Extension activation events
- Language selection
- Error reports (no code content)

**Control:** `legesher.telemetry.enabled` setting (default: true)

### ML Training Data (Opt-in Only)

You can optionally help improve Legesher's translation models by sharing anonymous feedback when you change our translation suggestions.

#### What We Collect

- **Translation corrections**: When you change a Legesher suggestion (e.g., "media" → "promedio")
- **Code context**: High-level structure (function, variable, class)
- **Operation type**: Basic categorization (arithmetic, string manipulation, etc.)

#### What We DON'T Collect

- ❌ Your actual code or file contents
- ❌ File paths or directory structure
- ❌ Personal information or credentials
- ❌ User-defined variable or function names
- ❌ Literal values from your code

#### How It's Used

This data helps us:

1. Improve translation accuracy for your language
2. Understand how native speakers approach coding problems
3. Identify cultural and linguistic patterns in programming

#### Control

- **Setting:** `legesher.telemetry.contributeToMLTraining`
- **Default:** `false` (you must explicitly opt in)
- **Change anytime:** VS Code Settings → Search "Legesher ML Training"

## GDPR & CCPA Compliance

### Your Rights

Under GDPR and CCPA, you have the right to:

- **Access** your data (contact: <privacy@legesher.com>)
- **Delete** your data (contact: <privacy@legesher.com>)
- **Export** your data in machine-readable format
- **Opt out** at any time via settings

### Data Storage

- **Location:** Azure Application Insights (US region)
- **Retention:** 90 days for telemetry, anonymized ML data retained indefinitely
- **Security:** Encrypted in transit (TLS) and at rest

## Contact

Questions about privacy? Email us at **<privacy@legesher.com>**

---

**Last Updated:** March 5, 2026
