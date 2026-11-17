"""`legesher run` honours a configured ``python_version`` and survives a Python newer than the packs.

Two defects, one ticket (CORE-2828). On Python 3.15 every pack lookup asked for
``packs/3.15.yml``, which no pack ships, so the run failed in every language.
The loader now serves a pack's newest tier to a newer interpreter
(``libs/i18n/tests/test_newest_tier_fallback.py``). And pinning
``python_version`` in ``.legesher/config.yml`` did not help, because ``run``
passed it only to the traceback renderer, never to the import hook, the error
handler or the translator for the script itself.

"Newer" is derived from the packs (their newest tier plus one minor), so the
subprocess cases exercise the 3.15 path on any interpreter: the configured
version stands in for the running one.
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

import pytest
from click.testing import CliRunner

from legesher.cli import run as run_module
from legesher.config import LegesherConfig
from legesher.runtime import error_handler, import_hook
from legesher_core import TokenTranslator
from legesher_i18n import LanguagePackLoader
from legesher_i18n.schema_validator import SchemaValidator

TIERS = LanguagePackLoader().list_available_versions("python")
NEWEST = TIERS[-1]
_major, _minor = (int(part) for part in NEWEST.split("."))
#: One minor release past every shipped tier: Python 3.15 on 17 Nov 2026.
NEWER = f"{_major}.{_minor + 1}"
OLDEST = TIERS[0]


class TestTheConfiguredVersionReachesEveryHook:
    @pytest.mark.parametrize("version", [OLDEST, NEWER])
    def test_the_import_hook_takes_it(self, version):
        finder = import_hook.install_import_hook("ar", python_version=version)
        try:
            assert finder.translator.python_version == version
            assert finder.reverse_translator.python_version == version
        finally:
            import_hook.uninstall_import_hook()

    @pytest.mark.parametrize("version", [OLDEST, NEWER])
    def test_the_error_handler_takes_it(self, version, monkeypatch):
        monkeypatch.setattr(sys, "excepthook", sys.excepthook)
        handler = error_handler.install_error_handler("ar", python_version=version)
        assert handler.translator.python_version == version

    def test_both_read_it_from_the_config_when_no_language_is_given(self, monkeypatch):
        monkeypatch.setattr(sys, "excepthook", sys.excepthook)
        config = LegesherConfig(language="ar", python_version=OLDEST)
        monkeypatch.setattr(
            LegesherConfig, "load", classmethod(lambda cls, *a, **k: config)
        )
        finder = import_hook.install_import_hook()
        try:
            assert finder.translator.python_version == OLDEST
        finally:
            import_hook.uninstall_import_hook()
        assert error_handler.install_error_handler().translator.python_version == OLDEST

    def test_run_passes_it_to_the_hook_the_handler_the_script_and_the_renderer(
        self, tmp_path, monkeypatch
    ):
        seen: dict[str, object] = {}

        class _Identity:
            def reverse(self):
                return self

            def translate_code(self, code):
                return code

        def fake_from_language_pack(language, python_version=None):
            seen["script"] = python_version
            return _Identity()

        config = LegesherConfig(language="ar", python_version=OLDEST)
        monkeypatch.setattr(
            LegesherConfig, "load", classmethod(lambda cls, *a, **k: config)
        )
        monkeypatch.setattr(
            run_module,
            "install_import_hook",
            lambda language, python_version=None: seen.setdefault(
                "hook", python_version
            ),
        )
        monkeypatch.setattr(
            run_module,
            "install_error_handler",
            lambda language, python_version=None: seen.setdefault(
                "handler", python_version
            ),
        )
        monkeypatch.setattr(
            run_module.legesher_runtime,
            "install",
            lambda language, python_version, **kw: seen.setdefault(
                "renderer", python_version
            ),
        )
        monkeypatch.setattr(
            run_module.TokenTranslator, "from_language_pack", fake_from_language_pack
        )

        monkeypatch.setattr(sys, "argv", list(sys.argv))  # run() rewrites it
        script = tmp_path / "programa.py"
        script.write_text("x = 1\n", encoding="utf-8")
        result = CliRunner().invoke(run_module.run, [str(script)])

        assert result.exit_code == 0, result.output
        assert seen == {
            "hook": OLDEST,
            "handler": OLDEST,
            "renderer": OLDEST,
            "script": OLDEST,
        }


# -- the CLI on a Python newer than the packs, end to end ---------------------

#: Identifiers that are not Latin: vocalised Arabic, pointed Hebrew, Devanagari
#: with virama and matras, Sinhala with a ZWJ conjunct. (function, parameter, text)
IDENTIFIERS = {
    "ar": ("رَحِّبْ", "اِسْمٌ", "مَرْحَبًا"),
    "he": ("בָּרֵךְ", "שֵׁם", "שָׁלוֹם"),
    "hi": ("अभिवादन", "नाम", "नमस्ते"),
    "si": ("ප්‍රකාශය", "නම", "ආයුබෝවන්"),
}

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
    unicode_version = tuple(
        int(part) for part in unicodedata.unidata_version.split(".")
    )
    if unicode_version < (15, 1) and any(ch in xid_313 for ch in english):
        reason = (
            "CORE-1521: needs Unicode 15.1 identifier rules (CPython 3.13+); "
            f"this interpreter has {unicodedata.unidata_version}"
        )
    elif sys.version_info < (3, 12):
        native = TokenTranslator.from_language_pack(lang, NEWEST).translate_code(
            english
        )
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
    native = TokenTranslator.from_language_pack(lang, NEWEST).translate_code(english)
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
    # The error is the script's, and the localized traceback found the pack:
    # the exception's name is the newest tier's word for it.
    assert result.returncode == 1, result.stderr
    word = newest.exceptions["zerodivisionerror"]
    assert word in result.stderr, result.stderr
    assert "PackNotFoundError" not in result.stderr
