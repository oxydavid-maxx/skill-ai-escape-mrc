"""Phase 3: RC audit — 3 sequential rounds in one phase, no outer loop.

Previous design had MAX_OUTER_ATTEMPTS=3 + 3 inner rounds = up to 9 calls.
That over-implemented the skill. SKILL says 3 challenge rounds then move on;
residual risks go into the Residual Risk Register in the final report.

Audit LLM has WebSearch tool available (via CLI native tool-use or SDK
web_search tool) — it uses that directly during a round when it wants to
benchmark a claim, instead of us pre-baking batched SoA results.
"""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd import schemas

NUM_ROUNDS = 3


def phase_3_rc_audit(state: dict) -> dict:
    system = load_prompt("rc_audit")
    state.setdefault("phase_3_rounds", [])
    residual = []

    for round_num in range(1, NUM_ROUNDS + 1):
        # Build prompt with current (possibly updated) why_chains.
        user_msg = (
            f"Round {round_num} of {NUM_ROUNDS}.\n\n"
            f"Why chains (4 quadrants):\n"
            f"{json.dumps(state['why_chains'], ensure_ascii=False)[:6000]}\n\n"
            "Use WebSearch if you want to verify or benchmark a specific claim."
        )
        try:
            audit = call_claude(
                model=model_for_role("rc_audit"),
                system=system,
                user=user_msg,
                json_schema=schemas.RC_AUDIT,
                purpose=f"phase_3_rc_audit_round_{round_num}",
                allow_tools=True,
            )
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] phase_3 round {round_num} failed: {str(e)[:150]}; skipping round\n")
            audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED", "_fallback": True}
        state["phase_3_rounds"].append(audit)

        # Apply ADDRESSABLE fixes to the why_chains in-place so round N+1
        # sees the corrected chains.
        _apply_fixes(state["why_chains"], audit)

        # Collect residuals
        for w in audit.get("weaknesses", []) or []:
            if isinstance(w, dict) and w.get("classification") == "RESIDUAL":
                residual.append(w)

        if audit.get("verdict") == "EXHAUSTED":
            break

    state["phase_3_residual_risks"] = residual
    state["phase_3_verdict"] = "EXHAUSTED"  # always proceed after 3 rounds
    state["phase_3_complete"] = True
    return state


def _apply_fixes(why_chains: dict, audit: dict) -> None:
    """Append suggested_fix as audit_note on the specific why step."""
    for w in audit.get("weaknesses", []) or []:
        if not isinstance(w, dict) or w.get("classification") != "ADDRESSABLE":
            continue
        q = w.get("quadrant")
        n = w.get("why_step_n")
        if q not in why_chains:
            continue
        chain = why_chains[q]
        if not isinstance(chain, dict):
            continue
        for why in chain.get("whys", []):
            if isinstance(why, dict) and why.get("n") == n:
                why.setdefault("audit_notes", []).append(w.get("suggested_fix", ""))
                break
