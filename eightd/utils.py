"""File ops, slug generation, prompt loading."""
import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def sluggify(text: str, max_len: int = 60) -> str:
    """Convert text to URL-safe slug."""
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:max_len]


def load_prompt(name: str) -> str:
    """Load a prompt template from prompts/ directory."""
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def safe_read_text(path: Path) -> str:
    """Read a file; return empty string if missing or unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""
