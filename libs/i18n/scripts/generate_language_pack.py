#!/usr/bin/env python3
"""
Generate language packs for new Python versions.

This script generates complete language packs (base English + translated versions)
for a new Python version, leveraging existing translations via inheritance.

Usage:
    python generate_language_pack.py --version 3.14 --input python-content-3.14.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class LanguagePackGenerator:
    """Generate language packs for Python versions."""

    def __init__(
        self,
        version: str,
        languages_dir: Path,
        supported_languages: Optional[List[str]] = None,
    ):
        """Initialize pack generator."""
        self.version = version
        self.languages_dir = languages_dir
        self.python_dir = languages_dir / "python"
        self.version_dir = self.python_dir / version
        self.version_index_path = self.python_dir / "version-index.yml"
        self.supported_languages = supported_languages or ["es", "ar", "zh"]
        self.parent_version = self._find_parent_version()

    def _find_parent_version(self) -> Optional[str]:
        """Find the parent version for inheritance."""
        if not self.version_index_path.exists():
            return None

        with open(self.version_index_path) as f:
            index = yaml.safe_load(f)

        if not index or "python_versions" not in index:
            return None

        versions = sorted(
            index["python_versions"].keys(),
            key=lambda v: tuple(map(int, v.split("."))),
        )

        current = tuple(map(int, self.version.split(".")))
        parent = None

        for v in versions:
            v_tuple = tuple(map(int, v.split(".")))
            if v_tuple < current:
                parent = v

        return parent

    def generate_base_pack(
        self, content: Dict[str, Any], dry_run: bool = False
    ) -> Path:
        """Generate base English language pack."""
        pack = {
            "language": "en",
            "language_name": "English",
            "target": "python",
            "python_version": self.version,
            "mlcp_version": "1.0",
        }

        if self.parent_version:
            pack["extends"] = f"../{self.parent_version}/en.yml"

        # Add keywords
        if "keywords" in content:
            keywords_dict = {}
            for kw in content["keywords"].get("all", []):
                keywords_dict[kw] = kw
            pack["keywords"] = keywords_dict

        # Add built-in functions
        if "builtins" in content:
            builtins_dict = {}
            for name, info in content["builtins"].items():
                builtins_dict[name] = {
                    "name": name,
                    "docstring": info.get("docstring", ""),
                }
            pack["builtins"] = builtins_dict

        # Add built-in types
        if "types" in content:
            types_dict = {}
            for name, info in content["types"].items():
                if info.get("category") == "exception":
                    continue
                types_dict[name] = {
                    "name": name,
                    "docstring": info.get("docstring", ""),
                }
            pack["types"] = types_dict

        # Add metadata
        pack["metadata"] = {
            "auto_generated": True,
            "generated_at": datetime.now().isoformat(),
            "total_items": (
                len(pack.get("keywords", {}))
                + len(pack.get("builtins", {}))
                + len(pack.get("types", {}))
            ),
        }

        output_path = self.version_dir / "en.yml"

        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(pack, f, sort_keys=False, allow_unicode=True)
            print(f"✓ Generated base pack: {output_path}")
        else:
            print(f"[DRY RUN] Would generate: {output_path}")

        return output_path

    def generate_translated_pack(
        self,
        language_code: str,
        translations: Dict[str, Any],
        base_content: Dict[str, Any],
        dry_run: bool = False,
    ) -> Path:
        """Generate translated language pack."""
        language_names = {
            "es": "Spanish",
            "ar": "Arabic",
            "zh": "Chinese",
        }

        pack = {
            "language": language_code,
            "language_name": language_names.get(language_code, language_code.upper()),
            "target": "python",
            "python_version": self.version,
            "mlcp_version": "1.0",
        }

        if self.parent_version:
            pack["extends"] = f"../{self.parent_version}/{language_code}.yml"

        # Add translated keywords
        keywords_dict = {}
        for kw in base_content["keywords"].get("all", []):
            if kw in translations.get("keywords", {}):
                trans = translations["keywords"][kw]
                if isinstance(trans, dict):
                    keywords_dict[kw] = trans.get("translation", kw)
                else:
                    keywords_dict[kw] = trans
            else:
                keywords_dict[kw] = kw

        pack["keywords"] = keywords_dict

        # Add translated built-ins
        builtins_dict = {}
        for name in base_content.get("builtins", {}).keys():
            if name in translations.get("builtins", {}):
                trans = translations["builtins"][name]
                if isinstance(trans, dict):
                    builtins_dict[name] = trans.get("translation", name)
                else:
                    builtins_dict[name] = trans
            else:
                builtins_dict[name] = name

        pack["builtins"] = builtins_dict

        # Add translated types
        types_dict = {}
        for name in base_content.get("types", {}).keys():
            if base_content["types"][name].get("category") == "exception":
                continue

            if name in translations.get("types", {}):
                trans = translations["types"][name]
                if isinstance(trans, dict):
                    types_dict[name] = trans.get("translation", name)
                else:
                    types_dict[name] = trans
            else:
                types_dict[name] = name

        pack["types"] = types_dict

        stats = translations.get("statistics", {})
        pack["metadata"] = {
            "auto_generated": True,
            "generated_at": datetime.now().isoformat(),
            "reuse_rate": stats.get("reuse_rate", "N/A"),
            "review_status": "needs-review"
            if stats.get("new_items", 0) > 0
            else "stable",
        }

        output_path = self.version_dir / f"{language_code}.yml"

        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(pack, f, sort_keys=False, allow_unicode=True)
            print(
                f"✓ Generated {language_names.get(language_code)} pack: {output_path}"
            )
        else:
            print(f"[DRY RUN] Would generate: {output_path}")

        return output_path

    def update_version_index(
        self, content: Dict[str, Any], dry_run: bool = False
    ) -> None:
        """Update version-index.yml with new Python version."""
        if self.version_index_path.exists():
            with open(self.version_index_path) as f:
                index = yaml.safe_load(f) or {}
        else:
            index = {"python_versions": {}, "metadata": {}}

        added_keywords = []
        if self.parent_version and "keywords" in content:
            parent_path = self.python_dir / self.parent_version / "en.yml"
            if parent_path.exists():
                with open(parent_path) as f:
                    parent_pack = yaml.safe_load(f)
                parent_keywords = set(parent_pack.get("keywords", {}).keys())
                current_keywords = set(content["keywords"].get("all", []))
                added_keywords = sorted(current_keywords - parent_keywords)

        index["python_versions"][self.version] = {
            "added_keywords": added_keywords,
            "extends": self.parent_version,
            "supported_languages": ["en"] + self.supported_languages,
        }

        index["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "latest_version": self.version,
        }

        if not dry_run:
            with open(self.version_index_path, "w", encoding="utf-8") as f:
                yaml.dump(index, f, sort_keys=False, allow_unicode=True)
            print(f"✓ Updated version index: {self.version_index_path}")
        else:
            print(f"[DRY RUN] Would update: {self.version_index_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate language packs")
    parser.add_argument("--version", required=True, help="Python version")
    parser.add_argument(
        "--input", type=Path, required=True, help="Extracted content JSON"
    )
    parser.add_argument("--translations-dir", type=Path, help="Translations directory")
    parser.add_argument("--languages-dir", type=Path, default=Path("languages"))
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    generator = LanguagePackGenerator(
        version=args.version,
        languages_dir=args.languages_dir,
    )

    with open(args.input) as f:
        content = json.load(f)

    print(f"\n📦 Generating language packs for Python {args.version}...")
    generator.generate_base_pack(content, dry_run=args.dry_run)

    if not args.base_only and args.translations_dir:
        for lang in generator.supported_languages:
            trans_file = args.translations_dir / f"python-{args.version}-{lang}.json"
            if trans_file.exists():
                with open(trans_file) as f:
                    translations = json.load(f)
                generator.generate_translated_pack(
                    lang, translations, content, dry_run=args.dry_run
                )

    generator.update_version_index(content, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n✓ Generated language packs for Python {args.version}")


if __name__ == "__main__":
    main()
