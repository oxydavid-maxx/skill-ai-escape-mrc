"""Phase 8 — collect Phase 4 corrective/prevention actions + Phase 6 verification
into a normalized JSON list for downstream writing-plans dispatch.

Pure-Python; no SDK call.

WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
WIKI-FINDING: coexisting old+new path for the same data is a latent dual-emission bug.
WIKI-ACTION: this module is the SINGLE consumer of phase_4_actions and
             phase_6_verification_plan for dispatch; no fallback human-courier path kept.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


# Quadrant key mapping: eightd state uses lowercase q1_trc_nc form,
# but the dispatched plan + report convention uses TRC-NC form. Translate.
_QUADRANT_LABELS = {
    "q1_trc_nc": "TRC-NC",
    "q2_trc_nd": "TRC-ND",
    "q3_mrc_nc": "MRC-NC",
    "q4_mrc_nd": "MRC-ND",
}


def _normalize_action(action: Any, source_quadrant: str) -> dict[str, Any]:
    """Normalize either a dict or an LLM-returned string into the action schema."""
    if isinstance(action, dict):
        return {
            "title": action.get("title") or action.get("action") or "",
            "description": action.get("description") or action.get("action") or "",
            "files_touched": action.get("files") or action.get("files_touched") or [],
            "owner": action.get("owner", "kuangyu"),
            "priority": action.get("priority", "medium"),
            "source_quadrant": source_quadrant,
        }
    # Fallback: action is a string or unknown shape
    text = str(action) if action is not None else ""
    return {
        "title": text[:80],
        "description": text,
        "files_touched": [],
        "owner": "kuangyu",
        "priority": "medium",
        "source_quadrant": source_quadrant,
    }


def phase_8_collect_actions(state: dict) -> dict:
    run_dir = Path(state["run_dir"])
    actions_path = run_dir / "actions.json"
    out: list[dict[str, Any]] = []

    # Real eightd state shape (per state.py + phase_4_actions.py):
    #   corrective_actions: dict[quadrant_key, action_dict]
    #   prevention_actions: dict[quadrant_key, action_dict]
    #   verification_plan: dict (single)
    # Quadrant keys: q1_trc_nc, q2_trc_nd, q3_mrc_nc, q4_mrc_nd
    corrective = state.get("corrective_actions") or {}
    prevention = state.get("prevention_actions") or {}
    for quadrant_key, label in _QUADRANT_LABELS.items():
        c = corrective.get(quadrant_key)
        if c is not None:
            out.append(_normalize_action(c, f"corrective:{label}"))
        p = prevention.get(quadrant_key)
        if p is not None:
            out.append(_normalize_action(p, f"prevention:{label}"))

    verification_plan = state.get("verification_plan")
    if verification_plan:
        if isinstance(verification_plan, dict):
            # Single verification plan dict — flatten it as one action item
            out.append(_normalize_action(verification_plan, "verification"))
        elif isinstance(verification_plan, list):
            for item in verification_plan:
                out.append(_normalize_action(item, "verification"))

    actions_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"actions_path": str(actions_path), "actions_count": len(out), "phase_8_complete": True}
