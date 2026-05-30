"""Phase 0: dual-tier research ??problem-specific + meta-level cross-domain.

CORE GUARANTEE: Phase 0 is Python-forced execution. Claude does NOT decide
whether to search. Python runs the searches; results go into state.
"""
import glob
import sys
import time
from pathlib import Path

from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.sdk_client import call_claude, websearch
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.parallel import parallel_map
from ai_escape_mrc.stage_summary import emit_stage_progress
from ai_escape_mrc.utils import load_prompt, safe_read_text
from ai_escape_mrc import schemas

WIKI_INDEX_PATH = Path("D:/D-claude/personal-wiki/wiki/index.md")
WIKI_CONCEPTS_DIR = Path("D:/D-claude/personal-wiki/wiki/concepts")
MEMORY_GLOB = str(Path.home() / ".claude" / "projects" / "*" / "memory" / "feedback_*.md")

# Reduced 5 -> 2 sites per user feedback: "20 searches is overkill".
# Trade latency for coverage. GitHub (code) + Reddit (discussion) are the
# highest-signal sources; others can be added via additional AI Escape MRC runs if needed.
PROMINENT_SITES = [
    "github.com",
    "reddit.com",
]


def _safe_websearch(query_text: str) -> dict:
    """Run one websearch but never let a failure abort the whole pipeline.

    Phase 0 is "Python-forced" research, but a single search outage (network,
    rate limit, tool unavailable in the runtime) must NOT discard all upstream
    work. On failure we return an empty-result record tagged with the error so
    downstream phases degrade gracefully instead of crashing.
    """
    try:
        return websearch(query_text)
    except Exception as e:
        sys.stderr.write(
            f"[WARN] websearch failed for {query_text[:60]!r}: "
            f"{type(e).__name__}: {str(e)[:120]}; continuing without it\n"
        )
        return {
            "query": query_text,
            "results": "",
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "timestamp": time.time(),
        }


def phase_0_research(state: dict) -> dict:
    problem = state["problem"]

    # 0a: Problem-specific keywords (schema-constrained, defensive)
    emit_stage_progress(
        "phase_0_research",
        state,
        "Extracting problem keywords.",
        f"Problem length: {len(problem)} characters.",
    )
    try:
        kw_result = call_claude(
            model=model_for_role("keyword_extraction"),
            system=load_prompt("keyword_extraction"),
            user=problem,
            json_schema=schemas.KEYWORD_EXTRACTION,
            purpose="keyword_extraction",
        )
        keywords = kw_result.get("keywords") if isinstance(kw_result, dict) else None
        if not keywords:
            raise ValueError(f"empty keywords from LLM: {kw_result!r}")
    except VisibilityContractError:
        raise
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(f"[WARN] keyword_extraction failed: {str(e)[:150]}; using problem words\n")
        keywords = problem.split()[:5]
    kw_str = " ".join(keywords)
    emit_stage_progress(
        "phase_0_research",
        state,
        "Keyword extraction complete.",
        f"Keywords: {', '.join(str(k) for k in keywords[:6])}.",
    )

    # 0b: Meta categorization (schema-constrained, defensive)
    emit_stage_progress("phase_0_research", state, "Classifying meta failure categories.")
    try:
        meta = call_claude(
            model=model_for_role("meta_categorization"),
            system=load_prompt("meta_categorization"),
            user=problem,
            json_schema=schemas.META_CATEGORIZATION,
            purpose="meta_categorization",
        )
        if not isinstance(meta, dict) or "categories" not in meta or "domains" not in meta:
            raise ValueError(f"unexpected meta shape: {meta!r}")
    except VisibilityContractError:
        raise
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(f"[WARN] meta_categorization failed: {str(e)[:150]}; using stubs\n")
        meta = {
            "categories": ["workflow orchestration", "state invariant enforcement", "observability"],
            "domains": ["aerospace fault tolerance", "manufacturing quality control", "financial workflow"],
        }
    state["meta_categories"] = meta["categories"]
    state["meta_domains"] = meta["domains"]
    emit_stage_progress(
        "phase_0_research",
        state,
        "Meta categorization complete.",
        f"Categories: {', '.join(meta['categories'][:3])}.",
        f"Cross-domain analogies: {', '.join(meta['domains'][:3])}.",
    )

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
    emit_stage_progress(
        "phase_0_research",
        state,
        "Running web research batch.",
        f"Queries: {len(all_queries)} total ({len(specific_queries)} specific, "
        f"{len(meta_queries)} meta, {len(cross_queries)} cross-domain).",
        f"First query: {all_queries[0] if all_queries else '(none)'}",
    )
    all_results = parallel_map(_safe_websearch, all_queries, max_workers=5)
    emit_stage_progress(
        "phase_0_research",
        state,
        "Web research batch complete.",
        f"Results collected: {len(all_results)}.",
    )

    n_spec = len(specific_queries)
    n_meta = len(meta_queries)
    state["websearch_specific"] = all_results[:n_spec]
    state["websearch_meta"] = all_results[n_spec:n_spec + n_meta]
    state["websearch_cross_domain"] = all_results[n_spec + n_meta:]

    # Wiki: index + up to 5 relevant concept pages (defensive)
    state["wiki_pages"] = []
    wiki_index_text = safe_read_text(WIKI_INDEX_PATH)
    if wiki_index_text:
        emit_stage_progress("phase_0_research", state, "Selecting relevant wiki concept pages.")
        try:
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
            relevant_slugs = slug_result.get("slugs", []) if isinstance(slug_result, dict) else []
        except VisibilityContractError:
            raise
        except Exception as e:
            import sys as _sys
            _sys.stderr.write(f"[WARN] wiki slug selection failed: {str(e)[:150]}; skipping wiki\n")
            relevant_slugs = []
        for slug in relevant_slugs[:5]:
            page_path = WIKI_CONCEPTS_DIR / f"{slug}.md"
            content = safe_read_text(page_path)
            if content:
                state["wiki_pages"].append({"path": str(page_path), "content": content})
        emit_stage_progress(
            "phase_0_research",
            state,
            "Wiki concept loading complete.",
            f"Pages loaded: {len(state['wiki_pages'])}.",
        )
    else:
        emit_stage_progress("phase_0_research", state, "Wiki index not found; skipping wiki concept lookup.")

    # Memory: all feedback_*.md
    emit_stage_progress("phase_0_research", state, "Loading local feedback memory entries.")
    state["memory_entries"] = []
    for f in glob.glob(MEMORY_GLOB):
        content = safe_read_text(Path(f))
        if content:
            state["memory_entries"].append({"path": f, "content": content})
    emit_stage_progress(
        "phase_0_research",
        state,
        "Local memory loading complete.",
        f"Entries loaded: {len(state['memory_entries'])}.",
    )

    state["phase_0_complete"] = True
    return state
