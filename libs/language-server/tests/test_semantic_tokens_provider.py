"""Tests for semantic tokens provider (CORE-450, CORE-709, CORE-895).

Tests cover:
- Basic keyword highlighting for Spanish, Arabic, Chinese
- Builtin highlighting (CORE-709)
- Exception highlighting (CORE-709)
- Context-aware: class names, function names, first param (CORE-895)
- Edge cases: strings, comments, mixed languages
- Token encoding correctness
- Performance requirements (<100ms for 1000 lines)
"""

import time

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.providers.semantic_tokens import (
    TOKEN_TYPE_CLASS,
    TOKEN_TYPE_FUNCTION,
    TOKEN_TYPE_KEYWORD,
    TOKEN_TYPE_PARAMETER,
    SemanticTokensProvider,
    provide_semantic_tokens,
)
from legesher_language_server.server import LegesherLanguageServer


class TestSemanticTokensProvider:
    """Tests for SemanticTokensProvider class."""

    def test_spanish_keywords_basic(self):
        """Test basic Spanish keyword highlighting."""
        code = """definir saludar():
    devolver "Hola"

clase MiClase:
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        # Force load keyword mappings
        provider._load_token_mappings()

        # Get tokens (synchronous)
        tokens = provider.get_semantic_tokens()

        # Should find: definir, saludar, devolver, clase, MiClase, pasar
        assert len(tokens) == 6

        # Verify first token (definir) — keyword
        line, char, length, token_type, modifiers = tokens[0]
        assert line == 0
        assert char == 0
        assert length == len("definir")
        assert token_type == TOKEN_TYPE_KEYWORD
        assert modifiers == 0

        # Second token (saludar) — function name after def
        assert tokens[1][3] == TOKEN_TYPE_FUNCTION

        # clase — keyword, MiClase — class name
        class_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        assert len(class_tokens) == 1
        assert class_tokens[0][2] == len("MiClase")

    def test_arabic_keywords_basic(self):
        """Test basic Arabic keyword highlighting."""
        code = """تعريف مرحبا():
    إرجاع "مرحبا"
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="ar",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should find: تعريف (def), مرحبا (func name), إرجاع (return)
        assert len(tokens) == 3
        assert tokens[0][3] == TOKEN_TYPE_KEYWORD  # تعريف
        assert tokens[1][3] == TOKEN_TYPE_FUNCTION  # مرحبا (func name)
        assert tokens[2][3] == TOKEN_TYPE_KEYWORD  # إرجاع

    def test_keywords_in_strings_ignored(self):
        """Test that keywords inside strings are NOT highlighted."""
        code = """definir test():
    resultado = "definir devolver clase"
    devolver resultado
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should find: definir (keyword), test (func name), devolver (keyword)
        # Not the keywords inside the string
        assert len(tokens) == 3

        # Verify no tokens are on the string line
        for line, _char, _length, _token_type, _modifiers in tokens:
            assert line != 1  # Line 1 has the string

    def test_keywords_in_comments_ignored(self):
        """Test that keywords inside comments are NOT highlighted."""
        code = """# Este es un comentario con definir y devolver
definir test():
    # Otro comentario con clase
    devolver 42
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should find: definir, test (func name), devolver (not the ones in comments)
        assert len(tokens) == 3

        # Verify first token is on line 1 (not line 0 which is comment)
        assert tokens[0][0] == 1

    def test_mixed_english_spanish(self):
        """Test mixed English and Spanish code."""
        code = """def english_func():
    return 42

definir spanish_func():
    devolver 43
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should find: def, english_func, return, definir, spanish_func, devolver
        assert len(tokens) == 6
        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        assert len(func_tokens) == 2  # english_func, spanish_func

    def test_multiline_statements(self):
        """Test keywords in multiline statements."""
        code = """si (
    condicion1 y
    condicion2
):
    devolver verdadero
