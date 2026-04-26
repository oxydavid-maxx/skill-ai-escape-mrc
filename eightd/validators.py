# WIKI-CONSULTED: silent-staleness#three-layer-defense
# WIKI-FINDING: Output validation is layer 2 of the silent-staleness defense —
#   detect degraded output before it propagates to downstream consumers.
#   Phase 9 can silently emit a too-short or structurally invalid plan.md;
#   without this check the FSM transitions to Phase 10 with a broken artifact.
# WIKI-ACTION: validate_phase9_plan() asserts size + structural markers before
#   the FSM is allowed to transition; raises typed exception on failure so the
#   caller can emit a fail-closed gate artifact (R13 compliant — no degraded warning).
"""Output-contract validators for 8D pipeline phases.

Each validator raises a typed exception (from eightd.errors) on failure.
No degraded-success warnings are emitted (R13 compliance) — callers receive
a typed exception and must route to a fail-closed state.
"""
from __future__ import annotations

from pathlib import Path

from eightd.errors import Phase9OutputContractError


#: Minimum acceptable plan.md size in bytes.
PLAN_MIN_BYTES: int = 500

#: Structural markers that must appear in a valid plan.md.
PLAN_REQUIRED_MARKERS: tuple[str, ...] = ("## Task",)


def validate_phase9_plan(
    plan_path: Path,
    *,
    min_bytes: int = PLAN_MIN_BYTES,
    required_markers: tuple[str, ...] = PLAN_REQUIRED_MARKERS,
) -> None:
    """Assert plan.md meets the Phase 9 output contract.

    Checks (in order):
    1. File exists at ``plan_path``.
    2. File size > ``min_bytes``.
    3. Content contains every marker in ``required_markers``.

    Raises:
        Phase9OutputContractError: on the first failing predicate.
            The ``predicate`` attribute names the check that failed.

    Args:
        plan_path: Path to the plan.md file produced by Phase 9.
        min_bytes: Minimum acceptable file size in bytes (default 500).
        required_markers: Tuple of strings that must appear in the content.
    """
    plan_path = Path(plan_path)

    # Predicate 1: file exists
    if not plan_path.exists():
        raise Phase9OutputContractError(
            f"plan.md not found at {plan_path}",
            predicate="file_exists",
        )

    # Predicate 2: size check
    size = plan_path.stat().st_size
    if size <= min_bytes:
        raise Phase9OutputContractError(
            f"plan.md too small: {size} bytes <= {min_bytes} bytes threshold",
            predicate="min_size",
        )

    # Predicate 3: structural markers
    content = plan_path.read_text(encoding="utf-8")
    for marker in required_markers:
        if marker not in content:
            raise Phase9OutputContractError(
                f"plan.md missing required marker: {marker!r}",
                predicate=f"marker:{marker}",
            )
