# Legesher Monorepo Makefile
# ===========================
# Common commands for development, testing, and code generation.

.PHONY: help install generate generate-languages check-generated test test-all test-i18n test-core test-legesher test-language-server test-mcp lint format typecheck clean vscode-compile vscode-package

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
	@echo "  make check-generated      Verify generated files match source (for CI)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-i18n            Run i18n package tests"
	@echo "  make test-core            Run core package tests"
	@echo "  make test-legesher        Run legesher package tests"
	@echo "  make test-language-server Run language-server tests"
	@echo "  make test-mcp             Run MCP server tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run linters (ruff)"
	@echo "  make format               Format code (black, ruff)"
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
generate: generate-languages
	@echo "All code generation complete!"

# Generate TypeScript language definitions from languages.json
# Source: libs/i18n/legesher_i18n/languages.json
# Output: libs/vs-code/src/generated/languages.ts
generate-languages:
	@echo "Generating TypeScript from languages.json..."
	uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
	@echo "Done! Don't forget to rebuild the VS Code extension: make vscode-compile"

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

test-runtime:
	@echo "Running runtime tests..."
	cd libs/runtime && uv run pytest tests/ -v

# Test with coverage
test-coverage:
	@echo "Running tests with coverage..."
	uv run pytest libs/ --cov --cov-report=term-missing --cov-report=html

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@echo "Running linters..."
	uv run ruff check libs/

format:
	@echo "Formatting code..."
	uv run ruff check --fix libs/
	uv run black libs/

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
# This regenerates from source and compares to committed version
check-generated:
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
