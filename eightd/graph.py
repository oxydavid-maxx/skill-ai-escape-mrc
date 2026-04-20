"""LangGraph StateGraph construction for 8D pipeline."""
from langgraph.graph import StateGraph, START, END
from eightd.state import EightDState

from eightd.phases.phase_0_research import phase_0_research
from eightd.phases.phase_1_is_isnt import phase_1_is_isnt
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis
from eightd.phases.phase_3_soa import phase_3_soa_research
from eightd.phases.phase_3_rc_audit import phase_3_rc_audit, route_from_phase_3
from eightd.phases.phase_4_actions import phase_4_actions
from eightd.phases.phase_5_soa import phase_5_soa_research
from eightd.phases.phase_5_prevention_audit import (
    phase_5_prevention_audit, route_from_phase_5,
)
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.phases.phase_7_soa import phase_7_soa_research
from eightd.phases.phase_7_report import phase_7_report


def build_graph(checkpointer=None):
    g = StateGraph(EightDState)

    g.add_node("phase_0_research", phase_0_research)
    g.add_node("phase_1_is_isnt", phase_1_is_isnt)
    g.add_node("phase_2_why_analysis", phase_2_why_analysis)
    g.add_node("phase_3_soa", phase_3_soa_research)
    g.add_node("phase_3_rc_audit", phase_3_rc_audit)
    g.add_node("phase_4_actions", phase_4_actions)
    g.add_node("phase_5_soa", phase_5_soa_research)
    g.add_node("phase_5_prevention_audit", phase_5_prevention_audit)
    g.add_node("phase_6_verification", phase_6_verification)
    g.add_node("phase_7_soa", phase_7_soa_research)
    g.add_node("phase_7_report", phase_7_report)

    g.add_edge(START, "phase_0_research")
    g.add_edge("phase_0_research", "phase_1_is_isnt")
    g.add_edge("phase_1_is_isnt", "phase_2_why_analysis")
    g.add_edge("phase_2_why_analysis", "phase_3_soa")
    g.add_edge("phase_3_soa", "phase_3_rc_audit")
    g.add_conditional_edges(
        "phase_3_rc_audit",
        route_from_phase_3,
        {
            "phase_2_why_analysis": "phase_2_why_analysis",
            "phase_4_actions": "phase_4_actions",
        },
    )
    g.add_edge("phase_4_actions", "phase_5_soa")
    g.add_edge("phase_5_soa", "phase_5_prevention_audit")
    g.add_conditional_edges(
        "phase_5_prevention_audit",
        route_from_phase_5,
        {
            "phase_4_actions": "phase_4_actions",
            "phase_6_verification": "phase_6_verification",
        },
    )
    g.add_edge("phase_6_verification", "phase_7_soa")
    g.add_edge("phase_7_soa", "phase_7_report")
    g.add_edge("phase_7_report", END)

    return g.compile(checkpointer=checkpointer)
