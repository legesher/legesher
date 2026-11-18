"""Unit tests for error_handler module."""

import sys
import io
from unittest.mock import Mock, patch

from legesher.runtime.error_handler import (
    LegesherErrorHandler,
    install_error_handler,
)
from legesher.runtime.source_mapper import (
    get_source_mapper,
    reset_source_mapper,
)


class TestLegesherErrorHandler:
    """Test LegesherErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_source_mapper()
        self.handler = LegesherErrorHandler("es")
        self.mapper = get_source_mapper()

    def test_initialization(self):
        """Test error handler initialization."""
        handler = LegesherErrorHandler("es")

        assert handler.language == "es"
        assert handler.source_mapper is not None
        assert handler.exception_names == {}
        assert handler.message_templates == {}

    def test_translate_message_mvp(self):
        """Test message translation (MVP: returns English)."""
        message = "name x is not defined"
        result = self.handler._translate_message(message)
        assert result == message

    def test_format_exception_returns_string(self):
        """Test that format_exception returns a formatted string."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            exc_type = type(e)
            exc_value = e
            exc_traceback = e.__traceback__

            result = self.handler.format_exception(exc_type, exc_value, exc_traceback)

        assert isinstance(result, str)
        assert "Traceback (most recent call last):" in result
        assert "ValueError" in result
        assert "test error" in result


class TestInstallErrorHandler:
    """Test install_error_handler function."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_source_mapper()
        self.original_excepthook = sys.excepthook

    def teardown_method(self):
        """Restore original excepthook."""
        sys.excepthook = self.original_excepthook

    def test_install_with_explicit_language(self):
        """Test installing error handler with explicit language."""
        handler = install_error_handler("es")

        assert isinstance(handler, LegesherErrorHandler)
        assert handler.language == "es"
        # Check that excepthook is a function (the wrapper function)
        assert callable(sys.excepthook)

    @patch("legesher.runtime.error_handler.LegesherConfig.load")
    def test_install_from_config(self, mock_load):
        """Test installing error handler from project config."""
        mock_config = Mock()
        mock_config.language = "ar"
        mock_load.return_value = mock_config

        handler = install_error_handler()

        assert handler.language == "ar"
        mock_load.assert_called_once()

    @patch("legesher.runtime.error_handler.LegesherConfig.load")
    def test_install_from_config_uses_config_language(self, mock_load):
        """Test installing without explicit language uses config."""
        mock_config = Mock()
        mock_config.language = "fr"
        mock_load.return_value = mock_config

        handler = install_error_handler()

        assert handler.language == "fr"


class TestErrorHandlerIntegration:
    """Integration tests for error handler with source mapper."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_source_mapper()
        self.handler = LegesherErrorHandler("es")
        self.mapper = get_source_mapper()

    def test_error_shows_native_source_code(self):
        """Test that errors show native language source code."""
        native_source = "si verdad:\n    imprimir(hola)"
        english_source = "if True:\n    print(hello)"

        self.mapper.register_mapping("test_prog.py", native_source, english_source)

        native_line = self.mapper.get_native_source_line("test_prog.py", 2)

        assert "imprimir" in native_line

    def test_excepthook_integration(self):
        """Test that installed handler catches exceptions."""
        captured_output = io.StringIO()

        install_error_handler("es")

        old_stderr = sys.stderr
        sys.stderr = captured_output

        try:
            try:
                raise ValueError("test exception")
            except ValueError as e:
                sys.excepthook(type(e), e, e.__traceback__)
        finally:
            sys.stderr = old_stderr

        output = captured_output.getvalue()

        assert "Traceback" in output
        assert "ValueError" in output
        assert "test exception" in output
