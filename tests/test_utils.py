from pathlib import Path
from eightd.utils import sluggify, load_prompt, safe_read_text


def test_sluggify_basic():
    assert sluggify("Hello World") == "hello-world"


def test_sluggify_removes_special():
    assert sluggify("Daily Brief: Pipeline Empty!") == "daily-brief-pipeline-empty"


def test_sluggify_truncates():
    long = "a" * 100
    assert len(sluggify(long, max_len=50)) == 50


def test_load_prompt_reads_file(tmp_path, monkeypatch):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "foo.txt").write_text("Hello prompt", encoding="utf-8")
    monkeypatch.setattr("eightd.utils.PROMPTS_DIR", prompts_dir)
    assert load_prompt("foo") == "Hello prompt"


def test_safe_read_text_missing_returns_empty():
    assert safe_read_text(Path("/nonexistent/path")) == ""


def test_safe_read_text_reads_utf8(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("中文 content", encoding="utf-8")
    assert safe_read_text(f) == "中文 content"
