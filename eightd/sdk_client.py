"""Claude Agent SDK transport for skill-8d-mrc.

Replaces eightd/anthropic_client.py's subprocess CLI pattern with the official
claude-agent-sdk. Same external surface (sync call_claude, websearch) so phases
don't need async conversion.

Design contract:
- Synchronous API (call_claude, websearch) — internally bridges to async SDK via asyncio.run.
- env={"CLAUDECODE":"", "CLAUDE_SDK_CALL":"1"} on every SDK call:
    - CLAUDECODE="" bypasses the nested-session rejection (Issue #573).
    - CLAUDE_SDK_CALL="1" triggers the superpowers SessionStart short-circuit.
- setting_sources=None → no CLAUDE.md / auto-memory loading.
- output_format={"type":"json_schema","schema":schema} → Claude emits schema
  data as a ToolUseBlock(name="StructuredOutput", input={...}) inside the
  AssistantMessage content, not on ResultMessage.structured_output.
- max_turns >= 2 required when schema is used (tool_use + tool_result cycle).
- OpenRouter fallback preserved for API-error cases.
- progress events emitted via eightd.progress (same contract as before).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query
from tenacity import retry, stop_after_attempt, wait_exponential


# Environment handed to every SDK call. Do not mutate per-call.
_SDK_ENV: dict[str, str] = {
    "CLAUDECODE": "",
    "CLAUDE_SDK_CALL": "1",
}


def _emit(channel: str, event: str, payload: dict, **extra: Any) -> None:
    """Best-effort progress event emit. Matches anthropic_client.py contract."""
    try:
        from eightd import progress as _p
        _p.emit(channel, event, payload, **extra)
    except Exception:
        pass


async def _collect_messages(msg_iter) -> dict:
    """Iterate an SDK message async-iterator, return aggregated result.

    Returns dict with keys:
      text       - str, concatenation of all TextBlock.text (joined by '\n')
      structured - dict | None, from the first ToolUseBlock named "StructuredOutput"
      is_error   - bool, final ResultMessage.is_error (or False if absent)
      usage      - dict, final ResultMessage.usage (or {} if absent)
    """
    text_parts: list[str] = []
    structured: dict | None = None
    is_error = False
    usage: dict = {}

    async for msg in msg_iter:
        content = getattr(msg, "content", None)
        if isinstance(content, list):
            for block in content:
                t = getattr(block, "text", None)
                if t:
                    text_parts.append(t)
                if getattr(block, "name", None) == "StructuredOutput":
                    structured = getattr(block, "input", None)
        if hasattr(msg, "is_error"):
            is_error = bool(getattr(msg, "is_error", False))
        if hasattr(msg, "usage"):
            u = getattr(msg, "usage", None)
            if isinstance(u, dict):
                usage = u

    return {
        "text": "\n".join(text_parts),
        "structured": structured,
        "is_error": is_error,
        "usage": usage,
    }


async def _sdk_query(
    *,
    prompt: str,
    system_prompt: str,
    schema: dict | None,
    timeout_sec: int,
    max_turns: int,
) -> dict:
    """Run one SDK query with skill-8d-mrc's standard options.

    Returns the dict produced by `_collect_messages`.
    Raises asyncio.TimeoutError on timeout.
    """
    opts_kwargs: dict[str, Any] = dict(
        system_prompt=system_prompt,
        setting_sources=None,
        allowed_tools=[],
        max_turns=max_turns,
        env=dict(_SDK_ENV),
    )
    if schema is not None:
        opts_kwargs["output_format"] = {"type": "json_schema", "schema": schema}

    options = ClaudeAgentOptions(**opts_kwargs)

    async def _run():
        return await _collect_messages(query(prompt=prompt, options=options))

    return await asyncio.wait_for(_run(), timeout=timeout_sec)


def _dump_parse_failure(text: str, context: str = "") -> None:
    """Save failed text to runs/_parse_failures/ for post-mortem.

    Mirrors anthropic_client.py:_dump_parse_failure. Best-effort only.
    """
    try:
        import datetime
        dump_dir = Path(__file__).parent.parent / "runs" / "_parse_failures"
        dump_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dump = dump_dir / f"{ts}_{context}.txt"
        dump.write_text(text, encoding="utf-8")
    except Exception:
        pass


def _extract_json(text: str):
    """Robust JSON extraction with multiple fallback strategies.

    Strategies tried in order:
      1. Bare JSON (standalone object or array)
      2. Fenced code block (```json ... ``` or plain ```)
      3. Embedded in prose (outermost balanced braces/brackets)

    Raises json.JSONDecodeError if all strategies fail; also dumps to
    runs/_parse_failures/ for debugging.
    """
    if not text or not text.strip():
        raise json.JSONDecodeError("empty input", text or "", 0)

    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    for pat in (
        r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```",
        r"```\s*(\{.*?\}|\[.*?\])\s*```",
    ):
        m = re.search(pat, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue

    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        while start != -1:
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape:
                    escape = False
                    continue
                if ch == "\\" and in_string:
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
            start = text.find(open_ch, start + 1)

    _dump_parse_failure(text, "extract_json_all_strategies_failed")
    raise json.JSONDecodeError(
        f"no valid JSON found in text (first 300 chars: {text[:300]!r})",
        text,
        0,
    )


def _translate_model_for_openrouter(model: str) -> str:
    """Translate Anthropic model ID to OpenRouter format.

    Examples:
      claude-opus-4-6 -> anthropic/claude-opus-4
      claude-sonnet-4-6 -> anthropic/claude-sonnet-4
      claude-haiku-4-5-20251001 -> anthropic/claude-3.5-haiku
    """
    m = model.lower()
    m = re.sub(r"-\d{8}$", "", m)
    if "opus" in m:
        return "anthropic/claude-opus-4"
    if "sonnet" in m:
        return "anthropic/claude-sonnet-4"
    if "haiku" in m:
        return "anthropic/claude-3.5-haiku"
    return "anthropic/claude-sonnet-4"


def _openrouter_key() -> str:
    """Resolve OpenRouter API key from config.yaml or env. Raises if absent."""
    try:
        import yaml
        cfg_path = Path("D:/D-claude/daily_brief/config.yaml")
        if cfg_path.exists():
            with open(cfg_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            k = (cfg.get("openrouter") or {}).get("api_key", "")
            if k:
                return k.strip()
    except Exception:
        pass
    k = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not k:
        raise RuntimeError("No OpenRouter key available (neither config.yaml nor env)")
    return k


def _call_openrouter_text(
    model: str, system: str, user: str, max_tokens: int, temperature: float
) -> str:
    """Fallback: plain text LLM call via OpenRouter's OpenAI-compatible API."""
    import openai
    client = openai.OpenAI(api_key=_openrouter_key(), base_url="https://openrouter.ai/api/v1")
    resp = client.chat.completions.create(
        model=_translate_model_for_openrouter(model),
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_openrouter_websearch(query_text: str, max_tokens: int) -> str:
    """Fallback: websearch via OpenRouter :online model variants."""
    import openai
    client = openai.OpenAI(api_key=_openrouter_key(), base_url="https://openrouter.ai/api/v1")
    resp = client.chat.completions.create(
        model="anthropic/claude-sonnet-4:online",
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": f"Search: {query_text}\n\nProvide top 3 findings with source URLs and brief summaries.",
        }],
    )
    return resp.choices[0].message.content or ""
