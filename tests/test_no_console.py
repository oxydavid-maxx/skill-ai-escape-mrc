import os

from ai_escape_mrc.no_console import CREATE_NO_WINDOW, hidden_creationflags, hidden_python_command
from run_ai_escape_mrc_hidden import _ensure_run_id, _split_launcher_args


def test_hidden_creationflags_adds_create_no_window_on_windows():
    flags = hidden_creationflags(0)
    if os.name == "nt":
        assert flags & CREATE_NO_WINDOW
    else:
        assert flags == 0


def test_hidden_python_command_never_uses_py_launcher():
    cmd = hidden_python_command("run_ai_escape_mrc.py", "--resume", "run-1")
    exe = os.path.basename(cmd[0]).lower()

    assert exe != "py.exe"
    assert cmd[1:] == ["run_ai_escape_mrc.py", "--resume", "run-1"]


def test_hidden_launcher_streams_by_default_and_detach_is_explicit():
    detach, json_output, args = _split_launcher_args(["--user-email", "u@example.com", "problem"])
    assert detach is False
    assert json_output is False
    assert args == ["--user-email", "u@example.com", "problem"]

    detach, json_output, args = _split_launcher_args(["--detach", "--user-email", "u@example.com", "problem"])
    assert detach is True
    assert json_output is False
    assert args == ["--user-email", "u@example.com", "problem"]


def test_hidden_launcher_agent_mode_is_detached_json():
    detach, json_output, args = _split_launcher_args(["--agent", "--user-email", "u@example.com", "problem"])

    assert detach is True
    assert json_output is True
    assert args == ["--user-email", "u@example.com", "problem"]


def test_hidden_launcher_agent_watch_streams_json_metadata_plus_output():
    detach, json_output, args = _split_launcher_args([
        "--agent", "--watch", "--user-email", "u@example.com", "problem"
    ])

    assert detach is False
    assert json_output is True
    assert args == ["--user-email", "u@example.com", "problem"]


def test_hidden_launcher_injects_run_id_for_new_runs():
    args = ["--user-email", "u@example.com", "problem"]

    run_id = _ensure_run_id(args)

    assert run_id is not None
    assert args[:2] == ["--run-id", run_id]


def test_hidden_launcher_preserves_existing_run_id():
    args = ["--run-id", "run-fixed", "problem"]

    run_id = _ensure_run_id(args)

    assert run_id == "run-fixed"
    assert args == ["--run-id", "run-fixed", "problem"]
