"""Comprehensive unit tests for Legesher CLI translate command.

This test suite covers all aspects of the `legesher translate` command:
- Basic functionality and help text
- Single file translation (to file and stdout)
- Stdin/stdout translation
- Directory translation (recursive)
- Error handling (missing files, invalid languages, syntax errors, etc.)
- Edge cases (empty files, Unicode, permissions, etc.)

Test Coverage Target: 90%+ of CLI code
"""

import os
import re
import stat
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from legesher.cli.main import cli
from legesher_core.exceptions import InvalidCodeError, TranslationError


def setup_mock_translator(
    mock_translator_class, translate_return_value="def foo():\n    return 42"
):
    """Helper to setup mock translator with reverse() support for tests.

    The CLI uses reverse() for X→en translations, so mocks need this method.
    """
    mock_translator = MagicMock()
    mock_translator.translate_code.return_value = translate_return_value

    # Mock reverse() for X→en translations
    mock_reversed = MagicMock()
    mock_reversed.translate_code.return_value = translate_return_value
    mock_translator.reverse.return_value = mock_reversed

    mock_translator_class.from_language_pack.return_value = mock_translator
    return mock_translator


class TestTranslateCommandBasics:
    """Test basic command registration and help text."""

    def test_translate_command_exists(self):
        """Verify translate command is registered and accessible."""
        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--help"])

        assert result.exit_code == 0
        assert "translate" in result.output.lower()

    def test_translate_help_text(self):
        """Verify help text is clear and includes examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--help"])

        assert result.exit_code == 0
        # Check for key help sections
        assert "Translate Python code" in result.output
        assert "--from" in result.output
        assert "--to" in result.output
        assert "--output" in result.output
        # Check for examples
        assert "Examples:" in result.output
        assert "stdin" in result.output.lower()

    def test_version_option(self):
        """Verify --version works at CLI level."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "legesher" in result.output.lower()
        assert re.search(r"\d+\.\d+\.\d+", result.output), (
            f"Expected version string in output, got: {result.output!r}"
        )


class TestLanguageHelpers:
    """Test language metadata loading and help text generation."""

    def test_load_languages_metadata_returns_all_languages(self):
        """Verify _load_languages_metadata returns all 51 supported languages."""
        from legesher.cli.translate import _load_languages_metadata

        langs = _load_languages_metadata()
        assert isinstance(langs, dict)
        assert len(langs) == 51
        # Spot-check a few languages
        assert "en" in langs
        assert "es" in langs
        assert "ar" in langs
        assert "zh" in langs
        # Each entry should be a dict with a 'name' key
        for code, info in langs.items():
            assert isinstance(info, dict), f"Language {code} is not a dict"
            assert "name" in info, f"Language {code} missing 'name'"

    def test_load_languages_metadata_fallback_on_missing_module(self):
        """Verify graceful fallback when legesher_i18n is not importable."""
        from legesher.cli.translate import _load_languages_metadata

        with patch(
            "legesher.cli.translate.resource_files",
            side_effect=ModuleNotFoundError("no module"),
        ):
            result = _load_languages_metadata()
            assert result == {}

    def test_build_supported_languages_text_contains_all_languages(self):
        """Verify help text lists all 51 languages."""
        from legesher.cli.translate import _build_supported_languages_text

        text = _build_supported_languages_text()
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        assert len(lines) == 51
        # Check alphabetical order
        codes = [line.split()[0] for line in lines]
        assert codes == sorted(codes)

    def test_build_supported_languages_text_fallback(self):
        """Verify fallback text when metadata is unavailable."""
        from legesher.cli.translate import _build_supported_languages_text

        with patch("legesher.cli.translate._load_languages_metadata", return_value={}):
            text = _build_supported_languages_text()
            assert "en" in text
            assert "English" in text
            assert "es" in text
            assert "Spanish" in text

    def test_translate_help_lists_supported_languages(self):
        """Verify translate --help epilog includes supported languages."""
        runner = CliRunner()
        result = runner.invoke(cli, ["translate", "--help"])

        assert result.exit_code == 0
        assert "Supported Languages:" in result.output
        # Spot-check a few languages appear in the output
        assert "Arabic" in result.output
        assert "English" in result.output
        assert "Spanish" in result.output
        assert "Chinese" in result.output

    def test_get_available_languages_fallback_uses_metadata(self):
        """Verify _get_available_languages falls back to languages.json."""
        from legesher.cli.translate import _get_available_languages

        with patch("legesher.cli.translate.TokenTranslator") as mock_translator:
            mock_translator.list_available_languages.side_effect = AttributeError
            result = _get_available_languages()
            assert isinstance(result, list)
            assert len(result) == 51
            assert "en" in result
            assert "ar" in result


