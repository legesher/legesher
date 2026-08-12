---
title: Privacy Policy — VS Code Extension & Documentation
description: Product-specific privacy practices for the Legesher VS Code extension and documentation site
---

**Last Updated:** April 20, 2026

> **Looking for the company-wide policy?** General terms — including your rights, how to contact us,
> retention periods, GDPR/CCPA/CPRA disclosures, and who we are — live in the
> [company-wide Privacy Policy at www.legesher.io/privacy](https://www.legesher.io/privacy).
> This page covers the product-specific details for the Legesher **VS Code extension** and this
> **documentation site** (`docs.legesher.io`).

## Scope of this page

This page supplements the [company-wide Privacy Policy](https://www.legesher.io/privacy) with details
specific to:

- The **Legesher VS Code extension**, published to the VS Code Marketplace
- The **Legesher documentation site** at `docs.legesher.io`

## VS Code Extension

### Local processing

Your source code is processed entirely **locally on your machine**. We never send your code to our
servers or any third-party services. All translation, git filters, and IntelliSense features run
100% offline.

### Basic telemetry (optional)

When enabled, we collect anonymous usage statistics to help us improve the product:

- Extension activation events
- Feature usage frequency (which commands you use)
- Language pack usage (which languages you translate to/from)
- Language changes: what prompted the change (choosing from the language picker, editing a setting,
  switching files), whether the setting that supplied the language came from your user, workspace, or
  folder settings, and whether the change succeeded — so we can tell a language you asked for and got
  from one you asked for and did not
- Language detection outcomes: whether a file's language was detected or the detector declined, and how
  strong the match was. Only the language code and the score are sent, never the tokens they came from
- Extension performance metrics (startup time, responsiveness)
- Error reports (crash reports, error messages — no code content)

**What we do NOT collect:**

- ❌ Your source code or file contents
- ❌ Personally identifiable information (name, email, IP address)
- ❌ Project names or file paths
- ❌ User-defined variable or function names
- ❌ Literal values from your code
- ❌ Sensitive data of any kind

**Control:** you can disable telemetry at any time in VS Code settings:

```json
{
  "legesher.telemetry.enabled": false
}
```

### ML training data (opt-in only)

You can optionally help improve Legesher's translation models by sharing anonymous feedback when you
change our translation suggestions.

#### What we collect

- **Translation corrections**: when you change a Legesher suggestion (e.g., "media" → "promedio")
- **Code context**: high-level structure (function, variable, class)
- **Operation type**: basic categorization (arithmetic, string manipulation, etc.)

#### How it's used

This data helps us:

1. Improve translation accuracy for your language
2. Understand how native speakers approach coding problems
3. Identify cultural and linguistic patterns in programming

#### Control

- **Setting:** `legesher.telemetry.contributeToMLTraining`
- **Default:** `false` (you must explicitly opt in)
- **Change anytime:** VS Code Settings → search "Legesher ML Training"

### Telemetry storage

- **Location:** Azure Application Insights (US region)
- **Retention:** 90 days for telemetry; anonymized ML training data retained indefinitely
- **Security:** industry-standard encryption (TLS 1.3 in transit, AES-256 at rest)

### VS Code's own telemetry

VS Code itself collects telemetry independently of Legesher. See the
[VS Code Privacy Statement](https://code.visualstudio.com/docs/supporting/faq#_microsoft-privacy-statement)
and VS Code telemetry settings.

## Documentation Site (docs.legesher.io)

### Hosting

This documentation site is hosted on [Vercel](https://vercel.com). Vercel processes standard server
access logs (IP addresses, request timestamps, URLs) as part of normal hosting operations. See
[Vercel's Privacy Policy](https://vercel.com/legal/privacy-policy) for details.

### Analytics

This site uses [Vercel Web Analytics](https://vercel.com/docs/analytics/privacy-policy), which is
designed to be privacy-compliant:

- **No cookies:** Vercel Web Analytics does not use cookies or any client-side storage
- **No personal identifiers:** visitors are identified by an anonymous hash that cannot be used to
  track individuals across sites
- **No cross-site tracking:** data cannot reconstruct browsing sessions or identify individual users
- **Aggregated data only:** we see page view counts, referrers, geolocation (country/region level),
  device type, and browser, all in aggregate

Data collected per page view: URL, referrer, geolocation (country/region), device OS, browser, device
type, and timestamp. No IP addresses, user agents, or personal information are stored.

Because Vercel Web Analytics collects no personal data and uses no cookies, no consent banner is
required under GDPR or ePrivacy regulations.

### Fonts

All fonts (Noto Sans) are self-hosted and served directly from `docs.legesher.io`. No third-party
font services are used, so no data is shared with external providers when loading pages.

## GDPR & CCPA Compliance

Your rights under GDPR, UK GDPR, CCPA/CPRA, and other regional privacy laws apply to both the
anonymous telemetry and the opt-in ML training data described above. In particular, you may:

- **Disable all telemetry** at any time via VS Code settings (see the _Control_ notes in each
  section above) — the fastest way to stop data collection entirely
- **Request access, correction, or deletion** of any data we have collected, by emailing
  [privacy@legesher.com](mailto:privacy@legesher.com)
- **Withdraw ML-training consent** by turning off `legesher.telemetry.contributeToMLTraining`;
  future collection stops immediately, and you can request deletion of historical anonymous
  contributions by emailing us
- **Lodge a complaint** with your local Data Protection Authority (EEA) or the
  [Information Commissioner's Office](https://ico.org.uk/make-a-complaint/) (UK) if you
  believe we have handled your data improperly

The full enumeration of your rights — including GDPR Articles 15–22, CCPA/CPRA categories, state
privacy laws (Virginia, Colorado, Connecticut, Utah, Nevada), international transfer basis,
retention periods, and who we are (Legesher Inc and Legesher Global Tech Limited) — lives in the
[company-wide Privacy Policy](https://www.legesher.io/privacy).

For privacy-specific questions about the extension or this docs site, email
[privacy@legesher.com](mailto:privacy@legesher.com).
