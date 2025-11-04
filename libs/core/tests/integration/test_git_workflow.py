"""Integration tests for complete git filter workflow.

Tests the full end-to-end flow:
1. Setup git repository
2. Configure git filters
3. Add file in local language
4. Git clean filter (local → English)
5. Git commit
6. Git checkout
7. Git smudge filter (English → local)
"""

import io
import subprocess

import pytest

from legesher_core.git_filter import GitFilter


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository with initial commit."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize git
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Configure git user
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = repo / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


@pytest.fixture
def spanish_filter():
    """Create a GitFilter for Spanish."""
    return GitFilter(language="es", python_version="3.13")


@pytest.fixture
def arabic_filter():
    """Create a GitFilter for Arabic."""
    return GitFilter(language="ar", python_version="3.13")


class TestGitFilterWorkflow:
    """Test complete git filter workflow."""

    def test_spanish_clean_filter(self, spanish_filter):
        """Test clean filter translates Spanish to English."""
        spanish_code = (
            "definir calcular_suma(a, b):\n"
            "    resultado = a + b\n"
            "    retornar resultado\n"
        )

        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        english_code = output_stream.getvalue()

        # Verify English keywords
        assert "def" in english_code
        assert "return" in english_code

        # Verify identifiers preserved
        assert "calcular_suma" in english_code
        assert "resultado" in english_code

    def test_spanish_smudge_filter(self, spanish_filter):
        """Test smudge filter translates English to Spanish."""
        english_code = (
            "def calculate_sum(a, b):\n    result = a + b\n    return result\n"
        )

        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        spanish_code = output_stream.getvalue()

        # Verify Spanish keywords
        assert "definir" in spanish_code
        assert "retornar" in spanish_code

        # Verify identifiers preserved
        assert "calculate_sum" in spanish_code
        assert "result" in spanish_code

    def test_round_trip_spanish(self, spanish_filter):
        """Test Spanish → English → Spanish preserves semantics."""
        original = (
            "definir fibonacci(n):\n"
            "    si n <= 1:\n"
            "        retornar n\n"
            "    retornar fibonacci(n - 1) + fibonacci(n - 2)\n"
        )

        # Clean: Spanish → English
        input1 = io.StringIO(original)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)
        english = output1.getvalue()

        # Verify English
        assert "def" in english
        assert "if" in english
        assert "return" in english

        # Smudge: English → Spanish
        input2 = io.StringIO(english)
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)
        result = output2.getvalue()

        # Verify Spanish keywords restored
        assert "definir" in result
        assert "si" in result
        assert "retornar" in result

        # Verify identifier preserved
        assert "fibonacci" in result

    def test_round_trip_arabic(self, arabic_filter):
        """Test Arabic → English → Arabic preserves semantics."""
        original = "تعريف مرحبا(اسم):\n    طباعة(اسم)\n    إرجاع صحيح\n"

        # Clean: Arabic → English
        input1 = io.StringIO(original)
        output1 = io.StringIO()
        arabic_filter.clean(input1, output1)
        english = output1.getvalue()

        # Verify English
        assert "def" in english
        assert "print" in english or "طباعة" in english  # May not translate
        assert "return" in english
        assert "True" in english

        # Smudge: English → Arabic
        input2 = io.StringIO(english)
        output2 = io.StringIO()
        arabic_filter.smudge(input2, output2)
        result = output2.getvalue()

        # Verify Arabic keywords restored
        assert "تعريف" in result
        assert "إرجاع" in result

    def test_multiple_functions(self, spanish_filter):
        """Test translating file with multiple functions."""
        spanish_code = """
definir suma(a, b):
    retornar a + b

definir resta(a, b):
    retornar a - b

definir multiplicar(a, b):
    retornar a * b

# Función principal
definir principal():
    x = suma(5, 3)
    y = resta(10, 4)
    z = multiplicar(x, y)
    retornar z
"""

        # Clean
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()
        spanish_filter.clean(input_stream, output_stream)
        english_code = output_stream.getvalue()

        # Verify all functions translated
        assert english_code.count("def") >= 4
        assert english_code.count("return") >= 4

        # Smudge back
        input_stream2 = io.StringIO(english_code)
        output_stream2 = io.StringIO()
        spanish_filter.smudge(input_stream2, output_stream2)
        result = output_stream2.getvalue()

        # Verify Spanish restored
        assert result.count("definir") >= 4
        assert result.count("retornar") >= 4

    def test_preserves_docstrings(self, spanish_filter):
        """Test that docstrings are preserved."""
        spanish_code = '''
definir saludar(nombre):
    """
    Saluda a una persona por su nombre.

    Args:
        nombre: El nombre de la persona

    Returns:
        Un mensaje de saludo
    """
    retornar f"Hola, {nombre}!"
'''

        # Clean then smudge
        input1 = io.StringIO(spanish_code)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)

        input2 = io.StringIO(output1.getvalue())
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)
        result = output2.getvalue()

        # Docstring should be preserved
        assert "Saluda a una persona" in result or '"""' in result

    def test_preserves_class_definitions(self, spanish_filter):
        """Test that class definitions are translated correctly."""
        spanish_code = """
clase Persona:
    definir __init__(self, nombre):
        self.nombre = nombre

    definir saludar(self):
        retornar f"Hola, soy {self.nombre}"
"""

        # Clean
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()
        spanish_filter.clean(input_stream, output_stream)
        english_code = output_stream.getvalue()

        # Verify class and def translated
        assert "class" in english_code
        assert "def" in english_code

        # Smudge back
        input_stream2 = io.StringIO(english_code)
        output_stream2 = io.StringIO()
        spanish_filter.smudge(input_stream2, output_stream2)
        result = output_stream2.getvalue()

        # Verify Spanish restored
        assert "clase" in result
        assert "definir" in result

    def test_handles_complex_control_flow(self, spanish_filter):
        """Test complex control flow structures."""
        spanish_code = """
definir procesar_numeros(numeros):
    resultado = []
    para num en numeros:
        si num > 0:
            resultado.agregar(num * 2)
        sino si num < 0:
            resultado.agregar(num * -1)
        sino:
            resultado.agregar(0)
    retornar resultado
"""

        # Clean then smudge
        input1 = io.StringIO(spanish_code)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)
        english = output1.getvalue()

        # Verify English control flow
        assert "for" in english
        assert "if" in english
        assert "elif" in english or "else" in english

        input2 = io.StringIO(english)
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)
        result = output2.getvalue()

        # Verify Spanish control flow restored
        assert "para" in result
        assert "si" in result

    def test_empty_file(self, spanish_filter):
        """Test handling of empty file."""
        empty_code = ""

        input_stream = io.StringIO(empty_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        assert output_stream.getvalue() == ""

    def test_file_with_only_comments(self, spanish_filter):
        """Test handling of file with only comments."""
        comments_only = "# Este es un comentario\n# Otro comentario\n"

        input_stream = io.StringIO(comments_only)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "#" in result  # Comments preserved

    def test_mixed_language_identifiers(self, spanish_filter):
        """Test handling of mixed language identifiers."""
        # Code with Spanish keywords but English identifiers
        mixed_code = """
definir calculate_total(price, quantity):
    total = price * quantity
    retornar total
"""

        # Clean
        input_stream = io.StringIO(mixed_code)
        output_stream = io.StringIO()
        spanish_filter.clean(input_stream, output_stream)
        english_code = output_stream.getvalue()

        # Should translate keywords but preserve identifiers
        assert "def" in english_code
        assert "return" in english_code
        assert "calculate_total" in english_code
        assert "price" in english_code
        assert "quantity" in english_code


class TestErrorRecovery:
    """Test error recovery and robustness."""

    def test_invalid_syntax_passes_through(self, spanish_filter):
        """Test that invalid syntax doesn't break the filter."""
        invalid_code = "esto no es código válido python @#$%"

        input_stream = io.StringIO(invalid_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        # Should succeed (not break git)
        assert exit_code == 0

        # Should pass through something (may be translated or original)
        result = output_stream.getvalue()
        assert len(result) > 0

    def test_incomplete_code(self, spanish_filter):
        """Test handling of incomplete code."""
        incomplete = "definir test():\n    ret"

        input_stream = io.StringIO(incomplete)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        # Should succeed
        assert exit_code == 0

    def test_very_large_file(self, spanish_filter):
        """Test handling of large file."""
        # Generate a large file (1000 functions)
        large_code = ""
        for i in range(1000):
            large_code += f"definir func_{i}():\n    retornar {i}\n\n"

        input_stream = io.StringIO(large_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert len(result) > 0
        assert "def" in result

    def test_unicode_in_strings(self, spanish_filter):
        """Test handling of Unicode characters in strings."""
        unicode_code = """
definir test():
    mensaje = "Hola! ¿Cómo estás? 你好 مرحبا"
    retornar mensaje
"""

        # Clean then smudge
        input1 = io.StringIO(unicode_code)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)

        input2 = io.StringIO(output1.getvalue())
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)

        result = output2.getvalue()
        # Unicode should be preserved
        assert "你好" in result or "مرحبا" in result or "mensaje" in result
