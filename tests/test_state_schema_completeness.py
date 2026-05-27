"""Regression guard: every state key written by a phase must be declared in
AiEscapeMrcState. LangGraph's StateGraph drops undeclared keys silently on
merge, which previously bypassed Phase 7's emission gate
(phase_3_status / phase_5_status went missing -> _assert_emission_prerequisites
fell into the "legacy" branch and emitted reports on top of failed audits).

Caught from a real run: run-1779848190-166dcec3 (2026-05-27) — phase_3_status,
phase_3_residual_risks, phase_5_status, phase_5_residual_risks were all None in
the final checkpoint despite being assigned by phase_3_rc_audit.py / phase_5.
"""
from __future__ import annotations

import re
from pathlib import Path

PKG = Path(__file__).parent.parent / "ai_escape_mrc"
STATE_PY = PKG / "state.py"
PHASES_DIR = PKG / "phases"

_ASSIGN_RE = re.compile(r"""state\[['"]([a-zA-Z_][a-zA-Z0-9_]*)['"]\]\s*=""")
_SETDEFAULT_RE = re.compile(r"""state\.setdefault\(\s*['"]([a-zA-Z_][a-zA-Z0-9_]*)['"]""")
_FIELD_RE = re.compile(r"^\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:")


def _declared_state_keys() -> set[str]:
    keys: set[str] = set()
    for line in STATE_PY.read_text(encoding="utf-8").splitlines():
        m = _FIELD_RE.match(line)
        if m and not m.group(1).startswith("_"):
            keys.add(m.group(1))
    return keys


def _written_state_keys() -> dict[str, list[str]]:
    """Return {key: [files_that_write_it]}."""
    written: dict[str, list[str]] = {}
    for py in PHASES_DIR.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for m in _ASSIGN_RE.finditer(text):
            written.setdefault(m.group(1), []).append(py.name)
        for m in _SETDEFAULT_RE.finditer(text):
            written.setdefault(m.group(1), []).append(py.name)
    return written


def test_every_written_state_key_is_declared():
    declared = _declared_state_keys()
    written = _written_state_keys()
    undeclared = {k: v for k, v in written.items() if k not in declared}
    assert not undeclared, (
        "Phase code writes state keys not declared in AiEscapeMrcState. "
        "LangGraph drops undeclared keys silently on channel merge, so "
        "downstream phases will see None and may bypass guard predicates. "
        f"Add these to state.py: {undeclared}"
    )
