"""Paper lookup routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import ApiKeyDep, DbDep, SettingsDep
from app.core.exceptions import NotFoundError
from app.schemas import PaperSummaryOut
from app.services.research_service import ResearchService

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/{paper_id}", response_model=PaperSummaryOut)
async def get_paper(
    paper_id: uuid.UUID,
    db: DbDep,
    settings: SettingsDep,
    _: ApiKeyDep,
) -> PaperSummaryOut:
    service = ResearchService(db, settings)
    try:
        paper = await service.get_paper(paper_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return PaperSummaryOut.model_validate(paper)
