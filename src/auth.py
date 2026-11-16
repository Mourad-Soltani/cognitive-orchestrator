"""Authentication & Rate Limiting."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os

from src.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

VALID_KEYS = set()
if settings.api_keys:
    VALID_KEYS = {k.strip() for k in settings.api_keys.split(",") if k.strip()}

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in {"1", "true", "yes"}

# auto_error=False so demo can omit the header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str | None = Security(api_key_header)) -> str:
    if DEMO_MODE or not VALID_KEYS:
        return api_key or "demo"
    if not api_key or api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
    return api_key


def get_limiter():
    return limiter
