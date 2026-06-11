"""Tree-sitter parser wrapper for Python code."""

import logging

from tree_sitter import Language, Parser, Query, Tree
import tree_sitter_python

logger = logging.getLogger(__name__)


class TreeSitterError(Exception):
    """Raised when tree-sitter operations fail."""

    pass


class PythonParser:
    """Wrapper for tree-sitter Python parser.

    This class provides a simple interface for parsing Python code
    using tree-sitter. It handles grammar loading and provides
    utilities for common operations.

    Example:
        >>> parser = PythonParser()
        >>> tree = parser.parse("def hello(): pass")
        >>> print(tree.root_node.type)
        'module'
    """

    def __init__(self):
        """Initialize the Python parser with tree-sitter grammar."""
        try:
            logger.debug("Initializing Python parser with tree-sitter")
            # Load Python grammar
            self.language = Language(tree_sitter_python.language())

            # Create parser instance
            self.parser = Parser(self.language)
            logger.debug("Python parser initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Python parser: %s", e)
            raise TreeSitterError(f"Failed to initialize Python parser: {e}") from e

    def parse(self, source_code: str | bytes, encoding: str = "utf-8") -> Tree:
        """Parse Python source code into an AST.

        Args:
            source_code: Python source code as string or bytes
            encoding: Character encoding to use when converting strings to bytes.
                     Defaults to 'utf-8'. Ignored if source_code is already bytes.

        Returns:
            Tree object representing the parsed AST

        Raises:
            TreeSitterError: If parsing fails or encoding is invalid

        Example:
            >>> parser = PythonParser()
            >>> tree = parser.parse("x = 1 + 2")
            >>> print(tree.root_node.child_count)
            1
        """
        # Convert string to bytes if needed
        if isinstance(source_code, str):
            # Legesher mandates UTF-8 for source. Fail closed on any non-UTF-8
            # request rather than silently re-encoding, so multilingual (esp.
            # RTL) code is never mangled and a wrong-encoding caller is caught.
            normalized_encoding = encoding.lower().replace("_", "-")
            if normalized_encoding not in ("utf-8", "utf8"):
                raise TreeSitterError(
                    f"Legesher source must be UTF-8; got encoding {encoding!r}"
                )
            try:
                source_bytes = source_code.encode(encoding)
            except (UnicodeEncodeError, LookupError) as e:
                logger.error("Failed to encode source code with %s: %s", encoding, e)
                raise TreeSitterError(
                    f"Failed to encode source code with {encoding}: {e}"
                ) from e
        else:
            source_bytes = source_code

        code_size = len(source_bytes)
        logger.debug("Parsing %d bytes of Python code", code_size)

        try:
            tree = self.parser.parse(source_bytes)

            if tree is None:
                raise TreeSitterError("Parser returned None")

            logger.debug(
                "Successfully parsed %d bytes; AST has %d nodes",
                code_size,
                tree.root_node.child_count,
            )
            return tree

        except TreeSitterError:
            raise
        except Exception as e:
            logger.error("Failed to parse source code (%d bytes): %s", code_size, e)
            raise TreeSitterError(f"Failed to parse source code: {e}") from e

    def parse_incremental(
        self,
        source_code: str | bytes,
        old_tree: Tree | None = None,
        encoding: str = "utf-8",
    ) -> Tree:
        """Parse code incrementally using previous tree.

        This method enables incremental parsing, which is more efficient
        for real-time editing scenarios. If no old_tree is provided,
        falls back to regular parsing.

        Args:
            source_code: Updated Python source code
            old_tree: Previous parse tree (for incremental parsing)
            encoding: Character encoding to use when converting strings to bytes.
                     Defaults to 'utf-8'. Ignored if source_code is already bytes.

        Returns:
            Updated Tree object

        Example:
            >>> parser = PythonParser()
            >>> tree1 = parser.parse("def foo(): pass")
            >>> tree2 = parser.parse_incremental("def foo():\\n    return 42", tree1)
            >>> # With custom encoding
            >>> tree3 = parser.parse_incremental(code, tree2, encoding="latin-1")
        """
        if isinstance(source_code, str):
            # Legesher mandates UTF-8 for source. Fail closed on any non-UTF-8
            # request rather than silently re-encoding, so multilingual (esp.
            # RTL) code is never mangled and a wrong-encoding caller is caught.
            normalized_encoding = encoding.lower().replace("_", "-")
            if normalized_encoding not in ("utf-8", "utf8"):
                raise TreeSitterError(
                    f"Legesher source must be UTF-8; got encoding {encoding!r}"
                )
            try:
                source_bytes = source_code.encode(encoding)
            except (UnicodeEncodeError, LookupError) as e:
                logger.error("Failed to encode source code with %s: %s", encoding, e)
                raise TreeSitterError(
                    f"Failed to encode source code with {encoding}: {e}"
                ) from e
        else:
            source_bytes = source_code

        code_size = len(source_bytes)
        if old_tree is not None:
            logger.debug("Incremental parse: updating %d bytes of code", code_size)
        else:
            logger.debug(
                "Fallback to full parse: %d bytes (no previous tree)", code_size
            )

        try:
            # Use old_tree for incremental parsing, or None for full parse
            if old_tree is not None:
                tree = self.parser.parse(source_bytes, old_tree)
            else:
                tree = self.parser.parse(source_bytes)

            if tree is None:
                raise TreeSitterError("Parser returned None")

            logger.debug(
                "Incremental parse complete: %d bytes, %d nodes",
                code_size,
                tree.root_node.child_count,
            )
            return tree

        except TreeSitterError:
            raise
        except Exception as e:
            logger.error("Failed to parse incrementally (%d bytes): %s", code_size, e)
            raise TreeSitterError(f"Failed to parse incrementally: {e}") from e

    def query(self, query_string: str) -> Query:
        """Create a query object for pattern matching.

        Args:
            query_string: Tree-sitter query string (S-expression format)

        Returns:
            Query object that can be used with QueryCursor

        Raises:
            TreeSitterError: If query compilation fails

        Example:
            >>> parser = PythonParser()
            >>> query = parser.query("(function_definition) @func")
            >>> tree = parser.parse("def hello(): pass")
            >>> cursor = QueryCursor(query)
            >>> matches = cursor.matches(tree.root_node)
            >>> len(list(matches))
            1
        """
        logger.debug("Compiling query: %s", query_string[:100])
        try:
            compiled_query = Query(self.language, query_string)
            logger.debug("Query compiled successfully")
            return compiled_query
        except Exception as e:
            logger.error("Failed to compile query: %s", e)
            raise TreeSitterError(f"Failed to compile query: {e}") from e
