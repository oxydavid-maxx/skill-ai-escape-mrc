# WIKI-EXEMPT: new typed-exception definitions ??no wiki-governed pattern applies
"""Typed exceptions for the AI Escape MRC pipeline.

Typed exceptions make failure routing explicit and testable.
Each exception carries enough context for the FSM to emit a fail-closed
gate artifact (no degraded-success warnings per R13).
"""
from __future__ import annotations


class Phase9TimeoutError(Exception):
    """Phase 9 call_claude() exceeded the wall-clock timeout.

    Raised when the threading watchdog fires before call_claude() returns.
    Callers should write a fail-closed gate artifact with status='phase9_timeout'
    and must NOT emit a degraded plan.md (R13 compliance).
    """


class Phase9OutputContractError(Exception):
    """Phase 9 output failed the post-call contract validator.

    Raised when validate_phase9_plan() finds that plan.md is missing,
    too small, or lacks required structural markers.  The ``predicate``
    attribute names the failing check for diagnostics.

    Callers should write a fail-closed gate artifact with
    status='phase9_contract_failed' (R13 ??no degraded emission).
    """

    def __init__(self, message: str, predicate: str = "") -> None:
        super().__init__(message)
        self.predicate = predicate


class OutputIdentityContractError(Exception):
    """Generated output used a legacy skill identity or command name."""

    def __init__(self, message: str, predicate: str = "") -> None:
        super().__init__(message)
        self.predicate = predicate


class VisibilityContractError(Exception):
    """Runtime visibility receipt emission failed.

    AI Escape MRC treats user-visible progress and durable phase receipts as
    deterministic runtime output, not as optional logging. This exception is
    raised when a required screen, progress, summary, or error artifact cannot
    be emitted.
    """

    def __init__(self, message: str, *, phase: str = "", sink: str = "") -> None:
        super().__init__(message)
        self.phase = phase
        self.sink = sink
