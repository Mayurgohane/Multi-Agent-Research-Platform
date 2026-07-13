"""API health endpoint tests with dependency overrides."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1 import health
from app.core.deps import get_db, get_redis


@pytest.fixture
def app():
    application = FastAPI()
    application.include_router(health.router)

    async def fake_db():
        session = MagicMock()
        session.execute = AsyncMock(return_value=None)
        yield session

    async def fake_redis():
        redis = MagicMock()
        redis.ping = AsyncMock(return_value=True)
        return redis

    application.dependency_overrides[get_db] = fake_db
    application.dependency_overrides[get_redis] = fake_redis
    yield application
    application.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.asyncio
async def test_ready(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] is True
    assert body["redis"] is True
    assert body["status"] == "ok"
