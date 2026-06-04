"""Phase 7: render report + closure audit."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.utils import load_prompt, sluggify
from ai_escape_mrc.validators import legacy_identity_instruction, sanitize_legacy_identity
URL_RE = re.compile(r"https?://[^\s)\"']+")


class PrerequisiteRefusedError(RuntimeError):
    """Phase 7 refused to emit because a prior phase did not pass.

    Raised when phase_3_status or phase_5_status is anything other than
    'passed'. Catches the ecosystem-wide degraded-emission-with-warning
    anti-pattern at its source ??instead of emitting a report containing
    'EXHAUSTED with fallback' / 'no citations were retrieved', we refuse
    to emit and surface the structural failure to the operator.

    Bypass: set CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS=1 with
    explicit reason captured in
    CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS_REASON.
    """


def phase_7_report(state: dict) -> dict:
    # WIKI-CONSULTED: silent-staleness#data-level-freshness-check
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
    # WIKI-FINDING: prior code emitted a report regardless of phase_3/phase_5
    #   audit status, even when those phases used the _fallback path due to
    #   LLM errors or never produced real citations. Phase 7 then composed a
    #   self-exonerating warning ("EXHAUSTED with fallback", "no external URL
    #   citations were retrieved... proceeding") and shipped it. Per ecosystem
    #   AI Escape MRC 2026-04-25 (run-1777092777-6e277c0c), Section B Q1 corrective:
    #   Phase 7 must predicate emission on `phase_N.status == 'passed'`.
    # WIKI-ACTION: hard-gate emission. Refuse to emit (raise) if any required
    #   phase has status != 'passed'. Operator-side EXEMPT via env var, with
    #   reason captured for audit trail.
    _assert_emission_prerequisites(state)

    # Closure audit (pure Python) runs BEFORE render so the report can include
    # the closure section in its deterministic body.
    state["closure_audit"] = _run_closure_audit(state)

    rendered = _render_report(state)
    # Sanitize-then-proceed: rewrite deprecated self-identity tokens to the
    # active identity rather than raising (a cosmetic naming token must never
    # destroy a finished run at this near-final phase).
    rendered = sanitize_legacy_identity(rendered)

    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    run_report = run_dir / "report.md"
    run_report.write_text(rendered, encoding="utf-8")

    canonical = _canonical_report_path(state)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(rendered, encoding="utf-8")
    state["report_path"] = str(canonical)

    # Email-send migrated to phase_10_emit_and_wait as final delivery.
    # Per function-replacement-convention wiki: WIKI-CONSULTED: function-replacement-convention
    # WIKI-FINDING: "later means never" ??coexistence creates dual-function silent failure.
    # WIKI-ACTION: email-send removed here in same commit as phase_10 wiring (no dual-emission window).

    state["phase_7_complete"] = True
    return state


def _assert_emission_prerequisites(state: dict) -> None:
    """Refuse to emit a report when prior audit phases are not 'passed'.

    # WIKI-CONSULTED: silent-staleness#data-level-freshness-check
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
    # WIKI-FINDING: silent-staleness pattern says 'Data fetch fails ??fallback
    #   to cache ??build output from stale data ??user trusts output ??makes
    #   decisions on outdated information'. Phase 7's prior 'always emit' code
    #   was the same anti-pattern at LLM-output level: audit fails ??fallback
    #   verdict ??build report from incomplete state ??user trusts report ??
    #   acts on a degraded forensic. Per the wiki page, the fix is to refuse
    #   emission rather than to ship with a warning.
    # WIKI-ACTION: hard-gate emission. Refuse to emit (raise) if any required
    #   phase has status != 'passed'. Operator-side EXEMPT via env var, with
    #   reason captured for audit trail (per feature-flag emergency-bypass
    #   pattern: kill-switch is permanent, defaults to enforced, requires
    #   explicit operator action with documented reason to bypass).

    Implements the Q1 corrective from ecosystem escape review 2026-04-25
    (run-1777092777-6e277c0c). The earlier silent-emission failure mode
    let Phase 7 produce reports on top of fallback audits, with the
    failure smuggled into the report as a self-exonerating warning sentence.
    This refuses at the structural boundary instead.
    """
    bypass = os.environ.get("CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS") == "1"
    bypass_reason = os.environ.get("CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS_REASON", "")

    failed: list[str] = []
    for phase_num in (3, 5):
        phase_key = f"phase_{phase_num}_status"
        status = state.get(phase_key)
        if status is None:
            status = _reconstruct_audit_status(state, phase_num)
            if status is None:
                failed.append(f"{phase_key}=missing")
                continue
            state[phase_key] = status
        _reconstruct_residual_risks(state, phase_num)
        if status != "passed":
            failed.append(f"{phase_key}={status}")

    if not failed:
        return

    if bypass:
        state.setdefault("phase_7_bypassed_failures", []).extend(failed)
        state["phase_7_bypass_reason"] = bypass_reason or "(no reason given)"
        import sys
        sys.stderr.write(
            f"[phase_7] WARNING: CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS=1 set; "
            f"emitting despite {failed}. Reason: {state['phase_7_bypass_reason']}\n"
        )
        return

    raise PrerequisiteRefusedError(
        f"Refusing to emit Phase 7 report: prerequisite phase(s) did not pass: "
        f"{', '.join(failed)}. The earlier audit phase(s) used the _fallback "
        f"path (LLM error or no real audit). Per ecosystem-wide degraded-"
        f"emission-with-warning anti-pattern (AI Escape MRC 2026-04-25), reports must not "
        f"ship on top of failed audits with a self-exonerating warning. "
        f"Re-run the failed phase(s), or set "
        f"CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS=1 with reason in "
        f"CLAUDE_AI_ESCAPE_MRC_EMIT_DESPITE_FAILED_AUDITS_REASON if you have an explicit "
        f"operator-side justification."
    )


def _reconstruct_audit_status(state: dict, phase_num: int) -> str | None:
    """Infer audit status from persisted rounds for older checkpoints.

    LangGraph drops undeclared state keys. A real 2026-05-27 run persisted
    phase_3_rounds/phase_5_rounds but lost phase_3_status/phase_5_status before
    the schema was fixed. Treat missing status as unsafe unless the rounds are
    present and show no fallback marker.
    """
    rounds = state.get(f"phase_{phase_num}_rounds")
    if not isinstance(rounds, list) or not rounds:
        return None
    has_fallback_round = any(
        (not isinstance(r, dict)) or bool(r.get("_fallback"))
        for r in rounds
    )
    return "failed" if has_fallback_round else "passed"


def _reconstruct_residual_risks(state: dict, phase_num: int) -> None:
    """Restore residual risk registers from persisted audit rounds if missing."""
    key = f"phase_{phase_num}_residual_risks"
    if state.get(key) is not None:
        return
    rounds = state.get(f"phase_{phase_num}_rounds")
    if not isinstance(rounds, list):
        return
    residual = []
    for audit in rounds:
        if not isinstance(audit, dict):
            continue
        for weakness in audit.get("weaknesses", []) or []:
            if isinstance(weakness, dict) and weakness.get("classification") == "RESIDUAL":
                residual.append(weakness)
    state[key] = residual


def _canonical_report_path(state: dict) -> Path:
    slug = sluggify(state["problem"])
    date_str = datetime.now().strftime("%Y-%m-%d")
    default_base = Path(__file__).parent.parent.parent / "docs" / "ai-escape-mrc-reports"
    base = Path(os.environ.get("CLAUDE_AI_ESCAPE_MRC_REPORTS_DIR", str(default_base)))
    return base / f"ai-escape-mrc-{date_str}-{slug}.md"


def _load_template() -> str:
    template_path = Path(__file__).parent.parent.parent / "templates" / "ai_escape_mrc_report_template.md"
    return template_path.read_text(encoding="utf-8") if template_path.exists() else ""


def _render_report(state: dict) -> str:
    """Render the report DETERMINISTICALLY from full state (no LLM, no timeout).

    The prior implementation sent clipped state to one ~30-min LLM call, which
    both lost fidelity (input clipped to 180 chars/leaf) and was the documented
    Phase-7 timeout failure mode. The template is structured placeholders, so we
    fill them directly from the un-clipped state via render.render_report.

    A legacy all-LLM render remains as a defensive fallback only if the
    deterministic output is implausibly short.
    """
    from ai_escape_mrc.render import render_report

    template = _load_template()
    rendered = render_report(state, template, state.get("closure_audit"))

    if len(rendered) < 1500:
        # Deterministic render produced almost nothing (unexpected state shape);
        # fall back to the legacy LLM render so we still emit something.
        return _legacy_llm_render(state, template)
    return rendered


def _legacy_llm_render(state: dict, template: str) -> str:
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-FINDING: 600s default sdk_client timeout caused every Phase 7 on a
    #   complex problem to TimeoutError after 10 min. Kept as a fallback only.
    return call_claude(
        model=model_for_role("report_generation"),
        system=(
            load_prompt("report_render")
            + "\n\n"
            + legacy_identity_instruction()
            + "\n\nTemplate to follow:\n"
            + template
        ),
        user=json.dumps(_state_summary(state), ensure_ascii=False),
        max_tokens=8000,
        purpose="phase_7_report_render_fallback",
        timeout_sec=1800,
    )


def _state_summary(state: dict) -> dict:
    """Minimal state summary for report render. Does NOT include progress
    events (bloats prompt to 30-50K chars for no real value ??the report
    should document decisions, not a replay of JSONL events)."""
    summary = {
        "problem": state.get("problem"),
        "run_id": state.get("run_id"),
        "date": datetime.now().isoformat(),
        "is_isnt_table": _clip_for_report(state.get("is_isnt_table")),
        "why_chains": _clip_for_report(state.get("why_chains")),
        "corrective_actions": _clip_for_report(state.get("corrective_actions")),
        "prevention_actions": _clip_for_report(state.get("prevention_actions")),
        "verification_plan": _clip_for_report(state.get("verification_plan")),
        "phase_3_rounds": _compact_audit_rounds(state.get("phase_3_rounds")),
        "phase_5_rounds": _compact_audit_rounds(state.get("phase_5_rounds")),
        "phase_3_residual_risks": _clip_for_report(state.get("phase_3_residual_risks")),
        "phase_5_residual_risks": _clip_for_report(state.get("phase_5_residual_risks")),
        "meta_categories": state.get("meta_categories"),
        "meta_domains": state.get("meta_domains"),
    }
    return summary


def _clip_for_report(value, *, max_str: int = 180, max_list_items: int = 6):
    """Bound report-render payload size while preserving structure.

    Phase 7 is a synthesis step, not a raw transcript archive. Large LLM prose
    fields from earlier phases can push the report prompt past 100K characters
    and make the SDK transport fragile. Clip individual leaves with explicit
    markers so the generated report does not pretend it saw hidden text.
    """
    if isinstance(value, str):
        if len(value) <= max_str:
            return value
        omitted = len(value) - max_str
        return value[:max_str] + f"\n[... clipped {omitted} chars for report render ...]"
    if isinstance(value, list):
        clipped = [
            _clip_for_report(item, max_str=max_str, max_list_items=max_list_items)
            for item in value[:max_list_items]
        ]
        if len(value) > max_list_items:
            clipped.append({"_clipped_items": len(value) - max_list_items})
        return clipped
    if isinstance(value, dict):
        return {
            k: _clip_for_report(v, max_str=max_str, max_list_items=max_list_items)
            for k, v in value.items()
        }
    return value


def _compact_audit_rounds(rounds):
    if not isinstance(rounds, list):
        return rounds
    compact = []
    for audit in rounds:
        if not isinstance(audit, dict):
            compact.append(_clip_for_report(audit))
            continue
        weaknesses = audit.get("weaknesses", []) or []
        residual_count = sum(
            1 for w in weaknesses
            if isinstance(w, dict) and w.get("classification") == "RESIDUAL"
        )
        addressable_count = sum(
            1 for w in weaknesses
            if isinstance(w, dict) and w.get("classification") == "ADDRESSABLE"
        )
        compact.append({
            "round": audit.get("round"),
            "verdict": audit.get("verdict"),
            "_fallback": audit.get("_fallback"),
            "weakness_count": len(weaknesses),
            "residual_count": residual_count,
            "addressable_count": addressable_count,
            "sample_weaknesses": _clip_for_report(weaknesses[:2], max_str=180, max_list_items=2),
        })
    return compact


def _run_closure_audit(state: dict) -> dict:
    """Closure audit matches the new action shape:
      - Corrective only for Q1+Q2 (TRC)
      - Prevention only for Q3+Q4 (MRC)
      - Proof of action covers all 4 quadrants in verification_plan
    """
    from ai_escape_mrc.state import active_quadrants

    # When the incident-class router set mrc_applicable=False, the MRC quadrants
    # are intentionally absent (corrective-only run). The closure audit must
    # expect only the ACTIVE quadrants, otherwise a correct corrective-only run
    # would be flagged incomplete.
    expected_q = active_quadrants(state)
    mrc_active = "q3_mrc_nc" in expected_q

    checks = {
        "root_cause_matrix_complete": all(
            q in state.get("why_chains", {}) for q in expected_q
        ),
        "corrective_q1_q2_present": all(
            q in state.get("corrective_actions", {}) for q in
            ["q1_trc_nc", "q2_trc_nd"]
        ),
        "prevention_q3_q4_present": (
            all(q in state.get("prevention_actions", {}) for q in ["q3_mrc_nc", "q4_mrc_nd"])
            if mrc_active else True  # MRC N/A: prevention intentionally absent
        ),
        "verification_plan_present": bool(state.get("verification_plan")),
        "phase_3_done": state.get("phase_3_complete") is True,
        "phase_5_done": state.get("phase_5_complete") is True,
    }
    checks["overall_pass"] = all(checks.values())
    return checks
