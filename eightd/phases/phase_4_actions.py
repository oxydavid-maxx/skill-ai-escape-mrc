"""Phase 4: Corrective + Prevention actions, 4 quadrants each."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.parallel import parallel_run
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def _normalize_action_dict(v):
    """Coerce LLM action output into a dict.

    Observed LLM output shapes:
      - dict  -> pass through
      - [dict] single-element list -> unwrap
      - other -> wrap with _parse_warning so audit phase can still iterate
    """
    if isinstance(v, dict):
        return v
    if isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict):
        return v[0]
    return {
        "action": str(v)[:500],
        "_parse_warning": f"expected dict, got {type(v).__name__}",
    }


def phase_4_actions(state: dict) -> dict:
    corrective_prompt = load_prompt("corrective_action")
    prevention_prompt = load_prompt("prevention_action")

    state["corrective_actions"] = {}
    state["prevention_actions"] = {}

    def _corrective_for(quadrant: str):
        payload = json.dumps({
            "quadrant": quadrant,
            "root_cause": state["why_chains"].get(quadrant, {}),
            "problem": state["problem"],
        }, ensure_ascii=False)
        return quadrant, "corrective", call_claude(
            model=model_for_role("corrective_action"),
            system=corrective_prompt,
            user=payload,
            parse_json=True,
        )

    def _prevention_for(quadrant: str):
        payload = json.dumps({
            "quadrant": quadrant,
            "root_cause": state["why_chains"].get(quadrant, {}),
            "problem": state["problem"],
        }, ensure_ascii=False)
        return quadrant, "prevention", call_claude(
            model=model_for_role("prevention_action"),
            system=prevention_prompt,
            user=payload,
            parse_json=True,
        )

    # Fan out all 8 calls (4 quadrants x {corrective, prevention}) in parallel.
    tasks = []
    for q in QUADRANTS:
        tasks.append(lambda q=q: _corrective_for(q))
        tasks.append(lambda q=q: _prevention_for(q))

    for quadrant, kind, result in parallel_run(tasks, max_workers=5):
        normalized = _normalize_action_dict(result)
        if kind == "corrective":
            state["corrective_actions"][quadrant] = normalized
        else:
            state["prevention_actions"][quadrant] = normalized

    state["phase_4_complete"] = True
    return state