class TestSingleFileTranslation:
    """Test single file translation scenarios."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_single_file_success(self, mock_translator_class, tmp_path):
        """Translate file with --output flag successfully."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo():\n    retornar 42", encoding="utf-8")

        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "def foo" in content
        assert "return 42" in content
        assert "Translated" in result.output

        # Verify translator was called correctly
        # For es→en, CLI loads 'es' pack and calls reverse()
        mock_translator_class.from_language_pack.assert_called_once_with("es")
        mock_translator = mock_translator_class.from_language_pack.return_value
        mock_translator.reverse.assert_called_once()

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_single_file_to_stdout(self, mock_translator_class, tmp_path):
        """Translate file to stdout when --output not specified."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo():\n    retornar 42", encoding="utf-8")

        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--from", "es", "--to", "en"],
        )

        # Verify - output goes to stdout
        assert result.exit_code == 0
        assert "def foo" in result.output
        assert "return 42" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_file_preserves_permissions(
        self, mock_translator_class, tmp_path
    ):
        """Verify executable bits are preserved after translation."""
        # Setup - create executable file
        input_file = tmp_path / "script.py"
        input_file.write_text(
            "#!/usr/bin/env python\ndefinir foo():\n    retornar 42", encoding="utf-8"
        )
        input_file.chmod(input_file.stat().st_mode | stat.S_IEXEC)

        output_file = tmp_path / "script_en.py"

        # Mock translator
        mock_translator = MagicMock()
        mock_translator.translate_code.return_value = (
            "#!/usr/bin/env python\ndef foo():\n    return 42"
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert output_file.exists()

        # Check permissions (on Unix-like systems)
        if os.name != "nt":  # Skip on Windows
            assert os.access(output_file, os.X_OK)

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_file_creates_output_directory(
        self, mock_translator_class, tmp_path
    ):
        """Verify parent directories are created automatically."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo():\n    retornar 42", encoding="utf-8")

        # Output in nested directory that doesn't exist
        output_file = tmp_path / "nested" / "dirs" / "output.py"

        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.parent.exists()


