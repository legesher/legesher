"""Pinned vectors for the text-identity contract (CORE-2024).

These outputs are baked into ``.legesher/`` artifacts on disk, so they are
frozen: a failing pin here means an artifact-breaking change, not a test to
update. The carve's removal phase (CORE-2027) duplicates these pins into the
map engine's own suite, making drift visible on both sides.
"""

from legesher_core.text_identity import (
    CONTENT_HASH_LENGTH,
    compare_key,
    content_hash,
    legacy_nfc_hash,
    normalize_nfc,
    normalize_text,
)


class TestPinnedVectors:
    def test_content_hash_ascii(self):
        assert content_hash("hello") == "2cf24dba5fb0a30e"

    def test_content_hash_folds_crlf(self):
        assert content_hash("a\r\nb") == content_hash("a\nb") == "7e18f737311b2dc3"

    def test_content_hash_nfc_stable(self):
        composed = "café"
        decomposed = "café"
        assert content_hash(composed) == content_hash(decomposed) == "850f7dc43910ff89"

    def test_legacy_hash_preserves_crlf(self):
        assert legacy_nfc_hash("a\r\nb") == "18745f36a05e2907"
        assert legacy_nfc_hash("a\r\nb") != content_hash("a\r\nb")

    def test_legacy_and_content_agree_on_lf_only_text(self):
        assert legacy_nfc_hash("a\nb") == content_hash("a\nb")

    def test_hash_length(self):
        assert len(content_hash("x")) == CONTENT_HASH_LENGTH == 16


class TestNormalization:
    def test_normalize_text_is_lf_then_nfc(self):
        assert normalize_text("café\r\n") == "café\n"

    def test_unicode_line_separators_are_content(self):
        # U+2028/U+2029/U+0085 are content, not terminators.
        text = "a\u2028b\u2029c\u0085d"
        assert normalize_text(text) == text

    def test_normalize_nfc_is_idempotent(self):
        assert normalize_nfc(normalize_nfc("café")) == "café"


class TestCompareKey:
    def test_fullwidth_folds(self):
        assert compare_key("Ｆｕｌｌ") == "full"

    def test_ligature_folds(self):
        assert compare_key("ﬁle") == "file"

    def test_case_folds(self):
        assert compare_key("Print") == compare_key("PRINT") == "print"


class TestReExports:
    # These two assertions leave with the map family (CORE-2027 removal
    # phase); until then the register_map re-exports must be the same
    # objects, never copies.
    def test_node_identity_reexports_are_identical(self):
        from legesher_core.register_map.node_identity import content_hash as via_map

        assert via_map is content_hash

    def test_node_identity_normalize_reexport_is_identical(self):
        from legesher_core.register_map.node_identity import normalize_text as via_map

        assert via_map is normalize_text

    def test_correction_reexport_is_identical(self):
        from legesher_core.register_map.correction import compare_key as via_map

        assert via_map is compare_key
