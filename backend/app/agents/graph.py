"""LangGraph orchestration for the academic research pipeline."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.critic import critic_node, should_continue_search
from app.agents.planner import planner_node
from app.agents.reader import reader_node
from app.agents.searcher import searcher_node
from app.agents.state import ResearchState
from app.agents.writer import writer_node
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.arxiv_client import ArxivClient
from app.services.llm import LLMClient
from app.services.semantic_scholar import SemanticScholarClient

logger = get_logger(__name__)


class ResearchGraph:
    """Compiles and runs the multi-agent research workflow."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        llm: LLMClient | None = None,
        arxiv: ArxivClient | None = None,
        s2: SemanticScholarClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or LLMClient(self.settings)
        self.arxiv = arxiv or ArxivClient(self.settings)
        self.s2 = s2 or SemanticScholarClient(self.settings)
        self._graph = self._build()

    def _build(self):
        graph = StateGraph(ResearchState)

        async def planner(state: ResearchState) -> dict[str, Any]:
            return await planner_node(state, self.llm)

        async def searcher(state: ResearchState) -> dict[str, Any]:
            return await searcher_node(state, self.arxiv, self.s2)

        async def reader(state: ResearchState) -> dict[str, Any]:
            return await reader_node(state, self.llm)

        async def critic(state: ResearchState) -> dict[str, Any]:
            return await critic_node(state, self.llm)

        async def writer(state: ResearchState) -> dict[str, Any]:
            return await writer_node(state, self.llm)

        graph.add_node("planner", planner)
        graph.add_node("searcher", searcher)
        graph.add_node("reader", reader)
        graph.add_node("critic", critic)
        graph.add_node("writer", writer)

        graph.set_entry_point("planner")
        graph.add_edge("planner", "searcher")
        graph.add_edge("searcher", "reader")
        graph.add_edge("reader", "critic")
        graph.add_conditional_edges(
            "critic",
            should_continue_search,
            {"searcher": "searcher", "writer": "writer"},
        )
        graph.add_edge("writer", END)
        return graph.compile()

    async def run(self, initial: ResearchState) -> ResearchState:
        logger.info("research_graph_start", topic=initial.get("topic"))
        result = await self._graph.ainvoke(initial)
        logger.info(
            "research_graph_done",
            topic=initial.get("topic"),
            status=result.get("status"),
            papers=len(result.get("papers") or []),
        )
        return result  # type: ignore[return-value]

    async def aclose(self) -> None:
        await self.s2.aclose()