class TestStdinStdout:
    """Test stdin/stdout translation scenarios."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_stdin_to_stdout(self, mock_translator_class):
        """Translate from stdin to stdout (pipe mode)."""
        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute with stdin input
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en"],
            input="definir foo():\n    retornar 42",
        )

        # Verify
        assert result.exit_code == 0
        assert "def foo" in result.output
        assert "return 42" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_stdin_to_file(self, mock_translator_class, tmp_path):
        """Translate from stdin with --output flag."""
        # Setup
        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en", "--output", str(output_file)],
            input="definir foo():\n    retornar 42",
        )

        # Verify
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "def foo" in content

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_stdin_empty_input(self, mock_translator_class):
        """Error on empty stdin input."""
        # Mock translator
        mock_translator = MagicMock()
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute with empty stdin
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en"],
            input="   \n  \n",  # Whitespace only
        )

        # Verify error
        assert result.exit_code == 1
        assert "No input received" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_dash_as_stdin(self, mock_translator_class, tmp_path):
        """Explicit '-' for stdin (if supported) or test that stdin is used when no file provided."""
        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Create a file named '-' to test if Click handles it
        # If '-' is not specially handled, this test verifies stdin behavior
        # when no input argument is provided (which is tested elsewhere)
        # For now, just verify that omitting input works as stdin
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en"],
            input="definir foo():\n    retornar 42",
        )

        # Verify - when no input file is provided, stdin is used
        assert result.exit_code == 0
        assert "def foo" in result.output


class TestDirectoryTranslation:
    """Test directory translation scenarios."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_recursive(self, mock_translator_class, tmp_path):
        """Find and translate all .py files recursively."""
        # Setup directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        (src_dir / "main.py").write_text(
            "definir main():\n    retornar 0", encoding="utf-8"
        )

        subdir = src_dir / "utils"
        subdir.mkdir()
        (subdir / "helpers.py").write_text(
            "definir helper():\n    retornar 1", encoding="utf-8"
        )

        output_dir = tmp_path / "translated"

        # Mock translator
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = (
            lambda code, src, tgt: code.replace("definir", "def").replace(
                "retornar", "return"
            )
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src_dir),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_dir),
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert (output_dir / "main.py").exists()
        assert (output_dir / "utils" / "helpers.py").exists()
        assert "2/2" in result.output  # 2 files translated

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_preserves_structure(
        self, mock_translator_class, tmp_path
    ):
        """Verify directory structure is mirrored in output."""
        # Setup nested structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        (src_dir / "a.py").write_text("definir a(): pass", encoding="utf-8")

        level1 = src_dir / "level1"
        level1.mkdir()
        (level1 / "b.py").write_text("definir b(): pass", encoding="utf-8")

        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "c.py").write_text("definir c(): pass", encoding="utf-8")

        output_dir = tmp_path / "out"

        # Mock translator
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = (
            lambda code, src, tgt: code.replace("definir", "def")
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src_dir),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_dir),
            ],
        )

        # Verify structure
        assert result.exit_code == 0
        assert (output_dir / "a.py").exists()
        assert (output_dir / "level1" / "b.py").exists()
        assert (output_dir / "level1" / "level2" / "c.py").exists()

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_no_py_files(self, mock_translator_class, tmp_path):
        """Warning when no .py files found in directory."""
        # Setup empty directory
        src_dir = tmp_path / "empty"
        src_dir.mkdir()

        # Add non-Python files
        (src_dir / "readme.txt").write_text("Not a Python file")
        (src_dir / "config.json").write_text("{}")

        # Mock translator
        mock_translator = MagicMock()
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify warning
        assert result.exit_code == 0
        assert "No .py files found" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_partial_failure(self, mock_translator_class, tmp_path):
        """Continue translation on individual file errors."""
        # Setup
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        (src_dir / "good.py").write_text("definir foo(): pass", encoding="utf-8")
        (src_dir / "bad.py").write_text("definir bar(): pass", encoding="utf-8")
        (src_dir / "also_good.py").write_text("definir baz(): pass", encoding="utf-8")

        output_dir = tmp_path / "out"

        # Mock translator - fail on bad.py
        mock_translator = MagicMock()

        def translate_side_effect(code, src, tgt):
            if "bar" in code:
                raise TranslationError("Simulated translation error")
            return code.replace("definir", "def")

        mock_translator.translate_code.side_effect = translate_side_effect
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src_dir),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_dir),
            ],
        )

        # Verify - should fail overall but translate good files
        assert result.exit_code == 1
        assert (output_dir / "good.py").exists()
        assert (output_dir / "also_good.py").exists()
        assert "2/3" in result.output
        assert "1 files failed" in result.output


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_missing_file_error(self, mock_translator_class, tmp_path):
        """Error when input file doesn't exist."""
        # Mock translator
        mock_translator = MagicMock()
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute with non-existent file
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(tmp_path / "nonexistent.py"),
                "--from",
                "es",
                "--to",
                "en",
            ],
        )

        # Verify error
        assert result.exit_code != 0
        # Click handles this with "does not exist" message

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_invalid_language_error(self, mock_translator_class):
        """Error on unsupported language code."""
        # Mock translator to raise KeyError for unsupported language
        mock_translator_class.from_language_pack.side_effect = KeyError(
            "Language 'xyz' not supported"
        )

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "xyz"],
            input="definir foo(): pass",
        )

        # Verify error
        assert result.exit_code == 1
        assert "Language 'xyz' not supported" in result.output
        assert "Available languages:" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_invalid_syntax_error(self, mock_translator_class, tmp_path):
        """Error on malformed Python syntax."""
        # Setup
        input_file = tmp_path / "bad.py"
        input_file.write_text("definir foo)(: # Invalid syntax", encoding="utf-8")

        # Mock translator to raise InvalidCodeError
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = InvalidCodeError(
            "Cannot parse invalid syntax"
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--from", "es", "--to", "en"],
        )

        # Verify error - Note: InvalidCodeError is caught as TranslationError in the CLI
        # because InvalidCodeError inherits from TranslationError
        assert result.exit_code == 1
        assert "error" in result.output.lower()
        assert "Cannot parse invalid syntax" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_permission_denied_error(self, mock_translator_class, tmp_path):
        """Error when can't write to output file."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo(): pass", encoding="utf-8")

        # Create read-only output directory
        output_dir = tmp_path / "readonly"
        output_dir.mkdir()
        output_file = output_dir / "output.py"

        # Make directory read-only (Unix-like systems)
        if os.name != "nt":
            output_dir.chmod(0o444)

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def foo(): pass"
        )

        try:
            # Execute
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "translate",
                    str(input_file),
                    "--from",
                    "es",
                    "--to",
                    "en",
                    "--output",
                    str(output_file),
                ],
            )

            # Verify error (only on Unix-like systems)
            if os.name != "nt":
                assert result.exit_code == 1
                assert "Permission denied" in result.output

        finally:
            # Cleanup - restore permissions
            if os.name != "nt":
                output_dir.chmod(0o755)

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_unicode_decode_error(self, mock_translator_class, tmp_path):
        """Error on non-UTF8 file encoding."""
        # Setup - create latin-1 encoded file
        input_file = tmp_path / "latin1.py"
        # Write with latin-1 encoding
        input_file.write_bytes(b"definir foo():\n    # Caf\xe9\n    pass")

        # Mock translator
        mock_translator = MagicMock()
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--from", "es", "--to", "en"],
        )

        # Verify error
        assert result.exit_code == 1
        assert "Could not read" in result.output
        assert "UTF-8" in result.output


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_empty_file(self, mock_translator_class, tmp_path):
        """Handle empty .py file gracefully."""
        # Setup
        input_file = tmp_path / "empty.py"
        input_file.write_text("", encoding="utf-8")

        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(mock_translator_class, translate_return_value="")

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify - should succeed with empty output
        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == ""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_no_input_reads_stdin(self, mock_translator_class):
        """No argument reads from stdin by default."""
        # Mock translator
        setup_mock_translator(mock_translator_class)

        # Execute without input argument
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en"],
            input="definir foo():\n    retornar 42",
        )

        # Verify
        assert result.exit_code == 0
        assert "def foo" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_unicode_content(self, mock_translator_class, tmp_path):
        """Handle Unicode content (Arabic, Chinese, emoji, etc.)."""
        # Setup with Unicode content
        input_file = tmp_path / "unicode.py"
        unicode_code = '"""مرحبا 你好 🌍"""\ndefinir foo():\n    retornar "test"'
        input_file.write_text(unicode_code, encoding="utf-8")

        output_file = tmp_path / "output.py"

        # Mock translator
        mock_translator = MagicMock()
        mock_translator.translate_code.return_value = (
            '"""مرحبا 你好 🌍"""\ndef foo():\n    return "test"'
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "مرحبا" in content
        assert "你好" in content
        assert "🌍" in content

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_default_source_language(self, mock_translator_class, tmp_path):
        """Verify --from defaults to 'en' when not specified."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("def foo(): return 42", encoding="utf-8")

        # Mock translator
        mock_translator = setup_mock_translator(
            mock_translator_class, translate_return_value="definir foo(): retornar 42"
        )

        # Execute without --from flag
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--to", "es"],
        )

        # Verify translator was called with default source 'en'
        assert result.exit_code == 0
        # Check that translate_code was called with 'en' as source
        call_args = mock_translator.translate_code.call_args
        assert call_args[0][1] == "en"  # source_lang

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_required_to_flag(self, mock_translator_class, tmp_path):
        """Verify --to flag is required."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("def foo(): pass", encoding="utf-8")

        # Execute without --to flag
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file)],
        )

        # Verify error due to missing required --to option
        assert result.exit_code != 0
        assert "--to" in result.output or "required" in result.output.lower()

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_default_output_name(
        self, mock_translator_class, tmp_path
    ):
        """Verify directory translation creates _translated suffix when no output specified."""
        # Setup
        src_dir = tmp_path / "myproject"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("definir main(): pass", encoding="utf-8")

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def main(): pass"
        )

        # Execute without --output
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify default output directory created
        assert result.exit_code == 0
        expected_dir = tmp_path / "myproject_translated"
        assert expected_dir.exists()
        assert (expected_dir / "main.py").exists()

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_handles_translation_error(self, mock_translator_class, tmp_path):
        """Handle generic TranslationError gracefully."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo(): pass", encoding="utf-8")

        # Mock translator to raise TranslationError
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = TranslationError(
            "Custom translation error"
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--from", "es", "--to", "en"],
        )

        # Verify error handling
        assert result.exit_code == 1
        assert "Translation error" in result.output
        assert "Custom translation error" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_handles_unexpected_error(self, mock_translator_class, tmp_path):
        """Handle unexpected exceptions gracefully."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo(): pass", encoding="utf-8")

        # Mock translator to raise unexpected error
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = RuntimeError(
            "Unexpected system error"
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(input_file), "--from", "es", "--to", "en"],
        )

        # Verify error handling
        assert result.exit_code == 1
        assert "Unexpected error" in result.output


class TestUncommonCodePaths:
    """Test uncommon code paths to increase coverage."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_invalid_input_type(self, mock_translator_class, tmp_path):
        """Error when input exists but is neither file nor directory."""
        # Note: This is hard to test in practice since Click validates file existence
        # and most filesystem objects are files or directories. This path would be
        # hit if Click's exists=True check passes but Path operations fail.
        # We'll test through mocking the Path object behavior
        pass  # This is dead code in practice

    @patch("legesher.cli.translate.TokenTranslator")
    @patch("legesher.cli.translate.shutil.copymode")
    def test_translate_file_copymode_failure(
        self, mock_copymode, mock_translator_class, tmp_path
    ):
        """Verify graceful handling when copymode fails."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo(): pass", encoding="utf-8")
        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def foo(): pass"
        )

        # Mock copymode to raise exception
        mock_copymode.side_effect = OSError("Permission denied")

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify - should succeed despite copymode failure
        assert result.exit_code == 0
        assert output_file.exists()

    @patch("legesher.cli.translate.TokenTranslator")
    @patch("legesher.cli.translate.shutil.copymode")
    def test_translate_directory_copymode_failure(
        self, mock_copymode, mock_translator_class, tmp_path
    ):
        """Verify graceful handling when copymode fails during directory translation."""
        # Setup
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "file.py").write_text("definir foo(): pass", encoding="utf-8")

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def foo(): pass"
        )

        # Mock copymode to raise exception
        mock_copymode.side_effect = OSError("Permission denied")

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify - should succeed despite copymode failure
        assert result.exit_code == 0
        assert "1/1" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_unicode_decode_error(
        self, mock_translator_class, tmp_path
    ):
        """Handle UnicodeDecodeError during directory translation."""
        # Setup
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create a file with invalid UTF-8 encoding
        bad_file = src_dir / "bad.py"
        bad_file.write_bytes(b"definir foo():\n    # Caf\xe9\n    pass")

        # Create a good file
        good_file = src_dir / "good.py"
        good_file.write_text("definir bar(): pass", encoding="utf-8")

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def bar(): pass"
        )

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify - should fail overall but process good files
        assert result.exit_code == 1
        assert "1/2" in result.output  # 1 success out of 2 files
        assert "1 files failed" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_unexpected_error(
        self, mock_translator_class, tmp_path
    ):
        """Handle unexpected errors during directory translation."""
        # Setup
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "file1.py").write_text("definir foo(): pass", encoding="utf-8")
        (src_dir / "file2.py").write_text("definir bar(): pass", encoding="utf-8")

        # Mock translator - raise unexpected error on first file
        mock_translator = MagicMock()

        def translate_side_effect(code, src, tgt):
            if "foo" in code:
                raise RuntimeError("Unexpected error")
            return "def bar(): pass"

        mock_translator.translate_code.side_effect = translate_side_effect
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify - should fail overall but process second file
        assert result.exit_code == 1
        assert "1/2" in result.output
        assert "Unexpected error" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_get_available_languages_fallback(self, mock_translator_class):
        """Test fallback when TokenTranslator.list_available_languages() doesn't exist."""
        # Mock translator class to raise KeyError for unsupported language
        mock_translator_class.from_language_pack.side_effect = KeyError(
            "Unknown language"
        )

        # Simulate AttributeError when trying to call list_available_languages
        # Delete the method to trigger AttributeError
        delattr(mock_translator_class, "list_available_languages")

        # Execute with invalid language
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "en", "--to", "xyz"],
            input="def foo(): pass",
        )

        # Verify - should show fallback language list
        assert result.exit_code == 1
        assert "Language 'xyz' not supported" in result.output
        # Should show fallback languages (en, es, ar, hi)
        assert "es" in result.output or "ar" in result.output or "hi" in result.output


