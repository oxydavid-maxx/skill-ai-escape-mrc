"""LangGraph StateGraph construction for the AI Escape MRC pipeline.

Topology (simplified from prior version):
  START
    -> phase_0_research
    -> phase_1_is_isnt
    -> phase_2_why_analysis  (4 parallel quadrant Whys)
    -> phase_3_rc_audit      (3 sequential rounds, tool-use websearch)
    -> phase_4_actions       (2 corrective + 2 prevention, parallel)
    -> phase_5_prevention_audit  (3 sequential rounds, tool-use websearch)
    -> phase_6_verification  (1 unified plan)
    -> phase_7_report
    -> phase_8_collect_actions
    -> phase_9_write_plan
    -> phase_10_emit_and_wait
    -> END

Removed from prior: phase_3_soa, phase_5_soa, phase_7_soa (pre-batched SoA
replaced by tool-use websearch inside audit phases).
Removed: conditional REWORK edges (audits now run fixed 3 rounds then move
on; residual risks logged).
"""
import os
from functools import wraps
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphInterrupt
from ai_escape_mrc.state import AiEscapeMrcState

# Max audit->regenerate round-trips per loop (phase_3->phase_2, phase_5->phase_4).
# Default 2; set CLAUDE_AI_ESCAPE_MRC_MAX_REWORK=0 to disable looping entirely
# (reverts to the linear, faster behavior).
def _max_rework() -> int:
    try:
        return max(0, int(os.environ.get("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "2")))
    except (TypeError, ValueError):
        return 2


def _route_after_rc_audit(state: dict) -> str:
    """REWORK + under the rework cap -> regenerate why-chains; else proceed."""
    if state.get("phase_3_verdict") == "REWORK" and state.get("phase_3_attempt_count", 0) <= _max_rework():
        return "phase_2_why_analysis"
    return "phase_4_actions"


def _route_after_prev_audit(state: dict) -> str:
    """REWORK + under the rework cap -> regenerate actions; else collect actions
    (which then fans out to verification ∥ plan)."""
    if state.get("phase_5_verdict") == "REWORK" and state.get("phase_5_attempt_count", 0) <= _max_rework():
        return "phase_4_actions"
    return "phase_8_collect_actions"

from ai_escape_mrc.phases.phase_0_research import phase_0_research
from ai_escape_mrc.phases.phase_1_is_isnt import phase_1_is_isnt
from ai_escape_mrc.phases.phase_2_why_analysis import phase_2_why_analysis
from ai_escape_mrc.phases.phase_3_rc_audit import phase_3_rc_audit
from ai_escape_mrc.phases.phase_4_actions import phase_4_actions
from ai_escape_mrc.phases.phase_5_prevention_audit import phase_5_prevention_audit
from ai_escape_mrc.phases.phase_6_verification import phase_6_verification
from ai_escape_mrc.phases.phase_7_report import phase_7_report
from ai_escape_mrc.phases.phase_8_collect_actions import phase_8_collect_actions
from ai_escape_mrc.phases.phase_9_write_plan import phase_9_write_plan
from ai_escape_mrc.phases.phase_10_emit_and_wait import phase_10_emit_and_wait


def _wrap_with_progress(name: str, fn):
    """Decorator: enforce visibility receipts around each node invocation."""
    @wraps(fn)
    def wrapper(state):
        from ai_escape_mrc import progress as _p
        from ai_escape_mrc.stage_summary import (
            emit_phase_error,
            emit_phase_start_summary,
            emit_stage_summary,
        )

        emit_phase_start_summary(name, state)
        _p.phase_start(name, {"state_keys": list(state.keys())[:20]})
        try:
            result = fn(state)
            if not isinstance(result, dict):
                raise TypeError(f"{name} must return dict state patch, got {type(result).__name__}")
            merged = dict(state)
            merged.update(result)
            summary_patch = emit_stage_summary(name, merged)
            result.update(summary_patch)
            _p.phase_end(name, {"ok": True})
            return result
        except GraphInterrupt:
            _p.emit(name, "phase_interrupt", {"reason": "awaiting_human_approval"})
            raise
        except Exception as e:
            emit_phase_error(name, state, e)
            _p.emit(name, "phase_error", {"error": type(e).__name__, "message": str(e)[:300]})
            raise
    return wrapper


def build_graph(checkpointer=None):
    g = StateGraph(AiEscapeMrcState)

    g.add_node("phase_0_research", _wrap_with_progress("phase_0_research", phase_0_research))
    g.add_node("phase_1_is_isnt", _wrap_with_progress("phase_1_is_isnt", phase_1_is_isnt))
    g.add_node("phase_2_why_analysis", _wrap_with_progress("phase_2_why_analysis", phase_2_why_analysis))
    g.add_node("phase_3_rc_audit", _wrap_with_progress("phase_3_rc_audit", phase_3_rc_audit))
    g.add_node("phase_4_actions", _wrap_with_progress("phase_4_actions", phase_4_actions))
    g.add_node("phase_5_prevention_audit", _wrap_with_progress("phase_5_prevention_audit", phase_5_prevention_audit))
    g.add_node("phase_6_verification", _wrap_with_progress("phase_6_verification", phase_6_verification))
    g.add_node("phase_7_report", _wrap_with_progress("phase_7_report", phase_7_report))
    g.add_node("phase_8_collect_actions", _wrap_with_progress("phase_8_collect_actions", phase_8_collect_actions))
    g.add_node("phase_9_write_plan", _wrap_with_progress("phase_9_write_plan", phase_9_write_plan))
    g.add_node("phase_10_emit_and_wait", _wrap_with_progress("phase_10_emit_and_wait", phase_10_emit_and_wait))

    g.add_edge(START, "phase_0_research")
    g.add_edge("phase_0_research", "phase_1_is_isnt")
    g.add_edge("phase_1_is_isnt", "phase_2_why_analysis")
    g.add_edge("phase_2_why_analysis", "phase_3_rc_audit")
    # RC audit may loop back to phase_2 to regenerate why-chains (REWORK).
    g.add_conditional_edges(
        "phase_3_rc_audit",
        _route_after_rc_audit,
        {"phase_2_why_analysis": "phase_2_why_analysis", "phase_4_actions": "phase_4_actions"},
    )
    g.add_edge("phase_4_actions", "phase_5_prevention_audit")
    # Prevention audit may loop back to phase_4 to regenerate actions (REWORK);
    # otherwise it proceeds to collect the finalized actions.
    g.add_conditional_edges(
        "phase_5_prevention_audit",
        _route_after_prev_audit,
        {"phase_4_actions": "phase_4_actions", "phase_8_collect_actions": "phase_8_collect_actions"},
    )
    # Tail parallelism: phase_6 (verification) and phase_9 (plan) both read the
    # finalized actions and write independent artifacts, so they run concurrently
    # after the actions are collected. phase_7 (report) is the join: it waits for
    # both before rendering.
    g.add_edge("phase_8_collect_actions", "phase_6_verification")
    g.add_edge("phase_8_collect_actions", "phase_9_write_plan")
    g.add_edge("phase_6_verification", "phase_7_report")
    g.add_edge("phase_9_write_plan", "phase_7_report")
    g.add_edge("phase_7_report", "phase_10_emit_and_wait")
    g.add_edge("phase_10_emit_and_wait", END)

    return g.compile(checkpointer=checkpointer)
