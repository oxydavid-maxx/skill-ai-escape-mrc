# skill-8d-mrc LangGraph Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Convert `skill-8d-mrc` from markdown-instruction-driven to Python LangGraph FSM with structurally-enforced phase exit criteria, Outlook COM email delivery, and three 4-quadrant matrices (Root Cause + Corrective + Proof of Action).

**Architecture:** Python package `eightd/` using LangGraph StateGraph. Each 8D phase is a graph node. Phase 0 + audit-SoA phases force searches via Python (not LLM requests). Exit criteria enforced by conditional edges. SQLite checkpointer per-run with auto-cleanup on success. Runtime model selection via `/v1/models` query.

**Tech Stack:** Python 3.12 (`py -3`), `langgraph`, `langchain-anthropic`, `anthropic` SDK, `tenacity` (retry), `markdown` (HTML email), `pywin32` (Outlook COM), `pytest`.

---

## File Structure

```
D:/D-claude/skills/skill-8d-mrc/
├── SKILL.md                          # MODIFIED: thin 30-line wrapper
├── SKILL.md.backup-20260420          # NEW: original 23KB kept as reference
├── run_8d.py                         # NEW: CLI entry point
├── requirements.txt                  # NEW
├── .gitignore                        # MODIFIED: add runs/
├── eightd/
│   ├── __init__.py                   # NEW
│   ├── state.py                      # NEW: EightDState TypedDict
│   ├── graph.py                      # NEW: StateGraph construction + edges
│   ├── models.py                     # NEW: runtime model selection
│   ├── anthropic_client.py           # NEW: API wrapper with retry
│   ├── utils.py                      # NEW: file ops, slug, json helpers
│   ├── delivery/
│   │   ├── __init__.py               # NEW
│   │   └── email.py                  # NEW: Outlook COM sender
│   ├── phases/
│   │   ├── __init__.py               # NEW
│   │   ├── phase_0_research.py       # NEW: dual-tier research
│   │   ├── phase_1_is_isnt.py        # NEW
│   │   ├── phase_2_why_analysis.py   # NEW: 4 quadrants × ≥10 whys
│   │   ├── phase_3_soa.py            # NEW: pre-audit SoA search
│   │   ├── phase_3_rc_audit.py       # NEW: LLM-judge + SoA citation check
│   │   ├── phase_4_actions.py        # NEW: corrective + prevention per quadrant
│   │   ├── phase_5_soa.py            # NEW
│   │   ├── phase_5_prevention_audit.py # NEW
│   │   ├── phase_6_verification.py   # NEW: plan + Proof of Action matrix
│   │   ├── phase_7_soa.py            # NEW
│   │   └── phase_7_report.py         # NEW: 3 tables + closure + delivery
│   └── prompts/
│       ├── keyword_extraction.txt    # NEW
│       ├── meta_categorization.txt   # NEW
│       ├── why_analysis.txt          # NEW (per quadrant)
│       ├── rc_audit.txt              # NEW (extracted from agents/rc_audit_agent.md)
│       ├── corrective_action.txt     # NEW
│       ├── prevention_action.txt     # NEW
│       ├── prevention_audit.txt      # NEW (from agents/prevention_audit_agent.md)
│       ├── proof_of_action.txt       # NEW
│       └── report_render.txt         # NEW
├── templates/
│   └── 8d_report_template.md         # MODIFIED: add Corrective + Proof tables
├── tests/
│   ├── __init__.py                   # NEW
│   ├── conftest.py                   # NEW: fixtures
│   ├── test_models.py                # NEW
│   ├── test_anthropic_client.py      # NEW
│   ├── test_phase_0.py               # NEW
│   ├── test_phase_2_exit.py          # NEW
│   ├── test_phase_3_loop.py          # NEW
│   ├── test_phase_4_actions.py       # NEW
│   ├── test_phase_6_proof.py         # NEW
│   ├── test_graph_topology.py        # NEW
│   ├── test_checkpointer.py          # NEW
│   ├── test_email_delivery.py        # NEW
│   └── fixtures/
│       ├── mock_anthropic.py         # NEW
│       └── sample_problem.json       # NEW
└── agents/                           # UNCHANGED: kept for reference
    ├── rc_audit_agent.md
    └── prevention_audit_agent.md
```

All paths are absolute from the skill repo root: `D:/D-claude/skills/skill-8d-mrc/`.

---

## Task 1: Scaffold directory + requirements + gitignore

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/requirements.txt`
- Modify: `D:/D-claude/skills/skill-8d-mrc/.gitignore`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/__init__.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/__init__.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/delivery/__init__.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/prompts/.gitkeep`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/__init__.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/fixtures/__init__.py`

- [ ] **Step 1: Create directory skeleton**

```bash
cd D:/D-claude/skills/skill-8d-mrc
mkdir -p eightd/phases eightd/prompts eightd/delivery tests/fixtures
touch eightd/__init__.py eightd/phases/__init__.py eightd/delivery/__init__.py eightd/prompts/.gitkeep tests/__init__.py tests/fixtures/__init__.py
```

- [ ] **Step 2: Create `requirements.txt`**

```
langgraph>=0.2.0
langchain-anthropic>=0.2.0
anthropic>=0.40.0
tenacity>=8.2.0
markdown>=3.5.0
pywin32>=306; sys_platform == 'win32'
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 3: Update `.gitignore`**

Read current `.gitignore`; append:
```
# LangGraph runtime state (per-run SQLite + logs)
runs/
# Model discovery cache
.anthropic-models-cache.json
# Python
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Install deps**

```bash
py -3 -m pip install -r D:/D-claude/skills/skill-8d-mrc/requirements.txt
```
Expected: successful install, no errors.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add requirements.txt .gitignore eightd tests
git commit -m "scaffold: create eightd/ package skeleton + requirements"
```

---

## Task 2: Model selection (`eightd/models.py`) with tests

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/models.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_models.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_models.py`:

```python
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from eightd.models import (
    get_models,
    model_for_role,
    _latest_in_tier,
    _version_tuple,
    FALLBACK_MODELS,
)


def test_version_tuple_parses_basic():
    assert _version_tuple("claude-opus-4-6") == (4, 6, 0)
    assert _version_tuple("claude-opus-4-7") == (4, 7, 0)
    assert _version_tuple("claude-haiku-4-5-20251001") == (4, 5, 20251001)


def test_version_tuple_no_version_returns_zeros():
    assert _version_tuple("random-name") == (0, 0, 0)


def test_latest_in_tier_picks_highest():
    fake_models = [
        MagicMock(id="claude-opus-4-6"),
        MagicMock(id="claude-opus-4-7"),
        MagicMock(id="claude-sonnet-4-6"),
    ]
    assert _latest_in_tier(fake_models, "opus") == "claude-opus-4-7"


def test_latest_in_tier_fallback_when_empty():
    assert _latest_in_tier([], "opus") == FALLBACK_MODELS["opus"]


def test_model_for_role_dispatches_by_tier():
    with patch("eightd.models.get_models") as mock_get:
        mock_get.return_value = {
            "opus": "claude-opus-4-7",
            "sonnet": "claude-sonnet-4-7",
            "haiku": "claude-haiku-4-5",
        }
        assert model_for_role("rc_audit") == "claude-opus-4-7"
        assert model_for_role("report_generation") == "claude-sonnet-4-7"
        assert model_for_role("keyword_extraction") == "claude-haiku-4-5"


def test_model_for_role_unknown_defaults_sonnet():
    with patch("eightd.models.get_models") as mock_get:
        mock_get.return_value = {
            "opus": "a", "sonnet": "b", "haiku": "c",
        }
        assert model_for_role("unknown_role") == "b"


def test_get_models_uses_cache_when_fresh(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "timestamp": time.time() - 3600,  # 1 hour old
        "models": {"opus": "cached-opus", "sonnet": "cached-sonnet", "haiku": "cached-haiku"},
    }))
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    assert get_models()["opus"] == "cached-opus"


def test_get_models_refreshes_when_stale(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "timestamp": time.time() - 25 * 3600,  # >24 hours old
        "models": {"opus": "stale", "sonnet": "stale", "haiku": "stale"},
    }))
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    with patch("eightd.models.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.models.list.return_value.data = [
            MagicMock(id="claude-opus-4-8"),
            MagicMock(id="claude-sonnet-4-8"),
            MagicMock(id="claude-haiku-4-6"),
        ]
        mock_anthropic.return_value = mock_client
        result = get_models()
        assert result["opus"] == "claude-opus-4-8"


def test_get_models_falls_back_when_api_fails(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"  # does not exist
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    with patch("eightd.models.Anthropic") as mock_anthropic:
        mock_anthropic.side_effect = Exception("API down")
        assert get_models() == FALLBACK_MODELS
```

- [ ] **Step 2: Run test, expect failure**

```bash
cd D:/D-claude/skills/skill-8d-mrc
py -3 -m pytest tests/test_models.py -v
```
Expected: FAIL with "No module named 'eightd.models'".

- [ ] **Step 3: Implement `eightd/models.py`**

```python
"""Runtime model selection with tier dispatch and 24h cache."""
import json
import re
import time
from pathlib import Path
from anthropic import Anthropic

CACHE_PATH = Path(__file__).parent.parent / ".anthropic-models-cache.json"
CACHE_TTL_SECONDS = 24 * 3600

FALLBACK_MODELS = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

TIER_ROLES = {
    "opus": [
        "why_analysis", "rc_audit", "prevention_audit", "closure_audit",
        "corrective_action", "prevention_action", "proof_of_action",
    ],
    "sonnet": [
        "meta_categorization", "report_generation", "is_isnt_extraction",
    ],
    "haiku": [
        "keyword_extraction", "simple_classification",
    ],
}


def get_models() -> dict[str, str]:
    """Return {tier: model_id} dict. Uses 24h cache, falls back on API failure."""
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if time.time() - cache["timestamp"] < CACHE_TTL_SECONDS:
                return cache["models"]
        except Exception:
            pass

    try:
        client = Anthropic()
        all_models = list(client.models.list(limit=100).data)
        selected = {
            tier: _latest_in_tier(all_models, tier)
            for tier in ["opus", "sonnet", "haiku"]
        }
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps({"timestamp": time.time(), "models": selected}),
            encoding="utf-8",
        )
        return selected
    except Exception as e:
        print(f"[WARN] model discovery failed ({e}); using fallback", flush=True)
        return FALLBACK_MODELS


