"""Direct unit tests for LocalEngine — the branches the MCP layer can't reach.

The rest of the suite drives the server through an MCP client session on
purpose. That leaves three kinds of behavior unexercised, and this module
covers exactly those (CORE-1815, CORE-1806):

- ``compile_check``'s defensive ``(ValueError, RecursionError, MemoryError)``
  branch, which CPython no longer reaches on its own — null bytes became a
  SyntaxError — so it is provoked directly.
- The sanitization seams, reachable only by making the loader or the engine
  fail; every active language has a pack, so nothing fails naturally.
- The caches: the ``(source, target, version)`` translator cache and the
  process-wide singleton, under real threads.
"""

from __future__ import annotations

import builtins
import threading
from typing import Any

import pytest
from legesher_core.exceptions import TranslationError
from legesher_i18n.exceptions import LanguagePackError
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.term_definitions import YAML_SECTION_CATEGORIES

from legesher_mcp import engine as engine_module
from legesher_mcp.engine import CATEGORIES, EngineError, LocalEngine, get_engine

#: A message shaped like the ones the loader really raises: absolute path,
#: pack filename, and a traceback fragment. None of it may escape.
LEAKY_MESSAGE = (
    "Failed to load /Users/someone/legesher/libs/i18n/language-packs/"
    "python/es/packs/3.13.yml\nTraceback (most recent call last):\n  ..."
)


@pytest.fixture
def local_engine() -> LocalEngine:
    """A private engine — never the process singleton other tests warm."""
    return LocalEngine()


# -- compile_check defensive branches -------------------------------------


@pytest.mark.parametrize("failure", [ValueError, RecursionError, MemoryError])
def test_compile_check_treats_hard_failures_as_invalid_source(
    monkeypatch: pytest.MonkeyPatch, failure: type[Exception]
) -> None:
    """A compiler blow-up is a validation verdict, never a server crash."""

    def explode(*args: object, **kwargs: object) -> None:
        raise failure("boom")

    monkeypatch.setattr(builtins, "compile", explode)
    outcome = LocalEngine.compile_check("x = 1\n")
    assert outcome.valid is False
    assert outcome.issue is not None
    assert outcome.issue.message == "Source could not be compiled."
    # No line/offset to report — the compiler never got far enough.
    assert outcome.issue.line is None
    assert outcome.issue.offset is None


def test_compile_check_defensive_branch_leaks_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The generic message must not carry the underlying exception text."""

    def explode(*args: object, **kwargs: object) -> None:
        raise ValueError(LEAKY_MESSAGE)

    monkeypatch.setattr(builtins, "compile", explode)
    outcome = LocalEngine.compile_check("x = 1\n")
    assert outcome.issue is not None
    assert "/Users/" not in outcome.issue.message
    assert "Traceback" not in outcome.issue.message


def test_compile_check_reports_syntax_location() -> None:
    outcome = LocalEngine.compile_check("def broken(:\n    pass\n")
    assert outcome.valid is False
    assert outcome.issue is not None
    assert outcome.issue.line == 1


def test_compile_check_never_names_a_real_file() -> None:
    """Diagnostics carry a placeholder filename, not a path from the caller."""
    outcome = LocalEngine.compile_check("def broken(:\n")
    assert outcome.issue is not None
    assert "/" not in (outcome.issue.message or "")


def test_compile_check_accepts_valid_source() -> None:
    assert LocalEngine.compile_check("x = 1\n").valid is True


def test_compile_check_does_not_execute_the_source(tmp_path: Any) -> None:
    """Validation is compile-only: side effects in the source never run."""
    marker = tmp_path / "should-not-exist"
    source = f"import pathlib\npathlib.Path({str(marker)!r}).write_text('ran')\n"
    assert LocalEngine.compile_check(source).valid is True
    assert not marker.exists()


# -- language gate ---------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        "",
        "e",
        "toolongcode",
        "EN",
        "es_MX",
        "../etc/passwd",
        "es/../../secret",
        "zz",  # well-formed but not in the registry
        "es\x00",
    ],
)
def test_language_gate_rejects(local_engine: LocalEngine, code: str) -> None:
    with pytest.raises(EngineError) as excinfo:
        local_engine.ensure_known_language(code)
    assert excinfo.value.code == "unsupported_language"


def test_language_gate_truncates_the_echoed_code(local_engine: LocalEngine) -> None:
    """A hostile code is echoed back bounded, so it cannot be a payload."""
    with pytest.raises(EngineError) as excinfo:
        local_engine.ensure_known_language("x" * 5000)
    assert len(str(excinfo.value)) < 200


@pytest.mark.parametrize("code", ["en", "es", "ar"])
def test_language_gate_accepts_registered_codes(local_engine: LocalEngine, code: str) -> None:
    local_engine.ensure_known_language(code)


def test_load_pack_gates_the_language_before_touching_disk(
    local_engine: LocalEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The allowlist runs first — a crafted code never reaches the loader."""

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("loader was reached for an unregistered language")

    monkeypatch.setattr(local_engine._loader, "load", fail)
    with pytest.raises(EngineError) as excinfo:
        local_engine.load_pack("../../etc", "3.13")
    assert excinfo.value.code == "unsupported_language"


