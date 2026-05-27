"""Phase 4: Corrective (Q1+Q2) + Prevention (Q3+Q4) ??4 parallel calls total.

Per SKILL.md:
  Q1 (TRC-NC) ??Corrective
  Q2 (TRC-ND) ??Corrective
  Q3 (MRC-NC) ??Prevention
  Q4 (MRC-ND) ??Prevention

Prior version generated prevention for ALL 4 quadrants (8 calls) ??wrong.
"""
import json
from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.parallel import parallel_run
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc import schemas

CORRECTIVE_QUADRANTS = ["q1_trc_nc", "q2_trc_nd"]
PREVENTION_QUADRANTS = ["q3_mrc_nc", "q4_mrc_nd"]


def _normalize_action_dict(v):
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

    def _build_payload(q):
        return json.dumps({
            "quadrant": q,
            "root_cause": state["why_chains"].get(q, {}),
            "problem": state["problem"],
        }, ensure_ascii=False)

    def _corrective(q):
        try:
            r = call_claude(
                model=model_for_role("corrective_action"),
                system=corrective_prompt,
                user=_build_payload(q),
                json_schema=schemas.CORRECTIVE_ACTION,
                purpose=f"corrective_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] corrective {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD ??LLM failed",
                       "rationale": "populate manually", "_fallback": True}

    def _prevention(q):
        try:
            r = call_claude(
                model=model_for_role("prevention_action"),
                system=prevention_prompt,
                user=_build_payload(q),
                json_schema=schemas.PREVENTION_ACTION,
                purpose=f"prevention_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] prevention {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD ??LLM failed",
                       "gate_test": {"scope": "FAIL", "persistence": "FAIL", "measurability": "FAIL"},
                       "hierarchy_level": 5, "_fallback": True}

    tasks = (
        [lambda q=q: _corrective(q) for q in CORRECTIVE_QUADRANTS]
        + [lambda q=q: _prevention(q) for q in PREVENTION_QUADRANTS]
    )

    state["corrective_actions"] = {}
    state["prevention_actions"] = {}
    for q, result in parallel_run(tasks, max_workers=4):
        normalized = _normalize_action_dict(result)
        if q in CORRECTIVE_QUADRANTS:
            state["corrective_actions"][q] = normalized
        else:
            state["prevention_actions"][q] = normalized

    state["phase_4_complete"] = True
    return state
