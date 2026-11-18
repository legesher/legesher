"""Run command for executing native language Python code.

This module implements the `legesher run` command that enables seamless
execution of Python code written in any natural language.

Example:
    $ legesher run mi_programa.py
    $ legesher run mi_programa.py --lang es
    $ legesher run mi_programa.py --args "--verbose"
"""

import logging
import shlex
import sys
from pathlib import Path
from types import TracebackType

import click
import legesher_runtime

from legesher.config import LegesherConfig, find_project_config
from legesher.runtime import install_error_handler, install_import_hook
from legesher.runtime.source_mapper import get_source_mapper
from legesher_core import TokenTranslator

logger = logging.getLogger(__name__)


def _from_script(tb: TracebackType | None, script: str) -> TracebackType | None:
    """The traceback from the script's first frame on; None if it has none.

    The frames above it are this command's own (the console script, click,
    ``run``), which ``python script.py`` would never show.
    """
    while tb is not None and tb.tb_frame.f_code.co_filename != script:
        tb = tb.tb_next
    return tb


def _language_note(script: Path, config: LegesherConfig) -> str:
    """Which language a script that did not compile was read as, and why.

    A file written in one language and read as another fails on its first
    keyword, and Python's ``SyntaxError`` cannot say that the language was
    the problem. Printed only when ``--lang`` did not name the language.
    """
    lines = [
        f"legesher: {path} could not be used, so none of its settings apply: {problem}."
        for path, problem in config.left_out
    ]
    if config.language_source is not None:
        lines.append(
            f"legesher: {script.name} was read as '{config.language}', the "
            f"language set in {config.language_source}."
        )
        lines.append(
            "legesher: if it is written in another language, pass --lang <code>."
        )
        return "\n".join(lines)
    if config.left_out:
        fix = "fix the file above"
    elif find_project_config() is not None:
        fix = "set one with: legesher config set language <code>"
    else:
        fix = "set one with: legesher init"
    why = (
        "no usable config names a language"
        if config.left_out
        else "no language is configured here"
    )
    lines.append(f"legesher: {script.name} was read as English (en), because {why}.")
    lines.append(
        f"legesher: if it is written in another language, pass --lang <code>, or {fix}"
    )
    return "\n".join(lines)


@click.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--lang", help="Language code (default: auto-detect from config)")
@click.option("--args", help="Arguments to pass to script (space-separated)")
def run(script: str, lang: str | None, args: str | None):
    """Execute native language Python code.

    ⚠️  SECURITY WARNING: This executes arbitrary Python code with full system access.
    Only run scripts from trusted sources. Translation does not add sandboxing or
    security restrictions.

    Legesher run enables seamless execution of Python code written in
    any natural language. The import hook automatically translates imports,
    and errors are displayed with native source code lines.

    Examples:

        \b
        $ legesher run programa.py
        $ legesher run programa.py --lang es
        $ legesher run programa.py --args "--verbose --output results.txt"
    """
    # Load config: --lang overrides the project/user config resolution.
    config = LegesherConfig.load()
    language = lang or config.language

    # Install runtime hooks
    install_import_hook(language)
    install_error_handler(language)
    # Localized tracebacks (CORE-1679): installed LAST so the error handler
    # above is the fallback chain when the renderer degrades. The source
    # mapper is passed through so frames compiled from TRANSLATED source
    # (this command compiles translated code under the native filename)
    # render the native line, remap line numbers, and drop the
    # translated-offset PEP 657 carets instead of misplacing them.
    # Best-effort — a failure here must never stop the script from running.
    try:
        legesher_runtime.install(
            language, config.python_version, source_map=get_source_mapper()
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"localized tracebacks unavailable: {exc}")

    # Prepare sys.argv for the script
    script_path = Path(script).resolve()
    if args:
        # Use shlex to properly parse quoted arguments
        sys.argv = [str(script_path)] + shlex.split(args)
    else:
        sys.argv = [str(script_path)]

    # Execute the script in its own namespace
    script_globals = {
        "__name__": "__main__",
        "__file__": str(script_path),
        "__builtins__": __builtins__,
    }

    try:
        with open(script_path, encoding="utf-8") as f:
            native_code = f.read()

        # Translate main script if needed (import hook only handles imports)
        # from_language_pack creates EN->target translator, so we reverse for target->EN
        en_to_native = TokenTranslator.from_language_pack(language)
        native_to_en = en_to_native.reverse()
        code = native_to_en.translate_code(native_code)

        # Register source mapping for error reporting
        source_mapper = get_source_mapper()
        source_mapper.register_mapping(
            filename=str(script_path),
            native_source=native_code,
            english_source=code,
        )

        # Compile and execute translated code
        compiled = compile(code, str(script_path), "exec")
        exec(compiled, script_globals)

    except SystemExit:
        raise  # Allow scripts to exit normally
    except KeyboardInterrupt:
        sys.exit(130)  # Standard Unix exit code for Ctrl+C
    except Exception as exc:
        # Report the script's error as `python script.py` would: from the
        # script's first frame (a syntax error in the script has none, and
        # CPython prints it without a header), through the installed hook,
        # exit status 1. An error before the script ran, such as a file that
        # cannot be decoded, is the command's own and keeps every frame.
        # A script that does not compile under a language nobody named on
        # the command line is followed by a note saying which one it was.
        script_file = str(script_path)
        tb = _from_script(exc.__traceback__, script_file)
        compile_error = isinstance(exc, SyntaxError) and exc.filename == script_file
        if tb is None and not compile_error:
            raise
        sys.excepthook(type(exc), exc, tb)
        if compile_error and lang is None:
            click.echo(_language_note(script_path, config), err=True)
        sys.exit(1)
