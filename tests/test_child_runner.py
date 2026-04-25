"""Tests for eightd/child_runner.py — CLAUDECODE env strip (Issue #573 mitigation)."""
import os
import subprocess
import sys
from pathlib import Path


def test_child_runner_strips_claudecode(tmp_path):
    env = {**os.environ, "CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli"}
    out_file = tmp_path / "env_dump.txt"
    proc = subprocess.run(
        [sys.executable, "-c",
         "import eightd.child_runner; import os, sys; "
         f"open(r'{out_file}', 'w').write(str({{k: os.environ.get(k) for k in ['CLAUDECODE','CLAUDE_CODE_ENTRYPOINT']}}))"
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert proc.returncode == 0, proc.stderr
    dump = out_file.read_text()
    assert "'CLAUDECODE': None" in dump, f"CLAUDECODE not popped: {dump}"
    assert "'CLAUDE_CODE_ENTRYPOINT': None" in dump, f"CCE not popped: {dump}"
