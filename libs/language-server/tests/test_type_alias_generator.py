"""Tests for type alias generation for localized type hints.

Tests the TypeAliasGenerator which creates Python TypeAlias statements
to preserve localized type hint names while maintaining type-checker compatibility.

Test for CORE-360 - enhanced Python intelligence.
"""

from legesher_language_server.type_alias_generator import TypeAlias, TypeAliasGenerator


class TestTypeAliasGenerator:
    """Test TypeAliasGenerator for creating type aliases."""

    def test_spanish_type_mapping(self):
        """Test default Spanish type mappings."""
        generator = TypeAliasGenerator(target_lang="es")

        assert generator.translate_type_name("entero") == "int"
        assert generator.translate_type_name("cadena") == "str"
        assert generator.translate_type_name("flotante") == "float"
        assert generator.translate_type_name("booleano") == "bool"
        assert generator.translate_type_name("lista") == "list"

    def test_arabic_type_mapping(self):
        """Test default Arabic type mappings."""
        generator = TypeAliasGenerator(target_lang="ar")

        assert generator.translate_type_name("صحيح") == "int"
        assert generator.translate_type_name("نص") == "str"
        assert generator.translate_type_name("عائم") == "float"

    def test_custom_type_mapping(self):
        """Test custom type mapping."""
        custom_map = {"entier": "int", "chaine": "str"}
        generator = TypeAliasGenerator(target_lang="fr", type_mapping=custom_map)

        assert generator.translate_type_name("entier") == "int"
        assert generator.translate_type_name("chaine") == "str"

    def test_extract_simple_type_hints(self):
        """Test extracting simple type hints from code."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x: entero, y: cadena) -> booleano:
    return True
"""

        result = generator.generate_with_aliases(code)

        # Should generate aliases for all three types
        assert "entero: TypeAlias = int" in result
        assert "cadena: TypeAlias = str" in result
        assert "booleano: TypeAlias = bool" in result
        assert "from typing import TypeAlias" in result

    def test_extract_generic_type_hints(self):
        """Test extracting generic type hints (List[int], etc)."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def process(items: Lista[entero]) -> Opcional[cadena]:
    return None
"""

        result = generator.generate_with_aliases(code)

        assert "Lista: TypeAlias = List" in result
        assert "entero: TypeAlias = int" in result
        assert "Opcional: TypeAlias = Optional" in result
        assert "cadena: TypeAlias = str" in result

    def test_no_aliases_for_english_types(self):
        """Test that English types don't generate aliases."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x: int, y: str) -> bool:
    return True
"""

        result = generator.generate_with_aliases(code)

        # No aliases should be generated for English types
        assert "int: TypeAlias" not in result
        assert "str: TypeAlias" not in result
        assert "from typing import TypeAlias" not in result

    def test_mixed_localized_and_english_types(self):
        """Test code with both localized and English types."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x: entero, y: int, z: cadena) -> bool:
    return True
"""

        result = generator.generate_with_aliases(code)

        # Only localized types get aliases
        assert "entero: TypeAlias = int" in result
        assert "cadena: TypeAlias = str" in result
        assert "int: TypeAlias" not in result
        assert "bool: TypeAlias" not in result

    def test_variable_type_annotations(self):
        """Test type annotations on variables."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
x: entero = 42
name: cadena = "test"
"""

        result = generator.generate_with_aliases(code)

        assert "entero: TypeAlias = int" in result
        assert "cadena: TypeAlias = str" in result

    def test_no_duplicate_aliases(self):
        """Test that duplicate type usages only create one alias."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x: entero, y: entero) -> entero:
    return x + y
"""

        result = generator.generate_with_aliases(code)

        # Should only have one alias for entero
        alias_count = result.count("entero: TypeAlias = int")
        assert alias_count == 1

    def test_invalid_syntax_graceful_degradation(self):
        """Test that invalid syntax returns code as-is."""
        generator = TypeAliasGenerator(target_lang="es")

        code = "def foo(x: entero"  # Incomplete, invalid syntax

        result = generator.generate_with_aliases(code)

        # Should return original code unchanged
        assert result == code

    def test_no_type_hints_returns_unchanged(self):
        """Test code without type hints returns unchanged."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x, y):
    return x + y
"""

        result = generator.generate_with_aliases(code)

        # No aliases needed, should be unchanged
        assert result == code

    def test_alias_block_formatting(self):
        """Test that alias block is properly formatted."""
        generator = TypeAliasGenerator(target_lang="es")

        code = "def foo(x: entero) -> cadena:\n    pass"

        result = generator.generate_with_aliases(code)

        # Check structure
        lines = result.split("\n")
        assert lines[0] == "from typing import TypeAlias"
        assert lines[1] == ""  # Blank line after import
        assert "cadena: TypeAlias = str" in result
        assert "entero: TypeAlias = int" in result

        # Aliases should be sorted alphabetically
        cadena_idx = result.index("cadena: TypeAlias")
        entero_idx = result.index("entero: TypeAlias")
        assert cadena_idx < entero_idx

    def test_union_types(self):
        """Test Union type hints."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
from typing import Union
def foo(x: Union[entero, cadena]) -> entero:
    return 0
"""

        result = generator.generate_with_aliases(code)

        assert "entero: TypeAlias = int" in result
        assert "cadena: TypeAlias = str" in result

    def test_string_annotations(self):
        """Test forward reference string annotations."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def foo(x: "entero") -> "cadena":
    return "test"
"""

        result = generator.generate_with_aliases(code)

        assert "entero: TypeAlias = int" in result
        assert "cadena: TypeAlias = str" in result

    def test_is_localized_type(self):
        """Test checking if a name is a localized type."""
        generator = TypeAliasGenerator(target_lang="es")

        assert generator.is_localized_type("entero") is True
        assert generator.is_localized_type("cadena") is True
        assert generator.is_localized_type("int") is False
        assert generator.is_localized_type("str") is False
        assert generator.is_localized_type("unknown") is False

    def test_get_alias_mapping(self):
        """Test getting all configured aliases."""
        generator = TypeAliasGenerator(target_lang="es")

        aliases = generator.get_alias_mapping()

        assert isinstance(aliases, dict)
        assert "entero" in aliases
        assert aliases["entero"] == TypeAlias(localized_name="entero", english_name="int")
        assert aliases["cadena"] == TypeAlias(localized_name="cadena", english_name="str")


