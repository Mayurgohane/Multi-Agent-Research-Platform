"""Reader agent — extracts claims/methods/limitations from papers."""

from __future__ import annotations

from typing import Any

from app.agents.state import PaperExtraction, ResearchState, append_event, papers_to_state
from app.core.logging import get_logger
from app.services.llm import LLMClient
from app.services.paper_dto import PaperRecord

logger = get_logger(__name__)

SYSTEM = """You are an academic paper reader.
Extract key claims, methods, and limitations from the paper abstract/metadata.
Score relevance to the research topic from 0 to 1.
Be concise and faithful to the source; do not invent findings.
"""


async def reader_node(state: ResearchState, llm: LLMClient) -> dict[str, Any]:
    topic = state["topic"]
    plan = state.get("plan") or {}
    criteria = plan.get("inclusion_criteria") or []
    raw_papers = state.get("papers") or []
    enriched: list[PaperRecord] = []

    for item in raw_papers:
        paper = PaperRecord.model_validate(item)
        if paper.extractions:
            enriched.append(paper)
            continue

        user = (
            f"Research topic: {topic}\n"
            f"Inclusion criteria: {criteria}\n"
            f"Title: {paper.title}\n"
            f"Year: {paper.year}\n"
            f"Venue: {paper.venue}\n"
            f"Authors: {', '.join(paper.authors)}\n"
            f"Abstract: {paper.abstract or 'N/A'}\n"
        )
        try:
            extraction = await llm.complete(
                system=SYSTEM,
                user=user,
                response_model=PaperExtraction,
            )
            assert isinstance(extraction, PaperExtraction)
            paper.extractions = extraction.model_dump()
            paper.relevance_score = extraction.relevance_score
        except Exception as exc:  # noqa: BLE001
            logger.warning("reader_paper_failed", title=paper.title, error=str(exc))
            paper.extractions = {
                "claims": [],
                "methods": [],
                "limitations": [],
                "relevance_rationale": f"Extraction failed: {exc}",
                "relevance_score": 0.3,
            }
            paper.relevance_score = 0.3
        enriched.append(paper)

    enriched.sort(key=lambda p: p.relevance_score or 0.0, reverse=True)
    logger.info("reader_done", papers=len(enriched))
    return {
        "papers": papers_to_state(enriched),
        "events": append_event(
            state,
            agent="reader",
            event_type="reading_complete",
            message=f"Extracted insights from {len(enriched)} papers",
            payload={"paper_count": len(enriched)},
        ),
    }
