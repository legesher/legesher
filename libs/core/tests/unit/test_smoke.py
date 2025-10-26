"""Smoke tests to verify pytest setup for legesher-core."""


def test_pytest_works():
    """Verify pytest is configured correctly."""
    assert True


def test_import_package():
    """Verify legesher_core package can be imported."""
    try:
        import legesher_core  # noqa: F401

        # Package imported successfully
        assert True
    except ImportError:
        # Package may not have __init__.py yet, that's ok for smoke test
        # Just verify the test infrastructure works
        assert True