def _latest_in_tier(models: list, tier: str) -> str:
    candidates = [m.id for m in models if tier in m.id.lower()]
    return max(candidates, key=_version_tuple) if candidates else FALLBACK_MODELS[tier]


def _version_tuple(model_id: str) -> tuple:
    m = re.search(r"(\d+)-(\d+)(?:-(\d+))?", model_id)
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    return (0, 0, 0)


def model_for_role(role: str) -> str:
    models = get_models()
    for tier, roles in TIER_ROLES.items():
        if role in roles:
            return models[tier]
    return models["sonnet"]
```

- [ ] **Step 4: Run tests, expect pass**

```bash
cd D:/D-claude/skills/skill-8d-mrc
py -3 -m pytest tests/test_models.py -v
```
Expected: 8/8 PASS.

- [ ] **Step 5: Commit**

```bash
git add eightd/models.py tests/test_models.py
git commit -m "feat: runtime model selection with tier dispatch (eightd/models.py)"
```

---

## Task 3: Anthropic client wrapper with retry + websearch

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/anthropic_client.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_anthropic_client.py`

- [ ] **Step 1: Write test**

Create `tests/test_anthropic_client.py`:

```python
import json
from unittest.mock import patch, MagicMock
import pytest

from eightd.anthropic_client import _extract_json, call_claude, websearch


def test_extract_json_plain():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_from_fenced_code_block():
    text = 'Some preamble\n```json\n{"x": 2}\n```\nafter'
    assert _extract_json(text) == {"x": 2}


def test_extract_json_from_fenced_array():
    text = '```json\n[1, 2, 3]\n```'
    assert _extract_json(text) == [1, 2, 3]


def test_extract_json_no_fence_language():
    text = '```\n{"y": 3}\n```'
    assert _extract_json(text) == {"y": 3}


def test_call_claude_returns_text():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="hello")]
        mock_client.messages.create.return_value = mock_resp
        assert call_claude("m", "sys", "usr") == "hello"


def test_call_claude_parses_json():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text='{"z": 4}')]
        mock_client.messages.create.return_value = mock_resp
        assert call_claude("m", "sys", "usr", parse_json=True) == {"z": 4}


def test_websearch_returns_structured_result():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="finding 1")]
        mock_client.messages.create.return_value = mock_resp
        result = websearch("test query")
        assert result["query"] == "test query"
        assert "results" in result
        assert "timestamp" in result
```

- [ ] **Step 2: Run test, expect failure**

```bash
py -3 -m pytest tests/test_anthropic_client.py -v
```
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `eightd/anthropic_client.py`**

```python
"""Thin Anthropic client wrapper with retry + JSON extraction + websearch."""
import json
import re
import time
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

_client = Anthropic()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def call_claude(
    model: str,
    system: str,
    user: str,
    parse_json: bool = False,
    max_tokens: int = 8000,
    temperature: float = 0.3,
):
    """Call Anthropic messages API with retry. Optionally parse JSON from response."""
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def websearch(query: str, max_tokens: int = 4000) -> dict:
    """Execute a web search via Anthropic's web_search tool. Returns structured dict."""
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
    return {
        "query": query,
        "results": text.strip(),
        "timestamp": time.time(),
    }


def _extract_json(text: str):
    """Robust JSON extraction — handles fenced code blocks with/without language tag."""
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    return json.loads(text.strip())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
py -3 -m pytest tests/test_anthropic_client.py -v
```
Expected: 7/7 PASS.

- [ ] **Step 5: Commit**

```bash
git add eightd/anthropic_client.py tests/test_anthropic_client.py
git commit -m "feat: Anthropic client wrapper with retry + JSON extraction + websearch"
```

---

## Task 4: State schema (`eightd/state.py`)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/state.py`

- [ ] **Step 1: Write state module**

```python
"""EightDState: LangGraph state schema for the 8D MRC FSM."""
from typing import TypedDict, Literal, Optional


class EightDState(TypedDict, total=False):
    # Input
    problem: str
    run_id: str
    run_dir: str

    # Phase 0: forced research
    phase_0_complete: bool
    websearch_specific: list[dict]
    websearch_meta: list[dict]
    websearch_cross_domain: list[dict]
    meta_categories: list[str]
    meta_domains: list[str]
    wiki_pages: list[dict]
    memory_entries: list[dict]

    # Phase 1: IS/IS NOT
    phase_1_complete: bool
    is_isnt_table: dict

    # Phase 2: Why analysis
    phase_2_complete: bool
    why_chains: dict

    # Phase 3: SoA research + RC audit
    phase_3_soa_research: list[dict]
    phase_3_rounds: list[dict]
    phase_3_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_3_complete: bool

    # Phase 4: Corrective + Prevention actions (4 quadrants each)
    phase_4_complete: bool
    corrective_actions: dict
    prevention_actions: dict

    # Phase 5: SoA + Prevention audit
    phase_5_soa_research: list[dict]
    phase_5_rounds: list[dict]
    phase_5_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_5_complete: bool

    # Phase 6: Verification plan + Proof of Action matrix
    phase_6_complete: bool
    verification_plan: dict
    proof_of_action: dict

    # Phase 7: SoA + Report + closure + email delivery
    phase_7_soa_research: list[dict]
    phase_7_complete: bool
    report_path: Optional[str]
    wiki_ingest_drafts: list[dict]
    closure_audit: dict
    email_sent: bool
    email_delivery_log: Optional[str]

    # Metadata
    models_used: dict
    api_call_count: int
    start_time: str
    end_time: Optional[str]


QUADRANTS = ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
```

- [ ] **Step 2: Verify importable**

```bash
py -3 -c "from eightd.state import EightDState, QUADRANTS; print('OK', QUADRANTS)"
```
Expected: `OK ['q1_trc_nc', 'q2_trc_nd', 'q3_mrc_nc', 'q4_mrc_nd']`

- [ ] **Step 3: Commit**

```bash
git add eightd/state.py
git commit -m "feat: EightDState TypedDict schema"
```

---

## Task 5: Utils (`eightd/utils.py`)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/utils.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_utils.py`

- [ ] **Step 1: Write test**

```python
# tests/test_utils.py
from eightd.utils import sluggify, load_prompt, safe_read_text
from pathlib import Path


def test_sluggify_basic():
    assert sluggify("Hello World") == "hello-world"


def test_sluggify_removes_special():
    assert sluggify("Daily Brief: Pipeline Empty!") == "daily-brief-pipeline-empty"


def test_sluggify_truncates():
    long = "a" * 100
    assert len(sluggify(long, max_len=50)) == 50


def test_load_prompt_reads_file(tmp_path, monkeypatch):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "foo.txt").write_text("Hello prompt", encoding="utf-8")
    monkeypatch.setattr("eightd.utils.PROMPTS_DIR", prompts_dir)
    assert load_prompt("foo") == "Hello prompt"


def test_safe_read_text_missing_returns_empty():
    assert safe_read_text(Path("/nonexistent/path")) == ""


def test_safe_read_text_reads_utf8(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("中文 content", encoding="utf-8")
    assert safe_read_text(f) == "中文 content"
```

- [ ] **Step 2: Run test, expect failure**

```bash
py -3 -m pytest tests/test_utils.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `eightd/utils.py`**

```python
"""File ops, slug generation, prompt loading."""
import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def sluggify(text: str, max_len: int = 60) -> str:
    """Convert text to URL-safe slug."""
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:max_len]


