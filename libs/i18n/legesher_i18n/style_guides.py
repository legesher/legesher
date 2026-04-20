"""Style guide loader for translation pipeline.

This module loads and merges hierarchical YAML style guide files
that define language-specific translation conventions. Style guides
follow a three-level hierarchy:

  1. ``python.yml`` — base rules for all Python translations
  2. ``_ltr.yml`` or ``_rtl.yml`` — direction-specific rules
  3. ``{lang}.yml`` — language-specific overrides (optional)

Each level deep-merges on top of the previous, with later files
winning on key conflicts.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

_LANG_CODE_RE = re.compile(r"^[a-z]{2,3}$")

logger = logging.getLogger(__name__)

# Path to the canonical language metadata file
_LANGUAGES_JSON = Path(__file__).parent / "languages.json"


class StyleGuideLoader:
    """Load and merge hierarchical YAML style guide files.

    Style guides provide translation conventions organised in a three-level
    hierarchy: base (Python), then direction (LTR or RTL), then
    language-specific overrides. Each level deep-merges on top of the
    previous, with later files winning on key conflicts.

    Example:
        >>> loader = StyleGuideLoader()
        >>> guide = loader.load("ar")  # merges python.yml + _rtl.yml + ar.yml
        >>> guide["formatting"]["comment_prefix"]
        '#'
    """

    def __init__(self, style_guides_dir: Path | None = None) -> None:
        """Initialise the style guide loader.

        Args:
            style_guides_dir: Directory containing style guide YAML files.
                Defaults to ``libs/i18n/style-guides/`` relative to this file.
        """
        if style_guides_dir is None:
            self.style_guides_dir = Path(__file__).parent.parent / "style-guides"
        else:
            self.style_guides_dir = Path(style_guides_dir)

        self._rtl_languages: set[str] | None = None
        self._cache: dict[str, dict[str, Any]] = {}
        logger.info("StyleGuideLoader initialised: %s", self.style_guides_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, language_code: str) -> dict[str, Any]:
        """Load and deep-merge the style guide hierarchy for a language.

        Args:
            language_code: ISO 639-1 language code (e.g. ``"es"``, ``"ar"``).
                Must be 2-3 lowercase ASCII letters.

        Returns:
            Merged style guide dictionary.

        Raises:
            FileNotFoundError: If the base ``python.yml`` file does not exist.
            ValueError: If ``language_code`` is not a valid ISO 639-1 code.
        """
        if not _LANG_CODE_RE.match(language_code):
            raise ValueError(
                f"Invalid language code: {language_code!r}. "
                "Must be 2-3 lowercase ASCII letters."
            )

        if language_code in self._cache:
            return self._cache[language_code]

        hierarchy = self._resolve_hierarchy(language_code)
        merged: dict[str, Any] = {}

        for path in hierarchy:
            if not path.exists():
                logger.warning("Style guide file not found, skipping: %s", path)
                continue

            try:
                with open(path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)

                if not isinstance(data, dict):
                    logger.warning(
                        "Style guide file did not parse as a dict, skipping: %s",
                        path,
                    )
                    continue

                merged = self._deep_merge(merged, data)
                logger.debug(
                    "Loaded style guide: %s (%d top-level keys)",
                    path.name,
                    len(data),
                )
            except yaml.YAMLError as exc:
                logger.error("Error parsing style guide %s: %s", path, exc)
            except OSError as exc:
                logger.error("Error reading style guide %s: %s", path, exc)

        self._cache[language_code] = merged
        return merged

    def get_supported_languages(self) -> list[str]:
        """List language codes that have a dedicated style guide file.

        Returns only language-specific guides (e.g. ``ar.yml``), excluding
        the base ``python.yml`` and direction files (``_ltr.yml``,
        ``_rtl.yml``).

        Returns:
            Sorted list of language codes.
        """
        if not self.style_guides_dir.exists():
            logger.warning(
                "Style guides directory does not exist: %s",
                self.style_guides_dir,
            )
            return []

        excluded = {"python", "_ltr", "_rtl"}
        codes = [
            f.stem
            for f in self.style_guides_dir.glob("*.yml")
            if f.is_file() and f.stem not in excluded
        ]

        logger.info("Found %d language-specific style guides", len(codes))
        return sorted(codes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_hierarchy(self, language_code: str) -> list[Path]:
        """Determine the ordered list of style guide files to load.

        The hierarchy is always:
          1. ``python.yml`` (base — required)
          2. ``_rtl.yml`` or ``_ltr.yml`` (direction layer)
          3. ``{language_code}.yml`` (language-specific — optional)

        Args:
            language_code: ISO 639-1 language code.

        Returns:
            Ordered list of file paths to load and merge.

        Raises:
            FileNotFoundError: If ``python.yml`` does not exist.
        """
        base = self.style_guides_dir / "python.yml"
        if not base.exists():
            raise FileNotFoundError(
                f"Base style guide not found: {base}. The python.yml file is required."
            )

        hierarchy: list[Path] = [base]

        # Direction layer
        if self._is_rtl(language_code):
            hierarchy.append(self.style_guides_dir / "_rtl.yml")
        else:
            hierarchy.append(self.style_guides_dir / "_ltr.yml")

        # Language-specific layer
        lang_file = self.style_guides_dir / f"{language_code}.yml"
        if lang_file.exists():
            hierarchy.append(lang_file)
        else:
            logger.debug(
                "No language-specific style guide for '%s' — "
                "using base + direction only",
                language_code,
            )

        return hierarchy

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge *override* into *base*.

        For overlapping keys:
          - If both values are dicts, recurse.
          - Otherwise the ``override`` value wins.

        Neither input dict is mutated.

        Args:
            base: The base dictionary.
            override: The dictionary whose values take precedence.

        Returns:
            A new merged dictionary.
        """
        merged = dict(base)
        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _is_rtl(self, language_code: str) -> bool:
        """Check whether *language_code* is a right-to-left language.

        Uses ``languages.json`` as the source of truth.
        """
        if self._rtl_languages is None:
            self._rtl_languages = self._load_rtl_set()
        return language_code in self._rtl_languages

    def _load_rtl_set(self) -> set[str]:
        """Load the set of RTL language codes from ``languages.json``."""
        try:
            with open(_LANGUAGES_JSON, encoding="utf-8") as fh:
                data = json.load(fh)

            languages = data.get("languages", {})
            rtl_codes = {
                code for code, meta in languages.items() if meta.get("rtl") is True
            }
            logger.debug("RTL languages: %s", rtl_codes)
            return rtl_codes
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load languages.json: %s", exc)
            return set()
