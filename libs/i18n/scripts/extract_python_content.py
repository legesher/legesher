#!/usr/bin/env python3
"""
Extract localizable content from Python.

This script extracts keywords, built-in functions, built-in types, and docstrings
from Python for use in Legesher language packs.

Supports three extraction methods:
1. Runtime extraction (default) - Uses current Python installation
2. GitHub fetch - Downloads from CPython repository for specific versions
3. Multi-version - Extracts from multiple installed Python versions

Usage:
    # Extract from current Python
    python extract_python_content.py

    # Extract from specific installed version
    python extract_python_content.py --python-version 3.13

    # Fetch from GitHub (works without local installation)
    python extract_python_content.py --version 3.14 --method github

    # Extract from multiple versions
    python extract_python_content.py --versions 3.10,3.11,3.12,3.13

Output:
    JSON file with all extracted content:
    {
        "python_version": "3.13.0",
        "keywords": [...],
        "builtins": {...},
        "types": {...},
        "docstrings": {...},
        "metadata": {...}
    }
"""

import argparse
import inspect
import json
import keyword
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print(
        "Warning: 'requests' not available. GitHub fetch method disabled.",
        file=sys.stderr,
    )


class PythonContentExtractor:
    """Extract localizable content from Python."""

    def __init__(self, python_version: Optional[str] = None):
        """
        Initialize extractor.

        Args:
            python_version: Python version string (e.g., "3.13").
                          If None, uses current Python version.
        """
        if python_version:
            self.version = python_version
        else:
            self.version = f"{sys.version_info.major}.{sys.version_info.minor}"

        self.full_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def extract_keywords(self) -> Dict[str, List[str]]:
        """
        Extract Python keywords (hard and soft).

        Returns:
            Dict with 'hard' and 'soft' keyword lists
        """
        hard_keywords = keyword.kwlist.copy()
        soft_keywords = keyword.softkwlist.copy()

        return {
            "hard": sorted(hard_keywords),
            "soft": sorted(soft_keywords),
            "all": sorted(hard_keywords + soft_keywords),
        }

    def extract_builtin_functions(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract built-in functions with docstrings.

        Returns:
            Dict mapping function name to metadata
        """
        import builtins

        functions = {}

        for name in dir(builtins):
            if name.startswith("_"):
                continue

            obj = getattr(builtins, name)

            # Filter for callables that aren't types
            if callable(obj) and not isinstance(obj, type):
                docstring = inspect.getdoc(obj)
                signature = self._get_signature(obj)

                functions[name] = {
                    "name": name,
                    "docstring": docstring,
                    "signature": signature,
                    "category": self._categorize_builtin(name),
                }

        return functions

    def extract_builtin_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract built-in types with docstrings.

        Returns:
            Dict mapping type name to metadata
        """
        import builtins

        types = {}

        for name in dir(builtins):
            if name.startswith("_"):
                continue

            obj = getattr(builtins, name)

            # Filter for types
            if isinstance(obj, type):
                docstring = inspect.getdoc(obj)

                types[name] = {
                    "name": name,
                    "docstring": docstring,
                    "category": self._categorize_type(name),
                }

        return types

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all localizable content.

        Returns:
            Complete dictionary of all extracted content
        """
        keywords = self.extract_keywords()
        functions = self.extract_builtin_functions()
        types = self.extract_builtin_types()

        # Count totals
        total_items = (
            len(keywords["hard"]) + len(keywords["soft"]) + len(functions) + len(types)
        )

        return {
            "python_version": self.version,
            "python_full_version": self.full_version,
            "keywords": keywords,
            "builtins": functions,
            "types": types,
            "statistics": {
                "total_items": total_items,
                "keywords_hard": len(keywords["hard"]),
                "keywords_soft": len(keywords["soft"]),
                "builtins": len(functions),
                "types": len(types),
            },
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "python_implementation": sys.implementation.name,
                "platform": sys.platform,
                "extraction_method": "runtime",
            },
        }

    @staticmethod
    def _get_signature(obj: Any) -> Optional[str]:
        """Get function signature as string."""
        try:
            sig = inspect.signature(obj)
            return str(sig)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _categorize_builtin(name: str) -> str:
        """Categorize a built-in function."""
        # I/O functions
        if name in ("print", "input", "open"):
            return "io"

        # Type conversion
        if name in ("int", "str", "float", "bool", "list", "dict", "tuple", "set"):
            return "conversion"

        # Iteration
        if name in ("iter", "next", "enumerate", "zip", "map", "filter", "range"):
            return "iteration"

        # Introspection
        if name in (
            "type",
            "isinstance",
            "issubclass",
            "callable",
            "hasattr",
            "getattr",
            "setattr",
            "delattr",
            "dir",
            "vars",
            "locals",
            "globals",
        ):
            return "introspection"

        # Math
        if name in ("abs", "round", "min", "max", "sum", "pow", "divmod"):
            return "math"

        # Sequence operations
        if name in ("len", "sorted", "reversed", "all", "any"):
            return "sequence"

        # Object operations
        if name in (
            "id",
            "hash",
            "repr",
            "ascii",
            "format",
            "bin",
            "hex",
            "oct",
            "ord",
            "chr",
        ):
            return "object"

        # Code execution
        if name in ("eval", "exec", "compile"):
            return "execution"

        # Async
        if name in ("aiter", "anext"):
            return "async"

        # Debugging
        if name in ("breakpoint",):
            return "debug"

        # Help
        if name in ("help", "copyright", "credits", "license", "quit", "exit"):
            return "help"

        return "other"

    @staticmethod
    def _categorize_type(name: str) -> str:
        """Categorize a built-in type."""
        # Numeric types
        if name in ("int", "float", "complex", "bool"):
            return "numeric"

        # Sequence types
        if name in ("list", "tuple", "range"):
            return "sequence"

        # Text type
        if name in ("str",):
            return "text"

        # Binary types
        if name in ("bytes", "bytearray", "memoryview"):
            return "binary"

        # Set types
        if name in ("set", "frozenset"):
            return "set"

        # Mapping types
        if name in ("dict",):
            return "mapping"

        # Exception types
        if (
            name.endswith("Error")
            or name.endswith("Warning")
            or name in ("Exception", "BaseException")
        ):
            return "exception"

        # Type-related
        if name in ("type", "object", "property", "classmethod", "staticmethod"):
            return "type"

        # Other
        return "other"


class GitHubExtractor:
    """Extract Python content from GitHub (for uninstalled versions)."""

    BASE_URL = "https://raw.githubusercontent.com/python/cpython"

    def __init__(self, version: str):
        """
        Initialize GitHub extractor.

        Args:
            version: Python version (e.g., "3.14")
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library required for GitHub extraction")

        self.version = version
        self.tag = f"v{version}.0"

    def fetch_keyword_list(self) -> Dict[str, List[str]]:
        """
        Fetch keyword list from GitHub.

        Returns:
            Dict with keyword lists
        """
        url = f"{self.BASE_URL}/{self.tag}/Lib/keyword.py"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch from GitHub: {e}")

        content = response.text

        # Parse kwlist and softkwlist from the file
        hard_keywords = self._parse_kwlist(content, "kwlist")
        soft_keywords = self._parse_kwlist(content, "softkwlist")

        return {
            "hard": sorted(hard_keywords),
            "soft": sorted(soft_keywords),
            "all": sorted(hard_keywords + soft_keywords),
        }

    @staticmethod
    def _parse_kwlist(content: str, list_name: str) -> List[str]:
        """
        Parse keyword list from keyword.py source.

        Args:
            content: File content
            list_name: Name of list to parse ('kwlist' or 'softkwlist')

        Returns:
            List of keywords
        """
        keywords = []

        # Find the list definition
        in_list = False
        for line in content.split("\n"):
            line = line.strip()

            # Start of list
            if f"{list_name} = [" in line:
                in_list = True
                continue

            # End of list
            if in_list and "]" in line:
                break

            # Extract keywords from list
            if in_list and line.startswith("'"):
                # Remove quotes and trailing comma
                keyword = line.strip("',")
                if keyword:
                    keywords.append(keyword)

        return keywords

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all available content from GitHub.

        Note: Only keywords can be reliably extracted from GitHub.
        Built-in functions and types require runtime introspection.

        Returns:
            Dict with extracted content
        """
        keywords = self.fetch_keyword_list()

        return {
            "python_version": self.version,
            "python_full_version": f"{self.version}.0",
            "keywords": keywords,
            "statistics": {
                "keywords_hard": len(keywords["hard"]),
                "keywords_soft": len(keywords["soft"]),
                "keywords_total": len(keywords["all"]),
            },
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "extraction_method": "github",
                "github_tag": self.tag,
                "note": "Only keywords available via GitHub extraction. "
                "Built-ins and types require runtime extraction.",
            },
        }


def save_to_json(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save extracted data to JSON file.

    Args:
        data: Data to save
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract localizable content from Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--version", help='Python version to extract (e.g., "3.14")')

    parser.add_argument(
        "--method",
        choices=["runtime", "github"],
        default="runtime",
        help="Extraction method (default: runtime)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: python-content-{version}.json)",
    )

    parser.add_argument(
        "--versions",
        help='Comma-separated list of versions to extract (e.g., "3.10,3.11,3.12")',
    )

    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print summary to stdout"
    )

    args = parser.parse_args()

    # Handle multi-version extraction
    if args.versions:
        versions = [v.strip() for v in args.versions.split(",")]
        for version in versions:
            extract_version(version, args.method, args.output, args.pretty)
        return

    # Single version extraction
    version = args.version or f"{sys.version_info.major}.{sys.version_info.minor}"
    extract_version(version, args.method, args.output, args.pretty)


def extract_version(
    version: str, method: str, output_path: Optional[Path], pretty: bool
) -> None:
    """
    Extract content for a single Python version.

    Args:
        version: Python version
        method: Extraction method
        output_path: Output file path
        pretty: Whether to print pretty summary
    """
    print(f"Extracting Python {version} content using {method} method...")

    try:
        if method == "runtime":
            extractor = PythonContentExtractor(version)
            data = extractor.extract_all()
        else:  # github
            extractor = GitHubExtractor(version)
            data = extractor.extract_all()

        # Determine output path
        if not output_path:
            output_path = Path(f"python-content-{version}.json")

        save_to_json(data, output_path)

        # Print summary
        if pretty:
            print_summary(data)

        print(f"\n✓ Successfully extracted Python {version} content")

    except Exception as e:
        print(f"✗ Error extracting Python {version}: {e}", file=sys.stderr)
        sys.exit(1)


def print_summary(data: Dict[str, Any]) -> None:
    """Print a pretty summary of extracted data."""
    print("\n" + "=" * 60)
    print(f"Python {data['python_version']} Localization Content")
    print("=" * 60)

    stats = data.get("statistics", {})

    print("\n📊 Statistics:")
    print(f"  Total items: {stats.get('total_items', 'N/A')}")
    print(f"  Keywords (hard): {stats.get('keywords_hard', 0)}")
    print(f"  Keywords (soft): {stats.get('keywords_soft', 0)}")
    print(f"  Built-in functions: {stats.get('builtins', 0)}")
    print(f"  Built-in types: {stats.get('types', 0)}")

    if "keywords" in data:
        print(f"\n🔑 Keywords ({len(data['keywords'].get('all', []))}):")
        keywords = data["keywords"].get("all", [])
        # Print first 10
        for i, kw in enumerate(keywords[:10]):
            print(f"  {kw}", end="")
            if i < 9 and i < len(keywords) - 1:
                print(", ", end="")
        if len(keywords) > 10:
            print(f"... and {len(keywords) - 10} more")
        else:
            print()

    metadata = data.get("metadata", {})
    print("\nℹ️  Metadata:")
    print(f"  Method: {metadata.get('extraction_method', 'unknown')}")
    print(f"  Extracted: {metadata.get('extracted_at', 'unknown')}")

    print("=" * 60)


if __name__ == "__main__":
    main()
