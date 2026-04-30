"""LLMTranslator collision retry / suffix recovery (CORE-710 + CORE-950).

CORE-710 added a pack-aware ``IdentifierMap.add()`` that raises
``ValueError`` when an LLM-proposed identifier translation matches a
reserved pack value (e.g. ``self -> propio`` for Spanish). The
deferred wiring left ``LLMTranslator.translate_code`` exposed: a single
collision would crash the whole batch.

CORE-950 closes this in two layers:

1. Prompt: ``forbidden_values`` lists every reserved value (already
   shipped). LLM avoids collisions in the first place.
2. Translator: ``LLMTranslator`` constructs a pack-aware ``IdentifierMap``
   and the batch loop catches ``ValueError``, applying a numeric
   suffix as a deterministic fallback so the batch survives.

These tests cover layer 2.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from legesher_core.tree_sitter.identifier_map import IdentifierMap
from legesher_core.tree_sitter.llm_translator import LLMTranslator


def _mock_pack(
    *,
    self_value: str = "propio",
    cls_value: str = "clase",
) -> MagicMock:
    """Build a mock LanguagePack with one collision target."""
    pack = MagicMock()
    pack.keywords = {"def": "definir", "return": "devolver"}
    pack.builtins = {"print": "imprimir"}
    pack.exceptions = {}
    pack.reserved_words = {"self": self_value, "cls": cls_value}
    pack.language = "es"
    return pack


class _CollidingBackend:
    """Backend whose first response always collides with self_value."""

    def __init__(self, collision_value: str = "propio") -> None:
        self.collision_value = collision_value
        self.batch_calls: list[list[dict[str, Any]]] = []

    def translate_text(
        self, text: str, source_lang: str, target_lang: str, context: dict | None = None
    ) -> str:
        return self.collision_value

    def translate_batch(
        self, items: list[dict], source_lang: str, target_lang: str
    ) -> list[str]:
        self.batch_calls.append(list(items))
        # Identifier batches: always return the colliding value.
        if items and "kind" not in items[0].get("context", {}):
            return [self.collision_value for _ in items]
        # Text batches: return the original text unchanged so we don't
        # accidentally crash the test on text translation logic.
        return [item.get("text", "") for item in items]


class TestPackAwareCollisionRetry:
    def test_translation_completes_when_llm_proposes_colliding_value(self) -> None:
        """The colliding-backend would crash on .add() without recovery.
        With the suffix fallback, translate_code must complete and the
        translated code must NOT contain a bare collision with the
        reserved value.
        """
        pack = _mock_pack()
        ident_map = IdentifierMap(pack=pack)
        backend = _CollidingBackend(collision_value="propio")

        translator = LLMTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            backend=backend,
            reserved_word_map=pack.reserved_words,
            identifier_map=ident_map,
        )

        code = "def f():\n    e = 1\n    return e\n"
        # Must not raise ValueError despite the colliding LLM response.
        translated = translator.translate_code(code, source_lang="en", target_lang="es")

        assert isinstance(translated, str)
        # The bare collision value is not a valid stand-in for `e` --
        # the suffix path should have produced something with a numeric
        # tail. We don't pin the exact suffix to leave room for
        # incremental policy changes.
        assert "propio_" in translated, (
            f"Suffix recovery did not fire -- translated code:\n{translated}"
        )

    def test_identifier_map_survives_collision(self) -> None:
        """The IdentifierMap entry for the colliding source identifier
        must be set to the suffixed value, not skipped.
        """
        pack = _mock_pack()
        ident_map = IdentifierMap(pack=pack)
        backend = _CollidingBackend(collision_value="propio")

        translator = LLMTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            backend=backend,
            reserved_word_map=pack.reserved_words,
            identifier_map=ident_map,
        )

        translator.translate_code(
            "def f():\n    e = 1\n    return e\n",
            source_lang="en",
            target_lang="es",
        )

        stored = ident_map.get("e", "es")
        assert stored is not None
        assert stored.startswith("propio_"), (
            f"IdentifierMap should hold the suffixed value, got {stored!r}"
        )

    def test_no_collision_no_suffix(self) -> None:
        """Negative regression: when the LLM does not propose a
        colliding value, no suffix is applied.
        """
        pack = _mock_pack()
        ident_map = IdentifierMap(pack=pack)
        backend = _CollidingBackend(collision_value="error_var")

        translator = LLMTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            backend=backend,
            reserved_word_map=pack.reserved_words,
            identifier_map=ident_map,
        )

        translator.translate_code(
            "def f():\n    e = 1\n    return e\n",
            source_lang="en",
            target_lang="es",
        )

        assert ident_map.get("e", "es") == "error_var"

    def test_pack_aware_map_constructed_when_no_explicit_map(self) -> None:
        """LLMTranslator does not implicitly attach a pack to a
        default-constructed IdentifierMap -- callers wanting collision
        detection must pass IdentifierMap(pack=...) themselves.
        Documenting this contract so a future change doesn't silently
        regress to the no-detection state.
        """
        backend = _CollidingBackend(collision_value="propio")
        translator = LLMTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            backend=backend,
        )
        # Default IdentifierMap has no pack -- collisions silently allowed.
        assert translator.identifier_map.pack is None


class TestSuffixRecoveryStableHash:
    """The hash fallback in ``_suffix_until_clean`` must be stable
    across processes so the IdentifierMap round-trips correctly between
    runs. Copilot review on PR #237 flagged the original
    ``abs(hash(text)) % 10000`` for using Python's process-randomized
    hash and a too-small modular space.
    """

    def _build_translator_forcing_hash_path(
        self,
    ) -> tuple[LLMTranslator, IdentifierMap]:
        """Construct a translator whose pack reserves every numeric
        suffix the loop would try (``_2`` through ``_9``) so
        ``_suffix_until_clean`` must fall through to the
        ``hashlib.sha256`` branch.
        """
        pack = _mock_pack()
        pack.reserved_words = {
            "self": "propio",
            "cls": "clase",
            **{f"_n{i}": f"propio_{i}" for i in range(2, 10)},
        }
        ident_map = IdentifierMap(pack=pack)
        backend = _CollidingBackend(collision_value="propio")
        translator = LLMTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            backend=backend,
            reserved_word_map=pack.reserved_words,
            identifier_map=ident_map,
        )
        return translator, ident_map

    def test_hash_path_produces_deterministic_suffix_within_run(self) -> None:
        """Two passes through ``_suffix_until_clean`` with the same
        source text and base must produce the same hashed candidate.
        Cheap surrogate for cross-process determinism (real test of
        that property would need a subprocess).
        """
        translator, ident_map = self._build_translator_forcing_hash_path()
        first = translator._suffix_until_clean("e", "es", "propio")
        ident_map._map.pop("e", None)  # reset so we can call again
        second = translator._suffix_until_clean("e", "es", "propio")
        assert first == second, (
            f"hash-suffixed candidate must be deterministic per source text; "
            f"got {first!r} then {second!r}"
        )
        # Sanity: the chosen suffix must be a hex string (sha256-derived),
        # not a numeric one (the numeric range was reserved).
        suffix = first.removeprefix("propio_")
        assert len(suffix) >= 16, (
            f"Expected sha256 hex suffix (>=16 chars), got {suffix!r}"
        )
        int(suffix[:16], 16)  # must parse as hex; raises ValueError otherwise

    def test_hash_path_does_not_use_python_builtin_hash(self) -> None:
        """If the implementation regressed to ``hash()``, the suffix
        would change per process. A subprocess check is the most
        rigorous check; we simulate by computing the expected sha256
        suffix and asserting the implementation matches.
        """
        import hashlib

        translator, _ = self._build_translator_forcing_hash_path()
        candidate = translator._suffix_until_clean("e", "es", "propio")

        expected_prefix = hashlib.sha256(b"e").hexdigest()[:16]
        assert candidate.endswith(expected_prefix) or expected_prefix in candidate, (
            f"Suffix must be derived from sha256(text); got {candidate!r}, "
            f"expected something containing {expected_prefix!r}"
        )
