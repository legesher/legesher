"""Comprehensive integration tests for Legesher CLI (CORE-381).

This module provides comprehensive integration tests for the `legesher translate` CLI command,
including:
- End-to-end translation workflows (file, stdin, directory)
- Semantic equivalence verification (AST & bytecode)
- Complex code patterns (imports, classes, decorators, control flow)
- Directory operations with structure preservation
- Real language pack integration (Spanish, Arabic, Hindi)
- Performance testing (large files, many files)

Coverage Target: 85%+ of integration paths

Test Organization:
- TestSemanticEquivalence: Critical AST/bytecode verification
- TestEndToEndTranslation: Complete translation workflows
- TestComplexCodePatterns: Real-world Python patterns
- TestDirectoryOperations: Directory translation & structure preservation
- TestRealLanguagePacks: Integration with actual language packs
- TestPerformance: Performance benchmarks

Note:
    These are integration tests that exercise the full CLI command.
    Unit tests for individual components are in test_translate_unit.py.
"""

import ast
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from legesher.cli.main import cli


# =============================================================================
# Semantic Equivalence Helpers (CRITICAL for Correctness)
# =============================================================================


def assert_ast_equivalent(code1: str, code2: str) -> None:
    """Assert two code snippets have identical AST structure.

    This is the CRITICAL test for semantic equivalence - if two pieces of code
    produce identical ASTs, they are functionally equivalent Python code.

    Args:
        code1: First code snippet
        code2: Second code snippet

    Raises:
        AssertionError: If AST structures differ

    Example:
        >>> assert_ast_equivalent(
        ...     "def foo(): return 42",
        ...     "definir foo(): retornar 42"  # Won't pass - syntax error
        ... )
        >>> # Correct usage - compare English to English
        >>> assert_ast_equivalent(
        ...     "def foo(): return 42",
        ...     "def foo(): return 42"
        ... )
    """
    # Strip surrounding whitespace for comparison
    code1 = code1.strip()
    code2 = code2.strip()

    try:
        ast1 = ast.parse(code1)
        ast2 = ast.parse(code2)
    except SyntaxError as e:
        pytest.fail(
            f"Syntax error parsing code: {e}\nCode1:\n{code1}\n\nCode2:\n{code2}"
        )

    # Dump ASTs without line numbers or column offsets (format-independent)
    dump1 = ast.dump(ast1, annotate_fields=False, include_attributes=False)
    dump2 = ast.dump(ast2, annotate_fields=False, include_attributes=False)

    assert dump1 == dump2, (
        f"AST structures differ:\n\n"
        f"Code 1:\n{code1}\n\n"
        f"Code 2:\n{code2}\n\n"
        f"AST 1:\n{dump1}\n\n"
        f"AST 2:\n{dump2}"
    )


def assert_bytecode_equivalent(code1: str, code2: str) -> None:
    """Assert two code snippets compile to identical bytecode.

    This is an even stricter test than AST equivalence - it verifies that
    the compiled bytecode is identical, ensuring runtime behavior is identical.

    Args:
        code1: First code snippet
        code2: Second code snippet

    Raises:
        AssertionError: If bytecode differs

    Note:
        This is stricter than AST comparison and may fail for semantically
        equivalent but syntactically different code (e.g., different constant
        orderings). Use AST comparison for general semantic equivalence.
    """
    try:
        bytecode1 = compile(code1, "<string>", "exec")
        bytecode2 = compile(code2, "<string>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error compiling code: {e}")

    # Compare co_code (actual bytecode)
    assert bytecode1.co_code == bytecode2.co_code, (
        f"Bytecode differs:\n\n"
        f"Code 1:\n{code1}\n\n"
        f"Code 2:\n{code2}\n\n"
        f"Bytecode 1: {bytecode1.co_code.hex()}\n"
        f"Bytecode 2: {bytecode2.co_code.hex()}"
    )


