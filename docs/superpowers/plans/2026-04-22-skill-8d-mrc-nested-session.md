# skill-8d-mrc Nested-Session Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `eightd/anthropic_client.py`'s `claude -p` subprocess transport with the Claude Agent SDK (`claude-agent-sdk==0.1.63`); migrate every phase caller; delete the legacy module in the same commit that finishes the migration; add a `CLAUDE_SDK_CALL=1` env short-circuit to the superpowers SessionStart hook to eliminate the ~23K-token context injection on SDK subprocess sessions.

**Architecture:** `eightd/sdk_client.py` (new) exposes synchronous `call_claude()` and `websearch()` functions with the same signatures as the legacy module. Internals use `asyncio.run()` to bridge to the SDK's async `query()`. Existing phase code and `eightd/parallel.py` thread-pool parallelism remain unchanged. One bash hook gets a one-line env guard.

**Tech Stack:** Python 3.12, `claude-agent-sdk==0.1.63`, `anthropic` (retained only for the SDK fallback path), `tenacity` (retry), `asyncio`, bash (hook patch).

**Spec:** `D:/D-claude/skills/skill-8d-mrc/docs/superpowers/specs/2026-04-22-skill-8d-mrc-nested-session-design.md`

**Deliberate deviation from spec Section 4.2:** The spec suggests converting phase functions from `def` → `async def`. This plan keeps the phase functions synchronous to minimize blast radius and preserve the existing `eightd/parallel.py` thread-pool parallelism that already works. The sync `call_claude()` bridges to the SDK's async API via `asyncio.run()` internally. Full async-native phases remain a future improvement.

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Modify | Pin `claude-agent-sdk==0.1.63` |
| `~/.claude/plugins/cache/claude-plugins-official/superpowers/*/hooks/*SessionStart*.sh` | Modify (one line) | Exit early when `CLAUDE_SDK_CALL=1` |
| `eightd/sdk_client.py` | **NEW** | Sync `call_claude` + `websearch`; async SDK bridge; schema parsing; retry; OpenRouter fallback; `_extract_json` |
| `eightd/anthropic_client.py` | **Delete** (final task, same commit) | Dead after migration |
| `eightd/phases/phase_0_research.py` … `phase_7_report.py` | Modify (import line only) | `from eightd.anthropic_client` → `from eightd.sdk_client` |
| `tests/test_sdk_client.py` | **NEW** | Unit tests for sdk_client against mocked SDK |
| `tests/test_anthropic_client.py` | **Delete** (final task) | Replaced |
| `tests/fixtures/mock_anthropic.py` | Keep unchanged | Mock shape is signature-agnostic; works on both modules |

---

## Task 1: Locate + patch superpowers SessionStart hook

**Files:**
- Locate: `~/.claude/plugins/cache/claude-plugins-official/superpowers/*/hooks/` (exact filename unknown until grep)
- Modify: the SessionStart hook script found

- [ ] **Step 1: Find the superpowers SessionStart hook**

Run:
```bash
grep -rln "SessionStart" ~/.claude/plugins/cache/claude-plugins-official/superpowers/ 2>/dev/null
```

Expected: one or more paths ending in `.sh` or `.py`. If multiple, pick the one that emits `using-superpowers` / `additionalContext` text (use `grep -l "additionalContext"` on the candidates).

Record the resolved absolute path as `HOOK_PATH` in your scratchpad for subsequent steps.

- [ ] **Step 2: Read the hook to confirm it's a bash script and identify insertion point**

Run:
```bash
head -20 "$HOOK_PATH"
```

Expected: a bash shebang (`#!/bin/bash` or `#!/usr/bin/env bash`). Note the line after the shebang / initial comments — that's the insertion point.

If the hook turns out to be Python (`.py` extension, python shebang), use the Python equivalent in Step 3: `import os, sys; os.environ.get("CLAUDE_SDK_CALL") == "1" and sys.exit(0)`.

