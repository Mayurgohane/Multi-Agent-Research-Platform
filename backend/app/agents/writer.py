"""Writer agent — produces a cited literature review."""

from __future__ import annotations

from typing import Any

from app.agents.state import LiteratureReport, ResearchState, append_event
from app.core.logging import get_logger
from app.services.llm import LLMClient

logger = get_logger(__name__)

SYSTEM = """You are an academic literature review writer.
Write a clear, structured review grounded only in the provided papers.
Use inline citations like [1], [2] matching the numbered bibliography.
Include: executive summary, thematic synthesis, methods landscape,
limitations/gaps, and open questions.
Also return full markdown suitable for publication as a draft review.
"""


def _build_bibliography(papers: list[dict[str, Any]]) -> dict[str, Any]:
    citation_map: dict[str, Any] = {}
    lines: list[str] = []
    for idx, paper in enumerate(papers, start=1):
        authors = paper.get("authors") or []
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        year = paper.get("year") or "n.d."
        title = paper.get("title")
        url = paper.get("url") or ""
        doi = paper.get("doi")
        entry = f"[{idx}] {author_str} ({year}). {title}."
        if doi:
            entry += f" DOI: {doi}."
        if url:
            entry += f" {url}"
        lines.append(entry)
        citation_map[str(idx)] = {
            "title": title,
            "authors": authors,
            "year": paper.get("year"),
            "url": url,
            "doi": doi,
            "arxiv_id": paper.get("arxiv_id"),
            "semantic_scholar_id": paper.get("semantic_scholar_id"),
        }
    return {"lines": lines, "citation_map": citation_map}


async def writer_node(state: ResearchState, llm: LLMClient) -> dict[str, Any]:
    topic = state["topic"]
    papers = sorted(
        state.get("papers") or [],
        key=lambda p: p.get("relevance_score") or 0.0,
        reverse=True,
    )
    bib = _build_bibliography(papers)
    critic = state.get("critic") or {}

    paper_blocks = []
    for idx, paper in enumerate(papers, start=1):
        paper_blocks.append(
            {
                "citation": idx,
                "title": paper.get("title"),
                "year": paper.get("year"),
                "venue": paper.get("venue"),
                "abstract": paper.get("abstract"),
                "extractions": paper.get("extractions"),
            }
        )

    user = (
        f"Topic: {topic}\n"
        f"Research plan: {state.get('plan')}\n"
        f"Critic assessment: {critic}\n"
        f"Papers:\n{paper_blocks}\n"
        f"Bibliography lines:\n{bib['lines']}\n"
        "Write the literature review. Include a References section using the bibliography lines."
    )
    report = await llm.complete(
        system=SYSTEM,
        user=user,
        response_model=LiteratureReport,
    )
    assert isinstance(report, LiteratureReport)

    markdown = report.markdown.strip()
    if "References" not in markdown and bib["lines"]:
        markdown = markdown + "\n\n## References\n\n" + "\n".join(bib["lines"])

    content_json = {
        "title": report.title,
        "executive_summary": report.executive_summary,
        "sections": report.sections,
        "open_questions": report.open_questions,
        "critic": critic,
        "paper_count": len(papers),
    }

    logger.info("writer_done", papers=len(papers), title=report.title)
    return {
        "report": {
            "content_md": markdown,
            "content_json": content_json,
            "citation_map": bib["citation_map"],
        },
        "status": "completed",
        "events": append_event(
            state,
            agent="writer",
            event_type="report_ready",
            message=f"Generated literature review: {report.title}",
            payload={"paper_count": len(papers)},
        ),
    }
