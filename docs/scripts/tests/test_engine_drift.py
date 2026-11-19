import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "libs" / "core"))
from generate_snippets import categorize_tokens, load_packs  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tokens import token_stream  # noqa: E402

legesher_core = pytest.importorskip(
    "legesher_core"
)  # needs tree-sitter until CORE-1555

SOURCE = (
    Path(__file__)
    .resolve()
    .parents[2]
    .joinpath("snippets", "hello-world.py")
    .read_text()
)


@pytest.mark.parametrize("lang", ["es", "ar", "zh"])
def test_replica_matches_engine(lang):
    translator = legesher_core.TokenTranslator.from_language_pack(lang)
    engine_out = translator.translate_code(SOURCE, source_lang="en", target_lang=lang)
    ours = "".join(t for t, _ in categorize_tokens(SOURCE, load_packs("3.12")[lang]))
    assert token_stream(ours) == token_stream(engine_out)