- [ ] **Step 3: Add the short-circuit guard**

For bash, insert after the shebang and initial comments:
```bash
# Skip superpowers additionalContext injection for skill-8d-mrc SDK calls.
# Interactive sessions and normal Claude Code use continue unchanged.
[ "$CLAUDE_SDK_CALL" = "1" ] && exit 0
```

- [ ] **Step 4: Verify interactive behavior unaffected**

Run:
```bash
echo '{"hook_event_name":"SessionStart","session_id":"probe","transcript_path":""}' | bash "$HOOK_PATH"
```

Expected: non-empty JSON output containing `additionalContext`. Record `exit_code=$?`; must be 0.

- [ ] **Step 5: Verify env short-circuit works**

Run:
```bash
echo '{"hook_event_name":"SessionStart","session_id":"probe","transcript_path":""}' | CLAUDE_SDK_CALL=1 bash "$HOOK_PATH"
```

Expected: empty stdout, exit 0.

- [ ] **Step 6: Commit (auto-push hook handles the push)**

```bash
cd ~/.claude
git add plugins/cache/claude-plugins-official/superpowers/
git commit -m "feat(hooks): short-circuit superpowers SessionStart on CLAUDE_SDK_CALL=1

Adds an env-gated early exit at the top of the superpowers SessionStart
hook. When CLAUDE_SDK_CALL=1 is in env (set by skill-8d-mrc's SDK client),
the hook exits 0 without injecting additionalContext. Interactive Claude
Code sessions are unaffected (env not set)."
```

---

## Task 2: Pin SDK version in requirements.txt

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/requirements.txt`

- [ ] **Step 1: Read current requirements**

Run:
```bash
cat D:/D-claude/skills/skill-8d-mrc/requirements.txt
```

Expected: existing requirements list. Locate whether `claude-agent-sdk` is already listed.

- [ ] **Step 2: Add or update the pin**

If absent, append. If present, update.

Add line:
```
claude-agent-sdk==0.1.63
```

- [ ] **Step 3: Install**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pip install -r requirements.txt
```

Expected: `Successfully installed claude-agent-sdk-0.1.63` or `Requirement already satisfied`.

- [ ] **Step 4: Verify import**

Run:
```bash
py -3 -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"
```

Expected: `0.1.63`.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add requirements.txt
git commit -m "deps: pin claude-agent-sdk==0.1.63"
```

---

## Task 3: Create sdk_client.py skeleton (imports + constants)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`

- [ ] **Step 1: Write the skeleton**

Create `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py` with:

```python
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
```

- [ ] **Step 2: Verify import**

Run:
```bash
py -3 -c "from eightd import sdk_client; print(sdk_client._SDK_ENV)"
```

Expected: `{'CLAUDECODE': '', 'CLAUDE_SDK_CALL': '1'}`.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py
git commit -m "feat(sdk_client): add module skeleton with imports and constants"
```

---

## Task 4: Implement `_collect_messages` async helper (TDD)

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_sdk_client.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_sdk_client.py`:

```python
"""Tests for eightd.sdk_client — the Claude Agent SDK transport."""
import asyncio
from unittest.mock import patch
import pytest


class FakeTextBlock:
    def __init__(self, text):
        self.text = text


class FakeToolUseBlock:
    def __init__(self, name, input_dict):
        self.name = name
        self.input = input_dict
        # no .text — intentionally absent to mimic the real SDK shape


class FakeAssistantMessage:
    def __init__(self, content):
        self.content = content


class FakeResultMessage:
    def __init__(self, is_error=False, usage=None):
        self.is_error = is_error
        self.usage = usage or {}
        self.structured_output = None


async def _async_iter(items):
    for x in items:
        yield x


def _patch_query(messages):
    """Return a context manager that replaces claude_agent_sdk.query with a stub."""
    async def fake_query(*, prompt, options=None, **_):
        async for m in _async_iter(messages):
            yield m
    return patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw))


def test_collect_messages_extracts_text():
    from eightd.sdk_client import _collect_messages
    msgs = [FakeAssistantMessage([FakeTextBlock("hello")]), FakeResultMessage()]
    result = asyncio.run(_collect_messages(msgs))
    assert result["text"] == "hello"
    assert result["structured"] is None
    assert result["is_error"] is False


def test_collect_messages_extracts_structured_output():
    from eightd.sdk_client import _collect_messages
    msgs = [
        FakeAssistantMessage([FakeToolUseBlock("StructuredOutput", {"key": "value"})]),
        FakeResultMessage(),
    ]
    result = asyncio.run(_collect_messages(msgs))
    assert result["structured"] == {"key": "value"}
    assert result["text"] == ""


def test_collect_messages_concatenates_multiple_text_blocks():
    from eightd.sdk_client import _collect_messages
    msgs = [
        FakeAssistantMessage([FakeTextBlock("part1"), FakeTextBlock("part2")]),
        FakeResultMessage(),
    ]
    result = asyncio.run(_collect_messages(msgs))
    assert result["text"] == "part1\npart2"


def test_collect_messages_surfaces_is_error():
    from eightd.sdk_client import _collect_messages
    msgs = [FakeResultMessage(is_error=True)]
    result = asyncio.run(_collect_messages(msgs))
    assert result["is_error"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 4 tests fail with `AttributeError: module 'eightd.sdk_client' has no attribute '_collect_messages'`.

- [ ] **Step 3: Implement `_collect_messages` in sdk_client.py**

Append to `eightd/sdk_client.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk_client): add _collect_messages async helper + tests"
```

---

## Task 5: Implement async `_sdk_query` core (TDD)

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/tests/test_sdk_client.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sdk_client.py`:

```python
def test_sdk_query_plain_text():
    """_sdk_query returns dict with text when no schema."""
    from eightd import sdk_client
    msgs = [FakeAssistantMessage([FakeTextBlock("OK")]), FakeResultMessage()]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        result = asyncio.run(sdk_client._sdk_query(
            prompt="say OK", system_prompt="be brief", schema=None, timeout_sec=10, max_turns=3,
        ))
    assert result["text"] == "OK"


def test_sdk_query_passes_env_and_schema():
    """_sdk_query must construct ClaudeAgentOptions with SDK env + schema."""
    from eightd import sdk_client
    captured = {}

    async def fake_query(*, prompt, options=None, **_):
        captured["prompt"] = prompt
        captured["options"] = options
        yield FakeResultMessage()

    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        asyncio.run(sdk_client._sdk_query(
            prompt="hi", system_prompt="s", schema=schema, timeout_sec=10, max_turns=3,
        ))
    opts = captured["options"]
    assert opts.env == {"CLAUDECODE": "", "CLAUDE_SDK_CALL": "1"}
    assert opts.setting_sources is None
    assert opts.output_format == {"type": "json_schema", "schema": schema}
    assert opts.system_prompt == "s"
    assert opts.max_turns == 3


def test_sdk_query_times_out():
    """_sdk_query raises TimeoutError when query exceeds timeout_sec."""
    from eightd import sdk_client

    async def slow_query(**kw):
        await asyncio.sleep(2.0)
        yield FakeResultMessage()

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: slow_query(**kw)):
        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(sdk_client._sdk_query(
                prompt="p", system_prompt="s", schema=None, timeout_sec=0.1, max_turns=3,
            ))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: 3 new failures (`_sdk_query` not defined).

- [ ] **Step 3: Implement `_sdk_query` in sdk_client.py**

Append to `eightd/sdk_client.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk_client): add async _sdk_query with options construction + timeout"
```

---

## Task 6: Implement `_extract_json` + `_dump_parse_failure` helpers

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/tests/test_sdk_client.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sdk_client.py`:

```python
def test_extract_json_bare_object():
    from eightd.sdk_client import _extract_json
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    from eightd.sdk_client import _extract_json
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_embedded_in_prose():
    from eightd.sdk_client import _extract_json
    assert _extract_json('Here is it: {"a": 1} end.') == {"a": 1}


def test_extract_json_raises_on_garbage():
    import json as _j
    from eightd.sdk_client import _extract_json
    with pytest.raises(_j.JSONDecodeError):
        _extract_json("no json here at all")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v -k extract_json
```

Expected: 4 failures (`_extract_json` not defined).

- [ ] **Step 3: Port helpers from anthropic_client.py**

Append to `eightd/sdk_client.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 11 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk_client): port _extract_json + _dump_parse_failure helpers"
```

---

## Task 7: Implement OpenRouter fallback helpers

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`

- [ ] **Step 1: Port OpenRouter helpers**

Append to `eightd/sdk_client.py`:

```python
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


def _call_openrouter_websearch(query: str, max_tokens: int) -> str:
    """Fallback: websearch via OpenRouter :online model variants."""
    import openai
    client = openai.OpenAI(api_key=_openrouter_key(), base_url="https://openrouter.ai/api/v1")
    resp = client.chat.completions.create(
        model="anthropic/claude-sonnet-4:online",
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": f"Search: {query}\n\nProvide top 3 findings with source URLs and brief summaries.",
        }],
    )
    return resp.choices[0].message.content or ""
```

- [ ] **Step 2: Verify imports**

Run:
```bash
py -3 -c "from eightd.sdk_client import _translate_model_for_openrouter as t; assert t('claude-opus-4-6') == 'anthropic/claude-opus-4'; assert t('claude-sonnet-4-6-20260101') == 'anthropic/claude-sonnet-4'; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py
git commit -m "feat(sdk_client): port OpenRouter fallback helpers"
```

---

## Task 8: Implement sync `call_claude` public API (TDD)

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/tests/test_sdk_client.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sdk_client.py`:

```python
def test_call_claude_text_mode_returns_string():
    from eightd import sdk_client
    msgs = [FakeAssistantMessage([FakeTextBlock("a bullet")]), FakeResultMessage()]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        result = sdk_client.call_claude(
            model="claude-opus-4-6", system="s", user="u", purpose="test",
        )
    assert result == "a bullet"


def test_call_claude_schema_mode_returns_dict():
    from eightd import sdk_client
    msgs = [
        FakeAssistantMessage([FakeToolUseBlock("StructuredOutput", {"k": 1})]),
        FakeResultMessage(),
    ]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    schema = {"type": "object", "properties": {"k": {"type": "integer"}}}
    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        result = sdk_client.call_claude(
            model="claude-opus-4-6", system="s", user="u",
            json_schema=schema, purpose="test",
        )
    assert result == {"k": 1}


def test_call_claude_parse_json_mode_extracts_object():
    from eightd import sdk_client
    msgs = [
        FakeAssistantMessage([FakeTextBlock('Here: {"a": 1} done.')]),
        FakeResultMessage(),
    ]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        result = sdk_client.call_claude(
            model="claude-opus-4-6", system="s", user="u",
            parse_json=True, purpose="test",
        )
    assert result == {"a": 1}


def test_call_claude_empty_text_raises():
    from eightd import sdk_client
    msgs = [FakeResultMessage()]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        with pytest.raises(RuntimeError, match="empty"):
            sdk_client.call_claude(
                model="claude-opus-4-6", system="s", user="u", purpose="test",
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v -k call_claude
```

Expected: 4 new failures (`call_claude` not defined).

- [ ] **Step 3: Implement `call_claude`**

Append to `eightd/sdk_client.py`:

```python
def _should_retry(retry_state) -> bool:
    """Retry on transport/network errors, NOT on JSONDecodeError.

    JSON parse failures are deterministic given same prompt.
    """
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if exc is None:
        return False
    if isinstance(exc, json.JSONDecodeError):
        return False
    return True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30),
       retry=_should_retry)
def call_claude(
    model: str,
    system: str,
    user: str,
    parse_json: bool = False,
    max_tokens: int = 8000,
    temperature: float = 0.3,
    purpose: str = "unknown",
    allow_tools: bool = False,
    json_schema: dict | None = None,
):
    """Call Claude via the Agent SDK. Drop-in replacement for the legacy
    anthropic_client.call_claude.

    Signature and return shapes match the legacy module:
      - text mode           -> str
      - json_schema != None -> dict (schema-conformant)
      - parse_json=True     -> dict (best-effort JSON parse)

    `model`, `max_tokens`, `temperature`, `allow_tools` are accepted for
    signature compatibility with the legacy caller. The SDK version ignores
    model/max_tokens/temperature (delegated to the claude CLI's own model
    selection); `allow_tools` is currently unused because this skill never
    needs WebSearch inside a schema call (websearch() is the dedicated path).

    On SDK failure (timeout, non-retryable error), falls through to
    OpenRouter — preserving the existing resilience guarantee.
    """
    _emit("llm", "llm_call_start",
          {"purpose": purpose, "prompt_len": len(user)}, model=model)

    try:
        result = asyncio.run(_sdk_query(
            prompt=user,
            system_prompt=system.rstrip(),
            schema=json_schema,
            timeout_sec=300,
            max_turns=3,
        ))
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(
            f"[WARN] SDK failed ({purpose}): {type(e).__name__}: {str(e)[:200]}; "
            "falling back to OpenRouter\n"
        )
        text = _call_openrouter_text(model, system, user, max_tokens, temperature)
        _emit("llm", "llm_call_end",
              {"purpose": purpose, "text_len": len(text)}, model=model)
        if json_schema is not None or parse_json:
            return _extract_json(text)
        return text

    if json_schema is not None:
        so = result.get("structured")
        if so is None:
            raise RuntimeError(
                f"SDK schema call returned no structured output "
                f"(is_error={result['is_error']}, text_len={len(result['text'])})"
            )
        _emit("llm", "llm_call_end",
              {"purpose": purpose, "text_len": len(json.dumps(so))}, model=model)
        return so

    text = result["text"]
    if not text:
        raise RuntimeError(
            f"SDK returned empty text (is_error={result['is_error']}, "
            f"purpose={purpose})"
        )

    _emit("llm", "llm_call_end",
          {"purpose": purpose, "text_len": len(text)}, model=model)

    if parse_json:
        try:
            return _extract_json(text)
        except json.JSONDecodeError:
            _dump_parse_failure(text, f"{purpose}_first_attempt")
            raise
    return text
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 15 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk_client): implement sync call_claude with retry + OpenRouter fallback"
```

---

## Task 9: Implement `websearch` (TDD)

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/sdk_client.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/tests/test_sdk_client.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sdk_client.py`:

```python
def test_websearch_returns_expected_shape():
    from eightd import sdk_client
    msgs = [
        FakeAssistantMessage([FakeTextBlock("- result 1\n- result 2")]),
        FakeResultMessage(),
    ]

    async def fake_query(**kw):
        for m in msgs:
            yield m

    with patch("eightd.sdk_client.query", side_effect=lambda **kw: fake_query(**kw)):
        out = sdk_client.websearch("site:example.com topic")
    assert out["query"] == "site:example.com topic"
    assert "- result 1" in out["results"]
    assert isinstance(out["timestamp"], float)
```

- [ ] **Step 2: Run to verify fail**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v -k websearch
```

Expected: failure (`websearch` not defined).

- [ ] **Step 3: Implement websearch**

