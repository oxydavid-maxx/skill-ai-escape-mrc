from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ActionItem(BaseModel):
    """Normalized action item from Phase 8 collection."""
    model_config = ConfigDict(strict=True, extra="forbid")
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    files_touched: list[str] = Field(default_factory=list)
    owner: str = "kuangyu"
    priority: Literal["low", "medium", "high", "verification"] = "medium"
    source_quadrant: str


class PhaseMetadata(BaseModel):
    """Runtime metadata from the cloud agent session."""
    model_config = ConfigDict(strict=True, extra="forbid")
    phases_completed: list[str]
    phase_durations_sec: dict[str, float]
    total_runtime_sec: float
    total_tokens_used: dict[str, int]


class CloudPayload(BaseModel):
    """Structured payload returned by the skill-8d-mrc Managed Agent.

    Strict mode + extra-forbidden so any deviation from the contract
    raises ValidationError at the boundary (R13 fail-closed).

    Per spec docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md.

    WIKI-CONSULTED: degraded-emission-with-warning
    WIKI-FINDING: producer must validate own output; never ship malformed artifact
    WIKI-ACTION: trigger_8d.py validates against this schema BEFORE writing artifacts
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    report_md: str = Field(..., min_length=1000)
    actions_json: list[ActionItem]
    plan_md: str = Field(..., min_length=500)
    phase_metadata: PhaseMetadata