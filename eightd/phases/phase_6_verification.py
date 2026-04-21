"""Phase 6: Verification plan + Proof of Action 4-quadrant matrix."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.parallel import parallel_map
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def _safe_dict(v):
    """Coerce to dict for payload rendering; tolerate list-wrapped or other shapes."""
    if isinstance(v, dict):
        return v
    if isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict):
        return v[0]
    return {"action": str(v)[:500]} if v else {}


def phase_6_verification(state: dict) -> dict:
    proof_prompt = load_prompt("proof_of_action")

    def _proof_for(quadrant: str):
        payload = json.dumps({
            "quadrant": quadrant,
            "corrective": _safe_dict(state["corrective_actions"].get(quadrant, {})),
            "prevention": _safe_dict(state["prevention_actions"].get(quadrant, {})),
        }, ensure_ascii=False)
        return quadrant, call_claude(
            model=model_for_role("proof_of_action"),
            system=proof_prompt,
            user=payload,
            parse_json=True,
        )

    # 4 quadrants → parallel fan-out.
    results = parallel_map(_proof_for, QUADRANTS, max_workers=4)
    state["proof_of_action"] = {q: p for q, p in results}

    state["verification_plan"] = {
        "metrics": [state["proof_of_action"][q].get("metric") for q in QUADRANTS if isinstance(state["proof_of_action"][q], dict)],
        "data_sources": [state["proof_of_action"][q].get("data_source") for q in QUADRANTS if isinstance(state["proof_of_action"][q], dict)],
        "timeframe_default": "6 months",
        "failure_response_default": "re-open 8D for the affected quadrant",
    }
    state["phase_6_complete"] = True
    return state
