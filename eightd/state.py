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

    # Phase 3: SoA + RC audit
    phase_3_soa_research: list[dict]
    phase_3_rounds: list[dict]
    phase_3_verdict: Optional[Literal["EXHAUSTED", "REWORK"]]
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
    phase_5_complete: bool
    phase_5_attempt_count: int  # outer Phase4<->Phase5 loop attempt

    # Phase 6: Verification + Proof of Action
    phase_6_complete: bool
    verification_plan: dict
    proof_of_action: dict

    # Phase 7: SoA + Report + closure + delivery
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
