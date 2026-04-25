from eightd.graph import build_graph


def test_graph_compiles():
    g = build_graph()
    assert g is not None


def test_graph_has_all_phase_nodes():
    g = build_graph()
    expected_nodes = {
        "phase_0_research", "phase_1_is_isnt", "phase_2_why_analysis",
        "phase_3_rc_audit", "phase_4_actions",
        "phase_5_prevention_audit",
        "phase_6_verification", "phase_7_report",
        "phase_8_collect_actions", "phase_9_write_plan",
        "phase_10_emit_and_wait", "phase_11_execute",
    }
    nodes = set(g.get_graph().nodes.keys())
    assert expected_nodes.issubset(nodes)


def test_graph_has_no_soa_phase_nodes():
    """SoA phases deleted — replaced by tool-use websearch inside audits."""
    g = build_graph()
    nodes = set(g.get_graph().nodes.keys())
    assert "phase_3_soa" not in nodes
    assert "phase_5_soa" not in nodes
    assert "phase_7_soa" not in nodes
