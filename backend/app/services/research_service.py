"""Persist and execute research jobs."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph import ResearchGraph
from app.agents.state import ResearchState
from app.core.config import Settings, get_settings
from app.core.exceptions import JobStateError, NotFoundError
from app.core.logging import get_logger
from app.models import AgentEvent, JobPaper, JobStatus, Paper, Report, ResearchJob
from app.services.paper_dto import PaperRecord

logger = get_logger(__name__)


class ResearchService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def create_job(
        self,
        *,
        topic: str,
        max_papers: int | None = None,
        max_critic_loops: int | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        inclusion_notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> ResearchJob:
        if idempotency_key:
            existing = await self.session.scalar(
                select(ResearchJob).where(ResearchJob.idempotency_key == idempotency_key)
            )
            if existing:
                return existing

        config = {
            "max_papers": max_papers or self.settings.default_max_papers,
            "max_critic_loops": max_critic_loops
            if max_critic_loops is not None
            else self.settings.default_max_critic_loops,
            "year_from": year_from,
            "year_to": year_to,
            "inclusion_notes": inclusion_notes,
        }
        job = ResearchJob(
            topic=topic.strip(),
            status=JobStatus.QUEUED.value,
            config=config,
            idempotency_key=idempotency_key,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(self, job_id: uuid.UUID, *, detail: bool = False) -> ResearchJob:
        stmt = select(ResearchJob).where(ResearchJob.id == job_id)
        if detail:
            stmt = stmt.options(
                selectinload(ResearchJob.events),
                selectinload(ResearchJob.job_papers).selectinload(JobPaper.paper),
                selectinload(ResearchJob.report),
            )
        job = await self.session.scalar(stmt)
        if not job:
            raise NotFoundError(f"Research job {job_id} not found")
        return job

    async def list_jobs(
        self, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[ResearchJob], int]:
        from sqlalchemy import func

        total = await self.session.scalar(select(func.count()).select_from(ResearchJob)) or 0
        offset = (page - 1) * page_size
        rows = (
            await self.session.scalars(
                select(ResearchJob)
                .order_by(ResearchJob.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()
        return list(rows), int(total)

    async def cancel_job(self, job_id: uuid.UUID) -> ResearchJob:
        job = await self.get_job(job_id)
        if job.status in {JobStatus.COMPLETED.value, JobStatus.FAILED.value}:
            raise JobStateError(f"Cannot cancel job in status {job.status}")
        job.mark_cancelled()
        await self.session.flush()
        return job

    async def get_report(self, job_id: uuid.UUID) -> Report:
        job = await self.get_job(job_id, detail=True)
        if not job.report:
            raise NotFoundError(f"Report for job {job_id} not found")
        return job.report

    async def get_paper(self, paper_id: uuid.UUID) -> Paper:
        paper = await self.session.scalar(select(Paper).where(Paper.id == paper_id))
        if not paper:
            raise NotFoundError(f"Paper {paper_id} not found")
        return paper

    async def run_job(self, job_id: uuid.UUID, graph: ResearchGraph | None = None) -> ResearchJob:
        job = await self.get_job(job_id)
        if job.status == JobStatus.CANCELLED.value:
            logger.info("job_skipped_cancelled", job_id=str(job_id))
            return job
        if job.status not in {JobStatus.QUEUED.value, JobStatus.RUNNING.value}:
            raise JobStateError(f"Job {job_id} is not runnable (status={job.status})")

        job.mark_running()
        await self._add_event(job, "orchestrator", "job_started", "Research job started")
        await self.session.commit()

        owns_graph = graph is None
        graph = graph or ResearchGraph(self.settings)
        try:
            initial: ResearchState = {
                "topic": job.topic,
                "max_papers": int(job.config.get("max_papers", self.settings.default_max_papers)),
                "max_critic_loops": int(
                    job.config.get(
                        "max_critic_loops",
                        self.settings.default_max_critic_loops,
                    )
                ),
                "year_from": job.config.get("year_from"),
                "year_to": job.config.get("year_to"),
                "inclusion_notes": job.config.get("inclusion_notes"),
                "papers": [],
                "queries": [],
                "events": [],
                "critic_loops": 0,
                "status": "running",
            }
            result = await graph.run(initial)

            # Re-check cancellation
            await self.session.refresh(job)
            if job.status == JobStatus.CANCELLED.value:
                return job

            await self._persist_result(job, result)
            job.mark_completed()
            await self._add_event(
                job,
                "orchestrator",
                "job_completed",
                "Research job completed successfully",
            )
            await self.session.commit()
            return job
        except Exception as exc:  # noqa: BLE001
            logger.exception("job_failed", job_id=str(job_id))
            await self.session.rollback()
            job = await self.get_job(job_id)
            job.mark_failed(str(exc))
            await self._add_event(
                job,
                "orchestrator",
                "job_failed",
                str(exc),
                payload={"error": str(exc)},
            )
            await self.session.commit()
            raise
        finally:
            if owns_graph:
                await graph.aclose()

    async def _persist_result(self, job: ResearchJob, result: ResearchState) -> None:
        for event in result.get("events") or []:
            await self._add_event(
                job,
                event.get("agent", "unknown"),
                event.get("event_type", "event"),
                event.get("message"),
                payload=event.get("payload") or {},
            )

        for item in result.get("papers") or []:
            record = PaperRecord.model_validate(item)
            paper = await self._upsert_paper(record)
            link = JobPaper(
                job_id=job.id,
                paper_id=paper.id,
                relevance_score=record.relevance_score,
                role="included",
            )
            self.session.add(link)

        report_data = result.get("report") or {}
        if report_data:
            report = Report(
                job_id=job.id,
                content_md=report_data.get("content_md") or "",
                content_json=report_data.get("content_json") or {},
                citation_map=report_data.get("citation_map") or {},
            )
            self.session.add(report)

        await self.session.flush()

    async def _upsert_paper(self, record: PaperRecord) -> Paper:
        existing: Paper | None = None
        if record.doi:
            existing = await self.session.scalar(select(Paper).where(Paper.doi == record.doi))
        if existing is None and record.arxiv_id:
            existing = await self.session.scalar(
                select(Paper).where(Paper.arxiv_id == record.arxiv_id)
            )
        if existing is None and record.semantic_scholar_id:
            existing = await self.session.scalar(
                select(Paper).where(Paper.semantic_scholar_id == record.semantic_scholar_id)
            )

        if existing:
            existing.abstract = existing.abstract or record.abstract
            existing.authors = existing.authors or record.authors
            existing.venue = existing.venue or record.venue
            existing.year = existing.year or record.year
            existing.url = existing.url or record.url
            counts = [c for c in (existing.citation_count, record.citation_count) if c is not None]
            existing.citation_count = max(counts) if counts else None
            if record.extractions:
                existing.extractions = {**existing.extractions, **record.extractions}
            await self.session.flush()
            return existing

        paper = Paper(
            title=record.title,
            abstract=record.abstract,
            authors=record.authors,
            venue=record.venue,
            year=record.year,
            url=record.url,
            source=record.source,
            arxiv_id=record.arxiv_id,
            doi=record.doi,
            semantic_scholar_id=record.semantic_scholar_id,
            citation_count=record.citation_count,
            extractions=record.extractions,
            raw_metadata=record.raw_metadata,
        )
        self.session.add(paper)
        await self.session.flush()
        return paper

    async def _add_event(
        self,
        job: ResearchJob,
        agent: str,
        event_type: str,
        message: str | None,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            AgentEvent(
                job_id=job.id,
                agent=agent,
                event_type=event_type,
                message=message,
                payload=payload or {},
            )
        )
