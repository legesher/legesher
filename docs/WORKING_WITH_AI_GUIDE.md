# Working with AI Assistants - Legesher Project Guide

**Last Updated**: 2025-10-25
**Purpose**: Best practices for using AI assistants with the Legesher monorepo

---

## Quick Start

**Most Important Things to Know:**

1. **CLAUDE.md is automatically loaded** - AI assistants already have access to it
2. **Reference specific sections** instead of asking vague questions
3. **Use slash commands** for common workflows (implement, architecture review, security check)
4. **Always mention the constraint** when relevant (Security, Privacy, Performance, Git Compatibility)
5. **Reference Linear issues** when implementing features

**Your Next Steps:**

1. Create `.claude/commands/` directory in your **repository root** with custom slash commands (see below)
2. Start conversations with context: `"I'm implementing [feature from Linear]. According to CLAUDE.md [relevant section]..."`
3. Keep CLAUDE.md open in a side panel for quick reference

**Note on Slash Commands:**
- Location: `.claude/commands/` in repository root (same level as `CLAUDE.md`)
- Git behavior: **Commit these to git** - they're project-specific, not user-specific
- Team benefit: Shared commands ensure consistent development practices

---

## Recommended Slash Commands

Create these files in `.claude/commands/` (in repository root) for quick access to common workflows.

**Setup:**
```bash
mkdir -p .claude/commands
# Then create the .md files below
# Commit them to git so your team can use them too
```

### `/architecture` - Architecture Discussions

**File: `.claude/commands/architecture.md`**

```markdown
You are helping review or discuss architectural decisions for the Legesher project.

Before responding:
1. Read the current architectural decisions in CLAUDE.md (Quick Reference > Key Architectural Decisions)
2. Review the relevant sections of CLAUDE.md for context
3. Check if this relates to any open issues in Linear workspace

When discussing changes:
- Reference the existing decision and rationale
- Explain trade-offs of the proposed change
- Consider impact on all 5 packages (core, i18n, legesher, vs-code, pride)
- Note which phase of the roadmap this would affect
- Consider the Important Constraints (Security, Privacy, Performance, Git Compatibility, etc.)

The user's architectural question or proposed change is:
```

---

### `/implement` - Feature Implementation

**File: `.claude/commands/implement.md`**

```markdown
You are helping implement a feature for the Legesher project.

IMPORTANT: Before starting implementation:
1. Check CLAUDE.md Project Status - understand current phase
2. Review Package Interdependencies to understand build order (Tier 1 → 2 → 3 → 4)
3. Check Important Constraints (Security, Privacy, Performance, etc.)
4. Follow the "Implementing a new feature" workflow in CLAUDE.md

Implementation requirements:
- Follow architectural decisions (no debates on settled topics)
- Write tests alongside implementation (even though test dirs are currently empty)
- Update package README.md as you implement
- Consider cross-package impacts
- Use Python >=3.13 features
- Follow security best practices

The feature to implement is:
```

---

### `/security-check` - Security Review

**File: `.claude/commands/security-check.md`**

```markdown
You are performing a security review for the Legesher project.

CRITICAL CONTEXT:
Legesher is a code translation tool that handles developers' source code. Security is paramount.

Before reviewing:
1. Read the Security constraint in CLAUDE.md (Important Constraints section)
2. Remember: Users may have proprietary code - privacy is critical
3. This tool must work offline (local-first approach)

Security checklist:
- [ ] Input validation (malformed code should fail gracefully)
- [ ] No code execution (never eval/exec translated code)
- [ ] Path traversal prevention (when reading language packs)
- [ ] Code injection prevention (in translation logic)
- [ ] File system access controls
- [ ] Privacy leaks (no data sent to cloud without explicit opt-in)
- [ ] Dependency vulnerabilities
- [ ] Error messages (don't leak sensitive paths or code)

The code or feature to review is:
```

---

## Best Practices

### 1. Start Conversations with Context

❌ **Don't:**
```
How do I add Spanish support?
```

✅ **Do:**
```
I'm adding a Spanish language pack for Python translation. According to CLAUDE.md, v0.1 milestone includes 3 language packs (ES, AR, ZH).
Following the "Adding a new language pack" workflow in CLAUDE.md,
what should the directory structure look like in libs/i18n/?
```

---

