"""Shared artifact I/O primitives (CORE-1710).

Covers the family-level acceptance criteria: a write killed mid-flight
leaves the PREVIOUS valid artifact intact, and there is exactly one
semver parser behind every artifact's version envelope.
"""

import json
import os
from pathlib import Path

import pytest

from legesher_core.artifact_io import atomic_write_text, parse_semver
from legesher_core.register_map import (
    RegisterMap,
    RegisterMapDocument,
    RegisterMapEntry,
)
from legesher_core.translation_memory import TranslationMemoryDocument


def _entry(node_id: str = "n000001") -> RegisterMapEntry:
    from legesher_core.register_map import content_hash

    return RegisterMapEntry(
        node_id=node_id,
        element_class="identifier",
        original_text="calculate_tax",
        structural_path="module/function_definition[0]/identifier[0]",
        content_hash=content_hash("calculate_tax"),
    )


def _register_document() -> RegisterMapDocument:
    document = RegisterMapDocument()
    register_map = RegisterMap(file="src/tax.py")
    register_map.add(_entry())
    document.files["src/tax.py"] = register_map
    return document


class TestAtomicWrite:
    def test_writes_content(self, tmp_path):
        target = tmp_path / "artifact.json"
        atomic_write_text(target, '{"a": 1}\n')
        assert target.read_text(encoding="utf-8") == '{"a": 1}\n'

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / ".legesher" / "nested" / "artifact.json"
        atomic_write_text(target, "x\n")
        assert target.read_text(encoding="utf-8") == "x\n"

    def test_failed_write_leaves_previous_artifact_intact(self, tmp_path, monkeypatch):
        """The whole point: a crash mid-write must not destroy the file.

        ``Path.write_text`` truncates first, so the old artifact is gone
        the instant the write begins. The temp+replace path keeps it
        until the replace succeeds.
        """
        target = tmp_path / "artifact.json"
        original = '{"valid": true}\n'
        target.write_text(original, encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            atomic_write_text(target, '{"replacement": true}\n')

        assert target.read_text(encoding="utf-8") == original
        assert json.loads(target.read_text(encoding="utf-8")) == {"valid": True}

    def test_failed_write_leaves_no_temp_file_behind(self, tmp_path, monkeypatch):
        """A stray temp file in .legesher/ would show up in git status."""
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            atomic_write_text(target, "new\n")
        assert [p.name for p in tmp_path.iterdir()] == ["artifact.json"]

    def test_temp_file_is_a_sibling(self, tmp_path):
        """os.replace is only atomic within a filesystem, so the temp
        file must live in the destination's own directory."""
        target = tmp_path / "artifact.json"
        seen: list[Path] = []
        real_replace = os.replace

        def spy(src, dst):
            seen.append(Path(src))
            return real_replace(src, dst)

        import legesher_core.artifact_io as module

        original = module.os.replace
        module.os.replace = spy
        try:
            atomic_write_text(target, "x\n")
        finally:
            module.os.replace = original
        assert seen and seen[0].parent == tmp_path

    def test_writes_lf_regardless_of_platform_default(self, tmp_path):
        """The committed artifact must not differ by who wrote it."""
        target = tmp_path / "artifact.json"
        atomic_write_text(target, "line1\nline2\n")
        assert target.read_bytes() == b"line1\nline2\n"


class TestAtomicSaveAcrossTheFamily:
    """Every artifact writer routes through the atomic helper."""

    def test_register_map_save_survives_a_killed_write(self, tmp_path, monkeypatch):
        path = tmp_path / ".legesher" / "register_map.json"
        _register_document().save(path)
        before = path.read_text(encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("killed mid-write")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            _register_document().save(path)
        assert path.read_text(encoding="utf-8") == before
        RegisterMapDocument.load(path)  # still parses

    def test_translation_memory_save_survives_a_killed_write(
        self, tmp_path, monkeypatch
    ):
        path = tmp_path / ".legesher" / "translation_memory.json"
        document = TranslationMemoryDocument()
        document.get_or_create("src/tax.py").add(
            "n000001", "# a comment", "es", "# un comentario", minted_by="model"
        )
        document.save(path)
        before = path.read_text(encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("killed mid-write")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            document.save(path)
        assert path.read_text(encoding="utf-8") == before
        TranslationMemoryDocument.load(path)  # still parses


class TestParseSemver:
    def test_parses(self):
        assert parse_semver("1.2.3") == (1, 2, 3)

    @pytest.mark.parametrize("bad", ["1.2", "1.2.3.4", "x.y.z", "", "1.2.x"])
    def test_rejects_malformed(self, bad):
        with pytest.raises(ValueError, match="Invalid schema_version"):
            parse_semver(bad)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="Invalid schema_version"):
            parse_semver(None)  # type: ignore[arg-type]

    def test_is_the_only_parser(self):
        """One parser, both consumers — the duplication CORE-1710 removed."""
        import legesher_core.register_map.model as register_model
        import legesher_core.translation_memory.model as tm_model

        assert register_model.parse_semver is parse_semver
        assert tm_model.parse_semver is parse_semver
        assert not hasattr(register_model, "_parse_semver")
        assert not hasattr(tm_model, "_parse_semver")


class TestFileMode:
    """mkstemp creates 0600 and os.replace carries the temp file's mode
    onto the destination — a plain temp+replace silently tightens a
    world-readable artifact to owner-only on its first save."""

    def test_existing_mode_is_preserved(self, tmp_path):
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")
        os.chmod(target, 0o644)
        atomic_write_text(target, "new\n")
        assert target.stat().st_mode & 0o777 == 0o644

    def test_an_unusual_existing_mode_is_preserved(self, tmp_path):
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")
        os.chmod(target, 0o664)
        atomic_write_text(target, "new\n")
        assert target.stat().st_mode & 0o777 == 0o664

    def test_a_new_file_gets_the_umask_default_not_0600(self, tmp_path):
        target = tmp_path / "artifact.json"
        atomic_write_text(target, "x\n")
        umask = os.umask(0)
        os.umask(umask)
        assert target.stat().st_mode & 0o777 == 0o666 & ~umask

    def test_register_map_save_does_not_tighten_permissions(self, tmp_path):
        path = tmp_path / ".legesher" / "register_map.json"
        _register_document().save(path)
        os.chmod(path, 0o644)
        _register_document().save(path)
        assert path.stat().st_mode & 0o777 == 0o644
