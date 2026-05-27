"""Start AI Escape MRC in a Windows-hidden Python process.

This wrapper is for local background runs where opening a visible console would
interrupt the user's desktop. It redirects stdout/stderr to runs/_manual_logs/.
"""
from __future__ import annotations

import subprocess
import sys
import time
import uuid
import json
from pathlib import Path

from ai_escape_mrc.no_console import hidden_creationflags, hidden_python_command


def _split_launcher_args(argv: list[str]) -> tuple[bool, bool, list[str]]:
    """Return (detach, json_output, args_for_run_script)."""
    agent = "--agent" in argv
    watch = "--watch" in argv
    detach = ("--detach" in argv or agent) and not watch
    json_output = "--json" in argv or agent
    stripped = [
        arg for arg in argv
        if arg not in {"--detach", "--json", "--agent", "--watch"}
    ]
    return detach, json_output, stripped


def main() -> int:
    detach, json_output, run_args = _split_launcher_args(sys.argv[1:])
    skill_dir = Path(__file__).parent
    run_id = _ensure_run_id(run_args)
    run_dir = skill_dir / "runs" / run_id if run_id else None
    logs = skill_dir / "runs" / "_manual_logs"
    logs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_path = logs / f"hidden-{stamp}.out.log"
    err_path = logs / f"hidden-{stamp}.err.log"
    out = out_path.open("ab")
    err = err_path.open("ab")
    cmd = hidden_python_command(skill_dir / "run_ai_escape_mrc.py", *run_args)
    proc = subprocess.Popen(
        cmd,
        cwd=str(skill_dir.parent.parent),
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=err,
        creationflags=hidden_creationflags(),
        close_fds=True,
    )
    out.close()
    err.close()
    metadata = {
        "pid": proc.pid,
        "run_id": run_id,
        "run_dir": str(run_dir) if run_dir else None,
        "stdout": str(out_path),
        "stderr": str(err_path),
        "status_command": (
            f"py -3 {skill_dir / 'run_ai_escape_mrc.py'} --status-json {run_dir}"
            if run_dir else None
        ),
        "watch_mode": not detach,
    }
    if json_output:
        print(json.dumps(metadata, ensure_ascii=False))
    else:
        print(f"AI Escape MRC hidden run started. PID: {proc.pid}")
        print(f"stdout: {out_path}")
        print(f"stderr: {err_path}")
    if detach:
        return 0
    print("Streaming hidden run output.", flush=True)
    return _follow_logs(proc, out_path, err_path)


def _ensure_run_id(run_args: list[str]) -> str | None:
    if "--resume" in run_args or "--status-json" in run_args or "--gc" in run_args:
        return None
    if "--run-id" in run_args:
        idx = run_args.index("--run-id")
        return run_args[idx + 1] if idx + 1 < len(run_args) else None
    for arg in run_args:
        if arg.startswith("--run-id="):
            return arg.split("=", 1)[1]
    run_id = f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_args[:0] = ["--run-id", run_id]
    return run_id


def _follow_logs(proc: subprocess.Popen, out_path: Path, err_path: Path) -> int:
    offsets = {out_path: 0, err_path: 0}
    while True:
        _drain_log(out_path, offsets, sys.stdout)
        _drain_log(err_path, offsets, sys.stderr)
        rc = proc.poll()
        if rc is not None:
            _drain_log(out_path, offsets, sys.stdout)
            _drain_log(err_path, offsets, sys.stderr)
            return int(rc)
        time.sleep(1)


def _drain_log(path: Path, offsets: dict[Path, int], stream) -> None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(offsets.get(path, 0))
            text = f.read()
            offsets[path] = f.tell()
    except OSError:
        return
    if text:
        stream.write(text)
        stream.flush()


if __name__ == "__main__":
    raise SystemExit(main())
