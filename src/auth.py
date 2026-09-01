"""Authentication & Rate Limiting."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from src.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

VALID_KEYS = set()
if settings.api_keys:
    VALID_KEYS = {k.strip() for k in settings.api_keys.split(",") if k.strip()}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def validate_api_key(api_key: str = Security(api_key_header)) -> str:
    if not VALID_KEYS:
        return api_key
    if api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
    return api_key


def get_limiter():
    return limiter
