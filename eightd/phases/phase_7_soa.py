"""Phase 7a: light SoA research on 8D report framing."""
from eightd.anthropic_client import websearch


def phase_7_soa_research(state: dict) -> dict:
    queries = [
        "8D report best practice 2026 site:github.com",
        "root cause analysis report quality rubric",
        "8D D5 D6 D7 D8 explained site:reddit.com",
    ]
    state["phase_7_soa_research"] = [websearch(q) for q in queries]
    return state
