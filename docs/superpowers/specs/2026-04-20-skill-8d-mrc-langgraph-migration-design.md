# skill-8d-mrc → LangGraph FSM Migration — Design Spec

**Date**: 2026-04-20
**Scope**: Migrate `skill-8d-mrc` from markdown-instruction-driven (current) to LangGraph FSM-driven (Python). Phases become graph nodes with structural exit criteria enforced by code, not text.
**Related 8Ds**: All five 2026-04-20 8Ds, especially `8d-2026-04-20-hook-ceiling-and-migration-trigger.md` (migration decision)
**Migration order context**: First of four planned migrations: (1) **skill-8d-mrc [this]**, (2) personal-wiki ingest, (3) skill-deep-study, (4) daily_brief.

---

## Context

The `skill-8d-mrc` skill (at `D:/D-claude/skills/skill-8d-mrc/SKILL.md`, 23KB) defines 8 phases (0-7 + optional 8). Phase 0 is MANDATORY: consult wiki + memory + online before any Why analysis. On 2026-04-20, Phase 0 was skipped **five times in a single day** — producing five 8D reports that ALL documented the same root cause class: text-instruction-without-gate failure.

The root cause: markdown-embedded instructions rely on LLM compliance. Hook-based enforcement tops at ~84% (community benchmark). Even with `UserPromptSubmit` hook injecting MANDATORY reminders, Claude partially complied — search scope was too narrow, missing architectural alternatives (LangGraph, Temporal) until user explicitly asked.

The 5th 8D concluded: **today is the migration trigger**. Move 8d-mrc from markdown to **LangGraph** — Python state machine where phase transitions are controlled by code, not LLM willpower. Phase 0 does not "ask Claude to search" — Python directly runs the searches, stores results in state, and only allows transition to Phase 2 once state contains the required evidence.

---

## Goals