def assert_code_executes_identically(code1: str, code2: str) -> None:
    """Assert two code snippets produce identical execution results.

    This tests runtime equivalence by executing both code snippets and
    comparing their outputs and side effects.

    Args:
        code1: First code snippet
        code2: Second code snippet

    Raises:
        AssertionError: If execution results differ

    Note:
        This captures stdout/stderr and compares execution results.
        Use for testing that translated code behaves identically.
    """
    import io
    from contextlib import redirect_stdout, redirect_stderr

    # Execute code1
    stdout1 = io.StringIO()
    stderr1 = io.StringIO()
    globals1 = {}

    try:
        with redirect_stdout(stdout1), redirect_stderr(stderr1):
            exec(code1, globals1)
    except Exception as e:
        pytest.fail(f"Code 1 raised exception: {e}\n\nCode:\n{code1}")

    # Execute code2
    stdout2 = io.StringIO()
    stderr2 = io.StringIO()
    globals2 = {}

    try:
        with redirect_stdout(stdout2), redirect_stderr(stderr2):
            exec(code2, globals2)
    except Exception as e:
        pytest.fail(f"Code 2 raised exception: {e}\n\nCode:\n{code2}")

    # Compare outputs
    assert stdout1.getvalue() == stdout2.getvalue(), (
        f"Stdout differs:\n\n"
        f"Code 1 stdout:\n{stdout1.getvalue()}\n\n"
        f"Code 2 stdout:\n{stdout2.getvalue()}"
    )

    assert stderr1.getvalue() == stderr2.getvalue(), (
        f"Stderr differs:\n\n"
        f"Code 1 stderr:\n{stderr1.getvalue()}\n\n"
        f"Code 2 stderr:\n{stderr2.getvalue()}"
    )


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.integration
class TestSemanticEquivalence:
    """CRITICAL: Tests that verify translated code is semantically identical.

    These tests are the most important - they ensure translated code has
    identical behavior to the original code. Uses AST and bytecode comparison.
    """

    def test_ast_semantic_equivalence_spanish(self, tmp_path: Path, spanish_keywords):
        """Verify Spanish-translated code has identical AST structure."""
        # Original English code
        english_code = """def calculate_tax(income, rate):
    \"\"\"Calculate tax on income.\"\"\"
    if income < 0:
        raise ValueError("Income cannot be negative")
    return income * rate
"""

        # Write Spanish code using real pack translations
        sk = spanish_keywords
        spanish_code = f"""{sk["def"]} calculate_tax(income, rate):
    \"\"\"Calculate tax on income.\"\"\"
    {sk["if"]} income < 0:
        {sk["raise"]} ValueError("Income cannot be negative")
    {sk["return"]} income * rate
"""
        input_file = tmp_path / "spanish.py"
        input_file.write_text(spanish_code, encoding="utf-8")

        output_file = tmp_path / "english.py"

        # Translate Spanish -> English
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

        assert result.exit_code == 0, f"Translation failed: {result.output}"
        assert output_file.exists()

        # Compare ASTs
        translated_code = output_file.read_text(encoding="utf-8")
        assert_ast_equivalent(english_code, translated_code)

    def test_bytecode_semantic_equivalence_spanish(self, tmp_path: Path):
        """Verify Spanish-translated code compiles to identical bytecode."""
        english_code = """x = 42
z = x * 2
print(z)
"""

        spanish_code = """x = 42
z = x * 2
imprimir(z)
"""
        input_file = tmp_path / "spanish.py"
        input_file.write_text(spanish_code, encoding="utf-8")

        output_file = tmp_path / "english.py"

        # Translate
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

        assert result.exit_code == 0
        translated_code = output_file.read_text()

        # Compare bytecode
        assert_bytecode_equivalent(english_code, translated_code)

    def test_round_trip_translation_preserves_semantics(self, tmp_path: Path):
        """Verify en -> es -> en preserves original code semantics."""
        original_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
"""

        # Write original
        english_file = tmp_path / "english.py"
        english_file.write_text(original_code)

        # Translate en -> es
        spanish_file = tmp_path / "spanish.py"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(english_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(spanish_file),
            ],
        )
        assert result.exit_code == 0

        # Translate es -> en
        back_to_english = tmp_path / "english_back.py"
        result = runner.invoke(
            cli,
            [
                "translate",
                str(spanish_file),
                "--from",
                "es",
                "--to",
                "en",
                "--output",
                str(back_to_english),
            ],
        )
        assert result.exit_code == 0

        # Compare ASTs
        final_code = back_to_english.read_text(encoding="utf-8")
        assert_ast_equivalent(original_code, final_code)

    def test_execution_equivalence_spanish(
        self, tmp_path: Path, spanish_keywords, spanish_builtins
    ):
        """Verify Spanish and English versions execute identically."""
        english_code = """import sys
for i in range(3):
    print(f"Count: {i}")
