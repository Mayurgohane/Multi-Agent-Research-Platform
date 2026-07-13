"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app import __version__
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        json_logs=settings.app_env != "development",
    )
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    logger.info("api_started", env=settings.app_env, version=__version__)
    try:
        yield
    finally:
        redis = getattr(app.state, "redis", None)
        if redis is not None:
            await redis.close()
        await dispose_engine()
        logger.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        status = 404 if exc.code == "not_found" else 409 if exc.code == "job_state_error" else 400
        return ORJSONResponse(
            status_code=status,
            content={"detail": exc.message, "code": exc.code},
        )

    # Health routes are mounted both under prefix and root for probes
    app.include_router(api_router, prefix=settings.api_prefix)
    from app.api.v1 import health

    app.include_router(health.router)
    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug and settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
