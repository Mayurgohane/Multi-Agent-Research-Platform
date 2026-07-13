"""arXiv search client."""

from __future__ import annotations

import asyncio

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.services.paper_dto import PaperRecord

logger = get_logger(__name__)


class ArxivClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _search_sync(
        self,
        query: str,
        *,
        max_results: int,
        year_from: int | None,
        year_to: int | None,
    ) -> list[PaperRecord]:
        client = arxiv.Client(
            page_size=min(max_results, 50),
            delay_seconds=3.0,
            num_retries=2,
        )
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        papers: list[PaperRecord] = []
        for result in client.results(search):
            year = result.published.year if result.published else None
            if year_from and year and year < year_from:
                continue
            if year_to and year and year > year_to:
                continue
            arxiv_id = result.get_short_id()
            papers.append(
                PaperRecord(
                    title=result.title.strip(),
                    abstract=(result.summary or "").strip() or None,
                    authors=[a.name for a in result.authors],
                    venue="arXiv",
                    year=year,
                    url=result.entry_id,
                    source="arxiv",
                    arxiv_id=arxiv_id,
                    doi=result.doi,
                    raw_metadata={
                        "categories": list(result.categories),
                        "primary_category": result.primary_category,
                        "pdf_url": result.pdf_url,
                        "comment": result.comment,
                    },
                )
            )
            if len(papers) >= max_results:
                break
        return papers

    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PaperRecord]:
        logger.info("arxiv_search", query=query, max_results=max_results)
        try:
            return await asyncio.to_thread(
                self._search_sync,
                query,
                max_results=max_results,
                year_from=year_from,
                year_to=year_to,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("arxiv_search_failed", query=query)
            raise ExternalServiceError(str(exc), service="arxiv") from exc

    async def get_by_id(self, arxiv_id: str) -> PaperRecord | None:
        results = await self.search(f"id:{arxiv_id}", max_results=1)
        return results[0] if results else None
