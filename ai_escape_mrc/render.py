# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: Phase 10 gate emission must be deterministic — never depend on LLM output.
#   The render helper builds a minimal plan header from structured action data alone,
#   so gate-file writing can succeed even when call_claude() is unavailable or fails.
# WIKI-ACTION: render_plan_header() is pure-Python with no LLM dependency; used as
#   a fallback header source in test assertions to prove Phase 10 independence.
"""Deterministic plan rendering helpers — no LLM dependency.

These utilities produce plan.md skeleton content from structured action dicts.
Phase 10 (gate-file emission) must remain independent of Phase 9's LLM call quality;
render_plan_header() makes that invariant testable.

WIKI-EXEMPT: silent-staleness — this module has no staleness surface (pure computation).
"""
from __future__ import annotations

import re
from typing import Any, Sequence

_QUADRANTS = ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
_CORRECTIVE_Q = {"q1_trc_nc", "q2_trc_nd"}
_PREVENTION_Q = {"q3_mrc_nc", "q4_mrc_nd"}
_URL_RE = re.compile(r"https?://[^\s)\]\"'>]+")


def render_plan_header(actions: Sequence[dict], topic: str = "") -> str:
    """Build a minimal plan Markdown header from action dicts — no LLM call.

    Produces the `# <topic> Implementation Plan` header plus one `## Task N:` line
    per action.  Intended as a deterministic fallback / skeleton renderer for tests
    and as proof that gate-file emission does not require LLM output.

    Args:
        actions: Sequence of action dicts with at least a ``title`` key.
        topic: Human-readable topic string for the plan header.

    Returns:
        A Markdown string suitable as a minimal plan.md skeleton.
    """
    header = f"# {topic or 'Implementation'} Plan\n\n"
    if not actions:
        header += "_No actions provided._\n"
        return header
    lines = []
    for idx, action in enumerate(actions, start=1):
        title = action.get("title") or f"Action {idx}"
        lines.append(f"## Task {idx}: {title}\n")
        desc = action.get("description", "")
        if desc:
            lines.append(f"{desc}\n")
        files = action.get("files_touched") or []
        if files:
            joined = ", ".join(str(f) for f in files)
            lines.append(f"**Files:** {joined}\n")
        lines.append("")
    return header + "\n".join(lines)


# --------------------------------------------------------------------------- #
# Deterministic report rendering (no LLM, faithful to full state)
# --------------------------------------------------------------------------- #

def _cell(value: Any, limit: int = 240) -> str:
    """Flatten a value into a single Markdown table cell."""
    s = str(value if value not in (None, "") else "—")
    s = s.replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()
    return (s[: limit - 1] + "…") if len(s) > limit else s


def _action_text(actions: dict, q: str) -> str:
    a = (actions or {}).get(q)
    if isinstance(a, dict):
        return a.get("action") or a.get("title") or a.get("description") or "—"
    if isinstance(a, str):
        return a
    return "—"


def _verif_map(vplan: Any) -> dict:
    if isinstance(vplan, dict):
        items = vplan.get("quadrants") or []
    elif isinstance(vplan, list):
        items = vplan
    else:
        items = []
    out = {}
    for it in items:
        if isinstance(it, dict) and it.get("quadrant"):
            out[it["quadrant"]] = it
    return out


def _render_is_isnt(tbl: Any) -> str:
    if not isinstance(tbl, dict):
        return "_(not available)_"
    rows = ["| Dimension | IS | IS NOT | Distinction |", "|---|---|---|---|"]
    for dim in ("what", "where", "when", "extent"):
        d = tbl.get(dim) or {}
        if not isinstance(d, dict):
            continue
        rows.append(f"| **{dim}** | {_cell(d.get('is'))} | {_cell(d.get('is_not'))} | {_cell(d.get('distinction'))} |")
    return "\n".join(rows)


