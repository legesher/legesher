# Security Policy

## Supported Versions

We take security seriously across all Legesher packages. The table below shows which
versions are currently receiving security updates:

| Package                  | Version | Supported          |
| ------------------------ | ------- | ------------------ |
| legesher-core            | 0.5.x   | :white_check_mark: |
| legesher-i18n            | 0.5.x   | :white_check_mark: |
| legesher (CLI)           | 0.5.x   | :white_check_mark: |
| legesher-language-server | 0.1.x   | :white_check_mark: |
| legesher-vs-code         | 0.1.x   | :white_check_mark: |
| legesher-home            | 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We appreciate responsible disclosure of security vulnerabilities. If you discover a security issue, please follow these steps:

### 1. Do NOT Publicly Disclose

**Please do not:**

- Open a public GitHub issue
- Discuss the vulnerability in public forums
- Share exploit code publicly

### 2. Report Privately

**Preferred method - GitHub Security Advisory:**

1. Go to the [Security tab](https://github.com/legesher/legesher/security) of this repository
2. Click "Report a vulnerability"
3. Fill out the private security advisory form

**Alternative method - Email:**
Send details to: **<security@legesher.com>**

Include in your report:

- Description of the vulnerability
- Steps to reproduce
- Affected versions/packages
- Potential impact
- Suggested fix (if available)

### 3. What to Expect

**Timeline:**

- **24 hours**: Initial acknowledgment of your report
- **72 hours**: Preliminary assessment and severity classification
- **7 days**: Detailed response with timeline for fix
- **30-90 days**: Target for patch release (depending on severity)

**Communication:**

- We will keep you informed throughout the process
- We will credit you in the security advisory (unless you prefer anonymity)
- We may request additional information or clarification

### 4. Coordinated Disclosure

- We follow a **90-day disclosure deadline** from initial report
- We will work with you to agree on disclosure timing
- Public disclosure will happen after patch is released
- We will credit researchers in our security advisories

## Security Vulnerability Response

### Critical Vulnerabilities

- **Immediate response** within 24 hours
- **Emergency patches** released as soon as possible
- **Public disclosure** after patch is available

### High/Medium Vulnerabilities

- **Assessment** within 72 hours
- **Patches** included in next scheduled release or dedicated security release
- **Public disclosure** coordinated with patch release

### Low Vulnerabilities

- **Assessment** within 1 week
- **Fixes** included in next regular release
- **Public disclosure** with release notes

## Security Best Practices

### For Users

When using Legesher packages:

1. **Keep packages updated** to the latest versions
2. **Review dependencies** regularly for known vulnerabilities
3. **Use official releases** from PyPI or GitHub releases only
4. **Validate signatures** when available
5. **Follow principle of least privilege** for API keys and credentials

### For Contributors

When contributing to Legesher:

1. **Never commit secrets** (API keys, passwords, tokens)
2. **Validate all inputs** to prevent injection attacks
3. **Use parameterized queries** for database operations
4. **Follow secure coding guidelines** for Python
5. **Run security linters** (bandit, safety) on your changes

### For Enterprise Users

Additional recommendations:

1. **Internal security review** before deployment
2. **Monitor security advisories** for all dependencies
3. **Implement web application firewalls** for cloud deployments
4. **Regular security audits** of your Legesher implementation
5. **Contact us** for enterprise security assessments

## Known Security Considerations

### Multi-License Structure

- **Open source packages** (core, i18n, vs-code) are publicly auditable
- **Proprietary packages** (home) source code is visible but usage is restricted
- **All packages** are subject to the same security review standards

### Data Handling

- **Local translation**: No data leaves your machine (free tier)
- **Cloud features**: Data transmitted to Legesher servers (premium tier)
- **Encryption**: All cloud communications use TLS 1.3+
- **Privacy**: See our [Privacy Policy](https://legesher.io/privacy) for details

### VS Code Extension

- **Permissions**: Extension requests minimal VS Code API permissions
- **No telemetry** in open source version (configurable in premium)
- **Local execution**: Code analysis happens locally by default

## Security Contacts

- **Security Team**: <security@legesher.com>
- **Response Time**: Within 24 hours for critical issues

## Bug Bounty Program

We currently do not have a formal bug bounty program. However:

- We greatly appreciate responsible disclosure
- Contributors will be publicly credited (if desired)
- For significant vulnerabilities, we may offer rewards on a case-by-case basis
- Contact <security@legesher.com> to discuss

## Past Security Advisories

No security advisories have been published yet. When we do publish them, they will be listed here and at:

- <https://github.com/legesher/legesher/security/advisories>

## Compliance and Certifications

We are working towards:

- SOC 2 Type II compliance (for cloud services)
- GDPR compliance (data privacy)
- Regular third-party security audits

Current status updates available at: <https://legesher.io/security>

## Security-Related Dependencies

We monitor dependencies using:

- GitHub Dependabot
- Safety CLI for Python packages
- Regular dependency audits

Dependency security updates are prioritized and applied promptly.

## Questions?

For general security questions (not vulnerabilities):

- GitHub Discussions: [Security category](https://github.com/legesher/legesher/discussions/categories/security)
- Email: <security@legesher.com>

Thank you for helping keep Legesher and our community safe!

---

**Last updated**: 2026-02-25
**Version**: 1.0
