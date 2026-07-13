"""Pydantic schemas for research jobs and papers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchCreateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=2000)
    max_papers: int | None = Field(default=None, ge=1, le=100)
    max_critic_loops: int | None = Field(default=None, ge=0, le=5)
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    inclusion_notes: str | None = Field(default=None, max_length=4000)
    idempotency_key: str | None = Field(default=None, max_length=128)


class AgentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent: str
    event_type: str
    message: str | None
    payload: dict[str, Any]
    created_at: datetime


class PaperSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    abstract: str | None
    authors: list[Any]
    venue: str | None
    year: int | None
    url: str | None
    source: str
    arxiv_id: str | None
    doi: str | None
    semantic_scholar_id: str | None
    citation_count: int | None
    extractions: dict[str, Any]


class JobPaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relevance_score: float | None
    role: str
    paper: PaperSummaryOut


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    content_md: str
    content_json: dict[str, Any]
    citation_map: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ResearchJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    status: str
    config: dict[str, Any]
    error: str | None
    idempotency_key: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ResearchJobDetailOut(ResearchJobOut):
    events: list[AgentEventOut] = Field(default_factory=list)
    papers: list[JobPaperOut] = Field(default_factory=list)


class ResearchJobListOut(BaseModel):
    items: list[ResearchJobOut]
    total: int
    page: int
    page_size: int


class HealthOut(BaseModel):
    status: str
    version: str


class ReadyOut(BaseModel):
    status: str
    database: bool
    redis: bool
