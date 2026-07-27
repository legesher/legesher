"""Per-target profile + guide loading for generation prompts.

The CORE-1503 target-profile system, sliced to what generation consumes today
(CORE-1608): each programming-language target owns a directory under
``libs/i18n/spec/targets/{target}/`` holding

- ``profile.json`` -- machine-readable target facts (version-token grammar,
  partitions, identifier grammar, contextual keywords) plus the
  prompt-consumed rule strings under ``prompt_rules``, and
- ``GUIDE.md`` -- the prose the machine rules can't carry, rendered verbatim
  (minus its leading provenance/lint comments) into the PromptBuilder's
  "Target Guide" section.

Per-target DATA, never per-target code paths: this loader returns data and
the PromptBuilder substitutes it -- no ``if target == ...`` branch exists in
any consumer. A target with no spec directory (today: ``python``) resolves to
an empty spec and consumers keep their historical defaults byte-for-byte;
migrating Python onto a profile stays with CORE-1503.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Strips every leading HTML comment so GUIDE.md can carry provenance notes
# and lint directives without spending prompt tokens on them.
_LEADING_COMMENT_RE = re.compile(r"\A(?:\s*<!--.*?-->)+\s*", re.DOTALL)

# Target names become path segments: constrain them hard.
_TARGET_RE = re.compile(r"\A[a-z][a-z0-9_-]{0,31}\Z")


class TargetProfileLoader:
    """Load a target's ``profile.json`` + ``GUIDE.md`` from the spec tree."""

    def __init__(self, targets_dir: Path | None = None) -> None:
        """Initialise the loader.

        Args:
            targets_dir: Directory containing per-target spec directories.
                Defaults to ``libs/i18n/spec/targets/`` relative to this
                file, mirroring ``StyleGuideLoader``.
        """
        if targets_dir is None:
            self.targets_dir = Path(__file__).parent.parent / "spec" / "targets"
        else:
            self.targets_dir = Path(targets_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, target: str) -> dict[str, Any]:
        """Return ``{"profile": dict, "guide": str}`` for *target*.

        A target with no spec directory returns ``{}`` -- the signal that a
        consumer must keep its target-neutral defaults untouched. A present
        but unreadable ``profile.json`` raises instead of being skipped:
        silently dropping it would hand a generation run another language's
        instincts, which is the exact defect this module exists to prevent.

        Args:
            target: Target name (e.g. ``"javascript"``).

        Raises:
            ValueError: If *target* is not a valid target name, or its
                ``profile.json`` exists but cannot be parsed into an object.
        """
        if not _TARGET_RE.match(target):
            raise ValueError(
                f"Invalid target name: {target!r}. Must be lowercase "
                "letters/digits/hyphen/underscore, starting with a letter."
            )

        if target in self._cache:
            return self._cache[target]

        target_dir = self.targets_dir / target
        profile_path = target_dir / "profile.json"
        guide_path = target_dir / "GUIDE.md"

        spec: dict[str, Any] = {}
        if profile_path.is_file() or guide_path.is_file():
            profile: dict[str, Any] = {}
            if profile_path.is_file():
                try:
                    with open(profile_path, encoding="utf-8") as fh:
                        profile = json.load(fh)
                except (OSError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"Unreadable target profile {profile_path}: {exc}"
                    ) from exc
                if not isinstance(profile, dict):
                    raise ValueError(
                        f"Target profile {profile_path} must be a JSON "
                        f"object, got {type(profile).__name__}"
                    )
            guide = ""
            if guide_path.is_file():
                guide = _LEADING_COMMENT_RE.sub(
                    "", guide_path.read_text(encoding="utf-8")
                ).strip()
            spec = {"profile": profile, "guide": guide}
            logger.info("Loaded target spec: %s", target_dir)

        self._cache[target] = spec
        return spec
