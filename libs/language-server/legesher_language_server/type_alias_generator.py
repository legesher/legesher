"""Type alias generation for localized type hints.

This module generates Python TypeAlias statements to preserve localized
type hint names while maintaining compatibility with Pylance's type checker.

For example, if a Spanish developer writes:
    def foo(x: entero) -> cadena:
        return str(x)

We generate:
    from typing import TypeAlias
    entero: TypeAlias = int
    cadena: TypeAlias = str

    def foo(x: entero) -> cadena:
        return str(x)

This allows Pylance to understand the types while preserving the user's
localized type names in error messages.

Implementation for CORE-360 - Pylance Integration.
"""

import ast
import re
from typing import NamedTuple

# Common Python type names that may be localized
BUILTIN_TYPES = {
    "int",
    "str",
    "float",
    "bool",
    "list",
    "dict",
    "tuple",
    "set",
    "frozenset",
    "bytes",
    "bytearray",
    "type",
    "object",
    "None",
}

TYPING_TYPES = {
    "List",
    "Dict",
    "Tuple",
    "Set",
    "FrozenSet",
    "Optional",
    "Union",
    "Any",
    "Callable",
    "Iterable",
    "Iterator",
    "Sequence",
    "Mapping",
    "TypeVar",
    "Generic",
}


class TypeAlias(NamedTuple):
    """A type alias mapping.

    Attributes:
        localized_name: The localized type name (e.g., 'entero')
        english_name: The English type name (e.g., 'int')
    """

    localized_name: str
    english_name: str


