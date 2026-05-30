"""Phase 3 audit ??3 sequential rounds in one invocation, no outer loop.

Rounds now run through a single persistent ClaudeSession (one subprocess for
all rounds). Tests patch ClaudeSession with a fake context manager whose
``ask()`` yields the per-round audit dicts.
"""
from unittest.mock import patch
from ai_escape_mrc.phases.phase_3_rc_audit import phase_3_rc_audit, NUM_ROUNDS


def _base_state():
    return {
        "why_chains": {
            "q1_trc_nc": {"whys": [{"n": 1, "why": "a"}], "root": "r1"},
            "q2_trc_nd": {"whys": [{"n": 1, "why": "b"}], "root": "r2"},
            "q3_mrc_nc": {"whys": [{"n": 1, "why": "c"}], "root": "r3"},
            "q4_mrc_nd": {"whys": [{"n": 1, "why": "d"}], "root": "r4"},
        }
    }


class _FakeSession:
    """Stand-in for ClaudeSession: records how many times it connected and
    delegates each ask() to a supplied responder."""

    instances = []

    def __init__(self, responder):
        self._responder = responder
        self.connects = 0
        self.asks = 0
        _FakeSession.instances.append(self)

    def __enter__(self):
        self.connects += 1
        return self

    def __exit__(self, *exc):
        return False

    def ask(self, user, purpose="unknown"):
        self.asks += 1
        return self._responder()


def _patch_session(responder):
    """Patch ClaudeSession so constructing it returns a single _FakeSession
    bound to ``responder`` (one connect for the whole phase)."""
    _FakeSession.instances = []
    session = _FakeSession(responder)
    return patch(
        "ai_escape_mrc.phases.phase_3_rc_audit.ClaudeSession",
        side_effect=lambda **kw: session,
    ), session


def test_audit_stops_early_on_exhausted():
    calls = {"n": 0}

    def responder():
        calls["n"] += 1
        return {"round": calls["n"], "weaknesses": [], "verdict": "EXHAUSTED"}

    ctx, session = _patch_session(responder)
    with ctx:
        result = phase_3_rc_audit(_base_state())

    assert calls["n"] == 1  # stopped at first EXHAUSTED
    assert session.connects == 1  # one persistent session for the phase
    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True
    assert len(result["phase_3_rounds"]) == 1


def test_audit_runs_all_3_rounds_when_continue():
    calls = {"n": 0}

    def responder():
        calls["n"] += 1
        return {
            "round": calls["n"],
            "weaknesses": [
                {"quadrant": "q1_trc_nc", "why_step_n": 1,
                 "classification": "ADDRESSABLE", "issue": "thin",
                 "suggested_fix": "deepen"},
            ],
            "verdict": "CONTINUE",
        }

    ctx, session = _patch_session(responder)
    with ctx:
        result = phase_3_rc_audit(_base_state())

    # CONTINUE + an ADDRESSABLE weakness every round -> no early convergence.
    assert calls["n"] == NUM_ROUNDS
    assert session.connects == 1  # still just one persistent session
    # Fixes were applied in-place to why_chains
    assert any(
        "audit_notes" in w
        for w in result["why_chains"]["q1_trc_nc"]["whys"]
    )


def test_audit_collects_residual_risks():
    call_seq = [
        {"verdict": "CONTINUE", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "RESIDUAL",
             "issue": "inherent limit", "suggested_fix": "accept"},
        ]},
        {"verdict": "EXHAUSTED", "weaknesses": []},
    ]
    it = iter(call_seq)

    ctx, _ = _patch_session(lambda: next(it))
    with ctx:
        result = phase_3_rc_audit(_base_state())

    assert len(result["phase_3_residual_risks"]) == 1
    assert result["phase_3_residual_risks"][0]["quadrant"] == "q3_mrc_nc"


def test_audit_converges_when_no_addressable_weakness():
    """Quality-preserving early exit: a real round with no ADDRESSABLE weakness
    means further rounds add nothing, so the audit stops (still EXHAUSTED)."""
    calls = {"n": 0}

    def responder():
        calls["n"] += 1
        return {"verdict": "CONTINUE", "weaknesses": []}

    ctx, _ = _patch_session(responder)
    with ctx:
        result = phase_3_rc_audit(_base_state())

    assert calls["n"] == 1  # converged after the first empty round
    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True
