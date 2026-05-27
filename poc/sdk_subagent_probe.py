# WIKI-EXEMPT: POC feasibility probe for SDK subagent approach; disposable code in poc/ dir, not production, not modifying wiki-governed runtime behavior.
"""POC: verify claude-agent-sdk-python works with Max OAuth + narrow context + schema enforcement.

Five tests:
  1. Auth ??does the SDK pick up Max OAuth without ANTHROPIC_API_KEY?
  2. Narrow-scope ??does setting_sources=None + system_prompt prevent drift/agent-mode?
  3. Schema ??does output_format json_schema return structured output?
  4. Nested schema ??does it handle a complex IS/IS NOT shape?
  5. Parallel ??can we asyncio.gather 4 queries concurrently?

Run: py -3 D:/D-claude/skills/skill-ai-escape-mrc/poc/sdk_subagent_probe.py
"""
import asyncio
import json
import os
import time
import traceback
from typing import Any

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except Exception as e:
    print(f"[FATAL] cannot import claude_agent_sdk: {e}")
    raise


# Issue #573 workaround ??clear CLAUDECODE so nested session isn't rejected.
ENV_CLEAN = {"CLAUDECODE": ""}


async def run_query(name: str, prompt: str, options: ClaudeAgentOptions, timeout_sec: int = 90) -> dict[str, Any]:
    """Run a single query, collect text + structured_output, return diagnostics."""
    t0 = time.monotonic()
    text_blocks: list[str] = []
    structured: Any = None
    error: str | None = None
    message_count = 0

    try:
        async def _run():
            nonlocal structured, message_count
            async for msg in query(prompt=prompt, options=options):
                message_count += 1
                content = getattr(msg, "content", None)
                if isinstance(content, list):
                    for block in content:
                        text = getattr(block, "text", None)
                        if text:
                            text_blocks.append(text)
                        # Schema enforcement arrives as a StructuredOutput tool_use
                        if getattr(block, "name", None) == "StructuredOutput":
                            structured = getattr(block, "input", None)
                so = getattr(msg, "structured_output", None)
                if so is not None:
                    structured = so

        await asyncio.wait_for(_run(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        error = f"timeout after {timeout_sec}s"
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        traceback.print_exc()

    elapsed = time.monotonic() - t0
    joined = "\n".join(text_blocks)
    result = {
        "name": name,
        "elapsed_sec": round(elapsed, 2),
        "messages": message_count,
        "text_len": len(joined),
        "text_preview": joined[:300],
        "structured_output": structured,
        "error": error,
    }
    print(f"\n[{name}] elapsed={result['elapsed_sec']}s msgs={message_count} text_len={len(joined)} err={error}")
    if joined:
        print(f"  preview: {joined[:200]!r}")
    if structured is not None:
        print(f"  structured: {json.dumps(structured, ensure_ascii=False)[:300]}")
    return result


async def test_1_auth() -> dict[str, Any]:
    """Trivial auth check: can SDK talk to Anthropic via Max OAuth?"""
    opts = ClaudeAgentOptions(
        setting_sources=None,
        allowed_tools=[],
        system_prompt="Reply with the single word: OK",
        env=ENV_CLEAN,
        max_turns=3,
    )
    return await run_query("test_1_auth", "say OK", opts, timeout_sec=30)


async def test_2_narrow_scope() -> dict[str, Any]:
    """Does narrow prompt resist agent-mode drift?

    Prompt is deliberately the kind of open-ended question that made the CLI
    drift into research mode yesterday. With setting_sources=None + strict
    system_prompt + no tools, SDK should emit 3 bullets, not a research report.
    """
    opts = ClaudeAgentOptions(
        setting_sources=None,
        allowed_tools=[],
        system_prompt=(
            "You are a narrow keyword extractor. Extract exactly 3 keywords from the user's "
            "question. Reply ONLY with a bulleted list of 3 items. Do not explain, do not "
            "research, do not ask questions."
        ),
        env=ENV_CLEAN,
        max_turns=3,
    )
    prompt = "Why did we migrate to LangChain+LangGraph only now in 2026 when simpler orchestrators exist?"
    return await run_query("test_2_narrow_scope", prompt, opts, timeout_sec=45)


async def test_3_simple_schema() -> dict[str, Any]:
    """Does output_format json_schema produce structured output?"""
    schema = {
        "type": "object",
        "properties": {
            "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
        },
        "required": ["keywords"],
    }
    opts = ClaudeAgentOptions(
        setting_sources=None,
        allowed_tools=[],
        system_prompt="Extract 3 keywords. Return JSON matching the schema.",
        output_format={"type": "json_schema", "schema": schema},
        env=ENV_CLEAN,
        max_turns=3,
    )
    return await run_query(
        "test_3_simple_schema",
        "Problem: pipeline hangs on third-party CLI subprocess calls",
        opts,
        timeout_sec=45,
    )


async def test_4_nested_schema() -> dict[str, Any]:
    """Complex IS/IS NOT shape ??the kind Phase 1 needs."""
    schema = {
        "type": "object",
        "properties": {
            "is_is_not": {
                "type": "object",
                "properties": {
                    "what": {"type": "object", "properties": {"is": {"type": "string"}, "is_not": {"type": "string"}, "distinction": {"type": "string"}}, "required": ["is", "is_not", "distinction"]},
                    "where": {"type": "object", "properties": {"is": {"type": "string"}, "is_not": {"type": "string"}, "distinction": {"type": "string"}}, "required": ["is", "is_not", "distinction"]},
                    "when": {"type": "object", "properties": {"is": {"type": "string"}, "is_not": {"type": "string"}, "distinction": {"type": "string"}}, "required": ["is", "is_not", "distinction"]},
                    "extent": {"type": "object", "properties": {"is": {"type": "string"}, "is_not": {"type": "string"}, "distinction": {"type": "string"}}, "required": ["is", "is_not", "distinction"]},
                },
                "required": ["what", "where", "when", "extent"],
            },
        },
        "required": ["is_is_not"],
    }
    opts = ClaudeAgentOptions(
        setting_sources=None,
        allowed_tools=[],
        system_prompt="Fill the IS/IS NOT table for the problem. Return JSON matching the schema.",
        output_format={"type": "json_schema", "schema": schema},
        env=ENV_CLEAN,
        max_turns=3,
    )
    return await run_query(
        "test_4_nested_schema",
        "Problem: skill-ai-escape-mrc pipeline runs 79 min inside Claude Code session but 10 min from terminal.",
        opts,
        timeout_sec=90,
    )


async def test_5_parallelism() -> dict[str, Any]:
    """4 parallel queries via asyncio.gather ??Phase 2 four-quadrant pattern."""
    quadrants = ["Q1 TRC-NC", "Q2 TRC-ND", "Q3 MRC-NC", "Q4 MRC-ND"]

    async def one(q: str) -> dict[str, Any]:
        opts = ClaudeAgentOptions(
            setting_sources=None,
            allowed_tools=[],
            system_prompt=f"You analyze quadrant {q}. Reply with a single sentence.",
            env=ENV_CLEAN,
            max_turns=3,
        )
        return await run_query(f"test_5_{q.replace(' ', '_')}", "Problem: CLI subprocess hangs.", opts, timeout_sec=45)

    t0 = time.monotonic()
    results = await asyncio.gather(*(one(q) for q in quadrants), return_exceptions=True)
    elapsed = time.monotonic() - t0
    return {
        "name": "test_5_parallelism",
        "elapsed_sec": round(elapsed, 2),
        "sub_results": [r if isinstance(r, dict) else {"error": str(r)} for r in results],
    }


async def main() -> None:
    print(f"ANTHROPIC_API_KEY set: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
    print(f"CLAUDECODE in env: {os.environ.get('CLAUDECODE')!r}")
    print(f"Starting POC at {time.strftime('%H:%M:%S')}")

    results = []
    for fn in (test_1_auth, test_2_narrow_scope, test_3_simple_schema, test_4_nested_schema, test_5_parallelism):
        try:
            r = await fn()
        except Exception as e:
            r = {"name": fn.__name__, "error": f"{type(e).__name__}: {e}"}
            traceback.print_exc()
        results.append(r)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        name = r.get("name", "?")
        err = r.get("error")
        elapsed = r.get("elapsed_sec", "?")
        status = "FAIL" if err else "PASS"
        print(f"{status:4s} {name:32s} elapsed={elapsed}s err={err}")


if __name__ == "__main__":
    asyncio.run(main())
