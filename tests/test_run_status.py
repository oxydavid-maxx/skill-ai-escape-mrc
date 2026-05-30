import json
import time

from ai_escape_mrc.run_status import resolve_run_dir, status_for_run


def _append_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_follow_run_streams_screens_until_complete(tmp_path):
    import io
    from ai_escape_mrc.run_status import follow_run

    run_dir = tmp_path / "run-watch"
    run_dir.mkdir()
    now = time.time()
    _append_jsonl(
        run_dir / "progress.jsonl",
        [
            {"ts": now - 2, "phase": "phase_10_emit_and_wait", "event": "phase_start", "detail": {}, "total_elapsed_sec": 1},
            {"ts": now - 1, "phase": "phase_10_emit_and_wait", "event": "phase_end", "detail": {"ok": True}, "total_elapsed_sec": 2},
        ],
    )
    _append_jsonl(
        run_dir / "stage-progress.jsonl",
        [{"ts": "2026-01-01T00:00:00", "phase": "phase_0_research", "screen": "[AI Escape MRC] Phase 0\n- step A"}],
    )
    _append_jsonl(
        run_dir / "stage-summaries.jsonl",
        [{"ts": "2026-01-01T00:00:01", "kind": "phase_summary", "phase": "phase_10_emit_and_wait",
          "screen": "[AI Escape MRC] Phase 10\n- delivered"}],
    )

    out = io.StringIO()
    rc = follow_run(str(run_dir), default_runs_dir=tmp_path, stream=out, poll_sec=0.01)
    text = out.getvalue()

    assert rc == 0  # terminal "complete"
    assert "step A" in text          # streamed a stage-progress screen
    assert "delivered" in text       # streamed a stage-summary screen
    assert "Status: complete" in text  # final human summary


def test_follow_run_not_found_returns_1(tmp_path):
    import io
    from ai_escape_mrc.run_status import follow_run

    out = io.StringIO()
    rc = follow_run("run-does-not-exist", default_runs_dir=tmp_path,
                    stream=out, poll_sec=0.01, wait_for_start_sec=0.0)
    assert rc == 1
    assert "not found" in out.getvalue()


def test_status_for_run_reports_current_phase_and_summary(tmp_path):
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    now = time.time()
    _append_jsonl(
        run_dir / "progress.jsonl",
        [
            {"ts": now - 10, "phase": "phase_0_research", "event": "phase_start", "detail": {}, "total_elapsed_sec": 0},
            {"ts": now - 5, "phase": "phase_0_research", "event": "phase_end", "detail": {"ok": True}, "total_elapsed_sec": 5},
            {"ts": now - 1, "phase": "phase_1_is_isnt", "event": "phase_start", "detail": {}, "total_elapsed_sec": 6},
        ],
    )
    _append_jsonl(
        run_dir / "stage-summaries.jsonl",
        [{"phase": "phase_0_research", "screen": "[AI Escape MRC] Phase 0 Research\n- done"}],
    )
    _append_jsonl(
        run_dir / "stage-progress.jsonl",
        [{"phase": "phase_1_is_isnt", "message": "Extracting IS / IS NOT."}],
    )

    status = status_for_run(str(run_dir))

    assert status["exists"] is True
    assert status["current_phase"] == "phase_1_is_isnt"
    assert status["completed_phases"] == ["phase_0_research"]
    assert status["latest_progress"]["message"] == "Extracting IS / IS NOT."
    assert "Phase 1" in status["human_summary"]


def test_status_for_missing_run_is_not_found(tmp_path):
    status = status_for_run("run-missing", default_runs_dir=tmp_path)

    assert status["exists"] is False
    assert status["status"] == "not_found"


def test_resolve_run_dir_prefers_default_runs_dir(tmp_path):
    run_dir = tmp_path / "run-fixed"
    run_dir.mkdir()

    assert resolve_run_dir("run-fixed", default_runs_dir=tmp_path) == run_dir.resolve()