class TestRealWorldScenarios:
    """Test real-world code scenarios."""

    def test_complete_spanish_function(self):
        """Test complete Spanish function with multiple type hints."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def calcular_impuesto(ingreso: flotante, tasa: flotante) -> flotante:
    '''Calcula el impuesto basado en el ingreso y la tasa.'''
    return ingreso * tasa
"""

        result = generator.generate_with_aliases(code)

        # Check aliases generated
        assert "from typing import TypeAlias" in result
        assert "flotante: TypeAlias = float" in result

        # Original code should be preserved
        assert "def calcular_impuesto(ingreso: flotante, tasa: flotante) -> flotante:" in result
        assert "return ingreso * tasa" in result

    def test_class_with_type_hints(self):
        """Test class with typed attributes and methods."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
class Persona:
    nombre: cadena
    edad: entero

    def __init__(self, nombre: cadena, edad: entero):
        self.nombre = nombre
        self.edad = edad

    def es_adulto(self) -> booleano:
        return self.edad >= 18
"""

        result = generator.generate_with_aliases(code)

        assert "cadena: TypeAlias = str" in result
        assert "entero: TypeAlias = int" in result
        assert "booleano: TypeAlias = bool" in result

        # Original class structure preserved
        assert "class Persona:" in result
        assert "def __init__" in result

    def test_complex_generic_types(self):
        """Test complex generic types like List[Dict[str, int]]."""
        generator = TypeAliasGenerator(target_lang="es")

        code = """
def process_data(
    items: Lista[Diccionario[cadena, entero]]
) -> Opcional[Lista[entero]]:
    return None
"""

        result = generator.generate_with_aliases(code)

        # All used types should have aliases
        assert "Lista: TypeAlias = List" in result
        assert "Diccionario: TypeAlias = Dict" in result
        assert "cadena: TypeAlias = str" in result
        assert "entero: TypeAlias = int" in result
        assert "Opcional: TypeAlias = Optional" in result

    def test_type_alias_preserves_semantics(self):
        """Test that generated code is valid Python with aliases."""
        generator = TypeAliasGenerator(target_lang="es")

        original_code = """
def sumar(a: entero, b: entero) -> entero:
    return a + b
"""

        result = generator.generate_with_aliases(original_code)

        # Result should be valid Python that tools like Pyright can understand
        assert result.startswith("from typing import TypeAlias")
        assert "entero: TypeAlias = int" in result
        assert "def sumar(a: entero, b: entero) -> entero:" in result

        # The function signature is preserved with localized names
        # But the type checker will understand 'entero' as 'int' via the TypeAlias
