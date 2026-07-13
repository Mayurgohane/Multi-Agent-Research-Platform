"""Research job API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import ApiKeyDep, DbDep, RedisDep, SettingsDep
from app.core.exceptions import JobStateError, NotFoundError
from app.models import JobStatus
from app.schemas import (
    JobPaperOut,
    PaperSummaryOut,
    ReportOut,
    ResearchCreateRequest,
    ResearchJobDetailOut,
    ResearchJobListOut,
    ResearchJobOut,
)
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


def _to_detail(job) -> ResearchJobDetailOut:
    papers = []
    for link in job.job_papers or []:
        papers.append(
            JobPaperOut(
                relevance_score=link.relevance_score,
                role=link.role,
                paper=PaperSummaryOut.model_validate(link.paper),
            )
        )
    base = ResearchJobOut.model_validate(job)
    return ResearchJobDetailOut(
        **base.model_dump(),
        events=job.events or [],
        papers=papers,
    )


@router.post(
    "",
    response_model=ResearchJobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_research(
    body: ResearchCreateRequest,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
    _: ApiKeyDep,
) -> ResearchJobOut:
    service = ResearchService(db, settings)
    job = await service.create_job(
        topic=body.topic,
        max_papers=body.max_papers,
        max_critic_loops=body.max_critic_loops,
        year_from=body.year_from,
        year_to=body.year_to,
        inclusion_notes=body.inclusion_notes,
        idempotency_key=body.idempotency_key,
    )
    await db.flush()

    if job.status == JobStatus.QUEUED.value and not job.arq_job_id:
        arq_job = await redis.enqueue_job("run_research_job", str(job.id))
        job.arq_job_id = arq_job.job_id if arq_job else None
        await db.flush()

    return ResearchJobOut.model_validate(job)


@router.get("", response_model=ResearchJobListOut)
async def list_research(
    db: DbDep,
    settings: SettingsDep,
    _: ApiKeyDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ResearchJobListOut:
    service = ResearchService(db, settings)
    items, total = await service.list_jobs(page=page, page_size=page_size)
    return ResearchJobListOut(
        items=[ResearchJobOut.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=ResearchJobDetailOut)
async def get_research(
    job_id: uuid.UUID,
    db: DbDep,
    settings: SettingsDep,
    _: ApiKeyDep,
) -> ResearchJobDetailOut:
    service = ResearchService(db, settings)
    try:
        job = await service.get_job(job_id, detail=True)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return _to_detail(job)


@router.get("/{job_id}/report", response_model=ReportOut)
async def get_research_report(
    job_id: uuid.UUID,
    db: DbDep,
    settings: SettingsDep,
    _: ApiKeyDep,
) -> ReportOut:
    service = ResearchService(db, settings)
    try:
        report = await service.get_report(job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return ReportOut.model_validate(report)


@router.delete("/{job_id}", response_model=ResearchJobOut)
async def cancel_research(
    job_id: uuid.UUID,
    db: DbDep,
    settings: SettingsDep,
    _: ApiKeyDep,
) -> ResearchJobOut:
    service = ResearchService(db, settings)
    try:
        job = await service.cancel_job(job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except JobStateError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    return ResearchJobOut.model_validate(job)
