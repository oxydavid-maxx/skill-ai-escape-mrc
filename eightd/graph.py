"""LangGraph StateGraph construction for 8D pipeline.

Topology (simplified from prior version):
  START
    → phase_0_research
    → phase_1_is_isnt
    → phase_2_why_analysis  (4 parallel quadrant Whys)
    → phase_3_rc_audit      (3 sequential rounds, tool-use websearch)
    → phase_4_actions       (2 corrective + 2 prevention, parallel)
    → phase_5_prevention_audit  (3 sequential rounds, tool-use websearch)
    → phase_6_verification  (1 unified plan)
    → phase_7_report
    → END

Removed from prior: phase_3_soa, phase_5_soa, phase_7_soa (pre-batched SoA
replaced by tool-use websearch inside audit phases).
Removed: conditional REWORK edges (audits now run fixed 3 rounds then move
on; residual risks logged).
"""
from functools import wraps
from langgraph.graph import StateGraph, START, END
from eightd.state import EightDState

from eightd.phases.phase_0_research import phase_0_research
from eightd.phases.phase_1_is_isnt import phase_1_is_isnt
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis
from eightd.phases.phase_3_rc_audit import phase_3_rc_audit
from eightd.phases.phase_4_actions import phase_4_actions
from eightd.phases.phase_5_prevention_audit import phase_5_prevention_audit
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.phases.phase_7_report import phase_7_report
from eightd.phases.phase_8_collect_actions import phase_8_collect_actions
from eightd.phases.phase_9_write_plan import phase_9_write_plan
from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait
from eightd.phases.phase_11_execute import phase_11_execute


def _wrap_with_progress(name: str, fn):
    """Decorator: emit phase_start / phase_end around each node invocation."""
    @wraps(fn)
    def wrapper(state):
        try:
            from eightd import progress as _p
            _p.phase_start(name, {"state_keys": list(state.keys())[:20]})
        except Exception:
            pass
        try:
            result = fn(state)
            try:
                from eightd import progress as _p
                _p.phase_end(name, {"ok": True})
            except Exception:
                pass
            return result
        except Exception as e:
            try:
                from eightd import progress as _p
                _p.emit(name, "phase_error", {"error": type(e).__name__, "message": str(e)[:300]})
            except Exception:
                pass
            raise
    return wrapper


def build_graph(checkpointer=None):
    g = StateGraph(EightDState)

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
    g.add_node("phase_11_execute", _wrap_with_progress("phase_11_execute", phase_11_execute))

    g.add_edge(START, "phase_0_research")
    g.add_edge("phase_0_research", "phase_1_is_isnt")
    g.add_edge("phase_1_is_isnt", "phase_2_why_analysis")
    g.add_edge("phase_2_why_analysis", "phase_3_rc_audit")
    g.add_edge("phase_3_rc_audit", "phase_4_actions")
    g.add_edge("phase_4_actions", "phase_5_prevention_audit")
    g.add_edge("phase_5_prevention_audit", "phase_6_verification")
    g.add_edge("phase_6_verification", "phase_7_report")
    g.add_edge("phase_7_report", "phase_8_collect_actions")
    g.add_edge("phase_8_collect_actions", "phase_9_write_plan")
    g.add_edge("phase_9_write_plan", "phase_10_emit_and_wait")
    g.add_edge("phase_10_emit_and_wait", "phase_11_execute")
    g.add_edge("phase_11_execute", END)

    return g.compile(checkpointer=checkpointer)
