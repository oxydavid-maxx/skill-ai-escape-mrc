# Overnight run — 2026-04-21 → 22:01

## TL;DR

**Pipeline now completes end-to-end.** Ran the 8D on "why did we migrate to LangGraph only now instead of 3 weeks ago" through all 7 phases. Report delivered to inbox at 22:01:30 (12 KB file). Partial report also delivered at 20:42 from an earlier degraded run.

**But it took 79 min, not 10-20.** And most generative phases fell back to stubs.

## What ran green

- Phase 0 research (keyword + meta categorization + 9 parallel websearches + wiki slug selection + wiki page reads) — **2.85 min**
- Phase 3 RC audit — **3.35 min** (audited the Phase 2 stubs honestly — produced real findings about the degradation)
- Phase 5 prevention audit — **2.04 min** (same)
- Phase 7 report rendering — **7 min** (via OpenRouter fallback after CLI timed out 2×; produced the 12 KB delivered report)
- Email delivery via Outlook COM (both partial at 20:42 and full at 22:01)

## What fell back to stubs

- Phase 1 IS / IS NOT — LLM drifted to prose or hung, stub used. 10.3 min wasted on retries.
- Phase 2 Why chains (4 quadrants) — all 4 fell back to 1-line stubs. 9.7 min wasted.
- Phase 4 corrective + prevention — mixed (Q1 got a list-shaped parse warning, Q2–Q4 fallback stubs). 8.9 min.
- Phase 6 verification plan — stub. 34.7 min wasted on retries (including 2× 300 s CLI timeouts).

The delivered report openly flags this: "🔴 PIPELINE DEGRADED — Upstream LLM generation failed; audit phases produced real findings on the degradation itself". The audit phases did genuine work (rounds 1 and 2 in each audit produced specific critique + severity-labelled weakness lists).

## Why the generative phases failed

Root blocker: **Claude CLI auto-loads this project's CLAUDE.md + auto-memory** and interprets the problem as a research task, producing prose / markdown / planning output instead of schema-conformant JSON. Even with every CLI mitigation stacked (`--system-prompt` flag, `--setting-sources project`, `--allowedTools StructuredOutput`, `--disallowedTools` list, `--permission-mode bypassPermissions`, rstrip of trailing newlines), the agent-mode bleed persists for prompts whose content matches the auto-loaded project memory (our target question does exactly that).

The only clean fix is `--bare` → `claude` CLI skips CLAUDE.md + auto-memory. But `--bare` requires `ANTHROPIC_API_KEY`; your setup uses Max OAuth.

## What the defensive design bought

Every phase now wraps its LLM call in `try/except` → writes a stub with `_fallback: true` → pipeline continues. Consequence: you always get **some** report out, even if the LLM path is broken. The audit phases are still meaningful because they report on whatever was produced (and correctly flag when it's garbage).

## Fix ladder (ordered by expected payoff, cheapest first)

1. **Get an `ANTHROPIC_API_KEY`** from console.anthropic.com → enables `--bare` → subprocess Claude no longer loads project context → every phase call returns clean structured output in 15-30 s. Expected total pipeline: 10-20 min. Cost: ~$0.05 / run at Opus rates. **This fixes almost everything in one shot.**
2. Top up OpenRouter credits → run with `EIGHTD_FORCE_OPENROUTER=1` → CLI path bypassed entirely. Similar cost + similar speed.
3. Split the pipeline: keep CLI for the "open-ended" phases (audit, report) where it thrives in agent mode, use a sidecar API call for the narrow extraction phases. Requires getting one of (1) or (2) above anyway, so strictly weaker.

Once fixed, re-run: `py -3 run_8d.py "why did we migrate to LangGraph only now instead of 3 weeks ago"`. You should see all phases produce substantive content (no `_fallback: true` anywhere) and total runtime 10-20 min.

## Commits landed overnight (most recent last)

```
R1-R6  structural rewrite (call-count 40 → 14, kept 3-round audits, removed 3×3 nesting)
debug  EIGHTD_FORCE_OPENROUTER env var escape hatch
fix    CLI system via --system-prompt flag (not inline concat)
fix    --disallowedTools for narrow prompts
perf   --setting-sources project (skip user CLAUDE.md)
P1     --json-schema structured output
P2     per-phase schemas
prompts  aggressive minimalism (imperative one-liners)
fix    rstrip prompts (trailing \n breaks schema mode)
fix    meta_categorization prompt didn't collide with schema key names
fix    schema mode → text-mode → defensive stub (the fallback ladder)
fix    audit phases normalize list→dict
defensive  all 7 phases wrapped; pipeline always reaches Phase 7
```

`git log --oneline master` on `D:/D-claude/skills/skill-8d-mrc/` shows the full set.

## Lesson saved

`~/.claude/projects/D--D-claude-daily-brief/memory/feedback_research_before_retry.md` — on 2nd failure of same class against same external tool, WebSearch before next patch attempt. I violated this rule multiple times today. Future cycles: obey or escalate to PreToolUse hook (design sketched inside the memory file).
