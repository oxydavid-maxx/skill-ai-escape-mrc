# WIKI-EXEMPT: POC message inspection.
"""Dump full message stream for json_schema query to see if structured output arrives despite CLI exit 1."""
import asyncio, json
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    schema = {
        "type": "object",
        "properties": {"keywords": {"type": "array", "items": {"type": "string"}}},
        "required": ["keywords"],
    }
    opts = ClaudeAgentOptions(
        setting_sources=None,
        allowed_tools=[],
        system_prompt="Return JSON matching schema.",
        output_format={"type": "json_schema", "schema": schema},
        env={"CLAUDECODE": ""},
        max_turns=1,
    )
    try:
        async for msg in query(prompt="Extract 3 keywords from: pipeline hangs on subprocess", options=opts):
            cls = type(msg).__name__
            print(f"\n--- {cls} ---")
            for attr in dir(msg):
                if attr.startswith("_"):
                    continue
                try:
                    v = getattr(msg, attr)
                except Exception:
                    continue
                if callable(v):
                    continue
                r = repr(v)
                if len(r) > 500:
                    r = r[:500] + "..."
                print(f"  {attr} = {r}")
    except Exception as e:
        print(f"\nERR: {type(e).__name__}: {e}")

asyncio.run(main())
