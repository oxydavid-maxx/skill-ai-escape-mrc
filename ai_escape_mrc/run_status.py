"""Status reader for AI Escape MRC run artifacts."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ai_escape_mrc.stage_summary import PHASE_TITLES


def status_for_run(identifier: str, *, default_runs_dir: Path | None = None) -> dict[str, Any]:
    """Return a JSON-serializable status snapshot for a run id or run directory."""
    run_dir = resolve_run_dir(identifier, default_runs_dir=default_runs_dir)
    if run_dir is None:
        return {
            "exists": False,
            "run_id": Path(identifier).name,
            "run_dir": str(identifier),
            "status": "not_found",
            "human_summary": f"AI Escape MRC run not found: {identifier}",
        }

    events = _read_jsonl(run_dir / "progress.jsonl")
    summaries = _read_jsonl(run_dir / "stage-summaries.jsonl")
    progress_entries = _read_jsonl(run_dir / "stage-progress.jsonl")
    last_event = events[-1] if events else None
    latest_summary = summaries[-1] if summaries else None
    latest_progress = progress_entries[-1] if progress_entries else None
    delivery_status = _read_json(run_dir / "delivery-status.json")
    error = _read_json(run_dir / "run-error.json")
    current_phase = _current_phase(events)
    completed = _unique_phases([
        e.get("phase")
        for e in events
        if e.get("event") == "phase_end" and e.get("detail", {}).get("ok") is True
    ] + [
        s.get("phase")
        for s in summaries
        if s.get("kind") == "phase_summary"
    ])
    now = time.time()
    last_ts = float(last_event.get("ts", now)) if isinstance(last_event, dict) else now
    since_last = max(0.0, now - last_ts)
    active_error = _active_error(error, last_event)
    status = "error" if active_error else _status_name(current_phase, last_event)
    if not active_error and "phase_10_emit_and_wait" in completed:
        if isinstance(delivery_status, dict) and delivery_status.get("email_delivery_result") == "failed":
            status = "delivery_failed"
        else:
            status = "complete"
        current_phase = None
    human_summary = _human_summary(
        run_id=run_dir.name,
        status=status,
        current_phase=current_phase,
        last_event=last_event,
        latest_summary=latest_summary,
        latest_progress=latest_progress,
        error=active_error,
        since_last=since_last,
    )

    return {
        "exists": True,
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "status": status,
        "current_phase": current_phase,
        "current_phase_title": PHASE_TITLES.get(current_phase or "", current_phase),
        "completed_phases": completed,
        "last_event": last_event,
        "latest_progress": latest_progress,
        "error": active_error,
        "latest_summary": latest_summary,
        "elapsed_sec": _elapsed(events),
        "since_last_event_sec": round(since_last, 1),
        "stalled": since_last >= 300,
        "progress_path": str(run_dir / "progress.jsonl"),
        "stage_progress_path": str(run_dir / "stage-progress.jsonl"),
        "stage_summaries_path": str(run_dir / "stage-summaries.md"),
        "stage_summaries_jsonl_path": str(run_dir / "stage-summaries.jsonl"),
        "report_path": _maybe_path(run_dir / "report.md"),
        "plan_path": _maybe_path(run_dir / "plan.md"),
        "run_error_path": _maybe_path(run_dir / "run-error.json") if active_error else None,
        "delivery_status_path": _maybe_path(run_dir / "delivery-status.json"),
        "delivery_status": delivery_status,
        "human_summary": human_summary,
    }


def resolve_run_dir(identifier: str, *, default_runs_dir: Path | None = None) -> Path | None:
    value = Path(identifier)
    if value.exists() and value.is_dir():
        return value.resolve()

    candidates: list[Path] = []
    if default_runs_dir is not None:
        candidates.append(default_runs_dir / identifier)
    skill_runs = Path(__file__).resolve().parent.parent / "runs"
    candidates.append(skill_runs / identifier)
    codex_memories = Path.home() / ".codex" / "memories"
    if codex_memories.exists():
        candidates.extend(codex_memories.glob(f"*/runs/{identifier}"))

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"error_type": "InvalidRunErrorJson", "message": str(path)}
    return value if isinstance(value, dict) else None


def _unique_phases(values: list[Any]) -> list[str]:
    phases: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or value in seen:
            continue
        phases.append(value)
        seen.add(value)
    return phases


def _active_error(error: dict[str, Any] | None, last_event: dict[str, Any] | None) -> dict[str, Any] | None:
    if not error:
        return None
    if not last_event:
        return error
    if last_event.get("event") == "phase_error":
        return error
    error_ts = _parse_ts(error.get("ts"))
    try:
        last_ts = float(last_event.get("ts", 0))
    except (TypeError, ValueError):
        last_ts = 0.0
    return error if error_ts >= last_ts else None


def _parse_ts(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            from datetime import datetime
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
    return 0.0


def _current_phase(events: list[dict[str, Any]]) -> str | None:
    current: str | None = None
    for event in events:
        name = event.get("event")
        phase = event.get("phase")
        if name == "phase_start" and isinstance(phase, str):
            current = phase
        elif name == "phase_end" and phase == current:
            current = None
        elif name == "phase_error" and isinstance(phase, str):
            current = phase
    return current


def _status_name(current_phase: str | None, last_event: dict[str, Any] | None) -> str:
    if not last_event:
        return "starting"
    if last_event.get("event") == "phase_error":
        return "error"
    if last_event.get("event") == "phase_interrupt":
        return "awaiting_approval"
    if current_phase:
        return "running"
    if last_event.get("event") == "phase_end":
        return "between_phases"
    return "running"


def _elapsed(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.0
    last = events[-1]
    value = last.get("total_elapsed_sec")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _maybe_path(path: Path) -> str | None:
    return str(path) if path.exists() else None


def _human_summary(
    *,
    run_id: str,
    status: str,
    current_phase: str | None,
    last_event: dict[str, Any] | None,
    latest_summary: dict[str, Any] | None,
    latest_progress: dict[str, Any] | None,
    error: dict[str, Any] | None,
    since_last: float,
) -> str:
    title = PHASE_TITLES.get(current_phase or "", current_phase or "between phases")
    lines = [f"[AI Escape MRC] {run_id}", f"- Status: {status}; phase: {title}"]
    if error:
        phase = error.get("title") or error.get("phase") or title
        lines.append(f"- Failed at: {phase}")
        lines.append(f"- Error: {error.get('error_type', 'Error')}: {str(error.get('message', ''))[:180]}")
    if latest_progress:
        lines.append(f"- Progress: {latest_progress.get('message', '(unknown)')}")
    if latest_summary:
        screen = str(latest_summary.get("screen") or "").splitlines()
        if screen:
            lines.append(f"- Latest summary: {' / '.join(screen[1:4])}")
    if last_event:
        detail = last_event.get("detail") or {}
        purpose = detail.get("purpose") or detail.get("query")
        if purpose:
            lines.append(f"- Last event: {last_event.get('event')} ({str(purpose)[:100]})")
        else:
            lines.append(f"- Last event: {last_event.get('event')}")
    lines.append(f"- Last update: {round(since_last, 1)}s ago")
    return "\n".join(lines)
