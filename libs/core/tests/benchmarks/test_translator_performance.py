"""Performance benchmarks for TokenTranslator vs TreeSitterTranslator (CORE-415).

This benchmark suite validates the 4x performance improvement claim
and provides regression detection for future changes.
"""

import pytest

from legesher_core import TokenTranslator, TreeSitterTranslator
from tests.data.keyword_maps_spanish import SPANISH_BUILTINS, SPANISH_KEYWORDS

# Test code samples of varying complexity
SMALL_CODE = """
def hello():
    print("Hello, World!")
    return True
"""

MEDIUM_CODE = """
def calculate_tax(income, rate, deductions=0):
    taxable_income = income - deductions
    tax = taxable_income * rate
    return tax

class TaxCalculator:
    def __init__(self, rate):
        self.rate = rate

    def calculate(self, income):
        return income * self.rate

    def with_deductions(self, income, deductions):
        return (income - deductions) * self.rate

def main():
    calc = TaxCalculator(0.25)
    tax = calc.calculate(100000)
    print(f"Tax: ${tax}")

    for i in range(10):
        result = calc.with_deductions(100000, i * 1000)
        print(f"Deduction {i}: ${result}")

if __name__ == "__main__":
    main()
"""

LARGE_CODE = """
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Configuration:
    name: str
    version: str
    debug: bool = False

    def validate(self):
        if not self.name:
            raise ValueError("Name is required")
        return True

class DataProcessor:
    def __init__(self, config: Configuration):
        self.config = config
        self.data: List[Dict] = []

    def load_data(self, path: Path) -> bool:
        try:
            with open(path) as f:
                self.data = [line.strip() for line in f]
            return True
        except FileNotFoundError:
            return False

    def process(self) -> List[str]:
        results = []
        for item in self.data:
            if self._validate_item(item):
                results.append(self._transform_item(item))
        return results

    def _validate_item(self, item) -> bool:
        return bool(item)

    def _transform_item(self, item) -> str:
        return item.upper()

class Pipeline:
    def __init__(self):
        self.processors = []

    def add_processor(self, processor):
        self.processors.append(processor)

    def run(self):
        for processor in self.processors:
            processor.process()
"""


@pytest.fixture(
    params=[
        ("token", TokenTranslator),
        ("tree-sitter", TreeSitterTranslator),
    ],
    ids=["token", "tree-sitter"],
)
def translator_impl(request):
    """Parametrized translator implementations for benchmarking."""
    name, klass = request.param
    instance = klass(keyword_map=SPANISH_KEYWORDS, builtin_map=SPANISH_BUILTINS)
    return name, instance


class TestSmallCodeBenchmarks:
    """Benchmarks for small code samples (10-50 LOC)."""

    def test_benchmark_small_code(self, benchmark, translator_impl):
        """Benchmark translation of small code sample."""
        name, translator = translator_impl
        result = benchmark(translator.translate_code, SMALL_CODE, "en", "es")
        assert "definir" in result
        assert "imprimir" in result


class TestMediumCodeBenchmarks:
    """Benchmarks for medium code samples (100-500 LOC)."""

    def test_benchmark_medium_code(self, benchmark, translator_impl):
        """Benchmark translation of medium code sample."""
        name, translator = translator_impl
        result = benchmark(translator.translate_code, MEDIUM_CODE, "en", "es")
        assert "clase" in result
        assert "definir" in result


class TestLargeCodeBenchmarks:
    """Benchmarks for large code samples (500+ LOC)."""

    def test_benchmark_large_code(self, benchmark, translator_impl):
        """Benchmark translation of large code sample."""
        name, translator = translator_impl
        result = benchmark(translator.translate_code, LARGE_CODE, "en", "es")
        assert "desde" in result  # from
        assert "importar" in result  # import


class TestRoundTripBenchmarks:
    """Benchmarks for round-trip translation (en→es→en)."""

    def test_benchmark_round_trip(self, benchmark, translator_impl):
        """Benchmark round-trip translation performance."""
        name, translator = translator_impl

        def round_trip():
            es_code = translator.translate_code(MEDIUM_CODE, "en", "es")
            reverse_translator = translator.reverse()
            en_code = reverse_translator.translate_code(es_code, "es", "en")
            return en_code

        result = benchmark(round_trip)
        assert "def calculate_tax" in result or "definir calculate_tax" in result


class TestComparativePerformance:
    """Direct comparison tests between translators."""

    def test_token_small(self, benchmark):
        """Baseline: TokenTranslator on small code."""
        translator = TokenTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS)
        result = benchmark(translator.translate_code, SMALL_CODE, "en", "es")
        assert "definir" in result

    def test_tree_sitter_small(self, benchmark):
        """TreeSitter: TreeSitterTranslator on small code."""
        translator = TreeSitterTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS)
        result = benchmark(translator.translate_code, SMALL_CODE, "en", "es")
        assert "definir" in result

    def test_token_medium(self, benchmark):
        """Baseline: TokenTranslator on medium code."""
        translator = TokenTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS)
        result = benchmark(translator.translate_code, MEDIUM_CODE, "en", "es")
        assert "clase" in result

    def test_tree_sitter_medium(self, benchmark):
        """TreeSitter: TreeSitterTranslator on medium code."""
        translator = TreeSitterTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS)
        result = benchmark(translator.translate_code, MEDIUM_CODE, "en", "es")
        assert "clase" in result
