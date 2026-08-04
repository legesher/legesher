# Changelog - legesher-runtime

All notable changes to legesher-runtime are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Added

- Initial legesher-runtime package: localized tracebacks for Python.
  [CORE-1679]
  - `install(lang=..., python_version=None)` wraps `sys.excepthook`,
    `threading.excepthook`, and `sys.unraisablehook` so uncaught exceptions
    render with localized traceback structure, exception type names (from
    the python language pack), and error messages (from the message
    catalog's anchored matchers, with named slot values preserved).
    `uninstall()` restores the prior hooks.
  - Unmatched messages pass through untranslated; the hooks never raise
    (any renderer failure falls back to the original traceback verbatim,
    and `render()` itself degrades a bogus traceback object to a minimal
    `Type: message` line). Hook fidelity matches CPython: the threading
    hook is silent on `SystemExit`, and the unraisable hook builds its
    whole report in one stderr write (omitting the object part when there
    is none). `uninstall()` restores a hook only when the live hook is
    still Legesher's, so a handler installed on top by someone else is
    never clobbered.
  - PEP 657 carets are never misplaced: byte-identical passthrough at the
    renderer for plain files; for frames compiled from translated source
    under `legesher run` (source-mapped files) the native line is shown,
    the line number remapped, and the translated-offset caret/anchor lines
    dropped — no caret beats a wrong caret. Full caret column re-map
    through the token translation is tracked as follow-up.
  - `TracebackRenderer` is standalone (the hooks are thin adapters) for
    reuse by localized logging.
  - RTL v1 posture: Arabic output is emitted in logical order with no bidi
    control characters; see README for the display-order limitation.
