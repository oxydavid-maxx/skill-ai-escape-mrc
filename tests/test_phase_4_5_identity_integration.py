"""Integration: phase_4 producer-side legacy-identity gate end-to-end.

Simulates a real-world contamination event: phase_4 prevention call for q3
returns an `eightd-*` literal on the first attempt; the producer-side
`_call_with_legacy_term_retry` wrapper detects it (sanitize round-trip is a
no-op iff clean), retries with a critique, and the retry returns clean.
Everything else (corrective q1, q2; prevention q4) is clean on first try.
Final `state.prevention_actions` and `state.corrective_actions` must be clean
on the consumer-side path that phase_7/phase_9 would later run (sanitize no-op).

Note on mock shape: phase_4 uses `parallel_run(max_workers=4)` which
dispatches the 4 calls to a ThreadPoolExecutor — call ordering is
non-deterministic. A plain `iter([...])` mock as drafted in the plan would
mis-route under thread-scheduling jitter. Instead this test uses a stateful
mock keyed by (system prompt: corrective vs prevention) and a thread-safe
counter for q3 prevention attempts (only q3's first attempt returns the
legacy literal). This preserves the intended scenario regardless of which
order the executor happens to run the 4 tasks in.
"""
import json
import threading
from unittest.mock import patch

from ai_escape_mrc.phases.phase_4_actions import phase_4_actions
from ai_escape_mrc.validators import sanitize_legacy_identity


def _assert_clean(payload):
    """Consumer-side check: the final state is already free of legacy identity
    tokens, so sanitizing it is a no-op (the producer gate kept it clean)."""
    serialized = json.dumps(payload, ensure_ascii=False)
    assert sanitize_legacy_identity(serialized) == serialized


def test_phase_4_5_clean_after_legacy_retry_at_phase_4():
    """phase_4 prevention q3 first response has eightd-, retry clean.

    Final corrective_actions + prevention_actions state must be clean for the
    downstream (consumer-side) sanitize path that phase_7 / phase_9 run on the
    artifact emission path (sanitize is a no-op on clean state).
    """
    # Thread-safe counter for prevention calls; only the FIRST prevention
    # call gets the contaminated response (simulating q3's first attempt).
    # Subsequent prevention calls (q3 retry + q4 first try) get clean
    # responses. Corrective calls (q1, q2) always clean.
    lock = threading.Lock()
    prevention_call_count = {"n": 0}

    def fake_call(**kw):
        system = (kw.get("system") or "").lower()
        if "corrective" in system:
            return {"action": "verify aem-resolve binary", "rationale": "clean"}
        # prevention branch
        with lock:
            prevention_call_count["n"] += 1
            n = prevention_call_count["n"]
        if n == 1:
            # First prevention call gets the contaminated response.
            return {
                "action": "create eightd-omission-resolve CLI",
                "gate_test": {"scope": "PASS"},
            }
        # All subsequent prevention calls (retry of the contaminated one,
        # plus the other quadrant's first call) get clean responses.
        return {
            "action": "create aem-omission-resolve CLI",
            "gate_test": {"scope": "PASS"},
        }

    state = {
        "problem": "p",
        "why_chains": {
            q: {"whys": [], "root": "r"}
            for q in ("q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd")
        },
    }

    with patch(
        "ai_escape_mrc.phases.phase_4_actions.call_claude",
        side_effect=fake_call,
    ):
        state = phase_4_actions(state)

    # Producer-side gate kept the legacy literal out of final state.
    assert "eightd" not in str(state["prevention_actions"]).lower()
    assert "eightd" not in str(state["corrective_actions"]).lower()

    # At least one retry happened (3 prevention calls total: q3-bad, q3-retry, q4).
    # (q4 might have been the "first prevention call" under scheduling jitter, in
    # which case q3 would have been the second/third — but in EITHER case the
    # FIRST prevention call gets contaminated and triggers exactly one retry,
    # so prevention_call_count >= 3.)
    assert prevention_call_count["n"] >= 3, (
        f"expected >=3 prevention calls (2 first-tries + 1 retry), "
        f"got {prevention_call_count['n']}"
    )

    # Final state is clean for the consumer-side path that phase_7/phase_9 run.
    # This is the integration assertion: the producer gate (retry-then-sanitize)
    # keeps downstream inputs clean, so sanitizing the final state is a no-op.
    _assert_clean(state["corrective_actions"])
    _assert_clean(state["prevention_actions"])

    # Sanity: both quadrants populated for each action class.
    assert set(state["corrective_actions"].keys()) == {"q1_trc_nc", "q2_trc_nd"}
    assert set(state["prevention_actions"].keys()) == {"q3_mrc_nc", "q4_mrc_nd"}
