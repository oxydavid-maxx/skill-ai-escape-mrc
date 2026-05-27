import sys
import subprocess
from pathlib import Path


def test_gc_flag_does_not_crash():
    script = Path(__file__).parent.parent / "run_ai_escape_mrc.py"
    result = subprocess.run(
        [sys.executable, str(script), "--gc"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0


def test_dry_run_prints_plan():
    script = Path(__file__).parent.parent / "run_ai_escape_mrc.py"
    result = subprocess.run(
        [sys.executable, str(script), "test problem", "--dry-run"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "Would invoke" in result.stdout
