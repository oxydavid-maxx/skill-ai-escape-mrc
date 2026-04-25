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


def phase_8_collect_actions(state: dict) -> dict:
    run_dir = Path(state["run_dir"])
    actions_path = run_dir / "actions.json"
    out: list[dict[str, Any]] = []

    p4 = state.get("phase_4_actions") or {}
    for quadrant in ("TRC-NC", "TRC-ND", "MRC-NC", "MRC-ND"):
        for item in (p4.get(quadrant) or []):
            out.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "files_touched": item.get("files") or item.get("files_touched") or [],
                "owner": item.get("owner", "kuangyu"),
                "priority": item.get("priority", "medium"),
                "source_quadrant": quadrant,
            })

    for item in (state.get("phase_6_verification_plan") or []):
        out.append({
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "files_touched": item.get("files") or [],
            "owner": item.get("owner", "kuangyu"),
            "priority": "verification",
            "source_quadrant": "verification",
        })

    actions_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"actions_path": str(actions_path), "actions_count": len(out), "phase_8_complete": True}
