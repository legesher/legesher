# legesher-runtime

Localized tracebacks for Python: uncaught exceptions render with the
traceback structure, exception type name, and error message in the
developer's natural language.

```python
import legesher_runtime

legesher_runtime.install(lang="es")
1 / 0
```

```text
Rastreo (llamada más reciente al final):
  Archivo "ejemplo.py", línea 2, en <module>
    1 / 0
errordedivisiónporcero: división por cero
```

Or via the CLI, which resolves the language from the project's
`.legesher/config.yml`:

```bash
legesher run programa.py --lang es
```

## What it does

- `install(lang=..., python_version=None)` wraps `sys.excepthook`,
  `threading.excepthook`, and `sys.unraisablehook`. `python_version=None`
  follows the running interpreter — the right default, since the messages
  being rendered are raised by this interpreter.
- Structural strings (`Traceback (most recent call last):`, `File …, line …,
  in …`, the chained-exception sentences) and message templates come from the
  Legesher message catalog; the catalog's matchers carry named slots, so
  values (names, counts, types, paths) survive translation.
- Exception TYPE names come from the python language pack for the language,
  consumed as-is.
- `uninstall()` restores the hooks that were live before the first
  `install()`.
- `TracebackRenderer` is a standalone class (the hooks are thin adapters), so
  it can be reused for localized logging.

## Guarantees

- **Unmatched messages pass through untranslated.** A message the catalog has
  no matcher for is printed exactly as CPython produced it (with the type
  name still localized when the pack knows it).
- **The hooks never raise.** Any renderer failure falls back to the original
  traceback verbatim, via the previously installed hook — and
  `TracebackRenderer.render()` holds the same contract standalone: a bogus
  traceback object degrades to a minimal `Type: message` line.
- **PEP 657 carets are never misplaced.** Two regimes:
  - *Plain files* (no source mapping): the echoed source line and its
    caret/anchor line pass through **byte-for-byte** — byte-identical
    passthrough at the renderer.
  - *Translated files under `legesher run`*: the interpreter computed caret
    columns against the **translated** source, so against the displayed
    native line they would be wrong by construction. The renderer therefore
    shows the native source line (via the source mapper), remaps the line
    number, and **drops** the caret/anchor lines — no caret beats a wrong
    caret. A real column re-map through the token translation is tracked as
    a follow-up on the ticket.

## Known limitation: multi-line messages and PEP 678 notes (v1)

The renderer rewrites CPython's formatted text line by line. The final
`ExceptionType: message` line is recognized as a flush-left line matching
that shape — which means a flush-left **continuation line** of a multi-line
exception message, or [PEP 678](https://peps.python.org/pep-0678/)
`add_note()` content, that happens to look like `SomeType: text` can be
falsely localized as if it were an exception line. Values interpolated into
single-line messages are not affected (slot substitution is scoped by the
matched template). The eventual fix is a renderer that walks
`traceback.TracebackException` instead of re-parsing formatted text; until
then, multi-line message bodies are passed through except for lines with
that exact shape.

## Known limitation: RTL display order (v1)

Arabic (and other RTL-script) tracebacks are emitted in **logical order**
with no bidi control characters inserted. How a mixed run like

```text
الملف "ejemplo.py"، السطر 2، في <module>
```

is displayed depends entirely on the terminal's bidi implementation: some
terminals reorder it correctly, many render it left-to-right. This matches
the project-wide v1 posture (stored and emitted strings stay clean of bidi
controls; isolation/ordering is a display-layer concern). Revisiting this —
e.g. optional bidi isolation of interpolated LTR values for terminals that do
implement the bidi algorithm — is tracked with the RTL rendering work.

## License

Apache-2.0.
