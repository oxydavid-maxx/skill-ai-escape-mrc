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
USE_CLI = not _api_key and _CLAUDE_PATH is not None
_client = Anthropic(api_key=_api_key) if _api_key else None


def _call_cli(prompt: str, timeout: int = 300) -> str:
    """Call Claude via CLI subprocess. Uses user's Claude Code subscription.

    MUST strip CLAUDECODE + CLAUDE_CODE_ENTRYPOINT from child env — otherwise
    claude CLI detects nested session and refuses (silent hang).
    See module docstring.

    Logs stdout/stderr preview on empty output for debugging.
    """
    import sys as _sys
    child_env = os.environ.copy()
    child_env.pop("CLAUDECODE", None)
    child_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="eightd_prompt_")
    os.close(fd)
    try:
        Path(tmp_path).write_text(prompt, encoding="utf-8")
        with open(tmp_path, "r", encoding="utf-8") as stdin_f:
            result = subprocess.run(
                [_CLAUDE_PATH, "-p", "--output-format", "text"],
                stdin=stdin_f,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                shell=False,
                env=child_env,
            )
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI failed (rc={result.returncode}): {result.stderr[:500]}")
        out = result.stdout.strip()
        if not out:
            # Log diagnostic info on empty output
            _sys.stderr.write(
                f"[WARN] claude CLI returned empty stdout. "
                f"rc={result.returncode} stderr_preview={result.stderr[:300]!r} "
                f"prompt_preview={prompt[:100]!r}\n"
            )
            raise RuntimeError("claude CLI returned empty stdout")
        return out
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


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
        model="anthropic/claude-3.5-haiku:online",  # :online enables web search
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def call_claude(
    model: str,
    system: str,
    user: str,
    parse_json: bool = False,
    max_tokens: int = 8000,
    temperature: float = 0.3,
):
    """Call Claude with retry. Priority: direct SDK -> CLI -> OpenRouter."""
    if _client is not None:
        resp = _client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = resp.content[0].text
    elif USE_CLI:
        prompt = f"System instructions:\n{system}\n\n---\n\n{user}"
        try:
            text = _call_cli(prompt)
        except Exception as e:
            # CLI failed — fall back to OpenRouter if available
            import sys as _sys
            _sys.stderr.write(f"[WARN] CLI failed: {e}; falling back to OpenRouter\n")
            text = _call_openrouter(model, system, user, max_tokens, temperature)
    else:
        # No CLI — try OpenRouter directly
        text = _call_openrouter(model, system, user, max_tokens, temperature)
    if parse_json:
        return _extract_json(text)
    return text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def websearch(query: str, max_tokens: int = 4000) -> dict:
    """Web search via Claude. SDK path uses web_search tool; CLI path asks Claude
    Code to search (which has WebSearch tool built in)."""
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
        prompt = (
            f"Please use the WebSearch tool to search for: {query}\n\n"
            "Then provide the top 3 findings with source URLs and brief summaries. "
            "Format as plain text with clear URL citations."
        )
        try:
            text = _call_cli(prompt)
        except Exception as e:
            import sys as _sys
            _sys.stderr.write(f"[WARN] CLI websearch failed: {e}; falling back to OpenRouter :online\n")
            text = _call_openrouter_websearch(query, max_tokens)
    else:
        text = _call_openrouter_websearch(query, max_tokens)
    return {
        "query": query,
        "results": text.strip(),
        "timestamp": time.time(),
    }


def _extract_json(text: str):
    """Robust JSON extraction — multiple fallback strategies for LLM outputs.

    Handles:
    1. Bare JSON (``{...}`` or ``[...]`` standalone)
    2. Fenced code block with ```json or plain ```
    3. JSON embedded in prose (finds outermost balanced {} or [])
    4. Multiple JSON blocks (returns first valid)
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

    # All strategies failed
    raise json.JSONDecodeError(
        f"no valid JSON found in text (first 200 chars: {text[:200]!r})",
        text,
        0,
    )
