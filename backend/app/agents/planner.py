"""Planner agent — expands a research topic into searchable queries."""

from __future__ import annotations

from typing import Any

from app.agents.state import ResearchPlan, ResearchState, append_event
from app.core.logging import get_logger
from app.services.llm import LLMClient

logger = get_logger(__name__)

SYSTEM = """You are an academic research planner.
Given a literature review topic, produce a focused search plan.
Prefer precise scholarly queries suitable for arXiv and Semantic Scholar.
Keep queries specific; avoid overly broad single-word queries.
"""


async def planner_node(state: ResearchState, llm: LLMClient) -> dict[str, Any]:
    topic = state["topic"]
    inclusion = state.get("inclusion_notes") or ""
    user = (
        f"Topic: {topic}\n"
        f"Inclusion notes: {inclusion or 'none'}\n"
        f"Year from: {state.get('year_from')}\n"
        f"Year to: {state.get('year_to')}\n"
        "Produce 3-6 search queries, sub-questions, and inclusion/exclusion criteria."
    )
    plan = await llm.complete(
        system=SYSTEM,
        user=user,
        response_model=ResearchPlan,
    )
    assert isinstance(plan, ResearchPlan)
    if not plan.queries:
        plan.queries = [topic]

    logger.info("planner_done", query_count=len(plan.queries))
    return {
        "plan": plan.model_dump(),
        "queries": plan.queries,
        "events": append_event(
            state,
            agent="planner",
            event_type="plan_ready",
            message=f"Planned {len(plan.queries)} search queries",
            payload=plan.model_dump(),
        ),
    }
