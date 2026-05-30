"""Deterministic report renderer (no LLM) — render.render_report."""
from ai_escape_mrc.render import render_report

_TEMPLATE = """# AI Escape MRC Report: {problem_slug}
**Date**: {date}
**Problem**: {problem}
**Run ID**: {run_id}

## Section A: Root Cause Matrix
| TRC | Q1: {q1_trc_nc_root} | Q2: {q2_trc_nd_root} |
| MRC | Q3: {q3_mrc_nc_root} | Q4: {q4_mrc_nd_root} |

## Section B: Corrective
| TRC | {q1_corrective} | {q2_corrective} |

## Section B2: Prevention
| MRC | {q3_prevention} | {q4_prevention} |

## Section C: Proof
| Q1 metric={q1_metric} target={q1_target} |

## IS/IS NOT
{is_isnt_table_rendered}

## Why Chains
{why_chains_rendered}

## Phase 3
{phase_3_rounds_rendered}

## Phase 4
{phase_4_rendered}

## Phase 5
{phase_5_rounds_rendered}

## Phase 6
{phase_6_rendered}

## Citations
{soa_citations_rendered}

## Closure
{closure_audit_rendered}
"""


def _state():
    return {
        "problem": "pytest collection aborted on Python 3.11",
        "run_id": "run-x",
        "is_isnt_table": {
            "what": {"is": "SyntaxError at collection", "is_not": "test failure", "distinction": "interpreter cannot parse"},
            "where": {"is": "one test file", "is_not": "prod code", "distinction": "scoped"},
            "when": {"is": "on 3.11", "is_not": "on 3.12", "distinction": "version-conditional"},
            "extent": {"is": "whole suite skipped", "is_not": "one test", "distinction": "all-or-nothing"},
        },
        "why_chains": {
            "q1_trc_nc": {"whys": [{"n": 1, "why": "nested-quote f-string", "new_insight": "PEP 701 only on 3.12"}],
                          "root": "linter target-version not pinned to requires-python", "audit_notes": []},
            "q2_trc_nd": {"whys": [{"n": 1, "why": "no AST checker"}], "root": "no cross-version syntax gate"},
            "q3_mrc_nc": {"whys": [{"n": 1, "why": "no improvement loop"}], "root": "no process owner"},
            "q4_mrc_nd": {"whys": [{"n": 1, "why": "no failure-mode audit"}], "root": "CI health undecomposed"},
        },
        "corrective_actions": {
            "q1_trc_nc": {"action": "patch the f-string", "rationale": "single origin", "owner": "team"},
            "q2_trc_nd": {"action": "add target-version py311", "rationale": "close the gap"},
        },
        "prevention_actions": {
            "q3_mrc_nc": {"action": "generate CI matrix from requires-python",
                          "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
                          "hierarchy_level": 3, "deployment_scope": "PROJECT"},
            "q4_mrc_nd": {"action": "pre-commit ruff", "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
                          "hierarchy_level": 2},
        },
        "verification_plan": {
            "quadrants": [
                {"quadrant": "q1_trc_nc", "action_type": "corrective", "metric": "CollectError count", "target": "0", "data_source": "CI logs https://example.com/ci"},
                {"quadrant": "q2_trc_nd", "action_type": "corrective", "metric": "py_compile failures", "target": "0"},
                {"quadrant": "q3_mrc_nc", "action_type": "prevention", "metric": "matrix coverage", "target": "100%"},
                {"quadrant": "q4_mrc_nd", "action_type": "prevention", "metric": "floor-incompatible commits", "target": "0"},
            ],
            "overall_timeframe": "6 months",
        },
        "phase_3_rounds": [
            {"round": 1, "verdict": "CONTINUE", "weaknesses": [
                {"classification": "ADDRESSABLE", "quadrant": "q1_trc_nc", "why_step_n": 3,
                 "issue": "exit code wrong", "suggested_fix": "use exit 2",
                 "evidence": "see https://peps.python.org/pep-0701/"}]},
            {"round": 2, "verdict": "EXHAUSTED", "weaknesses": []},
        ],
        "phase_5_rounds": [
            {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
                {"classification": "RESIDUAL", "quadrant": "q3_mrc_nc", "issue": "branch protection not IaC"}]},
        ],
    }


def test_render_report_fills_all_sections():
    closure = {"root_cause_matrix_complete": True, "verification_plan_present": True, "overall_pass": True}
    out = render_report(_state(), _TEMPLATE, closure)

    # placeholders all substituted
    for ph in ("{problem}", "{run_id}", "{why_chains_rendered}", "{phase_3_rounds_rendered}",
               "{q1_trc_nc_root}", "{closure_audit_rendered}", "{q1_metric}"):
        assert ph not in out
    # matrices
    assert "linter target-version not pinned" in out
    assert "patch the f-string" in out
    assert "generate CI matrix from requires-python" in out
    assert "CollectError count" in out
    # full detail sections
    assert "nested-quote f-string" in out          # why chain text
    assert "PEP 701 only on 3.12" in out            # new_insight
    assert "exit code wrong" in out                 # audit weakness
    assert "use exit 2" in out                      # suggested fix
    assert "ADDRESSABLE" in out and "RESIDUAL" in out
    # citation harvested from weakness evidence
    assert "https://peps.python.org/pep-0701/" in out
    # closure
    assert "root_cause_matrix_complete" in out
    assert len(out) > 1500


def test_render_report_handles_sparse_state():
    out = render_report({"problem": "p", "run_id": "r"}, _TEMPLATE, None)
    assert "not available" in out  # missing sections degrade, no crash
    for ph in ("{why_chains_rendered}", "{q1_trc_nc_root}", "{phase_6_rendered}"):
        assert ph not in out