class TypeAliasGenerator:
    """Generates TypeAlias statements for localized type hints.

    This class scans Python code for localized type hints and generates
    the necessary TypeAlias imports to make them valid Python that
    Pylance can type-check.

    Example:
        >>> generator = TypeAliasGenerator(target_lang='es')
        >>> code = "def foo(x: entero) -> cadena: pass"
        >>> augmented = generator.generate_with_aliases(code)
        >>> print(augmented)
        from typing import TypeAlias

        entero: TypeAlias = int
        cadena: TypeAlias = str

        def foo(x: entero) -> cadena: pass
    """

    def __init__(self, target_lang: str, type_mapping: dict[str, str] | None = None):
        """Initialize type alias generator.

        Args:
            target_lang: Target language code (e.g., 'es', 'ar')
            type_mapping: Optional custom type mapping from localized to English.
                         If None, will use default mappings for the language.
        """
        self.target_lang = target_lang
        self.type_mapping = type_mapping or self._load_default_mapping(target_lang)

    def _load_default_mapping(self, lang: str) -> dict[str, str]:
        """Load default type mappings for a language.

        Args:
            lang: Language code

        Returns:
            Dictionary mapping localized type names to English
        """
        # Spanish mappings
        if lang == "es":
            return {
                "entero": "int",
                "cadena": "str",
                "flotante": "float",
                "booleano": "bool",
                "lista": "list",
                "diccionario": "dict",
                "tupla": "tuple",
                "conjunto": "set",
                "bytes": "bytes",
                "ninguno": "None",
                "Lista": "List",
                "Diccionario": "Dict",
                "Tupla": "Tuple",
                "Conjunto": "Set",
                "Opcional": "Optional",
                "Union": "Union",
                "Cualquiera": "Any",
                "Llamable": "Callable",
            }
        # Arabic mappings
        elif lang == "ar":
            return {
                "صحيح": "int",
                "نص": "str",
                "عائم": "float",
                "منطقي": "bool",
                "قائمة": "list",
                "قاموس": "dict",
                "صف": "tuple",
                "مجموعة": "set",
            }
        else:
            # Default: empty mapping (no localized types)
            return {}

    def generate_with_aliases(self, code: str) -> str:
        """Generate code with TypeAlias statements prepended.

        Args:
            code: Original Python code with localized type hints

        Returns:
            Code with TypeAlias imports and statements prepended,
            or original code if it cannot be parsed (graceful degradation)
        """
        # Extract all localized type hints from code
        localized_types = self._extract_type_hints(code)

        if not localized_types:
            # No localized types found, return as-is
            return code

        # Generate alias block
        alias_block = self._generate_alias_block(localized_types)

        # Prepend to code
        return f"{alias_block}\n{code}"

    def _extract_type_hints(self, code: str) -> set[str]:
        """Extract all type hint names from code.

        Args:
            code: Python source code

        Returns:
            Set of type hint names that match localized types
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Can't parse - return empty set (graceful degradation)
            return set()

        type_hints = set()

        # Walk AST to find type annotations
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check argument annotations
                for arg in node.args.args:
                    if arg.annotation:
                        type_hints.update(self._extract_names_from_annotation(arg.annotation))

                # Check return annotation
                if node.returns:
                    type_hints.update(self._extract_names_from_annotation(node.returns))

            elif isinstance(node, ast.AnnAssign):
                # Variable annotations
                if node.annotation:
                    type_hints.update(self._extract_names_from_annotation(node.annotation))

        # Filter to only localized types we know about
        return {t for t in type_hints if t in self.type_mapping}

    def _extract_names_from_annotation(self, annotation: ast.expr) -> set[str]:
        """Extract all names from a type annotation node.

        Args:
            annotation: AST annotation node

        Returns:
            Set of identifier names in the annotation
        """
        names = set()

        if isinstance(annotation, ast.Name):
            names.add(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            # Handle parameterized types like List[int]
            names.update(self._extract_names_from_annotation(annotation.value))
            names.update(self._extract_names_from_annotation(annotation.slice))
        elif isinstance(annotation, ast.Tuple):
            # Handle tuple of types
            for elt in annotation.elts:
                names.update(self._extract_names_from_annotation(elt))
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            # Handle Union syntax with | (PEP 604)
            names.update(self._extract_names_from_annotation(annotation.left))
            names.update(self._extract_names_from_annotation(annotation.right))
        elif isinstance(annotation, ast.Constant):
            # String annotations (forward references)
            if isinstance(annotation.value, str):
                # Parse string annotation
                names.update(self._extract_names_from_string_annotation(annotation.value))

        return names

    def _extract_names_from_string_annotation(self, annotation_str: str) -> set[str]:
        """Extract type names from string annotation.

        Args:
            annotation_str: String containing type annotation

        Returns:
            Set of identifier names
        """
        # Simple regex to extract identifiers
        # This is a heuristic - not perfect but good enough for most cases
        pattern = r"\b([A-Za-z_\u0080-\uFFFF][A-Za-z0-9_\u0080-\uFFFF]*)\b"
        names = set(re.findall(pattern, annotation_str))

        # Filter to only localized types
        return {n for n in names if n in self.type_mapping}

    def _generate_alias_block(self, localized_types: set[str]) -> str:
        """Generate TypeAlias block for localized types.

        Args:
            localized_types: Set of localized type names found in code

        Returns:
            String containing import and TypeAlias statements
        """
        lines = ["from typing import TypeAlias", ""]

        # Sort for deterministic output
        for localized_type in sorted(localized_types):
            english_type = self.type_mapping[localized_type]
            lines.append(f"{localized_type}: TypeAlias = {english_type}")

        lines.append("")  # Blank line before code
        return "\n".join(lines)

    def get_alias_mapping(self) -> dict[str, TypeAlias]:
        """Get all configured type aliases.

        Returns:
            Dictionary mapping localized names to TypeAlias objects
        """
        return {
            local: TypeAlias(localized_name=local, english_name=english)
            for local, english in self.type_mapping.items()
        }

    def is_localized_type(self, name: str) -> bool:
        """Check if a name is a known localized type.

        Args:
            name: Type name to check

        Returns:
            True if name is a localized type in the mapping
        """
        return name in self.type_mapping

    def translate_type_name(self, localized_name: str) -> str | None:
        """Translate a localized type name to English.

        Args:
            localized_name: Localized type name

        Returns:
            English type name or None if not found
        """
        return self.type_mapping.get(localized_name)
