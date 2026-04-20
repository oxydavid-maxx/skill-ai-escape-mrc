"""Phase 4: Corrective + Prevention actions, 4 quadrants each."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_4_actions(state: dict) -> dict:
    corrective_prompt = load_prompt("corrective_action")
    prevention_prompt = load_prompt("prevention_action")

    state["corrective_actions"] = {}
    state["prevention_actions"] = {}

    for quadrant in QUADRANTS:
        root_cause_chain = state["why_chains"].get(quadrant, {})
        user_payload = json.dumps({
            "quadrant": quadrant,
            "root_cause": root_cause_chain,
            "problem": state["problem"],
        }, ensure_ascii=False)

        corrective = call_claude(
            model=model_for_role("corrective_action"),
            system=corrective_prompt,
            user=user_payload,
            parse_json=True,
        )
        state["corrective_actions"][quadrant] = corrective

        prevention = call_claude(
            model=model_for_role("prevention_action"),
            system=prevention_prompt,
            user=user_payload,
            parse_json=True,
        )
        state["prevention_actions"][quadrant] = prevention

    state["phase_4_complete"] = True
    return state
