# Legesher Monorepo Makefile
# ===========================
# Common commands for development, testing, and code generation.

.PHONY: help install generate generate-languages generate-docs generate-schema-reference check-generated check-generated-languages check-generated-docs check-generated-schema-reference test test-all test-i18n test-core test-legesher test-language-server test-mcp test-mcp-scheduled test-runtime bench lint format typecheck clean vscode-compile vscode-package

# Default target
help:
	@echo "Legesher Monorepo Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install              Install all dependencies (uv sync)"
	@echo ""
	@echo "Code Generation:"
	@echo "  make generate             Generate all derived files"
	@echo "  make generate-languages   Generate TypeScript from languages.json"
	@echo "  make generate-docs        Generate docs snippet/highlight artifacts (docs/generated)"
	@echo "  make generate-schema-reference  Generate the i18n schema v2 reference from the SQL"
	@echo "  make check-generated      Verify generated files match source (for CI)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-i18n            Run i18n package tests"
	@echo "  make test-core            Run core package tests"
	@echo "  make test-legesher        Run legesher package tests"
	@echo "  make test-language-server Run language-server tests"
	@echo "  make test-mcp             Run MCP server tests"
	@echo "  make test-mcp-scheduled   Run release-tier MCP suites (all packs, wheel spawn)"
	@echo "  make test-runtime         Run runtime package tests"
	@echo "  make bench                Run the pytest-benchmark suites with timing on"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run linters (ruff)"
	@echo "  make format               Format code (ruff)"
	@echo "  make typecheck            Run type checking (mypy)"
	@echo ""
	@echo "VS Code Extension:"
	@echo "  make vscode-compile       Compile VS Code extension"
	@echo "  make vscode-package       Package VS Code extension (.vsix)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                Clean build artifacts"

# ============================================================================
# Setup
# ============================================================================

install:
	uv sync --all-extras

# ============================================================================
# Code Generation
# ============================================================================

# Generate all derived files from source of truth
generate: generate-languages generate-docs generate-schema-reference
	@echo "All code generation complete!"

# Generate TypeScript language definitions from languages.json
# Source: libs/i18n/legesher_i18n/languages.json
# Output: libs/vs-code/src/generated/languages.ts
generate-languages:
	@echo "Generating TypeScript from languages.json..."
	uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
	@echo "Done! Don't forget to rebuild the VS Code extension: make vscode-compile"

# Generate the docs site's snippet/highlight artifacts
# Source: docs/snippets/*.py + shipped packs + languages.json (no translations.db needed)
# Output: docs/generated/
generate-docs:
	@echo "Generating docs snippet artifacts..."
	uv run python docs/scripts/generate_snippets.py --snippets docs/snippets --out docs/generated
	@echo "Done!"

# Generate the translations schema v2 reference (CORE-2232)
# Source: libs/i18n/legesher_i18n/db/schema_v2.sql (structure, parsed as text)
#       + libs/i18n/legesher_i18n/db/schema_v2.descriptions.yml (prose)
# Output: libs/i18n/docs/schema-v2-reference.md (no translations.db needed)
# Refuses, naming the offender, when the SQL and the descriptions disagree.
generate-schema-reference:
	@echo "Generating the schema v2 reference..."
	uv run python libs/i18n/scripts/generate_schema_reference.py
	@echo "Done!"

# ============================================================================
# Testing
# ============================================================================

# Run all tests across the monorepo
test: test-i18n test-core test-legesher test-language-server test-mcp test-runtime
	@echo "All tests complete!"

test-all: test

# Individual package tests
test-i18n:
	@echo "Running i18n tests..."
	cd libs/i18n && uv run pytest tests/ -v

test-core:
	@echo "Running core tests..."
	cd libs/core && uv run pytest tests/ -v

test-legesher:
	@echo "Running legesher tests..."
	cd libs/legesher && uv run pytest tests/ -v