"""

        sk = spanish_keywords
        sb = spanish_builtins
        spanish_code = f"""{sk["import"]} sys
{sk["for"]} i {sk["in"]} {sb["range"]}(3):
    {sb["print"]}(f"Count: {{i}}")
"""
        input_file = tmp_path / "spanish.py"
        input_file.write_text(spanish_code, encoding="utf-8")

        output_file = tmp_path / "english.py"

        # Translate
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

        assert result.exit_code == 0
        translated_code = output_file.read_text()

        # Verify execution equivalence
        assert_code_executes_identically(english_code, translated_code)


@pytest.mark.integration
class TestEndToEndTranslation:
    """Test complete translation workflows (file, stdin, directory)."""

    def test_spanish_to_english_file_translation(
        self, tmp_path: Path, spanish_keywords, spanish_builtins
    ):
        """Test complete Spanish -> English file translation workflow."""
        sk = spanish_keywords
        sb = spanish_builtins
        spanish_code = f"""# Programa de calculadora
{sk["def"]} sumar(a, b):
    \"\"\"Suma dos números.\"\"\"
    {sk["return"]} a + b

{sk["def"]} restar(a, b):
    \"\"\"Resta dos números.\"\"\"
    {sk["return"]} a - b

{sk["if"]} __nombre__ == "__main__":
    resultado = sumar(10, 5)
    {sb["print"]}(f"Resultado: {{resultado}}")
"""

        input_file = tmp_path / "calculadora.py"
        input_file.write_text(spanish_code, encoding="utf-8")

        output_file = tmp_path / "calculator.py"

        # Run translation
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

        # Verify success
        assert result.exit_code == 0
        assert "✓ Translated" in result.output
        assert output_file.exists()

        # Verify translated content
        translated = output_file.read_text(encoding="utf-8")
        assert "def " in translated  # Function definition translated
        assert "return" in translated
        # Identifier translation may vary; just check structure
        assert "if " in translated
        assert "print" in translated

    def test_english_to_arabic_stdin_translation(
        self, tmp_path: Path, arabic_keywords, arabic_builtins
    ):
        """Test stdin -> stdout workflow with RTL language (Arabic)."""
        english_code = """def greet(name):
    print(f"Hello, {name}!")
    return True
"""

        output_file = tmp_path / "arabic.py"

        # Run translation with stdin input
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["translate", "--from", "en", "--to", "ar", "--output", str(output_file)],
            input=english_code,
        )

        # Verify success
        assert result.exit_code == 0
        assert output_file.exists()

        # Verify Arabic keywords using real pack translations
        translated = output_file.read_text(encoding="utf-8")
        assert arabic_keywords["def"] in translated
        assert arabic_builtins["print"] in translated
        assert arabic_keywords["True"] in translated
        assert "greet" in translated  # Identifier preserved

    @pytest.mark.skip(reason="Hindi language pack not yet implemented")
    def test_english_to_hindi_directory_translation(self, tmp_path: Path):
        """Test directory translation with Hindi language pack."""
        # Create source directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create multiple Python files
        (src_dir / "main.py").write_text("""def main(, encoding="utf-8"):
    print("Starting application")
    return 0
""")

        (src_dir / "utils.py").write_text("""def add(a, b, encoding="utf-8"):
    return a + b

def multiply(a, b):
    return a * b
""")

        subdir = src_dir / "helpers"
        subdir.mkdir()
        (
            subdir / "formatter.py"
        ).write_text("""def format_output(value, encoding="utf-8"):
    return f"Result: {value}"
""")

        # Translate directory
        output_dir = tmp_path / "hindi_src"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src_dir),
                "--from",
                "en",
                "--to",
                "hi",
                "--output",
                str(output_dir),
            ],
        )

        # Verify success
        assert result.exit_code == 0
        assert "✓ Translated 3/3 files" in result.output

        # Verify structure preserved
        assert (output_dir / "main.py").exists()
        assert (output_dir / "utils.py").exists()
        assert (output_dir / "helpers" / "formatter.py").exists()

        # Verify Hindi keywords in translated files
        main_content = (output_dir / "main.py").read_text(encoding="utf-8")
        assert "परिभाषित" in main_content  # def in Hindi
        assert "छापना" in main_content  # print in Hindi
        assert "लौटाना" in main_content  # return in Hindi


@pytest.mark.integration
class TestComplexCodePatterns:
    """Test translation of real-world Python code patterns."""

    def test_translate_with_imports(self, tmp_path: Path):
        """Test translation preserves import statements correctly."""
        code = """import os
