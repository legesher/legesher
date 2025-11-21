"""Run command for executing native language Python code.

This module implements the `legesher run` command that enables seamless
execution of Python code written in any natural language.

Example:
    $ legesher run mi_programa.py
    $ legesher run mi_programa.py --lang es
    $ legesher run mi_programa.py --args "--verbose"
"""

import shlex
import sys
from pathlib import Path
from typing import Optional

import click

from legesher.config import LegesherConfig
from legesher.runtime import install_error_handler, install_import_hook
from legesher.runtime.source_mapper import get_source_mapper
from legesher_core import TokenTranslator


@click.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--lang", help="Language code (default: auto-detect from config)")
@click.option("--args", help="Arguments to pass to script (space-separated)")
def run(script: str, lang: Optional[str], args: Optional[str]):
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
    # Load config
    config = LegesherConfig.load()
    language = lang or config.language

    # Install runtime hooks
    install_import_hook(language)
    install_error_handler(language)

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
        translator = TokenTranslator.from_language_pack(language)
        code = translator.translate_code(
            native_code, source_lang=language, target_lang="en"
        )

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
    except Exception:
        # Exception will be handled by our custom excepthook
        raise