test-language-server:
	@echo "Running language-server tests..."
	cd libs/language-server && uv run pytest tests/ -v

test-mcp:
	@echo "Running MCP server tests..."
	cd libs/mcp && uv run pytest tests/ -v

# Release-tier MCP suites: the all-packs round-trip sweep (CORE-1745) and the
# clean-environment wheel spawn test (CORE-1746). Excluded from `test-mcp`
# because they build wheels and sweep every pack. release-mcp.yml runs them
# as the release gate (CORE-626); this target is the local equivalent, so run
# it green before cutting a legesher-mcp release.
test-mcp-scheduled:
	@echo "Running scheduled (release-tier) MCP suites..."
	cd libs/mcp && uv run pytest tests/ -v -m scheduled

test-runtime:
	@echo "Running runtime tests..."
	cd libs/runtime && uv run pytest tests/ -v

# Test with coverage
test-coverage:
	@echo "Running tests with coverage..."
	uv run pytest libs/ --benchmark-disable --cov --cov-report=term-missing --cov-report=html

# Benchmarks are opt-in (CORE-2129). `--benchmark-disable` in the core and
# legesher pytest addopts runs each benchmark once as a plain test, so the
# per-commit suites stay fast and assert behaviour rather than timing. This
# target turns the timing back on, runs only the benchmarks, and autosaves
# the results under .benchmarks/ (gitignored) for `pytest-benchmark compare`.
# One invocation per package: both suites live in a `tests` package, and a
# single pytest run would import the second `tests.benchmarks` as the first.
bench:
	@echo "Running benchmarks (timing on, autosave to .benchmarks/)..."
	cd libs/core && uv run pytest tests/benchmarks/ --benchmark-enable --benchmark-only --benchmark-autosave
	cd libs/legesher && uv run pytest tests/benchmarks/ --benchmark-enable --benchmark-only --benchmark-autosave

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@echo "Running linters..."
	uv run ruff check libs/

format:
	@echo "Formatting code..."
	uv run ruff check --fix libs/
	uv run ruff format libs/

typecheck:
	@echo "Running type checker..."
	uv run mypy libs/core libs/i18n libs/legesher libs/language-server libs/mcp

# ============================================================================
# VS Code Extension
# ============================================================================

vscode-compile:
	@echo "Compiling VS Code extension..."
	cd libs/vs-code && npm run compile

vscode-compile-prod:
	@echo "Compiling VS Code extension (production)..."
	cd libs/vs-code && npm run compile:prod

vscode-package:
	@echo "Packaging VS Code extension..."
	cd libs/vs-code && npm run package

vscode-watch:
	@echo "Starting VS Code extension watch mode..."
	cd libs/vs-code && npm run watch

# ============================================================================
# Utilities
# ============================================================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf libs/vs-code/out 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	@echo "Clean complete!"

# Verify generated files are up-to-date (for CI)
# This regenerates from source and compares to committed version.
# Three parts: the language-registry artifacts (needs the local
# translations.db), the docs/generated artifacts (DB-free), and the schema
# v2 reference (DB-free).
check-generated: check-generated-languages check-generated-docs check-generated-schema-reference

# The control-plane DB is git-ignored (maintainer checkouts only), and the
# generator refuses to run without it (CORE-1887) — so in a DB-less clone
# this half skips cleanly instead of failing before the docs half runs.
TRANSLATIONS_DB := libs/i18n/legesher_i18n/db/translations.db

check-generated-languages:
ifeq ($(wildcard $(TRANSLATIONS_DB)),)
	@echo "SKIP: $(TRANSLATIONS_DB) not present (DB-less clone) — cannot regenerate the language registry (CORE-1887); skipping its drift check."
