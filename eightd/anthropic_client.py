"""Thin Anthropic client wrapper with retry + JSON extraction + websearch."""
import json
import os
import re
import time
from pathlib import Path
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential


def _resolve_api_key() -> str:
    """Priority: ANTHROPIC_API_KEY env -> daily_brief config.yaml anthropic.api_key -> env ANTHROPIC fallback."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    cfg_path = Path("D:/D-claude/daily_brief/config.yaml")
    if cfg_path.exists():
        try:
            import yaml
            with open(cfg_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            k = (cfg.get("anthropic") or {}).get("api_key", "")
            if k:
                return k.strip()
        except Exception:
            pass
    return ""


_api_key = _resolve_api_key()
if _api_key:
    _client = Anthropic(api_key=_api_key)
else:
    _client = Anthropic()  # will raise on first call if no key discoverable


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def call_claude(
    model: str,
    system: str,
    user: str,
    parse_json: bool = False,
    max_tokens: int = 8000,
    temperature: float = 0.3,
):
    """Call Anthropic messages API with retry. Optionally parse JSON from response."""
    resp = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text
    if parse_json:
        return _extract_json(text)
    return text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def websearch(query: str, max_tokens: int = 4000) -> dict:
    """Execute a web search via Anthropic's web_search tool. Returns structured dict."""
    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }],
        messages=[{
            "role": "user",
            "content": (
                f"Search: {query}\n\n"
                "Provide top 3 findings with source URLs and brief summaries."
            ),
        }],
    )
    text = ""
    for block in resp.content:
        if hasattr(block, "text"):
            text += block.text + "\n"
    return {
        "query": query,
        "results": text.strip(),
        "timestamp": time.time(),
    }


def _extract_json(text: str):
    """Robust JSON extraction — handles fenced code blocks with/without language tag."""
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    return json.loads(text.strip())