def test_status_for_run_reports_run_error_artifact(tmp_path):
    run_dir = tmp_path / "run-error"
    run_dir.mkdir()
    (run_dir / "run-error.json").write_text(
        json.dumps({
            "phase": "phase_5_prevention_audit",
            "title": "Phase 5 Prevention Audit",
            "error_type": "OSError",
            "message": "Invalid argument",
        }),
        encoding="utf-8",
    )

    status = status_for_run(str(run_dir))

    assert status["status"] == "error"
    assert status["error"]["phase"] == "phase_5_prevention_audit"
    assert status["run_error_path"] == str(run_dir / "run-error.json")
    assert "Failed at: Phase 5 Prevention Audit" in status["human_summary"]


def test_status_ignores_stale_error_after_resume_progress(tmp_path):
    run_dir = tmp_path / "run-resumed"
    run_dir.mkdir()
    now = time.time()
    (run_dir / "run-error.json").write_text(
        json.dumps({
            "ts": "2026-05-27T00:00:00+00:00",
            "phase": "phase_9_write_plan",
            "title": "Phase 9 Plan",
            "error_type": "OutputIdentityContractError",
            "message": "old failure",
        }),
        encoding="utf-8",
    )
    _append_jsonl(
        run_dir / "progress.jsonl",
        [
            {"ts": now, "phase": "phase_9_write_plan", "event": "phase_start", "detail": {}, "total_elapsed_sec": 0},
            {"ts": now + 1, "phase": "llm", "event": "llm_call_start", "detail": {"purpose": "phase_9_write_plan"}, "total_elapsed_sec": 1},
        ],
    )

    status = status_for_run(str(run_dir))

    assert status["status"] == "running"
    assert status["error"] is None
    assert status["run_error_path"] is None


def test_status_reports_complete_when_phase10_delivery_succeeds(tmp_path):
    run_dir = tmp_path / "run-complete"
    run_dir.mkdir()
    now = time.time()
    _append_jsonl(
        run_dir / "progress.jsonl",
        [
            {"ts": now, "phase": "phase_10_emit_and_wait", "event": "phase_start", "detail": {}, "total_elapsed_sec": 0},
            {"ts": now + 1, "phase": "phase_10_emit_and_wait", "event": "phase_end", "detail": {"ok": True}, "total_elapsed_sec": 1},
        ],
    )
    _append_jsonl(
        run_dir / "stage-summaries.jsonl",
        [
            {"kind": "phase_summary", "phase": "phase_10_emit_and_wait", "screen": "[AI Escape MRC] Phase 10 Final Delivery\n- Delivery outcome: email sent."},
        ],
    )
    (run_dir / "delivery-status.json").write_text(
        json.dumps({"email_delivery_result": "sent"}),
        encoding="utf-8",
    )

    status = status_for_run(str(run_dir))

    assert status["status"] == "complete"
    assert status["current_phase"] is None
    assert "phase_10_emit_and_wait" in status["completed_phases"]


def test_status_reports_delivery_failed_after_phase10_email_failure(tmp_path):
    run_dir = tmp_path / "run-delivery-failed"
    run_dir.mkdir()
    now = time.time()
    _append_jsonl(
        run_dir / "progress.jsonl",
        [
            {"ts": now, "phase": "phase_10_emit_and_wait", "event": "phase_start", "detail": {}, "total_elapsed_sec": 0},
            {"ts": now + 1, "phase": "phase_10_emit_and_wait", "event": "phase_end", "detail": {"ok": True}, "total_elapsed_sec": 1},
        ],
    )
    _append_jsonl(
        run_dir / "stage-summaries.jsonl",
        [
            {"kind": "phase_summary", "phase": "phase_10_emit_and_wait", "screen": "[AI Escape MRC] Phase 10 Final Delivery\n- Delivery outcome: email failed."},
        ],
    )
    (run_dir / "delivery-status.json").write_text(
        json.dumps({"email_delivery_result": "failed", "email_delivery_error": "Outlook missing"}),
        encoding="utf-8",
    )

    status = status_for_run(str(run_dir))

    assert status["status"] == "delivery_failed"
    assert status["current_phase"] is None
    assert status["delivery_status"]["email_delivery_error"] == "Outlook missing"
