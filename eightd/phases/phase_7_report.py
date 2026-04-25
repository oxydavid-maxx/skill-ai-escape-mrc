"""Phase 7: render report + closure audit + email delivery."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from eightd.sdk_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt, sluggify
URL_RE = re.compile(r"https?://[^\s)\"']+")


class PrerequisiteRefusedError(RuntimeError):
    """Phase 7 refused to emit because a prior phase did not pass.

    Raised when phase_3_status or phase_5_status is anything other than
    'passed'. Catches the ecosystem-wide degraded-emission-with-warning
    anti-pattern at its source — instead of emitting a report containing
    'EXHAUSTED with fallback' / 'no citations were retrieved', we refuse
    to emit and surface the structural failure to the operator.

    Bypass: set EIGHTD_EMIT_DESPITE_FAILED_AUDITS=1 with explicit reason
    captured in EIGHTD_EMIT_DESPITE_FAILED_AUDITS_REASON.
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
    #   8D 2026-04-25 (run-1777092777-6e277c0c), Section B Q1 corrective:
    #   Phase 7 must predicate emission on `phase_N.status == 'passed'`.
    # WIKI-ACTION: hard-gate emission. Refuse to emit (raise) if any required
    #   phase has status != 'passed'. Operator-side EXEMPT via env var, with
    #   reason captured for audit trail.
    _assert_emission_prerequisites(state)
    rendered = _render_report(state)

    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    run_report = run_dir / "report.md"
    run_report.write_text(rendered, encoding="utf-8")

    canonical = _canonical_report_path(state)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(rendered, encoding="utf-8")
    state["report_path"] = str(canonical)

    state["closure_audit"] = _run_closure_audit(state)

    # Email-send migrated to phase_10_emit_and_wait per spec
    # 2026-04-25-sdk-auto-dispatch-design.md (single consolidated email
    # with report + plan + approval portal).
    # Per function-replacement-convention wiki: WIKI-CONSULTED: function-replacement-convention
    # WIKI-FINDING: "later means never" — coexistence creates dual-function silent failure.
    # WIKI-ACTION: email-send removed here in same commit as phase_10 wiring (no dual-emission window).

    state["phase_7_complete"] = True
    return state


def _assert_emission_prerequisites(state: dict) -> None:
    """Refuse to emit a report when prior audit phases are not 'passed'.

    # WIKI-CONSULTED: silent-staleness#data-level-freshness-check
    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-CONSULTED: function-replacement-convention
    # WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
    # WIKI-FINDING: silent-staleness pattern says 'Data fetch fails → fallback
    #   to cache → build output from stale data → user trusts output → makes
    #   decisions on outdated information'. Phase 7's prior 'always emit' code
    #   was the same anti-pattern at LLM-output level: audit fails → fallback
    #   verdict → build report from incomplete state → user trusts report →
    #   acts on a degraded forensic. Per the wiki page, the fix is to refuse
    #   emission rather than to ship with a warning.
    # WIKI-ACTION: hard-gate emission. Refuse to emit (raise) if any required
    #   phase has status != 'passed'. Operator-side EXEMPT via env var, with
    #   reason captured for audit trail (per feature-flag emergency-bypass
    #   pattern: kill-switch is permanent, defaults to enforced, requires
    #   explicit operator action with documented reason to bypass).

    Implements the Q1 corrective from ecosystem 8D 2026-04-25
    (run-1777092777-6e277c0c). The earlier silent-emission failure mode
    let Phase 7 produce reports on top of fallback audits, with the
    failure smuggled into the report as a self-exonerating warning sentence.
    This refuses at the structural boundary instead.
    """
    bypass = os.environ.get("EIGHTD_EMIT_DESPITE_FAILED_AUDITS") == "1"
    bypass_reason = os.environ.get("EIGHTD_EMIT_DESPITE_FAILED_AUDITS_REASON", "")

    failed: list[str] = []
    for phase_key in ("phase_3_status", "phase_5_status"):
        status = state.get(phase_key)
        if status is None:
            # Older runs / partial state lack the field; treat as legacy and
            # allow (those runs predate the corrective). Tag for the operator.
            state.setdefault("phase_7_legacy_emission", []).append(
                f"{phase_key} missing (pre-2026-04-25 run)"
            )
            continue
        if status != "passed":
            failed.append(f"{phase_key}={status}")

    if not failed:
        return

    if bypass:
        state.setdefault("phase_7_bypassed_failures", []).extend(failed)
        state["phase_7_bypass_reason"] = bypass_reason or "(no reason given)"
        import sys
        sys.stderr.write(
            f"[phase_7] WARNING: EIGHTD_EMIT_DESPITE_FAILED_AUDITS=1 set; "
            f"emitting despite {failed}. Reason: {state['phase_7_bypass_reason']}\n"
        )
        return

    raise PrerequisiteRefusedError(
        f"Refusing to emit Phase 7 report: prerequisite phase(s) did not pass: "
        f"{', '.join(failed)}. The earlier audit phase(s) used the _fallback "
        f"path (LLM error or no real audit). Per ecosystem-wide degraded-"
        f"emission-with-warning anti-pattern (8D 2026-04-25), reports must not "
        f"ship on top of failed audits with a self-exonerating warning. "
        f"Re-run the failed phase(s), or set "
        f"EIGHTD_EMIT_DESPITE_FAILED_AUDITS=1 with reason in "
        f"EIGHTD_EMIT_DESPITE_FAILED_AUDITS_REASON if you have an explicit "
        f"operator-side justification."
    )