else
	@echo "Checking if generated files are up-to-date..."
	@cp libs/vs-code/src/generated/languages.ts /tmp/languages.ts.committed
	@$(MAKE) generate-languages > /dev/null 2>&1
	@if diff -q libs/vs-code/src/generated/languages.ts /tmp/languages.ts.committed > /dev/null 2>&1; then \
		echo "Generated files are up-to-date!"; \
		cp /tmp/languages.ts.committed libs/vs-code/src/generated/languages.ts; \
	else \
		echo "ERROR: Generated files are out of date!"; \
		echo "  Source: libs/i18n/legesher_i18n/languages.json"; \
		echo "  Generated: libs/vs-code/src/generated/languages.ts"; \
		echo ""; \
		echo "Run 'make generate' and commit the changes."; \
		cp /tmp/languages.ts.committed libs/vs-code/src/generated/languages.ts; \
		exit 1; \
	fi
endif

# Drift gate for docs/generated (CORE-2044): the docs site's snippet and
# highlight artifacts are derived from docs/snippets/*.py plus the shipped
# packs and languages.json, but nothing failed when the source moved and the
# committed artifacts did not (the PR #151 highlight-terms drift was caught
# by eye). Regenerates into a temp dir and diffs — read-only on the tree,
# and DB-free (unlike the registry half above), so it runs in a fresh clone.
check-generated-docs:
	@echo "Checking if docs/generated is up-to-date..."
	@tmp=$$(mktemp -d); \
	if ! uv run python docs/scripts/generate_snippets.py --snippets docs/snippets --out "$$tmp/out" > "$$tmp/regen.log" 2>&1; then \
		echo "ERROR: docs snippet regeneration failed:"; \
		cat "$$tmp/regen.log"; \
		rm -rf "$$tmp"; \
		exit 1; \
	fi; \
	if diff -r "$$tmp/out" docs/generated > /dev/null 2>&1; then \
		echo "docs/generated is up-to-date!"; \
		rm -rf "$$tmp"; \
	else \
		echo "ERROR: docs/generated is out of date!"; \
		echo "  Source: docs/snippets/ + shipped language packs + languages.json"; \
		echo "  Generated: docs/generated/"; \
		diff -r -q "$$tmp/out" docs/generated || true; \
		echo ""; \
		echo "Run 'make generate-docs' and commit the changes."; \
		rm -rf "$$tmp"; \
		exit 1; \
	fi

# Drift gate for the schema v2 reference (CORE-2232): the last hand-written
# schema reference rotted because nothing failed when schema_v2.sql moved and
# the prose did not. Regenerates into a temp dir and diffs, read-only on the
# tree and DB-free (the SQL is parsed as text), so it runs in a fresh clone.
# A regeneration failure is the other half of the gate: the generator refuses
# when the SQL and its descriptions disagree, and names the offender. The
# EXIT trap removes the temp dir on every path, including an interrupt.
SCHEMA_REFERENCE := libs/i18n/docs/schema-v2-reference.md

check-generated-schema-reference:
	@echo "Checking if $(SCHEMA_REFERENCE) is up-to-date..."
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	if ! uv run python libs/i18n/scripts/generate_schema_reference.py --out "$$tmp" > "$$tmp/regen.log" 2>&1; then \
		echo "ERROR: schema reference regeneration failed:"; \
		cat "$$tmp/regen.log"; \
		exit 1; \
	fi; \
	if diff -q "$$tmp/schema-v2-reference.md" $(SCHEMA_REFERENCE) > /dev/null 2>&1; then \
		echo "$(SCHEMA_REFERENCE) is up-to-date!"; \
	else \
		echo "ERROR: $(SCHEMA_REFERENCE) is out of date!"; \
		echo "  Source: libs/i18n/legesher_i18n/db/schema_v2.sql + schema_v2.descriptions.yml"; \
		echo "  Generated: $(SCHEMA_REFERENCE)"; \
		diff -u $(SCHEMA_REFERENCE) "$$tmp/schema-v2-reference.md" || true; \
		echo ""; \
		echo "Run 'make generate-schema-reference' and commit the changes."; \
		exit 1; \
	fi
