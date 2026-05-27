"""Structural validation tests for skill-ai-escape-mrc-v1.yaml.

Validates the Managed Agents agent definition file has required keys,
correct model, expected tools, no MCP servers, and a resolvable system prompt.

WIKI-CONSULTED: degraded-emission-with-warning#fail-closed
WIKI-FINDING: agent YAML must specify model name and tools before deployment
WIKI-ACTION: these tests run in CI to catch YAML drift before live dispatch
"""
from __future__ import annotations
from pathlib import Path
import yaml

YAML_PATH = Path(__file__).parent.parent / "ai_escape_mrc" / "managed_agent" / "skill-ai-escape-mrc-v1.yaml"
YAML_DIR = YAML_PATH.parent


def _load_yaml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def test_yaml_parses():
    """YAML file must parse without errors."""
    doc = _load_yaml()
    assert isinstance(doc, dict)


def test_required_keys_present():
    """All mandatory keys must be present in the agent definition."""
    doc = _load_yaml()
    for key in ("name", "model", "tools"):
        assert key in doc, f"Required key missing: {key}"


def test_model_is_opus_4_6():
    """Model must be claude-opus-4-6 (spec requirement for AI Escape MRC quality)."""
    doc = _load_yaml()
    assert doc["model"] == "claude-opus-4-6", f"Unexpected model: {doc["model"]}"


def test_tools_include_websearch_and_agent_toolset():
    """Both websearch_20260401 and agent_toolset_20260401 must be listed."""
    doc = _load_yaml()
    tool_types = [t.get("type") for t in doc.get("tools", [])]
    assert "websearch_20260401" in tool_types, "websearch_20260401 missing from tools"
    assert "agent_toolset_20260401" in tool_types, "agent_toolset_20260401 missing from tools"


def test_no_mcp_servers_in_v1():
    """v1 must not configure MCP servers (avoids always_ask permission policy)."""
    doc = _load_yaml()
    mcp = doc.get("mcp_servers", [])
    assert mcp == [] or mcp is None, f"v1 should have no MCP servers; got: {mcp}"


def test_system_prompt_file_exists():
    """system_prompt_path must point to an existing file relative to the YAML."""
    doc = _load_yaml()
    prompt_rel = doc.get("system_prompt_path")
    assert prompt_rel is not None, "system_prompt_path key missing"
    prompt_abs = (YAML_DIR / prompt_rel).resolve()
    assert prompt_abs.exists(), f"system_prompt file not found: {prompt_abs}"
    # System prompt must not be empty
    content = prompt_abs.read_text(encoding="utf-8")
    assert len(content) > 500, f"system_prompt too short ({len(content)} chars)"
