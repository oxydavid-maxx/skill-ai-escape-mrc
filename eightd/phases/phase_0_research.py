"""Phase 0: dual-tier research — problem-specific + meta-level cross-domain.

CORE GUARANTEE: Phase 0 is Python-forced execution. Claude does NOT decide
whether to search. Python runs the searches; results go into state.
"""
import glob
from pathlib import Path

from eightd.anthropic_client import call_claude, websearch
from eightd.models import model_for_role
from eightd.parallel import parallel_map
from eightd.utils import load_prompt, safe_read_text
from eightd import schemas

WIKI_INDEX_PATH = Path("D:/D-claude/personal-wiki/wiki/index.md")
WIKI_CONCEPTS_DIR = Path("D:/D-claude/personal-wiki/wiki/concepts")
MEMORY_GLOB = str(Path.home() / ".claude" / "projects" / "*" / "memory" / "feedback_*.md")

# Reduced 5 -> 2 sites per user feedback: "20 searches is overkill".
# Trade latency for coverage. GitHub (code) + Reddit (discussion) are the
# highest-signal sources; others can be added via additional 8D runs if needed.
PROMINENT_SITES = [
    "github.com",
    "reddit.com",
]


def phase_0_research(state: dict) -> dict:
    problem = state["problem"]

    # 0a: Problem-specific keywords (schema-constrained)
    kw_result = call_claude(
        model=model_for_role("keyword_extraction"),
        system=load_prompt("keyword_extraction"),
        user=problem,
        json_schema=schemas.KEYWORD_EXTRACTION,
        purpose="keyword_extraction",
    )
    keywords = kw_result["keywords"]
    kw_str = " ".join(keywords)

    # 0b: Meta categorization (schema-constrained)
    meta = call_claude(
        model=model_for_role("meta_categorization"),
        system=load_prompt("meta_categorization"),
        user=problem,
        json_schema=schemas.META_CATEGORIZATION,
        purpose="meta_categorization",
    )
    state["meta_categories"] = meta["categories"]
    state["meta_domains"] = meta["domains"]

    # Build full websearch query list and run in parallel.
    # Order is preserved by parallel_map so we can slice back into sections.
    specific_queries = [
        f"how to solve {kw_str}",
        f"{kw_str} best practices 2026",
    ]
    meta_queries = [
        f"{category} site:{site}"
        for category in meta["categories"]
        for site in PROMINENT_SITES
    ]
    # Cross-domain: limit to 1 domain to save latency. First domain is most
    # semantically distant per Opus's ordering (reduced from 3 to 1).
    cross_queries = [
        f"how does {domain} solve {meta['categories'][0]}"
        for domain in meta["domains"][:1]
    ]

    all_queries = specific_queries + meta_queries + cross_queries
    all_results = parallel_map(websearch, all_queries, max_workers=5)

    n_spec = len(specific_queries)
    n_meta = len(meta_queries)
    state["websearch_specific"] = all_results[:n_spec]
    state["websearch_meta"] = all_results[n_spec:n_spec + n_meta]
    state["websearch_cross_domain"] = all_results[n_spec + n_meta:]

    # Wiki: index + up to 5 relevant concept pages
    state["wiki_pages"] = []
    wiki_index_text = safe_read_text(WIKI_INDEX_PATH)
    if wiki_index_text:
        slug_result = call_claude(
            model=model_for_role("simple_classification"),
            system=(
                "Pick up to 5 slug strings from the wiki index most relevant "
                "to the problem. Slugs must appear in the index verbatim."
            ),
            user=f"Index:\n{wiki_index_text}\n\nProblem:\n{problem}",
            json_schema=schemas.WIKI_SLUG_SELECTION,
            purpose="wiki_slug_selection",
        )
        relevant_slugs = slug_result["slugs"]
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
