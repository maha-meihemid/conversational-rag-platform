import secrets
from functools import lru_cache
from hashlib import sha256
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.services.conversation import ConversationService, create_conversation_service

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    expected_key = settings.app_api_key.get_secret_value()
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured.",
        )
    if api_key is None or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return sha256(api_key.encode()).hexdigest()


APIKeyDependency = Annotated[str, Security(require_api_key)]


@lru_cache
def get_chat_rate_limiter() -> RateLimiter:
    return RateLimiter(
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def enforce_chat_rate_limit(
    client_id: APIKeyDependency,
    limiter: Annotated[RateLimiter, Depends(get_chat_rate_limiter)],
) -> None:
    retry_after = limiter.check(client_id)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many chat requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


ChatRateLimitDependency = Annotated[None, Depends(enforce_chat_rate_limit)]


@lru_cache
def get_conversation_service() -> ConversationService:
    return create_conversation_service()