def load_prompt(name: str) -> str:
    """Load a prompt template from prompts/ directory."""
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def safe_read_text(path: Path) -> str:
    """Read a file; return empty string if missing or unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""
```

- [ ] **Step 4: Run test, expect pass**

```bash
py -3 -m pytest tests/test_utils.py -v
```
Expected: 6/6 PASS.

- [ ] **Step 5: Commit**

```bash
git add eightd/utils.py tests/test_utils.py
git commit -m "feat: utils — sluggify, load_prompt, safe_read_text"
```

---

## Task 6: Prompt files (extracted from existing agent MDs)

**Files:** Create 9 files in `D:/D-claude/skills/skill-8d-mrc/eightd/prompts/`

- [ ] **Step 1: Create `keyword_extraction.txt`**

```
You extract high-signal technical keywords from a problem description.

Rules:
- Output a JSON array of 3-5 keywords
- Prefer technical nouns over verbs
- Strip filler words ("the", "a", "some")
- No markdown fences, just raw JSON

Example output:
["pipeline", "silent failure", "token refresh", "state drift"]
```

- [ ] **Step 2: Create `meta_categorization.txt`**

```
Step back from the problem specifics. Identify the HIGHER-LEVEL problem
category this belongs to, and adjacent domains that solve this class.

Output strict JSON:
{
  "categories": ["<3 abstract category names, NOT tool-specific>"],
  "domains": ["<3 different domains/industries that solve this class>"]
}

Examples of abstract categories (good): "workflow orchestration",
"state invariant enforcement", "distributed consensus", "observability",
"error budget management".

Examples of tool-specific (BAD, DO NOT USE): "Claude Code hooks",
"Python decorators", "Git pre-commit".

Examples of adjacent domains: "game AI state machines",
"financial workflow engines", "CI/CD pipeline gates",
"aerospace fault tolerance".
```

- [ ] **Step 3: Create `why_analysis.txt`**

```
You are doing Phase 2 of an 8D root cause analysis for ONE quadrant.

Quadrants:
- q1_trc_nc: Technical root cause, Non-Conformance (direct technical
  cause that produced the defect)
- q2_trc_nd: Technical root cause, Non-Detection (detection method that
  failed to catch it)
- q3_mrc_nc: Managerial root cause, Non-Conformance (process/governance
  gap that allowed it)
- q4_mrc_nd: Managerial root cause, Non-Detection (control system gap
  allowing detection miss)

Task: Produce a chain of at least 10 Whys for the assigned quadrant.
Each Why MUST be a genuinely new causal insight, not a restatement.

Stopping criterion: all 4 tests pass — Condition (ongoing state, not
one-time event), On/Off (introducing reproduces, removing suppresses),
Class (explains the class not just this instance), Controllability
(organization can act on it).

Output JSON:
{
  "quadrant": "<quadrant_key>",
  "whys": [
    {"n": 1, "why": "...", "new_insight": "..."},
    ...
    {"n": 10, "why": "...", "new_insight": "..."}
  ],
  "root": "<the deepest controllable cause at the bottom of the chain>"
}

MUST have at least 10 whys. MRC must be at management-system level
(process, governance, policy) NOT code-level (delete function, add check).
```

- [ ] **Step 4: Create `rc_audit.txt`**

Extract relevant portion from `D:/D-claude/skills/skill-8d-mrc/agents/rc_audit_agent.md`. Use this template:

```
You are an adversarial auditor for 8D root cause analysis.

Inputs you receive:
- The Why chains for 4 quadrants (Phase 2 output)
- Phase 3a SoA research results (state-of-the-art root cause analysis
  best practices from GitHub/Reddit/StackExchange/Arxiv)

REQUIRED BEHAVIOR:
1. Challenge each Why step: is it a new insight or a rephrase?
2. Check MRC quadrants are at management level (not code-level).
3. Check ND quadrants are as deep as NC quadrants.
4. BENCHMARK the analysis against SoA research: cite at least 2
   specific URLs from SoA results where the SoA suggests a better
   framing or additional angle. If the SoA suggests the analysis is
   missing a category of root cause, add to the audit.

Output JSON:
{
  "round": <int>,
  "weaknesses": [
    {
      "quadrant": "<q1|q2|q3|q4>",
      "why_step_n": <int>,
      "classification": "ADDRESSABLE|RESIDUAL",
      "issue": "...",
      "suggested_fix": "...",
      "soa_citation": "<URL>"
    }
  ],
  "soa_citations_used": ["<URL1>", "<URL2>"],
  "verdict": "EXHAUSTED|REWORK|CONTINUE"
}

Verdict rules:
- EXHAUSTED: no ADDRESSABLE weaknesses remain; at least 2 soa_citations
- REWORK: too many ADDRESSABLE weaknesses, analysis needs Phase 2 redo
- CONTINUE: some ADDRESSABLE, fix and recheck next round
```

- [ ] **Step 5: Create `corrective_action.txt`**

```
Design a CORRECTIVE action for ONE quadrant. Corrective = fixes THIS
specific instance, not the class.

Input: quadrant key + root cause chain + problem description.

Output JSON:
{
  "quadrant": "<q1..q4>",
  "action": "<what to do, one sentence>",
  "rationale": "<why this fixes this instance>",
  "owner": "<who does it, default 'self'>",
  "target_date": "<ISO date>",
  "evidence_of_completion": "<how we verify this corrective is done>"
}

A corrective action is NOT prevention — it does not aim to prevent the
class. Keep it scoped to this single instance.
```

- [ ] **Step 6: Create `prevention_action.txt`**

```
Design a PREVENTION action for ONE quadrant. Prevention = prevents
the CLASS across future occurrences.

Gate test (ALL 3 required):
- Scope: prevents the CLASS, not just this instance
- Persistence: embedded in process/tooling, works without individual memory
- Measurability: third-party auditor can verify in 6 months

Prevention hierarchy (strongest to weakest):
1. Eliminate (architecturally impossible)
2. Detect at creation (tooling)
3. Detect before merge (process gate)
4. Detect after merge (monitoring)
5. Mitigate impact

Q3 and Q4 must aim for levels 1-3.

Output JSON:
{
  "quadrant": "<q1..q4>",
  "action": "<what to do>",
  "gate_test": {
    "scope": "PASS|FAIL",
    "scope_evidence": "...",
    "persistence": "PASS|FAIL",
    "persistence_evidence": "...",
    "measurability": "PASS|FAIL",
    "measurability_evidence": "..."
  },
  "hierarchy_level": 1-5,
  "failure_mode_of_prevention": "<how this prevention itself could fail>",
  "deployment_scope": "PROJECT|GLOBAL",
  "scope_justification": "..."
}

If any gate_test field is FAIL, the action is corrective in disguise.
Reject and redesign.
```

- [ ] **Step 7: Create `prevention_audit.txt`**

Extract from `D:/D-claude/skills/skill-8d-mrc/agents/prevention_audit_agent.md` (research-first check was added earlier). Template:

```
You are an adversarial auditor for prevention actions — SEPARATE from
the RC auditor (fresh eyes, no confirmation bias).

FIRST check (MANDATORY): research evidence.
- Did the analyst search state-of-the-art prevention methods for this
  class? Verify by looking at Phase 5a SoA research results provided.
- Cite ≥2 specific SoA URLs where the approach compares to or diverges
  from the proposed prevention.
- If SoA results show a STRONGER prevention the analyst missed → REWORK.

Subsequent checks:
- Corrective vs Preventive (gate test must pass all 3)
- Hierarchy level (should be 1-3 for Q3/Q4)
- Failure mode of prevention
- Conflict with existing mechanisms

Output JSON:
{
  "round": <int>,
  "soa_citations_used": ["<URL1>", "<URL2>"],
  "stronger_alternatives_found_in_soa": ["<description>"] or [],
  "weaknesses": [
    {
      "quadrant": "<q1..q4>",
      "issue": "...",
      "classification": "ADDRESSABLE|RESIDUAL",
      "suggested_fix": "..."
    }
  ],
  "verdict": "EXHAUSTED|REWORK|CONTINUE"
}
```

- [ ] **Step 8: Create `proof_of_action.txt`**

```
Design Proof of Action for ONE quadrant. Proof of Action = concrete
evidence specification proving the actions (corrective + prevention)
for this quadrant worked.

Input: quadrant + corrective action + prevention action.

Output JSON:
{
  "quadrant": "<q1..q4>",
  "metric": "<what to measure, specific and quantitative>",
  "data_source": "<where the measurement comes from, file/log/API/dashboard>",
  "target": "<numeric target, e.g. 'zero recurrences in 30 days'>",
  "baseline": "<current value before action>",
  "measurement_schedule": "<cadence, e.g. 'daily at 09:00', 'weekly Sunday'>",
  "failure_response": "<what to do if metric shows action did not work>"
}

The metric must be objectively verifiable by a third party. Avoid
"team is more careful" or other unmeasurable phrasings.
```

- [ ] **Step 9: Create `report_render.txt`**

```
You render the final 8D report in markdown. The state dict contains
all phases' outputs.

MUST produce these sections in order:
1. Title + metadata (date, problem, run_id)
2. Section A: Root Cause Matrix (4-quadrant table)
3. Section B: Corrective Actions Matrix (4-quadrant table)
4. Section B2: Prevention Actions Matrix (4-quadrant table with gate test)
5. Section C: Proof of Action Matrix (4-quadrant table with metric+target)
6. IS/IS NOT table
7. Why chains (4 quadrants, full detail)
8. Audit rounds (phase 3 + phase 5)
9. SoA citations (deduplicated list across all phase 3/5/7 SoA searches)
10. Verification plan
11. Wiki ingest drafts (if any)
12. Closure audit summary

Use the template at templates/8d_report_template.md as structure
reference. Output ONLY the rendered markdown — no preamble, no
explanation, no code fences around the whole thing.
```

- [ ] **Step 10: Create `is_isnt_extraction.txt`**

```
Produce Phase 1 IS/IS NOT problem definition.

Output JSON:
{
  "what": {"is": "...", "is_not": "...", "distinction": "..."},
  "where": {"is": "...", "is_not": "...", "distinction": "..."},
  "when": {"is": "...", "is_not": "...", "distinction": "..."},
  "extent": {"is": "...", "is_not": "...", "distinction": "..."}
}

The DISTINCTION column explains WHY the difference matters — what
changes the distinction implies for root cause hypotheses.
```

- [ ] **Step 11: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git add eightd/prompts/
git commit -m "feat: prompt templates for all phases"
```

---

## Task 7: Phase 0 — dual-tier research (the crown jewel)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_0_research.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_0.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/fixtures/mock_anthropic.py`

- [ ] **Step 1: Create test fixture `tests/fixtures/mock_anthropic.py`**

```python
"""Deterministic mock for Anthropic API used in tests."""
from unittest.mock import MagicMock


def make_call_claude_mock(responses: dict):
    """Return a call_claude replacement that dispatches by role or system-prompt prefix.

    responses keys are substrings of system prompt; values are the returned object
    (str for text, dict/list for parse_json=True).
    """

    def mock_call(model, system, user, parse_json=False, max_tokens=None, temperature=None):
        for key, value in responses.items():
            if key in system:
                return value
        raise KeyError(f"No mock response matches system prefix: {system[:50]}")

    return mock_call


def make_websearch_mock(results_by_query: dict | None = None):
    """Return a websearch replacement. If results_by_query provided, dispatch
    by substring match; otherwise return a generic result."""

    def mock_search(query, max_tokens=None):
        content = "generic search result"
        if results_by_query:
            for key, val in results_by_query.items():
                if key in query:
                    content = val
                    break
        return {"query": query, "results": content, "timestamp": 0.0}

    return mock_search
```

- [ ] **Step 2: Write test `tests/test_phase_0.py`**

```python
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from eightd.phases.phase_0_research import phase_0_research
from tests.fixtures.mock_anthropic import make_call_claude_mock, make_websearch_mock


@pytest.fixture
def base_state():
    return {
        "problem": "daily_brief pipeline produced empty briefing",
        "run_id": "test-run-001",
        "run_dir": "/tmp/test-run-001",
    }


def test_phase_0_populates_all_required_fields(base_state, tmp_path, monkeypatch):
    # Mock wiki index path to point at tmp_path
    wiki_index = tmp_path / "index.md"
    wiki_index.write_text("- silent-staleness\n- self-healing-automation", encoding="utf-8")
    concepts_dir = tmp_path / "concepts"
    concepts_dir.mkdir()
    (concepts_dir / "silent-staleness.md").write_text("silent staleness content", encoding="utf-8")

    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_INDEX_PATH",
        wiki_index,
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_CONCEPTS_DIR",
        concepts_dir,
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "memory" / "feedback_*.md"),
    )

    call_claude_mock = make_call_claude_mock({
        "extract": ["pipeline", "empty briefing"],
        "Step back": {
            "categories": ["silent failure detection", "pipeline invariants", "data freshness"],
            "domains": ["ETL engineering", "monitoring systems", "fault-tolerant logging"],
        },
        "list up to 5": ["silent-staleness"],
    })
    websearch_mock = make_websearch_mock()

    with patch("eightd.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("eightd.phases.phase_0_research.websearch", side_effect=websearch_mock):
        result = phase_0_research(dict(base_state))

    assert result["phase_0_complete"] is True
    assert len(result["websearch_specific"]) == 2
    assert len(result["websearch_meta"]) == 15  # 3 categories × 5 sites
    assert len(result["websearch_cross_domain"]) == 3  # 3 domains
    assert len(result["meta_categories"]) == 3
    assert len(result["meta_domains"]) == 3
    assert len(result["wiki_pages"]) == 1


def test_phase_0_missing_wiki_does_not_crash(base_state, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_INDEX_PATH",
        tmp_path / "nonexistent.md",
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "nothing" / "feedback_*.md"),
    )
    call_claude_mock = make_call_claude_mock({
        "extract": ["kw"],
        "Step back": {"categories": ["c1", "c2", "c3"], "domains": ["d1", "d2", "d3"]},
    })
    with patch("eightd.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("eightd.phases.phase_0_research.websearch", side_effect=make_websearch_mock()):
        result = phase_0_research(dict(base_state))
    assert result["phase_0_complete"] is True
    assert result["wiki_pages"] == []
    assert result["memory_entries"] == []
```

- [ ] **Step 3: Run test, expect failure**

```bash
py -3 -m pytest tests/test_phase_0.py -v
```
Expected: FAIL (phase_0_research module missing).

- [ ] **Step 4: Implement `eightd/phases/phase_0_research.py`**

```python
"""Phase 0: dual-tier research — problem-specific + meta-level cross-domain.

