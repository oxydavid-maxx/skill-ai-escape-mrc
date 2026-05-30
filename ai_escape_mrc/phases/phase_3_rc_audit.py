"""Phase 3: RC audit ??3 sequential rounds in one phase, no outer loop.

Previous design had MAX_OUTER_ATTEMPTS=3 + 3 inner rounds = up to 9 calls.
That over-implemented the skill. SKILL says 3 challenge rounds then move on;
residual risks go into the Residual Risk Register in the final report.

Audit LLM has WebSearch tool available (via CLI native tool-use or SDK
web_search tool) ??it uses that directly during a round when it wants to
benchmark a claim, instead of us pre-baking batched SoA results.
"""
import json
from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import ClaudeSession
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc import schemas

NUM_ROUNDS = 2


def phase_3_rc_audit(state: dict) -> dict:
    system = load_prompt("rc_audit")
    state.setdefault("phase_3_rounds", [])
    residual = []

    # All rounds share one system prompt + schema and form a natural
    # conversation (round N+1 challenges round N's corrected chains), so they
    # run through a single persistent session: one subprocess startup instead
    # of NUM_ROUNDS, and far fewer spawns on a flaky transport. Each round's
    # prompt still carries the full why_chains so it stays correct even if the
    # session must reconnect mid-run.
    with ClaudeSession(
        system=system,
        model=model_for_role("rc_audit"),
        schema=schemas.RC_AUDIT,
        allow_tools=True,
    ) as sess:
        for round_num in range(1, NUM_ROUNDS + 1):
            # Build prompt with current (possibly updated) why_chains.
            user_msg = (
                f"Round {round_num} of {NUM_ROUNDS}.\n\n"
                f"Why chains (4 quadrants):\n"
                f"{json.dumps(state['why_chains'], ensure_ascii=False)[:6000]}\n\n"
                "Use WebSearch if you want to verify or benchmark a specific claim."
            )
            try:
                audit = sess.ask(user_msg, purpose=f"phase_3_rc_audit_round_{round_num}")
            except VisibilityContractError:
                raise
            except Exception as e:
                import sys
                sys.stderr.write(f"[WARN] phase_3 round {round_num} failed: {str(e)[:150]}; skipping round\n")
                audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED", "_fallback": True}
            # Normalize: LLM sometimes returns a bare list of weaknesses or list-wrapped
            # dict; coerce to dict shape so downstream .get works.
            if isinstance(audit, list):
                if len(audit) == 1 and isinstance(audit[0], dict):
                    audit = audit[0]
                else:
                    audit = {"round": round_num, "weaknesses": audit, "verdict": "EXHAUSTED",
                             "_normalized_from_list": True}
            if not isinstance(audit, dict):
                audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED",
                         "_fallback": True}
            state["phase_3_rounds"].append(audit)

            # Apply ADDRESSABLE fixes to the why_chains in-place so round N+1
            # sees the corrected chains.
            _apply_fixes(state["why_chains"], audit)

            # Collect residuals
            for w in audit.get("weaknesses", []) or []:
                if isinstance(w, dict) and w.get("classification") == "RESIDUAL":
                    residual.append(w)

            # Quality-preserving early exit: stop when the audit declares itself
            # exhausted OR a real (non-fallback) round surfaces no ADDRESSABLE
            # weakness (converged) — skipping only rounds that would add nothing.
            if audit.get("verdict") == "EXHAUSTED":
                break
            if not audit.get("_fallback") and not _has_addressable(audit):
                break

    state["phase_3_residual_risks"] = residual
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-FINDING: prior code hardcoded `state["phase_3_verdict"] = "EXHAUSTED"`
    #   regardless of whether rounds ran normally or fell back due to LLM errors.
    #   This let Phase 7 emit reports on top of fundamentally incomplete audits
    #   ("EXHAUSTED with fallback" warning shipped instead of refused) ??exact
    #   ecosystem-wide degraded-emission-with-warning anti-pattern documented in
    #   AI Escape MRC run-1777092777-6e277c0c (2026-04-25), Section B Q1 corrective.
    # WIKI-ACTION: distinguish PASSED (rounds ran naturally) vs FAILED (any
    #   round used the _fallback path due to LLM/parse error). Phase 7 must
    #   predicate emission on phase_3_status == "passed"; otherwise refuse.
    has_fallback_round = any(
        isinstance(r, dict) and r.get("_fallback") for r in state["phase_3_rounds"]
    )
    state["phase_3_verdict"] = "EXHAUSTED"
    state["phase_3_status"] = "failed" if has_fallback_round else "passed"
    state["phase_3_complete"] = True
    return state


def _has_addressable(audit: dict) -> bool:
    """True if the audit round surfaced at least one ADDRESSABLE weakness."""
    for w in audit.get("weaknesses", []) or []:
        if isinstance(w, dict) and w.get("classification") == "ADDRESSABLE":
            return True
    return False


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
