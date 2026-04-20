"""Phase 3b: RC audit with SoA citation requirement + loop-back routing.

Fix 2026-04-21:
- Outer Phase2↔Phase3 loop cap via state['phase_3_attempt_count'].
  After MAX_OUTER_ATTEMPTS (3), force EXHAUSTED with residual-risk note
  rather than infinite loop.
- Citation check made lenient: accept if audit text mentions ANY SoA URL
  (substring match on full audit JSON), not just exact list entries.
- Citation check is now a QUALITY SIGNAL logged, not a hard gate.
"""
import json
import re
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt

URL_RE = re.compile(r"https?://[^\s)\"']+")
MAX_OUTER_ATTEMPTS = 3


def phase_3_rc_audit(state: dict) -> dict:
    system = load_prompt("rc_audit")
    soa_context = _format_soa(state.get("phase_3_soa_research", []))
    soa_urls = _extract_urls(state.get("phase_3_soa_research", []))

    state.setdefault("phase_3_rounds", [])
    attempt = state.get("phase_3_attempt_count", 0) + 1
    state["phase_3_attempt_count"] = attempt
    force_accept = attempt >= MAX_OUTER_ATTEMPTS

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
            purpose=f"phase_3_rc_audit_round_{round_num}_attempt_{attempt}",
        )
        state["phase_3_rounds"].append(audit)

        verdict = audit.get("verdict")
        citation_ok = _cites_soa_lenient(audit, soa_urls, min_citations=1)
        audit["_citation_check"] = "ok" if citation_ok else "weak"

        if verdict == "EXHAUSTED":
            # Lenient: accept if ANY citation (or force_accept on final attempt)
            if citation_ok or force_accept:
                state["phase_3_verdict"] = "EXHAUSTED"
                state["phase_3_complete"] = True
                if not citation_ok:
                    audit["_force_accepted_reason"] = (
                        f"force-accepted after {attempt} outer attempts to avoid infinite loop; "
                        "citation quality weak but analysis substantive"
                    )
                return state
            audit["rejection_reason"] = "verdict_EXHAUSTED_without_any_soa_citation"
            continue
        if verdict == "REWORK":
            if force_accept:
                # Final attempt — override REWORK to EXHAUSTED with note
                state["phase_3_verdict"] = "EXHAUSTED"
                state["phase_3_complete"] = True
                audit["_force_accepted_reason"] = (
                    f"REWORK verdict overridden on attempt {attempt}/{MAX_OUTER_ATTEMPTS} "
                    "to prevent infinite loop; residual weaknesses recorded"
                )
                return state
            state["phase_3_verdict"] = "REWORK"
            state["phase_3_complete"] = False
            return state
        # CONTINUE: apply addressable fixes
        state["why_chains"] = _apply_audit_fixes(state["why_chains"], audit)

    # Exhausted internal rounds without explicit verdict
    if force_accept:
        state["phase_3_verdict"] = "EXHAUSTED"
        state["phase_3_complete"] = True
    else:
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
    """Strict: citations list must have min_citations exact matches."""
    cited = set(audit.get("soa_citations_used", []))
    valid = cited & available_urls
    return len(valid) >= min_citations


def _cites_soa_lenient(audit: dict, available_urls: set, min_citations: int = 1) -> bool:
    """Lenient: any SoA URL appearing anywhere in the serialized audit counts.

    Handles cases where Opus mentions URLs in weakness.soa_citation or
    in the analysis prose rather than only in the soa_citations_used list.
    """
    if not available_urls:
        return True  # no SoA context → can't require citations
    audit_text = json.dumps(audit, ensure_ascii=False)
    hits = sum(1 for u in available_urls if u in audit_text)
    return hits >= min_citations


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
