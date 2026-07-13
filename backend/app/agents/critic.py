"""Critic agent — coverage gaps and optional follow-up searches."""

from __future__ import annotations

from typing import Any

from app.agents.state import CriticAssessment, ResearchState, append_event
from app.core.logging import get_logger
from app.services.llm import LLMClient

logger = get_logger(__name__)

SYSTEM = """You are a rigorous academic research critic.
Assess whether the collected papers adequately cover the topic.
Identify gaps, contradictions, and whether another search round is warranted.
Only set should_continue=true when gaps are material and additional_queries are specific.
"""


async def critic_node(state: ResearchState, llm: LLMClient) -> dict[str, Any]:
    topic = state["topic"]
    loops = int(state.get("critic_loops") or 0)
    max_loops = int(state.get("max_critic_loops") or 2)
    papers = state.get("papers") or []

    paper_summaries = []
    for p in papers[:30]:
        paper_summaries.append(
            {
                "title": p.get("title"),
                "year": p.get("year"),
                "relevance_score": p.get("relevance_score"),
                "extractions": p.get("extractions"),
            }
        )

    user = (
        f"Topic: {topic}\n"
        f"Plan: {state.get('plan')}\n"
        f"Critic loop: {loops}/{max_loops}\n"
        f"Papers ({len(papers)}):\n{paper_summaries}\n"
        "Assess coverage and decide if another search round is needed."
    )
    assessment = await llm.complete(
        system=SYSTEM,
        user=user,
        response_model=CriticAssessment,
    )
    assert isinstance(assessment, CriticAssessment)

    if loops >= max_loops:
        assessment.should_continue = False
        assessment.additional_queries = []

    updates: dict[str, Any] = {
        "critic": assessment.model_dump(),
        "critic_loops": loops + 1,
        "events": append_event(
            state,
            agent="critic",
            event_type="critique_complete",
            message=assessment.summary or "Critique finished",
            payload=assessment.model_dump(),
        ),
    }
    if assessment.should_continue and assessment.additional_queries:
        updates["queries"] = assessment.additional_queries

    logger.info(
        "critic_done",
        coverage=assessment.coverage_score,
        continue_search=assessment.should_continue,
        loop=loops + 1,
    )
    return updates


def should_continue_search(state: ResearchState) -> str:
    critic = state.get("critic") or {}
    if critic.get("should_continue") and critic.get("additional_queries"):
        return "searcher"
    return "writer"
