"""AST element extractor for LLM-powered full code translation.

Walks a tree-sitter Python AST and extracts all translatable elements
(identifiers, comments, docstrings, strings) with rich context for
LLM translation.
"""

import logging
import re

from legesher_i18n.term_definitions import IMPLICIT_PARAMS as _IMPLICIT_PARAMS_SOURCE

from ..token_mapper import TokenMapper
from ..types import IdentifierRole, TranslatableElement
from .parser import PythonParser

logger = logging.getLogger(__name__)


# Dunder/magic methods that must NOT be translated
DUNDER_PATTERN = re.compile(r"^__[a-zA-Z0-9]+__$")

# Implicit params: Python conventions handled deterministically by the
# language pack's implicit_params section rather than the LLM (CORE-710).
# Single source of truth: legesher_i18n.term_definitions.IMPLICIT_PARAMS.
# Materialized as a frozenset at module load time for O(1) containment
# checks on the extractor hot path. If the canonical list ever expands
# beyond {self, cls}, this picks up the change automatically.
IMPLICIT_PARAMS = frozenset(_IMPLICIT_PARAMS_SOURCE)

# Standard library top-level module names (Python 3.10+)
# Used to skip stdlib import names
STDLIB_MODULES = frozenset(
    {
        "abc",
        "aifc",
        "argparse",
        "array",
        "ast",
        "asynchat",
        "asyncio",
        "asyncore",
        "atexit",
        "audioop",
        "base64",
        "bdb",
        "binascii",
        "binhex",
        "bisect",
        "builtins",
        "bz2",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "cProfile",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "numbers",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "tomllib",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        # Common internal/private modules
        "_thread",
        "_io",
        "_collections_abc",
        "posixpath",
        "ntpath",
        "genericpath",
        "stat",
    }
)

# Shebang and encoding declaration patterns
SHEBANG_PATTERN = re.compile(r"^#!")
ENCODING_PATTERN = re.compile(r"^#.*?coding[=:]\s*([-\w.]+)")
# Cultural comment pattern (MLCP protocol)
CULTURAL_COMMENT_PATTERN = re.compile(r"^#\s*@culture\[")


