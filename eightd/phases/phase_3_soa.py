"""Phase 3a: SoA research on root cause analysis best practice."""
from eightd.anthropic_client import websearch
from eightd.parallel import parallel_map


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
    state["phase_3_soa_research"] = parallel_map(websearch, queries)
    return state
