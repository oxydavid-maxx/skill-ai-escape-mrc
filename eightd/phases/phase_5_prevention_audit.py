"""Phase 5b: Prevention audit with SoA citation requirement + loop cap."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.phases.phase_3_rc_audit import (
    _format_soa, _extract_urls, _cites_soa_lenient, MAX_OUTER_ATTEMPTS,
)


def phase_5_prevention_audit(state: dict) -> dict:
    system = load_prompt("prevention_audit")
    soa_context = _format_soa(state.get("phase_5_soa_research", []))
    soa_urls = _extract_urls(state.get("phase_5_soa_research", []))

    state.setdefault("phase_5_rounds", [])
    attempt = state.get("phase_5_attempt_count", 0) + 1
    state["phase_5_attempt_count"] = attempt
    force_accept = attempt >= MAX_OUTER_ATTEMPTS

    for round_num in range(1, 4):
        user_msg = (
            f"Round: {round_num}\n\n"
            f"Prevention actions:\n"
            f"{json.dumps(state['prevention_actions'], ensure_ascii=False)[:5000]}\n\n"
            f"Phase 5a SoA research:\n{soa_context}"
        )
        audit = call_claude(
            model=model_for_role("prevention_audit"),
            system=system,
            user=user_msg,
            parse_json=True,
            purpose=f"phase_5_prevention_audit_round_{round_num}_attempt_{attempt}",
        )
        state["phase_5_rounds"].append(audit)

        verdict = audit.get("verdict")
        citation_ok = _cites_soa_lenient(audit, soa_urls, min_citations=1)
        audit["_citation_check"] = "ok" if citation_ok else "weak"

        if verdict == "EXHAUSTED":
            if citation_ok or force_accept:
                state["phase_5_verdict"] = "EXHAUSTED"
                state["phase_5_complete"] = True
                if not citation_ok:
                    audit["_force_accepted_reason"] = (
                        f"force-accepted after {attempt} outer attempts"
                    )
                return state
            audit["rejection_reason"] = "verdict_EXHAUSTED_without_any_soa_citation"
            continue
        if verdict == "REWORK":
            if force_accept:
                state["phase_5_verdict"] = "EXHAUSTED"
                state["phase_5_complete"] = True
                audit["_force_accepted_reason"] = (
                    f"REWORK overridden on attempt {attempt}/{MAX_OUTER_ATTEMPTS}"
                )
                return state
            state["phase_5_verdict"] = "REWORK"
            state["phase_5_complete"] = False
            return state
        for w in audit.get("weaknesses", []):
            q = w.get("quadrant")
            if q in state["prevention_actions"]:
                pa = state["prevention_actions"][q]
                # phase_4 normalizes to dict, but guard here in case of
                # checkpoint resume from an older run that saved a list shape.
                if isinstance(pa, dict):
                    pa.setdefault("audit_notes", []).append(
                        w.get("suggested_fix", "")
                    )

    if force_accept:
        state["phase_5_verdict"] = "EXHAUSTED"
        state["phase_5_complete"] = True
    else:
        state["phase_5_verdict"] = "REWORK"
        state["phase_5_complete"] = False
    return state


def route_from_phase_5(state: dict) -> str:
    if state.get("phase_5_verdict") == "REWORK":
        state["phase_4_complete"] = False
        return "phase_4_actions"
    return "phase_6_verification"
