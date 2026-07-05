#!/usr/bin/env python3
"""
Comprehensive validation and auto-fix script for Python context documents.

Validates:
1. Code block indentation (Python syntax must be correct)
2. Template structure (10 required sections)
3. index.json synchronization with actual files
4. Cross-reference consistency

Auto-fixes:
- Code block indentation issues
- index.json synchronization

Usage:
    python validate_and_fix_context_docs.py [--fix] [--report-only]
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Stores validation results for a document."""

    filename: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    is_valid: bool = True


class ContextDocValidator:
    """Validates and fixes Python context documents."""

    REQUIRED_SECTIONS = [
        "Quick Summary",
        "Code Examples FIRST",
        "Pattern Classification",
        "Etymology",
        "Concept Explanation",
        "Linguistic Form Recommendation",
        "Ambiguity Resolution",
        "Cross-References",
        "Confidence Calibration",
        "Translation Validation Checklist",
    ]

    def __init__(self, docs_dir: Path, fix_mode: bool = False):
        self.docs_dir = docs_dir
        self.fix_mode = fix_mode
        self.results: list[ValidationResult] = []

    def validate_all(self) -> tuple[int, int, int]:
        """Validate all context documents. Returns (valid_count, error_count, warning_count)."""
        md_files = sorted(self.docs_dir.glob("*.md"))
        # Exclude README.md
        md_files = [f for f in md_files if f.name != "README.md"]

        for md_file in md_files:
            result = self.validate_document(md_file)
            self.results.append(result)

        valid_count = sum(1 for r in self.results if r.is_valid)
        error_count = sum(len(r.errors) for r in self.results)
        warning_count = sum(len(r.warnings) for r in self.results)

        return valid_count, error_count, warning_count

    def validate_document(self, filepath: Path) -> ValidationResult:
        """Validate a single document."""
        result = ValidationResult(filename=filepath.name)

        try:
            content = filepath.read_text(encoding="utf-8")

            # Check code block indentation
            code_issues = self.check_code_blocks(content, filepath.stem)
            if code_issues:
                result.errors.extend(code_issues)
                result.is_valid = False

                # Fix if requested
                if self.fix_mode:
                    fixed_content = self.fix_code_blocks(content)
                    filepath.write_text(fixed_content, encoding="utf-8")
                    result.info.append("Fixed code block indentation")

            # Check template structure
            missing_sections = self.check_template_structure(content)
            if missing_sections:
                result.warnings.extend(
                    [f"Missing section: {section}" for section in missing_sections]
                )

            # Check cross-references exist
            missing_refs = self.check_cross_references(content)
            if missing_refs:
                result.warnings.extend(
                    [
                        f"Cross-reference to non-existent document: {ref}"
                        for ref in missing_refs
                    ]
                )

        except Exception as e:
            result.errors.append(f"Failed to process: {str(e)}")
            result.is_valid = False

        return result

    def check_code_blocks(self, content: str, term: str) -> list[str]:
        """Check Python code blocks for correct indentation."""
        issues = []

        # Find all Python code blocks
        python_blocks = re.findall(r"```python\n(.*?)\n```", content, re.DOTALL)

        for i, block in enumerate(python_blocks, 1):
            # Check if this looks like class/function code without indentation
            lines = block.split("\n")
            for j, line in enumerate(lines, 1):
                # Check for class/def without proper indentation
                if line.strip().startswith(("class ", "def ")) and j > 1:
                    # Check if previous line suggests this should be indented
                    prev_line = lines[j - 2] if j > 1 else ""
                    if prev_line.strip().startswith(
                        ("class ", "def ")
                    ) and not line.startswith("    "):
                        issues.append(
                            f"Code block {i}, line {j}: Method/class definition appears unindented"
                        )
                        break

            # Try parsing as Python
            try:
                compile(block, f"<{term}_block_{i}>", "exec")
            except SyntaxError as e:
                issues.append(
                    f"Code block {i}, line {e.lineno}: Python syntax error: {e.msg}"
                )

        return issues

    def fix_code_blocks(self, content: str) -> str:
        """Fix indentation in Python code blocks."""

        def fix_block(match):
            block = match.group(1)
            lines = block.split("\n")
            fixed_lines = []
            indent_level = 0

            for line in lines:
                stripped = line.strip()

                # Decrease indent for closing or dedenting keywords
                if stripped in ("", "pass"):
                    fixed_lines.append(
                        "    " * indent_level + stripped if stripped else ""
                    )
                    continue

                # Dedent before else, elif, except, finally
                if stripped.startswith(
                    ("else:", "elif ", "except:", "except ", "finally:")
                ):
                    indent_level = max(0, indent_level - 1)

                # Add current indentation
                if stripped:
                    fixed_lines.append("    " * indent_level + stripped)
                else:
                    fixed_lines.append("")

                # Increase indent after class, def, if, for, while, with, try, except, etc.
                if stripped.endswith(":"):
                    indent_level += 1

            return f"```python\n{chr(10).join(fixed_lines)}\n```"

        # Fix all Python code blocks
        fixed_content = re.sub(
            r"```python\n(.*?)\n```", fix_block, content, flags=re.DOTALL
        )

        return fixed_content

    def check_template_structure(self, content: str) -> list[str]:
        """Check if all required sections are present."""
        missing = []
        for section in self.REQUIRED_SECTIONS:
            # Look for section header (## or ###)
            pattern = rf"^##+ {re.escape(section)}"
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(section)
        return missing

    def check_cross_references(self, content: str) -> set[str]:
        """Check if cross-referenced terms have documents."""
        # Find terms mentioned in cross-references section
        cross_ref_section = re.search(
            r"## Cross-References.*?(?=^##|\Z)", content, re.DOTALL | re.MULTILINE
        )

        if not cross_ref_section:
            return set()

        section_text = cross_ref_section.group(0)

        # Find backtick-quoted terms
        mentioned_terms = set(re.findall(r"`(\w+)`", section_text))

        # Check which ones have documents
        missing = set()
        for term in mentioned_terms:
            term_file = self.docs_dir / f"{term.lower()}.md"
            if not term_file.exists():
                missing.add(term)

        return missing

    def validate_index_json(self) -> ValidationResult:
        """Validate index.json matches actual files."""
        result = ValidationResult(filename="index.json")

        index_path = self.docs_dir / "index.json"
        if not index_path.exists():
            result.errors.append("index.json not found")
            result.is_valid = False
            return result

        try:
            with open(index_path) as f:
                index_data = json.load(f)

            # Get actual .md files (exclude README.md)
            actual_files = set(
                f.stem for f in self.docs_dir.glob("*.md") if f.name != "README.md"
            )

            # Get indexed files
            indexed_files = set(
                doc["filename"].replace(".md", "") for doc in index_data["documents"]
            )

            # Check counts
            actual_count = len(actual_files)
            indexed_count = len(indexed_files)
            claimed_count = index_data.get("total_documents", 0)

            if claimed_count != actual_count:
                result.errors.append(
                    f"Document count mismatch: index claims {claimed_count}, "
                    f"found {actual_count} files"
                )
                result.is_valid = False

            if claimed_count != indexed_count:
                result.errors.append(
                    f"Index inconsistency: claims {claimed_count} documents, "
                    f"but contains {indexed_count} entries"
                )
                result.is_valid = False

            # Check for missing/extra files
            missing_from_index = actual_files - indexed_files
            extra_in_index = indexed_files - actual_files

            if missing_from_index:
                result.errors.append(
                    f"Files not in index: {', '.join(sorted(missing_from_index))}"
                )
                result.is_valid = False

            if extra_in_index:
                result.errors.append(
                    f"Index entries without files: {', '.join(sorted(extra_in_index))}"
                )
                result.is_valid = False

            # Fix if requested
            if self.fix_mode and not result.is_valid:
                self.fix_index_json(actual_files, index_data, index_path)
                result.info.append("Regenerated index.json with correct file list")

        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            result.is_valid = False
        except Exception as e:
            result.errors.append(f"Error validating index: {e}")
            result.is_valid = False

        return result

    def fix_index_json(
        self, actual_files: set[str], index_data: dict, index_path: Path
    ):
        """Regenerate index.json to match actual files."""
        # Keep existing entries that have matching files
        existing_docs = {
            doc["filename"].replace(".md", ""): doc for doc in index_data["documents"]
        }

        new_documents = []
        for filename in sorted(actual_files):
            if filename in existing_docs:
                # Keep existing metadata
                new_documents.append(existing_docs[filename])
            else:
                # Create minimal entry for new file
                new_documents.append(
                    {
                        "term": filename,
                        "filename": f"{filename}.md",
                        "category": "unknown",
                        "type": "unknown",
                        "difficulty": "MEDIUM",
                        "summary": "Needs manual update",
                    }
                )

        index_data["total_documents"] = len(new_documents)
        index_data["documents"] = new_documents

        with open(index_path, "w") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("CONTEXT DOCUMENTS VALIDATION REPORT")
        print("=" * 80 + "\n")

        valid_count = sum(1 for r in self.results if r.is_valid)
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)

        print(f"Total Documents: {len(self.results)}")
        print(
            f"Valid: {valid_count} ({'%.1f' % (valid_count / len(self.results) * 100)}%)"
        )
        print(f"With Errors: {len(self.results) - valid_count}")
        print(f"Total Errors: {total_errors}")
        print(f"Total Warnings: {total_warnings}\n")

        # Documents with errors
        if total_errors > 0:
            print("\n" + "-" * 80)
            print("DOCUMENTS WITH ERRORS")
            print("-" * 80)
            for result in self.results:
                if result.errors:
                    print(f"\n❌ {result.filename}")
                    for error in result.errors:
                        print(f"   ERROR: {error}")

        # Documents with warnings
        if total_warnings > 0:
            print("\n" + "-" * 80)
            print("DOCUMENTS WITH WARNINGS")
            print("-" * 80)
            for result in self.results:
                if result.warnings:
                    print(f"\n⚠️  {result.filename}")
                    for warning in result.warnings:
                        print(f"   WARNING: {warning}")

        # Fixes applied
        fixes_applied = [r for r in self.results if r.info]
        if fixes_applied:
            print("\n" + "-" * 80)
            print("FIXES APPLIED")
            print("-" * 80)
            for result in fixes_applied:
                print(f"\n✅ {result.filename}")
                for info in result.info:
                    print(f"   {info}")

        print("\n" + "=" * 80 + "\n")

        # Summary
        if total_errors == 0 and total_warnings == 0:
            print("✨ ALL DOCUMENTS ARE VALID!")
        elif total_errors == 0:
            print(f"✓ No critical errors (but {total_warnings} warnings to review)")
        else:
            print(
                f"✗ {total_errors} errors found across {len(self.results) - valid_count} documents"
            )

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate Python context documents")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only print report, don't validate files",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path(__file__).parent.parent / "context" / "python",
        help="Path to context documents directory",
    )

    args = parser.parse_args()

    if not args.docs_dir.exists():
        print(f"Error: Directory not found: {args.docs_dir}")
        sys.exit(1)

    validator = ContextDocValidator(args.docs_dir, fix_mode=args.fix)

    if not args.report_only:
        print("Validating context documents...")
        if args.fix:
            print("(Fix mode enabled - will auto-fix issues)")

        # Validate all documents
        valid_count, error_count, warning_count = validator.validate_all()

        # Validate index.json
        index_result = validator.validate_index_json()
        validator.results.append(index_result)

    # Print report
    validator.print_report()

    # Exit code
    if any(not r.is_valid for r in validator.results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
