"""Phase 4: Corrective (Q1+Q2) + Prevention (Q3+Q4) ??4 parallel calls total.

Per SKILL.md:
  Q1 (TRC-NC) ??Corrective
  Q2 (TRC-ND) ??Corrective
  Q3 (MRC-NC) ??Prevention
  Q4 (MRC-ND) ??Prevention

Prior version generated prevention for ALL 4 quadrants (8 calls) ??wrong.
"""
import json
from ai_escape_mrc.errors import VisibilityContractError, OutputIdentityContractError
from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.parallel import parallel_run
from ai_escape_mrc.utils import load_prompt
from ai_escape_mrc.validators import (
    validate_action_payload,
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
)
from ai_escape_mrc import schemas

CORRECTIVE_QUADRANTS = ["q1_trc_nc", "q2_trc_nd"]
PREVENTION_QUADRANTS = ["q3_mrc_nc", "q4_mrc_nd"]


def _normalize_action_dict(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict):
        return v[0]
    return {
        "action": str(v)[:500],
        "_parse_warning": f"expected dict, got {type(v).__name__}",
    }


def _call_with_legacy_term_retry(call_fn, *, system, user, json_schema, purpose):
    """Run an LLM call; on legacy-identity-term detection, retry once with a
    named critique injected; if the retry still trips the gate, re-raise.

    No fallback stub on identity failures - that would defeat the producer
    gate. Transport errors (SDK crashes / timeouts) are handled by the
    caller's existing try/except, not here.
    """
    for attempt in (1, 2):
        result = call_fn(
            model=model_for_role(purpose),
            system=system,
            user=user,
            json_schema=json_schema,
            purpose=purpose if attempt == 1 else f"{purpose}_retry_legacy",
        )
        try:
            validate_action_payload(result, artifact_name=f"phase_4 {purpose} (attempt {attempt})")
            return result
        except OutputIdentityContractError:
            if attempt == 2:
                raise
            offending = next(
                (t for t in FORBIDDEN_LEGACY_IDENTITY_TERMS if t in str(result)),
                "unspecified legacy term",
            )
            user = (
                f"{user}\n\n"
                f"REGENERATE: your previous response contained forbidden legacy "
                f"identity literal {offending!r}. Per the IDENTITY RENAME RULE in "
                f"the system prompt, rewrite using the active identity (e.g. "
                f"`eightd-X` -> `aem-X`). Emit the corrected JSON only."
            )
    # Unreachable (loop always returns or raises) - present only to satisfy linters
    raise RuntimeError("unreachable")  # pragma: no cover


def phase_4_actions(state: dict) -> dict:
    corrective_prompt = load_prompt("corrective_action")
    prevention_prompt = load_prompt("prevention_action")

    # Capture prior prevention actions + latest audit BEFORE we reset state, so a
    # phase_5 loop-back (REWORK) can REVISE rather than regenerate blind.
    prior_prevention = dict(state.get("prevention_actions") or {})
    p5_rounds = state.get("phase_5_rounds") or []
    refl = state.get("framing_reflection") or {}
    higher_q = refl.get("higher_level_question") if isinstance(refl, dict) else None

    def _revision_for(q):
        if q not in PREVENTION_QUADRANTS or not p5_rounds:
            return None
        prior = prior_prevention.get(q)
        if not isinstance(prior, dict):
            return None
        latest = p5_rounds[-1] if isinstance(p5_rounds[-1], dict) else {}
        crits = [
            {"issue": w.get("issue"), "suggested_fix": w.get("suggested_fix")}
            for w in (latest.get("weaknesses") or [])
            if isinstance(w, dict) and w.get("quadrant") == q
        ]
        return {
            "instruction": ("REVISION PASS: the prevention audit returned REWORK. Revise this "
                            "prevention action to address every critique; keep what is sound; "
                            "do not start from scratch."),
            "prior_action": prior,
            "auditor_critique": crits or "address the framing-level flaw the audit raised",
        }

    def _build_payload(q):
        payload = {
            "quadrant": q,
            "root_cause": state["why_chains"].get(q, {}),
            "problem": state["problem"],
        }
        if higher_q:
            payload["higher_level_question_to_respect"] = higher_q
        revision = _revision_for(q)
        if revision:
            payload["revision"] = revision
        return json.dumps(payload, ensure_ascii=False)

    def _corrective(q):
        try:
            r = _call_with_legacy_term_retry(
                call_claude,
                system=corrective_prompt,
                user=_build_payload(q),
                json_schema=schemas.CORRECTIVE_ACTION,
                purpose=f"corrective_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except OutputIdentityContractError:
            # Identity contamination is a content error, NOT a transport error.
            # Fail closed - no stub fallback, no degraded emission (R13 compliance).
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] corrective {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD ??LLM failed",
                       "rationale": "populate manually", "_fallback": True}

    def _prevention(q):
        try:
            r = _call_with_legacy_term_retry(
                call_claude,
                system=prevention_prompt,
                user=_build_payload(q),
                json_schema=schemas.PREVENTION_ACTION,
                purpose=f"prevention_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except OutputIdentityContractError:
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] prevention {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD ??LLM failed",
                       "gate_test": {"scope": "FAIL", "persistence": "FAIL", "measurability": "FAIL"},
                       "hierarchy_level": 5, "_fallback": True}

    if p5_rounds and prior_prevention:
        # Targeted rework from phase_5: corrective (Q1/Q2) is not audited by
        # phase_5, so keep it unchanged; only regenerate the critiqued prevention
        # quadrants (or all prevention if the REWORK was a pure framing verdict).
        latest = p5_rounds[-1] if isinstance(p5_rounds[-1], dict) else {}
        critiqued = {
            w.get("quadrant") for w in (latest.get("weaknesses") or [])
            if isinstance(w, dict) and w.get("quadrant") in PREVENTION_QUADRANTS
        } or set(PREVENTION_QUADRANTS)
        prev_to_run = [q for q in PREVENTION_QUADRANTS if q in critiqued]
        tasks = [lambda q=q: _prevention(q) for q in prev_to_run]
        # Preserve prior corrective + uncritiqued prevention.
        state["corrective_actions"] = dict(state.get("corrective_actions") or {})
        state["prevention_actions"] = dict(prior_prevention)
    else:
        tasks = (
            [lambda q=q: _corrective(q) for q in CORRECTIVE_QUADRANTS]
            + [lambda q=q: _prevention(q) for q in PREVENTION_QUADRANTS]
        )
        state["corrective_actions"] = {}
        state["prevention_actions"] = {}

    for q, result in parallel_run(tasks, max_workers=4):
        normalized = _normalize_action_dict(result)
        if q in CORRECTIVE_QUADRANTS:
            state["corrective_actions"][q] = normalized
        else:
            state["prevention_actions"][q] = normalized

    state["phase_4_complete"] = True
    return state
