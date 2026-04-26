# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: Local import inside a nested except block binds the name at function
#   scope in CPython; all prior references to that name in main() become local reads,
#   which fail with UnboundLocalError if the binding line was not yet executed.
# WIKI-ACTION: Removed the local 'import sys' inside the heartbeat except-block;
#   module-level import (line 4 of run_8d.py) is now the sole binding.
"""Regression tests: GraphInterrupt path in run_8d.main() must not raise UnboundLocalError.

Root cause (fixed 2026-04-26): a local `import sys` inside the heartbeat except-block
caused Python to treat `sys` as a local variable throughout main(). Any code path
that hit `sys.stderr` without passing through that except-block got UnboundLocalError.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_saver(mock_saver):
    """Wire a mock SqliteSaver context manager that just returns a MagicMock."""
    ctx = MagicMock()
    mock_saver.return_value.__enter__ = lambda s: ctx
    mock_saver.return_value.__exit__ = MagicMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_graph_interrupt_returns_0_no_unbound_error(tmp_path, capsys):
    """GraphInterrupt path must exit 0 and print the awaiting-approval message.

    Before the fix, main() raised UnboundLocalError at the sys.stderr.write call
    inside the heartbeat except-block (or at the 'Run incomplete' print later)
    because a local `import sys` shadowed the module-level name throughout main().
    After the fix it must not raise at all.
    """
    import run_8d
    from langgraph.errors import GraphInterrupt

    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = GraphInterrupt("awaiting human approval")

    with patch("run_8d.build_graph", return_value=fake_graph), \
         patch("run_8d.SqliteSaver.from_conn_string") as mock_saver, \
         patch("run_8d.RUNS_DIR", tmp_path), \
         patch("eightd.progress.init", return_value=None), \
         patch("eightd.heartbeat.start", return_value=None), \
         patch("sys.argv", ["run_8d", "some test problem"]):

        _make_fake_saver(mock_saver)
        rc = run_8d.main()

    assert rc == 0, f"Expected exit 0 on GraphInterrupt, got {rc}"
    captured = capsys.readouterr()
    assert "Awaiting approval" in captured.err, (
        f"Expected 'Awaiting approval' in stderr; got: {captured.err!r}"
    )


def test_incomplete_run_returns_2_no_unbound_error(tmp_path, capsys):
    """'Run incomplete' path (no phase_11_complete) must exit 2 without UnboundLocalError."""
    import run_8d

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {"phase_11_complete": False}

    with patch("run_8d.build_graph", return_value=fake_graph), \
         patch("run_8d.SqliteSaver.from_conn_string") as mock_saver, \
         patch("run_8d.RUNS_DIR", tmp_path), \
         patch("eightd.progress.init", return_value=None), \
         patch("eightd.heartbeat.start", return_value=None), \
         patch("sys.argv", ["run_8d", "some test problem"]):

        _make_fake_saver(mock_saver)
        rc = run_8d.main()

    assert rc == 2, f"Expected exit 2 on incomplete run, got {rc}"
    captured = capsys.readouterr()
    assert "incomplete" in captured.err.lower(), (
        f"Expected 'incomplete' in stderr; got: {captured.err!r}"
    )


def test_heartbeat_failure_then_graph_interrupt_exits_0(tmp_path, capsys):
    """Exact regression path: heartbeat raises (fires the except-block that
    previously had the local 'import sys'), then GraphInterrupt is raised.
    Both sys.stderr paths must work without UnboundLocalError.
    """
    import run_8d
    from langgraph.errors import GraphInterrupt

    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = GraphInterrupt("awaiting human approval")

    with patch("run_8d.build_graph", return_value=fake_graph), \
         patch("run_8d.SqliteSaver.from_conn_string") as mock_saver, \
         patch("run_8d.RUNS_DIR", tmp_path), \
         patch("eightd.progress.init", return_value=None), \
         patch("eightd.heartbeat.start", side_effect=RuntimeError("port busy")), \
         patch("sys.argv", ["run_8d", "some test problem"]):

        _make_fake_saver(mock_saver)
        rc = run_8d.main()

    assert rc == 0, f"Expected exit 0; got {rc}"
    captured = capsys.readouterr()
    assert "heartbeat" in captured.err.lower(), "Expected heartbeat warning in stderr"
    assert "Awaiting approval" in captured.err, "Expected approval message in stderr"
