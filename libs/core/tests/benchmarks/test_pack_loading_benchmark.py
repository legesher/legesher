"""Pack loading and token translation across every shipped pack.

These were wall-clock assertions in the per-commit integration suite
(``tests/integration/test_migrated_packs.py``), where loading 50 packs had
to finish under 1.0 s; the first Linux rehearsal of ci.yml measured 1.043 s
and went red for a reason that was not a defect. Timing now runs only under
``make bench``; the per-commit guarantees are structural and stay in the
integration suite (every loadable pack loads, the second load is the cached
object, translation runs for every language).
"""

from legesher_core.transformer import TokenTranslator
from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from tests.interpreter_gaps import unloadable_here

PACK_VERSION = "3.13"
LANGUAGES = [code for code in sorted(get_active_language_codes()) if code != "en"]
LOADABLE = [code for code in LANGUAGES if unloadable_here(code, PACK_VERSION) is None]

SAMPLE = """def calculate_tax(income, rate):
    if income > 50000:
        return income * rate
    else:
        return 0

for item in range(10):
    print(item)
"""


def test_loading_every_pack(benchmark, timing_on):
    """Cold loads: the cache is cleared before each round.

    Without that, the measurement would change character the day the
    loadable set fits the loader's 32-slot cache and rounds after the first
    became hits.
    """
    loader = LanguagePackLoader()

    def load_all():
        loader.load.cache_clear()
        for code in LOADABLE:
            loader.load(code, "python", PACK_VERSION)

    benchmark(load_all)


def test_translating_a_file_into_every_language(benchmark, timing_on):
    loader = LanguagePackLoader()
    translators = {}
    for code in LOADABLE:
        pack = loader.load(code, "python", PACK_VERSION)
        translators[code] = TokenTranslator(
            keyword_map={**pack.keywords, **{v: k for k, v in pack.keywords.items()}},
            builtin_map={**pack.builtins, **{v: k for k, v in pack.builtins.items()}},
        )

    def translate_all():
        for code, translator in translators.items():
            translator.translate_code(SAMPLE, "en", code)

    benchmark(translate_all)
