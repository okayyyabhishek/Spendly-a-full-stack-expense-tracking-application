"""Operational health endpoint used by local development and deployment checks."""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API availability",
)
def health_check() -> HealthResponse:
    """Return a lightweight liveness response without exposing configuration or database details."""
    return HealthResponse(status="ok", service="expense-tracker-api", version="0.1.0")