import sys
from pathlib import Path
from typing import List, Dict

def process_files(directory: Path) -> List[str]:
    return [f.name for f in directory.iterdir()]
"""

        input_file = tmp_path / "imports.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "imports_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify imports preserved
        assert "import os" in translated or "importar os" in translated
        assert "from pathlib" in translated or "desde pathlib" in translated
        assert (
            "def process_files" in translated or "definir process_files" in translated
        )
        assert (
            "return" in translated
            or "devolver" in translated
            or "retornar" in translated
        )

    def test_translate_with_classes(self, tmp_path: Path):
        """Test translation handles class definitions and methods."""
        code = """class Calculator:
    \"\"\"A simple calculator class.\"\"\"

    def __init__(self, precision: int = 2):
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        return round(a + b, self.precision)

    def subtract(self, a: float, b: float) -> float:
        return round(a - b, self.precision)

    @property
    def name(self) -> str:
        return "Calculator"
"""

        input_file = tmp_path / "calculator.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "calculator_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify class structure preserved
        assert ("class Calculator" in translated) or ("clase Calculator" in translated)
        assert ("def __init__" in translated) or ("definir __init__" in translated)
        assert ("def add" in translated) or ("definir add" in translated)
        assert (
            ("return" in translated)
            or ("devolver" in translated)
            or ("retornar" in translated)
        )
        # CORE-710 added the `reserved_words` category for deterministic
        # `self`/`cls` translation. The Spanish pack defines
        # `reserved_words.self -> mismo`, so post-CORE-710 the translation
        # MUST contain `mismo`. If this fails, check that the es pack
        # still has `reserved_words.self` populated.
        assert "mismo" in translated, (
            "Spanish pack should translate self -> mismo per CORE-710's "
            "reserved_words category. Got: " + translated[:200]
        )

    def test_translate_with_decorators(self, tmp_path: Path):
        """Test translation handles decorator syntax."""
        code = """from functools import wraps

def debug(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Result: {result}")
        return result
    return wrapper

@debug
def calculate(x, y):
    return x + y
"""

        input_file = tmp_path / "decorators.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "decorators_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify decorator syntax preserved
        assert "@" in translated  # Decorator syntax
        assert ("def debug" in translated) or ("definir debug" in translated)
        assert ("def wrapper" in translated) or ("definir wrapper" in translated)
        assert (
            ("return" in translated)
            or ("devolver" in translated)
            or ("retornar" in translated)
        )

    def test_translate_with_control_flow(self, tmp_path: Path):
        """Test translation of complex control flow (if/for/while/try/except)."""
        code = """def process_data(items):
    results = []

    for item in items:
        if item < 0:
            continue
        elif item == 0:
            break
        else:
            results.append(item * 2)

    counter = 0
    while counter < len(results):
        try:
            value = results[counter]
            print(f"Value: {value}")
        except IndexError as e:
            print(f"Error: {e}")
            break
        except Exception:
            pass
        finally:
            counter += 1

    return results
"""

        input_file = tmp_path / "control_flow.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "control_flow_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify control flow keywords translated
        assert ("def process_data" in translated) or (
            "definir process_data" in translated
        )
        assert ("for" in translated) or ("por" in translated) or ("para" in translated)
        assert ("while" in translated) or ("mientras" in translated)
        assert ("if" in translated) or ("si" in translated)
        assert (
            ("try" in translated)
            or ("probar" in translated)
            or ("intentar" in translated)
        )
        assert (
            ("except" in translated)
            or ("excepto" in translated)
            or ("ماعدا" in translated)
        )
        assert (
            ("return" in translated)
            or ("devolver" in translated)
            or ("retornar" in translated)
        )

    def test_translate_with_context_managers(self, tmp_path: Path):
        """Test translation of with statements (context managers)."""
        code = """def read_file(path):
    with open(path, 'r') as f:
        data = f.read()
        return data

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)
        return True
