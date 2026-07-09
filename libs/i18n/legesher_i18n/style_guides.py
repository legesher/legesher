"""Style guide loader for the translation pipeline.

Loads and deep-merges the hierarchical YAML style guides that describe, per
language, the Python conventions its script can express — the rules/profile
schema: ``supports`` capability flags, ``naming`` rules, ``script``
constraints, and a rendering font. A language guide declares an ``extends``
chain that is resolved in full before merging:

  1. ``python.yml`` — the base every guide extends
  2. ``_ltr.yml`` / ``_rtl.yml`` — the writing-direction layer
  3. ``_cjk.yml`` / ``_arabic.yml`` / … — the script-family overlay (optional)
  4. ``{lang}.yml`` — the language guide itself

Each level deep-merges on top of the previous, with later files winning on key
conflicts. The overlays are content-free structural nodes, so a merged guide's
rules come from the leaf language file; the chain still determines which files
are consulted and in what order.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

_LANG_CODE_RE = re.compile(r"^[a-z]{2,3}$")
# A style-guide filename an ``extends`` entry may name: a bare ``{code}.yml`` /
# ``python.yml`` / ``_overlay.yml``, no path separators or ``..``. Entries that
# fail this are dropped, so a guide can never steer the loader outside its dir.
_SAFE_OVERLAY_NAME = re.compile(r"^_?[a-z0-9][a-z0-9_-]*\.ya?ml$")

logger = logging.getLogger(__name__)

# Path to the canonical language metadata file
_LANGUAGES_JSON = Path(__file__).parent / "languages.json"


class StyleGuideLoader:
    """Load and deep-merge the hierarchical YAML style guides.

    A language guide is assembled from its declared ``extends`` chain — base
    (``python.yml``) → direction (``_ltr``/``_rtl``) → optional script-family
    overlay (``_cjk``, ``_arabic``, …) → the language file. Each level
    deep-merges on top of the previous, later files winning on key conflicts.

    Example:
        >>> loader = StyleGuideLoader()
        >>> guide = loader.load("ar")  # python.yml + _rtl.yml + _arabic.yml + ar.yml
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
        # Parsed-file cache: a single file is read for its ``extends`` during
        # chain resolution and again for its body during the merge, so parse
        # each path at most once per loader instance.
        self._file_cache: dict[str, dict[str, Any] | None] = {}
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
            data = self._load_yaml(path)
            if data is None:
                continue
            merged = self._deep_merge(merged, data)
            logger.debug(
                "Merged style guide: %s (%d top-level keys)", path.name, len(data)
            )

        self._cache[language_code] = merged
        return merged

    def get_supported_languages(self) -> list[str]:
        """List language codes that have a dedicated style guide file.

        Returns only language-specific guides (e.g. ``ar.yml``), excluding
        the base ``python.yml`` and any overlay files. Overlays are the
        underscore-prefixed building blocks — direction layers (``_ltr.yml``,
        ``_rtl.yml``) and script-family overlays (``_cjk.yml``,
        ``_arabic.yml``, …) — which are not loadable language codes.

        Returns:
            Sorted list of language codes.
        """
        if not self.style_guides_dir.exists():
            logger.warning(
                "Style guides directory does not exist: %s",
                self.style_guides_dir,
            )
            return []

        # ``python.yml`` is the base; every ``_*.yml`` file is an overlay
        # (direction layer or script-family overlay) and is not a loadable
        # language code, so both are excluded from the supported list.
        codes = [
            f.stem
            for f in self.style_guides_dir.glob("*.yml")
            if f.is_file() and f.stem != "python" and not f.stem.startswith("_")
        ]

        logger.info("Found %d language-specific style guides", len(codes))
        return sorted(codes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_hierarchy(self, language_code: str) -> list[Path]:
        """Determine the ordered list of style guide files to load.

        When a ``{language_code}.yml`` guide exists, its declared ``extends``
        chain is resolved in full — base → direction → script-family → language
        — by following each file's ``extends`` list transitively. This is what
        pulls a script-family overlay (``_cjk.yml``, ``_arabic.yml``, …) into
        the merge for its member languages. The chain is de-duplicated (a file
        shared by several ancestors is merged once, at its earliest position)
        and cycle-detected.

        When no language guide exists, the loader falls back to the fixed
        ``python.yml`` → ``_rtl.yml``/``_ltr.yml`` hierarchy so callers still
        get base + direction conventions.

        Args:
            language_code: ISO 639-1 language code.

        Returns:
            Ordered list of file paths to load and merge, base-first.

        Raises:
            FileNotFoundError: If ``python.yml`` does not exist.
            ValueError: If the ``extends`` graph contains a cycle.
        """
        base = self.style_guides_dir / "python.yml"
        if not base.exists():
            raise FileNotFoundError(
                f"Base style guide not found: {base}. The python.yml file is required."
            )

        lang_file = self.style_guides_dir / f"{language_code}.yml"
        if lang_file.exists():
            if self._read_extends(lang_file):
                return self._resolve_extends_chain(lang_file)
            # Guide exists but declares no ``extends`` (or is malformed): fall
            # back to the fixed base → direction → language hierarchy so it
            # still inherits the base and direction layers.
            direction = "_rtl.yml" if self._is_rtl(language_code) else "_ltr.yml"
            return [base, self.style_guides_dir / direction, lang_file]

        # No language-specific guide — base + direction only.
        logger.debug(
            "No language-specific style guide for '%s' — using base + direction only",
            language_code,
        )
        direction = "_rtl.yml" if self._is_rtl(language_code) else "_ltr.yml"
        return [base, self.style_guides_dir / direction]

    def _resolve_extends_chain(self, lang_file: Path) -> list[Path]:
        """Resolve a guide's full ``extends`` chain into an ordered file list.

        Performs a post-order traversal of the ``extends`` graph so ancestors
        are merged before the files that extend them, appending *lang_file*
        last. Each file appears once (first-seen position wins). A file that
        appears in its own ancestry raises ``ValueError``.
        """
        ordered: list[Path] = []
        seen: set[str] = set()

        def visit(path: Path, stack: tuple[str, ...]) -> None:
            if path.name in stack:
                cycle = " -> ".join((*stack, path.name))
                raise ValueError(f"Cyclic style-guide extends chain: {cycle}")
            if path.name in seen:
                return
            for parent in self._read_extends(path):
                visit(self.style_guides_dir / parent, (*stack, path.name))
            seen.add(path.name)
            ordered.append(path)

        visit(lang_file, ())
        return ordered

    def _load_yaml(self, path: Path) -> dict[str, Any] | None:
        """Parse a style-guide file once per loader, caching the result.

        The resolver reads a file's ``extends`` and the merge step reads its
        body, so without caching each file is parsed several times per
        :meth:`load`. Returns the parsed mapping, or ``None`` when the file is
        missing, unreadable, or does not parse to a dict.
        """
        key = str(path)
        if key in self._file_cache:
            return self._file_cache[key]

        result: dict[str, Any] | None = None
        if not path.exists():
            logger.warning("Style guide file not found, skipping: %s", path)
        else:
            try:
                with open(path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                if isinstance(data, dict):
                    result = data
                else:
                    logger.warning(
                        "Style guide file did not parse as a dict, skipping: %s",
                        path,
                    )
            except yaml.YAMLError as exc:
                logger.error("Error parsing style guide %s: %s", path, exc)
            except OSError as exc:
                logger.error("Error reading style guide %s: %s", path, exc)

        self._file_cache[key] = result
        return result

    def _read_extends(self, path: Path) -> list[str]:
        """Return the validated ``extends`` list declared in a style guide file.

        Missing files, parse errors, and a missing/invalid ``extends`` key all
        yield an empty list — resolution treats them as roots rather than
        failing, and the merge step logs any file it then cannot read. Each
        entry must be a bare style-guide filename (:data:`_SAFE_OVERLAY_NAME`);
        an entry with a path separator or ``..`` is dropped with a warning, so a
        guide can never make the loader read outside its directory.
        """
        data = self._load_yaml(path)
        if not (isinstance(data, dict) and isinstance(data.get("extends"), list)):
            return []
        parents: list[str] = []
        for entry in data["extends"]:
            name = str(entry)
            if _SAFE_OVERLAY_NAME.match(name):
                parents.append(name)
            else:
                logger.warning(
                    "Ignoring unsafe extends entry %r in %s "
                    "(must be a bare style-guide filename)",
                    name,
                    path,
                )
        return parents

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
