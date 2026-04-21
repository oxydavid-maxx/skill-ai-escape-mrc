"""Phase 2: Why analysis — 4 quadrants, >=10 whys each, enforced by count."""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.parallel import parallel_map
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_2_why_analysis(state: dict) -> dict:
    # Quadrants are independent — fan out in parallel.
    results = parallel_map(lambda q: _analyze_quadrant_with_retry(state, q), QUADRANTS, max_workers=4)
    chains = dict(zip(QUADRANTS, results))
    state["why_chains"] = chains
    state["phase_2_complete"] = True
    return state


def _analyze_quadrant_with_retry(state: dict, quadrant: str) -> dict:
    chain = _run_quadrant(state, quadrant)
    attempts = 0
    while len(chain.get("whys", [])) < 10 and attempts < 3:
        chain = _run_quadrant(state, quadrant, retry_note=True)
        attempts += 1
    if len(chain.get("whys", [])) < 10:
        raise RuntimeError(f"Phase 2: {quadrant} failed to produce 10 whys after 3 retries")
    return chain


def _run_quadrant(state: dict, quadrant: str, retry_note: bool = False) -> dict:
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
    if retry_note:
        user_msg += "\nIMPORTANT: prior attempt had fewer than 10 whys. Produce at least 10 distinct causal steps."
    return call_claude(
        model=model_for_role("why_analysis"),
        system=load_prompt("why_analysis"),
        user=user_msg,
        parse_json=True,
        max_tokens=12000,
    )