### 2. Reference Constraints When Relevant

```
I'm implementing the translator class. Given our Privacy constraint (local-first, cloud optional),
should I make the cloud translation an opt-in plugin system?
```

---

### 3. Use the Tier System

```
I want to add a utility function. Looking at Package Interdependencies,
should this go in Tier 1 (core) since multiple packages will use it?
```

---

### 4. Reference Milestones

```
This feature is part of v0.1 MVP milestone. According to CLAUDE.md,
v0.1 requires: basic translation, CLI, git integration, 3 language packs.
Are we on track?
```

---

## CLAUDE.md Quick Reference

### Most Useful Sections:

1. **Project Status** - Current phase and maturity
2. **Package Interdependencies** - Tier system and dependencies
3. **Important Constraints** - Security, Privacy, Performance, Git Compatibility
4. **Key Architectural Decisions** - Quick decision reference
5. **Common Workflows** - Step-by-step procedures
6. **Quick Reference > Key Documentation** - Links to all planning docs

### Important Constraints (Always Consider):

1. **Security**: Code translation tools handle source code - critical security practices required
2. **Privacy**: Local-first approach, cloud optional, never required
3. **Performance**: Real-time IDE translation requires fast AST transformation
4. **Git Compatibility**: All workflows must work seamlessly with canonical English storage
5. **Extensibility**: Design for multiple programming languages (starting with Python)
6. **IDE Agnostic**: VS Code first, but consider Zed, PyCharm, Cursor, Windsurf
7. **Python Versions**: Version-aware language packs support Python 3.x evolution

---

## Example Conversations

### Example 1: Feature Implementation

**User:**
```
I'm ready to start implementing. Let's work on the Token-Based Transformer in libs/core/.
```

**AI:**
```
Great! The Token-Based Transformer is in libs/core/ (Tier 1 - Foundation). According to CLAUDE.md's Key Architectural Decisions, we're using "Token-based for MVP, Tree-sitter for production".

This requires:
1. Simple keyword mapping without full parsing
2. Whitespace preservation
3. Comment preservation
4. Basic error handling

Should we break this down into subtasks?
```

---

### Example 2: Architecture Discussion

**User:**
```
/architecture We're planning token-based for MVP, but when should we switch to Tree-sitter?
```

**AI:**
```
According to your Key Architectural Decisions: "AST Transformation: Token-based for MVP, Tree-sitter for production"

The switch should happen after v0.1 MVP is complete and stable:
- Core token-based transformer is working
- Basic language packs are complete
- CLI is functional

Recommendation: Stick with token-based for v0.1 MVP, plan Tree-sitter migration for v0.5+.
This aligns with your Performance constraint (real-time IDE translation needs).

Reasons to wait:
- Token-based is simpler and faster to develop
- Proves the concept first
- Tree-sitter adds complexity best handled after MVP validation
```

---

## Best Practices Summary

| Scenario | Best Approach | Example |
|----------|---------------|---------|
| **Architecture Discussion** | Slash command `/architecture` | `/architecture Should we switch to Tree-sitter now?` |
| **Feature Implementation** | Slash command `/implement` | `/implement Version-Aware Language Pack System` |
| **Quick Question** | Reference CLAUDE.md section | `Per Key Architectural Decisions, we use git filters. How?` |
| **Security Review** | Slash command `/security-check` | `/security-check Review the file upload handler` |
| **Package-specific Work** | IDE selection + tier reference | `In libs/core (Tier 1), implementing transformer` |

---

## Additional Resources

**Key Documentation Files:**
- [CLAUDE.md](../CLAUDE.md) - AI assistant guidance (loaded automatically)
- [Getting Started](./src/content/docs/index.mdx) - Project overview
- [Package READMEs](../libs/) - Individual package documentation
- Architecture documentation (in development)

---

## Quick Win

**Create the commands directory and start with `/implement`:**

```bash
mkdir -p .claude/commands
# Copy the /implement command template from above into:
# .claude/commands/implement.md
# Then commit to git so your team can use it
git add .claude/commands/
git commit -m "feat: add /implement slash command for AI-assisted development"
```

This will be your most-used command during active development.

The key to effective AI assistance is **providing context**. The more context you provide upfront, the better the AI response will be. CLAUDE.md is designed to give AI assistants everything they need to help you effectively.
