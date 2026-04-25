"""Phase 7: render report + closure audit + email delivery."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from eightd.sdk_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt, sluggify
from eightd.delivery.email import send_8d_report_email

URL_RE = re.compile(r"https?://[^\s)\"']+")


def phase_7_report(state: dict) -> dict:
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

    try:
        log = send_8d_report_email(
            report_md=rendered,
            report_path=canonical,
            problem_summary=state["problem"][:200],
        )
        state["email_sent"] = True
        state["email_delivery_log"] = log
    except Exception as e:
        state["email_sent"] = False
        state["email_delivery_log"] = f"FAIL: {type(e).__name__}: {e}"

    state["phase_7_complete"] = True
    return state


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
