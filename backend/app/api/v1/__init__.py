"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import health, papers, research

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(research.router)
api_router.include_router(papers.router)
