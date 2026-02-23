---
title: Privacy Policy
description: Legesher privacy policy and data collection practices
---

# Privacy Policy

## Overview

Legesher is committed to protecting your privacy. This policy explains what data we collect and how we use it.

## Data Collection

### Basic Telemetry (Optional)

When enabled, we collect anonymous usage statistics:

- Extension activation events
- Language selection
- Error reports (no code content)

**Control:** `legesher.telemetry.enabled` setting (default: true)

### ML Training Data (Opt-in Only) {#ml-training}

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

**Last Updated:** December 2, 2025
