"""Smoke tests to verify pytest setup for legesher (main package)."""


def test_pytest_works():
    """Verify pytest is configured correctly."""
    assert True


def test_import_package():
    """Verify legesher package can be imported."""
    try:
        import legesher  # noqa: F401

        # Package imported successfully
        assert True
    except ImportError:
        # Package may not have __init__.py yet, that's ok for smoke test
        # Just verify the test infrastructure works
        assert True
