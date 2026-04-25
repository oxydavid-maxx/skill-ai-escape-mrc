"""Heartbeat thread for long-running 8D runs.

Emits human-readable progress summaries to stderr every HEARTBEAT_INTERVAL seconds
(default 300s = 5 min). Also posts to Telegram diagnostics topic if configured.

Design motivation: progress.jsonl captures every LLM call + phase transition, but
per-event logs are noisy. User cannot tell from 100+ lines of JSON whether the run
is making progress or stuck. The heartbeat aggregates recent events into a single
line a human can read, and flags stalls where no new event arrived.

Started automatically by run_8d.py at launch. Runs as a daemon thread so it exits
with the main process when the LangGraph pipeline completes.

Persisted-requirement source: `~/.claude/feedback_skill_progress_reporting.md`
(long-running skills >10 min MUST emit human-readable progress every 5-10 min).

# WIKI-CONSULTED: silent-staleness#data-level-freshness-check
# WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
# WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
# WIKI-FINDING: silent-staleness says freshness must be derived from content, not wall
#   clock. Applied here: stall detection compares time.time() against the ts field
#   INSIDE the last progress.jsonl event (content timestamp), not against the heartbeat
#   thread's own clock. If the main process hangs and writes no events, time.time()
#   advances but event.ts does not, so the gap grows and triggers a stall warning.
# WIKI-FINDING: progress.py docstring claimed 'An external monitor can tail this file
#   to report every 10 min' - promise made, monitor never built, user was blind to
#   long-run progress. Text-only directive rot per Instruction Failure Escalation Ladder.
# WIKI-ACTION: built-in (daemon thread inside run_8d.py), not external - removes the
#   'someone will build the monitor separately' failure mode. Heartbeat starts at
#   process init and dies with the process, so it cannot be forgotten.
# WIKI-ACTION: emit destination is stderr + optional Telegram diagnostics topic -
#   reaches user both at terminal and on phone, no single point of delivery failure.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

DEFAULT_INTERVAL_SEC = 300   # 5 min
STALL_THRESHOLD_SEC = 600    # warn if no new events for 10 min


def _load_telegram_cfg() -> dict | None:
    cfg_path = Path.home() / ".claude" / "telegram.json"
    if not cfg_path.exists():
        return None
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _post_telegram(msg: str, cfg: dict) -> None:
    try:
        import requests

        token = cfg["bot_token"]
        chat = cfg["group_chat_id"]
        thread = cfg.get("topics", {}).get("diagnostics")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat, "text": msg}
        if thread is not None:
            data["message_thread_id"] = thread
        requests.post(url, data=data, timeout=10)
    except Exception:
        pass  # heartbeat never raises up to the LangGraph thread


def _read_progress_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return events


def _heartbeat_loop(run_dir: Path, run_id: str, interval_sec: int, to_telegram: bool) -> None:
    progress_path = run_dir / "progress.jsonl"
    last_event_count = 0
    tg_cfg = _load_telegram_cfg() if to_telegram else None
    sys.stderr.write(
        f"[heartbeat] started: run_id={run_id} interval={interval_sec}s "
        f"telegram={'on' if tg_cfg else 'off'}\n"
    )
    sys.stderr.flush()

    while True:
        time.sleep(interval_sec)
        try:
            events = _read_progress_events(progress_path)
            n = len(events)
            new_events = n - last_event_count
            last_event_count = n

            if n == 0:
                sys.stderr.write(f"[heartbeat] run_id={run_id} - waiting for first event\n")
                sys.stderr.flush()
                continue

            last = events[-1]
            phase = last.get("phase", "?")
            event = last.get("event", "?")
            total = last.get("total_elapsed_sec", 0)
            minutes = total / 60.0

            # Content-based freshness check per silent-staleness wiki:
            # compare wall clock against the ts embedded in the LAST event, not
            # against the heartbeat's own loop timer.
            now = time.time()
            last_ts = last.get("ts", now)
            since_last = now - last_ts
            stalled = since_last > STALL_THRESHOLD_SEC

            detail = last.get("detail", {}) or {}
            detail_bits = []
            if "purpose" in detail:
                detail_bits.append(f"purpose={detail['purpose']}")
            if "text_len" in detail:
                detail_bits.append(f"text_len={detail['text_len']}")
            if "prompt_len" in detail:
                detail_bits.append(f"prompt_len={detail['prompt_len']}")
            detail_str = " ".join(detail_bits)

            status = "STALLED" if stalled else "running"
            msg = (
                f"[heartbeat] {status} run_id={run_id} "
                f"elapsed={minutes:.1f}min phase={phase} last_event={event} "
                f"new_events_in_last_{interval_sec // 60}min={new_events} "
                f"since_last_event={since_last:.0f}s {detail_str}"
            )
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
            if tg_cfg is not None:
                _post_telegram(msg, tg_cfg)

            if stalled:
                warn = (
                    f"[heartbeat STALL WARNING] run_id={run_id}: no new progress event "
                    f"for {since_last:.0f}s (threshold {STALL_THRESHOLD_SEC}s). "
                    f"Last was {event} in {phase}."
                )
                sys.stderr.write(warn + "\n")
                sys.stderr.flush()
                if tg_cfg is not None:
                    _post_telegram(warn, tg_cfg)

        except Exception as e:
            # Never raise - heartbeat failures must not kill the run
            sys.stderr.write(f"[heartbeat] internal error: {e}\n")
            sys.stderr.flush()


def start(run_dir: Path, run_id: str,
          interval_sec: int | None = None,
          to_telegram: bool = True) -> threading.Thread:
    """Start a daemon heartbeat thread. Returns the thread (for tests).

    Environment overrides:
      HEARTBEAT_INTERVAL_SEC  - override default 300s
      HEARTBEAT_DISABLE=1     - skip starting the heartbeat (for smoke tests)
    """
    if os.environ.get("HEARTBEAT_DISABLE") == "1":
        sys.stderr.write("[heartbeat] disabled via HEARTBEAT_DISABLE=1\n")
        sys.stderr.flush()
        return threading.Thread(target=lambda: None, daemon=True)

    if interval_sec is None:
        try:
            interval_sec = int(os.environ.get("HEARTBEAT_INTERVAL_SEC", DEFAULT_INTERVAL_SEC))
        except ValueError:
            interval_sec = DEFAULT_INTERVAL_SEC

    t = threading.Thread(
        target=_heartbeat_loop,
        args=(run_dir, run_id, interval_sec, to_telegram),
        daemon=True,
        name=f"8d-heartbeat-{run_id}",
    )
    t.start()
    return t
