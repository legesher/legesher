"""Guards on the pack version-bump gate (CORE-1655, CORE-2058).

The gate exists because a language pack's content is its API: shipping two
vocabularies under one version is silent breakage, and nothing about the
install looks different.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_I18N_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _I18N_ROOT / "scripts" / "require_pack_version_bump.py"


def _load_module():
    sys.path.insert(0, str(_I18N_ROOT))
    spec = importlib.util.spec_from_file_location("require_pack_version_bump", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_module()


def test_every_shipped_pack_declares_one_version() -> None:
    """The repo-wide invariant, and the reason this gate was written.

    50 of 51 packs declared two different versions before CORE-2058 --
    ``__init__.py`` exactly one patch behind ``pyproject.toml`` in every case,
    because the bumps moved one file and not the other. This is what stops it
    silently reaccumulating.
    """
    problems = gate.check_agreement(gate.all_packs())
    assert not problems, "packs declaring two versions:\n" + "\n".join(problems)


def test_the_tree_has_the_packs_we_think_it_has() -> None:
    """A guard on the guard: an empty sweep would pass the test above."""
    pairs = gate.all_packs()
    assert len(pairs) == 51, f"expected 51 pairings, found {len(pairs)}"
    assert ("python", "ar") in pairs


def test_only_pack_content_triggers_the_gate() -> None:
    """A README beside a pack must not demand a version bump.

    The trigger is anchored on the ``packs/`` directory, not "any yml under the
    locale" -- otherwise every doc edit would ask for a release.
    """
    content = (
        "libs/i18n/language-packs/python/ar/legesher_i18n_python_ar/packs/3.12.yml"
    )
    assert gate.changed_packs([content]) == {("python", "ar")}

    for unrelated in (
        "libs/i18n/language-packs/python/ar/README.md",
        "libs/i18n/language-packs/python/ar/pyproject.toml",
        "libs/i18n/scripts/export_packs.py",
        "libs/i18n/language-packs/python/ar/style-guide.yml",
    ):
        assert gate.changed_packs([unrelated]) == set(), unrelated


def test_the_trigger_is_target_aware() -> None:
    """A JavaScript pack is its own pairing, versioned on its own clock."""
    js = "libs/i18n/language-packs/javascript/ar/legesher_i18n_javascript_ar/packs/es2023.yml"
    assert gate.changed_packs([js]) == {("javascript", "ar")}


def test_bump_patch_increments_only_the_patch() -> None:
    assert gate.bump_patch("0.0.4") == "0.0.5"
    assert gate.bump_patch("1.2.9") == "1.2.10"
    assert gate.bump_patch("0.9.0") == "0.9.1"


def test_bump_patch_refuses_a_version_it_cannot_reason_about() -> None:
    """Better to stop than to guess at a shape that is not semver.

    A date-shaped or pre-release version bumped blindly produces a number
    nobody chose, which is worse than a refusal naming the file.
    """
    for bad in ("2026.08.24", "1.0", "0.1.0rc1", ""):
        with pytest.raises(gate.PackVersionError, match="major.minor.patch"):
            gate.bump_patch(bad)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A miniature monorepo with one pack, committed."""

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    pack = tmp_path / "libs/i18n/language-packs/python/xx"
    (pack / "legesher_i18n_python_xx/packs").mkdir(parents=True)
    (pack / "pyproject.toml").write_text('version = "0.0.1"\n', encoding="utf-8")
    (pack / "legesher_i18n_python_xx/__init__.py").write_text(
        '__version__ = "0.0.1"\n', encoding="utf-8"
    )
    (pack / "legesher_i18n_python_xx/packs/3.12.yml").write_text(
        "keywords:\n  for: por\n", encoding="utf-8"
    )
    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    git("add", "-A")
    git("commit", "-qm", "seed")
    return tmp_path


