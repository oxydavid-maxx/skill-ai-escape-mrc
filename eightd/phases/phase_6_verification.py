"""Phase 6: Single verification plan call — 4 quadrant metrics in one output.

Prior version made 4 separate LLM calls (one per quadrant). SKILL.md asks
for ONE verification plan with a table of metrics. Consolidated.
"""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt


def phase_6_verification(state: dict) -> dict:
    payload = json.dumps({
        "corrective_actions": state.get("corrective_actions", {}),
        "prevention_actions": state.get("prevention_actions", {}),
        "problem": state.get("problem", ""),
    }, ensure_ascii=False)

    plan = call_claude(
        model=model_for_role("proof_of_action"),
        system=load_prompt("proof_of_action"),
        user=payload,
        parse_json=True,
        purpose="phase_6_verification_plan",
    )

    state["verification_plan"] = plan

    # Backward-compat: old closure audit expects proof_of_action keyed by quadrant.
    # Re-expose the table that way for any downstream consumer.
    per_q = {}
    for row in plan.get("quadrants", []) or []:
        if isinstance(row, dict) and row.get("quadrant"):
            per_q[row["quadrant"]] = row
    state["proof_of_action"] = per_q

    state["phase_6_complete"] = True
    return state
