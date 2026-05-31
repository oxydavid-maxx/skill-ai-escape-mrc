"""Phase 2: Why analysis ??4 parallel quadrant Why chains, schema-constrained."""
from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.parallel import parallel_map
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc.state import QUADRANTS
from ai_escape_mrc import schemas


def _critiqued_quadrants(state: dict) -> set:
    rounds = state.get("phase_3_rounds") or []
    if not rounds:
        return set()
    latest = rounds[-1] if isinstance(rounds[-1], dict) else {}
    return {
        w.get("quadrant") for w in (latest.get("weaknesses") or [])
        if isinstance(w, dict) and w.get("quadrant") in QUADRANTS
    }


def phase_2_why_analysis(state: dict) -> dict:
    prior = state.get("why_chains") or {}
    is_rework = bool(prior) and bool(state.get("phase_3_rounds"))

    if is_rework:
        # Targeted rework: only regenerate the quadrants the audit actually
        # critiqued; reuse the prior chain for the rest (no LLM call). If the
        # REWORK carried no quadrant-specific weakness (pure framing verdict),
        # regenerate all four.
        targets = _critiqued_quadrants(state) or set(QUADRANTS)
        to_run = [q for q in QUADRANTS if q in targets]
        results = parallel_map(lambda q: _run_quadrant_safe(state, q), to_run, max_workers=4)
        chains = dict(prior)
        for q, r in zip(to_run, results):
            chains[q] = r
        state["why_chains"] = chains
    else:
        results = parallel_map(lambda q: _run_quadrant_safe(state, q), QUADRANTS, max_workers=4)
        state["why_chains"] = dict(zip(QUADRANTS, results))

    state["phase_2_complete"] = True
    return state


def _run_quadrant_safe(state: dict, quadrant: str) -> dict:
    try:
        return _run_quadrant(state, quadrant)
    except VisibilityContractError:
        raise
    except Exception as e:
        import sys
        sys.stderr.write(f"[WARN] phase_2 {quadrant} failed: {str(e)[:150]}; using stub\n")
        return {
            "quadrant": quadrant,
            "whys": [{"n": 1, "why": "LLM call failed ??populate manually", "new_insight": ""}],
            "root": "unknown",
            "_fallback": True,
        }


def _framing_block(state: dict) -> str:
    refl = state.get("framing_reflection") or {}
    if not isinstance(refl, dict) or not (refl.get("higher_level_question") or refl.get("reframing")):
        return ""
    return (
        "Higher-level framing to respect BEFORE diving into technical detail:\n"
        f"- Reframing: {refl.get('reframing', '')}\n"
        f"- Keep answering: {refl.get('higher_level_question', '')}\n\n"
    )


def _rework_block(state: dict, quadrant: str) -> str:
    """On a loop-back (RC audit returned REWORK), give this quadrant its prior
    chain + the auditor's critique so it REVISES rather than regenerates blind."""
    rounds = state.get("phase_3_rounds") or []
    prior = (state.get("why_chains") or {}).get(quadrant)
    if not rounds or not isinstance(prior, dict):
        return ""
    latest = rounds[-1] if isinstance(rounds[-1], dict) else {}
    critiques = [
        w for w in (latest.get("weaknesses", []) or [])
        if isinstance(w, dict) and w.get("quadrant") == quadrant
        and w.get("classification") in ("ADDRESSABLE", None)
    ]
    crit_text = "\n".join(
        f"  - [why {w.get('why_step_n')}] {w.get('issue', '')} -> fix: {w.get('suggested_fix', '')}"
        for w in critiques
    ) or "  - (no quadrant-specific critique; address the framing flaw)"
    return (
        "REVISION PASS (the audit sent this back for REWORK). Here is your prior "
        "why-chain for this quadrant and the auditor's critique. Revise to address "
        "EVERY critique, keep what is sound, and deepen where flagged — do not "
        "start from scratch.\n"
        f"Prior root: {prior.get('root', '')}\n"
        f"Auditor critique:\n{crit_text}\n\n"
    )


def _run_quadrant(state: dict, quadrant: str) -> dict:
    user_msg = (
        f"Quadrant: {quadrant}\n"
        f"Problem: {state['problem']}\n\n"
        f"{_framing_block(state)}"
        f"{_rework_block(state, quadrant)}"
        f"IS/IS NOT:\n{state.get('is_isnt_table')}\n\n"
        f"Research context (top findings):\n"
    )
    for s in state.get("websearch_specific", [])[:3]:
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
