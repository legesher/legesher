"""The entitlement seam: default-open, listed-not-hidden, one gateable tool.

Every tool this server ships is listed for every caller. Entitlement is a
call-time policy, not a visibility one: when a caller invokes a tool it is
not entitled to, the answer is an actionable message — what the tool does,
that it requires a Legesher account on the hosted instance, and where to
go — never an opaque failure or a missing tool.

The seam is deliberately narrow, and the narrowness is the promise:

- **The default is open.** :func:`allow_all` is the policy every server
  gets unless a deployment passes its own gate to the factory. The stdio
  entry point and the self-host HTTP entry never install one — local and
  self-hosted use is never gated.
- **Only the tools in :data:`GATEABLE_TOOLS` can be gated at all.** Today
  that is exactly ``map_existing_codebase``. For every other tool —
  ``validate_identifier_translations`` in particular, which is permanently
  free — the gate is never even consulted, so no deployment can gate them
  without changing this open package in the open.
- **The denial text lives here.** What a denied call says is part of this
  package, auditable next to the tools themselves. A gate may append one
  deployment-specific line (:attr:`GateDecision.detail` — a sign-in hint,
  for example) but cannot replace the message.

Supplying per-request context
-----------------------------

A gate decides from the tool name plus whatever per-request context the
deployment resolved (an authenticated identity, an entitlement set). The
transport layer cannot thread that through MCP calls itself, so it rides
the execution context: a wrapper — typically ASGI middleware in front of
the app from ``create_http_app`` — resolves its caller and wraps the
request in :func:`request_context`; the server reads the ambient value and
passes it to the gate on every gated call. Where nothing set a context,
the gate receives ``None``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "ALLOW",
    "GATEABLE_TOOLS",
    "EntitlementGate",
    "GateDecision",
    "allow_all",
    "current_request_context",
    "denial_message",
    "request_context",
]


@dataclass(frozen=True)
class GateDecision:
    """One entitlement verdict for one tool call."""

    allowed: bool
    #: Optional deployment-specific line appended to the package's denial
    #: message (for example, a sign-in URL or device code). Ignored when
    #: ``allowed`` is true.
    detail: str | None = None


#: The affirmative decision, for gates to return by reference.
ALLOW = GateDecision(allowed=True)


class EntitlementGate(Protocol):
    """The policy hook the server factory accepts.

    Called once per invocation of a gateable tool, with the tool name and
    the ambient per-request context (see :func:`request_context`); returns
    whether the call may proceed. Never called for tools outside
    :data:`GATEABLE_TOOLS`. A plain function with this signature is a
    valid gate.
    """

    def __call__(self, tool: str, context: Any) -> GateDecision:
        """Decide whether ``tool`` may run for the caller in ``context``."""
        ...


def allow_all(tool: str, context: Any) -> GateDecision:
    """The default policy: every tool, every caller, no questions."""
    return ALLOW


#: What each gateable tool's denial says. Machine-readable membership and
#: caller-facing copy in one place: a tool is gateable exactly when this
#: package ships denial copy for it, so growing the gated set is a change
#: to the open package — visible in the open — rather than a deployment
#: flag. The message must say what the tool does, that it requires a
#: Legesher account on the hosted instance, and where to go.
_DENIALS: dict[str, str] = {
    "map_existing_codebase": (
        "map_existing_codebase reports what translating a whole codebase "
        "into a language would look like — per-file coverage, unmapped "
        "constructs, and an aggregate summary. On the hosted instance it "
        "requires a Legesher account: sign in or create one at "
        "https://legesher.io, then retry. Local and self-hosted servers "
        "never gate this tool."
    ),
}

#: The only tools a gate is ever consulted for. Everything else is
#: permanently free by construction: ``validate_identifier_translations``
#: and the rest never reach a gate at all.
GATEABLE_TOOLS: frozenset[str] = frozenset(_DENIALS)


def denial_message(tool: str, detail: str | None = None) -> str:
    """The full text an unentitled call of ``tool`` receives.

    The package's copy leads; ``detail`` (from :attr:`GateDecision.detail`)
    is appended as an extra sentence when a deployment provides one.
    """
    text = _DENIALS[tool]
    if detail:
        text = f"{text} {detail}"
    return f"entitlement_required: {text}"


#: The ambient per-request context a gate reads. Deliberately untyped: its
#: shape belongs to the deployment that sets it and the gate that reads it;
#: this package only carries it between the two.
_request_context: ContextVar[Any] = ContextVar("legesher_mcp_request_context", default=None)


def current_request_context() -> Any:
    """The context the current execution is running under (None if unset)."""
    return _request_context.get()


@contextmanager
def request_context(value: Any) -> Iterator[None]:
    """Expose ``value`` to the gate for the duration of the block.

    Context-variable semantics: the value is visible to the wrapped call
    and to tasks started inside the block, and is restored on exit — so an
    ASGI middleware wrapping each request in this context manager scopes
    the value to exactly that request, including the task the streamable
    HTTP transport spawns to serve it.
    """
    token = _request_context.set(value)
    try:
        yield
    finally:
        _request_context.reset(token)
