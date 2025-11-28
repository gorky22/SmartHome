from fastapi import Header, HTTPException, status
import os
from typing import Set


from .config import settings


def _get_api_keys() -> Set[str]:
    raw = settings.sensors_api_keys or ""
    return {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key(x_api_key: str | None = Header(None)) -> str | None:
    """FastAPI dependency to require a valid API key in the X-API-Key header.

    If the environment variable SENSORS_API_KEYS is empty the API is open (no key required).
    Otherwise a valid X-API-Key header must be provided.
    """
    keys = _get_api_keys()
    if not keys:
        # No keys configured => open endpoint for development
        return None

    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    if x_api_key not in keys:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    return x_api_key