1. **Eliminate Phase 0 skip**: Phase 0 logic is Python code; cannot be skipped.
2. **Dual-tier research enforcement**: Phase 0 does BOTH problem-specific AND meta-level research (prevents the "hooks vs LangGraph" category blindness we hit today).
3. **Audit phases also research SoA**: Phase 3 (RC audit), Phase 5 (prevention audit), Phase 7 (closure audit) each do their own state-of-the-art / global-optimal search BEFORE auditing. No audit relies purely on internal knowledge.
4. **Structural phase ordering**: Phase N cannot execute until Phase N-1 exit criteria are met in state.
5. **Audit loops are real loops**: Phase 3 and Phase 5 audit nodes can route back to re-run earlier phases if quality gates fail.
6. **Resumable execution**: Crashed / interrupted runs can `--resume` from last checkpoint.
7. **Clean state between runs**: No accumulated cross-run state pollution.
8. **Future-proof model selection**: Auto-adapt to newest Anthropic models without code changes.
9. **Three 4-quadrant tables in final report**: Root Causes (existing), Corrective Actions (new), Proof of Action (new). Each maps to the TRC-NC / TRC-ND / MRC-NC / MRC-ND matrix for full 8D symmetry.
10. **Email delivery on success**: Completed report is automatically emailed to the user via Outlook COM (reusing daily_brief's `email_sender.py` pattern). Telegram secondary delivery optional.

---

## Non-Goals

- **Phase 8 (post-implementation verification)**: deferred. Migration v1 covers Phase 0-7 only. Phase 8 needs real post-fix monitoring; different architectural concerns. Handled in separate later migration.
- **Migrating other skills in this spec**: this spec is 8d-mrc ONLY. personal-wiki, deep-study, daily_brief are separate future specs.
- **Replacing hook-based governance globally**: hooks stay active for interactive sessions. This migration is per-skill.
- **Claude Agent SDK adoption**: LangGraph is sufficient; Agent SDK is overkill for this scope.
- **Temporal**: Windows without Docker makes Temporal heavy. LangGraph's SqliteSaver approximates durable execution for single-user scale.

---

## Architecture

### High-level flow

```
User in Claude Code (any project): "run 8D on problem X"
    ↓
Claude Code reads SKILL.md (thin wrapper)
    ↓
Claude Code executes via Bash:
    py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "problem X" [--resume <run_id>]
    ↓
Python (LangGraph FSM) drives phases 0-7
    - Direct Anthropic API calls (no Claude Code involvement)
    - State persisted to runs/<run_id>/checkpoint.db (SQLite)
    - Logs to runs/<run_id>/log.txt
    ↓
Final report written to:
    - runs/<run_id>/report.md (run artifact)
    - docs/8d-reports/8d-YYYY-MM-DD-<slug>.md (project archive, existing convention)
    ↓
Python exits with path to report
    ↓
Claude Code reads report, summarizes to user
    ↓
On success: Python deletes runs/<run_id>/ (clean state)
On failure: runs/<run_id>/ persists for --resume
```

### LangGraph State Schema

```python
from typing import TypedDict, Literal, Optional
from langgraph.graph import MessagesState

class EightDState(TypedDict):
    # Input
    problem: str
    run_id: str
    run_dir: str

    # Phase 0: Research (forced by Python)
    phase_0_complete: bool
    websearch_specific: list[dict]  # problem-keyword searches
    websearch_meta: list[dict]  # site:github, site:reddit, etc.
    websearch_cross_domain: list[dict]  # other-domain solutions
    meta_categories: list[str]  # reframed problem categories
    meta_domains: list[str]  # cross-pollination domains
    wiki_pages: list[dict]  # {path, content}
    memory_entries: list[dict]  # {path, content}

    # Phase 1: IS/IS NOT
    phase_1_complete: bool
    is_isnt_table: dict

    # Phase 2: Why analysis (4 quadrants, ≥10 whys each)
    phase_2_complete: bool
    why_chains: dict  # {q1_trc_nc: [...], q2_trc_nd: [...], q3_mrc_nc: [...], q4_mrc_nd: [...]}

    # Phase 3: RC audit (includes pre-audit SoA research)
    phase_3_soa_research: list[dict]  # SoA searches on root cause analysis best practice
    phase_3_rounds: list[dict]  # each round's critique
    phase_3_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_3_complete: bool

    # Phase 4: Corrective + Prevention actions (4 quadrants EACH)
    # Corrective = fix THIS instance (Q1, Q2) + fix the occurrence + detection of THIS class (Q3, Q4 corrective)
    # Prevention = actions with gate tests (Scope/Persistence/Measurability)
    phase_4_complete: bool
    corrective_actions: dict  # {q1: {action, rationale}, q2: {...}, q3: {...}, q4: {...}}
    prevention_actions: dict  # {q1: {action, gate_test, hierarchy_level}, q2, q3, q4}

    # Phase 5: Prevention audit (includes pre-audit SoA research)
    phase_5_soa_research: list[dict]  # SoA searches on prevention methods for this class
    phase_5_rounds: list[dict]
    phase_5_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_5_complete: bool

    # Phase 6: Verification plan + Proof of Action matrix
    # Proof of Action = concrete evidence each quadrant's action works
    phase_6_complete: bool
    verification_plan: dict  # overall verification plan
    proof_of_action: dict  # {q1: {metric, data_source, target, baseline, measurement_schedule}, q2, q3, q4}

    # Phase 7: Report + closure audit + delivery
    phase_7_soa_research: list[dict]  # SoA searches on 8D report quality / framing
    phase_7_complete: bool
    report_path: Optional[str]
    wiki_ingest_drafts: list[dict]
    closure_audit: dict
    email_sent: bool
    email_delivery_log: Optional[str]

    # Metadata
    models_used: dict  # {"opus": "claude-opus-4-6", "sonnet": "...", "haiku": "..."}
    api_call_count: int
    start_time: str
    end_time: Optional[str]
```

### Graph Topology

```
START → phase_0_research → phase_1_is_isnt → phase_2_why_analysis
                                                       ↓
                                      phase_3_soa_research (NEW pre-audit)
                                                       ↓
                                                phase_3_rc_audit
                                                    ↓      ↑
                                              [EXHAUSTED] [REWORK]
                                                    ↓      ↑
                                       phase_4_corrective_and_prevention
                                                       ↓
                                      phase_5_soa_research (NEW pre-audit)
                                                       ↓
                                              phase_5_prevention_audit
                                                   ↓      ↑
                                             [EXHAUSTED] [REWORK]
                                                   ↓      ↑
                                     phase_6_verification_and_proof_of_action
                                                       ↓
                                       phase_7_soa_research (report framing)
                                                       ↓
                                     phase_7_report_closure_delivery
                                                       ↓
                                                      END
```

Key conditional edges:
- `phase_3_rc_audit` → if REWORK → back to `phase_2_why_analysis`; if EXHAUSTED → forward
- `phase_5_prevention_audit` → if REWORK → back to `phase_4_corrective_and_prevention`; if EXHAUSTED → forward
- `phase_7` terminal step includes email delivery; failure to deliver does NOT block END but logs warning

---

## Components

### C1: Directory structure

```
D:/D-claude/skills/skill-8d-mrc/
├── SKILL.md                          # Thin wrapper (new, replaces 23KB)
├── SKILL.md.backup-20260420          # Original (kept for reference)
├── run_8d.py                         # Main CLI entry point (new)
├── eightd/                           # Python package (new)
│   ├── __init__.py
│   ├── state.py                      # EightDState TypedDict
│   ├── graph.py                      # LangGraph construction
│   ├── models.py                     # Model selection (dynamic)
│   ├── phases/                       # One file per phase
│   │   ├── __init__.py
│   │   ├── phase_0_research.py
│   │   ├── phase_1_is_isnt.py
│   │   ├── phase_2_why_analysis.py
│   │   ├── phase_3_rc_audit.py
│   │   ├── phase_4_prevention.py
│   │   ├── phase_5_prevention_audit.py
│   │   ├── phase_6_verification.py
│   │   └── phase_7_report.py
│   ├── anthropic_client.py           # Thin wrapper with retry + model-tier dispatch
│   ├── prompts/                      # System prompts for each phase (extracted from old .md files)
│   │   ├── rc_audit_system.txt       # From agents/rc_audit_agent.md
│   │   ├── prevention_audit_system.txt # From agents/prevention_audit_agent.md
│   │   ├── why_analysis_system.txt
│   │   └── ...
│   └── utils.py                      # File ops, sluggification, etc.
├── tests/                            # pytest tests (new)
│   ├── test_phase_0.py
│   ├── test_phase_graph.py
│   ├── test_model_selection.py
│   └── fixtures/
├── runs/                             # Runtime state (gitignored)
│   └── <run_id>/
│       ├── checkpoint.db             # SQLite checkpoint
│       ├── log.txt
│       └── report.md
├── requirements.txt                  # langgraph, anthropic, tenacity, etc.
├── .gitignore                        # exclude runs/
└── agents/                           # LEGACY — kept as reference, not used
    ├── rc_audit_agent.md
    └── prevention_audit_agent.md
```

### C2: SKILL.md (thin wrapper)

Replace 23KB markdown with ~30 lines:

```markdown
# 8D MRC — LangGraph-driven

This skill runs a FSM-enforced 8D root cause analysis. Phase order and exit
criteria are enforced by Python code, not markdown.

## Invocation

When user asks for 8D analysis, execute via Bash:

    py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "<problem description>"

Optional flags:
    --resume <run_id>     Resume an interrupted run
    --gc                  Clean up runs older than 30 days
    --dry-run             Plan only; do not call Anthropic API

## What the user gets

On success, the report is written to `docs/8d-reports/8d-YYYY-MM-DD-<slug>.md`
in the current project. `run_8d.py` exits with that path on stdout.

Summarize the report for the user. Do not attempt to run the phases yourself.
The Python FSM is the only correct implementation.

## Legacy markdown

The original skill markdown is at `SKILL.md.backup-20260420` for reference.
Do not follow its instructions manually — use `run_8d.py` instead.
```

### C3: Model selection (`eightd/models.py`)

Runtime query + tier classification + cache:

```python
import json, time, os
from pathlib import Path
from anthropic import Anthropic

CACHE_PATH = Path.home() / ".claude" / "hooks" / "anthropic-models-cache.json"
CACHE_TTL_SECONDS = 24 * 3600

FALLBACK_MODELS = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

TIER_ROLES = {
    "opus": ["why_analysis", "rc_audit", "prevention_audit", "closure_audit"],
    "sonnet": ["meta_categorization", "report_generation", "is_isnt_extraction"],
    "haiku": ["keyword_extraction", "simple_classification"],
}

def get_models() -> dict[str, str]:
    """Return {tier: model_id} dict. Checks cache, falls back to hardcoded."""
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())
        if time.time() - cache["timestamp"] < CACHE_TTL_SECONDS:
            return cache["models"]

    # Refresh from API
    try:
        client = Anthropic()
        all_models = client.models.list(limit=100).data
        selected = {
            tier: _latest_in_tier(all_models, tier)
            for tier in ["opus", "sonnet", "haiku"]
        }
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps({
            "timestamp": time.time(),
            "models": selected,
        }))
        return selected
    except Exception as e:
        print(f"[WARN] model discovery failed ({e}), using fallback")
        return FALLBACK_MODELS

def _latest_in_tier(models: list, tier: str) -> str:
    """Pick highest-version model matching tier name."""
    candidates = [m.id for m in models if tier in m.id.lower()]
    # Sort by version number (claude-opus-4-6 < claude-opus-4-7)
    return max(candidates, key=_version_tuple) if candidates else FALLBACK_MODELS[tier]

def _version_tuple(model_id: str) -> tuple:
    """Extract version for sorting. claude-opus-4-6 -> (4, 6, '')"""
    import re
    m = re.search(r'(\d+)-(\d+)(?:-(\d+))?', model_id)
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    return (0, 0, 0)

def model_for_role(role: str) -> str:
    """Lookup model for a role by tier mapping."""
    models = get_models()
    for tier, roles in TIER_ROLES.items():
        if role in roles:
            return models[tier]
    return models["sonnet"]  # default
```

### C4: Phase 0 implementation (the crown jewel)

`eightd/phases/phase_0_research.py`:

```python
from ..anthropic_client import call_claude, websearch
from ..models import model_for_role
from pathlib import Path
import glob

def phase_0_research(state: EightDState) -> EightDState:
    """
    CORE GUARANTEE: Phase 0 is NOT a request to Claude — it is direct Python
    execution of searches. Claude sees the results in Phase 2+, but cannot skip
    the research because Python already did it.
    """
    problem = state["problem"]

    # ---- Tier 0a: Problem-specific search ----
    keywords = call_claude(
        model=model_for_role("keyword_extraction"),
        system="Extract 3-5 high-signal keywords from the problem. Output as JSON array.",
        user=problem,
        parse_json=True,
    )
    state["websearch_specific"] = [
        websearch(f"how to solve {' '.join(keywords)}"),
        websearch(f"{' '.join(keywords)} best practices 2026"),
    ]

    # ---- Tier 0b: Meta-level search (prevents category blindness) ----
    meta = call_claude(
        model=model_for_role("meta_categorization"),
        system=(
            "Step back from the problem specifics. Identify the HIGHER-LEVEL problem "
            "category and adjacent domains that solve this class of problem.\n\n"
            "Output JSON: {\n"
            '  "categories": [3 abstract category names, NOT tool-specific],\n'
            '  "domains": [3 different domains/industries that solve this class]\n'
            "}"
        ),
        user=problem,
        parse_json=True,
    )
    state["meta_categories"] = meta["categories"]
    state["meta_domains"] = meta["domains"]

    PROMINENT_SITES = [
        "github.com", "reddit.com", "stackoverflow.com",
        "news.ycombinator.com", "arxiv.org",
    ]

    state["websearch_meta"] = []
    for cat in meta["categories"]:
        for site in PROMINENT_SITES:
            state["websearch_meta"].append(
                websearch(f"{cat} site:{site}")
            )

    state["websearch_cross_domain"] = []
    for domain in meta["domains"]:
        state["websearch_cross_domain"].append(
            websearch(f"how does {domain} solve {meta['categories'][0]}")
        )

    # ---- Wiki + memory (local knowledge base) ----
    wiki_index_path = Path("D:/D-claude/personal-wiki/wiki/index.md")
    if wiki_index_path.exists():
        wiki_index_text = wiki_index_path.read_text(encoding="utf-8")
        relevant_slugs = call_claude(
            model=model_for_role("simple_classification"),
            system="From this wiki index, list up to 5 page slugs most relevant to the problem. Output as JSON array of slugs (e.g. ['wiki-to-code-traceability', 'self-healing-automation']).",
            user=f"Index:\n{wiki_index_text}\n\nProblem:\n{problem}",
            parse_json=True,
        )
        state["wiki_pages"] = []
        for slug in relevant_slugs:
            page_path = Path(f"D:/D-claude/personal-wiki/wiki/concepts/{slug}.md")
            if page_path.exists():
                state["wiki_pages"].append({
                    "path": str(page_path),
                    "content": page_path.read_text(encoding="utf-8"),
                })

    # Memory entries (all feedback_*.md across projects)
    memory_files = glob.glob(str(Path.home() / ".claude/projects/*/memory/feedback_*.md"))
    state["memory_entries"] = [
        {"path": f, "content": Path(f).read_text(encoding="utf-8")}
        for f in memory_files
    ]

    state["phase_0_complete"] = True
    return state
```

**Key property**: this function DOES THE WORK, not asks Claude to do it. The LLM is called only for semantic helpers (keyword extraction, meta categorization, slug selection) — never to decide whether to search.

### C5: Exit criteria pattern (Q5 answer: hybrid)

Per Q5 decision (C): data-collection phases use structural counts; audit phases use LLM-judge.

| Phase | Exit criterion type | Enforcement |
|-------|---------------------|-------------|
| 0 Research | Structural count | Python forced; ≥2 specific searches, ≥15 meta-site searches, ≥3 cross-domain searches, wiki + memory loaded |
| 1 IS/IS NOT | Structural | 4 dimensions filled (WHAT/WHERE/WHEN/EXTENT) in state |
| 2 Why analysis | Structural | ≥10 whys per quadrant AND 4 quadrants present |
| **3a SoA research** | Structural | **≥5 SoA searches on root-cause-analysis best practice (multi-site: github/reddit/arxiv/stackexchange/medium)** |
| 3b RC audit | LLM-judge | Verdict EXHAUSTED; audit must CITE SoA results from 3a (structural check: audit text contains ≥2 SoA URLs) |
| 4 Corrective + Prevention | Structural | **Both corrective AND prevention actions present for Q1-Q4**; prevention gate test recorded |
| **5a SoA research** | Structural | **≥5 SoA searches on prevention methods for this class** |
| 5b Prevention audit | LLM-judge | Verdict EXHAUSTED; cites SoA results from 5a |
| 6 Verification + Proof | Structural | Verification plan + **proof of action 4-quadrant table** (metric + data source + target + baseline + schedule per quadrant) |
| **7a SoA research** | Structural | **≥3 searches on 8D report best practice / framing** (shorter; less critical) |
| 7b Report + closure + delivery | Structural | All 3 report tables filled (RC, Corrective, Proof); wiki ingest drafts if recommended; **report emailed to user via Outlook COM** (success flag in state) |

### C6: Phase 3 (RC audit) with pre-audit SoA research

Two separate nodes — structural research first, LLM audit second:

```python
# eightd/phases/phase_3_soa.py
def phase_3_soa_research(state: EightDState) -> EightDState:
    """
    SoA search for root cause analysis best practices before auditing.
    Python-forced, same discipline as Phase 0.
    """
    problem_summary = state["problem"][:200]
    categories = state.get("meta_categories", [])

    state["phase_3_soa_research"] = []
    # State-of-the-art searches on RC analysis methodology
    queries = [
        f"state of the art root cause analysis for {categories[0] if categories else 'software failures'}",
        f"5 whys critique limitations alternatives 2026",
        f"root cause analysis framework best practice site:github.com",
        f"root cause analysis critique site:reddit.com",
        f"fishbone vs 5whys vs FMEA site:stackexchange.com",
    ]
    for q in queries:
        state["phase_3_soa_research"].append(websearch(q))
    return state


# eightd/phases/phase_3_rc_audit.py
def phase_3_rc_audit(state: EightDState) -> EightDState:
    """
    RC audit — uses SoA research from Phase 3a to benchmark the Why analysis.
    Up to 3 challenge rounds; then classifies weaknesses.
    """
    system = Path(__file__).parent.parent / "prompts" / "rc_audit_system.txt"
    system_text = system.read_text(encoding="utf-8")

    # Inject SoA research into user context
    soa_context = _format_soa_for_prompt(state["phase_3_soa_research"])

    for round_num in range(1, 4):
        audit_result = call_claude(
            model=model_for_role("rc_audit"),
            system=system_text,
            user=_build_audit_user_message(state, round_num, soa_context=soa_context),
            parse_json=True,
        )
        state.setdefault("phase_3_rounds", []).append(audit_result)

        if audit_result.get("verdict") == "EXHAUSTED":
            # Structural check: audit cited SoA
            if _audit_cites_soa(audit_result, state["phase_3_soa_research"]):
                state["phase_3_verdict"] = "EXHAUSTED"
                state["phase_3_complete"] = True
                return state
            # Auditor didn't cite SoA — force another round with stronger prompt
            state["phase_3_rounds"][-1]["rejection_reason"] = "verdict_without_soa_citation"

        # ADDRESSABLE weaknesses or rejection — apply fixes
        state["why_chains"] = _apply_audit_fixes(state, audit_result)

    # 3 rounds exhausted without reaching valid EXHAUSTED verdict
    state["phase_3_verdict"] = "REWORK"
    state["phase_3_complete"] = False
    return state


def _audit_cites_soa(audit_result: dict, soa_research: list[dict]) -> bool:
    """Structural: audit text must mention ≥2 unique URLs from SoA search results."""
    audit_text = json.dumps(audit_result)
    soa_urls = [r["url"] for r in soa_research for r in r.get("results", []) if "url" in r]
    hits = sum(1 for url in soa_urls if url in audit_text)
    return hits >= 2


def _route_from_phase_3(state: EightDState) -> str:
    """Conditional edge function."""
    if state["phase_3_verdict"] == "REWORK":
        state["phase_2_complete"] = False  # force re-run
        return "phase_2_why_analysis"
    return "phase_4_corrective_and_prevention"
```

**Phase 5 (prevention audit) follows identical pattern**: `phase_5_soa_research` node (searches "state of the art prevention methods for <category>") → `phase_5_prevention_audit` node uses SoA results, must cite ≥2 URLs.

**Phase 7 closure audit** has a lighter SoA step (searches "8D report best practice", "root cause analysis report quality rubric") since framing is well-established.

### C6b: Phase 4 — BOTH corrective AND prevention per quadrant

```python
# eightd/phases/phase_4_corrective_and_prevention.py
def phase_4_corrective_and_prevention(state: EightDState) -> EightDState:
    """
    For each quadrant (Q1/TRC-NC, Q2/TRC-ND, Q3/MRC-NC, Q4/MRC-ND):
    - Corrective action: fix THIS instance / detection miss
    - Prevention action: fix the CLASS (gate test required)
    """
    state["corrective_actions"] = {}
    state["prevention_actions"] = {}

    for quadrant_key, root_cause in state["why_chains"].items():
        # Corrective: one-shot fix for this specific case
        corrective = call_claude(
            model=model_for_role("why_analysis"),
            system=_load_prompt("corrective_action_system.txt"),
            user=json.dumps({"quadrant": quadrant_key, "root_cause": root_cause, "problem": state["problem"]}),
            parse_json=True,
        )
        state["corrective_actions"][quadrant_key] = corrective

        # Prevention: class-level action with gate test (only for Q3, Q4 per methodology;
        # Q1, Q2 can also have prevention for completeness)
        prevention = call_claude(
            model=model_for_role("why_analysis"),
            system=_load_prompt("prevention_action_system.txt"),
            user=json.dumps({"quadrant": quadrant_key, "root_cause": root_cause, "problem": state["problem"]}),
            parse_json=True,
        )
        state["prevention_actions"][quadrant_key] = prevention

    state["phase_4_complete"] = True
    return state
```

### C6c: Phase 6 — Verification plan + Proof of Action matrix

```python
# eightd/phases/phase_6_verification.py
def phase_6_verification_and_proof_of_action(state: EightDState) -> EightDState:
    """
    Two outputs:
    1. Overall verification plan (existing)
    2. Proof of Action 4-quadrant table: per-quadrant concrete evidence specification
    """
    # Proof of Action: for each quadrant, what constitutes evidence the action worked?
    state["proof_of_action"] = {}
    for quadrant_key in ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]:
        corrective = state["corrective_actions"][quadrant_key]
        prevention = state["prevention_actions"][quadrant_key]

        proof = call_claude(
            model=model_for_role("why_analysis"),
            system=_load_prompt("proof_of_action_system.txt"),
            user=json.dumps({
                "quadrant": quadrant_key,
                "corrective": corrective,
                "prevention": prevention,
            }),
            parse_json=True,
        )
        # Required fields per quadrant:
        # - metric: what to measure
        # - data_source: where the measurement comes from
        # - target: numeric target (e.g., "zero recurrences in 30 days")
        # - baseline: current value
        # - measurement_schedule: when/how often
        state["proof_of_action"][quadrant_key] = proof

    # Overall verification plan (existing, keeps)
    state["verification_plan"] = _generate_verification_plan(state)
    state["phase_6_complete"] = True
    return state
```

### C6d: Phase 7 — Report (3 tables) + email delivery

```python
# eightd/phases/phase_7_report.py
def phase_7_report_closure_delivery(state: EightDState) -> EightDState:
    """
    Generate final report with THREE 4-quadrant tables:
    1. Root Causes (existing)
    2. Corrective Actions (new)
    3. Proof of Action (new)
    Then email to user.
    """
    template = Path(__file__).parent.parent.parent / "templates" / "8d_report_template.md"
    rendered = render_report(state, template)

    # Write both to run dir and to canonical project location
    run_report = Path(state["run_dir"]) / "report.md"
    run_report.write_text(rendered, encoding="utf-8")

    canonical = _canonical_report_path(state)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(rendered, encoding="utf-8")
    state["report_path"] = str(canonical)

    # Closure audit (already has SoA from phase_7_soa_research)
    state["closure_audit"] = run_closure_audit(state)

    # Email delivery
    try:
        from eightd.delivery.email import send_8d_report_email
        log = send_8d_report_email(
            report_md=rendered,
            report_path=canonical,
            problem_summary=state["problem"][:200],
        )
        state["email_sent"] = True
        state["email_delivery_log"] = log
    except Exception as e:
        state["email_sent"] = False
        state["email_delivery_log"] = f"FAIL: {e}"
        # Non-blocking; we still have the file on disk

    state["phase_7_complete"] = True
    return state
```

### C11: Email delivery (`eightd/delivery/email.py`)

Reuse daily_brief's Outlook COM approach:

```python
"""
Email delivery for 8D reports via Outlook COM (Windows only).
Pattern: copy of daily_brief/publishers/email_sender.py with skill-specific subject/body.
"""
import sys
from pathlib import Path


def send_8d_report_email(report_md: str, report_path: Path, problem_summary: str) -> str:
    """Send 8D report as HTML email via Outlook COM. Returns delivery log string."""
    import win32com.client
    from datetime import datetime

    html_body = _md_to_html(report_md)

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 = olMailItem
    mail.To = _get_recipient()  # reads from config (see below)
    mail.Subject = f"[8D Report] {problem_summary[:100]} — {datetime.now():%Y-%m-%d}"
    mail.HTMLBody = html_body
    # Attach markdown file too
    mail.Attachments.Add(str(report_path.resolve()))
    mail.Send()

    return f"OK: sent to {mail.To} at {datetime.now().isoformat()}"


def _get_recipient() -> str:
    """Read user email from ~/.claude/email.json; fallback to env var."""
    import json, os
    cfg_path = Path.home() / ".claude" / "email.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text())["recipient"]
    return os.environ.get("CLAUDE_EIGHTD_EMAIL", "")


def _md_to_html(md_text: str) -> str:
    """Markdown to styled HTML (simplified copy of daily_brief's _md_to_html)."""
    try:
        import markdown
        body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        import html as html_mod
        body = f"<pre style='white-space: pre-wrap; font-family: monospace'>{html_mod.escape(md_text)}</pre>"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;padding:20px;line-height:1.6}}
h1{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}}
h2{{color:#2980b9;margin-top:30px}}
table{{border-collapse:collapse;margin:15px 0}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f4f4f4}}
</style></head><body>{body}</body></html>"""
```

### C12: Email config (`~/.claude/email.json`)

New config file (user-editable):

```json
{
  "recipient": "kuangyu@realtek.com",
  "cc": [],
  "enabled": true
}
```

If `enabled: false`, `send_8d_report_email` is still called but returns "SKIPPED: email disabled in config".

### C7: Checkpointer + cleanup

```python
# run_8d.py main
import argparse, shutil, uuid, time, sys
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

RUNS_DIR = Path(__file__).parent / "runs"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("problem", nargs="?", help="Problem description")
    ap.add_argument("--resume", dest="resume_id", help="Resume run by ID")
    ap.add_argument("--gc", action="store_true", help="Clean abandoned runs >30d")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.gc:
        gc_runs()
        sys.exit(0)

    run_id = args.resume_id or f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    db_path = run_dir / "checkpoint.db"
    saver = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")

    graph = build_graph(checkpointer=saver)
    config = {"configurable": {"thread_id": run_id}}

    if args.resume_id:
        initial = None  # resume from checkpoint
    else:
        initial = {"problem": args.problem, "run_id": run_id, "run_dir": str(run_dir)}

    final_state = graph.invoke(initial, config=config)

    if final_state.get("phase_7_complete"):
        # Copy report to canonical location
        report_src = run_dir / "report.md"
        report_dst = _canonical_report_path(final_state)
        shutil.copy2(report_src, report_dst)
        print(str(report_dst))  # stdout path for Claude Code to read

        # Clean up run dir on success
        shutil.rmtree(run_dir)
    else:
        print(f"Run incomplete. Use --resume {run_id} to continue.", file=sys.stderr)
        sys.exit(2)

def gc_runs():
    cutoff = time.time() - 30 * 86400
    for rundir in RUNS_DIR.iterdir():
        if rundir.is_dir() and rundir.stat().st_mtime < cutoff:
            shutil.rmtree(rundir)

if __name__ == "__main__":
    main()
```

### C8: Anthropic client wrapper

```python
# eightd/anthropic_client.py
import json, time
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

_client = Anthropic()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def call_claude(model: str, system: str, user: str, parse_json: bool = False,
                max_tokens: int = 8000, temperature: float = 0.3):
    resp = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text
    if parse_json:
        return _extract_json(text)
    return text

def websearch(query: str) -> dict:
    """Use Anthropic's Claude+WebSearch tool."""
    resp = _client.messages.create(
        model="claude-sonnet-4-6",  # web search lightweight
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": f"Search: {query}\n\nProvide top 3 findings with source URLs."}],
    )
    return {
        "query": query,
        "results": resp.content[-1].text if resp.content else "",
        "timestamp": time.time(),
    }

def _extract_json(text: str):
    """Robust JSON extraction (handles ```json code fences)."""
    import re
    m = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    return json.loads(text)
```

### C9: Testing strategy

TDD where feasible:

```
tests/
├── test_phase_0.py           # Mock websearch/call_claude, verify state populated correctly
├── test_phase_2_exit_criteria.py  # ≥10 whys enforcement
├── test_phase_3_loop.py      # REWORK routes back to phase_2
├── test_model_selection.py   # Cache behavior, fallback, version sort
├── test_checkpointer.py      # Resume from midway state
└── fixtures/
    ├── mock_anthropic.py     # Fake API with deterministic responses
    └── sample_problem.txt
```

Integration test: one end-to-end run against a known simple problem with mocked API, verify report produced.

### C9b: Updated report template (three 4-quadrant tables)

The new `templates/8d_report_template.md` MUST produce three parallel tables at different sections of the final report:

```markdown
## Section A: Root Cause Matrix (existing)
|       | Non-Conformance (NC)                | Non-Detection (ND)                  |
|-------|-------------------------------------|-------------------------------------|
| TRC   | Q1: {root cause one-liner}          | Q2: {root cause one-liner}          |
| MRC   | Q3: {root cause one-liner}          | Q4: {root cause one-liner}          |

## Section B: Corrective Actions Matrix (NEW)
|       | Non-Conformance (NC)                | Non-Detection (ND)                  |
|-------|-------------------------------------|-------------------------------------|
| TRC   | Q1 corrective: {action one-liner}   | Q2 corrective: {action one-liner}   |
| MRC   | Q3 corrective: {action one-liner}   | Q4 corrective: {action one-liner}   |

## Section B2: Prevention Actions Matrix (existing — for full 8D symmetry)
|       | Non-Conformance (NC)                | Non-Detection (ND)                  |
|-------|-------------------------------------|-------------------------------------|
| TRC   | Q1 prevention: {action + gate test} | Q2 prevention: {action + gate test} |
| MRC   | Q3 prevention: {action + gate test} | Q4 prevention: {action + gate test} |

## Section C: Proof of Action Matrix (NEW)
|       | Non-Conformance (NC)                  | Non-Detection (ND)                 |
|-------|---------------------------------------|------------------------------------|
| TRC   | Q1: metric={...}, target={...}        | Q2: metric={...}, target={...}     |
| MRC   | Q3: metric={...}, target={...}        | Q4: metric={...}, target={...}     |
```

Full sections continue as before (IS/IS NOT, Why chains, audit rounds, verification plan, wiki ingest drafts) — the three tables are summary matrices at the top; body sections contain details.

### C10: SKILL.md backup + existing 8D compatibility

- Rename current `SKILL.md` → `SKILL.md.backup-20260420`
- Write new thin wrapper as SKILL.md (per C2)
- Existing `agents/rc_audit_agent.md` and `prevention_audit_agent.md` kept as reference (used as source for extracting `prompts/*_system.txt`)
- Existing `templates/8d_report_template.md` used by `phase_7_report.py` to produce report markdown

---

## Data Flow — End-to-end example

User in Claude Code session (mobile):

1. User types: "run 8D on: daily_brief pipeline produced empty briefing despite source data being present"
2. Claude Code reads `SKILL.md` (thin wrapper)
3. Claude Code executes Bash:
   ```
   py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py \
     "daily_brief pipeline produced empty briefing despite source data being present"
   ```
4. Python starts:
   - Discovers latest models: `{opus: claude-opus-4-6, sonnet: ..., haiku: ...}`
   - Creates `runs/run-1745247000-abc12345/checkpoint.db`
5. LangGraph runs phase_0_research:
   - Extracts keywords: `["pipeline", "empty briefing", "source data"]`
   - Searches specific: 2 WebSearch calls
   - Meta categorizes → categories: `["silent failure detection", "pipeline invariants", "data freshness"]`, domains: `["ETL engineering", "monitoring systems", "fault-tolerant logging"]`
   - 15 meta WebSearches (3 categories × 5 sites)
   - 3 cross-domain WebSearches
   - Wiki pages: reads `silent-staleness.md`, `self-healing-automation.md`, etc.
   - Memory: reads all `feedback_*.md`
6. phase_1_is_isnt runs
7. phase_2_why_analysis (10+ whys × 4 quadrants)
8. phase_3_rc_audit (≤3 rounds, may loop)
9. phase_4_prevention
10. phase_5_prevention_audit (≤3 rounds, may loop)
11. phase_6_verification
12. phase_7_report — writes `runs/run-.../report.md`
13. Python copies report → `docs/8d-reports/8d-2026-04-20-daily-brief-empty-output.md`
14. Python prints the path to stdout, deletes `runs/run-.../`
15. Claude Code reads the report, summarizes for user on mobile

---

## Testing & Verification

### T1: Unit tests (pytest)
- Each phase function tested with mocked Anthropic client
- Model selection: cache hit, cache miss, fallback path, version sort

### T2: Dry-run integration
- `py -3 run_8d.py "test problem" --dry-run` prints phase plan without API calls

### T3: Real end-to-end (manual)
- First migration validation: run against one of today's 5 documented problems
- Compare produced report to the hand-written 8D report on same problem
- Acceptance: Phase 0 produces ≥15 WebSearch results; categories + domains populated; report has all 4 quadrant cells filled

### T4: Failure resumability
- Kill Python mid-Phase 2
- Run `py -3 run_8d.py --resume <run_id>`
- Verify state resumes from last completed phase

### T5: Model adaptation
- Temporarily modify FALLBACK_MODELS to include fake "opus-5-0"
- Verify selection prefers the new version (when cache refreshed)

### T6: No accumulated state
- Run 3 independent 8Ds sequentially
- Verify `runs/` is empty after each success (cleaned up)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| API cost spike (15-20 WebSearch per run) | Each WebSearch is ~$0.01; full 8D ~$0.5-1. Acceptable for this scale. Add `--max-searches N` flag for budget cap. |
| Anthropic API rate limit | tenacity retry with exponential backoff (already in wrapper) |
| LangGraph version churn | Pin version in requirements.txt; test before upgrading |
| Existing markdown skill users confused by change | Backup kept as `SKILL.md.backup-...`; new thin SKILL.md explicitly says to use run_8d.py |
| Python crash leaves orphan runs/ dir | `--gc` flag for cleanup; 30d auto-delete |
| Report path mismatch (project uses different convention) | `run_8d.py` has `--output-dir` flag; defaults to `cwd/docs/8d-reports/` |

---

## File Inventory

### New files
- `D:/D-claude/skills/skill-8d-mrc/run_8d.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/__init__.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/state.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/graph.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/models.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/anthropic_client.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/utils.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/phases/__init__.py`
- `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_0_research.py` through `phase_7_report.py` (8 files)
- `D:/D-claude/skills/skill-8d-mrc/eightd/prompts/*.txt` (extracted system prompts — ~6 files)
- `D:/D-claude/skills/skill-8d-mrc/tests/test_*.py` (~6 test files)
- `D:/D-claude/skills/skill-8d-mrc/tests/fixtures/mock_anthropic.py`
- `D:/D-claude/skills/skill-8d-mrc/requirements.txt`

### Modified files
- `D:/D-claude/skills/skill-8d-mrc/SKILL.md` (from 23KB to ~30 lines, thin wrapper)
- `D:/D-claude/skills/skill-8d-mrc/.gitignore` (add `runs/`)

### Renamed files
- `SKILL.md` → `SKILL.md.backup-20260420` (before replacement)

### Unchanged (kept as reference)
- `agents/rc_audit_agent.md`
- `agents/prevention_audit_agent.md`
- `templates/8d_report_template.md`

---

## Success Criteria

1. **Phase 0 cannot be skipped**: running `py -3 run_8d.py "any problem"` always produces state with ≥15 WebSearch calls, ≥3 meta categories, ≥3 cross-domain searches, wiki+memory entries populated.
2. **All T1-T6 tests pass**.
3. **End-to-end E2E against one of today's problems produces a report whose quality matches or exceeds the hand-written version**.
4. **Runs directory is empty** after successful completion.
5. **Report copied to `docs/8d-reports/`** with conventional filename.
6. **Existing Claude Code invocation (via Skill()) still works** — user types "run 8D on X", Claude Code reads thin SKILL.md, runs Python, returns report.

---

## Out of Scope / Deferred

- Phase 8 post-implementation verification (separate future migration)
- Migrating the other 3 skills (personal-wiki, deep-study, daily_brief) — each gets its own spec
- Replacing hooks with LangGraph globally — hooks stay for interactive
- Integration with Telegram/Notion for report delivery (report path returned; delivery is Claude Code's job)
- Multi-user / concurrent-run handling (single-user project, YAGNI)

---

## Implementation Order (informing plan)

Rough sequencing:

1. **Scaffold**: directory, requirements.txt, `.gitignore`, empty stubs
2. **Anthropic client + models**: `anthropic_client.py`, `models.py` + tests
3. **State schema + graph skeleton**: `state.py`, `graph.py` (empty nodes, edges defined)
4. **Phase 0**: the crown jewel — full implementation + test
5. **Phases 1, 2, 4, 6, 7** (structural): straightforward nodes
6. **Phases 3, 5** (audit): LLM-judge with loop routing
7. **Prompts extraction**: system prompts from current `agents/*.md` → `prompts/*.txt`
8. **Checkpointer + run_8d.py CLI**: resume, gc, dry-run
9. **SKILL.md thin wrapper**: replace 23KB, backup original
10. **Integration test**: E2E against known problem
11. **Commit + skill repo push**