CORE GUARANTEE: Phase 0 is Python-forced execution. Claude does NOT decide
whether to search. Python runs the searches; results go into state.
"""
import glob
import os
from pathlib import Path

from eightd.anthropic_client import call_claude, websearch
from eightd.models import model_for_role
from eightd.utils import load_prompt, safe_read_text

WIKI_INDEX_PATH = Path("D:/D-claude/personal-wiki/wiki/index.md")
WIKI_CONCEPTS_DIR = Path("D:/D-claude/personal-wiki/wiki/concepts")
MEMORY_GLOB = str(Path.home() / ".claude" / "projects" / "*" / "memory" / "feedback_*.md")

PROMINENT_SITES = [
    "github.com",
    "reddit.com",
    "stackoverflow.com",
    "news.ycombinator.com",
    "arxiv.org",
]


def phase_0_research(state: dict) -> dict:
    problem = state["problem"]

    # 0a: Problem-specific keywords + searches
    keywords = call_claude(
        model=model_for_role("keyword_extraction"),
        system=load_prompt("keyword_extraction"),
        user=problem,
        parse_json=True,
    )
    kw_str = " ".join(keywords)
    state["websearch_specific"] = [
        websearch(f"how to solve {kw_str}"),
        websearch(f"{kw_str} best practices 2026"),
    ]

    # 0b: Meta categorization + multi-site searches
    meta = call_claude(
        model=model_for_role("meta_categorization"),
        system=load_prompt("meta_categorization"),
        user=problem,
        parse_json=True,
    )
    state["meta_categories"] = meta["categories"]
    state["meta_domains"] = meta["domains"]

    state["websearch_meta"] = []
    for category in meta["categories"]:
        for site in PROMINENT_SITES:
            state["websearch_meta"].append(
                websearch(f"{category} site:{site}")
            )

    state["websearch_cross_domain"] = []
    for domain in meta["domains"]:
        state["websearch_cross_domain"].append(
            websearch(f"how does {domain} solve {meta['categories'][0]}")
        )

    # Wiki: index + up to 5 relevant concept pages
    state["wiki_pages"] = []
    wiki_index_text = safe_read_text(WIKI_INDEX_PATH)
    if wiki_index_text:
        relevant_slugs = call_claude(
            model=model_for_role("simple_classification"),
            system=(
                "From this wiki index, list up to 5 page slugs most relevant "
                "to the problem. Output a JSON array of slug strings."
            ),
            user=f"Index:\n{wiki_index_text}\n\nProblem:\n{problem}",
            parse_json=True,
        )
        for slug in relevant_slugs[:5]:
            page_path = WIKI_CONCEPTS_DIR / f"{slug}.md"
            content = safe_read_text(page_path)
            if content:
                state["wiki_pages"].append({"path": str(page_path), "content": content})

    # Memory: all feedback_*.md
    state["memory_entries"] = []
    for f in glob.glob(MEMORY_GLOB):
        content = safe_read_text(Path(f))
        if content:
            state["memory_entries"].append({"path": f, "content": content})

    state["phase_0_complete"] = True
    return state
```

- [ ] **Step 5: Run tests, expect pass**

```bash
py -3 -m pytest tests/test_phase_0.py -v
```
Expected: 2/2 PASS.

- [ ] **Step 6: Commit**

```bash
git add eightd/phases/phase_0_research.py tests/test_phase_0.py tests/fixtures/mock_anthropic.py
git commit -m "feat(phase_0): dual-tier forced research — problem-specific + meta"
```

---

---

## Task 8: Phase 1 (IS/IS NOT) + Phase 2 (Why analysis)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_1_is_isnt.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_2_why_analysis.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_2_exit.py`

- [ ] **Step 1: Implement `phase_1_is_isnt.py`**

```python
"""Phase 1: IS/IS NOT problem definition."""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt


def phase_1_is_isnt(state: dict) -> dict:
    context = (
        f"Problem:\n{state['problem']}\n\n"
        f"Research highlights (first 3 specific searches):\n"
    )
    for s in state.get("websearch_specific", [])[:3]:
        context += f"- Q: {s['query']}\n  Results: {s['results'][:300]}\n"

    result = call_claude(
        model=model_for_role("is_isnt_extraction"),
        system=load_prompt("is_isnt_extraction"),
        user=context,
        parse_json=True,
    )
    state["is_isnt_table"] = result
    state["phase_1_complete"] = True
    return state
```

- [ ] **Step 2: Implement `phase_2_why_analysis.py`**

```python
"""Phase 2: Why analysis — 4 quadrants, ≥10 whys each, enforced by count."""
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_2_why_analysis(state: dict) -> dict:
    chains = {}
    for quadrant in QUADRANTS:
        chain = _run_quadrant(state, quadrant)
        # Enforcement: retry if <10 whys
        attempts = 0
        while len(chain.get("whys", [])) < 10 and attempts < 3:
            chain = _run_quadrant(state, quadrant, retry_note=True)
            attempts += 1
        if len(chain.get("whys", [])) < 10:
            raise RuntimeError(f"Phase 2: {quadrant} failed to produce 10 whys after 3 retries")
        chains[quadrant] = chain
    state["why_chains"] = chains
    state["phase_2_complete"] = True
    return state


def _run_quadrant(state: dict, quadrant: str, retry_note: bool = False) -> dict:
    user_msg = (
        f"Quadrant: {quadrant}\n"
        f"Problem: {state['problem']}\n\n"
        f"IS/IS NOT:\n{state.get('is_isnt_table')}\n\n"
        f"Research context (top findings):\n"
    )
    for s in state.get("websearch_specific", [])[:2]:
        user_msg += f"- {s['query']}: {s['results'][:200]}\n"
    for w in state.get("wiki_pages", [])[:2]:
        user_msg += f"- wiki: {w['path']}\n  {w['content'][:300]}\n"
    if retry_note:
        user_msg += "\nIMPORTANT: prior attempt had fewer than 10 whys. Produce at least 10 distinct causal steps."
    return call_claude(
        model=model_for_role("why_analysis"),
        system=load_prompt("why_analysis"),
        user=user_msg,
        parse_json=True,
        max_tokens=12000,
    )
```

- [ ] **Step 3: Write test for Phase 2 exit criterion**

```python
# tests/test_phase_2_exit.py
from unittest.mock import patch
import pytest
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis


def _make_chain(n_whys):
    return {"quadrant": "q", "whys": [{"n": i, "why": f"w{i}"} for i in range(1, n_whys + 1)], "root": "r"}


def test_phase_2_requires_10_whys_per_quadrant():
    state = {
        "problem": "x",
        "is_isnt_table": {},
        "websearch_specific": [],
        "wiki_pages": [],
    }
    responses = [_make_chain(10)] * 4  # 4 quadrants
    with patch("eightd.phases.phase_2_why_analysis.call_claude", side_effect=responses):
        result = phase_2_why_analysis(state)
    assert result["phase_2_complete"] is True
    assert len(result["why_chains"]) == 4
    for q, chain in result["why_chains"].items():
        assert len(chain["whys"]) == 10


def test_phase_2_raises_if_cant_get_10_whys():
    state = {"problem": "x", "is_isnt_table": {}, "websearch_specific": [], "wiki_pages": []}
    # Always returns only 5 whys — should fail after 3 retries on first quadrant
    responses = [_make_chain(5)] * 20
    with patch("eightd.phases.phase_2_why_analysis.call_claude", side_effect=responses), \
         pytest.raises(RuntimeError, match="failed to produce 10 whys"):
        phase_2_why_analysis(state)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
py -3 -m pytest tests/test_phase_2_exit.py -v
```
Expected: 2/2 PASS.

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_1_is_isnt.py eightd/phases/phase_2_why_analysis.py tests/test_phase_2_exit.py
git commit -m "feat(phase_1,2): IS/IS NOT + Why analysis with ≥10 whys enforcement"
```

---

## Task 9: Phase 3 — SoA + RC audit loop

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_3_soa.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_3_rc_audit.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_3_loop.py`

- [ ] **Step 1: Implement `phase_3_soa.py`**

```python
"""Phase 3a: SoA research on root cause analysis best practice."""
from eightd.anthropic_client import websearch


def phase_3_soa_research(state: dict) -> dict:
    categories = state.get("meta_categories", [])
    cat0 = categories[0] if categories else "software failures"
    queries = [
        f"state of the art root cause analysis for {cat0}",
        "5 whys critique limitations alternatives 2026",
        "root cause analysis framework best practice site:github.com",
        "root cause analysis critique site:reddit.com",
        "fishbone vs 5whys vs FMEA site:stackexchange.com",
    ]
    state["phase_3_soa_research"] = [websearch(q) for q in queries]
    return state
```

- [ ] **Step 2: Implement `phase_3_rc_audit.py`**

```python
"""Phase 3b: RC audit with SoA citation requirement + loop-back routing."""
import json
import re
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt

URL_RE = re.compile(r"https?://[^\s)\"']+")


def phase_3_rc_audit(state: dict) -> dict:
    system = load_prompt("rc_audit")
    soa_context = _format_soa(state.get("phase_3_soa_research", []))
    soa_urls = _extract_urls(state.get("phase_3_soa_research", []))

    state.setdefault("phase_3_rounds", [])

    for round_num in range(1, 4):
        user_msg = (
            f"Round: {round_num}\n\n"
            f"Why chains:\n{json.dumps(state['why_chains'], ensure_ascii=False)[:5000]}\n\n"
            f"Phase 3a SoA research:\n{soa_context}"
        )
        audit = call_claude(
            model=model_for_role("rc_audit"),
            system=system,
            user=user_msg,
            parse_json=True,
        )
        state["phase_3_rounds"].append(audit)

        verdict = audit.get("verdict")
        if verdict == "EXHAUSTED":
            if _cites_soa(audit, soa_urls, min_citations=2):
                state["phase_3_verdict"] = "EXHAUSTED"
                state["phase_3_complete"] = True
                return state
            audit["rejection_reason"] = "verdict_EXHAUSTED_without_soa_citations"
            continue
        if verdict == "REWORK":
            state["phase_3_verdict"] = "REWORK"
            state["phase_3_complete"] = False
            return state
        # CONTINUE: apply addressable fixes and re-run
        state["why_chains"] = _apply_audit_fixes(state["why_chains"], audit)

    # Out of rounds without EXHAUSTED verdict
    state["phase_3_verdict"] = "REWORK"
    state["phase_3_complete"] = False
    return state


def _format_soa(research: list[dict]) -> str:
    out = []
    for r in research:
        out.append(f"Query: {r['query']}\nResults:\n{r['results'][:1500]}\n---\n")
    return "\n".join(out)


def _extract_urls(research: list[dict]) -> set[str]:
    urls = set()
    for r in research:
        urls.update(URL_RE.findall(r.get("results", "")))
    return urls


def _cites_soa(audit: dict, available_urls: set, min_citations: int = 2) -> bool:
    cited = set(audit.get("soa_citations_used", []))
    valid = cited & available_urls
    return len(valid) >= min_citations


def _apply_audit_fixes(why_chains: dict, audit: dict) -> dict:
    # Simple heuristic: append audit weaknesses as notes on affected whys
    for w in audit.get("weaknesses", []):
        q = w.get("quadrant")
        n = w.get("why_step_n")
        if q in why_chains and w.get("classification") == "ADDRESSABLE":
            for why in why_chains[q].get("whys", []):
                if why.get("n") == n:
                    why.setdefault("audit_notes", []).append(w.get("suggested_fix", ""))
    return why_chains


def route_from_phase_3(state: dict) -> str:
    """Conditional edge function for LangGraph."""
    if state.get("phase_3_verdict") == "REWORK":
        state["phase_2_complete"] = False
        return "phase_2_why_analysis"
    return "phase_4_actions"
```

- [ ] **Step 3: Write test**

```python
# tests/test_phase_3_loop.py
from unittest.mock import patch
import pytest
from eightd.phases.phase_3_rc_audit import (
    phase_3_rc_audit, _cites_soa, route_from_phase_3,
)


def test_cites_soa_true_when_enough_urls():
    audit = {"soa_citations_used": ["https://a.com", "https://b.com", "https://c.com"]}
    urls = {"https://a.com", "https://b.com"}
    assert _cites_soa(audit, urls, min_citations=2) is True


def test_cites_soa_false_when_urls_not_in_available():
    audit = {"soa_citations_used": ["https://fake.com"]}
    urls = {"https://real.com"}
    assert _cites_soa(audit, urls, min_citations=1) is False


def test_phase_3_exhausted_with_citations_completes():
    state = {
        "why_chains": {"q1_trc_nc": {"whys": []}},
        "phase_3_soa_research": [
            {"query": "x", "results": "See https://a.com and https://b.com"},
        ],
    }
    with patch(
        "eightd.phases.phase_3_rc_audit.call_claude",
        return_value={
            "round": 1,
            "weaknesses": [],
            "soa_citations_used": ["https://a.com", "https://b.com"],
            "verdict": "EXHAUSTED",
        },
    ):
        result = phase_3_rc_audit(state)
    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True


def test_phase_3_exhausted_without_citations_retries_then_reworks():
    state = {
        "why_chains": {"q1_trc_nc": {"whys": []}},
        "phase_3_soa_research": [{"query": "x", "results": "See https://a.com"}],
    }
    with patch(
        "eightd.phases.phase_3_rc_audit.call_claude",
        return_value={
            "round": 1,
            "weaknesses": [],
            "soa_citations_used": [],  # no citations
            "verdict": "EXHAUSTED",
        },
    ):
        result = phase_3_rc_audit(state)
    # Without citations, should be rejected and eventually REWORK after 3 rounds
    assert result["phase_3_verdict"] == "REWORK"
    assert result["phase_3_complete"] is False


def test_route_rework_goes_back_to_phase_2():
    state = {"phase_3_verdict": "REWORK"}
    assert route_from_phase_3(state) == "phase_2_why_analysis"
    assert state["phase_2_complete"] is False


def test_route_exhausted_goes_forward():
    state = {"phase_3_verdict": "EXHAUSTED"}
    assert route_from_phase_3(state) == "phase_4_actions"
```

- [ ] **Step 4: Run tests, expect pass**

```bash
py -3 -m pytest tests/test_phase_3_loop.py -v
```
Expected: 6/6 PASS.

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_3_soa.py eightd/phases/phase_3_rc_audit.py tests/test_phase_3_loop.py
git commit -m "feat(phase_3): SoA research + RC audit with citation requirement + loop routing"
```

---

## Task 10: Phase 4 — Corrective + Prevention per quadrant

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_4_actions.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_4_actions.py`

- [ ] **Step 1: Implement `phase_4_actions.py`**

```python
"""Phase 4: Corrective + Prevention actions, 4 quadrants each."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_4_actions(state: dict) -> dict:
    corrective_prompt = load_prompt("corrective_action")
    prevention_prompt = load_prompt("prevention_action")

    state["corrective_actions"] = {}
    state["prevention_actions"] = {}

    for quadrant in QUADRANTS:
        root_cause_chain = state["why_chains"].get(quadrant, {})
        user_payload = json.dumps({
            "quadrant": quadrant,
            "root_cause": root_cause_chain,
            "problem": state["problem"],
        }, ensure_ascii=False)

        corrective = call_claude(
            model=model_for_role("corrective_action"),
            system=corrective_prompt,
            user=user_payload,
            parse_json=True,
        )
        state["corrective_actions"][quadrant] = corrective

        prevention = call_claude(
            model=model_for_role("prevention_action"),
            system=prevention_prompt,
            user=user_payload,
            parse_json=True,
        )
        state["prevention_actions"][quadrant] = prevention

    state["phase_4_complete"] = True
    return state
