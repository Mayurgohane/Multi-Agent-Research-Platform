"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.deps import DbDep, RedisDep
from app.schemas import HealthOut, ReadyOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok", version=__version__)


@router.get("/ready", response_model=ReadyOut)
async def ready(db: DbDep, redis: RedisDep) -> ReadyOut:
    database_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # noqa: BLE001
        database_ok = False

    try:
        pong = await redis.ping()
        redis_ok = bool(pong)
    except Exception:  # noqa: BLE001
        redis_ok = False

    status = "ok" if database_ok and redis_ok else "degraded"
    return ReadyOut(status=status, database=database_ok, redis=redis_ok)
