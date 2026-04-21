"""Phase 1: IS/IS NOT problem definition."""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd import schemas


def phase_1_is_isnt(state: dict) -> dict:
    context = (
        f"Problem:\n{state['problem']}\n\n"
        f"Research highlights (first 3 specific searches):\n"
    )
    for s in state.get("websearch_specific", [])[:3]:
        context += f"- Q: {s['query']}\n  Results: {s['results'][:300]}\n"

    result = call_claude(
        model=model_for_role("is_isnt_extraction"),
        system=load_prompt("is_isnt_extraction"),
        user=context,
        json_schema=schemas.IS_ISNT_EXTRACTION,
        purpose="is_isnt_extraction",
    )
    state["is_isnt_table"] = result
    state["phase_1_complete"] = True
    return state
