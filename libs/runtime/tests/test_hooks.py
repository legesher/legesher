"""install()/uninstall() hook behavior (CORE-1679)."""

from __future__ import annotations

import sys
import threading
import types

import pytest

import legesher_runtime
from legesher_runtime import hooks


@pytest.fixture(autouse=True)
def clean_hooks():
    """Every test starts and ends with the real hooks in place."""
    originals = (sys.excepthook, threading.excepthook, sys.unraisablehook)
    yield
    legesher_runtime.uninstall()
    sys.excepthook, threading.excepthook, sys.unraisablehook = originals
    hooks._saved = None


def capture_exc_info(code):
    try:
        code()
    except BaseException:
        return sys.exc_info()
    raise AssertionError("did not raise")


class TestInstallUninstall:
    def test_install_swaps_all_three_hooks(self):
        before = (sys.excepthook, threading.excepthook, sys.unraisablehook)
        legesher_runtime.install("es")
        assert sys.excepthook is not before[0]
        assert threading.excepthook is not before[1]
        assert sys.unraisablehook is not before[2]

    def test_uninstall_restores_prior_hooks(self):
        before = (sys.excepthook, threading.excepthook, sys.unraisablehook)
        legesher_runtime.install("es")
        legesher_runtime.uninstall()
        assert (sys.excepthook, threading.excepthook, sys.unraisablehook) == before

    def test_reinstall_then_one_uninstall_returns_to_origin(self):
        before = sys.excepthook
        legesher_runtime.install("es")
        legesher_runtime.install("ar")  # replaces, but remembers the ORIGINAL
        legesher_runtime.uninstall()
        assert sys.excepthook is before

    def test_uninstall_leaves_foreign_hooks_installed_after_ours(self):
        # Review repro: a hook installed OVER ours used to get clobbered.
        original_threading = threading.excepthook
        legesher_runtime.install("es")

        def foreign_hook(exc_type, exc_value, exc_tb):
            pass

        sys.excepthook = foreign_hook  # someone else layered on top
        legesher_runtime.uninstall()
        assert sys.excepthook is foreign_hook  # foreign hook survives
        assert threading.excepthook is original_threading  # ours restored

    def test_uninstall_without_install_is_a_noop(self):
        before = sys.excepthook
        legesher_runtime.uninstall()
        assert sys.excepthook is before

    def test_install_returns_the_renderer(self):
        renderer = legesher_runtime.install("es")
        assert renderer.lang == "es"


class TestExcepthook:
    def test_uncaught_exception_renders_localized(self, capsys):
        legesher_runtime.install("es")
        exc_info = capture_exc_info(lambda: 1 / 0)
        sys.excepthook(*exc_info)
        err = capsys.readouterr().err
        assert "Rastreo (llamada más reciente al final):" in err
        assert "errordedivisiónporcero: división por cero" in err

    def test_hook_never_raises_falls_back_to_prior_hook(self, capsys):
        recorded = []

        def prior_hook(exc_type, exc_value, exc_tb):
            recorded.append(exc_type)

        sys.excepthook = prior_hook
        renderer = legesher_runtime.install("es")

        def explode(*_args, **_kwargs):
            raise RuntimeError("renderer bug")

        renderer.render = explode  # type: ignore[method-assign]
        exc_info = capture_exc_info(lambda: 1 / 0)
        sys.excepthook(*exc_info)  # must not raise
        assert recorded == [ZeroDivisionError]
        assert capsys.readouterr().err == ""  # nothing half-written

    def test_hook_fallback_is_guarded_against_a_broken_prior_hook(self):
        # Strict never-raise: renderer fails AND the prior hook fails —
        # the wrapper must still not raise.
        def broken_prior(exc_type, exc_value, exc_tb):
            raise OSError("stderr is gone")

        sys.excepthook = broken_prior
        renderer = legesher_runtime.install("es")

        def explode(*_args, **_kwargs):
            raise RuntimeError("renderer bug")

        renderer.render = explode  # type: ignore[method-assign]
        exc_info = capture_exc_info(lambda: 1 / 0)
        sys.excepthook(*exc_info)  # must not raise

    def test_threading_excepthook_renders_localized(self, capsys):
        legesher_runtime.install("es")

        def target():
            raise ValueError("boom in thread")

        thread = threading.Thread(target=target, name="hilo")
        thread.start()
        thread.join()
        err = capsys.readouterr().err
        assert "Exception in thread hilo:" in err
        assert "errordevalor: boom in thread" in err

    def test_threading_excepthook_is_silent_on_systemexit(self, capsys):
        # Review repro: a thread raising SystemExit(3) used to spew a full
        # localized traceback; CPython's stock hook is silent.
        legesher_runtime.install("es")

        def target():
            raise SystemExit(3)

        thread = threading.Thread(target=target, name="hilo")
        thread.start()
        thread.join()
        assert capsys.readouterr().err == ""

    def test_unraisablehook_renders_localized_single_write(self, capsys, monkeypatch):
        legesher_runtime.install("es")
        exc_info = capture_exc_info(lambda: 1 / 0)
        unraisable = types.SimpleNamespace(
            exc_type=exc_info[0],
            exc_value=exc_info[1],
            exc_traceback=exc_info[2],
            err_msg=None,
            object=None,
        )
        writes = []
        real_write = sys.stderr.write
        monkeypatch.setattr(sys.stderr, "write", lambda s: (writes.append(s), real_write(s))[1])
        sys.unraisablehook(unraisable)
        err = capsys.readouterr().err
        # object is None: no ": None" repr appended (CPython fidelity).
        assert err.startswith("Exception ignored in\n")
        assert "errordedivisiónporcero: división por cero" in err
        assert len(writes) == 1  # the whole report is ONE stderr write

    def test_unraisablehook_failure_cannot_interleave_output(self, capsys):
        # Review repro: a failure between two writes used to leave a
        # half-written header before the fallback's full output. With one
        # write, a renderer failure produces ONLY the fallback's output.
        recorded = []

        def prior_unraisable(unraisable):
            recorded.append(unraisable)

        sys.unraisablehook = prior_unraisable
        renderer = legesher_runtime.install("es")

        def explode(*_args, **_kwargs):
            raise RuntimeError("renderer bug")

        renderer.render = explode  # type: ignore[method-assign]
        exc_info = capture_exc_info(lambda: 1 / 0)
        unraisable = types.SimpleNamespace(
            exc_type=exc_info[0],
            exc_value=exc_info[1],
            exc_traceback=exc_info[2],
            err_msg=None,
            object="<some object>",
        )
        sys.unraisablehook(unraisable)
        assert recorded == [unraisable]  # fallback got the whole event
        assert capsys.readouterr().err == ""  # and nothing half-written from ours

    def test_unraisablehook_includes_object_repr_when_present(self, capsys):
        legesher_runtime.install("es")
        exc_info = capture_exc_info(lambda: 1 / 0)
        unraisable = types.SimpleNamespace(
            exc_type=exc_info[0],
            exc_value=exc_info[1],
            exc_traceback=exc_info[2],
            err_msg=None,
            object="mi objeto",
        )
        sys.unraisablehook(unraisable)
        err = capsys.readouterr().err
        assert err.startswith("Exception ignored in: 'mi objeto'\n")
