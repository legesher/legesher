"""Tests for the TM store schema and versioned serialization (CORE-411 item 1).

Covers the TMSegment / TranslationMemory / TranslationMemoryDocument
dataclasses, the (node identity, source-content hash, target language) key,
the versioned JSON artifact under .legesher/, order-stable serialization,
and lossless embeddability in the register-map artifact family.
"""

import json

import pytest

from legesher_core.text_identity import content_hash
from legesher_core.translation_memory.model import (
    ARTIFACT_KIND,
    DEFAULT_ARTIFACT_FILENAME,
    MINTED_BY,
    SCHEMA_VERSION,
    SEGMENT_STATUSES,
    TMSegment,
    TranslationMemory,
    TranslationMemoryDocument,
    default_artifact_path,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_segment(node_id="n000001", source_text="# compute the tax", **overrides):
    defaults = dict(
        node_id=node_id,
        source_hash=content_hash(source_text),
        target_lang="es",
        source_text=source_text,
        translated_text="# calcular el impuesto",
        minted_by="model",
        minted_at="2026-08-04T00:00:00+00:00",
        attribution="test-model",
    )
    defaults.update(overrides)
    return TMSegment(**defaults)


# ---------------------------------------------------------------------------
# TMSegment
# ---------------------------------------------------------------------------


class TestTMSegment:
    def test_provenance_vocabulary(self):
        assert MINTED_BY == frozenset({"model", "human", "import"})
        assert SEGMENT_STATUSES == frozenset({"active", "stale"})

    def test_key_is_node_hash_lang(self):
        segment = make_segment()
        assert segment.key == (
            "n000001",
            content_hash("# compute the tax"),
            "es",
        )

    def test_round_trips_via_dict(self):
        segment = make_segment()
        restored = TMSegment.from_dict(segment.to_dict())
        assert restored == segment

    def test_invalid_minted_by_rejected(self):
        with pytest.raises(ValueError, match="minted_by"):
            make_segment(minted_by="gremlin")

    def test_invalid_status_rejected(self):
        with pytest.raises(ValueError, match="status"):
            make_segment(status="pending")

    def test_text_is_stored_nfc(self):
        # "e" + COMBINING ACUTE ACCENT must be stored precomposed (U+00E9).
        decomposed = "café"
        segment = make_segment(
            source_text=decomposed,
            source_hash=content_hash(decomposed),
            translated_text=decomposed,
        )
        assert segment.source_text == "café"
        assert segment.translated_text == "café"
        # And the stored hash matches the NFC contract.
        assert segment.source_hash == content_hash("café")

    def test_hash_must_match_source_text(self):
        with pytest.raises(ValueError, match="source_hash"):
            make_segment(source_hash="00" * 8)


# ---------------------------------------------------------------------------
# TranslationMemory — store behavior + order-stable serialization
# ---------------------------------------------------------------------------


class TestTranslationMemory:
    def test_add_computes_source_hash(self):
        tm = TranslationMemory(file="src/example.py")
        segment = tm.add("n000001", "# hello", "es", "# hola", minted_by="human")
        assert segment.source_hash == content_hash("# hello")
        assert segment.key in tm.segments

    def test_add_rejects_unknown_minted_by(self):
        tm = TranslationMemory()
        with pytest.raises(ValueError, match="minted_by"):
            tm.add("n000001", "# hello", "es", "# hola", minted_by="wizard")

    def test_add_same_key_replaces(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        replaced = tm.add("n000001", "# hello", "es", "# buenas", minted_by="human")
        assert len(tm.segments) == 1
        assert tm.segments[replaced.key].translated_text == "# buenas"
        assert tm.segments[replaced.key].minted_by == "human"

    def test_serialization_is_insertion_order_independent(self):
        """Same content, different insertion order -> identical payload."""
        a = TranslationMemory(file="src/example.py")
        b = TranslationMemory(file="src/example.py")
        entries = [
            ("n000002", "# beta", "es", "# beta-es"),
            ("n000001", "# alpha", "ar", "# alpha-ar"),
            ("n000001", "# alpha", "es", "# alpha-es"),
        ]
        for node_id, source, lang, translated in entries:
            a.add(
                node_id,
                source,
                lang,
                translated,
                minted_by="import",
                minted_at="2026-08-04T00:00:00+00:00",
            )
        for node_id, source, lang, translated in reversed(entries):
            b.add(
                node_id,
                source,
                lang,
                translated,
                minted_by="import",
                minted_at="2026-08-04T00:00:00+00:00",
            )
        assert a.to_dict() == b.to_dict()
        serialized = [(s["node_id"], s["target_lang"]) for s in a.to_dict()["segments"]]
        assert serialized == sorted(serialized)

    def test_round_trips_via_dict(self):
        tm = TranslationMemory(file="src/example.py")
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        tm.add("n000002", "docstring text", "es", "texto", minted_by="human")
        restored = TranslationMemory.from_dict(tm.to_dict())
        assert restored.file == tm.file
        assert restored.segments == tm.segments

    def test_counters_are_not_serialized(self):
        """Counters are session instrumentation, not artifact state — a
        cache run must not dirty the committed artifact."""
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        tm.lookup("n000001", "# hello", "es")
        tm.lookup("n000009", "# nope", "es")
        payload = json.dumps(tm.to_dict())
        assert "hits" not in payload
        assert "misses" not in payload
        restored = TranslationMemory.from_dict(tm.to_dict())
        assert restored.stats()["hits"] == 0
        assert restored.stats()["misses"] == 0

    def test_from_dict_rejects_duplicate_keys(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        data = tm.to_dict()
        data["segments"].append(dict(data["segments"][0]))
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            TranslationMemory.from_dict(data)


# ---------------------------------------------------------------------------
# TranslationMemoryDocument — versioned artifact under .legesher/
# ---------------------------------------------------------------------------


class TestTranslationMemoryDocument:
    def make_document(self):
        doc = TranslationMemoryDocument(source_lang="en")
        tm = doc.get_or_create("src/example.py")
        tm.add(
            "n000001",
            "# compute the tax",
            "es",
            "# calcular el impuesto",
            minted_by="model",
            minted_at="2026-08-04T00:00:00+00:00",
        )
        return doc

    def test_schema_version_is_semver(self):
        major, minor, patch = SCHEMA_VERSION.split(".")
        assert major.isdigit() and minor.isdigit() and patch.isdigit()

    def test_get_or_create_is_idempotent(self):
        doc = TranslationMemoryDocument()
        first = doc.get_or_create("src/example.py")
        second = doc.get_or_create("src/example.py")
        assert first is second
        assert first.file == "src/example.py"

    def test_round_trips_via_dict(self):
        doc = self.make_document()
        restored = TranslationMemoryDocument.from_dict(doc.to_dict())
        assert restored.schema_version == SCHEMA_VERSION
        assert restored.source_lang == "en"
        assert set(restored.files) == {"src/example.py"}
        assert (
            restored.files["src/example.py"].segments
            == doc.files["src/example.py"].segments
        )

    def test_save_and_load_round_trip(self, tmp_path):
        doc = self.make_document()
        path = default_artifact_path(tmp_path)
        assert path == tmp_path / ".legesher" / DEFAULT_ARTIFACT_FILENAME
        doc.save(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["artifact"] == ARTIFACT_KIND
        restored = TranslationMemoryDocument.load(path)
        assert restored.to_dict() == doc.to_dict()

    def test_saved_artifact_is_byte_stable(self, tmp_path):
        """Save -> load -> save produces byte-identical files (git-friendly)."""
        doc = self.make_document()
        first = tmp_path / "first.json"
        second = tmp_path / "second.json"
        doc.save(first)
        TranslationMemoryDocument.load(first).save(second)
        assert first.read_bytes() == second.read_bytes()

    def test_load_rejects_wrong_artifact_kind(self, tmp_path):
        data = self.make_document().to_dict()
        data["artifact"] = "something-else"
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="artifact"):
            TranslationMemoryDocument.load(path)

    def test_load_rejects_incompatible_major_version(self, tmp_path):
        data = self.make_document().to_dict()
        data["schema_version"] = "999.0.0"
        path = tmp_path / "future.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="schema_version"):
            TranslationMemoryDocument.load(path)

    def test_load_accepts_newer_minor_version(self, tmp_path):
        data = self.make_document().to_dict()
        major = SCHEMA_VERSION.split(".")[0]
        data["schema_version"] = f"{major}.999.0"
        path = tmp_path / "minor.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        restored = TranslationMemoryDocument.load(path)
        assert restored.schema_version == f"{major}.999.0"

    def test_document_stats_aggregates_files(self):
        doc = self.make_document()
        other = doc.get_or_create("src/other.py")
        other.add("n000001", "# hi", "es", "# hola", minted_by="human")
        doc.files["src/example.py"].lookup("n000001", "# compute the tax", "es")
        other.lookup("n000001", "# edited", "es")
        stats = doc.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["segments"] == 2


# ---------------------------------------------------------------------------
# Artifact family — lossless embedding contract (CORE-1435 / CORE-1663)
# ---------------------------------------------------------------------------


class TestArtifactFamilyEmbedding:
    def test_payload_embeds_losslessly_in_a_combined_document(self, tmp_path):
        """The document payload is self-describing and embeds losslessly
        under a single key of a future combined artifact — the same
        discipline as the artifact-family embed contract."""
        doc = TranslationMemoryDocument(source_lang="en")
        tm = doc.get_or_create("src/example.py")
        tm.add(
            "n000001",
            "# compute the tax",
            "ar",
            "# احسب الضريبة",
            minted_by="human",
            minted_at="2026-08-04T00:00:00+00:00",
            attribution="native-review",
        )

        # Embedded payload == standalone file payload, byte-shape identical.
        standalone = tmp_path / "translation_memory.json"
        doc.save(standalone)
        file_payload = json.loads(standalone.read_text(encoding="utf-8"))
        combined = {"translation_memory": doc.to_dict()}
        assert combined["translation_memory"] == file_payload

        # And it restores losslessly from the combined document.
        round_tripped = json.loads(json.dumps(combined, ensure_ascii=False))
        restored = TranslationMemoryDocument.from_dict(
            round_tripped["translation_memory"]
        )
        assert restored.to_dict() == doc.to_dict()
