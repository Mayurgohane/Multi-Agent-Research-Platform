"""Semantic Scholar Graph API client."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.services.paper_dto import PaperRecord

logger = get_logger(__name__)

S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = (
    "paperId,externalIds,title,abstract,year,venue,citationCount,authors,url,publicationTypes"
)


class SemanticScholarClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self.settings.arxiv_user_agent,
        }
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key.get_secret_value()
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=S2_BASE,
                timeout=self.settings.http_timeout_seconds,
                headers=self._headers(),
            )
        return self._client

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PaperRecord]:
        logger.info("s2_search", query=query, max_results=max_results)
        client = await self._get_client()
        params: dict[str, Any] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": S2_FIELDS,
        }
        if year_from or year_to:
            start = year_from or 1900
            end = year_to or 2100
            params["year"] = f"{start}-{end}"

        try:
            response = await client.get("/paper/search", params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("s2_search_failed", query=query)
            raise ExternalServiceError(str(exc), service="semantic_scholar") from exc

        papers: list[PaperRecord] = []
        for item in data.get("data") or []:
            record = self._to_record(item)
            if record:
                papers.append(record)
            if len(papers) >= max_results:
                break
        return papers

    async def get_paper(self, paper_id: str) -> PaperRecord | None:
        client = await self._get_client()
        try:
            response = await client.get(
                f"/paper/{paper_id}",
                params={"fields": S2_FIELDS},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._to_record(response.json())
        except httpx.HTTPError as exc:
            raise ExternalServiceError(str(exc), service="semantic_scholar") from exc

    def _to_record(self, item: dict[str, Any]) -> PaperRecord | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None
        external = item.get("externalIds") or {}
        authors = [a.get("name") for a in (item.get("authors") or []) if a.get("name")]
        return PaperRecord(
            title=title,
            abstract=(item.get("abstract") or None),
            authors=authors,
            venue=item.get("venue"),
            year=item.get("year"),
            url=item.get("url"),
            source="semantic_scholar",
            arxiv_id=external.get("ArXiv"),
            doi=external.get("DOI"),
            semantic_scholar_id=item.get("paperId"),
            citation_count=item.get("citationCount"),
            raw_metadata={
                "publicationTypes": item.get("publicationTypes"),
                "externalIds": external,
            },
        )