def _render_why_chains(chains: Any) -> str:
    if not isinstance(chains, dict):
        return "_(not available)_"
    out = []
    for q in _QUADRANTS:
        chain = chains.get(q)
        if not isinstance(chain, dict):
            continue
        out.append(f"### {q}")
        for why in chain.get("whys", []) or []:
            if not isinstance(why, dict):
                continue
            line = f"{why.get('n', '?')}. {why.get('why', '')}"
            if why.get("new_insight"):
                line += f"\n   - _insight:_ {why['new_insight']}"
            for note in why.get("audit_notes", []) or []:
                if note:
                    line += f"\n   - _audit note:_ {note}"
            out.append(line)
        out.append(f"\n**Root cause:** {chain.get('root', '—')}\n")
    return "\n".join(out) if out else "_(not available)_"


def _render_audit_rounds(rounds: Any) -> str:
    if not isinstance(rounds, list) or not rounds:
        return "_(no audit rounds recorded)_"
    out = []
    for audit in rounds:
        if not isinstance(audit, dict):
            continue
        tag = " _(fallback)_" if audit.get("_fallback") else ""
        out.append(f"### Round {audit.get('round', '?')} — verdict: {audit.get('verdict', '?')}{tag}")
        weaknesses = audit.get("weaknesses", []) or []
        if not weaknesses:
            out.append("- _(no weaknesses surfaced)_")
        for w in weaknesses:
            if not isinstance(w, dict):
                continue
            cls = w.get("classification", "?")
            q = w.get("quadrant", "?")
            step = w.get("why_step_n")
            head = f"- **{cls}** [{q}{f' / why {step}' if step is not None else ''}]: {w.get('issue', '')}"
            out.append(head)
            if w.get("suggested_fix"):
                out.append(f"  - fix: {w['suggested_fix']}")
            if w.get("evidence"):
                out.append(f"  - evidence: {w['evidence']}")
        out.append("")
    return "\n".join(out)


def _render_phase_4(corrective: dict, prevention: dict) -> str:
    out = []
    for q in _QUADRANTS:
        out.append(f"### {q}")
        if q in _CORRECTIVE_Q:
            a = (corrective or {}).get(q)
            if isinstance(a, dict):
                out.append(f"- **Corrective:** {a.get('action', '—')}")
                for k in ("rationale", "owner", "target_date", "evidence_of_completion"):
                    if a.get(k):
                        out.append(f"  - {k}: {a[k]}")
            else:
                out.append("- **Corrective:** —")
        if q in _PREVENTION_Q:
            a = (prevention or {}).get(q)
            if isinstance(a, dict):
                out.append(f"- **Prevention:** {a.get('action', '—')}")
                gt = a.get("gate_test") or {}
                if isinstance(gt, dict):
                    for dim in ("scope", "persistence", "measurability"):
                        out.append(f"  - {dim}: {gt.get(dim, '?')} — {gt.get(dim + '_evidence', '')}")
                for k in ("hierarchy_level", "failure_mode_of_prevention", "deployment_scope", "scope_justification"):
                    if a.get(k) not in (None, ""):
                        out.append(f"  - {k}: {a[k]}")
            else:
                out.append("- **Prevention:** —")
        out.append("")
    return "\n".join(out)


def _render_phase_6(vplan: Any) -> str:
    vmap = _verif_map(vplan)
    if not vmap:
        return "_(not available)_"
    out = []
    for q in _QUADRANTS:
        it = vmap.get(q)
        if not isinstance(it, dict):
            continue
        out.append(f"### {q} ({it.get('action_type', '?')})")
        for k in ("metric", "data_source", "target", "baseline", "measurement_schedule", "failure_response"):
            if it.get(k):
                out.append(f"- {k}: {it[k]}")
        out.append("")
    if isinstance(vplan, dict) and vplan.get("overall_timeframe"):
        out.append(f"**Overall timeframe:** {vplan['overall_timeframe']}")
    return "\n".join(out)


def _render_citations(state: dict) -> str:
    urls: list[str] = []
    seen = set()

    def _harvest(text: str):
        for u in _URL_RE.findall(text or ""):
            u = u.rstrip(".,;")
            if u not in seen:
                seen.add(u)
                urls.append(u)

    for rounds_key in ("phase_3_rounds", "phase_5_rounds"):
        for audit in state.get(rounds_key, []) or []:
            if isinstance(audit, dict):
                for w in audit.get("weaknesses", []) or []:
                    if isinstance(w, dict):
                        _harvest(str(w.get("evidence", "")))
    for ws_key in ("websearch_specific", "websearch_meta", "websearch_cross_domain"):
        for res in state.get(ws_key, []) or []:
            if isinstance(res, dict):
                _harvest(str(res.get("results", "")))
    if not urls:
        return "_(no external citations retrieved)_"
    return "\n".join(f"- {u}" for u in urls)


