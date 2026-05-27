"""Tests for heartbeat formatting and stall threshold per-phase calibration.

# WIKI-CONSULTED: long-running-progress-heartbeat#built-in-not-external
# WIKI-CONSULTED: silent-staleness#data-level-freshness-check
# WIKI-CONSULTED: function-replacement-convention#delete-old-in-same-commit
# WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
# WIKI-FINDING: heartbeat must answer "what's happening + how long left + what's next",
#   not just "still alive". Generic 600s STALL_THRESHOLD was the failure mode for
#   Phase 7 (~750s typical). These tests pin per-phase calibration to prevent
#   regression to a single global threshold.
# WIKI-FINDING: per silent-staleness, freshness comes from event.ts (content), not
#   from heartbeat-loop wall clock; tests construct events with explicit ts so
#   the boundary check is deterministic.
# WIKI-ACTION: tests treat _format_heartbeat_line as a pure function (now param
#   injectable) so behaviour is reproducible and not flake-prone ??covers the
#   format contract AND the stall-threshold ladder in one place.

Covers:
  - new format includes phase label, total elapsed, in-flight detail, next-phase
  - phase 7 stall threshold = 750 * 1.5 = 1125s, NOT the old global 600s
  - unknown phase falls back gracefully (no crash, uses DEFAULT_STALL_THRESHOLD_SEC)
  - empty events => waiting message
  - phase 8 (typical=1s) clamps to 60s floor (no instant false stall)
"""
from __future__ import annotations

from ai_escape_mrc.heartbeat import (
    DEFAULT_STALL_THRESHOLD_SEC,
    NEXT_PHASE,
    PHASE_NAMES,
    TYPICAL_PHASE_DURATIONS_SEC,
    _format_heartbeat_line,
    _stall_threshold_for,
)


def _evt(phase: str, event: str, ts: float, total: float = 0.0, **detail) -> dict:
    return {
        "phase": phase,
        "event": event,
        "ts": ts,
        "total_elapsed_sec": total,
        "detail": detail or {},
    }


def test_phase_7_stall_threshold_is_1125s():
    """Phase 7 typical 750s * 1.5 = 1125s ??old static 600s would have false-positived."""
    assert _stall_threshold_for("phase_7_report") == 1125


def test_phase_1_stall_threshold_is_90s():
    """Phase 1 typical 60s * 1.5 = 90s."""
    assert _stall_threshold_for("phase_1_is_isnt") == 90


def test_unknown_phase_uses_default_threshold():
    """Unknown phase name => DEFAULT_STALL_THRESHOLD_SEC (1200s), no crash."""
    assert _stall_threshold_for("phase_99_invented") == DEFAULT_STALL_THRESHOLD_SEC


def test_instant_phase_threshold_clamped_to_floor():
    """Phase 8 typical=1s would yield 1.5s ??clamp to 60s floor to prevent false alarms."""
    assert _stall_threshold_for("phase_8_collect_actions") == 60


def test_empty_events_returns_waiting_line():
    msg, stalled, phase = _format_heartbeat_line("run-X", [], now=1000.0)
    assert "waiting for first event" in msg
    assert stalled is False
    assert phase == ""


def test_format_includes_phase_label_total_elapsed_in_flight_and_next():
    """Format target:
       [heartbeat] run-X | Phase 7/11 (...) | 22.5min total | event ... in flight 63s/typical 750s (~13min) | next: Phase 8/11 (...)
    """
    now = 2000.0
    events = [_evt("phase_7_report", "llm_call_start", ts=now - 63, total=22.5 * 60)]
    msg, stalled, phase = _format_heartbeat_line("run-X", events, now=now)

    assert "run-X" in msg
    assert PHASE_NAMES["phase_7_report"] in msg
    assert "22.5min total" in msg
    assert "llm_call_start" in msg
    assert "63s" in msg
    assert "750s" in msg
    assert "~13min" in msg
    assert "next:" in msg
    assert PHASE_NAMES[NEXT_PHASE["phase_7_report"]] in msg
    assert stalled is False  # 63s well under 1125s
    assert phase == "phase_7_report"


def test_phase_7_not_stalled_at_700s():
    """Inside Phase 7 typical envelope (700s < 1125s threshold) => not stalled."""
    now = 5000.0
    events = [_evt("phase_7_report", "llm_call_start", ts=now - 700, total=15 * 60)]
    _, stalled, _ = _format_heartbeat_line("run-X", events, now=now)
    assert stalled is False


def test_phase_7_stalls_after_threshold():
    """Past Phase 7 threshold (1125s) => stalled."""
    now = 5000.0
    events = [_evt("phase_7_report", "llm_call_start", ts=now - 1200, total=20 * 60)]
    _, stalled, _ = _format_heartbeat_line("run-X", events, now=now)
    assert stalled is True


def test_all_phase_names_have_typical_duration():
    """Every phase that gets a friendly name should also have a calibrated duration
    (or be explicitly excluded). Catches typos and missing calibrations."""
    for k in PHASE_NAMES:
        assert k in TYPICAL_PHASE_DURATIONS_SEC, f"missing typical duration for {k}"


def test_all_phases_have_next_edge():
    """Every phase needs a NEXT_PHASE entry (terminal phase points to 'END')."""
    for k in PHASE_NAMES:
        assert k in NEXT_PHASE, f"missing NEXT_PHASE entry for {k}"


def test_unknown_phase_format_does_not_crash():
    """Heartbeat must never crash on an unknown phase ??fallback to raw phase string."""
    now = 3000.0
    events = [_evt("phase_xx_unknown", "weird_event", ts=now - 30, total=2 * 60)]
    msg, stalled, phase = _format_heartbeat_line("run-X", events, now=now)
    assert "phase_xx_unknown" in msg  # falls back to raw key
    assert "next:" in msg  # still emits a next field even if unknown
    assert stalled is False
    assert phase == "phase_xx_unknown"
