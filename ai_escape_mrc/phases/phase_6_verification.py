"""Phase 6: Single verification plan call ??4 quadrant metrics in one output.

Prior version made 4 separate LLM calls (one per quadrant). SKILL.md asks
for ONE verification plan with a table of metrics. Consolidated.
"""
import json
from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc import schemas


def phase_6_verification(state: dict) -> dict:
    payload = json.dumps({
        "corrective_actions": state.get("corrective_actions", {}),
        "prevention_actions": state.get("prevention_actions", {}),
        "problem": state.get("problem", ""),
    }, ensure_ascii=False)

    try:
        plan = call_claude(
            model=model_for_role("proof_of_action"),
            system=load_prompt("proof_of_action"),
            user=payload,
            json_schema=schemas.VERIFICATION_PLAN,
            purpose="phase_6_verification_plan",
        )
    except VisibilityContractError:
        raise
    except Exception as e:
        import sys
        sys.stderr.write(f"[WARN] phase_6 verification LLM failed: {str(e)[:200]}; using stub\n")
        plan = {
            "quadrants": [
                {"quadrant": q,
                 "action_type": "corrective" if q.startswith("q1") or q.startswith("q2") else "prevention",
                 "metric": "TBD", "target": "TBD", "data_source": "TBD",
                 "baseline": "unknown", "measurement_schedule": "TBD",
                 "failure_response": "TBD"}
                for q in ("q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd")
            ],
            "overall_timeframe": "6 months minimum",
            "phase_8_trigger": "next recurrence of same problem class",
            "_fallback": True,
        }

    # Backward-compat: old closure audit expects proof_of_action keyed by quadrant.
    per_q = {}
    for row in plan.get("quadrants", []) or []:
        if isinstance(row, dict) and row.get("quadrant"):
            per_q[row["quadrant"]] = row

    # Return a PATCH (not the whole state): phase_6 runs in parallel with phase_9
    # (plan), so it must only declare the keys it owns to avoid a concurrent-update
    # conflict in LangGraph.
    return {
        "verification_plan": plan,
        "proof_of_action": per_q,
        "phase_6_complete": True,
    }
