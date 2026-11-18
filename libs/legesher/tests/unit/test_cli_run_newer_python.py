"""`legesher run` survives a Python newer than every tier the packs have.

On Python 3.15 every pack lookup asked for ``packs/3.15.yml``, which no pack
ships, so the run failed in every language. The loader now serves a pack's
newest tier to a newer interpreter
(``libs/i18n/tests/test_newest_tier_fallback.py``); these tests hold the
surfaces of ``legesher run`` to it.

"Newer" is derived from the packs (their newest tier plus one minor), so both
groups exercise the 3.15 path on any interpreter:

* In process, the engine is told the running interpreter is that newer
  version, and the import hook and the error handler must still install with
  the newest tier's words.
* In a subprocess, the project's config names that newer version. The
  localized traceback takes its tier from the config, so its lookup goes
  through the rule. The import hook and the script itself take the running
  interpreter's tier, whatever the config names.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tokenize
import unicodedata
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from legesher.runtime import error_handler, import_hook
from legesher_core import TokenTranslator
from legesher_core import transformer as transformer_module
from legesher_i18n import LanguagePackLoader
from legesher_i18n.schema_validator import SchemaValidator

TIERS = LanguagePackLoader().list_available_versions("python")
NEWEST = TIERS[-1]
_major, _minor = (int(part) for part in NEWEST.split("."))
#: One minor release past every shipped tier (3.15 while the packs end at 3.14).
NEWER = f"{_major}.{_minor + 1}"

#: Identifiers that are not Latin: vocalised Arabic, pointed Hebrew, Devanagari
#: with virama and matras, Sinhala with a ZWJ conjunct. (function, parameter, text)
IDENTIFIERS = {
    "ar": ("رَحِّبْ", "اِسْمٌ", "مَرْحَبًا"),
    "he": ("בָּרֵךְ", "שֵׁם", "שָׁלוֹם"),
    "hi": ("अभिवादन", "नाम", "नमस्ते"),
    "si": ("ප්‍රකාශය", "නම", "ආයුබෝවන්"),
}


# -- the hooks on a Python newer than the packs, in process -------------------


class _NewerInterpreter:
    """``sys`` as the engine would see it on a Python one minor past the packs."""

    version_info = SimpleNamespace(major=_major, minor=_minor + 1)

    def __getattr__(self, name: str) -> object:
        return getattr(sys, name)


@pytest.fixture
def newer_interpreter(monkeypatch):
    """The engine picks the pack tier as if it ran on ``NEWER``.

    Each test asserts the translator it got reports ``NEWER``, so a change in
    where the engine reads the interpreter's version fails here, by name.
    """
    monkeypatch.setattr(transformer_module, "sys", _NewerInterpreter())


def _maps(translator: TokenTranslator) -> tuple[dict[str, str], dict[str, str]]:
    return translator.mapper.keyword_map, translator.mapper.builtin_map


UNICODE_VERSION = tuple(int(part) for part in unicodedata.unidata_version.split("."))


def _xfail_where_the_newest_tier_cannot_load(request, lang: str) -> None:
    """Mark the case strict xfail where this interpreter rejects the newest tier.

    The schema validator checks every rendering with the running interpreter's
    ``str.isidentifier()``. Before Unicode 15.1 (CPython 3.10 to 3.12) that
    rejects ZWJ, ZWNJ and the katakana middle dot, so a pack whose later tiers
    spell words with them does not load at those tiers at all (core's gap 2,
    CORE-1521). Decided from the pack's own files, not a list of languages.
    """
    if UNICODE_VERSION >= (15, 1):
        return
    xid_313 = SchemaValidator._XID_ONLY_FROM_CPYTHON_313
    packs = LanguagePackLoader()._discover_packs()[f"python-{lang}"] / "packs"
    for tier in TIERS:
        data = yaml.safe_load((packs / f"{tier}.yml").read_text(encoding="utf-8"))
        for section, entries in data.items():
            if not isinstance(entries, dict):
                continue
            for key, value in entries.items():
                if isinstance(value, str) and any(ch in xid_313 for ch in value):
                    request.applymarker(
                        pytest.mark.xfail(
                            strict=True,
                            reason=(
                                f"CORE-1521: {lang} {tier}.yml {section}.{key} needs "
                                "Unicode 15.1 identifier rules (CPython 3.13+); this "
                                f"interpreter has {unicodedata.unidata_version}"
                            ),
                        )
                    )
                    return


@pytest.mark.parametrize("lang", sorted(IDENTIFIERS))
class TestTheHooksInstallOnANewerPython:
    """Each hook gets the pack's newest tier, whole.

    Compared with a translator built at ``NEWEST`` by name. Every pack's later
    tiers add terms the earlier ones lack, so an older tier served by mistake
    is a different map, not an equal one.
    """

    def test_the_import_hook_is_served_the_newest_tier(
        self, lang, newer_interpreter, request
    ):
        _xfail_where_the_newest_tier_cannot_load(request, lang)
        expected = TokenTranslator.from_language_pack(lang, NEWEST)
        finder = import_hook.install_import_hook(lang)
        try:
            assert finder.translator.python_version == NEWER
            assert _maps(finder.translator) == _maps(expected)
        finally:
            import_hook.uninstall_import_hook()

    def test_the_error_handler_is_served_the_newest_tier(
        self, lang, newer_interpreter, monkeypatch, request
    ):
        _xfail_where_the_newest_tier_cannot_load(request, lang)
        monkeypatch.setattr(sys, "excepthook", sys.excepthook)
        expected = TokenTranslator.from_language_pack(lang, NEWEST)
        handler = error_handler.install_error_handler(lang)
        assert handler.translator.python_version == NEWER
        assert _maps(handler.translator) == _maps(expected)


@pytest.mark.parametrize("lang", sorted(IDENTIFIERS))
def test_a_later_tier_is_a_different_map(lang, request):
    """The premise of the class above, checked against the packs."""
    _xfail_where_the_newest_tier_cannot_load(request, lang)
    oldest = TokenTranslator.from_language_pack(lang, TIERS[0])
    newest = TokenTranslator.from_language_pack(lang, NEWEST)
    assert _maps(oldest) != _maps(newest)


# -- the CLI on a Python newer than the packs, end to end ---------------------

ENGLISH = (
    'def {fn}({param}):\n    return {param}\n\nprint({fn}("{text}"))\nprint(1 / 0)\n'
)

#: The console script's body (see test_cli_run.py for why not ``-m``).
CLI = "from legesher.cli.main import cli; cli()"


def _error_tokens(source: str) -> Counter[str]:
    try:
        return Counter(
            token.string
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.ERRORTOKEN
        )
    except tokenize.TokenError:
        return Counter()


def _xfail_on_interpreter_gaps(request, english: str, lang: str) -> None:
    """Mark the case strict xfail where an older interpreter cannot run it.

    The same two gaps ``libs/core/tests/interpreter_gaps.py`` records, decided
    from the data rather than a list of languages:

    * Unicode before 15.1 (CPython 3.10 to 3.12) rejects ZWJ in an identifier,
      so the Sinhala conjunct is a ``SyntaxError`` and the si 3.13+ tiers do not
      load (core's gap 2, CORE-1521).
    * The pure-Python tokenizer (CPython 3.10 and 3.11) splits a pack rendering
      that carries a combining mark into ERRORTOKEN fragments, so the return
      hop never matches it (core's gap 1, CORE-2192).
    """
    xid_313 = SchemaValidator._XID_ONLY_FROM_CPYTHON_313
    if UNICODE_VERSION < (15, 1) and any(ch in xid_313 for ch in english):
        reason = (
            "CORE-1521: needs Unicode 15.1 identifier rules (CPython 3.13+); "
            f"this interpreter has {unicodedata.unidata_version}"
        )
    elif sys.version_info < (3, 12):
        native = TokenTranslator.from_language_pack(lang).translate_code(english)
        fragments = _error_tokens(native) - _error_tokens(english)
        if not fragments:
            return
        reason = (
            "CORE-2192: the pure-Python tokenizer splits a rendering with a "
            "combining mark, so the return hop never matches it"
        )
    else:
        return
    request.applymarker(pytest.mark.xfail(strict=True, reason=reason))


@pytest.mark.parametrize("lang", sorted(IDENTIFIERS))
def test_run_on_a_python_newer_than_the_packs(tmp_path: Path, lang: str, request):
    fn, param, text = IDENTIFIERS[lang]
    english = ENGLISH.format(fn=fn, param=param, text=text)
    _xfail_on_interpreter_gaps(request, english, lang)

    newest = LanguagePackLoader().load(lang, "python", NEWEST)
    # Written in the words of the tier `run` reads the script with: the running
    # interpreter's (on a Python newer than the packs, the newest tier).
    native = TokenTranslator.from_language_pack(lang).translate_code(english)
    assert native != english  # the script is really written in the pack's words

    project = tmp_path / "project"
    (project / ".legesher").mkdir(parents=True)
    (project / ".legesher" / "config.yml").write_text(
        f"language: {lang}\npython_version: '{NEWER}'\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    script = project / "programa.py"
    script.write_text(native, encoding="utf-8")

    home = tmp_path / "home"
    home.mkdir()
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "HOME": str(home),
        "USERPROFILE": str(home),
    }
    result = subprocess.run(
        [sys.executable, "-c", CLI, "run", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=project,
        env=env,
        check=False,
    )

    # The function ran and its native identifiers survived byte for byte.
    assert result.stdout == f"{text}\n", result.stderr
    # The error is the script's, and the localized traceback, which asked for
    # the configured (newer) version, found the pack: the exception's name is
    # the newest tier's word for it.
    assert result.returncode == 1, result.stderr
    word = newest.exceptions["zerodivisionerror"]
    assert word in result.stderr, result.stderr
    assert "PackNotFoundError" not in result.stderr


# -- a config that names an older version than the interpreter ----------------

#: True and False are among the words a pack may spell differently from one
#: tier to the next (Sinhala does, from its 3.13 tier on).
TRUTH = '{fn} = True\nif {fn} and not False:\n    print("{text}")\n'


@pytest.mark.parametrize("lang", sorted(IDENTIFIERS))
def test_translate_then_run_under_a_config_that_names_the_oldest_tier(
    tmp_path: Path, lang: str, request
):
    """What `translate` writes, `run` reads, whatever version the config names.

    `legesher init` records the floor of the project's ``requires-python`` as
    ``python_version``, so a config naming a version older than the running
    interpreter is the usual one. `translate` writes with the interpreter's
    tier; `run` has to read the script with the same tier.
    """
    fn, _, text = IDENTIFIERS[lang]
    english = TRUTH.format(fn=fn, text=text)
    _xfail_on_interpreter_gaps(request, english, lang)

    project = tmp_path / "project"
    (project / ".legesher").mkdir(parents=True)
    (project / ".legesher" / "config.yml").write_text(
        f"language: {lang}\npython_version: '{TIERS[0]}'\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    (project / "source.py").write_text(english, encoding="utf-8")

    home = tmp_path / "home"
    home.mkdir()
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "HOME": str(home),
        "USERPROFILE": str(home),
    }

    def legesher(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", CLI, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=project,
            env=env,
            check=False,
        )

    translated = legesher(
        "translate",
        "source.py",
        "--from",
        "en",
        "--to",
        lang,
        "--output",
        "programa.py",
    )
    assert translated.returncode == 0, translated.stderr
    native = (project / "programa.py").read_text(encoding="utf-8")
    assert native != english  # the script is really written in the pack's words

    result = legesher("run", "programa.py")
    assert result.stdout == f"{text}\n", result.stderr
    assert result.returncode == 0, result.stderr