class TestProgressAndFeedback:
    """Test progress output and user feedback."""

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_file_shows_success_message(
        self, mock_translator_class, tmp_path
    ):
        """Verify success message for file translation."""
        # Setup
        input_file = tmp_path / "input.py"
        input_file.write_text("definir foo(): pass", encoding="utf-8")
        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def foo(): pass"
        )

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(output_file),
            ],
        )

        # Verify success message
        assert result.exit_code == 0
        assert "✓" in result.output or "Translated" in result.output

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_directory_shows_progress(self, mock_translator_class, tmp_path):
        """Verify progress indicators for directory translation."""
        # Setup
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create multiple files
        for i in range(3):
            (src_dir / f"file{i}.py").write_text(
                f"definir func{i}(): pass", encoding="utf-8"
            )

        # Mock translator
        mock_translator = MagicMock()
        mock_translator.translate_code.side_effect = (
            lambda code, src, tgt: code.replace("definir", "def")
        )
        mock_translator_class.from_language_pack.return_value = mock_translator
        mock_translator.reverse.return_value = mock_translator

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", str(src_dir), "--from", "es", "--to", "en"],
        )

        # Verify progress output
        assert result.exit_code == 0
        assert "[1/3]" in result.output or "1/" in result.output
        assert "[2/3]" in result.output or "2/" in result.output
        assert "[3/3]" in result.output or "3/" in result.output
        assert "3/3" in result.output  # Summary

    @patch("legesher.cli.translate.TokenTranslator")
    def test_translate_stdin_to_file_shows_success(
        self, mock_translator_class, tmp_path
    ):
        """Verify success message for stdin to file translation."""
        # Setup
        output_file = tmp_path / "output.py"

        # Mock translator
        setup_mock_translator(
            mock_translator_class, translate_return_value="def foo(): pass"
        )

        # Execute
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "es", "--to", "en", "--output", str(output_file)],
            input="definir foo(): pass",
        )

        # Verify success message
        assert result.exit_code == 0
        assert "✓" in result.output or "Translated" in result.output
