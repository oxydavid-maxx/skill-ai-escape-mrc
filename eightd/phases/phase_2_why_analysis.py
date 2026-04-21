"""Phase 2: Why analysis — 4 parallel quadrant Why chains, schema-constrained."""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.parallel import parallel_map
from eightd.utils import load_prompt
from eightd.state import QUADRANTS
from eightd import schemas


def phase_2_why_analysis(state: dict) -> dict:
    results = parallel_map(lambda q: _run_quadrant_safe(state, q), QUADRANTS, max_workers=4)
    state["why_chains"] = dict(zip(QUADRANTS, results))
    state["phase_2_complete"] = True
    return state


def _run_quadrant_safe(state: dict, quadrant: str) -> dict:
    try:
        return _run_quadrant(state, quadrant)
    except Exception as e:
        import sys
        sys.stderr.write(f"[WARN] phase_2 {quadrant} failed: {str(e)[:150]}; using stub\n")
        return {
            "quadrant": quadrant,
            "whys": [{"n": 1, "why": "LLM call failed — populate manually", "new_insight": ""}],
            "root": "unknown",
            "_fallback": True,
        }


def _run_quadrant(state: dict, quadrant: str) -> dict:
    user_msg = (
        f"Quadrant: {quadrant}\n"
        f"Problem: {state['problem']}\n\n"
        f"IS/IS NOT:\n{state.get('is_isnt_table')}\n\n"
        f"Research context (top findings):\n"
    )
    for s in state.get("websearch_specific", [])[:2]:
        user_msg += f"- {s['query']}: {s['results'][:200]}\n"
    for w in state.get("wiki_pages", [])[:2]:
        user_msg += f"- wiki: {w['path']}\n  {w['content'][:300]}\n"
    return call_claude(
        model=model_for_role("why_analysis"),
        system=load_prompt("why_analysis"),
        user=user_msg,
        json_schema=schemas.WHY_ANALYSIS,
        max_tokens=8000,
        purpose=f"why_{quadrant}",
    )
