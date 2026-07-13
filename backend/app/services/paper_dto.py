"""Shared paper DTO used across search clients and agents."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", "", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


class PaperRecord(BaseModel):
    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    url: str | None = None
    source: Literal["arxiv", "semantic_scholar", "merged"] = "arxiv"
    arxiv_id: str | None = None
    doi: str | None = None
    semantic_scholar_id: str | None = None
    citation_count: int | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    extractions: dict[str, Any] = Field(default_factory=dict)
    relevance_score: float | None = None

    @property
    def title_key(self) -> str:
        return normalize_title(self.title)

    def merge(self, other: PaperRecord) -> PaperRecord:
        """Merge duplicate records preferring richer metadata."""
        return PaperRecord(
            title=self.title or other.title,
            abstract=self.abstract or other.abstract,
            authors=self.authors or other.authors,
            venue=self.venue or other.venue,
            year=self.year or other.year,
            url=self.url or other.url,
            source="merged",
            arxiv_id=self.arxiv_id or other.arxiv_id,
            doi=self.doi or other.doi,
            semantic_scholar_id=self.semantic_scholar_id or other.semantic_scholar_id,
            citation_count=_max_optional(self.citation_count, other.citation_count),
            raw_metadata={**other.raw_metadata, **self.raw_metadata},
            extractions={**other.extractions, **self.extractions},
            relevance_score=_max_optional(self.relevance_score, other.relevance_score),
        )


def _max_optional(a: int | float | None, b: int | float | None) -> int | float | None:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def dedupe_papers(papers: list[PaperRecord]) -> list[PaperRecord]:
    """Dedupe by DOI, arXiv ID, Semantic Scholar ID, then normalized title."""
    by_key: dict[str, PaperRecord] = {}
    order: list[str] = []

    for paper in papers:
        keys: list[str] = []
        if paper.doi:
            keys.append(f"doi:{paper.doi.lower()}")
        if paper.arxiv_id:
            keys.append(f"arxiv:{paper.arxiv_id.lower()}")
        if paper.semantic_scholar_id:
            keys.append(f"s2:{paper.semantic_scholar_id}")
        keys.append(f"title:{paper.title_key}")

        existing_key: str | None = None
        for key in keys:
            if key in by_key:
                existing_key = key
                break

        if existing_key is None:
            primary = keys[0]
            by_key[primary] = paper
            for key in keys[1:]:
                by_key[key] = paper
            order.append(primary)
        else:
            merged = by_key[existing_key].merge(paper)
            # Rebind all known keys to merged record
            affected = [k for k, v in by_key.items() if v is by_key[existing_key] or k in keys]
            for key in {*affected, *keys}:
                by_key[key] = merged

    seen: set[int] = set()
    result: list[PaperRecord] = []
    for key in order:
        paper = by_key[key]
        identity = id(paper)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(paper)
    return result