Append to `eightd/sdk_client.py`:

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def websearch(query_text: str, max_tokens: int = 4000) -> dict:
    """Web search via Agent SDK. Returns {query, results, timestamp}.

    Drop-in replacement for anthropic_client.websearch. Uses SDK with
    WebSearch tool permitted; on SDK failure falls through to OpenRouter
    :online model.
    """
    _emit("websearch", "search_start", {"query": query_text[:80]})

    system_prompt = "You are a web research assistant. Use the WebSearch tool when asked."
    user_prompt = (
        f"Please use the WebSearch tool to search for: {query_text}\n\n"
        "Then provide the top 3 findings with source URLs and brief summaries. "
        "Format as plain text with clear URL citations."
    )

    try:
        opts = ClaudeAgentOptions(
            system_prompt=system_prompt,
            setting_sources=None,
            allowed_tools=["WebSearch"],
            max_turns=5,
            env=dict(_SDK_ENV),
        )

        async def _run():
            return await _collect_messages(query(prompt=user_prompt, options=opts))

        result = asyncio.run(asyncio.wait_for(_run(), timeout=180))
        text = result["text"]
        if not text:
            raise RuntimeError("SDK websearch returned empty text")
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(
            f"[WARN] SDK websearch failed: {type(e).__name__}: {str(e)[:200]}; "
            "falling back to OpenRouter :online\n"
        )
        text = _call_openrouter_websearch(query_text, max_tokens)

    _emit("websearch", "search_end",
          {"query": query_text[:80], "text_len": len(text)})
    return {
        "query": query_text,
        "results": text.strip(),
        "timestamp": time.time(),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_sdk_client.py -v
```

Expected: all 16 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk_client): implement websearch with OpenRouter fallback"
```

---

## Task 10: Live smoke test of sdk_client

**Files:** (read-only smoke)

- [ ] **Step 1: Run the existing POC to confirm SDK is healthy**

Run:
```bash
py -3 D:/D-claude/skills/skill-8d-mrc/poc/sdk_subagent_probe.py
```

Expected: `SUMMARY` line shows `PASS` on all 5 tests (auth, narrow-scope, simple schema, nested schema, parallelism).

- [ ] **Step 2: Directly smoke-test the new sdk_client**

Run:
```bash
py -3 -c "
from eightd.sdk_client import call_claude, websearch
r = call_claude(model='claude-opus-4-6', system='reply with OK', user='go', purpose='smoke')
print('TEXT:', repr(r))
w = websearch('claude agent sdk 2026')
print('SEARCH text_len:', len(w['results']))
"
```

Expected: `TEXT: 'OK'` (case-insensitive), `SEARCH text_len:` > 0.

- [ ] **Step 3: No commit — this is a verification step**

Skip if both smokes pass. If anything fails, escalate to the user with the failure output.

---

## Task 11: Migrate phase_0_research.py import

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_0_research.py:9`

- [ ] **Step 1: Replace the import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_0_research.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude, websearch',
              'from eightd.sdk_client import call_claude, websearch')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Run phase_0 tests**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_0.py -v
```

Expected: all tests pass (existing mock pattern is signature-agnostic).

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_0_research.py
git commit -m "refactor(phase_0): migrate import to sdk_client"
```

---

## Task 12: Migrate phase_1_is_isnt.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_1_is_isnt.py:3`

- [ ] **Step 1: Replace the import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_1_is_isnt.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Verify no phase_1 test broke**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/ -v -k "phase_1 or test_graph_topology or test_models" --no-header
```

Expected: tests pass or report "no tests ran matching".

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_1_is_isnt.py
git commit -m "refactor(phase_1): migrate import to sdk_client"
```

---

## Task 13: Migrate phase_2_why_analysis.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_2_why_analysis.py:2`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_2_why_analysis.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Run phase_2 tests**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_2_exit.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_2_why_analysis.py
git commit -m "refactor(phase_2): migrate import to sdk_client"
```

---

## Task 14: Migrate phase_3_rc_audit.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_3_rc_audit.py:12`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_3_rc_audit.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Run phase_3 tests**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_3_loop.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_3_rc_audit.py
git commit -m "refactor(phase_3): migrate import to sdk_client"
```

---

## Task 15: Migrate phase_4_actions.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_4_actions.py:12`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_4_actions.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Run phase_4 tests**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_4_actions.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_4_actions.py
git commit -m "refactor(phase_4): migrate import to sdk_client"
```

---

## Task 16: Migrate phase_5_prevention_audit.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_5_prevention_audit.py:7`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_5_prevention_audit.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Verify no breakage**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -c "from eightd.phases import phase_5_prevention_audit; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_5_prevention_audit.py
git commit -m "refactor(phase_5): migrate import to sdk_client"
```

---

## Task 17: Migrate phase_6_verification.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_6_verification.py:7`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_6_verification.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Run phase_6 tests**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_6_proof.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_6_verification.py
git commit -m "refactor(phase_6): migrate import to sdk_client"
```

---

## Task 18: Migrate phase_7_report.py

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_report.py:8`

- [ ] **Step 1: Replace import**

Run:
```bash
py -3 -c "
p = 'D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_report.py'
s = open(p, encoding='utf-8').read()
s = s.replace('from eightd.anthropic_client import call_claude',
              'from eightd.sdk_client import call_claude')
open(p, 'w', encoding='utf-8').write(s)
print('done')
"
```

Expected: `done`.

- [ ] **Step 2: Confirm import**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -c "from eightd.phases import phase_7_report; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/phases/phase_7_report.py
git commit -m "refactor(phase_7): migrate import to sdk_client"
```

---

## Task 19: Delete legacy module + legacy tests in same commit

**Files:**
- Delete: `D:/D-claude/skills/skill-8d-mrc/eightd/anthropic_client.py`
- Delete: `D:/D-claude/skills/skill-8d-mrc/tests/test_anthropic_client.py`

Per the function-replacement-convention wiki (referenced in the spec), this is the critical "delete in the same commit" step. It enforces migration via `NameError` at import time.

- [ ] **Step 1: Verify no code still imports anthropic_client**

Run:
```bash
cd /d/D-claude/skills/skill-8d-mrc && grep -rn "anthropic_client" eightd/ tests/ run_8d.py 2>/dev/null | grep -v __pycache__ | grep -v ".pyc"
```

Expected: **no output** (zero hits in source files). If any hit appears, STOP and fix that caller first.

- [ ] **Step 2: Delete the legacy module**

Run:
```bash
rm D:/D-claude/skills/skill-8d-mrc/eightd/anthropic_client.py
rm D:/D-claude/skills/skill-8d-mrc/tests/test_anthropic_client.py
```

- [ ] **Step 3: Run the full test suite**

Run:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/ -v
```

Expected: all tests pass. Any `ImportError` or `ModuleNotFoundError` referencing `anthropic_client` means Step 1 was missed — locate and fix the caller, then rerun.

- [ ] **Step 4: Confirm with grep that no reference survived**

Run:
```bash
cd /d/D-claude/skills/skill-8d-mrc && grep -rn "anthropic_client" eightd/ tests/ run_8d.py 2>/dev/null | grep -v __pycache__
```

Expected: no output.

- [ ] **Step 5: Commit — this is the cutover commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add -A
git commit -m "refactor: delete legacy anthropic_client subprocess CLI transport

Per function-replacement-convention wiki: delete the replaced module in
the same commit that finishes the migration. All phase callers now import
from eightd.sdk_client. NameError at import time now enforces correctness
across all call sites (Level 1 architectural elimination).

Rollback path: git revert this SHA."
```

---

## Task 20: End-to-end smoke run

**Files:** (no changes, observation only)

- [ ] **Step 1: Run the pipeline on a small fixture problem**

Run (in a terminal window that is NOT inside a Claude Code session, if available; otherwise proceed — CLAUDE_SDK_CALL workaround should still apply):
```bash
cd D:/D-claude/skills/skill-8d-mrc
py -3 run_8d.py "Test: a small synthetic problem for the smoke run"
```

Expected: pipeline completes in < 20 minutes wall clock. Output report written to `docs/8d-reports/8d-YYYY-MM-DD-*.md`.

If the run exceeds 30 minutes, STOP and capture:
- The last 200 lines of `runs/<id>/progress.jsonl`
- The `ResultMessage.usage.cache_creation_input_tokens` (check via a one-off probe) to confirm < 3K (proves SessionStart short-circuit is working)
- Escalate.

- [ ] **Step 2: Inspect progress.jsonl for parallelism evidence**

Run:
```bash
py -3 -c "
import json, sys
from pathlib import Path
runs = sorted(Path('D:/D-claude/skills/skill-8d-mrc/runs').glob('*/progress.jsonl'))
if not runs:
    sys.exit('no runs')
lines = runs[-1].read_text(encoding='utf-8').splitlines()
events = [json.loads(l) for l in lines if l.strip()]
starts = [e for e in events if e.get('event') in ('llm_call_start', 'search_start')]
print(f'run: {runs[-1].parent.name}')
print(f'total events: {len(events)}')
print(f'calls started: {len(starts)}')
# Overlap check: any two consecutive starts within 1 second = parallelism proof
from itertools import islice
for a, b in zip(starts, list(starts)[1:]):
    dt = b['ts'] - a['ts']
    if dt < 1.0:
        print(f'OVERLAPPING starts detected: {a.get(\"purpose\") or a.get(\"query\", \"\")[:40]} + {b.get(\"purpose\") or b.get(\"query\",\"\")[:40]} (dt={dt:.3f}s)')
        break
else:
    print('WARNING: no overlapping starts — parallelism may be degraded')
"
```

Expected: `OVERLAPPING starts detected: ...` appears — proves thread-pool parallelism survived the refactor. (If degraded, it is acceptable to proceed since per-call latency under SDK is already expected to be lower; log as an observation rather than a blocker.)

- [ ] **Step 3: No commit — verification only**

If steps 1 and 2 pass, the refactor is complete. If any fail, escalate.

---

## Self-Review

**Spec coverage check:**

| Spec section | Implementing task(s) |
|---|---|
| §3 Decision (SDK + env short-circuit) | Task 1 (hook patch), Task 3 (sdk_client env constants) |
| §4.1 Process topology | Tasks 3–9 (sdk_client construction), 11–18 (phase migration) |
| §4.2 Module-level changes | All tasks; Task 19 is the cutover |
| §4.3 sdk_client.py contract | Tasks 3–9 |
| §4.4 Env short-circuit | Task 1 |
| §4.5 Parallelism | Inherited from unchanged `eightd/parallel.py`; verified in Task 20 Step 2 |
| §4.6 Schema handling / StructuredOutput | Task 4 (_collect_messages), Task 5 (_sdk_query), Task 8 (call_claude) |
| §5 Execution modes | Task 20 verifies end-to-end |
| §6 Rollout (no flag, delete in same commit) | Task 19 |
| §7 Testing — unit | Tasks 4, 5, 6, 8, 9 |
| §7 Testing — integration | Task 10, Task 20 |
| §8 Risks | Addressed: `StructuredOutput` name fallback (not implemented beyond the primary path — if the tool name changes, the SDK error message will surface immediately; explicit fallback can be added if an incident occurs) |
| §10 Verification item 7 (grep returns no hits) | Task 19 Step 4 |

**Placeholder scan:** none found. No TBD/TODO/"handle edge cases"/"similar to above" language.

**Type consistency:** `call_claude` return types (`str | dict`) match legacy signature throughout. `websearch` return shape `{query, results, timestamp}` consistent across Tasks 9 and phases.

**Scope:** single subsystem (skill-8d-mrc LLM transport). Does not require decomposition.

---

## Execution Handoff

Plan complete and saved to `D:/D-claude/skills/skill-8d-mrc/docs/superpowers/plans/2026-04-22-skill-8d-mrc-nested-session.md`.

**Next:** Pipeline flows into `superpowers:subagent-driven-development` per user's pre-authorization. Fresh subagent per task, two-stage review between each.