```

- [ ] **Step 2: Write test**

```python
# tests/test_phase_4_actions.py
from unittest.mock import patch
from eightd.phases.phase_4_actions import phase_4_actions
from eightd.state import QUADRANTS


def test_phase_4_produces_both_corrective_and_prevention_per_quadrant():
    state = {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"} for q in QUADRANTS},
    }

    def fake_call(model, system, user, parse_json=False, **kw):
        if "corrective" in system.lower():
            return {"quadrant": "x", "action": "fix this instance", "rationale": "..."}
        return {"quadrant": "x", "action": "prevent class", "gate_test": {"scope": "PASS"}, "hierarchy_level": 2}

    with patch("eightd.phases.phase_4_actions.call_claude", side_effect=fake_call):
        result = phase_4_actions(state)

    assert set(result["corrective_actions"].keys()) == set(QUADRANTS)
    assert set(result["prevention_actions"].keys()) == set(QUADRANTS)
    assert result["phase_4_complete"] is True
```

- [ ] **Step 3: Run test**

```bash
py -3 -m pytest tests/test_phase_4_actions.py -v
```
Expected: 1/1 PASS.

- [ ] **Step 4: Commit**

```bash
git add eightd/phases/phase_4_actions.py tests/test_phase_4_actions.py
git commit -m "feat(phase_4): corrective + prevention actions per quadrant"
```

---

## Task 11: Phase 5 — SoA + Prevention audit loop

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_5_soa.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_5_prevention_audit.py`

