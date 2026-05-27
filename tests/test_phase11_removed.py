from pathlib import Path


def test_phase11_execution_modules_removed():
    skill_dir = Path(__file__).resolve().parent.parent
    assert not (skill_dir / "ai_escape_mrc" / "phases" / "phase_11_execute.py").exists()
    assert not (skill_dir / "ai_escape_mrc" / "child_runner.py").exists()


def test_active_code_does_not_invoke_executing_plans():
    skill_dir = Path(__file__).resolve().parent.parent
    active_roots = [
        skill_dir / "ai_escape_mrc",
        skill_dir / "run_ai_escape_mrc.py",
        skill_dir / "trigger_ai_escape_mrc.py",
    ]
    hits = []
    for root in active_roots:
        files = [root] if root.is_file() else root.rglob("*.py")
        for path in files:
            text = path.read_text(encoding="utf-8")
            if "superpowers:executing-plans" in text or "--mode execute" in text:
                hits.append(str(path.relative_to(skill_dir)))
    assert not hits