# -- sanitization seams ----------------------------------------------------


def test_load_pack_sanitizes_loader_failures(
    local_engine: LocalEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def raise_pack_error(*args: object, **kwargs: object) -> None:
        raise LanguagePackError(LEAKY_MESSAGE)

    monkeypatch.setattr(local_engine._loader, "load", raise_pack_error)
    with pytest.raises(EngineError) as excinfo:
        local_engine.load_pack("es", "3.13")
    assert excinfo.value.code == "language_pack_not_found"
    message = str(excinfo.value)
    assert "/Users/" not in message
    assert ".yml" not in message
    assert "Traceback" not in message
    assert "es" in message and "3.13" in message


@pytest.mark.parametrize("failure", [LanguagePackError, TranslationError])
def test_build_translator_sanitizes_failures(
    monkeypatch: pytest.MonkeyPatch, failure: type[Exception]
) -> None:
    def raise_failure(*args: object, **kwargs: object) -> None:
        raise failure(LEAKY_MESSAGE)

    monkeypatch.setattr(engine_module, "create_translator_from_language_pack", raise_failure)
    with pytest.raises(EngineError) as excinfo:
        LocalEngine._build_translator("en", "es", "3.13")
    assert excinfo.value.code == "language_pack_not_found"
    message = str(excinfo.value)
    assert "/Users/" not in message
    assert "Traceback" not in message


def test_run_sanitizes_engine_translation_failures() -> None:
    class Exploding:
        def translate_code(self, *args: object, **kwargs: object) -> str:
            raise TranslationError(LEAKY_MESSAGE)

    with pytest.raises(EngineError) as excinfo:
        LocalEngine._run(Exploding(), "x = 1", "en", "es")
    assert excinfo.value.code == "invalid_source"
    assert str(excinfo.value) == "Source could not be tokenized as Python code."


def test_run_rejects_a_non_string_engine_result() -> None:
    """Contract guard: anything but str (or (str, meta)) is a failure."""

    class WrongType:
        def translate_code(self, *args: object, **kwargs: object) -> object:
            return {"unexpected": "shape"}

    with pytest.raises(EngineError) as excinfo:
        LocalEngine._run(WrongType(), "x = 1", "en", "es")
    assert excinfo.value.code == "invalid_source"


def test_run_unwraps_the_code_metadata_tuple() -> None:
    class TupleReturning:
        def translate_code(self, *args: object, **kwargs: object) -> tuple[str, dict[str, str]]:
            return ("translated", {"meta": "ignored"})

    assert LocalEngine._run(TupleReturning(), "x = 1", "en", "es") == "translated"


def test_translate_gates_both_languages(local_engine: LocalEngine) -> None:
    with pytest.raises(EngineError) as excinfo:
        local_engine.translate(
            source="x = 1", source_lang="en", target_lang="zz", python_version="3.13"
        )
    assert excinfo.value.code == "unsupported_language"


def test_translate_is_a_no_op_for_identical_languages(local_engine: LocalEngine) -> None:
    outcome = local_engine.translate(
        source="x = 1", source_lang="es", target_lang="es", python_version="3.13"
    )
    assert outcome.translated_source == "x = 1"
    assert outcome.pivoted is False


def test_scan_constructs_reports_untokenizable_source_as_a_result(
    local_engine: LocalEngine,
) -> None:
    """A lexer failure is data (tokenized=False), not an exception."""
    scan = local_engine.scan_constructs("def broken(\n", "3.13")
    assert scan.tokenized is False
    assert scan.ordered == []
    assert scan.counts == {}


# -- translator cache ------------------------------------------------------


def test_translator_cache_reuses_one_instance_per_triple(
    local_engine: LocalEngine,
) -> None:
    first = local_engine._translator_for("en", "es", "3.13")
    second = local_engine._translator_for("en", "es", "3.13")
    assert first is second


@pytest.mark.parametrize(
    "triple",
    [("en", "ar", "3.13"), ("en", "es", "3.12"), ("es", "en", "3.13")],
)
def test_translator_cache_keys_on_all_three_components(
    local_engine: LocalEngine, triple: tuple[str, str, str]
) -> None:
    """Changing any component of the key must yield a different translator."""
    baseline = local_engine._translator_for("en", "es", "3.13")
    assert local_engine._translator_for(*triple) is not baseline


def _build_counter(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[tuple[str, str, str], int], threading.Lock]:
    """Count translator builds per triple, slowly enough to expose races."""
    counts: dict[tuple[str, str, str], int] = {}
    counts_lock = threading.Lock()
    original = LocalEngine._build_translator

    def counting(source_lang: str, target_lang: str, python_version: str) -> Any:
        with counts_lock:
            key = (source_lang, target_lang, python_version)
            counts[key] = counts.get(key, 0) + 1
        # Widen the window a real race would need to be observed.
        threading.Event().wait(0.01)
        return original(source_lang, target_lang, python_version)

    monkeypatch.setattr(LocalEngine, "_build_translator", staticmethod(counting))
    return counts, counts_lock


def test_concurrent_identical_requests_build_one_translator(
    local_engine: LocalEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """32 threads racing on one triple must not build 32 translators."""
    counts, _ = _build_counter(monkeypatch)
    results: list[Any] = []
    results_lock = threading.Lock()
    start = threading.Barrier(32)

    def worker() -> None:
        start.wait()
        translator = local_engine._translator_for("en", "es", "3.13")
        with results_lock:
            results.append(translator)

    threads = [threading.Thread(target=worker) for _ in range(32)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert counts == {("en", "es", "3.13"): 1}
    assert len(results) == 32
    assert all(translator is results[0] for translator in results)


def test_concurrent_distinct_requests_build_one_translator_each(
    local_engine: LocalEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Distinct triples each get exactly one build, and none are cross-wired."""
    counts, _ = _build_counter(monkeypatch)
    triples = [
        ("en", "es", "3.13"),
        ("en", "ar", "3.13"),
        ("es", "en", "3.13"),
        ("en", "es", "3.12"),
    ]
    repeats = 6
    observed: dict[tuple[str, str, str], list[Any]] = {triple: [] for triple in triples}
    observed_lock = threading.Lock()
    start = threading.Barrier(len(triples) * repeats)

    def worker(triple: tuple[str, str, str]) -> None:
        start.wait()
        translator = local_engine._translator_for(*triple)
        with observed_lock:
            observed[triple].append(translator)

    threads = [
        threading.Thread(target=worker, args=(triple,))
        for triple in triples
        for _ in range(repeats)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert counts == dict.fromkeys(triples, 1)
    for triple, instances in observed.items():
        assert len(instances) == repeats
        assert all(instance is instances[0] for instance in instances), triple
    # One cache entry per triple, and no two triples share an instance.
    identities = {triple: id(instances[0]) for triple, instances in observed.items()}
    assert len(set(identities.values())) == len(triples)


def test_concurrent_translate_calls_agree(local_engine: LocalEngine) -> None:
    """End-to-end: parallel translate() calls return identical output."""
    source = "def greet(name):\n    print(name)\n"
    results: list[str] = []
    errors: list[BaseException] = []
    results_lock = threading.Lock()
    start = threading.Barrier(16)

    def worker(index: int) -> None:
        target = ("es", "ar", "fr", "de")[index % 4]
        start.wait()
        try:
            outcome = local_engine.translate(
                source=source, source_lang="en", target_lang=target, python_version="3.13"
            )
        except BaseException as exc:  # noqa: BLE001 — recorded, then re-raised below
            with results_lock:
                errors.append(exc)
            return
        with results_lock:
            results.append(f"{target}:{outcome.translated_source}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert len(results) == 16
    # Four distinct targets, each producing one consistent answer.
    assert len(set(results)) == 4


# -- process singleton -----------------------------------------------------


def test_get_engine_returns_the_same_instance() -> None:
    assert get_engine() is get_engine()


def test_get_engine_is_singular_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """The double-checked lock must not hand out two engines under a race."""
    monkeypatch.setattr(engine_module, "_engine", None)
    constructed = []
    constructed_lock = threading.Lock()
    original_init = LocalEngine.__init__

    def slow_init(self: LocalEngine, *args: Any, **kwargs: Any) -> None:
        # Sleep INSIDE construction: without the lock, other threads would
        # sail past the None check and build their own engine here.
        threading.Event().wait(0.02)
        original_init(self, *args, **kwargs)
        with constructed_lock:
            constructed.append(self)

    monkeypatch.setattr(LocalEngine, "__init__", slow_init)

    engines: list[LocalEngine] = []
    engines_lock = threading.Lock()
    start = threading.Barrier(24)

    def worker() -> None:
        start.wait()
        instance = get_engine()
        with engines_lock:
            engines.append(instance)

    threads = [threading.Thread(target=worker) for _ in range(24)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(constructed) == 1, f"{len(constructed)} engines built, expected 1"
    assert len(engines) == 24
    assert all(instance is engines[0] for instance in engines)


# -- pack discovery: TTL and explicit invalidation -------------------------


def test_pack_discovery_is_cached_within_the_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = LocalEngine(pack_discovery_ttl=3600.0)
    calls = {"count": 0}
    real = LanguagePackLoader.list_available_languages

    def counting(self: LanguagePackLoader, target: str = "python") -> list[tuple[str, str]]:
        calls["count"] += 1
        return real(self, target)

    monkeypatch.setattr(LanguagePackLoader, "list_available_languages", counting)
    first = engine._discover_pack_codes()
    second = engine._discover_pack_codes()
    assert calls["count"] == 1
    assert first == second


def test_pack_discovery_rescans_after_the_ttl_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pack installed mid-process shows up without restarting the server."""
    engine = LocalEngine(pack_discovery_ttl=0.0)
    scans = {"count": 0}

    def fake_list(self: LanguagePackLoader, target: str = "python") -> list[tuple[str, str]]:
        scans["count"] += 1
        if scans["count"] == 1:
            return [("es", "Spanish")]
        return [("es", "Spanish"), ("ar", "Arabic")]

    monkeypatch.setattr(LanguagePackLoader, "list_available_languages", fake_list)
    assert engine._discover_pack_codes() == frozenset({"es"})
    assert engine._discover_pack_codes() == frozenset({"es", "ar"})
    assert scans["count"] == 2


def test_pack_discovery_ttl_drops_the_loaders_own_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rescanning is pointless unless the loader re-walks the filesystem too."""
    engine = LocalEngine(pack_discovery_ttl=0.0)
    refreshes = {"count": 0}
    original = LanguagePackLoader.refresh_discovery

    def counting(self: LanguagePackLoader) -> None:
        refreshes["count"] += 1
        original(self)

    monkeypatch.setattr(LanguagePackLoader, "refresh_discovery", counting)
    engine._discover_pack_codes()
    engine._discover_pack_codes()
    assert refreshes["count"] == 2


def test_refresh_packs_invalidates_every_pack_derived_cache() -> None:
    """The explicit hook drops availability, loaded packs, and translators."""
    engine = LocalEngine(pack_discovery_ttl=3600.0)
    engine._discover_pack_codes()
    translator = engine._translator_for("en", "es", "3.13")
    assert engine._pack_codes is not None
    assert engine._translators

    engine.refresh_packs()

    assert engine._pack_codes is None
    assert engine._translators == {}
    # A rebuilt translator is a genuinely new object, not the dropped one.
    assert engine._translator_for("en", "es", "3.13") is not translator


def test_list_languages_reflects_a_refreshed_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pack_available flips once discovery is redone, not only at boot."""
    engine = LocalEngine(pack_discovery_ttl=0.0)
    visible = {"codes": [("es", "Spanish")]}

    monkeypatch.setattr(
        LanguagePackLoader,
        "list_available_languages",
        lambda self, target="python": list(visible["codes"]),
    )
    before = {info.code: info.pack_available for info in engine.list_languages()}
    assert before["es"] is True
    assert before["ar"] is False

    visible["codes"] = [("es", "Spanish"), ("ar", "Arabic")]
    after = {info.code: info.pack_available for info in engine.list_languages()}
    assert after["ar"] is True


def test_refresh_packs_is_safe_under_concurrency() -> None:
    """Refreshing while translations are in flight must not corrupt state."""
    engine = LocalEngine(pack_discovery_ttl=0.0)
    errors: list[BaseException] = []
    errors_lock = threading.Lock()
    stop = threading.Event()

    def translator_worker() -> None:
        try:
            while not stop.is_set():
                engine._translator_for("en", "es", "3.13")
                engine._discover_pack_codes()
        except BaseException as exc:  # noqa: BLE001 — surfaced via `errors`
            with errors_lock:
                errors.append(exc)

    def refresh_worker() -> None:
        try:
            for _ in range(20):
                engine.refresh_packs()
                threading.Event().wait(0.005)
        except BaseException as exc:  # noqa: BLE001 — surfaced via `errors`
            with errors_lock:
                errors.append(exc)

    workers = [threading.Thread(target=translator_worker) for _ in range(4)]
    refresher = threading.Thread(target=refresh_worker)
    for worker in workers:
        worker.start()
    refresher.start()
    refresher.join()
    stop.set()
    for worker in workers:
        worker.join()

    assert not errors, errors


# -- category vocabulary ----------------------------------------------------


def test_categories_matches_the_canonical_section_vocabulary() -> None:
    """CATEGORIES covers exactly the pack's own section names.

    Set equality on purpose, against a literal on purpose: CATEGORIES
    stays a hand-written tuple because its ORDER is a contract (lookup
    precedence — ``keywords`` wins over ``implicit_params`` on conflict),
    while ``YAML_SECTION_CATEGORIES``'s ordering is an accident of how the
    dict was authored. Deriving one from the other would launder that
    accident into a contract; this pins membership and nothing more.
    """
    assert set(CATEGORIES) == set(YAML_SECTION_CATEGORIES)
