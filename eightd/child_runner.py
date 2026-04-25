"""Child SDK process entry point for skill-8d-mrc auto-dispatch (Phase 9 + 11).

Pops CLAUDECODE and CLAUDE_CODE_ENTRYPOINT before importing claude_agent_sdk
to dodge nested-session detection (Issue #573, wiki claude-agent-sdk-patterns).
"""
from __future__ import annotations
import argparse
import os
import sys

# WIKI-CONSULTED: claude-agent-sdk-patterns#issue-573
# WIKI-FINDING: subprocess inherits CLAUDECODE=1; spawned CLI rejects nested session.
# WIKI-ACTION: pop env vars BEFORE importing claude_agent_sdk so its session-init
#              probe doesn't see them.
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)


def main() -> int:
    ap = argparse.ArgumentParser(prog="eightd.child_runner")
    ap.add_argument("--mode", choices=["plan", "execute"], required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--actions-path", help="Path to actions.json (mode=plan)")
    ap.add_argument("--plan-path", required=True, help="Path to plan.md (input for execute, output for plan)")
    args = ap.parse_args()

    # Defer SDK import until after env strip (paranoid)
    from claude_agent_sdk import query, ClaudeAgentOptions  # noqa: F401

    if args.mode == "plan":
        return _run_plan(args)
    return _run_execute(args)


def _run_plan(args) -> int:
    from claude_agent_sdk import query, ClaudeAgentOptions
    import asyncio
    prompt = (
        f"Invoke superpowers:writing-plans on the actions in {args.actions_path}. "
        f"Output the plan to {args.plan_path}. Run ID: {args.run_id}."
    )
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Write", "WebSearch"],
    )
    return asyncio.run(_collect(query(prompt=prompt, options=options)))


def _run_execute(args) -> int:
    from claude_agent_sdk import query, ClaudeAgentOptions
    import asyncio
    exempt = (
        f"EXEMPT R1 R2 R3 R4 R5 R9 child-of-8d: SDK-dispatched child session "
        f"executing approved plan from 8D run {args.run_id}. Parent ran the "
        f"full pipeline; child only implements the approved plan."
    )
    prompt = (
        f"{exempt}\n\nInvoke superpowers:executing-plans on the plan at "
        f"{args.plan_path}. Run ID: {args.run_id}."
    )
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "Bash", "WebSearch"],
    )
    return asyncio.run(_collect(query(prompt=prompt, options=options)))


async def _collect(msg_iter) -> int:
    async for msg in msg_iter:
        # Forward to stderr for parent heartbeat capture
        print(repr(msg)[:500], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