class TranslatableExtractor:
    """Extracts all translatable elements from a Python AST.

    Walks the tree-sitter AST depth-first and collects identifiers,
    comments, docstrings, and string literals with rich context for
    LLM translation.

    Elements that are keywords, builtins, dunder methods, or stdlib
    imports are skipped (they're handled by the existing translator
    or must be preserved).
    """

    def __init__(self, mapper: TokenMapper):
        """Initialize with a TokenMapper to identify keywords/builtins.

        Args:
            mapper: TokenMapper with keyword_map and builtin_map for
                   identifying which identifiers are already handled.
        """
        self.mapper = mapper
        self.parser = PythonParser()

    def extract(self, source_code: str) -> list[TranslatableElement]:
        """Extract all translatable elements from source code.

        Args:
            source_code: Python source code string

        Returns:
            List of TranslatableElement instances sorted by start_byte
        """
        tree = self.parser.parse(source_code)
        elements: list[TranslatableElement] = []
        source_lines = source_code.split("\n")

        self._walk(tree.root_node, elements, source_code, source_lines)

        # Sort by position for deterministic ordering
        elements.sort(key=lambda e: e.start_byte)
        return elements

    def _walk(
        self,
        node,
        elements: list[TranslatableElement],
        source_code: str,
        source_lines: list[str],
    ) -> None:
        """Recursively walk the AST and collect translatable elements."""
        # Handle each node type
        if node.type == "comment":
            self._extract_comment(node, elements, source_lines)
        elif node.type == "string":
            self._extract_string_or_docstring(node, elements, source_code, source_lines)
        elif node.type == "identifier":
            self._extract_identifier(node, elements, source_code, source_lines)

        # Recurse into children
        for child in node.children:
            self._walk(child, elements, source_code, source_lines)

    def _extract_comment(
        self,
        node,
        elements: list[TranslatableElement],
        source_lines: list[str],
    ) -> None:
        """Extract a comment if it's not a shebang, encoding decl, or cultural comment."""
        try:
            text = node.text.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return

        # Skip special comments
        if SHEBANG_PATTERN.match(text):
            return
        if ENCODING_PATTERN.match(text):
            return
        if CULTURAL_COMMENT_PATTERN.match(text):
            return

        # Strip the # prefix for translation, preserve prefix for reinsertion
        # Match: one or more # followed by optional single space (PEP 8: "# comment")
        stripped = text.lstrip()
        match = re.match(r"(#+\s?)", stripped)
        hash_prefix = match.group(1) if match else "# "

        # Content is everything after the hash prefix
        content = stripped[len(hash_prefix) :]
        if not content.strip():
            return  # Empty comment

        # Get surrounding context
        line_num = node.start_point[0]
        surrounding = self._get_surrounding_lines(source_lines, line_num, 2)

        elements.append(
            TranslatableElement(
                kind="comment",
                text=content,  # Content only — no # prefix
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                role="other",
                context={
                    "surrounding_code": surrounding,
                    "line": line_num,
                    "hash_prefix": hash_prefix,
                },
            )
        )

    def _extract_string_or_docstring(
        self,
        node,
        elements: list[TranslatableElement],
        source_code: str,
        source_lines: list[str],
    ) -> None:
        """Extract a string literal, detecting if it's a docstring by position."""
        try:
            text = node.text.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return

        # Detect if this is a docstring (first expr statement in func/class/module body)
        is_docstring = self.is_docstring(node)

        # Detect quote style and prefix
        quote_style, prefix = self._parse_string_delimiters(text)

        # Skip f-string nodes — we handle their string_content children instead
        # But only if this is an f-string (has interpolation children)
        if prefix and "f" in prefix.lower():
            # For f-strings, extract only the string_content parts (not interpolations)
            self._extract_fstring_parts(
                node, elements, source_code, source_lines, is_docstring
            )
            return

        # Extract the string content (without quotes and prefix)
        content = self._strip_string_delimiters(text, quote_style, prefix)
        if not content or not content.strip():
            return

        line_num = node.start_point[0]
        context = self._get_surrounding_lines(source_lines, line_num, 2)

        elements.append(
            TranslatableElement(
                kind="docstring" if is_docstring else "string",
                text=content,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                role="other",
                context={"surrounding_code": context, "line": line_num},
                quote_style=quote_style,
                prefix=prefix,
            )
        )

    def _extract_fstring_parts(
        self,
        node,
        elements: list[TranslatableElement],
        source_code: str,
        source_lines: list[str],
        is_docstring: bool,
    ) -> None:
        """Extract translatable string_content parts from f-strings, skipping {expr}."""
        # Detect if the f-string uses triple quotes (handles all prefix combos: f, fr, rf, etc.)
        try:
            fstring_text = node.text.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            fstring_text = ""
        # Strip prefix letters to find the quote delimiter
        stripped_prefix = fstring_text.lstrip("rRuUfFbB")
        is_triple_quoted = stripped_prefix.startswith(('"""', "'''"))

        for child in node.children:
            if child.type == "string_content":
                try:
                    text = child.text.decode("utf-8")
                except (UnicodeDecodeError, AttributeError):
                    continue
                if text.strip():
                    line_num = child.start_point[0]
                    context = self._get_surrounding_lines(source_lines, line_num, 2)
                    elements.append(
                        TranslatableElement(
                            kind="docstring" if is_docstring else "string",
                            text=text,
                            start_byte=child.start_byte,
                            end_byte=child.end_byte,
                            role="other",
                            context={
                                "surrounding_code": context,
                                "line": line_num,
                                "is_fstring_content": True,
                                "is_triple_quoted": is_triple_quoted,
                            },
                        )
                    )
            elif child.type == "interpolation":
                # Skip {expression} parts — they're code, not translatable text
                pass
            else:
                # Recurse for nested structures
                self._extract_fstring_parts(
                    child, elements, source_code, source_lines, is_docstring
                )

    def _extract_identifier(
        self,
        node,
        elements: list[TranslatableElement],
        source_code: str,
        source_lines: list[str],
    ) -> None:
        """Extract a user-defined identifier (skip keywords, builtins, dunders, stdlib)."""
        try:
            text = node.text.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return

        # Skip keywords and builtins (already handled by TreeSitterTranslator)
        if self.mapper.get_keyword(text) is not None:
            return
        if self.mapper.get_builtin(text) is not None:
            return

        # CORE-710: skip implicit params (self, cls) in any AST position.
        # They're translated deterministically by the language pack's
        # implicit_params section at the translator level (see
        # TokenMapper.get_implicit_param), so sending them to the LLM
        # wastes tokens and risks inconsistent translations. Both
        # parameter-position usages (`def foo(self):`) and body-position
        # usages (`self.x`) are skipped — the translator's dispatch order
        # (implicit_param_map before IdentifierMap) ensures correct
        # substitution at output time regardless of where they appear.
        if text in IMPLICIT_PARAMS:
            return

        # Skip dunder/magic methods
        if DUNDER_PATTERN.match(text):
            return

        # Skip single-character identifiers (usually not worth translating)
        # Actually, don't skip — short names like `x` or `i` might need
        # translation context

        # Skip stdlib module names in import contexts
        if self._is_import_name(node) and text in STDLIB_MODULES:
            return

        # Determine the identifier's role based on parent node
        role = self.determine_role(node)

        # Detect naming convention
        naming_convention = self._detect_naming_convention(text)

        # Get surrounding context
        line_num = node.start_point[0]
        surrounding = self._get_surrounding_lines(source_lines, line_num, 3)

        # Get type hint if available
        type_hint = self._get_type_hint(node)

        # Get docstring if this is a function/class name
        docstring = None
        if role in ("function_name", "class_name"):
            docstring = self._get_associated_docstring(node)

        context: dict = {
            "surrounding_code": surrounding,
            "naming_convention": naming_convention,
            "line": line_num,
        }
        if type_hint:
            context["type_hint"] = type_hint
        if docstring:
            context["docstring"] = docstring

        elements.append(
            TranslatableElement(
                kind="identifier",
                text=text,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                role=role,
                context=context,
            )
        )

    # --- Helper methods ---

    def is_docstring(self, string_node) -> bool:
        """Check if a string node is a docstring (first expr in body).

        Public API: the register-map builder
        (``legesher_core.register_map.builder``) relies on this to split
        ``docstring`` from ``string`` in the element-class taxonomy.
        """
        parent = string_node.parent
        if parent is None or parent.type != "expression_statement":
            return False
        grandparent = parent.parent
        if grandparent is None:
            return False
        # Check if this is the first statement in a function/class/module body
        if grandparent.type in ("module", "block"):
            # For block (function/class body), check it's the first child
            for child in grandparent.children:
                if child.type == "expression_statement":
                    return child == parent
                # Skip pass, comments, etc. before the docstring
                if child.type not in (
                    "comment",
                    "newline",
                    "indent",
                    "dedent",
                    "NEWLINE",
                ):
                    break
        return False

    def _is_import_name(self, node) -> bool:
        """Check if an identifier is part of an import statement."""
        parent = node.parent
        while parent is not None:
            if parent.type in ("import_statement", "import_from_statement"):
                return True
            parent = parent.parent
        return False

    def determine_role(self, node) -> IdentifierRole:
        """Determine the identifier's role based on its position in the AST.

        Public API: the register-map builder
        (``legesher_core.register_map.builder``) uses this for identifiers
        the extractor itself skips (dunders, implicit params, stdlib
        imports) so every entry still carries a role.
        """
        parent = node.parent
        if parent is None:
            return "other"

        if parent.type == "function_definition":
            # Check if this is the function name (first identifier child)
            if node == self._first_identifier_child(parent):
                return "function_name"
        elif parent.type == "class_definition":
            if node == self._first_identifier_child(parent):
                return "class_name"
        elif parent.type in (
            "parameters",
            "default_parameter",
            "typed_parameter",
            "typed_default_parameter",
            "list_splat_pattern",
            "dictionary_splat_pattern",
        ):
            return "parameter"
        elif parent.type == "attribute":
            # Attribute access: obj.attr — the second identifier is the attribute
            children = [c for c in parent.children if c.type == "identifier"]
            if len(children) >= 2 and node == children[-1]:
                return "attribute"
        elif parent.type in ("assignment", "augmented_assignment"):
            # Left side of assignment
            left = parent.children[0] if parent.children else None
            if left is not None and self._node_contains(left, node):
                return "variable"
        elif parent.type == "for_statement":
            # Loop variable
            if parent.children and node.start_byte < parent.children[0].end_byte + 10:
                return "variable"
        elif parent.type == "import_from_statement":
            return "module"
        elif parent.type == "import_statement":
            return "module"

        return "other"

    def _first_identifier_child(self, node):
        """Get the first identifier child of a node."""
        for child in node.children:
            if child.type == "identifier":
                return child
        return None

    @staticmethod
    def _node_contains(parent_node, target_node) -> bool:
        """Check if parent_node contains target_node."""
        return (
            parent_node.start_byte <= target_node.start_byte
            and parent_node.end_byte >= target_node.end_byte
        )

    @staticmethod
    def _detect_naming_convention(text: str) -> str:
        """Detect the naming convention of an identifier."""
        if not text:
            return "unknown"
        if "_" in text:
            if text.isupper():
                return "SCREAMING_SNAKE_CASE"
            return "snake_case"
        if text[0].isupper():
            return "PascalCase"
        if any(c.isupper() for c in text[1:]):
            return "camelCase"
        return "lowercase"

    @staticmethod
    def _get_surrounding_lines(
        source_lines: list[str], line_num: int, radius: int
    ) -> str:
        """Get lines surrounding the given line number."""
        start = max(0, line_num - radius)
        end = min(len(source_lines), line_num + radius + 1)
        return "\n".join(source_lines[start:end])

    def _get_type_hint(self, node) -> str | None:
        """Get the type hint for an identifier if available."""
        parent = node.parent
        if parent is None:
            return None
        # typed_parameter: name: Type
        if parent.type in ("typed_parameter", "typed_default_parameter"):
            for child in parent.children:
                if child.type == "type":
                    try:
                        return child.text.decode("utf-8")
                    except (UnicodeDecodeError, AttributeError):
                        pass
        return None

    def _get_associated_docstring(self, node) -> str | None:
        """Get the docstring of the function/class this identifier names."""
        parent = node.parent  # function_definition or class_definition
        if parent is None:
            return None
        # Find the body (block) node
        for child in parent.children:
            if child.type == "block":
                # First expression_statement with a string child is the docstring
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for sub in stmt.children:
                            if sub.type == "string":
                                try:
                                    raw = sub.text.decode("utf-8")
                                    # Strip quotes
                                    return self._strip_string_delimiters(
                                        raw, None, None
                                    )
                                except (UnicodeDecodeError, AttributeError):
                                    pass
                        break
                    if stmt.type not in ("comment", "newline", "NEWLINE"):
                        break
        return None

    @staticmethod
    def _parse_string_delimiters(text: str) -> tuple[str | None, str | None]:
        """Parse a string literal to extract quote style and prefix.

        Returns:
            (quote_style, prefix) tuple
        """
        prefix = ""
        remaining = text
        # Extract prefix (f, r, b, u, combinations like rb, fr, etc.)
        while remaining and remaining[0].lower() in "frbu":
            prefix += remaining[0]
            remaining = remaining[1:]

        prefix = prefix if prefix else None

        # Detect quote style
        if remaining.startswith('"""') or remaining.startswith("'''"):
            quote_style = remaining[:3]
        elif remaining.startswith('"') or remaining.startswith("'"):
            quote_style = remaining[0]
        else:
            quote_style = None

        return quote_style, prefix

    @staticmethod
    def _strip_string_delimiters(
        text: str, _quote_style: str | None = None, _prefix: str | None = None
    ) -> str:
        """Strip prefix and quotes from a string literal to get content."""
        remaining = text
        # Strip prefix
        while remaining and remaining[0].lower() in "frbu":
            remaining = remaining[1:]
        # Strip quotes
        for q in ['"""', "'''", '"', "'"]:
            if remaining.startswith(q) and remaining.endswith(q):
                return remaining[len(q) : -len(q)]
        return remaining
