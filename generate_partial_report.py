"""Emergency partial report generator from checkpoint state.

Extracts state from runs/<id>/checkpoint.db and produces a full-detail
markdown 8D report. Skips phases 6 and 7 (never reached due to Phase 5
AttributeError bug in prior run). Includes:
- Phase 0 research dump
- Phase 1 IS/IS NOT
- Phase 2 Why chains (full)
- Phase 3 audit rounds (full)
- Phase 4 corrective + prevention actions (full)
- Phase 5 partial (1 round only)
- Pipeline timeline from progress.jsonl
- SoA citations deduplicated

Also sends email via Outlook COM.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r"D:/D-claude/skills/skill-8d-mrc")
from langgraph.checkpoint.sqlite import SqliteSaver
from eightd.delivery.email import send_8d_report_email
from eightd.utils import sluggify


def extract_state(run_dir: Path) -> dict:
    db = str(run_dir / "checkpoint.db")
    thread_id = run_dir.name
    with SqliteSaver.from_conn_string(db) as s:
        cfg = {"configurable": {"thread_id": thread_id}}
        ckpt = s.get_tuple(cfg)
        if ckpt is None:
            raise RuntimeError("No checkpoint found")
        return ckpt.checkpoint.get("channel_values", {})


def load_progress(run_dir: Path) -> list[dict]:
    p = run_dir / "progress.jsonl"
    if not p.exists():
        return []
    events = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events


def collect_soa_urls(state: dict) -> set:
    import re
    URL = re.compile(r"https?://[^\s)\"'\]]+")
    urls = set()
    for key in ("phase_3_soa_research", "phase_5_soa_research", "phase_7_soa_research"):
        for entry in state.get(key, []) or []:
            urls.update(URL.findall(str(entry.get("results", ""))))
    return urls


def render_report(state: dict, events: list[dict]) -> str:
    problem = state.get("problem", "")
    run_id = state.get("run_id", "")
    date = datetime.now().isoformat()
    total_sec = events[-1]["total_elapsed_sec"] if events else 0

    lines = []
    lines.append(f"# 8D Report (PARTIAL — pipeline crashed at Phase 5 run 2): {problem[:80]}")
    lines.append("")
    lines.append(f"**Date**: {date}")
    lines.append(f"**Problem**: {problem}")
    lines.append(f"**Run ID**: {run_id}")
    lines.append(f"**Total elapsed**: {total_sec/60:.1f} min")
    lines.append(f"**Model**: claude-opus-4-6 (via claude CLI / OpenRouter fallback)")
    lines.append("")
    lines.append("**Status**: Phases 0-4 complete. Phase 5 audit crashed (AttributeError: 'list' object has no attribute 'get') on attempt 2. Phases 6-7 not reached. This report is extracted directly from checkpoint state.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Pipeline timeline
    lines.append("## Pipeline Timeline")
    lines.append("")
    lines.append("| Phase | Start (s) | End (s) | Duration (min) |")
    lines.append("|-------|-----------|---------|----------------|")
    phase_starts = {}
    for e in events:
        if e.get("event") == "phase_start":
            phase_starts[e["phase"]] = e["total_elapsed_sec"]
        elif e.get("event") == "phase_end":
            start = phase_starts.get(e["phase"])
            if start is not None:
                dur = (e["total_elapsed_sec"] - start) / 60
                lines.append(f"| {e['phase']} | {start:.1f} | {e['total_elapsed_sec']:.1f} | {dur:.2f} |")
    lines.append("")

    # Meta categories
    cats = state.get("meta_categories", []) or []
    domains = state.get("meta_domains", []) or []
    lines.append("## Phase 0: Meta-Categorization")
    lines.append("")
    lines.append(f"**Meta categories identified**: {', '.join(cats)}")
    lines.append(f"**Cross-pollination domains**: {', '.join(domains)}")
    lines.append(f"**Wiki pages consulted**: {len(state.get('wiki_pages', []) or [])}")
    lines.append(f"**Memory entries (feedback_*.md)**: {len(state.get('memory_entries', []) or [])}")
    lines.append("")

    # Section A: Root Cause Matrix
    why_chains = state.get("why_chains", {}) or {}
    lines.append("## Section A: Root Cause Matrix")
    lines.append("")
    lines.append("| | Non-Conformance (NC) | Non-Detection (ND) |")
    lines.append("|---|---|---|")
    q1 = why_chains.get("q1_trc_nc", {}).get("root", "—")[:150]
    q2 = why_chains.get("q2_trc_nd", {}).get("root", "—")[:150]
    q3 = why_chains.get("q3_mrc_nc", {}).get("root", "—")[:150]
    q4 = why_chains.get("q4_mrc_nd", {}).get("root", "—")[:150]
    lines.append(f"| **TRC** | Q1: {q1} | Q2: {q2} |")
    lines.append(f"| **MRC** | Q3: {q3} | Q4: {q4} |")
    lines.append("")

    # Section B: Corrective Actions
    corrective = state.get("corrective_actions", {}) or {}
    lines.append("## Section B: Corrective Actions Matrix")
    lines.append("")
    lines.append("| | NC | ND |")
    lines.append("|---|---|---|")
    c1 = str(corrective.get("q1_trc_nc", {}).get("action", "—") if isinstance(corrective.get("q1_trc_nc"), dict) else corrective.get("q1_trc_nc", "—"))[:150]
    c2 = str(corrective.get("q2_trc_nd", {}).get("action", "—") if isinstance(corrective.get("q2_trc_nd"), dict) else corrective.get("q2_trc_nd", "—"))[:150]
    c3 = str(corrective.get("q3_mrc_nc", {}).get("action", "—") if isinstance(corrective.get("q3_mrc_nc"), dict) else corrective.get("q3_mrc_nc", "—"))[:150]
    c4 = str(corrective.get("q4_mrc_nd", {}).get("action", "—") if isinstance(corrective.get("q4_mrc_nd"), dict) else corrective.get("q4_mrc_nd", "—"))[:150]
    lines.append(f"| **TRC** | Q1: {c1} | Q2: {c2} |")
    lines.append(f"| **MRC** | Q3: {c3} | Q4: {c4} |")
    lines.append("")

    # Section B2: Prevention Actions
    prevention = state.get("prevention_actions", {}) or {}
    lines.append("## Section B2: Prevention Actions Matrix")
    lines.append("")
    lines.append("| | NC | ND |")
    lines.append("|---|---|---|")
    def p_action(q):
        pq = prevention.get(q, {})
        if isinstance(pq, list):
            pq = pq[0] if pq else {}
        if isinstance(pq, dict):
            return str(pq.get("action", "—"))[:150]
        return str(pq)[:150]
    lines.append(f"| **TRC** | Q1: {p_action('q1_trc_nc')} | Q2: {p_action('q2_trc_nd')} |")
    lines.append(f"| **MRC** | Q3: {p_action('q3_mrc_nc')} | Q4: {p_action('q4_mrc_nd')} |")
    lines.append("")

    # IS/IS NOT
    is_isnt = state.get("is_isnt_table", {}) or {}
    lines.append("## Phase 1: IS / IS NOT")
    lines.append("")
    lines.append("| Dimension | IS | IS NOT | Distinction |")
    lines.append("|-----------|-----|--------|-------------|")
    for dim in ("what", "where", "when", "extent"):
        row = is_isnt.get(dim, {})
        if isinstance(row, dict):
            lines.append(f"| **{dim.upper()}** | {str(row.get('is',''))[:200]} | {str(row.get('is_not',''))[:200]} | {str(row.get('distinction',''))[:200]} |")
    lines.append("")

    # Why chains full
    lines.append("## Phase 2: Why Chains (FULL)")
    lines.append("")
    for q_key in ("q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"):
        chain = why_chains.get(q_key, {})
        if not isinstance(chain, dict):
            continue
        whys = chain.get("whys", [])
        lines.append(f"### Quadrant {q_key}")
        lines.append("")
        for i, why in enumerate(whys, 1):
            if isinstance(why, dict):
                lines.append(f"{i}. **Why {why.get('n', i)}**: {why.get('why', '')}")
                if why.get("new_insight"):
                    lines.append(f"   - *New insight*: {why['new_insight']}")
        lines.append("")
        lines.append(f"**Root**: {chain.get('root', '—')}")
        lines.append("")

    # Phase 3 audit rounds
    lines.append("## Phase 3: RC Audit Rounds (FULL)")
    lines.append("")
    for i, r in enumerate(state.get("phase_3_rounds", []) or [], 1):
        lines.append(f"### Audit round {i}")
        lines.append(f"- **Verdict**: `{r.get('verdict')}`")
        if r.get("_citation_check"):
            lines.append(f"- **Citation check**: `{r.get('_citation_check')}`")
        if r.get("rejection_reason"):
            lines.append(f"- **Rejection reason**: {r.get('rejection_reason')}")
        if r.get("_force_accepted_reason"):
            lines.append(f"- **Force-accepted**: {r.get('_force_accepted_reason')}")
        weaknesses = r.get("weaknesses", [])
        if weaknesses:
            lines.append(f"- **Weaknesses found**: {len(weaknesses)}")
            for j, w in enumerate(weaknesses[:5], 1):
                if isinstance(w, dict):
                    lines.append(f"  {j}. [{w.get('classification','?')}] {w.get('quadrant','?')} why_{w.get('why_step_n','?')}: {str(w.get('issue',''))[:150]}")
                    if w.get("suggested_fix"):
                        lines.append(f"     - Fix: {str(w.get('suggested_fix',''))[:150]}")
        citations = r.get("soa_citations_used", [])
        if citations:
            lines.append(f"- **SoA citations used**: {', '.join(citations[:3])}")
        lines.append("")

    # Phase 4 full actions
    lines.append("## Phase 4: Full Actions per Quadrant")
    lines.append("")
    for q_key in ("q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"):
        lines.append(f"### Quadrant {q_key}")
        cor = corrective.get(q_key, {})
        if isinstance(cor, dict):
            lines.append("**Corrective**:")
            for k in ("action", "rationale", "owner", "target_date", "evidence_of_completion"):
                if cor.get(k):
                    lines.append(f"- *{k}*: {str(cor[k])[:300]}")
        prev = prevention.get(q_key, {})
        if isinstance(prev, list):
            prev = prev[0] if prev else {}
        if isinstance(prev, dict):
            lines.append("")
            lines.append("**Prevention**:")
            for k in ("action", "hierarchy_level", "failure_mode_of_prevention", "deployment_scope", "scope_justification"):
                if prev.get(k) is not None:
                    lines.append(f"- *{k}*: {str(prev[k])[:300]}")
            gate = prev.get("gate_test")
            if isinstance(gate, dict):
                lines.append(f"- *gate_test*: scope={gate.get('scope')}, persistence={gate.get('persistence')}, measurability={gate.get('measurability')}")
        lines.append("")

    # Phase 5 partial
    p5r = state.get("phase_5_rounds", []) or []
    if p5r:
        lines.append("## Phase 5: Prevention Audit (PARTIAL — 1 round before crash)")
        lines.append("")
        for i, r in enumerate(p5r, 1):
            if isinstance(r, dict):
                lines.append(f"### Round {i}")
                lines.append(f"- **Verdict**: `{r.get('verdict')}`")
                if r.get("stronger_alternatives_found_in_soa"):
                    lines.append(f"- **Stronger alternatives in SoA**: {r['stronger_alternatives_found_in_soa'][:3]}")
                lines.append("")

    # SoA citations
    urls = collect_soa_urls(state)
    if urls:
        lines.append("## SoA Citations (deduplicated)")
        lines.append("")
        for u in sorted(urls)[:30]:
            lines.append(f"- {u}")
        lines.append("")

    # Closing
    lines.append("## Status + known limitations")
    lines.append("")
    lines.append("- **Phases completed**: 0, 1, 2, 3 (3 audit loops to force-accept), 4")
    lines.append("- **Phases crashed**: 5 (AttributeError — 'list' object has no attribute 'get' on audit's attempt to modify prevention_actions[q])")
    lines.append("- **Phases not reached**: 6 (Proof of Action), 7 (Report rendering + closure audit)")
    lines.append(f"- **Total elapsed**: {total_sec/60:.1f} min")
    lines.append("- **Bug discovered**: prevention_actions[q] is sometimes a list, not a dict, from the LLM output; audit's `.setdefault('audit_notes', [])` call fails on list. Fix: normalize list-wrapped dicts in phase_4 or guard in phase_5 audit.")
    lines.append("")

    return "\n".join(lines)


def _resend_existing(report_path: Path) -> None:
    """Read an existing report from disk and re-deliver via send_8d_report_email.

    Skips checkpoint extraction + markdown regeneration. Used after a prior
    run already produced a report but delivery failed.
    """
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")
    report_md = report_path.read_text(encoding="utf-8")
    # Derive a short problem summary from the first H1 heading
    first_line = next(
        (ln for ln in report_md.splitlines() if ln.startswith("# ")),
        "8D Report",
    )
    problem_summary = first_line.lstrip("# ").strip()[:200]
    print(f"Resending existing report: {report_path} ({report_path.stat().st_size} bytes)")
    try:
        log = send_8d_report_email(report_md, report_path, problem_summary)
        print(f"Email: {log}")
    except Exception as e:
        print(f"Email FAIL: {e}")
        raise


def main():
    args = sys.argv[1:]

    # --resend <report_path> mode
    if args and args[0] == "--resend":
        if len(args) < 2:
            print("Usage: generate_partial_report.py --resend <report_path>")
            sys.exit(2)
        _resend_existing(Path(args[1]))
        return

    if not args:
        # Auto-detect latest run
        runs_dir = Path(r"D:/D-claude/skills/skill-8d-mrc/runs")
        latest = max(
            (r for r in runs_dir.iterdir() if r.is_dir() and r.name.startswith("run-")),
            key=lambda p: p.stat().st_mtime,
        )
        run_dir = latest
    else:
        run_dir = Path(args[0])

    print(f"Using run: {run_dir}")
    state = extract_state(run_dir)
    events = load_progress(run_dir)
    report_md = render_report(state, events)

    # Save report
    slug = sluggify(state.get("problem", "unknown"))
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = Path(os.environ.get("CLAUDE_EIGHTD_REPORTS_DIR", r"D:/D-claude/skills/skill-8d-mrc/docs/8d-reports")) / f"8d-{date_str}-{slug}-partial.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")
    print(f"Report written to: {out_path}")

    # Send email
    try:
        log = send_8d_report_email(report_md, out_path, state.get("problem", "")[:200])
        print(f"Email: {log}")
    except Exception as e:
        print(f"Email FAIL: {e}")

    print(out_path)


if __name__ == "__main__":
    main()
