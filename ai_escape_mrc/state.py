"""AiEscapeMrcState: LangGraph state schema for the AI Escape MRC FSM."""
import operator
from typing import Annotated, TypedDict, Literal, Optional


def _take_last(_a, b):
    """Reducer: keep the most recent write (for keys touched by every node's
    progress wrapper, so concurrent parallel branches don't raise
    InvalidUpdateError)."""
    return b


class AiEscapeMrcState(TypedDict, total=False):
    # Input
    problem: str
    run_id: str
    run_dir: str
    user_email: Optional[str]
    operator_email: Optional[str]
    # Visibility accumulators written by EVERY node's progress wrapper — given
    # reducers so the tail's parallel branches (phase_6 ∥ phase_9) can both write
    # them in the same super-step. stage_summaries receives per-node deltas.
    screen_summary: Annotated[Optional[str], _take_last]
    stage_summaries: Annotated[list[dict], operator.add]
    stage_summaries_path: Annotated[Optional[str], _take_last]
    visibility_receipt: Annotated[dict, _take_last]

    # Phase 0: forced research
    phase_0_complete: bool
    websearch_specific: list[dict]
    websearch_meta: list[dict]
    websearch_cross_domain: list[dict]
    meta_categories: list[str]
    meta_domains: list[str]
    framing_reflection: dict  # soul-searching reflection between search waves
    wiki_pages: list[dict]
    memory_entries: list[dict]

    # Phase 1: IS/IS NOT
    phase_1_complete: bool
    is_isnt_table: dict

    # Phase 2: Why analysis
    phase_2_complete: bool
    why_chains: dict

    # Phase 3: SoA + RC audit
    phase_3_soa_research: list[dict]
    phase_3_rounds: list[dict]
    phase_3_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_3_status: Optional[Literal["passed", "failed"]]
    phase_3_residual_risks: list[dict]
    phase_3_complete: bool
    phase_3_attempt_count: int  # outer Phase2<->Phase3 loop attempt

    # Phase 4: Corrective + Prevention per quadrant
    phase_4_complete: bool
    corrective_actions: dict
    prevention_actions: dict

    # Phase 5: SoA + Prevention audit
    phase_5_soa_research: list[dict]
    phase_5_rounds: list[dict]
    phase_5_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
    phase_5_status: Optional[Literal["passed", "failed"]]
    phase_5_residual_risks: list[dict]
    phase_5_complete: bool
    phase_5_attempt_count: int  # outer Phase4<->Phase5 loop attempt

    # Phase 6: Verification + Proof of Action
    phase_6_complete: bool
    verification_plan: dict
    proof_of_action: dict

    # Phase 7: SoA + Report + closure + delivery
    phase_7_soa_research: list[dict]
    phase_7_complete: bool
    phase_7_legacy_emission: list[str]
    phase_7_bypassed_failures: list[str]
    phase_7_bypass_reason: Optional[str]
    report_path: Optional[str]
    wiki_ingest_drafts: list[dict]
    closure_audit: dict
    email_sent: bool
    email_delivery_log: Optional[str]
    email_delivery_result: Optional[str]
    email_delivery_error: Optional[str]
    delivery_status_path: Optional[str]
    recipient_to: Optional[str]
    recipient_cc: list[str]
    recipient_source: Optional[str]

    # Phase 8: collect actions for SDK auto-dispatch
    phase_8_complete: bool
    actions_path: Optional[str]
    actions_count: int

    # Phase 9: SDK dispatch ??writing-plans
    phase_9_complete: bool
    plan_path: Optional[str]
    phase_9_error: Optional[str]

    # Phase 10: final report/plan delivery
    phase_10_complete: bool

    # Metadata
    models_used: dict
    api_call_count: int
    start_time: str
    end_time: Optional[str]


QUADRANTS = ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
