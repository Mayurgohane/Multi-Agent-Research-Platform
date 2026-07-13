"""ARQ worker for asynchronous research jobs."""

from __future__ import annotations

import uuid

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import get_session_factory
from app.services.research_service import ResearchService

logger = get_logger(__name__)


async def run_research_job(ctx: dict, job_id: str) -> str:
    """ARQ task entrypoint."""
    logger.info("worker_job_received", job_id=job_id)
    factory = get_session_factory()
    async with factory() as session:
        service = ResearchService(session)
        await service.run_job(uuid.UUID(job_id))
    logger.info("worker_job_finished", job_id=job_id)
    return job_id


async def startup(ctx: dict) -> None:
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        json_logs=settings.app_env != "development",
    )
    logger.info("worker_started", env=settings.app_env)


async def shutdown(ctx: dict) -> None:
    logger.info("worker_stopped")


class WorkerSettings:
    functions = [run_research_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 2
    job_timeout = 60 * 30  # 30 minutes
    keep_result = 60 * 60


def main() -> None:
    """CLI entry: python -m app.workers.research_worker"""
    import sys

    from arq.cli import cli

    sys.argv = ["arq", "app.workers.research_worker.WorkerSettings"]
    cli()


if __name__ == "__main__":
    main()
