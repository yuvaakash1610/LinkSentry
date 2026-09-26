from fastapi import APIRouter, Depends
from app.core.config import get_settings
from app.schemas.analyze import ModelInfoResponse
from app.schemas.response import HealthResponse
from app.services.model_service import ModelService, get_model_service

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns high-level service status without leaking internal paths or secrets.",
)
def get_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="linksentry-backend",
        version=settings.APP_VERSION,
    )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Model Metadata",
    description="Returns metadata about analytical models without exposing filesystem paths or secrets.",
)
def get_model_info(
    service: ModelService = Depends(get_model_service),
) -> ModelInfoResponse:
    return service.get_model_info()