sino:
    devolver falso
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should find: si, y, devolver, verdadero, sino, devolver, falso
        assert len(tokens) == 7

    def test_syntax_error_handling(self):
        """Test that syntax errors don't crash the provider."""
        code = """definir broken(
    # Missing closing paren
    devolver
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should return partial tokens collected before error
        # At minimum should find 'definir'
        assert len(tokens) >= 1

    def test_empty_document(self):
        """Test empty document returns no tokens."""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        assert len(tokens) == 0

    def test_token_encoding_delta_format(self):
        """Test that tokens are correctly encoded in LSP delta format."""
        code = """definir test():
    devolver 42
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()
        encoded = provider.encode_tokens(tokens)

        # 3 tokens × 5 integers: definir, test, devolver
        assert len(encoded) == 15

        # First token: definir at line 0, char 0
        assert encoded[0] == 0  # deltaLine
        assert encoded[1] == 0  # deltaChar
        assert encoded[2] == len("definir")  # length
        assert encoded[3] == TOKEN_TYPE_KEYWORD  # token type
        assert encoded[4] == 0  # modifiers

        # Second token: test at line 0, char 8 (function name after def)
        assert encoded[5] == 0  # deltaLine (same line)
        assert encoded[6] == 8  # deltaChar (relative: 8 - 0 = 8)
        assert encoded[7] == len("test")  # length
        assert encoded[8] == TOKEN_TYPE_FUNCTION  # function name

        # Third token: devolver at line 1, char 4
        assert encoded[10] == 1  # deltaLine (new line)
        assert encoded[11] == 4  # deltaChar (absolute on new line)
        assert encoded[12] == len("devolver")  # length
        assert encoded[13] == TOKEN_TYPE_KEYWORD

    def test_same_line_tokens_delta(self):
        """Test delta encoding for multiple tokens on same line."""
        code = """si condicion1 y condicion2:"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()
        encoded = provider.encode_tokens(tokens)

        # Should have: si, y
        assert len(tokens) == 2

        # First token: si at (0, 0)
        assert encoded[0] == 0  # deltaLine
        assert encoded[1] == 0  # deltaChar

        # Second token: y at (0, 14) - same line
        # Delta from previous: deltaLine=0, deltaChar=(14-0)=14
        assert encoded[5] == 0  # deltaLine (same line)
        assert encoded[6] == 14  # deltaChar (relative to previous token start)

    def test_invalid_language_pack(self):
        """Test handling of invalid language code."""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="invalid",  # Invalid language
            document_text="def test(): pass",
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Should return empty list (no keywords loaded)
        assert len(tokens) == 0

    def test_performance_large_file(self):
        """Test performance requirement: <100ms for 1000 lines."""
        # Generate 1000-line file with keywords
        lines = []
        for i in range(250):  # 250 functions × 4 lines = 1000 lines
            lines.append(f"definir func_{i}():")
            lines.append("    si verdadero:")
            lines.append(f"        devolver {i}")
            lines.append("")

        code = "\n".join(lines)
        # Note: splitlines() counts 999 because final line is empty
        assert len(code.splitlines()) >= 999

        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()

        # Measure time
        start = time.perf_counter()
        tokens = provider.get_semantic_tokens()
        _encoded = provider.encode_tokens(tokens)  # Verify encoding works
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify encoding worked
        assert _encoded is not None, "Encoded tokens should not be None"
        assert isinstance(_encoded, (list, tuple)), (
            f"Encoded tokens should be a list or tuple, got {type(_encoded)}"
        )

        # Verify tokens were found
        # 250 functions × (definir, func_N, si, verdadero, devolver) = 1250 tokens
        assert len(tokens) == 1250

        # Performance requirement: <100ms
        assert elapsed_ms < 100, f"Performance requirement failed: {elapsed_ms:.2f}ms"

        print(f"✓ Performance test passed: {elapsed_ms:.2f}ms for 1000 lines")

    def test_spanish_builtins_highlighted(self):
        """Test that translated builtins get correct token types (CORE-709).

        Builtin functions (print→imprimir) get TOKEN_TYPE_FUNCTION (yellow).
        Builtin types (float→flotante) get TOKEN_TYPE_CLASS (teal).
        """
        code = """imprimir("hola")
