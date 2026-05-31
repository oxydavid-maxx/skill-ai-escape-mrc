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
from ai_escape_mrc.parallel import parallel_map, parallel_run
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


def _reflect_on_framing(state: dict, problem: str, wave1_results: list) -> dict:
    """High-level reflection between search waves. Returns a dict with
    reframing / higher_level_question / wave2_queries. Best-effort: on failure
    returns an empty-ish dict so Phase 0 can fall back to default wave-2 queries."""
    findings = ""
    for r in wave1_results:
        if isinstance(r, dict):
            findings += f"- Q: {r.get('query', '')}\n  {str(r.get('results', ''))[:400]}\n"
    user_msg = (
        f"Problem:\n{problem}\n\n"
        f"Wave 1 search findings:\n{findings or '(no results retrieved)'}\n\n"
        "Reflect at the framing level and choose 3-4 follow-up searches."
    )
    try:
        out = call_claude(
            model=model_for_role("search_reflection"),
            system=load_prompt("search_reflection"),
            user=user_msg,
            json_schema=schemas.SEARCH_REFLECTION,
            purpose="search_reflection",
        )
        return out if isinstance(out, dict) else {}
    except VisibilityContractError:
        raise
    except Exception as e:
        sys.stderr.write(f"[WARN] search reflection failed: {str(e)[:150]}; using default wave-2 queries\n")
        return {}


def _extract_keywords(problem: str) -> list:
    try:
        kw_result = call_claude(
            model=model_for_role("keyword_extraction"),
            system=load_prompt("keyword_extraction"),
            user=problem,
            json_schema=schemas.KEYWORD_EXTRACTION,
            purpose="keyword_extraction",
        )
        keywords = kw_result.get("keywords") if isinstance(kw_result, dict) else None
        if keywords:
            return keywords
        raise ValueError(f"empty keywords from LLM: {kw_result!r}")
    except VisibilityContractError:
        raise
    except Exception as e:
        sys.stderr.write(f"[WARN] keyword_extraction failed: {str(e)[:150]}; using problem words\n")
        return problem.split()[:5]


def _categorize(problem: str) -> dict:
    try:
        meta = call_claude(
            model=model_for_role("meta_categorization"),
            system=load_prompt("meta_categorization"),
            user=problem,
            json_schema=schemas.META_CATEGORIZATION,
            purpose="meta_categorization",
        )
        if isinstance(meta, dict) and "categories" in meta and "domains" in meta:
            return meta
        raise ValueError(f"unexpected meta shape: {meta!r}")
    except VisibilityContractError:
        raise
    except Exception as e:
        sys.stderr.write(f"[WARN] meta_categorization failed: {str(e)[:150]}; using stubs\n")
        return {
            "categories": ["workflow orchestration", "state invariant enforcement", "observability"],
            "domains": ["aerospace fault tolerance", "manufacturing quality control", "financial workflow"],
        }


def phase_0_research(state: dict) -> dict:
    problem = state["problem"]

    # 0a + 0b: keywords and meta-categorization are independent (both only read
    # the raw problem) -> run them in parallel to shave a sequential LLM call.
    emit_stage_progress(
        "phase_0_research", state,
        "Extracting keywords + meta categories (parallel).",
        f"Problem length: {len(problem)} characters.",
    )
    keywords, meta = parallel_run(
        [lambda: _extract_keywords(problem), lambda: _categorize(problem)],
        max_workers=2,
    )
    kw_str = " ".join(keywords)
    state["meta_categories"] = meta["categories"]
    state["meta_domains"] = meta["domains"]
    emit_stage_progress(
        "phase_0_research", state,
        "Keyword + meta extraction complete.",
        f"Keywords: {', '.join(str(k) for k in keywords[:6])}.",
        f"Categories: {', '.join(meta['categories'][:3])}.",
        f"Cross-domain analogies: {', '.join(meta['domains'][:3])}.",
    )

    # Two-wave research: Wave 1 is deliberately BROAD/high-level (not just the
    # technical-specific lookup); then a "soul-searching" reflection challenges
    # the framing and chooses Wave 2's follow-up queries. Both waves are
    # consumed downstream (the old single-batch left meta/cross-domain orphaned).
    cats = meta.get("categories") or [kw_str]
    doms = meta.get("domains") or ["another industry"]
    category0 = cats[0]
    domain0 = doms[0]
    # Wave 1 widened to 5 (searches are parallel, so more ≈ ~free wall-clock):
    # 1 specific + 2 problem-class + 2 cross-domain.
    wave1_queries = [
        f"how to solve {kw_str}",
        f"{category0} how is this class of problem actually solved",
        f"{cats[1] if len(cats) > 1 else category0} systemic prevention best practices",
        f"how does {domain0} solve {category0}",
        f"how does {doms[1] if len(doms) > 1 else domain0} prevent {category0}",
    ]
    emit_stage_progress(
        "phase_0_research",
        state,
        "Web research wave 1 (broad / high-level).",
        f"Queries: {len(wave1_queries)} (specific + problem-class + cross-domain).",
        f"First query: {wave1_queries[0]}",
    )
    wave1_results = parallel_map(_safe_websearch, wave1_queries, max_workers=6)

    # Soul-searching reflection between waves: is the framing right, or are we
    # rushing into technical detail? Pick 2 follow-up searches to test/correct it.
    reflection = _reflect_on_framing(state, problem, wave1_results)
    state["framing_reflection"] = reflection
    emit_stage_progress(
        "phase_0_research",
        state,
        "Framing reflection complete.",
        f"Higher-level question: {str(reflection.get('higher_level_question', ''))[:160]}",
        f"Reframing: {str(reflection.get('reframing', ''))[:160]}",
    )

    wave2_queries = [q for q in (reflection.get("wave2_queries") or []) if isinstance(q, str) and q.strip()][:4]
    if not wave2_queries:
        # Defensive fallback if reflection produced no queries.
        wave2_queries = [
            f"{category0} systemic root cause prevention site:github.com",
            f"{kw_str} post-mortem lessons learned",
        ]
    emit_stage_progress(
        "phase_0_research",
        state,
        "Web research wave 2 (reflection-guided).",
        f"Queries: {len(wave2_queries)} (driven by the framing reflection).",
        f"First query: {wave2_queries[0]}",
    )
    wave2_results = parallel_map(_safe_websearch, wave2_queries, max_workers=6)

    # All research is consumed: wave1+wave2 are the primary signal; the broad
    # problem-class + cross-domain queries are also kept for report citations.
    state["websearch_specific"] = wave1_results + wave2_results
    state["websearch_meta"] = wave1_results[1:3]
    state["websearch_cross_domain"] = wave1_results[3:5]
    emit_stage_progress(
        "phase_0_research",
        state,
        "Web research complete (2 waves).",
        f"Results collected: {len(wave1_results) + len(wave2_results)} ({len(wave1_results)} wave-1, {len(wave2_results)} wave-2).",
    )

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
