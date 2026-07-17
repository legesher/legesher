"""Integration tests for the language-pack YAML pre-commit validator.

The pre-commit hook ``validate-language-pack-yaml`` (configured at
``.pre-commit-config.yaml``) runs ``libs/i18n/scripts/validate_language_pack_yaml.py``
on every changed pack YAML. CORE-710 added cross-section collision
detection at the schema level (``schema_validator.check_duplicates()
['cross_section_collisions']``). CORE-950 wires that into the
pre-commit script so a YAML edit introducing a cross-section collision
fails fast at commit time -- before it reaches the DB or production
translation runs.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATOR = _REPO_ROOT / "libs" / "i18n" / "scripts" / "validate_language_pack_yaml.py"


def _make_pack_dir(
    tmp_path: Path, target: str = "python", lang: str = "ur"
) -> Path:
    """Build a layout the validator recognises (must contain
    ``language-packs`` and ``packs`` in the path).
    """
    pack_dir = (
        tmp_path
        / "libs"
        / "i18n"
        / "language-packs"
        / target
        / lang
        / f"legesher_i18n_{target}_{lang}"
        / "packs"
    )
    pack_dir.mkdir(parents=True, exist_ok=True)
    return pack_dir


def _run_validator(pack_yaml: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "python", str(_VALIDATOR), str(pack_yaml)],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )


class TestCrossSectionCollisionGate:
    def test_blocks_reserved_word_colliding_with_keyword(self, tmp_path: Path) -> None:
        """Reserved-word ``self`` translation matching a keyword
        translation is the exact AYA-213 Cycle-4 Urdu failure mode --
        must be rejected.
        """
        pack_yml = _make_pack_dir(tmp_path) / "3.10.yml"
        pack_yml.write_text(
            textwrap.dedent("""
                language: ur
                target: python
                version: "3.10"
                keywords:
                  in: "میں"
                  def: "تعریف"
                builtins:
                  print: "چھاپ"
                exceptions:
                  ValueError: "قدرغلطی"
                reserved_words:
                  self: "میں"
                  cls: "جماعت"
                """).lstrip(),
            encoding="utf-8",
        )

        result = _run_validator(pack_yml)
        assert result.returncode != 0, (
            f"Validator should have rejected the collision. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "cross" in combined or "collision" in combined, (
            f"Validator output should mention the cross-section collision. "
            f"Output:\n{result.stdout}\n{result.stderr}"
        )

    def test_clean_pack_passes(self, tmp_path: Path) -> None:
        """Negative regression: a clean pack with distinct translations
        must still pass.
        """
        pack_yml = _make_pack_dir(tmp_path) / "3.10.yml"
        pack_yml.write_text(
            textwrap.dedent("""
                language: ur
                target: python
                version: "3.10"
                keywords:
                  in: "میں"
                  def: "تعریف"
                builtins:
                  print: "چھاپ"
                exceptions:
                  ValueError: "قدرغلطی"
                reserved_words:
                  self: "خود"
                  cls: "جماعتخود"
                """).lstrip(),
            encoding="utf-8",
        )

        result = _run_validator(pack_yml)
        assert result.returncode == 0, (
            f"Validator rejected a clean pack. stdout: {result.stdout}"
        )

    def test_blocks_reserved_word_colliding_with_builtin(self, tmp_path: Path) -> None:
        """A reserved-word value matching a builtin value is also a
        cross-section collision.
        """
        pack_yml = _make_pack_dir(tmp_path) / "3.10.yml"
        pack_yml.write_text(
            textwrap.dedent("""
                language: ur
                target: python
                version: "3.10"
                keywords:
                  def: "تعریف"
                builtins:
                  print: "چھاپ"
                exceptions:
                  ValueError: "قدرغلطی"
                reserved_words:
                  self: "چھاپ"
                  cls: "جماعت"
                """).lstrip(),
            encoding="utf-8",
        )

        result = _run_validator(pack_yml)
        assert result.returncode != 0
        combined = (result.stdout + result.stderr).lower()
        assert "cross" in combined or "collision" in combined

    def test_javascript_pack_allows_cross_section_homonym(
        self, tmp_path: Path
    ) -> None:
        """A JavaScript pack may reuse one value across partitions — acorn's
        AST is category-aware, so cross-partition homonyms are legal (CORE-1372).
        The same shape that fails for a Python pack must pass here.

        (``version`` is kept as ``N.N`` to satisfy the current Python-shaped
        version regex; generalizing that grammar is CORE-1503. This isolates the
        cross-section gate.)
        """
        pack_yml = (
            _make_pack_dir(tmp_path, target="javascript", lang="ur") / "3.10.yml"
        )
        pack_yml.write_text(
            textwrap.dedent("""
                language: ur
                target: javascript
                version: "3.10"
                keywords:
                  def: "تعریف"
                builtins:
                  print: "چھاپ"
                exceptions:
                  ValueError: "قدرغلطی"
                reserved_words:
                  self: "چھاپ"
                  cls: "جماعت"
                """).lstrip(),
            encoding="utf-8",
        )

        result = _run_validator(pack_yml)
        combined = (result.stdout + result.stderr).lower()
        assert result.returncode == 0, (
            f"JS pack with a cross-partition homonym should pass. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "cross" not in combined, (
            f"Cross-section check must not run for a JS target. "
            f"Output:\n{result.stdout}\n{result.stderr}"
        )