x = flotante(3)
z = entrada("prompt")
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # imprimir (print) and entrada (input) are builtin functions → FUNCTION
        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        assert len(func_tokens) == 2

        # flotante (float) is a builtin type → CLASS
        type_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        assert len(type_tokens) == 1

    def test_spanish_exceptions_highlighted(self):
        """Test that translated exceptions get TOKEN_TYPE_CLASS (CORE-709)."""
        code = """probar:
    pasar
excepto errordevalor:
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Find the exception token
        exception_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        assert len(exception_tokens) >= 1

        # Verify errordevalor is classified as CLASS
        error_token = exception_tokens[0]
        assert error_token[2] == len("errordevalor")  # length

    def test_mixed_keywords_builtins_exceptions(self):
        """Test all three token categories in one function (CORE-709)."""
        code = """definir procesar():
    probar:
        imprimir(flotante(entrada("num")))
    excepto errordevalor:
        devolver nulo
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        keyword_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_KEYWORD]
        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        class_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]

        # Keywords: definir, probar, excepto, devolver, nulo
        assert len(keyword_tokens) >= 5
        # FUNCTION tokens: procesar (func name) + imprimir, entrada (builtins)
        assert len(func_tokens) >= 3
        # CLASS tokens: errordevalor (exception) + flotante (builtin type)
        assert len(class_tokens) >= 2

    def test_english_builtins_in_mixed_code(self):
        """Test English builtins are highlighted when target is Spanish (CORE-709)."""
        code = """print("hello")
definir test():
    devolver float(42)
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # Helper to extract token name from source
        def token_name(t: tuple) -> str:
            return code.splitlines()[t[0]][t[1] : t[1] + t[2]]

        # "print" is a builtin function → TOKEN_TYPE_FUNCTION
        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        func_names = [token_name(t) for t in func_tokens]
        assert "print" in func_names

        # "float" is a builtin type → TOKEN_TYPE_CLASS
        class_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        class_names = [token_name(t) for t in class_tokens]
        assert "float" in class_names

    def test_class_name_highlighted(self):
        """Test class name after 'clase' gets TOKEN_TYPE_CLASS (CORE-895)."""
        code = """clase MiClase:
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # clase (keyword) + MiClase (class name) + pasar (keyword)
        assert len(tokens) == 3
        assert tokens[0][3] == TOKEN_TYPE_KEYWORD  # clase
        assert tokens[1][3] == TOKEN_TYPE_CLASS  # MiClase
        assert tokens[1][2] == len("MiClase")
        assert tokens[2][3] == TOKEN_TYPE_KEYWORD  # pasar

    def test_function_name_highlighted(self):
        """Test function name after 'definir' gets TOKEN_TYPE_FUNCTION (CORE-895)."""
        code = """definir mi_funcion():
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # definir (keyword) + mi_funcion (func name) + pasar (keyword)
        assert len(tokens) == 3
        assert tokens[0][3] == TOKEN_TYPE_KEYWORD  # definir
        assert tokens[1][3] == TOKEN_TYPE_FUNCTION  # mi_funcion
        assert tokens[1][2] == len("mi_funcion")

    def test_dunder_function_name_highlighted(self):
        """Test __init__ after 'definir' gets TOKEN_TYPE_FUNCTION (CORE-895)."""
        code = """definir __init__(propio):
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # definir (keyword) + __init__ (func name) + propio (first param) + pasar (keyword)
        assert len(tokens) == 4
        assert tokens[1][3] == TOKEN_TYPE_FUNCTION  # __init__
        assert tokens[1][2] == len("__init__")
        assert tokens[2][3] == TOKEN_TYPE_PARAMETER  # propio

    def test_first_param_highlighted(self):
        """Test first param gets TOKEN_TYPE_PARAMETER, second does not (CORE-895)."""
        code = """definir metodo(propio, x):
    pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # definir (keyword) + metodo (func) + propio (param) + pasar (keyword)
        # 'x' is NOT emitted (not a keyword/builtin/exception/contextual)
        assert len(tokens) == 4
        param_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_PARAMETER]
        assert len(param_tokens) == 1
        assert param_tokens[0][2] == len("propio")

    def test_class_with_method(self):
        """Test full class with method — class name, func name, first param (CORE-895)."""
        code = """clase ListaCompleta:
    definir __init__(propio):
        pasar

    definir agregar(propio, elemento):
        pasar
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        class_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        param_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_PARAMETER]
        keyword_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_KEYWORD]

        # Class: ListaCompleta
        assert len(class_tokens) == 1
        # Functions: __init__, agregar
        assert len(func_tokens) == 2
        # Params: propio × 2
        assert len(param_tokens) == 2
        # Keywords: clase, definir × 2, pasar × 2
        assert len(keyword_tokens) == 5

    def test_english_class_def_context(self):
        """Test context-aware works for English class/def in mixed code (CORE-895)."""
        code = """class Foo:
    def bar(self):
        pass
"""
        provider = SemanticTokensProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        provider._load_token_mappings()
        tokens = provider.get_semantic_tokens()

        # class (kw) + Foo (class name) + def (kw) + bar (func name) + self (param) + pass (kw)
        assert len(tokens) == 6

        class_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_CLASS]
        assert len(class_tokens) == 1  # Foo

        func_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_FUNCTION]
        assert len(func_tokens) == 1  # bar

        param_tokens = [t for t in tokens if t[3] == TOKEN_TYPE_PARAMETER]
        assert len(param_tokens) == 1  # self