- [ ] **Step 1: Implement `phase_5_soa.py`**

```python
"""Phase 5a: SoA research on prevention methods."""
from eightd.anthropic_client import websearch


def phase_5_soa_research(state: dict) -> dict:
    categories = state.get("meta_categories", [])
    cat0 = categories[0] if categories else "software failures"
    queries = [
        f"state of the art prevention methods for {cat0}",
        f"poka-yoke error-proofing techniques 2026",
        f"fault tolerance design patterns site:github.com",
        f"preventive controls best practices site:reddit.com",
        f"defense in depth strategies site:arxiv.org",
    ]
    state["phase_5_soa_research"] = [websearch(q) for q in queries]
    return state
```

- [ ] **Step 2: Implement `phase_5_prevention_audit.py`**

Reuses helpers from phase_3 module:

```python
"""Phase 5b: Prevention audit with SoA citation requirement."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.phases.phase_3_rc_audit import _format_soa, _extract_urls, _cites_soa


def phase_5_prevention_audit(state: dict) -> dict:
    system = load_prompt("prevention_audit")
    soa_context = _format_soa(state.get("phase_5_soa_research", []))
    soa_urls = _extract_urls(state.get("phase_5_soa_research", []))

    state.setdefault("phase_5_rounds", [])

    for round_num in range(1, 4):
        user_msg = (
            f"Round: {round_num}\n\n"
            f"Prevention actions:\n"
            f"{json.dumps(state['prevention_actions'], ensure_ascii=False)[:5000]}\n\n"
            f"Phase 5a SoA research:\n{soa_context}"
        )
        audit = call_claude(
            model=model_for_role("prevention_audit"),
            system=system,
            user=user_msg,
            parse_json=True,
        )
        state["phase_5_rounds"].append(audit)

        verdict = audit.get("verdict")
        if verdict == "EXHAUSTED":
            if _cites_soa(audit, soa_urls, min_citations=2):
                state["phase_5_verdict"] = "EXHAUSTED"
                state["phase_5_complete"] = True
                return state
            audit["rejection_reason"] = "verdict_EXHAUSTED_without_soa_citations"
            continue
        if verdict == "REWORK":
            state["phase_5_verdict"] = "REWORK"
            state["phase_5_complete"] = False
            return state
        # CONTINUE: note weaknesses but keep actions; iterate
        for w in audit.get("weaknesses", []):
            q = w.get("quadrant")
            if q in state["prevention_actions"]:
                state["prevention_actions"][q].setdefault("audit_notes", []).append(
                    w.get("suggested_fix", "")
                )

    state["phase_5_verdict"] = "REWORK"
    state["phase_5_complete"] = False
    return state


def route_from_phase_5(state: dict) -> str:
    if state.get("phase_5_verdict") == "REWORK":
        state["phase_4_complete"] = False
        return "phase_4_actions"
    return "phase_6_verification"
```

- [ ] **Step 3: Commit**

```bash
git add eightd/phases/phase_5_soa.py eightd/phases/phase_5_prevention_audit.py
git commit -m "feat(phase_5): SoA research + prevention audit with citation requirement"
```

---

## Task 12: Phase 6 — Verification plan + Proof of Action matrix

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_6_verification.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_6_proof.py`

- [ ] **Step 1: Implement `phase_6_verification.py`**

```python
"""Phase 6: Verification plan + Proof of Action 4-quadrant matrix."""
import json
from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt
from eightd.state import QUADRANTS


def phase_6_verification(state: dict) -> dict:
    proof_prompt = load_prompt("proof_of_action")
    state["proof_of_action"] = {}

    for quadrant in QUADRANTS:
        payload = json.dumps({
            "quadrant": quadrant,
            "corrective": state["corrective_actions"].get(quadrant, {}),
            "prevention": state["prevention_actions"].get(quadrant, {}),
        }, ensure_ascii=False)
        proof = call_claude(
            model=model_for_role("proof_of_action"),
            system=proof_prompt,
            user=payload,
            parse_json=True,
        )
        state["proof_of_action"][quadrant] = proof

    # Overall verification plan: simple summary across quadrants
    state["verification_plan"] = {
        "metrics": [state["proof_of_action"][q].get("metric") for q in QUADRANTS],
        "data_sources": [state["proof_of_action"][q].get("data_source") for q in QUADRANTS],
        "timeframe_default": "6 months",
        "failure_response_default": "re-open 8D for the affected quadrant",
    }
    state["phase_6_complete"] = True
    return state
```

- [ ] **Step 2: Write test**

```python
# tests/test_phase_6_proof.py
from unittest.mock import patch
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.state import QUADRANTS


def test_phase_6_produces_proof_for_all_4_quadrants():
    state = {
        "corrective_actions": {q: {"action": "c"} for q in QUADRANTS},
        "prevention_actions": {q: {"action": "p"} for q in QUADRANTS},
    }

    def fake_call(model, system, user, parse_json=False, **kw):
        return {
            "quadrant": "x",
            "metric": "count",
            "data_source": "log",
            "target": "zero",
            "baseline": "5",
            "measurement_schedule": "daily",
            "failure_response": "re-open",
        }

    with patch("eightd.phases.phase_6_verification.call_claude", side_effect=fake_call):
        result = phase_6_verification(state)

    assert set(result["proof_of_action"].keys()) == set(QUADRANTS)
    for q in QUADRANTS:
        assert "metric" in result["proof_of_action"][q]
        assert "target" in result["proof_of_action"][q]
    assert result["phase_6_complete"] is True
```

- [ ] **Step 3: Run test**

```bash
py -3 -m pytest tests/test_phase_6_proof.py -v
```

- [ ] **Step 4: Commit**

```bash
git add eightd/phases/phase_6_verification.py tests/test_phase_6_proof.py
git commit -m "feat(phase_6): verification plan + Proof of Action 4-quadrant matrix"
```

---

## Task 13: Phase 7 — SoA + Report + email delivery

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_soa.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_report.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/delivery/email.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_email_delivery.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/templates/8d_report_template.md`

- [ ] **Step 1: Implement `phase_7_soa.py`**

```python
"""Phase 7a: light SoA research on 8D report framing (shorter, less critical)."""
from eightd.anthropic_client import websearch


def phase_7_soa_research(state: dict) -> dict:
    queries = [
        "8D report best practice 2026 site:github.com",
        "root cause analysis report quality rubric",
        "8D D5 D6 D7 D8 explained site:reddit.com",
    ]
    state["phase_7_soa_research"] = [websearch(q) for q in queries]
    return state
```

- [ ] **Step 2: Modify `templates/8d_report_template.md`**

Read current file; replace entirely with:

```markdown
# 8D Report: {problem_slug}

**Date**: {date}
**Problem**: {problem}
**Run ID**: {run_id}

---

## Section A: Root Cause Matrix

|       | Non-Conformance (NC)                 | Non-Detection (ND)                   |
|-------|--------------------------------------|--------------------------------------|
| TRC   | Q1: {q1_trc_nc_root}                 | Q2: {q2_trc_nd_root}                 |
| MRC   | Q3: {q3_mrc_nc_root}                 | Q4: {q4_mrc_nd_root}                 |

---

## Section B: Corrective Actions Matrix

|       | Non-Conformance (NC)                 | Non-Detection (ND)                   |
|-------|--------------------------------------|--------------------------------------|
| TRC   | Q1: {q1_corrective}                  | Q2: {q2_corrective}                  |
| MRC   | Q3: {q3_corrective}                  | Q4: {q4_corrective}                  |

---

## Section B2: Prevention Actions Matrix

|       | Non-Conformance (NC)                 | Non-Detection (ND)                   |
|-------|--------------------------------------|--------------------------------------|
| TRC   | Q1: {q1_prevention}                  | Q2: {q2_prevention}                  |
| MRC   | Q3: {q3_prevention}                  | Q4: {q4_prevention}                  |

---

## Section C: Proof of Action Matrix

|       | Non-Conformance (NC)                                       | Non-Detection (ND)                                         |
|-------|------------------------------------------------------------|------------------------------------------------------------|
| TRC   | Q1: metric={q1_metric}, target={q1_target}                 | Q2: metric={q2_metric}, target={q2_target}                 |
| MRC   | Q3: metric={q3_metric}, target={q3_target}                 | Q4: metric={q4_metric}, target={q4_target}                 |

---

## Phase 1: IS / IS NOT

{is_isnt_table_rendered}

---

## Phase 2: Why Chains (4 quadrants)

{why_chains_rendered}

---

## Phase 3: RC Audit Rounds

{phase_3_rounds_rendered}

---

## Phase 4: Full Actions (Corrective + Prevention) per Quadrant

{phase_4_rendered}

---

## Phase 5: Prevention Audit Rounds

{phase_5_rounds_rendered}

---

## Phase 6: Verification Plan + Proof of Action

{phase_6_rendered}

---

## SoA Citations (deduplicated)

{soa_citations_rendered}

---

## Closure Audit

{closure_audit_rendered}

---

## Wiki Ingest Drafts

{wiki_ingest_drafts_rendered}
```

