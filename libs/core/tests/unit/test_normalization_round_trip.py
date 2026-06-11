"""Round-trip tests proving NFKC normalization did not regress exact matching
across real packs (en->xx->en)."""

import pytest

from legesher_core.transformer import TokenTranslator

SAMPLES = [
    "def greet():\n    print('Hello')\n",
    "def calculate(x):\n    if x > 0:\n        return x\n    return 0\n",
    "for i in range(3):\n    print(i)\n",
]


@pytest.mark.parametrize("source", SAMPLES)
def test_round_trip_spanish(source, spanish_keywords, spanish_builtins):
    en_to_es = TokenTranslator(
        keyword_map=spanish_keywords, builtin_map=spanish_builtins
    )
    es_to_en = TokenTranslator(
        keyword_map={v: k for k, v in spanish_keywords.items()},
        builtin_map={v: k for k, v in spanish_builtins.items()},
    )
    translated = en_to_es.translate_code(source, "en", "es")
    back = es_to_en.translate_code(translated, "es", "en")
    assert back == source


@pytest.mark.parametrize("source", SAMPLES)
def test_round_trip_chinese(source, chinese_keywords, chinese_builtins):
    en_to_zh = TokenTranslator(
        keyword_map=chinese_keywords, builtin_map=chinese_builtins
    )
    zh_to_en = TokenTranslator(
        keyword_map={v: k for k, v in chinese_keywords.items()},
        builtin_map={v: k for k, v in chinese_builtins.items()},
    )
    translated = en_to_zh.translate_code(source, "en", "zh")
    back = zh_to_en.translate_code(translated, "zh", "en")
    assert back == source
