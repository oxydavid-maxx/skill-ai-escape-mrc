"""Phase 5: Prevention audit — 3 sequential rounds, no outer loop.

Only audits Q3 (MRC-NC) and Q4 (MRC-ND) preventions — there are no
prevention actions for Q1/Q2 (those are corrective-only quadrants).
"""
import json
from eightd.sdk_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd import schemas

NUM_ROUNDS = 3
PREVENTION_QUADRANTS = ["q3_mrc_nc", "q4_mrc_nd"]


def phase_5_prevention_audit(state: dict) -> dict:
    system = load_prompt("prevention_audit")
    state.setdefault("phase_5_rounds", [])
    residual = []

    preventions = {
        q: state["prevention_actions"].get(q, {})
        for q in PREVENTION_QUADRANTS
    }

    for round_num in range(1, NUM_ROUNDS + 1):
        user_msg = (
            f"Round {round_num} of {NUM_ROUNDS}.\n\n"
            f"Prevention actions (Q3, Q4 only):\n"
            f"{json.dumps(preventions, ensure_ascii=False)[:5000]}\n\n"
            "Use WebSearch if you want to benchmark against state-of-the-art."
        )
        try:
            audit = call_claude(
                model=model_for_role("prevention_audit"),
                system=system,
                user=user_msg,
                json_schema=schemas.PREVENTION_AUDIT,
                purpose=f"phase_5_prevention_audit_round_{round_num}",
                allow_tools=True,
            )
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] phase_5 round {round_num} failed: {str(e)[:150]}; skipping round\n")
            audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED", "_fallback": True}
        if isinstance(audit, list):
            if len(audit) == 1 and isinstance(audit[0], dict):
                audit = audit[0]
            else:
                audit = {"round": round_num, "weaknesses": audit, "verdict": "EXHAUSTED",
                         "_normalized_from_list": True}
        if not isinstance(audit, dict):
            audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED",
                     "_fallback": True}
        state["phase_5_rounds"].append(audit)

        _apply_fixes(state["prevention_actions"], audit)

        for w in audit.get("weaknesses", []) or []:
            if isinstance(w, dict) and w.get("classification") == "RESIDUAL":
                residual.append(w)

        if audit.get("verdict") == "EXHAUSTED":
            break

    state["phase_5_residual_risks"] = residual
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-FINDING: same hardcoded "EXHAUSTED regardless" defect as phase_3;
    #   ecosystem 8D 2026-04-25 documented as instance #3 of degraded-emission-
    #   with-warning anti-pattern.
    # WIKI-ACTION: track failed-fallback rounds; surface as phase_5_status so
    #   Phase 7 emit can predicate on it.
    has_fallback_round = any(
        isinstance(r, dict) and r.get("_fallback") for r in state["phase_5_rounds"]
    )
    state["phase_5_verdict"] = "EXHAUSTED"
    state["phase_5_status"] = "failed" if has_fallback_round else "passed"
    state["phase_5_complete"] = True
    return state


def _apply_fixes(prevention_actions: dict, audit: dict) -> None:
    for w in audit.get("weaknesses", []) or []:
        if not isinstance(w, dict) or w.get("classification") != "ADDRESSABLE":
            continue
        q = w.get("quadrant")
        if q not in prevention_actions:
            continue
        pa = prevention_actions[q]
        if isinstance(pa, dict):
            pa.setdefault("audit_notes", []).append(w.get("suggested_fix", ""))
