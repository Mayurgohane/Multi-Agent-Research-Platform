"""Shared agent state and structured LLM response models."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

from app.services.paper_dto import PaperRecord


class ResearchPlan(BaseModel):
    queries: list[str] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    notes: str = ""


class PaperExtraction(BaseModel):
    claims: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    relevance_rationale: str = ""
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)


class CriticAssessment(BaseModel):
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    additional_queries: list[str] = Field(default_factory=list)
    should_continue: bool = False
    summary: str = ""


class LiteratureReport(BaseModel):
    title: str
    executive_summary: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    markdown: str = ""


class ResearchState(TypedDict, total=False):
    topic: str
    max_papers: int
    max_critic_loops: int
    year_from: int | None
    year_to: int | None
    inclusion_notes: str | None
    plan: dict[str, Any]
    queries: list[str]
    papers: list[dict[str, Any]]
    critic: dict[str, Any]
    critic_loops: int
    report: dict[str, Any]
    events: list[dict[str, Any]]
    status: Literal["running", "completed", "failed"]
    error: str | None


def papers_from_state(state: ResearchState) -> list[PaperRecord]:
    return [PaperRecord.model_validate(p) for p in state.get("papers", [])]


def papers_to_state(papers: list[PaperRecord]) -> list[dict[str, Any]]:
    return [p.model_dump() for p in papers]


def append_event(
    state: ResearchState,
    *,
    agent: str,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    events = list(state.get("events") or [])
    events.append(
        {
            "agent": agent,
            "event_type": event_type,
            "message": message,
            "payload": payload or {},
        }
    )
    return events
