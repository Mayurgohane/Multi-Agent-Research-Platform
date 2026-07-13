"""Security helpers and API-key dependency."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import Settings, get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings | None = None,
) -> None:
    """Validate X-API-Key when API key auth is enabled."""
    settings = settings or get_settings()
    if not settings.api_key_required:
        return

    expected = settings.api_key.get_secret_value() if settings.api_key else None
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
