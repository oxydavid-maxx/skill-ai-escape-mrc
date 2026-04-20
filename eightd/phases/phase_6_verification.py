"""Phase 6: Verification plan + Proof of Action 4-quadrant matrix."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_6_verification(state: dict) -> dict:
    proof_prompt = load_prompt("proof_of_action")
    state["proof_of_action"] = {}

    for quadrant in QUADRANTS:
        payload = json.dumps({
            "quadrant": quadrant,
            "corrective": state["corrective_actions"].get(quadrant, {}),
            "prevention": state["prevention_actions"].get(quadrant, {}),
        }, ensure_ascii=False)
        proof = call_claude(
            model=model_for_role("proof_of_action"),
            system=proof_prompt,
            user=payload,
            parse_json=True,
        )
        state["proof_of_action"][quadrant] = proof

    state["verification_plan"] = {
        "metrics": [state["proof_of_action"][q].get("metric") for q in QUADRANTS],
        "data_sources": [state["proof_of_action"][q].get("data_source") for q in QUADRANTS],
        "timeframe_default": "6 months",
        "failure_response_default": "re-open 8D for the affected quadrant",
    }
    state["phase_6_complete"] = True
    return state
