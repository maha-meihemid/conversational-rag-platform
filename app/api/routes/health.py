from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.models.health import HealthResponse, ReadinessResponse
from app.services.readiness import run_readiness_checks

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="conversational-rag-platform")


ReadinessChecksDependency = Annotated[
    dict[str, str],
    Depends(run_readiness_checks),
]


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(
    response: Response,
    checks: ReadinessChecksDependency,
) -> ReadinessResponse:
    is_ready = all(result == "ok" for result in checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if is_ready else "unavailable",
        checks=checks,
    )
