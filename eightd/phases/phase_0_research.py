"""Phase 0: dual-tier research — problem-specific + meta-level cross-domain.

CORE GUARANTEE: Phase 0 is Python-forced execution. Claude does NOT decide
whether to search. Python runs the searches; results go into state.
"""
import glob
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
