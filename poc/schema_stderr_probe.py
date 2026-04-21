# WIKI-EXEMPT: POC stderr capture, disposable.
"""Capture CLI stderr when output_format=json_schema is used, to see actual error."""
import asyncio, os
from claude_agent_sdk import query, ClaudeAgentOptions

stderr_lines = []

def cap(line: str) -> None:
    stderr_lines.append(line)

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
        stderr=cap,
    )
    try:
        async for msg in query(prompt="Extract 3 keywords from: pipeline hangs on subprocess", options=opts):
            print(f"MSG: {type(msg).__name__}")
    except Exception as e:
        print(f"ERR: {type(e).__name__}: {e}")
    print("=" * 40)
    print("STDERR CAPTURED:")
    for line in stderr_lines:
        print(line)

asyncio.run(main())
