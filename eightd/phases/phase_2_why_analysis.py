"""Phase 2: Why analysis — 4 parallel quadrant Why chains.

Prior version retried each quadrant up to 3 times if len(whys) < 10. That
multiplied calls by up to 3x. Trust the LLM once; if a chain is short, the
audit phase will catch it. The count requirement stays in the prompt.
"""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.parallel import parallel_map
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_2_why_analysis(state: dict) -> dict:
    results = parallel_map(lambda q: _run_quadrant(state, q), QUADRANTS, max_workers=4)
    state["why_chains"] = dict(zip(QUADRANTS, results))
    state["phase_2_complete"] = True
    return state


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
        parse_json=True,
        max_tokens=8000,
        purpose=f"why_{quadrant}",
    )
