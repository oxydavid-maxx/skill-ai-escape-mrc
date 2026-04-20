"""Phase 3b: RC audit with SoA citation requirement + loop-back routing."""
import json
import re
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt

URL_RE = re.compile(r"https?://[^\s)\"']+")


def phase_3_rc_audit(state: dict) -> dict:
    system = load_prompt("rc_audit")
    soa_context = _format_soa(state.get("phase_3_soa_research", []))
    soa_urls = _extract_urls(state.get("phase_3_soa_research", []))

    state.setdefault("phase_3_rounds", [])

    for round_num in range(1, 4):
        user_msg = (
            f"Round: {round_num}\n\n"
            f"Why chains:\n{json.dumps(state['why_chains'], ensure_ascii=False)[:5000]}\n\n"
            f"Phase 3a SoA research:\n{soa_context}"
        )
        audit = call_claude(
            model=model_for_role("rc_audit"),
            system=system,
            user=user_msg,
            parse_json=True,
        )
        state["phase_3_rounds"].append(audit)

        verdict = audit.get("verdict")
        if verdict == "EXHAUSTED":
            if _cites_soa(audit, soa_urls, min_citations=2):
                state["phase_3_verdict"] = "EXHAUSTED"
                state["phase_3_complete"] = True
                return state
            audit["rejection_reason"] = "verdict_EXHAUSTED_without_soa_citations"
            continue
        if verdict == "REWORK":
            state["phase_3_verdict"] = "REWORK"
            state["phase_3_complete"] = False
            return state
        # CONTINUE: apply addressable fixes
        state["why_chains"] = _apply_audit_fixes(state["why_chains"], audit)

    state["phase_3_verdict"] = "REWORK"
    state["phase_3_complete"] = False
    return state


def _format_soa(research: list[dict]) -> str:
    out = []
    for r in research:
        out.append(f"Query: {r['query']}\nResults:\n{r['results'][:1500]}\n---\n")
    return "\n".join(out)


def _extract_urls(research: list[dict]) -> set[str]:
    urls = set()
    for r in research:
        urls.update(URL_RE.findall(r.get("results", "")))
    return urls


def _cites_soa(audit: dict, available_urls: set, min_citations: int = 2) -> bool:
    cited = set(audit.get("soa_citations_used", []))
    valid = cited & available_urls
    return len(valid) >= min_citations


def _apply_audit_fixes(why_chains: dict, audit: dict) -> dict:
    for w in audit.get("weaknesses", []):
        q = w.get("quadrant")
        n = w.get("why_step_n")
        if q in why_chains and w.get("classification") == "ADDRESSABLE":
            for why in why_chains[q].get("whys", []):
                if why.get("n") == n:
                    why.setdefault("audit_notes", []).append(w.get("suggested_fix", ""))
    return why_chains


def route_from_phase_3(state: dict) -> str:
    if state.get("phase_3_verdict") == "REWORK":
        state["phase_2_complete"] = False
        return "phase_2_why_analysis"
    return "phase_4_actions"
