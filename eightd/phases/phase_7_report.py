"""Phase 7: render report + closure audit + email delivery."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from eightd.anthropic_client import call_claude
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
        "D:/D-claude/daily_brief/docs/8d-reports",
    )
    return Path(base) / f"8d-{date_str}-{slug}.md"


def _render_report(state: dict) -> str:
    template_path = Path(__file__).parent.parent.parent / "templates" / "8d_report_template.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    rendered = call_claude(
        model=model_for_role("report_generation"),
        system=load_prompt("report_render") + "\n\nTemplate to follow:\n" + template,
        user=json.dumps(_state_summary(state), ensure_ascii=False),
        max_tokens=16000,
    )
    return rendered


def _state_summary(state: dict) -> dict:
    return {
        "problem": state.get("problem"),
        "run_id": state.get("run_id"),
        "date": datetime.now().isoformat(),
        "is_isnt_table": state.get("is_isnt_table"),
        "why_chains": state.get("why_chains"),
        "corrective_actions": state.get("corrective_actions"),
        "prevention_actions": state.get("prevention_actions"),
        "proof_of_action": state.get("proof_of_action"),
        "verification_plan": state.get("verification_plan"),
        "phase_3_rounds": state.get("phase_3_rounds"),
        "phase_5_rounds": state.get("phase_5_rounds"),
        "soa_urls_deduped": sorted(_collect_soa_urls(state)),
    }


def _collect_soa_urls(state: dict) -> set:
    urls = set()
    for key in ["phase_3_soa_research", "phase_5_soa_research", "phase_7_soa_research"]:
        for entry in state.get(key, []):
            urls.update(URL_RE.findall(entry.get("results", "")))
    return urls


def _run_closure_audit(state: dict) -> dict:
    checks = {
        "root_cause_matrix_complete": all(
            q in state.get("why_chains", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "corrective_matrix_complete": all(
            q in state.get("corrective_actions", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "proof_matrix_complete": all(
            q in state.get("proof_of_action", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "phase_3_exhausted": state.get("phase_3_verdict") == "EXHAUSTED",
        "phase_5_exhausted": state.get("phase_5_verdict") == "EXHAUSTED",
    }
    checks["overall_pass"] = all(checks.values())
    return checks
