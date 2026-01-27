# legesher-home - Claude Code Guide

This file provides guidance for working with the `legesher-home` package.

## Package Overview

**Version**: 0.1.0
**Status**: Minimal Scaffold
**Python**: >=3.10,<4.0

Digital home and community platform package. A welcoming space for the Legesher community.

## Concept

The "digital home" concept represents:

- A place where people can invite others into their own corners of the internet
- Community showcase for projects and tools built with Legesher
- Shared community resources and perspectives
- Ways to see through others' lenses using their tools or shared community tools

## Current State

The package is currently scaffolded but not implemented:

```text
libs/home/
├── legesher_home/
│   └── __init__.py    # Minimal package init
├── pyproject.toml
├── README.md
└── tests/
```

## Dependencies

- `legesher>=0.1.0,<0.2.0`
- `legesher-core>=0.1.0,<0.2.0`
- `legesher-i18n>=0.1.0,<0.2.0`

## Planned Features

The following features are planned for future development:

- **Community Showcase**: Highlight projects using Legesher
- **Shared Tools**: Community-contributed utilities and configurations
- **Perspectives**: See code through different cultural/linguistic lenses
- **Profiles**: Developer profiles with language preferences

## Development Notes

This package was renamed from `legesher-pride` to `legesher-home` (CORE-515).

When implementing features:

1. Follow the community-first design philosophy
2. Ensure accessibility across languages and cultures
3. Add tests in the `tests/` directory
4. Update documentation as features are added

## Related Issues

- **CORE-515**: Package refactoring (rename from `legesher-pride` complete)