def _canonical_report_path(state: dict) -> Path:
    slug = sluggify(state["problem"])
    date_str = datetime.now().strftime("%Y-%m-%d")
    base = os.environ.get(
        "CLAUDE_EIGHTD_REPORTS_DIR",
        "D:/D-claude/skills/skill-8d-mrc/docs/8d-reports",
    )
    return Path(base) / f"8d-{date_str}-{slug}.md"


def _render_report(state: dict) -> str:
    template_path = Path(__file__).parent.parent.parent / "templates" / "8d_report_template.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    # WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
    # WIKI-FINDING: 600s default sdk_client timeout caused every Phase 7 on a
    #   complex problem to TimeoutError after 10 min (observed 2026-04-25 on two
    #   separate runs both with 123K-token input prompts). All Phase 0-6 work is
    #   preserved in checkpoint.db but no report emitted.
    # WIKI-ACTION: pass timeout_sec=1800 (30 min) for the report-render call. Matches
    #   Anthropic API docs' 60-min inference default, halved for earlier stall signal.
    #   Other phases still use the 600s default from sdk_client.call_claude.
    rendered = call_claude(
        model=model_for_role("report_generation"),
        system=load_prompt("report_render") + "\n\nTemplate to follow:\n" + template,
        user=json.dumps(_state_summary(state), ensure_ascii=False),
        max_tokens=8000,
        purpose="phase_7_report_render",
        timeout_sec=1800,
    )
    return rendered


def _state_summary(state: dict) -> dict:
    """Minimal state summary for report render. Does NOT include progress
    events (bloats prompt to 30-50K chars for no real value — the report
    should document decisions, not a replay of JSONL events)."""
    return {
        "problem": state.get("problem"),
        "run_id": state.get("run_id"),
        "date": datetime.now().isoformat(),
        "is_isnt_table": state.get("is_isnt_table"),
        "why_chains": state.get("why_chains"),
        "corrective_actions": state.get("corrective_actions"),
        "prevention_actions": state.get("prevention_actions"),
        "verification_plan": state.get("verification_plan"),
        "phase_3_rounds": state.get("phase_3_rounds"),
        "phase_5_rounds": state.get("phase_5_rounds"),
        "phase_3_residual_risks": state.get("phase_3_residual_risks"),
        "phase_5_residual_risks": state.get("phase_5_residual_risks"),
        "meta_categories": state.get("meta_categories"),
        "meta_domains": state.get("meta_domains"),
    }


def _run_closure_audit(state: dict) -> dict:
    """Closure audit matches the new action shape:
      - Corrective only for Q1+Q2 (TRC)
      - Prevention only for Q3+Q4 (MRC)
      - Proof of action covers all 4 quadrants in verification_plan
    """
    checks = {
        "root_cause_matrix_complete": all(
            q in state.get("why_chains", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "corrective_q1_q2_present": all(
            q in state.get("corrective_actions", {}) for q in
            ["q1_trc_nc", "q2_trc_nd"]
        ),
        "prevention_q3_q4_present": all(
            q in state.get("prevention_actions", {}) for q in
            ["q3_mrc_nc", "q4_mrc_nd"]
        ),
        "verification_plan_present": bool(state.get("verification_plan")),
        "phase_3_done": state.get("phase_3_complete") is True,
        "phase_5_done": state.get("phase_5_complete") is True,
    }
    checks["overall_pass"] = all(checks.values())
    return checks
