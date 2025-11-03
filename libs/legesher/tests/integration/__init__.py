"""Integration tests for Legesher CLI.

This package contains comprehensive integration tests that verify the complete
functionality of the Legesher CLI tool, including:

- End-to-end translation workflows
- Semantic equivalence verification
- Complex code pattern handling
- Directory operations
- Real language pack integration
- Performance characteristics

Test Modules:
    test_cli_integration: Comprehensive CLI integration tests with semantic equivalence

Coverage Target: 85%+ of integration paths

Usage:
    # Run all integration tests
    pytest tests/integration/

    # Run specific test class
    pytest tests/integration/test_cli_integration.py::TestSemanticEquivalence

    # Run excluding slow tests
    pytest tests/integration/ -m "not slow"

    # Run with coverage
    pytest tests/integration/ --cov=legesher --cov-report=html
"""
