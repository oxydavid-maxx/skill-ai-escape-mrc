"""Thin Anthropic client wrapper with retry + JSON extraction + websearch."""
import json
import re
import time
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

_client = Anthropic()


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
