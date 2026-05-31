"""Audit -> regenerate REWORK loop: routers, cap, and conditional edges."""
from ai_escape_mrc.graph import (
    build_graph,
    _route_after_rc_audit,
    _route_after_prev_audit,
    _max_rework,
)


def test_rc_router_loops_back_on_rework_under_cap(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "2")
    assert _route_after_rc_audit({"phase_3_verdict": "REWORK", "phase_3_attempt_count": 1}) == "phase_2_why_analysis"
    assert _route_after_rc_audit({"phase_3_verdict": "REWORK", "phase_3_attempt_count": 2}) == "phase_2_why_analysis"


def test_rc_router_proceeds_when_cap_reached(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "2")
    # 3rd visit (attempt_count=3) exceeds 2 reworks -> proceed forward.
    assert _route_after_rc_audit({"phase_3_verdict": "REWORK", "phase_3_attempt_count": 3}) == "phase_4_actions"


def test_rc_router_proceeds_on_exhausted(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "2")
    assert _route_after_rc_audit({"phase_3_verdict": "EXHAUSTED", "phase_3_attempt_count": 1}) == "phase_4_actions"


def test_prev_router_loops_back_on_rework(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "2")
    assert _route_after_prev_audit({"phase_5_verdict": "REWORK", "phase_5_attempt_count": 1}) == "phase_4_actions"
    assert _route_after_prev_audit({"phase_5_verdict": "EXHAUSTED", "phase_5_attempt_count": 1}) == "phase_8_collect_actions"


def test_max_rework_zero_disables_loop(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "0")
    assert _max_rework() == 0
    # First visit already exceeds 0 reworks -> never loops.
    assert _route_after_rc_audit({"phase_3_verdict": "REWORK", "phase_3_attempt_count": 1}) == "phase_4_actions"


def test_max_rework_default_and_bad_value(monkeypatch):
    monkeypatch.delenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", raising=False)
    assert _max_rework() == 2
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_MAX_REWORK", "not-a-number")
    assert _max_rework() == 2


def test_graph_has_loopback_edges():
    graph = build_graph().get_graph()
    edges = {(e.source, e.target) for e in graph.edges}
    # Conditional loop-back edges must exist.
    assert ("phase_3_rc_audit", "phase_2_why_analysis") in edges
    assert ("phase_5_prevention_audit", "phase_4_actions") in edges
    # Forward edges still present.
    assert ("phase_3_rc_audit", "phase_4_actions") in edges
    assert ("phase_5_prevention_audit", "phase_8_collect_actions") in edges
    # Tail parallelism: collect fans out to verification ∥ plan, join at report.
    assert ("phase_8_collect_actions", "phase_6_verification") in edges
    assert ("phase_8_collect_actions", "phase_9_write_plan") in edges
    assert ("phase_6_verification", "phase_7_report") in edges
    assert ("phase_9_write_plan", "phase_7_report") in edges