- [ ] **Step 3: Implement `eightd/delivery/email.py`**

```python
"""Outlook COM email delivery for 8D reports (Windows only)."""
import json
import os
from datetime import datetime
from pathlib import Path


def send_8d_report_email(report_md: str, report_path: Path, problem_summary: str) -> str:
    """Send report via Outlook COM. Returns log string."""
    import win32com.client

    html_body = _md_to_html(report_md)

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = _get_recipient()
    mail.Subject = f"[8D Report] {problem_summary[:100]} — {datetime.now():%Y-%m-%d}"
    mail.HTMLBody = html_body
    if report_path.exists():
        mail.Attachments.Add(str(report_path.resolve()))
    mail.Send()

    return f"OK: sent to {mail.To} at {datetime.now().isoformat()}"


def _get_recipient() -> str:
    cfg_path = Path.home() / ".claude" / "email.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))["recipient"]
        except Exception:
            pass
    return os.environ.get("CLAUDE_EIGHTD_EMAIL", "")


def _md_to_html(md_text: str) -> str:
    try:
        import markdown
        body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        import html as html_mod
        body = (
            "<pre style='white-space:pre-wrap;font-family:monospace'>"
            + html_mod.escape(md_text)
            + "</pre>"
        )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "body{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;"
        "padding:20px;line-height:1.6}"
        "h1{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}"
        "h2{color:#2980b9;margin-top:30px}"
        "table{border-collapse:collapse;margin:15px 0}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
        "th{background:#f4f4f4}"
        "</style></head><body>"
        + body
        + "</body></html>"
    )
```

- [ ] **Step 4: Implement `phase_7_report.py`**

```python
"""Phase 7: render report + closure audit + email delivery."""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from eightd.anthropic_client import call_claude
from eightd.models import model_for_role
from eightd.utils import load_prompt, sluggify
from eightd.delivery.email import send_8d_report_email

URL_RE = re.compile(r"https?://[^\s)\"']+")


def phase_7_report(state: dict) -> dict:
    rendered = _render_report(state)

    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    run_report = run_dir / "report.md"
    run_report.write_text(rendered, encoding="utf-8")

    canonical = _canonical_report_path(state)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(rendered, encoding="utf-8")
    state["report_path"] = str(canonical)

    # Closure audit (uses phase_7 SoA context)
    state["closure_audit"] = _run_closure_audit(state)

    # Email delivery (non-blocking on failure)
    try:
        log = send_8d_report_email(
            report_md=rendered,
            report_path=canonical,
            problem_summary=state["problem"][:200],
        )
        state["email_sent"] = True
        state["email_delivery_log"] = log
    except Exception as e:
        state["email_sent"] = False
        state["email_delivery_log"] = f"FAIL: {type(e).__name__}: {e}"

    state["phase_7_complete"] = True
    return state


def _canonical_report_path(state: dict) -> Path:
    slug = sluggify(state["problem"])
    date_str = datetime.now().strftime("%Y-%m-%d")
    # Default output: D:/D-claude/daily_brief/docs/8d-reports/ (existing convention)
    # If CLAUDE_EIGHTD_REPORTS_DIR env var set, use that instead.
    import os
    base = os.environ.get(
        "CLAUDE_EIGHTD_REPORTS_DIR",
        "D:/D-claude/daily_brief/docs/8d-reports",
    )
    return Path(base) / f"8d-{date_str}-{slug}.md"


def _render_report(state: dict) -> str:
    """Render report using LLM from state. Uses report_render.txt as system prompt."""
    template_path = Path(__file__).parent.parent.parent / "templates" / "8d_report_template.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    # LLM renders the final markdown using state + template
    rendered = call_claude(
        model=model_for_role("report_generation"),
        system=load_prompt("report_render") + "\n\nTemplate to follow:\n" + template,
        user=json.dumps(_state_summary(state), ensure_ascii=False),
        max_tokens=16000,
    )
    return rendered


def _state_summary(state: dict) -> dict:
    """Extract key fields for report rendering, trimming large lists."""
    return {
        "problem": state.get("problem"),
        "run_id": state.get("run_id"),
        "date": datetime.now().isoformat(),
        "is_isnt_table": state.get("is_isnt_table"),
        "why_chains": state.get("why_chains"),
        "corrective_actions": state.get("corrective_actions"),
        "prevention_actions": state.get("prevention_actions"),
        "proof_of_action": state.get("proof_of_action"),
        "verification_plan": state.get("verification_plan"),
        "phase_3_rounds": state.get("phase_3_rounds"),
        "phase_5_rounds": state.get("phase_5_rounds"),
        "soa_urls_deduped": sorted(_collect_soa_urls(state)),
    }


def _collect_soa_urls(state: dict) -> set:
    urls = set()
    for key in ["phase_3_soa_research", "phase_5_soa_research", "phase_7_soa_research"]:
        for entry in state.get(key, []):
            urls.update(URL_RE.findall(entry.get("results", "")))
    return urls


def _run_closure_audit(state: dict) -> dict:
    """Simple rule-based closure audit; LLM may be added later."""
    checks = {
        "root_cause_matrix_complete": all(
            q in state.get("why_chains", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "corrective_matrix_complete": all(
            q in state.get("corrective_actions", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "proof_matrix_complete": all(
            q in state.get("proof_of_action", {}) for q in
            ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
        ),
        "phase_3_exhausted": state.get("phase_3_verdict") == "EXHAUSTED",
        "phase_5_exhausted": state.get("phase_5_verdict") == "EXHAUSTED",
    }
    checks["overall_pass"] = all(checks.values())
    return checks
```

- [ ] **Step 5: Write email test**

```python
# tests/test_email_delivery.py
import sys
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Outlook COM only on Windows"
)


def test_send_email_calls_outlook(tmp_path):
    from eightd.delivery.email import send_8d_report_email

    fake_report = tmp_path / "r.md"
    fake_report.write_text("# test", encoding="utf-8")

    with patch("eightd.delivery.email.win32com") as mock_com, \
         patch("eightd.delivery.email._get_recipient", return_value="test@example.com"):
        mock_app = MagicMock()
        mock_mail = MagicMock()
        mock_app.CreateItem.return_value = mock_mail
        mock_com.client.Dispatch.return_value = mock_app

        log = send_8d_report_email("# test md", fake_report, "test problem")

    assert mock_mail.Send.called
    assert "OK" in log
```

- [ ] **Step 6: Run tests**

```bash
py -3 -m pytest tests/test_email_delivery.py -v
```
Expected: 1 PASS (or SKIPPED on non-Windows).

- [ ] **Step 7: Commit**

```bash
git add eightd/phases/phase_7_soa.py eightd/phases/phase_7_report.py eightd/delivery/email.py tests/test_email_delivery.py templates/8d_report_template.md
git commit -m "feat(phase_7): SoA + report render + closure + Outlook email delivery"
```

---

## Task 14: Graph construction (`eightd/graph.py`)

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/graph.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_graph_topology.py`

- [ ] **Step 1: Implement `graph.py`**

```python
"""LangGraph StateGraph construction for 8D pipeline."""
from langgraph.graph import StateGraph, START, END
from eightd.state import EightDState

from eightd.phases.phase_0_research import phase_0_research
from eightd.phases.phase_1_is_isnt import phase_1_is_isnt
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis
from eightd.phases.phase_3_soa import phase_3_soa_research
from eightd.phases.phase_3_rc_audit import phase_3_rc_audit, route_from_phase_3
from eightd.phases.phase_4_actions import phase_4_actions
from eightd.phases.phase_5_soa import phase_5_soa_research
from eightd.phases.phase_5_prevention_audit import (
    phase_5_prevention_audit, route_from_phase_5,
)
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.phases.phase_7_soa import phase_7_soa_research
from eightd.phases.phase_7_report import phase_7_report


