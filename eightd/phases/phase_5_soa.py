"""Phase 5a: SoA research on prevention methods."""
from eightd.anthropic_client import websearch


def phase_5_soa_research(state: dict) -> dict:
    categories = state.get("meta_categories", [])
    cat0 = categories[0] if categories else "software failures"
    queries = [
        f"state of the art prevention methods for {cat0}",
        "poka-yoke error-proofing techniques 2026",
        "fault tolerance design patterns site:github.com",
        "preventive controls best practices site:reddit.com",
        "defense in depth strategies site:arxiv.org",
    ]
    state["phase_5_soa_research"] = [websearch(q) for q in queries]
    return state
