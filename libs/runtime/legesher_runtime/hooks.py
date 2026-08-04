"""Exception-hook installation for localized tracebacks (CORE-1679).

Thin adapters over :class:`legesher_runtime.renderer.TracebackRenderer`:
:func:`install` wraps ``sys.excepthook``, ``threading.excepthook``, and
``sys.unraisablehook``; :func:`uninstall` restores whatever was installed
before — per hook, and only when the currently installed hook is still ours:
a hook somebody installed OVER ours in the meantime is left in place.

The hooks NEVER raise. Any renderer failure falls back to the previously
installed hook, and the fallback call itself is guarded as well (a broken
stderr must not raise out of the wrapper — nothing can be printed at that
point anyway), so the worst case is CPython's own traceback, or silence on a
dead stream.

Fidelity notes (matching CPython's stock hooks):

* ``threading.excepthook`` is SILENT on ``SystemExit`` — a thread calling
  ``sys.exit()`` is not an error and prints nothing.
* ``sys.unraisablehook`` omits the ``: {object!r}`` part when the unraisable
  carries no object, and the whole report is built first and written in ONE
  stderr write, so a stream failing mid-report can never leave a half-written
  header in front of the fallback's full output.
"""

from __future__ import annotations

import sys
import threading
from typing import Any

from .renderer import TracebackRenderer

__all__ = ["install", "uninstall"]

#: The hooks replaced by :func:`install` (originals) plus the wrappers we
#: installed (``our_*``, so uninstall can tell whether the live hook is still
#: ours), or None when not installed.
_saved: dict[str, Any] | None = None


def install(
    lang: str,
    python_version: str | None = None,
    *,
    db_path: object = None,
    source_map: Any = None,
) -> TracebackRenderer:
    """Install localized-traceback hooks for ``lang``.

    Args:
        lang: Target language code (``'es'``, ``'ar'``).
        python_version: ``'X.Y'`` tier for the message catalog and pack, or
            ``None`` to follow the running interpreter (the default: the
            messages being rendered are raised by this interpreter).
        db_path: Override the translations database (tests only).
        source_map: Optional source mapper (``has_mapping(filename)`` /
            ``get_native_line`` / ``get_native_source_line``) for frames
            compiled from translated source — see
            :class:`~legesher_runtime.renderer.TracebackRenderer` for how
            mapped frames are rendered.

    Returns:
        The renderer backing the hooks (reusable for logging, CORE-1437).

    Calling :func:`install` again replaces the previous installation but
    remembers the ORIGINAL hooks, so one :func:`uninstall` returns to the
    pre-Legesher state.
    """
    global _saved

    renderer = TracebackRenderer(lang, python_version, db_path=db_path, source_map=source_map)

    if _saved is None:
        _saved = {
            "excepthook": sys.excepthook,
            "threading_excepthook": threading.excepthook,
            "unraisablehook": sys.unraisablehook,
        }
    prior = _saved

    def excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: Any,
    ) -> None:
        try:
            sys.stderr.write(renderer.render(exc_type, exc_value, exc_tb))
        except BaseException:  # noqa: BLE001 - the never-raise contract
            try:
                prior["excepthook"](exc_type, exc_value, exc_tb)
            except BaseException:  # noqa: BLE001 - nothing can print here
                pass

    def threading_excepthook(args: Any) -> None:
        try:
            if args.exc_type is not None and issubclass(args.exc_type, SystemExit):
                return  # CPython's stock hook is silent on SystemExit
            thread_name = args.thread.name if args.thread is not None else "<unknown>"
            rendered = renderer.render(args.exc_type, args.exc_value, args.exc_traceback)
            sys.stderr.write(f"Exception in thread {thread_name}:\n{rendered}")
        except BaseException:  # noqa: BLE001
            try:
                prior["threading_excepthook"](args)
            except BaseException:  # noqa: BLE001
                pass

    def unraisablehook(unraisable: Any) -> None:
        try:
            header = unraisable.err_msg or "Exception ignored in"
            if unraisable.object is not None:
                header = f"{header}: {unraisable.object!r}"
            rendered = renderer.render(
                unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback
            )
            # ONE write: see the module docstring's fidelity notes.
            sys.stderr.write(f"{header}\n{rendered}")
        except BaseException:  # noqa: BLE001
            try:
                prior["unraisablehook"](unraisable)
            except BaseException:  # noqa: BLE001
                pass

    sys.excepthook = excepthook
    threading.excepthook = threading_excepthook
    sys.unraisablehook = unraisablehook
    _saved["our_excepthook"] = excepthook
    _saved["our_threading_excepthook"] = threading_excepthook
    _saved["our_unraisablehook"] = unraisablehook
    return renderer


def uninstall() -> None:
    """Restore the hooks that were live before the first :func:`install`.

    Per hook, and only when the currently installed hook is still ours — a
    hook installed on top of ours by someone else stays in place
    (uninstalling Legesher must not clobber a third party's handler).

    A no-op when nothing is installed.
    """
    global _saved
    if _saved is None:
        return
    if sys.excepthook is _saved.get("our_excepthook"):
        sys.excepthook = _saved["excepthook"]
    if threading.excepthook is _saved.get("our_threading_excepthook"):
        threading.excepthook = _saved["threading_excepthook"]
    if sys.unraisablehook is _saved.get("our_unraisablehook"):
        sys.unraisablehook = _saved["unraisablehook"]
    _saved = None