def build_graph(checkpointer=None):
    g = StateGraph(EightDState)

    g.add_node("phase_0_research", phase_0_research)
    g.add_node("phase_1_is_isnt", phase_1_is_isnt)
    g.add_node("phase_2_why_analysis", phase_2_why_analysis)
    g.add_node("phase_3_soa", phase_3_soa_research)
    g.add_node("phase_3_rc_audit", phase_3_rc_audit)
    g.add_node("phase_4_actions", phase_4_actions)
    g.add_node("phase_5_soa", phase_5_soa_research)
    g.add_node("phase_5_prevention_audit", phase_5_prevention_audit)
    g.add_node("phase_6_verification", phase_6_verification)
    g.add_node("phase_7_soa", phase_7_soa_research)
    g.add_node("phase_7_report", phase_7_report)

    g.add_edge(START, "phase_0_research")
    g.add_edge("phase_0_research", "phase_1_is_isnt")
    g.add_edge("phase_1_is_isnt", "phase_2_why_analysis")
    g.add_edge("phase_2_why_analysis", "phase_3_soa")
    g.add_edge("phase_3_soa", "phase_3_rc_audit")
    g.add_conditional_edges(
        "phase_3_rc_audit",
        route_from_phase_3,
        {
            "phase_2_why_analysis": "phase_2_why_analysis",
            "phase_4_actions": "phase_4_actions",
        },
    )
    g.add_edge("phase_4_actions", "phase_5_soa")
    g.add_edge("phase_5_soa", "phase_5_prevention_audit")
    g.add_conditional_edges(
        "phase_5_prevention_audit",
        route_from_phase_5,
        {
            "phase_4_actions": "phase_4_actions",
            "phase_6_verification": "phase_6_verification",
        },
    )
    g.add_edge("phase_6_verification", "phase_7_soa")
    g.add_edge("phase_7_soa", "phase_7_report")
    g.add_edge("phase_7_report", END)

    return g.compile(checkpointer=checkpointer)
```

- [ ] **Step 2: Write topology test**

```python
# tests/test_graph_topology.py
from eightd.graph import build_graph


def test_graph_compiles():
    g = build_graph()
    assert g is not None


def test_graph_has_all_phase_nodes():
    g = build_graph()
    expected_nodes = {
        "phase_0_research", "phase_1_is_isnt", "phase_2_why_analysis",
        "phase_3_soa", "phase_3_rc_audit",
        "phase_4_actions",
        "phase_5_soa", "phase_5_prevention_audit",
        "phase_6_verification",
        "phase_7_soa", "phase_7_report",
    }
    # get_graph() returns a drawable representation
    nodes = set(g.get_graph().nodes.keys())
    # nodes includes "__start__" and "__end__"; check expected are subset
    assert expected_nodes.issubset(nodes)
```

- [ ] **Step 3: Run test**

```bash
py -3 -m pytest tests/test_graph_topology.py -v
```

- [ ] **Step 4: Commit**

```bash
git add eightd/graph.py tests/test_graph_topology.py
git commit -m "feat: LangGraph StateGraph construction with conditional edges"
```

---

## Task 15: CLI entry point (`run_8d.py`) + checkpointer

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/run_8d.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_checkpointer.py`

- [ ] **Step 1: Implement `run_8d.py`**

```python
"""CLI entry point for 8D MRC LangGraph pipeline."""
import argparse
import shutil
import sys
import time
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from eightd.graph import build_graph

RUNS_DIR = Path(__file__).parent / "runs"
RUN_RETENTION_DAYS = 30


def main():
    ap = argparse.ArgumentParser(prog="run_8d")
    ap.add_argument("problem", nargs="?", help="Problem description")
    ap.add_argument("--resume", dest="resume_id")
    ap.add_argument("--gc", action="store_true", help="Clean runs older than 30d")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.gc:
        gc_runs()
        return 0

    if not args.problem and not args.resume_id:
        ap.error("problem is required (or use --resume <run_id>)")

    run_id = args.resume_id or f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    db_path = run_dir / "checkpoint.db"
    saver = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")

    with saver as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": run_id}}

        if args.resume_id:
            initial = None
        else:
            initial = {
                "problem": args.problem,
                "run_id": run_id,
                "run_dir": str(run_dir),
            }

        if args.dry_run:
            print(f"Would invoke graph with run_id={run_id}")
            return 0

        final_state = graph.invoke(initial, config=config)

    if final_state.get("phase_7_complete"):
        report_path = final_state.get("report_path")
        print(report_path)  # stdout path for Claude Code consumer
        # Clean up run dir on success
        shutil.rmtree(run_dir, ignore_errors=True)
        return 0

    print(
        f"Run incomplete. Use --resume {run_id} to continue.",
        file=sys.stderr,
    )
    return 2


def gc_runs():
    cutoff = time.time() - RUN_RETENTION_DAYS * 86400
    if not RUNS_DIR.exists():
        return
    for rundir in RUNS_DIR.iterdir():
        if rundir.is_dir() and rundir.stat().st_mtime < cutoff:
            shutil.rmtree(rundir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write checkpointer smoke test**

```python
# tests/test_checkpointer.py
import sys
import subprocess
from pathlib import Path


def test_gc_flag_does_not_crash():
    script = Path(__file__).parent.parent / "run_8d.py"
    result = subprocess.run(
        [sys.executable, str(script), "--gc"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0


def test_dry_run_prints_plan():
    script = Path(__file__).parent.parent / "run_8d.py"
    result = subprocess.run(
        [sys.executable, str(script), "test problem", "--dry-run"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "Would invoke" in result.stdout
```

- [ ] **Step 3: Run test**

```bash
py -3 -m pytest tests/test_checkpointer.py -v
```

- [ ] **Step 4: Commit**

```bash
git add run_8d.py tests/test_checkpointer.py
git commit -m "feat: run_8d.py CLI with SqliteSaver checkpointer + gc + dry-run"
```

---

## Task 16: Replace SKILL.md with thin wrapper

**Files:**
- Rename: `D:/D-claude/skills/skill-8d-mrc/SKILL.md` → `SKILL.md.backup-20260420`
- Replace: `D:/D-claude/skills/skill-8d-mrc/SKILL.md`

- [ ] **Step 1: Backup original**

```bash
cd D:/D-claude/skills/skill-8d-mrc
cp SKILL.md SKILL.md.backup-20260420
```

- [ ] **Step 2: Write new thin wrapper to `SKILL.md`** (overwrite)

```markdown
# 8D MRC — LangGraph-driven

This skill runs a FSM-enforced 8D root cause analysis. Phase order and exit
criteria are enforced by Python code, not markdown.

## Invocation

When the user asks for 8D analysis, execute via Bash:

    py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "<problem description>"

Optional flags:
    --resume <run_id>     Resume an interrupted run
    --gc                  Clean runs older than 30 days
    --dry-run             Plan only; do not call Anthropic API

## What the user gets

On success, `run_8d.py` prints the path to the final report on stdout.
The report is saved at a canonical project location (default:
`D:/D-claude/daily_brief/docs/8d-reports/`, overridable via
`CLAUDE_EIGHTD_REPORTS_DIR` env var). The report is also emailed to
the user via Outlook COM (configured in `~/.claude/email.json`).

Summarize the report for the user. Do not attempt to run phases manually —
the Python FSM is the only correct implementation.

## Legacy markdown

The original skill markdown is at `SKILL.md.backup-20260420` for reference.
Do not follow its instructions manually — use `run_8d.py`.

## Config

`~/.claude/email.json` (create if missing):
```json
{
  "recipient": "you@example.com",
  "enabled": true
}
```
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md SKILL.md.backup-20260420
git commit -m "refactor: replace SKILL.md with thin wrapper — LangGraph is primary"
```

---

## Task 17: Create email config + .governed-files entry

**Files:**
- Create: `~/.claude/email.json` (if not already exists)

- [ ] **Step 1: Create email config**

Check if `~/.claude/email.json` exists. If not, create:

```json
{
  "recipient": "kuangyu@realtek.com",
  "enabled": true
}
```

- [ ] **Step 2: Add to .governed-files manifest**

Read `~/.claude/.governed-files`; if `email.json` not listed, append:

```
email.json                      MONITORED   Email recipient config for 8d-mrc and related skills
```

- [ ] **Step 3: Commit (via auto-commit hook or manual)**

`~/.claude/` auto-commit+push hook triggers on Write.

---

## Task 18: Full pytest suite + fix failures

- [ ] **Step 1: Run full suite**

```bash
cd D:/D-claude/skills/skill-8d-mrc
py -3 -m pytest tests/ -v
```

- [ ] **Step 2: Fix any failures**

For each failing test, read the error, fix the underlying code or test, re-run.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: address pytest failures from full suite run"
```

---

## Task 19: Integration smoke test (real API)

- [ ] **Step 1: Run dry-run first**

```bash
cd D:/D-claude/skills/skill-8d-mrc
py -3 run_8d.py "test: simple recurring failure in a pipeline" --dry-run
```

Expected: exits 0, no API calls.

- [ ] **Step 2: Run real pipeline (small-scope problem)**

```bash
py -3 run_8d.py "test: skill-8d-mrc dry-run smoke check — why did an initial test fail"
```

Expected: completes in 5-15 min; prints report path to stdout; email sent.

- [ ] **Step 3: Verify outputs**

```bash
# Check report file exists
ls D:/D-claude/daily_brief/docs/8d-reports/8d-2026-04-21-*
# Check email was sent (check Outlook Sent folder manually, or hook log)
# Check runs/ was cleaned up
ls D:/D-claude/skills/skill-8d-mrc/runs/
# Expected: empty or only --resume abandoned runs
```

- [ ] **Step 4: Commit integration artifacts (if any)**

```bash
git add -A
git commit -m "test: integration smoke test completed successfully"
```

---

## Task 20: Push skill repo

- [ ] **Step 1: Push**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git push
```

---

## Self-Review Checklist

- [x] All spec goals covered by a task (Phase 0 dual-tier, SoA for 3/5/7, three 4-quadrant tables, email, runtime model selection, SQLite checkpointer, per-run cleanup)
- [x] No placeholders (all code shown verbatim in steps)
- [x] Type consistency (QUADRANTS constant reused; function signatures match)
- [x] TDD pattern: test → fail → implement → pass → commit per major component
- [x] Commit after every logical unit

---

## Execution Handoff

Per user instruction: **proceed directly to subagent-driven-development**, no approval gate.
REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`.

