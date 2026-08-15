"""Baseline performance benchmarks for CORE-446.

This records "before" metrics to validate cache performance improvements.

Run with: uv run pytest tests/benchmarks/test_baseline_performance.py -v -s
"""

import time
from pathlib import Path

import pytest


def test_baseline_keyword_translation_lookup():
    """Baseline: keyword_docs.get_keyword_translation() performance."""
    from legesher_language_server.utils.keyword_docs import KeywordDocumentation

    docs = KeywordDocumentation()

    # Test repeated lookups (simulates completion requests)
    keywords_to_test = ["def", "class", "if", "for", "while", "return", "import"]
    languages = ["es", "ar", "zh"]
    iterations = 10

    start = time.perf_counter()
    for _ in range(iterations):
        for lang in languages:
            for keyword in keywords_to_test:
                docs.get_keyword_translation(keyword, lang)
    elapsed_ms = (time.perf_counter() - start) * 1000

    avg_per_lookup = elapsed_ms / (iterations * len(languages) * len(keywords_to_test))

    print(f"\n{'=' * 60}")
    print("BASELINE: keyword_docs.get_keyword_translation()")
    print(f"{'=' * 60}")
    print(f"Total time: {elapsed_ms:.2f}ms")
    print(f"Lookups: {iterations * len(languages) * len(keywords_to_test)}")
    print(f"Avg per lookup: {avg_per_lookup:.2f}ms")
    print(f"Languages tested: {', '.join(languages)}")
    print(f"{'=' * 60}\n")

    # Record baseline - no assertion, just measurement
    assert avg_per_lookup > 0  # Sanity check


def test_baseline_enhanced_intelligence_keyword_map_load():
    """Baseline: EnhancedIntelligenceProxy._get_keyword_map() performance."""
    from legesher_language_server.config import LanguageServerConfig
    from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy

    config = LanguageServerConfig(source_language="es", target_language="en")

    # Measure initialization time (loads keyword map)
    start = time.perf_counter()
    proxy = EnhancedIntelligenceProxy(config)
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"\n{'=' * 60}")
    print("BASELINE: EnhancedIntelligenceProxy initialization (keyword map load)")
    print(f"{'=' * 60}")
    print(f"Initialization time: {elapsed_ms:.2f}ms")
    print(f"Language: {config.source_language}")
    print(f"{'=' * 60}\n")

    assert elapsed_ms > 0  # Sanity check
    assert proxy is not None


def test_baseline_language_pack_file_size():
    """Baseline: Measure language pack file sizes for cache memory estimation."""
    import os

    # Find pack directory by walking up from current file (more robust than hard-coded index)
    current = Path(__file__).parent
    pack_dir = None

    # Walk up to find the monorepo root (contains libs/ and i18n/)
    for _ in range(10):  # Limit depth to prevent infinite loop
        potential_pack_dir = current / "libs" / "i18n" / "language-packs" / "python"
        if potential_pack_dir.exists():
            pack_dir = potential_pack_dir
            break
        # Also check if we're inside libs already
        potential_pack_dir = current.parent / "i18n" / "language-packs" / "python"
        if potential_pack_dir.exists():
            pack_dir = potential_pack_dir
            break
        current = current.parent

    if not pack_dir or not pack_dir.exists():
        pytest.skip("Language pack directory not found")

    total_size = 0
    file_count = 0
    language_dirs = []

    for lang_dir in pack_dir.iterdir():
        if lang_dir.is_dir() and not lang_dir.name.startswith("."):
            language_dirs.append(lang_dir.name)
            packs_dir = lang_dir / f"legesher_i18n_python_{lang_dir.name}" / "packs"
            if packs_dir.exists():
                for yml_file in packs_dir.glob("*.yml"):
                    size = os.path.getsize(yml_file)
                    total_size += size
                    file_count += 1

    print(f"\n{'=' * 60}")
    print("BASELINE: Language pack file sizes")
    print(f"{'=' * 60}")
    print(f"Total files: {file_count}")
    print(f"Total size on disk: {total_size / 1024:.2f} KB ({total_size / 1024 / 1024:.2f} MB)")
    print(f"Avg per file: {total_size / file_count / 1024:.2f} KB" if file_count > 0 else "N/A")
    print(f"Languages: {len(language_dirs)}")
    print(f"Estimated in-memory (parsed): ~{total_size * 10 / 1024 / 1024:.2f} MB")
    print(f"{'=' * 60}\n")

    assert file_count > 0, "No language pack files found"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