def _render_closure(closure: Any) -> str:
    if not isinstance(closure, dict):
        return "_(not available)_"
    checks = closure.get("checks") if isinstance(closure.get("checks"), dict) else closure
    out = []
    for name, ok in checks.items():
        if isinstance(ok, bool):
            out.append(f"- {'✅' if ok else '❌'} {name}")
    return "\n".join(out) if out else "_(no closure checks recorded)_"


def render_report(state: dict, template: str, closure: Any = None) -> str:
    """Render the full AI Escape MRC report deterministically from state.

    No LLM call: every template placeholder is filled from the (un-clipped)
    structured phase outputs, so the report is faithful, complete, fast, and
    cannot time out. ``closure`` is the dict from phase_7's closure audit.
    """
    from datetime import datetime
    from ai_escape_mrc.utils import sluggify

    chains = state.get("why_chains") or {}
    corrective = state.get("corrective_actions") or {}
    prevention = state.get("prevention_actions") or {}
    vmap = _verif_map(state.get("verification_plan"))

    def root(q):
        c = chains.get(q)
        return _cell(c.get("root")) if isinstance(c, dict) else "—"

    def metric(q):
        it = vmap.get(q)
        return _cell(it.get("metric")) if isinstance(it, dict) else "—"

    def target(q):
        it = vmap.get(q)
        return _cell(it.get("target")) if isinstance(it, dict) else "—"

    repl = {
        "{problem_slug}": sluggify(state.get("problem", "")),
        "{date}": datetime.now().strftime("%Y-%m-%d"),
        "{problem}": str(state.get("problem", "")),
        "{run_id}": str(state.get("run_id", "")),
        "{q1_trc_nc_root}": root("q1_trc_nc"),
        "{q2_trc_nd_root}": root("q2_trc_nd"),
        "{q3_mrc_nc_root}": root("q3_mrc_nc"),
        "{q4_mrc_nd_root}": root("q4_mrc_nd"),
        "{q1_corrective}": _cell(_action_text(corrective, "q1_trc_nc")),
        "{q2_corrective}": _cell(_action_text(corrective, "q2_trc_nd")),
        "{q3_corrective}": "— (MRC: prevention-only)",
        "{q4_corrective}": "— (MRC: prevention-only)",
        "{q1_prevention}": "— (TRC: corrective-only)",
        "{q2_prevention}": "— (TRC: corrective-only)",
        "{q3_prevention}": _cell(_action_text(prevention, "q3_mrc_nc")),
        "{q4_prevention}": _cell(_action_text(prevention, "q4_mrc_nd")),
        "{q1_metric}": metric("q1_trc_nc"), "{q1_target}": target("q1_trc_nc"),
        "{q2_metric}": metric("q2_trc_nd"), "{q2_target}": target("q2_trc_nd"),
        "{q3_metric}": metric("q3_mrc_nc"), "{q3_target}": target("q3_mrc_nc"),
        "{q4_metric}": metric("q4_mrc_nd"), "{q4_target}": target("q4_mrc_nd"),
        "{is_isnt_table_rendered}": _render_is_isnt(state.get("is_isnt_table")),
        "{why_chains_rendered}": _render_why_chains(chains),
        "{phase_3_rounds_rendered}": _render_audit_rounds(state.get("phase_3_rounds")),
        "{phase_4_rendered}": _render_phase_4(corrective, prevention),
        "{phase_5_rounds_rendered}": _render_audit_rounds(state.get("phase_5_rounds")),
        "{phase_6_rendered}": _render_phase_6(state.get("verification_plan")),
        "{soa_citations_rendered}": _render_citations(state),
        "{closure_audit_rendered}": _render_closure(closure),
        "{wiki_ingest_drafts_rendered}": "_(none)_",
    }
    out = template
    for k, v in repl.items():
        out = out.replace(k, v)
    return out
