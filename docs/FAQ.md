# Legesher FAQ

Frequently Asked Questions about Legesher - Code in Your Language

**Last Updated:** November 2025
**Version:** v0.1.0

---

## Table of Contents

- [General Questions](#general-questions)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [Technical Details](#technical-details)
- [Compatibility & Integration](#compatibility--integration)
- [Troubleshooting](#troubleshooting)

---

## General Questions

### What is Legesher?

Legesher enables developers to write code in their native language instead of English. It provides lossless,
bidirectional translation between your language and English, with full IDE support and git integration. Currently
supports Python with more languages planned.

### Why does this exist?

Programming languages require English keywords, creating barriers for non-English speakers. Legesher removes this
barrier while maintaining compatibility with the global Python ecosystem. Your code stays in your language locally but
integrates seamlessly with English-based tools and repositories.

### Who is this for?

Legesher is for developers who prefer to code in their native language, educators teaching programming in non-English
contexts, and teams working in multilingual environments. It's also for anyone who believes programming should be
accessible regardless of language background.

### Is it production-ready?

Version 0.1.0 is an early release focused on core functionality. It's suitable for learning, teaching, and small
projects. Production use is possible but consider it beta software. We're actively improving stability and performance
based on community feedback.

### What languages are supported?

Currently Spanish (Español) and Arabic (العربية) for Python. More language packs are in development. You can contribute
your language by creating a language pack following our contribution guide. See our
[Language Pack Guide](./LANGUAGE_PACK_GUIDE.md) for details.

---

## How It Works

### How does translation work?

Legesher uses token-based transformation to translate Python keywords, built-ins, and identifiers between languages. It
parses your code into tokens, maps them using language packs, and outputs valid Python. The process is reversible,
ensuring lossless round-trip translation. See [Architecture](./ARCHITECTURE.md) for technical details.

### Is it really lossless?

Yes. Translation is deterministic and bijective. Code translated from Spanish to English and back to Spanish produces
identical results. We maintain this through careful token mapping, whitespace preservation, and comprehensive testing.
Comments and strings in your language are preserved as-is.

### What about performance?

Translation adds minimal overhead. Typical translation time is under 100ms for most files. Git filter integration means
translation happens automatically during commits and checkouts. IDE support provides real-time translation without
noticeable lag for files under 10,000 lines.

### Does it work with my IDE?

Currently, we provide a VS Code extension with full language server support. This includes syntax highlighting,
autocomplete, go-to-definition, and error checking in your language. Support for PyCharm, Zed, and other editors is
planned. See [IDE Support](./IDE_SUPPORT.md) for setup instructions.

### How does git integration work?

Legesher uses git filters to automatically translate code during commits and checkouts. Your local files stay in your
language, but the repository stores canonical English. This ensures compatibility with CI/CD, code review tools, and
team members using different languages. See [Git Integration](./GIT_INTEGRATION.md) for setup.

---

## Getting Started

### How do I install it?

Install via pip: `pip install legesher`. For Spanish support: `pip install legesher-i18n-python-es`. Configure your
language preference with `legesher config set language es`. Then initialize git filters with `legesher git install`.
See our [Quick Start Guide](./QUICK_START.md) for complete instructions.

### Do I need to know English?

No. Legesher is designed so you can code entirely in your native language. Documentation, error messages, and IDE
support are available in supported languages. However, some Python ecosystem tools and libraries may have English
documentation that hasn't been translated yet.

### Can I use it with existing projects?

Yes. Legesher can translate existing English Python code to your language. Use `legesher translate` to convert files or
directories. The translation is reversible, so you can switch back if needed. Always test thoroughly and keep backups
when translating existing projects.

### What if my language isn't supported?

You can create a language pack! Our language pack system is designed for community contributions. You'll need to
translate Python keywords and built-ins, then follow our validation process. Most language packs take 10-20 hours to
complete. See [Contributing a Language](./CONTRIBUTING.md#language-packs) for guidance.

### Is there a cost?

Legesher is completely free and open source under the MIT License. All language packs are also free. There are no
premium features, subscriptions, or hidden costs. We believe programming accessibility should be free for everyone.

---

## Contributing

### How can I help?

Many ways! Contribute language packs, improve documentation, add tests, fix bugs, or help with IDE extensions. Check
our [Contributing Guide](./CONTRIBUTING.md) for detailed options. Even non-code contributions like testing, translation
reviews, and community support are valuable.

### Can I add my language?

Absolutely! We welcome new language packs. You'll create a package mapping Python keywords to your language, add tests,
and submit for review. The process includes linguistic review by native speakers and automated validation. See our
[Language Pack Guide](./LANGUAGE_PACK_GUIDE.md) for step-by-step instructions.

### Do I need to be a programmer?

Not necessarily. Language pack creation requires understanding Python keywords but not advanced programming. Native
language expertise is more important. Documentation translation, testing, and community support don't require
programming skills at all. We value diverse contributions.

### What's the review process like?

Pull requests receive automated checks first, then maintainer review. Language packs require linguistic review by
native speakers and technical validation. Most PRs receive initial feedback within 48 hours. We prioritize helpful
feedback and inclusive review practices. See [Code Review Guidelines](./CONTRIBUTING.md#code-review).

### How long does it take?

Small bug fixes: days. Language packs: 2-4 weeks including review. Major features: varies by scope. We're a
community-driven project, so timelines depend on reviewer availability. Active communication and thorough PRs speed up
the process significantly.

---

## Technical Details

### What Python versions are supported?

Python 3.8+ is supported. Each language pack specifies which Python versions it covers. Our version-aware system
handles Python 3.10+ features like match/case statements separately from older versions. We test against Python 3.8,
3.9, 3.10, 3.11, and 3.12.

### Does it support async/await?

Yes. All modern Python features including async/await, type hints, f-strings, walrus operator, and match/case
statements are fully supported. Language packs translate these keywords appropriately for each Python version.

### What about type hints?

Type hints work normally. Built-in types like `int`, `str`, `list` can be translated to your language. Custom types
and imports from `typing` module are preserved. Your IDE will provide type checking in your language with our language
server support.

### How does it handle comments?

Comments in your language are preserved exactly as written. They're not translated unless you explicitly request it.
This means you can document your code entirely in your native language. Docstrings work the same way and integrate with
documentation tools.

### What's the file size impact?

None on repository size since git stores English. Local translated files are typically identical size to English
equivalents. Translation metadata adds approximately 1-2% overhead. Language packs are small (typically under 100KB)
and only needed during development.

---

## Compatibility & Integration

### Does it work with pytest?

Yes. Tests written in your language run with pytest normally. Use `legesher test` which wraps pytest with translation
support, or configure pytest to use our plugin. Assertions, fixtures, and parametrization all work in your language.
See [Testing Guide](./TESTING.md) for examples.

### Can I use it in CI/CD?

Yes. CI/CD pipelines run against the English version in your repository, so no special configuration needed. If you
want to run tests in your language in CI, install Legesher and the appropriate language pack in your CI environment.
See [CI/CD Integration](./CI_CD.md) for examples.

### What about Docker?

Legesher works in Docker containers. Add it to your requirements.txt or Dockerfile. The translation layer adds minimal
overhead to container builds. Git filters work inside containers when configured. See our
[Docker examples](../examples/docker) for reference configurations.

### Does it work with Django/Flask?

Yes. Both Django and Flask projects work with Legesher. You can write views, models, and templates in your language.
Framework-specific commands may need wrapping, but core functionality is fully supported. We have examples for both
frameworks in our [examples directory](../examples/).

### GitHub Actions support?

Yes. GitHub Actions workflows work perfectly since they run against the English version in your repo. To run tests in
your language in Actions, add Legesher installation to your workflow. See our
[.github/workflows](../.github/workflows) for examples.

---

## Troubleshooting

### Translation not working

First, verify your language pack is installed: `pip list | grep legesher-i18n`. Check language configuration:
`legesher config get language`. Try translating a simple file manually: `legesher translate input.py -o output.py`. If
issues persist, run with verbose logging: `legesher translate --verbose`. See [Troubleshooting Guide](./TROUBLESHOOTING.md).

### Git filters not applying

Verify filters are configured: `git config --list | grep filter.legesher`. Reinitialize filters:
`legesher git install --force`. Check .gitattributes file exists and contains `*.py filter=legesher`. Try manually
staging a file to test. See [Git Filter Debugging](./GIT_INTEGRATION.md#debugging) for detailed steps.

### Import errors

Ensure all required packages are installed: `pip install legesher legesher-i18n-python-XX` (replace XX with your
language). Check Python version compatibility: `python --version`. Verify virtual environment if using one. Clear pip
cache if needed: `pip cache purge`. Reinstall if necessary.

### Version conflicts

Legesher requires specific versions of dependencies. Check compatibility: `pip check`. Update all Legesher packages
together: `pip install --upgrade legesher legesher-i18n-python-XX`. If using poetry or pipenv, regenerate lock files.
Report persistent conflicts as bugs.

### Where to get help?

Check our [documentation](./README.md) first. Search existing
[GitHub issues](https://github.com/legesher/legesher/issues). Join our community discussions on GitHub. File a new
issue with minimal reproduction steps if needed. For sensitive questions, contact maintainers via email listed in
[SECURITY.md](./SECURITY.md).

---

## Still Have Questions?

Check our complete [documentation](./README.md) or join our community discussions on
[GitHub](https://github.com/legesher/legesher). We're here to help make programming accessible in your language.

**Can't find your answer?** [Open an issue](https://github.com/legesher/legesher/issues/new) and we'll update this FAQ.