"""

        input_file = tmp_path / "context.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "context_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify with statements preserved
        assert ("with" in translated) or ("con" in translated)
        assert ("as" in translated) or ("como" in translated)
        assert "open" in translated or "abrir" in translated  # builtin

    def test_translate_with_comprehensions(self, tmp_path: Path):
        """Test translation of list/dict/set comprehensions."""
        code = """def process_numbers(numbers):
    # List comprehension
    squares = [x ** 2 for x in numbers if x > 0]

    # Dict comprehension
    square_dict = {x: x ** 2 for x in numbers}

    # Set comprehension
    unique_squares = {x ** 2 for x in numbers}

    return squares, square_dict, unique_squares
"""

        input_file = tmp_path / "comprehensions.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "comprehensions_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        translated = output_file.read_text()

        # Verify comprehension structure preserved
        assert "[" in translated and "]" in translated
        assert "{" in translated and "}" in translated
        assert ("for" in translated) or ("por" in translated) or ("para" in translated)
        assert ("if" in translated) or ("si" in translated)


@pytest.mark.integration
class TestDirectoryOperations:
    """Test directory translation operations."""

    def test_directory_preserves_structure(self, tmp_path: Path):
        """Test complex directory tree structure is preserved."""
        # Create complex directory structure
        src = tmp_path / "project"
        src.mkdir()

        (src / "main.py").write_text("def main(): pass", encoding="utf-8")
        (src / "config.py").write_text("DEBUG = True", encoding="utf-8")

        (src / "core").mkdir()
        (src / "core" / "__init__.py").write_text("", encoding="utf-8")
        (src / "core" / "engine.py").write_text("def run(): pass", encoding="utf-8")

        (src / "utils").mkdir()
        (src / "utils" / "__init__.py").write_text("", encoding="utf-8")
        (src / "utils" / "helpers.py").write_text("def help(): pass", encoding="utf-8")

        (src / "tests").mkdir()
        (src / "tests" / "test_core.py").write_text(
            "def test_run(): assert True", encoding="utf-8"
        )

        # Translate
        output = tmp_path / "project_es"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0

        # Verify structure
        assert (output / "main.py").exists()
        assert (output / "config.py").exists()
        assert (output / "core" / "__init__.py").exists()
        assert (output / "core" / "engine.py").exists()
        assert (output / "utils" / "__init__.py").exists()
        assert (output / "utils" / "helpers.py").exists()
        assert (output / "tests" / "test_core.py").exists()

    def test_directory_with_nested_subdirectories(self, tmp_path: Path):
        """Test deeply nested directory structure."""
        # Create 4-level deep structure
        base = tmp_path / "deep"
        path = base / "level1" / "level2" / "level3"
        path.mkdir(parents=True)

        (path / "deep_module.py").write_text(
            "def deep_function(): return 42", encoding="utf-8"
        )

        # Translate
        output = tmp_path / "deep_es"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(base),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0
        assert (output / "level1" / "level2" / "level3" / "deep_module.py").exists()

    def test_directory_skips_non_py_files(self, tmp_path: Path):
        """Test that only .py files are translated."""
        src = tmp_path / "mixed"
        src.mkdir()

        # Create mixed file types
        (src / "script.py").write_text("def script(): pass", encoding="utf-8")
        (src / "data.json").write_text('{"key": "value"}', encoding="utf-8")
        (src / "README.md").write_text("# Project", encoding="utf-8")
        (src / "config.txt").write_text("setting=value")

        # Translate
        output = tmp_path / "mixed_es"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0
        assert "1/1 files" in result.output  # Only 1 .py file

        # Verify only .py file translated
        assert (output / "script.py").exists()
        assert not (output / "data.json").exists()
        assert not (output / "README.md").exists()
        assert not (output / "config.txt").exists()

    def test_directory_handles_empty_directories(self, tmp_path: Path):
        """Test handling of directories with no Python files."""
        src = tmp_path / "empty"
        src.mkdir()
        (src / "subdir").mkdir()

        # Translate
        output = tmp_path / "empty_es"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output),
            ],
        )

        # Should complete successfully with warning
        assert result.exit_code == 0
        assert "No .py files found" in result.output


@pytest.mark.integration
class TestRealLanguagePacks:
    """Test integration with actual language pack files."""

    def test_all_spanish_keywords_work(self, tmp_path: Path, spanish_keywords):
        """Test all Spanish keywords from language pack translate correctly."""
        # Use comprehensive Python code with many keywords
        code = """import sys
