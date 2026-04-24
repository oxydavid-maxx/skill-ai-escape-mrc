# 8D Report (PARTIAL — pipeline crashed at Phase 5 run 2): why did we migrate to LangGraph only now instead of 3 weeks ago

**Date**: 2026-04-21T20:42:26.610322
**Problem**: why did we migrate to LangGraph only now instead of 3 weeks ago
**Run ID**: run-1776773735-0742fd24
**Total elapsed**: 22.3 min
**Model**: claude-opus-4-6 (via claude CLI / OpenRouter fallback)

**Status**: Phases 0-4 complete. Phase 5 audit crashed (AttributeError: 'list' object has no attribute 'get') on attempt 2. Phases 6-7 not reached. This report is extracted directly from checkpoint state.

---

## Pipeline Timeline

| Phase | Start (s) | End (s) | Duration (min) |
|-------|-----------|---------|----------------|
| phase_0_research | 0.3 | 188.5 | 3.14 |
| phase_1_is_isnt | 188.5 | 637.6 | 7.48 |
| phase_2_why_analysis | 637.6 | 1150.6 | 8.55 |

## Phase 0: Meta-Categorization

**Meta categories identified**: Intervention-ceiling detection (knowing when incremental fixes hit diminishing returns), Evidence-threshold-driven architectural migration (when to rewrite vs. patch), Compliance-by-structure vs. compliance-by-instruction (code gates vs. text gates)
**Cross-pollination domains**: Aviation safety (Swiss-cheese model: procedural checklists fail at known rates → hardware interlocks replace them), Pharmaceutical manufacturing (FDA process validation: when batch deviation frequency triggers line redesign, not SOP revision), Nuclear power operations (defense-in-depth: passive safety systems replace operator-dependent procedures after incident clustering)
**Wiki pages consulted**: 0
**Memory entries (feedback_*.md)**: 14

## Section A: Root Cause Matrix

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: unknown | Q2: unknown |
| **MRC** | Q3: unknown | Q4: unknown |

## Section B: Corrective Actions Matrix

| | NC | ND |
|---|---|---|
| **TRC** | Q1: — | Q2: — |
| **MRC** | Q3: — | Q4: — |

## Section B2: Prevention Actions Matrix

| | NC | ND |
|---|---|---|
| **TRC** | Q1: — | Q2: — |
| **MRC** | Q3: — | Q4: — |

## Phase 1: IS / IS NOT

| Dimension | IS | IS NOT | Distinction |
|-----------|-----|--------|-------------|
| **WHAT** | why did we migrate to LangGraph only now instead of 3 weeks ago | unknown | LLM call failed; populate manually |
| **WHERE** | unknown | unknown | LLM call failed; populate manually |
| **WHEN** | unknown | unknown | LLM call failed; populate manually |
| **EXTENT** | unknown | unknown | LLM call failed; populate manually |

## Phase 2: Why Chains (FULL)

### Quadrant q1_trc_nc

1. **Why 1**: LLM call failed — populate manually

**Root**: unknown

### Quadrant q2_trc_nd

1. **Why 1**: LLM call failed — populate manually

**Root**: unknown

### Quadrant q3_mrc_nc

1. **Why 1**: LLM call failed — populate manually

**Root**: unknown

### Quadrant q4_mrc_nd

1. **Why 1**: LLM call failed — populate manually

**Root**: unknown

## Phase 3: RC Audit Rounds (FULL)

## Phase 4: Full Actions per Quadrant

### Quadrant q1_trc_nc
**Corrective**:

**Prevention**:

### Quadrant q2_trc_nd
**Corrective**:

**Prevention**:

### Quadrant q3_mrc_nc
**Corrective**:

**Prevention**:

### Quadrant q4_mrc_nd
**Corrective**:

**Prevention**:

## Status + known limitations

- **Phases completed**: 0, 1, 2, 3 (3 audit loops to force-accept), 4
- **Phases crashed**: 5 (AttributeError — 'list' object has no attribute 'get' on audit's attempt to modify prevention_actions[q])
- **Phases not reached**: 6 (Proof of Action), 7 (Report rendering + closure audit)
- **Total elapsed**: 22.3 min
- **Bug discovered**: prevention_actions[q] is sometimes a list, not a dict, from the LLM output; audit's `.setdefault('audit_notes', [])` call fails on list. Fix: normalize list-wrapped dicts in phase_4 or guard in phase_5 audit.