class TestSemanticTokensIntegration:
    """Integration tests with language server."""

    def test_provide_semantic_tokens_integration(self):
        """Test provide_semantic_tokens with server instance."""
        config = LanguageServerConfig(
            source_language="en", target_language="es", pylance_enabled=False
        )
        server = LegesherLanguageServer(config)

        # Add test document
        uri = "file:///test.py"
        code = """definir test():
    devolver 42
"""
        server.document_manager.open_document(uri=uri, text=code, version=1, language_id="python")

        # Get semantic tokens
        result = provide_semantic_tokens(server, uri)

        assert result is not None
        assert len(result.data) > 0
        # Should have 3 tokens × 5 integers = 15 (definir, test, devolver)
        assert len(result.data) == 15

    def test_missing_document(self):
        """Test semantic tokens for non-existent document."""
        config = LanguageServerConfig(
            source_language="en", target_language="es", pylance_enabled=False
        )
        server = LegesherLanguageServer(config)

        # Request tokens for non-existent document
        result = provide_semantic_tokens(server, "file:///nonexistent.py")

        assert result is None

    def test_real_world_code_spanish(self):
        """Test with real-world-style Spanish code."""
        config = LanguageServerConfig(
            source_language="en", target_language="es", pylance_enabled=False
        )
        server = LegesherLanguageServer(config)

        # Real-world-style code
        code = """desde typing importar List, Optional

clase Usuario:
    definir __init__(self, nombre: str, edad: int):
        self.nombre = nombre
        self.edad = edad

    definir es_adulto(self) -> bool:
        devolver self.edad >= 18

definir filtrar_adultos(usuarios: List[Usuario]) -> List[Usuario]:
    resultado = []
    por usuario en usuarios:
        si usuario.es_adulto():
            resultado.append(usuario)
    devolver resultado
"""
        uri = "file:///usuario.py"
        server.document_manager.open_document(uri=uri, text=code, version=1, language_id="python")

        result = provide_semantic_tokens(server, uri)

        assert result is not None
        assert len(result.data) > 0

        # Decode to verify keywords found
        # Expected keywords: desde, importar, clase, definir (×3), devolver (×2), por, en, si
        # Total: 11 keywords (List/Optional are types, not keywords)
        num_tokens = len(result.data) // 5
        assert num_tokens >= 11, f"Expected at least 11 tokens, got {num_tokens}"
