"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import require_api_key
from app.db.session import get_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis(request: Request) -> ArqRedis:
    redis: ArqRedis | None = getattr(request.app.state, "redis", None)
    if redis is None:
        settings = get_settings()
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        request.app.state.redis = redis
    return redis


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[ArqRedis, Depends(get_redis)]
ApiKeyDep = Annotated[None, Depends(require_api_key)]