def _point_gate_at(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retarget the module's roots at the fixture repo."""
    monkeypatch.setattr(gate, "_I18N_ROOT", repo_root / "libs/i18n")
    monkeypatch.setattr(gate, "PACKS_ROOT", repo_root / "libs/i18n/language-packs")


CONTENT = "libs/i18n/language-packs/python/xx/legesher_i18n_python_xx/packs/3.12.yml"


def test_content_change_without_a_bump_is_refused(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CORE-1655 case, end to end.

    This is the `while` correction: pack content edited, version untouched.
    """
    _point_gate_at(repo, monkeypatch)
    (repo / CONTENT).write_text("keywords:\n  for: para\n", encoding="utf-8")

    assert gate.main([CONTENT]) == 1


def test_content_change_with_a_bump_passes(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _point_gate_at(repo, monkeypatch)
    (repo / CONTENT).write_text("keywords:\n  for: para\n", encoding="utf-8")
    gate.write_version("python", "xx", "0.0.2")

    assert gate.main([CONTENT]) == 0


def test_a_bump_that_moves_only_pyproject_is_refused(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half-bump that produced CORE-2058's 50-pack drift.

    "The version changed" is satisfied here -- pyproject moved. The gate must
    still refuse, or the desync this whole ticket is about walks straight back
    in one pack at a time.
    """
    _point_gate_at(repo, monkeypatch)
    (repo / CONTENT).write_text("keywords:\n  for: para\n", encoding="utf-8")
    pyproject = repo / "libs/i18n/language-packs/python/xx/pyproject.toml"
    pyproject.write_text('version = "0.0.2"\n', encoding="utf-8")

    assert gate.main([CONTENT]) == 1


def test_fix_bumps_both_declarations_together(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--fix is what makes a 51-pack regeneration one command, not 51 edits."""
    _point_gate_at(repo, monkeypatch)
    (repo / CONTENT).write_text("keywords:\n  for: para\n", encoding="utf-8")

    assert gate.main(["--fix", CONTENT]) == 0
    assert gate.declared_versions("python", "xx") == ("0.0.2", "0.0.2")
    assert gate.main([CONTENT]) == 0


def test_fix_aligns_rather_than_double_bumping_a_hand_bumped_pack(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--fix after a hand bump must not skip a version.

    Someone who already moved pyproject and reached for --fix to finish the
    job should get agreement at the version they chose, not one past it.
    """
    _point_gate_at(repo, monkeypatch)
    (repo / CONTENT).write_text("keywords:\n  for: para\n", encoding="utf-8")
    pyproject = repo / "libs/i18n/language-packs/python/xx/pyproject.toml"
    pyproject.write_text('version = "0.1.0"\n', encoding="utf-8")

    assert gate.main(["--fix", CONTENT]) == 0
    assert gate.declared_versions("python", "xx") == ("0.1.0", "0.1.0")


def test_a_new_pack_is_not_asked_to_bump_a_version_it_never_had(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No committed version means nothing to move."""
    _point_gate_at(repo, monkeypatch)
    new = repo / "libs/i18n/language-packs/python/zz"
    (new / "legesher_i18n_python_zz/packs").mkdir(parents=True)
    (new / "pyproject.toml").write_text('version = "0.0.1"\n', encoding="utf-8")
    (new / "legesher_i18n_python_zz/__init__.py").write_text(
        '__version__ = "0.0.1"\n', encoding="utf-8"
    )
    (new / "legesher_i18n_python_zz/packs/3.12.yml").write_text(
        "x: y\n", encoding="utf-8"
    )

    path = "libs/i18n/language-packs/python/zz/legesher_i18n_python_zz/packs/3.12.yml"
    assert gate.main([path]) == 0


def test_a_commit_touching_no_pack_content_is_ignored(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _point_gate_at(repo, monkeypatch)
    assert gate.main(["libs/i18n/scripts/export_packs.py"]) == 0
    assert gate.main([]) == 0
