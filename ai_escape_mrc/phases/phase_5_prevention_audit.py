"""Phase 5: Prevention audit ??3 sequential rounds, no outer loop.

Only audits Q3 (MRC-NC) and Q4 (MRC-ND) preventions ??there are no
prevention actions for Q1/Q2 (those are corrective-only quadrants).
"""
import json
from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import ClaudeSession
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc import schemas
from ai_escape_mrc.validators import sanitize_legacy_identity, FORBIDDEN_LEGACY_IDENTITY_TERMS

# One internal critique per visit; the outer graph loop (phase_5 -> phase_4 on
# REWORK) is now the real iteration.
NUM_ROUNDS = 1
PREVENTION_QUADRANTS = ["q3_mrc_nc", "q4_mrc_nd"]


def _has_addressable(audit: dict) -> bool:
    """True if the audit round surfaced at least one weakness that triggers an
    in-place change: ADDRESSABLE (append a note) or OVER_SCOPED (cut/replace the
    control). Both keep the loop alive so the fix is actually applied."""
    for w in audit.get("weaknesses", []) or []:
        if isinstance(w, dict) and w.get("classification") in ("ADDRESSABLE", "OVER_SCOPED"):
            return True
    return False


def phase_5_prevention_audit(state: dict) -> dict:
    system = load_prompt("prevention_audit")
    state.setdefault("phase_5_rounds", [])
    residual = []

    prevention_actions = state.get("prevention_actions") or {}
    preventions = {
        q: prevention_actions.get(q, {})
        for q in PREVENTION_QUADRANTS
        if q in prevention_actions
    }

    # Corrective-only run (router set mrc_applicable=False, or no prevention
    # actions were produced): there is nothing to audit. No-op gracefully —
    # do NOT open a Claude session. Verdict EXHAUSTED, status passed (a clean
    # no-op is not a degraded/fallback audit).
    if not preventions:
        state["phase_5_residual_risks"] = []
        state["phase_5_verdict"] = "EXHAUSTED"
        state["phase_5_status"] = "passed"
        state["phase_5_attempt_count"] = state.get("phase_5_attempt_count", 0) + 1
        state["phase_5_complete"] = True
        return state

    # One persistent session across rounds (same rationale as phase_3): pay the
    # subprocess startup once and minimize spawns on a flaky transport.
    with ClaudeSession(
        system=system,
        model=model_for_role("prevention_audit"),
        schema=schemas.PREVENTION_AUDIT,
        allow_tools=True,
        max_turns=3,        # cap WebSearch to ~1-2 per audit (avoids 200-470s blowups)
        timeout_sec=240,    # bound the worst case; tool-less fallback on timeout
    ) as sess:
        for round_num in range(1, NUM_ROUNDS + 1):
            user_msg = (
                f"Round {round_num} of {NUM_ROUNDS}.\n\n"
                f"Prevention actions (Q3, Q4 only):\n"
                f"{json.dumps(preventions, ensure_ascii=False)[:20000]}\n\n"
                "Use WebSearch if you want to benchmark against state-of-the-art."
            )
            audit = None
            for attempt in (1, 2):
                try:
                    audit = sess.ask(user_msg, purpose=f"phase_5_prevention_audit_round_{round_num}_attempt_{attempt}")
                except VisibilityContractError:
                    raise
                except Exception as e:
                    import sys
                    sys.stderr.write(f"[WARN] phase_5 round {round_num} attempt {attempt} failed: {str(e)[:150]}; skipping round\n")
                    audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED", "_fallback": True}
                    break  # transport error → take the fallback, do not retry for identity reasons

                serialized = json.dumps(audit, ensure_ascii=False)
                if sanitize_legacy_identity(serialized) == serialized:
                    break  # clean → accept this audit
                if attempt == 2:
                    # Second attempt still dirty: sanitize deterministically and
                    # accept. Never raise — a cosmetic naming token can no longer
                    # destroy the audit (sanitize-then-proceed).
                    audit = json.loads(sanitize_legacy_identity(serialized))
                    break
                offending = next(
                    (t for t in FORBIDDEN_LEGACY_IDENTITY_TERMS if t in str(audit)),
                    "unspecified legacy term",
                )
                user_msg = (
                    f"{user_msg}\n\n"
                    f"REGENERATE: your previous audit response contained forbidden legacy "
                    f"identity literal {offending!r} in a `suggested_fix` or `issue` field. "
                    f"Per the IDENTITY RENAME RULE in the system prompt, rewrite using the "
                    f"active identity (`eightd-X` → `aem-X`, etc.). Emit the corrected JSON only."
                )
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

            # Quality-preserving early exit (see phase_3): stop on EXHAUSTED or
            # a real round with no ADDRESSABLE weakness (converged).
            if audit.get("verdict") == "EXHAUSTED":
                break
            if not audit.get("_fallback") and not _has_addressable(audit):
                break

    state["phase_5_residual_risks"] = residual
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-FINDING: same hardcoded "EXHAUSTED regardless" defect as phase_3;
    #   ecosystem escape review 2026-04-25 documented as instance #3 of degraded-emission-
    #   with-warning anti-pattern.
    # WIKI-ACTION: track failed-fallback rounds; surface as phase_5_status so
    #   Phase 7 emit can predicate on it.
    has_fallback_round = any(
        isinstance(r, dict) and r.get("_fallback") for r in state["phase_5_rounds"]
    )
    # Emit the real verdict so the graph can loop back to phase_4 on REWORK.
    this_visit = state["phase_5_rounds"][-1] if state["phase_5_rounds"] else {}
    raw_verdict = this_visit.get("verdict") if isinstance(this_visit, dict) else None
    if has_fallback_round or raw_verdict != "REWORK":
        verdict = "EXHAUSTED"
    else:
        verdict = "REWORK"
    state["phase_5_verdict"] = verdict
    state["phase_5_status"] = "failed" if has_fallback_round else "passed"
    state["phase_5_attempt_count"] = state.get("phase_5_attempt_count", 0) + 1
    state["phase_5_complete"] = True
    return state


def _apply_fixes(prevention_actions: dict, audit: dict) -> None:
    """Apply the audit's in-place fixes to the prevention actions.

    - ADDRESSABLE: append the suggested_fix as an audit note (additive).
    - OVER_SCOPED: CUT — replace the over-engineered control with the auditor's
      proportionate suggested_fix, recording the original under ``downscoped_from``
      so the cut is auditable (no silent deletion). This is the one path that can
      make the quality-control phase REMOVE bureaucracy, not only add to it.
    """
    for w in audit.get("weaknesses", []) or []:
        if not isinstance(w, dict):
            continue
        cls = w.get("classification")
        q = w.get("quadrant")
        if q not in prevention_actions:
            continue
        pa = prevention_actions[q]
        if not isinstance(pa, dict):
            continue
        if cls == "ADDRESSABLE":
            pa.setdefault("audit_notes", []).append(w.get("suggested_fix", ""))
        elif cls == "OVER_SCOPED":
            replacement = w.get("suggested_fix", "")
            if not replacement:
                # No proportionate alternative supplied: do not blind-delete the
                # control; record the over-scope finding as a note instead.
                pa.setdefault("audit_notes", []).append(
                    "OVER_SCOPED: " + str(w.get("issue", ""))
                )
                continue
            # Record the original control once (keep the FIRST original if a
            # later round cuts again) then replace with the proportionate one.
            pa.setdefault("downscoped_from", pa.get("action", ""))
            pa["action"] = replacement
            pa.setdefault("downscope_notes", []).append(w.get("issue", ""))
