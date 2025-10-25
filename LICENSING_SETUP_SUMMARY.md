# Legesher Licensing Setup Summary

This document summarizes the multi-license structure that has been set up for the Legesher monorepo.

## Overview

Your repository now implements **Option 1: Source Available Monorepo with Mixed Licensing**, which allows you to:
- Keep the entire codebase public and visible on GitHub
- Have different license terms for different packages
- Build an open protocol while maintaining commercial features
- Accept community contributions to open source packages

## Files Created

### License Files

1. **[LICENSE](LICENSE)** (root)
   - Explains the multi-license structure
   - Provides overview of all package licenses
   - Sets default proprietary license for unlicensed code

2. **[libs/core/LICENSE](libs/core/LICENSE)** - MIT License
3. **[libs/i18n/LICENSE](libs/i18n/LICENSE)** - MIT License
4. **[libs/vs-code/LICENSE](libs/vs-code/LICENSE)** - MIT License
5. **[libs/legesher/LICENSE](libs/legesher/LICENSE)** - Dual License (MIT + Commercial)
6. **[libs/pride/LICENSE](libs/pride/LICENSE)** - Proprietary

### Updated Files

#### Root README.md
- Added license badges showing licensing for each package
- Added licensing section explaining the structure
- Added contributing section with clear guidelines
- Updated with Quick Start and project overview

#### Package pyproject.toml Files
All packages now include:
- `license` metadata (MIT, dual, or proprietary)
- `keywords` for better discoverability
- `classifiers` for PyPI compliance:
  - Development status
  - License information
  - Python version compatibility
  - Topic categorization
  - Operating system support

### Contributing Guidelines

**[CONTRIBUTING.md](CONTRIBUTING.md)** includes:
- License structure explanation
- Which packages accept contributions
- Development setup instructions
- Contributor License Agreement (CLA) terms
- Code of Conduct
- Package-specific guidelines
- Translation contribution process

### GitHub Templates

Created in `.github/`:

1. **[ISSUE_TEMPLATE/bug_report.yml](.github/ISSUE_TEMPLATE/bug_report.yml)**
   - Package selection
   - Reproduction steps
   - Environment details
   - Code of Conduct agreement

2. **[ISSUE_TEMPLATE/feature_request.yml](.github/ISSUE_TEMPLATE/feature_request.yml)**
   - License awareness checkbox
   - Problem statement and solution
   - Use case description
   - Contribution interest checkbox

3. **[ISSUE_TEMPLATE/license_question.yml](.github/ISSUE_TEMPLATE/license_question.yml)**
   - Question categorization
   - Use case selection
   - Contact information for commercial inquiries

4. **[ISSUE_TEMPLATE/config.yml](.github/ISSUE_TEMPLATE/config.yml)**
   - Links to Discussions, Docs
   - Contact links for sales and security

5. **[PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)**
   - License agreement checkboxes
   - Package affected selection
   - Testing requirements
   - Documentation checklist

## License Structure

### Open Source (MIT) - Builds Ecosystem
- **legesher-core** - Core translation engine
- **legesher-i18n** - Language data and dictionaries
- **legesher-vs-code** - Editor integration

**Purpose**: Build trust, encourage adoption, create community

### Dual License (MIT + Commercial) - Freemium Model
- **legesher** - Main CLI and library
  - Free tier: Local translation (MIT)
  - Premium tier: Cloud sync, teams, analytics (Commercial)

**Purpose**: Revenue generation while maintaining open protocol

### Proprietary (Source Available) - Premium Features
- **legesher-pride** - Community showcase

**Purpose**: Protect commercial features while maintaining transparency

## What This Protects

Even though code is public and visible:

1. **Copyright** - Automatic protection for all code
2. **License Terms** - Legal restrictions on use
3. **Trademarks** - "Legesher" brand protection
4. **Commercial Value** - Premium features require license
5. **Contribution Terms** - Clear CLA for contributors

## Business Model Support

### For Users
- **Free tier**: Full access to open protocol via MIT packages
- **Visibility**: Can see all code for security review
- **Clear upgrade path**: Understand premium features before buying

### For Your Business
- **Open protocol adoption**: MIT packages encourage widespread use
- **Revenue protection**: Commercial features legally protected
- **Conversion funnel**: Free users can see (but not use) premium features
- **Community contributions**: Accept PRs to open packages only

## Next Steps (Optional)

You may want to:

1. **Update email addresses** in LICENSE files (currently using placeholder emails like sales@legesher.com)
2. **Create actual pricing page** at legesher.io/pricing
3. **Set up API authentication** to enforce premium features
4. **Add security policy** (.github/SECURITY.md)
5. **Create package README files** with license badges
6. **Add changelog** for tracking releases
7. **Set up CI/CD** to verify license headers
8. **Create license FAQ** in documentation

## Publishing to PyPI

When ready to publish:

### Open Source Packages (core, i18n, vs-code)
- Can be published to PyPI immediately
- Will display MIT license
- Classifiers will show up correctly

### Dual-Licensed Package (legesher)
- Can be published to PyPI
- Free tier functionality available via PyPI
- Premium features gated by authentication
- PyPI listing will show dual license

### Proprietary Package (pride)
- **DO NOT publish to PyPI** (has "Private :: Do Not Upload" classifier)
- Distribute only to licensed customers
- Consider private package repository

## Legal Disclaimer

This setup provides a reasonable licensing structure, but:
- Consider consulting with a lawyer for your specific situation
- Update placeholder email addresses with real contact points
- Ensure you have trademark protection for "Legesher" if desired
- Review license terms with legal counsel before major release

## Questions?

- Licensing: legal@legesher.com
- Commercial: sales@legesher.com
- Security: security@legesher.com
- General: GitHub Discussions

---

**Setup completed on**: 2025-10-25
**Monorepo structure**: Ready for open source + commercial use
**Status**: Ready to accept contributions to open source packages
