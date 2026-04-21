"""Phase 1: IS/IS NOT problem definition. Defensive — falls back to stub if LLM fails."""
import sys
from eightd.sdk_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd import schemas

_DIMS = ["what", "where", "when", "extent"]


def _stub_table(problem: str) -> dict:
    return {
        d: {"is": problem if d == "what" else "unknown",
            "is_not": "unknown",
            "distinction": "LLM call failed; populate manually"}
        for d in _DIMS
    }


def phase_1_is_isnt(state: dict) -> dict:
    context = (
        f"Problem:\n{state['problem']}\n\n"
        f"Research highlights (first 3 specific searches):\n"
    )
    for s in state.get("websearch_specific", [])[:3]:
        context += f"- Q: {s['query']}\n  Results: {s['results'][:300]}\n"

    try:
        result = call_claude(
            model=model_for_role("is_isnt_extraction"),
            system=load_prompt("is_isnt_extraction"),
            user=context,
            json_schema=schemas.IS_ISNT_EXTRACTION,
            purpose="is_isnt_extraction",
        )
    except Exception as e:
        sys.stderr.write(f"[WARN] phase_1 IS/IS NOT LLM failed: {type(e).__name__}: {str(e)[:200]}; using stub\n")
        result = _stub_table(state["problem"])

    # Defensive: if any dimension is missing, fill with stub values
    if not isinstance(result, dict):
        result = _stub_table(state["problem"])
    for d in _DIMS:
        if d not in result or not isinstance(result[d], dict):
            result[d] = {"is": "unknown", "is_not": "unknown", "distinction": "LLM output missing"}

    state["is_isnt_table"] = result
    state["phase_1_complete"] = True
    return state
