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
