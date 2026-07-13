"""Searcher agent — queries arXiv and Semantic Scholar."""

from __future__ import annotations

from typing import Any

from app.agents.state import ResearchState, append_event, papers_from_state, papers_to_state
from app.core.logging import get_logger
from app.services.arxiv_client import ArxivClient
from app.services.paper_dto import PaperRecord, dedupe_papers
from app.services.semantic_scholar import SemanticScholarClient

logger = get_logger(__name__)


async def searcher_node(
    state: ResearchState,
    arxiv: ArxivClient,
    s2: SemanticScholarClient,
) -> dict[str, Any]:
    queries = state.get("queries") or [state["topic"]]
    max_papers = state.get("max_papers") or 20
    per_source = max(3, max_papers // max(len(queries), 1))
    year_from = state.get("year_from")
    year_to = state.get("year_to")

    collected: list[PaperRecord] = papers_from_state(state)
    for query in queries:
        arxiv_hits = await arxiv.search(
            query,
            max_results=per_source,
            year_from=year_from,
            year_to=year_to,
        )
        s2_hits = await s2.search(
            query,
            max_results=per_source,
            year_from=year_from,
            year_to=year_to,
        )
        collected.extend(arxiv_hits)
        collected.extend(s2_hits)

    deduped = dedupe_papers(collected)
    # Prefer higher citation count when truncating
    deduped.sort(
        key=lambda p: (p.citation_count or 0, p.year or 0),
        reverse=True,
    )
    limited = deduped[:max_papers]

    logger.info(
        "searcher_done",
        queries=len(queries),
        raw=len(collected),
        deduped=len(deduped),
        kept=len(limited),
    )
    return {
        "papers": papers_to_state(limited),
        "events": append_event(
            state,
            agent="searcher",
            event_type="search_complete",
            message=f"Collected {len(limited)} unique papers",
            payload={"query_count": len(queries), "paper_count": len(limited)},
        ),
    }
