"""
API authentication middleware.

Supports API key authentication via header.
"""

from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader as FastAPIKeyHeader

from undertow.config import settings

# API key header configuration
APIKeyHeader = FastAPIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication",
)


async def api_key_auth(
    api_key: Optional[str] = Security(APIKeyHeader),
) -> str:
    """
    Validate API key from header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If key is missing or invalid
    """
    # Skip auth in development if no key configured
    if settings.is_development and not settings.api_keys:
        return "development"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


def require_auth():
    """
    Dependency that requires authentication.

    Use as a dependency in routes that need auth:

        @router.get("/protected", dependencies=[Depends(require_auth())])
        async def protected_route():
            ...
    """
    return Security(api_key_auth)