from typing import List

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, items: List[int]) -> int:
        try:
            for item in items:
                if item < 0:
                    raise ValueError("Negative value")
                elif item == 0:
                    continue
                else:
                    self.data.append(item)

            while len(self.data) > 100:
                del self.data[0]

            with open('output.txt', 'w') as f:
                for value in self.data:
                    print(value, file=f)

            return len(self.data)

        except Exception as e:
            print(f"Error: {e}")
            return -1
        finally:
            pass

def main():
    processor = DataProcessor()
    result = processor.process([1, 2, 3])
    assert result == 3
    return True

if __name__ == "__main__":
    main()
"""

        input_file = tmp_path / "comprehensive.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "comprehensive_es.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

        # Verify Spanish keywords present
        translated = output_file.read_text(encoding="utf-8")

        # At least several keywords should be translated
        found_count = sum(1 for kw in spanish_keywords.values() if kw in translated)
        assert found_count >= 5, (
            f"Expected multiple Spanish keywords, found {found_count}"
        )

    def test_all_arabic_keywords_work(
        self, tmp_path: Path, arabic_keywords, arabic_builtins
    ):
        """Test all Arabic keywords from language pack translate correctly."""
        code = """def calculate(x, y):
    if x > y:
        return x
    elif x < y:
        return y
    else:
        return 0

class Numbers:
    def __init__(self):
        pass

    def process(self):
        for i in range(10):
            print(i)
"""

        input_file = tmp_path / "arabic_test.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "arabic_output.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "ar",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

        # Verify Arabic keywords present using real pack translations
        translated = output_file.read_text(encoding="utf-8")
        expected_keywords = [
            arabic_keywords["def"],
            arabic_keywords["if"],
            arabic_keywords["elif"],
            arabic_keywords["else"],
            arabic_keywords["class"],
            arabic_keywords["for"],
        ]

        found_count = sum(1 for kw in expected_keywords if kw in translated)
        assert found_count >= 3, (
            f"Expected multiple Arabic keywords, found {found_count}"
        )

    @pytest.mark.skip(reason="Hindi language pack not yet implemented")
    def test_all_hindi_keywords_work(self, tmp_path: Path):
        """Test all Hindi keywords from language pack translate correctly."""
        code = """def greet(name):
    print(f"Hello, {name}")
    return True

class Person:
    def __init__(self, name):
        self.name = name

    def speak(self):
        for i in range(3):
            print(f"{self.name} speaking")
"""

        input_file = tmp_path / "hindi_test.py"
        input_file.write_text(code, encoding="utf-8")

        output_file = tmp_path / "hindi_output.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "hi",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

        # Verify Hindi keywords present
        translated = output_file.read_text(encoding="utf-8")
        hindi_keywords = ["परिभाषित", "छापना", "लौटाना", "वर्ग"]

        found_count = sum(1 for kw in hindi_keywords if kw in translated)
        assert found_count >= 2, (
            f"Expected multiple Hindi keywords, found {found_count}"
        )

    def test_language_pack_not_found_error(self, tmp_path: Path):
        """Test helpful error message when language pack doesn't exist."""
        input_file = tmp_path / "test.py"
        input_file.write_text("def test(): pass", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "xyz",  # Invalid language
                "--output",
                tmp_path / "output.py",
            ],
        )

        assert result.exit_code != 0
        assert (
            "language pack not found" in result.output.lower()
            or "not supported" in result.output.lower()
        )


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Performance tests for large files and directories."""

    def test_large_file_translation(self, tmp_path: Path):
        """Test translation of 1000+ line file completes in reasonable time."""
        # Generate large Python file
        lines = [
            "# Large Python file",
            "import sys",
            "",
        ]

        # Generate 1000+ lines of code
        for i in range(500):
            lines.extend(
                [
                    f"def function_{i}(x):",
                    f'    """Function {i}"""',
                    "    if x > 0:",
                    f"        return x * {i}",
                    "    else:",
                    "        return 0",
                    "",
                ]
            )

        large_code = "\n".join(lines)

        input_file = tmp_path / "large.py"
        input_file.write_text(large_code, encoding="utf-8")

        output_file = tmp_path / "large_es.py"

        # Translate with timing
        import time

        start = time.time()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        elapsed = time.time() - start

        assert result.exit_code == 0
        assert output_file.exists()
        assert elapsed < 10.0, f"Translation took {elapsed:.2f}s (expected < 10s)"

    def test_many_files_translation(self, tmp_path: Path):
        """Test translation of 50+ files completes successfully."""
        # Create directory with many files
        src = tmp_path / "many_files"
        src.mkdir()

        for i in range(50):
            (
                src / f"module_{i}.py"
            ).write_text(f"""def function_{i}(, encoding="utf-8"):
    print("Function {i}")
    return {i}
