"""Thin Anthropic client wrapper with retry + JSON extraction + websearch.

Priority chain for LLM calls:
1. ANTHROPIC_API_KEY env var  -> direct SDK (fastest)
2. daily_brief config.yaml anthropic.api_key -> direct SDK
3. claude CLI subprocess      -> uses Claude Code subscription (no extra cost)

## CLAUDECODE env note

When this module is invoked from inside a Claude Code Bash subprocess
(e.g. run_8d.py called via Bash tool), the parent env has CLAUDECODE=1
set. Child `claude` CLI detects this and refuses to launch with
"Claude Code cannot be launched inside another Claude Code session" —
producing a SILENT HANG via subprocess.run (child dies writing error
to stderr but parent blocks reading).

Documented fix: strip CLAUDECODE + CLAUDE_CODE_ENTRYPOINT from child env.
Source: anthropics/claude-agent-sdk-python Issue #573
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential


def _resolve_api_key() -> str:
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
# On Windows, prefer .cmd (npm wrapper) over bare "claude" (bash script)
def _find_claude_cli() -> str | None:
    if os.name == "nt":
        for candidate in [
            Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd",
            Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd",
        ]:
            if candidate.exists():
                return str(candidate)
    return shutil.which("claude")
_CLAUDE_PATH = _find_claude_cli()
# EIGHTD_FORCE_OPENROUTER=1 bypasses CLI entirely and routes all calls through
# OpenRouter. Used when CLI is intermittently returning empty stdout on long
# prompts (observed issue). Validates the pipeline structure without fighting
# CLI flakiness.
_FORCE_OPENROUTER = os.environ.get("EIGHTD_FORCE_OPENROUTER", "").strip() == "1"
USE_CLI = not _api_key and _CLAUDE_PATH is not None and not _FORCE_OPENROUTER
_client = Anthropic(api_key=_api_key) if _api_key else None


ALL_TOOLS_TO_BLOCK = [
    "Task", "Bash", "Edit", "Read", "Write",
    "WebSearch", "WebFetch", "Grep", "Glob", "NotebookEdit",
]
BLOCK_EXCEPT_WEBSEARCH = [
    "Task", "Bash", "Edit", "Read", "Write",
    "WebFetch", "Grep", "Glob", "NotebookEdit",
]


def _call_cli(system: str, user: str, model: str | None = None,
              timeout: int = 300, allow_websearch: bool = False,
              json_schema: dict | None = None):
    """Call Claude via CLI subprocess. Uses user's Claude Code subscription.

    Two modes:

    1. Text mode (json_schema=None): returns str.
       Uses --output-format text. Claude returns whatever it writes.
       Use for report generation, free-form content.

    2. Structured mode (json_schema != None): returns parsed dict.
       Uses --output-format json + --json-schema <schema>.
       Claude CLI uses constrained decoding — output is guaranteed to match
       the schema. Parses the multi-message array stdout and returns the
       `structured_output` field of the result message.
       This is the 2026 best practice per https://claudelog.com/faqs/what-
       is-output-format-in-claude-code/ — no parse retry, no prompt gymnastics.

    IMPORTANT: system and user are passed SEPARATELY via --system-prompt
    flag and stdin. Concatenated prompts trigger "System:" injection guard.

    Tools are BLOCKED by default via --disallowedTools. Without this,
    Claude's agent-mode default ignores narrow system prompts in favor of
    researching the user problem substantively.

    MUST strip CLAUDECODE + CLAUDE_CODE_ENTRYPOINT from child env.
    """
    import sys as _sys
    child_env = os.environ.copy()
    child_env.pop("CLAUDECODE", None)
    child_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    # --setting-sources project: skip loading ~/.claude/CLAUDE.md (which
    # @includes the 5KB wiki index and bloats every call's context). Keep
    # project-level CLAUDE.md so Claude still understands the codebase
    # conventions. Empirical speedup: ~140s → ~38s per call.
    args = [_CLAUDE_PATH, "-p",
            "--system-prompt", system,
            "--setting-sources", "project"]
    if json_schema is not None:
        # Schema mode: the CLI's internal "StructuredOutput" tool is what
        # emits schema-conformant output. Whitelist it (plus WebSearch if
        # the audit phase wants it) so Claude doesn't Task/Read/Bash for
        # open-ended research.
        allowed = ["StructuredOutput"]
        if allow_websearch:
            allowed.append("WebSearch")
        args.extend(["--output-format", "json",
                     "--json-schema", json.dumps(json_schema),
                     "--allowedTools", *allowed])
    else:
        # Text mode: block all non-whitelisted tools.
        blocked = BLOCK_EXCEPT_WEBSEARCH if allow_websearch else ALL_TOOLS_TO_BLOCK
        args.extend(["--output-format", "text",
                     "--disallowedTools", *blocked])
    if model:
        args.extend(["--model", model])

    result = subprocess.run(
        args,
        input=user,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        shell=False,
        env=child_env,
    )

    if json_schema is not None:
        # stdout is a JSON array of messages: [init, assistant, result]
        # Find the result message and return its structured_output field.
        try:
            messages = json.loads(result.stdout)
        except Exception as e:
            raise RuntimeError(
                f"claude CLI json-schema mode: stdout not JSON "
                f"(rc={result.returncode}): {result.stdout[:400]!r}"
            ) from e
        if not isinstance(messages, list):
            raise RuntimeError(
                f"claude CLI json-schema mode: expected list, got "
                f"{type(messages).__name__}: {str(messages)[:300]}"
            )
        for msg in messages:
            if isinstance(msg, dict) and msg.get("type") == "result":
                if msg.get("is_error"):
                    raise RuntimeError(
                        f"claude CLI returned error result: {msg.get('result', '')[:500]}"
                    )
                so = msg.get("structured_output")
                if so is None:
                    raise RuntimeError(
                        f"claude CLI result missing structured_output: {list(msg.keys())}"
                    )
                return so
        raise RuntimeError(
            f"claude CLI: no result message in output (types: "
            f"{[m.get('type') for m in messages if isinstance(m, dict)]})"
        )

    # Text mode
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed (rc={result.returncode}): {result.stderr[:500]}")
    out = result.stdout.strip()
    if not out:
        _sys.stderr.write(
            f"[WARN] claude CLI returned empty stdout. "
            f"rc={result.returncode} stderr_preview={result.stderr[:300]!r} "
            f"system_preview={system[:100]!r} user_preview={user[:100]!r}\n"
        )
        raise RuntimeError("claude CLI returned empty stdout")
    return out


def _call_openrouter_websearch(query: str, max_tokens: int) -> str:
    """OpenRouter has `:online` model variants with built-in web search."""
    try:
        import yaml
        cfg_path = Path("D:/D-claude/daily_brief/config.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        or_key = (cfg.get("openrouter") or {}).get("api_key", "")
    except Exception:
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not or_key:
        raise RuntimeError("No OpenRouter key for websearch fallback")

    import openai
    or_client = openai.OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
    resp = or_client.chat.completions.create(
        model="anthropic/claude-sonnet-4:online",  # :online enables web search; sonnet for search-summary is sufficient and avoids opus cost overruns. User directive: no haiku.
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": f"Search: {query}\n\nProvide top 3 findings with source URLs and brief summaries.",
        }],
    )
    return resp.choices[0].message.content or ""


def _call_openrouter(model: str, system: str, user: str, max_tokens: int, temperature: float) -> str:
    """Fallback: OpenRouter via OpenAI-compatible API."""
    try:
        import yaml
        cfg_path = Path("D:/D-claude/daily_brief/config.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        or_key = (cfg.get("openrouter") or {}).get("api_key", "")
    except Exception:
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not or_key:
        raise RuntimeError("No OpenRouter key available")

    import openai
    or_client = openai.OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
    or_model = _translate_model_for_openrouter(model)
    resp = or_client.chat.completions.create(
        model=or_model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def _translate_model_for_openrouter(model: str) -> str:
    """Translate Anthropic model ID to OpenRouter format.

    Examples:
    - claude-opus-4-6 -> anthropic/claude-opus-4
    - claude-sonnet-4-6 -> anthropic/claude-sonnet-4
    - claude-haiku-4-5-20251001 -> anthropic/claude-3.5-haiku (fallback tier match)
    """
    m = model.lower()
    # Strip -YYYYMMDD date suffix if present
    m = re.sub(r"-\d{8}$", "", m)
    # Extract tier
    if "opus" in m:
        return "anthropic/claude-opus-4"
    if "sonnet" in m:
        return "anthropic/claude-sonnet-4"
    if "haiku" in m:
        return "anthropic/claude-3.5-haiku"
    return "anthropic/claude-sonnet-4"  # default


def _sdk_call_with_optional_tools(model, system, user, max_tokens, temperature, allow_tools):
    """SDK path: supports tool-use loop when allow_tools=True.

    Anthropic's built-in web_search tool is server-side — we pass the tool
    definition and the API returns text directly. No client-side loop needed
    (server handles search internally and returns final text).
    """
    tools = None
    if allow_tools:
        tools = [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }]
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if tools is not None:
        kwargs["tools"] = tools
    resp = _client.messages.create(**kwargs)
    # Collect all text blocks (tool_use blocks are server-resolved)
    text_parts = []
    for block in resp.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)
    return "\n".join(text_parts) if text_parts else ""


def _should_retry(retry_state):
    """Retry on network/API errors, NOT on JSON parse errors.

    JSON parse failures are deterministic given same prompt — retrying the
    exact same input yields the exact same failure. Instead, call_claude
    handles parse errors by attempting an explicit JSON-only retry.
    """
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if exc is None:
        return False
    import json as _j
    if isinstance(exc, _j.JSONDecodeError):
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
    """Call Claude with retry. Priority: direct SDK -> CLI -> OpenRouter.

    json_schema (preferred when structured output is needed): pass a JSON
    schema object. CLI uses constrained decoding (--json-schema) so the
    returned value is GUARANTEED to match the schema. No parse retries.
    The function returns the parsed object, not a string.

    parse_json=True (legacy): ask for JSON in prompt, best-effort parse.
    Retained for prompts not yet converted to schema.

    allow_tools: WebSearch available to the model.
    """
    # Progress: emit start event
    try:
        from eightd import progress as _p
        _p.emit("llm", "llm_call_start", {"purpose": purpose, "prompt_len": len(user)}, model=model)
    except Exception:
        pass
    # Schema-constrained path: returns parsed object directly.
    # No text-mode fallback — when phases ask for schema output they want a
    # dict, not prose. If CLI schema mode fails, tenacity retries the whole
    # call; after 3 attempts we raise and the caller handles it.
    if json_schema is not None:
        if USE_CLI:
            result = _call_cli(system=system, user=user, model=model,
                               allow_websearch=allow_tools,
                               json_schema=json_schema)
            try:
                from eightd import progress as _p
                _p.emit("llm", "llm_call_end",
                        {"purpose": purpose, "text_len": len(json.dumps(result))},
                        model=model)
            except Exception:
                pass
            return result
        # No CLI available: OpenRouter path doesn't support schema mode.
        # Fall through with schema appended to system for best-effort.
        system = system + f"\n\nOutput must match this JSON schema:\n{json.dumps(json_schema)}"

    if _client is not None:
        text = _sdk_call_with_optional_tools(
            model=model, system=system, user=user,
            max_tokens=max_tokens, temperature=temperature,
            allow_tools=allow_tools,
        )
    elif USE_CLI:
        try:
            text = _call_cli(system=system, user=user, model=model,
                             allow_websearch=allow_tools)
        except Exception as e:
            import sys as _sys
            _sys.stderr.write(f"[WARN] CLI failed ({model}): {e}; falling back to OpenRouter\n")
            text = _call_openrouter(model, system, user, max_tokens, temperature)
    else:
        text = _call_openrouter(model, system, user, max_tokens, temperature)
    # Progress: emit end event
    try:
        from eightd import progress as _p
        _p.emit("llm", "llm_call_end", {"purpose": purpose, "text_len": len(text)}, model=model)
    except Exception:
        pass
    if parse_json:
        try:
            return _extract_json(text)
        except json.JSONDecodeError:
            # One explicit JSON-only retry with stricter prompt
            _dump_parse_failure(text, f"{purpose}_first_attempt")
            stricter_system = system + (
                "\n\nCRITICAL: Your previous response was not valid JSON. "
                "OUTPUT ONLY A SINGLE JSON OBJECT OR ARRAY. No prose, no markdown, no code fences, no explanation. "
                "Start your response with { or [ and end with } or ]. Nothing else."
            )
            # Directly re-call WITHOUT tenacity (single attempt)
            import sys as _sys
            _sys.stderr.write(f"[WARN] call_claude {purpose}: JSON parse failed, retrying with stricter prompt\n")
            if _client is not None:
                resp2 = _client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.0,  # minimize creativity on retry
                    system=stricter_system,
                    messages=[{"role": "user", "content": user}],
                )
                text2 = resp2.content[0].text
            elif USE_CLI:
                try:
                    text2 = _call_cli(system=stricter_system, user=user, model=model,
                                      allow_websearch=allow_tools)
                except Exception:
                    text2 = _call_openrouter(model, stricter_system, user, max_tokens, 0.0)
            else:
                text2 = _call_openrouter(model, stricter_system, user, max_tokens, 0.0)
            try:
                return _extract_json(text2)
            except json.JSONDecodeError:
                _dump_parse_failure(text2, f"{purpose}_second_attempt")
                raise
    return text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def websearch(query: str, max_tokens: int = 4000) -> dict:
    """Web search via Claude. SDK path uses web_search tool; CLI path asks Claude
    Code to search (which has WebSearch tool built in)."""
    # Progress: emit websearch start
    try:
        from eightd import progress as _p
        _p.emit("websearch", "search_start", {"query": query[:80]})
    except Exception:
        pass
    if _client is not None:
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
    elif USE_CLI:
        try:
            text = _call_cli(
                system="You are a web research assistant. Use the WebSearch tool when asked.",
                user=(
                    f"Please use the WebSearch tool to search for: {query}\n\n"
                    "Then provide the top 3 findings with source URLs and brief summaries. "
                    "Format as plain text with clear URL citations."
                ),
                allow_websearch=True,
            )
        except Exception as e:
            import sys as _sys
            _sys.stderr.write(f"[WARN] CLI websearch failed: {e}; falling back to OpenRouter :online\n")
            text = _call_openrouter_websearch(query, max_tokens)
    else:
        text = _call_openrouter_websearch(query, max_tokens)
    # Progress: emit websearch end
    try:
        from eightd import progress as _p
        _p.emit("websearch", "search_end", {"query": query[:80], "text_len": len(text)})
    except Exception:
        pass
    return {
        "query": query,
        "results": text.strip(),
        "timestamp": time.time(),
    }


def _dump_parse_failure(text: str, context: str = ""):
    """Save failed text to runs/_parse_failures/ for post-mortem."""
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
    """Robust JSON extraction — multiple fallback strategies for LLM outputs.

    Handles:
    1. Bare JSON (``{...}`` or ``[...]`` standalone)
    2. Fenced code block with ```json or plain ```
    3. JSON embedded in prose (finds outermost balanced {} or [])
    4. Multiple JSON blocks (returns first valid)

    On total failure, saves raw text to runs/_parse_failures/ for debug.
    """
    if not text or not text.strip():
        raise json.JSONDecodeError("empty input", text or "", 0)

    stripped = text.strip()

    # Strategy 1: direct parse (bare JSON)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2: fenced code block
    fence_patterns = [
        r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```",  # fenced with optional json tag
        r"```\s*(\{.*?\}|\[.*?\])\s*```",            # plain fence
    ]
    for pat in fence_patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue

    # Strategy 3: find outermost balanced {...} or [...] in the full text
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        while start != -1:
            # Walk forward counting depth
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
                            break  # try next opener
            start = text.find(open_ch, start + 1)

    # All strategies failed — dump + raise
    _dump_parse_failure(text, "extract_json_all_strategies_failed")
    raise json.JSONDecodeError(
        f"no valid JSON found in text (first 300 chars: {text[:300]!r})",
        text,
        0,
    )