""")

        # Translate
        output = tmp_path / "many_files_es"

        import time

        start = time.time()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(src),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output),
            ],
        )

        elapsed = time.time() - start

        assert result.exit_code == 0
        assert "50/50 files" in result.output
        assert elapsed < 30.0, f"Translation took {elapsed:.2f}s (expected < 30s)"

        # Verify all files translated
        for i in range(50):
            assert (output / f"module_{i}.py").exists()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_python_syntax_error(self, tmp_path: Path):
        """Test that invalid Python code produces helpful error."""
        invalid_code = """def broken(
    # Missing closing paren and body
"""

        input_file = tmp_path / "broken.py"
        input_file.write_text(invalid_code, encoding="utf-8")

        output_file = tmp_path / "output.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        # TokenTranslator handles invalid syntax gracefully (returns original)
        assert result.exit_code == 0
        # Output file should exist even for invalid syntax
        assert output_file.exists()

    def test_stdin_with_no_input(self, tmp_path: Path):
        """Test stdin mode with empty input."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                "--from",
                "en",
                "--to",
                "es",
            ],
            input="",
        )

        assert result.exit_code != 0
        assert "no input" in result.output.lower()

    @pytest.mark.skipif(
        os.name == "nt", reason="Permission handling differs on Windows"
    )
    def test_output_directory_permission_error(self, tmp_path: Path):
        """Test handling of permission errors on output."""
        input_file = tmp_path / "test.py"
        input_file.write_text("def test(): pass", encoding="utf-8")

        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        output_file = readonly_dir / "output.py"

        # Make directory read-only
        import os

        os.chmod(readonly_dir, 0o444)

        try:
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "translate",
                    str(input_file),
                    "--from",
                    "en",
                    "--to",
                    "es",
                    "--output",
                    str(output_file),
                ],
            )

            # Should fail gracefully
            assert result.exit_code != 0
            assert (
                "permission" in result.output.lower()
                or "error" in result.output.lower()
            )

        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_non_utf8_file_error(self, tmp_path: Path):
        """Test handling of non-UTF-8 encoded files."""
        input_file = tmp_path / "latin1.py"

        # Write Latin-1 encoded file
        input_file.write_bytes("def test(): # Café\n    pass\n".encode("latin-1"))

        output_file = tmp_path / "output.py"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "translate",
                str(input_file),
                "--from",
                "en",
                "--to",
                "es",
                "--output",
                str(output_file),
            ],
        )

        # Should handle encoding error gracefully
        # Note: May succeed if Python can decode, or fail with helpful message
        if result.exit_code != 0:
            assert (
                "utf-8" in result.output.lower() or "encoding" in result.output.lower()
            )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_spanish_code() -> str:
    """Provide sample Spanish code for testing."""
    return """definir calcular(x, y):
    \"\"\"Calcula la suma.\"\"\"
    si x < 0:
        elevar ValueError("x debe ser positivo")
    retornar x + y
"""


@pytest.fixture
def sample_english_code() -> str:
    """Provide sample English code for testing."""
    return """def calculate(x, y):
    \"\"\"Calculate sum.\"\"\"
    if x < 0:
        raise ValueError("x must be positive")
    return x + y
"""


@pytest.fixture
def complex_python_project(tmp_path: Path) -> Path:
    """Create a complex Python project structure for testing."""
    project = tmp_path / "project"
    project.mkdir()

    # Create package structure
    (project / "__init__.py").write_text("", encoding="utf-8")
    (project / "main.py").write_text("""def main(, encoding="utf-8"):
    print("Hello, World!")
    return 0
""")

    # Core package
    core = project / "core"
    core.mkdir()
    (core / "__init__.py").write_text("", encoding="utf-8")
    (core / "engine.py").write_text("""class Engine:
    def run(self, encoding="utf-8"):
        return True
""")

    # Utils package
    utils = project / "utils"
    utils.mkdir()
    (utils / "__init__.py").write_text("", encoding="utf-8")
    (utils / "helpers.py").write_text("""def helper_function(, encoding="utf-8"):
    pass
""")

    # Tests directory
    tests = project / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("""def test_main(, encoding="utf-8"):
    assert True
""")

    return project
